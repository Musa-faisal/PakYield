"""Integration tests for deterministic monthly CPI/yield alignment."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_monthly_cpi_yield_panel.py"

EXPECTED_SHA256 = "978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"

EXPECTED_HEADERS = [
    "period",
    "curve_type",
    "tenor",
    "tenor_years",
    "observation_count",
    "first_observation_date",
    "month_end_observation_date",
    "calendar_month_end_date",
    "month_end_lag_days",
    "month_end_yield_pct",
    "previous_available_period",
    "previous_month_end_observation_date",
    "previous_month_end_yield_pct",
    "period_gap_months",
    "monthly_yield_change_bps",
    "month_end_method",
    "monthly_change_method",
    "national_cpi_index",
    "cpi_inflation_yoy_pct",
    "cpi_base_year",
    "yield_source_organization",
    "yield_source_file",
    "yield_ingestion_run_id",
    "cpi_source_organization",
    "cpi_source_file",
    "cpi_ingestion_run_id",
]

PARTIAL_TENORS = {
    "1M",
    "2M",
    "3M",
    "4M",
    "6M",
    "9M",
}


def load_builder_module() -> ModuleType:
    """Load the monthly-panel builder."""

    spec = importlib.util.spec_from_file_location(
        "build_monthly_cpi_yield_panel",
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
    """Generate one isolated monthly panel."""

    output_path = tmp_path / file_name

    monkeypatch.setattr(
        BUILDER,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        BUILDER,
        "OUTPUT_PATH",
        output_path,
    )

    BUILDER.main()

    assert output_path.is_file()

    return output_path


def read_panel(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one generated panel."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        headers = list(reader.fieldnames or [])

        rows = list(reader)

    return (
        headers,
        rows,
    )


def database_inputs() -> tuple[
    list[object],
    dict[str, object],
]:
    """Load normalized yield and CPI inputs."""

    connection = get_connection(DATABASE_PATH)

    try:
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
            WHERE observation_date >= '2022-01-01'
            ORDER BY
                curve_type,
                tenor_years,
                tenor,
                observation_date
            """
        ).fetchall()

        cpi_rows = connection.execute(
            """
            SELECT
                period,
                national_cpi_index,
                cpi_inflation_yoy_pct,
                base_year,
                source_organization,
                source_file,
                ingestion_run_id
            FROM cpi_observations
            WHERE period >= '2022-01'
            ORDER BY period
            """
        ).fetchall()

    finally:
        connection.close()

    return (
        yields,
        {row["period"]: row for row in cpi_rows},
    )


def test_monthly_panel_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monthly panel must preserve its frozen structural contract."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "monthly.csv",
    )

    headers, rows = read_panel(output_path)

    assert headers == EXPECTED_HEADERS

    assert len(rows) == 1234

    assert dict(Counter(row["curve_type"] for row in rows)) == {
        "PKRV": 1134,
        "PKISRV": 100,
    }

    assert len({row["period"] for row in rows}) == 57

    assert min(row["period"] for row in rows) == "2022-01"

    assert max(row["period"] for row in rows) == "2026-09"

    assert (
        len(
            {
                (
                    row["curve_type"],
                    row["tenor"],
                )
                for row in rows
            }
        )
        == 25
    )

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_every_month_end_and_cpi_value_reconciles_to_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every monthly row must equal its normalized yield and CPI inputs."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "reconciliation.csv",
    )

    _, rows = read_panel(output_path)

    yields, cpi_by_period = database_inputs()

    monthly = defaultdict(list)

    for source in yields:
        monthly[
            (
                source["curve_type"],
                source["tenor"],
                source["observation_date"][:7],
            )
        ].append(source)

    assert len(monthly) == 1234

    for row in rows:
        key = (
            row["curve_type"],
            row["tenor"],
            row["period"],
        )

        source_rows = sorted(
            monthly[key],
            key=lambda source: source["observation_date"],
        )

        assert int(row["observation_count"]) == len(source_rows)

        assert row["first_observation_date"] == source_rows[0]["observation_date"]

        month_end_source = source_rows[-1]

        assert row["month_end_observation_date"] == month_end_source["observation_date"]

        assert Decimal(row["month_end_yield_pct"]) == Decimal(
            str(month_end_source["yield_pct"])
        )

        assert row["yield_source_file"] == month_end_source["source_file"]

        expected_run = 11 if row["curve_type"] == "PKRV" else 13

        assert int(row["yield_ingestion_run_id"]) == expected_run

        assert math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[row["tenor"]],
            rel_tol=0.0,
            abs_tol=1e-10,
        )

        cpi = cpi_by_period[row["period"]]

        assert Decimal(row["national_cpi_index"]) == Decimal(
            str(cpi["national_cpi_index"])
        )

        assert Decimal(row["cpi_inflation_yoy_pct"]) == Decimal(
            str(cpi["cpi_inflation_yoy_pct"])
        )

        assert row["cpi_source_file"] == cpi["source_file"]

        assert int(row["cpi_ingestion_run_id"]) == 1


