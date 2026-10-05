"""Load validated SBP MPC events into PakYield SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    DATASET_MPC_EVENTS,
    PROJECT_ROOT,
)
from pakyield.database.connection import (
    get_connection,
    initialize_database,
)

DECISIONS_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_decisions_validated.csv"

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_acquisition_plan.csv"

CROSSCHECK_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_policy_rate_crosscheck.csv"
)

EXPECTED_EVENTS = 39
EXPECTED_CHANGES = 17
EXPECTED_EXPLICIT_EFFECTIVE_DATES = 10

FIRST_EVENT_DATE = "2022-01-24"
LAST_EVENT_DATE = "2026-09-14"

SPECIAL_RATE_NOT_STATED_DATE = "2025-12-15"

SOURCE_ORGANIZATION = "State Bank of Pakistan"

SOURCE_DIRECTION_COUNTS = {
    "HOLD": 22,
    "RAISE": 9,
    "CUT": 8,
}

DATABASE_DIRECTION_COUNTS = {
    "HOLD": 22,
    "HIKE": 9,
    "CUT": 8,
}

DIRECTION_MAP = {
    "HOLD": "HOLD",
    "RAISE": "HIKE",
    "CUT": "CUT",
}

EXPECTED_EFFECTIVE_DATES = {
    "2023-06-26": "2023-06-27",
    "2024-06-10": "2024-06-11",
    "2024-07-29": "2024-07-30",
    "2024-09-12": "2024-09-13",
    "2024-11-04": "2024-11-05",
    "2024-12-16": "2024-12-17",
    "2025-01-27": "2025-01-28",
    "2025-05-05": "2025-05-06",
    "2025-12-15": "2025-12-16",
    "2026-04-27": "2026-04-28",
}


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


def decimal_or_none(
    value: str,
) -> Decimal | None:
    """Convert a source numeric string or blank to Decimal/None."""

    stripped = value.strip()

    if not stripped:
        return None

    return Decimal(stripped)


def validate_source_manifests(
    decisions: list[dict[str, str]],
    plan: list[dict[str, str]],
    crosscheck: list[dict[str, str]],
) -> None:
    """Validate the frozen MPC normalization source envelope."""

    assert len(decisions) == EXPECTED_EVENTS
    assert len(plan) == EXPECTED_EVENTS
    assert len(crosscheck) == EXPECTED_CHANGES

    decision_dates = [row["event_date"] for row in decisions]

    plan_dates = [row["event_date"] for row in plan]

    assert len(set(decision_dates)) == EXPECTED_EVENTS
    assert len(set(plan_dates)) == EXPECTED_EVENTS

    assert decision_dates == sorted(decision_dates)
    assert plan_dates == decision_dates

    assert decision_dates[0] == FIRST_EVENT_DATE
    assert decision_dates[-1] == LAST_EVENT_DATE

    direction_counts = Counter(row["decision_direction"] for row in decisions)

    assert dict(direction_counts) == SOURCE_DIRECTION_COUNTS

    changed = [row for row in decisions if row["decision_direction"] != "HOLD"]

    assert len(changed) == EXPECTED_CHANGES

    plan_by_date = {row["event_date"]: row for row in plan}

    for row in decisions:
        event_date = row["event_date"]

        assert row["decision_direction"] in DIRECTION_MAP

        assert row["source_file"]

        assert row["decision_text"]

        assert row["validation_status"] in {
            "VALIDATED_EXPLICIT_RATE",
            "VALIDATED_CHANGE_ONLY_RATE_NOT_STATED",
        }

        change = Decimal(row["change_bps"])

        assert change == change.to_integral_value()

        if row["decision_direction"] == "HOLD":
            assert change == 0

        elif row["decision_direction"] == "RAISE":
            assert change > 0

        elif row["decision_direction"] == "CUT":
            assert change < 0

        plan_row = plan_by_date[event_date]

        assert plan_row["resolved_file_name"] == row["source_file"]

        assert plan_row["resolution_status"] == "RESOLVED"

        assert plan_row["statement_title"]
        assert plan_row["source_url"]

    missing_announced = [
        row["event_date"] for row in decisions if not row["announced_policy_rate"]
    ]

    assert missing_announced == [SPECIAL_RATE_NOT_STATED_DATE]

    special = {row["event_date"]: row for row in decisions}[
        SPECIAL_RATE_NOT_STATED_DATE
    ]

    assert special["decision_direction"] == "CUT"
    assert special["change_bps"] == "-50"
    assert special["effective_date"] == "2025-12-16"

    assert special["effective_date_source"] == "STATEMENT_EXPLICIT"

    assert special["validation_status"] == "VALIDATED_CHANGE_ONLY_RATE_NOT_STATED"

    actual_effective = {
        row["event_date"]: row["effective_date"]
        for row in decisions
        if row["effective_date"]
    }

    assert actual_effective == EXPECTED_EFFECTIVE_DATES
    assert len(actual_effective) == (EXPECTED_EXPLICIT_EFFECTIVE_DATES)

    for row in decisions:
        if row["event_date"] in EXPECTED_EFFECTIVE_DATES:
            assert row["effective_date_source"] == "STATEMENT_EXPLICIT"
        else:
            assert row["effective_date"] == ""

            assert row["effective_date_source"] == "NOT_STATED"

    changed_dates = {row["event_date"] for row in changed}

    crosscheck_dates = {row["event_date"] for row in crosscheck}

    assert crosscheck_dates == changed_dates

    assert all(row["crosscheck_status"] == "MATCH" for row in crosscheck)

    derived = [
        row
        for row in crosscheck
        if (row["statement_rate_basis"] == "SEQUENCE_DERIVED_FOR_VALIDATION_ONLY")
    ]

    assert len(derived) == 1

    assert derived[0]["event_date"] == SPECIAL_RATE_NOT_STATED_DATE

    assert derived[0]["statement_resulting_rate"] == "10.5"


def build_normalized_rows(
    decisions: list[dict[str, str]],
    plan: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Build SQLite-ready MPC events without inventing statement fields."""

    plan_by_date = {row["event_date"]: row for row in plan}

    normalized: list[dict[str, object]] = []

    current_rate: Decimal | None = None

    for index, source in enumerate(decisions):
        event_date = source["event_date"]

        source_direction = source["decision_direction"]

        decision_type = DIRECTION_MAP[source_direction]

        change_bps_decimal = Decimal(source["change_bps"])

        change_bps = int(change_bps_decimal)

        announced_rate = decimal_or_none(source["announced_policy_rate"])

        if index == 0:
            assert source_direction == "HOLD"
            assert announced_rate is not None
            assert change_bps == 0

            previous_rate = announced_rate
            resulting_rate = announced_rate

        else:
            assert current_rate is not None

            previous_rate = current_rate

            if source_direction == "HOLD":
                assert change_bps == 0
                assert announced_rate is not None
                assert announced_rate == previous_rate

                resulting_rate = previous_rate

            else:
                resulting_rate = previous_rate + (Decimal(change_bps) / Decimal("100"))

                if announced_rate is not None:
                    assert announced_rate == resulting_rate

                else:
                    assert event_date == SPECIAL_RATE_NOT_STATED_DATE

        if event_date == SPECIAL_RATE_NOT_STATED_DATE:
            assert announced_rate is None
            assert resulting_rate == Decimal("10.5")

        current_rate = resulting_rate

        plan_row = plan_by_date[event_date]

        effective_date = source["effective_date"] or None

        notes = (
            "source_file="
            f"{source['source_file']}; "
            "previous_rate_pct="
            "sequence-derived from validated MPC chronology; "
            "announced_rate_pct="
            "statement-explicit only; "
            "effective_date_basis="
            f"{source['effective_date_source']}; "
            "validation_status="
            f"{source['validation_status']}."
        )

        if event_date == SPECIAL_RATE_NOT_STATED_DATE:
            notes += (
                " Resulting 10.5 percent rate is used "
                "only for sequence continuity and "
                "policy-series validation; it is not "
                "stored as a statement-announced rate."
            )

        normalized.append(
            {
                "event_date": event_date,
                "decision_type": decision_type,
                "previous_rate_pct": previous_rate,
                "announced_rate_pct": announced_rate,
                "change_bps": change_bps,
                "effective_date": effective_date,
                "statement_title": plan_row["statement_title"],
                "statement_url": plan_row["source_url"],
                "notes": notes,
            }
        )

    assert len(normalized) == EXPECTED_EVENTS

    database_counts = Counter(row["decision_type"] for row in normalized)

    assert dict(database_counts) == (DATABASE_DIRECTION_COUNTS)

    assert current_rate == Decimal("11.5")

    return normalized


