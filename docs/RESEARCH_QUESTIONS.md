# PakYield Lab — Research Questions, Hypotheses & Variable Definitions

## 1. Purpose of This Document

This document freezes the principal research questions, hypotheses, analytical variables, and operational definitions for PakYield Lab before empirical analysis begins.

Its purpose is to reduce retrospective hypothesis changes, analytical drift, and overinterpretation after the data are observed.

The hypotheses contained here are propositions to investigate.

They are not claims about what the Pakistani sovereign fixed-income market actually does.

No hypothesis is considered supported, unsupported, or partially supported until the relevant empirical analysis has been completed.

---

# 2. Central Research Question

> **How does monetary policy transmit across Pakistan's sovereign yield curve, and how do conventional and Shariah-compliant sovereign benchmark rates behave across maturities and monetary-policy regimes?**

This question contains two related research themes:

**Theme A — Monetary-policy transmission**

How benchmark sovereign yields across the maturity structure behave around changes and announcements in the State Bank of Pakistan's monetary-policy stance.

**Theme B — Conventional and Islamic benchmark structure**

How PKRV and PKISRV benchmark rates compare across similar maturities and through time.

The word **transmit** is used broadly.

Unless an identification strategy permits stronger inference, observed yield movements should be described as:

* changes;
* reactions;
* associations;
* co-movements;
* announcement-window movements.

They should not automatically be described as causal effects.

---

# 3. Research Question 1 — Conventional Yield-Curve Evolution

## RQ1

> **How has Pakistan's conventional sovereign benchmark yield curve evolved across different monetary-policy environments?**

The analysis should examine how the level and shape of the PKRV curve change through time.

Potential features include:

* short-maturity yields;
* medium-maturity yields;
* long-maturity yields;
* long-short term spreads;
* steepening;
* flattening;
* inversion where observable;
* overall curve level;
* slope;
* curvature.

The final maturity pairs will depend on actual historical coverage discovered during Phase 2.

---

# 4. Hypothesis 1 — Maturity Sensitivity

## H1

> **Short-maturity sovereign benchmark yields may exhibit larger movements around MPC announcements than longer-maturity sovereign benchmark yields.**

### Economic Motivation

Shorter-term sovereign yields are generally more closely connected to the expected path of near-term monetary-policy conditions.

Longer-term yields may also reflect:

* inflation expectations;
* term premia;
* fiscal risk;
* liquidity conditions;
* longer-run growth expectations;
* market supply and demand.

Therefore, short and long maturities need not react equally around policy announcements.

### Important Restriction

H1 does not state that short yields **will** react more strongly.

It states that this is an empirical proposition to test.

### Candidate Comparison

Subject to available maturity coverage, potential comparisons may include:

```text
3M versus 10Y
6M versus 10Y
1Y versus 5Y
1Y versus 10Y
2Y versus 10Y
```

The final comparisons must be based on reliable overlapping data.

### Candidate Measurements

Possible measures include:

```text
absolute event-window yield change
signed event-window yield change
mean event-window yield change
median event-window yield change
distribution of event-window yield changes
```

### Possible Outcomes

H1 may eventually be classified as:

```text
SUPPORTED
PARTIALLY SUPPORTED
NOT SUPPORTED
INCONCLUSIVE
```

These classifications must be evidence-based.

---

# 5. Research Question 2 — MPC Announcement-Window Reactions

## RQ2

> **How do different maturity points on Pakistan's sovereign yield curve behave within defined observation windows around State Bank of Pakistan Monetary Policy Committee announcements?**

The research should compare yield behavior around individual MPC events.

Initial candidate windows:

```text
[-1,+1]
[-3,+3]
[-5,+5]
```

where the observations surrounding the event should use available market dates rather than naïvely assuming every calendar day is a trading or reporting day.

---

# 6. MPC Event Definition

Each qualifying MPC observation should eventually include, where obtainable:

```text
event_id
announcement_date
effective_date
policy_rate_before
policy_rate_after
policy_rate_change_bps
decision_type
source
source_url
notes
```

Decision type:

