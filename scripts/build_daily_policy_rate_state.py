"""Build deterministic calendar-daily SBP policy-rate state."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    PROJECT_ROOT,
)
from pakyield.database.connection import (
    get_connection,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "policy_rate_daily_state.csv"

EXPECTED_START_DATE = date(
    2022,
    1,
    4,
)

EXPECTED_END_DATE = date(
    2026,
    9,
    30,
)

EXPECTED_ROWS = 1731

EXPECTED_POLICY_OBSERVATIONS = 18

EXPECTED_IN_RANGE_EFFECTIVE_DATES = 17

EXPECTED_SOURCE_ORGANIZATION = "State Bank of Pakistan"

EXPECTED_SOURCE_FILE = "data_series.csv"

EXPECTED_POLICY_SEQUENCE = (
    (
        "2021-12-15",
        Decimal("9.75"),
    ),
    (
        "2022-04-08",
        Decimal("12.25"),
    ),
    (
        "2022-05-24",
        Decimal("13.75"),
    ),
    (
        "2022-07-13",
        Decimal("15.0"),
    ),
    (
        "2022-11-28",
        Decimal("16.0"),
    ),
    (
        "2023-01-24",
        Decimal("17.0"),
    ),
    (
        "2023-03-03",
        Decimal("20.0"),
    ),
    (
        "2023-04-05",
        Decimal("21.0"),
    ),
    (
        "2023-06-27",
        Decimal("22.0"),
    ),
    (
        "2024-06-11",
        Decimal("20.5"),
    ),
    (
        "2024-07-30",
        Decimal("19.5"),
    ),
    (
        "2024-09-13",
        Decimal("17.5"),
    ),
    (
        "2024-11-05",
        Decimal("15.0"),
    ),
    (
        "2024-12-17",
        Decimal("13.0"),
    ),
    (
        "2025-01-28",
        Decimal("12.0"),
    ),
    (
        "2025-05-06",
        Decimal("11.0"),
    ),
    (
        "2025-12-16",
        Decimal("10.5"),
    ),
    (
        "2026-04-28",
        Decimal("11.5"),
    ),
)

EXPECTED_STATE_COUNTS = {
    "2021-12-15": 94,
    "2022-04-08": 46,
    "2022-05-24": 50,
    "2022-07-13": 138,
    "2022-11-28": 57,
    "2023-01-24": 38,
    "2023-03-03": 33,
    "2023-04-05": 83,
    "2023-06-27": 350,
    "2024-06-11": 49,
    "2024-07-30": 45,
    "2024-09-13": 53,
    "2024-11-05": 42,
    "2024-12-17": 42,
    "2025-01-28": 98,
    "2025-05-06": 224,
    "2025-12-16": 133,
    "2026-04-28": 156,
}

OUTPUT_FIELDS = [
    "date",
    "policy_rate_pct",
    "source_effective_date",
    "is_source_effective_date",
    "source_organization",
    "source_file",
]


def decimal_text(
    value: Decimal,
) -> str:
    """Render Decimal without unnecessary trailing zeros."""

    text = format(
        value,
        "f",
    )

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    return text


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


def load_policy_observations() -> list[dict[str, object]]:
    """Load and validate the frozen official policy-rate observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        rows = connection.execute(
            """
            SELECT
                effective_date,
                rate_pct,
                source_organization,
                source_file
            FROM policy_rate_observations
            ORDER BY effective_date
            """
        ).fetchall()

    finally:
        connection.close()

    if len(rows) != EXPECTED_POLICY_OBSERVATIONS:
        raise RuntimeError(f"Unexpected policy observation count: {len(rows)}")

    observations = []

    for row in rows:
        observations.append(
            {
                "effective_date": row["effective_date"],
                "effective_date_value": date.fromisoformat(row["effective_date"]),
                "rate_pct": Decimal(str(row["rate_pct"])),
                "source_organization": row["source_organization"],
                "source_file": row["source_file"],
            }
        )

    observed_sequence = tuple(
        (
            item["effective_date"],
            item["rate_pct"],
        )
        for item in observations
    )

    if observed_sequence != EXPECTED_POLICY_SEQUENCE:
        raise RuntimeError("Frozen official policy-rate sequence changed")

    for item in observations:
        if item["source_organization"] != EXPECTED_SOURCE_ORGANIZATION:
            raise RuntimeError(
                f"Unexpected policy-rate source organization: {item['effective_date']}"
            )

        if item["source_file"] != EXPECTED_SOURCE_FILE:
            raise RuntimeError(
                "Unexpected policy-rate source file: "
                f"{item['effective_date']} "
                f"{item['source_file']!r}"
            )

    return observations


def derive_daily_state(
    observations: list[dict[str, object]],
) -> list[dict[str, str]]:
    """Carry the latest effective official policy state across calendar dates."""

    output: list[
        dict[
            str,
            str,
        ]
    ] = []

    current_index = -1

    state_date = EXPECTED_START_DATE

    while state_date <= EXPECTED_END_DATE:
        while (
            current_index + 1 < len(observations)
            and observations[current_index + 1]["effective_date_value"] <= state_date
        ):
            current_index += 1

        if current_index < 0:
            raise RuntimeError(
                f"No official policy-rate state available for {state_date.isoformat()}"
            )

        source = observations[current_index]

        source_effective_date = source["effective_date"]

        is_source_effective_date = int(state_date.isoformat() == source_effective_date)

        output.append(
            {
                "date": state_date.isoformat(),
                "policy_rate_pct": decimal_text(source["rate_pct"]),
                "source_effective_date": source_effective_date,
                "is_source_effective_date": str(is_source_effective_date),
                "source_organization": source["source_organization"],
                "source_file": source["source_file"],
            }
        )

        state_date += timedelta(days=1)

    return output


