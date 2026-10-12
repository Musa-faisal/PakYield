"""Tests for the Phase 7B Streamlit presentation foundation."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(APP_DIR),
    )

from components.charts import (  # noqa: E402
    add_reference_line,
    apply_financial_chart_layout,
    empty_financial_figure,
)
from components.layout import (  # noqa: E402
    render_metric_card,
)
from styles.theme import (  # noqa: E402
    CHART_SEQUENCE,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_PANEL,
    PAKYIELD_CSS,
)


def test_theme_uses_dense_terminal_visual_contract() -> None:
    """Core visual tokens must preserve the dark terminal direction."""

    assert COLOR_BG == "#060708"
    assert COLOR_PANEL == "#0F1215"
    assert COLOR_ACCENT == "#FF9F1C"

    assert len(CHART_SEQUENCE) >= 6

    required_css = (
        ".pakyield-terminal-bar",
        ".pakyield-panel",
        ".pakyield-section",
        ".pakyield-status-pill",
        'section[data-testid="stSidebar"]',
        'div[data-testid="stDataFrame"]',
        'div[data-testid="stPlotlyChart"]',
    )

    for selector in required_css:
        assert selector in PAKYIELD_CSS


def test_chart_layout_applies_financial_terminal_defaults() -> None:
    """Plotly charts must share the terminal presentation defaults."""

    figure = go.Figure()

    result = apply_financial_chart_layout(
        figure,
        title="PKRV Curve",
        xaxis_title="Maturity",
        yaxis_title="Yield (%)",
        height=440,
    )

    assert result is figure
    assert figure.layout.height == 440
    assert figure.layout.paper_bgcolor == COLOR_BG
    assert figure.layout.plot_bgcolor == COLOR_BG
    assert figure.layout.hovermode == "x unified"
    assert figure.layout.title.text == "PKRV Curve"
    assert figure.layout.xaxis.title.text == "Maturity"
    assert figure.layout.yaxis.title.text == "Yield (%)"


def test_chart_colorway_is_frozen_to_shared_palette() -> None:
    """Charts must consume the central shared color sequence."""

    figure = go.Figure()

    apply_financial_chart_layout(figure)

    assert tuple(figure.layout.colorway) == CHART_SEQUENCE


def test_reference_line_is_annotation_only() -> None:
    """Reference lines must not manufacture chart observations."""

    figure = go.Figure()

    add_reference_line(
        figure,
        y=0.0,
        label="Zero",
    )

    assert len(figure.data) == 0

    assert len(figure.layout.shapes) == 1


def test_empty_figure_contains_no_data_traces() -> None:
    """Empty-state charts must remain genuinely empty."""

    figure = empty_financial_figure(title="No Data")

    assert len(figure.data) == 0

    assert len(figure.layout.annotations) >= 1

    assert (
        figure.layout.annotations[-1].text
        == "No eligible observations for the selected filters."
    )


def test_metric_card_rejects_unknown_direction() -> None:
    """Metric direction labels are constrained to the presentation contract."""

    with pytest.raises(
        ValueError,
        match="direction must be one of",
    ):
        render_metric_card(
            "10Y PKRV",
            "—",
            direction="up-ish",
        )
