"""PakYield fixed-income risk laboratory."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from app.components.presentation import (
    apply_institutional_css,
    render_disclaimer,
    style_plotly_figure,
)

from components.layout import (
    render_data_caption,
    render_page_header,
    render_section_header,
    render_terminal_bar,
)
from services.data import (
    fixed_income_analysis,
    fixed_income_price_curve,
)
from styles.theme import apply_theme

st.set_page_config(
    page_title="Fixed-Income Risk | PakYield",
    page_icon="📐",
    layout="wide",
)

apply_institutional_css()

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="RISK LAB",
)

render_page_header(
    "RISK",
    "Fixed-Income Risk Lab",
    (
        "Explore valuation, interest-rate sensitivity, "
        "cash flows, and rate-shock behaviour using the "
        "tested PakYield fixed-rate bullet bond engine."
    ),
)

st.info(
    "This calculator is a generic fixed-rate bullet bond model. "
    "It is not a universal Sukuk valuation model."
)

render_section_header("Bond Inputs")

input_col_1, input_col_2, input_col_3 = st.columns(3)

with input_col_1:
    face_value = st.number_input(
        "Face Value",
        min_value=1.0,
        value=1000.0,
        step=100.0,
        format="%.2f",
    )

    coupon_rate_pct = st.number_input(
        "Annual Coupon Rate (%)",
        min_value=0.0,
        value=12.0,
        step=0.25,
        format="%.2f",
    )

with input_col_2:
    ytm_pct = st.number_input(
        "Yield to Maturity (%)",
        min_value=0.0,
        value=12.0,
        step=0.25,
        format="%.2f",
    )

    frequency_label = st.selectbox(
        "Coupon Frequency",
        options=(
            "Annual",
            "Semiannual",
            "Quarterly",
        ),
        index=1,
    )

frequency_map = {
    "Annual": 1,
    "Semiannual": 2,
    "Quarterly": 4,
}

coupon_frequency = frequency_map[frequency_label]

with input_col_3:
    years_to_maturity = st.number_input(
        "Maturity (Years)",
        min_value=(1.0 / coupon_frequency),
        value=5.0,
        step=(1.0 / coupon_frequency),
        format="%.2f",
    )

    rate_shock_bps = st.number_input(
        "Selected Rate Shock (bps)",
        min_value=-2000,
        max_value=2000,
        value=100,
        step=25,
    )


try:
    analysis = fixed_income_analysis(
        face_value=face_value,
        coupon_rate_pct=(coupon_rate_pct),
        ytm_pct=ytm_pct,
        years_to_maturity=(years_to_maturity),
        coupon_frequency=(coupon_frequency),
        rate_shock_bps=int(rate_shock_bps),
    )

    price_curve = fixed_income_price_curve(
        face_value=face_value,
        coupon_rate_pct=(coupon_rate_pct),
        center_ytm_pct=(ytm_pct),
        years_to_maturity=(years_to_maturity),
        coupon_frequency=(coupon_frequency),
    )

except ValueError as exc:
    st.error(
        "The selected bond inputs cannot be valued by "
        f"the fixed-rate bullet model: {exc}"
    )

    st.stop()


render_section_header("Valuation & Risk Metrics")

metric_columns = st.columns(5)

metric_columns[0].metric(
    "Bond Price",
    f"{analysis['price']:,.2f}",
)

metric_columns[1].metric(
    "Macaulay Duration",
    (f"{analysis['macaulay_duration_years']:.3f} yrs"),
)

metric_columns[2].metric(
    "Modified Duration",
    (f"{analysis['modified_duration_years']:.3f} yrs"),
)

metric_columns[3].metric(
    "DV01",
    f"{analysis['dv01']:,.4f}",
)

metric_columns[4].metric(
    "Convexity",
    (f"{analysis['convexity_years_squared']:.3f}"),
)


cash_flows = analysis["cash_flows"]

scenarios = analysis["scenarios"]


render_section_header("Contractual Cash Flows")

cash_flow_figure = go.Figure()

cash_flow_figure.add_bar(
    x=[row["time_years"] for row in cash_flows],
    y=[row["total_cash_flow"] for row in cash_flows],
    name="Total Cash Flow",
)

cash_flow_figure.update_layout(
    xaxis_title="Time (Years)",
    yaxis_title="Cash Flow",
    hovermode="x unified",
)

style_plotly_figure(cash_flow_figure)
st.plotly_chart(
    cash_flow_figure,
    width="stretch",
)


render_section_header("Price-Yield Curve")

price_yield_figure = go.Figure()

price_yield_figure.add_scatter(
    x=[row["ytm_pct"] for row in price_curve],
    y=[row["price"] for row in price_curve],
    mode="lines",
    name="Repriced Bond",
)

price_yield_figure.add_scatter(
    x=[ytm_pct],
    y=[analysis["price"]],
    mode="markers",
    marker={
        "size": 10,
    },
    name="Current Input",
)

price_yield_figure.update_layout(
    xaxis_title="Yield to Maturity (%)",
    yaxis_title="Bond Price",
    hovermode="x unified",
)

style_plotly_figure(price_yield_figure)
st.plotly_chart(
    price_yield_figure,
    width="stretch",
)


render_section_header("Rate-Shock Scenarios")

scenario_figure = go.Figure()

shock_axis = [row["shock_bps"] for row in scenarios]

scenario_figure.add_scatter(
    x=shock_axis,
    y=[row["actual_repriced_price"] for row in scenarios],
    mode="lines+markers",
    name="Actual Repricing",
)

scenario_figure.add_scatter(
    x=shock_axis,
    y=[row["duration_only_price"] for row in scenarios],
    mode="lines+markers",
    name="Duration Only",
)

scenario_figure.add_scatter(
    x=shock_axis,
    y=[row["duration_convexity_price"] for row in scenarios],
    mode="lines+markers",
    name="Duration + Convexity",
)

scenario_figure.update_layout(
    xaxis_title="Yield Shock (bps)",
    yaxis_title="Bond Price",
    hovermode="x unified",
)

style_plotly_figure(scenario_figure)
st.plotly_chart(
    scenario_figure,
    width="stretch",
)


selected_shock = next(
    row for row in scenarios if row["shock_bps"] == int(rate_shock_bps)
)

selected_columns = st.columns(4)

selected_columns[0].metric(
    "Selected Shock",
    f"{int(rate_shock_bps):+d} bps",
)

selected_columns[1].metric(
    "Actual Repriced Value",
    (f"{selected_shock['actual_repriced_price']:,.2f}"),
)

selected_columns[2].metric(
    "Duration Estimate",
    (f"{selected_shock['duration_only_price']:,.2f}"),
)

selected_columns[3].metric(
    "Duration + Convexity",
    (f"{selected_shock['duration_convexity_price']:,.2f}"),
)


with st.expander("Scenario Details"):
    st.dataframe(
        scenarios,
        width="stretch",
        hide_index=True,
    )


render_section_header("How to Read the Results")

st.markdown(
    f"""
- The model price for the selected inputs is **{analysis["price"]:,.2f}**.
- Macaulay duration is **{analysis["macaulay_duration_years"]:.3f} years**;
  modified duration summarizes first-order price sensitivity to yield changes.
- DV01 is **{analysis["dv01"]:,.4f}** in the same currency units as face value
  and approximates the price effect of a one-basis-point yield move.
- Convexity is used with duration to improve the approximation for larger
  parallel yield changes.
- The scenario chart compares those approximations with full repricing by the
  tested backend engine.
"""
)

render_data_caption(
    "Financial calculations are produced by "
    "the tested fixed-income backend; the Streamlit page does not "
    "reimplement bond-pricing, duration, DV01, convexity, "
    "or shock formulas."
)

render_disclaimer()
