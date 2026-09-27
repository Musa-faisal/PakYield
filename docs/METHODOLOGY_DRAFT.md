# PakYield Lab — Methodology Draft

## 1. Purpose

This document defines the provisional empirical methodology for PakYield Lab before the principal datasets are collected and analyzed.

The methodology is intentionally described as a draft because several implementation choices depend on the real structure, coverage, and reliability of the source data.

The research methodology may be refined after the Phase 2 data-feasibility audit, but changes must be documented rather than made silently.

---

# 2. Research Design

PakYield Lab is primarily an empirical observational financial-market study.

The project combines:

* descriptive yield-curve analysis;
* monetary-policy announcement-window analysis;
* conventional versus Shariah-compliant benchmark comparison;
* macro-financial time-series analysis;
* fixed-income risk analytics;
* parametric yield-curve estimation.

The study is not designed initially as a causal identification exercise.

Therefore, unless stronger identification is later introduced, results will be interpreted as:

* market movements;
* associations;
* statistical relationships;
* announcement-window reactions;
* co-movements.

They will not automatically be interpreted as causal monetary-policy effects.

---

# 3. Research Workflow

The research workflow follows the broad sequence:

```text
Define
↓
Acquire
↓
Audit
↓
Clean
↓
Validate
↓
Transform
↓
Analyze
↓
Model
↓
Interpret
↓
Communicate
```

Data analysis should not begin before the relevant data have passed basic structural and quality checks.

---

# 4. Source Hierarchy

PakYield should prioritize authoritative sources.

The intended hierarchy is:

```text
1. Official Pakistani public-sector source
2. Official market or industry association source
3. Official publication or downloadable dataset
4. Reputable secondary source
5. Manual reconstruction only when necessary and documented
```

Likely primary organizations include:

```text
State Bank of Pakistan
Pakistan Bureau of Statistics
MUFAP or other authoritative benchmark publishers
```

The exact source URLs and files will be determined during Phase 2.

Secondary aggregators should not replace an available authoritative source merely because they are easier to download.

---

# 5. Raw-Data Preservation

Raw source data must be preserved in the form in which it was obtained wherever practical.

The intended pipeline is:

```text
source
↓
data/raw
↓
data/interim
↓
data/processed
↓
SQLite analytical database
↓
analysis and application
```

Raw files should not be manually overwritten after ingestion.

Cleaning and transformations should occur in reproducible code.

---

# 6. Core Dataset 1 — PKRV

PKRV will represent the conventional sovereign benchmark curve used in the project.

The Phase 2 audit must determine:

```text
available dates
available maturities
file format
observation frequency
missingness
historical consistency
methodology changes
publication timing
units
duplicate behavior
```

The project must not assume that the same tenor set exists throughout the entire historical sample.

---

# 7. Core Dataset 2 — PKISRV

PKISRV will represent the Shariah-compliant sovereign benchmark curve.

The same audit principles used for PKRV apply.

Special attention must be paid to:

```text
sample start date
maturity coverage
overlap with PKRV
missing dates
benchmark-definition changes
comparability across maturities
```

The PKRV/PKISRV comparison sample may therefore be shorter than the PKRV-only sample.

That is acceptable.

---

# 8. Core Dataset 3 — SBP Monetary-Policy Events

A structured MPC event dataset should be built from authoritative State Bank of Pakistan records.

Each event should attempt to record:

```text
event_id
announcement_date
effective_date
policy_rate_before
policy_rate_after
policy_rate_change_bps
decision_type
source_url
source_document
notes
```

Decision categories:

```text
HIKE
CUT
HOLD
```

Policy-rate changes are calculated as:

```text
(policy_rate_after - policy_rate_before) × 100
```

when rates are stored in percentage-point units.

---

# 9. Core Dataset 4 — Policy-Rate History

The policy-rate dataset should distinguish between:

```text
announcement date
effective date
rate level
rate change
```

