"""Verified, read-only econometrics data services for Streamlit.

No statistical estimation is performed in the presentation layer.
All numerical research results originate from audited artifacts.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from . import data as core_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTERIM = PROJECT_ROOT / "data" / "interim"


class EconometricsDataError(RuntimeError):
    """An analytical artifact failed its integrity contract."""


ARTIFACTS = {
    "inferential_manifest": {
        "filename": "inferential_diagnostics_manifest.csv",
        "rows": 7,
        "sha256": ("e059f18c249746136c02b20c593504408df4e873eca2b888209add7465473420"),
    },
    "correlations": {
        "filename": "phase10_correlation_diagnostics.csv",
        "rows": 68,
        "sha256": ("a143879d7cb2b13f1b8a3e4f4035d63ec085c581d920c9b8395758799d3ce97e"),
    },
    "adf": {
        "filename": "phase10_adf_stationarity.csv",
        "rows": 59,
        "sha256": ("bfccaa58ce21da2881f987ce9744eab7e2a63885de772e9545cf3570d53190e1"),
    },
    "vif": {
        "filename": "inferential_vif_diagnostics.csv",
        "rows": 59,
        "sha256": ("e896b23b815a45379954830b4daa458429ef575fbe705172895510c092ce64a4"),
    },
    "vif_manifest": {
        "filename": "inferential_vif_manifest.csv",
        "rows": 7,
        "sha256": ("f1224edf9111e3c8cdc2d71a4b69d827f5249891af0e208b87f74aa37f3c2b07"),
    },
    "residuals": {
        "filename": "phase10_regression_residual_diagnostics.csv",
        "rows": 59,
        "sha256": ("949abc4175515a16f8df9b91230123a7985cffece8491cdac729efdb1fa2a8a7"),
    },
}


INFERENTIAL_FAMILIES = (
    "yield_level_regime",
    "yield_change_regime",
    "term_spread_regime",
    "cross_curve_zero",
    "cross_curve_regime",
    "mpc_event_window",
    "monthly_cpi_yield",
)


def sha256_file(path: Path) -> str:
    """Hash a source artifact without modifying it."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_verified(
    path: Path,
    expected_sha: str,
    expected_rows: int,
) -> tuple[dict[str, str], ...]:
    """Fail closed if source bytes or row counts differ."""

    if not path.is_file():
        raise EconometricsDataError(f"Missing analytical artifact: {path}")

    actual_sha = sha256_file(path)

    if actual_sha != expected_sha:
        raise EconometricsDataError(f"Analytical artifact SHA mismatch: {path}")

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise EconometricsDataError(f"Missing CSV headers: {path}")

        rows = tuple(dict(row) for row in reader)

    if len(rows) != expected_rows:
        raise EconometricsDataError(
            f"Analytical row-count mismatch: {path}; "
            f"expected={expected_rows}; actual={len(rows)}"
        )

    return rows


def load_artifact(
    name: str,
) -> tuple[dict[str, str], ...]:
    """Load a statically registered and frozen artifact."""

    if name not in ARTIFACTS:
        raise KeyError(f"Unknown econometrics artifact: {name}")

    specification = ARTIFACTS[name]

    path = INTERIM / specification["filename"]

    return read_verified(
        path,
        specification["sha256"],
        specification["rows"],
    )


def load_inferential_manifest() -> tuple[dict[str, str], ...]:
    """Return seven validated inferential families."""

    rows = load_artifact("inferential_manifest")

    observed = {row["family"] for row in rows}

    if observed != set(INFERENTIAL_FAMILIES):
        raise EconometricsDataError("Inferential family universe changed")

    return rows


def load_inferential_family(
    family: str,
) -> tuple[dict[str, str], ...]:
    """Load one inferential family using its audited manifest."""

    if family not in INFERENTIAL_FAMILIES:
        raise KeyError(f"Unknown inferential family: {family}")

    manifest = {row["family"]: row for row in load_inferential_manifest()}

    specification = manifest[family]

    if specification["diagnostic_status"] != "PASS":
        raise EconometricsDataError(f"Inferential family not accepted: {family}")

    relative_path = Path(specification["artifact_path"])

    if relative_path.is_absolute():
        raise EconometricsDataError("Absolute inferential artifact path rejected")

    path = (PROJECT_ROOT / relative_path).resolve()

    if not path.is_relative_to(INTERIM.resolve()) or path.suffix.lower() != ".csv":
        raise EconometricsDataError(f"Invalid inferential artifact path: {path}")

    return read_verified(
        path,
        specification["artifact_sha256"],
        int(specification["total_rows"]),
    )


def load_correlation_diagnostics() -> tuple[dict[str, str], ...]:
    """Return observed, precomputed correlation results."""

    return load_artifact("correlations")


def load_adf_diagnostics() -> tuple[dict[str, str], ...]:
    """Return precomputed stationarity diagnostics."""

    return load_artifact("adf")


def load_vif_diagnostics() -> tuple[dict[str, str], ...]:
    """Return precomputed model VIF diagnostics."""

    return load_artifact("vif")


def load_residual_diagnostics() -> tuple[dict[str, str], ...]:
    """Return precomputed residual-model diagnostics."""

    return load_artifact("residuals")


def load_macro_monthly_series(
    curve_type: str,
    tenor: str,
    *,
    complete_only: bool = True,
) -> tuple[dict[str, str], ...]:
    """Return actual calendar-month CPI/yield observations.

    This never expands monthly observations into daily rows.
    """

    rows = []

    for row in core_data.load_monthly_cpi_rows():
        if row["curve_type"] != curve_type:
            continue

        if row["tenor"] != tenor:
            continue

        if complete_only and not (
            row["month_end_yield_pct"] and row["cpi_inflation_yoy_pct"]
        ):
            continue

        rows.append(row)

    return tuple(
        sorted(
            rows,
            key=lambda item: item["period"],
        )
    )


def correlation_table(
    *,
    family: str | None = None,
    curve_type: str | None = None,
    regime_label: str | None = None,
) -> tuple[dict[str, str], ...]:
    """Filter observed correlations without computing new ones."""

    rows = []

    for row in load_correlation_diagnostics():
        if family is not None and row["family"] != family:
            continue

        if curve_type is not None and row["curve_type"] != curve_type:
            continue

        if regime_label is not None and row["regime_label"] != regime_label:
            continue

        rows.append(row)

    return tuple(rows)


def regression_table(
    family: str,
) -> tuple[dict[str, str], ...]:
    """Return frozen inferential tests, including exclusions.

    This service preserves precomputed p-values, HAC settings,
    confidence intervals and analytical statuses.
    """

    return load_inferential_family(family)