```text
HIKE
CUT
HOLD
```

A rate change in basis points should be calculated as:

```text
policy_rate_change_bps
=
(policy_rate_after - policy_rate_before) × 100
```

if policy rates are stored in percentage-point units.

Example:

```text
22.00% → 20.50%
```

corresponds to:

```text
-150 bps
```

and should be classified as:

```text
CUT
```

---

# 7. Event-Window Definition

If an event occurs at event date `t0`, candidate windows include:

```text
[-1,+1]
[-3,+3]
[-5,+5]
```

These represent observation positions around the MPC event.

The final methodology must specify precisely how observations are selected when:

* the announcement occurs after market publication;
* the announcement occurs on a non-reporting day;
* yield observations are missing;
* a public holiday interrupts the window;
* adjacent MPC events are unusually close;
* the required maturity is unavailable.

This convention will not be invented during Phase 1.

It will be finalized after the Phase 2 source audit.

---

# 8. Event-Window Yield Change

For maturity `m`, a simple event-window yield change may be defined as:

```text
Δy_m,w
=
y_m,end(w) - y_m,start(w)
```

If yields are stored in percentage points, the corresponding basis-point movement is:

```text
Δy_m,w,bps
=
(y_m,end(w) - y_m,start(w)) × 100
```

Example:

```text
15.25% → 14.95%
```

equals:

```text
-30 bps
```

---

# 9. Event-Study Interpretation Restriction

The PakYield event study is initially designed as an:

> **MPC announcement-window study**

It is not automatically a causal event study.

Without a defensible identification strategy, it cannot separate the MPC announcement from all other information arriving during the same period.

Potential confounding influences could include:

* inflation releases;
* exchange-rate movements;
* fiscal announcements;
* geopolitical events;
* market-liquidity changes;
* government borrowing developments;
* global interest-rate changes;
* other macroeconomic news.

Therefore preferred wording is:

> The 1-year PKRV yield declined by X basis points within the selected observation window around the MPC announcement.

Avoid:

> The MPC decision caused the 1-year yield to decline by X basis points.

---

# 10. Monetary-Policy Surprise Restriction

PakYield must not use terms such as:

```text
policy surprise
monetary-policy surprise
unexpected policy shock
```

unless a defensible expectations measure is incorporated.

A difference between the previous policy rate and the announced rate is a:

> **policy-rate change**

It is not automatically a:

> **policy surprise**

because market participants may already have expected the decision.

---

# 11. Research Question 3 — Conventional vs Shariah-Compliant Benchmarks

## RQ3

> **How closely do comparable PKRV and PKISRV maturity points move together, and how does the PKISRV-PKRV spread vary across maturity and time?**

This question studies similarities and differences between Pakistan's conventional and Shariah-compliant sovereign benchmark structures.

Analytical dimensions may include:

* level differences;
* basis-point spreads;
* correlations;
* rolling correlations;
* spread volatility;
* maturity differences;
* time variation;
* monetary-policy environments.

---

# 12. Hypothesis 2 — Conventional/Islamic Co-Movement

## H2

> **Comparable PKRV and PKISRV maturity points may exhibit strong positive co-movement.**

### Economic Motivation

Both benchmark structures are exposed to many common macro-financial influences, potentially including:

* monetary policy;
* sovereign funding conditions;
* inflation;
* liquidity;
* fiscal conditions;
* investor risk preferences;
* domestic interest-rate expectations.

Therefore substantial co-movement may exist.

### Candidate Measurements

Potential measures include:

```text
Pearson correlation
Spearman correlation
rolling correlation
yield-change correlation
level correlation
```

The appropriate measures will depend on:

* stationarity;
* data frequency;
* sample size;
* missingness;
* overlapping maturity coverage.

### Interpretation Restriction

Strong correlation does not prove:

* economic equivalence;
* identical pricing mechanisms;
* identical risk;
* identical liquidity;
* causation.

---

# 13. PKISRV-PKRV Spread

For maturity `m` on date `t`:

