"""Integration tests for the Phase 8A publication evidence packet."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_research_publication_packet.py"

EXPECTED_INPUT_SHA = "50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002"


def load_builder_module() -> ModuleType:
    """Load the Phase 8A production builder."""

    spec = importlib.util.spec_from_file_location(
        "build_research_publication_packet",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> Path:
    """Generate the publication packet in a temporary location."""

    path = tmp_path / name

    monkeypatch.setattr(
        BUILDER,
        "OUTPUT_PATH",
        path,
    )

    BUILDER.main()

    assert path.is_file()

    return path


def test_publication_packet_preserves_complete_frozen_evidence_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Packet must preserve the complete 24-row frozen evidence register."""

    actual_input_sha = hashlib.sha256(BUILDER.INPUT_PATH.read_bytes()).hexdigest()

    assert actual_input_sha == EXPECTED_INPUT_SHA

    with BUILDER.INPUT_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        headers = list(reader.fieldnames or [])

        source_rows = list(reader)

    assert len(source_rows) == 24
    assert headers

    output = run_builder(
        tmp_path,
        monkeypatch,
        "packet.md",
    )

    text = output.read_text(encoding="utf-8")

    evidence_sections = re.findall(
        r"^## Evidence Row \d{2}$",
        text,
        flags=re.MULTILINE,
    )

    assert len(evidence_sections) == 24

    assert EXPECTED_INPUT_SHA in text

    for header in headers:
        assert text.count(f"- **{header}:**") == 24

    assert "convert descriptive evidence into inferential evidence" in text

    assert "reinterpret MPC announcement-window results as policy surprise" in text


def test_publication_packet_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated packet construction must be byte-identical."""

    first = run_builder(
        tmp_path,
        monkeypatch,
        "first.md",
    )

    first_bytes = first.read_bytes()

    second = run_builder(
        tmp_path,
        monkeypatch,
        "second.md",
    )

    second_bytes = second.read_bytes()

    assert first_bytes == second_bytes

    assert (
        hashlib.sha256(first_bytes).hexdigest()
        == hashlib.sha256(second_bytes).hexdigest()
    )
