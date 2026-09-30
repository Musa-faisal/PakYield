"""Freeze the standardized MUFAP PKISRV acquisition plan."""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "pkisrv_acquisition_plan.csv"

BASE_URL = "https://www.mufap.com.pk"

ENDPOINT = BASE_URL + "/WebRegulations/GetSecpFileById"

PAGE_URL = BASE_URL + "/WebRegulations/Index?Head=Pricing&title=PKRV%2FPKISRV%2FPKFRV"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": PAGE_URL,
    "X-Requested-With": "XMLHttpRequest",
}

PAKISTAN = ZoneInfo("Asia/Karachi")

FIELDS = [
    "observation_date",
    "api_date",
    "title",
    "file_name",
    "extension",
    "pk_id",
    "source_path",
    "source_url",
    "status",
    "notes",
]


def extract_rows(payload):
    """Return pricing records from MUFAP response."""

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in (
            "data",
            "Data",
            "result",
            "Result",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                return value

    raise RuntimeError("Unexpected MUFAP response structure")


def parse_api_date(raw):
    """Parse MUFAP API metadata timestamp."""

    match = re.search(
        r"/Date\((\d+)",
        str(raw),
    )

    if not match:
        return None

    milliseconds = int(match.group(1))

    return (
        datetime.fromtimestamp(
            milliseconds / 1000,
            tz=UTC,
        )
        .astimezone(PAKISTAN)
        .date()
    )


def parse_title_date(title):
    """Parse canonical observation date from PKISRV title."""

    match = re.fullmatch(
        r"PKISRV(\d{2})(\d{2})(20\d{2})",
        title.strip(),
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    day, month, year = match.groups()

    return datetime.strptime(
        f"{day}{month}{year}",
        "%d%m%Y",
    ).date()


def parse_file_date(file_name):
    """Parse observation date from PKISRV filename."""

    match = re.match(
        r"PKISRV(\d{2})(\d{2})(20\d{2})",
        file_name,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    day, month, year = match.groups()

    return datetime.strptime(
        f"{day}{month}{year}",
        "%d%m%Y",
    ).date()


def main() -> None:
    """Build the frozen standardized PKISRV metadata plan."""

    response = requests.post(
        ENDPOINT,
        data={
            "fk_HeaderSubMenuTabId": 46,
        },
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    rows = extract_rows(response.json())

    plan = []

    for row in rows:
        title = str(row.get("Title", "")).strip()

        if not title.upper().startswith("PKISRV"):
            continue

        observation_date = parse_title_date(title)

        if observation_date is None:
            continue

        if observation_date.isoformat() < "2025-02-03":
            continue

        file_path = str(
            row.get(
                "FilePath",
                "",
            )
        ).strip()

        file_name = Path(file_path).name

        file_date = parse_file_date(file_name)

        if file_date != observation_date:
            raise RuntimeError(f"Title/file date mismatch: {title} | {file_name}")

        api_date = parse_api_date(row.get("Date", ""))

        plan.append(
            {
                "observation_date": (observation_date.isoformat()),
                "api_date": (api_date.isoformat() if api_date else ""),
                "title": title,
                "file_name": file_name,
                "extension": (Path(file_name).suffix.lower()),
                "pk_id": str(
                    row.get(
                        "PkId",
                        row.get(
                            "PKId",
                            "",
                        ),
                    )
                ),
                "source_path": file_path,
                "source_url": urljoin(
                    BASE_URL,
                    file_path,
                ),
                "status": "READY",
                "notes": (
                    "API_DATE_DIFFERS"
                    if (api_date is not None and api_date != observation_date)
                    else ""
                ),
            }
        )

    plan.sort(
        key=lambda row: (
            row["observation_date"],
            row["file_name"],
        )
    )

    dates = [row["observation_date"] for row in plan]

    titles = [row["title"] for row in plan]

    files = [row["file_name"] for row in plan]

    assert len(plan) == 407
    assert len(set(dates)) == 407
    assert len(set(titles)) == 407
    assert len(set(files)) == 407

    assert dates[0] == "2025-02-03"
    assert dates[-1] == "2026-09-30"

    api_mismatches = sum(bool(row["notes"]) for row in plan)

    assert api_mismatches == 10

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(plan)

    temporary.replace(OUTPUT_PATH)

    extensions = Counter(row["extension"] for row in plan)

    years = Counter(row["observation_date"][:4] for row in plan)

    print("===== PKISRV ACQUISITION PLAN =====")
    print("Rows:", len(plan))
    print("Unique dates:", len(set(dates)))
    print("Start:", dates[0])
    print("End:", dates[-1])
    print(
        "API/date mismatches:",
        api_mismatches,
    )

    print("")
    print("===== EXTENSIONS =====")

    for extension, count in sorted(extensions.items()):
        print(
            extension,
            count,
        )

    print("")
    print("===== YEAR COUNTS =====")

    for year in sorted(years):
        print(
            year,
            years[year],
        )

    print("")
    print(
        "Plan:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )

    print("")
    print("PASS: PKISRV acquisition plan frozen")


if __name__ == "__main__":
    main()
