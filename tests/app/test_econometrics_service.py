"""Phase 13C verification for research presentation services."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services import econometrics


def test_inferential_manifest_is_exact() -> None:
    rows = econometrics.load_inferential_manifest()

    assert len(rows) == 7

    assert {row["family"] for row in rows} == set(econometrics.INFERENTIAL_FAMILIES)


def test_diagnostic_datasets_are_verified() -> None:
    assert len(econometrics.load_correlation_diagnostics()) == 68

    assert len(econometrics.load_adf_diagnostics()) == 59

    assert len(econometrics.load_vif_diagnostics()) == 59

    assert len(econometrics.load_residual_diagnostics()) == 59

    assert len(econometrics.load_artifact("vif_manifest")) == 7


def test_regression_table_preserves_audited_results() -> None:
    rows = econometrics.regression_table("yield_level_regime")

    assert len(rows) == 25

    assert all(
        "test_id" in row and "analysis_status" in row and "p_value_bh" in row
        for row in rows
    )


def test_macro_series_preserves_monthly_grain() -> None:
    rows = econometrics.load_macro_monthly_series(
        "PKRV",
        "1Y",
    )

    assert rows

    periods = [row["period"] for row in rows]

    assert periods == sorted(periods)

    assert len(periods) == len(set(periods))

    assert all(
        row["curve_type"] == "PKRV"
        and row["tenor"] == "1Y"
        and row["month_end_yield_pct"]
        and row["cpi_inflation_yoy_pct"]
        for row in rows
    )


def test_fail_closed_integrity_and_unknown_families(
    tmp_path: Path,
) -> None:
    bad_file = tmp_path / "altered.csv"

    bad_file.write_text(
        "value\n999\n",
        encoding="utf-8",
    )

    with pytest.raises(
        econometrics.EconometricsDataError,
        match="SHA mismatch",
    ):
        econometrics.read_verified(
            bad_file,
            "0" * 64,
            1,
        )

    with pytest.raises(KeyError):
        econometrics.regression_table("fabricated_model")

    with pytest.raises(KeyError):
        econometrics.load_artifact("unknown_artifact")
