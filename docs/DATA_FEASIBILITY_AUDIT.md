# PakYield Lab — Data Feasibility Audit

## Phase 2 Status

**Current Phase:** Phase 2 — Data Feasibility Audit
**Current Batch:** Batch 2.3 — SBP Policy Rate History
**Status:** IN PROGRESS

---

# 1. Purpose

The purpose of Phase 2 is to determine which proposed datasets are actually available, historically consistent, sufficiently complete, and practically obtainable before production ingestion code or the final analytical database is created.

No dataset should be accepted merely because a webpage or secondary source claims that it exists.

The feasibility audit should examine:

* source authority;
* date coverage;
* frequency;
* maturity or variable coverage;
* file format;
* accessibility;
* missingness;
* structural changes;
* reproducibility;
* licensing or usage limitations where relevant;
* suitable fallback sources.

---

# 2. Source Priority

PakYield will prefer sources in the following order:

1. authoritative primary publisher;
2. official government or regulatory source;
3. recognized industry body;
4. reputable secondary financial-data publisher;
5. third-party API or aggregator.

Secondary sources may be used for validation and gap investigation but should not silently replace an available authoritative source.

---

# 3. Dataset F01 — PKRV

## Dataset Identity

**Dataset:** Pakistan Revaluation Rates
**Abbreviation:** PKRV
**Research Role:** Conventional Pakistan sovereign benchmark yield curve
**Provisional Primary Publisher:** Mutual Funds Association of Pakistan (MUFAP)
**Status:** FEASIBILITY UNDER REVIEW

---

# 4. Primary-Source Discovery

MUFAP maintains a historical section titled:

> Daily PKRV & PKISRV Rates

The legacy archive exposes yearly navigation for PKRV data including:

```text
2012
2013
2014
2015
2016
2017
2018
2019
2020
2021
2022
2023
2024
```

Individual year/month pages contain date-specific PKRV links.

Historical daily observations are therefore confirmed to exist.

---

# 5. Confirmed Historical Evidence

Daily PKRV entries have been observed in MUFAP archive pages for dates in at least:

```text
2012
2013
2014
2016
2018
2019
2022
2024
```

This is sufficient to establish that the archive is genuinely daily rather than merely annual or monthly.

The Phase 2 audit must still determine the completeness of each year.

---

# 6. 2012 Evidence

MUFAP's June 2012 historical page contains separate PKRV observations for individual dates throughout the month.

Therefore:

```text
PKRV history by 2012: CONFIRMED
```

This does not yet establish that every month of 2012 is complete or usable.

---

# 7. 2024 Evidence

The MUFAP 2024 historical archive contains daily PKRV entries through at least June 7, 2024 on the legacy archive page examined during Batch 2.1.

The page also exposes separate PKISRV and PKFRV links.

---

# 8. Apparent Raw File Format

The historical PKRV links observed in the MUFAP archive point to files with the extension:

```text
.csv
```

A representative naming pattern is:

```text
PKRVDDMMYYYY.csv
```

Example conceptual filename:

```text
PKRV07062024.csv
```

This suggests that the original archive was designed around machine-readable daily CSV files.

However, actual accessibility must be tested independently.

---

# 9. Accessibility and Site Migration

Manual browser testing established that the historical download links exposed through the legacy MUFAP website are no longer reliable.

Representative legacy-file tests for:

* 2024;
* 2019;
* 2012;

returned HTTP 404 errors.

The legacy archive pages remain useful for confirming that historical daily PKRV observations existed, but their historical file links should not be treated as the production acquisition source.

A current MUFAP pricing page was subsequently identified at the official MUFAP website under:

`WebRegulations → Pricing → PKRV/PKISRV/PKFRV`

Manual browser inspection confirmed that historical CSV data corresponding to the tested periods are available through the current MUFAP website.

Therefore the working interpretation is that MUFAP migrated or re-hosted the PKRV/PKISRV/PKFRV historical data while leaving parts of the legacy archive publicly indexed.

The current MUFAP website should be treated as the primary acquisition interface.

