"""Tests for Yield Curve Lab selection and model-status handling."""

from __future__ import annotations

import pytest
from app.components.yield_curve_lab import (
    find_fit_status,
    select_curve_snapshot,
    select_tenor_history,
)


def test_snapshot_uses_exact_curve_and_date_and_sorts_tenors() -> None:
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

    result = select_curve_snapshot(rows, "PKRV", "2026-01-02")

    assert [row["tenor"] for row in result] == ["3M", "1Y"]
    assert all(row["curve_type"] == "PKRV" for row in result)
    assert all(row["observation_date"] == "2026-01-02" for row in result)


def test_history_uses_exact_curve_and_tenor_in_date_order() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-03",
            "tenor": "1Y",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-01",
            "tenor": "1Y",
        },
        {
            "curve_type": "PKISRV",
            "observation_date": "2026-01-02",
            "tenor": "1Y",
        },
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "tenor": "3M",
        },
    ]

    result = select_tenor_history(rows, "PKRV", "1Y")

    assert [row["observation_date"] for row in result] == [
        "2026-01-01",
        "2026-01-03",
    ]


def test_fit_status_preserves_ineligible_result() -> None:
    rows = [
        {
            "curve_type": "PKISRV",
            "observation_date": "2026-01-02",
            "fit_status": "INELIGIBLE",
            "ineligibility_reason": "POINTS_LT_10",
        }
    ]

    result = find_fit_status(rows, "PKISRV", "2026-01-02")

    assert result is not None
    assert result["fit_status"] == "INELIGIBLE"
    assert result["ineligibility_reason"] == "POINTS_LT_10"


def test_fit_status_returns_none_when_date_is_missing() -> None:
    rows = [
        {
            "curve_type": "PKRV",
            "observation_date": "2026-01-02",
            "fit_status": "FIT",
        }
    ]

    assert find_fit_status(rows, "PKRV", "2026-01-03") is None


def test_duplicate_fit_status_is_rejected() -> None:
    row = {
        "curve_type": "PKRV",
        "observation_date": "2026-01-02",
        "fit_status": "FIT",
    }

    with pytest.raises(ValueError, match="More than one"):
        find_fit_status([row, row], "PKRV", "2026-01-02")