where source information allows.

The project must not casually interchange announcement dates and effective dates.

For the event study, the announcement date is expected to be the primary event anchor unless the Phase 2 audit shows that another convention is more defensible.

---

# 10. Core Dataset 5 — CPI Inflation

Pakistan CPI data should preferably come from an authoritative public-sector source.

The intended working variable is likely:

```text
cpi_inflation_yoy_pct
```

representing year-on-year CPI inflation.

The Phase 2 audit must determine:

```text
exact series
headline versus other CPI measure
frequency
reference period
publication date
historical revisions
units
```

PakYield should not silently mix different inflation definitions.

---

# 11. Optional Exchange-Rate Dataset

PKR/USD may be included if a reliable and consistently defined source is available.

Provisional representation:

```text
pkr_per_usd
```

Under this convention:

```text
higher value = weaker PKR against USD
lower value  = stronger PKR against USD
```

FX inclusion is optional and should not delay the main research project.

---

# 12. Observation Model for Yield Data

The preferred long-form yield schema is:

```text
date
curve_type
tenor
maturity_years
yield_pct
source
```

Example:

```text
2025-01-15 | PKRV | 5Y | 5.0 | 12.40 | source
```

Long-form storage is preferred because it is easier to:

```text
validate
filter
group
join
plot
fit curves
add maturities
```

than a permanently wide table.

Wide representations may still be created for specific analytical tasks.

---

# 13. Yield Units

Benchmark yields should be stored in:

```text
percentage points
```

Example:

```text
12.50
```

means:

```text
12.50%
```

and not:

```text
0.125
```

unless a mathematical function explicitly converts the percentage rate into decimal form.

---

# 14. Basis-Point Convention

One basis point equals:

```text
0.01 percentage points
```

Therefore:

```text
12.00% → 12.25%
```

equals:

```text
+25 bps
```

and:

```text
18.00% → 16.50%
```

equals:

```text
-150 bps
```

The general conversion is:

```text
basis_point_change
=
(new_yield_pct - old_yield_pct) × 100
```

---

# 15. Tenor Normalization

Text maturities should be mapped to numeric years where appropriate.

Provisional examples:

```text
3M  → 0.25
6M  → 0.50
1Y  → 1.00
2Y  → 2.00
3Y  → 3.00
5Y  → 5.00
10Y → 10.00
```

The actual mapping table will be created from observed source maturities.

Unknown or unusual tenor labels should not be guessed.

---

# 16. Duplicate Handling

Potential duplicate records should be investigated before deletion.

A duplicate key may conceptually be:

```text
date + curve_type + tenor
```

If multiple values exist for the same key, the project must determine whether they represent:

```text
true duplicate
source revision
multiple publication times
parsing error
different instrument definition
```

Records should not simply be removed because a duplicate is inconvenient.

---

# 17. Missing Data

Missingness should be measured explicitly.

PakYield should distinguish:

```text
NA
zero
not applicable
source unavailable
non-reporting day
```

A missing yield must never automatically become:

```text
0.00%
```

Forward-filling yield data should not be the default.

Interpolation should be avoided in core empirical tests unless a specific method requires it and the generated observations are clearly identified.

---

# 18. Data-Quality Checks

Before analytical use, yield data should be checked for:

```text
invalid dates
duplicate keys
non-numeric yields
impossible maturity labels
missing yields
unexpected zeros
extreme values
date ordering
curve-type errors
unit inconsistencies
```

Extreme values are not automatically errors.

They must first be checked against the source.

---

# 19. Sample-Period Selection

The final sample period must be determined after Phase 2.

Candidate periods include approximately:

```text
2013–2026
2015–2026
2020–2026
```

The chosen sample should maximize useful history while maintaining sufficient:

```text
data reliability
definition consistency
maturity coverage
PKRV/PKISRV overlap
```

The longest possible sample is not necessarily the best sample.

---

