"""Resumable immutable acquisition of frozen MUFAP PKISRV raw artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "pkisrv_acquisition_plan.csv"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkisrv"

EXPECTED_PLAN_ROWS = 407
EXPECTED_START = "2025-02-03"
EXPECTED_END = "2026-09-30"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    ),
    "Referer": (
        "https://www.mufap.com.pk/"
        "WebRegulations/Index"
        "?Head=Pricing"
        "&title=PKRV%2FPKISRV%2FPKFRV"
    ),
}

PROVENANCE_FIELDS = [
    "dataset_id",
    "source_authority",
    "acquisition_source",
    "source_reference",
    "retrieved_at_utc",
    "raw_file_name",
    "raw_relative_path",
    "file_format",
    "sha256",
    "file_size_bytes",
    "status",
    "notes",
]


def sha256_bytes(raw: bytes) -> str:
    """Return SHA-256 hex digest."""

    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    """Return SHA-256 for an existing file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_plan() -> list[dict[str, str]]:
    """Read and validate the frozen acquisition plan."""

    with PLAN_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == EXPECTED_PLAN_ROWS

    dates = [row["observation_date"] for row in rows]

    assert len(set(dates)) == EXPECTED_PLAN_ROWS
    assert min(dates) == EXPECTED_START
    assert max(dates) == EXPECTED_END

    assert all(row["status"] == "READY" for row in rows)

    return rows


def read_provenance() -> list[dict[str, str]]:
    """Read existing provenance manifest."""

    if not PROVENANCE_PATH.exists():
        return []

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def append_provenance(
    row: dict[str, str],
) -> None:
    """Append exactly one provenance record."""

    exists = PROVENANCE_PATH.exists()

    with PROVENANCE_PATH.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=PROVENANCE_FIELDS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)

        file.flush()
        os.fsync(file.fileno())


def validate_response(
    *,
    raw: bytes,
    content_type: str,
    file_name: str,
) -> None:
    """Reject clearly invalid download responses."""

    if not raw:
        raise RuntimeError(f"{file_name}: empty response")

    prefix = raw[:300].lower()

    if b"<html" in prefix or b"<!doctype html" in prefix:
        raise RuntimeError(f"{file_name}: HTML returned instead of raw artifact")

    if "text/html" in content_type.lower():
        raise RuntimeError(f"{file_name}: unexpected HTML content type")


def main() -> None:
    """Acquire missing PKISRV artifacts safely."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.10,
    )

    args = parser.parse_args()

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plan = read_plan()
    provenance = read_provenance()

    pkisrv_provenance = [
        row
        for row in provenance
        if (row.get("dataset_id") == "PKISRV" and row.get("status") == "SUCCESS")
    ]

    provenance_by_file = {row["raw_file_name"]: row for row in pkisrv_provenance}

    if len(provenance_by_file) != len(pkisrv_provenance):
        raise RuntimeError("Duplicate successful PKISRV provenance rows found")

    plan_names = {row["file_name"] for row in plan}

    physical_files = {
        path.name: path
        for path in RAW_DIR.iterdir()
        if path.is_file()
        and not path.name.endswith(".part")
        and path.name != ".gitkeep"
    }

    unknown_files = set(physical_files) - plan_names

    if unknown_files:
        raise RuntimeError(f"Unexpected raw PKISRV files: {sorted(unknown_files)}")

    for file_name, path in physical_files.items():
        if file_name not in provenance_by_file:
            raise RuntimeError(f"Raw artifact exists without provenance: {file_name}")

        record = provenance_by_file[file_name]

        actual_size = path.stat().st_size
        expected_size = int(record["file_size_bytes"])

        if actual_size != expected_size:
            raise RuntimeError(f"{file_name}: size mismatch")

        actual_sha = sha256_file(path)

        if actual_sha != record["sha256"]:
            raise RuntimeError(f"{file_name}: SHA-256 mismatch")

    for file_name in provenance_by_file:
        if file_name not in physical_files:
            raise RuntimeError(f"Provenance exists without raw artifact: {file_name}")

    missing = [row for row in plan if row["file_name"] not in physical_files]

    scheduled = missing[: args.limit] if args.limit is not None else missing

    print("===== PKISRV BULK ACQUISITION =====")
    print(
        "Approved plan:",
        len(plan),
    )
    print(
        "Existing verified:",
        len(physical_files),
    )
    print(
        "Missing:",
        len(missing),
    )
    print(
        "Scheduled:",
        len(scheduled),
    )
    print(
        "Dry run:",
        args.dry_run,
    )

    if scheduled:
        print("")
        print(
            "First scheduled:",
            scheduled[0]["observation_date"],
            "|",
            scheduled[0]["file_name"],
        )
        print(
            "Last scheduled:",
            scheduled[-1]["observation_date"],
            "|",
            scheduled[-1]["file_name"],
        )

    if args.dry_run:
        print("")
        print("PASS: PKISRV acquisition dry run complete")
        return

    session = requests.Session()
    session.headers.update(HEADERS)

    completed = 0

    for index, row in enumerate(
        scheduled,
        start=1,
    ):
        file_name = row["file_name"]

        destination = RAW_DIR / file_name

        temporary = destination.with_name(destination.name + ".part")

        if temporary.exists():
            raise RuntimeError(f"Stale partial artifact exists: {temporary.name}")

        print(
            f"[{index}/{len(scheduled)}]",
            row["observation_date"],
            file_name,
        )

        response = None

        for attempt in range(
            1,
            4,
        ):
            try:
                response = session.get(
                    row["source_url"],
                    timeout=30,
                )

                response.raise_for_status()
                break

            except requests.RequestException:
                if attempt == 3:
                    raise

                time.sleep(float(attempt))

        assert response is not None

        raw = response.content

        validate_response(
            raw=raw,
            content_type=response.headers.get(
                "Content-Type",
                "",
            ),
            file_name=file_name,
        )

        expected_extension = row["extension"]

        if Path(file_name).suffix.lower() != expected_extension:
            raise RuntimeError(f"{file_name}: extension mismatch")

        expected_sha = sha256_bytes(raw)

        temporary.write_bytes(raw)

        if temporary.stat().st_size != len(raw):
            temporary.unlink(missing_ok=True)

            raise RuntimeError(f"{file_name}: temporary size verification failed")

        if sha256_file(temporary) != expected_sha:
            temporary.unlink(missing_ok=True)

            raise RuntimeError(f"{file_name}: temporary SHA verification failed")

        temporary.replace(destination)

        relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

        provenance_row = {
            "dataset_id": "PKISRV",
            "source_authority": "MUFAP",
            "acquisition_source": "MUFAP",
            "source_reference": row["source_url"],
            "retrieved_at_utc": (datetime.now(UTC).isoformat()),
            "raw_file_name": file_name,
            "raw_relative_path": relative_path,
            "file_format": (expected_extension.lstrip(".")),
            "sha256": expected_sha,
            "file_size_bytes": str(len(raw)),
            "status": "SUCCESS",
            "notes": (
                "canonical observation date "
                f"{row['observation_date']}; "
                "raw MUFAP artifact preserved unchanged"
            ),
        }

        try:
            append_provenance(provenance_row)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        completed += 1

        if args.delay > 0:
            time.sleep(args.delay)

    print("")
    print(
        "Downloaded this run:",
        completed,
    )
    print("PASS: PKISRV acquisition run complete")


if __name__ == "__main__":
    main()
