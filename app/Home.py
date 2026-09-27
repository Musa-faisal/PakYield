"""PakYield Lab Streamlit entry point."""

from __future__ import annotations

import streamlit as st

from components.layout import (
    render_metric_placeholder,
    render_page_header,
    render_placeholder,
)
from styles.theme import apply_theme

st.set_page_config(
    page_title="PakYield Lab",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

render_page_header(
    section="PakYield Lab",
    title="Pakistan Sovereign Fixed-Income Research Terminal",
    subtitle=(
        "Yield curves, monetary policy transmission, Islamic fixed income, "
        "risk analytics and empirical research."
    ),
)

metric_columns = st.columns(4)

with metric_columns[0]:
    render_metric_placeholder("Policy Rate")

with metric_columns[1]:
    render_metric_placeholder("1Y PKRV")

with metric_columns[2]:
    render_metric_placeholder("10Y PKRV")

with metric_columns[3]:
    render_metric_placeholder("10Y–2Y Slope")

st.markdown("### Market Workspace")

render_placeholder(
    "The research database is intentionally empty at this stage. "
    "Market charts and verified empirical results will appear here only after "
    "the PakYield ingestion and validation pipeline has been completed."
)

st.markdown("### Research Modules")

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

        Examine price sensitivity, duration, modified duration, DV01 and
        convexity.

        **Research**

        Review methodology, econometric analysis, limitations and verified
        findings.
        """
    )

st.caption(
    "PakYield Lab — research interface architecture initialized. "
    "No empirical results are displayed before validated data ingestion."
)
