# ruff: noqa: E501
# Embedded publication prose is intentionally not source-wrapped because wrapping would alter the generated Markdown paper.
"""Build the Phase 8B academic research paper from frozen project evidence."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = PROJECT_ROOT / "docs" / "ACADEMIC_RESEARCH_PAPER.md"

EVIDENCE_MAP_PATH = PROJECT_ROOT / "data" / "interim" / "research_evidence_map.csv"

SOURCE_PACKET_PATH = PROJECT_ROOT / "docs" / "RESEARCH_PUBLICATION_SOURCE_PACKET.md"

EXPECTED_EVIDENCE_MAP_SHA = (
    "50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002"
)

EXPECTED_SOURCE_PACKET_SHA = (
    "e317d0044c3829f3255a91420290abe0f61b4d0864c8833e4c131e1dfc644948"
)

FROZEN_ARTIFACTS = {
    "descriptive_cross": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "descriptive_cross_curve_differences.csv",
        "rows": 10,
        "sha": ("ec59b6148d5a5f2aa02b38cddfe3aeebb5bfa0f173e58e522b5df70961634477"),
    },
    "monthly_census": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "descriptive_monthly_sample_census.csv",
        "rows": 25,
        "sha": ("d6a427f5580da4b99ea21ae64902da9494fed6325b4b674b71d9a08eca071d33"),
    },
    "descriptive_events": {
        "path": PROJECT_ROOT / "data" / "interim" / "descriptive_mpc_event_windows.csv",
        "rows": 72,
        "sha": ("92c6af99dd2cbf445eef3c8964f3b4316778a81424ee04b74e4b2540a0fb11d3"),
    },
    "descriptive_terms": {
        "path": PROJECT_ROOT / "data" / "interim" / "descriptive_term_spreads.csv",
        "rows": 8,
        "sha": ("97f586c77e9636e09fd40d5fcc2f8049cee0fd95eb9b98eb66f4f5055f2cbf69"),
    },
    "descriptive_changes": {
        "path": PROJECT_ROOT / "data" / "interim" / "descriptive_yield_changes.csv",
        "rows": 50,
        "sha": ("a3a785b0c12ece10564ad3e2c0aea76e8cec100abbe34a83841f5276adb6f978"),
    },
    "descriptive_levels": {
        "path": PROJECT_ROOT / "data" / "interim" / "descriptive_yield_levels.csv",
        "rows": 50,
        "sha": ("88ce5b39d4dd29f4749be6bc75aaee9cd0f7cadce37c22c54c1fb6bf3db633a6"),
    },
    "infer_cross_regime": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "inferential_cross_curve_regime.csv",
        "rows": 5,
        "sha": ("f3cca17f6cf658828a9ac613d7fdf7764126e9da0a74760749a9109a8717a6a5"),
    },
    "infer_cross_zero": {
        "path": PROJECT_ROOT / "data" / "interim" / "inferential_cross_curve_zero.csv",
        "rows": 5,
        "sha": ("14a906144b79f4a81dbe8b2df752a607600871bfc9de7e098e079b44e31f75de"),
    },
    "infer_events": {
        "path": PROJECT_ROOT / "data" / "interim" / "inferential_mpc_event_windows.csv",
        "rows": 72,
        "sha": ("13673445d98051044a1fe5b019d712fadf6b4b544dde2c6cc64a8ca48441f2f1"),
    },
    "infer_terms": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "inferential_term_spread_regime.csv",
        "rows": 4,
        "sha": ("17f7222dda8f17e14830d64f268b076ac365e66012b4fdf6aa38527a835e1349"),
    },
    "infer_changes": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "inferential_yield_change_regime.csv",
        "rows": 25,
        "sha": ("4baf694f635fb183ef4072dde24b10924bd280241276940b83d19b2c3c2f9501"),
    },
    "infer_levels": {
        "path": PROJECT_ROOT
        / "data"
        / "interim"
        / "inferential_yield_level_regime.csv",
        "rows": 25,
        "sha": ("4c9ba3fdd6e920e905db3dc118e645ad904e2cbf0682c33d0c5228998790b1a4"),
    },
    "monthly_panel": {
        "path": PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv",
        "rows": 1234,
        "sha": ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
    },
}


def sha256_file(path: Path) -> str:
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV into dictionaries."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def verify_frozen_sources() -> dict[str, list[dict[str, str]]]:
    """Verify publication sources before writing prose."""

    if sha256_file(EVIDENCE_MAP_PATH) != EXPECTED_EVIDENCE_MAP_SHA:
        raise RuntimeError("Frozen research evidence map hash changed")

    if sha256_file(SOURCE_PACKET_PATH) != EXPECTED_SOURCE_PACKET_SHA:
        raise RuntimeError("Frozen publication source packet hash changed")

    evidence_map = read_csv(EVIDENCE_MAP_PATH)

    if len(evidence_map) != 24:
        raise RuntimeError("Expected 24 evidence-map rows")

    loaded: dict[
        str,
        list[dict[str, str]],
    ] = {}

    for name, spec in FROZEN_ARTIFACTS.items():
        path = spec["path"]

        if not path.is_file():
            raise RuntimeError(f"Missing frozen publication artifact: {path}")

        actual_hash = sha256_file(path)

        if actual_hash != spec["sha"]:
            raise RuntimeError(f"Frozen artifact hash changed: {path}")

        rows = read_csv(path)

        if len(rows) != spec["rows"]:
            raise RuntimeError(f"Frozen row count changed: {path}")

        loaded[name] = rows

    return loaded


def number(
    value: str,
    digits: int = 2,
) -> str:
    """Format one numeric CSV value."""

    if value == "":
        return "—"

    return f"{float(value):.{digits}f}"


def integer(value: str) -> str:
    """Format an integer-like CSV value."""

    if value == "":
        return "—"

    return f"{int(float(value)):,}"


def p_value(value: str) -> str:
    """Format a p-value without overstating precision."""

    if value == "":
        return "—"

    numeric = float(value)

    if numeric < 0.001:
        return f"{numeric:.2e}"

    return f"{numeric:.3f}"


def markdown_table(
    headers: list[str],
    rows: list[list[str]],
) -> str:
    """Create a compact Markdown table."""

    if not rows:
        return "_No rows satisfy this frozen selection rule._"

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def inferential_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Keep rows carrying a frozen inferential estimate."""

    return [row for row in rows if row["analysis_status"] == "INFERENTIAL"]


