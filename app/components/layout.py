"""Reusable presentation components for PakYield Streamlit pages."""

from __future__ import annotations

from html import escape

import streamlit as st


def render_terminal_bar(
    context: str = "Pakistan Sovereign Markets",
    status: str = "Research Terminal",
) -> None:
    """Render the compact PakYield terminal context bar."""

    st.markdown(
        f"""
        <div class="pakyield-terminal-bar">
            <span class="pakyield-terminal-brand">PAKYIELD</span>
            <span class="pakyield-terminal-context">{escape(context)}</span>
            <span class="pakyield-terminal-spacer"></span>
            <span class="pakyield-terminal-status">{escape(status)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    section: str,
    title: str,
    subtitle: str,
) -> None:
    """Render the shared PakYield page heading."""

    st.markdown(
        f"""
        <div class="pakyield-kicker">{escape(section)}</div>
        <div class="pakyield-title">{escape(title)}</div>
        <div class="pakyield-subtitle">{escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(
    title: str,
) -> None:
    """Render a compact research-terminal section heading."""

    st.markdown(
        f"""
        <div class="pakyield-section">{escape(title)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_placeholder(
    message: str,
) -> None:
    """Render a clearly marked placeholder without fabricated values."""

    st.markdown(
        f"""
        <div class="pakyield-placeholder">
            {escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    *,
    delta: str | None = None,
    direction: str = "neutral",
) -> None:
    """Render a compact terminal-style financial metric."""

    allowed_directions = {
        "positive",
        "negative",
        "neutral",
    }

    if direction not in allowed_directions:
        raise ValueError("direction must be one of: positive, negative, neutral")

    delta_html = ""

    if delta is not None:
        delta_html = (
            f'<div class="pakyield-delta pakyield-{direction}">{escape(delta)}</div>'
        )

    st.markdown(
        f"""
        <div class="pakyield-panel">
            <div class="pakyield-label">{escape(label)}</div>
            <div class="pakyield-value">{escape(value)}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_placeholder(
    label: str,
    value: str = "—",
) -> None:
    """Render a terminal-style placeholder metric."""

    render_metric_card(
        label,
        value,
    )


def render_status_pill(
    label: str,
    *,
    status: str = "neutral",
) -> None:
    """Render a small status marker."""

    allowed = {
        "neutral",
        "ok",
        "warn",
    }

    if status not in allowed:
        raise ValueError("status must be one of: neutral, ok, warn")

    modifier = "" if status == "neutral" else f" pakyield-status-pill--{status}"

    st.markdown(
        f"""
        <span class="pakyield-status-pill{modifier}">
            {escape(label)}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_callout(
    message: str,
) -> None:
    """Render a restrained research note or interpretation boundary."""

    st.markdown(
        f"""
        <div class="pakyield-callout">
            {escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_caption(
    message: str,
) -> None:
    """Render compact provenance or sample metadata."""

    st.markdown(
        f"""
        <div class="pakyield-caption">
            {escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )
