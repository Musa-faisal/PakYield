"""Integration tests for deterministic PKRV long-form normalization."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_pkrv_normalized_long.py"


def load_builder_module() -> ModuleType:
    """Load the PKRV normalization script from its repository path."""

    spec = importlib.util.spec_from_file_location(
        "build_pkrv_normalized_long",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()

RAW_DIR = BUILDER.RAW_DIR

CANONICAL_TENORS = tuple(BUILDER.PKRV_CANONICAL_TENORS)

TENOR_TO_YEARS = BUILDER.TENOR_TO_YEARS


def read_rows(
    path: Path,
) -> list[dict[str, str]]:
    """Read one generated PKRV long-form artifact."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
) -> Path:
    """Run full normalization into an isolated temporary output."""

    output_path = tmp_path / file_name

    # main() only uses PROJECT_ROOT for the display
    # path after all source paths have already been
    # resolved as module-level constants.
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


def test_pkrv_full_corpus_normalization_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All accepted PKRV files must produce exactly 22,800 source rows."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "pkrv_full.csv",
    )

    rows = read_rows(output_path)

    assert len(rows) == 22800

    keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in rows
    }

    assert len(keys) == 22800

    dates = {row["observation_date"] for row in rows}

    assert len(dates) == 1149

    assert min(dates) == "2022-01-04"

    assert max(dates) == "2026-09-28"

    date_counts = Counter(row["observation_date"] for row in rows)

    assert dict(Counter(date_counts.values())) == {
        20: 1119,
        14: 30,
    }

    year_counts = Counter(row["observation_date"][:4] for row in rows)

    assert dict(year_counts) == {
        "2022": 4840,
        "2023": 4620,
        "2024": 4800,
        "2025": 4960,
        "2026": 3580,
    }

    structural_counts = Counter(row["structural_class"] for row in rows)

    assert dict(structural_counts) == {
        "FULL_20": 22380,
        "PARTIAL_14": 420,
    }

    missing_partial = {
        "1M",
        "2M",
        "3M",
        "4M",
        "6M",
        "9M",
    }

    tenor_counts = Counter(row["tenor"] for row in rows)

    for tenor in CANONICAL_TENORS:
        expected = 1119 if tenor in missing_partial else 1149

        assert tenor_counts[tenor] == expected

    source_contract = {}

    for row in rows:
        tenor = row["tenor"]

        assert tenor in (TENOR_TO_YEARS)

        assert abs(float(row["tenor_years"]) - TENOR_TO_YEARS[tenor]) < 1e-10

        yield_pct = Decimal(row["yield_pct"])

        assert Decimal("0") < yield_pct < Decimal("100")

        assert row["source_organization"] == ("Mutual Funds Association of Pakistan")

        source_file = row["source_file"]

        contract = (
            row["structural_class"],
            row["source_layout"],
            row["source_value_field"],
        )

        previous = source_contract.get(source_file)

        if previous is None:
            source_contract[source_file] = contract

        else:
            assert previous == contract

    assert len(source_contract) == 1149

    layout_counts = Counter(contract[1] for contract in source_contract.values())

    assert dict(layout_counts) == {
        "CSV_DIRECT_RATE": 1003,
        "CSV_PUBLISHED_BENCHMARK": 139,
        "FIXED_WIDTH_AVG_RATE": 3,
        "FIXED_WIDTH_FMAP": 2,
        "XLSX_MID_RATE": 1,
        "XML_SPREADSHEETML": 1,
    }

    by_key = {
        (
            row["observation_date"],
            row["tenor"],
        ): row["yield_pct"]
        for row in rows
    }

    assert (
        by_key[
            (
                "2022-01-04",
                "1W",
            )
        ]
        == "9.99"
    )

    assert (
        by_key[
            (
                "2023-06-16",
                "1W",
            )
        ]
        == "21.53"
    )

    assert (
        by_key[
            (
                "2023-08-11",
                "1W",
            )
        ]
        == "21.82"
    )

    assert (
        by_key[
            (
                "2026-03-18",
                "20Y",
            )
        ]
        == "12.71"
    )

    partial_date = "2023-06-16"

    for tenor in missing_partial:
        assert (
            partial_date,
            tenor,
        ) not in keys


def test_pkrv_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated full-corpus normalization must generate identical bytes."""

    first = run_builder(
        tmp_path,
        monkeypatch,
        "first.csv",
    )

    first_bytes = first.read_bytes()

    first_hash = hashlib.sha256(first_bytes).hexdigest()

    second = run_builder(
        tmp_path,
        monkeypatch,
        "second.csv",
    )

    second_bytes = second.read_bytes()

    second_hash = hashlib.sha256(second_bytes).hexdigest()

    assert first_hash == second_hash

    assert first_bytes == second_bytes


def test_audited_exact_duplicate_rows_are_collapsed() -> None:
    """Known repeated source rows collapse without changing benchmark values."""

    expected = {
        "PKRV161120222132.csv": (
            "1W",
            Decimal("15.08"),
        ),
        "PKRV281220222162.csv": (
            "1Y",
            Decimal("16.99"),
        ),
        "PKRV291220222164.csv": (
            "4M",
            Decimal("16.96"),
        ),
        "PKRV301220222166.csv": (
            "8Y",
            Decimal("13.86"),
        ),
    }

    assert BUILDER.EXPECTED_EXACT_DUPLICATE_ROWS == {
        "PKRV161120222132.csv": {
            "1W": 3,
        },
        "PKRV281220222162.csv": {
            "1Y": 1,
        },
        "PKRV291220222164.csv": {
            "4M": 1,
        },
        "PKRV301220222166.csv": {
            "8Y": 1,
        },
    }

    for file_name, (
        tenor,
        expected_yield,
    ) in expected.items():
        values, _, _ = BUILDER.parse_csv_artifact(RAW_DIR / file_name)

        assert len(values) == 20

        assert values[tenor] == expected_yield


def test_conflicting_duplicate_source_row_fails_closed(
    tmp_path: Path,
) -> None:
    """A repeated tenor with different source content must be rejected."""

    source = RAW_DIR / "PKRV161120222132.csv"

    target = tmp_path / source.name

    text = source.read_text(encoding="utf-8")

    assert text.count("1W,15.08,0.00") == 4

    # Alter exactly one copy so the repeated tenor
    # is no longer an exact source-row duplicate.
    modified = text.replace(
        "1W,15.08,0.00",
        "1W,15.09,0.00",
        1,
    )

    target.write_text(
        modified,
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match=("Conflicting duplicate tenor row"),
    ):
        BUILDER.parse_csv_artifact(target)


def test_split_avg_rate_header_uses_terminal_rate_column() -> None:
    """Historical Avg,Rate exports must use the terminal published rate."""

    path = RAW_DIR / "PKRV11082023803.csv"

    values, layout, value_field = BUILDER.parse_csv_artifact(path)

    assert len(values) == 20

    assert layout == "CSV_PUBLISHED_BENCHMARK"

    assert value_field == "Avg Rate"

    assert values["1W"] == Decimal("21.82")

    assert values["20Y"] == Decimal("15.37")
