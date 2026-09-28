"""Central configuration for PakYield Lab.

This module contains stable project paths and research definitions that are
shared across ingestion, validation, analytics, database, and application code.

Do not place secrets in this file.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MUFAP_RAW_DIR = RAW_DATA_DIR / "mufap"
PAKDATAHUB_RAW_DIR = RAW_DATA_DIR / "pakdatahub"
SBP_RAW_DIR = RAW_DATA_DIR / "sbp"
PBS_RAW_DIR = RAW_DATA_DIR / "pbs"

NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

DATABASE_PATH = PROCESSED_DATA_DIR / "pakyield.sqlite3"


# ---------------------------------------------------------------------------
# Dataset identifiers
# ---------------------------------------------------------------------------

DATASET_PKRV = "PKRV"
DATASET_PKISRV = "PKISRV"
DATASET_POLICY_RATE = "SBP_POLICY_RATE"
DATASET_MPC_EVENTS = "SBP_MPC_EVENTS"
DATASET_CPI = "PBS_CPI"


# ---------------------------------------------------------------------------
# PKRV tenor definitions
# ---------------------------------------------------------------------------

PKRV_CANONICAL_TENORS = (
    "1W",
    "2W",
    "1M",
    "2M",
    "3M",
    "4M",
    "6M",
    "9M",
    "1Y",
    "2Y",
    "3Y",
    "4Y",
    "5Y",
    "6Y",
    "7Y",
    "8Y",
    "9Y",
    "10Y",
    "15Y",
    "20Y",
)

PKRV_FOCAL_TENORS = (
    "3M",
    "6M",
    "1Y",
    "2Y",
    "3Y",
    "5Y",
    "10Y",
    "15Y",
    "20Y",
)


# ---------------------------------------------------------------------------
# PKRV / PKISRV comparison universe
# ---------------------------------------------------------------------------

PKRV_PKISRV_COMMON_TENORS = (
    "1M",
    "3M",
    "6M",
    "9M",
    "1Y",
)

# ---------------------------------------------------------------------------
# Canonical tenor-to-years mapping
# ---------------------------------------------------------------------------

TENOR_TO_YEARS = {
    "1W": 7 / 365,
    "2W": 14 / 365,
    "1M": 1 / 12,
    "2M": 2 / 12,
    "3M": 3 / 12,
    "4M": 4 / 12,
    "6M": 6 / 12,
    "9M": 9 / 12,
    "1Y": 1.0,
    "2Y": 2.0,
    "3Y": 3.0,
    "4Y": 4.0,
    "5Y": 5.0,
    "6Y": 6.0,
    "7Y": 7.0,
    "8Y": 8.0,
    "9Y": 9.0,
    "10Y": 10.0,
    "15Y": 15.0,
    "20Y": 20.0,
}

# ---------------------------------------------------------------------------
# Preferred curve spreads
# ---------------------------------------------------------------------------

TERM_SPREADS = {
    "10Y-2Y": ("10Y", "2Y"),
    "10Y-1Y": ("10Y", "1Y"),
    "5Y-1Y": ("5Y", "1Y"),
    "3Y-3M": ("3Y", "3M"),
}


# ---------------------------------------------------------------------------
# MPC event-study configuration
# ---------------------------------------------------------------------------

MPC_EVENT_HALF_WINDOWS = (1, 3, 5)

MPC_EVENT_TYPES = (
    "HIKE",
    "CUT",
    "HOLD",
)

MPC_SHORT_END_TENORS = (
    "3M",
    "6M",
    "1Y",
)

MPC_LONGER_END_TENORS = (
    "5Y",
    "10Y",
)


# ---------------------------------------------------------------------------
# Research sample boundaries
# ---------------------------------------------------------------------------

PKRV_SAMPLE_START = date(2022, 1, 4)

PKRV_PKISRV_SAMPLE_START = date(2025, 2, 3)

MACRO_SAMPLE_START = date(2022, 1, 1)

# End dates are intentionally not frozen here.
# Pipelines will use the latest validated observation available within the
# approved research period rather than manufacturing a fixed terminal date.


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

YIELD_STORAGE_UNIT = "percent"
RATE_STORAGE_UNIT = "percent"
SPREAD_DISPLAY_UNIT = "basis_points"

BASIS_POINTS_PER_PERCENTAGE_POINT = 100.0


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

REQUIRED_PROJECT_DIRECTORIES = (
    DATA_DIR,
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    MUFAP_RAW_DIR,
    PAKDATAHUB_RAW_DIR,
    SBP_RAW_DIR,
    PBS_RAW_DIR,
    NOTEBOOKS_DIR,
    SQL_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    TABLES_DIR,
)


def validate_project_structure() -> list[Path]:
    """Return required project directories that are currently missing."""

    return [path for path in REQUIRED_PROJECT_DIRECTORIES if not path.is_dir()]
