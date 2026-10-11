"""Build deterministic Phase 6B inferential statistical outputs."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as scipy_stats
import statsmodels.api as sm

from pakyield.config import PROJECT_ROOT

YIELD_INPUT = PROJECT_ROOT / "data" / "interim" / "yield_regime_analysis_panel.csv"

TERM_INPUT = PROJECT_ROOT / "data" / "interim" / "term_spread_regime_analysis_panel.csv"

CROSS_INPUT = (
    PROJECT_ROOT / "data" / "interim" / "cross_curve_regime_analysis_panel.csv"
)

EVENT_INPUT = PROJECT_ROOT / "data" / "interim" / "mpc_event_window_panel.csv"

MONTHLY_INPUT = PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv"

INPUT_HASHES = {
    YIELD_INPUT: ("f8583955e1f30953b13d7a054c2df4e146063c7fcfcabe205fd9cc9b42158a30"),
    TERM_INPUT: ("d9fd6633941ab2d8932200ba45ac2e8e2619c1d77cbe30e751458d75e75311dd"),
    CROSS_INPUT: ("2a286e2847081c6df654b6e13e71e3e07ce2e5249a4a2cef61f7e6fd5400c384"),
    EVENT_INPUT: ("b99224391fd254d3404ca7e0ce27073b2fdceee12cc0703a54af9b32e125472f"),
    MONTHLY_INPUT: ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
}

OUTPUTS = {
    "yield_level_regime": (
        PROJECT_ROOT / "data" / "interim" / "inferential_yield_level_regime.csv"
    ),
    "yield_change_regime": (
        PROJECT_ROOT / "data" / "interim" / "inferential_yield_change_regime.csv"
    ),
    "term_spread_regime": (
        PROJECT_ROOT / "data" / "interim" / "inferential_term_spread_regime.csv"
    ),
    "cross_curve_zero": (
        PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_zero.csv"
    ),
    "cross_curve_regime": (
        PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_regime.csv"
    ),
    "mpc_event_window": (
        PROJECT_ROOT / "data" / "interim" / "inferential_mpc_event_windows.csv"
    ),
}

MANIFEST_OUTPUT = (
    PROJECT_ROOT / "data" / "interim" / "inferential_analysis_manifest.csv"
)

EVENT_MIN_N = 5
ALPHA = 0.05

COMMON_FIELDS = [
    "family",
    "test_id",
    "curve_type",
    "tenor",
    "spread_name",
    "half_window",
    "decision_type",
    "outcome_variable",
    "comparison",
    "test_method",
    "analysis_status",
    "exclusion_reason",
    "sample_n",
    "n_easing",
    "n_tightening",
    "hac_lag",
    "mean_easing",
    "mean_tightening",
    "estimate",
    "estimate_unit",
    "standard_error",
    "ci_95_low",
    "ci_95_high",
    "test_statistic",
    "p_value_raw",
    "p_value_bh",
    "reject_bh_0_05",
]

MANIFEST_FIELDS = [
    "family",
    "artifact_path",
    "row_count",
    "inferential_test_count",
    "descriptive_only_count",
    "sha256",
    "method",
    "multiple_testing_rule",
]


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def sha256_file(
    path: Path,
) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs() -> None:
    for path, expected in INPUT_HASHES.items():
        if not path.is_file():
            raise RuntimeError(f"Missing frozen input: {path}")

        actual = sha256_file(path)

        if actual != expected:
            raise RuntimeError(
                f"Frozen input changed: {path}\nexpected={expected}\nactual={actual}"
            )


def fmt(
    value: float | int | None,
) -> str:
    if value is None:
        return ""

    numeric = float(value)

    if not math.isfinite(numeric):
        raise RuntimeError(f"Non-finite numerical result: {value}")

    return format(
        numeric,
        ".17g",
    )


def automatic_hac_lag(
    n: int,
) -> int:
    if n <= 0:
        raise ValueError("n must be positive")

    return int(math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def bh_adjust(
    p_values: list[float],
) -> list[float]:
    """Benjamini-Hochberg adjustment with deterministic stable ordering."""

    m = len(p_values)

    if m == 0:
        return []

    order = sorted(
        range(m),
        key=lambda index: (
            p_values[index],
            index,
        ),
    )

    adjusted = [0.0 for _ in p_values]

    running = 1.0

    for rank_position in range(
        m,
        0,
        -1,
    ):
        index = order[rank_position - 1]

        candidate = p_values[index] * m / rank_position

        running = min(
            running,
            candidate,
            1.0,
        )

        adjusted[index] = running

    return adjusted


def write_csv_atomic(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
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


def hac_regime_test(
    observations: list[
        tuple[
            str,
            str,
            float,
        ]
    ],
) -> dict[str, Any]:
    """
    Compare TIGHTENING versus EASING via OLS coefficient with HAC covariance.

    observations:
        [(date, regime_label, outcome), ...]

    Effect estimate:
        mean(TIGHTENING) - mean(EASING)
    """

    ordered = sorted(
        observations,
        key=lambda item: item[0],
    )

    y = np.asarray(
        [item[2] for item in ordered],
        dtype=float,
    )

    tightening = np.asarray(
        [1.0 if item[1] == "TIGHTENING" else 0.0 for item in ordered],
        dtype=float,
    )

    regimes = [item[1] for item in ordered]

    n_easing = sum(regime == "EASING" for regime in regimes)

    n_tightening = sum(regime == "TIGHTENING" for regime in regimes)

    if n_easing == 0 or n_tightening == 0:
        raise RuntimeError("Both EASING and TIGHTENING must be represented")

    n = len(y)

    lag = automatic_hac_lag(n)

    design = sm.add_constant(
        tightening,
        has_constant="add",
    )

    result = sm.OLS(
        y,
        design,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": lag,
        },
        use_t=True,
    )

    confidence = result.conf_int(alpha=ALPHA)

    easing_values = y[tightening == 0.0]

    tightening_values = y[tightening == 1.0]

    estimate = float(result.params[1])

    arithmetic_difference = float(np.mean(tightening_values) - np.mean(easing_values))

    if not math.isclose(
        estimate,
        arithmetic_difference,
        rel_tol=1e-11,
        abs_tol=1e-11,
    ):
        raise RuntimeError(
            "OLS coefficient does not equal TIGHTENING-minus-EASING mean difference"
        )

    return {
        "sample_n": n,
        "n_easing": n_easing,
        "n_tightening": n_tightening,
        "hac_lag": lag,
        "mean_easing": float(np.mean(easing_values)),
        "mean_tightening": float(np.mean(tightening_values)),
        "estimate": estimate,
        "standard_error": float(result.bse[1]),
        "ci_95_low": float(confidence[1, 0]),
        "ci_95_high": float(confidence[1, 1]),
        "test_statistic": float(result.tvalues[1]),
        "p_value_raw": float(result.pvalues[1]),
    }


def hac_zero_test(
    observations: list[
        tuple[
            str,
            float,
        ]
    ],
) -> dict[str, Any]:
    """HAC intercept-only test of a time-series mean against zero."""

    ordered = sorted(
        observations,
        key=lambda item: item[0],
    )

    y = np.asarray(
        [item[1] for item in ordered],
        dtype=float,
    )

    n = len(y)

    lag = automatic_hac_lag(n)

    design = np.ones(
        (
            n,
            1,
        ),
        dtype=float,
    )

    result = sm.OLS(
        y,
        design,
    ).fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": lag,
        },
        use_t=True,
    )

    confidence = result.conf_int(alpha=ALPHA)

    estimate = float(result.params[0])

    if not math.isclose(
        estimate,
        float(np.mean(y)),
        rel_tol=1e-11,
        abs_tol=1e-11,
    ):
        raise RuntimeError("Intercept does not equal sample mean")

    return {
        "sample_n": n,
        "hac_lag": lag,
        "estimate": estimate,
        "standard_error": float(result.bse[0]),
        "ci_95_low": float(confidence[0, 0]),
        "ci_95_high": float(confidence[0, 1]),
        "test_statistic": float(result.tvalues[0]),
        "p_value_raw": float(result.pvalues[0]),
    }


def event_one_sample_test(
    values: list[float],
) -> dict[str, Any]:
    """Two-sided one-sample t-test of event-window mean against zero."""

    array = np.asarray(
        values,
        dtype=float,
    )

    n = len(array)

    mean_value = float(np.mean(array))

    if n < EVENT_MIN_N:
        return {
            "sample_n": n,
            "estimate": mean_value,
            "standard_error": None,
            "ci_95_low": None,
            "ci_95_high": None,
            "test_statistic": None,
            "p_value_raw": None,
        }

    standard_error = float(
        scipy_stats.sem(
            array,
            ddof=1,
        )
    )

    statistic, p_value = scipy_stats.ttest_1samp(
        array,
        popmean=0.0,
        alternative="two-sided",
    )

    critical = float(
        scipy_stats.t.ppf(
            1.0 - ALPHA / 2.0,
            df=n - 1,
        )
    )

    return {
        "sample_n": n,
        "estimate": mean_value,
        "standard_error": standard_error,
        "ci_95_low": (mean_value - critical * standard_error),
        "ci_95_high": (mean_value + critical * standard_error),
        "test_statistic": float(statistic),
        "p_value_raw": float(p_value),
    }


def empty_result_row() -> dict[str, str]:
    return {field: "" for field in COMMON_FIELDS}


def apply_bh(
    rows: list[dict[str, str]],
) -> None:
    inferential_indexes = [
        index
        for index, row in enumerate(rows)
        if (row["analysis_status"] == "INFERENTIAL" and row["p_value_raw"])
    ]

    p_values = [float(rows[index]["p_value_raw"]) for index in inferential_indexes]

    adjusted = bh_adjust(p_values)

    for index, q_value in zip(
        inferential_indexes,
        adjusted,
        strict=True,
    ):
        rows[index]["p_value_bh"] = fmt(q_value)

        rows[index]["reject_bh_0_05"] = "1" if q_value <= ALPHA else "0"


def regime_groups(
    rows: list[dict[str, str]],
    *,
    status_field: str,
    outcome_field: str,
    key_fields: tuple[str, ...],
) -> dict[
    tuple[str, ...],
    list[
        tuple[
            str,
            str,
            float,
        ]
    ],
]:
    groups = defaultdict(list)

    for row in rows:
        if row[status_field] != "ELIGIBLE":
            continue

        value = row[outcome_field]

        regime = row["regime_label"]

        if not value:
            continue

        if regime not in {
            "EASING",
            "TIGHTENING",
        }:
            continue

        key = tuple(row[field] for field in key_fields)

        groups[key].append(
            (
                row["observation_date"],
                regime,
                float(value),
            )
        )

    return groups


def build_regime_family(
    *,
    family: str,
    groups: dict[
        tuple[str, ...],
        list[
            tuple[
                str,
                str,
                float,
            ]
        ],
    ],
    key_names: tuple[str, ...],
    outcome_variable: str,
    estimate_unit: str,
) -> list[dict[str, str]]:
    output = []

    for key in sorted(groups):
        stats = hac_regime_test(groups[key])

        identifiers = dict(
            zip(
                key_names,
                key,
                strict=True,
            )
        )

        row = empty_result_row()

        row.update(
            {
                "family": family,
                "curve_type": identifiers.get(
                    "curve_type",
                    "",
                ),
                "tenor": identifiers.get(
                    "tenor",
                    "",
                ),
                "spread_name": identifiers.get(
                    "spread_name",
                    "",
                ),
                "outcome_variable": outcome_variable,
                "comparison": ("TIGHTENING_MINUS_EASING"),
                "test_method": ("OLS_HAC_NEWEY_WEST"),
                "analysis_status": ("INFERENTIAL"),
                "sample_n": str(stats["sample_n"]),
                "n_easing": str(stats["n_easing"]),
                "n_tightening": str(stats["n_tightening"]),
                "hac_lag": str(stats["hac_lag"]),
                "mean_easing": fmt(stats["mean_easing"]),
                "mean_tightening": fmt(stats["mean_tightening"]),
                "estimate": fmt(stats["estimate"]),
                "estimate_unit": estimate_unit,
                "standard_error": fmt(stats["standard_error"]),
                "ci_95_low": fmt(stats["ci_95_low"]),
                "ci_95_high": fmt(stats["ci_95_high"]),
                "test_statistic": fmt(stats["test_statistic"]),
                "p_value_raw": fmt(stats["p_value_raw"]),
            }
        )

        id_parts = [
            family,
        ]

        for name in key_names:
            id_parts.append(identifiers[name])

        row["test_id"] = "::".join(id_parts)

        output.append(row)

    apply_bh(output)

    return output


def build_cross_zero(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    groups = defaultdict(list)

    for row in rows:
        if row["paired_comparison_status"] != "ELIGIBLE":
            continue

        groups[row["tenor"]].append(
            (
                row["observation_date"],
                float(row["pkisrv_minus_pkrv_bps"]),
            )
        )

    output = []

    for tenor in sorted(groups):
        stats = hac_zero_test(groups[tenor])

        row = empty_result_row()

        row.update(
            {
                "family": "cross_curve_zero",
                "test_id": (f"cross_curve_zero::{tenor}"),
                "tenor": tenor,
                "outcome_variable": ("pkisrv_minus_pkrv_bps"),
                "comparison": ("MEAN_DIFFERENCE_VS_ZERO"),
                "test_method": ("INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST"),
                "analysis_status": ("INFERENTIAL"),
                "sample_n": str(stats["sample_n"]),
                "hac_lag": str(stats["hac_lag"]),
                "estimate": fmt(stats["estimate"]),
                "estimate_unit": "bps",
                "standard_error": fmt(stats["standard_error"]),
                "ci_95_low": fmt(stats["ci_95_low"]),
                "ci_95_high": fmt(stats["ci_95_high"]),
                "test_statistic": fmt(stats["test_statistic"]),
                "p_value_raw": fmt(stats["p_value_raw"]),
            }
        )

        output.append(row)

    apply_bh(output)

    return output


def build_event_family(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    groups = defaultdict(list)

    for row in rows:
        if row["eligibility_status"] != "ELIGIBLE":
            continue

        groups[
            (
                row["curve_type"],
                row["tenor"],
                row["half_window"],
                row["decision_type"],
            )
        ].append(float(row["window_change_bps"]))

    output = []

    for (
        curve_type,
        tenor,
        half_window,
        decision_type,
    ) in sorted(groups):
        values = groups[
            (
                curve_type,
                tenor,
                half_window,
                decision_type,
            )
        ]

        stats = event_one_sample_test(values)

        inferential = len(values) >= EVENT_MIN_N

        row = empty_result_row()

        row.update(
            {
                "family": "mpc_event_window",
                "test_id": "::".join(
                    [
                        "mpc_event_window",
                        curve_type,
                        tenor,
                        half_window,
                        decision_type,
                    ]
                ),
                "curve_type": curve_type,
                "tenor": tenor,
                "half_window": (half_window),
                "decision_type": (decision_type),
                "outcome_variable": ("window_change_bps"),
                "comparison": ("MEAN_WINDOW_CHANGE_VS_ZERO"),
                "test_method": ("ONE_SAMPLE_T_TEST" if inferential else "NOT_RUN"),
                "analysis_status": (
                    "INFERENTIAL" if inferential else "DESCRIPTIVE_ONLY"
                ),
                "exclusion_reason": (
                    "" if inferential else ("FEWER_THAN_5_ELIGIBLE_MPC_EVENTS")
                ),
                "sample_n": str(stats["sample_n"]),
                "estimate": fmt(stats["estimate"]),
                "estimate_unit": "bps",
                "standard_error": fmt(stats["standard_error"]),
                "ci_95_low": fmt(stats["ci_95_low"]),
                "ci_95_high": fmt(stats["ci_95_high"]),
                "test_statistic": fmt(stats["test_statistic"]),
                "p_value_raw": fmt(stats["p_value_raw"]),
            }
        )

        output.append(row)

    apply_bh(output)

    return output


def validate_census(
    outputs: dict[
        str,
        list[dict[str, str]],
    ],
) -> None:
    expected_rows = {
        "yield_level_regime": 25,
        "yield_change_regime": 25,
        "term_spread_regime": 4,
        "cross_curve_zero": 5,
        "cross_curve_regime": 5,
        "mpc_event_window": 72,
    }

    for family, expected in expected_rows.items():
        actual = len(outputs[family])

        if actual != expected:
            raise RuntimeError(f"{family}: expected {expected} rows, found {actual}")

    event_rows = outputs["mpc_event_window"]

    inferential = sum(row["analysis_status"] == "INFERENTIAL" for row in event_rows)

    descriptive = sum(
        row["analysis_status"] == "DESCRIPTIVE_ONLY" for row in event_rows
    )

    if inferential != 54:
        raise RuntimeError("Expected 54 inferential event-window tests")

    if descriptive != 18:
        raise RuntimeError("Expected 18 descriptive-only event-window groups")

    total_inferential = sum(
        sum(row["analysis_status"] == "INFERENTIAL" for row in rows)
        for rows in outputs.values()
    )

    if total_inferential != 118:
        raise RuntimeError(
            f"Expected 118 total Phase 6B inferential tests; found {total_inferential}"
        )

    for family, rows in outputs.items():
        inferential_rows = [
            row for row in rows if row["analysis_status"] == "INFERENTIAL"
        ]

        for row in inferential_rows:
            if not row["p_value_raw"]:
                raise RuntimeError(f"{family}: missing raw p-value")

            if not row["p_value_bh"]:
                raise RuntimeError(f"{family}: missing BH-adjusted p-value")

            p_raw = float(row["p_value_raw"])

            p_bh = float(row["p_value_bh"])

            if not (0.0 <= p_raw <= 1.0):
                raise RuntimeError(f"{family}: invalid raw p-value")

            if not (0.0 <= p_bh <= 1.0):
                raise RuntimeError(f"{family}: invalid BH p-value")


def build_manifest(
    outputs: dict[
        str,
        list[dict[str, str]],
    ],
) -> list[dict[str, str]]:
    methods = {
        "yield_level_regime": ("OLS_HAC_NEWEY_WEST"),
        "yield_change_regime": ("OLS_HAC_NEWEY_WEST"),
        "term_spread_regime": ("OLS_HAC_NEWEY_WEST"),
        "cross_curve_zero": ("INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST"),
        "cross_curve_regime": ("OLS_HAC_NEWEY_WEST"),
        "mpc_event_window": ("ONE_SAMPLE_T_TEST_IF_N_GE_5"),
    }

    rows = []

    for family in (
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_zero",
        "cross_curve_regime",
        "mpc_event_window",
    ):
        output_path = OUTPUTS[family]

        family_rows = outputs[family]

        inferential = sum(
            row["analysis_status"] == "INFERENTIAL" for row in family_rows
        )

        descriptive = sum(
            row["analysis_status"] == "DESCRIPTIVE_ONLY" for row in family_rows
        )

        rows.append(
            {
                "family": family,
                "artifact_path": str(output_path.relative_to(PROJECT_ROOT)),
                "row_count": str(len(family_rows)),
                "inferential_test_count": str(inferential),
                "descriptive_only_count": str(descriptive),
                "sha256": (sha256_file(output_path)),
                "method": methods[family],
                "multiple_testing_rule": ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"),
            }
        )

    rows.append(
        {
            "family": ("monthly_cpi_yield"),
            "artifact_path": str(MONTHLY_INPUT.relative_to(PROJECT_ROOT)),
            "row_count": str(len(read_csv(MONTHLY_INPUT))),
            "inferential_test_count": "0",
            "descriptive_only_count": "1234",
            "sha256": (sha256_file(MONTHLY_INPUT)),
            "method": ("DESCRIPTIVE_ONLY_IN_PHASE_6B"),
            "multiple_testing_rule": ("NOT_APPLICABLE"),
        }
    )

    return rows


def main() -> None:
    verify_inputs()

    yield_rows = read_csv(YIELD_INPUT)

    term_rows = read_csv(TERM_INPUT)

    cross_rows = read_csv(CROSS_INPUT)

    event_rows = read_csv(EVENT_INPUT)

    yield_level_groups = regime_groups(
        yield_rows,
        status_field=("yield_level_regime_analysis_status"),
        outcome_field="yield_pct",
        key_fields=(
            "curve_type",
            "tenor",
        ),
    )

    yield_change_groups = regime_groups(
        yield_rows,
        status_field=("yield_change_regime_analysis_status"),
        outcome_field=("yield_change_bps"),
        key_fields=(
            "curve_type",
            "tenor",
        ),
    )

    term_groups = regime_groups(
        term_rows,
        status_field=("joint_analysis_status"),
        outcome_field=("term_spread_bps"),
        key_fields=("spread_name",),
    )

    cross_regime_groups = regime_groups(
        cross_rows,
        status_field=("paired_comparison_status"),
        outcome_field=("pkisrv_minus_pkrv_bps"),
        key_fields=("tenor",),
    )

    outputs = {
        "yield_level_regime": (
            build_regime_family(
                family=("yield_level_regime"),
                groups=(yield_level_groups),
                key_names=(
                    "curve_type",
                    "tenor",
                ),
                outcome_variable=("yield_pct"),
                estimate_unit=("percentage_points"),
            )
        ),
        "yield_change_regime": (
            build_regime_family(
                family=("yield_change_regime"),
                groups=(yield_change_groups),
                key_names=(
                    "curve_type",
                    "tenor",
                ),
                outcome_variable=("yield_change_bps"),
                estimate_unit="bps",
            )
        ),
        "term_spread_regime": (
            build_regime_family(
                family=("term_spread_regime"),
                groups=(term_groups),
                key_names=("spread_name",),
                outcome_variable=("term_spread_bps"),
                estimate_unit="bps",
            )
        ),
        "cross_curve_zero": (build_cross_zero(cross_rows)),
        "cross_curve_regime": (
            build_regime_family(
                family=("cross_curve_regime"),
                groups=(cross_regime_groups),
                key_names=("tenor",),
                outcome_variable=("pkisrv_minus_pkrv_bps"),
                estimate_unit="bps",
            )
        ),
        "mpc_event_window": (build_event_family(event_rows)),
    }

    validate_census(outputs)

    for family, rows in outputs.items():
        write_csv_atomic(
            OUTPUTS[family],
            COMMON_FIELDS,
            rows,
        )

    manifest_rows = build_manifest(outputs)

    write_csv_atomic(
        MANIFEST_OUTPUT,
        MANIFEST_FIELDS,
        manifest_rows,
    )

    print("===== PHASE 6B INFERENTIAL OUTPUTS =====")

    total_inferential = 0

    for family in (
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_zero",
        "cross_curve_regime",
        "mpc_event_window",
    ):
        rows = outputs[family]

        inferential = [row for row in rows if row["analysis_status"] == "INFERENTIAL"]

        descriptive = [
            row for row in rows if row["analysis_status"] == "DESCRIPTIVE_ONLY"
        ]

        rejected = sum(row["reject_bh_0_05"] == "1" for row in inferential)

        total_inferential += len(inferential)

        print("")
        print(family)
        print(
            "  rows:",
            len(rows),
        )
        print(
            "  inferential:",
            len(inferential),
        )
        print(
            "  descriptive_only:",
            len(descriptive),
        )
        print(
            "  bh_reject_0_05:",
            rejected,
        )
        print(
            "  sha256:",
            sha256_file(OUTPUTS[family]),
        )

    print("")
    print(
        "total_inferential_tests:",
        total_inferential,
    )

    print(
        "monthly_inferential_tests:",
        0,
    )

    print("")
    print(
        "manifest:",
        MANIFEST_OUTPUT.relative_to(PROJECT_ROOT),
    )

    print(
        "manifest_sha256:",
        sha256_file(MANIFEST_OUTPUT),
    )

    print("")
    print("PASS: deterministic Phase 6B inferential outputs constructed")


if __name__ == "__main__":
    main()
