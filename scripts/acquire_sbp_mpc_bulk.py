"""Acquire frozen official SBP MPC statement PDFs with provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_acquisition_plan.csv"

UNIVERSE_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_event_universe.csv"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "sbp" / "mpc"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

EXCLUSIONS_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_document_exclusions.csv"
)

EXPECTED_ROWS = 39

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
    """Return SHA-256 for bytes."""

    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    """Return SHA-256 for a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read a UTF-8 CSV into dictionaries."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def load_provenance() -> list[dict[str, str]]:
    """Load the global raw-provenance manifest."""

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        assert reader.fieldnames == PROVENANCE_FIELDS, (
            f"Unexpected raw-provenance schema: {reader.fieldnames}"
        )

        return list(reader)


def validate_plan() -> list[dict[str, str]]:
    """Validate the canonical universe and resolved acquisition plan."""

    universe = read_csv(UNIVERSE_PATH)

    plan = read_csv(PLAN_PATH)

    assert len(universe) == EXPECTED_ROWS, (
        f"Expected {EXPECTED_ROWS} universe rows, found {len(universe)}"
    )

    assert len(plan) == EXPECTED_ROWS, (
        f"Expected {EXPECTED_ROWS} plan rows, found {len(plan)}"
    )

    universe_dates = [row["event_date"] for row in universe]

    plan_dates = [row["event_date"] for row in plan]

    assert len(set(universe_dates)) == EXPECTED_ROWS

    assert len(set(plan_dates)) == EXPECTED_ROWS

    assert universe_dates == plan_dates, (
        "Acquisition plan does not exactly match canonical MPC event universe"
    )

    expected_years = Counter(
        {
            "2022": 8,
            "2023": 9,
            "2024": 8,
            "2025": 8,
            "2026": 6,
        }
    )

    actual_years = Counter(row["year"] for row in plan)

    assert actual_years == expected_years, (
        f"Unexpected year distribution: {actual_years}"
    )

    file_names = []
    urls = []

    for row in plan:
        assert row["resolution_status"] == "RESOLVED"

        assert row["http_status"] == "200"

        file_name = row["resolved_file_name"]

        assert file_name.lower().endswith(".pdf")

        assert file_name

        expected_size = int(row["probe_bytes"])

        assert expected_size > 0

        expected_sha = row["probe_sha256"]

        assert len(expected_sha) == 64

        assert all(character in "0123456789abcdef" for character in expected_sha)

        url = row["source_url"]

        parsed = urlparse(url)

        assert parsed.scheme == "https"

        assert parsed.netloc == row["source_host"]

        assert parsed.netloc in {
            "archive.sbp.org.pk",
            "www.sbp.org.pk",
        }

        assert Path(parsed.path).name == file_name

        file_names.append(file_name)

        urls.append(url)

    assert len(set(file_names)) == EXPECTED_ROWS, (
        "Resolved MPC file names are not unique"
    )

    assert len(set(urls)) == EXPECTED_ROWS, "Resolved MPC URLs are not unique"

    return plan


def acquisition_source(
    host: str,
) -> str:
    """Describe the official SBP transport source."""

    if host == "archive.sbp.org.pk":
        return "SBP archive direct PDF"

    if host == "www.sbp.org.pk":
        return "SBP current-site direct PDF"

    raise RuntimeError(f"Unexpected SBP host: {host}")


def validate_raw_file(
    path: Path,
    row: dict[str, str],
) -> None:
    """Validate one frozen raw PDF against the approved plan."""

    raw = path.read_bytes()

    assert raw.startswith(b"%PDF"), f"Not a genuine PDF: {path.name}"

    expected_size = int(row["probe_bytes"])

    expected_sha = row["probe_sha256"]

    assert len(raw) == expected_size, (
        f"Size mismatch for {path.name}: expected {expected_size}, found {len(raw)}"
    )

    actual_sha = sha256_bytes(raw)

    assert actual_sha == expected_sha, (
        f"SHA-256 mismatch for {path.name}: expected {expected_sha}, found {actual_sha}"
    )


