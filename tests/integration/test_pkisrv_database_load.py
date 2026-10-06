"""Integration tests for normalized PKISRV SQLite loading."""

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

LOADER_PATH = PROJECT_ROOT / "scripts" / "load_pkisrv_database.py"


def load_loader_module() -> ModuleType:
    """Load the PKISRV database loader."""

    spec = importlib.util.spec_from_file_location(
        "load_pkisrv_database",
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

load_pkisrv = LOADER.load_pkisrv


def test_pkisrv_loader_writes_exact_normalized_state(
    tmp_path: Path,
) -> None:
    """First load must persist exactly the validated 2,015-row state."""

    database_path = tmp_path / "pakyield.sqlite3"

    result = load_pkisrv(database_path=database_path)

    assert result == (
        1,
        2015,
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
                WHERE curve_type = 'PKISRV'
                ORDER BY
                    observation_date,
                    tenor_years,
                    tenor
                """
        ).fetchall()

        assert len(rows) == 2015

        dates = {row["observation_date"] for row in rows}

        assert len(dates) == 403

        assert min(dates) == "2025-02-03"

        assert max(dates) == "2026-09-30"

        date_counts = Counter(row["observation_date"] for row in rows)

        assert dict(Counter(date_counts.values())) == {
            5: 403,
        }

        tenor_counts = Counter(row["tenor"] for row in rows)

        assert dict(tenor_counts) == {
            "1M": 403,
            "3M": 403,
            "6M": 403,
            "9M": 403,
            "1Y": 403,
        }

        assert {row["ingestion_run_id"] for row in rows} == {
            1,
        }

        assert {row["source_organization"] for row in rows} == {
            SOURCE_ORGANIZATION,
        }

        unique_source_files = {row["source_file"] for row in rows}

        assert len(unique_source_files) == 403

        by_key = {
            (
                row["observation_date"],
                row["tenor"],
            ): row
            for row in rows
        }

        assert by_key[
            (
                "2025-02-03",
                "1M",
            )
        ]["yield_pct"] == pytest.approx(10.70)

        assert by_key[
            (
                "2025-02-03",
                "6M",
            )
        ]["yield_pct"] == pytest.approx(17.71)

        assert by_key[
            (
                "2026-03-02",
                "1M",
            )
        ]["yield_pct"] == pytest.approx(7.76)

        assert by_key[
            (
                "2026-06-18",
                "1M",
            )
        ]["yield_pct"] == pytest.approx(11.83)

        for absent_date in {
            "2025-03-07",
            "2025-08-20",
            "2026-03-18",
            "2026-03-27",
        }:
            assert absent_date not in dates

        runs = connection.execute(
            """
                SELECT
                    status,
                    records_read,
                    records_written,
                    sha256
                FROM ingestion_runs
                WHERE dataset = 'PKISRV'
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
            2015,
            2015,
            EXPECTED_SHA256,
        )

    finally:
        connection.close()


def test_pkisrv_loader_is_idempotent(
    tmp_path: Path,
) -> None:
    """Matching rerun must validate all rows without writing duplicates."""

    database_path = tmp_path / "pakyield.sqlite3"

    first = load_pkisrv(database_path=database_path)

    second = load_pkisrv(database_path=database_path)

    assert first == (
        1,
        2015,
        0,
    )

    assert second == (
        2,
        0,
        2015,
    )

    connection = get_connection(database_path)

    try:
        count = connection.execute(
            """
                SELECT COUNT(*)
                FROM yield_observations
                WHERE curve_type = 'PKISRV'
                """
        ).fetchone()[0]

        assert count == 2015

        row_run_ids = {
            row["ingestion_run_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT
                    ingestion_run_id
                FROM yield_observations
                WHERE curve_type = 'PKISRV'
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
                WHERE dataset = 'PKISRV'
                ORDER BY ingestion_run_id
                """
        ).fetchall()

        assert len(runs) == 2

        assert tuple(runs[0]) == (
            "SUCCESS",
            2015,
            2015,
            EXPECTED_SHA256,
        )

        assert tuple(runs[1]) == (
            "SUCCESS",
            2015,
            0,
            EXPECTED_SHA256,
        )

    finally:
        connection.close()


def test_pkisrv_loader_fails_closed_on_existing_conflict(
    tmp_path: Path,
) -> None:
    """Conflicting existing PKISRV rows must survive unchanged."""

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
                "2025-02-03",
                "PKISRV",
                "1M",
                1 / 12,
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
        match=("Conflicting existing PKISRV row"),
    ):
        load_pkisrv(database_path=database_path)

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
                WHERE curve_type = 'PKISRV'
                """
        ).fetchall()

        assert len(rows) == 1

        assert rows[0]["observation_date"] == "2025-02-03"

        assert rows[0]["tenor"] == "1M"

        assert rows[0]["yield_pct"] == 99.0

        assert rows[0]["source_file"] == "wrong-source.csv"

        runs = connection.execute(
            """
                SELECT
                    status,
                    records_read,
                    records_written
                FROM ingestion_runs
                WHERE dataset = 'PKISRV'
                ORDER BY ingestion_run_id
                """
        ).fetchall()

        assert len(runs) == 1

        assert tuple(runs[0]) == (
            "FAILED",
            2015,
            0,
        )

    finally:
        connection.close()


def test_pkisrv_loader_rejects_tampered_artifact_before_database_mutation(
    tmp_path: Path,
) -> None:
    """Changed normalized bytes must fail before database creation."""

    tampered_path = tmp_path / "tampered.csv"

    original = NORMALIZED_PATH.read_bytes()

    tampered_path.write_bytes(original + b"\n")

    database_path = tmp_path / "should_not_exist.sqlite3"

    with pytest.raises(
        RuntimeError,
        match=("Normalized PKISRV SHA-256 mismatch"),
    ):
        load_pkisrv(
            database_path=database_path,
            normalized_path=tampered_path,
        )

    assert not (database_path.exists())


def test_pkisrv_loader_coexists_with_same_date_tenor_pkrv_row(
    tmp_path: Path,
) -> None:
    """PKRV and PKISRV may coexist on the same date and tenor."""

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
                "2025-02-03",
                "PKRV",
                "1M",
                1 / 12,
                12.34,
                SOURCE_ORGANIZATION,
                "pkrv-existing.csv",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    result = load_pkisrv(database_path=database_path)

    assert result == (
        1,
        2015,
        0,
    )

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
                SELECT
                    curve_type,
                    yield_pct,
                    source_file
                FROM yield_observations
                WHERE observation_date = '2025-02-03'
                  AND tenor = '1M'
                ORDER BY curve_type
                """
        ).fetchall()

        assert len(rows) == 2

        assert {row["curve_type"] for row in rows} == {
            "PKRV",
            "PKISRV",
        }

        by_curve = {row["curve_type"]: row for row in rows}

        assert by_curve["PKRV"]["yield_pct"] == pytest.approx(12.34)

        assert by_curve["PKRV"]["source_file"] == "pkrv-existing.csv"

        assert by_curve["PKISRV"]["yield_pct"] == pytest.approx(10.70)

    finally:
        connection.close()