The legacy MUFAP website should be treated as historical/archive evidence only.

---

# 10. Current MUFAP Source Verification

The current MUFAP pricing interface provides historical PKRV/PKISRV/PKFRV downloads.

Manual browser testing has confirmed availability for representative historical periods:

```text
2024 — AVAILABLE
2019 — AVAILABLE
2012 — AVAILABLE
```

This establishes that historical PKRV acquisition from the current authoritative MUFAP website is practically feasible.

Before Batch 2.1 is fully closed, representative downloaded CSV files must be inspected to determine:

* filename convention;
* column/header structure;
* date representation;
* tenor structure;
* yield units;
* presence of PKRV-only versus combined data;
* consistency across 2012, 2019, and 2024;
* whether the maturity universe changed across time.

No bulk download should begin until these structural checks are completed.

---

# 11. Current Maturity Evidence

Contemporary secondary PKRV publications show a broad curve containing maturities such as:

```text
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
```

Some historical sources may also contain additional maturities such as 30Y.

The final tenor universe remains unresolved until actual primary-source files are inspected across multiple years.

---

# 12. Units

Contemporary PKRV publications display yields in percentage terms.

The PakYield working convention remains:

```text
12.50 = 12.50%
```

Changes and spreads will later be expressed in basis points.

Actual MUFAP file headers and values must be inspected before confirming ingestion assumptions.

---

# 13. Secondary Validation Sources

Potential validation or fallback sources identified during Batch 2.1 include:

## Business Recorder

Provides dated PKRV tables with broad maturity coverage.

Potential role:

```text
cross-check
gap investigation
current-data verification
```

Not currently designated as the primary source.

## Mettis Global

Provides current PKRV maturity/value tables.

Potential role:

```text
cross-check
latest-value validation
```

Not currently designated as the primary source.

## PakDataHub

Advertises programmatic daily PKRV series across multiple maturities, with coverage from 2022 onward for many PKRV series.

Potential role:

```text
fallback API
cross-check
recent-data supplement
```

Not currently designated as the authoritative research source.

---

# 14. Source-Quality Limitation

MUFAP itself states that it collects and publishes PKRV, PKISRV, and PKFRV rates as received from third parties and does not warrant their timeliness, accuracy, or completeness.

This limitation must be preserved in the final research methodology and data-source discussion.

MUFAP publication should therefore be treated as an authoritative industry source, but not as error-free ground truth.

---

# 15. Initial PKRV Feasibility Assessment

Current findings:

```text
Dataset existence:               CONFIRMED
Historical archive:              CONFIRMED
Daily observations:              CONFIRMED
Coverage reaching 2012:          CONFIRMED
Recent benchmark activity:       CONFIRMED
Broad maturity structure:        CONFIRMED
CSV-style historical links:      CONFIRMED
Bulk download reliability:       UNRESOLVED
Browser accessibility:           TEST REQUIRED
Historical completeness:         UNRESOLVED
Historical tenor consistency:    UNRESOLVED
Final sample start:              DEFERRED
Final sample end:                DEFERRED
Final tenor universe:            DEFERRED
```

---

# 16. Provisional PKRV Decision

**Status:** DIRECTLY FEASIBLE — SCHEMA VERIFICATION PENDING
---

# 17. Do Not Do Yet

During Batch 2.1:

* do not bulk-download the archive;
* do not scrape hundreds of files;
* do not write production ingestion code;
* do not create the SQLite database;
* do not select the final sample period;
* do not select the final maturity set;
* do not repair missing observations;
* do not use secondary sources to silently fill MUFAP gaps.

The objective is feasibility assessment only.

---

# 18. Manual Test Results

## Test A — 2024

**Archive page accessible:** NOT YET TESTED
**PKRV link accessible:** NOT YET TESTED
**Download successful:** NOT YET TESTED
**Format observed:** NOT YET TESTED
**Tenors observed:** NOT YET TESTED
**Notes:** NOT YET TESTED

## Test B — 2019

