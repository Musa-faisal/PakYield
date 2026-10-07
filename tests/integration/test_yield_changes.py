"""Integration tests for previous-available-observation yield changes."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
    PKRV_CANONICAL_TENORS,
    PKRV_PKISRV_COMMON_TENORS,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_yield_changes.py"

EXPECTED_SHA256 = "96dcc5c05b09221c18d030929a1be5f7a879cae57a0390448fed4a9f19160090"

EXPECTED_HEADERS = [
    "observation_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "yield_pct",
    "previous_observation_date",
    "previous_yield_pct",
    "observation_gap_days",
    "yield_change_bps",
    "change_method",
    "source_organization",
    "source_file",
    "ingestion_run_id",
]

PARTIAL_MONTHLY = {
    "1M",
    "2M",
    "3M",
    "4M",
    "6M",
    "9M",
}

EXPECTED_SERIES_COUNTS = {
    **{
        (
            "PKRV",
            tenor,
        ): (1119 if tenor in PARTIAL_MONTHLY else 1149)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 403
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_MAX_GAPS = {
    **{
        (
            "PKRV",
            tenor,
        ): (54 if tenor in PARTIAL_MONTHLY else 7)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 6
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_TOP_15 = [
    (
        "PKISRV",
        "1M",
        "2026-07-10",
        "2026-07-13",
        Decimal("19.88"),
        Decimal("11.65"),
        Decimal("-823"),
        3,
    ),
    (
        "PKISRV",
        "1Y",
        "2025-02-03",
        "2025-02-04",
        Decimal("18.86"),
        Decimal("10.97"),
        Decimal("-789"),
        1,
    ),
    (
        "PKRV",
        "1W",
        "2023-04-12",
        "2023-04-13",
        Decimal("21.27"),
        Decimal("29"),
        Decimal("773"),
        1,
    ),
    (
        "PKISRV",
        "6M",
        "2025-02-03",
        "2025-02-04",
        Decimal("17.71"),
        Decimal("10.21"),
        Decimal("-750"),
        1,
    ),
    (
        "PKRV",
        "1W",
        "2023-04-13",
        "2023-04-14",
        Decimal("29"),
        Decimal("21.83"),
        Decimal("-717"),
        1,
    ),
    (
        "PKISRV",
        "1Y",
        "2025-08-15",
        "2025-08-18",
        Decimal("10.29"),
        Decimal("15.16"),
        Decimal("487"),
        3,
    ),
    (
        "PKISRV",
        "1Y",
        "2025-08-18",
        "2025-08-19",
        Decimal("15.16"),
        Decimal("10.43"),
        Decimal("-473"),
        1,
    ),
    (
        "PKISRV",
        "1M",
        "2025-12-31",
        "2026-01-02",
        Decimal("9.4"),
        Decimal("7.1"),
        Decimal("-230"),
        2,
    ),
    (
        "PKISRV",
        "9M",
        "2025-02-03",
        "2025-02-04",
        Decimal("13.5"),
        Decimal("11.28"),
        Decimal("-222"),
        1,
    ),
    (
        "PKISRV",
        "1M",
        "2025-07-28",
        "2025-07-29",
        Decimal("7.81"),
        Decimal("10.02"),
        Decimal("221"),
        1,
    ),
    (
        "PKRV",
        "1W",
        "2022-04-07",
        "2022-04-08",
        Decimal("10.15"),
        Decimal("12.34"),
        Decimal("219"),
        1,
    ),
    (
        "PKISRV",
        "6M",
        "2025-07-11",
        "2025-07-14",
        Decimal("12.01"),
        Decimal("9.99"),
        Decimal("-202"),
        3,
    ),
    (
        "PKISRV",
        "1M",
        "2025-07-25",
        "2025-07-28",
        Decimal("9.82"),
        Decimal("7.81"),
        Decimal("-201"),
        3,
    ),
    (
        "PKRV",
        "1W",
        "2024-09-12",
        "2024-09-13",
        Decimal("19.45"),
        Decimal("17.53"),
        Decimal("-192"),
        1,
    ),
    (
        "PKISRV",
        "1M",
        "2026-07-08",
        "2026-07-09",
        Decimal("16.56"),
        Decimal("18.45"),
        Decimal("189"),
        1,
    ),
]


def load_builder_module() -> ModuleType:
    """Load the yield-change builder."""

    spec = importlib.util.spec_from_file_location(
        "build_yield_changes",
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
    """Read one generated yield-change artifact."""

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


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Generate the artifact into an isolated location."""

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


def database_rows() -> list[object]:
    """Return frozen normalized yield observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        return connection.execute(
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
            ORDER BY
                curve_type,
                tenor_years,
                tenor,
                observation_date
            """
        ).fetchall()

    finally:
        connection.close()


