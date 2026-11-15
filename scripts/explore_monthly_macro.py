"""Exploratory monthly PKRV, policy-rate, and CPI analysis.

This script reads the existing monthly panel and SQLite database.

It writes no research output files and does not change frozen artifacts.
The model is exploratory and observational, not a causal or forecasting model.
"""

from __future__ import annotations

import bisect
import csv
import math
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PANEL_PATH = PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv"

DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "pakyield.sqlite3"

FOCAL_TENORS = ("3M", "1Y", "5Y", "10Y")
HAC_LAGS = 3
MINIMUM_OBSERVATIONS = 24


def month_boundaries(period: str) -> tuple[date, date]:
    """Return the previous and current calendar month-end for YYYY-MM."""
    start = date.fromisoformat(f"{period}-01")

    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)

    return start - timedelta(days=1), next_month - timedelta(days=1)


def month_index(period: str) -> int:
    """Convert YYYY-MM to an integer suitable for checking monthly gaps."""
    first_day = date.fromisoformat(f"{period}-01")
    return first_day.year * 12 + first_day.month


def policy_rate_on(
    target: date,
    effective_dates: list[date],
    rates: list[float],
) -> float | None:
    """Return the latest policy rate effective on or before the target date."""
    index = bisect.bisect_right(effective_dates, target) - 1

    return rates[index] if index >= 0 else None


def load_policy_changes() -> tuple[list[date], list[float]]:
    """Read policy-rate changes without modifying the SQLite database."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(f"Policy-rate database not found: {DATABASE_PATH}")

    database_uri = DATABASE_PATH.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(database_uri, uri=True) as connection:
        records = connection.execute(
            """
            SELECT effective_date, rate_pct
            FROM policy_rate_observations
            ORDER BY effective_date
            """
        ).fetchall()

    if not records:
        raise ValueError("No policy-rate observations were found.")

    effective_dates = [date.fromisoformat(record[0]) for record in records]
    rates = [float(record[1]) for record in records]

    if len(set(effective_dates)) != len(effective_dates):
        raise ValueError("Duplicate policy effective dates were found.")

    if any(not math.isfinite(rate) for rate in rates):
        raise ValueError("A policy-rate observation is not finite.")

    return effective_dates, rates


def build_sample(
    panel_rows: list[dict[str, str]],
    tenor: str,
    effective_dates: list[date],
    rates: list[float],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Build complete observed monthly rows for one PKRV maturity."""
    selected = [
        row
        for row in panel_rows
        if row["curve_type"] == "PKRV" and row["tenor"] == tenor
    ]

    periods = [row["period"] for row in selected]

    if len(periods) != len(set(periods)):
        raise ValueError(f"Duplicate monthly periods were found for {tenor}.")

    sample: list[dict[str, object]] = []
    missing_panel = 0
    missing_policy = 0

    for row in selected:
        yield_change = row["monthly_yield_change_bps"]
        inflation = row["cpi_inflation_yoy_pct"]

        if yield_change == "" or inflation == "":
            missing_panel += 1
            continue

        previous_end, current_end = month_boundaries(row["period"])

        previous_rate = policy_rate_on(
            previous_end,
            effective_dates,
            rates,
        )

        current_rate = policy_rate_on(
            current_end,
            effective_dates,
            rates,
        )

        if previous_rate is None or current_rate is None:
            missing_policy += 1
            continue

        numeric_values = (
            float(yield_change),
            float(inflation),
            previous_rate,
            current_rate,
        )

        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError(f"Non-finite value found for {tenor}, {row['period']}.")

        sample.append(
            {
                "period": row["period"],
                "yield_change_bps": float(yield_change),
                "policy_change_pct_points": current_rate - previous_rate,
                "inflation_yoy_pct": float(inflation),
            }
        )

    frame = pd.DataFrame(
        sample,
        columns=(
            "period",
            "yield_change_bps",
            "policy_change_pct_points",
            "inflation_yoy_pct",
        ),
    ).sort_values("period")

    exclusions = {
        "selected_months": len(selected),
        "missing_yield_change_or_cpi": missing_panel,
        "missing_policy_state": missing_policy,
    }

    return frame, exclusions


