"""Integration tests for deterministic sovereign term-spread panel."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
    TENOR_TO_YEARS,
    TERM_SPREADS,
)
from pakyield.database.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_term_spread_panel.py"

EXPECTED_SHA256 = "5123ff3d4abe4a667d0854f3e9a8a8f9bf208368b8227bd3d31da2f011adb0ed"

EXPECTED_HEADERS = [
    "observation_date",
    "curve_type",
    "spread_name",
    "long_tenor",
    "short_tenor",
    "long_tenor_years",
    "short_tenor_years",
    "long_yield_pct",
    "short_yield_pct",
    "term_spread_bps",
    "eligibility_status",
    "ineligibility_reason",
    "construction_method",
    "long_source_organization",
    "long_source_file",
    "long_ingestion_run_id",
    "short_source_organization",
    "short_source_file",
    "short_ingestion_run_id",
]

EXPECTED_SPREADS = {
    "10Y-2Y": ("10Y", "2Y"),
    "10Y-1Y": ("10Y", "1Y"),
    "5Y-1Y": ("5Y", "1Y"),
    "3Y-3M": ("3Y", "3M"),
}

EXPECTED_ELIGIBLE_BY_SPREAD = {
    "10Y-2Y": 1149,
    "10Y-1Y": 1149,
    "5Y-1Y": 1149,
    "3Y-3M": 1119,
}

EXPECTED_MISSING_SHORT_DATES = {
    "2023-06-16",
    "2023-06-19",
    "2023-06-20",
    "2023-06-21",
    "2023-06-22",
    "2023-06-23",
    "2023-06-26",
    "2023-06-27",
    "2023-07-04",
    "2023-07-06",
    "2023-07-07",
    "2023-07-10",
    "2023-07-11",
    "2023-07-12",
    "2023-07-13",
    "2023-07-14",
    "2023-07-17",
    "2023-07-18",
    "2023-07-19",
    "2023-07-20",
    "2023-07-21",
    "2023-07-25",
    "2023-07-26",
    "2023-07-27",
    "2023-07-31",
    "2023-08-01",
    "2023-08-02",
    "2023-08-03",
    "2023-08-04",
    "2023-08-07",
}

EXPECTED_SIGNS = {
    "10Y-2Y": {
        "POSITIVE": 473,
        "NEGATIVE": 676,
    },
    "10Y-1Y": {
        "POSITIVE": 483,
        "NEGATIVE": 664,
        "ZERO": 2,
    },
    "5Y-1Y": {
        "POSITIVE": 450,
        "NEGATIVE": 698,
        "ZERO": 1,
    },
    "3Y-3M": {
        "POSITIVE": 451,
        "NEGATIVE": 665,
        "ZERO": 3,
    },
}

EXPECTED_EXTREMA = {
    "10Y-2Y": {
        "min": (
            "2023-09-14",
            Decimal("-583"),
        ),
        "max": (
            "2025-07-16",
            Decimal("136"),
        ),
    },
    "10Y-1Y": {
        "min": (
            "2023-09-07",
            Decimal("-812"),
        ),
        "max": (
            "2025-06-26",
            Decimal("150"),
        ),
    },
    "5Y-1Y": {
        "min": (
            "2023-06-06",
            Decimal("-710"),
        ),
        "max": (
            "2026-04-07",
            Decimal("97"),
        ),
    },
    "3Y-3M": {
        "min": (
            "2023-12-06",
            Decimal("-535"),
        ),
        "max": (
            "2026-04-06",
            Decimal("158"),
        ),
    },
}


def load_builder_module() -> ModuleType:
    """Load the production term-spread builder."""

    spec = importlib.util.spec_from_file_location(
        "build_term_spread_panel",
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
    """Generate one isolated term-spread artifact."""

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
    """Read one generated term-spread CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def load_pkrv_database_rows() -> dict[
    tuple[str, str],
    object,
]:
    """Load exact normalized PKRV observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        rows = connection.execute(
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
            WHERE curve_type = 'PKRV'
            ORDER BY
                observation_date,
                tenor_years,
                tenor
            """
        ).fetchall()

    finally:
        connection.close()

    assert len(rows) == 22800

    return {
        (
            row["observation_date"],
            row["tenor"],
        ): row
        for row in rows
    }


