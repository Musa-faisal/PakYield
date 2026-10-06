"""Build deterministic long-form normalized PKISRV observations."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pakyield.config import (
    PKRV_PKISRV_COMMON_TENORS,
    PROJECT_ROOT,
    TENOR_TO_YEARS,
)

STRUCTURAL_PATH = PROJECT_ROOT / "data" / "manifests" / "pkisrv_structural_census.csv"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkisrv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "pkisrv_normalized_long.csv"

SOURCE_ORGANIZATION = "Mutual Funds Association of Pakistan"

SOURCE_LAYOUT = "CSV_PKISRV_RATES"

SOURCE_VALUE_FIELD = "PKISRV Rates (Yields)"

EXPECTED_MANIFEST_ROWS = 407
EXPECTED_ACCEPTED_DATES = 403
EXPECTED_ABSENT_DATES = 4
EXPECTED_ROWS = 2015

FIRST_ACCEPTED_DATE = "2025-02-03"

LAST_ACCEPTED_DATE = "2026-09-30"

EXPECTED_TENORS = tuple(PKRV_PKISRV_COMMON_TENORS)

EXPECTED_TENOR_SET = set(EXPECTED_TENORS)

EXPECTED_ABSENT_DATE_SET = {
    "2025-03-07",
    "2025-08-20",
    "2026-03-18",
    "2026-03-27",
}

EXPECTED_YEAR_DATE_COUNTS = {
    "2025": 224,
    "2026": 179,
}

EXPECTED_YEAR_ROW_COUNTS = {
    "2025": 1120,
    "2026": 895,
}

EXPECTED_TENOR_COUNTS = {tenor: EXPECTED_ACCEPTED_DATES for tenor in EXPECTED_TENORS}

EXPECTED_RAW_LABELS = {
    "1 - Month": "1M",
    "3 - Month": "3M",
    "6 - Month": "6M",
    "9 - Month": "9M",
    "1 - Year": "1Y",
}

EXPECTED_HEADER_TENOR = "Tenor"

EXPECTED_HEADER_VALUE = "PKISRV Rates (Yields)"

# Zero-based:
# (
#     tenor_column,
#     value_column,
#     tenor_row_width,
# )
#
# Counts were exhaustively verified across all
# 403 accepted COMPLETE_5 source artifacts.
EXPECTED_SIGNATURE_COUNTS = {
    (
        6,
        7,
        8,
    ): 241,
    (
        5,
        6,
        7,
    ): 94,
    (
        5,
        6,
        8,
    ): 56,
    (
        5,
        6,
        9,
    ): 5,
    (
        5,
        6,
        10,
    ): 2,
    (
        6,
        7,
        9,
    ): 2,
    (
        11,
        12,
        13,
    ): 1,
    (
        12,
        13,
        14,
    ): 1,
    (
        4,
        5,
        6,
    ): 1,
}

OUTPUT_FIELDS = [
    "observation_date",
    "tenor",
    "tenor_years",
    "yield_pct",
    "source_organization",
    "source_file",
    "structural_class",
    "source_layout",
    "source_value_field",
]

EXPECTED_SENTINELS = {
    "2025-02-03": {
        "1M": Decimal("10.70"),
        "3M": Decimal("10.42"),
        "6M": Decimal("17.71"),
        "9M": Decimal("13.50"),
        "1Y": Decimal("18.86"),
    },
    "2025-02-04": {
        "1M": Decimal("10.84"),
        "3M": Decimal("10.51"),
        "6M": Decimal("10.21"),
        "9M": Decimal("11.28"),
        "1Y": Decimal("10.97"),
    },
    "2025-02-14": {
        "1M": Decimal("10.13"),
        "3M": Decimal("10.29"),
        "6M": Decimal("10.65"),
        "9M": Decimal("11.47"),
        "1Y": Decimal("10.95"),
    },
    "2025-03-04": {
        "1M": Decimal("10.54"),
        "3M": Decimal("10.61"),
        "6M": Decimal("11.11"),
        "9M": Decimal("11.64"),
        "1Y": Decimal("10.93"),
    },
    "2026-03-02": {
        "1M": Decimal("7.76"),
        "3M": Decimal("8.76"),
        "6M": Decimal("10.26"),
        "9M": Decimal("10.23"),
        "1Y": Decimal("10.63"),
    },
    "2026-04-02": {
        "1M": Decimal("8.49"),
        "3M": Decimal("9.40"),
        "6M": Decimal("10.77"),
        "9M": Decimal("10.86"),
        "1Y": Decimal("10.82"),
    },
    "2026-06-04": {
        "1M": Decimal("9.84"),
        "3M": Decimal("10.58"),
        "6M": Decimal("10.94"),
        "9M": Decimal("10.87"),
        "1Y": Decimal("10.81"),
    },
    "2026-06-18": {
        "1M": Decimal("11.83"),
        "3M": Decimal("11.15"),
        "6M": Decimal("10.63"),
        "9M": Decimal("10.79"),
        "1Y": Decimal("10.83"),
    },
    "2026-09-25": {
        "1M": Decimal("10.75"),
        "3M": Decimal("10.04"),
        "6M": Decimal("10.75"),
        "9M": Decimal("12.55"),
        "1Y": Decimal("10.85"),
    },
}


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one UTF-8 manifest CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def clean_cell(
    value: object,
) -> str:
    """Normalize source cell whitespace only."""

    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def normalize_source_label(
    value: object,
) -> str:
    """Normalize dash variants and whitespace in one source label."""

    text = clean_cell(value)

    text = (
        text.replace(
            "–",
            "-",
        )
        .replace(
            "—",
            "-",
        )
        .replace(
            "−",
            "-",
        )
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def parse_percentage(
    value: object,
    *,
    context: str,
) -> Decimal:
    """Parse one source PKISRV percentage without rescaling."""

    text = clean_cell(value)

    if not text:
        raise RuntimeError(f"Blank PKISRV yield: {context}")

    if not text.endswith("%"):
        raise RuntimeError(
            "PKISRV source value is missing explicit "
            f"percent marker: {context}: {text!r}"
        )

    numeric_text = (
        text[:-1]
        .replace(
            ",",
            "",
        )
        .strip()
    )

    try:
        result = Decimal(numeric_text)

    except InvalidOperation as exc:
        raise RuntimeError(f"Invalid PKISRV yield {text!r}: {context}") from exc

    if not result.is_finite():
        raise RuntimeError(f"Non-finite PKISRV yield {text!r}: {context}")

    if not (Decimal("0") < result < Decimal("100")):
        raise RuntimeError(f"Implausible PKISRV yield {result}: {context}")

    return result


def decimal_text(
    value: Decimal,
) -> str:
    """Render Decimal without scientific notation or meaningless zeros."""

    text = format(
        value,
        "f",
    )

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    return text


def read_source_rows(
    path: Path,
) -> list[list[str]]:
    """Read one accepted UTF-8 PKISRV CSV source."""

    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(
            f"Accepted PKISRV artifact unexpectedly contains UTF-8 BOM: {path.name}"
        )

    try:
        text = raw.decode("utf-8")

    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"Accepted PKISRV artifact is not UTF-8: {path.name}"
        ) from exc

    rows = [list(row) for row in csv.reader(text.splitlines())]

    if not rows:
        raise RuntimeError(f"Empty accepted PKISRV artifact: {path.name}")

    return rows


def parse_artifact(
    path: Path,
) -> tuple[
    dict[str, Decimal],
    tuple[int, int, int],
]:
    """Parse one accepted five-tenor PKISRV benchmark block."""

    if path.suffix.lower() != ".csv":
        raise RuntimeError(f"Accepted PKISRV artifact is not CSV: {path.name}")

    rows = read_source_rows(path)

    occurrences: dict[
        str,
        list[
            tuple[
                int,
                int,
                str,
                str,
            ]
        ],
    ] = defaultdict(list)

    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            raw_label = normalize_source_label(value)

            tenor = EXPECTED_RAW_LABELS.get(raw_label)

            if tenor is None:
                continue

            if column_index + 1 >= len(row):
                raise RuntimeError(
                    f"PKISRV tenor has no adjacent value: {path.name} {tenor}"
                )

            occurrences[tenor].append(
                (
                    row_index,
                    column_index,
                    raw_label,
                    clean_cell(row[column_index + 1]),
                )
            )

    if set(occurrences) != EXPECTED_TENOR_SET:
        raise RuntimeError(
            "Accepted PKISRV tenor set changed: "
            f"{path.name}; "
            f"actual={sorted(occurrences)}"
        )

    for tenor in EXPECTED_TENORS:
        if len(occurrences[tenor]) != 1:
            raise RuntimeError(
                "PKISRV tenor occurrence count changed: "
                f"{path.name} {tenor}; "
                f"count={len(occurrences[tenor])}"
            )

    ordered = sorted(
        (
            values[0][0],
            values[0][1],
            tenor,
            values[0][2],
            values[0][3],
        )
        for tenor, values in occurrences.items()
    )

    ordered_tenors = tuple(item[2] for item in ordered)

    if ordered_tenors != EXPECTED_TENORS:
        raise RuntimeError(
            f"PKISRV tenor order changed: {path.name}; {ordered_tenors!r}"
        )

    row_indices = tuple(item[0] for item in ordered)

    tenor_columns = tuple(item[1] for item in ordered)

    if any(
        current != previous + 1
        for previous, current in zip(
            row_indices,
            row_indices[1:],
            strict=False,
        )
    ):
        raise RuntimeError(
            f"PKISRV benchmark rows are not contiguous: {path.name}; {row_indices!r}"
        )

    if len(set(tenor_columns)) != 1:
        raise RuntimeError(
            f"PKISRV tenor column changes within block: {path.name}; {tenor_columns!r}"
        )

    tenor_column = tenor_columns[0]

    value_column = tenor_column + 1

    row_widths = tuple(len(rows[row_index]) for row_index in row_indices)

    if len(set(row_widths)) != 1:
        raise RuntimeError(
            "PKISRV benchmark row widths differ within block: "
            f"{path.name}; "
            f"{row_widths!r}"
        )

    row_width = row_widths[0]

    if value_column >= row_width:
        raise RuntimeError(f"PKISRV value column is outside benchmark row: {path.name}")

    first_tenor_row = row_indices[0]

    header_index = first_tenor_row - 1

    if header_index < 0:
        raise RuntimeError(f"PKISRV benchmark header is missing: {path.name}")

    header = rows[header_index]

    if value_column >= len(header):
        raise RuntimeError(f"PKISRV benchmark header is too short: {path.name}")

    actual_tenor_header = clean_cell(header[tenor_column])

    actual_value_header = clean_cell(header[value_column])

    if actual_tenor_header != EXPECTED_HEADER_TENOR:
        raise RuntimeError(
            f"Unexpected PKISRV tenor header: {path.name}; {actual_tenor_header!r}"
        )

    if actual_value_header != EXPECTED_HEADER_VALUE:
        raise RuntimeError(
            f"Unexpected PKISRV value header: {path.name}; {actual_value_header!r}"
        )

    values: dict[str, Decimal] = {}

    for (
        _,
        observed_column,
        tenor,
        raw_label,
        raw_value,
    ) in ordered:
        if observed_column != tenor_column:
            raise RuntimeError(
                f"PKISRV tenor column changed unexpectedly: {path.name} {tenor}"
            )

        expected_raw_label = next(
            label
            for label, canonical in EXPECTED_RAW_LABELS.items()
            if canonical == tenor
        )

        if raw_label != expected_raw_label:
            raise RuntimeError(
                f"PKISRV raw tenor label changed: {path.name} {tenor}; {raw_label!r}"
            )

        values[tenor] = parse_percentage(
            raw_value,
            context=(f"{path.name} {tenor}"),
        )

    signature = (
        tenor_column,
        value_column,
        row_width,
    )

    return (
        values,
        signature,
    )


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 of one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def main() -> None:
    """Build and validate the complete PKISRV long-form artifact."""

    manifest = read_csv(STRUCTURAL_PATH)

    if len(manifest) != EXPECTED_MANIFEST_ROWS:
        raise RuntimeError(
            f"PKISRV structural manifest row count changed: {len(manifest)}"
        )

    accepted = [
        row
        for row in manifest
        if (
            row["structural_class"] == "COMPLETE_5"
            and row["validation_status"] == "ACCEPTED"
        )
    ]

    absent = [
        row
        for row in manifest
        if (
            row["structural_class"] == "ABSENT" and row["validation_status"] == "REVIEW"
        )
    ]

    if len(accepted) != EXPECTED_ACCEPTED_DATES:
        raise RuntimeError(f"Accepted PKISRV date count changed: {len(accepted)}")

    if len(absent) != EXPECTED_ABSENT_DATES:
        raise RuntimeError(f"ABSENT PKISRV date count changed: {len(absent)}")

    other = [row for row in manifest if row not in accepted and row not in absent]

    if other:
        raise RuntimeError(f"Unexpected PKISRV structural records exist: {len(other)}")

    actual_absent_dates = {row["observation_date"] for row in absent}

    if actual_absent_dates != EXPECTED_ABSENT_DATE_SET:
        raise RuntimeError(
            f"PKISRV source-level ABSENT dates changed: {sorted(actual_absent_dates)}"
        )

    canonical_string = "|".join(EXPECTED_TENORS)

    for row in absent:
        if (
            row["tenor_count"] != "0"
            or row["found_tenors"] != ""
            or row["missing_tenors"] != canonical_string
            or row["duplicate_tenors"] != ""
            or row["unparseable_tenors"] != ""
        ):
            raise RuntimeError(
                f"PKISRV ABSENT source contract changed: {row['observation_date']}"
            )

    accepted.sort(key=lambda row: row["observation_date"])

    if accepted[0]["observation_date"] != FIRST_ACCEPTED_DATE:
        raise RuntimeError("Unexpected first accepted PKISRV date")

    if accepted[-1]["observation_date"] != LAST_ACCEPTED_DATE:
        raise RuntimeError("Unexpected final accepted PKISRV date")

    accepted_year_counts = Counter(row["observation_date"][:4] for row in accepted)

    if dict(accepted_year_counts) != EXPECTED_YEAR_DATE_COUNTS:
        raise RuntimeError(
            f"Accepted PKISRV year counts changed: {dict(accepted_year_counts)}"
        )

    output: list[
        dict[
            str,
            str,
        ]
    ] = []

    signature_counts = Counter()

    date_row_counts = Counter()

    parsed_by_date: dict[
        str,
        dict[
            str,
            Decimal,
        ],
    ] = {}

    for metadata in accepted:
        observation_date = metadata["observation_date"]

        file_name = metadata["file_name"]

        if (
            metadata["extension"] != ".csv"
            or metadata["detected_format"] != "CSV_TEXT"
            or metadata["detected_encoding"] != "utf-8"
            or metadata["tenor_count"] != "5"
            or metadata["found_tenors"] != canonical_string
            or metadata["missing_tenors"] != ""
            or metadata["duplicate_tenors"] != ""
            or metadata["unparseable_tenors"] != ""
        ):
            raise RuntimeError(
                "Accepted PKISRV structural contract changed: "
                f"{observation_date} {file_name}"
            )

        path = RAW_DIR / file_name

        if not path.is_file():
            raise RuntimeError(f"Accepted PKISRV raw artifact missing: {file_name}")

        (
            values,
            signature,
        ) = parse_artifact(path)

        if set(values) != EXPECTED_TENOR_SET:
            raise RuntimeError(f"Parsed PKISRV tenor set changed: {file_name}")

        signature_counts[signature] += 1

        parsed_by_date[observation_date] = values

        for tenor in EXPECTED_TENORS:
            output.append(
                {
                    "observation_date": observation_date,
                    "tenor": tenor,
                    "tenor_years": format(
                        TENOR_TO_YEARS[tenor],
                        ".12g",
                    ),
                    "yield_pct": decimal_text(values[tenor]),
                    "source_organization": SOURCE_ORGANIZATION,
                    "source_file": file_name,
                    "structural_class": "COMPLETE_5",
                    "source_layout": SOURCE_LAYOUT,
                    "source_value_field": SOURCE_VALUE_FIELD,
                }
            )

            date_row_counts[observation_date] += 1

    if dict(signature_counts) != EXPECTED_SIGNATURE_COUNTS:
        raise RuntimeError(
            f"PKISRV source-layout signature census changed: {dict(signature_counts)}"
        )

    if len(output) != EXPECTED_ROWS:
        raise RuntimeError(
            f"Unexpected normalized PKISRV row count: {len(output)} != {EXPECTED_ROWS}"
        )

    keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in output
    }

    if len(keys) != EXPECTED_ROWS:
        raise RuntimeError("Duplicate normalized PKISRV date-tenor keys detected")

    if any(
        (
            absent_date,
            tenor,
        )
        in keys
        for absent_date in EXPECTED_ABSENT_DATE_SET
        for tenor in EXPECTED_TENORS
    ):
        raise RuntimeError(
            "Source-level ABSENT PKISRV date was manufactured into normalized output"
        )

    observed_date_distribution = Counter(date_row_counts.values())

    if dict(observed_date_distribution) != {
        5: EXPECTED_ACCEPTED_DATES,
    }:
        raise RuntimeError(
            f"Unexpected PKISRV per-date row counts: {dict(observed_date_distribution)}"
        )

    tenor_counts = Counter(row["tenor"] for row in output)

    if dict(tenor_counts) != EXPECTED_TENOR_COUNTS:
        raise RuntimeError(
            f"Unexpected normalized PKISRV tenor counts: {dict(tenor_counts)}"
        )

    year_row_counts = Counter(row["observation_date"][:4] for row in output)

    if dict(year_row_counts) != EXPECTED_YEAR_ROW_COUNTS:
        raise RuntimeError(f"Unexpected PKISRV rows by year: {dict(year_row_counts)}")

    for (
        observation_date,
        expected_values,
    ) in EXPECTED_SENTINELS.items():
        actual_values = parsed_by_date.get(observation_date)

        if actual_values is None:
            raise RuntimeError(f"PKISRV sentinel date missing: {observation_date}")

        for (
            tenor,
            expected_value,
        ) in expected_values.items():
            actual_value = actual_values.get(tenor)

            if actual_value != expected_value:
                raise RuntimeError(
                    "PKISRV sentinel mismatch "
                    f"{observation_date} "
                    f"{tenor}: "
                    f"{actual_value} "
                    f"!= {expected_value}"
                )

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

        writer.writerows(output)

    temporary.replace(OUTPUT_PATH)

    output_sha = sha256_file(OUTPUT_PATH)

    print("===== PKISRV NORMALIZED LONG FORM =====")

    print(
        "Accepted COMPLETE_5 dates:",
        len(accepted),
    )

    print(
        "Source-level ABSENT dates:",
        len(absent),
    )

    print(
        "Normalized rows:",
        len(output),
    )

    print(
        "Unique date-tenor keys:",
        len(keys),
    )

    print(
        "Date row-count distribution:",
        dict(sorted(observed_date_distribution.items())),
    )

    print(
        "Rows by year:",
        dict(sorted(year_row_counts.items())),
    )

    print("")
    print("Source-layout signatures:")

    for (
        signature,
        count,
    ) in sorted(signature_counts.items()):
        print(
            " ",
            signature,
            count,
        )

    print("")
    print("Tenor counts:")

    for tenor in EXPECTED_TENORS:
        print(
            " ",
            tenor,
            tenor_counts[tenor],
        )

    print("")
    print("Excluded ABSENT dates:")

    for observation_date in sorted(EXPECTED_ABSENT_DATE_SET):
        print(
            " ",
            observation_date,
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
    print("PASS: deterministic PKISRV long-form normalization contract satisfied")


if __name__ == "__main__":
    main()
