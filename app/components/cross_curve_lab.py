"""PKRV and PKISRV comparison using verified analytical observations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from app.services import data


def select_eligible_pairs(
    rows: Iterable[Mapping[str, str]],
) -> list[Mapping[str, str]]:
    """Keep recorded eligible pairs with both yields and their difference."""
    return [
        row
        for row in rows
        if row["paired_comparison_status"] == "ELIGIBLE"
        and row["match_status"] == "MATCHED"
        and row["pkrv_yield_pct"] != ""
        and row["pkisrv_yield_pct"] != ""
        and row["pkisrv_minus_pkrv_bps"] != ""
    ]


def pairs_for_date(
    rows: Iterable[Mapping[str, str]],
    observation_date: str,
) -> list[Mapping[str, str]]:
    """Return same-date pairs sorted by observed maturity."""
    selected = [row for row in rows if row["observation_date"] == observation_date]

    return sorted(selected, key=lambda row: float(row["tenor_years"]))


def history_for_tenor(
    rows: Iterable[Mapping[str, str]],
    tenor: str,
) -> list[Mapping[str, str]]:
    """Return recorded pairs for one exact maturity in date order."""
    selected = [row for row in rows if row["tenor"] == tenor]

    return sorted(selected, key=lambda row: row["observation_date"])


def render_cross_curve_lab() -> bool:
    """Render the existing verified cross-curve comparison panel."""
    try:
        source_rows = data.load_cross_curve_rows()
    except data.PresentationDataError as exc:
        st.error("The PKRV/PKISRV comparison data could not be verified.")
        st.code(str(exc))
        return False

    rows = select_eligible_pairs(source_rows)

    if not rows:
        st.info("No eligible paired benchmark observations are available.")
        return False

    dates = sorted({row["observation_date"] for row in rows}, reverse=True)

    selected_date = st.selectbox(
        "Matched observation date",
        dates,
        key="cross_curve_date",
    )

    snapshot = pairs_for_date(rows, selected_date)

    if not snapshot:
        return False

    st.subheader("Observed benchmark yields")

    curve_figure = go.Figure()

    for label, field in (
        ("PKRV", "pkrv_yield_pct"),
        ("PKISRV", "pkisrv_yield_pct"),
    ):
        curve_figure.add_trace(
            go.Scatter(
                x=[row["tenor"] for row in snapshot],
                y=[float(row[field]) for row in snapshot],
                mode="lines+markers",
                name=label,
                connectgaps=False,
                hovertemplate=(
                    "Maturity: %{x}<br>Yield: %{y:.2f}%<extra>%{fullData.name}</extra>"
                ),
            )
        )

    apply_financial_chart_layout(
        curve_figure,
        title=f"Matched observations — {selected_date}",
        xaxis_title="Observed maturity",
        yaxis_title="Yield (%)",
    )

    curve_figure.update_xaxes(type="category")

    st.plotly_chart(
        curve_figure,
        width="stretch",
        key="cross_curve_yields",
    )

    st.caption(
        "Both benchmarks are shown only where the existing panel records "
        "an eligible pair for the same date and maturity. Lines connect "
        "observed points for display; missing yields are not created."
    )

    st.subheader("PKISRV minus PKRV")

    spread_figure = go.Figure(
        go.Bar(
            x=[row["tenor"] for row in snapshot],
            y=[float(row["pkisrv_minus_pkrv_bps"]) for row in snapshot],
            name="Recorded difference",
            hovertemplate=(
                "Maturity: %{x}<br>PKISRV minus PKRV: %{y:.2f} bps<extra></extra>"
            ),
        )
    )

    apply_financial_chart_layout(
        spread_figure,
        title=f"Numerical benchmark difference — {selected_date}",
        xaxis_title="Observed maturity",
        yaxis_title="PKISRV minus PKRV (bps)",
    )

    spread_figure.update_xaxes(type="category")

    st.plotly_chart(
        spread_figure,
        width="stretch",
        key="cross_curve_difference",
    )

    with st.expander("View matched observations and source files"):
        st.dataframe(
            [
                {
                    "Date": row["observation_date"],
                    "Maturity": row["tenor"],
                    "PKRV yield (%)": float(row["pkrv_yield_pct"]),
                    "PKISRV yield (%)": float(row["pkisrv_yield_pct"]),
                    "Difference (bps)": float(row["pkisrv_minus_pkrv_bps"]),
                    "PKRV source file": row["pkrv_source_file"],
                    "PKISRV source file": row["pkisrv_source_file"],
                }
                for row in snapshot
            ],
            width="stretch",
            hide_index=True,
        )

    st.subheader("Difference through time")

    tenor_years: dict[str, float] = {}

    for row in rows:
        tenor_years[row["tenor"]] = float(row["tenor_years"])

    tenors = sorted(tenor_years, key=lambda tenor: tenor_years[tenor])

    if not tenors:
        st.info("No eligible maturity history is available.")
        return True

    selected_tenor = st.selectbox(
        "Matched maturity",
        tenors,
        key="cross_curve_tenor",
    )

    history = history_for_tenor(rows, selected_tenor)

    if not history:
        st.info("No eligible paired history is available for this maturity.")
        return True

    history_figure = go.Figure(
        go.Scatter(
            x=[row["observation_date"] for row in history],
            y=[float(row["pkisrv_minus_pkrv_bps"]) for row in history],
            mode="markers",
            marker={"size": 4},
            name="Recorded difference",
            hovertemplate=(
                "Date: %{x}<br>PKISRV minus PKRV: %{y:.2f} bps<extra></extra>"
            ),
        )
    )

    apply_financial_chart_layout(
        history_figure,
        title=f"{selected_tenor} matched benchmark differences",
        xaxis_title="Observation date",
        yaxis_title="PKISRV minus PKRV (bps)",
        hovermode="closest",
    )

    st.plotly_chart(
        history_figure,
        width="stretch",
        key="cross_curve_history",
    )

    st.caption(
        "Each marker is an eligible recorded pair. "
        "Missing or ineligible observations are not filled."
    )

    st.info(
        "These differences are numerical benchmark comparisons. "
        "They do not by themselves establish an Islamic, Sukuk, liquidity, "
        "credit, or other structural premium or discount."
    )

    return True
