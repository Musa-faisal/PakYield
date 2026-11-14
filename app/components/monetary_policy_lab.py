"""Monetary Policy Lab using verified, precomputed event-window data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from app.services import data


def select_event_rows(
    rows: Iterable[Mapping[str, str]],
    event_date: str,
    curve_type: str,
    half_window: str,
) -> list[Mapping[str, str]]:
    """Select an exact event, curve, and observation-window size."""
    selected = [
        row
        for row in rows
        if row["event_date"] == event_date
        and row["curve_type"] == curve_type
        and row["half_window"] == half_window
    ]

    return sorted(selected, key=lambda row: float(row["tenor_years"]))


def eligible_reactions(
    rows: Iterable[Mapping[str, str]],
) -> list[Mapping[str, str]]:
    """Return only source-declared eligible reactions with recorded values."""
    return [
        row
        for row in rows
        if row["eligibility_status"] == "ELIGIBLE" and row["window_change_bps"] != ""
    ]


def render_monetary_policy_lab() -> bool:
    """Display existing event-window observations without recomputing them."""
    try:
        rows = data.load_mpc_event_rows()
    except data.PresentationDataError as exc:
        st.error("The MPC event-window data could not be verified.")
        st.code(str(exc))
        return False

    if not rows:
        return False

    event_dates = sorted({row["event_date"] for row in rows}, reverse=True)

    event_date = st.selectbox(
        "MPC announcement date",
        event_dates,
        key="policy_lab_event_date",
    )

    event_rows = [row for row in rows if row["event_date"] == event_date]

    curves = sorted({row["curve_type"] for row in event_rows})

    if not curves:
        return False

    controls = st.columns(2)

    with controls[0]:
        curve_type = st.selectbox(
            "Benchmark curve",
            curves,
            index=curves.index("PKRV") if "PKRV" in curves else 0,
            key="policy_lab_curve",
        )

    curve_rows = [row for row in event_rows if row["curve_type"] == curve_type]

    windows = sorted(
        {row["half_window"] for row in curve_rows},
        key=int,
    )

    if not windows:
        return False

    with controls[1]:
        half_window = st.selectbox(
            "Observation window",
            windows,
            format_func=lambda value: f"[-{value}, +{value}]",
            key="policy_lab_window",
        )

    selected = select_event_rows(rows, event_date, curve_type, half_window)

    if not selected:
        return False

    event = selected[0]

    st.subheader("MPC decision")

    decision_columns = st.columns(4)

    with decision_columns[0]:
        st.metric("Decision", event["decision_type"] or "—")

    with decision_columns[1]:
        change = event["policy_change_bps"]
        st.metric("Policy change", f"{change} bps" if change else "—")

    with decision_columns[2]:
        previous_rate = event["previous_rate_pct"]
        st.metric(
            "Previous policy rate",
            f"{float(previous_rate):.2f}%" if previous_rate else "—",
        )

    with decision_columns[3]:
        announced_rate = event["announced_rate_pct"]
        st.metric(
            "Statement-announced rate",
            f"{float(announced_rate):.2f}%" if announced_rate else "—",
        )

    st.caption(
        "A missing statement-announced rate is shown as unavailable. "
        "It is not replaced with an inferred rate."
    )

    st.subheader("Yield movement by maturity")

    reactions = eligible_reactions(selected)

    if reactions:
        figure = go.Figure(
            go.Bar(
                x=[row["tenor"] for row in reactions],
                y=[float(row["window_change_bps"]) for row in reactions],
                name="Observed yield change",
                customdata=[
                    [
                        row["left_observation_date"],
                        row["right_observation_date"],
                    ]
                    for row in reactions
                ],
                hovertemplate=(
                    "Maturity: %{x}<br>"
                    "Yield change: %{y:.2f} bps<br>"
                    "Start observation: %{customdata[0]}<br>"
                    "End observation: %{customdata[1]}"
                    "<extra></extra>"
                ),
            )
        )

        apply_financial_chart_layout(
            figure,
            title=f"{curve_type} · {event_date} · [-{half_window}, +{half_window}]",
            xaxis_title="Observed maturity",
            yaxis_title="Yield change (bps)",
        )

        figure.update_xaxes(type="category")

        st.plotly_chart(
            figure,
            width="stretch",
            key="policy_lab_reactions",
        )
    else:
        st.info(
            "No eligible yield reactions are available for this selection. "
            "Review the recorded reasons below or select another event."
        )

    st.caption(
        "Endpoints are available curve observations strictly before and "
        "after the announcement date. The selected number indicates "
        "observation positions on each side, not calendar days."
    )

    with st.expander("View event-window observations and eligibility"):
        st.dataframe(
            [
                {
                    "Maturity": row["tenor"],
                    "Start date": row["left_observation_date"] or "—",
                    "End date": row["right_observation_date"] or "—",
                    "Start yield (%)": row["left_yield_pct"] or "—",
                    "End yield (%)": row["right_yield_pct"] or "—",
                    "Change (bps)": row["window_change_bps"] or "—",
                    "Status": row["eligibility_status"],
                    "Ineligibility reason": row["ineligibility_reason"] or "—",
                }
                for row in selected
            ],
            width="stretch",
            hide_index=True,
        )

    st.info(
        "This event study describes yield movements around MPC announcements. "
        "It does not by itself identify a policy surprise or establish causality."
    )

    return True
