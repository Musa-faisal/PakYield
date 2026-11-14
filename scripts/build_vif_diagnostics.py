"""Build fail-closed VIF diagnostics for current PakYield regressions."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import cast

import numpy as np
from statsmodels.stats.outliers_influence import (  # type: ignore[import-untyped]
    variance_inflation_factor,
)

from pakyield.config import PROJECT_ROOT  # type: ignore[import-untyped]

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "inferential_vif_diagnostics.csv"

MANIFEST_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "interim" / "inferential_vif_manifest.csv"
)

VIF_THRESHOLD = 5.0

SOURCE_SPECS = {
    "yield": {
        "path": (PROJECT_ROOT / "data" / "interim" / "yield_regime_analysis_panel.csv"),
        "sha": ("f8583955e1f30953b13d7a054c2df4e146063c7fcfcabe205fd9cc9b42158a30"),
        "rows": 24815,
    },
    "term": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "term_spread_regime_analysis_panel.csv"
        ),
        "sha": ("d9fd6633941ab2d8932200ba45ac2e8e2619c1d77cbe30e751458d75e75311dd"),
        "rows": 4596,
    },
    "cross": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "cross_curve_regime_analysis_panel.csv"
        ),
        "sha": ("2a286e2847081c6df654b6e13e71e3e07ce2e5249a4a2cef61f7e6fd5400c384"),
        "rows": 2035,
    },
}

INFERENTIAL_SPECS = {
    "yield_level_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_yield_level_regime.csv"
        ),
        "sha": ("4c9ba3fdd6e920e905db3dc118e645ad904e2cbf0682c33d0c5228998790b1a4"),
        "rows": 25,
    },
    "yield_change_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_yield_change_regime.csv"
        ),
        "sha": ("4baf694f635fb183ef4072dde24b10924bd280241276940b83d19b2c3c2f9501"),
        "rows": 25,
    },
    "term_spread_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_term_spread_regime.csv"
        ),
        "sha": ("17f7222dda8f17e14830d64f268b076ac365e66012b4fdf6aa38527a835e1349"),
        "rows": 4,
    },
    "cross_curve_regime": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_regime.csv"
        ),
        "sha": ("f3cca17f6cf658828a9ac613d7fdf7764126e9da0a74760749a9109a8717a6a5"),
        "rows": 5,
    },
}

INFERENTIAL_MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "interim" / "inferential_analysis_manifest.csv"
)

INFERENTIAL_MANIFEST_SHA = (
    "ec0dea0f785cb0a4f6a9ca5db684da21805701746c4160bb694bd739ab56bc10"
)

DETAIL_FIELDS = [
    "family",
    "test_id",
    "curve_type",
    "tenor",
    "spread_name",
    "test_method",
    "predictor_name",
    "predictor_count",
    "sample_n",
    "n_easing",
    "n_tightening",
    "vif",
    "threshold",
    "diagnostic_status",
    "diagnostic_note",
]

MANIFEST_FIELDS = [
    "family",
    "method",
    "vif_applicability",
    "model_count",
    "vif_row_count",
    "nonconstant_predictor_count",
    "max_vif",
    "threshold",
    "diagnostic_status",
    "reason",
]


def sha256_file(path: Path) -> str:
    """Return a file SHA-256."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read a CSV into dictionaries."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def write_csv_atomic(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Write a deterministic CSV atomically."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(path.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def verify_file(
    path: Path,
    expected_sha: str,
    expected_rows: int,
) -> list[dict[str, str]]:
    """Fail closed if a frozen input changed."""

    if not path.is_file():
        raise RuntimeError(f"Missing required VIF input: {path}")

    actual_sha = sha256_file(path)

    if actual_sha != expected_sha:
        raise RuntimeError(f"Frozen VIF input SHA mismatch: {path}")

    rows = read_csv(path)

    if len(rows) != expected_rows:
        raise RuntimeError(f"Frozen VIF input row-count mismatch: {path}")

    return rows


def format_number(value: float) -> str:
    """Format deterministic numeric output."""

    if not math.isfinite(value):
        raise RuntimeError(f"Non-finite VIF result: {value}")

    return format(value, ".12g")


