"""Integration tests for deterministic same-date PKRV/PKISRV comparison."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
    PKRV_PKISRV_COMMON_TENORS,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_pkrv_pkisrv_comparison.py"

EXPECTED_SHA256 = "9d17eda88a23c6106b3bab51bd56b2f64626488c533af0436e133b334dc32641"

EXPECTED_HEADERS = [
    "observation_date",
    "tenor",
    "tenor_years",
    "match_status",
    "pkrv_yield_pct",
    "pkisrv_yield_pct",
    "pkisrv_minus_pkrv_bps",
    "pkrv_source_organization",
    "pkrv_source_file",
    "pkrv_ingestion_run_id",
    "pkisrv_source_organization",
    "pkisrv_source_file",
    "pkisrv_ingestion_run_id",
]

EXPECTED_TENORS = (
    "1M",
    "3M",
    "6M",
    "9M",
    "1Y",
)

EXPECTED_PKRV_ONLY_DATES = {
    "2025-03-07",
    "2025-08-20",
    "2026-03-18",
    "2026-03-27",
}

EXPECTED_PKISRV_ONLY_DATES = {
    "2026-09-29",
    "2026-09-30",
}

EXPECTED_TOP_15 = [
    (
        "2026-07-10",
        "1M",
        Decimal("11.49"),
        Decimal("19.88"),
        Decimal("839"),
    ),
    (
        "2025-02-03",
        "1Y",
        Decimal("11.46"),
        Decimal("18.86"),
        Decimal("740"),
    ),
    (
        "2026-07-09",
        "1M",
        Decimal("11.44"),
        Decimal("18.45"),
        Decimal("701"),
    ),
    (
        "2025-02-03",
        "6M",
        Decimal("11.63"),
        Decimal("17.71"),
        Decimal("608"),
    ),
    (
        "2026-07-08",
        "1M",
        Decimal("11.53"),
        Decimal("16.56"),
        Decimal("503"),
    ),
    (
        "2025-08-18",
        "1Y",
        Decimal("10.91"),
        Decimal("15.16"),
        Decimal("425"),
    ),
    (
        "2026-07-07",
        "1M",
        Decimal("11.51"),
        Decimal("15.4"),
        Decimal("389"),
    ),
    (
        "2026-03-26",
        "1M",
        Decimal("10.77"),
        Decimal("7.51"),
        Decimal("-326"),
    ),
    (
        "2026-01-02",
        "1M",
        Decimal("10.31"),
        Decimal("7.1"),
        Decimal("-321"),
    ),
    (
        "2026-01-05",
        "1M",
        Decimal("10.3"),
        Decimal("7.1"),
        Decimal("-320"),
    ),
    (
        "2026-07-06",
        "1M",
        Decimal("11.5"),
        Decimal("14.64"),
        Decimal("314"),
    ),
    (
        "2026-03-17",
        "1M",
        Decimal("10.98"),
        Decimal("7.89"),
        Decimal("-309"),
    ),
    (
        "2026-05-14",
        "1M",
        Decimal("11.33"),
        Decimal("8.26"),
        Decimal("-307"),
    ),
    (
        "2026-05-13",
        "1M",
        Decimal("11.41"),
        Decimal("8.37"),
        Decimal("-304"),
    ),
    (
        "2026-03-19",
        "1M",
        Decimal("10.85"),
        Decimal("7.89"),
        Decimal("-296"),
    ),
]


def load_builder_module() -> ModuleType:
    """Load the comparison-panel builder."""

    spec = importlib.util.spec_from_file_location(
        "build_pkrv_pkisrv_comparison",
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
    """Read one generated comparison panel."""

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
    """Generate a panel into an isolated location."""

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


def normalized_rows() -> list[object]:
    """Return the frozen normalized comparison universe."""

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
            WHERE observation_date >= '2025-02-03'
              AND curve_type IN (
                  'PKRV',
                  'PKISRV'
              )
              AND tenor IN (
                  '1M',
                  '3M',
                  '6M',
                  '9M',
                  '1Y'
              )
            ORDER BY
                observation_date,
                tenor_years,
                tenor,
                curve_type
            """
        ).fetchall()

    finally:
        connection.close()


