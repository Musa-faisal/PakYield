"""Acquire frozen Pakistan Bureau of Statistics CPI source artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "pbs_cpi_acquisition_plan.csv"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pbs" / "cpi"

EXPECTED_ARTIFACTS = 4


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
    """Return SHA-256 of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def validate_plan(
    plan: list[dict[str, str]],
) -> None:
    """Validate the frozen acquisition plan."""

    assert len(plan) == EXPECTED_ARTIFACTS

    names = [row["resolved_file_name"] for row in plan]

    urls = [row["source_url"] for row in plan]

    ids = [row["artifact_id"] for row in plan]

    assert len(set(names)) == 4
    assert len(set(urls)) == 4
    assert len(set(ids)) == 4

    for row in plan:
        assert row["resolution_status"] == "RESOLVED"

        assert row["source_authority"] == "Pakistan Bureau of Statistics"

        assert row["source_url"].startswith("https://www.pbs.gov.pk/")

        assert row["resolved_file_name"].endswith(".pdf")

        assert int(row["probe_bytes"]) > 1000

        assert len(row["probe_sha256"]) == 64


def provenance_rows() -> list[dict[str, str]]:
    """Return existing PBS CPI provenance rows."""

    return [row for row in read_csv(PROVENANCE_PATH) if row["dataset_id"] == "PBS_CPI"]


def append_provenance(
    row: dict[str, str],
    path: Path,
) -> None:
    """Append one successful acquisition row preserving CSV CRLF."""

    with PROVENANCE_PATH.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames

    assert fieldnames is not None

    provenance = {
        "dataset_id": "PBS_CPI",
        "source_authority": "Pakistan Bureau of Statistics",
        "acquisition_source": "official PBS direct PDF download",
        "source_reference": row["source_url"],
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "raw_file_name": row["resolved_file_name"],
        "raw_relative_path": str(path.relative_to(PROJECT_ROOT)),
        "file_format": "pdf",
        "sha256": sha256_file(path),
        "file_size_bytes": str(path.stat().st_size),
        "status": "SUCCESS",
        "notes": row["notes"],
    }

    assert set(provenance) == set(fieldnames), (
        f"Provenance schema mismatch: expected {fieldnames}, built {list(provenance)}"
    )

    with PROVENANCE_PATH.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\r\n",
        )

        writer.writerow(provenance)


def validate_existing(
    row: dict[str, str],
    path: Path,
    provenance_by_name: dict[
        str,
        dict[str, str],
    ],
) -> None:
    """Validate an already acquired frozen artifact."""

    expected_size = int(row["probe_bytes"])

    expected_sha = row["probe_sha256"]

    assert path.exists()

    raw = path.read_bytes()

    assert raw.startswith(b"%PDF"), f"Existing file is not a PDF: {path.name}"

    assert len(raw) == expected_size, (
        f"Size drift for {path.name}: {len(raw)} != {expected_size}"
    )

    assert hashlib.sha256(raw).hexdigest() == expected_sha, f"SHA drift for {path.name}"

    assert path.name in provenance_by_name, (
        f"Existing raw file lacks provenance: {path.name}"
    )

    provenance = provenance_by_name[path.name]

    assert provenance["source_reference"] == row["source_url"]

    assert provenance["sha256"] == expected_sha

    assert int(provenance["file_size_bytes"]) == expected_size

    assert provenance["status"] == "SUCCESS"


