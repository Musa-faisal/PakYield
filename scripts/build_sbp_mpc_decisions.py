"""Extract and validate SBP MPC decisions from canonical statement PDFs."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PLAN_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_acquisition_plan.csv"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "sbp" / "mpc"

POLICY_RATE_PATH = (
    PROJECT_ROOT / "data" / "raw" / "sbp" / "policy_rate" / "data_series.csv"
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_decisions_validated.csv"

CROSSCHECK_PATH = (
    PROJECT_ROOT / "data" / "manifests" / "sbp_mpc_policy_rate_crosscheck.csv"
)

EXPECTED_EVENTS = 39
EXPECTED_CHANGES = 17

DECISION_FIELDS = [
    "event_date",
    "decision_direction",
    "change_bps",
    "announced_policy_rate",
    "effective_date",
    "effective_date_source",
    "source_file",
    "decision_text",
    "validation_status",
]

CROSSCHECK_FIELDS = [
    "event_date",
    "decision_direction",
    "statement_resulting_rate",
    "statement_rate_basis",
    "policy_observation_date",
    "policy_observation_value",
    "crosscheck_status",
]


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read a UTF-8 CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def extract_pdf_text(
    path: Path,
) -> str:
    """Extract embedded PDF text."""

    with pdfplumber.open(str(path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def normalize(
    text: str,
) -> str:
    """Normalize extraction artifacts without changing meaning."""

    replacements = {
        "\u00a0": " ",
        "–": "-",
        "—": "-",
        "’": "'",
        "“": '"',
        "”": '"',
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    # Normalize SBP's "w.e.f." abbreviation before decision-clause parsing.
    # pdfplumber may preserve backslashes before the dots, so support both
    # "w.e.f." and "w\.e\.f\." forms.
    text = re.sub(
        r"\bw(?:\\?\.)\s*e(?:\\?\.)\s*f(?:\\?\.)?",
        "with effect from",
        text,
        flags=re.IGNORECASE,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def decimal_string(
    value: Decimal,
) -> str:
    """Format Decimal without unnecessary trailing zeros."""

    rendered = format(
        value,
        "f",
    )

    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")

    return rendered


DECISION_PATTERNS = [
    (
        "RAISE",
        re.compile(
            r"(?P<decision>"
            r"(?:Monetary Policy Committee\s+\(MPC\)|"
            r"\bMPC\b|\bCommittee\b)"
            r".{0,220}?"
            r"\bdecided\b"
            r".{0,140}?"
            r"\b(?:raise|increase)\b"
            r"\s+the\s+policy\s+rate"
            r"\s+by\s+"
            r"(?P<bps>\d+(?:\.\d+)?)"
            r"\s*(?:basis\s+points?|bps)"
            r"\s+to\s+"
            r"(?P<rate>\d+(?:\.\d+)?)"
            r"\s*(?:percent|%)"
            r"(?P<tail>[^.]*\.)"
            r")",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "CUT",
        re.compile(
            r"(?P<decision>"
            r"(?:Monetary Policy Committee\s+\(MPC\)|"
            r"\bMPC\b|\bCommittee\b)"
            r".{0,220}?"
            r"\bdecided\b"
            r".{0,140}?"
            r"\b(?:cut|reduce|decrease)\b"
            r"\s+the\s+policy\s+rate"
            r"\s+by\s+"
            r"(?P<bps>\d+(?:\.\d+)?)"
            r"\s*(?:basis\s+points?|bps)"
            r"(?:"
            r"\s+to\s+"
            r"(?P<rate>\d+(?:\.\d+)?)"
            r"\s*(?:percent|%)"
            r")?"
            r"(?P<tail>[^.]*\.)"
            r")",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "HOLD",
        re.compile(
            r"(?P<decision>"
            r"(?:Monetary Policy Committee\s+\(MPC\)|"
            r"\bMPC\b|\bCommittee\b)"
            r".{0,220}?"
            r"\bdecided\b"
            r".{0,140}?"
            r"\b(?:maintain|keep)\b"
            r"\s+the\s+policy\s+rate"
            r"(?:\s+unchanged)?"
            r"\s+at\s+"
            r"(?P<rate>\d+(?:\.\d+)?)"
            r"\s*(?:percent|%)"
            r"(?P<tail>[^.]*\.)"
            r")",
            flags=re.IGNORECASE,
        ),
    ),
]


def extract_decision(
    text: str,
) -> tuple[
    str,
    Decimal,
    Decimal | None,
    str,
]:
    """Extract one current MPC decision clause."""

    matches: list[
        tuple[
            int,
            str,
            re.Match[str],
        ]
    ] = []

    for direction, pattern in DECISION_PATTERNS:
        for match in pattern.finditer(text):
            matches.append(
                (
                    match.start(),
                    direction,
                    match,
                )
            )

    assert matches, "No deterministic MPC decision clause found"

    matches.sort(key=lambda item: item[0])

    # The canonical statement should contain one
    # identifiable current decision. Historical discussion
    # later in the document must not supersede the first
    # direct decision clause.
    _, direction, match = matches[0]

    if direction == "HOLD":
        change_bps = Decimal("0")
    else:
        magnitude = Decimal(match.group("bps"))

        change_bps = magnitude if direction == "RAISE" else -magnitude

    rate_raw = match.groupdict().get("rate")

    announced_rate = Decimal(rate_raw) if rate_raw is not None else None

    decision_text = normalize(match.group("decision"))

    return (
        direction,
        change_bps,
        announced_rate,
        decision_text,
    )


def parse_human_date(
    raw: str,
) -> date:
    """Parse the date forms used in SBP decision clauses."""

    cleaned = normalize(raw)

    cleaned = re.sub(
        r"(\d{1,2})(?:st|nd|rd|th)\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE,
    )

    formats = [
        "%B %d, %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                cleaned,
                fmt,
            ).date()
        except ValueError:
            pass

    raise ValueError(f"Unsupported explicit effective date: {raw}")


def extract_effective_date(
    decision_text: str,
) -> tuple[
    date | None,
    str,
]:
    """Extract only an effective date explicitly stated by SBP."""

    patterns = [
        re.compile(
            r"\beffective\s+from\s+"
            r"(?P<date>"
            r"[A-Za-z]+\s+\d{1,2},\s+\d{4}"
            r")",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"\beffective\s+"
            r"(?P<date>"
            r"\d{1,2}(?:st|nd|rd|th)?"
            r"\s+[A-Za-z]+\s+\d{4}"
            r")",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"\bwith\s+effect\s+from\s+"
            r"(?P<date>"
            r"[A-Za-z]+\s+\d{1,2},\s+\d{4}"
            r")",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"\bw\\?\.?\s*e\\?\.?\s*f\\?\.?\s+"
            r"(?P<date>"
            r"[A-Za-z]+\s+\d{1,2},\s+\d{4}"
            r")",
            flags=re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.search(decision_text)

        if match:
            return (
                parse_human_date(match.group("date")),
                "STATEMENT_EXPLICIT",
            )

    return (
        None,
        "NOT_STATED",
    )


def parse_policy_date(
    raw: str,
) -> date:
    """Parse EasyData observation dates."""

    value = raw.strip()

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            ).date()
        except ValueError:
            pass

    raise ValueError(f"Unsupported EasyData date: {raw!r}")


def load_policy_rates() -> list[
    tuple[
        date,
        Decimal,
    ]
]:
    """Load the official EasyData policy-rate observations."""

    rows = read_csv(POLICY_RATE_PATH)

    observations = []

    for row in rows:
        observation_date = parse_policy_date(row["Observation Date"])

        if not (date(2022, 1, 1) <= observation_date <= date(2026, 12, 31)):
            continue

        observations.append(
            (
                observation_date,
                Decimal(row["Observation Value"]),
            )
        )

    observations.sort(key=lambda item: item[0])

    assert len(observations) == 17, (
        "Expected 17 official policy-rate observations "
        f"in 2022-2026, found {len(observations)}"
    )

    return observations


def build_decisions() -> list[dict[str, str]]:
    """Build the canonical validated MPC decision manifest."""

    plan = read_csv(PLAN_PATH)

    assert len(plan) == EXPECTED_EVENTS

    output = []

    running_rate: Decimal | None = None

    for index, row in enumerate(plan):
        event_date = date.fromisoformat(row["event_date"])

        source_file = row["resolved_file_name"]

        path = RAW_DIR / source_file

        assert path.exists()

        text = normalize(extract_pdf_text(path))

        assert "monetary policy statement" in text.lower()

        (
            direction,
            change_bps,
            announced_rate,
            decision_text,
        ) = extract_decision(text)

        (
            effective_date,
            effective_source,
        ) = extract_effective_date(decision_text)

        if index == 0:
            assert direction == "HOLD"
            assert announced_rate is not None

            running_rate = announced_rate

        else:
            assert running_rate is not None

            expected_rate = running_rate + (change_bps / Decimal("100"))

            if announced_rate is not None:
                assert announced_rate == expected_rate, (
                    f"Rate continuity failure on "
                    f"{event_date}: expected "
                    f"{expected_rate}, statement "
                    f"says {announced_rate}"
                )

                running_rate = announced_rate

            else:
                # Used only to validate continuity.
                # This value is deliberately NOT written
                # into announced_policy_rate.
                assert direction != "HOLD"

                running_rate = expected_rate

        if announced_rate is None:
            validation_status = "VALIDATED_CHANGE_ONLY_RATE_NOT_STATED"
        else:
            validation_status = "VALIDATED_EXPLICIT_RATE"

        output.append(
            {
                "event_date": event_date.isoformat(),
                "decision_direction": direction,
                "change_bps": decimal_string(change_bps),
                "announced_policy_rate": (
                    decimal_string(announced_rate) if announced_rate is not None else ""
                ),
                "effective_date": (
                    effective_date.isoformat() if effective_date is not None else ""
                ),
                "effective_date_source": effective_source,
                "source_file": source_file,
                "decision_text": decision_text,
                "validation_status": validation_status,
            }
        )

    assert len(output) == EXPECTED_EVENTS

    assert (
        sum(row["decision_direction"] != "HOLD" for row in output) == EXPECTED_CHANGES
    )

    missing_rates = [row for row in output if not row["announced_policy_rate"]]

    assert [row["event_date"] for row in missing_rates] == ["2025-12-15"]

    return output


def write_decisions(
    rows: list[dict[str, str]],
) -> None:
    """Write the validated decision manifest."""

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=DECISION_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(OUTPUT_PATH)


def build_crosscheck(
    decisions: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Cross-check every statement rate change against EasyData."""

    observations = load_policy_rates()

    changed = [row for row in decisions if row["decision_direction"] != "HOLD"]

    assert len(changed) == EXPECTED_CHANGES

    results = []

    previous_rate: Decimal | None = None

    for index, row in enumerate(decisions):
        event_date = date.fromisoformat(row["event_date"])

        announced_raw = row["announced_policy_rate"]

        change_bps = Decimal(row["change_bps"])

        if index == 0:
            assert announced_raw

            previous_rate = Decimal(announced_raw)

        else:
            assert previous_rate is not None

            validation_rate = (
                Decimal(announced_raw)
                if announced_raw
                else (previous_rate + (change_bps / Decimal("100")))
            )

            previous_rate = validation_rate

        if row["decision_direction"] == "HOLD":
            continue

        assert previous_rate is not None

        next_event_date = (
            date.fromisoformat(decisions[index + 1]["event_date"])
            if index + 1 < len(decisions)
            else date(
                2027,
                1,
                1,
            )
        )

        candidates = [
            (
                obs_date,
                obs_value,
            )
            for (
                obs_date,
                obs_value,
            ) in observations
            if (event_date <= obs_date < next_event_date)
        ]

        assert len(candidates) == 1, (
            f"Expected exactly one EasyData rate observation "
            f"after changed MPC event {event_date}, "
            f"found {candidates}"
        )

        (
            policy_date,
            policy_value,
        ) = candidates[0]

        assert policy_value == previous_rate, (
            f"EasyData mismatch for {event_date}: "
            f"statement sequence={previous_rate}, "
            f"EasyData={policy_value}"
        )

        explicit_effective = row["effective_date"]

        if explicit_effective:
            assert policy_date.isoformat() == explicit_effective, (
                f"Explicit effective-date mismatch "
                f"for {event_date}: statement "
                f"{explicit_effective}, EasyData "
                f"{policy_date}"
            )

        results.append(
            {
                "event_date": row["event_date"],
                "decision_direction": row["decision_direction"],
                "statement_resulting_rate": decimal_string(previous_rate),
                "statement_rate_basis": (
                    "EXPLICIT_STATEMENT"
                    if announced_raw
                    else ("SEQUENCE_DERIVED_FOR_VALIDATION_ONLY")
                ),
                "policy_observation_date": policy_date.isoformat(),
                "policy_observation_value": decimal_string(policy_value),
                "crosscheck_status": "MATCH",
            }
        )

    assert len(results) == EXPECTED_CHANGES

    assert all(row["crosscheck_status"] == "MATCH" for row in results)

    return results


