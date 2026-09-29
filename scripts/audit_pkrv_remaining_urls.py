"""Audit reachability of remaining approved PKRV source URLs."""

from __future__ import annotations

import csv
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

APPROVED_PLAN_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "pkrv_approved_acquisition_plan.csv"
)

PROVENANCE_PATH = PROJECT_ROOT / "data" / "manifests" / "raw_provenance.csv"

AUDIT_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_remaining_url_availability.csv"

RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "mufap" / "pkrv"

AUDIT_FIELDS = [
    "observation_date",
    "file_name",
    "source_url",
    "http_status",
    "content_type",
    "content_length",
    "result",
    "checked_at_utc",
    "error",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def write_csv(
    rows: list[dict[str, str]],
) -> None:
    """Write the availability audit atomically."""

    temporary = AUDIT_PATH.with_suffix(AUDIT_PATH.suffix + ".part")

    if temporary.exists():
        temporary.unlink()

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=AUDIT_FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(AUDIT_PATH)


def successful_paths() -> set[str]:
    """Return raw paths already backed by successful provenance."""

    rows = read_csv(PROVENANCE_PATH)

    return {
        row["raw_relative_path"]
        for row in rows
        if row["dataset_id"] == "PKRV" and row["status"] == "SUCCESS"
    }


def main() -> None:
    """Audit all approved PKRV URLs not yet acquired."""

    approved = read_csv(APPROVED_PLAN_PATH)

    completed = successful_paths()

    remaining: list[dict[str, str]] = []

    for row in approved:
        destination = RAW_DIRECTORY / row["file_name"]

        relative_path = destination.relative_to(PROJECT_ROOT).as_posix()

        if relative_path in completed:
            if not destination.is_file():
                raise RuntimeError(
                    f"Provenance exists without raw file: {relative_path}"
                )

            continue

        if destination.exists():
            raise RuntimeError(
                f"Raw file exists without successful provenance: {relative_path}"
            )

        remaining.append(row)

    print("===== REMAINING PKRV URL AUDIT =====")
    print(
        "Approved universe:",
        len(approved),
    )
    print(
        "Already acquired:",
        len(completed),
    )
    print(
        "Remaining URLs:",
        len(remaining),
    )
    print("")

    audit_rows: list[dict[str, str]] = []

    with requests.Session() as session:
        for index, row in enumerate(
            remaining,
            start=1,
        ):
            status = ""
            content_type = ""
            content_length = ""
            result = ""
            error = ""

            try:
                with session.get(
                    row["source_url"],
                    headers=HEADERS,
                    timeout=30,
                    stream=True,
                ) as response:
                    status = str(response.status_code)

                    content_type = response.headers.get(
                        "Content-Type",
                        "",
                    )

                    content_length = response.headers.get(
                        "Content-Length",
                        "",
                    )

                    if response.status_code == 200:
                        result = "AVAILABLE"
                    elif response.status_code == 404:
                        result = "HTTP_404"
                    else:
                        result = "HTTP_OTHER"

            except requests.RequestException as exc:
                result = "REQUEST_ERROR"
                error = f"{type(exc).__name__}: {exc}"

            audit_rows.append(
                {
                    "observation_date": row["observation_date"],
                    "file_name": row["file_name"],
                    "source_url": row["source_url"],
                    "http_status": status,
                    "content_type": content_type,
                    "content_length": content_length,
                    "result": result,
                    "checked_at_utc": (datetime.now(UTC).isoformat(timespec="seconds")),
                    "error": error,
                }
            )

            print(
                f"[{index:04d}/{len(remaining):04d}]",
                row["observation_date"],
                "|",
                status or "ERROR",
                "|",
                result,
                "|",
                row["file_name"],
            )

            time.sleep(0.05)

    write_csv(audit_rows)

    counts = Counter(row["result"] for row in audit_rows)

    print("")
    print("===== AVAILABILITY SUMMARY =====")

    for key in sorted(counts):
        print(f"{key}: {counts[key]}")

    unavailable = [row for row in audit_rows if row["result"] != "AVAILABLE"]

    print("")
    print(
        "Non-available rows:",
        len(unavailable),
    )

    for row in unavailable:
        print(
            row["observation_date"],
            "|",
            row["http_status"] or "ERROR",
            "|",
            row["result"],
            "|",
            row["file_name"],
        )

    print("")
    print(
        "Audit:",
        AUDIT_PATH.relative_to(PROJECT_ROOT),
    )

    print("PASS: URL availability audit completed without saving production artifacts")


if __name__ == "__main__":
    main()