def test_yield_change_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generated artifact must preserve the complete normalized yield universe."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "yield_changes.csv",
    )

    (
        headers,
        rows,
    ) = read_generated(output_path)

    assert headers == EXPECTED_HEADERS

    assert len(rows) == 24815

    keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        )
        for row in rows
    }

    assert len(keys) == 24815

    assert dict(Counter(row["curve_type"] for row in rows)) == {
        "PKRV": 22800,
        "PKISRV": 2015,
    }

    assert (
        dict(
            Counter(
                (
                    row["curve_type"],
                    row["tenor"],
                )
                for row in rows
            )
        )
        == EXPECTED_SERIES_COUNTS
    )

    first_rows = [row for row in rows if not row["previous_observation_date"]]

    changed_rows = [row for row in rows if row["previous_observation_date"]]

    assert len(first_rows) == 25

    assert len(changed_rows) == 24790

    assert {row["change_method"] for row in rows} == {
        "PREVIOUS_AVAILABLE_OBSERVATION",
    }

    assert {row["source_organization"] for row in rows} == {
        "Mutual Funds Association of Pakistan",
    }

    assert {
        int(row["ingestion_run_id"]) for row in rows if row["curve_type"] == "PKRV"
    } == {
        11,
    }

    assert {
        int(row["ingestion_run_id"]) for row in rows if row["curve_type"] == "PKISRV"
    } == {
        13,
    }

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_every_change_uses_actual_previous_database_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every predecessor must be the previous available row in its own series."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "predecessors.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    derived_by_key = {
        (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        ): row
        for row in rows
    }

    grouped = defaultdict(list)

    for row in database_rows():
        grouped[
            (
                row["curve_type"],
                row["tenor"],
            )
        ].append(row)

    assert len(grouped) == 25

    for (
        _series_key,
        source_rows,
    ) in grouped.items():
        source_rows = sorted(
            source_rows,
            key=lambda row: row["observation_date"],
        )

        previous = None

        for source in source_rows:
            key = (
                source["observation_date"],
                source["curve_type"],
                source["tenor"],
            )

            derived = derived_by_key[key]

            assert math.isclose(
                float(derived["tenor_years"]),
                TENOR_TO_YEARS[source["tenor"]],
                rel_tol=0.0,
                abs_tol=1e-10,
            )

            assert Decimal(derived["yield_pct"]) == Decimal(str(source["yield_pct"]))

            assert derived["source_file"] == source["source_file"]

            if previous is None:
                assert derived["previous_observation_date"] == ""

                assert derived["previous_yield_pct"] == ""

                assert derived["observation_gap_days"] == ""

                assert derived["yield_change_bps"] == ""

            else:
                current_yield = Decimal(str(source["yield_pct"]))

                previous_yield = Decimal(str(previous["yield_pct"]))

                gap_days = (
                    date.fromisoformat(source["observation_date"])
                    - date.fromisoformat(previous["observation_date"])
                ).days

                assert (
                    derived["previous_observation_date"] == previous["observation_date"]
                )

                assert Decimal(derived["previous_yield_pct"]) == previous_yield

                assert int(derived["observation_gap_days"]) == gap_days

                assert Decimal(derived["yield_change_bps"]) == (
                    current_yield - previous_yield
                ) * Decimal("100")

            previous = source


def test_gap_census_and_zero_changes_remain_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing market dates must remain gaps rather than synthetic daily rows."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "gaps.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    gap_maxima = {}

    zero_changes = 0

    for row in rows:
        if not row["observation_gap_days"]:
            continue

        key = (
            row["curve_type"],
            row["tenor"],
        )

        gap = int(row["observation_gap_days"])

        previous = gap_maxima.get(key)

        if previous is None or gap > previous:
            gap_maxima[key] = gap

        if Decimal(row["yield_change_bps"]) == Decimal("0"):
            zero_changes += 1

    assert gap_maxima == EXPECTED_MAX_GAPS

    assert zero_changes == 5548


def test_verified_extreme_change_ordering_is_locked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The audited top-15 raw-source extremes must remain unchanged."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "extremes.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    changed = [row for row in rows if row["yield_change_bps"]]

    top = sorted(
        changed,
        key=lambda row: abs(Decimal(row["yield_change_bps"])),
        reverse=True,
    )[:15]

    actual = [
        (
            row["curve_type"],
            row["tenor"],
            row["previous_observation_date"],
            row["observation_date"],
            Decimal(row["previous_yield_pct"]),
            Decimal(row["yield_pct"]),
            Decimal(row["yield_change_bps"]),
            int(row["observation_gap_days"]),
        )
        for row in top
    ]

    assert actual == EXPECTED_TOP_15


def test_yield_change_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated full-corpus generation must produce identical bytes."""

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
