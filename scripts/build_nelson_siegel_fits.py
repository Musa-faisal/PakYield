"""Build deterministic production Nelson-Siegel curve fits."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pakyield.analytics.nelson_siegel import (
    FIT_STATUS_FIT,
    FIT_STATUS_INELIGIBLE,
    GLOBAL_DECAY_LAMBDA,
    fit_nelson_siegel_fixed_decay,
)
from pakyield.config import (
    DATABASE_PATH,
    PROJECT_ROOT,
)
from pakyield.database.connection import (
    get_connection,
)

DATE_OUTPUT = PROJECT_ROOT / "data" / "interim" / "nelson_siegel_date_fits.csv"

POINT_OUTPUT = PROJECT_ROOT / "data" / "interim" / "nelson_siegel_fitted_yields.csv"

EXPECTED_SOURCE_ROWS = 24815

EXPECTED_CURVE_ROWS = {
    "PKRV": 22800,
    "PKISRV": 2015,
}

EXPECTED_CURVE_DATES = {
    "PKRV": 1149,
    "PKISRV": 403,
}

EXPECTED_DATE_STATUS = {
    ("PKRV", "FIT"): 1149,
    ("PKISRV", "INELIGIBLE"): 403,
}

EXPECTED_POINT_STATUS = {
    ("PKRV", "FIT"): 22800,
    ("PKISRV", "INELIGIBLE"): 2015,
}

PKISRV_EXPECTED_REASON = "POINTS_LT_10;NO_BELLY;NO_LONG;SPAN_LT_15Y"

DATE_FIELDS = [
    "observation_date",
    "curve_type",
    "fit_status",
    "ineligibility_reason",
    "n_points",
    "n_distinct_maturities",
    "min_maturity_years",
    "max_maturity_years",
    "maturity_span_years",
    "decay_lambda",
    "beta0",
    "beta1",
    "beta2",
    "rmse_pct_points",
    "design_rank",
    "design_condition_number",
    "fit_method",
]

POINT_FIELDS = [
    "yield_observation_id",
    "observation_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "observed_yield_pct",
    "fit_status",
    "ineligibility_reason",
    "decay_lambda",
    "beta0",
    "beta1",
    "beta2",
    "fitted_yield_pct",
    "residual_pct_points",
    "source_organization",
    "source_file",
    "ingestion_run_id",
]


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 for one file."""

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
    """Return repository-relative output path when possible."""

    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT)

    return path


def fmt_float(
    value: float | None,
) -> str:
    """Serialize model output deterministically."""

    if value is None:
        return ""

    return format(
        value,
        ".12f",
    )


