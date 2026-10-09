"""Integration tests for the Phase 6A deterministic descriptive baseline."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_descriptive_analysis_tables.py"

OUTPUTS = {
    "yield_levels": {
        "path": (PROJECT_ROOT / "data" / "interim" / "descriptive_yield_levels.csv"),
        "rows": 50,
        "sha": ("88ce5b39d4dd29f4749be6bc75aaee9cd0f7cadce37c22c54c1fb6bf3db633a6"),
    },
    "yield_changes": {
        "path": (PROJECT_ROOT / "data" / "interim" / "descriptive_yield_changes.csv"),
        "rows": 50,
        "sha": ("a3a785b0c12ece10564ad3e2c0aea76e8cec100abbe34a83841f5276adb6f978"),
    },
    "term_spreads": {
        "path": (PROJECT_ROOT / "data" / "interim" / "descriptive_term_spreads.csv"),
        "rows": 8,
        "sha": ("97f586c77e9636e09fd40d5fcc2f8049cee0fd95eb9b98eb66f4f5055f2cbf69"),
    },
    "cross_curve": {
        "path": (
            PROJECT_ROOT
            / "data"
            / "interim"
            / "descriptive_cross_curve_differences.csv"
        ),
        "rows": 10,
        "sha": ("ec59b6148d5a5f2aa02b38cddfe3aeebb5bfa0f173e58e522b5df70961634477"),
    },
    "event_windows": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "descriptive_mpc_event_windows.csv"
        ),
        "rows": 72,
        "sha": ("92c6af99dd2cbf445eef3c8964f3b4316778a81424ee04b74e4b2540a0fb11d3"),
    },
    "monthly_census": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "descriptive_monthly_sample_census.csv"
        ),
        "rows": 25,
        "sha": ("d6a427f5580da4b99ea21ae64902da9494fed6325b4b674b71d9a08eca071d33"),
    },
    "manifest": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "descriptive_analysis_manifest.csv"
        ),
        "rows": 6,
        "sha": ("129b4e4fde84db27f1f447174dbf7a671d56dbef98e691699c8b8051f4d9c3e0"),
    },
}

EXPECTED_SOURCE_N = {
    "yield_levels": 22742,
    "yield_changes": 22737,
    "term_spreads": 4164,
    "cross_curve": 1940,
    "event_windows": 688,
}


def sha256_file(
    path: Path,
) -> str:
    """Return the SHA-256 digest for one file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one CSV artifact."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def detect_count_field(
    rows: list[dict[str, str]],
) -> str:
    """Find the descriptive sample-size field."""

    assert rows

    candidates = (
        "n",
        "sample_n",
        "sample_size",
        "observation_count",
        "eligible_observation_count",
    )

    headers = set(rows[0])

    matches = [candidate for candidate in candidates if candidate in headers]

    assert len(matches) == 1

    return matches[0]


def test_phase6a_frozen_artifact_hashes_and_shapes() -> None:
    """All seven descriptive artifacts retain frozen bytes and shapes."""

    for spec in OUTPUTS.values():
        path = spec["path"]

        assert path.is_file()

        _, rows = read_csv(path)

        assert len(rows) == spec["rows"]

        assert sha256_file(path) == spec["sha"]


def test_phase6a_source_observation_census() -> None:
    """Descriptive tables represent the frozen eligible samples exactly."""

    for name, expected_n in EXPECTED_SOURCE_N.items():
        _, rows = read_csv(OUTPUTS[name]["path"])

        count_field = detect_count_field(rows)

        represented = sum(int(row[count_field]) for row in rows)

        assert represented == (expected_n)


def test_phase6a_manifest_reconciles_to_outputs() -> None:
    """The Phase 6A manifest must reconcile to all six table families."""

    _, rows = read_csv(OUTPUTS["manifest"]["path"])

    assert len(rows) == 6

    expected_files = {
        OUTPUTS[name]["path"].name
        for name in (
            "yield_levels",
            "yield_changes",
            "term_spreads",
            "cross_curve",
            "event_windows",
            "monthly_census",
        )
    }

    artifact_field_candidates = (
        "artifact_path",
        "output_path",
        "file_path",
        "artifact",
    )

    sha_field_candidates = (
        "sha256",
        "sha",
    )

    row_count_candidates = (
        "row_count",
        "rows",
        "group_count",
    )

    headers = set(rows[0])

    artifact_fields = [field for field in artifact_field_candidates if field in headers]

    sha_fields = [field for field in sha_field_candidates if field in headers]

    row_count_fields = [field for field in row_count_candidates if field in headers]

    assert len(artifact_fields) == 1

    assert len(sha_fields) == 1

    assert len(row_count_fields) == 1

    artifact_field = artifact_fields[0]

    sha_field = sha_fields[0]

    row_count_field = row_count_fields[0]

    observed_files = {Path(row[artifact_field]).name for row in rows}

    assert observed_files == (expected_files)

    spec_by_name = {
        OUTPUTS[name]["path"].name: OUTPUTS[name]
        for name in (
            "yield_levels",
            "yield_changes",
            "term_spreads",
            "cross_curve",
            "event_windows",
            "monthly_census",
        )
    }

    for row in rows:
        file_name = Path(row[artifact_field]).name

        spec = spec_by_name[file_name]

        assert row[sha_field] == spec["sha"]

        assert int(row[row_count_field]) == spec["rows"]


def test_phase6a_outputs_remain_descriptive_only() -> None:
    """Phase 6A outputs must not contain inferential result fields."""

    forbidden_exact = {
        "p_value",
        "pvalue",
        "p",
        "t_stat",
        "t_statistic",
        "z_stat",
        "z_statistic",
        "f_stat",
        "f_statistic",
        "coefficient",
        "beta",
        "standard_error",
        "stderr",
        "confidence_interval",
        "ci_lower",
        "ci_upper",
        "r_squared",
        "adjusted_r_squared",
        "causal_effect",
    }

    for name in (
        "yield_levels",
        "yield_changes",
        "term_spreads",
        "cross_curve",
        "event_windows",
        "monthly_census",
    ):
        headers, rows = read_csv(OUTPUTS[name]["path"])

        lowered = {header.lower() for header in headers}

        assert not (lowered & forbidden_exact)

        if "analysis_type" in headers:
            assert {row["analysis_type"] for row in rows} == {"DESCRIPTIVE_ONLY"}


def test_phase6a_builder_regeneration_is_byte_deterministic() -> None:
    """A production regeneration must leave all seven bytes unchanged."""

    before = {name: spec["path"].read_bytes() for name, spec in (OUTPUTS.items())}

    result = subprocess.run(
        [
            sys.executable,
            str(BUILDER_PATH),
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        "PASS: deterministic Phase 6A descriptive baseline constructed" in result.stdout
    )

    after = {name: spec["path"].read_bytes() for name, spec in (OUTPUTS.items())}

    assert before == after

    for name, spec in OUTPUTS.items():
        assert hashlib.sha256(after[name]).hexdigest() == (spec["sha"])
