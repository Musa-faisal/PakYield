"""Build deterministic exact-date sovereign term-spread panel."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
    TERM_SPREADS,
)
from pakyield.database.connection import get_connection

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "term_spread_panel.csv"

EXPECTED_TERM_SPREADS = {
    "10Y-2Y": ("10Y", "2Y"),
    "10Y-1Y": ("10Y", "1Y"),
    "5Y-1Y": ("5Y", "1Y"),
    "3Y-3M": ("3Y", "3M"),
}

EXPECTED_PKRV_ROWS = 22800
EXPECTED_PKRV_DATES = 1149

EXPECTED_TOTAL_ROWS = 4596
EXPECTED_ELIGIBLE_ROWS = 4566
EXPECTED_INELIGIBLE_ROWS = 30

EXPECTED_ROWS_BY_SPREAD = {
    "10Y-2Y": 1149,
    "10Y-1Y": 1149,
    "5Y-1Y": 1149,
    "3Y-3M": 1149,
}

EXPECTED_ELIGIBLE_BY_SPREAD = {
    "10Y-2Y": 1149,
    "10Y-1Y": 1149,
    "5Y-1Y": 1149,
    "3Y-3M": 1119,
}

EXPECTED_INELIGIBLE_BY_SPREAD = {
    "3Y-3M": 30,
}

EXPECTED_SIGN_COUNTS = {
    "10Y-2Y": {
        "POSITIVE": 473,
        "NEGATIVE": 676,
        "ZERO": 0,
    },
    "10Y-1Y": {
        "POSITIVE": 483,
        "NEGATIVE": 664,
        "ZERO": 2,
    },
    "5Y-1Y": {
        "POSITIVE": 450,
        "NEGATIVE": 698,
        "ZERO": 1,
    },
    "3Y-3M": {
        "POSITIVE": 451,
        "NEGATIVE": 665,
        "ZERO": 3,
    },
}

EXPECTED_EXTREMA = {
    "10Y-2Y": {
        "min": (
            "2023-09-14",
            Decimal("-583"),
        ),
        "max": (
            "2025-07-16",
            Decimal("136"),
        ),
    },
    "10Y-1Y": {
        "min": (
            "2023-09-07",
            Decimal("-812"),
        ),
        "max": (
            "2025-06-26",
            Decimal("150"),
        ),
    },
    "5Y-1Y": {
        "min": (
            "2023-06-06",
            Decimal("-710"),
        ),
        "max": (
            "2026-04-07",
            Decimal("97"),
        ),
    },
    "3Y-3M": {
        "min": (
            "2023-12-06",
            Decimal("-535"),
        ),
        "max": (
            "2026-04-06",
            Decimal("158"),
        ),
    },
}

EXPECTED_3Y_3M_MISSING_SHORT_DATES = {
    "2023-06-16",
    "2023-06-19",
    "2023-06-20",
    "2023-06-21",
    "2023-06-22",
    "2023-06-23",
    "2023-06-26",
    "2023-06-27",
    "2023-07-04",
    "2023-07-06",
    "2023-07-07",
    "2023-07-10",
    "2023-07-11",
    "2023-07-12",
    "2023-07-13",
    "2023-07-14",
    "2023-07-17",
    "2023-07-18",
    "2023-07-19",
    "2023-07-20",
    "2023-07-21",
    "2023-07-25",
    "2023-07-26",
    "2023-07-27",
    "2023-07-31",
    "2023-08-01",
    "2023-08-02",
    "2023-08-03",
    "2023-08-04",
    "2023-08-07",
}

SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"

EXPECTED_PKRV_INGESTION_RUNS = {
    11,
}

CURVE_TYPE = "PKRV"

ELIGIBLE = "ELIGIBLE"
INELIGIBLE = "INELIGIBLE"

MISSING_SHORT_LEG = "MISSING_SHORT_LEG"
MISSING_LONG_LEG = "MISSING_LONG_LEG"
MISSING_BOTH_LEGS = "MISSING_BOTH_LEGS"

CONSTRUCTION_METHOD = "EXACT_SAME_CURVE_SAME_DATE_OBSERVED_TENORS"

OUTPUT_FIELDS = [
    "observation_date",
    "curve_type",
    "spread_name",
    "long_tenor",
    "short_tenor",
    "long_tenor_years",
    "short_tenor_years",
    "long_yield_pct",
    "short_yield_pct",
    "term_spread_bps",
    "eligibility_status",
    "ineligibility_reason",
    "construction_method",
    "long_source_organization",
    "long_source_file",
    "long_ingestion_run_id",
    "short_source_organization",
    "short_source_file",
    "short_ingestion_run_id",
]


def decimal_text(
    value: Decimal,
) -> str:
    """Render one finite Decimal without unnecessary trailing zeros."""

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


def validate_configuration() -> None:
    """Validate the frozen D091 configuration contract."""

    if TERM_SPREADS != EXPECTED_TERM_SPREADS:
        raise RuntimeError("Configured TERM_SPREADS changed from D091")

    for (
        spread_name,
        (
            long_tenor,
            short_tenor,
        ),
    ) in TERM_SPREADS.items():
        if long_tenor not in TENOR_TO_YEARS:
            raise RuntimeError(f"Unknown long tenor for {spread_name}: {long_tenor}")

        if short_tenor not in TENOR_TO_YEARS:
            raise RuntimeError(f"Unknown short tenor for {spread_name}: {short_tenor}")

        if TENOR_TO_YEARS[long_tenor] <= TENOR_TO_YEARS[short_tenor]:
            raise RuntimeError(f"Invalid maturity ordering: {spread_name}")


def load_pkrv_observations() -> tuple[
    list[str],
    dict[
        tuple[
            str,
            str,
        ],
        dict[
            str,
            object,
        ],
    ],
]:
    """Load and validate frozen normalized PKRV observations."""

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
            WHERE curve_type = 'PKRV'
            ORDER BY
                observation_date,
                tenor_years,
                tenor
            """
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError(f"Production SQLite integrity failed: {integrity}")

    if foreign_key_issues:
        raise RuntimeError(
            f"Production SQLite foreign-key issues: {len(foreign_key_issues)}"
        )

    if len(rows) != EXPECTED_PKRV_ROWS:
        raise RuntimeError(f"Unexpected normalized PKRV row count: {len(rows)}")

    observations: dict[
        tuple[
            str,
            str,
        ],
        dict[
            str,
            object,
        ],
    ] = {}

    dates = set()

    ingestion_runs = set()

    for row in rows:
        observation_date = row["observation_date"]
        tenor = row["tenor"]

        if row["curve_type"] != CURVE_TYPE:
            raise RuntimeError(f"Unexpected curve type: {row['curve_type']}")

        key = (
            observation_date,
            tenor,
        )

        if key in observations:
            raise RuntimeError(f"Duplicate normalized PKRV key: {key}")

        if tenor not in TENOR_TO_YEARS:
            raise RuntimeError(f"Unknown PKRV tenor: {tenor}")

        if not math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[tenor],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(f"Unexpected tenor_years: {key}")

        yield_pct = Decimal(str(row["yield_pct"]))

        if not yield_pct.is_finite():
            raise RuntimeError(f"Non-finite PKRV yield: {key}")

        if row["source_organization"] != (SOURCE_ORGANIZATION):
            raise RuntimeError(f"Unexpected PKRV source organization: {key}")

        if not row["source_file"]:
            raise RuntimeError(f"Missing PKRV source file: {key}")

        if row["ingestion_run_id"] is None:
            raise RuntimeError(f"Missing PKRV ingestion run: {key}")

        ingestion_runs.add(int(row["ingestion_run_id"]))

        dates.add(observation_date)

        observations[key] = {
            "observation_date": observation_date,
            "tenor": tenor,
            "tenor_years": float(row["tenor_years"]),
            "yield_pct": yield_pct,
            "source_organization": (row["source_organization"]),
            "source_file": row["source_file"],
            "ingestion_run_id": int(row["ingestion_run_id"]),
        }

    if len(dates) != EXPECTED_PKRV_DATES:
        raise RuntimeError(f"Unexpected distinct PKRV date count: {len(dates)}")

    if ingestion_runs != EXPECTED_PKRV_INGESTION_RUNS:
        raise RuntimeError(f"Unexpected PKRV ingestion lineage: {ingestion_runs}")

    required_tenors = {tenor for legs in TERM_SPREADS.values() for tenor in legs}

    observed_tenors = {
        tenor
        for (
            _observation_date,
            tenor,
        ) in observations
    }

    missing_required = required_tenors - observed_tenors

    if missing_required:
        raise RuntimeError(
            f"Required PKRV spread tenors absent: {sorted(missing_required)}"
        )

    return (
        sorted(dates),
        observations,
    )


