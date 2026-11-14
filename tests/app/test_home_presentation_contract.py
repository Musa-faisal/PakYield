"""Presentation-contract tests for the PakYield Home surface."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PATH = PROJECT_ROOT / "app" / "Home.py"


def _source() -> str:
    return HOME_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source())


def _call_names() -> list[str]:
    names: list[str] = []

    for node in ast.walk(_tree()):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)

    return names


def test_home_uses_shared_presentation_contract() -> None:
    source = _source()
    calls = _call_names()

    assert "from app.components.presentation import" in source
    assert calls.count("apply_institutional_css") == 1
    assert calls.count("render_disclaimer") == 1


def test_home_uses_shared_section_and_methodology_surfaces() -> None:
    calls = _call_names()

    assert calls.count("render_section_header") == 2
    assert calls.count("render_methodology_note") == 1


def test_home_keeps_single_page_config_and_supported_width_api() -> None:
    source = _source()
    calls = _call_names()

    assert calls.count("set_page_config") == 1
    assert "use_container_width" not in source


def test_home_remains_presentation_only_and_data_safe() -> None:
    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "executemany",
        "read_csv",
        "read_excel",
        "read_json",
        "read_parquet",
        "read_sql",
        "read_sql_query",
    }

    observed: set[str] = set()

    for node in ast.walk(_tree()):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            observed.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            observed.add(node.func.attr)

    assert not (observed & forbidden_calls)

    source = _source()
    assert "sqlite3" not in source
    assert "pandas.read_" not in source
    assert "pd.read_" not in source


def test_home_uses_verified_market_data_and_research_boundary() -> None:
    source = _source()
    calls = _call_names()

    assert "from app.services import data" in source
    assert "latest_policy_context" in calls
    assert calls.count("latest_observed_yield") == 2
    assert "latest_term_spread" in calls
    assert "PresentationDataError" in source
    assert "historical research data, not live quotes" in source

    assert "research database is intentionally empty" not in source
    assert "Yield Curve Lab" in source
    assert "Monetary Policy Lab" in source
    assert "Islamic vs Conventional" in source
    assert "Fixed-Income Risk" in source
    assert "Research" in source
