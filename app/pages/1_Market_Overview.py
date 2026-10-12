"""PakYield market overview."""

import streamlit as st

from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from styles.theme import apply_theme

st.set_page_config(
    page_title="Market Overview | PakYield",
    page_icon="📈",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="MARKET OVERVIEW",
)

render_page_header(
    "MARKET",
    "Market Overview",
    (
        "A compact view of Pakistan's sovereign benchmark "
        "rates, monetary-policy context, and curve conditions."
    ),
)

render_section_header("Market Snapshot")

render_placeholder(
    "Market-summary metrics will appear here when the "
    "validated analytical data layer is connected."
)

render_section_header("Curve Monitor")

render_placeholder(
    "PKRV and PKISRV market views will be rendered here "
    "without interpolation or synthetic observations."
)

render_data_caption(
    "Presentation shell only — no analytical values are manufactured in this rollout."
)
