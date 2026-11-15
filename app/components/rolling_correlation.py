"""Display rolling correlations using matched benchmark observations."""

from __future__ import annotations

from collections.abc import Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from pakyield.analytics.rolling_correlation import rolling_yield_correlations


def render_rolling_correlation(
    history: list[Mapping[str, str]],
    tenor: str,
) -> None:
    """Render a rolling Pearson correlation for the selected maturity."""
    st.subheader("Rolling benchmark correlation")

    window = st.selectbox(
        "Matched-observation window",
        options=(30, 60, 120),
        index=1,
        key="cross_curve_rolling_window",
    )

    try:
        results = rolling_yield_correlations(history, window)
    except (KeyError, TypeError, ValueError) as exc:
        st.error("The rolling correlation could not be calculated safely.")
        st.code(str(exc))
        return

    available = [row for row in results if row["correlation"] is not None]

    if not available:
        st.info(
            "No correlation is available for this window. A full window "
            "of eligible matched observations with variation in both "
            "yield series is required."
        )
        return

    figure = go.Figure(
        go.Scatter(
            x=[row["observation_date"] for row in results],
            y=[row["correlation"] for row in results],
            mode="lines",
            name="Rolling Pearson correlation",
            connectgaps=False,
            hovertemplate=("Date: %{x}<br>Correlation: %{y:.3f}<extra></extra>"),
        )
    )

    apply_financial_chart_layout(
        figure,
        title=f"{tenor} · {window} matched observations",
        xaxis_title="Observation date",
        yaxis_title="Pearson correlation",
        hovermode="closest",
    )

    figure.update_yaxes(range=[-1.05, 1.05])

    st.plotly_chart(
        figure,
        width="stretch",
        key="cross_curve_rolling_chart",
    )

    st.caption(
        "Correlation compares yield levels in a rolling window of eligible "
        "same-date pairs. The window counts observations, not calendar days. "
        "Values are unavailable when the window is incomplete or either "
        "series has no variation. Correlation does not establish causality."
    )
