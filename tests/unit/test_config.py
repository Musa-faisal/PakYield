"""Unit tests for PakYield's central research configuration."""

from __future__ import annotations

from datetime import date

from pakyield.config import (
    BASIS_POINTS_PER_PERCENTAGE_POINT,
    MACRO_SAMPLE_START,
    MPC_EVENT_HALF_WINDOWS,
    MPC_EVENT_TYPES,
    PKRV_CANONICAL_TENORS,
    PKRV_FOCAL_TENORS,
    PKRV_PKISRV_COMMON_TENORS,
    PKRV_PKISRV_SAMPLE_START,
    PKRV_SAMPLE_START,
    TENOR_TO_YEARS,
    TERM_SPREADS,
    validate_project_structure,
)


def test_canonical_tenor_mapping_is_complete() -> None:
    """Every canonical PKRV tenor must have one numeric maturity coordinate."""

    assert set(TENOR_TO_YEARS) == set(PKRV_CANONICAL_TENORS)
    assert len(TENOR_TO_YEARS) == 20


def test_focal_tenors_are_canonical() -> None:
    """Every focal research tenor must belong to the canonical universe."""

    assert set(PKRV_FOCAL_TENORS).issubset(PKRV_CANONICAL_TENORS)


def test_comparison_tenors_are_canonical() -> None:
    """PKRV/PKISRV comparison tenors must belong to the canonical universe."""

    assert set(PKRV_PKISRV_COMMON_TENORS).issubset(PKRV_CANONICAL_TENORS)


def test_key_tenor_coordinates() -> None:
    """Important maturity coordinates should remain frozen."""

    assert TENOR_TO_YEARS["3M"] == 0.25
    assert TENOR_TO_YEARS["6M"] == 0.5
    assert TENOR_TO_YEARS["1Y"] == 1.0
    assert TENOR_TO_YEARS["10Y"] == 10.0
    assert TENOR_TO_YEARS["20Y"] == 20.0


def test_event_study_configuration() -> None:
    """Event windows and classifications should remain frozen."""

    assert MPC_EVENT_HALF_WINDOWS == (1, 3, 5)
    assert MPC_EVENT_TYPES == ("HIKE", "CUT", "HOLD")


def test_sample_start_dates() -> None:
    """Accepted analytical sample start dates should remain frozen."""

    assert PKRV_SAMPLE_START == date(2022, 1, 4)
    assert PKRV_PKISRV_SAMPLE_START == date(2025, 2, 3)
    assert MACRO_SAMPLE_START == date(2022, 1, 1)


def test_term_spread_definitions() -> None:
    """Preferred term spreads should use the accepted maturity pairs."""

    assert TERM_SPREADS["10Y-2Y"] == ("10Y", "2Y")
    assert TERM_SPREADS["10Y-1Y"] == ("10Y", "1Y")
    assert TERM_SPREADS["5Y-1Y"] == ("5Y", "1Y")
    assert TERM_SPREADS["3Y-3M"] == ("3Y", "3M")


def test_basis_point_conversion() -> None:
    """One percentage point must equal one hundred basis points."""

    assert BASIS_POINTS_PER_PERCENTAGE_POINT == 100.0


def test_required_project_structure_exists() -> None:
    """The configured local repository structure should be complete."""

    assert validate_project_structure() == []
