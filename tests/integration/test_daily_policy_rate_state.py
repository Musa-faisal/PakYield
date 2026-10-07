"""Integration tests for deterministic daily SBP policy-rate state."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
)
from pakyield.database.connection import (
    get_connection,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_daily_policy_rate_state.py"

EXPECTED_SHA256 = "7655ddc7fd5cfd051ce628f006d8c4851b54ee47d4cbd90760e86cf9ebfd368a"

EXPECTED_HEADERS = [
    "date",
    "policy_rate_pct",
    "source_effective_date",
    "is_source_effective_date",
    "source_organization",
    "source_file",
]

EXPECTED_STATE_COUNTS = {
    "2021-12-15": 94,
    "2022-04-08": 46,
    "2022-05-24": 50,
    "2022-07-13": 138,
    "2022-11-28": 57,
    "2023-01-24": 38,
    "2023-03-03": 33,
    "2023-04-05": 83,
    "2023-06-27": 350,
    "2024-06-11": 49,
    "2024-07-30": 45,
    "2024-09-13": 53,
    "2024-11-05": 42,
    "2024-12-17": 42,
    "2025-01-28": 98,
    "2025-05-06": 224,
    "2025-12-16": 133,
    "2026-04-28": 156,
}


def load_builder_module() -> ModuleType:
    """Load the daily policy-state builder."""

    spec = importlib.util.spec_from_file_location(
        "build_daily_policy_rate_state",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()


def read_generated(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one generated daily-state CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        headers = list(reader.fieldnames or [])

        rows = list(reader)

    return (
        headers,
        rows,
    )


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Run the builder into an isolated output location."""

    output_path = tmp_path / file_name

    monkeypatch.setattr(
        BUILDER,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        BUILDER,
        "OUTPUT_PATH",
        output_path,
    )

    BUILDER.main()

    assert output_path.is_file()

    return output_path


def official_policy_rows() -> list[object]:
    """Return the frozen official policy observations."""

    connection = get_connection(DATABASE_PATH)

    try:
        return connection.execute(
            """
            SELECT
                effective_date,
                rate_pct,
                source_organization,
                source_file
            FROM policy_rate_observations
            ORDER BY effective_date
            """
        ).fetchall()

    finally:
        connection.close()


def test_daily_policy_state_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generated state must contain every calendar day exactly once."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "daily_state.csv",
    )

    (
        headers,
        rows,
    ) = read_generated(output_path)

    assert headers == EXPECTED_HEADERS

    assert len(rows) == 1731

    assert rows[0]["date"] == "2022-01-04"

    assert rows[-1]["date"] == "2026-09-30"

    parsed_dates = [date.fromisoformat(row["date"]) for row in rows]

    expected_date = date(
        2022,
        1,
        4,
    )

    for actual_date in parsed_dates:
        assert actual_date == expected_date

        expected_date += timedelta(days=1)

    assert (
        dict(Counter(row["source_effective_date"] for row in rows))
        == EXPECTED_STATE_COUNTS
    )

    assert sum(row["is_source_effective_date"] == "1" for row in rows) == 17

    assert {row["source_organization"] for row in rows} == {
        "State Bank of Pakistan",
    }

    assert {row["source_file"] for row in rows} == {
        "data_series.csv",
    }

    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_each_daily_state_equals_latest_official_effective_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every day must use the latest official rate effective by that date."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "latest_effective.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    policy = official_policy_rows()

    assert len(policy) == 18

    pointer = 0

    for row in rows:
        state_date = date.fromisoformat(row["date"])

        while (
            pointer + 1 < len(policy)
            and date.fromisoformat(policy[pointer + 1]["effective_date"]) <= state_date
        ):
            pointer += 1

        source = policy[pointer]

        assert row["source_effective_date"] == source["effective_date"]

        assert Decimal(row["policy_rate_pct"]) == Decimal(str(source["rate_pct"]))


def test_all_union_yield_dates_have_exact_policy_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every normalized market date must resolve to the correct policy state."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "yield_dates.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    by_date = {row["date"]: row for row in rows}

    policy = official_policy_rows()

    connection = get_connection(DATABASE_PATH)

    try:
        yield_dates = [
            row["observation_date"]
            for row in connection.execute(
                """
                SELECT DISTINCT
                    observation_date
                FROM yield_observations
                ORDER BY observation_date
                """
            ).fetchall()
        ]

    finally:
        connection.close()

    assert len(yield_dates) == 1151

    for observation_date in yield_dates:
        assert observation_date in by_date

        eligible = [
            source
            for source in policy
            if (source["effective_date"] <= observation_date)
        ]

        assert eligible

        source = eligible[-1]

        derived = by_date[observation_date]

        assert derived["source_effective_date"] == source["effective_date"]

        assert Decimal(derived["policy_rate_pct"]) == Decimal(str(source["rate_pct"]))


def test_daily_policy_state_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated generation must produce exactly identical bytes."""

    first = run_builder(
        tmp_path,
        monkeypatch,
        "first.csv",
    )

    first_bytes = first.read_bytes()

    second = run_builder(
        tmp_path,
        monkeypatch,
        "second.csv",
    )

    second_bytes = second.read_bytes()

    assert first_bytes == second_bytes

    assert hashlib.sha256(first_bytes).hexdigest() == EXPECTED_SHA256

    assert hashlib.sha256(second_bytes).hexdigest() == EXPECTED_SHA256


def test_policy_effective_date_markers_and_transition_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Effective-date markers must occur only on official in-range transitions."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "transitions.csv",
    )

    (
        _,
        rows,
    ) = read_generated(output_path)

    by_date = {row["date"]: row for row in rows}

    policy = official_policy_rows()

    in_range = [
        row for row in policy if ("2022-01-04" <= row["effective_date"] <= "2026-09-30")
    ]

    assert len(in_range) == 17

    marked_dates = {
        row["date"] for row in rows if (row["is_source_effective_date"] == "1")
    }

    expected_marked_dates = {row["effective_date"] for row in in_range}

    assert marked_dates == expected_marked_dates

    assert "2021-12-15" not in marked_dates

    previous_source_date = "2021-12-15"

    for source in in_range:
        effective_date = source["effective_date"]

        effective_day = date.fromisoformat(effective_date)

        previous_day = (effective_day - timedelta(days=1)).isoformat()

        assert by_date[effective_date]["source_effective_date"] == effective_date

        assert by_date[effective_date]["is_source_effective_date"] == "1"

        assert by_date[previous_day]["source_effective_date"] == previous_source_date

        previous_source_date = effective_date
