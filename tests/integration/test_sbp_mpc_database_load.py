"""Integration tests for normalized SBP MPC database loading."""

from __future__ import annotations

import importlib.util
import sqlite3
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOADER_PATH = PROJECT_ROOT / "scripts" / "load_sbp_mpc_database.py"


def load_loader_module() -> ModuleType:
    """Load the MPC CLI module from its repository path."""

    spec = importlib.util.spec_from_file_location(
        "load_sbp_mpc_database",
        LOADER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


LOADER = load_loader_module()

SOURCE_ORGANIZATION = LOADER.SOURCE_ORGANIZATION

load_mpc_events = LOADER.load_mpc_events


def test_mpc_loader_writes_exact_validated_event_state(
    tmp_path: Path,
) -> None:
    """Loader must preserve the complete 39-event validated MPC universe."""

    database_path = tmp_path / "pakyield.sqlite3"

    result = load_mpc_events(database_path=database_path)

    assert result == (
        1,
        39,
        0,
    )

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT
                event_date,
                decision_type,
                previous_rate_pct,
                announced_rate_pct,
                change_bps,
                effective_date,
                statement_title,
                statement_url,
                source_organization,
                ingestion_run_id,
                notes
            FROM mpc_events
            ORDER BY event_date
            """
        ).fetchall()

        assert len(rows) == 39

        counts = Counter(row["decision_type"] for row in rows)

        assert dict(counts) == {
            "HOLD": 22,
            "HIKE": 9,
            "CUT": 8,
        }

        assert rows[0]["event_date"] == "2022-01-24"

        assert rows[0]["previous_rate_pct"] == 9.75

        assert rows[0]["announced_rate_pct"] == 9.75

        april_2022 = next(row for row in rows if row["event_date"] == "2022-04-07")

        assert april_2022["decision_type"] == "HIKE"

        assert april_2022["previous_rate_pct"] == 9.75

        assert april_2022["announced_rate_pct"] == 12.25

        assert april_2022["change_bps"] == 250

        december_2025 = next(row for row in rows if row["event_date"] == "2025-12-15")

        assert december_2025["decision_type"] == "CUT"

        assert december_2025["previous_rate_pct"] == 11.0

        assert december_2025["announced_rate_pct"] is None

        assert december_2025["change_bps"] == -50

        assert december_2025["effective_date"] == "2025-12-16"

        assert "not stored as a statement-announced rate" in december_2025["notes"]

        january_2026 = next(row for row in rows if row["event_date"] == "2026-01-26")

        assert january_2026["previous_rate_pct"] == 10.5

        assert january_2026["announced_rate_pct"] == 10.5

        explicit = [row for row in rows if row["effective_date"] is not None]

        assert len(explicit) == 10

        for row in rows:
            assert row["statement_title"]
            assert row["statement_url"]

            assert row["source_organization"] == SOURCE_ORGANIZATION

    finally:
        connection.close()


def test_mpc_loader_is_idempotent(
    tmp_path: Path,
) -> None:
    """A matching rerun validates all 39 events and writes no duplicates."""

    database_path = tmp_path / "pakyield.sqlite3"

    first = load_mpc_events(database_path=database_path)

    second = load_mpc_events(database_path=database_path)

    assert first == (
        1,
        39,
        0,
    )

    assert second == (
        2,
        0,
        39,
    )

    connection = get_connection(database_path)

    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM mpc_events
            """
        ).fetchone()[0]

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'SBP_MPC_EVENTS'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert count == 39
        assert len(runs) == 2

        assert tuple(runs[0]) == (
            "SUCCESS",
            39,
            39,
        )

        assert tuple(runs[1]) == (
            "SUCCESS",
            39,
            0,
        )

    finally:
        connection.close()


def test_mpc_loader_fails_closed_on_conflict(
    tmp_path: Path,
) -> None:
    """A conflicting existing MPC event must never be overwritten."""

    database_path = tmp_path / "pakyield.sqlite3"

    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO mpc_events (
                event_date,
                decision_type,
                previous_rate_pct,
                announced_rate_pct,
                change_bps,
                source_organization
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2022-01-24",
                "HOLD",
                9.75,
                99.0,
                0,
                SOURCE_ORGANIZATION,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match=("Conflicting existing SBP MPC row"),
    ):
        load_mpc_events(database_path=database_path)

    connection = get_connection(database_path)

    try:
        row = connection.execute(
            """
            SELECT announced_rate_pct
            FROM mpc_events
            WHERE event_date = '2022-01-24'
            """
        ).fetchone()

        assert row is not None

        assert row["announced_rate_pct"] == 99.0

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM mpc_events
            """
        ).fetchone()[0]

        failed = connection.execute(
            """
            SELECT
                status,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'SBP_MPC_EVENTS'
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


def test_mpc_unique_event_date_constraint(
    tmp_path: Path,
) -> None:
    """SQLite must enforce one normalized MPC record per event date."""

    database_path = tmp_path / "pakyield.sqlite3"

    load_mpc_events(database_path=database_path)

    connection = get_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO mpc_events (
                    event_date,
                    decision_type,
                    change_bps,
                    source_organization
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "2022-01-24",
                    "HOLD",
                    0,
                    SOURCE_ORGANIZATION,
                ),
            )

    finally:
        connection.close()
