"""Read-only access to PakYield's frozen analytical presentation inputs."""

from __future__ import annotations

import csv
import hashlib
from functools import cache
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
RUNTIME_DIR: Final = PROJECT_ROOT / "data" / "runtime"


ARTIFACTS: Final = {
    "yield": {
        "path": RUNTIME_DIR / "yield_regime_analysis_panel.csv",
        "rows": 24815,
        "sha256": ("f8583955e1f30953b13d7a054c2df4e146063c7fcfcabe205fd9cc9b42158a30"),
    },
    "term_spread": {
        "path": RUNTIME_DIR / "term_spread_regime_analysis_panel.csv",
        "rows": 4596,
        "sha256": ("d9fd6633941ab2d8932200ba45ac2e8e2619c1d77cbe30e751458d75e75311dd"),
    },
    "cross_curve": {
        "path": RUNTIME_DIR / "cross_curve_regime_analysis_panel.csv",
        "rows": 2035,
        "sha256": ("2a286e2847081c6df654b6e13e71e3e07ce2e5249a4a2cef61f7e6fd5400c384"),
    },
    "mpc_event": {
        "path": RUNTIME_DIR / "mpc_event_window_panel.csv",
        "rows": 936,
        "sha256": ("b99224391fd254d3404ca7e0ce27073b2fdceee12cc0703a54af9b32e125472f"),
    },
    "monthly_cpi": {
        "path": RUNTIME_DIR / "monthly_cpi_yield_panel.csv",
        "rows": 1234,
        "sha256": ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
    },
    "manifest": {
        "path": RUNTIME_DIR / "analysis_input_manifest.csv",
        "rows": 5,
        "sha256": ("ec0fe1e6c43f2dfbf246e8120a777720858b82498beb741f08d11cdb8df17aa4"),
    },
}


class PresentationDataError(RuntimeError):
    """Raised when a frozen presentation artifact violates its contract."""


def _sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


@cache
def load_rows(
    family: str,
) -> tuple[dict[str, str], ...]:
    """Load and verify one frozen analytical family."""

    if family not in ARTIFACTS:
        raise KeyError(f"Unknown analytical family: {family}")

    spec = ARTIFACTS[family]
    path = spec["path"]

    if not path.is_file():
        raise PresentationDataError(f"Missing frozen analytical artifact: {path}")

    actual_sha = _sha256(path)

    if actual_sha != spec["sha256"]:
        raise PresentationDataError(f"Frozen analytical artifact SHA mismatch: {path}")

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = tuple(dict(row) for row in csv.DictReader(file))

    if len(rows) != spec["rows"]:
        raise PresentationDataError(
            "Frozen analytical artifact row-count mismatch: "
            f"{path}; expected={spec['rows']}; actual={len(rows)}"
        )

    return rows


def load_yield_rows() -> tuple[dict[str, str], ...]:
    """Return the frozen yield level/change analytical panel."""

    return load_rows("yield")


def load_term_spread_rows() -> tuple[dict[str, str], ...]:
    """Return the frozen term-spread analytical panel."""

    return load_rows("term_spread")


def load_cross_curve_rows() -> tuple[dict[str, str], ...]:
    """Return the frozen exact-date PKRV/PKISRV comparison panel."""

    return load_rows("cross_curve")


def load_mpc_event_rows() -> tuple[dict[str, str], ...]:
    """Return the frozen MPC event-window panel."""

    return load_rows("mpc_event")


def load_monthly_cpi_rows() -> tuple[dict[str, str], ...]:
    """Return the frozen monthly CPI/yield panel."""

    return load_rows("monthly_cpi")


def load_analysis_manifest() -> tuple[dict[str, str], ...]:
    """Return the frozen five-family analysis manifest."""

    return load_rows("manifest")


def latest_curve_snapshot(
    curve_type: str,
    *,
    eligible_only: bool = True,
) -> tuple[dict[str, str], ...]:
    """Return the latest actual observed curve without interpolation."""

    rows = [
        row
        for row in load_yield_rows()
        if row["curve_type"] == curve_type
        and (
            not eligible_only or row["yield_level_regime_analysis_status"] == "ELIGIBLE"
        )
    ]

    if not rows:
        return ()

    latest_date = max(row["observation_date"] for row in rows)

    snapshot = [row for row in rows if row["observation_date"] == latest_date]

    return tuple(
        sorted(
            snapshot,
            key=lambda row: float(row["tenor_years"]),
        )
    )


def latest_observed_yield(
    curve_type: str,
    tenor: str,
    *,
    eligible_only: bool = True,
) -> dict[str, str] | None:
    """Return the latest actual observation for one curve and tenor."""

    rows = [
        row
        for row in load_yield_rows()
        if row["curve_type"] == curve_type
        and row["tenor"] == tenor
        and (
            not eligible_only or row["yield_level_regime_analysis_status"] == "ELIGIBLE"
        )
    ]

    if not rows:
        return None

    return max(
        rows,
        key=lambda row: row["observation_date"],
    )


def latest_term_spread(
    spread_name: str,
    *,
    eligible_only: bool = True,
) -> dict[str, str] | None:
    """Return the latest observed PKRV term spread."""

    rows = [
        row
        for row in load_term_spread_rows()
        if row["spread_name"] == spread_name
        and (not eligible_only or row["joint_analysis_status"] == "ELIGIBLE")
    ]

    if not rows:
        return None

    return max(
        rows,
        key=lambda row: row["observation_date"],
    )


def latest_policy_context() -> dict[str, str] | None:
    """Return latest exact-date policy context represented in yield data."""

    rows = load_yield_rows()

    if not rows:
        return None

    latest_date = max(row["observation_date"] for row in rows)

    candidates = [row for row in rows if row["observation_date"] == latest_date]

    if not candidates:
        return None

    first = candidates[0]

    signature = (
        first["policy_rate_pct"],
        first["regime_label"],
        first["regime_analysis_status"],
    )

    for row in candidates[1:]:
        if (
            row["policy_rate_pct"],
            row["regime_label"],
            row["regime_analysis_status"],
        ) != signature:
            raise PresentationDataError(
                "Latest-date policy/regime context is inconsistent."
            )

    return {
        "observation_date": latest_date,
        "policy_rate_pct": first["policy_rate_pct"],
        "regime_label": first["regime_label"],
        "regime_analysis_status": first["regime_analysis_status"],
    }


def eligible_event_windows() -> tuple[dict[str, str], ...]:
    """Return only source-declared eligible MPC event-window rows."""

    return tuple(
        row for row in load_mpc_event_rows() if row["eligibility_status"] == "ELIGIBLE"
    )


def eligible_cross_curve_rows() -> tuple[dict[str, str], ...]:
    """Return only frozen eligible exact-date paired comparisons."""

    return tuple(
        row
        for row in load_cross_curve_rows()
        if row["paired_comparison_status"] == "ELIGIBLE"
    )