**Archive page accessible:** NOT YET TESTED
**PKRV link accessible:** NOT YET TESTED
**Download successful:** NOT YET TESTED
**Format observed:** NOT YET TESTED
**Tenors observed:** NOT YET TESTED
**Notes:** NOT YET TESTED

## Test C — 2012

**Archive page accessible:** NOT YET TESTED
**PKRV link accessible:** NOT YET TESTED
**Download successful:** NOT YET TESTED
**Format observed:** NOT YET TESTED
**Tenors observed:** NOT YET TESTED
**Notes:** NOT YET TESTED

---

# 19. Batch 2.1 Exit Requirement

Batch 2.1 may be closed only after representative primary-source access has been tested sufficiently to classify PKRV acquisition as one of:

```text
DIRECTLY FEASIBLE
FEASIBLE WITH LEGACY-SOURCE WORKAROUND
FEASIBLE WITH DOCUMENTED SECONDARY FALLBACK
NOT PRACTICALLY FEASIBLE
```

No final classification has yet been made.

# 20. PKRV Browser and Schema Findings

Manual testing of MUFAP's current official pricing interface established that
reliably downloadable PKRV files are available from January 29, 2020 onward.

The legacy MUFAP archive contains historical listings extending before this
date and into earlier years, but representative legacy download links are no
longer reliably accessible.

Therefore:

- historical existence before 2020 is confirmed;
- reliable current acquisition before January 29, 2020 is not confirmed;
- the provisional directly obtainable PKRV sample begins January 29, 2020.

## Missing Dates

The MUFAP series does not contain an observation for every calendar date.

This is not automatically considered missing-data failure because the series
is based on available market/publication observations.

Potential reasons include:

- weekends;
- public holidays;
- non-publication dates;
- genuine archive gaps.

No missing PKRV observation will automatically be replaced by zero,
forward-filled, or interpolated.

Later coverage analysis will calculate actual publication coverage and identify
unusually long gaps.

## Observed Schema A — Final/Tidy PKRV File

A June 7, 2024 file uses:

- Tenor
- Mid Rate
- Change

Observed maturities include:

1W, 2W, 1M, 2M, 3M, 4M, 6M, 9M, 1Y, 2Y, 3Y, 4Y, 5Y, 6Y,
7Y, 8Y, 9Y, 10Y, 15Y, 20Y.

## Observed Schema B — Contributor/Matrix-Style File

A January 19, 2024 PKRV-labelled file uses a structurally different format.

It contains maturity buckets and multiple contributor/source columns rather
than the simple Tenor / Mid Rate / Change structure.

The meaning of these contributor columns will not be inferred without evidence.

This confirms that historical MUFAP PKRV files cannot be assumed to have one
uniform schema.

Production ingestion will therefore require schema detection and normalization.

## Revised PKRV Feasibility Classification

**DIRECTLY FEASIBLE FROM 2020 ONWARD — SCHEMA NORMALIZATION REQUIRED**

The exact project sample start remains provisional until PKISRV and other core
datasets are audited.

# 21. Dataset F02 — PKISRV

## Dataset Identity

**Dataset:** Pakistan Islamic Sovereign Revaluation Rates  
**Abbreviation:** PKISRV  
**Research Role:** Shariah-compliant Pakistan sovereign benchmark yield curve  
**Provisional Primary Publisher:** Mutual Funds Association of Pakistan (MUFAP)  
**Status:** FEASIBILITY UNDER REVIEW

---

# 22. Research Role

PKISRV is required for the central comparative component of PakYield.

The intended analysis will eventually compare PKISRV and PKRV at compatible
dates and maturities.

Potential later analyses include:

- benchmark-level comparison;
- PKISRV-PKRV spread;
- rolling co-movement;
- maturity-specific spread behavior;
- MPC announcement-window comparison;
- Islamic curve shape.

No such empirical analysis will begin until source feasibility and comparability
are established.

---

# 23. Primary Source

The primary candidate source is MUFAP's current official:

`PKRV/PKISRV/PKFRV`

pricing interface.

The legacy MUFAP archive confirms that PKISRV was historically published
alongside PKRV.

However, legacy download links have already been shown to be unreliable.

Therefore:

- current MUFAP website = primary acquisition candidate;
- legacy MUFAP website = historical-reference evidence only.

---

# 24. Current Economic Relevance

Current Pakistani asset-management documentation continues to use PKISRV as
a benchmark component.

Examples observed in current industry materials include:

- 3-month PKISRV;
- 6-month PKISRV;
- 12-month PKISRV.

This establishes that PKISRV remains an active market benchmark.

The complete maturity universe must still be verified from MUFAP source files.

---

# 25. Secondary Validation Evidence

A secondary data provider identifies daily MUFAP-sourced PKISRV series
including:

- 1M;
- 3M;
- 6M;
- 9M;
- 1Y.

Its visible history for these series begins in February 2025.

This source may later be used for cross-checking but does not determine
PakYield's authoritative sample period.

---

# 26. Key Feasibility Questions

FEASIBLE WITH DOCUMENTED SECONDARY ACQUISITION

Batch 2.2 must establish:

1. earliest PKISRV date currently downloadable from MUFAP;
2. latest available date;
3. file format;
4. file naming convention;
5. schema stability through time;
6. tenor universe;
7. historical changes in tenor universe;
8. overlap with PKRV;
9. whether missing dates mirror PKRV publication dates;
10. whether direct acquisition is sufficiently reproducible.

---

# 27. PKISRV Manual Tests

## Test A — Earliest Current MUFAP PKISRV

**Earliest date visible:** NOT YET TESTED  
**File downloads:** NOT YET TESTED  
**Filename:** NOT YET TESTED  
**Schema:** NOT YET TESTED  
**Tenors:** NOT YET TESTED  
**Notes:** NOT YET TESTED

## Test B — 2024 PKISRV

Target date where possible:

**June 7, 2024**

**File downloads:** NOT YET TESTED  
**Filename:** NOT YET TESTED  
**Schema:** NOT YET TESTED  
**Tenors:** NOT YET TESTED  
**Notes:** NOT YET TESTED

## Test C — Recent 2026 PKISRV

**Date tested:** NOT YET TESTED  
**File downloads:** NOT YET TESTED  
**Filename:** NOT YET TESTED  
**Schema:** NOT YET TESTED  
**Tenors:** NOT YET TESTED  
**Notes:** NOT YET TESTED

---

# 28. Comparability Rule

PKISRV and PKRV must be compared only when both observations exist for the
same date and a genuinely comparable tenor.

PakYield will not fabricate a PKRV/PKISRV match by silently substituting:

- nearby maturities;
- interpolated maturities;
- previous-day observations;
- unrelated instrument yields.

Any later interpolation must be separately justified and clearly labeled.

---

# 29. Provisional PKISRV Status

Current status:

**UNDER REVIEW**

No final PKISRV sample period or tenor universe has yet been selected.

FEASIBLE WITH DOCUMENTED SECONDARY ACQUISITION

# 31. Dataset F03 — SBP Policy Rate History

## Dataset Identity

**Dataset:** State Bank of Pakistan Policy (Target) Rate  
**Publisher:** State Bank of Pakistan  
**Primary Source:** SBP EasyData  
**Frequency:** As-needed / rate-change events  
**Unit:** Percent  
**Available Since:** May 25, 2015  
**Status:** FEASIBILITY UNDER REVIEW

---

# 32. Research Role

The SBP policy-rate series will provide the official monetary-policy rate
level used throughout PakYield.

It will support:

- monetary-policy regime classification;
- policy-rate change calculations;
- macroeconomic analysis;
- event-study metadata;
- yield-versus-policy-rate visualizations.

The policy-rate series is distinct from the MPC event dataset.

A policy-rate history records effective rate levels and changes.

An MPC event dataset records every policy meeting, including HIKE, CUT,
and HOLD decisions.

---

# 33. Source Authority

The State Bank of Pakistan is the authoritative source for Pakistan's
policy rate.

The EasyData series is therefore preferred over secondary financial-data
providers.

No secondary source is required for the core policy-rate history if
EasyData acquisition remains accessible.

---

# 34. Series Definition

