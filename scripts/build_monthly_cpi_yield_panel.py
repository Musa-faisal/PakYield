"""Build deterministic monthly CPI/yield alignment panel."""

from __future__ import annotations

import calendar
import csv
import hashlib
import math
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from pakyield.config import (
    DATABASE_PATH,
    MACRO_SAMPLE_START,
    PKRV_CANONICAL_TENORS,
    PKRV_PKISRV_COMMON_TENORS,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)
from pakyield.database.connection import (
    get_connection,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv"

EXPECTED_CPI_PERIODS = 57
EXPECTED_CPI_FIRST = "2022-01"
EXPECTED_CPI_LAST = "2026-09"

EXPECTED_TOTAL_ROWS = 1234
EXPECTED_PKRV_ROWS = 1134
EXPECTED_PKISRV_ROWS = 100

EXPECTED_FIRST_SERIES_ROWS = 25
EXPECTED_ROWS_WITH_PREVIOUS_AVAILABLE = 1209
EXPECTED_VALID_MONTHLY_CHANGES = 1203
EXPECTED_NONCONSECUTIVE_PREVIOUS_ROWS = 6

EXPECTED_PKRV_VALID_CHANGES = 1108
EXPECTED_PKISRV_VALID_CHANGES = 95

SOURCE_ORGANIZATION_YIELD = "Mutual Funds Association of Pakistan"

SOURCE_ORGANIZATION_CPI = "Pakistan Bureau of Statistics"

EXPECTED_CPI_SOURCE_FILES = {
    "indices_and_growth_rates_historical-1.pdf",
    "Monthly-Review-July-2026.pdf",
    "Monthly-Review-August-2026.pdf",
    "Monthly-Review-September2026.pdf",
}

EXPECTED_CPI_RUN_IDS = {
    1,
}

EXPECTED_YIELD_RUN_IDS = {
    "PKRV": {
        11,
    },
    "PKISRV": {
        13,
    },
}

PKRV_PARTIAL_MONTHLY_TENORS = {
    "1M",
    "2M",
    "3M",
    "4M",
    "6M",
    "9M",
}

EXPECTED_MONTH_COUNTS = {
    **{
        (
            "PKRV",
            tenor,
        ): (56 if tenor in PKRV_PARTIAL_MONTHLY_TENORS else 57)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 20
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_CHANGE_COUNTS = {
    **{
        (
            "PKRV",
            tenor,
        ): (54 if tenor in PKRV_PARTIAL_MONTHLY_TENORS else 56)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 19
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_MAX_LAG_DAYS = {
    **{
        (
            "PKRV",
            tenor,
        ): (15 if tenor in PKRV_PARTIAL_MONTHLY_TENORS else 3)
        for tenor in PKRV_CANONICAL_TENORS
    },
    **{
        (
            "PKISRV",
            tenor,
        ): 3
        for tenor in PKRV_PKISRV_COMMON_TENORS
    },
}

EXPECTED_MISSING_PKRV_PERIOD = "2023-07"

MONTH_END_METHOD = "LAST_AVAILABLE_OBSERVATION_WITHIN_CALENDAR_MONTH"

MONTHLY_CHANGE_METHOD = "CONSECUTIVE_CALENDAR_MONTH_END"

OUTPUT_FIELDS = [
    "period",
    "curve_type",
    "tenor",
    "tenor_years",
    "observation_count",
    "first_observation_date",
    "month_end_observation_date",
    "calendar_month_end_date",
    "month_end_lag_days",
    "month_end_yield_pct",
    "previous_available_period",
    "previous_month_end_observation_date",
    "previous_month_end_yield_pct",
    "period_gap_months",
    "monthly_yield_change_bps",
    "month_end_method",
    "monthly_change_method",
    "national_cpi_index",
    "cpi_inflation_yoy_pct",
    "cpi_base_year",
    "yield_source_organization",
    "yield_source_file",
    "yield_ingestion_run_id",
    "cpi_source_organization",
    "cpi_source_file",
    "cpi_ingestion_run_id",
]


def decimal_text(
    value: Decimal,
) -> str:
    """Render one finite Decimal without meaningless trailing zeros."""

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


def period_index(
    period: str,
) -> int:
    """Convert YYYY-MM to a monotonically increasing month index."""

    year = int(period[:4])

    month = int(period[5:7])

    if not (1 <= month <= 12):
        raise RuntimeError(f"Invalid period: {period}")

    return year * 12 + month - 1


def calendar_month_end(
    period: str,
) -> date:
    """Return the final calendar date for one YYYY-MM period."""

    year = int(period[:4])

    month = int(period[5:7])

    return date(
        year,
        month,
        calendar.monthrange(
            year,
            month,
        )[1],
    )


def load_source_data() -> tuple[
    dict[
        str,
        dict[
            str,
            object,
        ],
    ],
    list[
        dict[
            str,
            object,
        ]
    ],
]:
    """Load and validate the frozen CPI and yield source observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

        cpi_rows = connection.execute(
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
            WHERE period >= ?
            ORDER BY period
            """,
            (MACRO_SAMPLE_START.strftime("%Y-%m"),),
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
            WHERE observation_date >= ?
            ORDER BY
                curve_type,
                tenor_years,
                tenor,
                observation_date
            """,
            (MACRO_SAMPLE_START.isoformat(),),
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError(f"Production SQLite integrity check failed: {integrity}")

    if foreign_key_issues:
        raise RuntimeError(
            f"Production SQLite foreign-key issues exist: {len(foreign_key_issues)}"
        )

    if len(cpi_rows) != EXPECTED_CPI_PERIODS:
        raise RuntimeError(f"Unexpected CPI row count: {len(cpi_rows)}")

    periods = [row["period"] for row in cpi_rows]

    if periods[0] != EXPECTED_CPI_FIRST or periods[-1] != EXPECTED_CPI_LAST:
        raise RuntimeError("Unexpected CPI coverage")

    for (
        previous,
        current,
    ) in zip(
        periods,
        periods[1:],
        strict=False,
    ):
        if period_index(current) - period_index(previous) != 1:
            raise RuntimeError(
                f"CPI monthly sequence contains a gap: {previous} -> {current}"
            )

    cpi_by_period = {}

    for row in cpi_rows:
        period = row["period"]

        if period in cpi_by_period:
            raise RuntimeError(f"Duplicate CPI period: {period}")

        if row["base_year"] != "2015-16":
            raise RuntimeError(f"Unexpected CPI base year: {period}")

        if row["source_organization"] != SOURCE_ORGANIZATION_CPI:
            raise RuntimeError(f"Unexpected CPI source organization: {period}")

        cpi_index = Decimal(str(row["national_cpi_index"]))

        cpi_yoy = Decimal(str(row["cpi_inflation_yoy_pct"]))

        if not cpi_index.is_finite() or not cpi_yoy.is_finite():
            raise RuntimeError(f"Non-finite CPI value: {period}")

        cpi_by_period[period] = {
            "period": period,
            "national_cpi_index": cpi_index,
            "cpi_inflation_yoy_pct": cpi_yoy,
            "base_year": row["base_year"],
            "source_organization": row["source_organization"],
            "source_file": row["source_file"],
            "ingestion_run_id": int(row["ingestion_run_id"]),
        }

    actual_cpi_files = {row["source_file"] for row in cpi_by_period.values()}

    if actual_cpi_files != EXPECTED_CPI_SOURCE_FILES:
        raise RuntimeError(
            f"CPI source-file universe changed: {sorted(actual_cpi_files)}"
        )

    actual_cpi_runs = {row["ingestion_run_id"] for row in cpi_by_period.values()}

    if actual_cpi_runs != EXPECTED_CPI_RUN_IDS:
        raise RuntimeError(f"CPI ingestion lineage changed: {actual_cpi_runs}")

    normalized_yields = []

    curve_counts = Counter()

    curve_runs = defaultdict(set)

    keys = set()

    for row in yield_rows:
        curve_type = row["curve_type"]

        tenor = row["tenor"]

        observation_date = row["observation_date"]

        if curve_type == "PKRV":
            allowed_tenors = PKRV_CANONICAL_TENORS

        elif curve_type == "PKISRV":
            allowed_tenors = PKRV_PKISRV_COMMON_TENORS

        else:
            raise RuntimeError(f"Unexpected curve type: {curve_type}")

        if tenor not in allowed_tenors:
            raise RuntimeError(f"Unexpected tenor: {curve_type} {tenor}")

        key = (
            observation_date,
            curve_type,
            tenor,
        )

        if key in keys:
            raise RuntimeError(f"Duplicate normalized yield key: {key}")

        keys.add(key)

        if not math.isclose(
            float(row["tenor_years"]),
            TENOR_TO_YEARS[tenor],
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise RuntimeError(f"Unexpected tenor-years mapping: {key}")

        yield_pct = Decimal(str(row["yield_pct"]))

        if not yield_pct.is_finite():
            raise RuntimeError(f"Non-finite yield: {key}")

        if row["source_organization"] != SOURCE_ORGANIZATION_YIELD:
            raise RuntimeError(f"Unexpected yield source organization: {key}")

        ingestion_run_id = int(row["ingestion_run_id"])

        curve_counts[curve_type] += 1

        curve_runs[curve_type].add(ingestion_run_id)

        normalized_yields.append(
            {
                "observation_date": observation_date,
                "curve_type": curve_type,
                "tenor": tenor,
                "tenor_years": float(row["tenor_years"]),
                "yield_pct": yield_pct,
                "source_organization": row["source_organization"],
                "source_file": row["source_file"],
                "ingestion_run_id": ingestion_run_id,
            }
        )

    if dict(curve_counts) != {
        "PKRV": 22800,
        "PKISRV": 2015,
    }:
        raise RuntimeError(f"Unexpected normalized yield counts: {dict(curve_counts)}")

    for (
        curve_type,
        expected_runs,
    ) in EXPECTED_YIELD_RUN_IDS.items():
        if curve_runs[curve_type] != expected_runs:
            raise RuntimeError(
                "Unexpected yield ingestion lineage: "
                f"{curve_type} "
                f"{curve_runs[curve_type]}"
            )

    return (
        cpi_by_period,
        normalized_yields,
    )


def derive_monthly_panel(
    cpi_by_period: dict[
        str,
        dict[
            str,
            object,
        ],
    ],
    yield_rows: list[
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
    """Derive one row per observed curve-tenor-calendar-month cell."""

    monthly = defaultdict(list)

    for row in yield_rows:
        period = row["observation_date"][:7]

        if period not in cpi_by_period:
            raise RuntimeError(f"Yield month has no CPI observation: {period}")

        monthly[
            (
                row["curve_type"],
                row["tenor"],
                period,
            )
        ].append(row)

    rows = []

    curve_tenors = (
        (
            "PKRV",
            tuple(PKRV_CANONICAL_TENORS),
        ),
        (
            "PKISRV",
            tuple(PKRV_PKISRV_COMMON_TENORS),
        ),
    )

    for (
        curve_type,
        tenors,
    ) in curve_tenors:
        for tenor in tenors:
            periods = sorted(
                period
                for (
                    observed_curve,
                    observed_tenor,
                    period,
                ) in monthly
                if (observed_curve == curve_type and observed_tenor == tenor)
            )

            expected_months = EXPECTED_MONTH_COUNTS[
                (
                    curve_type,
                    tenor,
                )
            ]

            if len(periods) != expected_months:
                raise RuntimeError(
                    "Unexpected monthly coverage: "
                    f"{curve_type} {tenor} "
                    f"{len(periods)} "
                    f"!= {expected_months}"
                )

            if curve_type == "PKRV" and tenor in PKRV_PARTIAL_MONTHLY_TENORS:
                if EXPECTED_MISSING_PKRV_PERIOD in periods:
                    raise RuntimeError(
                        "Forbidden manufactured PKRV July 2023 "
                        f"monthly observation: {tenor}"
                    )

            previous_month_row = None

            for period in periods:
                source_rows = sorted(
                    monthly[
                        (
                            curve_type,
                            tenor,
                            period,
                        )
                    ],
                    key=lambda row: row["observation_date"],
                )

                first_source = source_rows[0]

                month_end_source = source_rows[-1]

                calendar_end = calendar_month_end(period)

                actual_month_end = date.fromisoformat(
                    month_end_source["observation_date"]
                )

                lag_days = (calendar_end - actual_month_end).days

                if lag_days < 0:
                    raise RuntimeError(
                        "Month-end source occurs after "
                        "calendar month end: "
                        f"{curve_type} {tenor} {period}"
                    )

                current_yield = month_end_source["yield_pct"]

                if previous_month_row is None:
                    previous_period = ""
                    previous_date = ""
                    previous_yield = ""
                    gap_months = ""
                    monthly_change = ""

                else:
                    previous_period = previous_month_row["period"]

                    previous_date = previous_month_row["month_end_observation_date"]

                    previous_yield_decimal = Decimal(
                        previous_month_row["month_end_yield_pct"]
                    )

                    gap_value = period_index(period) - period_index(previous_period)

                    if gap_value <= 0:
                        raise RuntimeError(
                            "Non-increasing monthly sequence: "
                            f"{curve_type} {tenor} "
                            f"{previous_period} -> {period}"
                        )

                    gap_months = str(gap_value)

                    previous_yield = decimal_text(previous_yield_decimal)

                    if gap_value == 1:
                        monthly_change_decimal = (
                            current_yield - previous_yield_decimal
                        ) * Decimal("100")

                        monthly_change = decimal_text(monthly_change_decimal)

                    else:
                        monthly_change = ""

                cpi = cpi_by_period[period]

                derived_row = {
                    "period": period,
                    "curve_type": curve_type,
                    "tenor": tenor,
                    "tenor_years": format(
                        TENOR_TO_YEARS[tenor],
                        ".12g",
                    ),
                    "observation_count": str(len(source_rows)),
                    "first_observation_date": first_source["observation_date"],
                    "month_end_observation_date": month_end_source["observation_date"],
                    "calendar_month_end_date": calendar_end.isoformat(),
                    "month_end_lag_days": str(lag_days),
                    "month_end_yield_pct": decimal_text(current_yield),
                    "previous_available_period": previous_period,
                    "previous_month_end_observation_date": previous_date,
                    "previous_month_end_yield_pct": previous_yield,
                    "period_gap_months": gap_months,
                    "monthly_yield_change_bps": monthly_change,
                    "month_end_method": MONTH_END_METHOD,
                    "monthly_change_method": MONTHLY_CHANGE_METHOD,
                    "national_cpi_index": decimal_text(cpi["national_cpi_index"]),
                    "cpi_inflation_yoy_pct": decimal_text(cpi["cpi_inflation_yoy_pct"]),
                    "cpi_base_year": cpi["base_year"],
                    "yield_source_organization": month_end_source[
                        "source_organization"
                    ],
                    "yield_source_file": month_end_source["source_file"],
                    "yield_ingestion_run_id": str(month_end_source["ingestion_run_id"]),
                    "cpi_source_organization": cpi["source_organization"],
                    "cpi_source_file": cpi["source_file"],
                    "cpi_ingestion_run_id": str(cpi["ingestion_run_id"]),
                }

                rows.append(derived_row)

                previous_month_row = derived_row

    curve_order = {
        "PKRV": 0,
        "PKISRV": 1,
    }

    tenor_order = {
        tenor: index
        for (
            index,
            tenor,
        ) in enumerate(PKRV_CANONICAL_TENORS)
    }

    rows.sort(
        key=lambda row: (
            row["period"],
            curve_order[row["curve_type"]],
            tenor_order[row["tenor"]],
        )
    )

    return rows


def validate_monthly_panel(
    rows: list[
        dict[
            str,
            str,
        ]
    ],
) -> None:
    """Validate the complete monthly alignment artifact."""

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"Unexpected monthly panel row count: {len(rows)}")

    keys = {
        (
            row["period"],
            row["curve_type"],
            row["tenor"],
        )
        for row in rows
    }

    if len(keys) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Duplicate monthly panel keys detected")

    curve_counts = Counter(row["curve_type"] for row in rows)

    if dict(curve_counts) != {
        "PKRV": EXPECTED_PKRV_ROWS,
        "PKISRV": EXPECTED_PKISRV_ROWS,
    }:
        raise RuntimeError(f"Unexpected monthly curve counts: {dict(curve_counts)}")

    series_counts = Counter(
        (
            row["curve_type"],
            row["tenor"],
        )
        for row in rows
    )

    if dict(series_counts) != EXPECTED_MONTH_COUNTS:
        raise RuntimeError("Monthly series counts changed")

    first_rows = [row for row in rows if (row["previous_available_period"] == "")]

    previous_rows = [row for row in rows if (row["previous_available_period"] != "")]

    valid_change_rows = [row for row in rows if (row["monthly_yield_change_bps"] != "")]

    gap_break_rows = [row for row in previous_rows if (row["period_gap_months"] != "1")]

    if len(first_rows) != EXPECTED_FIRST_SERIES_ROWS:
        raise RuntimeError(f"Unexpected first monthly series rows: {len(first_rows)}")

    if len(previous_rows) != EXPECTED_ROWS_WITH_PREVIOUS_AVAILABLE:
        raise RuntimeError(
            f"Unexpected rows with previous available month: {len(previous_rows)}"
        )

    if len(valid_change_rows) != EXPECTED_VALID_MONTHLY_CHANGES:
        raise RuntimeError(
            f"Unexpected valid monthly change count: {len(valid_change_rows)}"
        )

    if len(gap_break_rows) != EXPECTED_NONCONSECUTIVE_PREVIOUS_ROWS:
        raise RuntimeError(
            f"Unexpected nonconsecutive monthly rows: {len(gap_break_rows)}"
        )

    expected_gap_keys = {
        (
            "2023-08",
            "PKRV",
            tenor,
        )
        for tenor in PKRV_PARTIAL_MONTHLY_TENORS
    }

    actual_gap_keys = {
        (
            row["period"],
            row["curve_type"],
            row["tenor"],
        )
        for row in gap_break_rows
    }

    if actual_gap_keys != expected_gap_keys:
        raise RuntimeError(
            f"Monthly gap-break universe changed: {sorted(actual_gap_keys)}"
        )

    change_counts = Counter(
        (
            row["curve_type"],
            row["tenor"],
        )
        for row in valid_change_rows
    )

    if dict(change_counts) != EXPECTED_CHANGE_COUNTS:
        raise RuntimeError("Per-series monthly change counts changed")

    max_lags = defaultdict(int)

    for row in rows:
        key = (
            row["curve_type"],
            row["tenor"],
        )

        lag = int(row["month_end_lag_days"])

        max_lags[key] = max(
            max_lags[key],
            lag,
        )

        month_end_date = date.fromisoformat(row["month_end_observation_date"])

        expected_calendar_end = calendar_month_end(row["period"])

        if row["calendar_month_end_date"] != expected_calendar_end.isoformat():
            raise RuntimeError(f"Calendar month-end mismatch: {row['period']} {key}")

        expected_lag = (expected_calendar_end - month_end_date).days

        if lag != expected_lag:
            raise RuntimeError(f"Month-end lag mismatch: {row['period']} {key}")

        if row["month_end_method"] != MONTH_END_METHOD:
            raise RuntimeError("Unexpected month-end method")

        if row["monthly_change_method"] != MONTHLY_CHANGE_METHOD:
            raise RuntimeError("Unexpected monthly change method")

        if row["cpi_base_year"] != "2015-16":
            raise RuntimeError("Unexpected CPI base year in panel")

        if row["yield_source_organization"] != SOURCE_ORGANIZATION_YIELD:
            raise RuntimeError("Unexpected yield source organization in monthly panel")

        if row["cpi_source_organization"] != SOURCE_ORGANIZATION_CPI:
            raise RuntimeError("Unexpected CPI source organization in monthly panel")

    if dict(max_lags) != EXPECTED_MAX_LAG_DAYS:
        raise RuntimeError("Maximum month-end lag census changed")

    stale_rows = [row for row in rows if (int(row["month_end_lag_days"]) > 3)]

    expected_stale_keys = {
        (
            "2023-06",
            "PKRV",
            tenor,
        )
        for tenor in PKRV_PARTIAL_MONTHLY_TENORS
    }

    actual_stale_keys = {
        (
            row["period"],
            row["curve_type"],
            row["tenor"],
        )
        for row in stale_rows
    }

    if actual_stale_keys != expected_stale_keys:
        raise RuntimeError(
            "Unexpected >3-day month-end staleness "
            f"universe: {sorted(actual_stale_keys)}"
        )

    for row in stale_rows:
        if (
            row["month_end_observation_date"] != "2023-06-15"
            or row["calendar_month_end_date"] != "2023-06-30"
            or row["month_end_lag_days"] != "15"
        ):
            raise RuntimeError("June 2023 partial-tenor staleness changed")

    for row in first_rows:
        if any(
            row[field] != ""
            for field in (
                "previous_month_end_observation_date",
                "previous_month_end_yield_pct",
                "period_gap_months",
                "monthly_yield_change_bps",
            )
        ):
            raise RuntimeError(
                "First monthly row contains manufactured predecessor values"
            )

    for row in gap_break_rows:
        if (
            row["previous_available_period"] != "2023-06"
            or row["period"] != "2023-08"
            or row["period_gap_months"] != "2"
            or row["monthly_yield_change_bps"] != ""
        ):
            raise RuntimeError("July 2023 missing-period handling changed")

    for row in valid_change_rows:
        if row["period_gap_months"] != "1":
            raise RuntimeError(
                "Monthly change calculated across nonconsecutive periods"
            )

        current_yield = Decimal(row["month_end_yield_pct"])

        previous_yield = Decimal(row["previous_month_end_yield_pct"])

        expected_change = (current_yield - previous_yield) * Decimal("100")

        actual_change = Decimal(row["monthly_yield_change_bps"])

        if actual_change != expected_change:
            raise RuntimeError(
                "Monthly yield-change arithmetic mismatch: "
                f"{row['period']} "
                f"{row['curve_type']} "
                f"{row['tenor']}"
            )


def main() -> None:
    """Build the deterministic monthly CPI/yield alignment panel."""

    (
        cpi_by_period,
        yield_rows,
    ) = load_source_data()

    rows = derive_monthly_panel(
        cpi_by_period,
        yield_rows,
    )

    validate_monthly_panel(rows)

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

    curve_counts = Counter(row["curve_type"] for row in rows)

    first_rows = [row for row in rows if not row["previous_available_period"]]

    previous_rows = [row for row in rows if row["previous_available_period"]]

    valid_changes = [row for row in rows if row["monthly_yield_change_bps"]]

    gap_breaks = [row for row in previous_rows if (row["period_gap_months"] != "1")]

    stale_rows = [row for row in rows if (int(row["month_end_lag_days"]) > 3)]

    largest_changes = sorted(
        valid_changes,
        key=lambda row: abs(Decimal(row["monthly_yield_change_bps"])),
        reverse=True,
    )[:15]

    output_sha = sha256_file(OUTPUT_PATH)

    print("===== MONTHLY CPI / YIELD ALIGNMENT PANEL =====")

    print(
        "Panel rows:",
        len(rows),
    )

    print(
        "PKRV rows:",
        curve_counts["PKRV"],
    )

    print(
        "PKISRV rows:",
        curve_counts["PKISRV"],
    )

    print(
        "Distinct periods:",
        len({row["period"] for row in rows}),
    )

    print(
        "Coverage:",
        min(row["period"] for row in rows),
        "through",
        max(row["period"] for row in rows),
    )

    print(
        "First-series rows:",
        len(first_rows),
    )

    print(
        "Rows with previous available month:",
        len(previous_rows),
    )

    print(
        "Valid consecutive monthly changes:",
        len(valid_changes),
    )

    print(
        "Nonconsecutive previous-month rows:",
        len(gap_breaks),
    )

    print("")
    print("Valid changes by curve:")

    valid_change_counts = Counter(row["curve_type"] for row in valid_changes)

    print(
        "  PKRV:",
        valid_change_counts["PKRV"],
    )

    print(
        "  PKISRV:",
        valid_change_counts["PKISRV"],
    )

    print("")
    print("Explicit missing-month gap rows:")

    for row in gap_breaks:
        print(
            " ",
            row["curve_type"],
            row["tenor"],
            row["previous_available_period"],
            "->",
            row["period"],
            "gap_months=",
            row["period_gap_months"],
            "change_bps=",
            repr(row["monthly_yield_change_bps"]),
        )

    print("")
    print("Rows with month-end lag > 3 days:")

    for row in stale_rows:
        print(
            " ",
            row["period"],
            row["curve_type"],
            row["tenor"],
            "last_observation=",
            row["month_end_observation_date"],
            "calendar_month_end=",
            row["calendar_month_end_date"],
            "lag_days=",
            row["month_end_lag_days"],
        )

    print("")
    print("Largest absolute consecutive monthly yield changes:")

    for row in largest_changes:
        print(
            " ",
            row["curve_type"],
            row["tenor"],
            row["previous_available_period"],
            "->",
            row["period"],
            row["previous_month_end_yield_pct"],
            "->",
            row["month_end_yield_pct"],
            "change_bps=",
            row["monthly_yield_change_bps"],
            "current_source_date=",
            row["month_end_observation_date"],
        )

    print("")
    print("CPI sentinels:")

    for period in (
        "2022-01",
        "2023-06",
        "2023-07",
        "2023-08",
        "2025-02",
        "2026-07",
        "2026-08",
        "2026-09",
    ):
        cpi = cpi_by_period[period]

        print(
            " ",
            period,
            "index=",
            decimal_text(cpi["national_cpi_index"]),
            "yoy_pct=",
            decimal_text(cpi["cpi_inflation_yoy_pct"]),
            "source_file=",
            cpi["source_file"],
            "run=",
            cpi["ingestion_run_id"],
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
    print("PASS: deterministic monthly CPI/yield alignment contract satisfied")


if __name__ == "__main__":
    main()
