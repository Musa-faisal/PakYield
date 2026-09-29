"""PKRV raw-artifact decoding and tenor-normalization utilities."""

from __future__ import annotations

import re

from pakyield.config import PKRV_CANONICAL_TENORS

CANONICAL_TENORS = tuple(tenor.upper() for tenor in PKRV_CANONICAL_TENORS)

CANONICAL_TENOR_SET = set(CANONICAL_TENORS)

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

DAY_BUCKET_PATTERNS = (
    (re.compile(r"(?<!\d)(?:0|1)\s*-\s*7\s*days?", re.IGNORECASE), "1W"),
    (re.compile(r"(?<!\d)8\s*-\s*15\s*days?", re.IGNORECASE), "2W"),
    (re.compile(r"(?<!\d)16\s*-\s*30\s*days?", re.IGNORECASE), "1M"),
    (re.compile(r"(?<!\d)31\s*-\s*60\s*days?", re.IGNORECASE), "2M"),
    (re.compile(r"(?<!\d)61\s*-\s*90\s*days?", re.IGNORECASE), "3M"),
    (re.compile(r"(?<!\d)91\s*-\s*120\s*days?", re.IGNORECASE), "4M"),
    (re.compile(r"(?<!\d)121\s*-\s*180\s*days?", re.IGNORECASE), "6M"),
    (re.compile(r"(?<!\d)181\s*-\s*270\s*days?", re.IGNORECASE), "9M"),
    (re.compile(r"(?<!\d)271\s*-\s*365\s*days?", re.IGNORECASE), "1Y"),
)


def decode_text_bytes(raw: bytes) -> tuple[str, str]:
    """Decode legacy MUFAP text bytes without modifying the source."""

    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"

    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252"


def canonicalize_tenor(
    number: int,
    unit: str,
) -> str | None:
    """Convert conservative tenor aliases into canonical PKRV labels."""

    normalized = unit.upper()

    if normalized in {
        "W",
        "WK",
        "WKS",
        "WEEK",
        "WEEKS",
    }:
        candidate = f"{number}W"

    elif normalized in {
        "M",
        "MO",
        "MOS",
        "MON",
        "MONTH",
        "MONTHS",
    }:
        candidate = "1Y" if number == 12 else f"{number}M"

    elif normalized in {
        "Y",
        "YR",
        "YRS",
        "YEAR",
        "YEARS",
    }:
        candidate = f"{number}Y"

    else:
        return None

    if candidate in CANONICAL_TENOR_SET:
        return candidate

    return None


def extract_canonical_tenors(
    text: str,
) -> set[str]:
    """Extract direct, aliased, and legacy day-bucket PKRV tenors."""

    normalized_text = text.replace("–", "-").replace("—", "-")

    found: set[str] = set()

    for match in TENOR_PATTERN.finditer(normalized_text):
        candidate = canonicalize_tenor(
            int(match.group(1)),
            match.group(2),
        )

        if candidate is not None:
            found.add(candidate)

    for pattern, tenor in DAY_BUCKET_PATTERNS:
        if pattern.search(normalized_text):
            found.add(tenor)

    return found