def reject_count(
    rows: list[dict[str, str]],
) -> int:
    """Count BH-adjusted 5% rejections."""

    return sum(row["reject_bh_0_05"] == "1" for row in inferential_rows(rows))


def selected_pk_rv_descriptive_table(
    rows: list[dict[str, str]],
    value_unit: str,
) -> str:
    """Render representative PKRV maturities without changing evidence."""

    selected = {
        "3M",
        "1Y",
        "5Y",
        "10Y",
        "20Y",
    }

    data = [
        row for row in rows if row["curve_type"] == "PKRV" and row["tenor"] in selected
    ]

    ordering = {
        "3M": 0,
        "1Y": 1,
        "5Y": 2,
        "10Y": 3,
        "20Y": 4,
    }

    data.sort(
        key=lambda row: (
            ordering[row["tenor"]],
            row["regime_label"],
        )
    )

    return markdown_table(
        [
            "Tenor",
            "Regime",
            "n",
            f"Mean ({value_unit})",
            "Median",
            "Std. dev.",
        ],
        [
            [
                row["tenor"],
                row["regime_label"],
                integer(row["n"]),
                number(row["mean"]),
                number(row["median"]),
                number(row["sample_std"]),
            ]
            for row in data
        ],
    )


def term_descriptive_table(
    rows: list[dict[str, str]],
) -> str:
    """Render all frozen term-spread descriptive rows."""

    return markdown_table(
        [
            "Spread",
            "Regime",
            "n",
            "Mean (bps)",
            "Median",
            "Std. dev.",
        ],
        [
            [
                row["spread_name"],
                row["regime_label"],
                integer(row["n"]),
                number(row["mean"]),
                number(row["median"]),
                number(row["sample_std"]),
            ]
            for row in rows
        ],
    )


def cross_descriptive_table(
    rows: list[dict[str, str]],
) -> str:
    """Render all comparable-maturity difference rows."""

    return markdown_table(
        [
            "Tenor",
            "Regime",
            "n",
            "Mean difference (bps)",
            "Median",
            "Std. dev.",
        ],
        [
            [
                row["tenor"],
                row["regime_label"],
                integer(row["n"]),
                number(row["mean"]),
                number(row["median"]),
                number(row["sample_std"]),
            ]
            for row in rows
        ],
    )


def regime_inference_table(
    rows: list[dict[str, str]],
    label_field: str,
) -> str:
    """Render a complete frozen regime-comparison inferential family."""

    data = inferential_rows(rows)

    return markdown_table(
        [
            "Target",
            "n",
            "Easing mean",
            "Tightening mean",
            "Tightening − easing",
            "95% CI",
            "BH p",
            "Reject 5%",
        ],
        [
            [
                row[label_field],
                integer(row["sample_n"]),
                number(row["mean_easing"]),
                number(row["mean_tightening"]),
                number(row["estimate"]),
                (
                    "["
                    + number(row["ci_95_low"])
                    + ", "
                    + number(row["ci_95_high"])
                    + "]"
                ),
                p_value(row["p_value_bh"]),
                ("Yes" if row["reject_bh_0_05"] == "1" else "No"),
            ]
            for row in data
        ],
    )