def db_decimal_or_none(
    value: object,
) -> Decimal | None:
    """Convert SQLite numeric value to comparison-safe Decimal/None."""

    if value is None:
        return None

    return Decimal(str(value))


def validate_existing_row(
    existing: object,
    source: dict[str, object],
) -> None:
    """Reject any conflicting normalized MPC event."""

    conflicts: list[str] = []

    text_fields = (
        "event_date",
        "decision_type",
        "effective_date",
        "statement_title",
        "statement_url",
        "source_organization",
        "notes",
    )

    expected_text = {
        "event_date": source["event_date"],
        "decision_type": source["decision_type"],
        "effective_date": source["effective_date"],
        "statement_title": source["statement_title"],
        "statement_url": source["statement_url"],
        "source_organization": SOURCE_ORGANIZATION,
        "notes": source["notes"],
    }

    for field in text_fields:
        if existing[field] != expected_text[field]:
            conflicts.append(f"{field} {existing[field]!r} != {expected_text[field]!r}")

    expected_previous = source["previous_rate_pct"]

    actual_previous = db_decimal_or_none(existing["previous_rate_pct"])

    if actual_previous != expected_previous:
        conflicts.append(f"previous_rate_pct {actual_previous} != {expected_previous}")

    expected_announced = source["announced_rate_pct"]

    actual_announced = db_decimal_or_none(existing["announced_rate_pct"])

    if actual_announced != expected_announced:
        conflicts.append(
            f"announced_rate_pct {actual_announced} != {expected_announced}"
        )

    if existing["change_bps"] != source["change_bps"]:
        conflicts.append(
            f"change_bps {existing['change_bps']} != {source['change_bps']}"
        )

    if conflicts:
        raise RuntimeError(
            "Conflicting existing SBP MPC row for "
            f"{source['event_date']}: " + "; ".join(conflicts)
        )


