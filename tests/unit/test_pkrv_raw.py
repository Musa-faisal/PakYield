"""Tests for PKRV raw decoding and tenor normalization."""

from pakyield.validation.pkrv_raw import (
    CANONICAL_TENOR_SET,
    decode_text_bytes,
    extract_canonical_tenors,
)


def test_decode_utf8() -> None:
    text, encoding = decode_text_bytes(b"Tenor,Mid Rate,Change\n1Y,10.00,0.00\n")

    assert encoding == "utf-8"
    assert "Tenor" in text


def test_decode_utf8_bom() -> None:
    raw = b"\xef\xbb\xbfTenor,Mid Rate,Change\n"

    text, encoding = decode_text_bytes(raw)

    assert encoding == "utf-8-sig"
    assert text.startswith("Tenor")


def test_decode_utf16() -> None:
    raw = ("FINANCIAL MARKET ASSOCIATION PKRV").encode("utf-16")

    text, encoding = decode_text_bytes(raw)

    assert encoding == "utf-16"
    assert "PKRV" in text


def test_full_legacy_curve_normalization() -> None:
    text = """
    0-7days
    8-15days
    16-30days
    31-60days
    61-90days
    91-120days
    121-180days
    181-270days
    271-365days
    2years
    3years
    4years
    5years
    6years
    7years
    8years
    9years
    10years
    15years
    20years
    """

    assert extract_canonical_tenors(text) == CANONICAL_TENOR_SET


def test_partial_legacy_curve_remains_partial() -> None:
    text = """
    1wk
    2wk
    1y
    2y
    3y
    4y
    5y
    6y
    7y
    8y
    9y
    10y
    15y
    20y
    """

    tenors = extract_canonical_tenors(text)

    assert len(tenors) == 14

    assert {
        "1M",
        "2M",
        "3M",
        "4M",
        "6M",
        "9M",
    }.isdisjoint(tenors)