def selected_yield_inference_table(
    rows: list[dict[str, str]],
) -> str:
    """Render representative PKRV maturities from a yield inferential family."""

    selected = {
        "3M",
        "1Y",
        "5Y",
        "10Y",
        "20Y",
    }

    data = [
        row
        for row in inferential_rows(rows)
        if row["curve_type"] == "PKRV" and row["tenor"] in selected
    ]

    ordering = {
        "3M": 0,
        "1Y": 1,
        "5Y": 2,
        "10Y": 3,
        "20Y": 4,
    }

    data.sort(key=lambda row: ordering[row["tenor"]])

    return markdown_table(
        [
            "Tenor",
            "n",
            "Easing mean",
            "Tightening mean",
            "Estimate",
            "95% CI",
            "BH p",
            "Reject 5%",
        ],
        [
            [
                row["tenor"],
                integer(row["sample_n"]),
                number(row["mean_easing"]),
                number(row["mean_tightening"]),
                number(row["estimate"]),
                (
                    "["
                    + number(row["ci_95_low"])
                    + ", "
                    + number(row["ci_95_high"])
                    + "]"
                ),
                p_value(row["p_value_bh"]),
                ("Yes" if row["reject_bh_0_05"] == "1" else "No"),
            ]
            for row in data
        ],
    )


def zero_difference_table(
    rows: list[dict[str, str]],
) -> str:
    """Render the full cross-curve zero-mean test family."""

    data = inferential_rows(rows)

    return markdown_table(
        [
            "Tenor",
            "n",
            "Mean difference (bps)",
            "95% CI",
            "BH p",
            "Reject zero mean",
        ],
        [
            [
                row["tenor"],
                integer(row["sample_n"]),
                number(row["estimate"]),
                (
                    "["
                    + number(row["ci_95_low"])
                    + ", "
                    + number(row["ci_95_high"])
                    + "]"
                ),
                p_value(row["p_value_bh"]),
                ("Yes" if row["reject_bh_0_05"] == "1" else "No"),
            ]
            for row in data
        ],
    )


def event_rejection_table(
    rows: list[dict[str, str]],
) -> str:
    """Render every event-window test surviving BH correction."""

    rejected = [row for row in inferential_rows(rows) if row["reject_bh_0_05"] == "1"]

    rejected.sort(
        key=lambda row: (
            row["curve_type"],
            row["tenor"],
            int(row["half_window"]),
            row["decision_type"],
        )
    )

    return markdown_table(
        [
            "Curve",
            "Tenor",
            "Half-window",
            "Decision",
            "n",
            "Mean move (bps)",
            "95% CI",
            "BH p",
        ],
        [
            [
                row["curve_type"],
                row["tenor"],
                row["half_window"],
                row["decision_type"],
                integer(row["sample_n"]),
                number(row["estimate"]),
                (
                    "["
                    + number(row["ci_95_low"])
                    + ", "
                    + number(row["ci_95_high"])
                    + "]"
                ),
                p_value(row["p_value_bh"]),
            ]
            for row in rejected
        ],
    )


def artifact_source_table() -> str:
    """Render the frozen empirical source inventory."""

    rows = []

    for spec in FROZEN_ARTIFACTS.values():
        path = spec["path"].relative_to(PROJECT_ROOT)

        rows.append(
            [
                f"`{path}`",
                f"{spec['rows']:,}",
                f"`{spec['sha']}`",
            ]
        )

    return markdown_table(
        [
            "Frozen artifact",
            "Rows",
            "SHA-256",
        ],
        rows,
    )