# 20. Yield-Curve Construction

For date `t`, the observed yield curve consists of available maturity/yield pairs:

```text
(maturity_1, yield_1)
(maturity_2, yield_2)
...
(maturity_n, yield_n)
```

Observed curves should first be displayed using actual benchmark observations.

Interpolation or curve fitting must not be visually presented as if the fitted points were directly observed market benchmarks.

---

# 21. Yield-Curve Shape Measures

Subject to available maturities, PakYield may calculate:

```text
short-end yield
medium-term yield
long-end yield
term spreads
curve level
curve slope
curve curvature
```

Simple term spreads may include:

```text
10Y - 2Y
10Y - 1Y
5Y - 1Y
3Y - 3M
```

The final set must depend on historical coverage.

---

# 22. Term-Spread Formula

For long maturity `L` and short maturity `S`:

```text
term_spread_bps
=
(yield_L - yield_S) × 100
```

Example:

```text
10Y = 13.50%
2Y  = 14.25%
```

Then:

```text
10Y - 2Y = -75 bps
```

which indicates an inverted relationship for that selected pair.

---

# 23. Daily Yield Changes

For each curve and maturity:

```text
yield_change_bps_t
=
(yield_pct_t - yield_pct_t-1) × 100
```

The previous observation should normally mean the previous available market observation for that specific curve and tenor.

It should not blindly mean the previous calendar day.

---

# 24. Conventional/Islamic Matching

PKRV and PKISRV observations should be compared only when:

```text
date matches
maturity is comparable
both observations are available
definitions are sufficiently compatible
```

The merged dataset should preserve the original individual yields as well as the calculated spread.

---

# 25. PKISRV-PKRV Spread

For maturity `m` on date `t`:

```text
islamic_spread_bps
=
(PKISRV_m,t - PKRV_m,t) × 100
```

A positive value means PKISRV is numerically above PKRV.

A negative value means PKISRV is numerically below PKRV.

No economic cause is implied by the sign alone.

---

# 26. Conventional/Islamic Descriptive Analysis

The comparison should consider, where data permit:

```text
mean spread
median spread
standard deviation
minimum
maximum
interquartile range
rolling mean
rolling volatility
correlation
rolling correlation
```

Results should also be inspected maturity by maturity.

---

# 27. MPC Announcement-Window Design

The primary event-analysis component will examine yield movements around SBP MPC announcement dates.

Candidate observation windows are:

```text
[-1,+1]
[-3,+3]
[-5,+5]
```

The notation refers to available benchmark observations surrounding the event anchor.

It does not necessarily refer to calendar days.

---

# 28. Event Anchor

The provisional event anchor is:

```text
MPC announcement date
```

Phase 2 must verify:

```text
announcement timing
benchmark publication timing
weekends
holidays
missing observations
same-day usability
```

If announcements occur after the relevant yield observation for that day, the first usable post-announcement market observation may need to be treated as the effective post-event observation.

The convention must be applied consistently.

---

# 29. Event-Window Calculation

For a selected maturity and event window:

```text
event_window_change_bps
=
(yield_end - yield_start) × 100
```

The start and end observations must correspond to documented positions around the event.

The project should retain the underlying dates used in every event calculation.

---

# 30. Event-Level Data Structure

A processed event table may contain:

```text
event_id
announcement_date
decision_type
policy_rate_before
policy_rate_after
policy_rate_change_bps
curve_type
tenor
window
start_date
end_date
start_yield_pct
end_yield_pct
event_window_change_bps
```

This allows every aggregate result to be traced back to individual events.

---

# 31. Event Grouping

Events may be grouped by:

```text
HIKE
CUT
HOLD
```

Possible comparisons include:

```text
mean reaction
median reaction
reaction distribution
reaction by maturity
reaction by curve type
```

Sample sizes must be reported.

---

# 32. Event-Study Statistical Analysis

Where sample size permits, the study may calculate:

