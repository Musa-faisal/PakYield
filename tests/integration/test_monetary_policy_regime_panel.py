"""Integration tests for deterministic monetary-policy regime panel."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import DATABASE_PATH
from pakyield.database.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_monetary_policy_regime_panel.py"

EXPECTED_SHA256 = "d53f6301048f2261551d467e322fe820970a0db7eea145fe0221a45142d9ff4b"

EXPECTED_HEADERS = [
    "observation_date",
    "curve_type",
    "regime_label",
    "regime_analysis_status",
    "ineligibility_reason",
    "is_mpc_event_date",
    "same_day_mpc_event_type",
    "latest_prior_mpc_event_date",
    "latest_prior_mpc_event_type",
    "regime_origin_event_date",
    "regime_origin_event_type",
    "days_since_latest_prior_mpc_event",
    "days_since_regime_origin_event",
    "classification_method",
]

EXPECTED_REGIMES = {
    "UNCLASSIFIED": 66,
    "TIGHTENING": 724,
    "EASING": 762,
}

EXPECTED_STATUSES = {
    "INELIGIBLE": 114,
    "ELIGIBLE": 1438,
}

EXPECTED_REASONS = {
    "PRE_DIRECTIONAL_HISTORY": 63,
    "MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP": 51,
}

EXPECTED_ELIGIBLE_BY_CURVE_REGIME = {
    ("PKISRV", "EASING"): 290,
    ("PKISRV", "TIGHTENING"): 100,
    ("PKRV", "EASING"): 447,
    ("PKRV", "TIGHTENING"): 601,
}

EXPECTED_SAME_DAY_EVENT_TYPES = {
    "HOLD": 32,
    "HIKE": 10,
    "CUT": 9,
}

EXPECTED_LATEST_PRIOR_TYPES_ELIGIBLE = {
    "HIKE": 286,
    "HOLD": 848,
    "CUT": 304,
}

EXPECTED_HOLD_INHERITED_REGIMES = {
    "TIGHTENING": 415,
    "EASING": 433,
}

EXPECTED_HOLD_ORIGINS = {
    "HIKE": 415,
    "CUT": 433,
}


def load_builder_module() -> ModuleType:
    """Load the production regime builder."""

    spec = importlib.util.spec_from_file_location(
        "build_monetary_policy_regime_panel",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Generate one isolated regime artifact."""

    output_path = tmp_path / file_name

    monkeypatch.setattr(
        BUILDER,
        "OUTPUT_PATH",
        output_path,
    )

    BUILDER.main()

    assert output_path.is_file()

    return output_path


