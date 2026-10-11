"""Integration tests for deterministic Phase 6B inferential artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_inferential_analysis_tables.py"

MANIFEST_PATH = PROJECT_ROOT / "data" / "interim" / "inferential_analysis_manifest.csv"

EXPECTED = {
    "yield_level_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_yield_level_regime.csv"
        ),
        "rows": 25,
        "inferential": 25,
        "descriptive": 0,
        "sha": ("4c9ba3fdd6e920e905db3dc118e645ad904e2cbf0682c33d0c5228998790b1a4"),
        "method": "OLS_HAC_NEWEY_WEST",
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "yield_change_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_yield_change_regime.csv"
        ),
        "rows": 25,
        "inferential": 25,
        "descriptive": 0,
        "sha": ("4baf694f635fb183ef4072dde24b10924bd280241276940b83d19b2c3c2f9501"),
        "method": "OLS_HAC_NEWEY_WEST",
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "term_spread_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_term_spread_regime.csv"
        ),
        "rows": 4,
        "inferential": 4,
        "descriptive": 0,
        "sha": ("17f7222dda8f17e14830d64f268b076ac365e66012b4fdf6aa38527a835e1349"),
        "method": "OLS_HAC_NEWEY_WEST",
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "cross_curve_zero": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_zero.csv"
        ),
        "rows": 5,
        "inferential": 5,
        "descriptive": 0,
        "sha": ("14a906144b79f4a81dbe8b2df752a607600871bfc9de7e098e079b44e31f75de"),
        "method": ("INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST"),
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "cross_curve_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_regime.csv"
        ),
        "rows": 5,
        "inferential": 5,
        "descriptive": 0,
        "sha": ("f3cca17f6cf658828a9ac613d7fdf7764126e9da0a74760749a9109a8717a6a5"),
        "method": "OLS_HAC_NEWEY_WEST",
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "mpc_event_window": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_mpc_event_windows.csv"
        ),
        "rows": 72,
        "inferential": 54,
        "descriptive": 18,
        "sha": ("13673445d98051044a1fe5b019d712fadf6b4b544dde2c6cc64a8ca48441f2f1"),
        "method": ("ONE_SAMPLE_T_TEST_IF_N_GE_5"),
        "multiple_testing": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
    },
    "monthly_cpi_yield": {
        "path": (PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv"),
        "rows": 1234,
        "inferential": 0,
        "descriptive": 1234,
        "sha": ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
        "method": ("DESCRIPTIVE_ONLY_IN_PHASE_6B"),
        "multiple_testing": ("NOT_APPLICABLE"),
    },
}

EXPECTED_MANIFEST_SHA = (
    "ec0dea0f785cb0a4f6a9ca5db684da21805701746c4160bb694bd739ab56bc10"
)


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 for one file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read CSV rows."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def test_all_frozen_inferential_artifacts_match_hashes_and_rows() -> None:
    """All seven Phase 6B family artifacts remain frozen."""

    for family, spec in EXPECTED.items():
        path = spec["path"]

        assert path.is_file(), family

        rows = read_csv(path)

        assert len(rows) == spec["rows"], family

        assert sha256_file(path) == spec["sha"], family

    assert MANIFEST_PATH.is_file()

    assert sha256_file(MANIFEST_PATH) == EXPECTED_MANIFEST_SHA


def test_inferential_manifest_exact_family_contract() -> None:
    """Manifest metadata must match the frozen seven-family contract."""

    rows = read_csv(MANIFEST_PATH)

    assert len(rows) == 7

    by_family = {row["family"]: row for row in rows}

    assert set(by_family) == set(EXPECTED)

    for family, spec in EXPECTED.items():
        row = by_family[family]

        expected_relative_path = spec["path"].relative_to(PROJECT_ROOT).as_posix()

        assert row["artifact_path"] == expected_relative_path

        assert int(row["row_count"]) == spec["rows"]

        assert int(row["inferential_test_count"]) == spec["inferential"]

        assert int(row["descriptive_only_count"]) == spec["descriptive"]

        assert row["sha256"] == spec["sha"]

        assert row["method"] == spec["method"]

        assert row["multiple_testing_rule"] == spec["multiple_testing"]


def test_frozen_inferential_and_descriptive_census() -> None:
    """The Phase 6B inferential/descriptive census remains exact."""

    inferential_total = sum(int(spec["inferential"]) for spec in EXPECTED.values())

    descriptive_total = sum(int(spec["descriptive"]) for spec in EXPECTED.values())

    assert inferential_total == 118

    assert descriptive_total == 1252

    assert EXPECTED["mpc_event_window"]["inferential"] == 54

    assert EXPECTED["mpc_event_window"]["descriptive"] == 18

    assert EXPECTED["monthly_cpi_yield"]["inferential"] == 0

    assert EXPECTED["monthly_cpi_yield"]["descriptive"] == 1234


def test_multiple_testing_and_method_boundaries_are_explicit() -> None:
    """Family-level methods and correction boundaries remain explicit."""

    manifest = {row["family"]: row for row in read_csv(MANIFEST_PATH)}

    inferential_families = {
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_zero",
        "cross_curve_regime",
        "mpc_event_window",
    }

    for family in inferential_families:
        assert manifest[family]["multiple_testing_rule"] == (
            "BENJAMINI_HOCHBERG_WITHIN_FAMILY"
        )

    assert manifest["monthly_cpi_yield"]["multiple_testing_rule"] == "NOT_APPLICABLE"

    assert manifest["monthly_cpi_yield"]["method"] == ("DESCRIPTIVE_ONLY_IN_PHASE_6B")

    assert manifest["cross_curve_zero"]["method"] == (
        "INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST"
    )

    assert manifest["mpc_event_window"]["method"] == ("ONE_SAMPLE_T_TEST_IF_N_GE_5")


def test_inferential_builder_regeneration_is_byte_deterministic() -> None:
    """A production rebuild must reproduce every frozen byte exactly."""

    before = {family: sha256_file(spec["path"]) for family, spec in EXPECTED.items()}

    before_manifest = sha256_file(MANIFEST_PATH)

    subprocess.run(
        [
            sys.executable,
            str(BUILDER_PATH),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    after = {family: sha256_file(spec["path"]) for family, spec in EXPECTED.items()}

    after_manifest = sha256_file(MANIFEST_PATH)

    assert before == after

    assert before_manifest == after_manifest

    for family, spec in EXPECTED.items():
        assert after[family] == spec["sha"]

    assert after_manifest == EXPECTED_MANIFEST_SHA
