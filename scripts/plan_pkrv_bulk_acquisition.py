"""Build the PKRV bulk-acquisition plan without downloading raw artifacts."""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from pakyield.config import PKRV_SAMPLE_START

PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_URL = "https://www.mufap.com.pk/WebRegulations/GetSecpFileById"
BASE_URL = "https://www.mufap.com.pk"

API_PAYLOAD = {
    "fk_HeaderSubMenuTabId": 46,
}

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_bulk_acquisition_plan.csv"

ANOMALY_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_bulk_anomalies.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": (
        "https://www.mufap.com.pk/"
        "WebRegulations/Index"
        "?Head=Pricing"
        "&title=PKRV%2FPKISRV%2FPKFRV"
    ),
}

TITLE_PATTERN = re.compile(r"^PKRV\s*(?P<day>\d{2})(?P<month>\d{2})(?P<year>20\d{2})$")

PLAN_FIELDS = [
    "metadata_index",
    "observation_date",
    "year",
    "title",
    "source_path",
    "source_url",
    "file_name",
    "file_extension",
    "duplicate_count",
    "title_date_in_path",
    "status",
    "anomaly_codes",
    "plan_generated_at_utc",
]


def fetch_metadata() -> list[dict[str, object]]:
    """Fetch the current MUFAP pricing-file metadata."""

    response = requests.post(
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

    return rows


def parse_pkrv_date(title: str) -> date | None:
    """Parse a daily PKRV title such as PKRV04012022."""

    match = TITLE_PATTERN.fullmatch(title.strip().upper())

    if match is None:
        return None

    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    """Write a manifest atomically."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(path.suffix + ".part")

    if temporary.exists():
        temporary.unlink()

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=PLAN_FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def main() -> None:
    """Build the reproducible bulk-acquisition plan."""

    source_rows = fetch_metadata()

    candidates: list[dict[str, object]] = []

    for metadata_index, row in enumerate(source_rows):
        title = str(row.get("Title", "")).strip()

        observation_date = parse_pkrv_date(title)

        if observation_date is None:
            continue

        if observation_date < PKRV_SAMPLE_START:
            continue

        if observation_date.year > 2026:
            continue

        source_path = str(row.get("FilePath", "")).strip()

        if not source_path:
            raise RuntimeError(f"Missing FilePath for {title}")

        source_url = urljoin(
            BASE_URL,
            source_path,
        )

        file_name = Path(urlparse(source_url).path).name

        extension = Path(file_name).suffix.lower()

        candidates.append(
            {
                "metadata_index": metadata_index,
                "observation_date": observation_date,
                "year": observation_date.year,
                "title": title,
                "source_path": source_path,
                "source_url": source_url,
                "file_name": file_name,
                "file_extension": extension,
            }
        )

    if not candidates:
        raise RuntimeError("No PKRV candidates found")

    date_counts = Counter(item["observation_date"] for item in candidates)

    generated_at = datetime.now(UTC).isoformat(timespec="seconds")

    plan_rows: list[dict[str, object]] = []

    for item in candidates:
        observation_date = item["observation_date"]

        assert isinstance(
            observation_date,
            date,
        )

        source_path = str(item["source_path"])

        date_token = observation_date.strftime("%d%m%Y")

        duplicate_count = date_counts[observation_date]

        title_date_in_path = date_token in source_path

        extension = str(item["file_extension"])

        anomalies: list[str] = []

        if duplicate_count > 1:
            anomalies.append("DUPLICATE_OBSERVATION_DATE")

        if not title_date_in_path:
            anomalies.append("TITLE_DATE_NOT_IN_FILEPATH")

        if extension != ".csv":
            anomalies.append("NON_CSV_ARTIFACT")

        status = "READY" if not anomalies else "REVIEW"

        plan_rows.append(
            {
                "metadata_index": item["metadata_index"],
                "observation_date": (observation_date.isoformat()),
                "year": item["year"],
                "title": item["title"],
                "source_path": source_path,
                "source_url": item["source_url"],
                "file_name": item["file_name"],
                "file_extension": extension,
                "duplicate_count": (duplicate_count),
                "title_date_in_path": (str(title_date_in_path).upper()),
                "status": status,
                "anomaly_codes": ";".join(anomalies),
                "plan_generated_at_utc": (generated_at),
            }
        )

    plan_rows.sort(
        key=lambda row: (
            row["observation_date"],
            int(str(row["metadata_index"])),
        )
    )

    anomaly_rows = [row for row in plan_rows if row["status"] == "REVIEW"]

    write_csv(
        PLAN_PATH,
        plan_rows,
    )

    write_csv(
        ANOMALY_PATH,
        anomaly_rows,
    )

    year_counts = Counter(int(str(row["year"])) for row in plan_rows)

    status_counts = Counter(str(row["status"]) for row in plan_rows)

    extension_counts = Counter(str(row["file_extension"]) for row in plan_rows)

    unique_dates = {str(row["observation_date"]) for row in plan_rows}

    duplicate_dates = {
        str(row["observation_date"])
        for row in plan_rows
        if int(str(row["duplicate_count"])) > 1
    }

    print("===== PKRV BULK ACQUISITION PLAN =====")

    print(
        "Metadata rows from API:",
        len(source_rows),
    )

    print(
        "PKRV candidate rows:",
        len(plan_rows),
    )

    print(
        "Unique observation dates:",
        len(unique_dates),
    )

    print(
        "Duplicate observation dates:",
        len(duplicate_dates),
    )

    print("")

    print("===== YEAR COUNTS =====")

    for year in sorted(year_counts):
        print(f"{year}: {year_counts[year]}")

    print("")

    print("===== FILE EXTENSIONS =====")

    for extension in sorted(extension_counts):
        print(f"{extension or '<none>'}: {extension_counts[extension]}")

    print("")

    print("===== PLAN STATUS =====")

    for status in ("READY", "REVIEW"):
        print(f"{status}: {status_counts[status]}")

    print("")

    print("===== ANOMALIES =====")

    print(
        "Rows requiring review:",
        len(anomaly_rows),
    )

    for row in anomaly_rows:
        print(
            row["observation_date"],
            "|",
            row["title"],
            "|",
            row["file_name"],
            "|",
            row["anomaly_codes"],
        )

    print("")

    print(
        "Plan:",
        PLAN_PATH.relative_to(PROJECT_ROOT),
    )

    print(
        "Anomalies:",
        ANOMALY_PATH.relative_to(PROJECT_ROOT),
    )

    print("PASS: acquisition plan created; no raw artifacts downloaded")


if __name__ == "__main__":
    main()