```text
islamic_spread_bps(m,t)
=
[PKISRV(m,t) - PKRV(m,t)] × 100
```

assuming both benchmark yields are stored in percentage-point units.

Example:

```text
PKISRV 5Y = 12.30%
PKRV 5Y   = 12.10%
```

Then:

```text
PKISRV - PKRV = +20 bps
```

A positive value means the PKISRV benchmark is numerically higher on that date and maturity.

It does not by itself explain **why**.

---

# 14. Hypothesis 3 — Spread Variation

## H3

> **The PKISRV-PKRV spread may vary meaningfully across maturity and through time rather than remaining constant.**

Potential dimensions include:

```text
maturity
year
policy regime
market volatility
liquidity conditions
inflation environment
```

### Candidate Analysis

Possible measures include:

```text
mean spread
median spread
standard deviation
interquartile range
minimum
maximum
rolling average
rolling volatility
```

### Interpretation Restriction

PakYield must not automatically label this spread as:

```text
Islamic premium
Sukuk premium
Islamic discount
Shariah premium
Shariah discount
```

unless later research provides a defensible economic definition and supporting evidence.

For the core analysis, preferred language is:

> **PKISRV-PKRV spread**

---

# 15. Research Question 4 — Macroeconomic Relationships

## RQ4

> **What statistical relationships exist between Pakistan's macroeconomic environment and movements across selected portions of the sovereign yield curve?**

Potential explanatory or contextual variables include:

```text
SBP policy rate
CPI inflation
PKR/USD exchange rate
selected yield-curve spreads
```

The exact model specification will depend on the observed properties of the data.

---

# 16. Hypothesis 4 — Yield-Curve Slope Across Policy Environments

## H4

> **Selected long-short yield spreads may display different distributions across tightening, easing, and stable-policy environments.**

Potential spreads may include, subject to data coverage:

```text
10Y - 1Y
10Y - 2Y
5Y - 1Y
3Y - 3M
```

The final spread selection must be based on:

* historical availability;
* maturity consistency;
* overlapping sample length;
* missingness.

---

# 17. Monetary-Policy Environment Classification

A preliminary policy-state framework is:

```text
TIGHTENING
EASING
STABLE
```

However, the precise operational rule is not yet frozen.

Possible approaches may include classification based on:

* recent policy-rate changes;
* cumulative changes over a trailing period;
* intervals between MPC turning points.

Phase 1 deliberately does not select a regime algorithm without first examining the actual policy-rate history.

The chosen rule must later be:

* explicit;
* reproducible;
* applied consistently.

---

# 18. Core Variable Dictionary

## 18.1 Date

Variable:

```text
date
```

Type:

```text
date
```

Meaning:

Date associated with the benchmark yield observation.

---

## 18.2 Curve Type

Variable:

```text
curve_type
```

Expected categories:

```text
PKRV
PKISRV
```

---

## 18.3 Tenor

Variable:

```text
tenor
```

Potential values:

```text
3M
6M
1Y
2Y
3Y
5Y
10Y
```

Additional maturities may be retained where supported by source data.

---

## 18.4 Maturity in Years

Variable:

```text
maturity_years
```

Examples:

```text
3M  = 0.25
6M  = 0.50
1Y  = 1.00
2Y  = 2.00
5Y  = 5.00
10Y = 10.00
```

This numeric representation will be useful for:

* plotting;
* curve fitting;
* interpolation;
* Nelson-Siegel estimation.

---

## 18.5 Benchmark Yield

Variable:

```text
yield_pct
```

Unit:

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

---

## 18.6 Daily Yield Change

Variable:

```text
yield_change_bps
```

Definition:

```text
(yield_pct_t - yield_pct_t-1) × 100
```

Unit:

```text
basis points
```

---

## 18.7 Policy Rate

Variable:

```text
policy_rate_pct
```

Unit:

```text
percentage points
```

---

## 18.8 Policy-Rate Change

Variable:

```text
policy_rate_change_bps
```

Unit:

```text
basis points
```

---

## 18.9 MPC Decision Type

Variable:

```text
decision_type
```

Categories:

