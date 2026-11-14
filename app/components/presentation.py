"""Shared institutional presentation primitives for the PakYield application.

This module centralizes presentation-only behavior. It must not load project
data, query SQLite, estimate models, or alter analytical results.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import plotly.graph_objects as go
import streamlit as st

PALETTE = {
    "background": "#0b0e11",
    "surface": "#151a21",
    "surface_alt": "#20262c",
    "border": "#2a3036",
    "text": "#e7e9ea",
    "muted": "#9aa3ab",
    "accent": "#ff9f1c",
    "positive": "#38b27b",
    "negative": "#e05a5a",
    "blue": "#4da3ff",
    "purple": "#d679e8",
    "yellow": "#e8d35c",
    "cyan": "#75d1d1",
}

CHART_COLORS = (
    PALETTE["accent"],
    PALETTE["blue"],
    PALETTE["positive"],
    PALETTE["purple"],
    PALETTE["yellow"],
    PALETTE["cyan"],
    PALETTE["negative"],
)

APP_DISCLAIMER = (
    "PakYield is a research and educational analytics application. "
    "Outputs are descriptive unless an analysis explicitly states otherwise. "
    "They do not establish causality, do not represent investment advice, "
    "and should be interpreted together with the documented methodology, "
    "data coverage, and limitations."
)

INSTITUTIONAL_CSS = f"""
<style>
:root {{
    --py-background: {PALETTE["background"]};
    --py-surface: {PALETTE["surface"]};
    --py-surface-alt: {PALETTE["surface_alt"]};
    --py-border: {PALETTE["border"]};
    --py-text: {PALETTE["text"]};
    --py-muted: {PALETTE["muted"]};
    --py-accent: {PALETTE["accent"]};
    --py-positive: {PALETTE["positive"]};
    --py-negative: {PALETTE["negative"]};
}}

.block-container {{
    max-width: 1480px;
    padding-top: 5rem;
    padding-bottom: 4rem;
}}

[data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(
            circle at 8% -10%,
            rgba(255, 159, 28, 0.08),
            transparent 28rem
        ),
        var(--py-background);
}}

[data-testid="stHeader"] {{
    background: rgba(11, 14, 17, 0.86);
}}

[data-testid="stMetric"] {{
    background: linear-gradient(
        145deg,
        var(--py-surface),
        rgba(21, 26, 33, 0.78)
    );
    border: 1px solid var(--py-border);
    border-radius: 12px;
    padding: 0.9rem 1rem;
}}

[data-testid="stMetricLabel"] {{
    color: var(--py-muted);
}}

[data-testid="stMetricValue"] {{
    color: var(--py-text);
}}

[data-testid="stDataFrame"] {{
    border: 1px solid var(--py-border);
    border-radius: 10px;
    overflow: hidden;
}}

.py-eyebrow {{
    color: var(--py-accent);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}}

.py-page-title {{
    color: var(--py-text);
    font-size: clamp(2rem, 4vw, 3.25rem);
    font-weight: 700;
    letter-spacing: -0.035em;
    line-height: 1.05;
    margin: 0;
}}

.py-page-subtitle {{
    color: var(--py-muted);
    font-size: 1rem;
    line-height: 1.65;
    max-width: 900px;
    margin-top: 0.8rem;
    margin-bottom: 1.7rem;
}}

.py-section-title {{
    color: var(--py-text);
    font-size: 1.2rem;
    font-weight: 650;
    letter-spacing: -0.015em;
    margin-top: 1.5rem;
    margin-bottom: 0.15rem;
}}

.py-section-caption {{
    color: var(--py-muted);
    font-size: 0.86rem;
    line-height: 1.55;
    margin-bottom: 0.85rem;
}}

.py-disclaimer {{
    background: rgba(32, 38, 44, 0.55);
    border: 1px solid var(--py-border);
    border-left: 3px solid var(--py-accent);
    border-radius: 8px;
    color: var(--py-muted);
    font-size: 0.78rem;
    line-height: 1.55;
    margin-top: 2rem;
    padding: 0.8rem 1rem;
}}