def write_csv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Write one CSV atomically."""

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


def load_source_rows() -> list[dict[str, Any]]:
    """Load the normalized production yield universe."""

    connection = get_connection(DATABASE_PATH)

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

        rows = connection.execute(
            """
            SELECT
                yield_observation_id,
                observation_date,
                curve_type,
                tenor,
                tenor_years,
                yield_pct,
                source_organization,
                source_file,
                ingestion_run_id
            FROM yield_observations
            ORDER BY
                curve_type,
                observation_date,
                tenor_years,
                tenor
            """
        ).fetchall()

    finally:
        connection.close()

    if integrity != "ok":
        raise RuntimeError("SQLite integrity check failed")

    if foreign_key_issues:
        raise RuntimeError("SQLite foreign-key issues detected")

    output = [{key: row[key] for key in row.keys()} for row in rows]

    if len(output) != EXPECTED_SOURCE_ROWS:
        raise RuntimeError(f"Unexpected yield source row count: {len(output)}")

    curve_rows = Counter(str(row["curve_type"]) for row in output)

    if dict(curve_rows) != (EXPECTED_CURVE_ROWS):
        raise RuntimeError(f"Unexpected curve row census: {dict(curve_rows)}")

    return output


def build_outputs(
    source_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
]:
    """Construct date-level and point-level Nelson-Siegel outputs."""

    grouped: dict[
        tuple[str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)

    for row in source_rows:
        grouped[
            (
                str(row["curve_type"]),
                str(row["observation_date"]),
            )
        ].append(row)

    curve_date_counts = Counter(
        curve_type
        for (
            curve_type,
            _observation_date,
        ) in grouped
    )

    if dict(curve_date_counts) != EXPECTED_CURVE_DATES:
        raise RuntimeError(f"Unexpected curve-date census: {dict(curve_date_counts)}")

    date_rows: list[dict[str, str]] = []

    point_rows: list[dict[str, str]] = []

    for (
        curve_type,
        observation_date,
    ) in sorted(grouped):
        rows = sorted(
            grouped[
                (
                    curve_type,
                    observation_date,
                )
            ],
            key=lambda row: (
                float(row["tenor_years"]),
                str(row["tenor"]),
            ),
        )

        maturities = [float(row["tenor_years"]) for row in rows]

        yields_pct = [float(row["yield_pct"]) for row in rows]

        result = fit_nelson_siegel_fixed_decay(
            maturities,
            yields_pct,
        )

        eligibility = result.eligibility

        date_rows.append(
            {
                "observation_date": (observation_date),
                "curve_type": (curve_type),
                "fit_status": (result.status),
                "ineligibility_reason": (result.ineligibility_reason),
                "n_points": str(eligibility.n_points),
                "n_distinct_maturities": str(eligibility.n_distinct_maturities),
                "min_maturity_years": (fmt_float(eligibility.min_maturity_years)),
                "max_maturity_years": (fmt_float(eligibility.max_maturity_years)),
                "maturity_span_years": (fmt_float(eligibility.maturity_span_years)),
                "decay_lambda": (fmt_float(result.decay_lambda)),
                "beta0": (fmt_float(result.beta0)),
                "beta1": (fmt_float(result.beta1)),
                "beta2": (fmt_float(result.beta2)),
                "rmse_pct_points": (fmt_float(result.rmse_pct_points)),
                "design_rank": (
                    "" if result.design_rank is None else str(result.design_rank)
                ),
                "design_condition_number": (fmt_float(result.design_condition_number)),
                "fit_method": (result.fit_method),
            }
        )

        if result.status == FIT_STATUS_FIT:
            if len(result.fitted_yields) != len(rows):
                raise RuntimeError("Fitted-yield count does not match source rows")

            if len(result.residuals) != len(rows):
                raise RuntimeError("Residual count does not match source rows")

        for index, row in enumerate(rows):
            if result.status == FIT_STATUS_FIT:
                fitted = result.fitted_yields[index]

                residual = result.residuals[index]

            else:
                fitted = None
                residual = None

            point_rows.append(
                {
                    "yield_observation_id": str(row["yield_observation_id"]),
                    "observation_date": (observation_date),
                    "curve_type": (curve_type),
                    "tenor": str(row["tenor"]),
                    "tenor_years": str(row["tenor_years"]),
                    "observed_yield_pct": str(row["yield_pct"]),
                    "fit_status": (result.status),
                    "ineligibility_reason": (result.ineligibility_reason),
                    "decay_lambda": (fmt_float(result.decay_lambda)),
                    "beta0": (fmt_float(result.beta0)),
                    "beta1": (fmt_float(result.beta1)),
                    "beta2": (fmt_float(result.beta2)),
                    "fitted_yield_pct": (fmt_float(fitted)),
                    "residual_pct_points": (fmt_float(residual)),
                    "source_organization": str(row["source_organization"]),
                    "source_file": (
                        "" if row["source_file"] is None else str(row["source_file"])
                    ),
                    "ingestion_run_id": (
                        ""
                        if row["ingestion_run_id"] is None
                        else str(row["ingestion_run_id"])
                    ),
                }
            )

    return (
        date_rows,
        point_rows,
    )


def validate_outputs(
    date_rows: list[dict[str, str]],
    point_rows: list[dict[str, str]],
) -> None:
    """Fail closed on production census or contract drift."""

    if len(date_rows) != 1552:
        raise RuntimeError(f"Unexpected date-fit row count: {len(date_rows)}")

    if len(point_rows) != EXPECTED_SOURCE_ROWS:
        raise RuntimeError(f"Unexpected point-fit row count: {len(point_rows)}")

    date_status = Counter(
        (
            row["curve_type"],
            row["fit_status"],
        )
        for row in date_rows
    )

    if dict(date_status) != (EXPECTED_DATE_STATUS):
        raise RuntimeError(f"Unexpected date status census: {dict(date_status)}")

    point_status = Counter(
        (
            row["curve_type"],
            row["fit_status"],
        )
        for row in point_rows
    )

    if dict(point_status) != (EXPECTED_POINT_STATUS):
        raise RuntimeError(f"Unexpected point status census: {dict(point_status)}")

    failed = [
        row
        for row in date_rows
        if row["fit_status"]
        not in {
            FIT_STATUS_FIT,
            FIT_STATUS_INELIGIBLE,
        }
    ]

    if failed:
        raise RuntimeError("Unexpected Nelson-Siegel fit failures")

    pkrv = [row for row in date_rows if row["curve_type"] == "PKRV"]

    if not all(row["design_rank"] == "3" for row in pkrv):
        raise RuntimeError("PKRV design-rank failure detected")

    if not all(float(row["design_condition_number"]) < 100.0 for row in pkrv):
        raise RuntimeError("Unexpected PKRV conditioning")

    pkisrv = [row for row in date_rows if row["curve_type"] == "PKISRV"]

    if not all(row["ineligibility_reason"] == PKISRV_EXPECTED_REASON for row in pkisrv):
        raise RuntimeError("PKISRV structural-exclusion reason changed")

    if any(
        row["beta0"] or row["beta1"] or row["beta2"] or row["rmse_pct_points"]
        for row in pkisrv
    ):
        raise RuntimeError("Ineligible PKISRV date contains fit values")

    pkisrv_points = [row for row in point_rows if row["curve_type"] == "PKISRV"]

    if any(
        row["fitted_yield_pct"] or row["residual_pct_points"] for row in pkisrv_points
    ):
        raise RuntimeError("Ineligible PKISRV point contains fit values")


def main() -> None:
    """Build deterministic Phase 12 production outputs."""

    source_rows = load_source_rows()

    (
        date_rows,
        point_rows,
    ) = build_outputs(source_rows)

    validate_outputs(
        date_rows,
        point_rows,
    )

    write_csv(
        DATE_OUTPUT,
        DATE_FIELDS,
        date_rows,
    )

    write_csv(
        POINT_OUTPUT,
        POINT_FIELDS,
        point_rows,
    )

    status = Counter(
        (
            row["curve_type"],
            row["fit_status"],
        )
        for row in date_rows
    )

    pkrv_rmse = [
        float(row["rmse_pct_points"])
        for row in date_rows
        if (row["curve_type"] == "PKRV" and row["fit_status"] == "FIT")
    ]

    print("===== NELSON-SIEGEL PRODUCTION FITS =====")

    print(
        "fixed_decay_lambda:",
        GLOBAL_DECAY_LAMBDA,
    )

    print(
        "date_rows:",
        len(date_rows),
    )

    print(
        "point_rows:",
        len(point_rows),
    )

    print(
        "date_status:",
        dict(status),
    )

    print(
        "PKRV_RMSE_MIN:",
        min(pkrv_rmse),
    )

    print(
        "PKRV_RMSE_MAX:",
        max(pkrv_rmse),
    )

    print(
        "date_output:",
        display_path(DATE_OUTPUT),
    )

    print(
        "date_sha256:",
        sha256_file(DATE_OUTPUT),
    )

    print(
        "point_output:",
        display_path(POINT_OUTPUT),
    )

    print(
        "point_sha256:",
        sha256_file(POINT_OUTPUT),
    )

    print("")
    print("PASS: deterministic D105 Nelson-Siegel production outputs constructed")


if __name__ == "__main__":
    main()
