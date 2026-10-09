"""Build deterministic MPC announcement-window sovereign-yield panel."""

from __future__ import annotations

import csv
import hashlib
import math
from bisect import bisect_left, bisect_right
from collections import Counter
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    MPC_EVENT_HALF_WINDOWS,
    MPC_EVENT_TYPES,
    MPC_LONGER_END_TENORS,
    MPC_SHORT_END_TENORS,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import get_connection

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "mpc_event_window_panel.csv"

EXPECTED_EVENTS = 39
EXPECTED_YIELD_ROWS = 24815

EXPECTED_DECISION_COUNTS = {
    "HOLD": 22,
    "HIKE": 9,
    "CUT": 8,
}

EXPECTED_HALF_WINDOWS = (1, 3, 5)

PKRV_TENORS = tuple(MPC_SHORT_END_TENORS) + tuple(MPC_LONGER_END_TENORS)
PKISRV_TENORS = tuple(MPC_SHORT_END_TENORS)

CURVE_TENORS = {
    "PKRV": PKRV_TENORS,
    "PKISRV": PKISRV_TENORS,
}

EXPECTED_TOTAL_ROWS = 936
EXPECTED_PKRV_ROWS = 585
EXPECTED_PKISRV_ROWS = 351
EXPECTED_ELIGIBLE_ROWS = 688
EXPECTED_INELIGIBLE_ROWS = 248

EXPECTED_INELIGIBLE_REASONS = {
    "INSUFFICIENT_LEFT_CURVE_HISTORY": 234,
    "MISSING_TENOR_BOTH_ENDPOINTS": 12,
    "MISSING_TENOR_RIGHT_ENDPOINT": 2,
}

ENDPOINT_METHOD = "H_TH_AVAILABLE_CURVE_OBSERVATION_STRICTLY_AROUND_EVENT_DATE"

YIELD_SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"
MPC_SOURCE_ORGANIZATION = "State Bank of Pakistan"

OUTPUT_FIELDS = [
    "event_date",
    "decision_type",
    "policy_change_bps",
    "previous_rate_pct",
    "announced_rate_pct",
    "effective_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "half_window",
    "event_same_day_curve_observation",
    "left_observation_date",
    "right_observation_date",
    "left_yield_pct",
    "right_yield_pct",
    "window_change_bps",
    "eligibility_status",
    "ineligibility_reason",
    "endpoint_method",
    "left_source_organization",
    "left_source_file",
    "left_ingestion_run_id",
    "right_source_organization",
    "right_source_file",
    "right_ingestion_run_id",
    "mpc_source_organization",
    "mpc_ingestion_run_id",
]


def decimal_text(value: Decimal) -> str:
    """Render a finite Decimal without meaningless trailing zeros."""

    if not value.is_finite():
        raise RuntimeError(f"Non-finite decimal encountered: {value}")

    text = format(value, "f")

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    if text == "-0":
        return "0"

    return text


def optional_decimal_text(value: object) -> str:
    """Render SQLite numeric value or blank when source is NULL."""

    if value is None:
        return ""

    return decimal_text(Decimal(str(value)))