def validate_daily_state(
    rows: list[dict[str, str]],
) -> None:
    """Validate the complete derived daily policy-rate state."""

    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(
            f"Unexpected daily policy-state row count: {len(rows)} != {EXPECTED_ROWS}"
        )

    dates = [date.fromisoformat(row["date"]) for row in rows]

    if dates[0] != EXPECTED_START_DATE:
        raise RuntimeError("Unexpected first daily policy-state date")

    if dates[-1] != EXPECTED_END_DATE:
        raise RuntimeError("Unexpected last daily policy-state date")

    expected_date = EXPECTED_START_DATE

    for actual_date in dates:
        if actual_date != expected_date:
            raise RuntimeError(
                "Daily policy-state calendar gap: "
                f"expected={expected_date} "
                f"actual={actual_date}"
            )

        expected_date += timedelta(days=1)

    state_counts = Counter(row["source_effective_date"] for row in rows)

    if dict(state_counts) != EXPECTED_STATE_COUNTS:
        raise RuntimeError(
            f"Unexpected daily policy-state interval counts: {dict(state_counts)}"
        )

    effective_rows = [row for row in rows if (row["is_source_effective_date"] == "1")]

    if len(effective_rows) != EXPECTED_IN_RANGE_EFFECTIVE_DATES:
        raise RuntimeError(
            f"Unexpected in-range policy effective-date count: {len(effective_rows)}"
        )

    expected_in_range_effective_dates = {
        effective_date
        for (effective_date, _) in EXPECTED_POLICY_SEQUENCE
        if (
            EXPECTED_START_DATE
            <= date.fromisoformat(effective_date)
            <= EXPECTED_END_DATE
        )
    }

    actual_effective_dates = {row["date"] for row in effective_rows}

    if actual_effective_dates != expected_in_range_effective_dates:
        raise RuntimeError("Derived policy effective-date markers changed")

    source_rate_by_effective_date = {
        effective_date: rate for (effective_date, rate) in EXPECTED_POLICY_SEQUENCE
    }

    for row in rows:
        source_effective_date = row["source_effective_date"]

        expected_rate = source_rate_by_effective_date[source_effective_date]

        actual_rate = Decimal(row["policy_rate_pct"])

        if actual_rate != expected_rate:
            raise RuntimeError(
                "Daily policy-state rate mismatch: "
                f"{row['date']} "
                f"{actual_rate} "
                f"!= {expected_rate}"
            )

        if row["source_organization"] != EXPECTED_SOURCE_ORGANIZATION:
            raise RuntimeError(f"Unexpected source organization on {row['date']}")

        if row["source_file"] != EXPECTED_SOURCE_FILE:
            raise RuntimeError(f"Unexpected source file on {row['date']}")

    sentinels = {
        "2022-01-04": (
            Decimal("9.75"),
            "2021-12-15",
            "0",
        ),
        "2022-04-07": (
            Decimal("9.75"),
            "2021-12-15",
            "0",
        ),
        "2022-04-08": (
            Decimal("12.25"),
            "2022-04-08",
            "1",
        ),
        "2023-06-26": (
            Decimal("21"),
            "2023-04-05",
            "0",
        ),
        "2023-06-27": (
            Decimal("22"),
            "2023-06-27",
            "1",
        ),
        "2025-12-15": (
            Decimal("11"),
            "2025-05-06",
            "0",
        ),
        "2025-12-16": (
            Decimal("10.5"),
            "2025-12-16",
            "1",
        ),
        "2026-04-27": (
            Decimal("10.5"),
            "2025-12-16",
            "0",
        ),
        "2026-04-28": (
            Decimal("11.5"),
            "2026-04-28",
            "1",
        ),
        "2026-09-30": (
            Decimal("11.5"),
            "2026-04-28",
            "0",
        ),
    }

    by_date = {row["date"]: row for row in rows}

    for (
        sentinel_date,
        (
            expected_rate,
            expected_source_date,
            expected_marker,
        ),
    ) in sentinels.items():
        row = by_date[sentinel_date]

        if (
            Decimal(row["policy_rate_pct"]) != expected_rate
            or row["source_effective_date"] != expected_source_date
            or row["is_source_effective_date"] != expected_marker
        ):
            raise RuntimeError(f"Daily policy-state sentinel mismatch: {sentinel_date}")


def main() -> None:
    """Build the deterministic daily policy-rate state."""

    observations = load_policy_observations()

    rows = derive_daily_state(observations)

    validate_daily_state(rows)

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

    state_counts = Counter(row["source_effective_date"] for row in rows)

    output_sha = sha256_file(OUTPUT_PATH)

    print("===== DAILY POLICY-RATE STATE =====")

    print(
        "Official source observations:",
        len(observations),
    )

    print(
        "Calendar rows:",
        len(rows),
    )

    print(
        "Coverage:",
        rows[0]["date"],
        "through",
        rows[-1]["date"],
    )

    print(
        "Distinct policy states:",
        len(state_counts),
    )

    print(
        "In-range source effective dates:",
        sum(row["is_source_effective_date"] == "1" for row in rows),
    )

    print("")
    print("Calendar-day counts by source effective date:")

    for effective_date, _ in EXPECTED_POLICY_SEQUENCE:
        print(
            " ",
            effective_date,
            state_counts[effective_date],
        )

    print("")
    print(
        "Output:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )

    print(
        "SHA256:",
        output_sha,
    )

    print("")
    print("PASS: deterministic calendar-daily policy-rate state contract satisfied")


if __name__ == "__main__":
    main()
