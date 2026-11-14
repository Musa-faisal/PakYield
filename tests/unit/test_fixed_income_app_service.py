"""Tests for Phase 13 fixed-income application wiring."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data import (
    fixed_income_analysis,
    fixed_income_price_curve,
)

from pakyield.fixed_income import (
    analyze_fixed_rate_bullet,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAGE_PATH = PROJECT_ROOT / "app" / "pages" / "5_Fixed_Income_Risk.py"

SERVICE_PATH = PROJECT_ROOT / "app" / "services" / "data.py"


def test_service_core_metrics_match_tested_backend() -> None:
    """Application service must preserve backend valuation outputs."""

    service = fixed_income_analysis(
        face_value=1000.0,
        coupon_rate_pct=5.0,
        ytm_pct=5.0,
        years_to_maturity=5.0,
        coupon_frequency=2,
        rate_shock_bps=100,
    )

    backend = analyze_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.05,
        ytm=0.05,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert service["price"] == pytest.approx(backend.price)

    assert service["macaulay_duration_years"] == pytest.approx(
        backend.macaulay_duration_years
    )

    assert service["modified_duration_years"] == pytest.approx(
        backend.modified_duration_years
    )

    assert service["dv01"] == pytest.approx(backend.dv01)

    assert service["convexity_years_squared"] == pytest.approx(
        backend.convexity_years_squared
    )

    assert service["calculation_engine"] == (
        "pakyield.fixed_income.analyze_fixed_rate_bullet"
    )


def test_service_exposes_required_cash_flows_and_shocks() -> None:
    """UI service must expose contractual flows and required shocks."""

    result = fixed_income_analysis(
        face_value=1000.0,
        coupon_rate_pct=6.0,
        ytm_pct=7.0,
        years_to_maturity=5.0,
        coupon_frequency=2,
        rate_shock_bps=75,
    )

    cash_flows = result["cash_flows"]

    scenarios = result["scenarios"]

    assert len(cash_flows) == 10

    shocks = tuple(row["shock_bps"] for row in scenarios)

    for required in (
        -200,
        -100,
        -50,
        0,
        50,
        100,
        200,
        75,
    ):
        assert required in shocks

    selected = next(row for row in scenarios if row["shock_bps"] == 75)

    assert selected["actual_repriced_price"] > 0

    assert selected["duration_only_price"] > 0

    assert selected["duration_convexity_price"] > 0


def test_price_curve_uses_backend_and_is_downward_sloping() -> None:
    """The display price/yield curve must come from backend repricing."""

    curve = fixed_income_price_curve(
        face_value=1000.0,
        coupon_rate_pct=5.0,
        center_ytm_pct=5.0,
        years_to_maturity=5.0,
        coupon_frequency=2,
        points=41,
    )

    assert len(curve) == 41

    ytms = [row["ytm_pct"] for row in curve]

    prices = [row["price"] for row in curve]

    assert ytms == sorted(ytms)

    assert all(
        left > right
        for left, right in zip(
            prices,
            prices[1:],
            strict=False,
        )
    )


def test_invalid_fixed_income_inputs_fail_gracefully() -> None:
    """Invalid UI inputs must be rejected by the tested backend."""

    with pytest.raises(ValueError):
        fixed_income_analysis(
            face_value=-1000.0,
            coupon_rate_pct=5.0,
            ytm_pct=5.0,
            years_to_maturity=5.0,
            coupon_frequency=2,
            rate_shock_bps=100,
        )

    with pytest.raises(ValueError):
        fixed_income_price_curve(
            face_value=1000.0,
            coupon_rate_pct=5.0,
            center_ytm_pct=5.0,
            years_to_maturity=5.0,
            coupon_frequency=2,
            points=1,
        )


def test_page_uses_service_not_local_finance_formulas() -> None:
    """Streamlit page must consume service/backend results."""

    page = PAGE_PATH.read_text(encoding="utf-8")

    service = SERVICE_PATH.read_text(encoding="utf-8")

    required_page_signals = (
        "Fixed-Income Risk Lab",
        "Face Value",
        "Annual Coupon Rate (%)",
        "Yield to Maturity (%)",
        "Maturity (Years)",
        "Coupon Frequency",
        "Selected Rate Shock (bps)",
        "Bond Price",
        "Macaulay Duration",
        "Modified Duration",
        "DV01",
        "Convexity",
        "Contractual Cash Flows",
        "Price-Yield Curve",
        "Rate-Shock Scenarios",
        "fixed_income_analysis(",
        "fixed_income_price_curve(",
    )

    for signal in required_page_signals:
        assert signal in page

    assert "pakyield.fixed_income" not in page

    assert "analyze_fixed_rate_bullet(" not in page

    assert "price_fixed_rate_bullet(" not in page

    assert "from pakyield.fixed_income import analyze_fixed_rate_bullet" in service

    assert "from pakyield.fixed_income import price_fixed_rate_bullet" in service
