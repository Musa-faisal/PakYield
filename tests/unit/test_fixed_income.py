"""Unit tests for the Phase 11 fixed-rate bullet bond engine."""

from __future__ import annotations

import pytest

from pakyield.fixed_income import (
    DEFAULT_SHOCKS_BPS,
    analyze_fixed_rate_bullet,
    build_cash_flow_schedule,
    build_shock_scenarios,
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    price_fixed_rate_bullet,
)


def test_cash_flow_schedule_is_fixed_rate_bullet() -> None:
    """Coupons repeat and principal is repaid only at maturity."""

    flows = build_cash_flow_schedule(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=2.0,
        coupon_frequency=2,
    )

    assert len(flows) == 4

    assert [flow.period for flow in flows] == [
        1,
        2,
        3,
        4,
    ]

    assert [flow.time_years for flow in flows] == pytest.approx(
        [
            0.5,
            1.0,
            1.5,
            2.0,
        ]
    )

    for flow in flows[:-1]:
        assert flow.coupon_cash_flow == pytest.approx(50.0)

        assert flow.principal_cash_flow == pytest.approx(0.0)

        assert flow.total_cash_flow == pytest.approx(50.0)

    final = flows[-1]

    assert final.coupon_cash_flow == pytest.approx(50.0)

    assert final.principal_cash_flow == pytest.approx(1000.0)

    assert final.total_cash_flow == pytest.approx(1050.0)


def test_par_bond_prices_at_face_value() -> None:
    """Coupon rate equal to YTM prices a coupon-boundary bond at par."""

    price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert price == pytest.approx(
        1000.0,
        rel=1e-12,
        abs=1e-10,
    )


def test_premium_and_discount_relationship() -> None:
    """Coupon above YTM is premium; coupon below YTM is discount."""

    premium = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.12,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    discount = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.08,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert premium > 1000.0
    assert discount < 1000.0


def test_price_moves_inversely_with_yield() -> None:
    """Higher YTM produces lower price for the same bond."""

    low_yield_price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.08,
        years_to_maturity=7.0,
        coupon_frequency=2,
    )

    middle_yield_price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=7.0,
        coupon_frequency=2,
    )

    high_yield_price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.12,
        years_to_maturity=7.0,
        coupon_frequency=2,
    )

    assert low_yield_price > middle_yield_price > high_yield_price


def test_duration_relationships_are_correct() -> None:
    """Macaulay and modified duration satisfy the standard relationship."""

    macaulay = macaulay_duration(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.12,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    modified = modified_duration(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.12,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert 0.0 < macaulay < 5.0
    assert 0.0 < modified < macaulay

    assert modified == pytest.approx(
        macaulay / (1.0 + 0.12 / 2),
        rel=1e-12,
    )


def test_dv01_matches_explicit_one_bp_repricing() -> None:
    """Duration DV01 closely approximates an explicit +1 bp repricing."""

    base_price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    plus_one_bp_price = price_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.1001,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    actual_one_bp_loss = base_price - plus_one_bp_price

    duration_dv01 = dv01(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert duration_dv01 > 0.0

    assert duration_dv01 == pytest.approx(
        actual_one_bp_loss,
        rel=5e-4,
    )


def test_convexity_is_positive_and_improves_large_shock_approximation() -> None:
    """Convexity is positive and improves the ±200 bp approximation."""

    bond_convexity = convexity(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=10.0,
        coupon_frequency=2,
    )

    assert bond_convexity > 0.0

    scenarios = build_shock_scenarios(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=10.0,
        coupon_frequency=2,
    )

    by_shock = {scenario.shock_bps: scenario for scenario in scenarios}

    for shock in (
        -200,
        200,
    ):
        scenario = by_shock[shock]

        assert abs(scenario.duration_convexity_error) < abs(
            scenario.duration_only_error
        )


def test_required_shock_scenarios_and_actual_repricing() -> None:
    """The required seven shocks are present and actual prices are monotonic."""

    result = analyze_fixed_rate_bullet(
        face_value=1000.0,
        coupon_rate=0.10,
        ytm=0.10,
        years_to_maturity=5.0,
        coupon_frequency=2,
    )

    assert (
        tuple(scenario.shock_bps for scenario in result.scenarios) == DEFAULT_SHOCKS_BPS
    )

    actual_prices = [scenario.actual_repriced_price for scenario in result.scenarios]

    assert actual_prices == sorted(
        actual_prices,
        reverse=True,
    )

    zero = next(scenario for scenario in result.scenarios if scenario.shock_bps == 0)

    assert zero.actual_repriced_price == pytest.approx(result.price)

    assert zero.duration_only_price == pytest.approx(result.price)

    assert zero.duration_convexity_price == pytest.approx(result.price)

    assert zero.actual_price_change == pytest.approx(0.0)


def test_invalid_inputs_are_rejected() -> None:
    """Invalid bond specifications fail explicitly."""

    with pytest.raises(
        ValueError,
        match="face_value",
    ):
        price_fixed_rate_bullet(
            face_value=0.0,
            coupon_rate=0.10,
            ytm=0.10,
            years_to_maturity=5.0,
            coupon_frequency=2,
        )

    with pytest.raises(
        ValueError,
        match="coupon_rate",
    ):
        price_fixed_rate_bullet(
            face_value=1000.0,
            coupon_rate=-0.01,
            ytm=0.10,
            years_to_maturity=5.0,
            coupon_frequency=2,
        )

    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        price_fixed_rate_bullet(
            face_value=1000.0,
            coupon_rate=0.10,
            ytm=0.10,
            years_to_maturity=1.10,
            coupon_frequency=2,
        )

    with pytest.raises(
        ValueError,
        match="coupon_frequency",
    ):
        price_fixed_rate_bullet(
            face_value=1000.0,
            coupon_rate=0.10,
            ytm=0.10,
            years_to_maturity=5.0,
            coupon_frequency=0,
        )
