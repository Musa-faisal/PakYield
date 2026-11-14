"""Presentation contract for the Fixed-Income Risk page."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAGE_PATH = PROJECT_ROOT / "app" / "pages" / "5_Fixed_Income_Risk.py"

PAGE_TEXT = PAGE_PATH.read_text(encoding="utf-8")

TREE = ast.parse(
    PAGE_TEXT,
    filename=str(PAGE_PATH),
)


def named_calls(
    name: str,
) -> list[ast.Call]:
    """Return calls to a plain imported function."""

    return [
        node
        for node in ast.walk(TREE)
        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id == name
        )
    ]


def streamlit_calls(
    name: str,
) -> list[ast.Call]:
    """Return calls to st.<name>."""

    return [
        node
        for node in ast.walk(TREE)
        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Attribute,
            )
            and isinstance(
                node.func.value,
                ast.Name,
            )
            and node.func.value.id == "st"
            and node.func.attr == name
        )
    ]


def keyword_value(
    call: ast.Call,
    name: str,
) -> ast.expr | None:
    """Return one call keyword value."""

    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value

    return None


def test_fixed_income_uses_shared_presentation_foundation() -> None:
    """The page imports the required display-only helpers."""

    imports = set()

    for node in TREE.body:
        if (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module == "app.components.presentation"
        ):
            imports.update(alias.name for alias in node.names)

    assert {
        "apply_institutional_css",
        "render_disclaimer",
        "style_plotly_figure",
    }.issubset(imports)


def test_fixed_income_shell_order_and_disclaimer() -> None:
    """CSS follows page config and the disclaimer closes the page."""

    config_calls = streamlit_calls("set_page_config")

    css_calls = named_calls("apply_institutional_css")

    disclaimer_calls = named_calls("render_disclaimer")

    assert len(config_calls) == 1

    assert len(css_calls) == 1

    assert len(disclaimer_calls) == 1

    assert css_calls[0].lineno > config_calls[0].lineno

    assert PAGE_TEXT.rstrip().endswith("render_disclaimer()")


def test_fixed_income_uses_supported_width_contract() -> None:
    """All chart/table renders use stretch width without losing hide_index."""

    assert "use_container_width" not in PAGE_TEXT

    plot_calls = streamlit_calls("plotly_chart")

    dataframe_calls = streamlit_calls("dataframe")

    assert len(plot_calls) == 3

    assert len(dataframe_calls) == 1

    for call in plot_calls + dataframe_calls:
        width = keyword_value(
            call,
            "width",
        )

        assert isinstance(
            width,
            ast.Constant,
        )

        assert width.value == "stretch"

    hide_index = keyword_value(
        dataframe_calls[0],
        "hide_index",
    )

    assert isinstance(
        hide_index,
        ast.Constant,
    )

    assert hide_index.value is True


def test_fixed_income_centralizes_chart_styling() -> None:
    """Every existing Plotly figure receives shared presentation styling."""

    plot_calls = streamlit_calls("plotly_chart")

    style_calls = named_calls("style_plotly_figure")

    assert len(plot_calls) == 3

    assert len(style_calls) == 3

    plotted_arguments = [ast.unparse(call.args[0]) for call in plot_calls]

    styled_arguments = [ast.unparse(call.args[0]) for call in style_calls]

    assert sorted(plotted_arguments) == sorted(styled_arguments)


def test_fixed_income_page_keeps_data_access_boundary() -> None:
    """Presentation migration must not introduce direct persistence access."""

    forbidden = (
        "sqlite3",
        ".execute(",
        "SELECT ",
        "read_csv(",
        ".read_text(",
        ".read_bytes(",
        "open(",
    )

    for token in forbidden:
        assert token not in (PAGE_TEXT)
