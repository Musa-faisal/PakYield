"""Build deterministic Phase 6A descriptive empirical tables."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from collections.abc import Iterable
from decimal import (
    ROUND_HALF_UP,
    Decimal,
    getcontext,
)
from pathlib import Path

from pakyield.config import PROJECT_ROOT

getcontext().prec = 40

SIX_DP = Decimal("0.000001")

INPUTS = {
    "yield": {
        "path": (PROJECT_ROOT / "data" / "interim" / "yield_regime_analysis_panel.csv"),
        "rows": 24815,
        "sha": ("f8583955e1f30953b13d7a054c2df4e146063c7fcfcabe205fd9cc9b42158a30"),
    },
    "term": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "term_spread_regime_analysis_panel.csv"
        ),
        "rows": 4596,
        "sha": ("d9fd6633941ab2d8932200ba45ac2e8e2619c1d77cbe30e751458d75e75311dd"),
    },
    "cross": {
        "path": (
            PROJECT_ROOT / "data" / "interim" / "cross_curve_regime_analysis_panel.csv"
        ),
        "rows": 2035,
        "sha": ("2a286e2847081c6df654b6e13e71e3e07ce2e5249a4a2cef61f7e6fd5400c384"),
    },
    "event": {
        "path": (PROJECT_ROOT / "data" / "interim" / "mpc_event_window_panel.csv"),
        "rows": 936,
        "sha": ("b99224391fd254d3404ca7e0ce27073b2fdceee12cc0703a54af9b32e125472f"),
    },
    "monthly": {
        "path": (PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv"),
        "rows": 1234,
        "sha": ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
    },
    "analysis_manifest": {
        "path": (PROJECT_ROOT / "data" / "interim" / "analysis_input_manifest.csv"),
        "rows": 5,
        "sha": ("ec0fe1e6c43f2dfbf246e8120a777720858b82498beb741f08d11cdb8df17aa4"),
    },
}

OUTPUTS = {
    "yield_levels": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_yield_levels.csv"
    ),
    "yield_changes": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_yield_changes.csv"
    ),
    "term_spreads": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_term_spreads.csv"
    ),
    "cross_curve": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_cross_curve_differences.csv"
    ),
    "event_windows": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_mpc_event_windows.csv"
    ),
    "monthly_census": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_monthly_sample_census.csv"
    ),
    "manifest": (
        PROJECT_ROOT / "data" / "interim" / "descriptive_analysis_manifest.csv"
    ),
}

BASIC_STATS_FIELDS = [
    "n",
    "mean",
    "median",
    "sample_std",
    "min",
    "max",
]

SIGNED_STATS_FIELDS = BASIC_STATS_FIELDS + [
    "negative_count",
    "zero_count",
    "positive_count",
]


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 digest for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def display_path(
    path: Path,
) -> Path:
    """Return repository-relative path when possible."""

    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT)

    return path


def read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one CSV file."""

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
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Atomically write deterministic CSV output."""

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
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def load_inputs() -> dict[
    str,
    dict[str, object],
]:
    """Verify and load every frozen Phase 6A input."""

    loaded = {}

    for name, spec in INPUTS.items():
        path = spec["path"]

        if not path.is_file():
            raise RuntimeError(f"Missing frozen input: {path}")

        actual_sha = sha256_file(path)

        if actual_sha != spec["sha"]:
            raise RuntimeError(f"Frozen input hash changed: {path}")

        headers, rows = read_csv(path)

        if len(rows) != spec["rows"]:
            raise RuntimeError(f"Frozen input row count changed: {path}")

        loaded[name] = {
            "headers": headers,
            "rows": rows,
        }

    return loaded


def decimal_value(
    value: str,
) -> Decimal:
    """Parse one required decimal value."""

    if value == "":
        raise ValueError("Cannot parse blank decimal")

    return Decimal(value)


def format_decimal(
    value: Decimal,
) -> str:
    """Format one decimal deterministically to six places."""

    rounded = value.quantize(
        SIX_DP,
        rounding=ROUND_HALF_UP,
    )

    if rounded == 0:
        rounded = abs(rounded)

    return format(
        rounded,
        "f",
    )


def median_decimal(
    ordered: list[Decimal],
) -> Decimal:
    """Return deterministic median from sorted decimals."""

    count = len(ordered)

    midpoint = count // 2

    if count % 2:
        return ordered[midpoint]

    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)


def sample_std_decimal(
    values: list[Decimal],
    mean: Decimal,
) -> Decimal:
    """Return sample standard deviation."""

    count = len(values)

    if count <= 1:
        return Decimal(0)

    squared = sum((value - mean) ** 2 for value in values)

    variance = squared / Decimal(count - 1)

    return variance.sqrt()


def describe(
    values: Iterable[Decimal],
    *,
    signed: bool,
) -> dict[str, str]:
    """Return deterministic descriptive statistics."""

    materialized = list(values)

    if not materialized:
        raise RuntimeError("Cannot describe an empty sample")

    ordered = sorted(materialized)

    count = len(materialized)

    mean = sum(
        materialized,
        Decimal(0),
    ) / Decimal(count)

    median = median_decimal(ordered)

    sample_std = sample_std_decimal(
        materialized,
        mean,
    )

    result = {
        "n": str(count),
        "mean": format_decimal(mean),
        "median": format_decimal(median),
        "sample_std": format_decimal(sample_std),
        "min": format_decimal(ordered[0]),
        "max": format_decimal(ordered[-1]),
    }

    if signed:
        result.update(
            {
                "negative_count": str(sum(value < 0 for value in materialized)),
                "zero_count": str(sum(value == 0 for value in materialized)),
                "positive_count": str(sum(value > 0 for value in materialized)),
            }
        )

    return result


def grouped_numeric_summary(
    rows: list[dict[str, str]],
    *,
    group_fields: tuple[str, ...],
    value_field: str,
    eligibility_field: str,
    signed: bool,
) -> list[dict[str, str]]:
    """Summarize one eligible numeric variable by deterministic groups."""

    grouped: dict[
        tuple[str, ...],
        list[Decimal],
    ] = defaultdict(list)

    for row in rows:
        if row[eligibility_field] != "ELIGIBLE":
            continue

        raw_value = row[value_field]

        if raw_value == "":
            raise RuntimeError(f"Eligible row has blank {value_field}")

        key = tuple(row[field] for field in group_fields)

        grouped[key].append(decimal_value(raw_value))

    output = []

    for key in sorted(grouped):
        result = {
            field: value
            for field, value in zip(
                group_fields,
                key,
                strict=True,
            )
        }

        result.update(
            describe(
                grouped[key],
                signed=signed,
            )
        )

        output.append(result)

    return output


def build_yield_level_summary(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize eligible sovereign yield levels."""

    return grouped_numeric_summary(
        rows,
        group_fields=(
            "curve_type",
            "regime_label",
            "tenor",
        ),
        value_field="yield_pct",
        eligibility_field=("yield_level_regime_analysis_status"),
        signed=False,
    )


