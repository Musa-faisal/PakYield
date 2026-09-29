"""Acquire the approved MUFAP PKRV universe safely and resumably."""

from __future__ import annotations

import argparse
import csv
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from pakyield.ingestion.provenance import (
    file_size_bytes,
    sha256_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

APPROVED_PLAN_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "pkrv_approved_acquisition_plan.csv"
)

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkrv"

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Referer": (
        "https://www.mufap.com.pk/"
        "WebRegulations/Index"
        "?Head=Pricing"
        "&title=PKRV%2FPKISRV%2FPKFRV"
    ),
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Acquire approved PKRV artifacts with resumable provenance.")
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=("Validate plan, raw storage and provenance without downloading."),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=("Maximum number of new/recovered artifacts to acquire."),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.10,
        help="Delay between successful network requests.",
    )

    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def validate_provenance_schema() -> None:
    """Ensure the provenance manifest uses the accepted schema."""

    if not PROVENANCE_PATH.is_file():
        raise FileNotFoundError(f"Missing provenance manifest: {PROVENANCE_PATH}")

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

    if header != PROVENANCE_FIELDS:
        raise RuntimeError(
            "Provenance manifest schema does not match "
            "the accepted raw provenance contract."
        )


def successful_provenance_by_path() -> dict[str, dict[str, str]]:
    """Return successful PKRV provenance keyed by raw path."""

    rows = read_csv(PROVENANCE_PATH)

    result: dict[str, dict[str, str]] = {}

    for row in rows:
        if row["dataset_id"] != "PKRV":
            continue

        if row["status"] != "SUCCESS":
            continue

        relative_path = row["raw_relative_path"]

        if relative_path in result:
            raise RuntimeError(
                f"Duplicate successful provenance entry for {relative_path}"
            )

        result[relative_path] = row

    return result


def verify_existing_artifact(
    destination: Path,
    provenance: dict[str, str],
) -> None:
    """Verify an existing raw artifact against stored provenance."""

    actual_sha = sha256_file(destination)
    actual_size = file_size_bytes(destination)

    expected_sha = provenance["sha256"]

    try:
        expected_size = int(provenance["file_size_bytes"])
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid provenance file size for {destination.name}"
        ) from exc

    if actual_sha != expected_sha:
        raise RuntimeError(f"Existing raw artifact checksum mismatch: {destination}")

    if actual_size != expected_size:
        raise RuntimeError(f"Existing raw artifact size mismatch: {destination}")


def append_provenance(
    *,
    source_url: str,
    destination: Path,
    content_type: str,
    observation_date: str,
    selection_basis: str,
) -> None:
    """Append one successful raw acquisition record."""

    checksum = sha256_file(destination)
    size = file_size_bytes(destination)

    relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

    record = {
        "dataset_id": "PKRV",
        "source_authority": "MUFAP",
        "acquisition_source": ("MUFAP current pricing API approved acquisition plan"),
        "source_reference": source_url,
        "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "raw_file_name": destination.name,
        "raw_relative_path": relative_path,
        "file_format": (destination.suffix.lstrip(".").lower()),
        "sha256": checksum,
        "file_size_bytes": str(size),
        "status": "SUCCESS",
        "notes": (
            f"observation_date={observation_date}; "
            f"selection_basis={selection_basis}; "
            f"content_type={content_type}"
        ),
    }

    with PROVENANCE_PATH.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=PROVENANCE_FIELDS,
        )
        writer.writerow(record)


def download_bytes(
    session: requests.Session,
    source_url: str,
) -> tuple[bytes, str]:
    """Download one MUFAP artifact with bounded retries."""

    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            response = session.get(
                source_url,
                headers=HEADERS,
                timeout=30,
            )

            response.raise_for_status()

            content = response.content

            if not content:
                raise RuntimeError("MUFAP returned empty content")

            content_type = response.headers.get(
                "Content-Type",
                "",
            )

            lowered = content_type.lower()

            if "text/html" in lowered:
                raise RuntimeError(
                    "MUFAP returned HTML instead of the approved raw artifact"
                )

            return content, content_type

        except (
            requests.RequestException,
            RuntimeError,
        ) as exc:
            last_error = exc

            if attempt == 3:
                break

            time.sleep(float(attempt))

    assert last_error is not None
    raise RuntimeError(
        f"Download failed after 3 attempts: {source_url}"
    ) from last_error