def start_ingestion_run(
    connection: object,
    manifest_sha: str,
) -> int:
    """Create and commit a STARTED ingestion run."""

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
            DATASET_MPC_EVENTS,
            SOURCE_ORGANIZATION,
            ("data/manifests/sbp_mpc_decisions_validated.csv"),
            datetime.now(UTC).isoformat(),
            "STARTED",
            EXPECTED_EVENTS,
            0,
            manifest_sha,
            (
                "Normalize validated SBP MPC decisions "
                "into mpc_events; statement metadata "
                "joined from sbp_mpc_acquisition_plan.csv."
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
    """Mark the MPC normalization run successful."""

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
            EXPECTED_EVENTS,
            inserted,
            (
                "Validated SBP MPC normalization complete; "
                f"inserted={inserted}; "
                f"existing_validated={existing}; "
                "events=39; HOLD=22; HIKE=9; CUT=8; "
                "statement_explicit_effective_dates=10."
            ),
            run_id,
        ),
    )


def mark_run_failed(
    connection: object,
    run_id: int,
    message: str,
) -> None:
    """Persist loader failure after rolling back event writes."""

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
            EXPECTED_EVENTS,
            ("SBP MPC normalization failed: " + message[:500]),
            run_id,
        ),
    )

    connection.commit()


def validate_final_state(
    connection: object,
    normalized: list[dict[str, object]],
) -> None:
    """Reconcile SQLite exactly to the 39 canonical MPC events."""

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

    assert len(rows) == EXPECTED_EVENTS, (
        f"Unexpected normalized MPC row count: {len(rows)}"
    )

    normalized_by_date = {str(row["event_date"]): row for row in normalized}

    assert {row["event_date"] for row in rows} == set(normalized_by_date)

    for row in rows:
        validate_existing_row(
            row,
            normalized_by_date[row["event_date"]],
        )


def load_mpc_events(
    database_path: Path,
    decisions_path: Path = DECISIONS_PATH,
    plan_path: Path = PLAN_PATH,
    crosscheck_path: Path = CROSSCHECK_PATH,
) -> tuple[int, int, int]:
    """Load or validate all 39 canonical SBP MPC events."""

    decisions = read_csv(decisions_path)

    plan = read_csv(plan_path)

    crosscheck = read_csv(crosscheck_path)

    validate_source_manifests(
        decisions,
        plan,
        crosscheck,
    )

    normalized = build_normalized_rows(
        decisions,
        plan,
    )

    manifest_sha = sha256_file(decisions_path)

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
            existing = connection.execute(
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
                WHERE event_date = ?
                """,
                (row["event_date"],),
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
                INSERT INTO mpc_events (
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["event_date"],
                    row["decision_type"],
                    float(row["previous_rate_pct"]),
                    (
                        float(row["announced_rate_pct"])
                        if row["announced_rate_pct"] is not None
                        else None
                    ),
                    row["change_bps"],
                    row["effective_date"],
                    row["statement_title"],
                    row["statement_url"],
                    SOURCE_ORGANIZATION,
                    run_id,
                    row["notes"],
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
        "--decisions-path",
        type=Path,
        default=DECISIONS_PATH,
    )

    parser.add_argument(
        "--plan-path",
        type=Path,
        default=PLAN_PATH,
    )

    parser.add_argument(
        "--crosscheck-path",
        type=Path,
        default=CROSSCHECK_PATH,
    )

    args = parser.parse_args()

    (
        run_id,
        inserted,
        existing,
    ) = load_mpc_events(
        database_path=args.database_path,
        decisions_path=args.decisions_path,
        plan_path=args.plan_path,
        crosscheck_path=args.crosscheck_path,
    )

    print("===== SBP MPC DATABASE LOAD =====")

    print(
        "Database:",
        args.database_path,
    )

    print(
        "Ingestion run:",
        run_id,
    )

    print(
        "Canonical events:",
        EXPECTED_EVENTS,
    )

    print(
        "HOLD:",
        DATABASE_DIRECTION_COUNTS["HOLD"],
    )

    print(
        "HIKE:",
        DATABASE_DIRECTION_COUNTS["HIKE"],
    )

    print(
        "CUT:",
        DATABASE_DIRECTION_COUNTS["CUT"],
    )

    print(
        "Explicit effective dates:",
        EXPECTED_EXPLICIT_EFFECTIVE_DATES,
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
    print("PASS: SBP MPC database load complete")


if __name__ == "__main__":
    main()