SBP EasyData identifies the series as:

State Bank of Pakistan's Policy (Target) Rate

The target rate was introduced with effect from May 25, 2015.

The series is expressed in percent and updates when the policy-rate level
changes.

---

# 35. Intended Canonical Structure

The processed PakYield policy-rate event table should eventually contain:

date
policy_rate_pct

Example conceptual structure:

2015-05-25 | rate
2020-03-XX | rate
2024-XX-XX | rate
2026-04-28 | 11.50

Exact historical values will be ingested from the authoritative source
rather than manually entered from this document.

---

# 36. Daily Policy-Rate State

The source series is event-based.

For analyses requiring a daily policy-rate value, PakYield may construct
a step-function series in which each officially announced/effective rate
remains in force until the next effective rate change.

Conceptually:

policy_rate(date t)
=
most recent official policy rate effective on or before t

This transformation is appropriate for a policy variable that remains in
force between official changes.

The generated daily rows must be identifiable as derived observations
rather than new SBP announcements.

---

# 37. Monthly Policy-Rate State

For monthly macroeconomic analysis, PakYield may use a documented monthly
representation such as:

- month-end policy rate;
- rate change during month;
- cumulative policy-rate change during month.

The final convention will be chosen during the analytical-design phase.

---

# 38. Current 2026 Validation

SBP's current monetary-policy page reports a policy rate of 11.50 percent.

The September 14, 2026 MPC meeting kept the rate unchanged at 11.50
percent.

Therefore an unchanged MPC meeting does not necessarily create a new
observation in an as-needed rate-change series.

This distinction is important for the later MPC event dataset.

---

# 39. Initial Feasibility Assessment

Current findings:

Official publisher:                 CONFIRMED
Official time series:               CONFIRMED
Machine-readable system:            CONFIRMED
Unit:                               PERCENT
Frequency:                          AS NEEDED
Available since 2015:               CONFIRMED
Coverage for PakYield sample:       CONFIRMED
Secondary source required:          NO
Download structure:                 MANUAL TEST REQUIRED

Provisional classification:

DIRECTLY FEASIBLE

# 39. SBP Policy Rate Feasibility Result

Manual testing confirmed that SBP EasyData provides a directly downloadable
CSV for the official State Bank of Pakistan Policy (Target) Rate.

Observed CSV fields are:

- Dataset
- Series Key
- Series
- Observation Date
- Observation Value
- Unit
- Observation Status
- Observation Status Comment

The series key is:

`TS_GP_IR_SIRPR_AH.SBPOL0030`

The unit is:

`Percent`

The downloaded series is structured as policy-rate change observations rather
than one row per calendar day.

The latest downloaded observation is:

`28-Apr-2026 | 11.5 percent`

The series is sorted in reverse chronological order in the downloaded file.

## Intended Processing

The original event-based series will be preserved.

Where daily alignment with sovereign yields is required, PakYield may derive a
step-function daily policy-rate series in which the most recent effective
official policy rate remains in force until the next rate change.

This derived series must remain distinguishable from the original SBP
observations.

## Classification

**DIRECTLY FEASIBLE — OFFICIAL MACHINE-READABLE SOURCE**

No secondary provider is required for the core policy-rate history.

# 40. Dataset F04 — SBP MPC Events

## Dataset Identity

**Dataset:** Monetary Policy Committee Decisions  
**Publisher:** State Bank of Pakistan  
**Primary Source:** SBP Monetary Policy Statements archive  
**Frequency:** Event-based  
**Status:** FEASIBILITY UNDER REVIEW

---

# 41. Research Role

The MPC event dataset will provide the event dates required for PakYield's
announcement-window analysis.

Unlike the SBP policy-rate history, this dataset must include every MPC
decision, including meetings where the policy rate was unchanged.

Each event should eventually contain:

- event_id;
- announcement_date;
- policy_rate_before;
- policy_rate_after;
- policy_rate_change_bps;
- decision_type;
- source_url;
- source_document;
- notes.

Decision types:

- HIKE
- CUT
- HOLD

---

# 42. Primary Source

