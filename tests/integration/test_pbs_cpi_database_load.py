"""Integration tests for loading validated PBS CPI into SQLite."""

from __future__ import annotations

import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest

from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOADER_PATH = PROJECT_ROOT / "scripts" / "load_pbs_cpi_database.py"


def load_module():
    """Import the production loader from its script path."""

    spec = importlib.util.spec_from_file_location(
        "load_pbs_cpi_database",
        LOADER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


def test_first_load_writes_exactly_57_rows(
    tmp_path: Path,
) -> None:
    """A fresh CPI database receives exactly the validated source corpus."""

    module = load_module()

    database = tmp_path / "pakyield.sqlite3"

    (
        run_id,
        inserted,
        existing,
    ) = module.load_cpi(database)

    assert run_id > 0
    assert inserted == 57
    assert existing == 0

    connection = get_connection(database)

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM cpi_observations
            ORDER BY period
            """
        ).fetchall()

        assert len(rows) == 57

        assert rows[0]["period"] == "2022-01"

        assert rows[-1]["period"] == "2026-09"

    finally:
        connection.close()


def test_database_values_match_source_boundaries(
    tmp_path: Path,
) -> None:
    """Known CPI boundary values must survive normalization unchanged."""

    module = load_module()

    database = tmp_path / "pakyield.sqlite3"

    module.load_cpi(database)

    connection = get_connection(database)

    try:
        rows = {
            row["period"]: row
            for row in connection.execute(
                """
                SELECT *
                FROM cpi_observations
                """
            ).fetchall()
        }

        expected = {
            "2022-01": (
                Decimal("158.8"),
                Decimal("13.0"),
            ),
            "2026-06": (
                Decimal("293.5"),
                Decimal("11.1"),
            ),
            "2026-07": (
                Decimal("296.97"),
                Decimal("9.20"),
            ),
            "2026-08": (
                Decimal("300.50"),
                Decimal("11.15"),
            ),
            "2026-09": (
                Decimal("304.33"),
                Decimal("10.26"),
            ),
        }

        for period, values in expected.items():
            row = rows[period]

            assert Decimal(str(row["national_cpi_index"])) == values[0]

            assert Decimal(str(row["cpi_inflation_yoy_pct"])) == values[1]

            assert row["base_year"] == "2015-16"

            assert row["source_organization"] == ("Pakistan Bureau of Statistics")

            assert row["source_file"]

    finally:
        connection.close()


def test_second_load_is_idempotent(
    tmp_path: Path,
) -> None:
    """A second load validates existing rows and inserts nothing."""

    module = load_module()

    database = tmp_path / "pakyield.sqlite3"

    first = module.load_cpi(database)

    second = module.load_cpi(database)

    assert first[1:] == (
        57,
        0,
    )

    assert second[1:] == (
        0,
        57,
    )

    connection = get_connection(database)

    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM cpi_observations
            """
        ).fetchone()[0]

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'PBS_CPI'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert count == 57

        assert len(runs) == 2

        assert tuple(runs[0]) == (
            "SUCCESS",
            57,
            57,
        )

        assert tuple(runs[1]) == (
            "SUCCESS",
            57,
            0,
        )

    finally:
        connection.close()


def test_conflicting_existing_row_fails_closed(
    tmp_path: Path,
) -> None:
    """The loader must never overwrite conflicting CPI source values."""

    module = load_module()

    database = tmp_path / "pakyield.sqlite3"

    initialize_database(database_path=database)

    connection = get_connection(database)

    try:
        connection.execute(
            """
            INSERT INTO cpi_observations (
                period,
                national_cpi_index,
                cpi_inflation_yoy_pct,
                base_year,
                source_organization,
                source_file
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2022-01",
                999.0,
                13.0,
                "2015-16",
                "Pakistan Bureau of Statistics",
                ("indices_and_growth_rates_historical-1.pdf"),
            ),
        )

        connection.commit()

    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match=("Conflicting existing PBS CPI row"),
    ):
        module.load_cpi(database)

    connection = get_connection(database)

    try:
        row = connection.execute(
            """
            SELECT national_cpi_index
            FROM cpi_observations
            WHERE period = '2022-01'
            """
        ).fetchone()

        assert row is not None

        assert row["national_cpi_index"] == 999.0

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM cpi_observations
            """
        ).fetchone()[0]

        assert count == 1

        failed = connection.execute(
            """
            SELECT
                status,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'PBS_CPI'
            ORDER BY ingestion_run_id DESC
            LIMIT 1
            """
        ).fetchone()

        assert failed is not None

        assert failed["status"] == "FAILED"

        assert failed["records_written"] == 0

    finally:
        connection.close()
