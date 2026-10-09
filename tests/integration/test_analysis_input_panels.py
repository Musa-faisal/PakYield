"""Integration tests for deterministic D095 analysis-input panels."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_analysis_input_panels.py"

EXPECTED_HASHES = {
    "yield": ("f8583955e1f30953b13d7a054c2df4e146063c7fcfcabe205fd9cc9b42158a30"),
    "term": ("d9fd6633941ab2d8932200ba45ac2e8e2619c1d77cbe30e751458d75e75311dd"),
    "cross": ("2a286e2847081c6df654b6e13e71e3e07ce2e5249a4a2cef61f7e6fd5400c384"),
    "manifest": ("ec0fe1e6c43f2dfbf246e8120a777720858b82498beb741f08d11cdb8df17aa4"),
}

EXPECTED_YIELD_LEVEL_STATUS = {
    "INELIGIBLE": 2073,
    "ELIGIBLE": 22742,
}

EXPECTED_YIELD_CHANGE_STATUS = {
    "INELIGIBLE": 2078,
    "ELIGIBLE": 22737,
}

EXPECTED_YIELD_CHANGE_REASONS = {
    "NO_PREVIOUS_YIELD_OBSERVATION_AND_REGIME_INELIGIBLE": 20,
    "REGIME_INELIGIBLE": 2053,
    "NO_PREVIOUS_YIELD_OBSERVATION": 5,
}

EXPECTED_TERM_STATUS = {
    "INELIGIBLE": 432,
    "ELIGIBLE": 4164,
}

EXPECTED_TERM_REASONS = {
    "REGIME_INELIGIBLE": 402,
    "TERM_SPREAD_INELIGIBLE": 28,
    "TERM_SPREAD_AND_REGIME_INELIGIBLE": 2,
}

EXPECTED_TERM_ELIGIBLE_BY_REGIME = {
    ("10Y-1Y", "EASING"): 447,
    ("10Y-1Y", "TIGHTENING"): 601,
    ("10Y-2Y", "EASING"): 447,
    ("10Y-2Y", "TIGHTENING"): 601,
    ("3Y-3M", "EASING"): 447,
    ("3Y-3M", "TIGHTENING"): 573,
    ("5Y-1Y", "EASING"): 447,
    ("5Y-1Y", "TIGHTENING"): 601,
}

EXPECTED_CROSS_STATUS = {
    "ELIGIBLE": 1940,
    "INELIGIBLE": 95,
}

EXPECTED_CROSS_REASONS = {
    "CROSS_CURVE_PAIR_INELIGIBLE": 30,
    "REGIME_INELIGIBLE": 65,
}


def load_builder_module() -> ModuleType:
    """Load the production D095 analysis-input builder."""

    spec = importlib.util.spec_from_file_location(
        "build_analysis_input_panels",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one CSV artifact."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def configure_and_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """Generate all four D095 outputs in an isolated directory."""

    paths = {
        "yield": (tmp_path / "yield_regime_analysis_panel.csv"),
        "term": (tmp_path / "term_spread_regime_analysis_panel.csv"),
        "cross": (tmp_path / "cross_curve_regime_analysis_panel.csv"),
        "manifest": (tmp_path / "analysis_input_manifest.csv"),
    }

    monkeypatch.setattr(
        BUILDER,
        "YIELD_OUTPUT",
        paths["yield"],
    )

    monkeypatch.setattr(
        BUILDER,
        "TERM_OUTPUT",
        paths["term"],
    )

    monkeypatch.setattr(
        BUILDER,
        "CROSS_OUTPUT",
        paths["cross"],
    )

    monkeypatch.setattr(
        BUILDER,
        "MANIFEST_OUTPUT",
        paths["manifest"],
    )

    monkeypatch.setattr(
        BUILDER,
        "display_path",
        lambda path: Path("data") / "interim" / path.name,
    )

    BUILDER.main()

    for path in paths.values():
        assert path.is_file()

    return paths


def test_analysis_outputs_match_frozen_hashes_and_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All reconstructed outputs must match frozen production bytes."""

    paths = configure_and_run(
        tmp_path,
        monkeypatch,
    )

    expected_rows = {
        "yield": 24815,
        "term": 4596,
        "cross": 2035,
        "manifest": 5,
    }

    for name, path in paths.items():
        rows = read_csv(path)

        assert len(rows) == (expected_rows[name])

        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()

        assert actual_sha == (EXPECTED_HASHES[name])

    yield_rows = read_csv(paths["yield"])

    term_rows = read_csv(paths["term"])

    cross_rows = read_csv(paths["cross"])

    assert (
        len(
            {
                (
                    row["observation_date"],
                    row["curve_type"],
                    row["tenor"],
                )
                for row in yield_rows
            }
        )
        == 24815
    )

    assert (
        len(
            {
                (
                    row["observation_date"],
                    row["curve_type"],
                    row["spread_name"],
                )
                for row in term_rows
            }
        )
        == 4596
    )

    assert (
        len(
            {
                (
                    row["observation_date"],
                    row["tenor"],
                )
                for row in cross_rows
            }
        )
        == 2035
    )


