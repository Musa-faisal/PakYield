"""Load validated long-form PKISRV observations into PakYield SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    DATASET_PKISRV,
    PKRV_PKISRV_COMMON_TENORS,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

NORMALIZED_PATH = PROJECT_ROOT / "data" / "interim" / "pkisrv_normalized_long.csv"

NORMALIZED_SOURCE_FILE = "data/interim/pkisrv_normalized_long.csv"

SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"

CURVE_TYPE = "PKISRV"

EXPECTED_SHA256 = "b581918c66e3d867f17d3f81672c665ab843196be7e2a5764189738c8d193b98"

EXPECTED_ROWS = 2015
EXPECTED_DATES = 403
EXPECTED_ABSENT_DATES = 4

FIRST_DATE = "2025-02-03"
LAST_DATE = "2026-09-30"

EXPECTED_TENORS = tuple(PKRV_PKISRV_COMMON_TENORS)

EXPECTED_TENOR_SET = set(EXPECTED_TENORS)

EXPECTED_ABSENT_DATE_SET = {
    "2025-03-07",
    "2025-08-20",
    "2026-03-18",
    "2026-03-27",
}

EXPECTED_HEADERS = [
    "observation_date",
    "tenor",
    "tenor_years",
    "yield_pct",
    "source_organization",
    "source_file",
    "structural_class",
    "source_layout",
    "source_value_field",
]

EXPECTED_YEAR_COUNTS = {
    "2025": 1120,
    "2026": 895,
}

EXPECTED_STRUCTURAL_ROW_COUNTS = {
    "COMPLETE_5": 2015,
}

EXPECTED_LAYOUT_COUNTS = {
    "CSV_PKISRV_RATES": 403,
}

EXPECTED_VALUE_FIELD_COUNTS = {
    "PKISRV Rates (Yields)": 403,
}

EXPECTED_TENOR_COUNTS = {tenor: EXPECTED_DATES for tenor in EXPECTED_TENORS}

EXPECTED_SENTINELS = {
    (
        "2025-02-03",
        "1M",
    ): Decimal("10.70"),
    (
        "2025-02-03",
        "6M",
    ): Decimal("17.71"),
    (
        "2025-02-14",
        "1Y",
    ): Decimal("10.95"),
    (
        "2025-03-04",
        "1M",
    ): Decimal("10.54"),
    (
        "2026-03-02",
        "1M",
    ): Decimal("7.76"),
    (
        "2026-04-02",
        "3M",
    ): Decimal("9.40"),
    (
        "2026-06-04",
        "6M",
    ): Decimal("10.94"),
    (
        "2026-06-18",
        "1M",
    ): Decimal("11.83"),
    (
        "2026-09-25",
        "9M",
    ): Decimal("12.55"),
}


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


def read_normalized_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read the deterministic PKISRV long-form artifact."""

    if not path.is_file():
        raise FileNotFoundError(f"Normalized PKISRV artifact does not exist: {path}")

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


def parse_decimal(
    value: str,
    *,
    context: str,
) -> Decimal:
    """Parse one finite decimal value."""

    try:
        result = Decimal(value)

    except InvalidOperation as exc:
        raise RuntimeError(f"Invalid decimal {value!r}: {context}") from exc

    if not result.is_finite():
        raise RuntimeError(f"Non-finite decimal {value!r}: {context}")

    return result