def validate_existing_provenance(
    row: dict[str, str],
    provenance_rows: list[dict[str, str]],
) -> bool:
    """Validate an existing provenance row for one statement."""

    file_name = row["resolved_file_name"]

    matches = [
        item
        for item in provenance_rows
        if (
            item["dataset_id"] == "SBP_MPC_EVENTS"
            and item["raw_file_name"] == file_name
        )
    ]

    if not matches:
        return False

    assert len(matches) == 1, f"Duplicate provenance rows for {file_name}"

    existing = matches[0]

    expected_path = (RAW_DIR / file_name).relative_to(PROJECT_ROOT).as_posix()

    assert existing["source_authority"] == "State Bank of Pakistan"

    assert existing["source_reference"] == row["source_url"]

    assert existing["raw_relative_path"] == expected_path

    assert existing["file_format"] == "pdf"

    assert existing["sha256"] == row["probe_sha256"]

    assert int(existing["file_size_bytes"]) == int(row["probe_bytes"])

    assert existing["status"] == "SUCCESS"

    return True


def append_provenance(
    row: dict[str, str],
) -> None:
    """Append one successful immutable raw-artifact provenance row."""

    file_name = row["resolved_file_name"]

    raw_path = RAW_DIR / file_name

    parsed = urlparse(row["source_url"])

    provenance_row = [
        "SBP_MPC_EVENTS",
        "State Bank of Pakistan",
        acquisition_source(parsed.netloc),
        row["source_url"],
        datetime.now(UTC).isoformat(),
        file_name,
        raw_path.relative_to(PROJECT_ROOT).as_posix(),
        "pdf",
        row["probe_sha256"],
        row["probe_bytes"],
        "SUCCESS",
        (
            "canonical MPC statement date "
            f"{row['event_date']}; "
            "official SBP monetary policy statement; "
            "raw PDF preserved unchanged"
        ),
    ]

    buffer = io.StringIO(newline="")

    writer = csv.writer(
        buffer,
        lineterminator="\r\n",
    )

    writer.writerow(provenance_row)

    encoded = buffer.getvalue().encode("utf-8")

    with PROVENANCE_PATH.open("ab") as file:
        file.write(encoded)

        file.flush()

        os.fsync(file.fileno())