SBP maintains an official archive of Monetary Policy Statements.

SBP states that a Monetary Policy Statement is issued following each MPC
meeting and explains the decision taken at that meeting.

The archive contains historical statements across the PakYield research
period, including 2020 onward.

---

# 43. Preliminary Coverage Evidence

The official archive contains 2020 MPC statements including:

- January 28, 2020;
- March 17, 2020;
- March 24, 2020;
- April 16, 2020;
- May 15, 2020;
- June 25, 2020;
- September 21, 2020;
- November 23, 2020.

The archive also contains statements throughout subsequent years.

This confirms that event-level MPC history is available independently of
the policy-rate change series.

---

# 44. Required Event Classification

For each statement, PakYield will identify:

policy_rate_before
policy_rate_after
policy_rate_change_bps
decision_type

Classification rule:

policy_rate_after > policy_rate_before → HIKE

policy_rate_after < policy_rate_before → CUT

policy_rate_after = policy_rate_before → HOLD

The actual decision should also be verified against the wording of the
official statement.

---

# 45. Announcement Date

The date of the official Monetary Policy Statement will be treated as the
provisional announcement date.

Where necessary, announcement timing relative to PKRV publication will be
investigated before event-window calculations.

---

# 46. MPC Archive Feasibility Questions

Batch 2.4 must establish:

1. whether the archive covers the full intended research period;
2. whether statement dates are clearly available;
3. whether each statement identifies the decision;
4. whether HOLD events are included;
5. whether documents remain directly downloadable;
6. whether unusual emergency/inter-meeting actions exist;
7. whether the event list can be reconstructed reproducibly.

---

# 47. Provisional Classification

Current status:

**LIKELY DIRECTLY FEASIBLE — REPRESENTATIVE DOCUMENT TEST REQUIRED**

# 48. MPC Archive Verification Result

Representative manual verification of the official State Bank of Pakistan
Monetary Policy Statements archive was completed.

Three representative MPC statements were inspected:

## Test A — January 28, 2020

Official statement accessible: YES  
Decision classification: VERIFIED  
Policy-rate decision identifiable: YES

## Test B — January 23, 2023

Official statement accessible: YES  
Decision classification: HIKE  
Policy-rate decision identifiable: YES

The statement confirms that the policy rate was increased.

## Test C — September 14, 2026

Official statement accessible: YES  
Decision classification: HOLD  
Policy-rate decision identifiable: YES

The statement confirms that the policy rate was kept unchanged.

## Feasibility Conclusion

The official SBP Monetary Policy Statements archive provides sufficient
event-level information to reconstruct PakYield's MPC event dataset.

The archive supports identification of:

- announcement date;
- policy-rate decision;
- HIKE / CUT / HOLD classification;
- resulting policy rate;
- official source document.

HOLD decisions are available even when no new observation appears in the
SBP EasyData policy-rate-change series.

The policy-rate history and MPC event history will therefore be maintained
as separate but related datasets.

## Classification

**DIRECTLY FEASIBLE — OFFICIAL EVENT ARCHIVE**

# 49. Dataset F05 — Pakistan CPI Inflation

## Dataset Identity

**Dataset:** Consumer Price Index  
**Primary Authority:** Pakistan Bureau of Statistics  
**Frequency:** Monthly  
**Preferred Measure:** National headline CPI year-on-year inflation  
**Base Year:** 2015-16  
**Status:** FEASIBILITY UNDER REVIEW

---

# 50. Research Role

CPI inflation will provide the principal inflation variable for PakYield's
macroeconomic analysis.

Potential uses include:

- monetary-policy context;
- yield/inflation visualizations;
- monthly econometric analysis;
- interpretation of monetary-policy regimes.

The primary variable is expected to be:

`cpi_inflation_yoy_pct`

PakYield may additionally retain the National CPI index level where available.

---

# 51. Source Authority

Pakistan Bureau of Statistics is the authoritative source for Pakistan CPI.

PBS publishes:

- historical CPI indices and growth rates;
- monthly CPI reports;
- National, Urban, and Rural CPI information;
- monthly and year-on-year changes.

