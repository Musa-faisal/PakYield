"""Resolve canonical SBP MPC events to official statement PDF URLs."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]

UNIVERSE_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_event_universe.csv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_acquisition_plan.csv"

ARCHIVE_HOST = "archive.sbp.org.pk"
CURRENT_HOST = "www.sbp.org.pk"

OUTPUT_FIELDS = [
    "event_date",
    "year",
    "statement_title",
    "resolved_file_name",
    "source_host",
    "source_url",
    "http_status",
    "probe_bytes",
    "probe_sha256",
    "resolution_status",
    "notes",
]


def sha256_bytes(raw: bytes) -> str:
    """Return SHA-256 for bytes."""

    return hashlib.sha256(raw).hexdigest()


def month_variants(
    event_date: date,
) -> list[str]:
    """Return conservative month-case variants."""

    base = event_date.strftime("%b")

    variants = [
        base,
        base.upper(),
        base.lower(),
    ]

    # Historic SBP filenames occasionally contain
    # inconsistent capitalization.
    if base == "Jul":
        variants.extend(
            [
                "JuL",
                "JUL",
            ]
        )

    if base == "Sep":
        variants.extend(
            [
                "SEP",
                "SeP",
            ]
        )

    if base == "Oct":
        variants.extend(
            [
                "OCT",
                "OcT",
            ]
        )

    return list(dict.fromkeys(variants))


def candidate_urls(
    event_date: date,
) -> list[str]:
    """Generate plausible official SBP document URLs."""

    year = event_date.year
    day = event_date.day

    candidates: list[str] = []

    canonical_document_overrides = {
        date(2022, 7, 7): (
            "archive.sbp.org.pk",
            "/m_policy/2022/MPS-Jul-2022-Eng.pdf",
        ),
        date(2023, 1, 23): (
            "archive.sbp.org.pk",
            "/press/2023/Pr1-23-Jan-2023.pdf",
        ),
        date(2023, 6, 26): (
            "archive.sbp.org.pk",
            "/press/2023/Pr-26-Jun-2023-2.pdf",
        ),
        date(2024, 9, 12): (
            "archive.sbp.org.pk",
            "/m_policy/2024/MPS-Sep-2024-Eng.pdf",
        ),
    }

    override = canonical_document_overrides.get(event_date)

    if override is not None:
        host, relative_path = override

        candidates.append("https" + "://" + host + relative_path)

    current_asset_names = {
        date(2026, 7, 27): "MPS-July-2026-Eng.pdf",
        date(2026, 9, 14): "MPS-Sep-2026-Eng.pdf",
    }

    current_asset_name = current_asset_names.get(event_date)

    if current_asset_name is not None:
        candidates.append(
            "https"
            + "://"
            + CURRENT_HOST
            + "/assets/document/publications/"
            + current_asset_name
        )

    for month in month_variants(event_date):
        filename = f"Pr-{day:02d}-{month}-{year}.pdf"

        filename_with_suffix = f"Pr-{day:02d}-{month}-{year}-1.pdf"

        for host in (
            ARCHIVE_HOST,
            CURRENT_HOST,
        ):
            candidates.append("https" + "://" + host + f"/press/{year}/" + filename)

            candidates.append(
                "https" + "://" + host + f"/press/{year}/" + filename_with_suffix
            )

    month = event_date.strftime("%b")

    mps_filename = f"MPS-{month}-{year}-Eng.pdf"

    for host in (
        ARCHIVE_HOST,
        CURRENT_HOST,
    ):
        candidates.append("https" + "://" + host + f"/m_policy/{year}/" + mps_filename)

    return list(dict.fromkeys(candidates))


def probe_url(
    url: str,
) -> tuple[
    bool,
    str,
    int,
    str,
]:
    """Probe URL and accept only genuine PDF bytes."""

    with tempfile.NamedTemporaryFile(
        prefix="pakyield_mpc_probe_",
        suffix=".bin",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        command = [
            "curl",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            "20",
            "--user-agent",
            "Mozilla/5.0",
            "--write-out",
            "%{http_code}",
            url,
            "--output",
            str(temp_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        http_status = result.stdout.strip() or "CURL_ERROR"

        if not temp_path.exists():
            return (
                False,
                http_status,
                0,
                "",
            )

        raw = temp_path.read_bytes()

        if not raw.startswith(b"%PDF"):
            return (
                False,
                http_status,
                len(raw),
                "",
            )

        return (
            True,
            http_status,
            len(raw),
            sha256_bytes(raw),
        )

    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    """Resolve all canonical MPC events."""

    with UNIVERSE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        universe = list(csv.DictReader(file))

    assert len(universe) == 39

    results: list[dict[str, str]] = []

    for index, row in enumerate(
        universe,
        start=1,
    ):
        event_date = date.fromisoformat(row["event_date"])

        print("")
        print(
            f"[{index:02d}/39]",
            event_date.isoformat(),
        )

        resolved_url = ""
        resolved_status = ""
        resolved_bytes = 0
        resolved_sha = ""

        attempted = 0

        for url in candidate_urls(event_date):
            attempted += 1

            (
                is_pdf,
                http_status,
                byte_count,
                digest,
            ) = probe_url(url)

            if is_pdf:
                resolved_url = url
                resolved_status = http_status
                resolved_bytes = byte_count
                resolved_sha = digest

                print(
                    "  RESOLVED:",
                    url,
                )

                print(
                    "  bytes:",
                    byte_count,
                )

                break

        if resolved_url:
            parsed = urlparse(resolved_url)

            file_name = Path(parsed.path).name

            host = parsed.netloc

            status = "RESOLVED"

            notes = f"genuine PDF magic bytes; {attempted} candidate(s) tested"

        else:
            file_name = ""
            host = ""
            status = "UNRESOLVED"

            notes = f"no genuine PDF found after {attempted} official URL candidates"

            print(
                "  UNRESOLVED after",
                attempted,
                "candidate(s)",
            )

        results.append(
            {
                "event_date": row["event_date"],
                "year": row["year"],
                "statement_title": row["statement_title"],
                "resolved_file_name": file_name,
                "source_host": host,
                "source_url": resolved_url,
                "http_status": resolved_status,
                "probe_bytes": (str(resolved_bytes) if resolved_url else ""),
                "probe_sha256": resolved_sha,
                "resolution_status": status,
                "notes": notes,
            }
        )

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_FIELDS,
        )

        writer.writeheader()
        writer.writerows(results)

    temporary.replace(OUTPUT_PATH)

    resolved = [row for row in results if row["resolution_status"] == "RESOLVED"]

    unresolved = [row for row in results if row["resolution_status"] == "UNRESOLVED"]

    print("")
    print("===== SBP MPC URL RESOLUTION =====")

    print(
        "Universe:",
        len(results),
    )

    print(
        "Resolved:",
        len(resolved),
    )

    print(
        "Unresolved:",
        len(unresolved),
    )

    print("")
    print("===== RESOLVED BY YEAR =====")

    for year in range(
        2022,
        2027,
    ):
        count = sum(1 for row in resolved if row["year"] == str(year))

        print(
            year,
            count,
        )

    print("")
    print("===== UNRESOLVED EVENTS =====")

    for row in unresolved:
        print(
            row["event_date"],
            "|",
            row["statement_title"],
        )

    print("")
    print(
        "Plan:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )

    print("")
    print("PASS: SBP MPC URL resolution probe complete")


if __name__ == "__main__":
    main()