def write_crosscheck(
    rows: list[dict[str, str]],
) -> None:
    """Write the EasyData cross-check manifest."""

    temporary = CROSSCHECK_PATH.with_suffix(CROSSCHECK_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CROSSCHECK_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(CROSSCHECK_PATH)


def main() -> None:
    """Build and validate both MPC decision artifacts."""

    decisions = build_decisions()

    write_decisions(decisions)

    crosscheck = build_crosscheck(decisions)

    write_crosscheck(crosscheck)

    print("===== SBP MPC DECISION EXTRACTION =====")

    print(
        "Events:",
        len(decisions),
    )

    print(
        "HOLD:",
        sum(row["decision_direction"] == "HOLD" for row in decisions),
    )

    print(
        "RAISE:",
        sum(row["decision_direction"] == "RAISE" for row in decisions),
    )

    print(
        "CUT:",
        sum(row["decision_direction"] == "CUT" for row in decisions),
    )

    print(
        "Explicit effective dates:",
        sum(bool(row["effective_date"]) for row in decisions),
    )

    print(
        "Missing announced rates:",
        sum(not row["announced_policy_rate"] for row in decisions),
    )

    print("")
    print("===== POLICY-RATE CROSSCHECK =====")

    print(
        "Changed MPC events:",
        len(crosscheck),
    )

    print(
        "EasyData matches:",
        sum(row["crosscheck_status"] == "MATCH" for row in crosscheck),
    )

    print("")
    print(
        "PASS: 39 MPC decisions parsed and 17 policy-rate changes independently matched"
    )


if __name__ == "__main__":
    main()
