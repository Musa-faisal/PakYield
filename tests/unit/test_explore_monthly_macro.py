"""Tests for exploratory monthly policy-rate alignment."""

from __future__ import annotations

from datetime import date

from scripts.explore_monthly_macro import (
    build_sample,
    month_boundaries,
    policy_rate_on,
)


def test_month_boundaries_handle_year_end_and_leap_year() -> None:
    assert month_boundaries("2026-01") == (
        date(2025, 12, 31),
        date(2026, 1, 31),
    )

    assert month_boundaries("2024-02") == (
        date(2024, 1, 31),
        date(2024, 2, 29),
    )


def test_policy_state_uses_effective_date_without_looking_forward() -> None:
    dates = [date(2025, 12, 15), date(2026, 1, 15)]
    rates = [10.0, 11.0]

    assert policy_rate_on(date(2025, 12, 14), dates, rates) is None
    assert policy_rate_on(date(2025, 12, 31), dates, rates) == 10.0
    assert policy_rate_on(date(2026, 1, 15), dates, rates) == 11.0
    assert policy_rate_on(date(2026, 1, 31), dates, rates) == 11.0


def test_sample_uses_complete_rows_and_month_end_policy_change() -> None:
    rows = [
        {
            "period": "2026-01",
            "curve_type": "PKRV",
            "tenor": "1Y",
            "monthly_yield_change_bps": "25",
            "cpi_inflation_yoy_pct": "7.5",
        },
        {
            "period": "2026-02",
            "curve_type": "PKRV",
            "tenor": "1Y",
            "monthly_yield_change_bps": "",
            "cpi_inflation_yoy_pct": "8.0",
        },
    ]

    dates = [date(2025, 12, 15), date(2026, 1, 15)]
    rates = [10.0, 11.0]

    frame, exclusions = build_sample(rows, "1Y", dates, rates)

    assert len(frame) == 1
    assert frame.iloc[0]["yield_change_bps"] == 25.0
    assert frame.iloc[0]["policy_change_pct_points"] == 1.0
    assert frame.iloc[0]["inflation_yoy_pct"] == 7.5
    assert exclusions["missing_yield_change_or_cpi"] == 1


def test_longest_consecutive_sample_does_not_bridge_missing_months() -> None:
    import pandas as pd
    from scripts.explore_monthly_macro import longest_consecutive_sample

    frame = pd.DataFrame(
        {
            "period": [
                "2024-01",
                "2024-02",
                "2024-04",
                "2024-05",
                "2024-06",
            ]
        }
    )

    result = longest_consecutive_sample(frame)

    assert result["period"].tolist() == ["2024-04", "2024-05", "2024-06"]


def test_longest_consecutive_sample_uses_most_recent_run_on_tie() -> None:
    import pandas as pd
    from scripts.explore_monthly_macro import longest_consecutive_sample

    frame = pd.DataFrame(
        {
            "period": [
                "2024-01",
                "2024-02",
                "2024-04",
                "2024-05",
            ]
        }
    )

    result = longest_consecutive_sample(frame)

    assert result["period"].tolist() == ["2024-04", "2024-05"]
