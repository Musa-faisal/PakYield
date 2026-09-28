"""Unit tests for PakYield raw-data provenance utilities."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest

from pakyield.ingestion.provenance import file_size_bytes, sha256_file


def test_sha256_file(tmp_path: Path) -> None:
    """Checksum output should match hashlib for known bytes."""

    artifact = tmp_path / "artifact.txt"
    content = b"PakYield raw data provenance test"
    artifact.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert sha256_file(artifact) == expected


def test_file_size_bytes(tmp_path: Path) -> None:
    """File-size metadata should reflect stored bytes."""

    artifact = tmp_path / "artifact.bin"
    content = b"1234567890"
    artifact.write_bytes(content)

    assert file_size_bytes(artifact) == len(content)


@pytest.mark.parametrize(
    "function",
    [sha256_file, file_size_bytes],
)
def test_missing_artifact_rejected(
    tmp_path: Path,
    function: Callable[[Path], object],
) -> None:
    """Provenance functions must reject nonexistent artifacts."""

    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        function(missing)
