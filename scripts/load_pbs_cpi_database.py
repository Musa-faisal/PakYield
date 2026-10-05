"""Load validated PBS National CPI observations into PakYield SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    DATASET_CPI,
    PROJECT_ROOT,
)
from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "pbs_cpi_monthly_validated.csv"

EXPECTED_ROWS = 57

SOURCE_ORGANIZATION = "Pakistan Bureau of Statistics"

BASE_YEAR = "2015-16"


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one UTF-8 CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def sha256_file(
    path: Path,
) -> str:
    """Return the SHA-256 digest for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def validate_manifest(
    rows: list[dict[str, str]],
) -> None:
    """Validate the tracked CPI source manifest before DB mutation."""

    assert len(rows) == EXPECTED_ROWS

    periods = [row["period"] for row in rows]

    assert periods[0] == "2022-01"
    assert periods[-1] == "2026-09"

    assert len(set(periods)) == EXPECTED_ROWS

    for row in rows:
        assert row["national_cpi_index"]

        assert row["cpi_inflation_yoy_pct"]

        assert row["source_file"]

        assert row["validation_status"] == "SOURCE_EXPLICIT"

        index = Decimal(row["national_cpi_index"])

        yoy = Decimal(row["cpi_inflation_yoy_pct"])

        assert index > 0

        assert Decimal("-100") < yoy < Decimal("100")


def db_decimal(
    value: object,
) -> Decimal:
    """Convert a SQLite numeric value into a comparison-safe Decimal."""

    return Decimal(str(value))


def validate_existing_row(
    existing: object,
    source: dict[str, str],
) -> None:
    """Fail if an existing normalized CPI row differs from the source manifest."""

    period = source["period"]

    expected_index = Decimal(source["national_cpi_index"])

    expected_yoy = Decimal(source["cpi_inflation_yoy_pct"])

    actual_index = db_decimal(existing["national_cpi_index"])

    actual_yoy = db_decimal(existing["cpi_inflation_yoy_pct"])

    conflicts = []

    if actual_index != expected_index:
        conflicts.append(f"national_cpi_index {actual_index} != {expected_index}")

    if actual_yoy != expected_yoy:
        conflicts.append(f"cpi_inflation_yoy_pct {actual_yoy} != {expected_yoy}")

    if existing["base_year"] != BASE_YEAR:
        conflicts.append(f"base_year {existing['base_year']!r} != {BASE_YEAR!r}")

    if existing["source_organization"] != SOURCE_ORGANIZATION:
        conflicts.append(
            "source_organization "
            f"{existing['source_organization']!r} "
            f"!= {SOURCE_ORGANIZATION!r}"
        )

    if existing["source_file"] != source["source_file"]:
        conflicts.append(
            f"source_file {existing['source_file']!r} != {source['source_file']!r}"
        )

    if conflicts:
        raise RuntimeError(
            f"Conflicting existing PBS CPI row for {period}: " + "; ".join(conflicts)
        )