def read_artifact(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one generated regime CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def load_mpc_events() -> list[dict[str, object]]:
    """Load validated production MPC event chronology."""

    connection = get_connection(DATABASE_PATH)

    try:
        rows = connection.execute(
            """
            SELECT
                event_date,
                decision_type
            FROM mpc_events
            ORDER BY event_date
            """
        ).fetchall()

    finally:
        connection.close()

    assert len(rows) == 39

    return [
        {
            "event_date": date.fromisoformat(row["event_date"]),
            "event_date_text": row["event_date"],
            "event_type": row["decision_type"],
        }
        for row in rows
    ]


def test_regime_panel_full_frozen_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Frozen shape, census, and bytes remain exact."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "regimes.csv",
    )

    headers, rows = read_artifact(output_path)

    assert headers == EXPECTED_HEADERS

    assert len(rows) == 1552

    keys = {
        (
            row["curve_type"],
            row["observation_date"],
        )
        for row in rows
    }

    assert len(keys) == 1552

    dates = {row["observation_date"] for row in rows}

    assert len(dates) == 1151
    assert min(dates) == "2022-01-04"
    assert max(dates) == "2026-09-30"

    assert Counter(row["curve_type"] for row in rows) == {
        "PKRV": 1149,
        "PKISRV": 403,
    }

    assert Counter(row["regime_label"] for row in rows) == EXPECTED_REGIMES

    assert Counter(row["regime_analysis_status"] for row in rows) == EXPECTED_STATUSES

    assert (
        Counter(
            row["ineligibility_reason"]
            for row in rows
            if row["regime_analysis_status"] == "INELIGIBLE"
        )
        == EXPECTED_REASONS
    )

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_strict_before_rule_reconciles_to_mpc_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every row must use only MPC events strictly before its date."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "strict_before.csv",
    )

    _, rows = read_artifact(output_path)

    events = load_mpc_events()

    event_dates = [event["event_date"] for event in events]

    event_by_date = {event["event_date"]: event for event in events}

    directional_events = [
        event
        for event in events
        if event["event_type"]
        in {
            "HIKE",
            "CUT",
        }
    ]

    directional_dates = [event["event_date"] for event in directional_events]

    for row in rows:
        observation_date = date.fromisoformat(row["observation_date"])

        prior_index = (
            bisect_left(
                event_dates,
                observation_date,
            )
            - 1
        )

        directional_index = (
            bisect_left(
                directional_dates,
                observation_date,
            )
            - 1
        )

        latest_prior = events[prior_index] if prior_index >= 0 else None

        origin = (
            directional_events[directional_index] if directional_index >= 0 else None
        )

        same_day = event_by_date.get(observation_date)

        if latest_prior is None:
            assert row["latest_prior_mpc_event_date"] == ""

            assert row["latest_prior_mpc_event_type"] == ""

        else:
            assert row["latest_prior_mpc_event_date"] == latest_prior["event_date_text"]

            assert row["latest_prior_mpc_event_type"] == latest_prior["event_type"]

        if origin is None:
            assert row["regime_origin_event_date"] == ""

            assert row["regime_origin_event_type"] == ""

            assert row["regime_label"] == "UNCLASSIFIED"

        else:
            assert row["regime_origin_event_date"] == origin["event_date_text"]

            assert row["regime_origin_event_type"] == origin["event_type"]

            expected_regime = (
                "TIGHTENING" if origin["event_type"] == "HIKE" else "EASING"
            )

            assert row["regime_label"] == expected_regime

        if same_day is not None:
            assert row["is_mpc_event_date"] == "1"

            assert row["same_day_mpc_event_type"] == same_day["event_type"]

            assert row["regime_analysis_status"] == "INELIGIBLE"

            assert row["ineligibility_reason"] == (
                "MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP"
            )

        else:
            assert row["is_mpc_event_date"] == "0"


def test_hold_inheritance_and_frozen_regime_census(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HOLD meetings inherit the last HIKE/CUT direction."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "hold_inheritance.csv",
    )

    _, rows = read_artifact(output_path)

    eligible = [row for row in rows if row["regime_analysis_status"] == "ELIGIBLE"]

    assert (
        Counter(
            (
                row["curve_type"],
                row["regime_label"],
            )
            for row in eligible
        )
        == EXPECTED_ELIGIBLE_BY_CURVE_REGIME
    )

    assert (
        Counter(row["latest_prior_mpc_event_type"] for row in eligible)
        == EXPECTED_LATEST_PRIOR_TYPES_ELIGIBLE
    )

    after_hold = [
        row for row in eligible if row["latest_prior_mpc_event_type"] == "HOLD"
    ]

    assert len(after_hold) == 848

    assert (
        Counter(row["regime_label"] for row in after_hold)
        == EXPECTED_HOLD_INHERITED_REGIMES
    )

    assert (
        Counter(row["regime_origin_event_type"] for row in after_hold)
        == EXPECTED_HOLD_ORIGINS
    )

    assert not any(row["regime_label"] == "HOLD" for row in rows)


def test_same_date_cross_curve_metadata_and_event_census(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Identical dates across curves must share regime metadata."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "cross_curve.csv",
    )

    _, rows = read_artifact(output_path)

    event_rows = [row for row in rows if row["is_mpc_event_date"] == "1"]

    assert len(event_rows) == 51

    assert (
        Counter(row["same_day_mpc_event_type"] for row in event_rows)
        == EXPECTED_SAME_DAY_EVENT_TYPES
    )

    metadata_fields = (
        "regime_label",
        "regime_analysis_status",
        "ineligibility_reason",
        "is_mpc_event_date",
        "same_day_mpc_event_type",
        "latest_prior_mpc_event_date",
        "latest_prior_mpc_event_type",
        "regime_origin_event_date",
        "regime_origin_event_type",
        "days_since_latest_prior_mpc_event",
        "days_since_regime_origin_event",
        "classification_method",
    )

    by_date = defaultdict(set)

    for row in rows:
        by_date[row["observation_date"]].add(
            tuple(row[field] for field in metadata_fields)
        )

    assert all(len(values) == 1 for values in by_date.values())


def test_regime_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated construction must remain byte-identical."""

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

    assert hashlib.sha256(first_bytes).hexdigest() == EXPECTED_SHA256

    assert hashlib.sha256(second_bytes).hexdigest() == EXPECTED_SHA256
