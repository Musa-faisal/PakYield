"""Build deterministic monetary-policy directional-regime panel."""

from __future__ import annotations

import csv
import hashlib
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    PROJECT_ROOT,
)
from pakyield.database.connection import get_connection

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "monetary_policy_regime_panel.csv"

EXPECTED_MPC_EVENTS = 39

EXPECTED_CURVE_DATE_COUNTS = {
    "PKRV": 1149,
    "PKISRV": 403,
}

EXPECTED_TOTAL_ROWS = sum(EXPECTED_CURVE_DATE_COUNTS.values())

EVENT_TYPES = {
    "HIKE",
    "CUT",
    "HOLD",
}

REGIME_BY_DIRECTIONAL_EVENT = {
    "HIKE": "TIGHTENING",
    "CUT": "EASING",
}

ELIGIBLE = "ELIGIBLE"
INELIGIBLE = "INELIGIBLE"

PRE_DIRECTIONAL_HISTORY = "PRE_DIRECTIONAL_HISTORY"

MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP = "MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP"

CLASSIFICATION_METHOD = "LATEST_PRIOR_DIRECTIONAL_MPC_EVENT_STRICTLY_BEFORE_DATE"

OUTPUT_FIELDS = [
    "observation_date",
    "curve_type",
    "regime_label",
    "regime_analysis_status",
    "ineligibility_reason",
    "is_mpc_event_date",
    "same_day_mpc_event_type",
    "latest_prior_mpc_event_date",
    "latest_prior_mpc_event_type",
    "regime_origin_event_date",
    "regime_origin_event_type",
    "days_since_latest_prior_mpc_event",
    "days_since_regime_origin_event",
    "classification_method",
]


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