def start_ingestion_run(
    connection: object,
    manifest_sha: str,
) -> int:
    """Create and commit a STARTED ingestion-run record."""

    cursor = connection.execute(
        """
        INSERT INTO ingestion_runs (
            dataset,
            source_organization,
            source_file,
            retrieved_at,
            status,
            records_read,
            records_written,
            sha256,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DATASET_CPI,
            SOURCE_ORGANIZATION,
            "data/manifests/pbs_cpi_monthly_validated.csv",
            datetime.now(UTC).isoformat(),
            "STARTED",
            EXPECTED_ROWS,
            0,
            manifest_sha,
            ("Load validated National CPI source observations into cpi_observations."),
        ),
    )

    run_id = cursor.lastrowid

    assert run_id is not None

    connection.commit()

    return int(run_id)


def mark_run_success(
    connection: object,
    run_id: int,
    written: int,
    existing: int,
) -> None:
    """Mark an ingestion run successful."""

    connection.execute(
        """
        UPDATE ingestion_runs
        SET
            status = 'SUCCESS',
            records_read = ?,
            records_written = ?,
            notes = ?
        WHERE ingestion_run_id = ?
        """,
        (
            EXPECTED_ROWS,
            written,
            (
                "Validated PBS National CPI "
                f"load complete; inserted={written}; "
                f"existing_validated={existing}."
            ),
            run_id,
        ),
    )


def mark_run_failed(
    connection: object,
    run_id: int,
    message: str,
) -> None:
    """Persist failure status without altering normalized CPI rows."""

    connection.execute(
        """
        UPDATE ingestion_runs
        SET
            status = 'FAILED',
            records_read = ?,
            records_written = 0,
            notes = ?
        WHERE ingestion_run_id = ?
        """,
        (
            EXPECTED_ROWS,
            ("PBS CPI load failed: " + message[:500]),
            run_id,
        ),
    )

    connection.commit()


def load_cpi(
    database_path: Path,
    manifest_path: Path = MANIFEST_PATH,
) -> tuple[
    int,
    int,
    int,
]:
    """Load or validate all CPI rows.

    Returns:
        ingestion_run_id,
        inserted_count,
        existing_validated_count.
    """

    rows = read_csv(manifest_path)

    validate_manifest(rows)

    manifest_sha = sha256_file(manifest_path)

    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    run_id = start_ingestion_run(
        connection,
        manifest_sha,
    )

    inserted = 0
    existing_validated = 0

    try:
        connection.execute("BEGIN")

        for row in rows:
            existing = connection.execute(
                """
                SELECT
                    period,
                    national_cpi_index,
                    cpi_inflation_yoy_pct,
                    base_year,
                    source_organization,
                    source_file,
                    ingestion_run_id
                FROM cpi_observations
                WHERE period = ?
                """,
                (row["period"],),
            ).fetchone()

            if existing is not None:
                validate_existing_row(
                    existing,
                    row,
                )

                existing_validated += 1

                continue

            connection.execute(
                """
                INSERT INTO cpi_observations (
                    period,
                    national_cpi_index,
                    cpi_inflation_yoy_pct,
                    base_year,
                    source_organization,
                    source_file,
                    ingestion_run_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["period"],
                    float(Decimal(row["national_cpi_index"])),
                    float(Decimal(row["cpi_inflation_yoy_pct"])),
                    BASE_YEAR,
                    SOURCE_ORGANIZATION,
                    row["source_file"],
                    run_id,
                ),
            )

            inserted += 1

        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM cpi_observations
            """
        ).fetchone()[0]

        assert total == EXPECTED_ROWS, f"Unexpected CPI row count after load: {total}"

        mark_run_success(
            connection,
            run_id,
            inserted,
            existing_validated,
        )

        connection.commit()

    except Exception as exc:
        connection.rollback()

        mark_run_failed(
            connection,
            run_id,
            str(exc),
        )

        raise

    finally:
        connection.close()

    return (
        run_id,
        inserted,
        existing_validated,
    )


def main() -> None:
    """CLI entry point."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database-path",
        type=Path,
        default=DATABASE_PATH,
    )

    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=MANIFEST_PATH,
    )

    args = parser.parse_args()

    (
        run_id,
        inserted,
        existing,
    ) = load_cpi(
        database_path=args.database_path,
        manifest_path=args.manifest_path,
    )

    print("===== PBS CPI DATABASE LOAD =====")

    print(
        "Database:",
        args.database_path,
    )

    print(
        "Ingestion run:",
        run_id,
    )

    print(
        "Source rows:",
        EXPECTED_ROWS,
    )

    print(
        "Inserted:",
        inserted,
    )

    print(
        "Existing validated:",
        existing,
    )

    print("")
    print("PASS: PBS CPI database load complete")


if __name__ == "__main__":
    main()
