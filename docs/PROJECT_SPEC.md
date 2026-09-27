# PakYield Lab — Project Specification

## 1. Project Identity

**Project Name:** PakYield Lab

**Product Description:**
Pakistan Sovereign Fixed-Income & Monetary Policy Research Platform

**Research Subtitle:**
An Empirical Study of Pakistan's Conventional and Shariah-Compliant Sovereign Yield Curves

---

# 2. Project Purpose

PakYield Lab is an undergraduate financial-market research project designed to combine:

* Pakistani sovereign fixed-income data;
* monetary-policy analysis;
* conventional and Islamic benchmark yield curves;
* financial mathematics;
* econometrics;
* data engineering;
* SQL;
* Python;
* interactive visualization;
* reproducible research;
* academic writing.

The project is intentionally designed as a financial research platform rather than a conventional business-intelligence dashboard.

The finished system should allow a user to investigate:

* the shape of Pakistan's sovereign benchmark yield curve;
* historical changes across different maturities;
* conventional versus Shariah-compliant benchmark structures;
* movements around State Bank of Pakistan Monetary Policy Committee announcements;
* relationships between yields and selected macroeconomic variables;
* fixed-income interest-rate risk;
* fitted yield-curve factors.

---

# 3. Central Research Question

The central research question is:

> **How does monetary policy transmit across Pakistan's sovereign yield curve, and how do conventional and Shariah-compliant sovereign benchmark rates behave across maturities and monetary-policy regimes?**

The term **transmit** is used here in a broad financial-market sense.

The project must not automatically interpret observed yield movements as causal effects of monetary policy.

Where the methodology does not identify causality, the research should instead describe:

* co-movement;
* association;
* announcement-window reaction;
* yield change;
* statistical relationship.

---

# 4. Core Research Questions

## RQ1 — Conventional Yield-Curve Evolution

How has the shape of Pakistan's conventional sovereign benchmark yield curve evolved through different monetary-policy environments?

This question will consider, subject to actual tenor availability:

* yield levels;
* short-, medium-, and long-maturity rates;
* term spreads;
* steepening;
* flattening;
* inversion across selected maturity pairs;
* changes through time.

---

## RQ2 — MPC Announcement-Window Reactions

How do different maturity points on Pakistan's sovereign yield curve behave within defined windows around State Bank of Pakistan Monetary Policy Committee announcements?

The main event windows are expected to include:

* [-1,+1]
* [-3,+3]
* [-5,+5]

These windows should use available market observations rather than naïve calendar days where appropriate.

The study measures movements around announcements.

It does not automatically identify:

* policy surprises;
* pure monetary-policy shocks;
* causal effects.

---

## RQ3 — Conventional vs Shariah-Compliant Benchmark Rates

How closely do comparable PKRV and PKISRV maturity points move together, and how does the PKISRV-PKRV spread vary across maturity and time?

The analysis may include:

* contemporaneous spreads;
* average spreads;
* spread distributions;
* spread volatility;
* rolling correlations;
* changes through time;
* differences across monetary-policy environments.

The project must not automatically interpret a positive or negative spread as a structural Islamic premium or discount.

---

## RQ4 — Macroeconomic Relationships

What statistical relationships exist between Pakistan's macroeconomic environment and movements across different portions of the sovereign yield curve?

Potential contextual variables include:

* SBP policy rate;
* CPI inflation;
* PKR/USD exchange rate if reliable data are available;
* selected term spreads.

The final econometric specification will be determined only after data coverage, frequency, stationarity, and statistical suitability are investigated.

---

# 5. Initial Research Hypotheses

These are hypotheses to test, not conclusions.

## H1 — Maturity Sensitivity

Short-maturity sovereign benchmark yields may exhibit larger announcement-window movements than longer-maturity yields.

Possible outcome:

* supported;
* partially supported;
* unsupported.

The data will determine the result.

---

## H2 — Conventional/Islamic Co-Movement

Comparable PKRV and PKISRV maturity points may display strong positive co-movement.

The analysis may evaluate:

* unconditional correlations;
* rolling correlations;
* maturity-specific relationships.

A high correlation does not prove the two structures are economically identical.

---

## H3 — Spread Variation

The PKISRV-PKRV spread may vary across:

* maturity;
* year;
* monetary-policy environment;
* periods of market volatility.

The project will not assume that the spread is constant.

---

## H4 — Yield-Curve Slope

The distribution of selected long-short yield spreads may differ across periods characterized by:

* tightening;
* easing;
* stable policy rates.

The exact regime definition will be documented before formal comparison.

---

# 6. Unit of Analysis

Different modules require different units of analysis.

## Daily Yield-Curve Analysis

Unit:

> date × curve × tenor

Example conceptual record:

```text
2025-01-15 | PKRV | 5Y | observed benchmark yield
```

---

## MPC Event Study

Unit:

> MPC event × curve × tenor × event window

Example conceptual record:

```text
MPC event | PKRV | 1Y | [-3,+3] | yield reaction in bps
```

---

## Monthly Macroeconomic Analysis

Unit:

> month × selected yield measure

Monthly macroeconomic variables should not be mechanically duplicated across daily observations and treated as independent daily data.

---

# 7. Main Analytical Variables

## Yield Level

Working unit:

> percentage points

Example:

```text
12.50
```

represents:

```text
12.50%
```

not:

```text
0.125%
```

This convention must be documented in the final data dictionary.

---

## Yield Change

If yields are stored in percentage-point units:

```text
yield_change_bps
=
(yield_t - yield_t-1) × 100
```

Example:

```text
12.00% → 12.20%
```

equals:

```text
+20 basis points
```

---

## Term Spread

Potential examples, subject to real tenor coverage:

```text
10Y - 1Y
10Y - 2Y
5Y - 1Y
3Y - 3M
```

A term spread must not be calculated when one of the required maturities is unavailable or unreliable.

---

## Islamic-Conventional Spread

Primary definition:

```text
PKISRV - PKRV
```

at a comparable date and maturity.

Reported primarily in basis points.

---

## Policy-Rate Change

Measured in basis points.

Decision classification:

```text
HIKE
CUT
HOLD
```

---

# 8. Working Dataset Scope

## Mandatory Candidates

The project should attempt to obtain:

1. PKRV historical benchmark yields
2. PKISRV historical benchmark yields
3. SBP MPC event dates
4. SBP policy-rate history
5. Pakistan CPI/inflation series

---

## Optional Candidates

The following will be included only if the Phase 2 feasibility audit finds them reliable and practically obtainable:

* PKR/USD;
* MTB auction results;
* PIB auction results;
* government Ijara Sukuk auction information;
* government-security trading information.

Optional datasets must not delay or destabilize the core project.

---

# 9. Sample Period

The sample period is deliberately not finalized during Phase 1.

Candidate ranges for investigation include:

```text
2013–2026
2015–2026
2020–2026
```

The final sample period must be selected using:

* confirmed data availability;
* consistent definitions;
* reliable maturity coverage;
* PKRV/PKISRV overlap;
* missingness;
* format consistency;
* source accessibility.

A longer sample is not automatically better than a shorter but more reliable sample.

---

# 10. Tenor Universe

The final tenor universe is also deliberately unresolved.

Potential maturities may include:

```text
3M
6M
1Y
2Y
3Y
5Y
10Y
```

and others where consistently available.

No maturity becomes part of the official core set until Phase 2 verifies its historical coverage.

---

# 11. Monetary-Policy Event Study

The event study is a central analytical component.

Initial windows:

```text
[-1,+1]
[-3,+3]
[-5,+5]
```

The exact event-anchor convention will be documented after SBP announcement timing and market-data availability are verified.

For each eligible event, analysis may calculate:

* pre/post yield difference;
* cumulative available-observation movement;
* maturity-specific reaction;
* curve-specific reaction.

Aggregate statistics may include:

* count;
* mean;
* median;
* standard deviation;
* confidence interval.

Events may be grouped into:

```text
HIKE
CUT
HOLD
```

---

# 12. Econometric Scope

The project should include real econometric analysis but should not add complexity merely for appearance.

Planned areas include:

* descriptive statistics;
* correlation;
* stationarity testing;
* Augmented Dickey-Fuller tests;
* regression;
* HAC/Newey-West standard errors where appropriate;
* residual diagnostics;
* heteroskedasticity testing;
* autocorrelation assessment;
* multicollinearity checks;
* event-group comparison.

A provisional monthly specification may resemble:

```text
ΔYield_m,t
=
α
+ β1 ΔPolicyRate_t
+ β2 Inflation_t
+ β3 ΔFX_t
+ ε_t
```

This equation is not yet authoritative.

It may change based on:

* actual data frequency;
* stationarity;
* missingness;
* variable definition;
* statistical defensibility.

---

# 13. Nelson-Siegel Scope

