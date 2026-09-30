# PakYield Lab — Decision Ledger

## 1. Purpose

This document records significant research, engineering, data, and scope decisions made during the PakYield Lab project.

Its purpose is to preserve the reasoning behind decisions so that future changes are deliberate, traceable, and reproducible.

A decision should be recorded here when it materially affects:

* research design;
* interpretation;
* data coverage;
* architecture;
* analytical methodology;
* project scope;
* reproducibility;
* deployment;
* project credibility.

This file is not intended to record every minor formatting choice or routine coding detail.

---

# 2. Decision Status Vocabulary

The following statuses may be used:

```text
ACCEPTED
PROVISIONAL
DEFERRED
REJECTED
SUPERSEDED
```

Definitions:

```text
ACCEPTED
The decision is currently binding.

PROVISIONAL
The decision is the current working choice but may change after additional evidence.

DEFERRED
The decision cannot yet be made responsibly.

REJECTED
The option was considered and deliberately not selected.

SUPERSEDED
A previous decision has been replaced by a newer documented decision.
```

---

# 3. D001 — Project Positioning

**Status:** ACCEPTED

**Decision:**
PakYield Lab will be positioned as a sovereign fixed-income and monetary-policy research platform rather than a generic business-intelligence dashboard.

**Reasoning:**
The project's primary objective is financial research, empirical analysis, fixed-income modeling, econometrics, and reproducibility.

Visualization supports the research but is not the sole product.

**Implication:**
Feature decisions should prioritize research credibility over dashboard complexity.

---

# 4. D002 — Primary Research Market

**Status:** ACCEPTED

**Decision:**
The project will focus primarily on Pakistan's sovereign fixed-income market.

**Reasoning:**
The intended research contribution is specifically centered on Pakistani:

* sovereign benchmark yields;
* monetary policy;
* conventional fixed-income benchmarks;
* Shariah-compliant sovereign benchmarks.

**Implication:**
International data may be used only when it helps contextualize Pakistan-specific analysis.

---

# 5. D003 — Conventional Benchmark Series

**Status:** PROVISIONAL

**Decision:**
PKRV will serve as the principal conventional sovereign benchmark curve if the Phase 2 feasibility audit confirms adequate historical quality and coverage.

**Reasoning:**
PKRV is the intended benchmark series for conventional sovereign yield-curve analysis.

**Dependency:**
Phase 2 source validation.

---

# 6. D004 — Shariah-Compliant Benchmark Series

**Status:** PROVISIONAL

**Decision:**
PKISRV will serve as the principal Shariah-compliant sovereign benchmark curve if the Phase 2 feasibility audit confirms adequate historical quality and coverage.

**Reasoning:**
The project requires a comparable Islamic benchmark structure for analysis against PKRV.

**Dependency:**
Phase 2 source validation.

---

# 7. D005 — Final Sample Period

**Status:** DEFERRED

**Decision:**
Do not choose the final sample period during Phase 1.

Candidate ranges may include approximately:

```text
2013–2026
2015–2026
2020–2026
```

**Reasoning:**
The sample should be determined by actual data quality rather than aesthetic preference.

Factors to inspect include:

```text
source availability
historical consistency
missing observations
PKRV maturity coverage
PKISRV maturity coverage
PKRV/PKISRV overlap
benchmark-definition stability
```

**Implication:**
A shorter reliable dataset is preferable to a longer unreliable dataset.

---

# 8. D006 — Final Tenor Universe

**Status:** DEFERRED

**Decision:**
Do not pre-commit to an exact set of maturities.

**Reasoning:**
Historical benchmark maturity availability may differ over time.

**Implication:**
The Phase 2 audit will determine which tenors qualify for:

* core yield-curve analysis;
* term-spread analysis;
* event studies;
* PKRV/PKISRV comparison;
* Nelson-Siegel fitting.

---

# 9. D007 — Central Research Question

**Status:** ACCEPTED

**Decision:**
The Phase 1 central research question is:

> How does monetary policy transmit across Pakistan's sovereign yield curve, and how do conventional and Shariah-compliant sovereign benchmark rates behave across maturities and monetary-policy regimes?

**Interpretation Restriction:**
The word "transmit" is not itself a claim of identified causality.

Empirical conclusions must match the strength of the actual research design.

---

# 10. D008 — Principal Research Questions

**Status:** ACCEPTED

**Decision:**
PakYield will organize its empirical analysis around four principal research questions:

```text
RQ1 — Conventional yield-curve evolution

RQ2 — MPC announcement-window reactions

RQ3 — PKRV versus PKISRV co-movement and spread behavior

RQ4 — Macroeconomic relationships with selected yield measures
```

**Reasoning:**
These questions collectively cover the project's main fixed-income, monetary-policy, Islamic-finance, and econometric objectives without expanding into unrelated topics.

---

# 11. D009 — Principal Hypotheses

**Status:** ACCEPTED

**Decision:**
The project will begin empirical work with four pre-specified hypotheses:

```text
H1
Short-maturity benchmark yields may exhibit larger MPC announcement-window movements than longer-maturity yields.

H2
Comparable PKRV and PKISRV maturity points may exhibit strong positive co-movement.

H3
The PKISRV-PKRV spread may vary meaningfully across maturity and through time.

H4
Selected long-short yield spreads may display different distributions across tightening, easing, and stable-policy environments.
```

**Research Integrity Rule:**
The hypotheses must not be rewritten later merely because empirical results differ from initial expectations.

---

# 12. D010 — Unsupported Hypotheses

**Status:** ACCEPTED

**Decision:**
An unsupported hypothesis is a valid project result.

Possible summary outcomes are:

```text
SUPPORTED
PARTIALLY SUPPORTED
NOT SUPPORTED
INCONCLUSIVE
```

**Reasoning:**
The objective is to investigate the market honestly, not to engineer confirmation of the original hypotheses.

---

# 13. D011 — Empirical Data Requirement

**Status:** ACCEPTED

**Decision:**
The core research findings must use real-world empirical data.

**Allowed Synthetic Data:**
Synthetic observations may be used only for controlled software testing.

Examples include:

```text
unit tests
integration tests
edge-case tests
financial-math validation
```

**Prohibited Use:**
Synthetic observations must not be blended into the empirical market dataset or represented as actual Pakistani market observations.

---

# 14. D012 — Raw-Data Preservation

**Status:** ACCEPTED

**Decision:**
Raw source files should be retained unchanged wherever practical.

The intended architecture is:

```text
data/raw
↓
data/interim
↓
data/processed
↓
SQLite
↓
analysis
```

**Reasoning:**
This supports traceability, reproducibility, and error investigation.

---

# 15. D013 — Source Hierarchy

**Status:** ACCEPTED

**Decision:**
Official and authoritative sources should be preferred over secondary aggregators.

Priority should broadly follow:

```text
official government source
official central-bank source
official market/industry benchmark publisher
official downloadable publication
reputable secondary source
documented manual reconstruction
```

**Reasoning:**
Ease of downloading should not override source reliability.

---

# 16. D014 — Monetary-Policy Event Anchor

**Status:** PROVISIONAL

**Decision:**
The MPC announcement date will be the provisional event anchor.

**Reasoning:**
The research question concerns market movement around monetary-policy announcements.

**Dependency:**
Phase 2 must investigate announcement timing relative to benchmark observation/publication timing.

The effective analytical anchor may need refinement if same-day benchmark observations precede the actual policy announcement.

---

# 17. D015 — Event Windows

**Status:** PROVISIONAL

**Decision:**
Initial candidate event windows are:

```text
[-1,+1]
[-3,+3]
[-5,+5]
```

**Important Definition:**
These are intended to represent available market-observation positions, not automatically calendar days.

**Dependency:**
Phase 2 will verify data frequency, weekends, holidays, missing observations, and announcement timing.

---

# 18. D016 — Event-Study Interpretation

**Status:** ACCEPTED

**Decision:**
The initial MPC analysis will be described as an:

> MPC announcement-window study

rather than as a causal monetary-policy shock study.

**Reasoning:**
Observed yield movements around announcements may also reflect other information arriving during the same period.

**Approved Style:**

> The 1-year benchmark yield moved by X basis points within the selected window around the MPC announcement.

**Avoid:**

> The MPC decision caused the yield to move by X basis points.

unless a later methodology genuinely establishes causal identification.

---

# 19. D017 — Monetary-Policy Surprise Terminology

**Status:** ACCEPTED

**Decision:**
Do not call the policy-rate change a:

```text
monetary-policy surprise
policy surprise
unexpected policy shock
```