def sha256_file(path: Path) -> str:
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def load_normalized_inputs() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Load and validate frozen MPC events and normalized sovereign yields."""

    if tuple(MPC_EVENT_HALF_WINDOWS) != EXPECTED_HALF_WINDOWS:
        raise RuntimeError(
            f"Configured MPC half-windows changed: {MPC_EVENT_HALF_WINDOWS}"
        )

    if tuple(MPC_EVENT_TYPES) != ("HIKE", "CUT", "HOLD"):
        raise RuntimeError(f"Configured MPC event types changed: {MPC_EVENT_TYPES}")

    connection = get_connection(DATABASE_PATH)

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

        event_rows = connection.execute(
            """
            SELECT
                event_date,
                decision_type,
                previous_rate_pct,
                announced_rate_pct,
                change_bps,
                effective_date,
                source_organization,
                ingestion_run_id
            FROM mpc_events
            ORDER BY event_date
            """
        ).fetchall()

        yield_rows = connection.execute(
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
            WHERE curve_type IN ('PKRV', 'PKISRV')
            ORDER BY
                observation_date,
                curve_type,
                tenor_years,
                tenor
            """
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError(f"Production SQLite integrity check failed: {integrity}")

    if foreign_key_issues:
        raise RuntimeError(
            f"Production SQLite foreign-key issues: {len(foreign_key_issues)}"
        )

    if len(event_rows) != EXPECTED_EVENTS:
        raise RuntimeError(f"Unexpected MPC event count: {len(event_rows)}")

    if len(yield_rows) != EXPECTED_YIELD_ROWS:
        raise RuntimeError(f"Unexpected normalized yield count: {len(yield_rows)}")

    events: list[dict[str, object]] = []

    for row in event_rows:
        if row["source_organization"] != MPC_SOURCE_ORGANIZATION:
            raise RuntimeError(
                f"Unexpected MPC source organization: {row['event_date']}"
            )

        if row["ingestion_run_id"] is None:
            raise RuntimeError(f"Missing MPC ingestion lineage: {row['event_date']}")

        events.append(dict(row))

    decision_counts = Counter(str(row["decision_type"]) for row in events)

    if dict(decision_counts) != EXPECTED_DECISION_COUNTS:
        raise RuntimeError(f"Unexpected MPC decision counts: {dict(decision_counts)}")

    yields: list[dict[str, object]] = []
    seen_yield_keys: set[tuple[str, str, str]] = set()

    for row in yield_rows:
        key = (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        )

        if key in seen_yield_keys:
            raise RuntimeError(f"Duplicate normalized yield key: {key}")

        seen_yield_keys.add(key)

        if row["source_organization"] != YIELD_SOURCE_ORGANIZATION:
            raise RuntimeError(f"Unexpected yield source organization: {key}")

        if not row["source_file"]:
            raise RuntimeError(f"Missing yield source file: {key}")

        if row["ingestion_run_id"] is None:
            raise RuntimeError(f"Missing yield ingestion lineage: {key}")

        tenor = row["tenor"]

        if tenor not in TENOR_TO_YEARS:
            raise RuntimeError(f"Unknown normalized tenor: {tenor}")

        if not math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[tenor],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(f"Unexpected tenor_years: {key}")

        yield_pct = Decimal(str(row["yield_pct"]))

        if not yield_pct.is_finite():
            raise RuntimeError(f"Non-finite yield: {key}")

        yields.append(
            {
                **dict(row),
                "yield_pct_decimal": yield_pct,
            }
        )

    return events, yields


def build_indexes(
    yields: list[dict[str, object]],
) -> tuple[
    dict[str, list[str]],
    dict[tuple[str, str, str], dict[str, object]],
]:
    """Build curve-date and exact curve/date/tenor lookup indexes."""

    dates_by_curve: dict[str, set[str]] = {
        "PKRV": set(),
        "PKISRV": set(),
    }

    observations: dict[
        tuple[str, str, str],
        dict[str, object],
    ] = {}

    for row in yields:
        curve = str(row["curve_type"])
        observation_date = str(row["observation_date"])
        tenor = str(row["tenor"])

        if curve not in dates_by_curve:
            raise RuntimeError(f"Unexpected curve type: {curve}")

        dates_by_curve[curve].add(observation_date)

        key = (
            curve,
            observation_date,
            tenor,
        )

        if key in observations:
            raise RuntimeError(f"Duplicate indexed yield key: {key}")

        observations[key] = row

    sorted_dates = {curve: sorted(dates) for curve, dates in dates_by_curve.items()}

    if len(sorted_dates["PKRV"]) != 1149:
        raise RuntimeError(f"Unexpected PKRV date count: {len(sorted_dates['PKRV'])}")

    if len(sorted_dates["PKISRV"]) != 403:
        raise RuntimeError(
            f"Unexpected PKISRV date count: {len(sorted_dates['PKISRV'])}"
        )

    return sorted_dates, observations


def endpoint_dates(
    dates: list[str],
    event_date: str,
    half_window: int,
) -> tuple[str | None, str | None]:
    """Select h-th observed curve dates strictly before and after one event."""

    left_index = bisect_left(dates, event_date)
    right_index = bisect_right(dates, event_date)

    left = dates[left_index - half_window] if left_index >= half_window else None

    right_position = right_index + half_window - 1

    right = dates[right_position] if right_position < len(dates) else None

    return left, right


def endpoint_fields(
    observation: dict[str, object] | None,
    prefix: str,
) -> dict[str, str]:
    """Return one endpoint's value and lineage fields."""

    if observation is None:
        return {
            f"{prefix}_yield_pct": "",
            f"{prefix}_source_organization": "",
            f"{prefix}_source_file": "",
            f"{prefix}_ingestion_run_id": "",
        }

    return {
        f"{prefix}_yield_pct": decimal_text(observation["yield_pct_decimal"]),
        f"{prefix}_source_organization": str(observation["source_organization"]),
        f"{prefix}_source_file": str(observation["source_file"]),
        f"{prefix}_ingestion_run_id": str(observation["ingestion_run_id"]),
    }


