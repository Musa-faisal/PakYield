"""Build deterministic same-date PKRV/PKISRV comparison panel."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    PKRV_PKISRV_COMMON_TENORS,
    PKRV_PKISRV_SAMPLE_START,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "pkrv_pkisrv_same_date_panel.csv"

EXPECTED_TENORS = (
    "1M",
    "3M",
    "6M",
    "9M",
    "1Y",
)

EXPECTED_START_DATE = "2025-02-03"
EXPECTED_END_DATE = "2026-09-30"

EXPECTED_DISTINCT_DATES = 407
EXPECTED_ROWS_PER_TENOR = 407
EXPECTED_TOTAL_ROWS = 2035

EXPECTED_MATCHED_PER_TENOR = 401
EXPECTED_PKRV_ONLY_PER_TENOR = 4
EXPECTED_PKISRV_ONLY_PER_TENOR = 2

EXPECTED_MATCHED_ROWS = 2005
EXPECTED_PKRV_ONLY_ROWS = 20
EXPECTED_PKISRV_ONLY_ROWS = 10

EXPECTED_PKRV_SOURCE_FILES = 405
EXPECTED_PKISRV_SOURCE_FILES = 403

EXPECTED_PKRV_RUN_IDS = {
    11,
}

EXPECTED_PKISRV_RUN_IDS = {
    13,
}

EXPECTED_PKRV_ONLY_DATES = {
    "2025-03-07",
    "2025-08-20",
    "2026-03-18",
    "2026-03-27",
}

EXPECTED_PKISRV_ONLY_DATES = {
    "2026-09-29",
    "2026-09-30",
}

SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"

MATCHED = "MATCHED"
PKRV_ONLY = "PKRV_ONLY"
PKISRV_ONLY = "PKISRV_ONLY"

OUTPUT_FIELDS = [
    "observation_date",
    "tenor",
    "tenor_years",
    "match_status",
    "pkrv_yield_pct",
    "pkisrv_yield_pct",
    "pkisrv_minus_pkrv_bps",
    "pkrv_source_organization",
    "pkrv_source_file",
    "pkrv_ingestion_run_id",
    "pkisrv_source_organization",
    "pkisrv_source_file",
    "pkisrv_ingestion_run_id",
]

EXPECTED_SENTINELS = {
    (
        "2025-02-03",
        "1M",
    ): (
        Decimal("11.99"),
        Decimal("10.70"),
        Decimal("-129"),
    ),
    (
        "2025-02-03",
        "1Y",
    ): (
        Decimal("11.46"),
        Decimal("18.86"),
        Decimal("740"),
    ),
    (
        "2025-02-04",
        "6M",
    ): (
        Decimal("11.60"),
        Decimal("10.21"),
        Decimal("-139"),
    ),
    (
        "2026-04-02",
        "1Y",
    ): (
        Decimal("11.72"),
        Decimal("10.82"),
        Decimal("-90"),
    ),
    (
        "2026-09-25",
        "1M",
    ): (
        Decimal("11.49"),
        Decimal("10.75"),
        Decimal("-74"),
    ),
    (
        "2026-09-25",
        "1Y",
    ): (
        Decimal("12.14"),
        Decimal("10.85"),
        Decimal("-129"),
    ),
}


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


def load_comparison_observations() -> dict[
    tuple[
        str,
        str,
        str,
    ],
    dict[
        str,
        object,
    ],
]:
    """Load and validate the frozen normalized comparison universe."""

    if tuple(PKRV_PKISRV_COMMON_TENORS) != EXPECTED_TENORS:
        raise RuntimeError("Configured common-tenor universe changed")

    sample_start = PKRV_PKISRV_SAMPLE_START.isoformat()

    if sample_start != EXPECTED_START_DATE:
        raise RuntimeError(
            f"Configured PKRV/PKISRV sample start changed: {sample_start}"
        )

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
            WHERE observation_date >= ?
              AND curve_type IN (
                  'PKRV',
                  'PKISRV'
              )
              AND tenor IN (
                  '1M',
                  '3M',
                  '6M',
                  '9M',
                  '1Y'
              )
            ORDER BY
                observation_date,
                tenor_years,
                tenor,
                curve_type
            """,
            (sample_start,),
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError(f"Production SQLite integrity check failed: {integrity}")

    if foreign_key_issues:
        raise RuntimeError(
            f"Production SQLite foreign-key issues exist: {len(foreign_key_issues)}"
        )

    observations = {}

    source_files = defaultdict(set)

    ingestion_runs = defaultdict(set)

    for row in rows:
        observation_date = row["observation_date"]

        curve_type = row["curve_type"]

        tenor = row["tenor"]

        if curve_type not in {
            "PKRV",
            "PKISRV",
        }:
            raise RuntimeError(f"Unexpected curve type: {curve_type}")

        if tenor not in EXPECTED_TENORS:
            raise RuntimeError(f"Unexpected comparison tenor: {tenor}")

        key = (
            observation_date,
            curve_type,
            tenor,
        )

        if key in observations:
            raise RuntimeError(f"Duplicate normalized comparison key: {key}")

        expected_tenor_years = TENOR_TO_YEARS[tenor]

        if not math.isclose(
            float(row["tenor_years"]),
            expected_tenor_years,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(f"Unexpected tenor_years: {key}")

        yield_pct = Decimal(str(row["yield_pct"]))

        if not yield_pct.is_finite():
            raise RuntimeError(f"Non-finite comparison yield: {key}")

        if row["source_organization"] != SOURCE_ORGANIZATION:
            raise RuntimeError(f"Unexpected source organization: {key}")

        source_file = row["source_file"]

        if not source_file:
            raise RuntimeError(f"Missing comparison source file: {key}")

        ingestion_run_id = row["ingestion_run_id"]

        if ingestion_run_id is None:
            raise RuntimeError(f"Missing comparison ingestion lineage: {key}")

        observations[key] = {
            "observation_date": observation_date,
            "curve_type": curve_type,
            "tenor": tenor,
            "tenor_years": float(row["tenor_years"]),
            "yield_pct": yield_pct,
            "source_organization": row["source_organization"],
            "source_file": source_file,
            "ingestion_run_id": int(ingestion_run_id),
        }

        source_files[curve_type].add(source_file)

        ingestion_runs[curve_type].add(int(ingestion_run_id))

    if len(source_files["PKRV"]) != EXPECTED_PKRV_SOURCE_FILES:
        raise RuntimeError(
            f"Unexpected in-sample PKRV source-file count: {len(source_files['PKRV'])}"
        )

    if len(source_files["PKISRV"]) != EXPECTED_PKISRV_SOURCE_FILES:
        raise RuntimeError(
            "Unexpected in-sample PKISRV source-file count: "
            f"{len(source_files['PKISRV'])}"
        )

    if ingestion_runs["PKRV"] != EXPECTED_PKRV_RUN_IDS:
        raise RuntimeError(
            f"Unexpected PKRV ingestion lineage: {ingestion_runs['PKRV']}"
        )

    if ingestion_runs["PKISRV"] != EXPECTED_PKISRV_RUN_IDS:
        raise RuntimeError(
            f"Unexpected PKISRV ingestion lineage: {ingestion_runs['PKISRV']}"
        )

    return observations


def derive_comparison_panel(
    observations: dict[
        tuple[
            str,
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
    """Create a union panel while calculating spreads only for exact matches."""

    dates_by_tenor_curve = defaultdict(set)

    for (
        observation_date,
        curve_type,
        tenor,
    ) in observations:
        dates_by_tenor_curve[
            (
                tenor,
                curve_type,
            )
        ].add(observation_date)

    union_dates_all = set()

    for tenor in EXPECTED_TENORS:
        pkrv_dates = dates_by_tenor_curve[
            (
                tenor,
                "PKRV",
            )
        ]

        pkisrv_dates = dates_by_tenor_curve[
            (
                tenor,
                "PKISRV",
            )
        ]

        matched = pkrv_dates & pkisrv_dates

        pkrv_only = pkrv_dates - pkisrv_dates

        pkisrv_only = pkisrv_dates - pkrv_dates

        union_dates = pkrv_dates | pkisrv_dates

        if len(matched) != EXPECTED_MATCHED_PER_TENOR:
            raise RuntimeError(
                f"Matched-date count changed for {tenor}: {len(matched)}"
            )

        if pkrv_only != EXPECTED_PKRV_ONLY_DATES:
            raise RuntimeError(
                f"PKRV-only dates changed for {tenor}: {sorted(pkrv_only)}"
            )

        if pkisrv_only != EXPECTED_PKISRV_ONLY_DATES:
            raise RuntimeError(
                f"PKISRV-only dates changed for {tenor}: {sorted(pkisrv_only)}"
            )

        if len(union_dates) != EXPECTED_ROWS_PER_TENOR:
            raise RuntimeError(
                f"Union-date count changed for {tenor}: {len(union_dates)}"
            )

        union_dates_all.update(union_dates)

    if len(union_dates_all) != EXPECTED_DISTINCT_DATES:
        raise RuntimeError(
            f"Distinct comparison-date count changed: {len(union_dates_all)}"
        )

    if min(union_dates_all) != EXPECTED_START_DATE:
        raise RuntimeError("Unexpected first comparison date")

    if max(union_dates_all) != EXPECTED_END_DATE:
        raise RuntimeError("Unexpected final comparison date")

    output = []

    for observation_date in sorted(union_dates_all):
        for tenor in EXPECTED_TENORS:
            pkrv = observations.get(
                (
                    observation_date,
                    "PKRV",
                    tenor,
                )
            )

            pkisrv = observations.get(
                (
                    observation_date,
                    "PKISRV",
                    tenor,
                )
            )

            if pkrv is None and pkisrv is None:
                raise RuntimeError(
                    "Comparison union contains empty "
                    "date-tenor position: "
                    f"{observation_date} {tenor}"
                )

            if pkrv is not None and pkisrv is not None:
                match_status = MATCHED

                pkrv_yield = pkrv["yield_pct"]

                pkisrv_yield = pkisrv["yield_pct"]

                spread_bps = (pkisrv_yield - pkrv_yield) * Decimal("100")

                pkrv_yield_text = decimal_text(pkrv_yield)

                pkisrv_yield_text = decimal_text(pkisrv_yield)

                spread_text = decimal_text(spread_bps)

            elif pkrv is not None:
                match_status = PKRV_ONLY

                pkrv_yield_text = decimal_text(pkrv["yield_pct"])

                pkisrv_yield_text = ""
                spread_text = ""

            else:
                match_status = PKISRV_ONLY

                pkrv_yield_text = ""

                pkisrv_yield_text = decimal_text(pkisrv["yield_pct"])

                spread_text = ""

            output.append(
                {
                    "observation_date": observation_date,
                    "tenor": tenor,
                    "tenor_years": format(
                        TENOR_TO_YEARS[tenor],
                        ".12g",
                    ),
                    "match_status": match_status,
                    "pkrv_yield_pct": pkrv_yield_text,
                    "pkisrv_yield_pct": pkisrv_yield_text,
                    "pkisrv_minus_pkrv_bps": spread_text,
                    "pkrv_source_organization": (
                        pkrv["source_organization"] if pkrv is not None else ""
                    ),
                    "pkrv_source_file": (
                        pkrv["source_file"] if pkrv is not None else ""
                    ),
                    "pkrv_ingestion_run_id": (
                        str(pkrv["ingestion_run_id"]) if pkrv is not None else ""
                    ),
                    "pkisrv_source_organization": (
                        pkisrv["source_organization"] if pkisrv is not None else ""
                    ),
                    "pkisrv_source_file": (
                        pkisrv["source_file"] if pkisrv is not None else ""
                    ),
                    "pkisrv_ingestion_run_id": (
                        str(pkisrv["ingestion_run_id"]) if pkisrv is not None else ""
                    ),
                }
            )

    return output


def validate_comparison_panel(
    rows: list[
        dict[
            str,
            str,
        ]
    ],
) -> None:
    """Validate the complete same-date comparison union."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected comparison panel row count: {len(rows)}")

    keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate comparison date-tenor keys detected")

    status_counts = Counter(row["match_status"] for row in rows)

    expected_status_counts = {
        MATCHED: EXPECTED_MATCHED_ROWS,
        PKRV_ONLY: EXPECTED_PKRV_ONLY_ROWS,
        PKISRV_ONLY: EXPECTED_PKISRV_ONLY_ROWS,
    }

    if dict(status_counts) != expected_status_counts:
        raise RuntimeError(f"Comparison status counts changed: {dict(status_counts)}")

    tenor_counts = Counter(row["tenor"] for row in rows)

    if dict(tenor_counts) != {
        tenor: EXPECTED_ROWS_PER_TENOR for tenor in EXPECTED_TENORS
    }:
        raise RuntimeError(f"Comparison tenor row counts changed: {dict(tenor_counts)}")

    status_by_tenor = defaultdict(Counter)

    pkrv_source_files = set()
    pkisrv_source_files = set()

    pkrv_runs = set()
    pkisrv_runs = set()

    matched_rows = []

    for row in rows:
        observation_date = row["observation_date"]

        tenor = row["tenor"]

        status = row["match_status"]

        status_by_tenor[tenor][status] += 1

        if not math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[tenor],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(
                f"Comparison tenor_years mismatch: {observation_date} {tenor}"
            )

        if status == MATCHED:
            required_fields = (
                "pkrv_yield_pct",
                "pkisrv_yield_pct",
                "pkisrv_minus_pkrv_bps",
                "pkrv_source_organization",
                "pkrv_source_file",
                "pkrv_ingestion_run_id",
                "pkisrv_source_organization",
                "pkisrv_source_file",
                "pkisrv_ingestion_run_id",
            )

            if any(not row[field] for field in required_fields):
                raise RuntimeError(
                    f"MATCHED row contains missing values: {observation_date} {tenor}"
                )

            pkrv_yield = Decimal(row["pkrv_yield_pct"])

            pkisrv_yield = Decimal(row["pkisrv_yield_pct"])

            expected_spread = (pkisrv_yield - pkrv_yield) * Decimal("100")

            actual_spread = Decimal(row["pkisrv_minus_pkrv_bps"])

            if actual_spread != expected_spread:
                raise RuntimeError(
                    f"Comparison spread arithmetic mismatch: {observation_date} {tenor}"
                )

            matched_rows.append(row)

        elif status == PKRV_ONLY:
            if observation_date not in EXPECTED_PKRV_ONLY_DATES:
                raise RuntimeError(f"Unexpected PKRV_ONLY date: {observation_date}")

            if not row["pkrv_yield_pct"]:
                raise RuntimeError("PKRV_ONLY row lacks PKRV yield")

            if any(
                row[field]
                for field in (
                    "pkisrv_yield_pct",
                    "pkisrv_minus_pkrv_bps",
                    "pkisrv_source_organization",
                    "pkisrv_source_file",
                    "pkisrv_ingestion_run_id",
                )
            ):
                raise RuntimeError(
                    "PKRV_ONLY row contains manufactured "
                    "PKISRV values: "
                    f"{observation_date} {tenor}"
                )

        elif status == PKISRV_ONLY:
            if observation_date not in EXPECTED_PKISRV_ONLY_DATES:
                raise RuntimeError(f"Unexpected PKISRV_ONLY date: {observation_date}")

            if not row["pkisrv_yield_pct"]:
                raise RuntimeError("PKISRV_ONLY row lacks PKISRV yield")

            if any(
                row[field]
                for field in (
                    "pkrv_yield_pct",
                    "pkisrv_minus_pkrv_bps",
                    "pkrv_source_organization",
                    "pkrv_source_file",
                    "pkrv_ingestion_run_id",
                )
            ):
                raise RuntimeError(
                    "PKISRV_ONLY row contains manufactured "
                    "PKRV values: "
                    f"{observation_date} {tenor}"
                )

        else:
            raise RuntimeError(f"Unexpected comparison match status: {status}")

        if row["pkrv_source_file"]:
            pkrv_source_files.add(row["pkrv_source_file"])

        if row["pkisrv_source_file"]:
            pkisrv_source_files.add(row["pkisrv_source_file"])

        if row["pkrv_ingestion_run_id"]:
            pkrv_runs.add(int(row["pkrv_ingestion_run_id"]))

        if row["pkisrv_ingestion_run_id"]:
            pkisrv_runs.add(int(row["pkisrv_ingestion_run_id"]))

        if row["pkrv_source_organization"] and (
            row["pkrv_source_organization"] != SOURCE_ORGANIZATION
        ):
            raise RuntimeError("Unexpected PKRV source organization")

        if row["pkisrv_source_organization"] and (
            row["pkisrv_source_organization"] != SOURCE_ORGANIZATION
        ):
            raise RuntimeError("Unexpected PKISRV source organization")

    expected_tenor_status = {
        MATCHED: EXPECTED_MATCHED_PER_TENOR,
        PKRV_ONLY: EXPECTED_PKRV_ONLY_PER_TENOR,
        PKISRV_ONLY: EXPECTED_PKISRV_ONLY_PER_TENOR,
    }

    for tenor in EXPECTED_TENORS:
        if dict(status_by_tenor[tenor]) != expected_tenor_status:
            raise RuntimeError(
                "Per-tenor status distribution changed: "
                f"{tenor} "
                f"{dict(status_by_tenor[tenor])}"
            )

    if len(pkrv_source_files) != EXPECTED_PKRV_SOURCE_FILES:
        raise RuntimeError("Derived PKRV source-file count changed")

    if len(pkisrv_source_files) != EXPECTED_PKISRV_SOURCE_FILES:
        raise RuntimeError("Derived PKISRV source-file count changed")

    if pkrv_runs != EXPECTED_PKRV_RUN_IDS:
        raise RuntimeError("Derived PKRV ingestion lineage changed")

    if pkisrv_runs != EXPECTED_PKISRV_RUN_IDS:
        raise RuntimeError("Derived PKISRV ingestion lineage changed")

    by_key = {
        (
            row["observation_date"],
            row["tenor"],
        ): row
        for row in rows
    }

    for (
        key,
        (
            expected_pkrv,
            expected_pkisrv,
            expected_spread,
        ),
    ) in EXPECTED_SENTINELS.items():
        row = by_key[key]

        if row["match_status"] != MATCHED:
            raise RuntimeError(f"Spread sentinel is not MATCHED: {key}")

        actual_pkrv = Decimal(row["pkrv_yield_pct"])

        actual_pkisrv = Decimal(row["pkisrv_yield_pct"])

        actual_spread = Decimal(row["pkisrv_minus_pkrv_bps"])

        if (
            actual_pkrv != expected_pkrv
            or actual_pkisrv != expected_pkisrv
            or actual_spread != expected_spread
        ):
            raise RuntimeError(f"Spread sentinel changed: {key}")

    for observation_date in EXPECTED_PKRV_ONLY_DATES:
        for tenor in EXPECTED_TENORS:
            row = by_key[
                (
                    observation_date,
                    tenor,
                )
            ]

            if row["match_status"] != PKRV_ONLY:
                raise RuntimeError(
                    f"Expected PKRV_ONLY row changed: {observation_date} {tenor}"
                )

    for observation_date in EXPECTED_PKISRV_ONLY_DATES:
        for tenor in EXPECTED_TENORS:
            row = by_key[
                (
                    observation_date,
                    tenor,
                )
            ]

            if row["match_status"] != PKISRV_ONLY:
                raise RuntimeError(
                    f"Expected PKISRV_ONLY row changed: {observation_date} {tenor}"
                )

    if len(matched_rows) != EXPECTED_MATCHED_ROWS:
        raise RuntimeError("Unexpected matched-row count")


def main() -> None:
    """Build the deterministic PKRV/PKISRV union comparison panel."""

    observations = load_comparison_observations()

    rows = derive_comparison_panel(observations)

    validate_comparison_panel(rows)

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

    status_counts = Counter(row["match_status"] for row in rows)

    matched_rows = [row for row in rows if (row["match_status"] == MATCHED)]

    spread_values = [Decimal(row["pkisrv_minus_pkrv_bps"]) for row in matched_rows]

    positive_spreads = sum(value > Decimal("0") for value in spread_values)

    negative_spreads = sum(value < Decimal("0") for value in spread_values)

    zero_spreads = sum(value == Decimal("0") for value in spread_values)

    largest_absolute_spreads = sorted(
        matched_rows,
        key=lambda row: abs(Decimal(row["pkisrv_minus_pkrv_bps"])),
        reverse=True,
    )[:15]

    by_key = {
        (
            row["observation_date"],
            row["tenor"],
        ): row
        for row in rows
    }

    output_sha = sha256_file(OUTPUT_PATH)

    print("===== PKRV / PKISRV SAME-DATE COMPARISON PANEL =====")

    print(
        "Comparison rows:",
        len(rows),
    )

    print(
        "Distinct dates:",
        len({row["observation_date"] for row in rows}),
    )

    print(
        "Coverage:",
        rows[0]["observation_date"],
        "through",
        rows[-1]["observation_date"],
    )

    print(
        "Common tenors:",
        list(EXPECTED_TENORS),
    )

    print("")
    print("Status counts:")

    for status in (
        MATCHED,
        PKRV_ONLY,
        PKISRV_ONLY,
    ):
        print(
            " ",
            status,
            status_counts[status],
        )

    print("")
    print("Per-tenor status counts:")

    for tenor in EXPECTED_TENORS:
        tenor_rows = [row for row in rows if row["tenor"] == tenor]

        tenor_status = Counter(row["match_status"] for row in tenor_rows)

        print(
            " ",
            tenor,
            dict(tenor_status),
        )

    print("")
    print(
        "PKRV_ONLY dates:",
        sorted(EXPECTED_PKRV_ONLY_DATES),
    )

    print(
        "PKISRV_ONLY dates:",
        sorted(EXPECTED_PKISRV_ONLY_DATES),
    )

    print("")
    print("Matched spread-sign census:")

    print(
        "  Positive:",
        positive_spreads,
    )

    print(
        "  Negative:",
        negative_spreads,
    )

    print(
        "  Zero:",
        zero_spreads,
    )

    print("")
    print("Largest absolute PKISRV-PKRV spreads:")

    for row in largest_absolute_spreads:
        print(
            " ",
            row["observation_date"],
            row["tenor"],
            "PKRV=",
            row["pkrv_yield_pct"],
            "PKISRV=",
            row["pkisrv_yield_pct"],
            "spread_bps=",
            row["pkisrv_minus_pkrv_bps"],
        )

    print("")
    print("Spread sentinels:")

    for key in EXPECTED_SENTINELS:
        row = by_key[key]

        print(
            " ",
            key[0],
            key[1],
            "PKRV=",
            row["pkrv_yield_pct"],
            "PKISRV=",
            row["pkisrv_yield_pct"],
            "spread_bps=",
            row["pkisrv_minus_pkrv_bps"],
        )

    print("")
    print(
        "PKRV source files:",
        len({row["pkrv_source_file"] for row in rows if row["pkrv_source_file"]}),
    )

    print(
        "PKISRV source files:",
        len({row["pkisrv_source_file"] for row in rows if row["pkisrv_source_file"]}),
    )

    print(
        "PKRV ingestion runs:",
        {
            int(row["pkrv_ingestion_run_id"])
            for row in rows
            if row["pkrv_ingestion_run_id"]
        },
    )

    print(
        "PKISRV ingestion runs:",
        {
            int(row["pkisrv_ingestion_run_id"])
            for row in rows
            if row["pkisrv_ingestion_run_id"]
        },
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
        "PASS: deterministic same-date PKRV/PKISRV union comparison contract satisfied"
    )


if __name__ == "__main__":
    main()