PakYield will prioritize National headline CPI.

Weekly SPI will not substitute for monthly CPI.

---

# 52. Base-Year Convention

The intended project period uses CPI with base year:

`2015-16 = 100`

The project should avoid silently mixing CPI series based on different base
years.

If earlier historical series use another base year, any use of those series
must be documented.

---

# 53. Frequency

CPI is monthly.

PakYield will not repeat a monthly CPI observation across every daily yield
row and then treat those repeated values as independent observations.

Monthly econometric analysis will align CPI with an explicitly constructed
monthly yield dataset.

---

# 54. Acquisition Candidates

## Candidate A — PBS Direct

Preferred because PBS is the original statistical authority.

Required checks:

- historical coverage;
- National CPI availability;
- downloadable format;
- index and YoY availability;
- consistency of base year.

## Candidate B — SBP EasyData

Acceptable official dissemination route if the series is identified as
PBS-sourced.

Advantages may include:

- standardized time-series structure;
- CSV download;
- explicit dates;
- units;
- source metadata.

The underlying statistical authority would remain PBS.

---

# 55. Feasibility Questions

Batch 2.5 must establish:

1. whether monthly National CPI is downloadable;
2. earliest usable date;
3. latest available date;
4. whether index level is supplied;
5. whether YoY inflation is supplied directly;
6. whether the base is consistently 2015-16;
7. file format;
8. source metadata;
9. whether one continuous series covers the PakYield sample.

---

# 56. Provisional Classification

**LIKELY DIRECTLY FEASIBLE — DOWNLOAD TEST REQUIRED**

# 57. CPI Feasibility Result

Manual inspection confirmed that the Pakistan Bureau of Statistics historical
price-statistics publication contains machine-readable monthly CPI tables.

The official historical publication contains:

- National CPI index;
- Urban CPI index;
- Rural CPI index;
- WPI;
- National year-on-year inflation;
- Urban year-on-year inflation;
- Rural year-on-year inflation;
- WPI year-on-year inflation.

The data use the 2015-16 base and provide sufficient historical coverage for
PakYield's expected 2020-2026 research period.

The historical file contains National CPI index observations through at least
June 2026.

PBS also publishes current monthly CPI reports for subsequent months.

## Acquisition Decision

PakYield will use PBS directly as both:

- the authoritative statistical source; and
- the primary CPI acquisition source.

SBP EasyData may be used later as a validation source if service availability
permits, but it is not required for the core project.

The primary macroeconomic inflation variable will be:

`cpi_inflation_yoy_pct`

Frequency:

`Monthly`

Definition:

National headline CPI year-on-year percentage change.

Base:

`2015-16 = 100`

The National CPI index level will also be retained so that published YoY
inflation can be independently validated using the underlying index.

## Classification

**DIRECTLY FEASIBLE — OFFICIAL PBS SOURCE, PDF TABLE EXTRACTION REQUIRED**

# 57. CPI Feasibility Result

Manual inspection confirmed that the Pakistan Bureau of Statistics historical
price-statistics publication contains monthly CPI tables covering the PakYield
research period.

The official PBS publication contains:

- National CPI index;
- Urban CPI index;
- Rural CPI index;
- WPI;
- National year-on-year inflation;
- Urban year-on-year inflation;
- Rural year-on-year inflation;
- WPI year-on-year inflation.

The series uses the 2015-16 base.

The primary PakYield inflation variable will be:

`cpi_inflation_yoy_pct`

Frequency:

`Monthly`

Definition:

National headline CPI year-on-year percentage change.

The National CPI index level will also be retained for validation.

SBP EasyData was investigated as a possible machine-readable dissemination
route, but service availability was unreliable during the feasibility audit.

PakYield will therefore use PBS directly as the authoritative acquisition
source.

Historical PBS PDF tables will later be extracted programmatically and
validated against the published CPI index and year-on-year inflation values.

## Classification

**DIRECTLY FEASIBLE — OFFICIAL PBS SOURCE, PDF TABLE EXTRACTION REQUIRED**