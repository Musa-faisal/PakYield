"""PakYield monetary-policy laboratory."""

import streamlit as st
from app.components.presentation import apply_institutional_css, render_disclaimer

from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from components.monetary_policy_lab import render_monetary_policy_lab
from styles.theme import apply_theme

st.set_page_config(
    page_title="Monetary Policy Lab | PakYield",
    page_icon="🏦",
    layout="wide",
)

apply_theme()
apply_institutional_css()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="MONETARY POLICY LAB",
)

render_page_header(
    "POLICY",
    "Monetary Policy Lab",
    (
        "Examine SBP policy decisions and observed sovereign-yield "
        "movements around announcement dates."
    ),
)

render_section_header("MPC Announcement Windows")

if not render_monetary_policy_lab():
    render_placeholder(
        "No verified MPC event-window data are available for this selection."
    )

render_data_caption(
    "Historical research data from verified PakYield artifacts. "
    "Announcement-window movements do not by themselves establish causality."
)

render_disclaimer()