def derive_panel(
    events: list[dict[str, object]],
    dates_by_curve: dict[str, list[str]],
    observations: dict[
        tuple[str, str, str],
        dict[str, object],
    ],
) -> list[dict[str, str]]:
    """Derive complete explicit event × curve × tenor × window universe."""

    output: list[dict[str, str]] = []

    event_dates = {str(event["event_date"]) for event in events}

    audited_curve_windows: set[tuple[str, str, int]] = set()

    for event in events:
        event_date = str(event["event_date"])

        for curve in (
            "PKRV",
            "PKISRV",
        ):
            curve_dates = dates_by_curve[curve]
            curve_date_set = set(curve_dates)

            same_day = event_date in curve_date_set

            for half_window in EXPECTED_HALF_WINDOWS:
                left_date, right_date = endpoint_dates(
                    curve_dates,
                    event_date,
                    half_window,
                )

                if left_date is not None and right_date is not None:
                    audit_key = (
                        event_date,
                        curve,
                        half_window,
                    )

                    if audit_key not in audited_curve_windows:
                        other_events = {
                            candidate
                            for candidate in event_dates
                            if (
                                candidate != event_date
                                and left_date <= candidate <= right_date
                            )
                        }

                        if other_events:
                            raise RuntimeError(
                                "Event window contains another MPC event: "
                                f"{audit_key} {sorted(other_events)}"
                            )

                        audited_curve_windows.add(audit_key)

                for tenor in CURVE_TENORS[curve]:
                    left_observation = (
                        observations.get(
                            (
                                curve,
                                left_date,
                                tenor,
                            )
                        )
                        if left_date is not None
                        else None
                    )

                    right_observation = (
                        observations.get(
                            (
                                curve,
                                right_date,
                                tenor,
                            )
                        )
                        if right_date is not None
                        else None
                    )

                    if left_date is None:
                        status = "INELIGIBLE"
                        reason = "INSUFFICIENT_LEFT_CURVE_HISTORY"

                    elif right_date is None:
                        status = "INELIGIBLE"
                        reason = "INSUFFICIENT_RIGHT_CURVE_HISTORY"

                    elif left_observation is None and right_observation is None:
                        status = "INELIGIBLE"
                        reason = "MISSING_TENOR_BOTH_ENDPOINTS"

                    elif left_observation is None:
                        status = "INELIGIBLE"
                        reason = "MISSING_TENOR_LEFT_ENDPOINT"

                    elif right_observation is None:
                        status = "INELIGIBLE"
                        reason = "MISSING_TENOR_RIGHT_ENDPOINT"

                    else:
                        status = "ELIGIBLE"
                        reason = ""

                    if status == "ELIGIBLE":
                        left_yield = left_observation["yield_pct_decimal"]
                        right_yield = right_observation["yield_pct_decimal"]

                        change_bps = (right_yield - left_yield) * Decimal("100")

                        change_text = decimal_text(change_bps)

                    else:
                        change_text = ""

                    row = {
                        "event_date": event_date,
                        "decision_type": str(event["decision_type"]),
                        "policy_change_bps": str(event["change_bps"]),
                        "previous_rate_pct": optional_decimal_text(
                            event["previous_rate_pct"]
                        ),
                        "announced_rate_pct": optional_decimal_text(
                            event["announced_rate_pct"]
                        ),
                        "effective_date": (
                            str(event["effective_date"])
                            if event["effective_date"] is not None
                            else ""
                        ),
                        "curve_type": curve,
                        "tenor": tenor,
                        "tenor_years": format(
                            TENOR_TO_YEARS[tenor],
                            ".12g",
                        ),
                        "half_window": str(half_window),
                        "event_same_day_curve_observation": ("1" if same_day else "0"),
                        "left_observation_date": left_date or "",
                        "right_observation_date": right_date or "",
                        "window_change_bps": change_text,
                        "eligibility_status": status,
                        "ineligibility_reason": reason,
                        "endpoint_method": ENDPOINT_METHOD,
                        "mpc_source_organization": str(event["source_organization"]),
                        "mpc_ingestion_run_id": str(event["ingestion_run_id"]),
                    }

                    row.update(
                        endpoint_fields(
                            left_observation,
                            "left",
                        )
                    )

                    row.update(
                        endpoint_fields(
                            right_observation,
                            "right",
                        )
                    )

                    output.append(row)

    return output


