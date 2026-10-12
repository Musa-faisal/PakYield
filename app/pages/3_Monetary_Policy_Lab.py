"""PakYield monetary-policy laboratory."""

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
    page_title="Monetary Policy Lab | PakYield",
    page_icon="🏦",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="MONETARY POLICY LAB",
)

render_page_header(
    "POLICY",
    "Monetary Policy Lab",
    (
        "Examine SBP policy decisions, directional regimes, "
        "and observed sovereign-yield announcement windows."
    ),
)

render_section_header("Policy Timeline")

render_placeholder(
    "Validated MPC decisions and policy-rate state will be connected here."
)

render_section_header("Announcement Windows")

render_placeholder(
    "Observed-position MPC event windows will appear here "
    "using the frozen Phase 5C event-study contract."
)

render_data_caption(
    "Announcement-date observations are not silently treated "
    "as post-decision observations when intraday timing is unavailable."
)
