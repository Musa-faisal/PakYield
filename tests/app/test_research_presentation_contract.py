"""Presentation-contract tests for the Research Streamlit page."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAGE_PATH = PROJECT_ROOT / "app" / "pages" / "6_Research.py"


def source() -> str:
    """Return Research page source."""

    return PAGE_PATH.read_text(encoding="utf-8")


def test_research_uses_shared_presentation_helpers() -> None:
    """Research page must adopt the centralized presentation layer."""

    text = source()

    assert (
        "from app.components.presentation import "
        "apply_institutional_css, render_disclaimer" in text
    )

    assert text.count("apply_institutional_css()") == 1

    assert text.count("render_disclaimer()") == 1


def test_research_css_runs_after_page_config() -> None:
    """Streamlit config must precede shared CSS application."""

    text = source()

    config_index = text.index("st.set_page_config(")

    css_index = text.index("apply_institutional_css()")

    assert config_index < css_index


def test_research_disclaimer_is_rendered_after_css() -> None:
    """Institutional disclaimer belongs after presentation setup."""

    text = source()

    css_index = text.index("apply_institutional_css()")

    disclaimer_index = text.index("render_disclaimer()")

    assert css_index < disclaimer_index


def test_research_does_not_invent_plotly_or_dataframe_surface() -> None:
    """Migration must preserve the actual Research rendering surface."""

    text = source()

    assert text.count("st.plotly_chart(") == 0

    assert text.count("st.dataframe(") == 0

    assert "style_plotly_figure" not in text


def test_research_has_no_legacy_or_inline_presentation_overrides() -> None:
    """Research should use centralized presentation primitives."""

    text = source()

    assert "use_container_width=" not in text

    assert "<style" not in text.lower()
