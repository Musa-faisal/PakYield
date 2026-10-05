"""Build the validated monthly Pakistan National CPI source manifest."""

from __future__ import annotations

import csv
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pbs" / "cpi"

OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "pbs_cpi_monthly_validated.csv"

DIAGNOSTIC_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "pbs_cpi_cross_publication_diagnostic.csv"
)

HISTORICAL_FILE = "indices_and_growth_rates_historical-1.pdf"

MONTHLY_FILES = {
    "2026-07": "Monthly-Review-July-2026.pdf",
    "2026-08": "Monthly-Review-August-2026.pdf",
    "2026-09": "Monthly-Review-September2026.pdf",
}

EXPECTED_ROWS = 57

OUTPUT_FIELDS = [
    "period",
    "national_cpi_index",
    "cpi_inflation_yoy_pct",
    "cpi_inflation_mom_pct",
    "source_file",
    "source_role",
    "index_source_precision_dp",
    "yoy_source_precision_dp",
    "validation_status",
]

DIAGNOSTIC_FIELDS = [
    "current_period",
    "comparison_period",
    "historical_index",
    "monthly_review_prior_year_index",
    "difference_index_points",
    "disposition",
]

HISTORICAL_ROW = re.compile(
    r"^\s*"
    r"(?P<year>20\d{2})"
    r"\s+"
    r"(?P<month>1[0-2]|[1-9])"
    r"\s+"
    r"(?P<national>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<urban>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<rural>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<wpi>[+-]?\d+(?:\.\d+)?)"
    r"(?:\s+.*)?$"
)

GENERAL_ROW = re.compile(
    r"\bGeneral"
    r"\s+100(?:\.0+)?"
    r"\s+"
    r"(?P<current>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<previous>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<prior_year>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<mom>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<yoy>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<impact_mom>[+-]?\d+(?:\.\d+)?)"
    r"\s+"
    r"(?P<impact_yoy>[+-]?\d+(?:\.\d+)?)",
    flags=re.IGNORECASE,
)


