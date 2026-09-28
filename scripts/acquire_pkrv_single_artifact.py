"""Acquire one official MUFAP PKRV artifact with provenance."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from pakyield.config import PKRV_SAMPLE_START
from pakyield.ingestion.provenance import file_size_bytes, sha256_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_URL = "https://www.mufap.com.pk/WebRegulations/GetSecpFileById"

BASE_URL = "https://www.mufap.com.pk"

API_PAYLOAD = {
    "fk_HeaderSubMenuTabId": 46,
}

TARGET_TITLE = f"PKRV{PKRV_SAMPLE_START:%d%m%Y}"

RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkrv"

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

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
    "Accept": ("application/json, text/javascript, */*; q=0.01"),
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": (
        "https://www.mufap.com.pk/"
        "WebRegulations/Index"
        "?Head=Pricing"
        "&title=PKRV%2FPKISRV%2FPKFRV"
    ),
}


def fetch_source_metadata(
    session: requests.Session,
) -> dict[str, object]:
    """Return the unique MUFAP metadata row for the target PKRV date."""

    response = session.post(
        API_URL,
        json=API_PAYLOAD,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    rows = payload.get("data")

    if not isinstance(rows, list):
        raise RuntimeError("MUFAP API response does not contain a data list")

    matches = [
        row for row in rows if str(row.get("Title", "")).strip().upper() == TARGET_TITLE
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {TARGET_TITLE} record; found {len(matches)}"
        )

    return matches[0]


def initialize_provenance_manifest() -> None:
    """Create the provenance manifest with its accepted schema if needed."""

    PROVENANCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PROVENANCE_PATH.exists():
        with PROVENANCE_PATH.open(
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.reader(file)
            header = next(reader, None)

        if header != PROVENANCE_FIELDS:
            raise RuntimeError("Existing provenance manifest has an unexpected schema")

        return

    with PROVENANCE_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=PROVENANCE_FIELDS,
        )
        writer.writeheader()


def append_provenance(
    *,
    source_url: str,
    destination: Path,
    content_type: str,
) -> None:
    """Append one successful acquisition record."""

    checksum = sha256_file(destination)
    size = file_size_bytes(destination)

    relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

    with PROVENANCE_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        existing_rows = list(csv.DictReader(file))

    if any(
        row["raw_relative_path"] == relative_path and row["status"] == "SUCCESS"
        for row in existing_rows
    ):
        raise RuntimeError(f"Successful provenance already exists for {relative_path}")

    record = {
        "dataset_id": "PKRV",
        "source_authority": "MUFAP",
        "acquisition_source": "MUFAP current pricing API",
        "source_reference": source_url,
        "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "raw_file_name": destination.name,
        "raw_relative_path": relative_path,
        "file_format": destination.suffix.lstrip(".").lower(),
        "sha256": checksum,
        "file_size_bytes": str(size),
        "status": "SUCCESS",
        "notes": (f"title={TARGET_TITLE}; api={API_URL}; content_type={content_type}"),
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


def main() -> None:
    """Acquire one raw PKRV observation without transformation."""

    print("===== PKRV SINGLE-ARTIFACT ACQUISITION =====")
    print("Target:", TARGET_TITLE)

    RAW_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    initialize_provenance_manifest()

    with requests.Session() as session:
        metadata = fetch_source_metadata(session)

        source_path = str(metadata.get("FilePath", "")).strip()

        if not source_path:
            raise RuntimeError("MUFAP metadata does not contain FilePath")

        source_url = urljoin(
            BASE_URL,
            source_path,
        )

        source_name = Path(urlparse(source_url).path).name

        if not source_name:
            raise RuntimeError("Could not determine source filename")

        destination = RAW_DIRECTORY / source_name
        temporary = destination.with_name(destination.name + ".part")

        if destination.exists():
            raise FileExistsError(
                "Raw artifact already exists and will not "
                f"be overwritten: {destination}"
            )

        if temporary.exists():
            raise FileExistsError(
                f"Temporary acquisition file already exists: {temporary}"
            )

        print("Source URL:", source_url)
        print("Destination:", destination)

        response = session.get(
            source_url,
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        content = response.content

        if not content:
            raise RuntimeError("MUFAP returned an empty artifact")

        if "text/html" in content_type.lower():
            raise RuntimeError("MUFAP returned HTML instead of the raw artifact")

        temporary.write_bytes(content)
        temporary.rename(destination)

    append_provenance(
        source_url=source_url,
        destination=destination,
        content_type=content_type,
    )

    print("")
    print("ACQUISITION: SUCCESS")
    print("Title:", TARGET_TITLE)
    print("File:", destination.name)
    print(
        "Size:",
        file_size_bytes(destination),
        "bytes",
    )
    print(
        "SHA256:",
        sha256_file(destination),
    )
    print(
        "Provenance:",
        PROVENANCE_PATH.relative_to(PROJECT_ROOT),
    )


if __name__ == "__main__":
    main()