```text
count
mean
median
standard deviation
standard error
confidence interval
```

Potential group-comparison tests may be considered only after distributional properties and sample sizes are inspected.

The methodology should not automatically assume normality.

---

# 33. H1 Evaluation

H1 concerns relative maturity sensitivity around MPC announcements.

The preferred primary outcome is likely:

```text
absolute event-window yield change
```

because signed changes from hikes, cuts, and holds could cancel each other in an unconditional average.

Signed changes should still be reported separately.

H1 should be evaluated across multiple maturities rather than from one isolated event.

---

# 34. Causal Limitation of Event Analysis

The event window may contain information unrelated to monetary policy.

Therefore, unless additional identification is implemented:

```text
announcement-window reaction ≠ identified causal effect
```

The project will explicitly state this limitation.

---

# 35. Policy Surprise Limitation

The announced policy-rate change is not equivalent to the unexpected component of monetary policy.

Conceptually:

```text
announced policy change
=
expected component
+
unexpected component
```

PakYield does not initially observe this decomposition.

Therefore it will not call the full policy-rate change a monetary-policy surprise.

---

# 36. Policy-Regime Analysis

For H4, monetary-policy environments may eventually be categorized as:

```text
TIGHTENING
EASING
STABLE
```

The precise classification algorithm will be established after observing the policy-rate history.

Possible approaches include:

```text
direction of recent policy-rate changes
rolling cumulative rate change
intervals between policy turning points
```

The final algorithm must be deterministic and documented.

---

# 37. Macroeconomic Frequency Alignment

Yield observations may be daily while CPI is monthly.

The project will not create artificial statistical sample size by repeating the same monthly inflation value across every daily yield row and then treating each repeated value as independent information.

Instead, macroeconomic regressions will likely use an aligned lower-frequency dataset.

---

# 38. Monthly Yield Transformations

Candidate monthly yield measures include:

```text
month-end yield
monthly average yield
monthly yield change
```

The chosen transformation must match the research question.

For change-based regressions, one possible construction is:

```text
monthly_yield_change_bps
=
(month_end_yield_t - month_end_yield_t-1) × 100
```

---

# 39. Macroeconomic Regression Sequence

Before regression estimation, the project should:

```text
inspect plots
calculate descriptive statistics
inspect missingness
test relevant time-series properties
determine transformations
estimate model
inspect residual diagnostics
apply robust inference where justified
interpret economic magnitude
```

Model specification should follow the properties of the data.

---

# 40. Stationarity Analysis

Potential variables may exhibit persistence or trends.

PakYield may use the Augmented Dickey-Fuller test together with graphical inspection.

Possible responses to non-stationarity include:

```text
first differences
percentage changes
basis-point changes
alternative specification
```

Differencing should be theoretically meaningful rather than mechanical.

---

# 41. Provisional Regression Model

A provisional monthly model may resemble:

```text
ΔYield_m,t
=
α
+ β1 ΔPolicyRate_t
+ β2 Inflation_t
+ β3 ΔFX_t
+ ε_t
```

where:

```text
ΔYield_m,t
```

is a monthly change in the selected maturity yield.

This equation is provisional.

It must not be treated as final until data properties are observed.

---

# 42. Regression Interpretation

A regression coefficient represents a conditional statistical relationship under the model specification.

It does not automatically represent a causal effect.

The final paper should distinguish:

```text
statistical association
economic interpretation
causal interpretation
```

Only the first two are expected by default.

---

# 43. Regression Diagnostics

Where applicable, diagnostics should include:

```text
residual inspection
autocorrelation assessment
heteroskedasticity assessment
multicollinearity assessment
model-fit statistics
```

Possible tools include:

```text
Durbin-Watson
Ljung-Box
Breusch-Pagan
variance inflation factor
```

---

# 44. Robust Standard Errors

