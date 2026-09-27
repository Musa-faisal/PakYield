"""PakYield monetary policy research page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(page_title="Monetary Policy Lab | PakYield", layout="wide")

apply_theme()

render_page_header(
    "Research Module",
    "Monetary Policy Lab",
    "Analyze sovereign-yield movements around SBP MPC announcements.",
)

render_placeholder(
    "Event-study outputs will appear after MPC events and PKRV "
    "observations are validated."
)
