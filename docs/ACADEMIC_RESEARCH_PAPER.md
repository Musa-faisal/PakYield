# Monetary Policy, Sovereign Yield-Curve Dynamics, and Conventional–Shariah-Compliant Benchmark Comparisons in Pakistan

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
Benjamini-Hochberg-adjusted p-values. 24 of 25 frozen yield-level regime tests, 10 of 25 yield-change regime tests, 4 of 4 term-spread regime tests, 5 of 5 cross-curve zero-mean tests, and 4 of 5 cross-curve regime tests reject their respective null hypotheses after the frozen Benjamini-Hochberg adjustment. For MPC announcement windows, 0 of 54 inferential groups reject a zero mean window movement after the same multiplicity adjustment.

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

The monthly CPI/yield analytical panel contains 1,234 rows
across 57 distinct periods from
2022-01 through 2026-09. It contains
1,134 PKRV rows and 100 PKISRV
rows. CPI inflation is available throughout the frozen monthly analytical
panel. Monthly yield changes are non-missing for
1,203 rows and missing for
31 rows under the consecutive-calendar-month rule.

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

For half-window `h ∈ {1, 3, 5}`, the left endpoint is the `h`-th distinct
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

| Tenor | Regime | n | Mean (percentage points) | Median | Std. dev. |
| --- | --- | --- | --- | --- | --- |
| 3M | EASING | 447 | 12.59 | 11.24 | 2.89 |
| 3M | TIGHTENING | 573 | 17.76 | 17.73 | 3.92 |
| 1Y | EASING | 447 | 12.37 | 11.59 | 2.36 |
| 1Y | TIGHTENING | 601 | 18.09 | 18.90 | 3.80 |
| 5Y | EASING | 447 | 12.21 | 12.06 | 1.26 |
| 5Y | TIGHTENING | 601 | 14.42 | 15.07 | 1.62 |
| 10Y | EASING | 447 | 12.31 | 12.15 | 0.72 |
| 10Y | TIGHTENING | 601 | 13.95 | 14.15 | 1.26 |
| 20Y | EASING | 447 | 12.44 | 12.36 | 0.60 |
| 20Y | TIGHTENING | 601 | 14.05 | 14.01 | 0.93 |

This table is descriptive. It establishes sample means and distributions; it
does not by itself show that monetary policy caused the differences.

**Evidence source:** `data/interim/descriptive_yield_levels.csv`.

### 7.2 Daily yield changes

Daily changes are substantially noisier than levels and therefore answer a
different empirical question.

| Tenor | Regime | n | Mean (bps) | Median | Std. dev. |
| --- | --- | --- | --- | --- | --- |
| 3M | EASING | 447 | -2.09 | 0.00 | 10.47 |
| 3M | TIGHTENING | 573 | 1.31 | 1.00 | 15.03 |
| 1Y | EASING | 447 | -1.88 | 0.00 | 10.80 |
| 1Y | TIGHTENING | 601 | 1.35 | 0.00 | 16.00 |
| 5Y | EASING | 447 | -0.94 | 0.00 | 9.64 |
| 5Y | TIGHTENING | 601 | 0.52 | 0.00 | 11.10 |
| 10Y | EASING | 447 | -0.46 | 0.00 | 6.87 |
| 10Y | TIGHTENING | 601 | 0.34 | 0.00 | 8.27 |
| 20Y | EASING | 447 | -0.37 | 0.00 | 6.05 |
| 20Y | TIGHTENING | 601 | 0.21 | 0.00 | 6.27 |

**Evidence source:** `data/interim/descriptive_yield_changes.csv`.

### 7.3 Curve shape

The four selected PKRV long-short spreads display material distributional
differences across the two directional regimes.

| Spread | Regime | n | Mean (bps) | Median | Std. dev. |
| --- | --- | --- | --- | --- | --- |
| 10Y-1Y | EASING | 447 | -6.38 | 69.00 | 173.90 |
| 10Y-1Y | TIGHTENING | 601 | -413.47 | -407.00 | 264.93 |
| 10Y-2Y | EASING | 447 | 11.49 | 55.00 | 115.55 |
| 10Y-2Y | TIGHTENING | 601 | -220.75 | -286.00 | 178.05 |
| 3Y-3M | EASING | 447 | -49.72 | 12.00 | 139.99 |
| 3Y-3M | TIGHTENING | 573 | -221.47 | -207.00 | 175.02 |
| 5Y-1Y | EASING | 447 | -15.69 | 39.00 | 118.95 |
| 5Y-1Y | TIGHTENING | 601 | -367.04 | -326.00 | 230.76 |

Negative values indicate that the longer maturity is numerically below the
shorter maturity for the stated spread definition. No causal meaning is
assigned automatically to a negative or positive slope.

