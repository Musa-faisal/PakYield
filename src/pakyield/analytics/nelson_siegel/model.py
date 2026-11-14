"""Research-quality Nelson-Siegel yield-curve implementation.

The production model uses one globally frozen decay parameter and estimates
the three cross-sectional beta coefficients independently for each eligible
curve date.

The global decay parameter and eligibility rule are frozen by D105.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray

GLOBAL_DECAY_LAMBDA = 1.877661465308

MIN_DISTINCT_MATURITIES = 10
SHORT_MAX_YEARS = 1.0
BELLY_MAX_YEARS = 10.0
MIN_MATURITY_SPAN_YEARS = 15.0

FIT_STATUS_FIT = "FIT"
FIT_STATUS_INELIGIBLE = "INELIGIBLE"
FIT_STATUS_FAILED = "FIT_FAILED"

METHOD_FIXED_GLOBAL_LAMBDA = "FIXED_GLOBAL_LAMBDA_LINEAR_LEAST_SQUARES"


@dataclass(frozen=True)
class NelsonSiegelEligibility:
    """Cross-sectional production eligibility result."""

    eligible: bool
    reasons: tuple[str, ...]
    n_points: int
    n_distinct_maturities: int
    min_maturity_years: float
    max_maturity_years: float
    maturity_span_years: float


@dataclass(frozen=True)
class NelsonSiegelFit:
    """One fixed-decay Nelson-Siegel cross-sectional result."""

    status: str
    ineligibility_reason: str
    eligibility: NelsonSiegelEligibility
    decay_lambda: float
    beta0: float | None
    beta1: float | None
    beta2: float | None
    rmse_pct_points: float | None
    design_rank: int | None
    design_condition_number: float | None
    fitted_yields: tuple[float, ...]
    residuals: tuple[float, ...]
    fit_method: str


def _as_float_array(
    values: Iterable[float],
    *,
    name: str,
) -> NDArray[np.float64]:
    """Convert numeric input to a validated one-dimensional float array."""

    array = np.asarray(
        tuple(values),
        dtype=np.float64,
    )

    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")

    if array.size == 0:
        raise ValueError(f"{name} must not be empty")

    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")

    return array


def nelson_siegel_loadings(
    maturities_years: Iterable[float],
    *,
    decay_lambda: float = GLOBAL_DECAY_LAMBDA,
) -> NDArray[np.float64]:
    """Return the standard Nelson-Siegel design matrix.

    The specification is:

        y(t) = beta0
             + beta1 * L1(t)
             + beta2 * L2(t)

        L1(t) = (1 - exp(-lambda * t)) / (lambda * t)
        L2(t) = L1(t) - exp(-lambda * t)
    """

    if not isfinite(decay_lambda) or decay_lambda <= 0.0:
        raise ValueError("decay_lambda must be finite and positive")

    maturities = _as_float_array(
        maturities_years,
        name="maturities_years",
    )

    if np.any(maturities <= 0.0):
        raise ValueError("maturities_years must be strictly positive")

    x = decay_lambda * maturities

    level = np.ones_like(maturities)

    slope = -np.expm1(-x) / x

    curvature = slope - np.exp(-x)

    return np.column_stack(
        (
            level,
            slope,
            curvature,
        )
    )


def evaluate_nelson_siegel(
    maturities_years: Iterable[float],
    *,
    beta0: float,
    beta1: float,
    beta2: float,
    decay_lambda: float = GLOBAL_DECAY_LAMBDA,
) -> NDArray[np.float64]:
    """Evaluate a Nelson-Siegel curve at supplied maturities."""

    coefficients = np.asarray(
        (
            beta0,
            beta1,
            beta2,
        ),
        dtype=np.float64,
    )

    if not np.all(np.isfinite(coefficients)):
        raise ValueError("beta coefficients must be finite")

    design = nelson_siegel_loadings(
        maturities_years,
        decay_lambda=decay_lambda,
    )

    return design @ coefficients


def assess_nelson_siegel_eligibility(
    maturities_years: Iterable[float],
) -> NelsonSiegelEligibility:
    """Apply the frozen D105 research-quality maturity rule."""

    maturities = _as_float_array(
        maturities_years,
        name="maturities_years",
    )

    if np.any(maturities <= 0.0):
        raise ValueError("maturities_years must be strictly positive")

    unique = np.unique(maturities)

    minimum = float(np.min(unique))

    maximum = float(np.max(unique))

    span = maximum - minimum

    reasons: list[str] = []

    if unique.size < MIN_DISTINCT_MATURITIES:
        reasons.append("POINTS_LT_10")

    if not np.any(unique <= SHORT_MAX_YEARS):
        reasons.append("NO_SHORT")

    if not np.any((unique > SHORT_MAX_YEARS) & (unique <= BELLY_MAX_YEARS)):
        reasons.append("NO_BELLY")

    if not np.any(unique > BELLY_MAX_YEARS):
        reasons.append("NO_LONG")

    if span < MIN_MATURITY_SPAN_YEARS:
        reasons.append("SPAN_LT_15Y")

    return NelsonSiegelEligibility(
        eligible=not reasons,
        reasons=tuple(reasons),
        n_points=int(maturities.size),
        n_distinct_maturities=int(unique.size),
        min_maturity_years=minimum,
        max_maturity_years=maximum,
        maturity_span_years=span,
    )


def fit_nelson_siegel_fixed_decay(
    maturities_years: Iterable[float],
    yields_pct: Iterable[float],
    *,
    decay_lambda: float = GLOBAL_DECAY_LAMBDA,
    enforce_production_eligibility: bool = True,
) -> NelsonSiegelFit:
    """Fit beta coefficients for one curve cross section."""

    maturities = _as_float_array(
        maturities_years,
        name="maturities_years",
    )

    yields = _as_float_array(
        yields_pct,
        name="yields_pct",
    )

    if maturities.size != yields.size:
        raise ValueError("maturities_years and yields_pct must have the same length")

    if maturities.size < 3:
        raise ValueError("at least three observations are required")

    eligibility = assess_nelson_siegel_eligibility(maturities)

    if enforce_production_eligibility and not eligibility.eligible:
        return NelsonSiegelFit(
            status=FIT_STATUS_INELIGIBLE,
            ineligibility_reason=";".join(eligibility.reasons),
            eligibility=eligibility,
            decay_lambda=decay_lambda,
            beta0=None,
            beta1=None,
            beta2=None,
            rmse_pct_points=None,
            design_rank=None,
            design_condition_number=None,
            fitted_yields=(),
            residuals=(),
            fit_method=METHOD_FIXED_GLOBAL_LAMBDA,
        )

    design = nelson_siegel_loadings(
        maturities,
        decay_lambda=decay_lambda,
    )

    rank = int(np.linalg.matrix_rank(design))

    condition = float(np.linalg.cond(design))

    if rank < 3:
        return NelsonSiegelFit(
            status=FIT_STATUS_FAILED,
            ineligibility_reason=("DESIGN_RANK_LT_3"),
            eligibility=eligibility,
            decay_lambda=decay_lambda,
            beta0=None,
            beta1=None,
            beta2=None,
            rmse_pct_points=None,
            design_rank=rank,
            design_condition_number=condition,
            fitted_yields=(),
            residuals=(),
            fit_method=METHOD_FIXED_GLOBAL_LAMBDA,
        )

    coefficients, _, _, _ = np.linalg.lstsq(
        design,
        yields,
        rcond=None,
    )

    fitted = design @ coefficients

    residuals = yields - fitted

    rmse = float(np.sqrt(np.mean(residuals**2)))

    return NelsonSiegelFit(
        status=FIT_STATUS_FIT,
        ineligibility_reason="",
        eligibility=eligibility,
        decay_lambda=decay_lambda,
        beta0=float(coefficients[0]),
        beta1=float(coefficients[1]),
        beta2=float(coefficients[2]),
        rmse_pct_points=rmse,
        design_rank=rank,
        design_condition_number=condition,
        fitted_yields=tuple(float(value) for value in fitted),
        residuals=tuple(float(value) for value in residuals),
        fit_method=METHOD_FIXED_GLOBAL_LAMBDA,
    )
