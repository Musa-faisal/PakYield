"""Tests for Monetary Policy Lab event selection and eligibility."""

from __future__ import annotations

from app.components.monetary_policy_lab import (
    eligible_reactions,
    select_event_rows,
)


def test_event_selection_is_exact_and_sorts_by_maturity() -> None:
    rows = [
        {
            "event_date": "2026-01-01",
            "curve_type": "PKRV",
            "half_window": "1",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "event_date": "2026-01-01",
            "curve_type": "PKRV",
            "half_window": "1",
            "tenor": "3M",
            "tenor_years": "0.25",
        },
        {
            "event_date": "2026-01-01",
            "curve_type": "PKRV",
            "half_window": "3",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "event_date": "2026-01-02",
            "curve_type": "PKRV",
            "half_window": "1",
            "tenor": "1Y",
            "tenor_years": "1",
        },
        {
            "event_date": "2026-01-01",
            "curve_type": "PKISRV",
            "half_window": "1",
            "tenor": "1Y",
            "tenor_years": "1",
        },
    ]

    result = select_event_rows(rows, "2026-01-01", "PKRV", "1")

    assert [row["tenor"] for row in result] == ["3M", "1Y"]


def test_only_eligible_recorded_values_are_returned() -> None:
    rows = [
        {"tenor": "3M", "eligibility_status": "ELIGIBLE", "window_change_bps": "0"},
        {"tenor": "1Y", "eligibility_status": "INELIGIBLE", "window_change_bps": ""},
        {"tenor": "5Y", "eligibility_status": "ELIGIBLE", "window_change_bps": ""},
    ]

    result = eligible_reactions(rows)

    assert [row["tenor"] for row in result] == ["3M"]
    assert result[0]["window_change_bps"] == "0"


def test_no_matching_event_returns_empty_list() -> None:
    rows = [
        {
            "event_date": "2026-01-01",
            "curve_type": "PKRV",
            "half_window": "1",
            "tenor": "1Y",
            "tenor_years": "1",
        }
    ]

    assert select_event_rows(rows, "2026-01-02", "PKRV", "1") == []
