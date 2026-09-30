"""Tests for the frozen SBP policy-rate raw artifact and validator."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from decimal import Decimal
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_sbp_policy_rate_structural_census.py"

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "sbp" / "policy_rate" / "data_series.csv"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

CENSUS_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_policy_rate_structural_census.csv"
)

EXPECTED_SHA256 = "4dbf6d69a8ece64bd45e9f3fc8bdb0424d77ded1169b04e68696c5ee8d702420"


def load_validator_module() -> ModuleType:
    """Load the SBP validator directly from its script path."""

    spec = importlib.util.spec_from_file_location(
        "build_sbp_policy_rate_structural_census",
        SCRIPT_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


def test_frozen_raw_artifact_identity() -> None:
    """Frozen SBP raw bytes must remain immutable."""

    assert RAW_PATH.exists()

    raw = RAW_PATH.read_bytes()

    assert len(raw) == 6559

    digest = hashlib.sha256(raw).hexdigest()

    assert digest == EXPECTED_SHA256


def test_sbp_raw_source_structure() -> None:
    """Official SBP source CSV must retain its accepted schema."""

    with RAW_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 39

    assert {row["Series Key"] for row in rows} == {"TS_GP_IR_SIRPR_AH.SBPOL0030"}

    assert {row["Series"] for row in rows} == {"SBP Policy (Target) Rate"}

    assert {row["Unit"] for row in rows} == {"Percent"}

    assert {row["Observation Status"] for row in rows} == {"Normal"}

    assert {row["Observation Status Comment"] for row in rows} == {""}


def test_sbp_source_dates_are_unique() -> None:
    """Every source observation must have a unique effective date."""

    with RAW_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    dates = [row["Observation Date"] for row in rows]

    assert len(dates) == 39
    assert len(set(dates)) == 39


def test_policy_rate_values_are_valid() -> None:
    """Policy-rate values must parse and remain in valid bounds."""

    with RAW_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    values = [Decimal(row["Observation Value"]) for row in rows]

    assert len(values) == 39

    assert min(values) == Decimal("5.75")

    assert max(values) == Decimal("22")

    assert all(Decimal("0") < value < Decimal("100") for value in values)


def test_sbp_policy_rate_provenance_reconciles() -> None:
    """Provenance must exactly identify the frozen raw artifact."""

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = [
            row
            for row in csv.DictReader(file)
            if row["dataset_id"] == "SBP_POLICY_RATE"
        ]

    assert len(rows) == 1

    row = rows[0]

    assert row["source_authority"] == ("State Bank of Pakistan")

    assert row["acquisition_source"] == ("SBP EasyData browser download")

    assert row["raw_file_name"] == ("data_series.csv")

    assert row["raw_relative_path"] == ("data/raw/sbp/policy_rate/data_series.csv")

    assert row["sha256"] == EXPECTED_SHA256

    assert int(row["file_size_bytes"]) == 6559

    assert row["status"] == "SUCCESS"


def test_validator_accepts_frozen_artifact() -> None:
    """Validator integrity/provenance gates must accept the artifact."""

    module = load_validator_module()

    module.validate_raw_identity()
    module.validate_provenance()

    rows = module.load_source_rows()

    assert len(rows) == 39


def test_validator_classifies_valid_row() -> None:
    """A valid SBP source observation must be accepted."""

    module = load_validator_module()

    rows = module.load_source_rows()

    structural_class, status = module.classify_row(
        rows[0],
        duplicate_date=False,
    )

    assert structural_class == ("VALID_OBSERVATION")

    assert status == "ACCEPTED"


def test_validator_rejects_duplicate_date() -> None:
    """Duplicate dates must be explicitly reviewable."""

    module = load_validator_module()

    rows = module.load_source_rows()

    structural_class, status = module.classify_row(
        rows[0],
        duplicate_date=True,
    )

    assert "DUPLICATE_DATE" in (structural_class.split("|"))

    assert status == "REVIEW"


def test_structural_census_manifest_reconciles() -> None:
    """Generated census must contain exactly 39 accepted observations."""

    assert CENSUS_PATH.exists()

    with CENSUS_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 39

    assert {row["structural_class"] for row in rows} == {"VALID_OBSERVATION"}

    assert {row["validation_status"] for row in rows} == {"ACCEPTED"}

    dates = sorted(row["observation_date"] for row in rows)

    assert len(set(dates)) == 39

    assert dates[0] == ("2015-05-25")

    assert dates[-1] == ("2026-04-28")
