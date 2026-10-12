"""Audit frozen inferential-analysis outputs for internal statistical consistency."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter
from pathlib import Path

from pakyield.config import PROJECT_ROOT

MANIFEST_PATH = PROJECT_ROOT / "data" / "interim" / "inferential_analysis_manifest.csv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "inferential_diagnostics_manifest.csv"

EXPECTED_FAMILIES = (
    "yield_level_regime",
    "yield_change_regime",
    "term_spread_regime",
    "cross_curve_zero",
    "cross_curve_regime",
    "mpc_event_window",
    "monthly_cpi_yield",
)

INFERENTIAL_FAMILIES = {
    "yield_level_regime",
    "yield_change_regime",
    "term_spread_regime",
    "cross_curve_zero",
    "cross_curve_regime",
    "mpc_event_window",
}

EXPECTED_REJECT_COUNTS = {
    "yield_level_regime": {
        "reject": 24,
        "do_not_reject": 1,
    },
    "yield_change_regime": {
        "reject": 10,
        "do_not_reject": 15,
    },
    "term_spread_regime": {
        "reject": 4,
        "do_not_reject": 0,
    },
    "cross_curve_zero": {
        "reject": 5,
        "do_not_reject": 0,
    },
    "cross_curve_regime": {
        "reject": 4,
        "do_not_reject": 1,
    },
    "mpc_event_window": {
        "reject": 0,
        "do_not_reject": 54,
    },
}

EXPECTED_STATUS_COUNTS = {
    "yield_level_regime": {
        "INFERENTIAL": 25,
    },
    "yield_change_regime": {
        "INFERENTIAL": 25,
    },
    "term_spread_regime": {
        "INFERENTIAL": 4,
    },
    "cross_curve_zero": {
        "INFERENTIAL": 5,
    },
    "cross_curve_regime": {
        "INFERENTIAL": 5,
    },
    "mpc_event_window": {
        "INFERENTIAL": 54,
        "DESCRIPTIVE_ONLY": 18,
    },
    "monthly_cpi_yield": {
        "DESCRIPTIVE_ONLY": 1234,
    },
}

EXPECTED_SAMPLE_RANGES = {
    "yield_level_regime": (390, 1048),
    "yield_change_regime": (389, 1048),
    "term_spread_regime": (1020, 1048),
    "cross_curve_zero": (388, 388),
    "cross_curve_regime": (388, 388),
    "mpc_event_window": (8, 22),
}

OUTPUT_FIELDS = [
    "family",
    "artifact_path",
    "artifact_sha256",
    "total_rows",
    "inferential_rows",
    "descriptive_only_rows",
    "reject_count",
    "do_not_reject_count",
    "min_sample_size",
    "max_sample_size",
    "hac_lag_values",
    "bh_max_abs_diff",
    "bh_reject_reconciliation",
    "diagnostic_status",
]


def sha256_file(path: Path) -> str:
    """Return SHA-256 of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
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


def find_field(
    headers: list[str],
    candidates: tuple[str, ...],
    *,
    required: bool = True,
) -> str | None:
    """Find the first compatible field name."""

    for candidate in candidates:
        if candidate in headers:
            return candidate

    if required:
        raise RuntimeError(
            "Could not locate required field. "
            f"Candidates={candidates}; headers={headers}"
        )

    return None


def parse_bool(value: str) -> bool:
    """Parse serialized Boolean values."""

    normalized = value.strip().lower()

    if normalized in {
        "true",
        "1",
        "yes",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
    }:
        return False

    raise RuntimeError(f"Unexpected Boolean representation: {value!r}")


def benjamini_hochberg(
    p_values: list[float],
) -> list[float]:
    """Recompute Benjamini-Hochberg adjusted p-values."""

    count = len(p_values)

    if count == 0:
        return []

    ordered = sorted(
        enumerate(p_values),
        key=lambda pair: pair[1],
    )

    adjusted = [0.0] * count

    running_minimum = 1.0

    for reverse_rank in range(
        count,
        0,
        -1,
    ):
        original_index, p_value = ordered[reverse_rank - 1]

        candidate = p_value * count / reverse_rank

        running_minimum = min(
            running_minimum,
            candidate,
            1.0,
        )

        adjusted[original_index] = running_minimum

    return adjusted


