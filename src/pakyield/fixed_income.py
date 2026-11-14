"""Fixed-rate bullet bond pricing and interest-rate risk analytics.

This module intentionally implements a generic fixed-rate bullet bond only.
It is not a universal Sukuk valuation model and does not model embedded
options, irregular coupons, accrued interest, settlement dates, day-count
conventions, credit spreads, or stochastic rates.

Rates are supplied as decimal annual rates:
    0.10 == 10 percent

Valuation occurs on a coupon boundary. The first cash flow therefore occurs
one full coupon period after valuation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

DEFAULT_SHOCKS_BPS: tuple[int, ...] = (
    -200,
    -100,
    -50,
    0,
    50,
    100,
    200,
)


@dataclass(frozen=True, slots=True)
class CashFlow:
    """One contractual fixed-rate bullet bond cash flow."""

    period: int
    time_years: float
    coupon_cash_flow: float
    principal_cash_flow: float
    total_cash_flow: float
    discount_factor: float
    present_value: float


@dataclass(frozen=True, slots=True)
class ShockScenario:
    """Price response under one parallel YTM shock."""

    shock_bps: int
    shocked_ytm: float
    duration_only_price: float
    duration_convexity_price: float
    actual_repriced_price: float
    actual_price_change: float
    duration_only_error: float
    duration_convexity_error: float


@dataclass(frozen=True, slots=True)
class FixedRateBulletRisk:
    """Complete fixed-rate bullet bond valuation and risk result."""

    face_value: float
    coupon_rate: float
    ytm: float
    years_to_maturity: float
    coupon_frequency: int
    price: float
    macaulay_duration_years: float
    modified_duration_years: float
    dv01: float
    convexity_years_squared: float
    cash_flows: tuple[CashFlow, ...]
    scenarios: tuple[ShockScenario, ...]


def _validate_inputs(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> int:
    """Validate inputs and return the number of coupon periods."""

    numeric_values = {
        "face_value": face_value,
        "coupon_rate": coupon_rate,
        "ytm": ytm,
        "years_to_maturity": years_to_maturity,
    }

    for name, value in numeric_values.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    if face_value <= 0:
        raise ValueError("face_value must be greater than zero")

    if coupon_rate < 0:
        raise ValueError("coupon_rate must be non-negative")

    if years_to_maturity <= 0:
        raise ValueError("years_to_maturity must be greater than zero")

    if isinstance(coupon_frequency, bool):
        raise ValueError("coupon_frequency must be a positive integer")

    if coupon_frequency <= 0:
        raise ValueError("coupon_frequency must be a positive integer")

    raw_periods = years_to_maturity * coupon_frequency

    periods = round(raw_periods)

    if not math.isclose(
        raw_periods,
        periods,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "years_to_maturity * coupon_frequency "
            "must produce a whole number of coupon periods"
        )

    if periods <= 0:
        raise ValueError("bond must contain at least one coupon period")

    periodic_yield = ytm / coupon_frequency

    if 1.0 + periodic_yield <= 0.0:
        raise ValueError("ytm implies a non-positive discount base")

    return int(periods)


def build_cash_flow_schedule(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> tuple[CashFlow, ...]:
    """Build the discounted contractual cash-flow schedule."""

    periods = _validate_inputs(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    coupon_cash_flow = face_value * coupon_rate / coupon_frequency

    periodic_yield = ytm / coupon_frequency

    discount_base = 1.0 + periodic_yield

    cash_flows: list[CashFlow] = []

    for period in range(
        1,
        periods + 1,
    ):
        principal_cash_flow = face_value if period == periods else 0.0

        total_cash_flow = coupon_cash_flow + principal_cash_flow

        discount_factor = discount_base**period

        present_value = total_cash_flow / discount_factor

        cash_flows.append(
            CashFlow(
                period=period,
                time_years=(period / coupon_frequency),
                coupon_cash_flow=(coupon_cash_flow),
                principal_cash_flow=(principal_cash_flow),
                total_cash_flow=(total_cash_flow),
                discount_factor=(discount_factor),
                present_value=(present_value),
            )
        )

    return tuple(cash_flows)


def price_fixed_rate_bullet(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return the full present value of a fixed-rate bullet bond."""

    cash_flows = build_cash_flow_schedule(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    return sum(cash_flow.present_value for cash_flow in cash_flows)


def macaulay_duration(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return Macaulay duration in years."""

    cash_flows = build_cash_flow_schedule(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(cash_flow.present_value for cash_flow in cash_flows)

    weighted_time = sum(
        cash_flow.time_years * cash_flow.present_value for cash_flow in cash_flows
    )

    return weighted_time / price


def modified_duration(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return modified duration in years."""

    macaulay = macaulay_duration(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    return macaulay / (1.0 + ytm / coupon_frequency)


def dv01(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return duration-based DV01 for a one-basis-point yield move."""

    price = price_fixed_rate_bullet(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    duration = modified_duration(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    return duration * price * 0.0001


def convexity(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return annualized discrete-compounding convexity."""

    cash_flows = build_cash_flow_schedule(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(cash_flow.present_value for cash_flow in cash_flows)

    periodic_yield = ytm / coupon_frequency

    discount_base = 1.0 + periodic_yield

    second_derivative = sum(
        (cash_flow.period * (cash_flow.period + 1) * cash_flow.total_cash_flow)
        / (
            coupon_frequency
            * coupon_frequency
            * discount_base ** (cash_flow.period + 2)
        )
        for cash_flow in cash_flows
    )

    return second_derivative / price


def build_shock_scenarios(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
    shocks_bps: tuple[int, ...] = DEFAULT_SHOCKS_BPS,
) -> tuple[ShockScenario, ...]:
    """Compare duration, duration+convexity, and actual repricing."""

    if not shocks_bps:
        raise ValueError("shocks_bps must contain at least one shock")

    base_price = price_fixed_rate_bullet(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    duration = modified_duration(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    bond_convexity = convexity(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    scenarios: list[ShockScenario] = []

    for shock_bps in shocks_bps:
        delta_yield = shock_bps / 10_000.0

        shocked_ytm = ytm + delta_yield

        actual_price = price_fixed_rate_bullet(
            face_value=face_value,
            coupon_rate=coupon_rate,
            ytm=shocked_ytm,
            years_to_maturity=years_to_maturity,
            coupon_frequency=coupon_frequency,
        )

        duration_only_price = base_price * (1.0 - duration * delta_yield)

        duration_convexity_price = base_price * (
            1.0
            - duration * delta_yield
            + 0.5 * bond_convexity * delta_yield * delta_yield
        )

        scenarios.append(
            ShockScenario(
                shock_bps=shock_bps,
                shocked_ytm=shocked_ytm,
                duration_only_price=(duration_only_price),
                duration_convexity_price=(duration_convexity_price),
                actual_repriced_price=(actual_price),
                actual_price_change=(actual_price - base_price),
                duration_only_error=(duration_only_price - actual_price),
                duration_convexity_error=(duration_convexity_price - actual_price),
            )
        )

    return tuple(scenarios)


def analyze_fixed_rate_bullet(
    *,
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
    shocks_bps: tuple[int, ...] = DEFAULT_SHOCKS_BPS,
) -> FixedRateBulletRisk:
    """Run complete fixed-rate bullet valuation and risk analysis."""

    cash_flows = build_cash_flow_schedule(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(cash_flow.present_value for cash_flow in cash_flows)

    macaulay = (
        sum(cash_flow.time_years * cash_flow.present_value for cash_flow in cash_flows)
        / price
    )

    modified = macaulay / (1.0 + ytm / coupon_frequency)

    bond_dv01 = modified * price * 0.0001

    bond_convexity = convexity(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    scenarios = build_shock_scenarios(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
        shocks_bps=shocks_bps,
    )

    return FixedRateBulletRisk(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
        price=price,
        macaulay_duration_years=(macaulay),
        modified_duration_years=(modified),
        dv01=bond_dv01,
        convexity_years_squared=(bond_convexity),
        cash_flows=cash_flows,
        scenarios=scenarios,
    )
