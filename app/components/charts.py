"""Reusable Plotly presentation helpers for PakYield."""

from __future__ import annotations

import plotly.graph_objects as go

try:
    from styles.theme import (
        CHART_SEQUENCE,
        COLOR_ACCENT,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_GRID,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
    )
except ModuleNotFoundError:
    from app.styles.theme import (
        CHART_SEQUENCE,
        COLOR_ACCENT,
        COLOR_BG,
        COLOR_BORDER,
        COLOR_GRID,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
    )


def apply_financial_chart_layout(
    figure: go.Figure,
    *,
    title: str = "",
    xaxis_title: str = "",
    yaxis_title: str = "",
    height: int = 420,
    hovermode: str = "x unified",
) -> go.Figure:
    """Apply PakYield's dense research-terminal chart presentation."""

    figure.update_layout(
        title={
            "text": title,
            "x": 0.01,
            "xanchor": "left",
            "font": {
                "size": 14,
                "color": COLOR_TEXT,
            },
        },
        height=height,
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        font={
            "color": COLOR_TEXT_MUTED,
            "family": (
                "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            ),
            "size": 11,
        },
        margin={
            "l": 54,
            "r": 24,
            "t": 48 if title else 24,
            "b": 46,
        },
        hovermode=hovermode,
        hoverlabel={
            "bgcolor": "#111519",
            "bordercolor": COLOR_BORDER,
            "font": {
                "color": COLOR_TEXT,
                "size": 11,
            },
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
            "font": {
                "size": 10,
                "color": COLOR_TEXT_MUTED,
            },
        },
        colorway=list(CHART_SEQUENCE),
    )

    figure.update_xaxes(
        title_text=xaxis_title,
        showgrid=True,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor=COLOR_BORDER,
        tickfont={
            "size": 10,
            "color": COLOR_TEXT_MUTED,
        },
        title_font={
            "size": 10,
            "color": COLOR_TEXT_MUTED,
        },
        fixedrange=False,
    )

    figure.update_yaxes(
        title_text=yaxis_title,
        showgrid=True,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=COLOR_BORDER,
        zerolinewidth=1,
        showline=True,
        linecolor=COLOR_BORDER,
        tickfont={
            "size": 10,
            "color": COLOR_TEXT_MUTED,
        },
        title_font={
            "size": 10,
            "color": COLOR_TEXT_MUTED,
        },
        fixedrange=False,
    )

    return figure


def add_reference_line(
    figure: go.Figure,
    *,
    y: float,
    label: str | None = None,
) -> go.Figure:
    """Add a restrained horizontal analytical reference line."""

    figure.add_hline(
        y=y,
        line_width=1,
        line_dash="dot",
        line_color=COLOR_ACCENT,
        annotation_text=label,
        annotation_position="top left",
        annotation_font={
            "size": 10,
            "color": COLOR_ACCENT,
        },
    )

    return figure


def empty_financial_figure(
    *,
    title: str = "",
    message: str = "No eligible observations for the selected filters.",
    height: int = 360,
) -> go.Figure:
    """Create a truthful empty-state figure without manufacturing data."""

    figure = go.Figure()

    apply_financial_chart_layout(
        figure,
        title=title,
        height=height,
        hovermode="closest",
    )

    figure.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text=message,
        showarrow=False,
        font={
            "size": 12,
            "color": COLOR_TEXT_MUTED,
        },
    )

    figure.update_xaxes(visible=False)

    figure.update_yaxes(visible=False)

    return figure
