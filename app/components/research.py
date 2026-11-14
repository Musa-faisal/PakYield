"""Read-only research presentation components for PakYield.

All statistical outputs are loaded from the verified
econometrics service. This module performs no estimation,
hypothesis testing, or statistical inference.
"""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import plotly.graph_objects as go
import streamlit as st

from .charts import apply_financial_chart_layout

Rows = tuple[dict[str, str], ...]


FAMILY_LABELS = {
    "yield_level_regime": "Yield levels by regime",
    "yield_change_regime": "Yield changes by regime",
    "term_spread_regime": "Term spreads by regime",
    "cross_curve_zero": "Cross-curve zero comparison",
    "cross_curve_regime": "Cross-curve regime comparison",
    "mpc_event_window": "MPC announcement windows",
    "monthly_cpi_yield": "Monthly CPI and yields",
}


def _load_verified(
    service: ModuleType,
    loader: Callable[[], Rows],
    description: str,
) -> Rows:
    """Fail closed when a verified artifact is unavailable."""

    try:
        return loader()

    except service.EconometricsDataError as exc:
        st.error(
            f"{description} could not be verified. This research view has been stopped."
        )
        st.code(str(exc))
        st.stop()
        raise


def _render_rows(
    rows: Rows,
    *,
    empty_message: str = "No observations for this selection.",
) -> None:
    """Display source records without modifying their values."""

    if not rows:
        st.info(empty_message)
        return

    st.caption(
        f"{len(rows):,} verified records. Values are displayed as stored in the source."
    )

    st.dataframe(
        list(rows),
        width="stretch",
        hide_index=True,
    )


def _choices(
    rows: Rows,
    field: str,
) -> list[str]:
    """List actual observed filter labels."""

    return sorted({row[field] for row in rows if row.get(field)})


def _optional_filter(
    title: str,
    values: list[str],
    *,
    key: str,
) -> str | None:
    """Choose an optional exact-value filter."""

    selection = st.selectbox(
        title,
        ["All", *values],
        key=key,
    )

    return None if selection == "All" else selection


def _render_inferential_tests(
    service: ModuleType,
    manifest: Rows,
) -> None:
    """Show audited inferential families and recorded tests."""

    st.markdown("#### Inferential families")

    families = [row["family"] for row in manifest]

    family = st.selectbox(
        "Select an inferential family",
        families,
        format_func=lambda value: FAMILY_LABELS.get(
            value,
            value.replace("_", " ").title(),
        ),
        key="research_inferential_family",
    )

    specification = next(row for row in manifest if row["family"] == family)

    st.caption(
        "Audit status: "
        f"{specification['diagnostic_status']} "
        "· Registered rows: "
        f"{specification['total_rows']}"
    )

    rows = _load_verified(
        service,
        lambda: service.regression_table(family),
        "Inferential results",
    )

    _render_rows(rows)

    st.caption(
        "Reported coefficients, p-values, adjusted p-values, "
        "confidence intervals, model settings, exclusions, "
        "and analysis statuses come from frozen artifacts. "
        "No models are fitted on this page."
    )

    with st.expander(
        "View inferential-family audit manifest",
        expanded=False,
    ):
        _render_rows(manifest)


def _render_correlations(
    service: ModuleType,
) -> None:
    """Display precomputed correlations with exact filters."""

    st.markdown("#### Observed correlation diagnostics")

    all_rows = _load_verified(
        service,
        service.load_correlation_diagnostics,
        "Correlation diagnostics",
    )

    columns = st.columns(3)

    with columns[0]:
        family = _optional_filter(
            "Family",
            _choices(all_rows, "family"),
            key="research_correlation_family",
        )

    with columns[1]:
        curve = _optional_filter(
            "Curve",
            _choices(all_rows, "curve_type"),
            key="research_correlation_curve",
        )

    with columns[2]:
        regime = _optional_filter(
            "Regime",
            _choices(all_rows, "regime_label"),
            key="research_correlation_regime",
        )

    rows = _load_verified(
        service,
        lambda: service.correlation_table(
            family=family,
            curve_type=curve,
            regime_label=regime,
        ),
        "Filtered correlations",
    )

    _render_rows(rows)

    st.caption(
        "Correlations are precomputed observations, "
        "not causal estimates. Filtering does not "
        "recalculate any statistics."
    )


