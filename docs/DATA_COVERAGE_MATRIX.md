# PakYield Lab — Data Coverage Matrix

## 1. Purpose

This document consolidates the Phase 2 feasibility findings for all mandatory
PakYield datasets before final sample-period and tenor decisions are made.

---

# 2. Core Dataset Coverage

| Dataset | Authority | Acquisition Source | Frequency | Confirmed Coverage | Structure | Status |
|---|---|---|---|---|---|---|
| PKRV | MUFAP | Current MUFAP pricing interface | Daily / available market observations | Reliably downloadable from Jan 29, 2020 onward | Sovereign benchmark tenor curve; schema changes exist | PASS |
| PKISRV | MUFAP | PakDataHub for standardized tenor series; MUFAP for validation | Daily | Standardized tenor series from Feb 3, 2025 onward | 1M, 3M, 6M, 9M, 1Y | PASS |
| SBP Policy Rate | State Bank of Pakistan | SBP EasyData | Event-based / as needed | May 25, 2015 to current available change | Official rate-change observations | PASS |
| MPC Events | State Bank of Pakistan | SBP Monetary Policy Statements archive | Event-based | Covers PakYield research period | HIKE / CUT / HOLD statements | PASS |
| CPI Inflation | Pakistan Bureau of Statistics | PBS historical CPI publications | Monthly | Covers PakYield research period | National CPI index and YoY inflation | PASS |

---

# 3. PKRV Coverage

## Confirmed Directly Obtainable Period

Current official MUFAP files are reliably obtainable from:

January 29, 2020 onward.

Historical MUFAP archive pages show earlier observations, but older file links
are not reliably retrievable.

Therefore the provisional core PKRV period is:

2020–2026

subject to detailed publication-gap analysis during ingestion.

## Observed Maturities

A modern PKRV file contains:

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

Historical schema variation exists.

---

# 4. PKISRV Coverage

## Standardized Comparative Series

The standardized tenor-based PKISRV series is available from approximately:

February 3, 2025 onward.

Core tenors:

- 1M
- 3M
- 6M
- 9M
- 1Y

Earlier MUFAP files primarily contain instrument-level GOP Ijarah Sukuk
revaluation information and dealer quotes rather than a directly comparable
generic tenor curve.

Therefore the provisional PKRV/PKISRV comparative period is:

February 2025–2026.

---

# 5. PKRV / PKISRV Common Tenors

The directly comparable tenor intersection is provisionally:

- 1M
- 3M
- 6M
- 9M
- 1Y

These will be used for:

- PKISRV-PKRV spread analysis;
- co-movement analysis;
- rolling correlations;
- H2;
- H3.

No synthetic long-end PKISRV tenors will be created.

---

# 6. SBP Policy Rate Coverage

Official SBP policy-target-rate series:

Start:

May 25, 2015

Latest verified rate-change observation:

April 28, 2026

Unit:

Percent

The series contains 39 official rate observations in the downloaded feasibility
file.

This fully covers the proposed PakYield empirical period.

---

# 7. MPC Event Coverage

The official SBP Monetary Policy Statements archive provides event-level
monetary-policy decisions throughout the proposed PakYield period.

Events include:

- HIKE;
- CUT;
- HOLD.

The MPC event dataset will be maintained separately from the policy-rate-change
series.

This is necessary because HOLD decisions do not create a new rate level.

---

# 8. CPI Coverage

Pakistan Bureau of Statistics provides monthly National CPI data under the
2015-16 base.

The required research period is covered.

Primary variable:

cpi_inflation_yoy_pct

Secondary retained variable:

National CPI index.

Frequency:

Monthly.

---

# 9. Frequency Map

| Dataset | Frequency |
|---|---|
| PKRV | Daily / available observation |
| PKISRV | Daily / available observation |
| Policy rate | Event-based |
| MPC decisions | Event-based |
| CPI | Monthly |

Different frequencies must be aligned explicitly rather than merged naïvely.

---

# 10. Provisional Analytical Samples

## Sample A — Conventional Yield-Curve Research

Expected period:

2020–2026

Datasets:

- PKRV
- SBP policy rate
- MPC events
- CPI where monthly alignment is required

Uses:

- RQ1
- RQ2
- H1
- curve evolution
- event-study analysis
- Nelson-Siegel

---

## Sample B — Conventional / Islamic Comparison

Expected period:

February 2025–2026

Datasets:

- PKRV
- PKISRV

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
- spread analysis
- rolling co-movement

---

## Sample C — Monthly Macroeconomic Analysis

Expected period:

2020–2026

Datasets:

- selected PKRV monthly transformation
- SBP policy rate
- National CPI YoY inflation

Uses:

- RQ4
- H4 where policy regimes are involved
- econometric analysis

The exact monthly yield transformation remains deferred until implementation.

---

# 11. Optional Datasets Excluded from v1

The following are not required for the core v1 project:

- PKR/USD;
- MTB auction data;
- PIB auction data;
- Ijarah Sukuk auction data;
- government-security trading volume.

They may be added later as extensions.

---

# 12. Phase 2 Coverage Conclusion

All mandatory PakYield data categories have a feasible acquisition path.

No mandatory research question currently depends on an unavailable dataset.

Remaining Phase 2 decisions:

1. final research sample periods;
2. final PKRV core tenor universe;
3. final PKRV/PKISRV common tenor universe;
4. exact econometric monthly alignment convention;
5. final Phase 2 acceptance audit.

# 13. Final Tenor Decision

## PKRV Full Standardized Universe

1W, 2W, 1M, 2M, 3M, 4M, 6M, 9M, 1Y, 2Y, 3Y, 4Y, 5Y, 6Y,
7Y, 8Y, 9Y, 10Y, 15Y, 20Y.

## PKRV Focal Research Tenors

3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, 15Y, 20Y.

## PKRV / PKISRV Common Tenors

1M, 3M, 6M, 9M, 1Y.

## Preferred Term Spreads

10Y-2Y
10Y-1Y
5Y-1Y
3Y-3M

Tenors are used only when actually available in the underlying observation.
No missing maturity is synthetically created.