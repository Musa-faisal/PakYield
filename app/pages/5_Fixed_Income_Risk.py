"""PakYield fixed-income risk page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(page_title="Fixed-Income Risk | PakYield", layout="wide")

apply_theme()

render_page_header(
    "Analytics Module",
    "Fixed-Income Risk",
    "Bond pricing, duration, modified duration, DV01 and convexity.",
)

render_placeholder(
    "The quantitative risk engine will be connected in a later implementation phase."
)