def validate_panel(rows: list[dict[str, str]]) -> None:
    """Validate complete deterministic event-window artifact contract."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected event-window row count: {len(rows)}")

    keys = {
        (
            row["event_date"],
            row["curve_type"],
            row["tenor"],
            row["half_window"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate event-window analytical keys detected")

    curve_counts = Counter(row["curve_type"] for row in rows)

    if dict(curve_counts) != {
        "PKRV": EXPECTED_PKRV_ROWS,
        "PKISRV": EXPECTED_PKISRV_ROWS,
    }:
        raise RuntimeError(f"Unexpected curve row counts: {dict(curve_counts)}")

    status_counts = Counter(row["eligibility_status"] for row in rows)

    if dict(status_counts) != {
        "ELIGIBLE": EXPECTED_ELIGIBLE_ROWS,
        "INELIGIBLE": EXPECTED_INELIGIBLE_ROWS,
    }:
        raise RuntimeError(f"Unexpected eligibility counts: {dict(status_counts)}")

    reason_counts = Counter(
        row["ineligibility_reason"]
        for row in rows
        if row["eligibility_status"] == "INELIGIBLE"
    )

    if dict(reason_counts) != EXPECTED_INELIGIBLE_REASONS:
        raise RuntimeError(f"Unexpected ineligibility reasons: {dict(reason_counts)}")

    for row in rows:
        if row["curve_type"] == "PKISRV" and row["tenor"] in {
            "5Y",
            "10Y",
        }:
            raise RuntimeError(
                "Structurally unavailable PKISRV long tenor was manufactured"
            )

        if row["endpoint_method"] != ENDPOINT_METHOD:
            raise RuntimeError("Unexpected endpoint method")

        if row["eligibility_status"] == "ELIGIBLE":
            required = (
                "left_observation_date",
                "right_observation_date",
                "left_yield_pct",
                "right_yield_pct",
                "window_change_bps",
                "left_source_file",
                "right_source_file",
                "left_ingestion_run_id",
                "right_ingestion_run_id",
            )

            if any(not row[field] for field in required):
                raise RuntimeError(
                    "Eligible event-window row has missing required fields"
                )

            expected_change = (
                Decimal(row["right_yield_pct"]) - Decimal(row["left_yield_pct"])
            ) * Decimal("100")

            if Decimal(row["window_change_bps"]) != expected_change:
                raise RuntimeError("Eligible event-window basis-point change mismatch")

        else:
            if row["window_change_bps"] != "":
                raise RuntimeError(
                    "Ineligible event-window row contains manufactured change"
                )

    sentinel = {
        (
            row["half_window"],
            row["tenor"],
        ): row
        for row in rows
        if (row["event_date"] == "2024-06-10" and row["curve_type"] == "PKRV")
    }

    expected_sentinel_dates = {
        "1": (
            "2024-06-07",
            "2024-06-11",
        ),
        "3": (
            "2024-06-05",
            "2024-06-13",
        ),
        "5": (
            "2024-05-31",
            "2024-06-20",
        ),
    }

    for half_window, dates in expected_sentinel_dates.items():
        for tenor in PKRV_TENORS:
            row = sentinel[
                (
                    half_window,
                    tenor,
                )
            ]

            if (
                row["left_observation_date"],
                row["right_observation_date"],
            ) != dates:
                raise RuntimeError("2024-06-10 PKRV endpoint sentinel changed")

            if row["eligibility_status"] != "ELIGIBLE":
                raise RuntimeError("2024-06-10 PKRV tenor unexpectedly ineligible")


def main() -> None:
    """Build deterministic MPC event-window analytical panel."""

    events, yields = load_normalized_inputs()

    dates_by_curve, observations = build_indexes(yields)

    rows = derive_panel(
        events,
        dates_by_curve,
        observations,
    )

    validate_panel(rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(OUTPUT_PATH)

    status_counts = Counter(row["eligibility_status"] for row in rows)

    reason_counts = Counter(
        row["ineligibility_reason"]
        for row in rows
        if row["eligibility_status"] == "INELIGIBLE"
    )

    curve_counts = Counter(row["curve_type"] for row in rows)

    print("===== MPC EVENT-WINDOW PANEL =====")
    print("MPC events:", len(events))
    print("Rows:", len(rows))
    print("PKRV rows:", curve_counts["PKRV"])
    print("PKISRV rows:", curve_counts["PKISRV"])
    print("Eligible rows:", status_counts["ELIGIBLE"])
    print("Ineligible rows:", status_counts["INELIGIBLE"])

    print("")
    print("Ineligibility reasons:")

    for reason in sorted(reason_counts):
        print(" ", reason, reason_counts[reason])

    print("")
    try:
        output_display = OUTPUT_PATH.relative_to(PROJECT_ROOT)
    except ValueError:
        output_display = OUTPUT_PATH

    print(
        "Output:",
        output_display,
    )
    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print(
        "PASS: deterministic MPC event-window observation-position contract satisfied"
    )


if __name__ == "__main__":
    main()