```text
HIKE
CUT
HOLD
```

---

## 18.10 CPI Inflation

Provisional variable:

```text
cpi_inflation_yoy_pct
```

Expected interpretation:

Year-on-year CPI inflation rate in percentage points.

The exact CPI series must be confirmed during Phase 2.

---

## 18.11 Exchange Rate

Provisional variable:

```text
pkr_per_usd
```

Interpretation:

Pakistani rupees per US dollar.

An increase represents PKR depreciation against USD under this quotation convention.

FX remains optional until source feasibility is confirmed.

---

## 18.12 Term Spread

Generic variable:

```text
term_spread_bps
```

Example:

```text
10Y yield - 2Y yield
```

Unit:

```text
basis points
```

---

## 18.13 PKISRV-PKRV Spread

Variable:

```text
islamic_spread_bps
```

Definition:

```text
(PKISRV yield - PKRV yield) × 100
```

Unit:

```text
basis points
```

---

# 19. Dependent Variables

The project will not rely on only one dependent variable.

Different research questions require different outcomes.

Candidate dependent variables include:

## Event-Study Analysis

```text
event_window_yield_change_bps
```

---

## Time-Series Analysis

```text
yield_change_bps
```

for selected maturities.

---

## Conventional/Islamic Analysis

```text
islamic_spread_bps
```

and potentially:

```text
change_in_islamic_spread_bps
```

---

## Curve-Shape Analysis

Potential outcomes:

```text
term_spread_bps
Nelson-Siegel beta0
Nelson-Siegel beta1
Nelson-Siegel beta2
```

if successfully estimated.

---

# 20. Explanatory and Context Variables

Potential variables include:

```text
policy_rate_change_bps
policy_rate_pct
cpi_inflation_yoy_pct
exchange_rate_change
decision_type
policy_environment
calendar controls
```

These are provisional until data feasibility and statistical properties are examined.

---

# 21. Frequency Alignment

PakYield may contain variables observed at different frequencies.

Examples:

```text
benchmark yields → daily or available market observations
MPC decisions    → event dates
policy rate      → step-function/event history
CPI inflation    → monthly
FX               → daily or monthly
```

Different frequencies must not be merged carelessly.

For monthly regressions, daily yields may need to be transformed into a documented monthly measure such as:

```text
month-end
monthly mean
monthly change
```

The selected convention must be theoretically and statistically justified.

---

# 22. Missing Data Rule

PakYield should distinguish among:

```text
true zero
missing observation
not applicable
source unavailable
```

Missing yields must not automatically be replaced with zero.

Interpolation must not be used invisibly.

If interpolation is ever appropriate, the project must document:

* why;
* where;
* how;
* which observations were generated;
* how conclusions change without interpolation.

---

# 23. Outlier Rule

An unusual market observation is not automatically a data error.

Before deleting an extreme value, PakYield should determine whether it is:

```text
source error
parsing error
duplicate
unit error
legitimate market movement
```

Legitimate extreme market movements should normally remain in the research dataset.

---

# 24. Correlation Rule

Correlation describes statistical association.

It does not demonstrate causation.

If:

```text
corr(PKRV, PKISRV) = high
```

the correct interpretation is broadly:

> PKRV and PKISRV displayed strong statistical co-movement during the measured sample.

Not:

> PKRV determines PKISRV.

---

# 25. Regression Rule

Regression coefficients will be interpreted within the assumptions and limitations of the estimated model.

PakYield must report, where appropriate:

```text
coefficient
standard error
test statistic
p-value
confidence interval
sample size
R-squared
diagnostic results
```

Statistical significance alone must not be treated as economic importance.

---

# 26. Statistical Significance

A conventional threshold such as:

```text
α = 0.05
```

may be used where appropriate.

However:

```text
p < 0.05
```

does not automatically imply:

```text
large economic effect
causal relationship
useful prediction
important financial consequence
```

Effect size and economic interpretation must also be considered.

---

# 27. Stationarity

Time-series regressions involving yield levels or macroeconomic variables may require stationarity assessment.

