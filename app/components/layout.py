"""Reusable layout components for PakYield Streamlit pages."""

from __future__ import annotations

import streamlit as st


def render_page_header(
    section: str,
    title: str,
    subtitle: str,
) -> None:
    """Render the shared PakYield page heading."""

    st.markdown(
        f"""
        <div class="pakyield-kicker">{section}</div>
        <div class="pakyield-title">{title}</div>
        <div class="pakyield-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_placeholder(message: str) -> None:
    """Render a clearly marked pre-data placeholder."""

    st.markdown(
        f"""
        <div class="pakyield-placeholder">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_placeholder(
    label: str,
    value: str = "—",
) -> None:
    """Render a terminal-style placeholder metric."""

    st.markdown(
        f"""
        <div class="pakyield-panel">
            <div class="pakyield-label">{label}</div>
            <div class="pakyield-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
