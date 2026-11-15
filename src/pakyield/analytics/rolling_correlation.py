"""Rolling correlation for matched PKRV and PKISRV yield observations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from datetime import date

import pandas as pd


def rolling_yield_correlations(
    rows: Iterable[Mapping[str, str]],
    window: int,
) -> list[dict[str, object]]:
    """Calculate rolling Pearson correlations for one matched maturity.

    The window counts matched observations, not calendar days.

    The input must contain one row per date for a single maturity. Missing
    values must be handled before calling this function; this function never
    fills or interpolates them.
    """
    if isinstance(window, bool) or not isinstance(window, int) or window < 2:
        raise ValueError("window must be an integer of at least 2")

    ordered = sorted(rows, key=lambda row: row["observation_date"])

    if not ordered:
        return []

    dates = [row["observation_date"] for row in ordered]
    tenors = {row["tenor"] for row in ordered}

    if len(tenors) != 1:
        raise ValueError("Rows must contain exactly one maturity")

    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate observation dates are not allowed")

    for value in dates:
        date.fromisoformat(value)

    pkrv = [float(row["pkrv_yield_pct"]) for row in ordered]
    pkisrv = [float(row["pkisrv_yield_pct"]) for row in ordered]

    if not all(math.isfinite(value) for value in pkrv + pkisrv):
        raise ValueError("Yield observations must be finite")

    pkrv_series = pd.Series(pkrv, dtype="float64")
    pkisrv_series = pd.Series(pkisrv, dtype="float64")

    correlations = pkrv_series.rolling(
        window=window,
        min_periods=window,
    ).corr(pkisrv_series)

    output: list[dict[str, object]] = []

    for index, row in enumerate(ordered):
        correlation = correlations.iloc[index]

        output.append(
            {
                "observation_date": row["observation_date"],
                "tenor": row["tenor"],
                "window": window,
                "correlation": (
                    float(correlation) if math.isfinite(correlation) else None
                ),
            }
        )

    return output
