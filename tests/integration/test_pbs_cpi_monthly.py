"""Integration tests for the validated PBS National CPI corpus."""

from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MANIFEST_DIR = PROJECT_ROOT / "data" / "manifests"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pbs" / "cpi"

MONTHLY_PATH = MANIFEST_DIR / "pbs_cpi_monthly_validated.csv"

DIAGNOSTIC_PATH = MANIFEST_DIR / "pbs_cpi_cross_publication_diagnostic.csv"

PLAN_PATH = MANIFEST_DIR / "pbs_cpi_acquisition_plan.csv"

PROVENANCE_PATH = MANIFEST_DIR / "raw_provenance.csv"


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def monthly_sequence(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> list[str]:
    """Return an inclusive monthly sequence."""

    periods = []

    year = start_year
    month = start_month

    while year < end_year or (year == end_year and month <= end_month):
        periods.append(f"{year:04d}-{month:02d}")

        month += 1

        if month == 13:
            month = 1
            year += 1

    return periods


def test_monthly_corpus_has_exact_core_coverage() -> None:
    """The v1 CPI source corpus must contain all 57 required months."""

    rows = read_csv(MONTHLY_PATH)

    expected = monthly_sequence(
        2022,
        1,
        2026,
        9,
    )

    assert len(rows) == 57

    assert [row["period"] for row in rows] == expected

    assert len({row["period"] for row in rows}) == 57


def test_source_roles_and_precision_are_preserved() -> None:
    """Historical and monthly-review precision must not be homogenized."""

    rows = read_csv(MONTHLY_PATH)

    assert Counter(row["source_role"] for row in rows) == {
        "HISTORICAL_SERIES": 54,
        "MONTHLY_REVIEW": 3,
    }

    assert Counter(row["index_source_precision_dp"] for row in rows) == {
        "1": 54,
        "2": 3,
    }

    assert Counter(row["yoy_source_precision_dp"] for row in rows) == {
        "1": 54,
        "2": 3,
    }

    assert sum(bool(row["cpi_inflation_mom_pct"]) for row in rows) == 3

    assert all(row["validation_status"] == "SOURCE_EXPLICIT" for row in rows)


def test_boundary_observations_are_frozen() -> None:
    """Known source boundary values must remain unchanged."""

    rows = {row["period"]: row for row in read_csv(MONTHLY_PATH)}

    expected = {
        "2022-01": (
            "158.8",
            "13.0",
            "",
        ),
        "2026-06": (
            "293.5",
            "11.1",
            "",
        ),
        "2026-07": (
            "296.97",
            "9.20",
            "1.19",
        ),
        "2026-08": (
            "300.50",
            "11.15",
            "1.19",
        ),
        "2026-09": (
            "304.33",
            "10.26",
            "1.27",
        ),
    }

    for period, values in expected.items():
        row = rows[period]

        assert (
            row["national_cpi_index"],
            row["cpi_inflation_yoy_pct"],
            row["cpi_inflation_mom_pct"],
        ) == values


def test_transition_overlap_chain_is_consistent() -> None:
    """Current-month source values must preserve the validated overlap chain."""

    rows = {row["period"]: row for row in read_csv(MONTHLY_PATH)}

    assert Decimal(rows["2026-06"]["national_cpi_index"]) == Decimal("293.5")

    assert Decimal(rows["2026-07"]["national_cpi_index"]) == Decimal("296.97")

    assert Decimal(rows["2026-08"]["national_cpi_index"]) == Decimal("300.50")

    assert Decimal(rows["2026-09"]["national_cpi_index"]) == Decimal("304.33")


def test_cross_publication_differences_remain_diagnostic_only() -> None:
    """Later prior-year comparison columns must not revise historical rows."""

    diagnostics = read_csv(DIAGNOSTIC_PATH)

    assert len(diagnostics) == 3

    expected = {
        "2026-07": (
            "2025-07",
            "271.9",
            "271.94",
            "0.04",
        ),
        "2026-08": (
            "2025-08",
            "270.2",
            "270.35",
            "0.15",
        ),
        "2026-09": (
            "2025-09",
            "275.6",
            "276.01",
            "0.41",
        ),
    }

    for row in diagnostics:
        assert (
            row["comparison_period"],
            row["historical_index"],
            row["monthly_review_prior_year_index"],
            row["difference_index_points"],
        ) == expected[row["current_period"]]

        assert row["disposition"] == ("DIAGNOSTIC_ONLY_NO_RETROACTIVE_REPLACEMENT")


def test_raw_plan_and_provenance_cover_four_source_artifacts() -> None:
    """The frozen analytical corpus must trace to four acquired PBS PDFs."""

    plan = read_csv(PLAN_PATH)

    provenance = [
        row for row in read_csv(PROVENANCE_PATH) if row["dataset_id"] == "PBS_CPI"
    ]

    raw = list(RAW_DIR.glob("*.pdf"))

    assert len(plan) == 4
    assert len(provenance) == 4
    assert len(raw) == 4

    plan_names = {row["resolved_file_name"] for row in plan}

    provenance_names = {row["raw_file_name"] for row in provenance}

    raw_names = {path.name for path in raw}

    assert plan_names == (provenance_names)

    assert plan_names == (raw_names)


def test_no_partial_files_remain() -> None:
    """Completed acquisition/build steps must leave no temporary parts."""

    assert list(RAW_DIR.glob("*.part")) == []

    assert list(MANIFEST_DIR.glob("*.part")) == []
