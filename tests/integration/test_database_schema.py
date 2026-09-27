"""Integration tests for the PakYield SQLite research schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

EXPECTED_TABLES = {
    "schema_version",
    "ingestion_runs",
    "yield_observations",
    "policy_rate_observations",
    "mpc_events",
    "cpi_observations",
}


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    """Create an initialized temporary PakYield database."""

    path = tmp_path / "test_pakyield.sqlite3"

    initialize_database(database_path=path)

    return path


def test_database_initialization_creates_file(
    database_path: Path,
) -> None:
    """Initialization should create a SQLite database file."""

    assert database_path.is_file()


def test_database_initialization_is_idempotent(
    database_path: Path,
) -> None:
    """Running initialization repeatedly should remain safe."""

    initialize_database(database_path=database_path)
    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    try:
        version = connection.execute(
            """
            SELECT version
            FROM schema_version
            """
        ).fetchone()[0]

        assert version == 1
    finally:
        connection.close()


def test_expected_tables_exist(
    database_path: Path,
) -> None:
    """The initialized database must contain all core tables."""

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        actual_tables = {row["name"] for row in rows}

        assert actual_tables == EXPECTED_TABLES
    finally:
        connection.close()


def test_foreign_keys_are_enabled(
    database_path: Path,
) -> None:
    """Every PakYield application connection must enforce foreign keys."""

    connection = get_connection(database_path)

    try:
        enabled = connection.execute("PRAGMA foreign_keys;").fetchone()[0]

        assert enabled == 1
    finally:
        connection.close()


def test_duplicate_yield_observation_is_rejected(
    database_path: Path,
) -> None:
    """Date + curve + tenor must uniquely identify a yield observation."""

    connection = get_connection(database_path)

    row = (
        "2026-09-17",
        "PKRV",
        "1Y",
        1.0,
        10.86,
        "TEST",
    )

    try:
        connection.execute(
            """
            INSERT INTO yield_observations (
                observation_date,
                curve_type,
                tenor,
                tenor_years,
                yield_pct,
                source_organization
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            row,
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO yield_observations (
                    observation_date,
                    curve_type,
                    tenor,
                    tenor_years,
                    yield_pct,
                    source_organization
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("decision_type", "change_bps"),
    [
        ("HIKE", -100),
        ("CUT", 100),
        ("HOLD", 25),
    ],
)
def test_invalid_mpc_direction_is_rejected(
    database_path: Path,
    decision_type: str,
    change_bps: int,
) -> None:
    """MPC decision type and signed basis-point change must agree."""

    connection = get_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO mpc_events (
                    event_date,
                    decision_type,
                    change_bps
                )
                VALUES (?, ?, ?)
                """,
                (
                    f"2099-01-{abs(change_bps) % 20 + 1:02d}",
                    decision_type,
                    change_bps,
                ),
            )
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("decision_type", "change_bps"),
    [
        ("HIKE", 100),
        ("CUT", -100),
        ("HOLD", 0),
    ],
)
def test_valid_mpc_direction_is_accepted(
    database_path: Path,
    decision_type: str,
    change_bps: int,
) -> None:
    """Valid MPC decision/change combinations should be accepted."""

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO mpc_events (
                event_date,
                decision_type,
                change_bps
            )
            VALUES (?, ?, ?)
            """,
            (
                f"2098-01-{abs(change_bps) % 20 + 1:02d}",
                decision_type,
                change_bps,
            ),
        )

        connection.commit()
    finally:
        connection.close()


def test_duplicate_policy_rate_effective_date_is_rejected(
    database_path: Path,
) -> None:
    """Policy-rate effective dates must be unique."""

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO policy_rate_observations (
                effective_date,
                rate_pct
            )
            VALUES (?, ?)
            """,
            ("2026-04-28", 11.5),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO policy_rate_observations (
                    effective_date,
                    rate_pct
                )
                VALUES (?, ?)
                """,
                ("2026-04-28", 12.0),
            )
    finally:
        connection.close()


def test_duplicate_cpi_period_is_rejected(
    database_path: Path,
) -> None:
    """Only one normalized CPI observation may exist per month."""

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO cpi_observations (
                period,
                national_cpi_index,
                cpi_inflation_yoy_pct
            )
            VALUES (?, ?, ?)
            """,
            ("2026-08", 280.0, 6.5),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO cpi_observations (
                    period,
                    national_cpi_index,
                    cpi_inflation_yoy_pct
                )
                VALUES (?, ?, ?)
                """,
                ("2026-08", 281.0, 6.6),
            )
    finally:
        connection.close()


def test_invalid_curve_type_is_rejected(
    database_path: Path,
) -> None:
    """Only PKRV and PKISRV are valid normalized curve types."""

    connection = get_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO yield_observations (
                    observation_date,
                    curve_type,
                    tenor,
                    tenor_years,
                    yield_pct,
                    source_organization
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "2026-09-17",
                    "INVALID",
                    "1Y",
                    1.0,
                    10.0,
                    "TEST",
                ),
            )
    finally:
        connection.close()


def test_invalid_ingestion_dataset_is_rejected(
    database_path: Path,
) -> None:
    """Ingestion provenance must use an approved dataset identifier."""

    connection = get_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO ingestion_runs (
                    dataset,
                    source_organization,
                    retrieved_at,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "INVALID_DATASET",
                    "TEST",
                    "2026-09-20T00:00:00",
                    "SUCCESS",
                ),
            )
    finally:
        connection.close()
