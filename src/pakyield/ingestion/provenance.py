"""Provenance utilities for PakYield raw-data acquisition."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for a file."""

    if not path.is_file():
        raise FileNotFoundError(f"Raw artifact does not exist: {path}")

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def file_size_bytes(path: Path) -> int:
    """Return the size of a raw artifact in bytes."""

    if not path.is_file():
        raise FileNotFoundError(f"Raw artifact does not exist: {path}")

    return path.stat().st_size