def test_monthly_predecessor_and_change_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changes must exist only across consecutive observed calendar months."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "changes.csv",
    )

    _, rows = read_panel(output_path)

    by_series = defaultdict(list)

    for row in rows:
        by_series[
            (
                row["curve_type"],
                row["tenor"],
            )
        ].append(row)

    assert len(by_series) == 25

    first_count = 0
    previous_count = 0
    change_count = 0

    change_by_curve = Counter()

    for series_rows in by_series.values():
        series_rows.sort(key=lambda row: row["period"])

        for index, row in enumerate(series_rows):
            if index == 0:
                first_count += 1

                assert row["previous_available_period"] == ""

                assert row["period_gap_months"] == ""

                assert row["monthly_yield_change_bps"] == ""

                continue

            previous_count += 1

            previous = series_rows[index - 1]

            assert row["previous_available_period"] == previous["period"]

            assert (
                row["previous_month_end_observation_date"]
                == previous["month_end_observation_date"]
            )

            assert Decimal(row["previous_month_end_yield_pct"]) == Decimal(
                previous["month_end_yield_pct"]
            )

            previous_year = int(previous["period"][:4])

            previous_month = int(previous["period"][5:7])

            current_year = int(row["period"][:4])

            current_month = int(row["period"][5:7])

            gap = (
                current_year * 12
                + current_month
                - (previous_year * 12 + previous_month)
            )

            assert int(row["period_gap_months"]) == gap

            if gap == 1:
                change_count += 1

                change_by_curve[row["curve_type"]] += 1

                expected = (
                    Decimal(row["month_end_yield_pct"])
                    - Decimal(row["previous_month_end_yield_pct"])
                ) * Decimal("100")

                assert Decimal(row["monthly_yield_change_bps"]) == expected

            else:
                assert gap == 2

                assert row["curve_type"] == "PKRV"

                assert row["tenor"] in PARTIAL_TENORS

                assert previous["period"] == "2023-06"

                assert row["period"] == "2023-08"

                assert row["monthly_yield_change_bps"] == ""

    assert first_count == 25
    assert previous_count == 1209
    assert change_count == 1203

    assert dict(change_by_curve) == {
        "PKRV": 1108,
        "PKISRV": 95,
    }


def test_missing_july_and_month_end_staleness_remain_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Known June/July 2023 partial-tenor limitations must not be hidden."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "missingness.csv",
    )

    _, rows = read_panel(output_path)

    keys = {
        (
            row["period"],
            row["curve_type"],
            row["tenor"],
        )
        for row in rows
    }

    for tenor in PARTIAL_TENORS:
        assert (
            "2023-07",
            "PKRV",
            tenor,
        ) not in keys

    gap_rows = [
        row
        for row in rows
        if (row["previous_available_period"] and row["period_gap_months"] != "1")
    ]

    assert len(gap_rows) == 6

    assert {row["tenor"] for row in gap_rows} == PARTIAL_TENORS

    for row in gap_rows:
        assert row["period"] == "2023-08"

        assert row["previous_available_period"] == "2023-06"

        assert row["period_gap_months"] == "2"

        assert row["monthly_yield_change_bps"] == ""

    stale_rows = [row for row in rows if (int(row["month_end_lag_days"]) > 3)]

    assert len(stale_rows) == 6

    assert {row["tenor"] for row in stale_rows} == PARTIAL_TENORS

    for row in stale_rows:
        assert row["period"] == "2023-06"

        assert row["month_end_observation_date"] == "2023-06-15"

        assert row["calendar_month_end_date"] == "2023-06-30"

        assert row["month_end_lag_days"] == "15"


def test_monthly_panel_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated monthly generation must produce identical bytes."""

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