def build_yield_change_summary(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize eligible sovereign yield changes."""

    return grouped_numeric_summary(
        rows,
        group_fields=(
            "curve_type",
            "regime_label",
            "tenor",
        ),
        value_field="yield_change_bps",
        eligibility_field=("yield_change_regime_analysis_status"),
        signed=True,
    )


def build_term_summary(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize eligible PKRV term spreads."""

    return grouped_numeric_summary(
        rows,
        group_fields=(
            "spread_name",
            "regime_label",
        ),
        value_field="term_spread_bps",
        eligibility_field=("joint_analysis_status"),
        signed=True,
    )


def build_cross_summary(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize eligible numerical PKISRV-minus-PKRV differences."""

    return grouped_numeric_summary(
        rows,
        group_fields=(
            "tenor",
            "regime_label",
        ),
        value_field=("pkisrv_minus_pkrv_bps"),
        eligibility_field=("paired_comparison_status"),
        signed=True,
    )


def build_event_summary(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Summarize eligible MPC event-window yield changes."""

    return grouped_numeric_summary(
        rows,
        group_fields=(
            "curve_type",
            "tenor",
            "half_window",
            "decision_type",
        ),
        value_field="window_change_bps",
        eligibility_field=("eligibility_status"),
        signed=True,
    )


def build_monthly_census(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build monthly sample-availability census without daily expansion."""

    grouped: dict[
        tuple[str, str],
        list[dict[str, str]],
    ] = defaultdict(list)

    for row in rows:
        grouped[
            (
                row["curve_type"],
                row["tenor"],
            )
        ].append(row)

    output = []

    for key in sorted(grouped):
        group_rows = grouped[key]

        periods = sorted(row["period"] for row in group_rows)

        row_count = len(group_rows)

        month_end_yields = sum(bool(row["month_end_yield_pct"]) for row in group_rows)

        monthly_changes = sum(
            bool(row["monthly_yield_change_bps"]) for row in group_rows
        )

        cpi_values = sum(bool(row["cpi_inflation_yoy_pct"]) for row in group_rows)

        output.append(
            {
                "curve_type": key[0],
                "tenor": key[1],
                "row_count": str(row_count),
                "first_period": (periods[0]),
                "last_period": (periods[-1]),
                "month_end_yield_count": str(month_end_yields),
                "monthly_yield_change_count": str(monthly_changes),
                "monthly_yield_change_missing_count": str(row_count - monthly_changes),
                "cpi_inflation_count": str(cpi_values),
                "cpi_inflation_missing_count": str(row_count - cpi_values),
            }
        )

    return output


def build_manifest(
    outputs: list[
        tuple[
            str,
            Path,
            str,
            str,
            str,
        ]
    ],
) -> list[dict[str, str]]:
    """Build deterministic descriptive-analysis manifest."""

    manifest = []

    for (
        family,
        path,
        grain,
        variable,
        eligibility,
    ) in outputs:
        _, rows = read_csv(path)

        manifest.append(
            {
                "descriptive_family": family,
                "artifact_path": str(display_path(path)),
                "grain": grain,
                "described_variable": variable,
                "group_count": str(len(rows)),
                "sha256": sha256_file(path),
                "eligibility_rule": eligibility,
                "analysis_type": ("DESCRIPTIVE_ONLY"),
            }
        )

    return manifest


def main() -> None:
    """Build all deterministic Phase 6A descriptive outputs."""

    loaded = load_inputs()

    yield_rows = loaded["yield"]["rows"]

    term_rows = loaded["term"]["rows"]

    cross_rows = loaded["cross"]["rows"]

    event_rows = loaded["event"]["rows"]

    monthly_rows = loaded["monthly"]["rows"]

    yield_levels = build_yield_level_summary(yield_rows)

    yield_changes = build_yield_change_summary(yield_rows)

    term_spreads = build_term_summary(term_rows)

    cross_curve = build_cross_summary(cross_rows)

    event_windows = build_event_summary(event_rows)

    monthly_census = build_monthly_census(monthly_rows)

    write_csv(
        OUTPUTS["yield_levels"],
        [
            "curve_type",
            "regime_label",
            "tenor",
            *BASIC_STATS_FIELDS,
        ],
        yield_levels,
    )

    write_csv(
        OUTPUTS["yield_changes"],
        [
            "curve_type",
            "regime_label",
            "tenor",
            *SIGNED_STATS_FIELDS,
        ],
        yield_changes,
    )

    write_csv(
        OUTPUTS["term_spreads"],
        [
            "spread_name",
            "regime_label",
            *SIGNED_STATS_FIELDS,
        ],
        term_spreads,
    )

    write_csv(
        OUTPUTS["cross_curve"],
        [
            "tenor",
            "regime_label",
            *SIGNED_STATS_FIELDS,
        ],
        cross_curve,
    )

    write_csv(
        OUTPUTS["event_windows"],
        [
            "curve_type",
            "tenor",
            "half_window",
            "decision_type",
            *SIGNED_STATS_FIELDS,
        ],
        event_windows,
    )

    write_csv(
        OUTPUTS["monthly_census"],
        [
            "curve_type",
            "tenor",
            "row_count",
            "first_period",
            "last_period",
            "month_end_yield_count",
            "monthly_yield_change_count",
            "monthly_yield_change_missing_count",
            "cpi_inflation_count",
            "cpi_inflation_missing_count",
        ],
        monthly_census,
    )

    manifest_rows = build_manifest(
        [
            (
                "yield_levels",
                OUTPUTS["yield_levels"],
                ("curve_type × regime_label × tenor"),
                "yield_pct",
                ("yield_level_regime_analysis_status=ELIGIBLE"),
            ),
            (
                "yield_changes",
                OUTPUTS["yield_changes"],
                ("curve_type × regime_label × tenor"),
                "yield_change_bps",
                ("yield_change_regime_analysis_status=ELIGIBLE"),
            ),
            (
                "term_spreads",
                OUTPUTS["term_spreads"],
                ("spread_name × regime_label"),
                "term_spread_bps",
                ("joint_analysis_status=ELIGIBLE"),
            ),
            (
                "cross_curve_differences",
                OUTPUTS["cross_curve"],
                ("tenor × regime_label"),
                ("pkisrv_minus_pkrv_bps"),
                ("paired_comparison_status=ELIGIBLE"),
            ),
            (
                "mpc_event_windows",
                OUTPUTS["event_windows"],
                ("curve_type × tenor × half_window × decision_type"),
                "window_change_bps",
                ("eligibility_status=ELIGIBLE"),
            ),
            (
                "monthly_sample_census",
                OUTPUTS["monthly_census"],
                ("curve_type × tenor"),
                ("sample availability / missingness"),
                ("no daily expansion; source monthly rows preserved"),
            ),
        ]
    )

    write_csv(
        OUTPUTS["manifest"],
        [
            "descriptive_family",
            "artifact_path",
            "grain",
            "described_variable",
            "group_count",
            "sha256",
            "eligibility_rule",
            "analysis_type",
        ],
        manifest_rows,
    )

    print("===== PHASE 6A DESCRIPTIVE TABLES =====")

    print("")
    print(
        "yield level groups:",
        len(yield_levels),
    )

    print(
        "yield change groups:",
        len(yield_changes),
    )

    print(
        "term spread groups:",
        len(term_spreads),
    )

    print(
        "cross-curve groups:",
        len(cross_curve),
    )

    print(
        "event-window groups:",
        len(event_windows),
    )

    print(
        "monthly census groups:",
        len(monthly_census),
    )

    print("")
    print("source observations represented")

    print(
        "yield levels n:",
        sum(int(row["n"]) for row in yield_levels),
    )

    print(
        "yield changes n:",
        sum(int(row["n"]) for row in yield_changes),
    )

    print(
        "term spreads n:",
        sum(int(row["n"]) for row in term_spreads),
    )

    print(
        "cross differences n:",
        sum(int(row["n"]) for row in cross_curve),
    )

    print(
        "event windows n:",
        sum(int(row["n"]) for row in event_windows),
    )

    print("")
    print("SHA256:")

    for name, path in OUTPUTS.items():
        print(
            name,
            sha256_file(path),
        )

    print("")
    print("PASS: deterministic Phase 6A descriptive baseline constructed")


if __name__ == "__main__":
    main()