def main() -> None:
    """Acquire the approved PKRV universe."""

    args = parse_args()

    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    if args.delay < 0:
        raise SystemExit("--delay cannot be negative")

    validate_provenance_schema()

    approved_rows = read_csv(APPROVED_PLAN_PATH)

    if len(approved_rows) != 1159:
        raise RuntimeError(
            "Approved plan must contain exactly 1,159 artifacts; "
            f"found {len(approved_rows)}"
        )

    observation_dates = [row["observation_date"] for row in approved_rows]

    if len(set(observation_dates)) != 1159:
        raise RuntimeError(
            "Approved plan does not contain 1,159 unique observation dates"
        )

    RAW_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    stale_parts = sorted(RAW_DIRECTORY.glob("*.part"))

    if stale_parts:
        raise RuntimeError(
            f"Stale temporary files exist. Resolve before acquisition: {stale_parts}"
        )

    provenance_by_path = successful_provenance_by_path()

    verified_existing = 0
    missing = 0
    orphan_file = 0
    orphan_provenance = 0

    states: list[
        tuple[
            dict[str, str],
            Path,
            str,
            str,
        ]
    ] = []

    for row in approved_rows:
        destination = RAW_DIRECTORY / row["file_name"]

        relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

        provenance = provenance_by_path.get(relative_path)

        exists = destination.is_file()

        if exists and provenance is not None:
            verify_existing_artifact(
                destination,
                provenance,
            )

            verified_existing += 1

            states.append(
                (
                    row,
                    destination,
                    relative_path,
                    "VERIFIED_EXISTING",
                )
            )

            continue

        if exists and provenance is None:
            orphan_file += 1

            states.append(
                (
                    row,
                    destination,
                    relative_path,
                    "FILE_WITHOUT_PROVENANCE",
                )
            )

            continue

        if not exists and provenance is not None:
            orphan_provenance += 1

            states.append(
                (
                    row,
                    destination,
                    relative_path,
                    "PROVENANCE_WITHOUT_FILE",
                )
            )

            continue

        missing += 1

        states.append(
            (
                row,
                destination,
                relative_path,
                "MISSING",
            )
        )

    print("===== PKRV BULK ACQUISITION PREFLIGHT =====")
    print(
        "Approved artifacts:",
        len(approved_rows),
    )
    print(
        "Verified existing:",
        verified_existing,
    )
    print(
        "Missing:",
        missing,
    )
    print(
        "Files without provenance:",
        orphan_file,
    )
    print(
        "Provenance without files:",
        orphan_provenance,
    )

    if orphan_file:
        raise RuntimeError(
            "Raw files without provenance require "
            "manual reconciliation before bulk acquisition."
        )

    if orphan_provenance:
        raise RuntimeError(
            "Successful provenance records without raw files "
            "require manual reconciliation before bulk acquisition."
        )

    if args.dry_run:
        print("")
        print("PASS: dry-run preflight completed; no downloads performed")
        return

    source_gap_path = PROJECT_ROOT / "data" / "manifests" / "pkrv_source_gaps.csv"

    source_gap_rows = read_csv(source_gap_path)

    skip_file_names = {
        row["file_name"] for row in source_gap_rows if row["status"] == "SKIP"
    }

    expected_skip_files = {
        "PKRV13092023781.csv",
        "PKRV110920241274.csv",
    }

    if skip_file_names != expected_skip_files:
        raise RuntimeError(
            "PKRV skip manifest does not match "
            "the two accepted dead URLs. "
            f"Found: {sorted(skip_file_names)}"
        )

    acquisition_candidates = [
        state
        for state in states
        if state[3] == "MISSING" and state[0]["file_name"] not in skip_file_names
    ]

    if args.limit is not None:
        acquisition_candidates = acquisition_candidates[: args.limit]

    print("")
    print(
        "New artifacts scheduled:",
        len(acquisition_candidates),
    )

    if not acquisition_candidates:
        print("PASS: no new PKRV artifacts require acquisition")
        return

    downloaded = 0

    with requests.Session() as session:
        for index, (
            row,
            destination,
            relative_path,
            _state,
        ) in enumerate(
            acquisition_candidates,
            start=1,
        ):
            if destination.exists():
                raise FileExistsError(
                    f"Refusing to overwrite existing raw artifact: {destination}"
                )

            current_provenance = successful_provenance_by_path()

            if relative_path in current_provenance:
                raise RuntimeError(
                    "Successful provenance already exists "
                    f"for missing destination: {relative_path}"
                )

            temporary = destination.with_name(destination.name + ".part")

            if temporary.exists():
                raise FileExistsError(f"Temporary file already exists: {temporary}")

            content, content_type = download_bytes(
                session,
                row["source_url"],
            )

            temporary.write_bytes(content)

            if file_size_bytes(temporary) != len(content):
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"Temporary file size mismatch: {temporary}")

            temporary.replace(destination)

            try:
                append_provenance(
                    source_url=row["source_url"],
                    destination=destination,
                    content_type=content_type,
                    observation_date=row["observation_date"],
                    selection_basis=row["selection_basis"],
                )
            except Exception:
                destination.unlink(missing_ok=True)
                raise

            downloaded += 1

            print(
                f"[{index:04d}/{len(acquisition_candidates):04d}]",
                row["observation_date"],
                "|",
                destination.name,
                "|",
                file_size_bytes(destination),
                "bytes",
            )

            if args.delay:
                time.sleep(args.delay)

    print("")
    print(
        "ACQUISITION COMPLETE:",
        downloaded,
        "new artifact(s)",
    )


if __name__ == "__main__":
    main()
