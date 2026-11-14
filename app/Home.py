"""PakYield Lab home page using verified analytical artifacts."""

from __future__ import annotations

import streamlit as st

from app.components.presentation import (
    apply_institutional_css,
    render_disclaimer,
    render_methodology_note,
    render_section_header,
)
from app.services import data
from components.layout import render_metric_card, render_page_header
from styles.theme import apply_theme


def format_percent(value: str | None) -> str:
    """Format a percentage value without inventing missing observations."""
    if value is None or value == "":
        return "—"
    return f"{float(value):.2f}%"


def format_basis_points(value: str | None) -> str:
    """Format a basis-point value without inventing missing observations."""
    if value is None or value == "":
        return "—"
    return f"{float(value):.0f} bps"


st.set_page_config(
    page_title="PakYield Lab",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
apply_institutional_css()

render_page_header(
    section="PakYield Lab",
    title="Pakistan Sovereign Fixed-Income Research Terminal",
    subtitle=(
        "Explore Pakistani sovereign benchmark yields, monetary policy, "
        "fixed-income risk, and empirical research."
    ),
)

render_section_header("Market Workspace")

try:
    policy = data.latest_policy_context()
    one_year = data.latest_observed_yield("PKRV", "1Y")
    ten_year = data.latest_observed_yield("PKRV", "10Y")
    term_spread = data.latest_term_spread("10Y-2Y")
except data.PresentationDataError as exc:
    st.error(
        "The market data could not be verified. The affected metrics are unavailable."
    )
    st.code(str(exc))
else:
    columns = st.columns(4)

    with columns[0]:
        render_metric_card(
            "Policy Rate",
            format_percent(policy["policy_rate_pct"] if policy else None),
        )
        if policy:
            st.caption(f"Context date: {policy['observation_date']}")

    with columns[1]:
        render_metric_card(
            "1Y PKRV",
            format_percent(one_year["yield_pct"] if one_year else None),
        )
        if one_year:
            st.caption(f"Observed: {one_year['observation_date']}")

    with columns[2]:
        render_metric_card(
            "10Y PKRV",
            format_percent(ten_year["yield_pct"] if ten_year else None),
        )
        if ten_year:
            st.caption(f"Observed: {ten_year['observation_date']}")

    with columns[3]:
        render_metric_card(
            "10Y–2Y Slope",
            format_basis_points(
                term_spread["term_spread_bps"] if term_spread else None
            ),
        )
        if term_spread:
            st.caption(f"Observed: {term_spread['observation_date']}")

    st.caption(
        "Each metric shows its latest available verified observation. "
        "Dates may differ; these are historical research data, not live quotes."
    )

render_section_header("Research Modules")

left, right = st.columns(2)

with left:
    st.markdown(
        """
        **Yield Curve Lab**

        Explore Pakistan's conventional sovereign benchmark curve across
        maturities and time.

        **Monetary Policy Lab**

        Study yield movements around SBP Monetary Policy Committee events.

        **Islamic vs Conventional**

        Compare standardized PKISRV and PKRV observations at matching tenors.
        """
    )

with right:
    st.markdown(
        """
        **Fixed-Income Risk**

        Examine bond price sensitivity, duration, DV01 and convexity.

        **Research**

        Review methodology, econometric analysis and research limitations.
        """
    )

render_methodology_note(
    "Market metrics are drawn from verified PakYield analytical artifacts. "
    "Missing observations are not replaced with fabricated values."
)

render_disclaimer()
