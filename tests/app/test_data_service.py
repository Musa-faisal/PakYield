"""Tests for PakYield's read-only presentation data service."""

from __future__ import annotations

from collections import Counter

from app.services import data


def test_frozen_presentation_artifacts_load_exactly() -> None:
    """Every presentation family must satisfy its frozen contract."""

    expected = {
        "yield": 24815,
        "term_spread": 4596,
        "cross_curve": 2035,
        "mpc_event": 936,
        "monthly_cpi": 1234,
        "manifest": 5,
    }

    for family, row_count in expected.items():
        assert len(data.load_rows(family)) == row_count


def test_latest_curve_snapshot_is_observed_only() -> None:
    """Latest snapshots must be real source rows with unique tenors."""

    pkrv = data.latest_curve_snapshot("PKRV")

    pkisrv = data.latest_curve_snapshot("PKISRV")

    assert pkrv
    assert pkisrv

    for snapshot in (
        pkrv,
        pkisrv,
    ):
        dates = {row["observation_date"] for row in snapshot}

        tenors = [row["tenor"] for row in snapshot]

        assert len(dates) == 1
        assert len(tenors) == len(set(tenors))

        assert all(
            row["yield_level_regime_analysis_status"] == "ELIGIBLE" for row in snapshot
        )


def test_latest_market_selectors_return_real_rows() -> None:
    """Market headline selectors must return frozen observations."""

    one_year = data.latest_observed_yield(
        "PKRV",
        "1Y",
    )

    ten_year = data.latest_observed_yield(
        "PKRV",
        "10Y",
    )

    slope = data.latest_term_spread("10Y-2Y")

    policy = data.latest_policy_context()

    assert one_year is not None
    assert ten_year is not None
    assert slope is not None
    assert policy is not None

    assert one_year["yield_pct"]
    assert ten_year["yield_pct"]
    assert slope["term_spread_bps"]
    assert policy["policy_rate_pct"]

    assert slope["joint_analysis_status"] == "ELIGIBLE"


def test_frozen_eligibility_filters_are_preserved() -> None:
    """Service filters must use frozen source eligibility only."""

    event_rows = data.eligible_event_windows()

    cross_rows = data.eligible_cross_curve_rows()

    assert len(event_rows) == 688
    assert len(cross_rows) == 1940

    assert Counter(row["eligibility_status"] for row in event_rows) == {
        "ELIGIBLE": 688,
    }

    assert Counter(row["paired_comparison_status"] for row in cross_rows) == {
        "ELIGIBLE": 1940,
    }


def test_analysis_manifest_remains_five_separate_grains() -> None:
    """Presentation service must preserve the five analysis families."""

    rows = data.load_analysis_manifest()

    assert [row["analysis_family"] for row in rows] == [
        "yield_level_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
        "mpc_event_study",
        "monthly_cpi_yield",
    ]

    manifest = {row["analysis_family"]: row for row in rows}

    assert manifest["mpc_event_study"]["regime_join_rule"] == "NOT_JOINED"

    assert manifest["monthly_cpi_yield"]["regime_join_rule"] == (
        "NOT_JOINED_PENDING_MONTHLY_ANCHOR_CONTRACT"
    )
