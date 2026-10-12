"""PakYield fixed-income risk laboratory."""

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
    page_title="Fixed Income Risk | PakYield",
    page_icon="🛡️",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="RISK LAB",
)

render_page_header(
    "RISK",
    "Fixed Income Risk",
    (
        "Explore observed yield changes, maturity exposure, "
        "and descriptive sovereign fixed-income risk measures."
    ),
)

render_section_header("Yield-Move Monitor")

render_placeholder(
    "Validated yield-change distributions and maturity-level "
    "risk summaries will be connected here."
)

render_section_header("Risk Diagnostics")

render_placeholder(
    "Descriptive fixed-income risk diagnostics will appear "
    "here without introducing unsupported model assumptions."
)

render_data_caption(
    "This presentation layer does not imply predictive power, "
    "statistical significance, or causal monetary-policy effects."
)
