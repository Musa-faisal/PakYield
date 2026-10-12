"""PakYield read-only analytical presentation application."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

import streamlit as st
from app.services import data

APP_TITLE: Final = "PakYield Lab"

APP_SUBTITLE: Final = (
    "Pakistan Sovereign Yield Curve, Sukuk Benchmark Comparison "
    "& Monetary Policy Transmission"
)


def _float(
    value: str | None,
) -> float | None:
    """Convert a non-empty analytical string to float."""

    if value in {
        None,
        "",
    }:
        return None

    return float(value)


def _format_pct(
    value: str | None,
    *,
    decimals: int = 2,
) -> str:
    """Format one percentage value for presentation."""

    number = _float(value)

    if number is None:
        return "—"

    return f"{number:.{decimals}f}%"


def _format_bps(
    value: str | None,
    *,
    decimals: int = 0,
) -> str:
    """Format one basis-point value for presentation."""

    number = _float(value)

    if number is None:
        return "—"

    return f"{number:.{decimals}f} bps"


def _display_curve_name(
    curve_type: str,
) -> str:
    """Return presentation label without changing analytical meaning."""

    labels = {
        "PKRV": "PKRV",
        "PKISRV": "PKISRV",
    }

    return labels.get(
        curve_type,
        curve_type,
    )


def _curve_table(
    rows: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    """Return presentation-safe rows for a curve snapshot."""

    return [
        {
            "Tenor": row["tenor"],
            "Yield": _format_pct(row["yield_pct"]),
            "Date": row["observation_date"],
            "Regime": row["regime_label"],
        }
        for row in rows
    ]


def render_header() -> None:
    """Render application title and scope."""

    st.title(APP_TITLE)

    st.caption(APP_SUBTITLE)

    st.info(
        "Read-only analytical presentation. "
        "Displayed values come from frozen PakYield artifacts; "
        "no interpolation or synthetic observations are used."
    )


def render_market_overview() -> None:
    """Render latest frozen market observations."""

    policy = data.latest_policy_context()

    pkrv_1y = data.latest_observed_yield(
        "PKRV",
        "1Y",
    )

    pkrv_10y = data.latest_observed_yield(
        "PKRV",
        "10Y",
    )

    spread = data.latest_term_spread("10Y-2Y")

    st.header("Market overview")

    columns = st.columns(4)

    with columns[0]:
        st.metric(
            "Policy rate",
            (_format_pct(policy["policy_rate_pct"]) if policy else "—"),
        )

    with columns[1]:
        st.metric(
            "PKRV 1Y",
            (_format_pct(pkrv_1y["yield_pct"]) if pkrv_1y else "—"),
        )

    with columns[2]:
        st.metric(
            "PKRV 10Y",
            (_format_pct(pkrv_10y["yield_pct"]) if pkrv_10y else "—"),
        )

    with columns[3]:
        st.metric(
            "PKRV 10Y–2Y",
            (_format_bps(spread["term_spread_bps"]) if spread else "—"),
        )

    if policy:
        st.caption(
            "Latest policy-context date: "
            f"{policy['observation_date']} · "
            "Directional regime: "
            f"{policy['regime_label']}"
        )


def render_latest_curves() -> None:
    """Render latest observed PKRV and PKISRV snapshots."""

    st.header("Latest observed curves")

    st.caption(
        "Each snapshot uses the latest actual eligible observation "
        "available for that curve. Tenors are not interpolated."
    )

    pkrv = data.latest_curve_snapshot("PKRV")

    pkisrv = data.latest_curve_snapshot("PKISRV")

    left, right = st.columns(2)

    with left:
        st.subheader(_display_curve_name("PKRV"))

        if pkrv:
            st.dataframe(
                _curve_table(pkrv),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No eligible PKRV snapshot is available.")

    with right:
        st.subheader(_display_curve_name("PKISRV"))

        if pkisrv:
            st.dataframe(
                _curve_table(pkisrv),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No eligible PKISRV snapshot is available.")


def render_analysis_inventory() -> None:
    """Render the frozen five-family analytical inventory."""

    st.header("Analytical coverage")

    manifest = data.load_analysis_manifest()

    rows = [
        {
            "Analysis family": row["analysis_family"],
            "Rows": int(row["row_count"]),
            "Grain": row["grain"],
        }
        for row in manifest
    ]

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Event-study and monthly CPI/yield data retain their own "
        "analytical grains and are not collapsed into a universal table."
    )


def render_methodology_boundary() -> None:
    """Render concise analytical interpretation boundary."""

    with st.expander("Methodology boundaries"):
        st.markdown(
            """
- Yield and curve observations shown here are actual frozen observations.
- Missing observations are not converted to zero.
- PKRV/PKISRV comparisons require exact same-date comparable maturities.
- MPC event windows use available market-observation positions.
- Directional regime labels describe the latest prior directional MPC decision.
- The dashboard does not treat numerical PKRV/PKISRV differences as an
  Islamic, Sukuk, or Shariah premium or discount.
- Descriptive presentation does not by itself establish causality or
  statistical significance.
"""
        )


def main() -> None:
    """Render PakYield dashboard."""

    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📈",
        layout="wide",
    )

    render_header()

    render_market_overview()

    render_latest_curves()

    render_analysis_inventory()

    render_methodology_boundary()


if __name__ == "__main__":
    main()