def _render_diagnostics(
    service: ModuleType,
) -> None:
    """Display precomputed diagnostic tables."""

    st.markdown("#### Econometric diagnostics")

    loaders = {
        "ADF stationarity": service.load_adf_diagnostics,
        "Variance inflation factors": service.load_vif_diagnostics,
        "Regression residuals": service.load_residual_diagnostics,
    }

    selection = st.selectbox(
        "Diagnostic family",
        list(loaders),
        key="research_diagnostic_family",
    )

    rows = _load_verified(
        service,
        loaders[selection],
        "Econometric diagnostics",
    )

    _render_rows(rows)

    st.caption(
        "ADF, VIF, and residual diagnostics are displayed "
        "as precomputed research records. "
        "Interpretation must respect the recorded "
        "model, sample, eligibility, and diagnostic status."
    )

    if selection == "Variance inflation factors":
        with st.expander(
            "View VIF diagnostic manifest",
            expanded=False,
        ):
            vif_manifest = _load_verified(
                service,
                lambda: service.load_artifact("vif_manifest"),
                "VIF manifest",
            )

            _render_rows(vif_manifest)


def _render_macro_chart(
    rows: Rows,
) -> None:
    """Plot actual complete monthly observations as markers."""

    observed = [
        row
        for row in rows
        if (row.get("month_end_yield_pct") and row.get("cpi_inflation_yoy_pct"))
    ]

    if not observed:
        st.info("No complete monthly yield/CPI pairs are available for visualization.")
        return

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=[row["period"] for row in observed],
            y=[float(row["month_end_yield_pct"]) for row in observed],
            mode="markers",
            name="Observed yield (%)",
            marker={"size": 8},
            connectgaps=False,
        )
    )

    figure.add_trace(
        go.Scatter(
            x=[row["period"] for row in observed],
            y=[float(row["cpi_inflation_yoy_pct"]) for row in observed],
            mode="markers",
            name="CPI inflation YoY (%)",
            marker={"size": 8},
            connectgaps=False,
        )
    )

    apply_financial_chart_layout(
        figure,
        title="Observed monthly yield and CPI inflation",
        xaxis_title="Calendar month",
        yaxis_title="Percent (%)",
        height=420,
        hovermode="closest",
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="research_macro_observations_chart",
    )

    st.caption(
        "Markers represent observed monthly records only. "
        "No missing months or values are interpolated; "
        "co-movement does not establish causality."
    )


def _render_monthly_macro(
    service: ModuleType,
) -> None:
    """Visualize verified calendar-month CPI/yield observations."""

    st.markdown("#### Monthly macroeconomic observations")

    left, middle, right = st.columns(3)

    with left:
        curve = st.selectbox(
            "Benchmark curve",
            ["PKRV", "PKISRV"],
            key="research_macro_curve",
        )

    tenors = (
        ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y"]
        if curve == "PKRV"
        else ["3M", "6M", "1Y"]
    )

    with middle:
        tenor = st.selectbox(
            "Maturity",
            tenors,
            index=2,
            key="research_macro_tenor",
        )

    with right:
        include_incomplete = st.checkbox(
            "Show incomplete rows",
            value=False,
            key="research_macro_incomplete",
        )

    rows = _load_verified(
        service,
        lambda: service.load_macro_monthly_series(
            curve,
            tenor,
            complete_only=not include_incomplete,
        ),
        "Monthly CPI/yield observations",
    )

    _render_macro_chart(rows)

    with st.expander(
        "View underlying monthly observations",
        expanded=True,
    ):
        _render_rows(rows)

    st.caption(
        "Monthly yields use the source's last available "
        "observation within each calendar month. "
        "The table preserves the original period, "
        "observation dates, gaps, missing values, "
        "and source lineage."
    )


def render_research_workspace(
    service: ModuleType,
) -> None:
    """Render the service-backed Research / Econometrics workspace."""

    manifest = _load_verified(
        service,
        service.load_inferential_manifest,
        "Inferential research manifest",
    )

    st.caption(
        f"{len(manifest)} verified inferential families "
        "· Read-only statistical results "
        "· SHA-verified source artifacts"
    )

    tabs = st.tabs(
        [
            "Inferential tests",
            "Correlations",
            "Diagnostics",
            "Monthly CPI / yields",
        ]
    )

    with tabs[0]:
        _render_inferential_tests(
            service,
            manifest,
        )

    with tabs[1]:
        _render_correlations(
            service,
        )

    with tabs[2]:
        _render_diagnostics(
            service,
        )

    with tabs[3]:
        _render_monthly_macro(
            service,
        )