def download_row(
    row: dict[str, str],
) -> Path:
    """Download one official statement into the immutable raw layer."""

    file_name = row["resolved_file_name"]

    destination = RAW_DIR / file_name

    temporary = destination.with_suffix(destination.suffix + ".part")

    assert not temporary.exists(), f"Unexpected part file: {temporary}"

    command = [
        "curl",
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        "60",
        "--user-agent",
        "Mozilla/5.0",
        "--write-out",
        "%{http_code}",
        row["source_url"],
        "--output",
        str(temporary),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    http_status = result.stdout.strip()

    try:
        assert result.returncode == 0, (
            f"curl failed for {file_name}: {result.stderr.strip()}"
        )

        assert http_status == "200", f"HTTP {http_status} for {file_name}"

        assert temporary.exists()

        validate_raw_file(
            temporary,
            row,
        )

        temporary.replace(destination)

        return destination

    except Exception:
        temporary.unlink(missing_ok=True)

        raise


def validate_preserved_exclusions(
    provenance_rows: list[dict[str, str]],
) -> set[str]:
    """Validate preserved wrong-document raw artifacts."""

    exclusions = read_csv(EXCLUSIONS_PATH)

    assert len(exclusions) == 4, (
        f"Expected 4 preserved exclusions, found {len(exclusions)}"
    )

    names: set[str] = set()

    for row in exclusions:
        file_name = row["excluded_file_name"]

        assert file_name not in names, f"Duplicate exclusion: {file_name}"

        path = RAW_DIR / file_name

        assert path.exists(), f"Missing preserved exclusion: {file_name}"

        raw = path.read_bytes()

        assert raw.startswith(b"%PDF"), f"Excluded artifact is not PDF: {file_name}"

        assert len(raw) == int(row["excluded_size_bytes"])

        assert sha256_file(path) == row["excluded_sha256"]

        matches = [
            item
            for item in provenance_rows
            if (
                item["dataset_id"] == row["provenance_dataset_id"]
                and item["raw_file_name"] == file_name
            )
        ]

        assert len(matches) == 1, (
            f"Expected one provenance row for excluded {file_name}"
        )

        provenance = matches[0]

        assert provenance["source_reference"] == row["excluded_source_url"]

        assert provenance["sha256"] == row["excluded_sha256"]

        assert int(provenance["file_size_bytes"]) == int(row["excluded_size_bytes"])

        assert provenance["status"] == "SUCCESS"

        names.add(file_name)

    return names


def preflight(
    plan: list[dict[str, str]],
) -> tuple[
    int,
    int,
    int,
]:
    """Audit current raw/provenance closure without downloading."""

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    part_files = list(RAW_DIR.glob("*.part"))

    assert not part_files, f"Unexpected .part files: {part_files}"

    provenance_rows = load_provenance()

    existing = 0
    missing = 0
    provenance_count = 0

    approved_names = {row["resolved_file_name"] for row in plan}

    physical_files = {
        path.name
        for path in RAW_DIR.iterdir()
        if (path.is_file() and path.name != ".gitkeep")
    }

    exclusion_names = validate_preserved_exclusions(provenance_rows)

    assert approved_names.isdisjoint(exclusion_names), (
        "Accepted and excluded raw files overlap"
    )

    unexpected = physical_files - approved_names - exclusion_names

    assert not unexpected, f"Unexpected raw MPC files: {sorted(unexpected)}"

    for row in plan:
        path = RAW_DIR / row["resolved_file_name"]

        has_provenance = validate_existing_provenance(
            row,
            provenance_rows,
        )

        if has_provenance:
            provenance_count += 1

        if path.exists():
            validate_raw_file(
                path,
                row,
            )

            existing += 1

            assert has_provenance, (
                f"Existing raw artifact has no matching provenance: {path.name}"
            )

        else:
            missing += 1

            assert not has_provenance, (
                f"Provenance exists without raw artifact: {row['resolved_file_name']}"
            )

    return (
        existing,
        missing,
        provenance_count,
    )


def acquire(
    plan: list[dict[str, str]],
) -> None:
    """Acquire every missing approved MPC statement."""

    provenance_rows = load_provenance()

    for index, row in enumerate(
        plan,
        start=1,
    ):
        file_name = row["resolved_file_name"]

        destination = RAW_DIR / file_name

        if destination.exists():
            validate_raw_file(
                destination,
                row,
            )

            assert validate_existing_provenance(
                row,
                provenance_rows,
            )

            print(f"[{index:02d}/{EXPECTED_ROWS}] EXISTING {file_name}")

            continue

        print(f"[{index:02d}/{EXPECTED_ROWS}] DOWNLOAD {file_name}")

        download_row(row)

        append_provenance(row)

        provenance_rows = load_provenance()

        assert validate_existing_provenance(
            row,
            provenance_rows,
        )


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=("Validate the approved MPC acquisition plan without downloading."),
    )

    args = parser.parse_args()

    plan = validate_plan()

    (
        existing,
        missing,
        provenance_count,
    ) = preflight(plan)

    print("===== SBP MPC ACQUISITION PREFLIGHT =====")

    print(
        "Approved events:",
        len(plan),
    )

    print(
        "Existing raw artifacts:",
        existing,
    )

    print(
        "Missing raw artifacts:",
        missing,
    )

    print(
        "Successful provenance rows:",
        provenance_count,
    )

    print("")
    print("===== YEAR DISTRIBUTION =====")

    years = Counter(row["year"] for row in plan)

    for year, count in sorted(years.items()):
        print(
            year,
            count,
        )

    if args.dry_run:
        print("")
        print(
            "Scheduled downloads:",
            missing,
        )

        print("")
        print("PASS: SBP MPC acquisition dry-run complete")

        return

    acquire(plan)

    (
        final_existing,
        final_missing,
        final_provenance,
    ) = preflight(plan)

    assert final_existing == EXPECTED_ROWS
    assert final_missing == 0
    assert final_provenance == EXPECTED_ROWS

    print("")
    print("===== SBP MPC ACQUISITION CLOSURE =====")

    print(
        "Raw artifacts:",
        final_existing,
    )

    print(
        "Missing:",
        final_missing,
    )

    print(
        "Provenance rows:",
        final_provenance,
    )

    print("")
    print("PASS: all approved SBP MPC statements acquired")


if __name__ == "__main__":
    main()