def empty_leg_fields(
    prefix: str,
) -> dict[
    str,
    str,
]:
    """Return blank fields for one unavailable spread leg."""

    return {
        f"{prefix}_yield_pct": "",
        f"{prefix}_source_organization": "",
        f"{prefix}_source_file": "",
        f"{prefix}_ingestion_run_id": "",
    }


def observed_leg_fields(
    row: dict[
        str,
        object,
    ],
    prefix: str,
) -> dict[
    str,
    str,
]:
    """Return one observed leg's value and lineage."""

    return {
        f"{prefix}_yield_pct": decimal_text(row["yield_pct"]),
        f"{prefix}_source_organization": str(row["source_organization"]),
        f"{prefix}_source_file": str(row["source_file"]),
        f"{prefix}_ingestion_run_id": str(row["ingestion_run_id"]),
    }


def derive_term_spreads(
    dates: list[str],
    observations: dict[
        tuple[
            str,
            str,
        ],
        dict[
            str,
            object,
        ],
    ],
) -> list[
    dict[
        str,
        str,
    ]
]:
    """Build complete PKRV date × configured-spread panel."""

    output: list[
        dict[
            str,
            str,
        ]
    ] = []

    for observation_date in dates:
        for (
            spread_name,
            (
                long_tenor,
                short_tenor,
            ),
        ) in TERM_SPREADS.items():
            long_row = observations.get(
                (
                    observation_date,
                    long_tenor,
                )
            )

            short_row = observations.get(
                (
                    observation_date,
                    short_tenor,
                )
            )

            if long_row is not None and short_row is not None:
                status = ELIGIBLE
                reason = ""

                spread_bps = (long_row["yield_pct"] - short_row["yield_pct"]) * Decimal(
                    "100"
                )

                spread_text = decimal_text(spread_bps)

            elif long_row is not None and short_row is None:
                status = INELIGIBLE
                reason = MISSING_SHORT_LEG
                spread_text = ""

            elif long_row is None and short_row is not None:
                status = INELIGIBLE
                reason = MISSING_LONG_LEG
                spread_text = ""

            else:
                status = INELIGIBLE
                reason = MISSING_BOTH_LEGS
                spread_text = ""

            row = {
                "observation_date": (observation_date),
                "curve_type": CURVE_TYPE,
                "spread_name": spread_name,
                "long_tenor": long_tenor,
                "short_tenor": short_tenor,
                "long_tenor_years": format(
                    TENOR_TO_YEARS[long_tenor],
                    ".12g",
                ),
                "short_tenor_years": format(
                    TENOR_TO_YEARS[short_tenor],
                    ".12g",
                ),
                "term_spread_bps": (spread_text),
                "eligibility_status": status,
                "ineligibility_reason": reason,
                "construction_method": (CONSTRUCTION_METHOD),
            }

            if long_row is None:
                row.update(empty_leg_fields("long"))

            else:
                row.update(
                    observed_leg_fields(
                        long_row,
                        "long",
                    )
                )

            if short_row is None:
                row.update(empty_leg_fields("short"))

            else:
                row.update(
                    observed_leg_fields(
                        short_row,
                        "short",
                    )
                )

            output.append(row)

    return output


