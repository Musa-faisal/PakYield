"""Integration tests for final Phase 10 gap closure."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

from pakyield.config import PROJECT_ROOT

INTERIM = PROJECT_ROOT / "data" / "interim"

BUILDER = PROJECT_ROOT / "scripts" / "build_phase10_gap_closure.py"

AUDITOR = PROJECT_ROOT / "scripts" / "audit_phase10_gap_closure.py"

DESCRIPTIVE = (
    INTERIM / "phase10_descriptive_yield_levels.csv",
    INTERIM / "phase10_descriptive_yield_changes.csv",
    INTERIM / "phase10_descriptive_term_spreads.csv",
    INTERIM / "phase10_descriptive_cross_curve_differences.csv",
    INTERIM / "phase10_descriptive_mpc_event_windows.csv",
)

GENERATED = (
    *DESCRIPTIVE,
    INTERIM / "phase10_correlation_diagnostics.csv",
    INTERIM / "phase10_adf_stationarity.csv",
    INTERIM / "phase10_regression_residual_diagnostics.csv",
    INTERIM / "phase10_regression_residual_qq.csv",
    INTERIM / "phase10_gap_closure_manifest.csv",
)


def read_csv(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def sha(
    path: Path,
) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase10_builder_is_byte_deterministic() -> None:
    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )

    first = {path: sha(path) for path in GENERATED}

    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )

    second = {path: sha(path) for path in GENERATED}

    assert first == second


def test_descriptive_percentiles_are_present() -> None:
    for path in DESCRIPTIVE:
        headers, rows = read_csv(path)

        assert "percentile_25" in headers

        assert "percentile_75" in headers

        positive = [
            row
            for row in rows
            if row.get("sample_n", "") and int(float(row["sample_n"])) > 0
        ]

        assert all(row["percentile_25"] and row["percentile_75"] for row in positive)


def test_correlation_and_adf_are_executable() -> None:
    _, correlations = read_csv(INTERIM / "phase10_correlation_diagnostics.csv")

    assert any(
        row["analysis_status"] == "ELIGIBLE"
        and row["pearson_r"]
        and row["spearman_rho"]
        for row in correlations
    )

    _, adf = read_csv(INTERIM / "phase10_adf_stationarity.csv")

    assert any(
        row["analysis_status"] == "ELIGIBLE" and row["adf_statistic"] and row["p_value"]
        for row in adf
    )


def test_regression_residual_diagnostics_are_complete() -> None:
    _, residual = read_csv(INTERIM / "phase10_regression_residual_diagnostics.csv")

    eligible = [row for row in residual if row["analysis_status"] == "ELIGIBLE"]

    assert eligible

    for field in (
        "durbin_watson",
        "breusch_pagan_lm_p_value",
        "autocorrelation_lag1",
        "ljung_box_p_value",
    ):
        assert all(row[field] for row in eligible)

    _, qq = read_csv(INTERIM / "phase10_regression_residual_qq.csv")

    assert qq

    assert all(
        row["theoretical_normal_quantile"] and row["ordered_residual"] for row in qq
    )


def test_phase10_final_auditor_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(AUDITOR),
        ],
        check=True,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    assert "GENUINELY_MISSING:\n  NONE" in result.stdout

    assert "PASS: PHASE 10 GAP AUDIT HAS ZERO OPEN ITEMS" in result.stdout
