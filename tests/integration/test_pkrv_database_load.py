"""Integration tests for normalized PKRV SQLite loading."""

from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOADER_PATH = PROJECT_ROOT / "scripts" / "load_pkrv_database.py"


def load_loader_module() -> ModuleType:
    """Load the PKRV database loader from its repository path."""

    spec = importlib.util.spec_from_file_location(
        "load_pkrv_database",
        LOADER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


LOADER = load_loader_module()

NORMALIZED_PATH = LOADER.NORMALIZED_PATH

EXPECTED_SHA256 = LOADER.EXPECTED_SHA256

SOURCE_ORGANIZATION = LOADER.SOURCE_ORGANIZATION

load_pkrv = LOADER.load_pkrv


def test_pkrv_loader_writes_exact_normalized_state(
    tmp_path: Path,
) -> None:
    """First load must write exactly the validated 22,800-row PKRV state."""

    database_path = tmp_path / "pakyield.sqlite3"

    result = load_pkrv(database_path=database_path)

    assert result == (
        1,
        22800,
        0,
    )

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT
                observation_date,
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

        assert len(rows) == 22800

        dates = {row["observation_date"] for row in rows}

        assert len(dates) == 1149

        assert min(dates) == "2022-01-04"

        assert max(dates) == "2026-09-28"

        date_counts = Counter(row["observation_date"] for row in rows)

        assert dict(Counter(date_counts.values())) == {
            20: 1119,
            14: 30,
        }

        assert {row["ingestion_run_id"] for row in rows} == {
            1,
        }

        assert {row["source_organization"] for row in rows} == {
            SOURCE_ORGANIZATION,
        }

        unique_source_files = {row["source_file"] for row in rows}

        assert len(unique_source_files) == 1149

        by_key = {
            (
                row["observation_date"],
                row["tenor"],
            ): row
            for row in rows
        }

        assert by_key[
            (
                "2022-01-04",
                "1W",
            )
        ]["yield_pct"] == pytest.approx(9.99)

        assert by_key[
            (
                "2022-11-16",
                "1W",
            )
        ]["yield_pct"] == pytest.approx(15.08)

        assert by_key[
            (
                "2023-06-16",
                "1W",
            )
        ]["yield_pct"] == pytest.approx(21.53)

        assert by_key[
            (
                "2026-09-28",
                "20Y",
            )
        ]["yield_pct"] == pytest.approx(12.9)

        for tenor in {
            "1M",
            "2M",
            "3M",
            "4M",
            "6M",
            "9M",
        }:
            assert (
                "2023-06-16",
                tenor,
            ) not in by_key

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written,
                sha256
            FROM ingestion_runs
            WHERE dataset = 'PKRV'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert len(runs) == 1

        assert (
            runs[0]["status"],
            runs[0]["records_read"],
            runs[0]["records_written"],
            runs[0]["sha256"],
        ) == (
            "SUCCESS",
            22800,
            22800,
            EXPECTED_SHA256,
        )

    finally:
        connection.close()


def test_pkrv_loader_is_idempotent(
    tmp_path: Path,
) -> None:
    """Matching rerun must validate all PKRV rows and write zero duplicates."""

    database_path = tmp_path / "pakyield.sqlite3"

    first = load_pkrv(database_path=database_path)

    second = load_pkrv(database_path=database_path)

    assert first == (
        1,
        22800,
        0,
    )

    assert second == (
        2,
        0,
        22800,
    )

    connection = get_connection(database_path)

    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM yield_observations
            WHERE curve_type = 'PKRV'
            """
        ).fetchone()[0]

        assert count == 22800

        row_run_ids = {
            row["ingestion_run_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT
                    ingestion_run_id
                FROM yield_observations
                WHERE curve_type = 'PKRV'
                """
            ).fetchall()
        }

        assert row_run_ids == {
            1,
        }

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written,
                sha256
            FROM ingestion_runs
            WHERE dataset = 'PKRV'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert len(runs) == 2

        assert tuple(runs[0]) == (
            "SUCCESS",
            22800,
            22800,
            EXPECTED_SHA256,
        )

        assert tuple(runs[1]) == (
            "SUCCESS",
            22800,
            0,
            EXPECTED_SHA256,
        )

    finally:
        connection.close()


def test_pkrv_loader_fails_closed_on_existing_conflict(
    tmp_path: Path,
) -> None:
    """Conflicting existing PKRV rows must survive unchanged and fail the run."""

    database_path = tmp_path / "pakyield.sqlite3"

    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO yield_observations (
                observation_date,
                curve_type,
                tenor,
                tenor_years,
                yield_pct,
                source_organization,
                source_file
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2022-01-04",
                "PKRV",
                "1W",
                7 / 365,
                99.0,
                SOURCE_ORGANIZATION,
                "wrong-source.csv",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match=("Conflicting existing PKRV row"),
    ):
        load_pkrv(database_path=database_path)

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT
                observation_date,
                tenor,
                yield_pct,
                source_file
            FROM yield_observations
            WHERE curve_type = 'PKRV'
            """
        ).fetchall()

        assert len(rows) == 1

        assert rows[0]["observation_date"] == "2022-01-04"

        assert rows[0]["tenor"] == "1W"

        assert rows[0]["yield_pct"] == 99.0

        assert rows[0]["source_file"] == "wrong-source.csv"

        runs = connection.execute(
            """
            SELECT
                status,
                records_read,
                records_written
            FROM ingestion_runs
            WHERE dataset = 'PKRV'
            ORDER BY ingestion_run_id
            """
        ).fetchall()

        assert len(runs) == 1

        assert tuple(runs[0]) == (
            "FAILED",
            22800,
            0,
        )

    finally:
        connection.close()


def test_pkrv_loader_rejects_tampered_artifact_before_database_mutation(
    tmp_path: Path,
) -> None:
    """A changed long-form artifact must fail SHA validation before DB creation."""

    tampered_path = tmp_path / "tampered.csv"

    original = NORMALIZED_PATH.read_bytes()

    tampered_path.write_bytes(original + b"\n")

    database_path = tmp_path / "should_not_exist.sqlite3"

    with pytest.raises(
        RuntimeError,
        match=("Normalized PKRV SHA-256 mismatch"),
    ):
        load_pkrv(
            database_path=database_path,
            normalized_path=tampered_path,
        )

    assert not database_path.exists()