def extract_text(
    path: Path,
) -> str:
    """Extract embedded text from a PBS PDF."""

    with pdfplumber.open(str(path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def monthly_sequence(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> list[str]:
    """Return an inclusive sequence of YYYY-MM periods."""

    periods = []

    year = start_year
    month = start_month

    while year < end_year or (year == end_year and month <= end_month):
        periods.append(f"{year:04d}-{month:02d}")

        month += 1

        if month == 13:
            month = 1
            year += 1

    return periods


def parse_historical(
    text: str,
) -> tuple[
    dict[str, Decimal],
    dict[str, Decimal],
]:
    """Parse National index and YoY tables from the historical publication."""

    marker = "Historical Inflation Rate (Y-oY)"

    assert marker in text

    index_text, inflation_text = text.split(
        marker,
        1,
    )

    indices: dict[
        str,
        Decimal,
    ] = {}

    yoy: dict[
        str,
        Decimal,
    ] = {}

    for raw_line in index_text.splitlines():
        match = HISTORICAL_ROW.match(raw_line)

        if match is None:
            continue

        period = f"{int(match.group('year')):04d}-{int(match.group('month')):02d}"

        value = Decimal(match.group("national"))

        if period in indices:
            assert indices[period] == value
        else:
            indices[period] = value

    for raw_line in inflation_text.splitlines():
        match = HISTORICAL_ROW.match(raw_line)

        if match is None:
            continue

        period = f"{int(match.group('year')):04d}-{int(match.group('month')):02d}"

        value = Decimal(match.group("national"))

        if period in yoy:
            assert yoy[period] == value
        else:
            yoy[period] = value

    return (
        indices,
        yoy,
    )


def parse_monthly_review(
    path: Path,
) -> dict[str, Decimal]:
    """Parse the National General row from one PBS monthly review."""

    text = extract_text(path)

    lowered = text.lower()

    start = lowered.find("i. national consumer price index (ncpi)")

    assert start >= 0, f"National CPI section missing: {path.name}"

    end = lowered.find(
        "ii. urban consumer price index",
        start,
    )

    assert end > start, f"Urban CPI boundary missing: {path.name}"

    section = text[start:end]

    matches = list(GENERAL_ROW.finditer(section))

    assert len(matches) == 1, (
        f"Expected one National General row in {path.name}; found {len(matches)}"
    )

    match = matches[0]

    return {
        "current_index": Decimal(match.group("current")),
        "previous_index": Decimal(match.group("previous")),
        "prior_year_index": Decimal(match.group("prior_year")),
        "mom_pct": Decimal(match.group("mom")),
        "yoy_pct": Decimal(match.group("yoy")),
    }


def decimal_text(
    value: Decimal | None,
) -> str:
    """Render Decimal while preserving source precision."""

    if value is None:
        return ""

    return format(
        value,
        "f",
    )


def build_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
]:
    """Build analytical source rows and cross-publication diagnostics."""

    historical_path = RAW_DIR / HISTORICAL_FILE

    assert historical_path.exists()

    historical_text = extract_text(historical_path)

    (
        historical_indices,
        historical_yoy,
    ) = parse_historical(historical_text)

    historical_periods = monthly_sequence(
        2022,
        1,
        2026,
        6,
    )

    assert len(historical_periods) == 54

    assert all(period in historical_indices for period in historical_periods)

    assert all(period in historical_yoy for period in historical_periods)

    reviews = {}

    for period, name in MONTHLY_FILES.items():
        path = RAW_DIR / name

        assert path.exists()

        reviews[period] = parse_monthly_review(path)

    # June historical -> July review overlap.
    assert historical_indices["2026-06"] == reviews["2026-07"][
        "previous_index"
    ].quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )

    # Exact two-decimal overlap between successive reviews.
    assert reviews["2026-07"]["current_index"] == reviews["2026-08"]["previous_index"]

    assert reviews["2026-08"]["current_index"] == reviews["2026-09"]["previous_index"]

    rows = []

    for period in historical_periods:
        rows.append(
            {
                "period": period,
                "national_cpi_index": decimal_text(historical_indices[period]),
                "cpi_inflation_yoy_pct": decimal_text(historical_yoy[period]),
                "cpi_inflation_mom_pct": "",
                "source_file": HISTORICAL_FILE,
                "source_role": "HISTORICAL_SERIES",
                "index_source_precision_dp": "1",
                "yoy_source_precision_dp": "1",
                "validation_status": "SOURCE_EXPLICIT",
            }
        )

    for period in (
        "2026-07",
        "2026-08",
        "2026-09",
    ):
        parsed = reviews[period]

        rows.append(
            {
                "period": period,
                "national_cpi_index": decimal_text(parsed["current_index"]),
                "cpi_inflation_yoy_pct": decimal_text(parsed["yoy_pct"]),
                "cpi_inflation_mom_pct": decimal_text(parsed["mom_pct"]),
                "source_file": MONTHLY_FILES[period],
                "source_role": "MONTHLY_REVIEW",
                "index_source_precision_dp": "2",
                "yoy_source_precision_dp": "2",
                "validation_status": "SOURCE_EXPLICIT",
            }
        )

    expected_periods = monthly_sequence(
        2022,
        1,
        2026,
        9,
    )

    assert len(rows) == EXPECTED_ROWS

    assert [row["period"] for row in rows] == expected_periods

    assert len({row["period"] for row in rows}) == EXPECTED_ROWS

    diagnostics = []

    for current_period in (
        "2026-07",
        "2026-08",
        "2026-09",
    ):
        year, month = (int(piece) for piece in current_period.split("-"))

        comparison_period = f"{year - 1:04d}-{month:02d}"

        historical_value = historical_indices[comparison_period]

        monthly_value = reviews[current_period]["prior_year_index"]

        difference = monthly_value - historical_value

        diagnostics.append(
            {
                "current_period": current_period,
                "comparison_period": comparison_period,
                "historical_index": decimal_text(historical_value),
                "monthly_review_prior_year_index": decimal_text(monthly_value),
                "difference_index_points": decimal_text(difference),
                "disposition": ("DIAGNOSTIC_ONLY_NO_RETROACTIVE_REPLACEMENT"),
            }
        )

    assert len(diagnostics) == 3

    return (
        rows,
        diagnostics,
    )


def write_csv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Write one tracked validation artifact atomically."""

    temporary = path.with_suffix(path.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def main() -> None:
    """Build both validated PBS CPI manifests."""

    (
        rows,
        diagnostics,
    ) = build_rows()

    write_csv(
        OUTPUT_PATH,
        OUTPUT_FIELDS,
        rows,
    )

    write_csv(
        DIAGNOSTIC_PATH,
        DIAGNOSTIC_FIELDS,
        diagnostics,
    )

    print("===== PBS CPI MONTHLY BUILD =====")

    print(
        "Validated monthly rows:",
        len(rows),
    )

    print(
        "First period:",
        rows[0]["period"],
    )

    print(
        "Last period:",
        rows[-1]["period"],
    )

    print(
        "Historical-source rows:",
        sum(row["source_role"] == "HISTORICAL_SERIES" for row in rows),
    )

    print(
        "Monthly-review rows:",
        sum(row["source_role"] == "MONTHLY_REVIEW" for row in rows),
    )

    print(
        "Cross-publication diagnostics:",
        len(diagnostics),
    )

    print("")
    print("PASS: PBS CPI monthly validation artifacts built")


if __name__ == "__main__":
    main()
