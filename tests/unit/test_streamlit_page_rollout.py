"""Structural tests for Phase 7C Streamlit page rollout."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

PAGES = [
    APP_DIR / "pages" / "1_Market_Overview.py",
    APP_DIR / "pages" / "2_Yield_Curve_Lab.py",
    APP_DIR / "pages" / "3_Monetary_Policy_Lab.py",
    APP_DIR / "pages" / "4_Islamic_vs_Conventional.py",
    APP_DIR / "pages" / "5_Fixed_Income_Risk.py",
    APP_DIR / "pages" / "6_Research.py",
]

EXPECTED_PAGE_TITLES = {
    "1_Market_Overview.py": "Market Overview",
    "2_Yield_Curve_Lab.py": "Yield Curve Lab",
    "3_Monetary_Policy_Lab.py": "Monetary Policy Lab",
    "4_Islamic_vs_Conventional.py": "Islamic vs Conventional",
    "5_Fixed_Income_Risk.py": "Fixed Income Risk",
    "6_Research.py": "Research",
}


def parse(path: Path) -> ast.Module:
    """Parse one Streamlit page."""

    return ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )


def imported_names(
    tree: ast.Module,
    module_name: str,
) -> set[str]:
    """Return names imported from one module."""

    names: set[str] = set()

    for node in ast.walk(tree):
        if (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module == module_name
        ):
            names.update(alias.name for alias in node.names)

    return names


def called_names(
    tree: ast.Module,
) -> list[str]:
    """Return direct function-call names."""

    names = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if isinstance(
            node.func,
            ast.Name,
        ):
            names.append(node.func.id)

    return names


def test_all_six_pages_use_shared_theme() -> None:
    """Every lab page must adopt the central theme."""

    for path in PAGES:
        tree = parse(path)

        imports = imported_names(
            tree,
            "styles.theme",
        )

        assert "apply_theme" in imports, path.name

        assert "apply_theme" in called_names(tree), path.name


def test_all_six_pages_use_shared_layout_components() -> None:
    """Every lab page must use the shared page-shell API."""

    required = {
        "render_terminal_bar",
        "render_page_header",
        "render_section_header",
        "render_placeholder",
        "render_data_caption",
    }

    for path in PAGES:
        tree = parse(path)

        imports = imported_names(
            tree,
            "components.layout",
        )

        assert required.issubset(imports), (
            path.name,
            required - imports,
        )

        calls = set(called_names(tree))

        assert required.issubset(calls), (
            path.name,
            required - calls,
        )


def test_each_page_keeps_single_page_config_call() -> None:
    """Streamlit page configuration must remain exactly once."""

    for path in PAGES:
        tree = parse(path)

        count = 0

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            function = node.func

            if (
                isinstance(
                    function,
                    ast.Attribute,
                )
                and isinstance(
                    function.value,
                    ast.Name,
                )
                and function.value.id == "st"
                and function.attr == "set_page_config"
            ):
                count += 1

        assert count == 1, (
            path.name,
            count,
        )


def test_rollout_pages_do_not_introduce_direct_data_or_plotting() -> None:
    """Presentation rollout must not invent analytical outputs."""

    forbidden_streamlit_calls = {
        "dataframe",
        "data_editor",
        "table",
        "metric",
        "plotly_chart",
    }

    for path in PAGES:
        tree = parse(path)

        observed = set()

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            function = node.func

            if (
                isinstance(
                    function,
                    ast.Attribute,
                )
                and isinstance(
                    function.value,
                    ast.Name,
                )
                and function.value.id == "st"
            ):
                observed.add(function.attr)

        assert not (observed & forbidden_streamlit_calls), (
            path.name,
            observed & forbidden_streamlit_calls,
        )


def test_page_titles_remain_semantically_correct() -> None:
    """Each page must retain its expected public title."""

    for path in PAGES:
        text = path.read_text(encoding="utf-8")

        assert EXPECTED_PAGE_TITLES[path.name] in text, path.name
