"""Tests for exact-match cross-curve presentation selection."""

from __future__ import annotations

from app.components.cross_curve_lab import (
    history_for_tenor,
    pairs_for_date,
    select_eligible_pairs,
)


def test_only_complete_eligible_matched_pairs_are_selected() -> None:
    rows = [
        {
            "tenor": "3M",
            "paired_comparison_status": "ELIGIBLE",
            "match_status": "MATCHED",
            "pkrv_yield_pct": "12",
            "pkisrv_yield_pct": "12.2",
            "pkisrv_minus_pkrv_bps": "20",
        },
        {
            "tenor": "6M",
            "paired_comparison_status": "INELIGIBLE",
            "match_status": "MATCHED",
            "pkrv_yield_pct": "12",
            "pkisrv_yield_pct": "12.2",
            "pkisrv_minus_pkrv_bps": "20",
        },
        {
            "tenor": "1Y",
            "paired_comparison_status": "ELIGIBLE",
            "match_status": "MATCHED",
            "pkrv_yield_pct": "12",
            "pkisrv_yield_pct": "",
            "pkisrv_minus_pkrv_bps": "",
        },
        {
            "tenor": "9M",
            "paired_comparison_status": "ELIGIBLE",
            "match_status": "MATCHED",
            "pkrv_yield_pct": "12",
            "pkisrv_yield_pct": "12",
            "pkisrv_minus_pkrv_bps": "0",
        },
    ]

    result = select_eligible_pairs(rows)

    assert [row["tenor"] for row in result] == ["3M", "9M"]


def test_snapshot_uses_exact_date_and_sorts_by_maturity() -> None:
    rows = [
        {"observation_date": "2026-01-02", "tenor": "1Y", "tenor_years": "1"},
        {"observation_date": "2026-01-02", "tenor": "3M", "tenor_years": "0.25"},
        {"observation_date": "2026-01-01", "tenor": "6M", "tenor_years": "0.5"},
    ]

    result = pairs_for_date(rows, "2026-01-02")

    assert [row["tenor"] for row in result] == ["3M", "1Y"]


def test_history_uses_exact_tenor_and_sorts_by_date() -> None:
    rows = [
        {"observation_date": "2026-01-03", "tenor": "1Y"},
        {"observation_date": "2026-01-01", "tenor": "1Y"},
        {"observation_date": "2026-01-02", "tenor": "3M"},
    ]

    result = history_for_tenor(rows, "1Y")

    assert [row["observation_date"] for row in result] == [
        "2026-01-01",
        "2026-01-03",
    ]


def test_missing_date_returns_no_pairs() -> None:
    rows = [{"observation_date": "2026-01-01", "tenor": "1Y", "tenor_years": "1"}]

    assert pairs_for_date(rows, "2026-01-02") == []