def main() -> None:
    """Generate the academic paper."""

    data = verify_frozen_sources()

    levels = data["descriptive_levels"]

    changes = data["descriptive_changes"]

    terms = data["descriptive_terms"]

    cross = data["descriptive_cross"]

    monthly_panel = data["monthly_panel"]

    infer_levels = data["infer_levels"]

    infer_changes = data["infer_changes"]

    infer_terms = data["infer_terms"]

    infer_events = data["infer_events"]

    infer_cross_zero = data["infer_cross_zero"]

    infer_cross_regime = data["infer_cross_regime"]

    level_inferential_n = len(inferential_rows(infer_levels))

    change_inferential_n = len(inferential_rows(infer_changes))

    term_inferential_n = len(inferential_rows(infer_terms))

    event_inferential_n = len(inferential_rows(infer_events))

    cross_zero_inferential_n = len(inferential_rows(infer_cross_zero))

    cross_regime_inferential_n = len(inferential_rows(infer_cross_regime))

    level_rejections = reject_count(infer_levels)

    change_rejections = reject_count(infer_changes)

    term_rejections = reject_count(infer_terms)

    event_rejections = reject_count(infer_events)

    cross_zero_rejections = reject_count(infer_cross_zero)

    cross_regime_rejections = reject_count(infer_cross_regime)

    monthly_periods = sorted({row["period"] for row in monthly_panel})

    monthly_change_nonmissing = sum(
        bool(row["monthly_yield_change_bps"]) for row in monthly_panel
    )

    monthly_change_missing = len(monthly_panel) - monthly_change_nonmissing

    monthly_curves = Counter(row["curve_type"] for row in monthly_panel)

    publication_summary = (
        f"{level_rejections} of {level_inferential_n} frozen "
        "yield-level regime tests, "
        f"{change_rejections} of {change_inferential_n} "
        "yield-change regime tests, "
        f"{term_rejections} of {term_inferential_n} "
        "term-spread regime tests, "
        f"{cross_zero_rejections} of "
        f"{cross_zero_inferential_n} cross-curve zero-mean tests, "
        f"and {cross_regime_rejections} of "
        f"{cross_regime_inferential_n} cross-curve regime tests "
        "reject their respective null hypotheses after the frozen "
        "Benjamini-Hochberg adjustment. "
        f"For MPC announcement windows, {event_rejections} of "
        f"{event_inferential_n} inferential groups reject a zero "
        "mean window movement after the same multiplicity adjustment."
    )

    paper = f"""# Monetary Policy, Sovereign Yield-Curve Dynamics, and Conventional–Shariah-Compliant Benchmark Comparisons in Pakistan

## 1. Abstract

This paper examines how Pakistan's sovereign benchmark yield structure varies
across monetary-policy environments, how benchmark yields move within defined
observation windows around State Bank of Pakistan Monetary Policy Committee
(MPC) announcements, and how comparable conventional PKRV and
Shariah-compliant PKISRV benchmark rates differ numerically where exact-date
maturity matches are available. The empirical system uses provenance-controlled
benchmark-yield data, official policy-rate and MPC records, and Pakistan Bureau
of Statistics national CPI observations. The conventional PKRV sample contains
22,800 source-observed benchmark yields across 1,149 accepted market dates from
4 January 2022 through 28 September 2026. PKISRV contains 2,015 observations
across 403 accepted market dates from 3 February 2025 through 30 September
2026. The event dataset contains 39 validated MPC meetings.

The analysis deliberately separates descriptive evidence from inferential
evidence. Directional monetary-policy regimes are observational classifications,
not causal treatments. MPC windows are based on available market-observation
positions rather than assumed calendar trading days. Comparable PKRV/PKISRV
differences are constructed only on exact same dates and maturities. The frozen
inferential layer reports HAC-based regime comparisons where applicable,
one-sample event-window tests, confidence intervals, and
Benjamini-Hochberg-adjusted p-values. {publication_summary}

These findings document substantial empirical differences across regimes,
maturities, and benchmark families, but they do not identify causal monetary
transmission, monetary-policy surprises, or structural reasons for PKISRV-PKRV
differences. Macroeconomic CPI/yield evidence remains descriptive in the frozen
research layer.

**Evidence sources:** `data/interim/research_evidence_map.csv`;
`docs/RESEARCH_PUBLICATION_SOURCE_PACKET.md`; frozen inferential artifacts
listed in Section 16.

## 2. Research Motivation

Pakistan's sovereign benchmark curve provides a direct view of how market
interest-rate benchmarks vary across maturities and over changing
monetary-policy environments. A maturity-specific approach matters because a
single yield cannot describe the entire term structure: shorter maturities,
intermediate maturities, and longer maturities may exhibit different level,
change, and curve-shape patterns.

The project also permits a separate comparison between conventional PKRV and
Shariah-compliant PKISRV benchmark structures. That comparison is useful only
when the two structures are matched carefully. Accordingly, this study treats
the numerical quantity `PKISRV - PKRV` as a benchmark difference, not as an
economic premium or discount.

The research design therefore addresses three empirical needs: disciplined
yield-curve measurement, announcement-window evidence around MPC meetings, and
exact-date conventional/Shariah-compliant benchmark comparison. A fourth
macroeconomic question involving CPI is retained, but the frozen evidence does
not support an inferential macroeconomic model.

**Evidence source:** `docs/RESEARCH_QUESTIONS.md`;
`data/interim/research_evidence_map.csv`.

## 3. Institutional and Market Context

The empirical system combines benchmark rates published through the Mutual
Funds Association of Pakistan with official State Bank of Pakistan monetary
policy information and Pakistan Bureau of Statistics CPI data. PKRV represents
the conventional sovereign benchmark curve used in this project. PKISRV
provides the Shariah-compliant sovereign benchmark observations available in
the normalized sample.

The State Bank of Pakistan's MPC decisions are classified at source as `HIKE`,
`CUT`, or `HOLD`. The later analytical regime layer uses directional states:
a prior hike establishes `TIGHTENING`, a prior cut establishes `EASING`, and a
hold inherits the latest prior directional state. An observation on the same
calendar date as an MPC announcement is not automatically treated as
post-announcement because compatible intraday timestamps are unavailable.

This institutional setup is important for interpretation. The study observes
benchmark yields and official policy decisions; it does not observe a complete
market-expectations series capable of identifying an unexpected monetary-policy
shock.

**Evidence sources:** normalized PakYield database lineage; frozen MPC,
regime, and publication evidence artifacts.

## 4. Research Questions

The accepted central research question is:

> How does monetary policy transmit across Pakistan's sovereign yield curve,
> and how do conventional and Shariah-compliant sovereign benchmark rates
> behave across maturities and monetary-policy regimes?

The four frozen research questions are:

1. **RQ1 — Conventional yield-curve evolution:** How has Pakistan's
   conventional sovereign benchmark yield curve evolved across different
   monetary-policy environments?
2. **RQ2 — MPC announcement-window reactions:** How do maturity points behave
   within defined observation windows around SBP MPC announcements?
3. **RQ3 — Conventional versus Shariah-compliant benchmarks:** How closely do
   comparable PKRV and PKISRV maturity points move together, and how does the
   numerical PKISRV-PKRV difference vary across maturity and time?
4. **RQ4 — Macroeconomic relationships:** What statistical relationships exist
   between Pakistan's macroeconomic environment and selected portions of the
   sovereign yield curve?

The pre-analysis hypotheses concern short-versus-long announcement-window
sensitivity (H1), conventional/PKISRV co-movement (H2), cross-curve difference
variation (H3), and term-spread differences across policy environments (H4).

The frozen publication evidence does **not** contain a dedicated direct
short-minus-long event-response contrast for H1 or a dedicated correlation or
co-movement inferential family for H2. Those hypotheses therefore cannot be
resolved directly from the available frozen tests.

**Evidence sources:** `docs/RESEARCH_QUESTIONS.md`;
`data/interim/research_evidence_map.csv`.

## 5. Data and Sample

The normalized empirical sample contains:

- 22,800 PKRV benchmark-yield observations over 1,149 accepted market dates,
  covering 4 January 2022 to 28 September 2026;
- 2,015 PKISRV observations over 403 accepted market dates, covering
  3 February 2025 to 30 September 2026;
- 39 validated SBP MPC events from 24 January 2022 to 14 September 2026;
- 18 official policy-rate observations, comprising one pre-sample state anchor
  and 17 in-sample changes;
- 57 monthly national CPI observations from January 2022 through September
  2026.

The monthly CPI/yield analytical panel contains {len(monthly_panel):,} rows
across {len(monthly_periods)} distinct periods from
{monthly_periods[0]} through {monthly_periods[-1]}. It contains
{monthly_curves["PKRV"]:,} PKRV rows and {monthly_curves["PKISRV"]:,} PKISRV
rows. CPI inflation is available throughout the frozen monthly analytical
panel. Monthly yield changes are non-missing for
{monthly_change_nonmissing:,} rows and missing for
{monthly_change_missing:,} rows under the consecutive-calendar-month rule.

PKISRV has a shorter historical window and a narrower observed tenor universe
than PKRV. Cross-curve evidence must therefore be interpreted over the
available common date-tenor sample rather than as a full-history comparison.

**Evidence sources:** `data/interim/descriptive_monthly_sample_census.csv`;
`data/interim/monthly_cpi_yield_panel.csv`; normalized project state.

## 6. Methodology

### 6.1 Yield observations and daily changes

Yield changes use the previous available observation within the exact
`curve_type × tenor` series. Missing observations are not treated as zero, and
no hidden interpolation is introduced.

### 6.2 Term spreads

Selected PKRV term spreads are formed only from exact same-date observed
maturities. The frozen spread set is `10Y-2Y`, `10Y-1Y`, `5Y-1Y`, and
`3Y-3M`. When a required leg is absent, the spread remains ineligible rather
than being reconstructed from another date or maturity.

### 6.3 Monetary-policy regimes

Directional regimes use MPC decisions strictly before a yield observation.
`HIKE` establishes `TIGHTENING`, `CUT` establishes `EASING`, and `HOLD`
inherits the latest directional state. MPC announcement dates themselves are
excluded from ordinary regime-comparison eligibility when intraday ordering
cannot be established.

### 6.4 MPC announcement windows

For half-window `h ∈ {{1, 3, 5}}`, the left endpoint is the `h`-th distinct
available curve observation strictly before the event date and the right
endpoint is the `h`-th distinct available observation strictly after it. The
window movement is the right yield minus the left yield in basis points.
Same-day observations do not replace either endpoint.

These are announcement-window movements, not estimates of policy surprise or
identified causal effects.

### 6.5 PKRV/PKISRV comparison

Cross-curve comparisons require the exact same calendar date and exact
comparable maturity. The numerical comparison is:

`(PKISRV yield − PKRV yield) × 100`

in basis points. No structural pricing interpretation is attached to the sign
or magnitude without separate evidence.

### 6.6 Inferential layer

Frozen directional-regime comparisons use the test method recorded in the
inferential artifacts, predominantly `OLS_HAC_NEWEY_WEST`, with the frozen HAC
lag reported per test. Mean cross-curve differences against zero use
`INTERCEPT_ONLY_OLS_HAC_NEWEY_WEST`. MPC announcement-window group means are
tested against zero using the frozen `ONE_SAMPLE_T_TEST` family.

The project reports raw and Benjamini-Hochberg-adjusted p-values and uses the
frozen `reject_bh_0_05` indicator for multiplicity-adjusted 5% decisions.
Statistical rejection is not treated as proof of economic importance or
causality.

**Evidence sources:** frozen Phase 5C and Phase 6 analytical contracts;
inferential artifacts listed in Section 16.

## 7. Descriptive Evidence

### 7.1 Conventional benchmark levels

Representative PKRV maturities show visibly different yield-level
distributions across the directional regimes.

{selected_pk_rv_descriptive_table(levels, "percentage points")}

This table is descriptive. It establishes sample means and distributions; it
does not by itself show that monetary policy caused the differences.

**Evidence source:** `data/interim/descriptive_yield_levels.csv`.

### 7.2 Daily yield changes

Daily changes are substantially noisier than levels and therefore answer a
different empirical question.

{selected_pk_rv_descriptive_table(changes, "bps")}

**Evidence source:** `data/interim/descriptive_yield_changes.csv`.

### 7.3 Curve shape

The four selected PKRV long-short spreads display material distributional
differences across the two directional regimes.

{term_descriptive_table(terms)}

Negative values indicate that the longer maturity is numerically below the
shorter maturity for the stated spread definition. No causal meaning is
assigned automatically to a negative or positive slope.

**Evidence source:** `data/interim/descriptive_term_spreads.csv`.

## 8. MPC Announcement-Window Results

The descriptive event family contains 72 maturity/window/decision groups.
The corresponding inferential artifact contains
{event_inferential_n} groups with inferential estimates. After the frozen
Benjamini-Hochberg adjustment, {event_rejections} of those groups reject a
zero mean announcement-window movement at the 5% level.

The complete set of multiplicity-adjusted rejections, if any, is:

{event_rejection_table(infer_events)}

This result should be interpreted conservatively. A failure to reject does not
show that a maturity never moves materially around individual MPC meetings,
while a rejection does not identify the MPC announcement as the sole cause of
the movement. In addition, no market-expectations series is available, so the
policy-rate decision itself must not be described as a monetary-policy
surprise.

H1 remains unresolved as a direct short-versus-long hypothesis because the
frozen research layer does not contain a dedicated direct maturity-contrast
test. Maturity-specific event tests are informative but are not equivalent to
testing whether short-maturity responses exceed long-maturity responses.

**Evidence sources:** `data/interim/descriptive_mpc_event_windows.csv`;
`data/interim/inferential_mpc_event_windows.csv`;
`data/interim/research_evidence_map.csv`.

## 9. Monetary-Policy Regime Results

The regime evidence is strongest for yield **levels**, where
{level_rejections} of {level_inferential_n} frozen tests reject equality
between tightening and easing means after multiplicity adjustment. Yield
**changes** produce {change_rejections} rejections among
{change_inferential_n} frozen regime tests, indicating that conclusions about
levels should not be mechanically transferred to daily changes.

Representative PKRV yield-level comparisons are:

{selected_yield_inference_table(infer_levels)}

Representative PKRV yield-change comparisons are:

{selected_yield_inference_table(infer_changes)}

The selected long-short term-spread family contains
{term_inferential_n} inferential tests, of which {term_rejections} reject the
regime-equality null after adjustment.

{regime_inference_table(infer_terms, "spread_name")}

These are observational regime comparisons. The estimates document
differences between classified periods; they do not establish that a policy
decision caused the full difference in yields or curve slope.

**Evidence sources:** `data/interim/inferential_yield_level_regime.csv`;
`data/interim/inferential_yield_change_regime.csv`;
`data/interim/inferential_term_spread_regime.csv`.

## 10. PKRV/PKISRV Comparative Results

Exact-date, exact-maturity matched observations show that the numerical
PKISRV-PKRV difference varies across both maturity and regime.

{cross_descriptive_table(cross)}

The frozen zero-mean tests provide the following maturity-specific estimates:

{zero_difference_table(infer_cross_zero)}

Across the {cross_zero_inferential_n} frozen maturity-specific zero-mean
tests, {cross_zero_rejections} reject a zero mean after the
Benjamini-Hochberg adjustment.

The directional-regime comparison for the same numerical difference is:

{regime_inference_table(infer_cross_regime, "tenor")}

Among these {cross_regime_inferential_n} tests,
{cross_regime_rejections} reject equality between tightening and easing
means after multiplicity adjustment.

These results establish numerical benchmark differences and, where the test
rejects, statistically distinguishable frozen comparisons. They do **not**
identify the cause of those differences. In particular, the differences are
not labeled Islamic, Sukuk, Shariah, liquidity, credit, tax, or other
structural premia.

H2 also remains directly unresolved because the frozen research layer does
not contain the correlation or other co-movement test specified as necessary
for a direct evaluation of that hypothesis.

**Evidence sources:** `data/interim/descriptive_cross_curve_differences.csv`;
`data/interim/inferential_cross_curve_zero.csv`;
`data/interim/inferential_cross_curve_regime.csv`;
`data/interim/research_evidence_map.csv`.

## 11. Inferential Findings

The frozen inferential evidence can be summarized without extending beyond
its statistical scope:

- Yield-level directional-regime tests reject equality in
  **{level_rejections}/{level_inferential_n}** frozen tests after BH
  adjustment.
- Yield-change directional-regime tests reject equality in
  **{change_rejections}/{change_inferential_n}** tests.
- Selected term-spread directional-regime tests reject equality in
  **{term_rejections}/{term_inferential_n}** tests.
- MPC announcement-window tests reject a zero mean in
  **{event_rejections}/{event_inferential_n}** inferential groups.
- Cross-curve zero-mean tests reject in
  **{cross_zero_rejections}/{cross_zero_inferential_n}** comparable
  maturities.
- Cross-curve directional-regime tests reject equality in
  **{cross_regime_rejections}/{cross_regime_inferential_n}** comparable
  maturities.

These counts use the frozen adjusted decisions rather than selectively
reporting raw p-values. They are not causal estimates.

The evidence available for H3 and H4 includes direct inferential families for
regime variation. The publication layer reports those tests but does not
manufacture an additional formal hypothesis-status artifact. H1 and H2 retain
the direct-test limitations identified in the frozen evidence register.

**Evidence source:** frozen inferential artifacts and
`data/interim/research_evidence_map.csv`.

## 12. Macroeconomic Evidence

The monthly CPI/yield family covers {len(monthly_periods)} periods and
{len(monthly_panel):,} curve-tenor-month observations. It provides a verified
sample for describing monthly yield and CPI availability.

However, the frozen research evidence explicitly classifies this family as
descriptive-only. No macroeconomic inferential relationship, causal model, or
forecasting model has been estimated in the accepted evidence layer.
Consequently RQ4 remains open at the inferential level.

This boundary is substantive rather than cosmetic: a monthly panel containing
both yields and CPI does not by itself justify statements about the statistical
effect of inflation on sovereign yields.

**Evidence sources:** `data/interim/descriptive_monthly_sample_census.csv`;
`data/interim/monthly_cpi_yield_panel.csv`;
`data/interim/research_evidence_map.csv`.

## 13. Limitations

Several limitations materially restrict interpretation.

First, MPC announcement windows do not constitute a causal identification
strategy. Other macroeconomic, fiscal, liquidity, exchange-rate, geopolitical,
or market information may arrive during the same observation window.

Second, no market-expectations series is incorporated. A policy-rate change is
therefore a policy-rate change, not an identified policy surprise.

Third, PKISRV begins later than PKRV and has a narrower observed maturity
universe. Cross-curve results therefore refer only to exact overlapping
date-maturity observations.

Fourth, H1 lacks a frozen direct short-minus-long event-response contrast, so
individual maturity significance cannot resolve the hypothesis.

Fifth, H2 lacks a frozen direct correlation or co-movement inferential family.
Distributions of cross-curve differences are not substitutes for a direct
co-movement statistic.

Sixth, the CPI/yield family remains descriptive. RQ4 therefore has no accepted
inferential macroeconomic estimate.

Seventh, observational regime comparisons may be influenced by variables that
co-vary with the monetary-policy environment. They should not be interpreted
as causal treatment effects.

Finally, statistical significance and economic significance are distinct.
The frozen inferential layer supplies estimates, uncertainty measures, and
multiple-testing adjustments, but economic interpretation remains narrower
than those statistical outputs.

## 14. Conclusion

PakYield provides a reproducible empirical view of Pakistan's conventional
sovereign benchmark curve, a shorter Shariah-compliant benchmark history, and
their behavior across directional monetary-policy environments and MPC
announcement windows.

The strongest frozen evidence concerns systematic differences in benchmark
**levels** across policy regimes and measurable variation in selected term
spreads and exact-date PKISRV-PKRV differences. Daily yield-change evidence is
more mixed than level evidence. Announcement-window averages also vary across
maturity, decision type, and window length, but the multiplicity-adjusted
inferential layer is deliberately more restrictive than a simple inspection
of raw movements.

The cross-curve results establish that numerical PKISRV-PKRV differences are
not constant across all observed maturity-regime combinations. They do not
establish the structural mechanism responsible for those differences.
Likewise, regime associations do not establish causal monetary-policy
transmission.

The study therefore answers the empirical questions at the level supported by
the frozen evidence while retaining explicit unresolved areas: causal
identification, policy-surprise measurement, direct short-versus-long event
contrasts, direct cross-curve co-movement inference, and macroeconomic
regression analysis.

## 15. Reproducibility Note

This paper is generated by:

`scripts/build_academic_research_paper.py`

The builder verifies the frozen SHA-256 hashes and row counts of every
publication evidence artifact before writing the paper. If any upstream
publication artifact changes, construction fails rather than silently
regenerating a different empirical narrative.

The publication evidence register contains 24 rows and is frozen at:

`{EXPECTED_EVIDENCE_MAP_SHA}`

The publication source packet is frozen at:

`{EXPECTED_SOURCE_PACKET_SHA}`

The paper is generated from evidence artifacts only; it performs no new
statistical estimation.

## 16. References and Source Notes

### Primary data organizations

- **Mutual Funds Association of Pakistan (MUFAP):** source organization for
  normalized PKRV and PKISRV benchmark-yield observations used by PakYield.
- **State Bank of Pakistan (SBP):** source organization for official policy-rate
  observations and validated MPC decisions.
- **Pakistan Bureau of Statistics (PBS):** source organization for national CPI
  observations.

### Frozen project evidence

{artifact_source_table()}

### Publication governance sources

- `docs/RESEARCH_QUESTIONS.md` — frozen research questions, hypotheses,
  variable definitions, and interpretation restrictions.
- `docs/PUBLICATION_PLAN.md` — required publication structure and
  non-negotiable interpretation boundaries.
- `docs/RESEARCH_PUBLICATION_SOURCE_PACKET.md` — frozen evidence-to-publication
  register.
- `data/interim/research_evidence_map.csv` — machine-readable evidence map.

All substantive empirical statements in this paper are intended to remain
within the interpretation boundaries assigned to those frozen sources.
"""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        paper,
        encoding="utf-8",
    )

    print("===== ACADEMIC RESEARCH PAPER =====")

    print(
        "Output:",
        OUTPUT_PATH.relative_to(PROJECT_ROOT),
    )

    print(
        "Lines:",
        len(paper.splitlines()),
    )

    print(
        "Words:",
        len(paper.split()),
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print("Frozen inferential rejection census:")

    print(
        "  yield_level_regime:",
        f"{level_rejections}/{level_inferential_n}",
    )

    print(
        "  yield_change_regime:",
        f"{change_rejections}/{change_inferential_n}",
    )

    print(
        "  term_spread_regime:",
        f"{term_rejections}/{term_inferential_n}",
    )

    print(
        "  mpc_event_window:",
        f"{event_rejections}/{event_inferential_n}",
    )

    print(
        "  cross_curve_zero:",
        f"{cross_zero_rejections}/{cross_zero_inferential_n}",
    )

    print(
        "  cross_curve_regime:",
        f"{cross_regime_rejections}/{cross_regime_inferential_n}",
    )

    print("")
    print("PASS: evidence-grounded Phase 8B academic paper constructed")


if __name__ == "__main__":
    main()
