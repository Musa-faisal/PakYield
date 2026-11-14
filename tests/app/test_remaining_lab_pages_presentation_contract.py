"""Presentation-contract tests for the four remaining PakYield lab pages."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAGES = [
    PROJECT_ROOT / "app" / "pages" / "1_Market_Overview.py",
    PROJECT_ROOT / "app" / "pages" / "2_Yield_Curve_Lab.py",
    PROJECT_ROOT / "app" / "pages" / "3_Monetary_Policy_Lab.py",
    PROJECT_ROOT / "app" / "pages" / "4_Islamic_vs_Conventional.py",
]


def source(
    path: Path,
) -> str:
    """Return one page's source text."""

    return path.read_text(encoding="utf-8")


def test_all_remaining_pages_use_shared_presentation_module() -> None:
    """Every remaining lab page must adopt the institutional layer."""

    for path in PAGES:
        text = source(path)

        assert "from app.components.presentation import" in text

        assert "apply_institutional_css" in text

        assert "render_disclaimer" in text


def test_all_remaining_pages_apply_institutional_css_once() -> None:
    """Institutional CSS is applied once per page."""

    for path in PAGES:
        text = source(path)

        assert text.count("apply_institutional_css()") == 1


def test_all_remaining_pages_render_disclaimer_once() -> None:
    """Each page renders the shared disclaimer exactly once."""

    for path in PAGES:
        text = source(path)

        assert text.count("render_disclaimer()") == 1


def test_all_remaining_pages_preserve_section_structure() -> None:
    """Existing institutional section hierarchy remains present."""

    for path in PAGES:
        text = source(path)

        assert text.count("render_section_header(") >= 1


def test_all_remaining_pages_avoid_legacy_width_api() -> None:
    """Migrated pages must not reintroduce deprecated width syntax."""

    for path in PAGES:
        text = source(path)

        assert "use_container_width=" not in text