def eligible_regime_rows(
    family: str,
    inferential_row: dict[str, str],
    sources: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    """Reconstruct the exact sample underlying one regime regression."""

    curve_type = inferential_row["curve_type"]

    tenor = inferential_row["tenor"]

    spread_name = inferential_row["spread_name"]

    if family == "yield_level_regime":
        rows = [
            row
            for row in sources["yield"]
            if (
                row["curve_type"] == curve_type
                and row["tenor"] == tenor
                and row["yield_level_regime_analysis_status"] == "ELIGIBLE"
            )
        ]

    elif family == "yield_change_regime":
        rows = [
            row
            for row in sources["yield"]
            if (
                row["curve_type"] == curve_type
                and row["tenor"] == tenor
                and row["yield_change_regime_analysis_status"] == "ELIGIBLE"
            )
        ]

    elif family == "term_spread_regime":
        rows = [
            row
            for row in sources["term"]
            if (
                row["spread_name"] == spread_name
                and row["joint_analysis_status"] == "ELIGIBLE"
            )
        ]

    elif family == "cross_curve_regime":
        rows = [
            row
            for row in sources["cross"]
            if (row["tenor"] == tenor and row["paired_comparison_status"] == "ELIGIBLE")
        ]

    else:
        raise RuntimeError(f"Unsupported VIF regression family: {family}")

    invalid_regimes = {
        row["regime_label"]
        for row in rows
        if row["regime_label"]
        not in {
            "EASING",
            "TIGHTENING",
        }
    }

    if invalid_regimes:
        raise RuntimeError(
            f"Unexpected regime in VIF sample: {sorted(invalid_regimes)}"
        )

    return rows


def calculate_regime_indicator_vif(
    rows: list[dict[str, str]],
) -> float:
    """Calculate VIF for the sole nonconstant regime predictor."""

    indicator = np.asarray(
        [1.0 if row["regime_label"] == "TIGHTENING" else 0.0 for row in rows],
        dtype=float,
    )

    if indicator.size < 2:
        raise RuntimeError("VIF sample has fewer than two observations")

    unique_values = set(indicator.tolist())

    if unique_values != {
        0.0,
        1.0,
    }:
        raise RuntimeError(
            "VIF predictor does not contain both EASING and TIGHTENING observations"
        )

    design = np.column_stack(
        [
            np.ones(
                indicator.size,
                dtype=float,
            ),
            indicator,
        ]
    )

    value = float(
        variance_inflation_factor(
            design,
            1,
        )
    )

    if not math.isfinite(value):
        raise RuntimeError(f"Non-finite VIF: {value}")

    return value


def build_detail_rows(
    sources: dict[
        str,
        list[dict[str, str]],
    ],
    inferential: dict[
        str,
        list[dict[str, str]],
    ],
) -> list[dict[str, str]]:
    """Build one VIF observation per current regime regression."""

    output = []

    for family in (
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
    ):
        for inferential_row in inferential[family]:
            if inferential_row["analysis_status"] != "INFERENTIAL":
                raise RuntimeError(
                    "VIF regression row is not inferential: "
                    f"{inferential_row['test_id']}"
                )

            if inferential_row["test_method"] != "OLS_HAC_NEWEY_WEST":
                raise RuntimeError(
                    f"Unexpected VIF regression method: {inferential_row['test_id']}"
                )

            rows = eligible_regime_rows(
                family,
                inferential_row,
                sources,
            )

            sample_n = len(rows)

            n_easing = sum(row["regime_label"] == "EASING" for row in rows)

            n_tightening = sum(row["regime_label"] == "TIGHTENING" for row in rows)

            if sample_n != int(inferential_row["sample_n"]):
                raise RuntimeError(
                    f"VIF sample_n mismatch for {inferential_row['test_id']}"
                )

            if n_easing != int(inferential_row["n_easing"]):
                raise RuntimeError(
                    f"VIF EASING count mismatch for {inferential_row['test_id']}"
                )

            if n_tightening != int(inferential_row["n_tightening"]):
                raise RuntimeError(
                    f"VIF TIGHTENING count mismatch for {inferential_row['test_id']}"
                )

            if n_easing + n_tightening != sample_n:
                raise RuntimeError("VIF sample contains unexpected regimes")

            vif_value = calculate_regime_indicator_vif(rows)

            if not math.isclose(
                vif_value,
                1.0,
                rel_tol=0.0,
                abs_tol=1e-10,
            ):
                raise RuntimeError(
                    "Single-predictor VIF should equal 1: "
                    f"{inferential_row['test_id']} "
                    f"{vif_value}"
                )

            status = "PASS" if vif_value <= VIF_THRESHOLD else "FAIL"

            output.append(
                {
                    "family": family,
                    "test_id": (inferential_row["test_id"]),
                    "curve_type": (inferential_row["curve_type"]),
                    "tenor": (inferential_row["tenor"]),
                    "spread_name": (inferential_row["spread_name"]),
                    "test_method": (inferential_row["test_method"]),
                    "predictor_name": ("regime_tightening_indicator"),
                    "predictor_count": "1",
                    "sample_n": str(sample_n),
                    "n_easing": str(n_easing),
                    "n_tightening": str(n_tightening),
                    "vif": format_number(vif_value),
                    "threshold": (format_number(VIF_THRESHOLD)),
                    "diagnostic_status": (status),
                    "diagnostic_note": (
                        "SINGLE_NONCONSTANT_PREDICTOR_VIF_EQUALS_ONE_BY_CONSTRUCTION"
                    ),
                }
            )

    return output


def build_manifest_rows(
    detail_rows: list[dict[str, str]],
    inferential_manifest: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize VIF applicability across all seven inferential families."""

    detail_by_family: dict[
        str,
        list[dict[str, str]],
    ] = {}

    for row in detail_rows:
        detail_by_family.setdefault(
            row["family"],
            [],
        ).append(row)

    manifest_by_family = {row["family"]: row for row in inferential_manifest}

    expected_families = [
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_zero",
        "cross_curve_regime",
        "mpc_event_window",
        "monthly_cpi_yield",
    ]

    if set(manifest_by_family) != set(expected_families):
        raise RuntimeError("Unexpected inferential manifest family universe")

    output = []

    applicable = {
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_regime",
    }

    for family in expected_families:
        manifest = manifest_by_family[family]

        method = manifest["method"]

        model_count = int(manifest["inferential_test_count"])

        family_detail = detail_by_family.get(
            family,
            [],
        )

        if family in applicable:
            if len(family_detail) != model_count:
                raise RuntimeError(f"VIF detail/model-count mismatch: {family}")

            max_vif = max(float(row["vif"]) for row in family_detail)

            if not math.isclose(
                max_vif,
                1.0,
                rel_tol=0.0,
                abs_tol=1e-10,
            ):
                raise RuntimeError(f"Unexpected max VIF for {family}: {max_vif}")

            row = {
                "family": family,
                "method": method,
                "vif_applicability": ("APPLICABLE_TRIVIAL_SINGLE_PREDICTOR"),
                "model_count": str(model_count),
                "vif_row_count": str(len(family_detail)),
                "nonconstant_predictor_count": "1",
                "max_vif": (format_number(max_vif)),
                "threshold": (format_number(VIF_THRESHOLD)),
                "diagnostic_status": "PASS",
                "reason": (
                    "CURRENT_MODEL_HAS_ONE_NONCONSTANT_"
                    "PREDICTOR_SO_MULTICOLLINEARITY_"
                    "AMONG_PREDICTORS_CANNOT_ARISE"
                ),
            }

        elif family == "cross_curve_zero":
            if method != "INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST":
                raise RuntimeError("Unexpected cross_curve_zero method")

            row = {
                "family": family,
                "method": method,
                "vif_applicability": ("NOT_APPLICABLE"),
                "model_count": str(model_count),
                "vif_row_count": "0",
                "nonconstant_predictor_count": "0",
                "max_vif": "",
                "threshold": "",
                "diagnostic_status": ("NOT_APPLICABLE"),
                "reason": ("INTERCEPT_ONLY_MODEL_HAS_NO_NONCONSTANT_PREDICTOR"),
            }

        elif family == "mpc_event_window":
            row = {
                "family": family,
                "method": method,
                "vif_applicability": ("NOT_APPLICABLE"),
                "model_count": str(model_count),
                "vif_row_count": "0",
                "nonconstant_predictor_count": "0",
                "max_vif": "",
                "threshold": "",
                "diagnostic_status": ("NOT_APPLICABLE"),
                "reason": ("ONE_SAMPLE_T_TEST_HAS_NO_REGRESSION_DESIGN_MATRIX"),
            }

        elif family == "monthly_cpi_yield":
            if model_count != 0:
                raise RuntimeError(
                    "Monthly CPI family unexpectedly contains inferential tests"
                )

            row = {
                "family": family,
                "method": method,
                "vif_applicability": ("NOT_APPLICABLE"),
                "model_count": "0",
                "vif_row_count": "0",
                "nonconstant_predictor_count": "0",
                "max_vif": "",
                "threshold": "",
                "diagnostic_status": ("NOT_APPLICABLE"),
                "reason": ("DESCRIPTIVE_ONLY_FAMILY_HAS_NO_REGRESSION_DESIGN_MATRIX"),
            }

        else:
            raise RuntimeError(f"Unhandled VIF family: {family}")

        output.append(row)

    return output


def validate_outputs(
    detail_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
) -> None:
    """Validate the complete VIF evidence contract."""

    expected_detail_counts = {
        "yield_level_regime": 25,
        "yield_change_regime": 25,
        "term_spread_regime": 4,
        "cross_curve_regime": 5,
    }

    counts = Counter(row["family"] for row in detail_rows)

    if counts != expected_detail_counts:
        raise RuntimeError(f"Unexpected VIF detail census: {dict(counts)}")

    if len(detail_rows) != 59:
        raise RuntimeError(f"Unexpected VIF detail row count: {len(detail_rows)}")

    keys = {
        (
            row["family"],
            row["test_id"],
            row["predictor_name"],
        )
        for row in detail_rows
    }

    if len(keys) != 59:
        raise RuntimeError("Duplicate VIF detail analytical key")

    if any(row["diagnostic_status"] != "PASS" for row in detail_rows):
        raise RuntimeError("At least one applicable VIF row failed")

    if any(
        not math.isclose(
            float(row["vif"]),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-10,
        )
        for row in detail_rows
    ):
        raise RuntimeError("Applicable VIF value differs from 1")

    if len(manifest_rows) != 7:
        raise RuntimeError("VIF manifest must contain 7 families")

    status_counts = Counter(row["diagnostic_status"] for row in manifest_rows)

    if status_counts != {
        "PASS": 4,
        "NOT_APPLICABLE": 3,
    }:
        raise RuntimeError(
            f"Unexpected VIF manifest status census: {dict(status_counts)}"
        )


def display_path(path: Path) -> Path:
    """Display a repository-relative path when possible."""

    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT)

    return path


def main() -> None:
    """Build complete Phase 10 VIF diagnostic evidence."""

    sources = {
        name: verify_file(
            cast(Path, spec["path"]),
            cast(str, spec["sha"]),
            cast(int, spec["rows"]),
        )
        for name, spec in SOURCE_SPECS.items()
    }

    inferential = {
        family: verify_file(
            cast(Path, spec["path"]),
            cast(str, spec["sha"]),
            cast(int, spec["rows"]),
        )
        for family, spec in (INFERENTIAL_SPECS.items())
    }

    inferential_manifest = verify_file(
        INFERENTIAL_MANIFEST_PATH,
        INFERENTIAL_MANIFEST_SHA,
        7,
    )

    detail_rows = build_detail_rows(
        sources,
        inferential,
    )

    manifest_rows = build_manifest_rows(
        detail_rows,
        inferential_manifest,
    )

    validate_outputs(
        detail_rows,
        manifest_rows,
    )

    write_csv_atomic(
        OUTPUT_PATH,
        DETAIL_FIELDS,
        detail_rows,
    )

    write_csv_atomic(
        MANIFEST_OUTPUT_PATH,
        MANIFEST_FIELDS,
        manifest_rows,
    )

    print("===== PHASE 10 VIF DIAGNOSTICS =====")

    print(
        "Detail rows:",
        len(detail_rows),
    )

    print(
        "Detail families:",
        dict(Counter(row["family"] for row in detail_rows)),
    )

    print(
        "VIF values:",
        sorted({row["vif"] for row in detail_rows}),
    )

    print(
        "Detail statuses:",
        dict(Counter(row["diagnostic_status"] for row in detail_rows)),
    )

    print(
        "Manifest rows:",
        len(manifest_rows),
    )

    print(
        "Manifest statuses:",
        dict(Counter(row["diagnostic_status"] for row in manifest_rows)),
    )

    print(
        "Output:",
        display_path(OUTPUT_PATH),
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print(
        "Manifest:",
        display_path(MANIFEST_OUTPUT_PATH),
    )

    print(
        "Manifest SHA256:",
        sha256_file(MANIFEST_OUTPUT_PATH),
    )

    print("")
    print(
        "PASS: Phase 10 VIF implementation "
        "reconstructed every applicable "
        "regression design matrix"
    )


if __name__ == "__main__":
    main()
