"""PakYield market overview page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(page_title="Market Overview | PakYield", layout="wide")

apply_theme()

render_page_header(
    "Market",
    "Market Overview",
    "High-level view of Pakistan's sovereign yield environment.",
)

render_placeholder(
    "Market metrics will populate after validated research data is ingested."
)
