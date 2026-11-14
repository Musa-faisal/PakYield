"""Market Overview presentation using verified PakYield observations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from app.services import data


def curve_snapshot(
    rows: Iterable[Mapping[str, str]],
    curve_type: str,
    observation_date: str,
) -> list[Mapping[str, str]]:
    """Return observed points for an exact curve and date, sorted by maturity."""
    selected = [
        row
        for row in rows
        if row["curve_type"] == curve_type
        and row["observation_date"] == observation_date
    ]

    return sorted(selected, key=lambda row: float(row["tenor_years"]))


def matched_curve_changes(
    current: Iterable[Mapping[str, str]],
    comparison: Iterable[Mapping[str, str]],
) -> list[dict[str, object]]:
    """Compare only maturities observed on both selected dates."""
    previous_by_tenor = {row["tenor"]: row for row in comparison}
    changes: list[dict[str, object]] = []

    for row in current:
        previous = previous_by_tenor.get(row["tenor"])

        if previous is None:
            continue

        changes.append(
            {
                "tenor": row["tenor"],
                "tenor_years": float(row["tenor_years"]),
                "change_bps": (float(row["yield_pct"]) - float(previous["yield_pct"]))
                * 100.0,
            }
        )

    return changes


def render_market_workspace() -> bool:
    """Render the market workspace or report that no data are available."""
    try:
        rows = data.load_yield_rows()
    except data.PresentationDataError as exc:
        st.error("The market artifact could not be verified.")
        st.code(str(exc))
        return False

    curves = sorted({row["curve_type"] for row in rows})

    if not curves:
        return False

    curve_type = st.selectbox(
        "Benchmark curve",
        curves,
        index=curves.index("PKRV") if "PKRV" in curves else 0,
        key="market_curve_type",
    )

    available_dates = sorted(
        {row["observation_date"] for row in rows if row["curve_type"] == curve_type},
        reverse=True,
    )

    if not available_dates:
        return False

    control_columns = st.columns(2)

    with control_columns[0]:
        current_date = st.selectbox(
            "As-of observation date",
            available_dates,
            index=0,
            key="market_current_date",
        )

    with control_columns[1]:
        comparison_date = st.selectbox(
            "Comparison observation date",
            available_dates,
            index=1 if len(available_dates) > 1 else 0,
            key="market_comparison_date",
        )

    current = curve_snapshot(rows, curve_type, current_date)
    comparison = curve_snapshot(rows, curve_type, comparison_date)

    if not current:
        return False

    st.subheader("Observed yield curves")

    curve_figure = go.Figure()

    for label, snapshot in (
        (current_date, current),
        (comparison_date, comparison),
    ):
        if not snapshot:
            continue

        curve_figure.add_trace(
            go.Scatter(
                x=[row["tenor"] for row in snapshot],
                y=[float(row["yield_pct"]) for row in snapshot],
                mode="lines+markers",
                name=label,
                connectgaps=False,
                hovertemplate=(
                    "Maturity: %{x}<br>Yield: %{y:.2f}%<extra>%{fullData.name}</extra>"
                ),
            )
        )

    apply_financial_chart_layout(
        curve_figure,
        title=f"{curve_type} observed benchmark yields",
        xaxis_title="Observed maturity",
        yaxis_title="Yield (%)",
    )

    curve_figure.update_xaxes(type="category")
    st.plotly_chart(curve_figure, width="stretch", key="market_curve_chart")

    st.caption(
        "Only published observations for the selected dates are shown. "
        "The lines connect observed points for display; no maturity "
        "values are interpolated."
    )

    st.subheader("Movement by maturity")

    changes = matched_curve_changes(current, comparison)

    if changes:
        change_figure = go.Figure(
            go.Bar(
                x=[row["tenor"] for row in changes],
                y=[row["change_bps"] for row in changes],
                name="Yield change",
                hovertemplate="Maturity: %{x}<br>Change: %{y:.2f} bps<extra></extra>",
            )
        )

        apply_financial_chart_layout(
            change_figure,
            title=f"{current_date} minus {comparison_date}",
            xaxis_title="Matched maturity",
            yaxis_title="Yield change (bps)",
        )

        change_figure.update_xaxes(type="category")

        st.plotly_chart(
            change_figure,
            width="stretch",
            key="market_change_chart",
        )

        st.caption(
            "The change equals the as-of yield minus the comparison-date "
            "yield. Only exact matching maturities are included."
        )
    else:
        st.info(
            "The selected dates have no matching observed maturities. "
            "Select another comparison date."
        )

    return True