def validate_normalized_artifact(
    path: Path,
) -> list[dict[str, str]]:
    """Validate the complete frozen PKISRV long-form source."""

    actual_sha = sha256_file(path)

    if actual_sha != EXPECTED_SHA256:
        raise RuntimeError(
            f"Normalized PKISRV SHA-256 mismatch: {actual_sha} != {EXPECTED_SHA256}"
        )

    (
        headers,
        rows,
    ) = read_normalized_csv(path)

    if headers != EXPECTED_HEADERS:
        raise RuntimeError(f"Unexpected normalized PKISRV header: {headers!r}")

    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(
            f"Unexpected normalized PKISRV row count: {len(rows)} != {EXPECTED_ROWS}"
        )

    keys: set[
        tuple[
            str,
            str,
        ]
    ] = set()

    dates: set[str] = set()

    date_counts: Counter[str] = Counter()

    tenor_counts: Counter[str] = Counter()

    year_counts: Counter[str] = Counter()

    structural_counts: Counter[str] = Counter()

    date_contract: dict[
        str,
        tuple[
            str,
            str,
        ],
    ] = {}

    source_contract: dict[
        str,
        tuple[
            str,
            str,
            str,
            str,
        ],
    ] = {}

    by_key: dict[
        tuple[
            str,
            str,
        ],
        Decimal,
    ] = {}

    for row in rows:
        observation_date = row["observation_date"]

        tenor = row["tenor"]

        key = (
            observation_date,
            tenor,
        )

        if key in keys:
            raise RuntimeError(f"Duplicate normalized PKISRV key: {key}")

        keys.add(key)

        dates.add(observation_date)

        if tenor not in EXPECTED_TENOR_SET:
            raise RuntimeError(f"Unexpected normalized PKISRV tenor: {tenor}")

        tenor_years = float(row["tenor_years"])

        expected_years = TENOR_TO_YEARS[tenor]

        if not math.isclose(
            tenor_years,
            expected_years,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(
                "Unexpected tenor_years for "
                f"{observation_date} "
                f"{tenor}: "
                f"{tenor_years} "
                f"!= {expected_years}"
            )

        yield_pct = parse_decimal(
            row["yield_pct"],
            context=(f"{observation_date} {tenor}"),
        )

        if not (Decimal("0") < yield_pct < Decimal("100")):
            raise RuntimeError(
                "Implausible normalized PKISRV yield for "
                f"{observation_date} "
                f"{tenor}: "
                f"{yield_pct}"
            )

        if row["source_organization"] != SOURCE_ORGANIZATION:
            raise RuntimeError(
                f"Unexpected PKISRV source organization for {observation_date} {tenor}"
            )

        source_file = row["source_file"]

        if not source_file:
            raise RuntimeError(
                f"Missing PKISRV source file for {observation_date} {tenor}"
            )

        structural_class = row["structural_class"]

        if structural_class != "COMPLETE_5":
            raise RuntimeError(
                f"Unexpected PKISRV structural class: {structural_class}"
            )

        source_layout = row["source_layout"]

        if source_layout != "CSV_PKISRV_RATES":
            raise RuntimeError(f"Unexpected PKISRV source layout: {source_layout!r}")

        source_value_field = row["source_value_field"]

        if source_value_field != "PKISRV Rates (Yields)":
            raise RuntimeError(
                f"Unexpected PKISRV source value field: {source_value_field!r}"
            )

        current_date_contract = (
            source_file,
            structural_class,
        )

        previous_date_contract = date_contract.get(observation_date)

        if (
            previous_date_contract is not None
            and previous_date_contract != current_date_contract
        ):
            raise RuntimeError(
                f"Inconsistent PKISRV source contract within date {observation_date}"
            )

        date_contract[observation_date] = current_date_contract

        current_source_contract = (
            observation_date,
            structural_class,
            source_layout,
            source_value_field,
        )

        previous_source_contract = source_contract.get(source_file)

        if (
            previous_source_contract is not None
            and previous_source_contract != current_source_contract
        ):
            raise RuntimeError(
                f"Inconsistent PKISRV source-file contract: {source_file}"
            )

        source_contract[source_file] = current_source_contract

        date_counts[observation_date] += 1

        tenor_counts[tenor] += 1

        year_counts[observation_date[:4]] += 1

        structural_counts[structural_class] += 1

        by_key[key] = yield_pct

    if len(keys) != EXPECTED_ROWS:
        raise RuntimeError("Unexpected unique PKISRV key count")

    if len(dates) != EXPECTED_DATES:
        raise RuntimeError(f"Unexpected PKISRV date count: {len(dates)}")

    if min(dates) != FIRST_DATE:
        raise RuntimeError(f"Unexpected first PKISRV date: {min(dates)}")

    if max(dates) != LAST_DATE:
        raise RuntimeError(f"Unexpected final PKISRV date: {max(dates)}")

    count_distribution = Counter(date_counts.values())

    if dict(count_distribution) != {
        5: EXPECTED_DATES,
    }:
        raise RuntimeError(
            f"Unexpected PKISRV per-date row distribution: {dict(count_distribution)}"
        )

    if dict(year_counts) != EXPECTED_YEAR_COUNTS:
        raise RuntimeError(f"Unexpected PKISRV rows by year: {dict(year_counts)}")

    if dict(structural_counts) != EXPECTED_STRUCTURAL_ROW_COUNTS:
        raise RuntimeError(
            f"Unexpected PKISRV structural row counts: {dict(structural_counts)}"
        )

    if dict(tenor_counts) != EXPECTED_TENOR_COUNTS:
        raise RuntimeError(f"Unexpected PKISRV tenor counts: {dict(tenor_counts)}")

    if len(source_contract) != EXPECTED_DATES:
        raise RuntimeError(
            f"Unexpected PKISRV source-file count: {len(source_contract)}"
        )

    layout_counts = Counter(contract[2] for contract in source_contract.values())

    if dict(layout_counts) != EXPECTED_LAYOUT_COUNTS:
        raise RuntimeError(
            f"Unexpected PKISRV source-layout counts: {dict(layout_counts)}"
        )

    value_field_counts = Counter(contract[3] for contract in source_contract.values())

    if dict(value_field_counts) != EXPECTED_VALUE_FIELD_COUNTS:
        raise RuntimeError(
            f"Unexpected PKISRV source-value-field counts: {dict(value_field_counts)}"
        )

    for observation_date in date_contract:
        if date_counts[observation_date] != 5:
            raise RuntimeError(
                f"COMPLETE_5 class disagrees with row count: {observation_date}"
            )

    for (
        key,
        expected,
    ) in EXPECTED_SENTINELS.items():
        actual = by_key.get(key)

        if actual != expected:
            raise RuntimeError(
                f"PKISRV normalized sentinel mismatch {key}: {actual} != {expected}"
            )

    for absent_date in EXPECTED_ABSENT_DATE_SET:
        if absent_date in dates:
            raise RuntimeError(
                "Source-level ABSENT PKISRV date "
                "appears in normalized artifact: "
                f"{absent_date}"
            )

    return rows


def db_float_equal(
    actual: object,
    expected: float,
    *,
    tolerance: float = 1e-10,
) -> bool:
    """Compare one SQLite numeric value to a normalized float."""

    return math.isclose(
        float(actual),
        expected,
        rel_tol=0.0,
        abs_tol=tolerance,
    )


def validate_existing_row(
    existing: object,
    source: dict[str, str],
) -> None:
    """Reject an existing PKISRV row when normalized semantics differ."""

    observation_date = source["observation_date"]

    tenor = source["tenor"]

    expected_tenor_years = float(source["tenor_years"])

    expected_yield = float(Decimal(source["yield_pct"]))

    conflicts: list[str] = []

    if existing["curve_type"] != CURVE_TYPE:
        conflicts.append(f"curve_type {existing['curve_type']!r} != {CURVE_TYPE!r}")

    if not db_float_equal(
        existing["tenor_years"],
        expected_tenor_years,
    ):
        conflicts.append(
            f"tenor_years {existing['tenor_years']} != {expected_tenor_years}"
        )

    if not db_float_equal(
        existing["yield_pct"],
        expected_yield,
    ):
        conflicts.append(f"yield_pct {existing['yield_pct']} != {expected_yield}")

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
            "Conflicting existing PKISRV row for "
            f"{observation_date} "
            f"{tenor}: " + "; ".join(conflicts)
        )


