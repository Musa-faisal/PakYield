"""PakYield research documentation page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(page_title="Research | PakYield", layout="wide")

apply_theme()

render_page_header(
    "Research",
    "Methodology & Findings",
    "Research design, econometric methodology, limitations and verified results.",
)

render_placeholder(
    "Research findings will be published only after empirical analysis "
    "is completed and validated."
)
