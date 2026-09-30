"""Build structural census for the frozen SBP policy-rate raw artifact."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "sbp" / "policy_rate" / "data_series.csv"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_policy_rate_structural_census.csv"
)

EXPECTED_SHA256 = "4dbf6d69a8ece64bd45e9f3fc8bdb0424d77ded1169b04e68696c5ee8d702420"

EXPECTED_SIZE_BYTES = 6559
EXPECTED_OBSERVATIONS = 39

EXPECTED_FIRST_DATE = "2015-05-25"
EXPECTED_LAST_DATE = "2026-04-28"

EXPECTED_DATASET = "Structure of Interest Rate: State Bank of Pakistan Policy Rates"

EXPECTED_SERIES_KEY = "TS_GP_IR_SIRPR_AH.SBPOL0030"

EXPECTED_SERIES = "SBP Policy (Target) Rate"

EXPECTED_UNIT = "Percent"

EXPECTED_SOURCE_STATUS = "Normal"

EXPECTED_HEADER = [
    "Dataset",
    "Series Key",
    "Series",
    "Observation Date",
    "Observation Value",
    "Unit",
    "Observation Status",
    "Observation Status Comment",
]

OUTPUT_FIELDS = [
    "raw_file_name",
    "dataset",
    "series_key",
    "series",
    "observation_date",
    "observation_value",
    "unit",
    "observation_status",
    "observation_status_comment",
    "structural_class",
    "validation_status",
]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def validate_raw_identity() -> None:
    """Verify that the frozen raw artifact matches its accepted identity."""

    assert RAW_PATH.exists(), f"SBP policy-rate raw artifact missing: {RAW_PATH}"

    size = RAW_PATH.stat().st_size
    digest = sha256_file(RAW_PATH)

    assert size == EXPECTED_SIZE_BYTES, (
        "SBP policy-rate raw file size changed: "
        f"expected {EXPECTED_SIZE_BYTES}, found {size}"
    )

    assert digest == EXPECTED_SHA256, (
        "SBP policy-rate raw SHA-256 changed: "
        f"expected {EXPECTED_SHA256}, found {digest}"
    )


def validate_provenance() -> None:
    """Verify one-to-one provenance for the frozen raw artifact."""

    assert PROVENANCE_PATH.exists(), (
        f"Raw provenance manifest missing: {PROVENANCE_PATH}"
    )

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = [
            row
            for row in csv.DictReader(file)
            if row["dataset_id"] == "SBP_POLICY_RATE"
        ]

    assert len(rows) == 1, (
        f"Expected exactly one SBP_POLICY_RATE provenance row, found {len(rows)}"
    )

    row = rows[0]

    expected_relative_path = RAW_PATH.relative_to(PROJECT_ROOT).as_posix()

    assert row["source_authority"] == ("State Bank of Pakistan")

    assert row["acquisition_source"] == ("SBP EasyData browser download")

    assert row["raw_file_name"] == RAW_PATH.name

    assert row["raw_relative_path"] == expected_relative_path

    assert row["file_format"] == "csv"

    assert row["sha256"] == EXPECTED_SHA256

    assert int(row["file_size_bytes"]) == EXPECTED_SIZE_BYTES

    assert row["status"] == "SUCCESS"


def load_source_rows() -> list[dict[str, str]]:
    """Load and validate the source CSV envelope."""

    raw = RAW_PATH.read_bytes()

    assert not raw.startswith(
        (
            b"\xef\xbb\xbf",
            b"\xff\xfe",
            b"\xfe\xff",
        )
    ), "Unexpected BOM detected in SBP policy-rate raw CSV"

    text = raw.decode("utf-8")

    lines = text.splitlines()

    assert lines, "SBP policy-rate raw CSV is empty"

    reader = csv.DictReader(lines)

    assert reader.fieldnames == EXPECTED_HEADER, (
        f"Unexpected SBP policy-rate CSV header: {reader.fieldnames}"
    )

    return list(reader)


def classify_row(
    row: dict[str, str],
    duplicate_date: bool,
) -> tuple[str, str]:
    """Classify one SBP policy-rate source observation."""

    issues: list[str] = []

    if row["Dataset"] != EXPECTED_DATASET:
        issues.append("BAD_DATASET")

    if row["Series Key"] != EXPECTED_SERIES_KEY:
        issues.append("BAD_SERIES_KEY")

    if row["Series"] != EXPECTED_SERIES:
        issues.append("BAD_SERIES")

    if row["Unit"] != EXPECTED_UNIT:
        issues.append("BAD_UNIT")

    if row["Observation Status"] != EXPECTED_SOURCE_STATUS:
        issues.append("BAD_SOURCE_STATUS")

    if row["Observation Status Comment"] != "":
        issues.append("NONEMPTY_STATUS_COMMENT")

    date_text = row["Observation Date"].strip()

    try:
        datetime.strptime(
            date_text,
            "%d-%b-%Y",
        )
    except ValueError:
        issues.append("UNPARSEABLE_DATE")

    value_text = row["Observation Value"].strip()

    try:
        value = Decimal(value_text)

        if value <= 0:
            issues.append("NONPOSITIVE_VALUE")

        if value >= Decimal("100"):
            issues.append("IMPLAUSIBLE_VALUE")

    except InvalidOperation:
        issues.append("UNPARSEABLE_VALUE")

    if duplicate_date:
        issues.append("DUPLICATE_DATE")

    if issues:
        return (
            "|".join(issues),
            "REVIEW",
        )

    return (
        "VALID_OBSERVATION",
        "ACCEPTED",
    )


def main() -> None:
    """Build and persist the SBP policy-rate structural census."""

    validate_raw_identity()
    validate_provenance()

    source_rows = load_source_rows()

    assert len(source_rows) == EXPECTED_OBSERVATIONS, (
        "Unexpected SBP policy-rate observation count: "
        f"expected {EXPECTED_OBSERVATIONS}, "
        f"found {len(source_rows)}"
    )

    raw_dates = [row["Observation Date"].strip() for row in source_rows]

    date_counts = Counter(raw_dates)

    results: list[dict[str, str]] = []

    parsed_dates = []

    for row in source_rows:
        date_text = row["Observation Date"].strip()

        duplicate_date = date_counts[date_text] > 1

        structural_class, validation_status = classify_row(
            row,
            duplicate_date,
        )

        try:
            parsed_date = datetime.strptime(
                date_text,
                "%d-%b-%Y",
            ).date()

            canonical_date = parsed_date.isoformat()

            parsed_dates.append(parsed_date)

        except ValueError:
            canonical_date = ""

        results.append(
            {
                "raw_file_name": RAW_PATH.name,
                "dataset": row["Dataset"],
                "series_key": row["Series Key"],
                "series": row["Series"],
                "observation_date": canonical_date,
                "observation_value": row["Observation Value"].strip(),
                "unit": row["Unit"],
                "observation_status": row["Observation Status"],
                "observation_status_comment": row["Observation Status Comment"],
                "structural_class": structural_class,
                "validation_status": validation_status,
            }
        )

    assert len(results) == EXPECTED_OBSERVATIONS

    review = [row for row in results if row["validation_status"] != "ACCEPTED"]

    assert not review, (
        f"SBP policy-rate structural census contains {len(review)} review rows"
    )

    assert len(parsed_dates) == EXPECTED_OBSERVATIONS

    assert len(set(parsed_dates)) == EXPECTED_OBSERVATIONS, (
        "SBP policy-rate source contains duplicate dates"
    )

    descending = parsed_dates == sorted(
        parsed_dates,
        reverse=True,
    )

    assert descending, "SBP policy-rate source is not in descending date order"

    first_date = min(parsed_dates).isoformat()
    last_date = max(parsed_dates).isoformat()

    assert first_date == EXPECTED_FIRST_DATE, f"Unexpected first date: {first_date}"

    assert last_date == EXPECTED_LAST_DATE, f"Unexpected last date: {last_date}"

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
        writer.writerows(results)

    temporary.replace(OUTPUT_PATH)

    classes = Counter(row["structural_class"] for row in results)

    statuses = Counter(row["validation_status"] for row in results)

    year_counts = Counter(
        row["observation_date"][:4]
        for row in results
        if row["validation_status"] == "ACCEPTED"
    )

    values = [
        Decimal(row["observation_value"])
        for row in results
        if row["validation_status"] == "ACCEPTED"
    ]

    print("")
    print("===== SBP POLICY RATE STRUCTURAL CENSUS =====")

    print(
        "Rows:",
        len(results),
    )

    print("")
    print("===== STRUCTURAL CLASSES =====")

    for name, count in sorted(classes.items()):
        print(
            name,
            count,
        )

    print("")
    print("===== VALIDATION STATUS =====")

    for name, count in sorted(statuses.items()):
        print(
            name,
            count,
        )

    print("")
    print("===== DATE COVERAGE =====")

    print(
        "First chronological date:",
        first_date,
    )

    print(
        "Last chronological date:",
        last_date,
    )

    print(
        "Unique dates:",
        len(set(parsed_dates)),
    )

    print(
        "Descending source order:",
        descending,
    )

    print("")
    print("===== VALUE COVERAGE =====")

    print(
        "Minimum rate:",
        min(values),
    )

    print(
        "Maximum rate:",
        max(values),
    )

    print("")
    print("===== ACCEPTED BY YEAR =====")

    for year, count in sorted(year_counts.items()):
        print(
            year,
            count,
        )

    print("")
    print("===== REVIEW RECORDS =====")

    print(
        "Count:",
        len(review),
    )

    for row in review:
        print(
            row["observation_date"] or "<UNPARSEABLE_DATE>",
            "|",
            row["structural_class"],
        )

    print("")
    print(
        "Raw SHA-256:",
        sha256_file(RAW_PATH),
    )

    print(
        "Raw bytes:",
        RAW_PATH.stat().st_size,
    )

    print(
        "Manifest:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )

    print("")
    print("PASS: SBP policy-rate structural census complete")


if __name__ == "__main__":
    main()
