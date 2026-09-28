"""Resolve reviewed PKRV metadata and build the approved acquisition universe."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_bulk_acquisition_plan.csv"

ANOMALY_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_bulk_anomalies.csv"

RESOLUTION_PATH = PROJECT_ROOT / "data" / "manifests" / "pkrv_anomaly_resolution.csv"

APPROVED_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "pkrv_approved_acquisition_plan.csv"
)

RESOLUTION_FIELDS = [
    "observation_date",
    "file_name",
    "decision",
    "resolution_reason",
    "probe_sha256",
]

RESOLUTIONS = {
    "PKRV300320221960.csv": (
        "KEEP",
        (
            "Byte-identical duplicate; canonical 20-tenor PKRV; "
            "lower metadata index selected deterministically."
        ),
        "410745b152cbffc5240b5023731a0a74548f91aeefb6bca999e7e8ba38d99942",
    ),
    "PKRV300320221963.csv": (
        "REJECT",
        (
            "Byte-identical duplicate of selected 2022-03-30 artifact; "
            "redundant metadata entry."
        ),
        "410745b152cbffc5240b5023731a0a74548f91aeefb6bca999e7e8ba38d99942",
    ),
    "PKRV310320221961.csv": (
        "KEEP",
        (
            "Byte-identical duplicate; contains complete 20-tenor PKRV "
            "curve plus trailing blank row; lower metadata index selected."
        ),
        "e5972957b8090e959fc7c319e2c7bd29e6a17c622ee436c369f31ea410ee702f",
    ),
    "PKRV310320221962.csv": (
        "REJECT",
        (
            "Byte-identical duplicate of selected 2022-03-31 artifact; "
            "redundant metadata entry."
        ),
        "e5972957b8090e959fc7c319e2c7bd29e6a17c622ee436c369f31ea410ee702f",
    ),
    "PKRV24072023833.csv": (
        "REJECT",
        (
            "Metadata title says 2024 but filepath contains 2023; artifact "
            "is an old-style dealer/rate sheet, not canonical daily PKRV."
        ),
        "91bfcc8f41c9ec8bfcf62ca0861d81aadd16c3aa32a6cc340a06f0263c42fdd9",
    ),
    "PKRV24072024679.csv": (
        "KEEP",
        "Canonical 20-tenor PKRV CSV for 2024-07-24.",
        "d714e3e8b824b2d66990e7fdee5e72d09836769ed63a8ca16689b09c0154caae",
    ),
    "PKRV0208020241026.csv": (
        "KEEP",
        (
            "Canonical 20-tenor PKRV CSV; filename contains a malformed "
            "date token but source contents and metadata identify 2024-08-02."
        ),
        "053e052b62fee03be0f346962f2b16ad99751d18087c69f36f0a9e5ca1a9d9c9",
    ),
    "PKISRV230920241327.csv": (
        "REJECT",
        (
            "Artifact is GOP Ijarah Sukuk revaluation / PKISRV content, "
            "not the conventional PKRV curve."
        ),
        "73ef6b5b40ebd0e50a61bc5eab68107254931bd569ae3acbd6dd19e66c12b19c",
    ),
    "PKRV230920241328.csv": (
        "KEEP",
        "Canonical 20-tenor PKRV CSV for 2024-09-23.",
        "01fe94fdcc02e1e45efe0d5fd7244b6c651f5ded7fb41bc8461c300bc397e2fb",
    ),
    "PKRV060120253092.csv": (
        "REJECT",
        "MUFAP metadata entry resolves to HTTP 404; no production artifact.",
        "",
    ),
    "PKRV060120253224.csv": (
        "KEEP",
        "HTTP 200 canonical 20-tenor PKRV CSV for 2025-01-06.",
        "51e6ad2451cc5bf83aecba98f53475215303abe1efac387834e7a1d89f1e4ebe",
    ),
    "PKRV2008202523896.xlsx": (
        "KEEP",
        (
            "Valid XLSX workbook with sheet PKRV20082025 and complete "
            "canonical 20-tenor Tenor/Mid Rate/Change structure."
        ),
        "104e2ffeb2ed1a4cde320c2e9903c98e6d55212154d82e9975fff78b0af742e1",
    ),
    "PKRV1803202624793.xls": (
        "KEEP",
        (
            "File uses .xls extension but contains Spreadsheet XML; "
            "verified complete canonical 20-tenor PKRV curve."
        ),
        "5e7d2bee7450fbbbefb30cc9fe5263fcdf01754e0f430f5162d93dcc990fdfd3",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV manifest."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Write a CSV manifest atomically."""

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
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def main() -> None:
    """Resolve reviewed metadata and create one approved artifact per date."""

    plan_rows = read_csv(PLAN_PATH)
    anomaly_rows = read_csv(ANOMALY_PATH)

    anomaly_names = {row["file_name"] for row in anomaly_rows}

    resolution_names = set(RESOLUTIONS)

    if anomaly_names != resolution_names:
        missing = sorted(anomaly_names - resolution_names)
        unexpected = sorted(resolution_names - anomaly_names)

        raise RuntimeError(
            "Resolution mapping does not exactly match anomaly manifest. "
            f"Missing={missing}; unexpected={unexpected}"
        )

    resolution_rows = []

    for row in anomaly_rows:
        file_name = row["file_name"]

        decision, reason, checksum = RESOLUTIONS[file_name]

        resolution_rows.append(
            {
                "observation_date": row["observation_date"],
                "file_name": file_name,
                "decision": decision,
                "resolution_reason": reason,
                "probe_sha256": checksum,
            }
        )

    approved_rows = []

    for row in plan_rows:
        status = row["status"]
        file_name = row["file_name"]

        if status == "READY":
            selected = dict(row)
            selected["selection_basis"] = "AUTO_READY"
            selected["selection_note"] = "No metadata anomaly detected."
            approved_rows.append(selected)
            continue

        if status != "REVIEW":
            raise RuntimeError(f"Unexpected plan status: {status}")

        decision, reason, _ = RESOLUTIONS[file_name]

        if decision == "KEEP":
            selected = dict(row)
            selected["selection_basis"] = "ANOMALY_RESOLUTION"
            selected["selection_note"] = reason
            approved_rows.append(selected)

    approved_rows.sort(key=lambda row: row["observation_date"])

    plan_fields = list(plan_rows[0].keys())

    approved_fields = [
        *plan_fields,
        "selection_basis",
        "selection_note",
    ]

    write_csv(
        RESOLUTION_PATH,
        RESOLUTION_FIELDS,
        resolution_rows,
    )

    write_csv(
        APPROVED_PATH,
        approved_fields,
        approved_rows,
    )

    decision_counts = Counter(row["decision"] for row in resolution_rows)

    extension_counts = Counter(row["file_extension"] for row in approved_rows)

    dates = [row["observation_date"] for row in approved_rows]

    print("===== PKRV ANOMALY RESOLUTION =====")
    print(
        "Reviewed rows:",
        len(resolution_rows),
    )
    print(
        "KEEP:",
        decision_counts["KEEP"],
    )
    print(
        "REJECT:",
        decision_counts["REJECT"],
    )

    print("")
    print("===== APPROVED PKRV UNIVERSE =====")
    print(
        "Approved artifacts:",
        len(approved_rows),
    )
    print(
        "Unique dates:",
        len(set(dates)),
    )
    print(
        "First date:",
        min(dates),
    )
    print(
        "Last date:",
        max(dates),
    )

    print("")
    print("===== APPROVED FILE TYPES =====")

    for extension in sorted(extension_counts):
        print(f"{extension}: {extension_counts[extension]}")

    print("")
    print(
        "Resolution manifest:",
        RESOLUTION_PATH.relative_to(PROJECT_ROOT),
    )
    print(
        "Approved plan:",
        APPROVED_PATH.relative_to(PROJECT_ROOT),
    )


if __name__ == "__main__":
    main()
