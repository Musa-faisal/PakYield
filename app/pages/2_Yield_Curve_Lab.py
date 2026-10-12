"""PakYield sovereign yield-curve laboratory."""

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
    page_title="Yield Curve Lab | PakYield",
    page_icon="📉",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="YIELD CURVE LAB",
)

render_page_header(
    "CURVES",
    "Yield Curve Lab",
    (
        "Inspect the sovereign term structure across observed "
        "maturities while preserving source-date integrity."
    ),
)

render_section_header("Curve Explorer")

render_placeholder(
    "Interactive maturity and date controls will be connected "
    "to validated PKRV and PKISRV observations."
)

render_section_header("Term Structure Diagnostics")

render_placeholder(
    "Observed term spreads and curve-shape diagnostics will "
    "appear here using frozen analytical inputs."
)

render_data_caption(
    "No interpolation, nearest-tenor substitution, or "
    "synthetic curve points are introduced by this page shell."
)
