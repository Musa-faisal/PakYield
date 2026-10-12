"""Contract tests for the PakYield Streamlit presentation shell."""

from __future__ import annotations

import ast
from pathlib import Path

from app.services import data

from app import streamlit_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_PATH = PROJECT_ROOT / "app" / "streamlit_app.py"


def test_streamlit_app_imports_and_exposes_main() -> None:
    """Presentation application must import without executing itself."""

    assert callable(streamlit_app.main)

    assert streamlit_app.APP_TITLE == "PakYield Lab"


def test_streamlit_app_uses_service_layer_not_direct_csv_access() -> None:
    """UI must consume the 7C service instead of reading artifacts directly."""

    source = APP_PATH.read_text(encoding="utf-8")

    tree = ast.parse(source)

    direct_csv_calls = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if isinstance(
            node.func,
            ast.Attribute,
        ):
            if node.func.attr == "open":
                direct_csv_calls.append(node)

        if isinstance(
            node.func,
            ast.Name,
        ):
            if node.func.id in {
                "open",
                "DictReader",
                "reader",
            }:
                direct_csv_calls.append(node)

    assert not direct_csv_calls

    assert "from app.services import data" in source

    assert "data/interim" not in source


def test_market_overview_service_selectors_return_values() -> None:
    """Headline dashboard selectors must resolve frozen observations."""

    policy = data.latest_policy_context()

    one_year = data.latest_observed_yield(
        "PKRV",
        "1Y",
    )

    ten_year = data.latest_observed_yield(
        "PKRV",
        "10Y",
    )

    spread = data.latest_term_spread("10Y-2Y")

    assert policy is not None
    assert one_year is not None
    assert ten_year is not None
    assert spread is not None

    assert policy["policy_rate_pct"]

    assert one_year["yield_pct"]

    assert ten_year["yield_pct"]

    assert spread["term_spread_bps"]


def test_latest_curve_snapshots_are_available_for_both_curves() -> None:
    """Both frozen curve families must be present for presentation."""

    pkrv = data.latest_curve_snapshot("PKRV")

    pkisrv = data.latest_curve_snapshot("PKISRV")

    assert pkrv
    assert pkisrv

    assert all(row["curve_type"] == "PKRV" for row in pkrv)

    assert all(row["curve_type"] == "PKISRV" for row in pkisrv)


def test_manifest_preserves_five_analysis_families() -> None:
    """Dashboard inventory must remain aligned with frozen manifest."""

    manifest = data.load_analysis_manifest()

    assert [row["analysis_family"] for row in manifest] == [
        "yield_level_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
        "mpc_event_study",
        "monthly_cpi_yield",
    ]
