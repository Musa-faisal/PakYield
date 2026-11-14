"""Phase 13D Research / Econometrics presentation contract."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PAGE = ROOT / "app" / "pages" / "6_Research.py"

COMPONENT = ROOT / "app" / "components" / "research.py"


def parse(path: Path) -> ast.Module:
    """Parse source without executing Streamlit."""

    return ast.parse(path.read_text(encoding="utf-8"))


def names_called(
    tree: ast.Module,
) -> set[str]:
    """Collect directly named function calls."""

    return {
        node.func.id
        for node in ast.walk(tree)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name))
    }


def test_research_page_uses_shared_shell() -> None:
    """Research retains all required shared page components."""

    tree = parse(PAGE)

    calls = names_called(tree)

    assert {
        "apply_theme",
        "render_terminal_bar",
        "render_page_header",
        "render_section_header",
        "render_placeholder",
        "render_data_caption",
        "render_research_workspace",
    }.issubset(calls)

    page_configuration_calls = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "set_page_config"
        )
    ]

    assert len(page_configuration_calls) == 1


def test_research_page_contains_no_direct_data_rendering() -> None:
    """The page does not bypass the shared UI architecture."""

    tree = parse(PAGE)

    prohibited = {
        "dataframe",
        "data_editor",
        "table",
        "metric",
        "plotly_chart",
    }

    direct_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
        )
    }

    assert not (direct_calls & prohibited)


def test_research_component_uses_verified_service_api() -> None:
    """Research UI is backed by actual service methods."""

    tree = parse(COMPONENT)

    service_methods = {
        node.attr
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "service"
        )
    }

    assert {
        "load_inferential_manifest",
        "regression_table",
        "load_correlation_diagnostics",
        "correlation_table",
        "load_adf_diagnostics",
        "load_vif_diagnostics",
        "load_residual_diagnostics",
        "load_macro_monthly_series",
        "load_artifact",
    }.issubset(service_methods)


def test_research_interface_does_not_estimate_models() -> None:
    """The presentation layer must not perform inference."""

    source = COMPONENT.read_text(encoding="utf-8")

    prohibited = (
        "statsmodels",
        "scipy.stats",
        "numpy.linalg",
        ".fit(",
        ".corr(",
        "pearsonr(",
        "linregress(",
        "OLS(",
    )

    for token in prohibited:
        assert token not in source

    assert "read_verified" not in source
    assert "csv.DictReader" not in source
    assert "_load_verified" in source
    assert "connectgaps=False" in source


def test_research_uses_supported_streamlit_width_api() -> None:
    """Research renderers use the supported Streamlit width argument."""
    tree = parse(COMPONENT)
    renderers = {
        "dataframe",
        "plotly_chart",
    }
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
        and node.func.attr in renderers
    ]

    assert len(calls) == 2

    for node in calls:
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        assert "use_container_width" not in keywords
        width = keywords.get("width")
        assert isinstance(width, ast.Constant)
        assert width.value == "stretch"