def load_inputs() -> tuple[
    list[dict[str, object]],
    list[tuple[str, str]],
]:
    """Load validated MPC events and normalized curve-date universe."""

    connection = get_connection(DATABASE_PATH)

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

        event_rows = connection.execute(
            """

            SELECT
                event_date,
                decision_type AS event_type
            FROM mpc_events
            ORDER BY event_date

            """
        ).fetchall()

        curve_date_rows = connection.execute(
            """
            SELECT DISTINCT
                curve_type,
                observation_date
            FROM yield_observations
            ORDER BY
                observation_date,
                curve_type
            """
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError(f"SQLite integrity failed: {integrity}")

    if foreign_key_issues:
        raise RuntimeError(f"SQLite foreign-key issues: {len(foreign_key_issues)}")

    if len(event_rows) != EXPECTED_MPC_EVENTS:
        raise RuntimeError(f"Unexpected MPC event count: {len(event_rows)}")

    events: list[dict[str, object]] = []

    seen_event_dates = set()

    previous_date: date | None = None

    for row in event_rows:
        event_date_text = row["event_date"]

        event_type = row["event_type"]

        if event_type not in EVENT_TYPES:
            raise RuntimeError(f"Unexpected MPC event type: {event_type}")

        event_date = date.fromisoformat(event_date_text)

        if event_date in seen_event_dates:
            raise RuntimeError(f"Duplicate MPC event date: {event_date}")

        if previous_date is not None and event_date <= previous_date:
            raise RuntimeError("MPC events not strictly increasing")

        seen_event_dates.add(event_date)

        previous_date = event_date

        events.append(
            {
                "event_date": event_date,
                "event_date_text": event_date_text,
                "event_type": event_type,
            }
        )

    curve_dates = [
        (
            row["curve_type"],
            row["observation_date"],
        )
        for row in curve_date_rows
    ]

    counts = Counter(
        curve
        for (
            curve,
            _observation_date,
        ) in curve_dates
    )

    if dict(counts) != (EXPECTED_CURVE_DATE_COUNTS):
        raise RuntimeError(f"Unexpected normalized curve-date census: {dict(counts)}")

    if len(curve_dates) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected total curve-date rows: {len(curve_dates)}")

    if len(set(curve_dates)) != len(curve_dates):
        raise RuntimeError("Duplicate normalized curve-date key")

    return (
        events,
        curve_dates,
    )


def derive_panel(
    events: list[dict[str, object]],
    curve_dates: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """Classify every normalized curve-date under D093."""

    event_dates = [event["event_date"] for event in events]

    event_by_date = {event["event_date"]: event for event in events}

    directional_events = [
        event for event in events if event["event_type"] in REGIME_BY_DIRECTIONAL_EVENT
    ]

    directional_dates = [event["event_date"] for event in directional_events]

    output: list[dict[str, str]] = []

    for (
        curve_type,
        observation_date_text,
    ) in curve_dates:
        observation_date = date.fromisoformat(observation_date_text)

        same_day_event = event_by_date.get(observation_date)

        prior_event_index = (
            bisect_left(
                event_dates,
                observation_date,
            )
            - 1
        )

        if prior_event_index >= 0:
            latest_prior_event = events[prior_event_index]
        else:
            latest_prior_event = None

        directional_index = (
            bisect_left(
                directional_dates,
                observation_date,
            )
            - 1
        )

        if directional_index >= 0:
            regime_origin = directional_events[directional_index]
        else:
            regime_origin = None

        if regime_origin is None:
            regime_label = "UNCLASSIFIED"
        else:
            regime_label = REGIME_BY_DIRECTIONAL_EVENT[str(regime_origin["event_type"])]

        if same_day_event is not None:
            status = INELIGIBLE
            reason = MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP

        elif regime_origin is None:
            status = INELIGIBLE
            reason = PRE_DIRECTIONAL_HISTORY

        else:
            status = ELIGIBLE
            reason = ""

        if latest_prior_event is None:
            latest_prior_date = ""
            latest_prior_type = ""
            days_since_latest = ""

        else:
            latest_prior_date = str(latest_prior_event["event_date_text"])

            latest_prior_type = str(latest_prior_event["event_type"])

            days_since_latest = str(
                (observation_date - latest_prior_event["event_date"]).days
            )

        if regime_origin is None:
            origin_date = ""
            origin_type = ""
            days_since_origin = ""

        else:
            origin_date = str(regime_origin["event_date_text"])

            origin_type = str(regime_origin["event_type"])

            days_since_origin = str(
                (observation_date - regime_origin["event_date"]).days
            )

        output.append(
            {
                "observation_date": (observation_date_text),
                "curve_type": curve_type,
                "regime_label": regime_label,
                "regime_analysis_status": (status),
                "ineligibility_reason": (reason),
                "is_mpc_event_date": ("1" if same_day_event is not None else "0"),
                "same_day_mpc_event_type": (
                    str(same_day_event["event_type"])
                    if same_day_event is not None
                    else ""
                ),
                "latest_prior_mpc_event_date": (latest_prior_date),
                "latest_prior_mpc_event_type": (latest_prior_type),
                "regime_origin_event_date": (origin_date),
                "regime_origin_event_type": (origin_type),
                "days_since_latest_prior_mpc_event": (days_since_latest),
                "days_since_regime_origin_event": (days_since_origin),
                "classification_method": (CLASSIFICATION_METHOD),
            }
        )

    return output


def validate_panel(
    rows: list[dict[str, str]],
) -> None:
    """Validate the complete D093 analytical contract."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected regime-panel rows: {len(rows)}")

    keys = {
        (
            row["curve_type"],
            row["observation_date"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate regime analytical keys")

    curve_counts = Counter(row["curve_type"] for row in rows)

    if dict(curve_counts) != (EXPECTED_CURVE_DATE_COUNTS):
        raise RuntimeError(f"Unexpected curve census: {dict(curve_counts)}")

    allowed_regimes = {
        "TIGHTENING",
        "EASING",
        "UNCLASSIFIED",
    }

    observed_regimes = {row["regime_label"] for row in rows}

    if not observed_regimes.issubset(allowed_regimes):
        raise RuntimeError(f"Unexpected regime labels: {observed_regimes}")

    if "HOLD" in observed_regimes:
        raise RuntimeError("HOLD cannot be a directional regime")

    allowed_statuses = {
        ELIGIBLE,
        INELIGIBLE,
    }

    if {row["regime_analysis_status"] for row in rows} - allowed_statuses:
        raise RuntimeError("Unexpected regime-analysis status")

    for row in rows:
        if row["classification_method"] != (CLASSIFICATION_METHOD):
            raise RuntimeError("Unexpected classification method")

        status = row["regime_analysis_status"]

        reason = row["ineligibility_reason"]

        same_day = row["is_mpc_event_date"] == "1"

        regime = row["regime_label"]

        origin_type = row["regime_origin_event_type"]

        if same_day:
            if status != INELIGIBLE:
                raise RuntimeError("MPC event date marked eligible")

            if reason != (MPC_EVENT_DATE_NO_INTRADAY_TIMESTAMP):
                raise RuntimeError("Wrong event-date ineligibility reason")

            if row["same_day_mpc_event_type"] not in EVENT_TYPES:
                raise RuntimeError("Missing same-day MPC event type")

        elif regime == "UNCLASSIFIED":
            if status != INELIGIBLE:
                raise RuntimeError("UNCLASSIFIED row marked eligible")

            if reason != (PRE_DIRECTIONAL_HISTORY):
                raise RuntimeError("Wrong pre-history reason")

        else:
            if status != ELIGIBLE:
                raise RuntimeError("Ordinary classified date marked ineligible")

            if reason:
                raise RuntimeError("Eligible regime row has reason")

        if regime == "TIGHTENING":
            if origin_type != "HIKE":
                raise RuntimeError("TIGHTENING without HIKE origin")

        elif regime == "EASING":
            if origin_type != "CUT":
                raise RuntimeError("EASING without CUT origin")

        elif regime == "UNCLASSIFIED":
            if origin_type:
                raise RuntimeError("UNCLASSIFIED row has directional origin")

        if (
            row["latest_prior_mpc_event_date"] >= row["observation_date"]
            and row["latest_prior_mpc_event_date"]
        ):
            raise RuntimeError("Latest prior MPC event is not strictly prior")

        if (
            row["regime_origin_event_date"] >= row["observation_date"]
            and row["regime_origin_event_date"]
        ):
            raise RuntimeError("Regime origin is not strictly prior")

    date_metadata = defaultdict(set)

    metadata_fields = (
        "regime_label",
        "regime_analysis_status",
        "ineligibility_reason",
        "is_mpc_event_date",
        "same_day_mpc_event_type",
        "latest_prior_mpc_event_date",
        "latest_prior_mpc_event_type",
        "regime_origin_event_date",
        "regime_origin_event_type",
        "days_since_latest_prior_mpc_event",
        "days_since_regime_origin_event",
        "classification_method",
    )

    for row in rows:
        date_metadata[row["observation_date"]].add(
            tuple(row[field] for field in metadata_fields)
        )

    inconsistent_dates = {
        observation_date: values
        for (
            observation_date,
            values,
        ) in date_metadata.items()
        if len(values) != 1
    }

    if inconsistent_dates:
        raise RuntimeError("Cross-curve regime metadata differs on identical dates")


def main() -> None:
    """Build deterministic monetary-policy regime panel."""

    (
        events,
        curve_dates,
    ) = load_inputs()

    rows = derive_panel(
        events,
        curve_dates,
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

    regimes = Counter(row["regime_label"] for row in rows)

    statuses = Counter(row["regime_analysis_status"] for row in rows)

    reasons = Counter(
        row["ineligibility_reason"]
        for row in rows
        if row["regime_analysis_status"] == INELIGIBLE
    )

    curves = Counter(row["curve_type"] for row in rows)

    event_date_rows = sum(row["is_mpc_event_date"] == "1" for row in rows)

    distinct_dates = {row["observation_date"] for row in rows}

    try:
        output_display = OUTPUT_PATH.relative_to(PROJECT_ROOT)
    except ValueError:
        output_display = OUTPUT_PATH

    print("===== MONETARY-POLICY REGIME PANEL =====")

    print(
        "MPC events:",
        len(events),
    )

    print(
        "Rows:",
        len(rows),
    )

    print(
        "Distinct calendar dates:",
        len(distinct_dates),
    )

    print(
        "Curves:",
        dict(curves),
    )

    print(
        "Regimes:",
        dict(regimes),
    )

    print(
        "Statuses:",
        dict(statuses),
    )

    print(
        "Ineligibility reasons:",
        dict(reasons),
    )

    print(
        "MPC-event-date curve rows:",
        event_date_rows,
    )

    print(
        "Output:",
        output_display,
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print("PASS: deterministic D093 regime panel constructed")


if __name__ == "__main__":
    main()
