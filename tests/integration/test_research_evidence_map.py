"""Integration tests for the Phase 6D research-evidence map."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_research_evidence_map.py"

EXPECTED_SHA256 = "50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002"

EXPECTED_TARGETS = {
    "RQ1": 6,
    "RQ2": 3,
    "RQ3": 3,
    "RQ4": 2,
    "H1": 3,
    "H2": 2,
    "H3": 3,
    "H4": 2,
}

EXPECTED_CLASSES = {
    "DESCRIPTIVE": 10,
    "INFERENTIAL": 10,
    "DATA_LIMITATION": 4,
}


def load_builder() -> ModuleType:
    """Load the production evidence-map builder."""

    spec = importlib.util.spec_from_file_location(
        "build_research_evidence_map",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder()


def get_output_attribute() -> str:
    """Locate the builder's output Path constant."""

    candidates = []

    for name, value in vars(BUILDER).items():
        if not isinstance(
            value,
            Path,
        ):
            continue

        upper = name.upper()

        if "OUTPUT" in upper or ("MAP" in upper and "PATH" in upper):
            candidates.append(name)

    assert candidates, "No output Path constant found in evidence-map builder"

    csv_candidates = [
        name
        for name in candidates
        if str(
            getattr(
                BUILDER,
                name,
            )
        ).endswith(".csv")
    ]

    if len(csv_candidates) == 1:
        return csv_candidates[0]

    assert len(candidates) == 1

    return candidates[0]


OUTPUT_ATTRIBUTE = get_output_attribute()


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Generate one isolated research-evidence map."""

    output = tmp_path / file_name

    monkeypatch.setattr(
        BUILDER,
        OUTPUT_ATTRIBUTE,
        output,
    )

    BUILDER.main()

    assert output.is_file()

    return output


def read_map(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one evidence-map CSV."""

    with path.open(
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
    candidates: tuple[
        str,
        ...,
    ],
) -> str:
    """Resolve a required field from approved aliases."""

    for candidate in candidates:
        if candidate in headers:
            return candidate

    raise AssertionError(
        f"Required field not found. Candidates={candidates}; headers={headers}"
    )


def test_research_evidence_map_frozen_shape_and_sha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map row count and bytes remain frozen."""

    output = run_builder(
        tmp_path,
        monkeypatch,
        "research_evidence_map.csv",
    )

    _headers, rows = read_map(output)

    assert len(rows) == 24

    assert hashlib.sha256(output.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_research_target_census_is_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every RQ/H target retains its approved evidence count."""

    output = run_builder(
        tmp_path,
        monkeypatch,
        "targets.csv",
    )

    headers, rows = read_map(output)

    target_field = find_field(
        headers,
        (
            "target_id",
            "research_target",
            "target",
        ),
    )

    assert Counter(row[target_field] for row in rows) == EXPECTED_TARGETS


def test_evidence_class_census_is_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Descriptive/inferential/limitation classes remain exact."""

    output = run_builder(
        tmp_path,
        monkeypatch,
        "classes.csv",
    )

    headers, rows = read_map(output)

    evidence_field = find_field(
        headers,
        (
            "evidence_class",
            "evidence_type",
            "class",
        ),
    )

    assert Counter(row[evidence_field] for row in rows) == EXPECTED_CLASSES

    assert set(row[evidence_field] for row in rows) == {
        "DESCRIPTIVE",
        "INFERENTIAL",
        "DATA_LIMITATION",
    }


def test_all_targets_have_evidence_and_required_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No frozen evidence-map row is structurally empty."""

    output = run_builder(
        tmp_path,
        monkeypatch,
        "completeness.csv",
    )

    headers, rows = read_map(output)

    target_field = find_field(
        headers,
        (
            "target_id",
            "research_target",
            "target",
        ),
    )

    evidence_field = find_field(
        headers,
        (
            "evidence_class",
            "evidence_type",
            "class",
        ),
    )

    assert set(row[target_field] for row in rows) == set(EXPECTED_TARGETS)

    for row in rows:
        assert row[target_field].strip()

        assert row[evidence_field].strip()

        assert any(
            value.strip()
            for key, value in row.items()
            if key
            not in {
                target_field,
                evidence_field,
            }
            and isinstance(
                value,
                str,
            )
        )


def test_research_evidence_map_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated map construction remains byte-identical."""

    first = run_builder(
        tmp_path,
        monkeypatch,
        "first.csv",
    )

    first_bytes = first.read_bytes()

    second = run_builder(
        tmp_path,
        monkeypatch,
        "second.csv",
    )

    second_bytes = second.read_bytes()

    assert first_bytes == second_bytes

    assert hashlib.sha256(first_bytes).hexdigest() == EXPECTED_SHA256
