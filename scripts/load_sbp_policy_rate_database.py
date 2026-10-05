"""Load validated SBP Policy (Target) Rate observations into PakYield SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    DATASET_POLICY_RATE,
    PROJECT_ROOT,
)
from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_policy_rate_structural_census.csv"
)

EXPECTED_SOURCE_ROWS = 39
EXPECTED_IN_SAMPLE_ROWS = 17
EXPECTED_NORMALIZED_ROWS = 18

SOURCE_ORGANIZATION = "State Bank of Pakistan"

EXPECTED_SERIES_KEY = "TS_GP_IR_SIRPR_AH.SBPOL0030"
EXPECTED_SERIES = "SBP Policy (Target) Rate"
EXPECTED_UNIT = "Percent"
EXPECTED_STATUS = "Normal"

ANCHOR_DATE = "2021-12-15"
FIRST_IN_SAMPLE_DATE = "2022-04-08"
LAST_IN_SAMPLE_DATE = "2026-04-28"

EXPECTED_NORMALIZED = (
    ("2021-12-15", Decimal("9.75")),
    ("2022-04-08", Decimal("12.25")),
    ("2022-05-24", Decimal("13.75")),
    ("2022-07-13", Decimal("15")),
    ("2022-11-28", Decimal("16")),
    ("2023-01-24", Decimal("17")),
    ("2023-03-03", Decimal("20")),
    ("2023-04-05", Decimal("21")),
    ("2023-06-27", Decimal("22")),
    ("2024-06-11", Decimal("20.5")),
    ("2024-07-30", Decimal("19.5")),
    ("2024-09-13", Decimal("17.5")),
    ("2024-11-05", Decimal("15")),
    ("2024-12-17", Decimal("13")),
    ("2025-01-28", Decimal("12")),
    ("2025-05-06", Decimal("11")),
    ("2025-12-16", Decimal("10.5")),
    ("2026-04-28", Decimal("11.5")),
)

EXPECTED_DATES = {effective_date for effective_date, _ in EXPECTED_NORMALIZED}


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
    """Return SHA-256 for one file."""

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
) -> list[dict[str, str]]:
    """Validate the census and return the 18-row analytical state source."""

    assert len(rows) == EXPECTED_SOURCE_ROWS, (
        f"Unexpected policy-rate structural-census row count: {len(rows)}"
    )

    accepted = [row for row in rows if row["validation_status"] == "ACCEPTED"]

    assert len(accepted) == EXPECTED_SOURCE_ROWS

    for row in accepted:
        assert row["series_key"] == EXPECTED_SERIES_KEY
        assert row["series"] == EXPECTED_SERIES
        assert row["unit"] == EXPECTED_UNIT
        assert row["observation_status"] == EXPECTED_STATUS

        assert row["observation_status_comment"] == ""

        assert row["structural_class"] == "VALID_OBSERVATION"

        assert row["raw_file_name"] == "data_series.csv"

        Decimal(row["observation_value"])

    normalized = [row for row in accepted if row["observation_date"] in EXPECTED_DATES]

    normalized.sort(key=lambda row: row["observation_date"])

    assert len(normalized) == EXPECTED_NORMALIZED_ROWS

    actual = tuple(
        (
            row["observation_date"],
            Decimal(row["observation_value"]),
        )
        for row in normalized
    )

    assert actual == EXPECTED_NORMALIZED, (
        "Policy-rate normalized sequence differs from the frozen validated sequence"
    )

    in_sample = [
        row
        for row in normalized
        if (FIRST_IN_SAMPLE_DATE <= row["observation_date"] <= LAST_IN_SAMPLE_DATE)
    ]

    assert len(in_sample) == EXPECTED_IN_SAMPLE_ROWS

    return normalized


def db_decimal(
    value: object,
) -> Decimal:
    """Convert a SQLite numeric value to Decimal."""

    return Decimal(str(value))


def validate_existing_row(
    existing: object,
    source: dict[str, str],
) -> None:
    """Fail closed when an existing normalized observation conflicts."""

    effective_date = source["observation_date"]

    expected_rate = Decimal(source["observation_value"])

    actual_rate = db_decimal(existing["rate_pct"])

    conflicts: list[str] = []

    if actual_rate != expected_rate:
        conflicts.append(f"rate_pct {actual_rate} != {expected_rate}")

    if existing["series_key"] != EXPECTED_SERIES_KEY:
        conflicts.append(
            f"series_key {existing['series_key']!r} != {EXPECTED_SERIES_KEY!r}"
        )

    if existing["observation_status"] != source["observation_status"]:
        conflicts.append(
            "observation_status "
            f"{existing['observation_status']!r} "
            f"!= {source['observation_status']!r}"
        )

    expected_comment = source["observation_status_comment"] or None

    if existing["observation_status_comment"] != expected_comment:
        conflicts.append(
            "observation_status_comment "
            f"{existing['observation_status_comment']!r} "
            f"!= {expected_comment!r}"
        )

    if existing["source_organization"] != SOURCE_ORGANIZATION:
        conflicts.append(
            "source_organization "
            f"{existing['source_organization']!r} "
            f"!= {SOURCE_ORGANIZATION!r}"
        )

    if existing["source_file"] != source["raw_file_name"]:
        conflicts.append(
            f"source_file {existing['source_file']!r} != {source['raw_file_name']!r}"
        )

    if conflicts:
        raise RuntimeError(
            "Conflicting existing SBP policy-rate "
            f"row for {effective_date}: " + "; ".join(conflicts)
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
            DATASET_POLICY_RATE,
            SOURCE_ORGANIZATION,
            ("data/manifests/sbp_policy_rate_structural_census.csv"),
            datetime.now(UTC).isoformat(),
            "STARTED",
            EXPECTED_NORMALIZED_ROWS,
            0,
            manifest_sha,
            (
                "Load the pre-sample policy-rate anchor "
                "and validated 2022-2026 SBP Policy "
                "(Target) Rate changes."
            ),
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
    """Mark one ingestion run successful."""

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
            EXPECTED_NORMALIZED_ROWS,
            written,
            (
                "Validated SBP policy-rate load complete; "
                f"inserted={written}; "
                f"existing_validated={existing}; "
                f"normalized_rows={EXPECTED_NORMALIZED_ROWS}; "
                f"in_sample_changes={EXPECTED_IN_SAMPLE_ROWS}; "
                f"structural_source_rows={EXPECTED_SOURCE_ROWS}; "
                f"anchor={ANCHOR_DATE}."
            ),
            run_id,
        ),
    )


def mark_run_failed(
    connection: object,
    run_id: int,
    message: str,
) -> None:
    """Persist loader failure without retaining partial writes."""

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
            EXPECTED_NORMALIZED_ROWS,
            ("SBP policy-rate load failed: " + message[:500]),
            run_id,
        ),
    )

    connection.commit()


def validate_final_state(
    connection: object,
    normalized: list[dict[str, str]],
) -> None:
    """Reconcile the normalized policy-rate analytical state source."""

    database_rows = connection.execute(
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
        WHERE effective_date >= ?
          AND effective_date <= ?
        ORDER BY effective_date
        """,
        (
            ANCHOR_DATE,
            LAST_IN_SAMPLE_DATE,
        ),
    ).fetchall()

    assert len(database_rows) == EXPECTED_NORMALIZED_ROWS, (
        f"Unexpected normalized policy-rate row count: {len(database_rows)}"
    )

    source_by_date = {row["observation_date"]: row for row in normalized}

    assert {row["effective_date"] for row in database_rows} == set(source_by_date)

    for row in database_rows:
        validate_existing_row(
            row,
            source_by_date[row["effective_date"]],
        )


