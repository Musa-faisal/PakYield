"""Presentation-contract tests for the main PakYield dashboard."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DASHBOARD_PATH = PROJECT_ROOT / "app" / "streamlit_app.py"

PRESENTATION_PATH = PROJECT_ROOT / "app" / "components" / "presentation.py"


def dashboard_source() -> str:
    """Return main dashboard source."""

    return DASHBOARD_PATH.read_text(encoding="utf-8")


def dashboard_tree() -> ast.Module:
    """Return parsed main dashboard AST."""

    return ast.parse(dashboard_source())


def test_main_dashboard_uses_shared_presentation_foundation() -> None:
    """Dashboard must adopt the shared institutional layer."""

    source = dashboard_source()

    assert "from app.components.presentation import" in source

    assert "apply_institutional_css" in source

    assert "render_disclaimer" in source

    assert source.count("apply_institutional_css()") == 1

    assert source.count("render_disclaimer()") == 1


def test_main_dashboard_has_no_legacy_width_api() -> None:
    """Dashboard must use supported Streamlit width semantics."""

    source = dashboard_source()

    assert "use_container_width=" not in source

    tree = dashboard_tree()

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        for keyword in node.keywords:
            assert keyword.arg != "use_container_width"


def test_main_dashboard_keeps_page_config_before_presentation() -> None:
    """Page config must remain ahead of presentation rendering."""

    tree = dashboard_tree()

    page_config_line = None
    css_line = None

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        func = node.func

        if (
            isinstance(
                func,
                ast.Attribute,
            )
            and isinstance(
                func.value,
                ast.Name,
            )
            and func.value.id == "st"
            and func.attr == "set_page_config"
        ):
            page_config_line = node.lineno

        if (
            isinstance(
                func,
                ast.Name,
            )
            and func.id == "apply_institutional_css"
        ):
            css_line = node.lineno

    assert page_config_line is not None

    assert css_line is not None

    assert page_config_line < css_line


def test_main_dashboard_remains_service_driven() -> None:
    """Presentation migration must not introduce direct data access."""

    tree = dashboard_tree()

    forbidden_names = {
        "open",
        "read_csv",
        "read_excel",
        "read_parquet",
    }

    forbidden_attributes = {
        "execute",
        "executemany",
        "read_sql",
        "read_sql_query",
    }

    violations = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        func = node.func

        if (
            isinstance(
                func,
                ast.Name,
            )
            and func.id in forbidden_names
        ):
            violations.append(
                (
                    func.id,
                    node.lineno,
                )
            )

        if (
            isinstance(
                func,
                ast.Attribute,
            )
            and func.attr in forbidden_attributes
        ):
            violations.append(
                (
                    func.attr,
                    node.lineno,
                )
            )

    assert not violations


def test_presentation_layer_remains_available_to_dashboard() -> None:
    """Shared presentation foundation must exist and remain presentation-only."""

    assert PRESENTATION_PATH.is_file()

    source = PRESENTATION_PATH.read_text(encoding="utf-8")

    assert "def apply_institutional_css" in source

    assert "def render_disclaimer" in source

    forbidden = (
        "sqlite3",
        "pandas.read_",
        "read_csv(",
        "read_parquet(",
    )

    for token in forbidden:
        assert token not in source