def test_term_spread_panel_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D091 shape, census, and frozen bytes remain stable."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "term_spreads.csv",
    )

    headers, rows = read_artifact(output_path)

    assert TERM_SPREADS == EXPECTED_SPREADS
    assert headers == EXPECTED_HEADERS

    assert len(rows) == 4596

    keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["spread_name"],
        )
        for row in rows
    }

    assert len(keys) == 4596

    dates = {row["observation_date"] for row in rows}

    assert len(dates) == 1149
    assert min(dates) == "2022-01-04"
    assert max(dates) == "2026-09-28"

    assert Counter(row["curve_type"] for row in rows) == {
        "PKRV": 4596,
    }

    assert Counter(row["spread_name"] for row in rows) == {
        "10Y-2Y": 1149,
        "10Y-1Y": 1149,
        "5Y-1Y": 1149,
        "3Y-3M": 1149,
    }

    assert Counter(row["eligibility_status"] for row in rows) == {
        "ELIGIBLE": 4566,
        "INELIGIBLE": 30,
    }

    assert (
        Counter(
            row["spread_name"]
            for row in rows
            if row["eligibility_status"] == "ELIGIBLE"
        )
        == EXPECTED_ELIGIBLE_BY_SPREAD
    )

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_every_eligible_spread_reconciles_to_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eligible rows exactly reconcile to normalized PKRV."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "reconcile.csv",
    )

    _, rows = read_artifact(output_path)

    observations = load_pkrv_database_rows()

    for row in rows:
        assert row["curve_type"] == "PKRV"

        long_tenor = row["long_tenor"]

        short_tenor = row["short_tenor"]

        assert Decimal(row["long_tenor_years"]) == Decimal(
            str(TENOR_TO_YEARS[long_tenor])
        )

        assert Decimal(row["short_tenor_years"]) == Decimal(
            str(TENOR_TO_YEARS[short_tenor])
        )

        date = row["observation_date"]

        long_db = observations.get(
            (
                date,
                long_tenor,
            )
        )

        short_db = observations.get(
            (
                date,
                short_tenor,
            )
        )

        if row["eligibility_status"] != "ELIGIBLE":
            continue

        assert long_db is not None
        assert short_db is not None

        assert Decimal(row["long_yield_pct"]) == Decimal(str(long_db["yield_pct"]))

        assert Decimal(row["short_yield_pct"]) == Decimal(str(short_db["yield_pct"]))

        expected_spread = (
            Decimal(str(long_db["yield_pct"])) - Decimal(str(short_db["yield_pct"]))
        ) * Decimal("100")

        assert Decimal(row["term_spread_bps"]) == expected_spread

        assert row["long_source_file"] == long_db["source_file"]

        assert row["short_source_file"] == short_db["source_file"]

        assert int(row["long_ingestion_run_id"]) == int(long_db["ingestion_run_id"])

        assert int(row["short_ingestion_run_id"]) == int(short_db["ingestion_run_id"])


def test_missing_short_leg_remains_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The 30 absent 3M legs remain explicit missing cells."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "missingness.csv",
    )

    _, rows = read_artifact(output_path)

    missing = [row for row in rows if row["eligibility_status"] == "INELIGIBLE"]

    assert len(missing) == 30

    assert Counter(row["ineligibility_reason"] for row in missing) == {
        "MISSING_SHORT_LEG": 30,
    }

    assert {row["observation_date"] for row in missing} == EXPECTED_MISSING_SHORT_DATES

    for row in missing:
        assert row["spread_name"] == "3Y-3M"

        assert row["long_tenor"] == "3Y"

        assert row["short_tenor"] == "3M"

        assert row["long_yield_pct"] != ""

        assert row["short_yield_pct"] == ""

        assert row["term_spread_bps"] == ""

        assert row["long_source_file"] != ""

        assert row["short_source_file"] == ""

    assert not any(row["curve_type"] == "PKISRV" for row in rows)


def test_signs_and_extrema_match_frozen_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5C2A numerical evidence remains exactly stable."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "evidence.csv",
    )

    _, rows = read_artifact(output_path)

    signs = defaultdict(Counter)

    values = defaultdict(list)

    for row in rows:
        if row["eligibility_status"] != "ELIGIBLE":
            continue

        spread_name = row["spread_name"]

        value = Decimal(row["term_spread_bps"])

        if value > 0:
            signs[spread_name]["POSITIVE"] += 1

        elif value < 0:
            signs[spread_name]["NEGATIVE"] += 1

        else:
            signs[spread_name]["ZERO"] += 1

        values[spread_name].append(
            (
                row["observation_date"],
                value,
            )
        )

    for spread_name in EXPECTED_SIGNS:
        assert dict(signs[spread_name]) == EXPECTED_SIGNS[spread_name]

        minimum = min(
            values[spread_name],
            key=lambda item: item[1],
        )

        maximum = max(
            values[spread_name],
            key=lambda item: item[1],
        )

        assert minimum == (EXPECTED_EXTREMA[spread_name]["min"])

        assert maximum == (EXPECTED_EXTREMA[spread_name]["max"])


def test_term_spread_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated generation must produce identical bytes."""

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
