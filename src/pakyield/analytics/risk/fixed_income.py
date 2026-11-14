"""Generic fixed-rate bullet-bond pricing and interest-rate risk analytics.

This module implements deterministic mathematical analytics for a plain
fixed-rate bullet bond.

Rates are supplied as decimal annual rates:

    0.10 == 10%

The implementation does not claim to represent every Sukuk structure,
floating-rate instrument, amortizing security, embedded option, tax
convention, settlement convention, or market quoting convention.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isclose, isfinite

BASIS_POINT = 0.0001

STANDARD_RATE_SHOCKS_BPS: tuple[int, ...] = (
    -200,
    -100,
    -50,
    0,
    50,
    100,
    200,
)


@dataclass(frozen=True)
class CashFlow:
    """One contractual fixed-rate bond cash flow."""

    period: int
    time_years: float
    coupon: float
    principal: float
    total_cash_flow: float
    discount_factor: float
    present_value: float


@dataclass(frozen=True)
class BondMetrics:
    """Core fixed-rate bond valuation and risk measures."""

    price: float
    macaulay_duration_years: float
    modified_duration_years: float
    dv01: float
    convexity_years_squared: float


@dataclass(frozen=True)
class RateShockResult:
    """One parallel yield-shock comparison."""

    shock_bps: int
    shocked_ytm: float
    duration_only_price: float
    duration_convexity_price: float
    actual_repriced_price: float
    actual_price_change: float
    actual_price_change_pct: float


@dataclass(frozen=True)
class BondAnalysis:
    """Complete deterministic analysis for one fixed-rate bullet bond."""

    metrics: BondMetrics
    cash_flows: tuple[CashFlow, ...]
    rate_shocks: tuple[RateShockResult, ...]


def _validate_inputs(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> int:
    """Validate bond inputs and return the integer number of periods."""

    numeric_inputs = {
        "face_value": face_value,
        "annual_coupon_rate": annual_coupon_rate,
        "ytm": ytm,
        "years_to_maturity": years_to_maturity,
    }

    for name, value in numeric_inputs.items():
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")

    if face_value <= 0:
        raise ValueError("face_value must be greater than zero")

    if annual_coupon_rate < 0:
        raise ValueError("annual_coupon_rate cannot be negative")

    if years_to_maturity <= 0:
        raise ValueError("years_to_maturity must be greater than zero")

    if (
        isinstance(coupon_frequency, bool)
        or not isinstance(coupon_frequency, int)
        or coupon_frequency <= 0
    ):
        raise ValueError("coupon_frequency must be a positive integer")

    periods_float = years_to_maturity * coupon_frequency

    periods = round(periods_float)

    if not isclose(
        periods_float,
        periods,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "years_to_maturity × coupon_frequency "
            "must produce a whole number of coupon periods"
        )

    if periods < 1:
        raise ValueError("bond must contain at least one coupon period")

    periodic_base = 1.0 + ytm / coupon_frequency

    if periodic_base <= 0:
        raise ValueError("ytm produces a non-positive periodic discount base")

    return int(periods)


def cash_flow_schedule(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> tuple[CashFlow, ...]:
    """Return the complete discounted contractual cash-flow schedule."""

    periods = _validate_inputs(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    coupon = face_value * annual_coupon_rate / coupon_frequency

    periodic_yield = ytm / coupon_frequency

    periodic_base = 1.0 + periodic_yield

    rows: list[CashFlow] = []

    for period in range(
        1,
        periods + 1,
    ):
        principal = face_value if period == periods else 0.0

        total_cash_flow = coupon + principal

        discount_factor = 1.0 / periodic_base**period

        present_value = total_cash_flow * discount_factor

        rows.append(
            CashFlow(
                period=period,
                time_years=(period / coupon_frequency),
                coupon=coupon,
                principal=principal,
                total_cash_flow=(total_cash_flow),
                discount_factor=(discount_factor),
                present_value=(present_value),
            )
        )

    return tuple(rows)


def bond_price(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return the present value of all contractual bond cash flows."""

    schedule = cash_flow_schedule(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    return sum(row.present_value for row in schedule)


def macaulay_duration(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return Macaulay duration in years."""

    schedule = cash_flow_schedule(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(row.present_value for row in schedule)

    weighted_present_value = sum(row.time_years * row.present_value for row in schedule)

    return weighted_present_value / price


def modified_duration(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return modified duration in years."""

    macaulay = macaulay_duration(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    periodic_base = 1.0 + ytm / coupon_frequency

    return macaulay / periodic_base


def convexity(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return annual-yield convexity in years squared.

    For periodic compounding, convexity is:

        (1 / P f^2)
        × Σ[t(t+1) CF_t / (1 + y/f)^(t+2)]

    where ``t`` is the coupon-period index and ``f`` is coupon frequency.
    """

    schedule = cash_flow_schedule(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(row.present_value for row in schedule)

    periodic_base = 1.0 + ytm / coupon_frequency

    numerator = sum(
        (
            row.period
            * (row.period + 1)
            * row.total_cash_flow
            / periodic_base ** (row.period + 2)
        )
        for row in schedule
    )

    return numerator / (price * coupon_frequency**2)


def dv01(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> float:
    """Return duration-based DV01 for a one-basis-point yield move.

    DV01 is expressed in the same currency units as ``face_value`` and uses:

        modified duration × price × 0.0001
    """

    price = bond_price(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    duration = modified_duration(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    return duration * price * BASIS_POINT


def bond_metrics(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
) -> BondMetrics:
    """Calculate the complete core metric set for one bond."""

    schedule = cash_flow_schedule(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    price = sum(row.present_value for row in schedule)

    macaulay = sum(row.time_years * row.present_value for row in schedule) / price

    periodic_base = 1.0 + ytm / coupon_frequency

    modified = macaulay / periodic_base

    convexity_numerator = sum(
        (
            row.period
            * (row.period + 1)
            * row.total_cash_flow
            / periodic_base ** (row.period + 2)
        )
        for row in schedule
    )

    convexity_value = convexity_numerator / (price * coupon_frequency**2)

    dv01_value = modified * price * BASIS_POINT

    return BondMetrics(
        price=price,
        macaulay_duration_years=(macaulay),
        modified_duration_years=(modified),
        dv01=dv01_value,
        convexity_years_squared=(convexity_value),
    )


def rate_shock_scenarios(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
    shocks_bps: Iterable[int] = (STANDARD_RATE_SHOCKS_BPS),
) -> tuple[RateShockResult, ...]:
    """Compare duration, duration+convexity, and actual repricing."""

    metrics = bond_metrics(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    results: list[RateShockResult] = []

    for shock_bps in shocks_bps:
        if isinstance(
            shock_bps,
            bool,
        ) or not isinstance(
            shock_bps,
            int,
        ):
            raise ValueError("rate shocks must be integer basis points")

        delta_yield = shock_bps * BASIS_POINT

        shocked_ytm = ytm + delta_yield

        if 1.0 + shocked_ytm / coupon_frequency <= 0:
            raise ValueError(
                "rate shock produces a non-positive periodic discount base"
            )

        duration_return = -metrics.modified_duration_years * delta_yield

        duration_convexity_return = (
            duration_return + 0.5 * metrics.convexity_years_squared * delta_yield**2
        )

        duration_only_price = metrics.price * (1.0 + duration_return)

        duration_convexity_price = metrics.price * (1.0 + duration_convexity_return)

        actual_price = bond_price(
            face_value=face_value,
            annual_coupon_rate=annual_coupon_rate,
            ytm=shocked_ytm,
            years_to_maturity=years_to_maturity,
            coupon_frequency=coupon_frequency,
        )

        actual_change = actual_price - metrics.price

        results.append(
            RateShockResult(
                shock_bps=shock_bps,
                shocked_ytm=(shocked_ytm),
                duration_only_price=(duration_only_price),
                duration_convexity_price=(duration_convexity_price),
                actual_repriced_price=(actual_price),
                actual_price_change=(actual_change),
                actual_price_change_pct=(actual_change / metrics.price),
            )
        )

    return tuple(results)


def analyze_bond(
    *,
    face_value: float,
    annual_coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    coupon_frequency: int,
    shocks_bps: Iterable[int] = (STANDARD_RATE_SHOCKS_BPS),
) -> BondAnalysis:
    """Return metrics, contractual cash flows, and rate-shock scenarios."""

    schedule = cash_flow_schedule(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    metrics = bond_metrics(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
    )

    shocks = rate_shock_scenarios(
        face_value=face_value,
        annual_coupon_rate=annual_coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        coupon_frequency=coupon_frequency,
        shocks_bps=shocks_bps,
    )

    return BondAnalysis(
        metrics=metrics,
        cash_flows=schedule,
        rate_shocks=shocks,
    )
