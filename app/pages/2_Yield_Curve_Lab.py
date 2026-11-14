"""PakYield sovereign yield-curve laboratory."""

import streamlit as st
from app.components.presentation import apply_institutional_css, render_disclaimer

from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from components.yield_curve_lab import render_yield_curve_lab
from styles.theme import apply_theme

st.set_page_config(
    page_title="Yield Curve Lab | PakYield",
    page_icon="📉",
    layout="wide",
)

apply_theme()
apply_institutional_css()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="YIELD CURVE LAB",
)

render_page_header(
    "CURVES",
    "Yield Curve Lab",
    (
        "Explore observed sovereign benchmark curves, maturity histories, "
        "and eligible Nelson–Siegel model results."
    ),
)

render_section_header("Curve Explorer")

if not render_yield_curve_lab():
    render_placeholder(
        "No verified yield observations are available for this selection."
    )

render_data_caption(
    "Historical research data from verified PakYield artifacts. "
    "No missing benchmark observations are fabricated."
)

render_disclaimer()