.py-methodology {{
    color: var(--py-muted);
    border-left: 2px solid var(--py-border);
    font-size: 0.82rem;
    line-height: 1.55;
    margin: 0.75rem 0 1rem;
    padding-left: 0.9rem;
}}
</style>
"""


@dataclass(frozen=True)
class MetricSpec:
    """One display-only KPI specification."""

    label: str
    value: str
    delta: str | None = None
    help_text: str | None = None


def format_percent(
    value: float | int | None,
    digits: int = 2,
) -> str:
    """Format a value already expressed in percent units."""

    if value is None:
        return "—"

    return f"{float(value):,.{digits}f}%"


def format_bps(
    value: float | int | None,
    digits: int = 1,
) -> str:
    """Format a value expressed in basis points."""

    if value is None:
        return "—"

    return f"{float(value):,.{digits}f} bps"


def format_decimal(
    value: float | int | None,
    digits: int = 2,
) -> str:
    """Format a generic decimal value."""

    if value is None:
        return "—"

    return f"{float(value):,.{digits}f}"


def apply_institutional_css() -> None:
    """Apply the application-wide institutional presentation layer."""

    st.markdown(
        INSTITUTIONAL_CSS,
        unsafe_allow_html=True,
    )


def render_page_intro(
    title: str,
    subtitle: str,
    *,
    eyebrow: str | None = None,
) -> None:
    """Render a consistent research-page introduction."""

    if eyebrow:
        st.markdown(
            f'<div class="py-eyebrow">{eyebrow}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<h1 class="py-page-title">{title}</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="py-page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def render_section_header(
    title: str,
    caption: str | None = None,
) -> None:
    """Render a consistent section heading."""

    st.markdown(
        f'<div class="py-section-title">{title}</div>',
        unsafe_allow_html=True,
    )

    if caption:
        st.markdown(
            f'<div class="py-section-caption">{caption}</div>',
            unsafe_allow_html=True,
        )


def render_metric_row(
    metrics: Sequence[MetricSpec],
) -> None:
    """Render a responsive row of research KPIs."""

    if not metrics:
        return

    columns = st.columns(len(metrics))

    for column, metric in zip(
        columns,
        metrics,
        strict=True,
    ):
        with column:
            st.metric(
                label=metric.label,
                value=metric.value,
                delta=metric.delta,
                help=metric.help_text,
            )


def render_methodology_note(
    text: str,
) -> None:
    """Render concise methodology or interpretation guidance."""

    st.markdown(
        f'<div class="py-methodology">{text}</div>',
        unsafe_allow_html=True,
    )


def render_empty_state(
    message: str,
    *,
    detail: str | None = None,
) -> None:
    """Render a consistent no-data state."""

    body = message

    if detail:
        body = f"{message}\n\n{detail}"

    st.info(body)


def render_disclaimer() -> None:
    """Render the application research disclaimer."""

    st.markdown(
        (f'<div class="py-disclaimer">{APP_DISCLAIMER}</div>'),
        unsafe_allow_html=True,
    )


def style_plotly_figure(
    figure: go.Figure,
    *,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
) -> go.Figure:
    """Apply the shared PakYield Plotly presentation contract."""

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=PALETTE["background"],
        plot_bgcolor=PALETTE["surface"],
        font={
            "color": PALETTE["text"],
            "family": ("Inter, ui-sans-serif, system-ui, sans-serif"),
            "size": 12,
        },
        colorway=list(CHART_COLORS),
        hovermode="x unified",
        margin={
            "l": 20,
            "r": 20,
            "t": 55,
            "b": 25,
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
    )

    figure.update_xaxes(
        gridcolor=PALETTE["border"],
        zerolinecolor=PALETTE["border"],
        showline=False,
    )

    figure.update_yaxes(
        gridcolor=PALETTE["border"],
        zerolinecolor=PALETTE["border"],
        showline=False,
    )

    return figure


def render_plotly(
    figure: go.Figure,
    *,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    key: str | None = None,
) -> None:
    """Style and render a Plotly figure using supported width semantics."""

    styled = style_plotly_figure(
        figure,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
    )

    st.plotly_chart(
        styled,
        width="stretch",
        key=key,
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )


def render_dataframe(
    data: Any,
    **kwargs: Any,
) -> None:
    """Render tabular output using supported stretch-width semantics."""

    kwargs.pop(
        "use_container_width",
        None,
    )

    kwargs.setdefault(
        "width",
        "stretch",
    )

    st.dataframe(
        data,
        **kwargs,
    )
