"""Integration tests for normalized SBP policy-rate loading."""

from __future__ import annotations

import importlib.util
import sqlite3
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOADER_PATH = PROJECT_ROOT / "scripts" / "load_sbp_policy_rate_database.py"


def load_loader_module() -> ModuleType:
    """Load the policy-rate CLI module from its repository path."""

    spec = importlib.util.spec_from_file_location(
        "load_sbp_policy_rate_database",
        LOADER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


LOADER = load_loader_module()

EXPECTED_NORMALIZED = LOADER.EXPECTED_NORMALIZED
EXPECTED_NORMALIZED_ROWS = LOADER.EXPECTED_NORMALIZED_ROWS
EXPECTED_SERIES_KEY = LOADER.EXPECTED_SERIES_KEY
SOURCE_ORGANIZATION = LOADER.SOURCE_ORGANIZATION
load_policy_rate = LOADER.load_policy_rate


def test_policy_rate_loader_writes_anchor_and_core_sequence(
    tmp_path: Path,
) -> None:
    """Loader must persist one anchor plus 17 in-sample changes."""

    database_path = tmp_path / "pakyield.sqlite3"

    result = load_policy_rate(database_path=database_path)

    assert result == (
        1,
        18,
        0,
    )

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT
                effective_date,
                rate_pct,
                series_key,
                observation_status,
                observation_status_comment,
                source_organization,
                source_file,
                ingestion_run_id
            FROM policy_rate_observations
            ORDER BY effective_date
            """
        ).fetchall()

        assert len(rows) == EXPECTED_NORMALIZED_ROWS

        actual = tuple(
            (
                row["effective_date"],
                Decimal(str(row["rate_pct"])),
            )
            for row in rows
        )

        assert actual == EXPECTED_NORMALIZED

        assert rows[0]["effective_date"] == "2021-12-15"

        assert rows[0]["rate_pct"] == 9.75

        for row in rows:
            assert row["series_key"] == EXPECTED_SERIES_KEY

            assert row["observation_status"] == "Normal"

            assert row["observation_status_comment"] is None

            assert row["source_organization"] == SOURCE_ORGANIZATION

            assert row["source_file"] == "data_series.csv"

    finally:
        connection.close()


def test_policy_rate_loader_is_idempotent(
    tmp_path: Path,
) -> None:
    """A matching rerun validates all 18 rows without duplicates."""

    database_path = tmp_path / "pakyield.sqlite3"

    first = load_policy_rate(database_path=database_path)

    second = load_policy_rate(database_path=database_path)

    assert first == (
        1,
        18,
        0,
    )

    assert second == (
        2,
        0,
        18,
    )

    connection = get_connection(database_path)

    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM policy_rate_observations
            """
        ).fetchone()[0]

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'SBP_POLICY_RATE'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert count == 18
        assert len(runs) == 2

        assert tuple(runs[0]) == (
            "SUCCESS",
            18,
            18,
        )

        assert tuple(runs[1]) == (
            "SUCCESS",
            18,
            0,
        )

    finally:
        connection.close()


def test_policy_rate_loader_fails_closed_on_conflict(
    tmp_path: Path,
) -> None:
    """A conflicting anchor must never be silently overwritten."""

    database_path = tmp_path / "pakyield.sqlite3"

    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO policy_rate_observations (
                effective_date,
                rate_pct,
                series_key,
                observation_status,
                source_organization,
                source_file
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2021-12-15",
                99.0,
                EXPECTED_SERIES_KEY,
                "Normal",
                SOURCE_ORGANIZATION,
                "data_series.csv",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match=("Conflicting existing SBP policy-rate"),
    ):
        load_policy_rate(database_path=database_path)

    connection = get_connection(database_path)

    try:
        row = connection.execute(
            """
            SELECT rate_pct
            FROM policy_rate_observations
            WHERE effective_date = '2021-12-15'
            """
        ).fetchone()

        assert row is not None
        assert row["rate_pct"] == 99.0

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM policy_rate_observations
            """
        ).fetchone()[0]

        failed = connection.execute(
            """
            SELECT
                status,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'SBP_POLICY_RATE'
            ORDER BY ingestion_run_id DESC
            LIMIT 1
            """
        ).fetchone()

        assert count == 1

        assert failed is not None
        assert failed["status"] == "FAILED"
        assert failed["records_written"] == 0

    finally:
        connection.close()


def test_policy_rate_unique_effective_date_constraint(
    tmp_path: Path,
) -> None:
    """SQLite must enforce one observation per effective date."""

    database_path = tmp_path / "pakyield.sqlite3"

    load_policy_rate(database_path=database_path)

    connection = get_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO policy_rate_observations (
                    effective_date,
                    rate_pct,
                    series_key,
                    observation_status,
                    source_organization,
                    source_file
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "2021-12-15",
                    9.75,
                    EXPECTED_SERIES_KEY,
                    "Normal",
                    SOURCE_ORGANIZATION,
                    "data_series.csv",
                ),
            )

    finally:
        connection.close()