If regression residuals display heteroskedasticity or serial correlation, HAC/Newey-West standard errors may be used where methodologically appropriate.

The report should state when robust standard errors are used.

---

# 45. Statistical Significance

A conventional threshold such as:

```text
alpha = 0.05
```

may be used.

However, results should report more than binary significance.

Where appropriate, report:

```text
coefficient
standard error
p-value
confidence interval
effect magnitude
sample size
```

---

# 46. Economic Significance

A statistically significant movement can still be economically small.

Therefore PakYield should translate important yield effects into basis points whenever possible.

For example:

```text
coefficient = 0.15 percentage points
```

should also be understood as:

```text
15 basis points
```

when appropriate.

---

# 47. Correlation Analysis

PKRV/PKISRV analysis may use:

```text
Pearson correlation
Spearman correlation
rolling correlation
```

depending on the question and data characteristics.

Correlations may be calculated using both:

```text
yield levels
yield changes
```

because these answer different questions.

---

# 48. Multiple Comparisons

The project may evaluate multiple:

```text
maturities
windows
curves
regressions
```

This increases the chance of finding apparently significant results by chance.

The final report should clearly distinguish:

```text
primary tests
secondary analysis
exploratory findings
```

and should not selectively report only favorable results.

---

# 49. Nelson-Siegel Model

PakYield should attempt a Nelson-Siegel fit where sufficient maturity observations exist.

A common functional form is:

```text
y(τ)
=
β0
+
β1[(1 - exp(-τ/λ)) / (τ/λ)]
+
β2{[(1 - exp(-τ/λ)) / (τ/λ)] - exp(-τ/λ)}
```

where:

```text
τ  = maturity
β0 = long-run level factor
β1 = slope-related factor
β2 = curvature-related factor
λ  = decay parameter
```

Implementation details will be finalized during the modeling phase.

---

# 50. Nelson-Siegel Interpretation

Broadly:

```text
β0 → level
β1 → slope-related component
β2 → curvature-related component
```

These interpretations are approximate economic summaries rather than direct observed market quantities.

---

# 51. Nelson-Siegel Eligibility

A curve should not be fitted merely because an optimization algorithm can return parameters.

Dates with insufficient or poorly distributed maturity points should be excluded from model estimation.

The minimum maturity count and distribution requirement will be determined after real coverage is inspected.

---

# 52. Nelson-Siegel Fit Quality

Fit quality should include a measure such as:

```text
RMSE
```

between:

```text
observed benchmark yields
```

and:

```text
model-fitted yields
```

Poor-fit dates should be identifiable rather than hidden.

---

# 53. Fixed-Rate Bond Pricing

The risk engine will include a generic fixed-rate bullet bond.

For cash flows `CF_t` discounted at yield `y`:

```text
Price
=
Σ CF_t / (1 + y/f)^(f × t)
```

with frequency conventions implemented carefully.

This generic model is educational and analytical.

It should not be presented as a universal Sukuk-pricing model.

---

# 54. Macaulay Duration

Macaulay duration measures the weighted average time of discounted cash flows.

Conceptually:

```text
D_Mac
=
Σ[t × PV(CF_t)] / Price
```

with units in years when time is measured in years.

---

# 55. Modified Duration

Modified duration approximates percentage price sensitivity to yield changes.

For periodic compounding:

```text
D_Mod
=
D_Mac / (1 + y/f)
```

where `f` is payment frequency.

Exact implementation will depend on the calculator convention.

---

# 56. DV01

DV01 approximates the monetary price change for a one-basis-point yield movement.

Conceptually:

```text
DV01
≈
Modified Duration × Price × 0.0001
```

for a parallel one-basis-point change under the usual approximation.

---

# 57. Convexity

Convexity improves the approximation for larger yield changes.

Approximate price change:

```text
ΔP / P
≈
-D_Mod × Δy
+
0.5 × Convexity × (Δy)^2
```

The implementation should be tested numerically.

---