unless market expectations are explicitly measured using a defensible expectations dataset.

**Reasoning:**
An announced rate change contains both anticipated and potentially unanticipated components.

---

# 20. D018 — PKISRV-PKRV Spread Definition

**Status:** ACCEPTED

**Decision:**
For comparable maturity `m` and date `t`:

```text
islamic_spread_bps
=
(PKISRV_m,t - PKRV_m,t) × 100
```

assuming yields are stored in percentage-point units.

**Preferred Name:**

```text
PKISRV-PKRV spread
```

**Reasoning:**
This name describes exactly what was calculated without claiming an economic cause.

---

# 21. D019 — Islamic Premium/Discount Terminology

**Status:** ACCEPTED

**Decision:**
Do not automatically describe the PKISRV-PKRV spread as:

```text
Islamic premium
Sukuk premium
Shariah premium
Islamic discount
Sukuk discount
```

**Reasoning:**
A numerical spread alone does not establish its economic source.

Potential differences could reflect:

```text
liquidity
instrument structure
market segmentation
supply and demand
maturity differences
benchmark methodology
investor composition
other market factors
```

Any stronger terminology requires supporting evidence.

---

# 22. D020 — Yield Storage Unit

**Status:** ACCEPTED

**Decision:**
Benchmark yield values will be stored in percentage-point units.

Example:

```text
12.50
```

means:

```text
12.50%
```

**Reasoning:**
This representation is human-readable and closely matches financial-market source conventions.

Mathematical functions may convert these values to decimals internally where necessary.

---

# 23. D021 — Basis-Point Conversion

**Status:** ACCEPTED

**Decision:**

```text
basis_point_change
=
(new_yield_pct - old_yield_pct) × 100
```

Example:

```text
12.00% → 12.25%
=
+25 bps
```

**Reasoning:**
Basis points are the appropriate reporting unit for changes and spreads in fixed-income yields.

---

# 24. D022 — Yield Data Structure

**Status:** PROVISIONAL

**Decision:**
The canonical analytical yield table should use long-form storage.

Expected conceptual fields:

```text
date
curve_type
tenor
maturity_years
yield_pct
source
```

**Reasoning:**
Long-form data supports filtering, aggregation, curve construction, joins, validation, and future maturity additions more naturally than a permanently wide schema.

Wide-form views may still be generated when analytically useful.

---

# 25. D023 — Missing Yield Values

**Status:** ACCEPTED

**Decision:**
Missing yield observations must not automatically be replaced with zero.

**Reasoning:**
A zero yield is an economic value and is not equivalent to missing information.

PakYield should distinguish:

```text
missing
not applicable
non-reporting date
source unavailable
actual zero
```

where possible.

---

# 26. D024 — Interpolation

**Status:** ACCEPTED

**Decision:**
Interpolation will not be used invisibly in core empirical analysis.

**Reasoning:**
Generated observations must not be confused with directly observed benchmark yields.

If interpolation is later used for a specific modeling requirement, it must be documented and identifiable.

---

# 27. D025 — Extreme Observations

**Status:** ACCEPTED

**Decision:**
Extreme financial-market observations will not be automatically deleted as outliers.

**Reasoning:**
Large rate movements may represent genuine market behavior.

Before exclusion, investigate whether an observation reflects:

```text
source error
parsing error
unit error
duplicate
legitimate market movement
```

---

# 28. D026 — Mixed-Frequency Data

**Status:** ACCEPTED

**Decision:**
Monthly macroeconomic observations must not be mechanically repeated across daily yield observations and treated as independent daily observations in regression analysis.

**Reasoning:**
Such repetition would create artificial sample size and inappropriate statistical inference.

**Implication:**
Macroeconomic regression analysis will likely use an explicitly aligned lower-frequency dataset.

---

# 29. D027 — Final Macroeconomic Regression

**Status:** DEFERRED

**Decision:**
Do not freeze the final regression equation before inspecting the real data.

A provisional model may resemble:

```text
ΔYield_m,t
=
α
+ β1 ΔPolicyRate_t
+ β2 Inflation_t
+ β3 ΔFX_t
+ ε_t
```

**Reasoning:**
The appropriate specification depends on:

```text
data frequency
stationarity
missingness
sample length
multicollinearity
source availability
statistical diagnostics
```

---

# 30. D028 — Causality in Regression

**Status:** ACCEPTED

**Decision:**
Regression coefficients will not automatically be described as causal effects.

**Reasoning:**
The initial project design is observational and lacks a default causal identification strategy.

Preferred terminology includes:

```text
association
relationship
conditional relationship
co-movement
```

---

# 31. D029 — Statistical and Economic Significance

**Status:** ACCEPTED

**Decision:**
Statistical significance must not be treated as sufficient evidence of economic importance.

**Implication:**
Important regression results should be interpreted using:

```text
coefficient magnitude
basis-point magnitude
confidence intervals
sample size
economic context
```

alongside p-values.

---

# 32. D030 — Stationarity

**Status:** ACCEPTED

**Decision:**
Relevant time-series properties should be inspected before estimating regressions involving persistent financial or macroeconomic variables.

**Potential Tools:**

```text
visual inspection
Augmented Dickey-Fuller tests
differencing where justified
```

**Reasoning:**
PakYield should avoid naïve regressions between unrelated trending series.

---

# 33. D031 — Robust Standard Errors

**Status:** PROVISIONAL

**Decision:**
HAC/Newey-West standard errors may be used when residual properties justify them.

**Reasoning:**
Financial and macroeconomic time series may exhibit heteroskedasticity and serial correlation.

**Restriction:**
Robust inference must be documented rather than silently applied.

---

# 34. D032 — Multiple Testing

**Status:** ACCEPTED

**Decision:**
The final research output must distinguish between:

```text
primary hypothesis tests
secondary analysis
exploratory analysis
```

**Reasoning:**
Testing many maturities, windows, and specifications increases the likelihood of apparently significant findings arising by chance.

---

# 35. D033 — Nelson-Siegel Model

**Status:** ACCEPTED

**Decision:**
PakYield should attempt Nelson-Siegel yield-curve estimation where real maturity coverage makes the model defensible.

**Expected factors:**

```text
beta0 — level-related factor
beta1 — slope-related factor
beta2 — curvature-related factor
```

**Restriction:**
Optimization success alone does not prove a curve is suitable for interpretation.

---

# 36. D034 — Nelson-Siegel Eligibility Threshold

**Status:** DEFERRED

**Decision:**
Do not choose the minimum number or distribution of maturities required for Nelson-Siegel fitting until actual curve coverage has been audited.

**Reasoning:**
The criterion should reflect observed data structure rather than an arbitrary pre-analysis number.

---

# 37. D035 — Fixed-Income Risk Engine

**Status:** ACCEPTED

**Decision:**
PakYield will include a generic fixed-rate bullet-bond risk calculator.

Expected outputs include:

```text
price
Macaulay duration
modified duration
DV01
convexity
shocked price
```

**Reasoning:**
This demonstrates core fixed-income quantitative skills and allows users to connect yield movements with price risk.

---

# 38. D036 — Rate-Shock Scenarios

**Status:** ACCEPTED

**Decision:**
The baseline risk engine should support at least:

```text
-200 bps
-100 bps
-50 bps
0 bps
+50 bps
+100 bps
+200 bps
```

**Reasoning:**
These scenarios provide a clear symmetric range of rate shocks without unnecessary initial complexity.

---

# 39. D037 — Sukuk Pricing Limitation

**Status:** ACCEPTED

**Decision:**
The generic fixed-rate bond model must not be represented as a complete valuation engine for every Sukuk instrument.

**Reasoning:**
Real Sukuk may involve structural and contractual features not represented in a simple fixed-rate bullet bond.

---

# 40. D038 — Primary Programming Language

**Status:** ACCEPTED

**Decision:**
Use Python 3.12 as the primary programming environment.

**Verified Environment:**
Python 3.12.10.

**Reasoning:**
Python supports the required data engineering, econometrics, optimization, financial mathematics, testing, visualization, and Streamlit deployment.

---

# 41. D039 — Database

**Status:** PROVISIONAL

**Decision:**
Use SQLite as the default analytical database.

**Reasoning:**
The project is expected to contain a manageable research dataset and does not currently require a database server.

SQLite provides:

```text
SQL support
portability
simple reproducibility
zero server administration
easy Python integration
```

**Reconsideration Condition:**
Change only if real scale, concurrency, or deployment requirements justify it.

---

# 42. D040 — Application Framework

**Status:** ACCEPTED

