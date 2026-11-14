"""Yield Curve Lab presentation backed by verified analytical artifacts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import apply_financial_chart_layout
from app.services import data


def select_curve_snapshot(
    rows: Iterable[Mapping[str, str]],
    curve_type: str,
    observation_date: str,
) -> list[Mapping[str, str]]:
    """Return source observations for one exact curve and observation date."""
    snapshot = [
        row
        for row in rows
        if row["curve_type"] == curve_type
        and row["observation_date"] == observation_date
    ]

    return sorted(snapshot, key=lambda row: float(row["tenor_years"]))


def select_tenor_history(
    rows: Iterable[Mapping[str, str]],
    curve_type: str,
    tenor: str,
) -> list[Mapping[str, str]]:
    """Return observed history for one exact curve and maturity."""
    history = [
        row for row in rows if row["curve_type"] == curve_type and row["tenor"] == tenor
    ]

    return sorted(history, key=lambda row: row["observation_date"])


def find_fit_status(
    rows: Iterable[Mapping[str, str]],
    curve_type: str,
    observation_date: str,
) -> Mapping[str, str] | None:
    """Return the recorded fit status for the exact selected curve and date."""
    matches = [
        row
        for row in rows
        if row["curve_type"] == curve_type
        and row["observation_date"] == observation_date
    ]

    if len(matches) > 1:
        raise ValueError(
            "More than one Nelson–Siegel status exists for this curve and date."
        )

    return matches[0] if matches else None


def render_yield_curve_lab() -> bool:
    """Display verified curve observations and existing model outputs."""
    try:
        yield_rows = data.load_yield_rows()
    except data.PresentationDataError as exc:
        st.error("The yield observations could not be verified.")
        st.code(str(exc))
        return False

    curves = sorted({row["curve_type"] for row in yield_rows})

    if not curves:
        return False

    controls = st.columns(2)

    with controls[0]:
        curve_type = st.selectbox(
            "Benchmark curve",
            curves,
            index=curves.index("PKRV") if "PKRV" in curves else 0,
            key="yield_lab_curve",
        )

    available_dates = sorted(
        {
            row["observation_date"]
            for row in yield_rows
            if row["curve_type"] == curve_type
        },
        reverse=True,
    )

    if not available_dates:
        return False

    with controls[1]:
        selected_date = st.selectbox(
            "Observation date",
            available_dates,
            key="yield_lab_date",
        )

    snapshot = select_curve_snapshot(yield_rows, curve_type, selected_date)

    if not snapshot:
        return False

    st.subheader("Observed yield curve")

    curve_figure = go.Figure()

    curve_figure.add_trace(
        go.Scatter(
            x=[row["tenor"] for row in snapshot],
            y=[float(row["yield_pct"]) for row in snapshot],
            mode="lines+markers",
            name=f"{curve_type} observed",
            connectgaps=False,
            hovertemplate=(
                "Maturity: %{x}<br>Yield: %{y:.2f}%<extra>%{fullData.name}</extra>"
            ),
        )
    )

    apply_financial_chart_layout(
        curve_figure,
        title=f"{curve_type} — {selected_date}",
        xaxis_title="Observed maturity",
        yaxis_title="Yield (%)",
    )

    curve_figure.update_xaxes(type="category")

    st.plotly_chart(
        curve_figure,
        width="stretch",
        key="yield_lab_observed_curve",
    )

    st.caption(
        "The chart connects published observations for display. "
        "It does not create yields for missing maturities."
    )

    with st.expander("View observed curve data"):
        st.dataframe(
            [
                {
                    "Observation date": row["observation_date"],
                    "Maturity": row["tenor"],
                    "Maturity in years": float(row["tenor_years"]),
                    "Yield (%)": float(row["yield_pct"]),
                    "Source": row["source_organization"],
                    "Source file": row["source_file"],
                }
                for row in snapshot
            ],
            width="stretch",
            hide_index=True,
        )

    st.subheader("Maturity history")

    tenor_years: dict[str, float] = {}

    for row in yield_rows:
        if row["curve_type"] == curve_type:
            tenor_years[row["tenor"]] = float(row["tenor_years"])

    tenors = sorted(tenor_years, key=lambda tenor: tenor_years[tenor])

    if tenors:
        selected_tenor = st.selectbox(
            "Maturity",
            tenors,
            key="yield_lab_tenor",
        )

        history = select_tenor_history(yield_rows, curve_type, selected_tenor)

        if history:
            history_figure = go.Figure()

            history_figure.add_trace(
                go.Scatter(
                    x=[row["observation_date"] for row in history],
                    y=[float(row["yield_pct"]) for row in history],
                    mode="markers",
                    marker={"size": 4},
                    name=f"{curve_type} {selected_tenor}",
                    hovertemplate=(
                        "Date: %{x}<br>Yield: %{y:.2f}%<extra>%{fullData.name}</extra>"
                    ),
                )
            )

            apply_financial_chart_layout(
                history_figure,
                title=f"{curve_type} {selected_tenor} observed history",
                xaxis_title="Observation date",
                yaxis_title="Yield (%)",
                hovermode="closest",
            )

            st.plotly_chart(
                history_figure,
                width="stretch",
                key="yield_lab_tenor_history",
            )

            st.caption(
                "Each marker is an observed benchmark value. "
                "Missing dates are not filled."
            )
        else:
            st.info("No observed history is available for this maturity.")
    else:
        st.info("No maturity history is available for this curve.")

    st.subheader("Nelson–Siegel model")

    try:
        fit_status = find_fit_status(
            data.load_nelson_siegel_date_fits(),
            curve_type,
            selected_date,
        )
    except (data.PresentationDataError, ValueError) as exc:
        st.error("The Nelson–Siegel fit status could not be verified.")
        st.code(str(exc))
        return True

    if fit_status is None:
        st.info("No recorded model status exists for this curve and date.")
        return True

    if fit_status["fit_status"] != "FIT":
        reason = fit_status.get("ineligibility_reason") or "Not recorded"

        st.info(
            "A production Nelson–Siegel fit is unavailable for this curve "
            "and date under the project's maturity-coverage rules."
        )
        st.caption(f"Recorded status: {fit_status['fit_status']} · Reason: {reason}")
        return True

    try:
        fitted = data.nelson_siegel_curve(selected_date, curve_type)
    except data.PresentationDataError as exc:
        st.error("The fitted curve artifact could not be verified.")
        st.code(str(exc))
        return True

    if not fitted:
        st.warning(
            "The recorded status indicates a fit, but no verified fitted "
            "observations were found for this date."
        )
        return True

    fit_figure = go.Figure()

    fit_figure.add_trace(
        go.Scatter(
            x=[row["tenor"] for row in fitted],
            y=[float(row["observed_yield_pct"]) for row in fitted],
            mode="markers",
            name="Observed yield",
        )
    )

    fit_figure.add_trace(
        go.Scatter(
            x=[row["tenor"] for row in fitted],
            y=[float(row["fitted_yield_pct"]) for row in fitted],
            mode="lines+markers",
            name="Fitted yield",
        )
    )

    apply_financial_chart_layout(
        fit_figure,
        title=f"{curve_type} observed and fitted — {selected_date}",
        xaxis_title="Observed maturity",
        yaxis_title="Yield (%)",
    )

    fit_figure.update_xaxes(type="category")

    st.plotly_chart(
        fit_figure,
        width="stretch",
        key="yield_lab_nelson_siegel",
    )

    rmse = fit_status.get("rmse_pct_points")

    if rmse:
        st.caption(f"Fit RMSE: {float(rmse):.4f} percentage points.")
    else:
        st.caption("Fit RMSE is unavailable in the recorded model output.")

    st.caption(
        "These are previously fitted and verified model outputs. "
        "The model is descriptive and does not establish causality or "
        "forecasting ability."
    )

    return True
