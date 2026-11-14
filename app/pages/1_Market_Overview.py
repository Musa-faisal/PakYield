"""PakYield market overview."""

import streamlit as st
from app.components.presentation import apply_institutional_css, render_disclaimer

from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from components.market_overview import render_market_workspace
from styles.theme import apply_theme

st.set_page_config(
    page_title="Market Overview | PakYield",
    page_icon="📈",
    layout="wide",
)

apply_theme()
apply_institutional_css()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="MARKET OVERVIEW",
)

render_page_header(
    "MARKET",
    "Market Overview",
    (
        "Explore observed sovereign benchmark curves and compare "
        "yields across two available dates."
    ),
)

render_section_header("Market Snapshot")

if not render_market_workspace():
    render_placeholder(
        "No verified market observations are available for this selection."
    )

render_data_caption(
    "Historical research data from verified PakYield artifacts. "
    "These observations are not live market quotes."
)

render_disclaimer()
