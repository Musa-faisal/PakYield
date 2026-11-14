"""PakYield PKISRV and PKRV comparison laboratory."""

import streamlit as st
from app.components.presentation import apply_institutional_css, render_disclaimer

from components.cross_curve_lab import render_cross_curve_lab
from components.layout import (
    render_data_caption,
    render_page_header,
    render_placeholder,
    render_section_header,
    render_terminal_bar,
)
from styles.theme import apply_theme

st.set_page_config(
    page_title="Islamic vs Conventional | PakYield",
    page_icon="⚖️",
    layout="wide",
)

apply_theme()
apply_institutional_css()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="CROSS-CURVE LAB",
)

render_page_header(
    "CROSS-CURVE",
    "Islamic vs Conventional",
    ("Compare PKISRV and PKRV at the same observed dates and maturities."),
)

render_section_header("Comparable Maturities")

if not render_cross_curve_lab():
    render_placeholder("No verified matched benchmark observations are available.")

render_data_caption(
    "Differences are numerical comparisons only. Historical research "
    "observations are not live market quotes."
)

render_disclaimer()
