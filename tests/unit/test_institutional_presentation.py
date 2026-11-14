"""Contract tests for the shared institutional presentation foundation."""

from __future__ import annotations

import inspect

import plotly.graph_objects as go
from app.components import presentation


def test_palette_and_chart_color_contract() -> None:
    """The presentation palette must expose all institutional roles."""

    assert {
        "background",
        "surface",
        "surface_alt",
        "border",
        "text",
        "muted",
        "accent",
        "positive",
        "negative",
        "blue",
        "purple",
        "yellow",
        "cyan",
    }.issubset(presentation.PALETTE)

    assert len(presentation.CHART_COLORS) >= 6

    assert presentation.CHART_COLORS[0] == presentation.PALETTE["accent"]


def test_financial_formatters_keep_units_explicit() -> None:
    """Percent and basis-point formatting must never be ambiguous."""

    assert presentation.format_percent(12.345) == "12.35%"

    assert presentation.format_bps(-37.5) == "-37.5 bps"

    assert presentation.format_decimal(1234.567) == "1,234.57"

    assert presentation.format_percent(None) == "—"

    assert presentation.format_bps(None) == "—"


def test_plotly_style_contract_is_centralized() -> None:
    """Shared chart styling must set institutional layout behavior."""

    figure = go.Figure()

    returned = presentation.style_plotly_figure(
        figure,
        xaxis_title="Date",
        yaxis_title="Yield (%)",
    )

    assert returned is figure

    assert figure.layout.paper_bgcolor == presentation.PALETTE["background"]

    assert figure.layout.plot_bgcolor == presentation.PALETTE["surface"]

    assert figure.layout.hovermode == "x unified"

    assert figure.layout.xaxis.title.text == "Date"

    assert figure.layout.yaxis.title.text == "Yield (%)"

    assert figure.layout.legend.orientation == "h"


def test_disclaimer_sets_research_boundary() -> None:
    """The shared disclaimer must state the core interpretation boundary."""

    text = presentation.APP_DISCLAIMER.lower()

    assert "research" in text
    assert "descriptive" in text
    assert "causality" in text
    assert "investment advice" in text
    assert "methodology" in text


def test_shared_css_contains_core_institutional_surfaces() -> None:
    """The common CSS must style the major Streamlit research surfaces."""

    css = presentation.INSTITUTIONAL_CSS

    assert ".block-container" in css

    assert '[data-testid="stMetric"]' in css

    assert '[data-testid="stDataFrame"]' in css

    assert ".py-page-title" in css
    assert ".py-section-title" in css
    assert ".py-disclaimer" in css


def test_supported_width_api_and_no_data_access() -> None:
    """Presentation helpers must use modern width APIs and remain data-free."""

    source = inspect.getsource(presentation)

    assert 'width="stretch"' in source

    assert "use_container_width=True" not in source

    prohibited = (
        "sqlite3",
        "read_csv(",
        "read_sql",
        "get_connection(",
        "DATABASE_PATH",
        "yield_observations",
        "mpc_events",
    )

    for token in prohibited:
        assert token not in source