**Decision:**
Use Streamlit for the research application.

**Reasoning:**
Streamlit integrates naturally with the Python research stack and is sufficient for an interactive financial research platform.

A React frontend is not required for v1.0.

---

# 43. D041 — Interactive Visualization

**Status:** ACCEPTED

**Decision:**
Use Plotly for the primary interactive charts.

**Reasoning:**
The research application requires:

```text
hover inspection
date filtering
multi-series comparison
interactive yield curves
responsive financial charts
```

---

# 44. D042 — Statistical Package

**Status:** ACCEPTED

**Decision:**
Use statsmodels as the principal econometric/statistical modeling package.

**Reasoning:**
Statsmodels provides transparent regression output and statistical diagnostics suitable for academic-style analysis.

---

# 45. D043 — Numerical Optimization

**Status:** ACCEPTED

**Decision:**
Use SciPy where numerical optimization is required, including potential Nelson-Siegel estimation.

---

# 46. D044 — Jupyter

**Status:** ACCEPTED

**Decision:**
Use Jupyter notebooks for exploratory analysis, research investigation, and selected reproducible analytical demonstrations.

**Restriction:**
Core reusable logic should eventually migrate from notebooks into tested Python modules where appropriate.

---

# 47. D045 — VS Code

**Status:** ACCEPTED

**Decision:**
Use Visual Studio Code as the primary development environment.

Verified configuration includes:

```text
Python extension
Jupyter extension
Ruff extension
```

---

# 48. D046 — Git and GitHub

**Status:** ACCEPTED

**Decision:**
Use Git for version control and GitHub for remote repository hosting.

Verified Git configuration:

```text
default branch: main
GitHub SSH authentication: working
```

**Important:**
The final project repository will not be initialized during Phase 1.

Repository initialization belongs to Phase 3.

---

# 49. D047 — Homebrew

**Status:** REJECTED FOR CURRENT REQUIREMENTS

**Decision:**
Do not require Homebrew for the current PakYield development environment.

**Reasoning:**
The Homebrew installer repeatedly stalled on the current macOS environment.

All tools currently required for PakYield are already available without Homebrew, including:

```text
Python
pip
Git
SQLite
VS Code
Command Line Tools
Jupyter
Streamlit
```

**Reconsideration Condition:**
Homebrew may be revisited later only if a required dependency cannot be installed or managed adequately using the existing environment.

---

# 50. D048 — Production Virtual Environment

**Status:** ACCEPTED

**Decision:**
The final PakYield repository will use a project-specific Python virtual environment.

Expected local folder:

```text
.venv
```

**Reasoning:**
Project dependencies should remain isolated from global Python installations.

---

# 51. D049 — Phase 1 Workspace

**Status:** ACCEPTED

**Decision:**
Phase 1 research documents will initially be created in:

```text
~/PakYield-Phase1
```

without Git initialization.

**Reasoning:**
The final repository architecture belongs to a later project phase.

The research specification should be stabilized before repository scaffolding.

---

# 52. D050 — Scope Exclusions

**Status:** ACCEPTED

**Decision:**
PakYield v1.0 will not include unrelated product-development features merely to increase technical complexity.

Explicitly excluded from the required core include:

```text
authentication
user accounts
payments
brokerage integration
live trading
crypto
blockchain
AI chatbot
social networking
mobile application
React frontend
microservices
machine-learning price prediction
LSTM forecasting
XGBoost forecasting
```

**Reasoning:**
These features do not materially improve the central research question.

---

# 53. D051 — Forecasting Claims

**Status:** ACCEPTED

**Decision:**
Do not describe PakYield as a forecasting system unless a genuine predictive model with appropriate out-of-sample validation is later implemented.

---

# 54. D052 — Investment Advice

**Status:** ACCEPTED

**Decision:**
PakYield will not provide personal investment advice.

It will not produce:

```text
buy recommendations
sell recommendations
guaranteed forecasts
target prices
personalized portfolio recommendations
```

The application is an analytical and research platform.

---

# 55. D053 — Finding Presentation

**Status:** ACCEPTED

**Decision:**
Important empirical results should generally distinguish:

```text
Evidence
Interpretation
Limitation
```

**Reasoning:**
This prevents empirical observations from being blended with stronger unsupported conclusions.

---

# 56. D054 — Project Priority Order

**Status:** ACCEPTED

**Decision:**
PakYield development should prioritize:

```text
1. correctness
2. research credibility
3. real data
4. reproducibility
5. financial reasoning
6. statistical discipline
7. testing
8. clarity
9. professional presentation
```

**Reasoning:**
A technically flashy project with unreliable financial analysis would undermine the purpose of the project.

---

# 57. D055 — Scope Change Procedure

**Status:** ACCEPTED

**Decision:**
Major changes to:

```text
research question
sample period
tenor universe
source selection
methodology
database architecture
analytical interpretation
core application scope
```

must be documented in this decision ledger.

**Required Information for Future Decisions:**

```text
Decision ID
Date
Status
Decision
Reasoning
Evidence
Affected files/modules
Previous decision superseded, if any
```

---

# 58. Future Decision Template

Use this structure for future entries:

```text
# DXXX — Decision Title

Date:
Status:

Decision:

Reasoning:

Evidence:

Implications:

Affected Components:

Supersedes:
```

If the decision does not supersede another decision, write:

```text
Supersedes: None
```

---

# 59. Phase 1 Decision State

At completion of Phase 1:

**Accepted conceptual decisions include:**

```text
project positioning
central research question
RQ1–RQ4
H1–H4
research-integrity rules
event-study interpretation limits
PKISRV-PKRV spread convention
yield and basis-point units
core technical stack
scope exclusions
reproducibility principles
```

**Important unresolved decisions remain:**

```text
final sample period
final maturity universe
exact data sources
exact PKRV/PKISRV overlap period
event-date alignment implementation
policy-regime algorithm
FX inclusion
auction-data inclusion
final econometric equation
Nelson-Siegel eligibility threshold
```

These unresolved decisions are intentionally deferred until evidence is available.

---

# 60. Decision Ledger Status

**Status:** ACTIVE

This document becomes a permanent part of the PakYield project.

Future project phases should update it whenever a major research or engineering choice is made or revised.

# 61. D056 — PKRV Acquisition Boundary

Date: September 16, 2026  
Status: PROVISIONAL

Decision:

Use MUFAP's current official PKRV/PKISRV/PKFRV pricing interface as the primary
PKRV acquisition source.

For planning purposes, treat January 29, 2020 as the earliest currently
reliably downloadable PKRV observation.

Reasoning:

The current MUFAP interface provides downloadable historical CSV files from
this period onward, while older legacy archive links are no longer reliably
retrievable.

The downloaded files also demonstrate structural variation across dates, so
the later ingestion pipeline must support schema detection and normalization.

Implications:

- 2020–2026 becomes the leading candidate PKRV research period.
- Pre-2020 PKRV will not be required for the core project unless a reliable
  source is later identified.
- Missing calendar dates will not be synthetically filled.
- The final common sample remains dependent on PKISRV and other required
  datasets.

Affected Components:

- data feasibility audit
- later ingestion design
- sample-period selection
- yield-curve analysis
- event-study date alignment

Supersedes: None

# 62. D057 — Standardized PKISRV Acquisition

Date: September 17, 2026  
Status: ACCEPTED

Decision:

Use PakDataHub as the machine-readable acquisition source for the standardized
daily PKISRV tenor series, while treating MUFAP as the underlying authoritative
benchmark source and validation reference.

The core standardized PKISRV maturity set will be:

- 1M
- 3M
- 6M
- 9M
- 1Y

The comparative PKRV/PKISRV empirical sample will provisionally begin on
February 3, 2025.

Reasoning:

Historical MUFAP PKISRV downloads use changing instrument-level and
dealer-quote structures that would require substantial reconstruction.

Modern MUFAP files explicitly publish standardized PKISRV tenor yields under
SECP Direction 24 of 2024.

PakDataHub exposes these tenor series directly as daily MUFAP-sourced data,
providing a cleaner and more reproducible research interface appropriate for
the portfolio scope.

Implications:

- PKRV-only analysis may use a longer sample than PKRV/PKISRV comparison.
- PKRV/PKISRV comparison will use only common tenors.
- No synthetic long-end PKISRV maturities will be created.
- Nelson-Siegel modeling will focus on PKRV rather than PKISRV.
- MUFAP values will be spot-checked against PakDataHub during validation.

Affected Components:

- PKISRV ingestion
- sample design
- H2
- H3
- comparative dashboard pages
- methodology documentation

