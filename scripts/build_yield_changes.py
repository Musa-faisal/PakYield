"""Build deterministic previous-available-observation sovereign yield changes."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    PKRV_CANONICAL_TENORS,
    PKRV_PKISRV_COMMON_TENORS,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "yield_changes_long.csv"

EXPECTED_TOTAL_ROWS = 24815
EXPECTED_PKRV_ROWS = 22800
EXPECTED_PKISRV_ROWS = 2015

EXPECTED_SERIES = 25
EXPECTED_ROWS_WITH_PREVIOUS = 24790
EXPECTED_FIRST_ROWS = 25

SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"

CHANGE_METHOD = "PREVIOUS_AVAILABLE_OBSERVATION"

CURVE_TENORS = {
    "PKRV": tuple(PKRV_CANONICAL_TENORS),
    "PKISRV": tuple(PKRV_PKISRV_COMMON_TENORS),
}

PKRV_PARTIAL_MONTHLY_TENORS = {
    "1M",
    "2M",
    "3M",
    "4M",
    "6M",
    "9M",
}

EXPECTED_SERIES_ROW_COUNTS = {
    **{
        (
            "PKRV",
            tenor,
        ): (1119 if tenor in PKRV_PARTIAL_MONTHLY_TENORS else 1149)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 403
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_MAX_GAP_DAYS = {
    **{
        (
            "PKRV",
            tenor,
        ): (54 if tenor in PKRV_PARTIAL_MONTHLY_TENORS else 7)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 6
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_CURVE_SOURCE_FILES = {
    "PKRV": 1149,
    "PKISRV": 403,
}

EXPECTED_CURVE_INGESTION_RUNS = {
    "PKRV": {
        11,
    },
    "PKISRV": {
        13,
    },
}

OUTPUT_FIELDS = [
    "observation_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "yield_pct",
    "previous_observation_date",
    "previous_yield_pct",
    "observation_gap_days",
    "yield_change_bps",
    "change_method",
    "source_organization",
    "source_file",
    "ingestion_run_id",
]


def decimal_text(
    value: Decimal,
) -> str:
    """Render a finite Decimal without meaningless trailing zeros."""

    if not value.is_finite():
        raise RuntimeError(f"Non-finite decimal encountered: {value}")

    text = format(
        value,
        "f",
    )

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    if text == "-0":
        return "0"

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


def load_yield_observations() -> list[dict[str, object]]:
    """Load and validate the frozen normalized yield observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

        rows = connection.execute(
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
            f"Production SQLite foreign-key issues exist: {len(foreign_key_issues)}"
        )

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected normalized yield row count: {len(rows)}")

    output = []

    keys = set()

    curve_counts = Counter()

    source_files: dict[
        str,
        set[str],
    ] = defaultdict(set)

    ingestion_runs: dict[
        str,
        set[int],
    ] = defaultdict(set)

    for row in rows:
        observation_date = row["observation_date"]

        curve_type = row["curve_type"]

        tenor = row["tenor"]

        key = (
            observation_date,
            curve_type,
            tenor,
        )

        if key in keys:
            raise RuntimeError(f"Duplicate normalized yield key: {key}")

        keys.add(key)

        if curve_type not in CURVE_TENORS:
            raise RuntimeError(f"Unexpected curve type: {curve_type}")

        if tenor not in CURVE_TENORS[curve_type]:
            raise RuntimeError(f"Unexpected tenor for {curve_type}: {tenor}")

        expected_tenor_years = TENOR_TO_YEARS[tenor]

        if not math.isclose(
            float(row["tenor_years"]),
            expected_tenor_years,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(
                f"Unexpected tenor_years for {curve_type} {tenor} {observation_date}"
            )

        yield_pct = Decimal(str(row["yield_pct"]))

        if not yield_pct.is_finite():
            raise RuntimeError(f"Non-finite yield for {key}")

        if not (Decimal("-100") < yield_pct < Decimal("100")):
            raise RuntimeError(f"Yield outside database contract: {key} {yield_pct}")

        if row["source_organization"] != SOURCE_ORGANIZATION:
            raise RuntimeError(f"Unexpected yield source organization: {key}")

        source_file = row["source_file"]

        if not source_file:
            raise RuntimeError(f"Missing yield source file: {key}")

        ingestion_run_id = row["ingestion_run_id"]

        if ingestion_run_id is None:
            raise RuntimeError(f"Missing ingestion-run lineage: {key}")

        curve_counts[curve_type] += 1

        source_files[curve_type].add(source_file)

        ingestion_runs[curve_type].add(int(ingestion_run_id))

        output.append(
            {
                "observation_date": observation_date,
                "curve_type": curve_type,
                "tenor": tenor,
                "tenor_years": float(row["tenor_years"]),
                "yield_pct": yield_pct,
                "source_organization": row["source_organization"],
                "source_file": source_file,
                "ingestion_run_id": int(ingestion_run_id),
            }
        )

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Unexpected unique normalized yield key count")

    if dict(curve_counts) != {
        "PKRV": EXPECTED_PKRV_ROWS,
        "PKISRV": EXPECTED_PKISRV_ROWS,
    }:
        raise RuntimeError(f"Unexpected curve row counts: {dict(curve_counts)}")

    for (
        curve_type,
        expected_count,
    ) in EXPECTED_CURVE_SOURCE_FILES.items():
        actual_count = len(source_files[curve_type])

        if actual_count != expected_count:
            raise RuntimeError(
                f"Unexpected source-file count for {curve_type}: {actual_count}"
            )

    for (
        curve_type,
        expected_runs,
    ) in EXPECTED_CURVE_INGESTION_RUNS.items():
        actual_runs = ingestion_runs[curve_type]

        if actual_runs != expected_runs:
            raise RuntimeError(
                f"Unexpected ingestion lineage for {curve_type}: {actual_runs}"
            )

    return output


def derive_changes(
    observations: list[
        dict[
            str,
            object,
        ]
    ],
) -> list[
    dict[
        str,
        str,
    ]
]:
    """Derive yield changes using the previous available row per curve and tenor."""

    grouped: dict[
        tuple[
            str,
            str,
        ],
        list[
            dict[
                str,
                object,
            ]
        ],
    ] = defaultdict(list)

    for row in observations:
        grouped[
            (
                row["curve_type"],
                row["tenor"],
            )
        ].append(row)

    if len(grouped) != EXPECTED_SERIES:
        raise RuntimeError(f"Unexpected curve-tenor series count: {len(grouped)}")

    output = []

    for curve_type in (
        "PKRV",
        "PKISRV",
    ):
        for tenor in CURVE_TENORS[curve_type]:
            key = (
                curve_type,
                tenor,
            )

            series = grouped.get(
                key,
            )

            if series is None:
                raise RuntimeError(f"Missing normalized yield series: {key}")

            series = sorted(
                series,
                key=lambda row: row["observation_date"],
            )

            expected_count = EXPECTED_SERIES_ROW_COUNTS[key]

            if len(series) != expected_count:
                raise RuntimeError(
                    f"Unexpected row count for {key}: {len(series)} != {expected_count}"
                )

            previous = None

            for row in series:
                observation_date = row["observation_date"]

                current_date = date.fromisoformat(observation_date)

                current_yield = row["yield_pct"]

                if previous is None:
                    previous_date_text = ""
                    previous_yield_text = ""
                    gap_text = ""
                    change_text = ""

                else:
                    previous_date_text = previous["observation_date"]

                    previous_date = date.fromisoformat(previous_date_text)

                    gap_days = (current_date - previous_date).days

                    if gap_days <= 0:
                        raise RuntimeError(
                            "Non-increasing observation sequence "
                            f"for {key}: "
                            f"{previous_date_text} "
                            f"to {observation_date}"
                        )

                    previous_yield = previous["yield_pct"]

                    change_bps = (current_yield - previous_yield) * Decimal("100")

                    previous_yield_text = decimal_text(previous_yield)

                    gap_text = str(gap_days)

                    change_text = decimal_text(change_bps)

                output.append(
                    {
                        "observation_date": observation_date,
                        "curve_type": curve_type,
                        "tenor": tenor,
                        "tenor_years": format(
                            TENOR_TO_YEARS[tenor],
                            ".12g",
                        ),
                        "yield_pct": decimal_text(current_yield),
                        "previous_observation_date": previous_date_text,
                        "previous_yield_pct": previous_yield_text,
                        "observation_gap_days": gap_text,
                        "yield_change_bps": change_text,
                        "change_method": CHANGE_METHOD,
                        "source_organization": row["source_organization"],
                        "source_file": row["source_file"],
                        "ingestion_run_id": str(row["ingestion_run_id"]),
                    }
                )

                previous = row

    return output


def validate_changes(
    rows: list[
        dict[
            str,
            str,
        ]
    ],
) -> None:
    """Validate the complete previous-observation yield-change artifact."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected derived yield-change row count: {len(rows)}")

    keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate derived yield-change keys detected")

    first_rows = [row for row in rows if (row["previous_observation_date"] == "")]

    changed_rows = [row for row in rows if (row["previous_observation_date"] != "")]

    if len(first_rows) != EXPECTED_FIRST_ROWS:
        raise RuntimeError(f"Unexpected first-series-row count: {len(first_rows)}")

    if len(changed_rows) != EXPECTED_ROWS_WITH_PREVIOUS:
        raise RuntimeError(
            f"Unexpected rows with previous observations: {len(changed_rows)}"
        )

    first_series_keys = {
        (
            row["curve_type"],
            row["tenor"],
        )
        for row in first_rows
    }

    if len(first_series_keys) != EXPECTED_SERIES:
        raise RuntimeError("Not exactly one first row per curve-tenor series")

    for row in first_rows:
        if any(
            row[field] != ""
            for field in (
                "previous_yield_pct",
                "observation_gap_days",
                "yield_change_bps",
            )
        ):
            raise RuntimeError(
                "First series row contains manufactured "
                "previous-observation values: "
                f"{row['curve_type']} "
                f"{row['tenor']} "
                f"{row['observation_date']}"
            )

    gap_maxima: dict[
        tuple[
            str,
            str,
        ],
        int,
    ] = {}

    series_change_counts = Counter()

    for row in changed_rows:
        key = (
            row["curve_type"],
            row["tenor"],
        )

        previous_date = date.fromisoformat(row["previous_observation_date"])

        current_date = date.fromisoformat(row["observation_date"])

        expected_gap = (current_date - previous_date).days

        actual_gap = int(row["observation_gap_days"])

        if actual_gap != expected_gap:
            raise RuntimeError(f"Observation-gap mismatch: {row}")

        if actual_gap <= 0:
            raise RuntimeError(f"Non-positive observation gap: {row}")

        current_yield = Decimal(row["yield_pct"])

        previous_yield = Decimal(row["previous_yield_pct"])

        expected_change = (current_yield - previous_yield) * Decimal("100")

        actual_change = Decimal(row["yield_change_bps"])

        if actual_change != expected_change:
            raise RuntimeError(f"Yield-change arithmetic mismatch: {row}")

        if row["change_method"] != CHANGE_METHOD:
            raise RuntimeError("Unexpected change method")

        series_change_counts[key] += 1

        previous_max = gap_maxima.get(key)

        if previous_max is None or actual_gap > previous_max:
            gap_maxima[key] = actual_gap

    for (
        key,
        expected_rows,
    ) in EXPECTED_SERIES_ROW_COUNTS.items():
        expected_changes = expected_rows - 1

        actual_changes = series_change_counts[key]

        if actual_changes != expected_changes:
            raise RuntimeError(
                "Unexpected valid-change count for "
                f"{key}: "
                f"{actual_changes} "
                f"!= {expected_changes}"
            )

    if gap_maxima != EXPECTED_MAX_GAP_DAYS:
        raise RuntimeError(f"Maximum observation-gap census changed: {gap_maxima}")

    curve_counts = Counter(row["curve_type"] for row in rows)

    if dict(curve_counts) != {
        "PKRV": EXPECTED_PKRV_ROWS,
        "PKISRV": EXPECTED_PKISRV_ROWS,
    }:
        raise RuntimeError(f"Unexpected derived curve row counts: {dict(curve_counts)}")


def main() -> None:
    """Build deterministic previous-available-observation yield changes."""

    observations = load_yield_observations()

    rows = derive_changes(observations)

    validate_changes(rows)

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

    first_rows = [row for row in rows if not row["previous_observation_date"]]

    changed_rows = [row for row in rows if row["previous_observation_date"]]

    zero_changes = sum(
        Decimal(row["yield_change_bps"]) == Decimal("0") for row in changed_rows
    )

    largest_changes = sorted(
        changed_rows,
        key=lambda row: abs(Decimal(row["yield_change_bps"])),
        reverse=True,
    )[:15]

    output_sha = sha256_file(OUTPUT_PATH)

    print("===== PREVIOUS-AVAILABLE YIELD CHANGES =====")

    print(
        "Normalized input rows:",
        len(observations),
    )

    print(
        "Derived rows:",
        len(rows),
    )

    print(
        "Distinct curve-tenor series:",
        EXPECTED_SERIES,
    )

    print(
        "First rows with NULL previous state:",
        len(first_rows),
    )

    print(
        "Rows with valid previous observation:",
        len(changed_rows),
    )

    print(
        "Zero-bps changes:",
        zero_changes,
    )

    print("")
    print("Series row counts / maximum gaps:")

    grouped = defaultdict(list)

    for row in rows:
        grouped[
            (
                row["curve_type"],
                row["tenor"],
            )
        ].append(row)

    for key in sorted(grouped):
        nonfirst = [row for row in grouped[key] if row["observation_gap_days"]]

        maximum_gap = max(int(row["observation_gap_days"]) for row in nonfirst)

        print(
            " ",
            key,
            "rows=",
            len(grouped[key]),
            "max_gap_days=",
            maximum_gap,
        )

    print("")
    print("Largest absolute source-observed changes:")

    for row in largest_changes:
        print(
            " ",
            row["curve_type"],
            row["tenor"],
            row["previous_observation_date"],
            "->",
            row["observation_date"],
            row["previous_yield_pct"],
            "->",
            row["yield_pct"],
            "change_bps=",
            row["yield_change_bps"],
            "gap_days=",
            row["observation_gap_days"],
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
    print(
        "PASS: deterministic previous-available-observation "
        "yield-change contract satisfied"
    )


if __name__ == "__main__":
    main()