def load_policy_rate(
    database_path: Path,
    manifest_path: Path = MANIFEST_PATH,
) -> tuple[int, int, int]:
    """Load or validate the 18 normalized policy-rate observations."""

    source_rows = read_csv(manifest_path)

    normalized = validate_manifest(source_rows)

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

        for row in normalized:
            effective_date = row["observation_date"]

            existing = connection.execute(
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
                WHERE effective_date = ?
                """,
                (effective_date,),
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
                INSERT INTO policy_rate_observations (
                    effective_date,
                    rate_pct,
                    series_key,
                    observation_status,
                    observation_status_comment,
                    source_organization,
                    source_file,
                    ingestion_run_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    effective_date,
                    float(Decimal(row["observation_value"])),
                    EXPECTED_SERIES_KEY,
                    row["observation_status"],
                    (row["observation_status_comment"] or None),
                    SOURCE_ORGANIZATION,
                    row["raw_file_name"],
                    run_id,
                ),
            )

            inserted += 1

        validate_final_state(
            connection,
            normalized,
        )

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
    ) = load_policy_rate(
        database_path=args.database_path,
        manifest_path=args.manifest_path,
    )

    print("===== SBP POLICY RATE DATABASE LOAD =====")

    print(
        "Database:",
        args.database_path,
    )

    print(
        "Ingestion run:",
        run_id,
    )

    print(
        "Structural source rows:",
        EXPECTED_SOURCE_ROWS,
    )

    print(
        "Normalized rows:",
        EXPECTED_NORMALIZED_ROWS,
    )

    print(
        "Pre-sample anchors:",
        1,
    )

    print(
        "In-sample changes:",
        EXPECTED_IN_SAMPLE_ROWS,
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
    print("PASS: SBP policy-rate database load complete")


if __name__ == "__main__":
    main()
