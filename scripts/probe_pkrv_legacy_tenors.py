"""Probe legacy PKRV files for alternate tenor notation."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from pakyield.config import PKRV_CANONICAL_TENORS

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkrv"

CENSUS_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_structural_census.csv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_legacy_tenor_probe.csv"

FIELDS = [
    "file_name",
    "original_exact_tenor_count",
    "normalized_tenor_count",
    "normalized_tenors",
    "missing_after_normalization",
    "raw_tenor_tokens",
    "dataset_hints",
    "audit_classification",
]

CANONICAL = tuple(tenor.upper() for tenor in PKRV_CANONICAL_TENORS)

CANONICAL_SET = set(CANONICAL)

TENOR_PATTERN = re.compile(
    r"(?<![A-Z0-9])"
    r"0*(\d{1,2})"
    r"\s*[-_/]?\s*"
    r"("
    r"WEEKS?|WKS?|WK|W"
    r"|MONTHS?|MON|MOS|MO|M"
    r"|YEARS?|YRS?|YR|Y"
    r")"
    r"(?![A-Z0-9])",
    flags=re.IGNORECASE,
)


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read a CSV manifest."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def canonicalize(
    number: int,
    unit: str,
) -> str | None:
    """Map conservative legacy tenor notation to PakYield canonical tenor."""

    normalized_unit = unit.upper()

    week_units = {
        "W",
        "WK",
        "WKS",
        "WEEK",
        "WEEKS",
    }

    month_units = {
        "M",
        "MO",
        "MOS",
        "MON",
        "MONTH",
        "MONTHS",
    }

    year_units = {
        "Y",
        "YR",
        "YRS",
        "YEAR",
        "YEARS",
    }

    if normalized_unit in week_units:
        candidate = f"{number}W"

    elif normalized_unit in month_units:
        if number == 12:
            candidate = "1Y"
        else:
            candidate = f"{number}M"

    elif normalized_unit in year_units:
        candidate = f"{number}Y"

    else:
        return None

    if candidate in CANONICAL_SET:
        return candidate

    return None


def scan_text(
    text: str,
) -> tuple[set[str], list[str]]:
    """Find conservative tenor-like tokens anywhere in source text."""

    found: set[str] = set()
    raw_matches: list[str] = []

    for match in TENOR_PATTERN.finditer(text):
        number = int(match.group(1))

        unit = match.group(2)

        canonical = canonicalize(
            number,
            unit,
        )

        if canonical is None:
            continue

        token = match.group(0).strip()

        found.add(canonical)

        rendered = f"{token}->{canonical}"

        if rendered not in raw_matches:
            raw_matches.append(rendered)

    return found, raw_matches


def classification(
    *,
    found: set[str],
    dataset_hints: str,
) -> str:
    """Assign an audit-only classification."""

    hints = set(part for part in dataset_hints.split("|") if part)

    obvious_non_pkrv = {
        "PKFRV_FILENAME",
        "FLOATING_RATE_PIB_CONTENT",
        "KIBOR_CONTENT",
        "ISLAMIC_CONTENT",
    }

    if hints & obvious_non_pkrv:
        return "NON_PKRV_CONTENT_HINT"

    if found == CANONICAL_SET:
        return "FULL_20_AFTER_NORMALIZATION"

    if found:
        return "PARTIAL_AFTER_NORMALIZATION"

    return "UNRESOLVED_NO_TENORS"


def main() -> None:
    """Probe all structurally reviewed source files."""

    census = read_csv(CENSUS_PATH)

    review = [row for row in census if row["full_20_tenors"] != "TRUE"]

    if len(review) != 150:
        raise RuntimeError(f"Expected 150 structural-review files; found {len(review)}")

    output: list[dict[str, str]] = []

    for row in review:
        path = RAW_DIR / row["file_name"]

        if not path.is_file():
            raise FileNotFoundError(path)

        if path.suffix.lower() != ".csv":
            raise RuntimeError(f"Unexpected non-CSV review file: {path.name}")

        text = path.read_bytes().decode(
            "utf-8-sig",
            errors="replace",
        )

        found, raw_tokens = scan_text(text)

        missing = [tenor for tenor in CANONICAL if tenor not in found]

        audit_class = classification(
            found=found,
            dataset_hints=row["dataset_hints"],
        )

        output.append(
            {
                "file_name": row["file_name"],
                "original_exact_tenor_count": row["canonical_tenor_count"],
                "normalized_tenor_count": str(len(found)),
                "normalized_tenors": "|".join(
                    tenor for tenor in CANONICAL if tenor in found
                ),
                "missing_after_normalization": "|".join(missing),
                "raw_tenor_tokens": "|".join(raw_tokens),
                "dataset_hints": row["dataset_hints"],
                "audit_classification": (audit_class),
            }
        )

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(output)

    temporary.replace(OUTPUT_PATH)

    classes = Counter(row["audit_classification"] for row in output)

    coverage = Counter(int(row["normalized_tenor_count"]) for row in output)

    print("===== LEGACY TENOR PROBE =====")

    print(
        "Review files:",
        len(output),
    )

    print("")
    print("===== NORMALIZED COVERAGE =====")

    for count in sorted(
        coverage,
        reverse=True,
    ):
        print(
            f"{count:2d} tenors:",
            coverage[count],
        )

    print("")
    print("===== AUDIT CLASSIFICATIONS =====")

    for name, count in sorted(classes.items()):
        print(
            name,
            count,
        )

    print("")
    print("===== NON-PKRV HINTS =====")

    for row in output:
        if row["audit_classification"] == "NON_PKRV_CONTENT_HINT":
            print(
                row["file_name"],
                "|",
                row["normalized_tenor_count"],
                "tenors",
                "|",
                row["dataset_hints"],
            )

    print("")
    print("===== STILL UNRESOLVED =====")

    unresolved = [
        row for row in output if row["audit_classification"] == "UNRESOLVED_NO_TENORS"
    ]

    print(
        "Count:",
        len(unresolved),
    )

    for row in unresolved:
        print(
            row["file_name"],
            "|",
            row["dataset_hints"],
        )

    print("")
    print(
        "Probe:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )


if __name__ == "__main__":
    main()