def test_comparison_panel_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Panel must preserve the complete union comparison universe."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "comparison.csv",
    )

    (
        headers,
        rows,
    ) = read_generated(output_path)

    assert headers == EXPECTED_HEADERS

    assert tuple(PKRV_PKISRV_COMMON_TENORS) == EXPECTED_TENORS

    assert len(rows) == 2035

    assert rows[0]["observation_date"] == "2025-02-03"

    assert rows[-1]["observation_date"] == "2026-09-30"

    assert len({row["observation_date"] for row in rows}) == 407

    assert dict(Counter(row["match_status"] for row in rows)) == {
        "MATCHED": 2005,
        "PKRV_ONLY": 20,
        "PKISRV_ONLY": 10,
    }

    assert dict(Counter(row["tenor"] for row in rows)) == {
        tenor: 407 for tenor in EXPECTED_TENORS
    }

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_every_panel_row_reconciles_to_normalized_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every panel row must equal its actual same-date normalized inputs."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "database_reconciliation.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    database = {
        (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        ): row
        for row in normalized_rows()
    }

    assert len(database) == 4040

    for row in rows:
        observation_date = row["observation_date"]

        tenor = row["tenor"]

        assert math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[tenor],
            rel_tol=0.0,
            abs_tol=1e-10,
        )

        pkrv = database.get(
            (
                observation_date,
                "PKRV",
                tenor,
            )
        )

        pkisrv = database.get(
            (
                observation_date,
                "PKISRV",
                tenor,
            )
        )

        if pkrv is not None and pkisrv is not None:
            assert row["match_status"] == "MATCHED"

        elif pkrv is not None:
            assert row["match_status"] == "PKRV_ONLY"

        else:
            assert pkisrv is not None

            assert row["match_status"] == "PKISRV_ONLY"

        if pkrv is not None:
            assert Decimal(row["pkrv_yield_pct"]) == Decimal(str(pkrv["yield_pct"]))

            assert row["pkrv_source_file"] == pkrv["source_file"]

            assert int(row["pkrv_ingestion_run_id"]) == 11

        else:
            assert row["pkrv_yield_pct"] == ""

            assert row["pkrv_source_file"] == ""

            assert row["pkrv_ingestion_run_id"] == ""

        if pkisrv is not None:
            assert Decimal(row["pkisrv_yield_pct"]) == Decimal(str(pkisrv["yield_pct"]))

            assert row["pkisrv_source_file"] == pkisrv["source_file"]

            assert int(row["pkisrv_ingestion_run_id"]) == 13

        else:
            assert row["pkisrv_yield_pct"] == ""

            assert row["pkisrv_source_file"] == ""

            assert row["pkisrv_ingestion_run_id"] == ""

        if pkrv is not None and pkisrv is not None:
            expected_spread = (
                Decimal(str(pkisrv["yield_pct"])) - Decimal(str(pkrv["yield_pct"]))
            ) * Decimal("100")

            assert Decimal(row["pkisrv_minus_pkrv_bps"]) == expected_spread

        else:
            assert row["pkisrv_minus_pkrv_bps"] == ""


def test_unmatched_dates_remain_explicit_without_manufactured_spreads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unmatched observations must stay unmatched and carry no synthetic spread."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "unmatched.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    pkrv_only = [row for row in rows if (row["match_status"] == "PKRV_ONLY")]

    pkisrv_only = [row for row in rows if (row["match_status"] == "PKISRV_ONLY")]

    assert len(pkrv_only) == 20

    assert len(pkisrv_only) == 10

    assert {row["observation_date"] for row in pkrv_only} == EXPECTED_PKRV_ONLY_DATES

    assert {
        row["observation_date"] for row in pkisrv_only
    } == EXPECTED_PKISRV_ONLY_DATES

    for row in pkrv_only:
        assert row["pkrv_yield_pct"] != ""

        assert row["pkisrv_yield_pct"] == ""

        assert row["pkisrv_minus_pkrv_bps"] == ""

        assert row["pkisrv_source_file"] == ""

    for row in pkisrv_only:
        assert row["pkisrv_yield_pct"] != ""

        assert row["pkrv_yield_pct"] == ""

        assert row["pkisrv_minus_pkrv_bps"] == ""

        assert row["pkrv_source_file"] == ""


def test_spread_signs_and_verified_extremes_remain_locked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spread diagnostics already source-audited must remain unchanged."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "spreads.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    matched = [row for row in rows if (row["match_status"] == "MATCHED")]

    sign_counts = Counter()

    for row in matched:
        spread = Decimal(row["pkisrv_minus_pkrv_bps"])

        if spread > 0:
            sign_counts["POSITIVE"] += 1

        elif spread < 0:
            sign_counts["NEGATIVE"] += 1

        else:
            sign_counts["ZERO"] += 1

    assert dict(sign_counts) == {
        "POSITIVE": 313,
        "NEGATIVE": 1683,
        "ZERO": 9,
    }

    top = sorted(
        matched,
        key=lambda row: abs(Decimal(row["pkisrv_minus_pkrv_bps"])),
        reverse=True,
    )[:15]

    actual = [
        (
            row["observation_date"],
            row["tenor"],
            Decimal(row["pkrv_yield_pct"]),
            Decimal(row["pkisrv_yield_pct"]),
            Decimal(row["pkisrv_minus_pkrv_bps"]),
        )
        for row in top
    ]

    assert actual == EXPECTED_TOP_15


def test_comparison_panel_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated comparison generation must produce identical bytes."""

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
