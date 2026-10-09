"""Integration tests for deterministic MPC event-window panel."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from bisect import bisect_left, bisect_right
from collections import Counter
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
    MPC_EVENT_HALF_WINDOWS,
    MPC_LONGER_END_TENORS,
    MPC_SHORT_END_TENORS,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_mpc_event_window_panel.py"

EXPECTED_SHA256 = "b99224391fd254d3404ca7e0ce27073b2fdceee12cc0703a54af9b32e125472f"

EXPECTED_HEADERS = [
    "event_date",
    "decision_type",
    "policy_change_bps",
    "previous_rate_pct",
    "announced_rate_pct",
    "effective_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "half_window",
    "event_same_day_curve_observation",
    "left_observation_date",
    "right_observation_date",
    "left_yield_pct",
    "right_yield_pct",
    "window_change_bps",
    "eligibility_status",
    "ineligibility_reason",
    "endpoint_method",
    "left_source_organization",
    "left_source_file",
    "left_ingestion_run_id",
    "right_source_organization",
    "right_source_file",
    "right_ingestion_run_id",
    "mpc_source_organization",
    "mpc_ingestion_run_id",
]

EXPECTED_REASONS = {
    "INSUFFICIENT_LEFT_CURVE_HISTORY": 234,
    "MISSING_TENOR_BOTH_ENDPOINTS": 12,
    "MISSING_TENOR_RIGHT_ENDPOINT": 2,
}

PKRV_TENORS = tuple(MPC_SHORT_END_TENORS) + tuple(MPC_LONGER_END_TENORS)

PKISRV_TENORS = tuple(MPC_SHORT_END_TENORS)


def load_builder_module() -> ModuleType:
    """Load the event-window builder."""

    spec = importlib.util.spec_from_file_location(
        "build_mpc_event_window_panel",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()


def read_generated(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one generated event-window artifact."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Generate artifact into isolated temporary location."""

    output_path = tmp_path / file_name

    monkeypatch.setattr(
        BUILDER,
        "OUTPUT_PATH",
        output_path,
    )

    BUILDER.main()

    assert output_path.is_file()

    return output_path


def normalized_inputs() -> tuple[
    list[object],
    list[object],
]:
    """Return frozen normalized MPC and yield rows."""

    connection = get_connection(DATABASE_PATH)

    try:
        events = connection.execute(
            """
            SELECT
                event_date,
                decision_type,
                previous_rate_pct,
                announced_rate_pct,
                change_bps,
                effective_date,
                source_organization,
                ingestion_run_id
            FROM mpc_events
            ORDER BY event_date
            """
        ).fetchall()

        yields = connection.execute(
            """
            SELECT
                observation_date,
                curve_type,
                tenor,
                tenor_years,
                yield_pct,
                source_organization,
                source_file,
                ingestion_run_id
            FROM yield_observations
            WHERE curve_type IN ('PKRV', 'PKISRV')
            ORDER BY
                observation_date,
                curve_type,
                tenor_years,
                tenor
            """
        ).fetchall()

    finally:
        connection.close()

    return events, yields


def endpoint_dates(
    dates: list[str],
    event_date: str,
    half_window: int,
) -> tuple[str | None, str | None]:
    """Independently reproduce D090 endpoint selection."""

    left_index = bisect_left(dates, event_date)
    right_index = bisect_right(dates, event_date)

    left = dates[left_index - half_window] if left_index >= half_window else None

    right_position = right_index + half_window - 1

    right = dates[right_position] if right_position < len(dates) else None

    return left, right


