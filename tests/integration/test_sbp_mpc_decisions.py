"""Integration tests for the frozen SBP MPC event corpus."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MANIFEST_DIR = PROJECT_ROOT / "data" / "manifests"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "sbp" / "mpc"

UNIVERSE_PATH = MANIFEST_DIR / "sbp_mpc_event_universe.csv"

PLAN_PATH = MANIFEST_DIR / "sbp_mpc_acquisition_plan.csv"

EXCLUSIONS_PATH = MANIFEST_DIR / "sbp_mpc_document_exclusions.csv"

DECISIONS_PATH = MANIFEST_DIR / "sbp_mpc_decisions_validated.csv"

CROSSCHECK_PATH = MANIFEST_DIR / "sbp_mpc_policy_rate_crosscheck.csv"

PROVENANCE_PATH = MANIFEST_DIR / "raw_provenance.csv"

EXPECTED_YEAR_COUNTS = {
    "2022": 8,
    "2023": 9,
    "2024": 8,
    "2025": 8,
    "2026": 6,
}

EXPECTED_DIRECTION_COUNTS = {
    "HOLD": 22,
    "RAISE": 9,
    "CUT": 8,
}

EXPECTED_EXCLUSIONS = {
    "Pr-07-Jul-2022.pdf",
    "Pr-23-Jan-2023.pdf",
    "Pr-26-Jun-2023.pdf",
    "Pr-12-Sep-2024.pdf",
}

EXPECTED_EXPLICIT_EFFECTIVE_DATES = {
    "2023-06-26": "2023-06-27",
    "2024-06-10": "2024-06-11",
    "2024-07-29": "2024-07-30",
    "2024-09-12": "2024-09-13",
    "2024-11-04": "2024-11-05",
    "2024-12-16": "2024-12-17",
    "2025-01-27": "2025-01-28",
    "2025-05-05": "2025-05-06",
    "2025-12-15": "2025-12-16",
    "2026-04-27": "2026-04-28",
}


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read a CSV file."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 of one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def test_canonical_event_universe_matches_decisions() -> None:
    """The validated decisions must exactly cover the canonical universe."""

    universe = read_csv(UNIVERSE_PATH)

    decisions = read_csv(DECISIONS_PATH)

    assert len(universe) == 39
    assert len(decisions) == 39

    universe_dates = [row["event_date"] for row in universe]

    decision_dates = [row["event_date"] for row in decisions]

    assert len(set(universe_dates)) == 39

    assert len(set(decision_dates)) == 39

    assert universe_dates == sorted(universe_dates)

    assert decision_dates == (universe_dates)

    year_counts = Counter(row["year"] for row in universe)

    assert dict(year_counts) == EXPECTED_YEAR_COUNTS


def test_mpc_direction_and_change_counts() -> None:
    """Decision classifications must preserve the validated census."""

    decisions = read_csv(DECISIONS_PATH)

    direction_counts = Counter(row["decision_direction"] for row in decisions)

    assert dict(direction_counts) == EXPECTED_DIRECTION_COUNTS

    changed = [row for row in decisions if row["decision_direction"] != "HOLD"]

    assert len(changed) == 17

    assert all(
        row["change_bps"] == "0"
        for row in decisions
        if row["decision_direction"] == "HOLD"
    )

    assert all(
        float(row["change_bps"]) > 0
        for row in decisions
        if row["decision_direction"] == "RAISE"
    )

    assert all(
        float(row["change_bps"]) < 0
        for row in decisions
        if row["decision_direction"] == "CUT"
    )


def test_statement_only_rate_semantics_are_preserved() -> None:
    """A resulting rate must not be invented when SBP did not state it."""

    decisions = read_csv(DECISIONS_PATH)

    by_date = {row["event_date"]: row for row in decisions}

    missing_rates = [
        row["event_date"] for row in decisions if not row["announced_policy_rate"]
    ]

    assert missing_rates == ["2025-12-15"]

    december = by_date["2025-12-15"]

    assert december["decision_direction"] == "CUT"

    assert december["change_bps"] == "-50"

    assert december["announced_policy_rate"] == ""

    assert december["effective_date"] == "2025-12-16"

    assert december["effective_date_source"] == "STATEMENT_EXPLICIT"

    assert december["validation_status"] == ("VALIDATED_CHANGE_ONLY_RATE_NOT_STATED")


def test_explicit_effective_dates_are_statement_derived_only() -> None:
    """Only dates explicitly stated by SBP may populate effective_date."""

    decisions = read_csv(DECISIONS_PATH)

    actual = {
        row["event_date"]: row["effective_date"]
        for row in decisions
        if row["effective_date"]
    }

    assert actual == (EXPECTED_EXPLICIT_EFFECTIVE_DATES)

    for row in decisions:
        if row["event_date"] in (EXPECTED_EXPLICIT_EFFECTIVE_DATES):
            assert row["effective_date_source"] == "STATEMENT_EXPLICIT"
        else:
            assert row["effective_date"] == ""

            assert row["effective_date_source"] == "NOT_STATED"


def test_policy_rate_crosscheck_matches_all_changes() -> None:
    """Every changed MPC event must reconcile to official EasyData."""

    decisions = read_csv(DECISIONS_PATH)

    crosscheck = read_csv(CROSSCHECK_PATH)

    changed_dates = {
        row["event_date"] for row in decisions if row["decision_direction"] != "HOLD"
    }

    crosscheck_dates = {row["event_date"] for row in crosscheck}

    assert len(crosscheck) == 17

    assert len(crosscheck_dates) == 17

    assert crosscheck_dates == (changed_dates)

    assert all(row["crosscheck_status"] == "MATCH" for row in crosscheck)

    sequence_derived = [
        row
        for row in crosscheck
        if row["statement_rate_basis"] == ("SEQUENCE_DERIVED_FOR_VALIDATION_ONLY")
    ]

    assert len(sequence_derived) == 1

    row = sequence_derived[0]

    assert row["event_date"] == "2025-12-15"

    assert row["statement_resulting_rate"] == "10.5"

    assert row["policy_observation_date"] == "2025-12-16"

    assert row["policy_observation_value"] == "10.5"

    assert row["crosscheck_status"] == "MATCH"


def test_raw_corpus_plan_exclusions_and_provenance_reconcile() -> None:
    """Frozen raw bytes must equal 39 accepted plus four exclusions."""

    plan = read_csv(PLAN_PATH)

    exclusions = read_csv(EXCLUSIONS_PATH)

    provenance = [
        row
        for row in read_csv(PROVENANCE_PATH)
        if row["dataset_id"] == "SBP_MPC_EVENTS"
    ]

    accepted_names = {row["resolved_file_name"] for row in plan}

    excluded_names = {row["excluded_file_name"] for row in exclusions}

    physical = {path.name: path for path in RAW_DIR.glob("*.pdf")}

    assert len(plan) == 39
    assert len(accepted_names) == 39

    assert len(exclusions) == 4
    assert excluded_names == (EXPECTED_EXCLUSIONS)

    assert accepted_names.isdisjoint(excluded_names)

    assert len(physical) == 43

    assert set(physical) == (accepted_names | excluded_names)

    provenance_by_name = {row["raw_file_name"]: row for row in provenance}

    assert len(provenance) == 43

    assert len(provenance_by_name) == 43

    assert set(provenance_by_name) == set(physical)

    for row in plan:
        name = row["resolved_file_name"]

        path = physical[name]

        assert path.stat().st_size == int(row["probe_bytes"])

        assert sha256_file(path) == row["probe_sha256"]

        provenance_row = provenance_by_name[name]

        assert provenance_row["sha256"] == row["probe_sha256"]

        assert int(provenance_row["file_size_bytes"]) == int(row["probe_bytes"])

        assert provenance_row["source_reference"] == row["source_url"]

    for row in exclusions:
        name = row["excluded_file_name"]

        path = physical[name]

        assert path.stat().st_size == int(row["excluded_size_bytes"])

        assert sha256_file(path) == row["excluded_sha256"]

        provenance_row = provenance_by_name[name]

        assert provenance_row["sha256"] == row["excluded_sha256"]

        assert provenance_row["source_reference"] == row["excluded_source_url"]


def test_no_partial_files_remain() -> None:
    """Successful acquisition/build steps must leave no .part files."""

    raw_parts = list(RAW_DIR.glob("*.part"))

    manifest_parts = list(MANIFEST_DIR.glob("*.part"))

    assert raw_parts == []
    assert manifest_parts == []