The final research-quality version should attempt to estimate a Nelson-Siegel yield curve.

Broad factor interpretations:

* beta0 ≈ level;
* beta1 ≈ slope;
* beta2 ≈ curvature.

The model should not be estimated on dates with inadequate maturity coverage.

The minimum number of usable maturities will be determined after the data-feasibility audit.

Model evaluation should include fit error such as RMSE.

---

# 14. Fixed-Income Risk Scope

PakYield will include a generic fixed-rate bullet-bond calculator.

Expected outputs:

* price;
* Macaulay duration;
* modified duration;
* DV01;
* convexity;
* shocked price.

Expected scenarios:

```text
-200 bps
-100 bps
-50 bps
0 bps
+50 bps
+100 bps
+200 bps
```

The project must state clearly that the generic fixed-rate bond model does not automatically represent every Sukuk structure or floating-rate security.

---

# 15. Research Integrity Rules

The following rules are mandatory.

## Rule 1 — Real Data

The empirical analysis must use real source data.

Synthetic observations may be used only for:

* unit tests;
* integration tests;
* controlled demonstrations explicitly labeled synthetic.

---

## Rule 2 — No Manufactured Findings

Results will never be changed, filtered, selected, or worded merely to make hypotheses appear successful.

Null or statistically weak results remain valid research results.

---

## Rule 3 — Causal Language

Unless a methodology genuinely identifies causality, do not write:

> SBP caused yields to move.

Prefer:

> Yields changed by X basis points within the selected MPC announcement window.

---

## Rule 4 — Monetary-Policy Surprise

Do not use the phrase:

> monetary-policy surprise

unless the project obtains and correctly uses a defensible measure of market expectations.

---

## Rule 5 — Prediction

Do not describe the project as a forecasting model unless a genuine predictive methodology and out-of-sample evaluation are implemented.

---

## Rule 6 — Investment Advice

PakYield must not produce:

* buy recommendations;
* sell recommendations;
* target prices;
* guaranteed forecasts;
* portfolio recommendations presented as financial advice.

---

# 16. Interpretation Framework

For important results, the final project should distinguish:

## Evidence

What the calculation actually shows.

## Interpretation

What the result may plausibly suggest.

## Limitation

What cannot be concluded from the result.

This structure should appear in both the application and research paper where appropriate.

---

# 17. Core Technical Scope

The final platform is expected to demonstrate:

* Python;
* pandas;
* NumPy;
* SciPy;
* statsmodels;
* SQL;
* SQLite;
* Streamlit;
* Plotly;
* Jupyter;
* pytest;
* Git;
* GitHub;
* reproducible data engineering.

Technology is used to support the financial research question, not as an end in itself.

---

# 18. Explicitly Excluded Features

PakYield v1.0 does not require:

* authentication;
* user accounts;
* brokerage integration;
* live trading;
* crypto;
* blockchain;
* LSTM models;
* XGBoost prediction;
* AI chatbot;
* payments;
* social network;
* React frontend;
* mobile application;
* cloud microservices.

Any later feature addition requires a documented research or engineering justification.

---

# 19. Planned Final Outputs

PakYield should ultimately produce:

1. reproducible Python/SQL research pipeline;
2. validated SQLite analytical database;
3. Jupyter research notebooks;
4. yield-curve analytics engine;
5. MPC announcement-window study;
6. PKRV/PKISRV comparative analysis;
7. econometric analysis;
8. fixed-income risk engine;
9. Nelson-Siegel implementation;
10. deployed Streamlit application;
11. academic-style research paper;
12. two-page research brief;
13. professional GitHub repository;
14. LinkedIn launch materials;
15. CV/project-description material;
16. scholarship/SOP/interview material.

---

# 20. Definition of Project Success

PakYield will not be judged primarily by the number of features.

The priority order is:

1. correctness;
2. research credibility;
3. real data;
4. reproducibility;
5. financial reasoning;
6. statistical discipline;
7. testing;
8. clarity;
9. professional presentation.

A smaller analysis performed correctly is preferable to a larger project built on weak assumptions.

---

# 21. Phase 1 Status

This specification defines the project before real-data feasibility is known.

Therefore the following remain unresolved by design:

* final sample period;
* final tenor universe;
* exact source-file formats;
* final FX inclusion;
* final auction-data inclusion;
* exact macro regression equation;
* exact event-anchor convention;
* exact Nelson-Siegel minimum maturity requirement.

These items must be resolved later using real evidence rather than guesswork.