Potential procedures include:

```text
visual inspection
Augmented Dickey-Fuller test
differencing where justified
```

The project should avoid mechanically regressing unrelated non-stationary level series.

---

# 28. Autocorrelation and Heteroskedasticity

Financial and macroeconomic time-series residuals may violate classical OLS assumptions.

Diagnostics may include:

```text
residual plots
Durbin-Watson
Ljung-Box
Breusch-Pagan
```

Where justified, the project may use:

```text
HAC/Newey-West standard errors
```

The choice must be reported rather than silently applied.

---

# 29. Multicollinearity

Candidate regression variables may be correlated with each other.

Where appropriate, PakYield may inspect:

```text
correlation matrices
variance inflation factors
```

Models should prioritize interpretability over unnecessary variable accumulation.

---

# 30. Multiple Testing

If many maturities, windows, and statistical tests are evaluated, the project must recognize the possibility of false-positive findings.

The final paper should distinguish:

* primary hypotheses;
* secondary analysis;
* exploratory analysis.

Results should not be selectively highlighted merely because they cross a significance threshold.

---

# 31. Evidence Classification Framework

For final reporting, major claims should use the following structure.

## Evidence

What the measured data or statistical result directly shows.

## Interpretation

What the researcher believes the result may indicate economically.

## Limitation

Why the result should not be interpreted more strongly.

Example:

**Evidence:**
The 1-year PKRV yield moved by -35 bps within the selected [-3,+3] observation window.

**Interpretation:**
The short end of the conventional benchmark curve moved materially around this MPC event.

**Limitation:**
The design does not establish that the MPC announcement alone caused the movement.

---

# 32. Hypothesis Outcome Framework

Each hypothesis may ultimately receive one of four research-status descriptions:

```text
SUPPORTED
PARTIALLY SUPPORTED
NOT SUPPORTED
INCONCLUSIVE
```

These labels are not statistical tests by themselves.

They are summary descriptions based on the total evidence.

A hypothesis should not be labeled supported solely because one selected regression coefficient has a p-value below 0.05.

---

# 33. Exploratory vs Confirmatory Analysis

The four principal hypotheses constitute the project's primary pre-analysis hypotheses.

Additional patterns discovered after viewing the data should be clearly described as:

> exploratory findings

where appropriate.

This distinction reduces the risk of presenting post-hoc observations as if they had been predicted beforehand.

---

# 34. Data Feasibility Dependency

The research questions are fixed conceptually, but exact implementation remains dependent on the Phase 2 data audit.

Phase 2 may legitimately alter:

```text
sample start date
sample end date
tenor set
PKRV/PKISRV overlap period
event windows
optional variables
specific term spreads
regression frequency
```

if supported by documented source limitations.

Such changes should be recorded in `docs/DECISIONS.md`.

---

# 35. Primary Research Questions Summary

```text
RQ1:
How has Pakistan's conventional sovereign benchmark yield curve evolved across different monetary-policy environments?

RQ2:
How do different maturity points behave within defined windows around SBP MPC announcements?

RQ3:
How closely do comparable PKRV and PKISRV maturities move together, and how does the PKISRV-PKRV spread vary across maturity and time?

RQ4:
What statistical relationships exist between Pakistan's macroeconomic environment and movements across selected portions of the sovereign yield curve?
```

---

# 36. Primary Hypotheses Summary

```text
H1:
Short-maturity sovereign benchmark yields may exhibit larger MPC announcement-window movements than longer-maturity yields.

H2:
Comparable PKRV and PKISRV maturity points may exhibit strong positive co-movement.

H3:
The PKISRV-PKRV spread may vary meaningfully across maturity and through time.

H4:
Selected long-short yield spreads may display different distributions across tightening, easing, and stable-policy environments.
```

---

# 37. Research Integrity Statement

PakYield Lab will report what the evidence shows even when the results are:

* statistically insignificant;
* economically small;
* inconsistent with initial hypotheses;
* mixed across maturities;
* difficult to interpret.

The objective is not to prove H1–H4.

The objective is to test them transparently.