Supersedes: None

# 63. D058 — SBP Policy Rate Source

Date: September 17, 2026
Status: ACCEPTED

Decision:

Use the State Bank of Pakistan EasyData Policy (Target) Rate series as the
authoritative source for PakYield's policy-rate history.

Series key:

`TS_GP_IR_SIRPR_AH.SBPOL0030`

Reasoning:

SBP is the authoritative monetary-policy institution and EasyData provides
an official machine-readable CSV of the Policy (Target) Rate.

The downloaded feasibility file contains 39 official rate observations from
May 25, 2015 through April 28, 2026, fully covering PakYield's expected
empirical period.

Implications:

- no secondary provider is required for the core policy-rate history;
- original rate-change observations will be preserved;
- a derived daily step-function policy-rate series may later be created for
  alignment with daily yield observations;
- HOLD meetings will be represented separately in the MPC event dataset;
- announcement dates and effective rate dates must not be silently conflated.

Affected Components:

- policy-rate ingestion
- macroeconomic analysis
- monetary-policy regime classification
- MPC event study
- Streamlit policy-rate views

Supersedes: None

# 64. D059 — MPC Event Source

Date: September 17, 2026  
Status: ACCEPTED

Decision:

Use the State Bank of Pakistan Monetary Policy Statements archive as the
authoritative source for PakYield's MPC event dataset.

Reasoning:

The official archive provides event-level statements following MPC meetings
and includes both policy-rate changes and unchanged-rate decisions.

This is required because the SBP EasyData policy-rate series records rate
changes but does not independently identify every HOLD meeting.

Implications:

- MPC events will be maintained separately from policy-rate history.
- Every event will be classified as HIKE, CUT, or HOLD.
- Official statement dates will serve as provisional announcement dates.
- Policy-rate values will be cross-checked against the EasyData series.
- Closely spaced 2020 policy actions will be explicitly flagged during the
  event-study design.

Affected Components:

- event-study dataset
- H1
- MPC dashboard
- event-window calculations
- research paper

Supersedes: None

# 65. D060 — CPI Inflation Source

Date: September 20, 2026
Status: ACCEPTED

Decision:

Use Pakistan Bureau of Statistics as the authoritative and primary acquisition
source for PakYield's CPI inflation dataset.

The principal inflation variable will be monthly National headline CPI
year-on-year inflation using the 2015-16 base.

The National CPI index level will also be retained.

Reasoning:

PBS directly publishes historical monthly CPI indices and year-on-year growth
rates covering the PakYield research period.

SBP EasyData was considered as a convenient machine-readable distribution
route, but service availability was inconsistent during the feasibility audit
and is not necessary because the underlying PBS data are publicly available.

Implications:

- CPI acquisition will not depend on SBP EasyData.
- Historical PBS PDF tables will be extracted programmatically.
- Published YoY inflation will be cross-checked against the CPI index.
- Monthly macroeconomic analysis will use National headline CPI.
- Urban and Rural CPI may be retained as secondary variables.
- SPI will not substitute for CPI.

Affected Components:

- CPI ingestion
- macroeconomic analysis
- RQ4
- econometric models
- inflation visualizations

Supersedes: None

# 66. D061 — Optional Macro and Auction Datasets

Date: September 20, 2026
Status: ACCEPTED

Decision:

Exclude PKR/USD, government-security auction datasets, and government-security
trading datasets from the required PakYield v1 empirical scope.

Reasoning:

These datasets are useful contextual extensions but are not necessary to answer
the project's principal research questions.

PakYield already has sufficient core data through:

- PKRV;
- PKISRV;
- SBP policy-rate history;
- SBP MPC events;
- CPI inflation.

Adding optional FX and auction datasets during v1 would increase acquisition,
cleaning, validation, and modeling complexity without being necessary for the
core portfolio research contribution.

Implications:

- RQ4 will focus primarily on policy rate and CPI inflation.
- PKR/USD may be added later as an extension.
- Auction and trading datasets may be added later as advanced modules.
- The v1 project remains focused and reproducible.

Affected Components:

- Phase 2 scope
- macroeconomic analysis
- econometric specification
- dashboard scope
- research paper

Supersedes: None

# 67. D062 — Final Analytical Sample Periods

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will use different sample periods for different analytical modules
where required by actual data availability.

## Sample A — Conventional Yield-Curve and MPC Analysis

Period:

January 29, 2020 through the latest available 2026 observation.

Primary datasets:

- PKRV
- SBP policy rate
- SBP MPC events

Uses:

- RQ1
- RQ2
- H1
- conventional yield-curve analysis
- MPC announcement-window study
- Nelson-Siegel analysis

## Sample B — PKRV / PKISRV Comparative Analysis

Period:

February 3, 2025 through the latest common available 2026 observation.

Common tenors:

- 1M
- 3M
- 6M
- 9M
- 1Y

Uses:

- RQ3
- H2
- H3
- PKISRV-PKRV spread analysis
- rolling co-movement analysis

## Sample C — Monthly Macroeconomic Analysis

Period:

2020 through 2026, subject to exact monthly alignment during implementation.

Primary datasets:

- selected monthly PKRV transformation
- SBP policy rate
- National CPI YoY inflation

Uses:

- RQ4
- macroeconomic regressions
- policy-regime analysis

Reasoning:

The mandatory datasets do not share an identical historical starting date.

Using separate analytical samples preserves substantially more valid data than
forcing the entire project to begin in February 2025.

This approach also avoids reconstructing unreliable pre-2020 PKRV or
pre-standardization PKISRV observations.

Implications:

- sample size will be reported separately for every major analysis;
- charts and statistical outputs must identify their sample period;
- comparisons will use only dates and tenors available in the relevant datasets;
- no synthetic historical observations will be created.

Affected Components:

- all empirical analysis
- event study
- comparative analysis
- econometrics
- dashboard filters
- research paper

Supersedes:

D005 — Final Sample Period

# 68. D063 — Final Tenor Universe

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will retain all standardized PKRV maturities that are validly
available in the source data while using a smaller focal tenor set for
primary analysis and presentation.

## PKRV Canonical Tenor Universe

The standardized PKRV tenor vocabulary is:

1W
2W
1M
2M
3M
4M
6M
9M
1Y
2Y
3Y
4Y
5Y
6Y
7Y
8Y
9Y
10Y
15Y
20Y

A tenor will be retained only when it is genuinely present in the source
observation.

Missing tenors will not be manufactured.

## PKRV Focal Analytical Tenors

The primary maturity points for charts, tables, event-study summaries, and
interpretation will be:

3M
6M
1Y
2Y
3Y
5Y
10Y
15Y
20Y

This subset provides representation of:

- short end;
- intermediate maturities;
- long end.

Other valid PKRV maturities remain available for detailed analysis and
curve fitting.

## PKRV / PKISRV Comparative Tenors

The standardized common comparison universe is:

1M
3M
6M
9M
1Y

Only directly matching maturities will be used for PKISRV-PKRV comparisons.

No synthetic PKISRV maturity points will be created.

## Primary Term Spreads

Subject to both maturities being available on the relevant observation date,
the preferred term-spread measures are:

10Y - 2Y
10Y - 1Y
5Y - 1Y
3Y - 3M

These provide multiple views of short-versus-long curve shape.

## H1 Maturity Groups

For MPC announcement-window analysis, maturity sensitivity may be summarized
using representative groups.

Short end:

3M
6M
1Y

Longer end:

5Y
10Y

Individual maturity results will also be retained.

The group definitions are analytical summaries and do not replace the
underlying maturity-level observations.

## Nelson-Siegel

Nelson-Siegel estimation will use all valid PKRV maturity observations
available on an eligible date rather than only the focal analytical tenor set.

The minimum coverage requirement for an eligible curve will be finalized
during model implementation after empirical coverage diagnostics.

## Reasoning

Retaining the full observed tenor structure preserves information for
yield-curve fitting and exploratory analysis.

Using a smaller focal subset prevents the dashboard and research paper from
becoming unnecessarily crowded while still representing the short,
intermediate, and long portions of the curve.

The separate five-tenor PKRV/PKISRV universe reflects the actual standardized
PKISRV data available rather than creating artificial comparability.

Implications:

- ingestion must normalize recognized tenor labels;
- source observations remain authoritative;
- missing maturities remain missing;
- charts may default to focal tenors while allowing broader exploration;
- comparative Islamic/conventional analysis uses only common maturities;
- Nelson-Siegel may use a richer tenor set than other analytical modules.

Affected Components:

- yield-curve ingestion
- RQ1
- RQ2
- RQ3
- H1
- H2
- H3
- term-spread calculations
- Nelson-Siegel
- Streamlit charts
- research paper

Supersedes:

D006 — Final Tenor Universe

# 69. D064 — Streamlit Interface Direction

Date: September 20, 2026
Status: ACCEPTED

Decision:

The PakYield Streamlit research application will use a Bloomberg-inspired
visual and interaction direction.

The interface should emphasize:

- dark professional research-terminal presentation;
- high information density;
- compact controls;
- data-first layouts;
- prominent market metrics;
- efficient navigation;
- restrained visual decoration;
- strong tabular presentation;
- research-oriented charts and analytics.

The application may draw inspiration from Bloomberg-style financial interfaces
without attempting to reproduce proprietary Bloomberg software or branding.

Reasoning:

PakYield is intended to feel like a serious fixed-income research workstation
rather than a generic consumer dashboard.

Implications:

- Streamlit architecture should support reusable metric, chart, table, and
  navigation components;
- screen space should prioritize financial information;
- styling should remain consistent across research modules;
- later UI specifications will define typography, spacing, component hierarchy,
  navigation, and presentation rules.

Affected Components:

- Streamlit application
- UI design specification
- dashboard architecture
- chart layouts
- navigation
- final portfolio presentation

Supersedes: None

# 70. D065 — Production Repository Architecture

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will use a Python src-layout architecture with research data,
application code, analytical modules, tests, SQL, notebooks, and generated
research outputs separated into dedicated directories.

Primary structure:

- src/pakyield
- app
- data
- notebooks
- sql
- scripts
- tests
- reports
- docs

Analytical functionality under src/pakyield will be separated into:

- ingestion;
- cleaning;
- validation;
- database;
- yield-curve analytics;
- MPC event-study analytics;
- econometrics;
- fixed-income risk;
- Nelson-Siegel modeling;
- shared utilities.

Reasoning:

The project combines research, data engineering, quantitative finance, and a
Streamlit frontend.

Separating reusable financial logic from the application layer improves:

- testability;
- maintainability;
- reproducibility;
- clarity;
- future deployment.

The Streamlit application will call reusable PakYield modules rather than
implementing core financial logic directly inside UI pages.

Implications:

- reusable Python code belongs primarily under `src/pakyield`;
- exploratory work may occur under `notebooks`;
- Streamlit-specific presentation code belongs under `app`;
- raw, interim, and processed data remain separated;
- tests mirror production responsibilities;
- generated figures and tables are separated from source code.

Affected Components:

- Python packaging
- data pipeline
- analytics
- testing
- Streamlit application
- research workflow

Supersedes: None

# 71. D066 — Python Environment and Dependency Management

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will use a project-local Python 3.12 virtual environment located at:

`.venv`

Python package metadata and direct project dependencies will be defined in:

`pyproject.toml`

The project will be installed locally in editable mode during development.

An exact snapshot of installed package versions will be maintained in:

`requirements-lock.txt`

Reasoning:

A project-local environment prevents PakYield dependencies from interfering
with the system Python installation or unrelated projects.

Using `pyproject.toml` provides a modern canonical Python package definition,
while the lock snapshot improves reproducibility of the verified development
environment.

Core dependency categories include:

- numerical computing;
- data analysis;
- econometrics;
- scientific optimization;
- visualization;
- Streamlit;
- source acquisition;
- Excel parsing;
- PDF table extraction;
- Parquet support;
- notebooks;
- automated testing;
- linting;
- static type checking.

Implications:

- Python commands should normally run with `.venv` activated;
- production modules remain importable through the `src` package layout;
- `.venv` will never be committed to Git;
- dependency changes must be reflected in `pyproject.toml`;
- verified environments should regenerate `requirements-lock.txt`;
- unnecessary libraries should not be added merely for technical complexity.

Affected Components:

- all Python modules
- data ingestion
- econometrics
- fixed-income analytics
- Streamlit
- testing
- reproducibility

Supersedes: None

# 72. D067 — Centralized Research Configuration

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will maintain shared project paths and frozen research configuration
in:

`src/pakyield/config.py`

The configuration module will contain stable definitions including:

- repository paths;
- raw, interim and processed data locations;
- database location;
- dataset identifiers;
- canonical PKRV tenor universe;
- focal PKRV tenor universe;
- common PKRV/PKISRV tenor universe;
- preferred term spreads;
- MPC event classifications;
- MPC event-window sizes;
- approved analytical sample start dates;
- financial storage and display units.

Research assumptions that have already been formally accepted should not be
redefined independently inside ingestion, analytics, database, notebook or
Streamlit modules.

No API keys, passwords or other secrets will be stored in this module.

Reasoning:

Centralized configuration reduces duplicated assumptions and prevents
different components of the research platform from silently using conflicting
sample periods, maturity definitions, directory paths or units.

Implications:

- production modules should import shared definitions from
  `pakyield.config`;
- raw operating-system-specific absolute paths should not be hard-coded;
- `.env` infrastructure will not be introduced unless a genuine secret or
  environment-specific value becomes necessary;
- sample end dates remain driven by validated data availability;
- changes to frozen research definitions require corresponding updates to the
  decision log.

Affected Components:

- ingestion
- cleaning
- validation
- database
- analytics
- notebooks
- tests
- Streamlit
- reproducibility

Supersedes: None

# 73. D068 — SQLite Core Research Schema

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will use SQLite as the local analytical database for the v1 research
platform.

The generated database will be located at:

`data/processed/pakyield.sqlite3`

The initial normalized schema contains:

- `schema_version`;
- `ingestion_runs`;
- `yield_observations`;
- `policy_rate_observations`;
- `mpc_events`;
- `cpi_observations`.

PKRV and PKISRV observations will share the `yield_observations` table and
will be distinguished using the `curve_type` field.

The normalized yield uniqueness rule is:

`observation_date + curve_type + tenor`

The database stores yields and rates in percentage units rather than decimal
fractions.

Examples:

`12.50` means `12.50%`.

It does not mean:

`0.125`.

Foreign-key enforcement will be enabled on every application connection.

Raw source files remain outside SQLite under the `data/raw` hierarchy.

SQLite contains normalized research-ready observations and provenance rather
than replacing the raw evidence files.

The generated SQLite database itself will not be committed to Git.

Reasoning:

SQLite provides sufficient relational integrity, SQL capability,
reproducibility and portability for a single-researcher analytical project
without introducing an unnecessary database server.

A normalized schema also allows Python, notebooks, tests and Streamlit to use
the same underlying research data.

Implications:

- ingestion pipelines must preserve source provenance;
- duplicates at the defined observation key are rejected;
- PKRV and PKISRV remain distinguishable;
- MPC HIKE/CUT/HOLD classifications are constrained;
- processed database state can be rebuilt from source data;
- database schema changes must be versioned;
- analytical calculations should not silently overwrite raw observations.

Affected Components:

- ingestion
- validation
- SQL
- analytics
- econometrics
- notebooks
- testing
- Streamlit
- reproducibility

Supersedes: None

# 74. D069 — Data Dictionary and Tenor Coordinate Convention

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will maintain a canonical field-level data dictionary in:

`docs/DATA_DICTIONARY.md`

All normalized interest rates, sovereign benchmark yields, and CPI inflation
rates will be stored in percentage-point form.

Example:

`12.50`

means:

`12.50%`

not:

`0.125`.

Yield changes and spreads may be displayed in basis points using:

`1 percentage point = 100 basis points`.

Generic benchmark tenor labels will use one shared maturity-coordinate mapping.

Weeks use:

`days / 365`

Months use:

`months / 12`

Years use their stated year value.

Examples:

- 3M = 0.25 years
- 6M = 0.50 years
- 1Y = 1.00 year
- 10Y = 10.00 years

These coordinates represent generic benchmark maturity buckets and must not be
misrepresented as exact remaining maturities of individual securities.

Missing empirical observations remain missing and will not be converted to
zero or silently interpolated.

Derived analytical variables remain distinguishable from normalized source
observations.

Reasoning:

Explicit field definitions and unit conventions reduce the risk of silent
financial calculation errors and inconsistent interpretation across Python,
SQL, econometrics, notebooks, tests, and Streamlit.

Affected Components:

- data ingestion
- data validation
- database
- yield curves
- spreads
- Nelson-Siegel
- econometrics
- fixed-income analytics
- tests
- Streamlit
- research documentation

Supersedes: None

# 75. D070 — Database Integrity Testing Strategy

Date: September 20, 2026
Status: ACCEPTED