def main() -> None:
    """Run the complete Phase 6C inferential diagnostics audit."""

    manifest_headers, manifest_rows = read_csv(MANIFEST_PATH)

    required_manifest_headers = {
        "family",
        "artifact_path",
        "row_count",
        "inferential_test_count",
        "descriptive_only_count",
        "sha256",
        "method",
        "multiple_testing_rule",
    }

    if set(manifest_headers) != required_manifest_headers:
        raise RuntimeError("Unexpected inferential manifest schema")

    families = tuple(row["family"] for row in manifest_rows)

    if families != EXPECTED_FAMILIES:
        raise RuntimeError(f"Unexpected inferential family order/universe: {families}")

    output_rows: list[dict[str, str]] = []

    for manifest in manifest_rows:
        family = manifest["family"]

        artifact = PROJECT_ROOT / manifest["artifact_path"]

        if not artifact.is_file():
            raise RuntimeError(f"Missing inferential artifact: {artifact}")

        artifact_sha = sha256_file(artifact)

        if artifact_sha != manifest["sha256"]:
            raise RuntimeError(f"Inferential artifact SHA mismatch: {artifact}")

        headers, rows = read_csv(artifact)

        if len(rows) != int(manifest["row_count"]):
            raise RuntimeError(f"Manifest row-count mismatch: {family}")

        if family == "monthly_cpi_yield":
            status_counts = {"DESCRIPTIVE_ONLY": (len(rows))}

            if status_counts != (EXPECTED_STATUS_COUNTS[family]):
                raise RuntimeError("Monthly descriptive census changed")

            output_rows.append(
                {
                    "family": family,
                    "artifact_path": (manifest["artifact_path"]),
                    "artifact_sha256": (artifact_sha),
                    "total_rows": str(len(rows)),
                    "inferential_rows": "0",
                    "descriptive_only_rows": str(len(rows)),
                    "reject_count": "0",
                    "do_not_reject_count": "0",
                    "min_sample_size": "",
                    "max_sample_size": "",
                    "hac_lag_values": "",
                    "bh_max_abs_diff": "",
                    "bh_reject_reconciliation": ("NOT_APPLICABLE"),
                    "diagnostic_status": "PASS",
                }
            )

            continue

        status_field = find_field(
            headers,
            (
                "analysis_status",
                "inferential_status",
                "status",
            ),
        )

        test_id_field = find_field(
            headers,
            (
                "test_id",
                "analysis_id",
            ),
        )

        sample_size_field = find_field(
            headers,
            (
                "sample_size",
                "n",
                "sample_n",
                "sample_n",
            ),
        )

        p_value_field = find_field(
            headers,
            (
                "p_value_raw",
                "p_value",
                "pvalue",
            ),
        )

        adjusted_field = find_field(
            headers,
            (
                "p_value_bh",
                "bh_adjusted_p_value",
                "adjusted_p_value",
                "p_value_adjusted",
            ),
        )

        reject_field = find_field(
            headers,
            (
                "reject_bh_0_05",
                "reject_null",
                "reject_h0",
            ),
        )

        hac_field = find_field(
            headers,
            (
                "hac_lags",
                "hac_lag",
                "maxlags",
            ),
            required=False,
        )

        status_counts = Counter(row[status_field] for row in rows)

        if dict(status_counts) != (EXPECTED_STATUS_COUNTS[family]):
            raise RuntimeError(
                f"Inferential status census changed: {family} {dict(status_counts)}"
            )

        test_ids = [row[test_id_field] for row in rows]

        if len(test_ids) != len(set(test_ids)):
            raise RuntimeError(f"Duplicate test IDs: {family}")

        inferential_rows = [row for row in rows if row[status_field] == "INFERENTIAL"]

        descriptive_rows = [
            row for row in rows if row[status_field] == "DESCRIPTIVE_ONLY"
        ]

        for row in descriptive_rows:
            for field in (
                p_value_field,
                adjusted_field,
                reject_field,
            ):
                if row[field]:
                    raise RuntimeError(
                        f"Descriptive-only row contains inferential result: {family}"
                    )

        p_values = [float(row[p_value_field]) for row in inferential_rows]

        stored_adjusted = [float(row[adjusted_field]) for row in inferential_rows]

        recomputed_adjusted = benjamini_hochberg(p_values)

        max_abs_diff = max(
            (
                abs(observed - expected)
                for (
                    observed,
                    expected,
                ) in zip(
                    stored_adjusted,
                    recomputed_adjusted,
                    strict=True,
                )
            ),
            default=0.0,
        )

        if not math.isclose(
            max_abs_diff,
            0.0,
            abs_tol=1e-12,
        ):
            raise RuntimeError(
                f"BH adjusted p-values differ: {family} max_diff={max_abs_diff}"
            )

        reject_values = [parse_bool(row[reject_field]) for row in inferential_rows]

        expected_reject_values = [
            adjusted <= 0.05 for adjusted in (recomputed_adjusted)
        ]

        if reject_values != (expected_reject_values):
            raise RuntimeError(
                f"Reject flags do not match BH adjusted p<=0.05: {family}"
            )

        reject_count = sum(reject_values)

        do_not_reject_count = len(reject_values) - reject_count

        expected_rejects = EXPECTED_REJECT_COUNTS[family]

        if reject_count != (expected_rejects["reject"]):
            raise RuntimeError(f"Reject census changed: {family}")

        if do_not_reject_count != (expected_rejects["do_not_reject"]):
            raise RuntimeError(f"Do-not-reject census changed: {family}")

        sample_sizes = [int(row[sample_size_field]) for row in inferential_rows]

        minimum_n = min(sample_sizes)

        maximum_n = max(sample_sizes)

        if (
            minimum_n,
            maximum_n,
        ) != EXPECTED_SAMPLE_RANGES[family]:
            raise RuntimeError(f"Sample-size range changed: {family}")

        hac_values: list[str] = []

        if family != "mpc_event_window":
            if hac_field is None:
                raise RuntimeError(f"HAC family lacks explicit lag field: {family}")

            if not all(row[hac_field] for row in inferential_rows):
                raise RuntimeError(f"HAC inferential row missing lag: {family}")

            hac_values = sorted(
                {row[hac_field] for row in (inferential_rows)},
                key=int,
            )

        if family == "mpc_event_window":
            for row in rows:
                n = int(row[sample_size_field])

                expected_status = "INFERENTIAL" if n >= 5 else "DESCRIPTIVE_ONLY"

                if row[status_field] != expected_status:
                    raise RuntimeError("MPC n>=5 threshold contract changed")

        if manifest["multiple_testing_rule"] != ("BENJAMINI_HOCHBERG_WITHIN_FAMILY"):
            raise RuntimeError(f"Unexpected multiple-testing rule: {family}")

        output_rows.append(
            {
                "family": family,
                "artifact_path": (manifest["artifact_path"]),
                "artifact_sha256": (artifact_sha),
                "total_rows": str(len(rows)),
                "inferential_rows": str(len(inferential_rows)),
                "descriptive_only_rows": str(len(descriptive_rows)),
                "reject_count": str(reject_count),
                "do_not_reject_count": str(do_not_reject_count),
                "min_sample_size": str(minimum_n),
                "max_sample_size": str(maximum_n),
                "hac_lag_values": (",".join(hac_values)),
                "bh_max_abs_diff": (f"{max_abs_diff:.12g}"),
                "bh_reject_reconciliation": ("PASS"),
                "diagnostic_status": "PASS",
            }
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_FIELDS,
        )

        writer.writeheader()

        writer.writerows(output_rows)

    temporary.replace(OUTPUT_PATH)

    print("===== PHASE 6C INFERENTIAL DIAGNOSTICS =====")

    for row in output_rows:
        print("")
        print(row["family"])
        print(
            "  inferential:",
            row["inferential_rows"],
        )
        print(
            "  descriptive_only:",
            row["descriptive_only_rows"],
        )
        print(
            "  reject:",
            row["reject_count"],
        )
        print(
            "  do_not_reject:",
            row["do_not_reject_count"],
        )
        print(
            "  n_range:",
            (row["min_sample_size"] or "NA"),
            "to",
            (row["max_sample_size"] or "NA"),
        )
        print(
            "  hac_lags:",
            (row["hac_lag_values"] or "NA"),
        )
        print(
            "  diagnostic:",
            row["diagnostic_status"],
        )

    print("")
    print(
        "Output:",
        (
            OUTPUT_PATH.relative_to(PROJECT_ROOT)
            if OUTPUT_PATH.is_relative_to(PROJECT_ROOT)
            else OUTPUT_PATH
        ),
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print("PASS: Phase 6C inferential diagnostics contract satisfied")


if __name__ == "__main__":
    main()
