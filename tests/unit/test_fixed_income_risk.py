"""Mathematical fixtures for the Phase 11 fixed-income risk engine."""

from __future__ import annotations

import pytest

from pakyield.analytics.risk.fixed_income import (
    STANDARD_RATE_SHOCKS_BPS,
    analyze_bond,
    bond_metrics,
    bond_price,
    cash_flow_schedule,
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    rate_shock_scenarios,
)

BASE_BOND = {
    "face_value": 1000.0,
    "annual_coupon_rate": 0.10,
    "ytm": 0.10,
    "years_to_maturity": 5.0,
    "coupon_frequency": 2,
}


def test_par_bond_prices_at_face_value() -> None:
    """Coupon rate equal to YTM must price a standard bond at par."""

    price = bond_price(**BASE_BOND)

    assert price == pytest.approx(
        1000.0,
        rel=1e-12,
        abs=1e-10,
    )


def test_premium_and_discount_bond_relationships() -> None:
    """Coupon/YTM ordering must produce premium and discount pricing."""

    premium = bond_price(
        face_value=1000.0,
        annual_coupon_rate=0.12,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    discount = bond_price(
        face_value=1000.0,
        annual_coupon_rate=0.08,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert premium > 1000.0
    assert discount < 1000.0


def test_positive_yield_price_inverse_relationship() -> None:
    """Higher required yield must lower price for identical cash flows."""

    low_yield_price = bond_price(
        face_value=1000.0,
        annual_coupon_rate=0.10,
        ytm=0.08,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    high_yield_price = bond_price(
        face_value=1000.0,
        annual_coupon_rate=0.10,
        ytm=0.12,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert high_yield_price < low_yield_price


def test_cash_flow_schedule_respects_coupon_frequency() -> None:
    """Semiannual five-year bond must produce ten exact periods."""

    schedule = cash_flow_schedule(**BASE_BOND)

    assert len(schedule) == 10

    assert [row.period for row in schedule] == list(range(1, 11))

    assert schedule[0].time_years == pytest.approx(0.5)

    assert schedule[-1].time_years == pytest.approx(5.0)

    assert all(row.coupon == pytest.approx(50.0) for row in schedule)

    assert all(row.principal == pytest.approx(0.0) for row in schedule[:-1])

    assert schedule[-1].principal == pytest.approx(1000.0)

    assert schedule[-1].total_cash_flow == pytest.approx(1050.0)

    assert sum(row.present_value for row in schedule) == pytest.approx(1000.0)


def test_modified_duration_is_below_macaulay_at_positive_yield() -> None:
    """Periodic-compounding duration relationship must hold."""

    macaulay = macaulay_duration(**BASE_BOND)

    modified = modified_duration(**BASE_BOND)

    assert 0.0 < modified < macaulay

    assert macaulay <= BASE_BOND["years_to_maturity"]

    assert modified == pytest.approx(
        macaulay / (1.0 + BASE_BOND["ytm"] / BASE_BOND["coupon_frequency"])
    )


def test_dv01_agrees_with_explicit_one_basis_point_repricing() -> None:
    """Duration DV01 must closely match explicit 1 bp downward repricing."""

    base_price = bond_price(**BASE_BOND)

    duration_dv01 = dv01(**BASE_BOND)

    repriced = bond_price(
        **{
            **BASE_BOND,
            "ytm": (BASE_BOND["ytm"] - 0.0001),
        }
    )

    explicit_dv01 = repriced - base_price

    assert duration_dv01 > 0.0

    assert duration_dv01 == pytest.approx(
        explicit_dv01,
        rel=2e-3,
    )


def test_convexity_is_positive_for_standard_fixed_rate_bond() -> None:
    """Plain positive-cash-flow bullet bond must have positive convexity."""

    value = convexity(**BASE_BOND)

    assert value > 0.0


def test_bond_metrics_are_internally_consistent() -> None:
    """Aggregated metric API must equal individual calculations."""

    metrics = bond_metrics(**BASE_BOND)

    assert metrics.price == pytest.approx(bond_price(**BASE_BOND))

    assert metrics.macaulay_duration_years == pytest.approx(
        macaulay_duration(**BASE_BOND)
    )

    assert metrics.modified_duration_years == pytest.approx(
        modified_duration(**BASE_BOND)
    )

    assert metrics.dv01 == pytest.approx(dv01(**BASE_BOND))

    assert metrics.convexity_years_squared == pytest.approx(convexity(**BASE_BOND))


def test_required_rate_shock_scenarios_are_exact() -> None:
    """Phase 11 must expose the seven mandatory parallel rate shocks."""

    scenarios = rate_shock_scenarios(**BASE_BOND)

    assert tuple(row.shock_bps for row in scenarios) == STANDARD_RATE_SHOCKS_BPS

    zero = next(row for row in scenarios if row.shock_bps == 0)

    assert zero.actual_repriced_price == pytest.approx(1000.0)

    assert zero.duration_only_price == pytest.approx(1000.0)

    assert zero.duration_convexity_price == pytest.approx(1000.0)

    assert zero.actual_price_change == pytest.approx(0.0)

    assert zero.actual_price_change_pct == pytest.approx(0.0)


def test_convexity_improves_one_percent_rate_shock_estimate() -> None:
    """Duration+convexity should improve the +100 bp local approximation."""

    scenario = next(
        row for row in rate_shock_scenarios(**BASE_BOND) if row.shock_bps == 100
    )

    duration_error = abs(scenario.duration_only_price - scenario.actual_repriced_price)

    convexity_error = abs(
        scenario.duration_convexity_price - scenario.actual_repriced_price
    )

    assert convexity_error < duration_error


def test_analyze_bond_returns_complete_phase_11_payload() -> None:
    """Top-level API must contain metrics, schedule, and shock analysis."""

    result = analyze_bond(**BASE_BOND)

    assert result.metrics.price == pytest.approx(1000.0)

    assert len(result.cash_flows) == 10

    assert (
        tuple(row.shock_bps for row in result.rate_shocks) == STANDARD_RATE_SHOCKS_BPS
    )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        (
            "face_value",
            0.0,
        ),
        (
            "face_value",
            -1000.0,
        ),
        (
            "annual_coupon_rate",
            -0.01,
        ),
        (
            "years_to_maturity",
            0.0,
        ),
        (
            "coupon_frequency",
            0,
        ),
        (
            "coupon_frequency",
            -2,
        ),
    ],
)
def test_invalid_basic_inputs_fail_closed(
    field: str,
    value: float,
) -> None:
    """Invalid contract inputs must fail rather than produce fake metrics."""

    inputs = {
        **BASE_BOND,
        field: value,
    }

    with pytest.raises(ValueError):
        bond_price(**inputs)


def test_fractional_coupon_period_count_fails_closed() -> None:
    """Maturity/frequency combination must produce whole coupon periods."""

    with pytest.raises(
        ValueError,
        match=("whole number of coupon periods"),
    ):
        bond_price(
            face_value=1000.0,
            annual_coupon_rate=0.10,
            ytm=0.10,
            years_to_maturity=5.1,
            coupon_frequency=2,
        )


def test_non_positive_discount_base_fails_closed() -> None:
    """Yield cannot make the periodic discount denominator non-positive."""

    with pytest.raises(
        ValueError,
        match=("non-positive periodic discount base"),
    ):
        bond_price(
            face_value=1000.0,
            annual_coupon_rate=0.10,
            ytm=-2.0,
            years_to_maturity=5.0,
            coupon_frequency=2,
        )


def test_zero_coupon_bond_matches_closed_form_price() -> None:
    """Zero-coupon bullet fixture provides an independent pricing identity."""

    price = bond_price(
        face_value=1000.0,
        annual_coupon_rate=0.0,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=1,
    )

    expected = 1000.0 / 1.10**5

    assert price == pytest.approx(
        expected,
        rel=1e-12,
    )

    macaulay = macaulay_duration(
        face_value=1000.0,
        annual_coupon_rate=0.0,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=1,
    )

    assert macaulay == pytest.approx(5.0)
