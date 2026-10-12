"""PakYield research workspace."""

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
    page_title="Research | PakYield",
    page_icon="🔬",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="RESEARCH",
)

render_page_header(
    "RESEARCH",
    "Research",
    (
        "A controlled workspace for descriptive sovereign-yield, "
        "policy-regime, event-window, and CPI analysis."
    ),
)

render_section_header("Analysis Families")

render_placeholder(
    "Frozen analytical families and their eligibility filters will be surfaced here."
)

render_section_header("Research Notes")

render_placeholder(
    "Documented methodology, assumptions, and analysis outputs "
    "will be connected here in later phases."
)

render_data_caption(
    "Research views must preserve the frozen analytical grains "
    "and explicit missing-data rules."
)