# 58. Risk Scenarios

The risk engine should support scenarios such as:

```text
-200 bps
-100 bps
-50 bps
0 bps
+50 bps
+100 bps
+200 bps
```

Potential later extensions may include:

```text
steepener
flattener
short-end shock
long-end shock
```

but these are secondary to the basic parallel-shock engine.

---

# 59. Sukuk Limitation

The generic fixed-rate bond calculator must include a visible limitation.

It does not automatically model:

```text
Ijara-specific cash-flow structures
floating-rate Sukuk
embedded options
asset-specific contractual features
liquidity differences
Shariah structuring details
```

Therefore it should be described as a generic fixed-income risk engine, not a complete Sukuk valuation system.

---

# 60. Reproducibility

Every major empirical output should ultimately be reproducible from:

```text
raw source data
+
documented cleaning rules
+
version-controlled Python/SQL code
```

Manual spreadsheet transformations should be minimized.

Where manual intervention is unavoidable, it must be documented.

---

# 61. Validation Philosophy

PakYield should validate analytical outputs using independent checks where practical.

Examples include:

```text
basis-point calculations checked manually
spread formulas independently reproduced
bond-price examples checked analytically
SQL aggregates compared with pandas aggregates
Nelson-Siegel fitted values checked against raw curves
```

---

# 62. Testing

Automated tests should eventually cover:

```text
yield conversions
basis-point changes
tenor parsing
term spreads
PKISRV-PKRV spreads
bond pricing
duration
DV01
convexity
event-window logic
```

Synthetic data may be used in software tests because these tests validate code behavior, not empirical findings.

---

# 63. Research Output Structure

Major empirical findings should preferably be presented as:

```text
Evidence
Interpretation
Limitation
```

This structure helps separate what the data show from what the researcher infers.

---

# 64. Unsupported Result Handling

If the data fail to support a hypothesis, PakYield should report that result.

The following are valid outcomes:

```text
SUPPORTED
PARTIALLY SUPPORTED
NOT SUPPORTED
INCONCLUSIVE
```

The project is not considered unsuccessful because a hypothesis is unsupported.

---

# 65. Exploratory Findings

Patterns discovered after inspecting the data may still be valuable.

They should be identified as:

```text
exploratory
```

rather than rewritten as if they had been pre-specified hypotheses.

---

# 66. Known Methodological Limitations

Expected limitations may include:

```text
limited historical PKISRV coverage
changing maturity availability
missing market observations
benchmark methodology changes
small number of MPC events
lack of direct market-expectations data
mixed-frequency macroeconomic data
potential confounding news around MPC dates
liquidity differences across instruments
observational rather than experimental research design
```

The final list must be updated using evidence from the real dataset.

---

# 67. Phase 2 Dependency

This methodology cannot be considered final until Phase 2 verifies the actual sources.

The following remain intentionally unresolved:

```text
final sample period
final tenor universe
final source URLs
final PKRV/PKISRV overlap
event-date alignment convention
policy-regime algorithm
FX inclusion
auction-data inclusion
monthly yield transformation
final regression specification
Nelson-Siegel eligibility threshold
```

Any substantive methodological revision after the feasibility audit must be recorded in `docs/DECISIONS.md`.

---

# 68. Core Interpretation Boundary

PakYield should maintain the following hierarchy:

```text
Observed value
↓
Descriptive statistic
↓
Statistical association
↓
Economic interpretation
↓
Causal inference
```

Confidence requirements increase as the analysis moves downward.

The project expects to operate mainly within:

```text
Observed value
Descriptive statistic
Statistical association
Economic interpretation
```

Causal inference requires additional identification that is not assumed in the current design.

---

# 69. Methodology Status

**Status:** PROVISIONAL

This methodology defines the intended analytical framework before real-data feasibility is known.

It should be frozen as the Phase 1 baseline and revised only when actual source characteristics provide a documented reason.
