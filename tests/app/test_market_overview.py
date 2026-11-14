"""Tests for exact-date Market Overview calculations."""

from __future__ import annotations

import pytest
from app.components.market_overview import curve_snapshot, matched_curve_changes


def test_snapshot_uses_exact_curve_and_date_and_sorts_maturities() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
            "yield_pct": "12.0",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "3M",
            "tenor_years": "0.25",
            "yield_pct": "11.0",
        },
        {
            "curve_type": "PKISRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
            "yield_pct": "12.5",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-01",
            "tenor": "1Y",
            "tenor_years": "1",
            "yield_pct": "11.5",
        },
    ]

    result = curve_snapshot(rows, "PKRV", "2026-01-02")

    assert [row["tenor"] for row in result] == ["3M", "1Y"]
    assert all(row["observation_date"] == "2026-01-02" for row in result)
    assert all(row["curve_type"] == "PKRV" for row in result)


def test_changes_use_only_matched_tenors_and_percentage_units() -> None:
    current = [
        {"tenor": "3M", "tenor_years": "0.25", "yield_pct": "12.20"},
        {"tenor": "1Y", "tenor_years": "1", "yield_pct": "12.50"},
    ]
    comparison = [
        {"tenor": "3M", "tenor_years": "0.25", "yield_pct": "12.00"},
        {"tenor": "5Y", "tenor_years": "5", "yield_pct": "13.00"},
    ]

    result = matched_curve_changes(current, comparison)

    assert len(result) == 1
    assert result[0]["tenor"] == "3M"
    assert result[0]["change_bps"] == pytest.approx(20.0)


def test_changes_are_empty_when_no_tenors_match() -> None:
    current = [{"tenor": "3M", "tenor_years": "0.25", "yield_pct": "12"}]
    comparison = [{"tenor": "1Y", "tenor_years": "1", "yield_pct": "12"}]

    assert matched_curve_changes(current, comparison) == []