def test_yield_level_and_change_eligibility_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Yield level/change eligibility must remain variable-specific."""

    paths = configure_and_run(
        tmp_path,
        monkeypatch,
    )

    rows = read_csv(paths["yield"])

    assert (
        Counter(row["yield_level_regime_analysis_status"] for row in rows)
        == EXPECTED_YIELD_LEVEL_STATUS
    )

    assert (
        Counter(row["yield_change_regime_analysis_status"] for row in rows)
        == EXPECTED_YIELD_CHANGE_STATUS
    )

    assert (
        Counter(
            row["yield_change_regime_ineligibility_reason"]
            for row in rows
            if row["yield_change_regime_analysis_status"] == "INELIGIBLE"
        )
        == EXPECTED_YIELD_CHANGE_REASONS
    )

    for row in rows:
        assert row["policy_rate_pct"]

        assert row["regime_label"]

        if row["yield_change_regime_analysis_status"] == "ELIGIBLE":
            assert row["yield_change_bps"]

            assert row["regime_analysis_status"] == "ELIGIBLE"


def test_term_spread_joint_eligibility_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Term-spread and regime eligibility must both hold."""

    paths = configure_and_run(
        tmp_path,
        monkeypatch,
    )

    rows = read_csv(paths["term"])

    assert Counter(row["joint_analysis_status"] for row in rows) == EXPECTED_TERM_STATUS

    assert (
        Counter(
            row["joint_ineligibility_reason"]
            for row in rows
            if row["joint_analysis_status"] == "INELIGIBLE"
        )
        == EXPECTED_TERM_REASONS
    )

    eligible = [row for row in rows if row["joint_analysis_status"] == "ELIGIBLE"]

    assert (
        Counter(
            (
                row["spread_name"],
                row["regime_label"],
            )
            for row in eligible
        )
        == EXPECTED_TERM_ELIGIBLE_BY_REGIME
    )

    for row in eligible:
        assert row["eligibility_status"] == "ELIGIBLE"

        assert row["regime_analysis_status"] == "ELIGIBLE"

        assert row["term_spread_bps"]


