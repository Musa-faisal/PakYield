"""Tests for rolling matched-yield correlation."""

from __future__ import annotations

import pytest

from pakyield.analytics.rolling_correlation import rolling_yield_correlations


def row(day: str, tenor: str, pkrv: str, pkisrv: str) -> dict[str, str]:
    return {
        "observation_date": day,
        "tenor": tenor,
        "pkrv_yield_pct": pkrv,
        "pkisrv_yield_pct": pkisrv,
    }


def test_full_window_is_required_and_positive_correlation_is_correct() -> None:
    rows = [
        row("2026-01-03", "1Y", "3", "6"),
        row("2026-01-01", "1Y", "1", "2"),
        row("2026-01-02", "1Y", "2", "4"),
    ]

    result = rolling_yield_correlations(rows, 3)

    assert [item["observation_date"] for item in result] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
    ]
    assert result[0]["correlation"] is None
    assert result[1]["correlation"] is None
    assert result[2]["correlation"] == pytest.approx(1.0)


def test_negative_correlation_is_correct() -> None:
    rows = [
        row("2026-01-01", "3M", "1", "3"),
        row("2026-01-02", "3M", "2", "2"),
        row("2026-01-03", "3M", "3", "1"),
    ]

    result = rolling_yield_correlations(rows, 3)

    assert result[-1]["correlation"] == pytest.approx(-1.0)


def test_constant_series_has_no_defined_correlation() -> None:
    rows = [
        row("2026-01-01", "1Y", "1", "2"),
        row("2026-01-02", "1Y", "1", "3"),
        row("2026-01-03", "1Y", "1", "4"),
    ]

    result = rolling_yield_correlations(rows, 3)

    assert result[-1]["correlation"] is None


def test_duplicate_dates_are_rejected() -> None:
    rows = [
        row("2026-01-01", "1Y", "1", "2"),
        row("2026-01-01", "1Y", "2", "3"),
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        rolling_yield_correlations(rows, 2)


def test_mixed_maturities_are_rejected() -> None:
    rows = [
        row("2026-01-01", "3M", "1", "2"),
        row("2026-01-02", "1Y", "2", "3"),
    ]

    with pytest.raises(ValueError, match="maturity"):
        rolling_yield_correlations(rows, 2)


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="window"):
        rolling_yield_correlations([], 1)