def validate_term_spreads(
    rows: list[
        dict[
            str,
            str,
        ]
    ],
) -> None:
    """Validate full deterministic D091 term-spread panel."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected term-spread row count: {len(rows)}")

    keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["spread_name"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate term-spread analytical keys detected")

    if {row["curve_type"] for row in rows} != {
        CURVE_TYPE,
    }:
        raise RuntimeError("Unexpected curve represented in term-spread panel")

    dates = {row["observation_date"] for row in rows}

    if len(dates) != EXPECTED_PKRV_DATES:
        raise RuntimeError(f"Unexpected term-spread date count: {len(dates)}")

    if min(dates) != "2022-01-04":
        raise RuntimeError("Unexpected first term-spread date")

    if max(dates) != "2026-09-28":
        raise RuntimeError("Unexpected last term-spread date")

    rows_by_spread = Counter(row["spread_name"] for row in rows)

    if dict(rows_by_spread) != (EXPECTED_ROWS_BY_SPREAD):
        raise RuntimeError(f"Unexpected rows by spread: {dict(rows_by_spread)}")

    status_counts = Counter(row["eligibility_status"] for row in rows)

    if dict(status_counts) != {
        ELIGIBLE: EXPECTED_ELIGIBLE_ROWS,
        INELIGIBLE: EXPECTED_INELIGIBLE_ROWS,
    }:
        raise RuntimeError(
            f"Unexpected term-spread eligibility census: {dict(status_counts)}"
        )

    eligible_by_spread = Counter(
        row["spread_name"] for row in rows if row["eligibility_status"] == ELIGIBLE
    )

    if dict(eligible_by_spread) != (EXPECTED_ELIGIBLE_BY_SPREAD):
        raise RuntimeError(
            f"Unexpected eligible rows by spread: {dict(eligible_by_spread)}"
        )

    ineligible_by_spread = Counter(
        row["spread_name"] for row in rows if row["eligibility_status"] == INELIGIBLE
    )

    if dict(ineligible_by_spread) != (EXPECTED_INELIGIBLE_BY_SPREAD):
        raise RuntimeError(
            f"Unexpected ineligible rows by spread: {dict(ineligible_by_spread)}"
        )

    reasons = Counter(
        row["ineligibility_reason"]
        for row in rows
        if row["eligibility_status"] == INELIGIBLE
    )

    if dict(reasons) != {
        MISSING_SHORT_LEG: 30,
    }:
        raise RuntimeError(f"Unexpected ineligibility reasons: {dict(reasons)}")

    missing_short_rows = [
        row for row in rows if row["ineligibility_reason"] == MISSING_SHORT_LEG
    ]

    missing_short_dates = {row["observation_date"] for row in missing_short_rows}

    if missing_short_dates != (EXPECTED_3Y_3M_MISSING_SHORT_DATES):
        raise RuntimeError("3Y-3M missing-short date set changed")

    for row in missing_short_rows:
        if row["spread_name"] != "3Y-3M":
            raise RuntimeError("Unexpected spread has missing short leg")

        if row["long_tenor"] != "3Y":
            raise RuntimeError("Unexpected long tenor on missing-short row")

        if row["short_tenor"] != "3M":
            raise RuntimeError("Unexpected short tenor on missing-short row")

        if not row["long_yield_pct"]:
            raise RuntimeError("Observed 3Y leg missing from ineligible row")

        if row["short_yield_pct"]:
            raise RuntimeError("Missing 3M leg unexpectedly populated")

        if row["term_spread_bps"]:
            raise RuntimeError("Ineligible 3Y-3M row has manufactured spread")

    sign_counts = defaultdict(Counter)

    values_by_spread = defaultdict(list)

    for row in rows:
        if row["construction_method"] != (CONSTRUCTION_METHOD):
            raise RuntimeError("Unexpected term-spread construction method")

        long_tenor = row["long_tenor"]

        short_tenor = row["short_tenor"]

        if TENOR_TO_YEARS[long_tenor] <= TENOR_TO_YEARS[short_tenor]:
            raise RuntimeError("Non-positive maturity ordering in derived panel")

        if row["eligibility_status"] == (ELIGIBLE):
            required = (
                "long_yield_pct",
                "short_yield_pct",
                "term_spread_bps",
                "long_source_organization",
                "long_source_file",
                "long_ingestion_run_id",
                "short_source_organization",
                "short_source_file",
                "short_ingestion_run_id",
            )

            if any(not row[field] for field in required):
                raise RuntimeError("Eligible spread row has missing required fields")

            if row["long_source_organization"] != SOURCE_ORGANIZATION:
                raise RuntimeError("Unexpected long-leg source organization")

            if row["short_source_organization"] != SOURCE_ORGANIZATION:
                raise RuntimeError("Unexpected short-leg source organization")

            if row["long_source_file"] != row["short_source_file"]:
                raise RuntimeError("Matched spread legs have different source files")

            if row["long_ingestion_run_id"] != row["short_ingestion_run_id"]:
                raise RuntimeError("Matched spread legs have different ingestion runs")

            expected_spread = (
                Decimal(row["long_yield_pct"]) - Decimal(row["short_yield_pct"])
            ) * Decimal("100")

            actual_spread = Decimal(row["term_spread_bps"])

            if actual_spread != expected_spread:
                raise RuntimeError(
                    "Term-spread arithmetic mismatch: "
                    f"{row['observation_date']} "
                    f"{row['spread_name']}"
                )

            spread_name = row["spread_name"]

            if actual_spread > 0:
                sign_counts[spread_name]["POSITIVE"] += 1

            elif actual_spread < 0:
                sign_counts[spread_name]["NEGATIVE"] += 1

            else:
                sign_counts[spread_name]["ZERO"] += 1

            values_by_spread[spread_name].append(
                (
                    row["observation_date"],
                    actual_spread,
                )
            )

        else:
            if row["term_spread_bps"]:
                raise RuntimeError("Ineligible spread row contains calculated spread")

    for spread_name in TERM_SPREADS:
        observed_signs = {
            sign: sign_counts[spread_name][sign]
            for sign in (
                "POSITIVE",
                "NEGATIVE",
                "ZERO",
            )
        }

        if observed_signs != (EXPECTED_SIGN_COUNTS[spread_name]):
            raise RuntimeError(
                f"Unexpected sign census for {spread_name}: {observed_signs}"
            )

        values = values_by_spread[spread_name]

        minimum = min(
            values,
            key=lambda item: item[1],
        )

        maximum = max(
            values,
            key=lambda item: item[1],
        )

        if minimum != (EXPECTED_EXTREMA[spread_name]["min"]):
            raise RuntimeError(f"Minimum spread changed for {spread_name}: {minimum}")

        if maximum != (EXPECTED_EXTREMA[spread_name]["max"]):
            raise RuntimeError(f"Maximum spread changed for {spread_name}: {maximum}")


def main() -> None:
    """Build the deterministic sovereign term-spread panel."""

    validate_configuration()

    (
        dates,
        observations,
    ) = load_pkrv_observations()

    rows = derive_term_spreads(
        dates,
        observations,
    )

    validate_term_spreads(rows)

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

    eligible_by_spread = Counter(
        row["spread_name"] for row in rows if row["eligibility_status"] == ELIGIBLE
    )

    print("===== SOVEREIGN TERM-SPREAD PANEL =====")

    print(
        "PKRV dates:",
        len(dates),
    )

    print(
        "Configured spreads:",
        len(TERM_SPREADS),
    )

    print(
        "Rows:",
        len(rows),
    )

    print(
        "Eligible rows:",
        status_counts[ELIGIBLE],
    )

    print(
        "Ineligible rows:",
        status_counts[INELIGIBLE],
    )

    print("")
    print("Eligible rows by spread:")

    for spread_name in TERM_SPREADS:
        print(
            " ",
            spread_name,
            eligible_by_spread[spread_name],
        )

    print("")
    print(
        "Ineligible reason:",
        MISSING_SHORT_LEG,
        EXPECTED_INELIGIBLE_ROWS,
    )

    print("")
    print(
        "Output:",
        (
            OUTPUT_PATH.relative_to(PROJECT_ROOT)
            if OUTPUT_PATH.is_relative_to(PROJECT_ROOT)
            else OUTPUT_PATH
        ),
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print("PASS: deterministic D091 term-spread construction contract satisfied")


if __name__ == "__main__":
    main()
