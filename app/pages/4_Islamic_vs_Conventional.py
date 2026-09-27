"""PakYield Islamic versus conventional research page."""

import streamlit as st

from components.layout import render_page_header, render_placeholder
from styles.theme import apply_theme

st.set_page_config(
    page_title="Islamic vs Conventional | PakYield",
    layout="wide",
)

apply_theme()

render_page_header(
    "Research Module",
    "Islamic vs Conventional",
    "Compare standardized PKISRV and PKRV benchmark observations.",
)

render_placeholder(
    "Comparative analysis will use only verified matching dates and tenors."
)
