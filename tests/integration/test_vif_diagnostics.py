"""Integration tests for the Phase 10 VIF implementation."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_vif_diagnostics.py"


def load_module() -> ModuleType:
    """Load the production VIF builder."""

    spec = importlib.util.spec_from_file_location(
        "build_vif_diagnostics",
        SCRIPT_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


VIF = load_module()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one test artifact."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    """Run VIF generation into isolated temporary outputs."""

    detail = tmp_path / "inferential_vif_diagnostics.csv"

    manifest = tmp_path / "inferential_vif_manifest.csv"

    monkeypatch.setattr(
        VIF,
        "OUTPUT_PATH",
        detail,
    )

    monkeypatch.setattr(
        VIF,
        "MANIFEST_OUTPUT_PATH",
        manifest,
    )

    VIF.main()

    assert detail.is_file()
    assert manifest.is_file()

    return detail, manifest


def test_vif_detail_census_and_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every applicable current regression has an actual VIF calculation."""

    detail, _ = run_builder(
        tmp_path,
        monkeypatch,
    )

    rows = read_csv(detail)

    assert len(rows) == 59

    assert Counter(row["family"] for row in rows) == {
        "yield_level_regime": 25,
        "yield_change_regime": 25,
        "term_spread_regime": 4,
        "cross_curve_regime": 5,
    }

    assert all(row["predictor_name"] == "regime_tightening_indicator" for row in rows)

    assert all(row["predictor_count"] == "1" for row in rows)

    assert all(
        math.isclose(
            float(row["vif"]),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-10,
        )
        for row in rows
    )

    assert all(row["diagnostic_status"] == "PASS" for row in rows)


def test_vif_samples_reconcile_to_inferential_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VIF sample sizes must match the exact inferential models."""

    detail, _ = run_builder(
        tmp_path,
        monkeypatch,
    )

    rows = read_csv(detail)

    inferential = {}

    for family, spec in VIF.INFERENTIAL_SPECS.items():
        with spec["path"].open(
            newline="",
            encoding="utf-8",
        ) as file:
            for row in csv.DictReader(file):
                inferential[
                    (
                        family,
                        row["test_id"],
                    )
                ] = row

    for row in rows:
        source = inferential[
            (
                row["family"],
                row["test_id"],
            )
        ]

        assert row["sample_n"] == source["sample_n"]

        assert row["n_easing"] == source["n_easing"]

        assert row["n_tightening"] == source["n_tightening"]

        assert int(row["n_easing"]) + int(row["n_tightening"]) == int(row["sample_n"])


def test_vif_manifest_marks_nonapplicable_families_explicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Intercept-only, t-test, and descriptive families are explicit N/A."""

    _, manifest = run_builder(
        tmp_path,
        monkeypatch,
    )

    rows = read_csv(manifest)

    assert len(rows) == 7

    by_family = {row["family"]: row for row in rows}

    for family in (
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
    ):
        assert by_family[family]["diagnostic_status"] == "PASS"

        assert by_family[family]["vif_applicability"] == (
            "APPLICABLE_TRIVIAL_SINGLE_PREDICTOR"
        )

        assert math.isclose(
            float(by_family[family]["max_vif"]),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-10,
        )

    assert by_family["cross_curve_zero"]["diagnostic_status"] == "NOT_APPLICABLE"

    assert "INTERCEPT_ONLY" in by_family["cross_curve_zero"]["reason"]

    assert by_family["mpc_event_window"]["diagnostic_status"] == "NOT_APPLICABLE"

    assert "ONE_SAMPLE_T_TEST" in by_family["mpc_event_window"]["reason"]

    assert by_family["monthly_cpi_yield"]["diagnostic_status"] == "NOT_APPLICABLE"

    assert "DESCRIPTIVE_ONLY" in by_family["monthly_cpi_yield"]["reason"]


def test_vif_threshold_and_model_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Current VIF evidence must correspond only to the one-regressor OLS models."""

    detail, manifest = run_builder(
        tmp_path,
        monkeypatch,
    )

    detail_rows = read_csv(detail)
    manifest_rows = read_csv(manifest)

    assert all(float(row["threshold"]) == 5.0 for row in detail_rows)

    assert all(row["test_method"] == "OLS_HAC_NEWEY_WEST" for row in detail_rows)

    assert all(
        row["diagnostic_note"]
        == ("SINGLE_NONCONSTANT_PREDICTOR_VIF_EQUALS_ONE_BY_CONSTRUCTION")
        for row in detail_rows
    )

    assert Counter(row["diagnostic_status"] for row in manifest_rows) == {
        "PASS": 4,
        "NOT_APPLICABLE": 3,
    }


def test_vif_outputs_are_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated VIF construction must be byte-identical."""

    detail, manifest = run_builder(
        tmp_path,
        monkeypatch,
    )

    first_detail = detail.read_bytes()

    first_manifest = manifest.read_bytes()

    VIF.main()

    second_detail = detail.read_bytes()

    second_manifest = manifest.read_bytes()

    assert first_detail == second_detail

    assert first_manifest == second_manifest

    assert (
        hashlib.sha256(first_detail).hexdigest()
        == hashlib.sha256(second_detail).hexdigest()
    )

    assert (
        hashlib.sha256(first_manifest).hexdigest()
        == hashlib.sha256(second_manifest).hexdigest()
    )