def start_ingestion_run(
    connection: object,
    artifact_sha: str,
) -> int:
    """Create and commit one STARTED PKISRV ingestion run."""

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
            DATASET_PKISRV,
            SOURCE_ORGANIZATION,
            NORMALIZED_SOURCE_FILE,
            datetime.now(UTC).isoformat(),
            "STARTED",
            EXPECTED_ROWS,
            0,
            artifact_sha,
            (
                "Load frozen deterministic PKISRV "
                "long-form normalization artifact; "
                "403 COMPLETE_5 dates; "
                "4 source-level ABSENT dates excluded; "
                "five standardized tenors; "
                "no interpolation or recovery."
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
    inserted: int,
    existing: int,
) -> None:
    """Mark one PKISRV ingestion run successful."""

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
            inserted,
            (
                "Validated PKISRV database load complete; "
                f"inserted={inserted}; "
                f"existing_validated={existing}; "
                f"normalized_rows={EXPECTED_ROWS}; "
                f"dates={EXPECTED_DATES}; "
                f"complete_5={EXPECTED_DATES}; "
                f"source_absent={EXPECTED_ABSENT_DATES}; "
                "interpolation=0; recovery=0."
            ),
            run_id,
        ),
    )


def mark_run_failed(
    connection: object,
    run_id: int,
    message: str,
) -> None:
    """Persist loader failure without retaining partial PKISRV writes."""

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
            ("PKISRV database load failed: " + message[:500]),
            run_id,
        ),
    )

    connection.commit()