**Evidence source:** `data/interim/descriptive_term_spreads.csv`.

## 8. MPC Announcement-Window Results

The descriptive event family contains 72 maturity/window/decision groups.
The corresponding inferential artifact contains
54 groups with inferential estimates. After the frozen
Benjamini-Hochberg adjustment, 0 of those groups reject a
zero mean announcement-window movement at the 5% level.

The complete set of multiplicity-adjusted rejections, if any, is:

_No rows satisfy this frozen selection rule._

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
24 of 25 frozen tests reject equality
between tightening and easing means after multiplicity adjustment. Yield
**changes** produce 10 rejections among
25 frozen regime tests, indicating that conclusions about
levels should not be mechanically transferred to daily changes.

Representative PKRV yield-level comparisons are:

| Tenor | n | Easing mean | Tightening mean | Estimate | 95% CI | BH p | Reject 5% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3M | 1,020 | 12.59 | 17.76 | 5.17 | [4.08, 6.27] | 1.56e-19 | Yes |
| 1Y | 1,048 | 12.37 | 18.09 | 5.72 | [4.74, 6.70] | 9.98e-28 | Yes |
| 5Y | 1,048 | 12.21 | 14.42 | 2.20 | [1.74, 2.66] | 3.90e-20 | Yes |
| 10Y | 1,048 | 12.31 | 13.95 | 1.64 | [1.33, 1.96] | 1.00e-22 | Yes |
| 20Y | 1,048 | 12.44 | 14.05 | 1.60 | [1.36, 1.85] | 4.47e-34 | Yes |

Representative PKRV yield-change comparisons are:

| Tenor | n | Easing mean | Tightening mean | Estimate | 95% CI | BH p | Reject 5% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3M | 1,020 | -2.09 | 1.31 | 3.40 | [1.57, 5.22] | 0.001 | Yes |
| 1Y | 1,048 | -1.88 | 1.35 | 3.23 | [1.28, 5.19] | 0.004 | Yes |
| 5Y | 1,048 | -0.94 | 0.52 | 1.46 | [0.03, 2.89] | 0.072 | No |
| 10Y | 1,048 | -0.46 | 0.34 | 0.80 | [-0.20, 1.81] | 0.147 | No |
| 20Y | 1,048 | -0.37 | 0.21 | 0.58 | [-0.21, 1.37] | 0.180 | No |

The selected long-short term-spread family contains
4 inferential tests, of which 4 reject the
regime-equality null after adjustment.

| Target | n | Easing mean | Tightening mean | Tightening − easing | 95% CI | BH p | Reject 5% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10Y-1Y | 1,048 | -6.38 | -413.47 | -407.08 | [-476.53, -337.64] | 1.29e-28 | Yes |
| 10Y-2Y | 1,048 | 11.49 | -220.75 | -232.24 | [-278.86, -185.63] | 1.56e-21 | Yes |
| 3Y-3M | 1,020 | -49.72 | -221.47 | -171.75 | [-222.08, -121.41] | 3.54e-11 | Yes |
| 5Y-1Y | 1,048 | -15.69 | -367.04 | -351.36 | [-407.45, -295.27] | 6.27e-32 | Yes |

These are observational regime comparisons. The estimates document
differences between classified periods; they do not establish that a policy
decision caused the full difference in yields or curve slope.

**Evidence sources:** `data/interim/inferential_yield_level_regime.csv`;
`data/interim/inferential_yield_change_regime.csv`;
`data/interim/inferential_term_spread_regime.csv`.

## 10. PKRV/PKISRV Comparative Results

Exact-date, exact-maturity matched observations show that the numerical
PKISRV-PKRV difference varies across both maturity and regime.

| Tenor | Regime | n | Mean difference (bps) | Median | Std. dev. |
| --- | --- | --- | --- | --- | --- |
| 1M | EASING | 290 | -146.06 | -126.00 | 66.94 |
| 1M | TIGHTENING | 98 | -49.07 | -30.00 | 189.20 |
| 1Y | EASING | 290 | -14.06 | -2.00 | 71.93 |
| 1Y | TIGHTENING | 98 | -117.35 | -113.00 | 37.22 |
| 3M | EASING | 290 | -114.02 | -110.50 | 53.67 |
| 3M | TIGHTENING | 98 | -127.55 | -131.50 | 55.82 |
| 6M | EASING | 290 | -45.83 | -59.50 | 77.55 |
| 6M | TIGHTENING | 98 | -122.46 | -118.50 | 16.26 |
| 9M | EASING | 290 | -40.76 | -50.00 | 61.91 |
| 9M | TIGHTENING | 98 | -79.19 | -83.00 | 63.32 |

The frozen zero-mean tests provide the following maturity-specific estimates:

| Tenor | n | Mean difference (bps) | 95% CI | BH p | Reject zero mean |
| --- | --- | --- | --- | --- | --- |
| 1M | 388 | -121.56 | [-148.07, -95.05] | 2.29e-17 | Yes |
| 1Y | 388 | -40.15 | [-56.01, -24.29] | 9.75e-07 | Yes |
| 3M | 388 | -117.44 | [-130.19, -104.68] | 8.44e-53 | Yes |
| 6M | 388 | -65.19 | [-81.14, -49.23] | 1.94e-14 | Yes |
| 9M | 388 | -50.47 | [-65.62, -35.32] | 2.32e-10 | Yes |

Across the 5 frozen maturity-specific zero-mean
tests, 5 reject a zero mean after the
Benjamini-Hochberg adjustment.

The directional-regime comparison for the same numerical difference is:

| Target | n | Easing mean | Tightening mean | Tightening − easing | 95% CI | BH p | Reject 5% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1M | 388 | -146.06 | -49.07 | 96.99 | [14.45, 179.54] | 0.033 | Yes |
| 1Y | 388 | -14.06 | -117.35 | -103.29 | [-125.64, -80.93] | 2.75e-17 | Yes |
| 3M | 388 | -114.02 | -127.55 | -13.53 | [-43.21, 16.15] | 0.371 | No |
| 6M | 388 | -45.83 | -122.46 | -76.62 | [-96.20, -57.05] | 2.93e-13 | Yes |
| 9M | 388 | -40.76 | -79.19 | -38.43 | [-72.30, -4.56] | 0.033 | Yes |

Among these 5 tests,
4 reject equality between tightening and easing
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
  **24/25** frozen tests after BH
  adjustment.
- Yield-change directional-regime tests reject equality in
  **10/25** tests.
- Selected term-spread directional-regime tests reject equality in
  **4/4** tests.
- MPC announcement-window tests reject a zero mean in
  **0/54** inferential groups.
- Cross-curve zero-mean tests reject in
  **5/5** comparable
  maturities.
- Cross-curve directional-regime tests reject equality in
  **4/5** comparable
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

The monthly CPI/yield family covers 57 periods and
1,234 curve-tenor-month observations. It provides a verified
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

`50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002`

The publication source packet is frozen at:

`e317d0044c3829f3255a91420290abe0f61b4d0864c8833e4c131e1dfc644948`

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

| Frozen artifact | Rows | SHA-256 |
| --- | --- | --- |
| `data/interim/descriptive_cross_curve_differences.csv` | 10 | `ec59b6148d5a5f2aa02b38cddfe3aeebb5bfa0f173e58e522b5df70961634477` |
| `data/interim/descriptive_monthly_sample_census.csv` | 25 | `d6a427f5580da4b99ea21ae64902da9494fed6325b4b674b71d9a08eca071d33` |
| `data/interim/descriptive_mpc_event_windows.csv` | 72 | `92c6af99dd2cbf445eef3c8964f3b4316778a81424ee04b74e4b2540a0fb11d3` |
| `data/interim/descriptive_term_spreads.csv` | 8 | `97f586c77e9636e09fd40d5fcc2f8049cee0fd95eb9b98eb66f4f5055f2cbf69` |
| `data/interim/descriptive_yield_changes.csv` | 50 | `a3a785b0c12ece10564ad3e2c0aea76e8cec100abbe34a83841f5276adb6f978` |
| `data/interim/descriptive_yield_levels.csv` | 50 | `88ce5b39d4dd29f4749be6bc75aaee9cd0f7cadce37c22c54c1fb6bf3db633a6` |
| `data/interim/inferential_cross_curve_regime.csv` | 5 | `f3cca17f6cf658828a9ac613d7fdf7764126e9da0a74760749a9109a8717a6a5` |
| `data/interim/inferential_cross_curve_zero.csv` | 5 | `14a906144b79f4a81dbe8b2df752a607600871bfc9de7e098e079b44e31f75de` |
| `data/interim/inferential_mpc_event_windows.csv` | 72 | `13673445d98051044a1fe5b019d712fadf6b4b544dde2c6cc64a8ca48441f2f1` |
| `data/interim/inferential_term_spread_regime.csv` | 4 | `17f7222dda8f17e14830d64f268b076ac365e66012b4fdf6aa38527a835e1349` |
| `data/interim/inferential_yield_change_regime.csv` | 25 | `4baf694f635fb183ef4072dde24b10924bd280241276940b83d19b2c3c2f9501` |
| `data/interim/inferential_yield_level_regime.csv` | 25 | `4c9ba3fdd6e920e905db3dc118e645ad904e2cbf0682c33d0c5228998790b1a4` |
| `data/interim/monthly_cpi_yield_panel.csv` | 1,234 | `978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7` |

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
