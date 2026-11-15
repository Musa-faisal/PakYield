"""Interactive Home dashboard using verified benchmark observations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from app.services import data

HOME_CSS = """
<style>
.pakyield-home-intro {
    padding: 1.1rem 1.25rem;
    margin: 0.4rem 0 1rem 0;
    border: 1px solid #303a45;
    border-left: 3px solid #ff9f1c;
    border-radius: 8px;
    background: linear-gradient(110deg, #171b20 0%, #0c1116 100%);
}

.pakyield-home-intro-label {
    color: #ffb447;
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

.pakyield-home-intro-title {
    color: #f2f4f5;
    font-size: 1.25rem;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 0.4rem;
}

.pakyield-home-intro-copy {
    color: #aab4bd;
    font-size: 0.88rem;
    line-height: 1.5;
}
</style>
"""


def select_observed_curve(
    rows: Iterable[Mapping[str, str]],
    curve_type: str,
    observation_date: str,
) -> list[Mapping[str, str]]:
    """Return actual observations for one curve and exact date."""
    selected = [
        row
        for row in rows
        if row["curve_type"] == curve_type
        and row["observation_date"] == observation_date
    ]

    return sorted(selected, key=lambda row: float(row["tenor_years"]))


def render_home_dashboard() -> None:
    """Render the interactive Home curve explorer."""
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="pakyield-home-intro">
            <div class="pakyield-home-intro-label">Explore the evidence</div>
            <div class="pakyield-home-intro-title">
                Pakistan's sovereign yield curve, one date at a time
            </div>
            <div class="pakyield-home-intro-copy">
                Choose a benchmark and an observation date to explore
                the published maturity structure. Each point below is an
                observed historical value.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        rows = data.load_yield_rows()
    except data.PresentationDataError as exc:
        st.error("The dashboard curve data could not be verified.")
        st.code(str(exc))
        return

    curves = sorted({row["curve_type"] for row in rows})

    if not curves:
        st.info("No verified curve observations are available.")
        return

    controls = st.columns([1, 2])

    with controls[0]:
        selected_curve = st.selectbox(
            "Benchmark",
            curves,
            index=curves.index("PKRV") if "PKRV" in curves else 0,
            key="home_dashboard_curve",
        )

    available_dates = sorted(
        {
            row["observation_date"]
            for row in rows
            if row["curve_type"] == selected_curve
        },
        reverse=True,
    )

    if not available_dates:
        st.info("No observation dates are available for this benchmark.")
        return

    with controls[1]:
        selected_date = st.selectbox(
            "Observation date",
            available_dates,
            key="home_dashboard_date",
        )

    snapshot = select_observed_curve(rows, selected_curve, selected_date)

    if not snapshot:
        st.info("No observed maturities are available for this selection.")
        return

    yields = [float(row["yield_pct"]) for row in snapshot]

    metrics = st.columns(3)

    with metrics[0]:
        st.metric("Observed maturities", str(len(snapshot)))

    with metrics[1]:
        st.metric("Lowest observed yield", f"{min(yields):.2f}%")

    with metrics[2]:
        st.metric("Highest observed yield", f"{max(yields):.2f}%")

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=[float(row["tenor_years"]) for row in snapshot],
            y=yields,
            customdata=[row["tenor"] for row in snapshot],
            mode="lines+markers",
            name=selected_curve,
            line={"width": 3},
            marker={"size": 8},
            connectgaps=False,
            hovertemplate=(
                "Maturity: %{customdata}<br>"
                "Years: %{x:.2f}<br>"
                "Yield: %{y:.2f}%"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    )

    apply_financial_chart_layout(
        figure,
        title=f"{selected_curve} observed curve — {selected_date}",
        xaxis_title="Maturity (years)",
        yaxis_title="Yield (%)",
        height=390,
        hovermode="closest",
    )

    st.plotly_chart(
        figure,
        width="stretch",
        key="home_dashboard_curve_chart",
    )

    st.caption(
        "Historical research data, not live prices. Lines connect observed "
        "points for display; yields for missing maturities are not created."
    )

    with st.expander("View the observations behind this chart"):
        st.dataframe(
            [
                {
                    "Date": row["observation_date"],
                    "Maturity": row["tenor"],
                    "Years": float(row["tenor_years"]),
                    "Yield (%)": float(row["yield_pct"]),
                    "Source": row["source_organization"],
                    "Source file": row["source_file"],
                }
                for row in snapshot
            ],
            width="stretch",
            hide_index=True,
        )