Decision:

PakYield will use automated pytest integration tests to validate the SQLite
research schema and its key integrity constraints.

Database integration tests will use temporary databases created by pytest
rather than the production research database.

The initial database test suite verifies:

- database creation;
- idempotent schema initialization;
- required table existence;
- foreign-key enforcement;
- yield-observation uniqueness;
- valid and invalid MPC decision/change direction;
- policy-rate effective-date uniqueness;
- CPI period uniqueness;
- valid sovereign curve classifications;
- valid ingestion dataset identifiers.

Reasoning:

Database constraints are part of the research-integrity layer and should be
continuously testable rather than verified only through one-time manual
terminal checks.

Temporary test databases ensure automated testing cannot contaminate empirical
research data.

Implications:

- production data must never be used as a pytest fixture;
- database schema changes require corresponding test updates;
- failed integrity tests block progression until resolved;
- ingestion development will later add further validation and pipeline tests;
- empirical datasets remain separate from synthetic test fixtures.

Affected Components:

- SQLite
- testing
- ingestion
- validation
- CI/CD
- reproducibility

Supersedes: None


# 76. D071 — Streamlit Application Architecture

Date: September 27, 2026
Status: ACCEPTED

Decision:

PakYield will use a multipage Streamlit application architecture with reusable
presentation components separated from research and analytical logic.

The initial application structure contains:

- Home;
- Market Overview;
- Yield Curve Lab;
- Monetary Policy Lab;
- Islamic vs Conventional;
- Fixed-Income Risk;
- Research.

Reusable interface functionality will reside primarily under:

- `app/components`;
- `app/styles`.

Core financial and empirical logic will remain under:

`src/pakyield`

and will not be implemented directly inside Streamlit page files.

The visual direction is Bloomberg-inspired rather than a reproduction of
Bloomberg proprietary software or branding.

The design emphasizes:

- dark financial-terminal presentation;
- dense information layout;
- compact controls;
- strong metric hierarchy;
- restrained decoration;
- research-first visualizations;
- consistent reusable components.

No empirical value or research finding may be fabricated for interface
demonstration.

Before validated datasets are available, application panels must clearly use
placeholders.

Reasoning:

Separating presentation from financial logic improves maintainability,
testability, reproducibility and later design iteration.

It also prevents the Streamlit application from becoming the source of
research calculations.

Implications:

- Streamlit consumes PakYield analytical modules;
- application pages remain relatively thin;
- reusable styling and layout components are shared;
- real values appear only after validated ingestion;
- interface styling may evolve without changing research logic.

Affected Components:

- Streamlit
- dashboard navigation
- charts
- metrics
- application testing
- portfolio presentation

Supersedes:

D064 only where this decision provides more detailed implementation direction.


# 77. D072 — Python Quality Gate Configuration

Date: September 27, 2026
Status: ACCEPTED

Decision:

PakYield will define its Python linting, formatting, automated testing,
coverage, and static type-checking configuration centrally in:

`pyproject.toml`

The initial quality toolchain consists of:

- Ruff for linting;
- Ruff formatter for formatting validation;
- pytest for automated tests;
- pytest-cov / coverage.py for test coverage reporting;
- mypy for static type checking.

Python 3.12 is the configured language target.

The initial Ruff lint families include:

- E — pycodestyle errors;
- F — Pyflakes;
- I — import sorting;
- UP — Python upgrade rules;
- B — flake8-bugbear.

Automated tests are separated into:

- `tests/unit`;
- `tests/integration`.

Research assumptions stored in the centralized configuration module will also
be protected by unit tests so that accepted sample periods, maturity universes,
event windows, spread definitions, and financial unit conventions cannot
change silently.

Reasoning:

A research project intended for GitHub, academic review, and portfolio use
requires repeatable quality gates rather than ad-hoc manual checks.

Linting, testing and static checking reduce accidental implementation errors
while preserving the distinction between software correctness and empirical
research validity.

Coverage percentage will be treated as a diagnostic rather than a target to
optimize artificially.

Implications:

- quality checks should be run before meaningful commits;
- failing tests block progression;
- lint failures should be resolved rather than ignored casually;
- type checking initially applies to production code under `src`;
- future modules should include tests appropriate to their research risk;
- passing software tests does not itself validate empirical conclusions.

Affected Components:

- Python development
- testing
- CI/CD
- reproducibility
- Git workflow
- future ingestion and analytics modules

Supersedes: None
# 78. D073 — Phase 3 Repository and Architecture Acceptance

Date: September 27, 2026
Status: ACCEPTED

Decision:

Phase 3 — Repository & Architecture is formally accepted.

The accepted Phase 3 baseline includes:

- permanent PakYield Git repository;
- production directory architecture;
- isolated Python 3.12 virtual environment;
- centralized research configuration;
- SQLite research database schema;
- formal data dictionary and storage conventions;
- automated database integrity tests;
- multipage Streamlit application architecture;
- Bloomberg-inspired research-terminal visual direction;
- centralized Ruff, pytest, coverage, and mypy quality gates;
- verified Git exclusions for local databases, environments, and secrets;
- GitHub SSH remote configuration;
- synchronized local and remote `main` branches.

Acceptance evidence includes:

- all required project directories validated;
- production empirical tables empty before ingestion;
- Streamlit application compiling successfully;
- six secondary Streamlit pages present;
- Ruff checks passing;
- Ruff formatting checks passing;
- 24 automated tests passing;
- mypy reporting no issues in production source files;
- forbidden local files absent from Git tracking;
- Phase 3 decision headings D064 through D072 verified;
- local and remote Git HEAD synchronized.

No empirical research findings have been manufactured or introduced during
this architecture phase.

Reasoning:

The software and research-governance foundation is sufficiently stable to
support the next implementation phase without mixing architecture work with
production data ingestion.

Implications:

- Phase 3 architecture is now the accepted baseline;
- subsequent work should build on this structure rather than bypass it;
- changes to accepted architectural conventions should be documented;
- production data ingestion begins only in the next explicitly started phase;
- empirical conclusions remain prohibited until validated data and analytical
  procedures support them.

Affected Components:

- entire PakYield repository
- Git workflow
- database architecture
- Streamlit architecture
- testing and quality gates
- research governance

Supersedes: None

# 79. D074 — Raw Data Acquisition and Provenance Contract

Date: September 29, 2026
Status: ACCEPTED

Decision:

PakYield production data acquisition will follow an immutable raw-data and
provenance-first workflow.

Production source artifacts will be stored under dataset-specific directories
within:

`data/raw/`

and will remain distinct from transformed data stored under:

- `data/interim/`;
- `data/processed/`.

The Phase 4 required production datasets are:

- PKRV;
- PKISRV;
- SBP policy rate;
- SBP MPC events;
- PBS CPI.

Every successfully acquired production artifact should retain sufficient
provenance to identify:

- dataset identifier;
- source authority;
- acquisition source;
- source reference;
- retrieval timestamp;
- local raw path;
- file format;
- SHA-256 checksum;
- file size;
- acquisition status;
- known source or schema issues.

Raw production files must not be manually altered to normalize schemas, fill
missing observations, change dates, convert units, remove apparent anomalies,
or manufacture consistent historical structures.

Source-format and schema differences are evidence about the source and must be
handled explicitly in later transformation stages.

Missing raw observations remain missing. They must not be represented as zero
unless the source itself reports zero.

Production raw market and macroeconomic files remain outside Git under the
current repository policy. Acquisition code, manifests, metadata contracts,
and documentation may be version controlled.

The raw-data stage does not establish empirical findings, causality, monetary
policy surprises, predictive relationships, or an Islamic premium or discount.

Reasoning:

PakYield is intended to support reproducible fixed-income research. Preserving
source artifacts and recording provenance before transformation makes it
possible to distinguish what the source actually supplied from what PakYield
later derives.

Checksums provide byte-level identification of acquired artifacts and reduce
the risk of silently replacing or modifying evidence used in later analysis.

Implications:

- cleaning never modifies production raw files in place;
- derived datasets must be traceable to raw artifacts;
- acquisitions should receive checksums and metadata;
- raw schema drift remains visible;
- ingestion failures must not be presented as successful acquisitions;
- empirical interpretation occurs only after validation and analysis.

Affected Components:

- data acquisition
- provenance
- raw data storage
- ingestion
- validation
- reproducibility
- research governance

Supersedes: None

# 80. D075 — Primary PKRV Empirical Sample Begins in 2022

Date: September 29, 2026
Status: ACCEPTED

Decision:

PakYield v1 will use 4 January 2022 as the beginning of the primary PKRV
empirical sample.

The primary PKRV research window is therefore:

**2022-01-04 through the latest validated 2026 observation.**

The required monetary-policy and macroeconomic analytical window is likewise
centered on 2022 through 2026.

The PKRV/PKISRV common comparative sample continues to begin on 3 February
2025.

The twelve monthly PKRV workbooks available for 2020 are optional historical
material and are not required for the primary empirical analysis.

PKRV observations for 2021 are excluded from required v1 because the current
MUFAP machine-readable archive does not expose those production artifacts
through the same reproducible acquisition path.

This decision does not imply that PKRV observations did not exist during 2021.

Reasoning:

The current MUFAP pricing API provides a consistent, machine-readable daily
PKRV archive from January 2022 through the current 2026 observation period.

Using that consistent period is preferable for the portfolio research project
to reconstructing a broken legacy archive solely to lengthen the historical
sample.

The 2022-2026 window provides substantial daily fixed-income data and multiple
monetary-policy regimes while preserving transparent and reproducible source
acquisition.

Implications:

- `PKRV_SAMPLE_START` becomes 2022-01-04;
- the primary macroeconomic analytical window begins in 2022;
- 2020 PKRV files are optional historical material;
- 2021 PKRV recovery is not required for v1;
- missing 2021 observations will not be interpolated or synthesized;
- conclusions must be scoped to the validated analytical period;
- earlier CPI observations may still be acquired as support data when needed
  for twelve-month inflation validation.

Affected Components:

- research scope
- PKRV acquisition
- monetary-policy event study
- CPI alignment
- configuration
- methodology
- portfolio documentation

Supersedes:

- D062 only with respect to the original 2020 PKRV and macro sample starts;
- D063 where sample-period assumptions depend on the previous PKRV start date.

# 81. D076 — Current MUFAP PKRV Source and Daily Raw Schema

Date: September 29, 2026
Status: ACCEPTED

Decision:

PakYield will use MUFAP's current Pricing API and the file references returned
by that API as the required v1 acquisition path for PKRV observations from the
accepted 2022-2026 primary sample.

The verified current MUFAP metadata endpoint is:

`https://www.mufap.com.pk/WebRegulations/GetSecpFileById`

using the PKRV/PKISRV/PKFRV pricing category represented by:

`fk_HeaderSubMenuTabId = 46`

A single production PKRV artifact for 4 January 2022 was successfully acquired
from MUFAP and preserved without transformation.

The verified raw daily PKRV CSV schema is:

- `Tenor`
- `Mid Rate`
- `Change`

The 4 January 2022 artifact contains exactly twenty tenor observations in this
order:

- 1W
- 2W
- 1M
- 2M
- 3M
- 4M
- 6M
- 9M
- 1Y
- 2Y
- 3Y
- 4Y
- 5Y
- 6Y
- 7Y
- 8Y
- 9Y
- 10Y
- 15Y
- 20Y

This sequence exactly matches `PKRV_CANONICAL_TENORS`.

The validated artifact is:

`PKRV040120221900.csv`

with:

- size: 329 bytes;
- SHA-256:
  `e2bee0efd2e87bcddb30332def0ba40c1bf2c5c33d9bae468692e2743c08f252`.

The production raw artifact remains excluded from Git while its provenance
metadata may be version controlled.

Reasoning:

A one-artifact acquisition was required before bulk downloading the historical
PKRV universe.

The validation established that:

- the current MUFAP API can be accessed reproducibly;
- the returned production file URL is valid;
- the source file can be stored unchanged;
- its checksum and file size can be reproduced;
- the daily PKRV file exposes the complete canonical tenor structure expected
  by PakYield;
- production raw files remain separate from version-controlled research code
  and metadata.

The raw `Change` field is preserved as supplied by MUFAP. Its economic and unit
interpretation will not be assumed merely from the column name and will be
validated before analytical use.

Implications:

- bulk PKRV acquisition may proceed for the accepted 2022-2026 sample;
- each production artifact must retain byte-level provenance;
- bulk acquisition must not overwrite existing raw artifacts silently;
- duplicate MUFAP metadata dates must be detected explicitly;
- title/file-path metadata discrepancies must remain auditable;
- raw PKRV data must not be cleaned in place;
- tenor/schema deviations must be surfaced rather than silently normalized;
- the meaning of the raw `Change` field remains subject to later validation.

Affected Components:

- MUFAP acquisition
- PKRV provenance
- PKRV schema validation
- raw-data storage
- bulk ingestion
- later cleaning and transformation

Supersedes:

- the obsolete legacy-MUFAP acquisition approach explored during Batch 4.2A.

# 82. D077 — PKRV Bulk Metadata Anomaly Resolution

Date: September 29, 2026
Status: ACCEPTED

Decision:

PakYield resolved all thirteen PKRV metadata rows classified for manual review
within the accepted 2022-2026 acquisition period.

The 1,164 MUFAP PKRV metadata rows are reduced to exactly 1,159 approved
observation artifacts, representing exactly 1,159 unique observation dates.

No missing observation is synthesized and no raw source file is modified.

Resolved cases:

### 30 March 2022

Two MUFAP CSV artifacts are byte-identical and contain the same canonical
twenty-tenor PKRV curve.

PakYield selects the lower-metadata-index artifact:

`PKRV300320221960.csv`

The duplicate `PKRV300320221963.csv` is excluded as redundant.

### 31 March 2022

Two MUFAP CSV artifacts are byte-identical.

Both contain the complete twenty-tenor PKRV curve followed by a blank row.

PakYield selects:

`PKRV310320221961.csv`

The duplicate `PKRV310320221962.csv` is excluded as redundant.

The trailing blank row remains part of the immutable raw artifact and may only
be handled in a later cleaning layer.

### 24 July 2024

`PKRV24072023833.csv` is excluded.

Its filepath contains a 2023 date token and its contents are an old-style
dealer/rate sheet rather than the canonical daily PKRV structure.

PakYield selects the canonical artifact:

`PKRV24072024679.csv`

### 2 August 2024

PakYield selects:

`PKRV0208020241026.csv`

The filename contains a malformed date token, but the MUFAP metadata and
artifact contents identify it as the valid canonical PKRV observation for
2 August 2024.

The raw filename is preserved unchanged.

### 23 September 2024

`PKISRV230920241327.csv` is excluded from PKRV acquisition because its contents
are GOP Ijarah Sukuk / PKISRV revaluation data.

PakYield selects:

`PKRV230920241328.csv`

which contains the canonical twenty-tenor PKRV curve.

### 6 January 2025

`PKRV060120253092.csv` is excluded because the MUFAP file reference currently
returns HTTP 404.

PakYield selects:

`PKRV060120253224.csv`

which returns HTTP 200 and contains the canonical twenty-tenor PKRV curve.

### 20 August 2025

PakYield accepts the source artifact:

`PKRV2008202523896.xlsx`

The XLSX workbook contains the expected `Tenor`, `Mid Rate`, and `Change`
columns and the complete canonical twenty-tenor PKRV sequence.

The XLSX file remains in its original source format.

### 18 March 2026

PakYield accepts:

`PKRV1803202624793.xls`

Despite the `.xls` extension, the source bytes are Microsoft Spreadsheet XML,
not a legacy binary XLS workbook.

The XML spreadsheet contains the expected `Tenor`, `Mid Rate`, and `Change`
structure and the complete canonical twenty-tenor PKRV sequence.

The raw artifact remains unchanged and retains its original `.xls` filename.

Selection policy:

- clean READY metadata rows are selected automatically;
- REVIEW rows require explicit evidence-based resolution;
- byte-identical duplicates use the lower metadata index as the deterministic
  selected artifact;
- a correct dataset and valid PKRV structure take precedence over misleading
  metadata or filenames;
- source-format deviations are preserved rather than converted in the raw
  layer;
- HTTP 404 metadata entries are not treated as successful acquisitions;
- exactly one artifact is selected for each approved observation date.

Result:

The approved PKRV acquisition universe contains:

- 1,159 artifacts;
- 1,159 unique observation dates;
- 1,157 CSV files;
- 1 XLSX file;
- 1 Spreadsheet XML artifact carrying an `.xls` extension;
- dates from 2022-01-04 through 2026-09-28.

Affected Components:

- PKRV bulk acquisition
- raw provenance
- anomaly resolution
- source-format routing
- later PKRV cleaning and normalization

# 84. D079 — PKRV Raw Structural Acceptance

Date: September 29, 2026
Status: ACCEPTED

Decision:

The Phase 4 PKRV metadata universe contains 1,159 approved MUFAP observation
dates covering the primary 2022-2026 sample.

Raw-source reconciliation identifies:

- 2 approved metadata dates whose MUFAP source artifacts are unavailable;
- 1,157 acquired immutable source artifacts;
- 8 acquired artifacts that are not PKRV yield curves:
  - 7 KIBOR attachments;
  - 1 PKFRV floating-rate PIB attachment.

The validated PKRV analytical source universe therefore contains 1,149
observations.

Structural validation of those 1,149 valid PKRV observations identifies:

- 1,119 full 20-tenor curves;
- 30 valid partial 14-tenor curves.

The 30 partial curves consistently contain:

- 1W;
- 2W;
- 1Y through 10Y where represented by the canonical maturity set;
- 15Y;
- 20Y.

They consistently lack:

- 1M;
- 2M;
- 3M;
- 4M;
- 6M;
- 9M.

These missing short-end observations will remain missing. PakYield will not
interpolate, synthesize, copy from adjacent dates, or otherwise manufacture the
six unavailable tenor values.

Legacy PKRV source formats are valid source observations where their historical
tenor conventions can be mapped deterministically to the canonical maturity
set.

Historical day buckets are normalized as:

- 0-7 days -> 1W;
- 8-15 days -> 2W;
- 16-30 days -> 1M;
- 31-60 days -> 2M;
- 61-90 days -> 3M;
- 91-120 days -> 4M;
- 121-180 days -> 6M;
- 181-270 days -> 9M;
- 271-365 days -> 1Y.

Two valid legacy PKRV artifacts are UTF-16 encoded and are decoded as UTF-16
based on their byte-order marks. Raw bytes remain unchanged.

The authoritative acquired-artifact structural classification is stored in:

`data/manifests/pkrv_structural_acceptance.csv`

The two unavailable MUFAP artifacts remain documented separately in:

`data/manifests/pkrv_source_gaps.csv`

Wrong-dataset acquired artifacts remain preserved in immutable raw storage and
provenance but are excluded from PKRV analysis according to:

`data/manifests/pkrv_validation_exclusions.csv`

Implications:

- Only rows classified ACCEPT in the structural acceptance manifest may enter
  PKRV yield parsing.
- PARTIAL_14 observations remain eligible for analyses whose required tenors
  are available.
- Analyses requiring a missing tenor must treat that tenor as unavailable for
  the affected date.
- Nelson-Siegel eligibility will be assessed separately using an explicit
  maturity-coverage rule.
- No source exclusion or missing tenor may be silently repaired.

# 85. D080 — PKISRV Canonical Date and Raw-Artifact Strategy

**Date:** 2026-09-30  
**Status:** ACCEPTED

For standardized PKISRV observations, the canonical observation date is the
date encoded in the MUFAP PKISRV title and file name, rather than the MUFAP API
metadata Date field.

The standardized acquisition window is frozen as:

- Start: 2025-02-03
- End: 2026-09-30
- Planned MUFAP artifacts: 407
- Unique canonical observation dates: 407
- File formats: 405 CSV, 1 XLS, 1 XLSX
- API-date/title-date mismatches: 10
- True canonical-date duplicates: 0

The following MUFAP special-format artifacts were inspected directly:

- 2025-08-20 — PKISRV2008202523897.xlsx
- 2026-03-18 — PKISRV1803202624792.xls

Both are valid MUFAP sovereign Islamic-security publications, but neither
contains the standardized five-tenor PKISRV benchmark block
(1M, 3M, 6M, 9M, 1Y).

These raw files will be preserved unchanged. No tenor values will be inferred,
interpolated, manufactured, or derived from their instrument-level data.

PakDataHub remains a secondary machine-readable standardized PKISRV source for
cross-source validation and, where independently verified, possible recovery of
a benchmark observation omitted from a MUFAP attachment. Any such recovery must
retain distinct provenance and must not be represented as coming from the MUFAP
raw attachment.

The complete 407-artifact MUFAP raw archive will be acquired before the final
structural census determines how many dates contain the standardized benchmark
block.

# 86. D081 — PKISRV Primary Source, Validation and Missing-Observation Policy

**Date:** 2026-09-30
**Status:** ACCEPTED

Direct MUFAP publications are the primary acquisition source for standardized
PKISRV observations.

The frozen standardized MUFAP archive covers 2025-02-03 through 2026-09-30:

- 407 authoritative MUFAP publication dates.
- 403 publications contain the complete standardized five-tenor benchmark
  block: 1M, 3M, 6M, 9M and 1Y.
- 4 publications omit the standardized benchmark block entirely:
  - 2025-03-07
  - 2025-08-20
  - 2026-03-18
  - 2026-03-27
- No partial benchmark blocks were found.
- No duplicate standardized tenors were found.
- No unparseable standardized benchmark rates were found.

The four missing standardized observations remain missing. They will not be
interpolated, forward-filled, backfilled, inferred from instrument prices or
otherwise manufactured.

PakDataHub is retained as a secondary machine-readable validation source, not
as the primary acquisition source.

For the accessible overlap:

- Each PakDataHub tenor contained 235 observations.
- All five tenor date sets were identical.
- The accessible overlap ran from 2025-09-30 through 2026-09-29.
- 235 dates were common to accepted MUFAP observations and PakDataHub.
- 1,175 date-tenor values were compared.
- All 1,175 values matched exactly.
- There were zero value mismatches.
- Maximum absolute difference was zero.
- PakDataHub supplied zero dates absent from the accepted MUFAP overlap.
- MUFAP contained 11 accepted dates not available through PakDataHub in the
  compared window.

Direct targeted PakDataHub probing also confirmed that 2026-03-18 and
2026-03-27 contain no standardized observations in any of the five tenors.

The 2025-03-07 and 2025-08-20 omissions predate the currently accessible
PakDataHub history window, so no PakDataHub recovery claim is made for those
dates.

Accordingly:

1. MUFAP direct raw artifacts are authoritative for acquisition.
2. PakDataHub is used for secondary overlap validation.
3. Canonical PKISRV observation dates come from the MUFAP title/file date.
4. Only COMPLETE_5 MUFAP records enter the standardized analytical PKISRV
   dataset.
5. The four source-level omissions remain explicit missing observations.
6. No synthetic recovery, interpolation or silent imputation is permitted.

# 87. D082 — SBP Policy-Rate Raw Source and Validation Policy

**Date:** 2026-09-30
**Status:** ACCEPTED

The official State Bank of Pakistan EasyData series
`TS_GP_IR_SIRPR_AH.SBPOL0030` is the authoritative v1 source for the
State Bank of Pakistan policy target rate.

Automated command-line access to the EasyData series page was blocked by a
Cloudflare challenge. The official public EasyData browser interface was
therefore used to download the source CSV. The browser-downloaded artifact
was preserved byte-for-byte in the raw layer.

Frozen raw artifact:

- Raw path: `data/raw/sbp/policy_rate/data_series.csv`
- Format: CSV
- Size: 6,559 bytes
- SHA-256:
  `4dbf6d69a8ece64bd45e9f3fc8bdb0424d77ded1169b04e68696c5ee8d702420`
- Series key: `TS_GP_IR_SIRPR_AH.SBPOL0030`
- Series name: `SBP Policy (Target) Rate`
- Unit: Percent
- Source observations: 39
- First chronological observation: 2015-05-25
- Last chronological observation: 2026-04-28
- Unique observation dates: 39
- Duplicate observation dates: 0
- Source-status values: 39 `Normal`
- Missing observation values: 0
- Structural review records: 0

The official source file is ordered in descending observation-date order and
is retained unchanged. The analytical layer may reorder observations
chronologically, but the raw source artifact must never be rewritten for
sorting, formatting or normalization.

The EasyData policy-rate series is an event-based rate-history series. Its
observation dates must not automatically be treated as the complete set of
Monetary Policy Committee meeting or announcement dates. MPC event dates and
policy decisions will be acquired separately from official SBP monetary
policy statement material.

For PakYield's core 2022-2026 empirical period, the source contains 17
policy-rate observations. The final available raw-series observation is
2026-04-28 at 11.5 percent.

Accordingly:

1. SBP EasyData is the authoritative policy-rate source for v1.
2. The frozen browser export is the immutable raw artifact.
3. All 39 source observations are structurally accepted.
4. Policy-rate observation dates remain distinct from the separately acquired
   MPC event calendar.
5. No missing dates or rates may be manufactured, interpolated or silently
   inferred.
6. Later transformations must preserve raw provenance and source values.