def download(
    row: dict[str, str],
) -> Path:
    """Download one frozen source artifact atomically."""

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_path = RAW_DIR / row["resolved_file_name"]

    part_path = Path(str(final_path) + ".part")

    part_path.unlink(missing_ok=True)

    result = subprocess.run(
        [
            "curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            "60",
            "--user-agent",
            "Mozilla/5.0",
            row["source_url"],
            "--output",
            str(part_path),
        ],
        check=False,
    )

    if result.returncode != 0:
        part_path.unlink(missing_ok=True)

        raise RuntimeError(
            f"curl failed for {row['artifact_id']} with exit code {result.returncode}"
        )

    raw = part_path.read_bytes()

    expected_size = int(row["probe_bytes"])

    expected_sha = row["probe_sha256"]

    if not raw.startswith(b"%PDF"):
        part_path.unlink(missing_ok=True)

        raise RuntimeError(f"Downloaded artifact is not PDF: {row['artifact_id']}")

    if len(raw) != expected_size:
        part_path.unlink(missing_ok=True)

        raise RuntimeError(
            f"Source-byte size drift for "
            f"{row['artifact_id']}: "
            f"{len(raw)} != {expected_size}"
        )

    actual_sha = hashlib.sha256(raw).hexdigest()

    if actual_sha != expected_sha:
        part_path.unlink(missing_ok=True)

        raise RuntimeError(
            f"Source-byte SHA drift for "
            f"{row['artifact_id']}: "
            f"{actual_sha} != {expected_sha}"
        )

    part_path.replace(final_path)

    return final_path


def main() -> None:
    """Acquire or validate all frozen PBS CPI artifacts."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    plan = read_csv(PLAN_PATH)

    validate_plan(plan)

    existing_provenance = provenance_rows()

    provenance_by_name = {row["raw_file_name"]: row for row in existing_provenance}

    assert len(provenance_by_name) == len(existing_provenance), (
        "Duplicate PBS CPI provenance filenames detected"
    )

    approved_names = {row["resolved_file_name"] for row in plan}

    physical_names = {path.name for path in RAW_DIR.glob("*.pdf")}

    unexpected = physical_names - approved_names

    assert not unexpected, f"Unexpected PBS CPI raw PDFs: {sorted(unexpected)}"

    existing = []
    missing = []

    for row in plan:
        path = RAW_DIR / row["resolved_file_name"]

        if path.exists():
            validate_existing(
                row,
                path,
                provenance_by_name,
            )

            existing.append(row)
        else:
            assert row["resolved_file_name"] not in provenance_by_name, (
                f"Provenance exists without raw file: {row['resolved_file_name']}"
            )

            missing.append(row)

    print("===== PBS CPI ACQUISITION PREFLIGHT =====")

    print(
        "Approved artifacts:",
        len(plan),
    )

    print(
        "Existing raw artifacts:",
        len(existing),
    )

    print(
        "Missing raw artifacts:",
        len(missing),
    )

    print(
        "Successful provenance rows:",
        len(existing_provenance),
    )

    if args.dry_run:
        print("")
        print(
            "Scheduled downloads:",
            len(missing),
        )

        print("")
        print("PASS: PBS CPI acquisition dry-run complete")

        return

    for index, row in enumerate(
        plan,
        start=1,
    ):
        name = row["resolved_file_name"]

        path = RAW_DIR / name

        if path.exists():
            print(f"[{index:02d}/04] EXISTING {name}")

            continue

        print(f"[{index:02d}/04] DOWNLOAD {name}")

        acquired = download(row)

        append_provenance(
            row,
            acquired,
        )

    final_provenance = provenance_rows()

    final_by_name = {row["raw_file_name"]: row for row in final_provenance}

    missing_after = []

    for row in plan:
        path = RAW_DIR / row["resolved_file_name"]

        if not path.exists():
            missing_after.append(row["resolved_file_name"])

            continue

        validate_existing(
            row,
            path,
            final_by_name,
        )

    assert not missing_after

    assert len(final_provenance) == EXPECTED_ARTIFACTS

    print("")
    print("===== PBS CPI ACQUISITION CLOSURE =====")

    print(
        "Raw artifacts:",
        EXPECTED_ARTIFACTS,
    )

    print(
        "Missing:",
        len(missing_after),
    )

    print(
        "Provenance rows:",
        len(final_provenance),
    )

    print("")
    print("PASS: all frozen PBS CPI raw artifacts acquired")


if __name__ == "__main__":
    main()
