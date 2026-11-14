"""Unit tests for the Nelson-Siegel production model."""

from __future__ import annotations

import numpy as np
import pytest

from pakyield.analytics.nelson_siegel import (
    FIT_STATUS_FIT,
    FIT_STATUS_INELIGIBLE,
    GLOBAL_DECAY_LAMBDA,
    assess_nelson_siegel_eligibility,
    evaluate_nelson_siegel,
    fit_nelson_siegel_fixed_decay,
    nelson_siegel_loadings,
)


def test_loadings_have_expected_shape_and_level_column() -> None:
    maturities = (
        0.25,
        1.0,
        5.0,
        10.0,
        20.0,
    )

    design = nelson_siegel_loadings(maturities)

    assert design.shape == (
        5,
        3,
    )

    assert np.allclose(
        design[:, 0],
        1.0,
    )

    assert np.all(design[:, 1] > 0.0)


def test_synthetic_fixed_decay_curve_recovers_betas() -> None:
    maturities = (
        1 / 52,
        2 / 52,
        1 / 12,
        2 / 12,
        0.25,
        4 / 12,
        0.5,
        0.75,
        1.0,
        2.0,
        3.0,
        5.0,
        10.0,
        20.0,
    )

    expected = (
        12.4,
        2.1,
        -1.3,
    )

    yields = evaluate_nelson_siegel(
        maturities,
        beta0=expected[0],
        beta1=expected[1],
        beta2=expected[2],
    )

    result = fit_nelson_siegel_fixed_decay(
        maturities,
        yields,
    )

    assert result.status == (FIT_STATUS_FIT)

    assert result.beta0 == (
        pytest.approx(
            expected[0],
            abs=1e-10,
        )
    )

    assert result.beta1 == (
        pytest.approx(
            expected[1],
            abs=1e-10,
        )
    )

    assert result.beta2 == (
        pytest.approx(
            expected[2],
            abs=1e-10,
        )
    )

    assert result.rmse_pct_points == (
        pytest.approx(
            0.0,
            abs=1e-10,
        )
    )


def test_pkrv_like_maturity_distribution_is_eligible() -> None:
    maturities = (
        1 / 52,
        2 / 52,
        1 / 12,
        2 / 12,
        0.25,
        0.5,
        1.0,
        2.0,
        5.0,
        10.0,
        15.0,
        20.0,
    )

    result = assess_nelson_siegel_eligibility(maturities)

    assert result.eligible
    assert result.reasons == ()
    assert result.n_distinct_maturities == 12
    assert result.maturity_span_years > 19.0


def test_pkisrv_like_curve_is_structurally_ineligible() -> None:
    maturities = (
        1 / 12,
        0.25,
        0.5,
        0.75,
        1.0,
    )

    eligibility = assess_nelson_siegel_eligibility(maturities)

    assert not eligibility.eligible

    assert eligibility.reasons == (
        "POINTS_LT_10",
        "NO_BELLY",
        "NO_LONG",
        "SPAN_LT_15Y",
    )

    yields = (
        11.0,
        11.1,
        11.2,
        11.3,
        11.4,
    )

    fit = fit_nelson_siegel_fixed_decay(
        maturities,
        yields,
    )

    assert fit.status == (FIT_STATUS_INELIGIBLE)

    assert fit.beta0 is None
    assert fit.beta1 is None
    assert fit.beta2 is None
    assert fit.fitted_yields == ()
    assert fit.residuals == ()


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError):
        nelson_siegel_loadings(
            (
                0.0,
                1.0,
                2.0,
            )
        )

    with pytest.raises(ValueError):
        nelson_siegel_loadings(
            (
                1.0,
                2.0,
                3.0,
            ),
            decay_lambda=0.0,
        )

    with pytest.raises(ValueError):
        fit_nelson_siegel_fixed_decay(
            (
                1.0,
                2.0,
                3.0,
            ),
            (
                10.0,
                11.0,
            ),
            enforce_production_eligibility=False,
        )

    with pytest.raises(ValueError):
        fit_nelson_siegel_fixed_decay(
            (
                1.0,
                2.0,
                3.0,
            ),
            (
                10.0,
                float("nan"),
                12.0,
            ),
            enforce_production_eligibility=False,
        )


def test_repeated_fixed_decay_fit_is_deterministic() -> None:
    maturities = (
        1 / 52,
        2 / 52,
        1 / 12,
        2 / 12,
        0.25,
        0.5,
        1.0,
        2.0,
        3.0,
        5.0,
        10.0,
        15.0,
        20.0,
    )

    yields = tuple(
        float(value)
        for value in (
            evaluate_nelson_siegel(
                maturities,
                beta0=12.0,
                beta1=1.5,
                beta2=-0.8,
                decay_lambda=(GLOBAL_DECAY_LAMBDA),
            )
        )
    )

    first = fit_nelson_siegel_fixed_decay(
        maturities,
        yields,
    )

    second = fit_nelson_siegel_fixed_decay(
        maturities,
        yields,
    )

    assert first == second
