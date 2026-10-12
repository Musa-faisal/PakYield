"""Integration tests for Phase 6C inferential diagnostics."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_inferential_diagnostics.py"

MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "interim" / "inferential_diagnostics_manifest.csv"
)

EXPECTED_SHA256 = "e059f18c249746136c02b20c593504408df4e873eca2b888209add7465473420"

EXPECTED_FAMILIES = {
    "yield_level_regime",
    "yield_change_regime",
    "term_spread_regime",
    "cross_curve_zero",
    "cross_curve_regime",
    "mpc_event_window",
    "monthly_cpi_yield",
}

EXPECTED_REJECTIONS = {
    "yield_level_regime": (24, 1),
    "yield_change_regime": (10, 15),
    "term_spread_regime": (4, 0),
    "cross_curve_zero": (5, 0),
    "cross_curve_regime": (4, 1),
    "mpc_event_window": (0, 54),
    "monthly_cpi_yield": (0, 0),
}


def read_manifest() -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read the Phase 6C diagnostic manifest."""

    with MANIFEST_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def find_field(
    headers: list[str],
    candidates: tuple[str, ...],
) -> str:
    """Resolve one compatible manifest field."""

    for candidate in candidates:
        if candidate in headers:
            return candidate

    raise AssertionError(
        f"Could not locate field from candidates: {candidates}; headers={headers}"
    )


def test_diagnostic_source_uses_canonical_inferential_fields() -> None:
    """The repaired 6C audit must use the canonical inference fields."""

    source = SCRIPT_PATH.read_text(encoding="utf-8")

    required = {
        "sample_n",
        "p_value_raw",
        "p_value_bh",
        "reject_bh_0_05",
    }

    for field in required:
        assert field in source

    assert "reject_bh_0_05" in source


def test_diagnostic_manifest_matches_frozen_bytes() -> None:
    """Production diagnostic manifest must retain exact frozen bytes."""

    assert MANIFEST_PATH.is_file()

    actual = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()

    assert actual == EXPECTED_SHA256

    _, rows = read_manifest()

    assert len(rows) == 7


def test_diagnostic_manifest_family_universe_is_exact() -> None:
    """Exactly seven frozen analysis families must be represented."""

    headers, rows = read_manifest()

    family_field = find_field(
        headers,
        (
            "analysis_family",
            "family",
            "test_family",
        ),
    )

    families = {row[family_field] for row in rows}

    assert families == EXPECTED_FAMILIES

    assert len(families) == 7


def test_bh_rejection_census_matches_frozen_diagnostics() -> None:
    """Stored family rejection counts must match the validated 6C audit."""

    headers, rows = read_manifest()

    family_field = find_field(
        headers,
        (
            "analysis_family",
            "family",
            "test_family",
        ),
    )

    reject_field = find_field(
        headers,
        (
            "reject_count",
            "bh_reject_count",
        ),
    )

    do_not_reject_field = find_field(
        headers,
        (
            "do_not_reject_count",
            "bh_do_not_reject_count",
        ),
    )

    observed = {
        row[family_field]: (
            int(row[reject_field]),
            int(row[do_not_reject_field]),
        )
        for row in rows
    }

    assert observed == EXPECTED_REJECTIONS

    assert sum(pair[0] for pair in observed.values()) == 47

    assert sum(pair[1] for pair in observed.values()) == 71


def test_diagnostic_regeneration_is_byte_deterministic(
    tmp_path: Path,
) -> None:
    """Re-running the production audit must reproduce the exact manifest."""

    del tmp_path

    first = MANIFEST_PATH.read_bytes()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    assert "PASS: Phase 6C inferential diagnostics contract satisfied" in result.stdout

    second = MANIFEST_PATH.read_bytes()

    assert first == second

    assert hashlib.sha256(second).hexdigest() == EXPECTED_SHA256
