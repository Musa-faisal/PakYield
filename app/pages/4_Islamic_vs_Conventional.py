"""PakYield PKISRV and PKRV comparison laboratory."""

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
    page_title="Islamic vs Conventional | PakYield",
    page_icon="⚖️",
    layout="wide",
)

apply_theme()

render_terminal_bar(
    context="PAKISTAN SOVEREIGN FIXED INCOME",
    status="CROSS-CURVE LAB",
)

render_page_header(
    "CROSS-CURVE",
    "Islamic vs Conventional",
    (
        "Compare PKISRV and PKRV numerically at exact same-date, "
        "same-maturity observations."
    ),
)

render_section_header("Comparable Maturities")

render_placeholder(
    "Exact-date PKISRV and PKRV comparisons will be connected "
    "to the validated cross-curve analytical panel."
)

render_section_header("Observed Difference")

render_placeholder(
    "Numerical PKISRV-minus-PKRV differences will appear here "
    "only where both observed legs exist."
)

render_data_caption(
    "Differences are numerical comparisons only and are not "
    "labelled as Islamic, Sukuk, Shariah, liquidity, or risk premia."
)
