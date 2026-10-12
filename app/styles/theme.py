"""Shared Bloomberg-inspired visual system for PakYield."""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# PakYield presentation tokens
# ---------------------------------------------------------------------------
#
# The visual direction is inspired by professional financial-market terminals:
# dark surfaces, compact information density, restrained decoration and an
# orange market-data accent. It does not reproduce Bloomberg branding,
# proprietary layouts or software.
# ---------------------------------------------------------------------------

COLOR_BG = "#060708"
COLOR_BG_ELEVATED = "#0B0D0F"
COLOR_PANEL = "#0F1215"
COLOR_PANEL_ALT = "#12161A"
COLOR_BORDER = "#2A3036"
COLOR_BORDER_STRONG = "#3A424B"

COLOR_TEXT = "#F2F4F5"
COLOR_TEXT_MUTED = "#9AA3AB"
COLOR_TEXT_DIM = "#6F7881"

COLOR_ACCENT = "#FF9F1C"
COLOR_ACCENT_SOFT = "#C97D11"

COLOR_POSITIVE = "#38B27B"
COLOR_NEGATIVE = "#E05A5A"
COLOR_NEUTRAL = "#AAB2BA"

COLOR_GRID = "#20262C"

CHART_SEQUENCE = (
    "#FF9F1C",
    "#4DA3FF",
    "#38B27B",
    "#D679E8",
    "#E8D35C",
    "#75D1D1",
    "#E05A5A",
    "#B8C0C8",
)


