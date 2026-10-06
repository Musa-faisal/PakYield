"""Integration tests for deterministic PKISRV long-form normalization."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_pkisrv_normalized_long.py"


def load_builder_module() -> ModuleType:
    """Load the PKISRV normalization script."""

    spec = importlib.util.spec_from_file_location(
        "build_pkisrv_normalized_long",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder_module()

EXPECTED_SHA256 = "b581918c66e3d867f17d3f81672c665ab843196be7e2a5764189738c8d193b98"

EXPECTED_ABSENT_DATES = {
    "2025-03-07",
    "2025-08-20",
    "2026-03-18",
    "2026-03-27",
}

RAW_LABELS = {
    "1 - Month": "1M",
    "3 - Month": "3M",
    "6 - Month": "6M",
    "9 - Month": "9M",
    "1 - Year": "1Y",
}


def read_rows(
    path: Path,
) -> list[dict[str, str]]:
    """Read one generated normalized artifact."""

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
    """Run normalization into an isolated temporary path."""

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


def direct_raw_values(
    path: Path,
) -> dict[str, Decimal]:
    """Independently parse the five published raw source percentages."""

    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))

    occurrences = defaultdict(list)

    for row in rows:
        for index, value in enumerate(row):
            label = " ".join(str(value).strip().split())

            tenor = RAW_LABELS.get(label)

            if tenor is None:
                continue

            assert index + 1 < len(row)

            raw_value = row[index + 1].strip()

            assert raw_value.endswith("%")

            occurrences[tenor].append(Decimal(raw_value[:-1].strip()))

    assert set(occurrences) == set(BUILDER.EXPECTED_TENORS)

    result = {}

    for tenor in BUILDER.EXPECTED_TENORS:
        assert len(occurrences[tenor]) == 1

        result[tenor] = occurrences[tenor][0]

    return result


def test_pkisrv_full_corpus_normalization_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All accepted PKISRV source values must reconcile to 2,015 rows."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "pkisrv_full.csv",
    )

    rows = read_rows(output_path)

    assert len(rows) == 2015

    keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in rows
    }

    assert len(keys) == 2015

    dates = {row["observation_date"] for row in rows}

    assert len(dates) == 403

    assert min(dates) == "2025-02-03"

    assert max(dates) == "2026-09-30"

    assert dict(Counter(Counter(row["observation_date"] for row in rows).values())) == {
        5: 403,
    }

    assert dict(Counter(row["observation_date"][:4] for row in rows)) == {
        "2025": 1120,
        "2026": 895,
    }

    assert dict(Counter(row["tenor"] for row in rows)) == {
        tenor: 403 for tenor in (BUILDER.EXPECTED_TENORS)
    }

    by_key = {
        (
            row["observation_date"],
            row["tenor"],
        ): row
        for row in rows
    }

    census = BUILDER.read_csv(BUILDER.STRUCTURAL_PATH)

    accepted = [
        row
        for row in census
        if (
            row["structural_class"] == "COMPLETE_5"
            and row["validation_status"] == "ACCEPTED"
        )
    ]

    assert len(accepted) == 403

    for metadata in accepted:
        observation_date = metadata["observation_date"]

        file_name = metadata["file_name"]

        raw_values = direct_raw_values(BUILDER.RAW_DIR / file_name)

        for tenor, expected in raw_values.items():
            normalized = by_key[
                (
                    observation_date,
                    tenor,
                )
            ]

            assert Decimal(normalized["yield_pct"]) == expected

            assert normalized["source_file"] == file_name

            assert normalized["source_organization"] == (
                "Mutual Funds Association of Pakistan"
            )

            assert normalized["structural_class"] == "COMPLETE_5"

            assert normalized["source_layout"] == "CSV_PKISRV_RATES"

            assert normalized["source_value_field"] == "PKISRV Rates (Yields)"


def test_pkisrv_regeneration_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated full-corpus generation must produce identical bytes."""

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

    first_hash = hashlib.sha256(first_bytes).hexdigest()

    second_hash = hashlib.sha256(second_bytes).hexdigest()

    assert first_hash == second_hash == EXPECTED_SHA256


def test_all_nine_audited_layout_signatures_parse_exactly() -> None:
    """One representative from every accepted layout must remain locked."""

    cases = {
        "PKISRV030220253196.csv": (
            (
                6,
                7,
                8,
            ),
            "2025-02-03",
        ),
        "PKISRV040220253203.csv": (
            (
                6,
                7,
                9,
            ),
            "2025-02-04",
        ),
        "PKISRV140220253243.csv": (
            (
                5,
                6,
                7,
            ),
            "2025-02-14",
        ),
        "PKISRV040320253302.csv": (
            (
                12,
                13,
                14,
            ),
            "2025-03-04",
        ),
        "PKISRV0203202624734.csv": (
            (
                4,
                5,
                6,
            ),
            "2026-03-02",
        ),
        "PKISRV0204202624845.csv": (
            (
                11,
                12,
                13,
            ),
            "2026-04-02",
        ),
        "PKISRV0406202625090.csv": (
            (
                5,
                6,
                8,
            ),
            "2026-06-04",
        ),
        "PKISRV1806202625143.csv": (
            (
                5,
                6,
                9,
            ),
            "2026-06-18",
        ),
        "PKISRV2509202625474.csv": (
            (
                5,
                6,
                10,
            ),
            "2026-09-25",
        ),
    }

    for file_name, (
        expected_signature,
        sentinel_date,
    ) in cases.items():
        (
            values,
            signature,
        ) = BUILDER.parse_artifact(BUILDER.RAW_DIR / file_name)

        assert signature == expected_signature

        assert values == BUILDER.EXPECTED_SENTINELS[sentinel_date]


def test_source_level_absent_dates_are_never_normalized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The four source omissions must remain absent, not manufactured."""

    output_path = run_builder(
        tmp_path,
        monkeypatch,
        "pkisrv_absence.csv",
    )

    rows = read_rows(output_path)

    normalized_dates = {row["observation_date"] for row in rows}

    assert normalized_dates.isdisjoint(EXPECTED_ABSENT_DATES)

    assert BUILDER.EXPECTED_ABSENT_DATE_SET == EXPECTED_ABSENT_DATES


def test_pkisrv_parser_fails_closed_when_publication_semantics_change(
    tmp_path: Path,
) -> None:
    """Changed benchmark header or missing percent marker must be rejected."""

    source = BUILDER.RAW_DIR / "PKISRV030220253196.csv"

    original = source.read_text(encoding="utf-8")

    assert "PKISRV Rates (Yields)" in original

    header_changed = tmp_path / "header_changed.csv"

    header_changed.write_text(
        original.replace(
            "PKISRV Rates (Yields)",
            "PKISRV Rate",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match=("Unexpected PKISRV value header"),
    ):
        BUILDER.parse_artifact(header_changed)

    assert "10.70%" in original

    percent_removed = tmp_path / "percent_removed.csv"

    percent_removed.write_text(
        original.replace(
            "10.70%",
            "10.70",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match=("missing explicit percent marker"),
    ):
        BUILDER.parse_artifact(percent_removed)
