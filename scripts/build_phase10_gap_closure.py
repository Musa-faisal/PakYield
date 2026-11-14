"""Close the remaining Phase 10 econometric/diagnostic gaps deterministically."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy.stats import pearsonr, probplot, spearmanr
from statsmodels.stats.diagnostic import (
    acorr_ljungbox,
    het_breuschpagan,
)
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller

from pakyield.config import PROJECT_ROOT

INTERIM = PROJECT_ROOT / "data" / "interim"

DESCRIPTIVE_SPECS = {
    "yield_levels": {
        "descriptive": INTERIM / "phase10_descriptive_yield_levels.csv",
        "source": INTERIM / "yield_regime_analysis_panel.csv",
        "value": "yield_pct",
        "status": "yield_level_regime_analysis_status",
        "dimensions": (
            "curve_type",
            "tenor",
            "regime_label",
        ),
    },
    "yield_changes": {
        "descriptive": INTERIM / "phase10_descriptive_yield_changes.csv",
        "source": INTERIM / "yield_regime_analysis_panel.csv",
        "value": "yield_change_bps",
        "status": "yield_change_regime_analysis_status",
        "dimensions": (
            "curve_type",
            "tenor",
            "regime_label",
        ),
    },
    "term_spreads": {
        "descriptive": INTERIM / "phase10_descriptive_term_spreads.csv",
        "source": INTERIM / "term_spread_regime_analysis_panel.csv",
        "value": "term_spread_bps",
        "status": "joint_analysis_status",
        "dimensions": (
            "curve_type",
            "spread_name",
            "regime_label",
        ),
    },
    "cross_curve": {
        "descriptive": INTERIM / "phase10_descriptive_cross_curve_differences.csv",
        "source": INTERIM / "cross_curve_regime_analysis_panel.csv",
        "value": "pkisrv_minus_pkrv_bps",
        "status": "paired_comparison_status",
        "dimensions": (
            "tenor",
            "regime_label",
        ),
    },
    "mpc_event_windows": {
        "descriptive": INTERIM / "phase10_descriptive_mpc_event_windows.csv",
        "source": INTERIM / "mpc_event_window_panel.csv",
        "value": "window_change_bps",
        "status": "eligibility_status",
        "dimensions": (
            "curve_type",
            "tenor",
            "half_window",
            "decision_type",
        ),
    },
}

CORRELATION_OUTPUT = INTERIM / "phase10_correlation_diagnostics.csv"

ADF_OUTPUT = INTERIM / "phase10_adf_stationarity.csv"

RESIDUAL_OUTPUT = INTERIM / "phase10_regression_residual_diagnostics.csv"

QQ_OUTPUT = INTERIM / "phase10_regression_residual_qq.csv"

MANIFEST_OUTPUT = INTERIM / "phase10_gap_closure_manifest.csv"

INFERENTIAL_SPECS = (
    {
        "result": INTERIM / "inferential_yield_level_regime.csv",
        "source": INTERIM / "yield_regime_analysis_panel.csv",
        "outcome": "yield_pct",
        "status": "yield_level_regime_analysis_status",
        "dimensions": (
            "curve_type",
            "tenor",
        ),
    },
    {
        "result": INTERIM / "inferential_yield_change_regime.csv",
        "source": INTERIM / "yield_regime_analysis_panel.csv",
        "outcome": "yield_change_bps",
        "status": "yield_change_regime_analysis_status",
        "dimensions": (
            "curve_type",
            "tenor",
        ),
    },
    {
        "result": INTERIM / "inferential_term_spread_regime.csv",
        "source": INTERIM / "term_spread_regime_analysis_panel.csv",
        "outcome": "term_spread_bps",
        "status": "joint_analysis_status",
        "dimensions": (
            "curve_type",
            "spread_name",
        ),
    },
    {
        "result": INTERIM / "inferential_cross_curve_regime.csv",
        "source": INTERIM / "cross_curve_regime_analysis_panel.csv",
        "outcome": "pkisrv_minus_pkrv_bps",
        "status": "paired_comparison_status",
        "dimensions": ("tenor",),
    },
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise RuntimeError(f"Missing required Phase 10 input: {path}")

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def write_csv(
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value: float) -> str:
    if not math.isfinite(value):
        return ""

    text = f"{value:.12f}".rstrip("0").rstrip(".")

    if text == "-0":
        return "0"

    return text


def percentile_linear(
    values: list[float],
    percentile: float,
) -> float:
    ordered = sorted(values)

    if not ordered:
        raise ValueError("Cannot calculate percentile of empty data")

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower

    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def eligible_values(
    source_rows: list[dict[str, str]],
    descriptive_row: dict[str, str],
    *,
    value_field: str,
    status_field: str,
    dimensions: tuple[str, ...],
) -> list[float]:
    values = []

    for source in source_rows:
        if source.get(status_field) != "ELIGIBLE":
            continue

        matches = True

        for dimension in dimensions:
            wanted = descriptive_row.get(
                dimension,
                "",
            )

            if wanted and source.get(dimension, "") != wanted:
                matches = False
                break

        if not matches:
            continue

        raw = source.get(
            value_field,
            "",
        )

        if not raw:
            continue

        values.append(float(raw))

    return values


def augment_descriptive_percentiles() -> list[Path]:
    updated = []

    for name, spec in DESCRIPTIVE_SPECS.items():
        descriptive_path = spec["descriptive"]

        source_path = spec["source"]

        headers, rows = read_csv(descriptive_path)

        _, source_rows = read_csv(source_path)

        fields = [
            field
            for field in headers
            if field
            not in {
                "percentile_25",
                "percentile_75",
            }
        ]

        fields.extend(
            [
                "percentile_25",
                "percentile_75",
            ]
        )

        for row in rows:
            values = eligible_values(
                source_rows,
                row,
                value_field=spec["value"],
                status_field=spec["status"],
                dimensions=spec["dimensions"],
            )

            sample_n = row.get(
                "sample_n",
                "",
            )

            if sample_n:
                expected_n = int(float(sample_n))

                if expected_n != len(values):
                    raise RuntimeError(
                        f"{name}: sample_n mismatch "
                        f"for {row}: "
                        f"expected={expected_n}, "
                        f"reconstructed={len(values)}"
                    )

            if values:
                row["percentile_25"] = number(
                    percentile_linear(
                        values,
                        0.25,
                    )
                )

                row["percentile_75"] = number(
                    percentile_linear(
                        values,
                        0.75,
                    )
                )

            else:
                row["percentile_25"] = ""

                row["percentile_75"] = ""

        write_csv(
            descriptive_path,
            fields,
            rows,
        )

        updated.append(descriptive_path)

    return updated


def correlation_rows() -> list[dict[str, str]]:
    specs = (
        {
            "family": "YIELD_LEVEL_POLICY_RATE",
            "path": INTERIM / "yield_regime_analysis_panel.csv",
            "status": "yield_level_regime_analysis_status",
            "x": "policy_rate_pct",
            "y": "yield_pct",
            "dimensions": (
                "curve_type",
                "tenor",
                "regime_label",
            ),
        },
        {
            "family": "TERM_SPREAD_POLICY_RATE",
            "path": INTERIM / "term_spread_regime_analysis_panel.csv",
            "status": "joint_analysis_status",
            "x": "policy_rate_pct",
            "y": "term_spread_bps",
            "dimensions": (
                "spread_name",
                "regime_label",
            ),
        },
        {
            "family": "CROSS_CURVE_DIFFERENCE_POLICY_RATE",
            "path": INTERIM / "cross_curve_regime_analysis_panel.csv",
            "status": "paired_comparison_status",
            "x": "policy_rate_pct",
            "y": "pkisrv_minus_pkrv_bps",
            "dimensions": (
                "tenor",
                "regime_label",
            ),
        },
    )

    output = []

    for spec in specs:
        _, rows = read_csv(spec["path"])

        groups = defaultdict(list)

        for row in rows:
            if row.get(spec["status"]) != "ELIGIBLE":
                continue

            if not row.get(spec["x"]) or not row.get(spec["y"]):
                continue

            key = tuple(
                row.get(
                    dimension,
                    "",
                )
                for dimension in spec["dimensions"]
            )

            groups[key].append(
                (
                    float(row[spec["x"]]),
                    float(row[spec["y"]]),
                )
            )

        for key in sorted(groups):
            pairs = groups[key]

            xs = np.asarray(
                [pair[0] for pair in pairs],
                dtype=float,
            )

            ys = np.asarray(
                [pair[1] for pair in pairs],
                dtype=float,
            )

            record = {
                "family": spec["family"],
                "curve_type": "",
                "tenor": "",
                "spread_name": "",
                "regime_label": "",
                "x_variable": spec["x"],
                "y_variable": spec["y"],
                "sample_n": str(len(pairs)),
                "pearson_r": "",
                "spearman_rho": "",
                "analysis_status": "",
                "exclusion_reason": "",
            }

            for dimension, value in zip(
                spec["dimensions"],
                key,
                strict=True,
            ):
                record[dimension] = value

            if len(pairs) < 3:
                record["analysis_status"] = "INELIGIBLE"

                record["exclusion_reason"] = "INSUFFICIENT_OBSERVATIONS"

            elif np.std(xs) == 0 or np.std(ys) == 0:
                record["analysis_status"] = "INELIGIBLE"

                record["exclusion_reason"] = "CONSTANT_SERIES"

            else:
                pearson = pearsonr(
                    xs,
                    ys,
                )

                spearman = spearmanr(
                    xs,
                    ys,
                )

                record["pearson_r"] = number(float(pearson.statistic))

                record["spearman_rho"] = number(float(spearman.statistic))

                record["analysis_status"] = "ELIGIBLE"

            output.append(record)

    return output


def build_correlation_diagnostics() -> None:
    rows = correlation_rows()

    fields = [
        "family",
        "curve_type",
        "tenor",
        "spread_name",
        "regime_label",
        "x_variable",
        "y_variable",
        "sample_n",
        "pearson_r",
        "spearman_rho",
        "analysis_status",
        "exclusion_reason",
    ]

    write_csv(
        CORRELATION_OUTPUT,
        fields,
        rows,
    )


def build_adf_stationarity() -> None:
    specs = (
        {
            "family": "YIELD_LEVEL",
            "path": INTERIM / "yield_changes_long.csv",
            "value": "yield_pct",
            "date": "observation_date",
            "dimensions": (
                "curve_type",
                "tenor",
            ),
            "status": None,
        },
        {
            "family": "YIELD_CHANGE",
            "path": INTERIM / "yield_changes_long.csv",
            "value": "yield_change_bps",
            "date": "observation_date",
            "dimensions": (
                "curve_type",
                "tenor",
            ),
            "status": None,
        },
        {
            "family": "TERM_SPREAD",
            "path": INTERIM / "term_spread_panel.csv",
            "value": "term_spread_bps",
            "date": "observation_date",
            "dimensions": ("spread_name",),
            "status": (
                "eligibility_status",
                "ELIGIBLE",
            ),
        },
        {
            "family": "CROSS_CURVE_DIFFERENCE",
            "path": INTERIM / "pkrv_pkisrv_same_date_panel.csv",
            "value": "pkisrv_minus_pkrv_bps",
            "date": "observation_date",
            "dimensions": ("tenor",),
            "status": None,
        },
    )

    output = []

    for spec in specs:
        _, rows = read_csv(spec["path"])

        groups = defaultdict(list)

        for row in rows:
            if spec["status"]:
                field, wanted = spec["status"]

                if row.get(field) != wanted:
                    continue

            raw = row.get(
                spec["value"],
                "",
            )

            if not raw:
                continue

            key = tuple(
                row.get(
                    dimension,
                    "",
                )
                for dimension in spec["dimensions"]
            )

            groups[key].append(
                (
                    row[spec["date"]],
                    float(raw),
                )
            )

        for key in sorted(groups):
            observations = sorted(
                groups[key],
                key=lambda item: item[0],
            )

            values = np.asarray(
                [item[1] for item in observations],
                dtype=float,
            )

            record = {
                "family": spec["family"],
                "curve_type": "",
                "tenor": "",
                "spread_name": "",
                "outcome_variable": (spec["value"]),
                "sample_n": str(len(values)),
                "adf_statistic": "",
                "p_value": "",
                "used_lag": "",
                "nobs": "",
                "critical_1pct": "",
                "critical_5pct": "",
                "critical_10pct": "",
                "analysis_status": "",
                "exclusion_reason": "",
            }

            for dimension, value in zip(
                spec["dimensions"],
                key,
                strict=True,
            ):
                record[dimension] = value

            if len(values) < 20:
                record["analysis_status"] = "INELIGIBLE"

                record["exclusion_reason"] = "INSUFFICIENT_OBSERVATIONS"

            elif np.std(values) == 0:
                record["analysis_status"] = "INELIGIBLE"

                record["exclusion_reason"] = "CONSTANT_SERIES"

            else:
                try:
                    result = adfuller(
                        values,
                        regression="c",
                        autolag="AIC",
                    )

                    record["adf_statistic"] = number(float(result[0]))

                    record["p_value"] = number(float(result[1]))

                    record["used_lag"] = str(int(result[2]))

                    record["nobs"] = str(int(result[3]))

                    critical = result[4]

                    record["critical_1pct"] = number(float(critical["1%"]))

                    record["critical_5pct"] = number(float(critical["5%"]))

                    record["critical_10pct"] = number(float(critical["10%"]))

                    record["analysis_status"] = "ELIGIBLE"

                except ValueError as error:
                    record["analysis_status"] = "INELIGIBLE"

                    record["exclusion_reason"] = "ADF_ERROR:" + str(error)

            output.append(record)

    fields = [
        "family",
        "curve_type",
        "tenor",
        "spread_name",
        "outcome_variable",
        "sample_n",
        "adf_statistic",
        "p_value",
        "used_lag",
        "nobs",
        "critical_1pct",
        "critical_5pct",
        "critical_10pct",
        "analysis_status",
        "exclusion_reason",
    ]

    write_csv(
        ADF_OUTPUT,
        fields,
        output,
    )


def source_sample(
    spec: dict[str, object],
    result_row: dict[str, str],
) -> list[dict[str, str]]:
    _, source_rows = read_csv(spec["source"])

    sample = []

    for row in source_rows:
        if row.get(spec["status"]) != "ELIGIBLE":
            continue

        if row.get("regime_label") not in {
            "EASING",
            "TIGHTENING",
        }:
            continue

        matched = True

        for dimension in spec["dimensions"]:
            wanted = result_row.get(
                dimension,
                "",
            )

            if (
                wanted
                and row.get(
                    dimension,
                    "",
                )
                != wanted
            ):
                matched = False
                break

        if not matched:
            continue

        if not row.get(
            spec["outcome"],
            "",
        ):
            continue

        sample.append(row)

    sample.sort(key=lambda row: row["observation_date"])

    return sample


def build_regression_residual_diagnostics() -> None:
    diagnostics = []
    qq_rows = []

    for spec in INFERENTIAL_SPECS:
        _, result_rows = read_csv(spec["result"])

        for result_row in result_rows:
            sample = source_sample(
                spec,
                result_row,
            )

            sample_n = len(sample)

            easing_n = sum(row["regime_label"] == "EASING" for row in sample)

            tightening_n = sum(row["regime_label"] == "TIGHTENING" for row in sample)

            expected_n = result_row.get(
                "sample_n",
                "",
            )

            expected_easing = result_row.get(
                "n_easing",
                "",
            )

            expected_tightening = result_row.get(
                "n_tightening",
                "",
            )

            if expected_n:
                if int(float(expected_n)) != sample_n:
                    raise RuntimeError(
                        "Inferential sample_n reconciliation "
                        f"failed for {result_row.get('test_id', '')}"
                    )

            if expected_easing:
                if int(float(expected_easing)) != easing_n:
                    raise RuntimeError(
                        "Inferential easing_n reconciliation "
                        f"failed for {result_row.get('test_id', '')}"
                    )

            if expected_tightening:
                if int(float(expected_tightening)) != tightening_n:
                    raise RuntimeError(
                        "Inferential tightening_n reconciliation "
                        f"failed for {result_row.get('test_id', '')}"
                    )

            record = {
                "family": result_row.get(
                    "family",
                    "",
                ),
                "test_id": result_row.get(
                    "test_id",
                    "",
                ),
                "curve_type": result_row.get(
                    "curve_type",
                    "",
                ),
                "tenor": result_row.get(
                    "tenor",
                    "",
                ),
                "spread_name": result_row.get(
                    "spread_name",
                    "",
                ),
                "outcome_variable": (spec["outcome"]),
                "sample_n": str(sample_n),
                "n_easing": str(easing_n),
                "n_tightening": str(tightening_n),
                "residual_mean": "",
                "residual_std": "",
                "durbin_watson": "",
                "breusch_pagan_lm": "",
                "breusch_pagan_lm_p_value": "",
                "breusch_pagan_f": "",
                "breusch_pagan_f_p_value": "",
                "autocorrelation_lag1": "",
                "ljung_box_lag": "",
                "ljung_box_statistic": "",
                "ljung_box_p_value": "",
                "analysis_status": "",
                "exclusion_reason": "",
            }

            if sample_n < 4 or easing_n == 0 or tightening_n == 0:
                record["analysis_status"] = "INELIGIBLE"

                record["exclusion_reason"] = "INSUFFICIENT_TWO_REGIME_SAMPLE"

                diagnostics.append(record)

                continue

            y = np.asarray(
                [float(row[spec["outcome"]]) for row in sample],
                dtype=float,
            )

            tightening = np.asarray(
                [1.0 if row["regime_label"] == "TIGHTENING" else 0.0 for row in sample],
                dtype=float,
            )

            exog = sm.add_constant(
                tightening,
                has_constant="add",
            )

            fitted = sm.OLS(
                y,
                exog,
            ).fit()

            residuals = np.asarray(
                fitted.resid,
                dtype=float,
            )

            bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(
                residuals,
                exog,
            )

            dw = durbin_watson(residuals)

            if (
                len(residuals) >= 3
                and np.std(residuals[:-1]) > 0
                and np.std(residuals[1:]) > 0
            ):
                lag1 = float(
                    np.corrcoef(
                        residuals[:-1],
                        residuals[1:],
                    )[0, 1]
                )
            else:
                lag1 = float("nan")

            ljung_lag = min(
                10,
                max(
                    1,
                    int(math.sqrt(len(residuals))),
                ),
                len(residuals) - 1,
            )

            ljung = acorr_ljungbox(
                residuals,
                lags=[ljung_lag],
                return_df=True,
            )

            lb_stat = float(ljung["lb_stat"].iloc[0])

            lb_p = float(ljung["lb_pvalue"].iloc[0])

            record["residual_mean"] = number(float(np.mean(residuals)))

            record["residual_std"] = number(
                float(
                    np.std(
                        residuals,
                        ddof=1,
                    )
                )
            )

            record["durbin_watson"] = number(float(dw))

            record["breusch_pagan_lm"] = number(float(bp_lm))

            record["breusch_pagan_lm_p_value"] = number(float(bp_lm_p))

            record["breusch_pagan_f"] = number(float(bp_f))

            record["breusch_pagan_f_p_value"] = number(float(bp_f_p))

            record["autocorrelation_lag1"] = number(lag1)

            record["ljung_box_lag"] = str(ljung_lag)

            record["ljung_box_statistic"] = number(lb_stat)

            record["ljung_box_p_value"] = number(lb_p)

            record["analysis_status"] = "ELIGIBLE"

            diagnostics.append(record)

            (
                (
                    theoretical_quantiles,
                    ordered_residuals,
                ),
                _,
            ) = probplot(
                residuals,
                dist="norm",
                fit=True,
            )

            for index, (
                theoretical,
                residual,
            ) in enumerate(
                zip(
                    theoretical_quantiles,
                    ordered_residuals,
                    strict=True,
                ),
                start=1,
            ):
                qq_rows.append(
                    {
                        "family": record["family"],
                        "test_id": record["test_id"],
                        "curve_type": record["curve_type"],
                        "tenor": record["tenor"],
                        "spread_name": record["spread_name"],
                        "point_index": str(index),
                        "theoretical_normal_quantile": number(float(theoretical)),
                        "ordered_residual": number(float(residual)),
                    }
                )

    diagnostic_fields = [
        "family",
        "test_id",
        "curve_type",
        "tenor",
        "spread_name",
        "outcome_variable",
        "sample_n",
        "n_easing",
        "n_tightening",
        "residual_mean",
        "residual_std",
        "durbin_watson",
        "breusch_pagan_lm",
        "breusch_pagan_lm_p_value",
        "breusch_pagan_f",
        "breusch_pagan_f_p_value",
        "autocorrelation_lag1",
        "ljung_box_lag",
        "ljung_box_statistic",
        "ljung_box_p_value",
        "analysis_status",
        "exclusion_reason",
    ]

    qq_fields = [
        "family",
        "test_id",
        "curve_type",
        "tenor",
        "spread_name",
        "point_index",
        "theoretical_normal_quantile",
        "ordered_residual",
    ]

    write_csv(
        RESIDUAL_OUTPUT,
        diagnostic_fields,
        diagnostics,
    )

    write_csv(
        QQ_OUTPUT,
        qq_fields,
        qq_rows,
    )


def build_manifest(
    descriptive_paths: list[Path],
) -> None:
    paths = [
        *descriptive_paths,
        CORRELATION_OUTPUT,
        ADF_OUTPUT,
        RESIDUAL_OUTPUT,
        QQ_OUTPUT,
    ]

    rows = []

    for path in paths:
        _, artifact_rows = read_csv(path)

        rows.append(
            {
                "artifact_path": str(path.relative_to(PROJECT_ROOT)),
                "row_count": str(len(artifact_rows)),
                "sha256": sha256_file(path),
            }
        )

    write_csv(
        MANIFEST_OUTPUT,
        [
            "artifact_path",
            "row_count",
            "sha256",
        ],
        rows,
    )


def main() -> None:
    descriptive_paths = augment_descriptive_percentiles()

    build_correlation_diagnostics()
    build_adf_stationarity()
    build_regression_residual_diagnostics()

    build_manifest(descriptive_paths)

    print("===== PHASE 10 GAP CLOSURE =====")

    for path in [
        *descriptive_paths,
        CORRELATION_OUTPUT,
        ADF_OUTPUT,
        RESIDUAL_OUTPUT,
        QQ_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        _, rows = read_csv(path)

        print(path.relative_to(PROJECT_ROOT))

        print(
            "  rows:",
            len(rows),
        )

        print(
            "  sha256:",
            sha256_file(path),
        )

    print("PASS: all executable Phase 10 gap-closure artifacts built")


if __name__ == "__main__":
    main()
