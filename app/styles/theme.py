"""Shared visual styling for the PakYield Streamlit application."""

from __future__ import annotations

import streamlit as st

PAKYIELD_CSS = """
<style>
    .stApp {
        background-color: #0b0e11;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .pakyield-kicker {
        color: #ff9f1c;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .pakyield-title {
        color: #f5f7fa;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .pakyield-subtitle {
        color: #9aa4b2;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }

    .pakyield-panel {
        border: 1px solid #27313d;
        background: #11161d;
        padding: 1rem;
        border-radius: 4px;
    }

    .pakyield-label {
        color: #8e99a8;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .pakyield-value {
        color: #f5f7fa;
        font-size: 1.45rem;
        font-weight: 700;
    }

    .pakyield-placeholder {
        border: 1px dashed #33404d;
        background: #0f141a;
        color: #8e99a8;
        padding: 1.25rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
</style>
"""


def apply_theme() -> None:
    """Apply PakYield's shared Streamlit CSS."""

    st.markdown(PAKYIELD_CSS, unsafe_allow_html=True)
