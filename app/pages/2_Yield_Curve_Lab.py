"""PakYield yield curve research page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(page_title="Yield Curve Lab | PakYield", layout="wide")

apply_theme()

render_page_header(
    "Research Module",
    "Yield Curve Lab",
    "Explore PKRV curve shape, maturity structure and historical movements.",
)

render_placeholder(
    "Yield-curve visualizations will be connected after the PKRV pipeline is validated."
)
