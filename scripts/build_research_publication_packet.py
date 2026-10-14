"""Build a deterministic publication packet from the frozen research evidence map."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = PROJECT_ROOT / "data" / "interim" / "research_evidence_map.csv"

OUTPUT_PATH = PROJECT_ROOT / "docs" / "RESEARCH_PUBLICATION_SOURCE_PACKET.md"

EXPECTED_INPUT_SHA256 = (
    "50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002"
)

EXPECTED_ROWS = 24


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def clean_value(
    value: str | None,
) -> str:
    """Normalize a CSV value for deterministic Markdown rendering."""

    if value is None:
        return ""

    return (
        value.replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .strip()
        .replace(
            "\n",
            "<br>",
        )
    )


def load_evidence() -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Load and verify the frozen evidence map."""

    if not INPUT_PATH.is_file():
        raise RuntimeError(f"Missing frozen evidence map: {INPUT_PATH}")

    actual_sha = sha256_file(INPUT_PATH)

    if actual_sha != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"Frozen evidence-map SHA changed: {actual_sha}")

    with INPUT_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        headers = list(reader.fieldnames or [])

        rows = [
            {header: clean_value(row.get(header)) for header in headers}
            for row in reader
        ]

    if not headers:
        raise RuntimeError("Evidence map has no headers")

    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"Unexpected evidence-map row count: {len(rows)}")

    return (
        headers,
        rows,
    )


def build_packet(
    headers: list[str],
    rows: list[dict[str, str]],
) -> str:
    """Render the complete publication evidence packet."""

    lines = [
        "# PakYield Lab — Research Publication Source Packet",
        "",
        "**Status:** FROZEN-SOURCE PUBLICATION INPUT",
        "",
        "This document is generated deterministically from the frozen Phase 6D "
        "research evidence map.",
        "",
        "It is a publication-writing source packet, not a new empirical-analysis "
        "layer.",
        "",
        "## Frozen source",
        "",
        f"- Artifact: `{INPUT_PATH.relative_to(PROJECT_ROOT)}`",
        f"- Evidence rows: {len(rows)}",
        f"- SHA-256: `{EXPECTED_INPUT_SHA256}`",
        "",
        "## Publication evidence boundary",
        "",
        "The publication layer must preserve the evidentiary status of the frozen "
        "research outputs.",
        "",
        "It must not:",
        "",
        "- manufacture missing observations;",
        "- bypass frozen analytical eligibility rules;",
        "- convert descriptive evidence into inferential evidence;",
        "- reinterpret MPC announcement-window results as policy surprise;",
        "- convert numerical PKISRV-PKRV differences into structural, Islamic, "
        "Sukuk, Shariah, liquidity, credit, tax, or other premia without "
        "separate supporting evidence;",
        "- create causal monetary-policy claims from observational comparisons;",
        "- report statistical conclusions not supported by the frozen research "
        "artifacts.",
        "",
        "## Evidence-map schema",
        "",
    ]

    for index, header in enumerate(
        headers,
        start=1,
    ):
        lines.append(f"{index}. `{header}`")

    lines.extend(
        [
            "",
            "## Complete frozen evidence register",
            "",
        ]
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        lines.extend(
            [
                f"## Evidence Row {index:02d}",
                "",
            ]
        )

        for header in headers:
            value = row[header]

            if value:
                rendered = value
            else:
                rendered = "_blank_"

            lines.append(f"- **{header}:** {rendered}")

        lines.append("")

    lines.extend(
        [
            "## Publication-use rule",
            "",
            "Every substantive result statement in the research paper or research "
            "brief must be traceable to this packet or to another explicitly "
            "identified frozen project artifact.",
            "",
            "Interpretation must remain narrower than or equal to the evidence "
            "recorded here.",
            "",
        ]
    )

    return "\n".join(lines)


def write_packet(
    text: str,
) -> None:
    """Atomically write the publication packet."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(OUTPUT_PATH)


def main() -> None:
    """Build the deterministic publication source packet."""

    headers, rows = load_evidence()

    packet = build_packet(
        headers,
        rows,
    )

    write_packet(packet)

    try:
        display_path = OUTPUT_PATH.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = OUTPUT_PATH

    print("===== RESEARCH PUBLICATION SOURCE PACKET =====")

    print(
        "Evidence rows:",
        len(rows),
    )

    print(
        "Evidence columns:",
        len(headers),
    )

    print(
        "Input SHA256:",
        sha256_file(INPUT_PATH),
    )

    print(
        "Output:",
        display_path,
    )

    print(
        "Output SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("PASS: deterministic publication source packet constructed")


if __name__ == "__main__":
    main()