def test_cross_curve_and_manifest_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cross-curve eligibility and grain manifest remain frozen."""

    paths = configure_and_run(
        tmp_path,
        monkeypatch,
    )

    cross_rows = read_csv(paths["cross"])

    manifest_rows = read_csv(paths["manifest"])

    assert (
        Counter(row["paired_comparison_status"] for row in cross_rows)
        == EXPECTED_CROSS_STATUS
    )

    assert (
        Counter(
            row["paired_comparison_ineligibility_reason"]
            for row in cross_rows
            if row["paired_comparison_status"] == "INELIGIBLE"
        )
        == EXPECTED_CROSS_REASONS
    )

    for row in cross_rows:
        if row["paired_comparison_status"] == "ELIGIBLE":
            assert row["pkrv_yield_pct"]

            assert row["pkisrv_yield_pct"]

            assert row["pkisrv_minus_pkrv_bps"]

            assert row["regime_analysis_status"] == "ELIGIBLE"

    assert [row["analysis_family"] for row in manifest_rows] == [
        "yield_level_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
        "mpc_event_study",
        "monthly_cpi_yield",
    ]

    assert {row["analysis_family"]: int(row["row_count"]) for row in manifest_rows} == {
        "yield_level_change_regime": 24815,
        "term_spread_regime": 4596,
        "cross_curve_regime": 2035,
        "mpc_event_study": 936,
        "monthly_cpi_yield": 1234,
    }

    manifest_by_family = {row["analysis_family"]: row for row in manifest_rows}

    assert manifest_by_family["mpc_event_study"]["regime_join_rule"] == "NOT_JOINED"

    assert manifest_by_family["monthly_cpi_yield"]["regime_join_rule"] == (
        "NOT_JOINED_PENDING_MONTHLY_ANCHOR_CONTRACT"
    )


def test_source_preservation_exact_joins_and_determinism(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Source fields, exact joins, and reconstructed bytes remain stable."""

    paths = configure_and_run(
        tmp_path,
        monkeypatch,
    )

    first_bytes = {name: path.read_bytes() for name, path in paths.items()}

    yield_rows = read_csv(paths["yield"])

    term_rows = read_csv(paths["term"])

    cross_rows = read_csv(paths["cross"])

    source_yield = read_csv(BUILDER.INPUTS["yield_changes"]["path"])

    source_term = read_csv(BUILDER.INPUTS["term_spreads"]["path"])

    source_cross = read_csv(BUILDER.INPUTS["cross_curve"]["path"])

    regime_rows = read_csv(BUILDER.INPUTS["regimes"]["path"])

    policy_rows = read_csv(BUILDER.INPUTS["policy_daily"]["path"])

    assert len(source_yield) == len(yield_rows)

    assert len(source_term) == len(term_rows)

    assert len(source_cross) == len(cross_rows)

    for source, derived in zip(
        source_yield,
        yield_rows,
        strict=True,
    ):
        assert {
            field: derived[field] for field in (BUILDER.YIELD_SOURCE_FIELDS)
        } == source

    for source, derived in zip(
        source_term,
        term_rows,
        strict=True,
    ):
        assert {
            field: derived[field] for field in (BUILDER.TERM_SOURCE_FIELDS)
        } == source

    for source, derived in zip(
        source_cross,
        cross_rows,
        strict=True,
    ):
        assert {
            field: derived[field] for field in (BUILDER.CROSS_SOURCE_FIELDS)
        } == source

    regime_by_curve_date = {
        (
            row["observation_date"],
            row["curve_type"],
        ): row
        for row in regime_rows
    }

    policy_by_date = {row["date"]: row for row in policy_rows}

    regime_by_date = {}

    for row in regime_rows:
        observation_date = row["observation_date"]

        existing = regime_by_date.get(observation_date)

        if existing is None:
            regime_by_date[observation_date] = row

        else:
            assert existing["regime_label"] == row["regime_label"]

            assert existing["regime_analysis_status"] == row["regime_analysis_status"]

            assert existing["ineligibility_reason"] == row["ineligibility_reason"]

    for row in yield_rows:
        regime = regime_by_curve_date[
            (
                row["observation_date"],
                row["curve_type"],
            )
        ]

        policy = policy_by_date[row["observation_date"]]

        assert row["regime_label"] == regime["regime_label"]

        assert row["regime_analysis_status"] == regime["regime_analysis_status"]

        assert row["policy_rate_pct"] == policy["policy_rate_pct"]

    for row in term_rows:
        regime = regime_by_curve_date[
            (
                row["observation_date"],
                row["curve_type"],
            )
        ]

        policy = policy_by_date[row["observation_date"]]

        assert row["regime_label"] == regime["regime_label"]

        assert row["policy_rate_pct"] == policy["policy_rate_pct"]

    for row in cross_rows:
        regime = regime_by_date[row["observation_date"]]

        policy = policy_by_date[row["observation_date"]]

        assert row["regime_label"] == regime["regime_label"]

        assert row["policy_rate_pct"] == policy["policy_rate_pct"]

    BUILDER.main()

    second_bytes = {name: path.read_bytes() for name, path in paths.items()}

    assert first_bytes == second_bytes

    for name, data in second_bytes.items():
        assert hashlib.sha256(data).hexdigest() == (EXPECTED_HASHES[name])