def longest_consecutive_sample(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the longest run of consecutive complete calendar months.

    When runs have equal length, the most recent run is selected.
    No missing observations are filled.
    """
    if frame.empty:
        return frame.copy()

    ordered = frame.sort_values("period").reset_index(drop=True)

    runs: list[tuple[int, int]] = []
    start = 0

    for index in range(1, len(ordered)):
        previous = month_index(str(ordered.iloc[index - 1]["period"]))
        current = month_index(str(ordered.iloc[index]["period"]))

        if current - previous != 1:
            runs.append((start, index))
            start = index

    runs.append((start, len(ordered)))

    best_start, best_end = max(
        runs,
        key=lambda run: (run[1] - run[0], run[1]),
    )

    return ordered.iloc[best_start:best_end].copy()


def print_adf(frame: pd.DataFrame, column: str) -> None:
    """Print an ADF diagnostic without claiming definitive stationarity."""
    values = frame[column].astype(float)

    try:
        statistic, p_value, used_lag, observations, _, _ = adfuller(
            values,
            autolag="AIC",
        )
    except ValueError as exc:
        print(f"  ADF {column}: unavailable ({exc})")
        return

    print(
        f"  ADF {column}: statistic={statistic:.4f}, "
        f"p={p_value:.4f}, lags={used_lag}, n={observations}"
    )


def run_exploration(
    frame: pd.DataFrame,
    tenor: str,
    exclusions: dict[str, int],
) -> None:
    """Print an exploratory OLS model with HAC standard errors."""
    contiguous = longest_consecutive_sample(frame)

    print(f"\n{'=' * 60}")
    print(f"PKRV maturity: {tenor}")
    print(f"Selected panel rows: {exclusions['selected_months']}")
    print(
        "Excluded: missing yield change or CPI = "
        f"{exclusions['missing_yield_change_or_cpi']}"
    )
    print(f"Excluded: missing policy state = {exclusions['missing_policy_state']}")
    print(f"Complete monthly observations: {len(frame)}")
    print(f"Consecutive observations used: {len(contiguous)}")
    print(
        "Complete observations outside selected consecutive run: "
        f"{len(frame) - len(contiguous)}"
    )

    if len(contiguous) < MINIMUM_OBSERVATIONS:
        print("Model unavailable: fewer than 24 consecutive complete months.")
        return

    first = contiguous["period"].iloc[0]
    last = contiguous["period"].iloc[-1]

    print(f"Consecutive model period: {first} to {last}")

    if contiguous["policy_change_pct_points"].nunique() < 2:
        print("Model unavailable: policy-rate changes have no variation.")
        return

    if contiguous["inflation_yoy_pct"].nunique() < 2:
        print("Model unavailable: CPI inflation has no variation.")
        return

    changed_months = int((contiguous["policy_change_pct_points"] != 0).sum())

    print(f"Months with a policy-rate change: {changed_months}")

    explanatory = sm.add_constant(
        contiguous[["policy_change_pct_points", "inflation_yoy_pct"]],
        has_constant="add",
    )

    model = sm.OLS(
        contiguous["yield_change_bps"],
        explanatory,
        missing="raise",
    ).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": HAC_LAGS},
    )

    print(f"\nExploratory OLS with HAC standard errors; maxlags={HAC_LAGS}")
    print(model.summary())

    print("\nADF diagnostics on the consecutive model sample:")

    for column in (
        "yield_change_bps",
        "policy_change_pct_points",
        "inflation_yoy_pct",
    ):
        print_adf(contiguous, column)

    print(
        "\nInterpretation boundary: these are exploratory associations "
        "in this sample. They do not establish causality or forecasting ability."
    )


def main() -> None:
    """Run the exploratory analysis using existing project inputs."""
    if not PANEL_PATH.is_file():
        raise FileNotFoundError(f"Monthly analysis panel not found: {PANEL_PATH}")

    with PANEL_PATH.open(newline="", encoding="utf-8") as file:
        panel_rows = list(csv.DictReader(file))

    effective_dates, rates = load_policy_changes()

    print("PAKYIELD EXPLORATORY MONTHLY MACRO ANALYSIS")
    print("Yield changes: basis points")
    print("Policy-rate changes: percentage points")
    print("CPI inflation: year-over-year percent")
    print("Existing inputs are read only; no output files are written.")
    print(
        "CPI is aligned by reference month. Publication timing is not modeled; "
        "this is not a real-time forecasting exercise."
    )

    for tenor in FOCAL_TENORS:
        frame, exclusions = build_sample(
            panel_rows,
            tenor,
            effective_dates,
            rates,
        )

        run_exploration(frame, tenor, exclusions)


if __name__ == "__main__":
    main()