PAKYIELD_CSS = f"""
<style>
    :root {{
        --pakyield-bg: {COLOR_BG};
        --pakyield-bg-elevated: {COLOR_BG_ELEVATED};
        --pakyield-panel: {COLOR_PANEL};
        --pakyield-panel-alt: {COLOR_PANEL_ALT};
        --pakyield-border: {COLOR_BORDER};
        --pakyield-border-strong: {COLOR_BORDER_STRONG};
        --pakyield-text: {COLOR_TEXT};
        --pakyield-muted: {COLOR_TEXT_MUTED};
        --pakyield-dim: {COLOR_TEXT_DIM};
        --pakyield-accent: {COLOR_ACCENT};
        --pakyield-accent-soft: {COLOR_ACCENT_SOFT};
        --pakyield-positive: {COLOR_POSITIVE};
        --pakyield-negative: {COLOR_NEGATIVE};
        --pakyield-grid: {COLOR_GRID};
    }}

    /* --------------------------------------------------------------- */
    /* Application shell                                               */
    /* --------------------------------------------------------------- */

    html,
    body,
    [class*="css"] {{
        font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }}

    .stApp {{
        background:
            linear-gradient(
                180deg,
                #070809 0%,
                var(--pakyield-bg) 240px
            );
        color: var(--pakyield-text);
    }}

    .block-container {{
        max-width: 1800px;
        padding-top: 0.85rem;
        padding-bottom: 2.25rem;
        padding-left: 1.35rem;
        padding-right: 1.35rem;
    }}

    header[data-testid="stHeader"] {{
        background: rgba(6, 7, 8, 0.94);
        border-bottom: 1px solid #161A1E;
    }}

    /* --------------------------------------------------------------- */
    /* Sidebar                                                         */
    /* --------------------------------------------------------------- */

    section[data-testid="stSidebar"] {{
        background: #080A0C;
        border-right: 1px solid var(--pakyield-border);
    }}

    section[data-testid="stSidebar"] > div {{
        padding-top: 0.7rem;
    }}

    section[data-testid="stSidebar"] a {{
        border-radius: 2px;
    }}

    section[data-testid="stSidebar"] a:hover {{
        background: #11151A;
    }}

    /* --------------------------------------------------------------- */
    /* Typography                                                      */
    /* --------------------------------------------------------------- */

    h1,
    h2,
    h3,
    h4 {{
        color: var(--pakyield-text);
        letter-spacing: -0.025em;
    }}

    h1 {{
        font-size: 1.8rem;
    }}

    h2 {{
        font-size: 1.35rem;
    }}

    h3 {{
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    p,
    li {{
        color: #CED3D7;
    }}

    code {{
        color: #F6B85B;
        background: #111418;
    }}

    /* --------------------------------------------------------------- */
    /* Shared PakYield terminal elements                               */
    /* --------------------------------------------------------------- */

    .pakyield-terminal-bar {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-height: 30px;
        padding: 0.35rem 0.55rem;
        margin-bottom: 0.8rem;
        background: #090B0D;
        border: 1px solid var(--pakyield-border);
        border-left: 3px solid var(--pakyield-accent);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.72rem;
        letter-spacing: 0.045em;
        text-transform: uppercase;
    }}

    .pakyield-terminal-brand {{
        color: var(--pakyield-accent);
        font-weight: 800;
    }}

    .pakyield-terminal-context {{
        color: var(--pakyield-muted);
    }}

    .pakyield-terminal-spacer {{
        flex: 1;
    }}

    .pakyield-terminal-status {{
        color: var(--pakyield-positive);
        font-weight: 700;
    }}

    .pakyield-kicker {{
        color: var(--pakyield-accent);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.28rem;
    }}

    .pakyield-title {{
        color: var(--pakyield-text);
        font-size: clamp(1.55rem, 2.4vw, 2.15rem);
        font-weight: 720;
        line-height: 1.08;
        letter-spacing: -0.035em;
        margin-bottom: 0.35rem;
    }}

    .pakyield-subtitle {{
        color: var(--pakyield-muted);
        font-size: 0.88rem;
        line-height: 1.45;
        max-width: 1100px;
        margin-bottom: 1rem;
    }}

    .pakyield-section {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-top: 1.25rem;
        margin-bottom: 0.55rem;
        color: var(--pakyield-text);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.77rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .pakyield-section::after {{
        content: "";
        flex: 1;
        height: 1px;
        background: var(--pakyield-border);
    }}

    .pakyield-panel {{
        position: relative;
        min-height: 92px;
        padding: 0.78rem 0.85rem;
        background: var(--pakyield-panel);
        border: 1px solid var(--pakyield-border);
        border-radius: 2px;
    }}

    .pakyield-panel::before {{
        content: "";
        position: absolute;
        top: -1px;
        left: -1px;
        width: 34px;
        height: 2px;
        background: var(--pakyield-accent);
    }}

    .pakyield-label {{
        color: var(--pakyield-muted);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .pakyield-value {{
        color: var(--pakyield-text);
        font-size: 1.42rem;
        font-weight: 760;
        line-height: 1.15;
        margin-top: 0.24rem;
        font-variant-numeric: tabular-nums;
    }}

    .pakyield-delta {{
        margin-top: 0.25rem;
        color: var(--pakyield-muted);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.67rem;
        font-variant-numeric: tabular-nums;
    }}

    .pakyield-positive {{
        color: var(--pakyield-positive);
    }}

    .pakyield-negative {{
        color: var(--pakyield-negative);
    }}

    .pakyield-neutral {{
        color: var(--pakyield-neutral);
    }}

    .pakyield-placeholder {{
        border: 1px dashed #343B43;
        border-left: 2px solid #48515A;
        background: #0B0E11;
        color: var(--pakyield-muted);
        padding: 0.95rem 1rem;
        border-radius: 2px;
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.76rem;
        line-height: 1.5;
    }}

    .pakyield-callout {{
        padding: 0.8rem 0.9rem;
        background: #0D1114;
        border: 1px solid var(--pakyield-border);
        border-left: 3px solid var(--pakyield-accent);
        color: #C7CDD2;
        font-size: 0.8rem;
        line-height: 1.45;
    }}

    .pakyield-caption {{
        color: var(--pakyield-dim);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.65rem;
        letter-spacing: 0.02em;
    }}

    .pakyield-status-pill {{
        display: inline-block;
        padding: 0.16rem 0.42rem;
        border: 1px solid #394149;
        border-radius: 2px;
        color: var(--pakyield-muted);
        background: #0C0F12;
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.62rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}

    .pakyield-status-pill--ok {{
        color: var(--pakyield-positive);
        border-color: rgba(56, 178, 123, 0.45);
    }}

    .pakyield-status-pill--warn {{
        color: var(--pakyield-accent);
        border-color: rgba(255, 159, 28, 0.45);
    }}

    /* --------------------------------------------------------------- */
    /* Streamlit controls                                              */
    /* --------------------------------------------------------------- */

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    .stDateInput > div > div {{
        background: #0D1013;
        border-color: var(--pakyield-border);
        border-radius: 2px;
    }}

    .stButton > button,
    .stDownloadButton > button {{
        min-height: 2rem;
        border-radius: 2px;
        border: 1px solid #3A424B;
        background: #111519;
        color: var(--pakyield-text);
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.72rem;
        font-weight: 700;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: var(--pakyield-accent);
        color: var(--pakyield-accent);
    }}

    div[data-testid="stTabs"] button {{
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace;
        font-size: 0.7rem;
        font-weight: 700;
    }}

    /* --------------------------------------------------------------- */
    /* Dataframes / tables                                             */
    /* --------------------------------------------------------------- */

    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--pakyield-border);
        border-radius: 2px;
    }}

    /* --------------------------------------------------------------- */
    /* Plotly container                                                */
    /* --------------------------------------------------------------- */

    div[data-testid="stPlotlyChart"] {{
        border: 1px solid #20262C;
        background: #090B0D;
        padding: 0.18rem;
    }}

    /* --------------------------------------------------------------- */
    /* Metric compatibility                                            */
    /* --------------------------------------------------------------- */

    div[data-testid="stMetric"] {{
        background: var(--pakyield-panel);
        border: 1px solid var(--pakyield-border);
        border-radius: 2px;
        padding: 0.7rem 0.8rem;
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--pakyield-muted);
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--pakyield-text);
        font-variant-numeric: tabular-nums;
    }}

    /* --------------------------------------------------------------- */
    /* Compact dividers                                                */
    /* --------------------------------------------------------------- */

    hr {{
        border: none;
        border-top: 1px solid var(--pakyield-border);
        margin-top: 0.9rem;
        margin-bottom: 0.9rem;
    }}

    footer {{
        visibility: hidden;
    }}
</style>
"""


def apply_theme() -> None:
    """Apply PakYield's Bloomberg-inspired Streamlit CSS."""

    st.markdown(
        PAKYIELD_CSS,
        unsafe_allow_html=True,
    )
