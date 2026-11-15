"""Tests for exact-date Home dashboard curve selection."""

from __future__ import annotations

from app.components.home_dashboard import select_observed_curve


def test_selection_uses_exact_curve_and_date() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "curve_type": "PKISRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-01",
            "tenor": "1Y",
            "tenor_years": "1",
        },
    ]

    result = select_observed_curve(rows, "PKRV", "2026-01-02")

    assert len(result) == 1
    assert result[0]["curve_type"] == "PKRV"
    assert result[0]["observation_date"] == "2026-01-02"


def test_selection_sorts_by_observed_maturity() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "3M",
            "tenor_years": "0.25",
        },
    ]

    result = select_observed_curve(rows, "PKRV", "2026-01-02")

    assert [row["tenor"] for row in result] == ["3M", "1Y"]


def test_missing_date_returns_no_observations() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
            "tenor_years": "1",
        }
    ]

    assert select_observed_curve(rows, "PKRV", "2026-01-03") == []