def validate_final_state(
    connection: object,
    source_rows: list[dict[str, str]],
) -> None:
    """Reconcile every normalized PKISRV row against SQLite."""

    database_rows = connection.execute(
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
            WHERE curve_type = 'PKISRV'
            ORDER BY
                observation_date,
                tenor_years,
                tenor
            """
    ).fetchall()

    if len(database_rows) != EXPECTED_ROWS:
        raise RuntimeError(
            f"Unexpected final PKISRV database row count: {len(database_rows)}"
        )

    source_by_key = {
        (
            row["observation_date"],
            row["tenor"],
        ): row
        for row in source_rows
    }

    database_keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in database_rows
    }

    if database_keys != set(source_by_key):
        raise RuntimeError(
            "Final PKISRV database keys do not match normalized source keys"
        )

    for row in database_rows:
        key = (
            row["observation_date"],
            row["tenor"],
        )

        validate_existing_row(
            row,
            source_by_key[key],
        )


def load_pkisrv(
    database_path: Path,
    normalized_path: Path = NORMALIZED_PATH,
) -> tuple[
    int,
    int,
    int,
]:
    """Load or validate all 2,015 normalized PKISRV observations."""

    source_rows = validate_normalized_artifact(normalized_path)

    artifact_sha = sha256_file(normalized_path)

    initialize_database(database_path=database_path)

    connection = get_connection(database_path)

    run_id = start_ingestion_run(
        connection,
        artifact_sha,
    )

    inserted = 0
    existing_validated = 0

    try:
        connection.execute("BEGIN")

        for row in source_rows:
            observation_date = row["observation_date"]

            tenor = row["tenor"]

            existing = connection.execute(
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
                    WHERE observation_date = ?
                      AND curve_type = ?
                      AND tenor = ?
                    """,
                (
                    observation_date,
                    CURVE_TYPE,
                    tenor,
                ),
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
                INSERT INTO yield_observations (
                    observation_date,
                    curve_type,
                    tenor,
                    tenor_years,
                    yield_pct,
                    source_organization,
                    source_file,
                    ingestion_run_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_date,
                    CURVE_TYPE,
                    tenor,
                    float(row["tenor_years"]),
                    float(Decimal(row["yield_pct"])),
                    SOURCE_ORGANIZATION,
                    row["source_file"],
                    run_id,
                ),
            )

            inserted += 1

        validate_final_state(
            connection,
            source_rows,
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
        "--normalized-path",
        type=Path,
        default=NORMALIZED_PATH,
    )

    args = parser.parse_args()

    (
        run_id,
        inserted,
        existing,
    ) = load_pkisrv(
        database_path=(args.database_path),
        normalized_path=(args.normalized_path),
    )

    print("===== PKISRV DATABASE LOAD =====")

    print(
        "Database:",
        args.database_path,
    )

    print(
        "Normalized artifact:",
        args.normalized_path,
    )

    print(
        "Ingestion run:",
        run_id,
    )

    print(
        "Normalized rows:",
        EXPECTED_ROWS,
    )

    print(
        "Accepted COMPLETE_5 dates:",
        EXPECTED_DATES,
    )

    print(
        "Source-level ABSENT dates:",
        EXPECTED_ABSENT_DATES,
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

    print("PASS: PKISRV database load complete")


if __name__ == "__main__":
    main()