def test_event_window_panel_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artifact shape, census, and frozen digest must remain stable."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "event_windows.csv",
    )

    headers, rows = read_generated(output_path)

    assert headers == EXPECTED_HEADERS
    assert tuple(MPC_EVENT_HALF_WINDOWS) == (1, 3, 5)

    assert len(rows) == 936

    keys = {
        (
            row["event_date"],
            row["curve_type"],
            row["tenor"],
            row["half_window"],
        )
        for row in rows
    }

    assert len(keys) == 936

    assert Counter(row["curve_type"] for row in rows) == {
        "PKRV": 585,
        "PKISRV": 351,
    }

    assert Counter(row["eligibility_status"] for row in rows) == {
        "ELIGIBLE": 688,
        "INELIGIBLE": 248,
    }

    assert (
        Counter(
            row["ineligibility_reason"]
            for row in rows
            if row["eligibility_status"] == "INELIGIBLE"
        )
        == EXPECTED_REASONS
    )

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_every_row_reconciles_to_normalized_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every endpoint and value must reconcile to actual normalized rows."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "reconcile.csv",
    )

    _, rows = read_generated(output_path)

    events, yields = normalized_inputs()

    event_by_date = {row["event_date"]: row for row in events}

    observations = {
        (
            row["curve_type"],
            row["observation_date"],
            row["tenor"],
        ): row
        for row in yields
    }

    dates_by_curve = {
        "PKRV": sorted(
            {row["observation_date"] for row in yields if row["curve_type"] == "PKRV"}
        ),
        "PKISRV": sorted(
            {row["observation_date"] for row in yields if row["curve_type"] == "PKISRV"}
        ),
    }

    for row in rows:
        event = event_by_date[row["event_date"]]

        assert row["decision_type"] == event["decision_type"]
        assert int(row["policy_change_bps"]) == event["change_bps"]

        assert row["mpc_source_organization"] == (event["source_organization"])

        assert int(row["mpc_ingestion_run_id"]) == (event["ingestion_run_id"])

        curve = row["curve_type"]
        tenor = row["tenor"]
        half_window = int(row["half_window"])

        assert Decimal(row["tenor_years"]) == Decimal(str(TENOR_TO_YEARS[tenor]))

        left_date, right_date = endpoint_dates(
            dates_by_curve[curve],
            row["event_date"],
            half_window,
        )

        assert row["left_observation_date"] == (left_date or "")

        assert row["right_observation_date"] == (right_date or "")

        left = (
            observations.get(
                (
                    curve,
                    left_date,
                    tenor,
                )
            )
            if left_date is not None
            else None
        )

        right = (
            observations.get(
                (
                    curve,
                    right_date,
                    tenor,
                )
            )
            if right_date is not None
            else None
        )

        if left is not None:
            assert Decimal(row["left_yield_pct"]) == Decimal(str(left["yield_pct"]))
            assert row["left_source_file"] == left["source_file"]
            assert int(row["left_ingestion_run_id"]) == (left["ingestion_run_id"])
        else:
            assert row["left_yield_pct"] == ""
            assert row["left_source_file"] == ""

        if right is not None:
            assert Decimal(row["right_yield_pct"]) == Decimal(str(right["yield_pct"]))
            assert row["right_source_file"] == right["source_file"]
            assert int(row["right_ingestion_run_id"]) == (right["ingestion_run_id"])
        else:
            assert row["right_yield_pct"] == ""
            assert row["right_source_file"] == ""

        if row["eligibility_status"] == "ELIGIBLE":
            assert left is not None
            assert right is not None

            expected_change = (
                Decimal(str(right["yield_pct"])) - Decimal(str(left["yield_pct"]))
            ) * Decimal("100")

            assert Decimal(row["window_change_bps"]) == (expected_change)

        else:
            assert row["window_change_bps"] == ""


def test_missing_endpoints_remain_explicit_without_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing history/tenors must never trigger interpolation or shifting."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "missingness.csv",
    )

    _, rows = read_generated(output_path)

    assert not any(
        row["curve_type"] == "PKISRV" and row["tenor"] in {"5Y", "10Y"} for row in rows
    )

    ineligible = [row for row in rows if row["eligibility_status"] == "INELIGIBLE"]

    assert len(ineligible) == 248

    assert (
        Counter(row["ineligibility_reason"] for row in ineligible) == EXPECTED_REASONS
    )

    missing_tenor_rows = [
        row
        for row in ineligible
        if row["ineligibility_reason"].startswith("MISSING_TENOR_")
    ]

    assert len(missing_tenor_rows) == 14

    for row in missing_tenor_rows:
        assert row["curve_type"] == "PKRV"
        assert row["tenor"] in {"3M", "6M"}
        assert row["event_date"] in {
            "2023-06-12",
            "2023-06-26",
            "2023-07-31",
        }

        assert row["window_change_bps"] == ""


def test_2024_06_10_uses_general_position_rule(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The no-same-day PKRV event must require no special-case override."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "june_2024.csv",
    )

    _, rows = read_generated(output_path)

    target = [
        row
        for row in rows
        if (row["event_date"] == "2024-06-10" and row["curve_type"] == "PKRV")
    ]

    assert len(target) == 15

    expected_dates = {
        "1": (
            "2024-06-07",
            "2024-06-11",
        ),
        "3": (
            "2024-06-05",
            "2024-06-13",
        ),
        "5": (
            "2024-05-31",
            "2024-06-20",
        ),
    }

    for row in target:
        assert row["event_same_day_curve_observation"] == "0"

        assert (
            row["left_observation_date"],
            row["right_observation_date"],
        ) == expected_dates[row["half_window"]]

        assert row["eligibility_status"] == "ELIGIBLE"


def test_event_window_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated generation must produce byte-identical artifacts."""

    first = run_builder(
        tmp_path,
        monkeypatch,
        "first.csv",
    )

    first_bytes = first.read_bytes()

    second = run_builder(
        tmp_path,
        monkeypatch,
        "second.csv",
    )

    second_bytes = second.read_bytes()

    assert first_bytes == second_bytes

    assert hashlib.sha256(first_bytes).hexdigest() == (EXPECTED_SHA256)

    assert hashlib.sha256(second_bytes).hexdigest() == (EXPECTED_SHA256)
