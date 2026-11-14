"""PakYield verified Research / Econometrics workspace."""

import streamlit as st
from app.components.presentation import apply_institutional_css, render_disclaimer

from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from components.research import render_research_workspace
from services import econometrics
from styles.theme import apply_theme

st.set_page_config(
    page_title="Research | PakYield",
    page_icon="🔬",
    layout="wide",
)

apply_institutional_css()

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="RESEARCH / ECONOMETRICS",
)

render_page_header(
    "RESEARCH",
    "Research",
    (
        "Explore verified sovereign-yield inferential tests, "
        "monetary-policy regime results, statistical "
        "diagnostics, and observed macroeconomic series."
    ),
)

render_section_header("Research / Econometrics Workbench")

render_research_workspace(econometrics)

render_section_header("Methodology & Research Controls")

with st.expander(
    "Analytical integrity and interpretation rules",
    expanded=False,
):
    render_placeholder(
        "Only frozen, SHA-verified research results are "
        "displayed. Missing observations, exclusions, "
        "non-significant results, and diagnostic warnings "
        "remain visible in their recorded source fields. "
        "This page does not estimate models or calculate "
        "statistical significance."
    )

render_data_caption(
    "Research outputs retain the approved analytical "
    "grains, eligibility rules, HAC settings, "
    "multiple-testing adjustments, and frozen "
    "source-artifact provenance."
)

render_disclaimer()
