# PakYield Lab — Phase 14 Manual UI QA

**Phase:** 14 — UI/UX Polish  
**Status:** MANUAL VERIFICATION PENDING  
**Application entrypoint:** `app/Home.py`

## Purpose

This document records the final manual user-interface acceptance review before
PakYield advances to the master Phase 15 full testing and audit.

Automated tests cannot prove visual hierarchy, readability, tooltip quality,
browser responsiveness, or whether a first-time visitor can understand the
application. These items therefore require direct browser inspection.

## Research-integrity boundary

Manual UI QA must not change validated calculations or analytical contracts.

Do not:

- invent missing observations;
- replace missing values with zero;
- infer unavailable values visually;
- describe PKRV/PKISRV numerical differences as Islamic, Sukuk, or Shariah
  premiums or discounts without separate evidence;
- describe MPC event-window movements as identified causal effects;
- describe a policy action as a market surprise without expectations data;
- imply causality from observational regression output.

## Global acceptance criteria

Every Streamlit surface must be checked for:

- page loads without an exception;
- institutional visual hierarchy;
- restrained financial-research styling;
- readable typography;
- consistent page width and spacing;
- sensible financial-number formatting;
- percentage formatting;
- basis-point formatting;
- chart titles, legends, axes, and tooltips;
- table readability;
- navigation consistency;
- methodology/context notes;
- research/investment disclaimer;
- understandable empty states;
- understandable invalid-input states;
- no clipped text or controls;
- no horizontal layout breakage at ordinary desktop width;
- no obviously broken narrow/mobile layout;
- no invented values when data are absent.

## Surface matrix

### 1. Home — `app/Home.py`

Status: **PENDING**

Verify:

- application purpose is immediately understandable;
- research scope is clear;
- major modules are easy to find;
- presentation is institutional rather than promotional;
- methodology/context note is visible;
- disclaimer is visible;
- navigation works.

### 2. Main Dashboard — `app/streamlit_app.py`

Status: **PENDING**

Verify:

- headline metrics render;
- tables remain readable;
- missing values are not presented as zero;
- layout remains understandable without developer explanation;
- disclaimer is visible.

### 3. Market Overview — `app/pages/1_Market_Overview.py`

Status: **PENDING**

Verify:

- normal case;
- earliest available date;
- latest available date;
- missing/unavailable date behavior;
- curve labels are clear;
- units are clear;
- methodology context is visible;
- disclaimer is visible.

### 4. Yield Curve Lab — `app/pages/2_Yield_Curve_Lab.py`

Status: **PENDING**

Verify:

- different curves;
- different dates;
- different tenors;
- earliest available curve;
- latest available curve;
- insufficient/missing observations;
- Nelson-Siegel availability or graceful failure where applicable;
- legends and tooltips are understandable;
- disclaimer is visible.

### 5. Monetary Policy Lab — `app/pages/3_Monetary_Policy_Lab.py`

Status: **PENDING**

Verify:

- MPC event selection;
- HIKE / CUT / HOLD cases;
- event-window display;
- missing/ineligible event-window cases;
- event-window units are basis points where appropriate;
- wording does not imply identified causal shocks;
- disclaimer is visible.

### 6. Islamic vs Conventional — `app/pages/4_Islamic_vs_Conventional.py`

Status: **PENDING**

Verify:

- matched PKRV/PKISRV cases;
- unmatched cases;
- exact comparable maturity handling;
- missing leg handling;
- numerical spread terminology only;
- no unsupported premium/discount interpretation;
- disclaimer is visible.

### 7. Fixed-Income Risk — `app/pages/5_Fixed_Income_Risk.py`

Status: **PENDING**

Verify:

- par bond input;
- premium bond input;
- discount bond input;
- extreme but valid rate input;
- invalid coupon/rate/maturity/frequency input;
- price;
- Macaulay duration;
- modified duration;
- DV01;
- convexity;
- rate-shock scenarios;
- duration-only estimate;
- duration + convexity estimate;
- actual repricing;
- model clearly remains a generic fixed-rate bullet-bond model;
- no claim that it is a universal Sukuk valuation model;
- disclaimer is visible.

### 8. Research — `app/pages/6_Research.py`

Status: **PENDING**

Verify:

- research question/context;
- methodology;
- descriptive results;
- inferential/econometric output;
- diagnostics;
- limitations;
- tables/charts remain legible;
- statistical relationships are not described automatically as causal;
- disclaimer is visible.

## Cross-browser/layout check

Status: **PENDING**

Check at minimum:

- normal desktop browser width;
- narrower browser window;
- navigation after changing pages repeatedly;
- browser refresh on a non-Home page.

## Empty/error-state check

Status: **PENDING**

Where controls permit it, verify:

- unavailable date;
- insufficient curve observations;
- invalid bond input;
- empty query/result;
- missing comparison leg.

The application must fail clearly and safely rather than inventing output.

## Final Phase 14 acceptance

Phase 14 may be marked **PASS** only when:

1. automated presentation-contract tests pass;
2. full project regression passes;
3. local Streamlit startup smoke test passes;
4. every manual surface above has been inspected;
5. no critical UI defect remains;
6. no research-integrity wording defect remains;
7. the first-time-user acceptance criterion is satisfied.

**First-time-user criterion:** a visitor can understand what PakYield does
without the project author standing beside them.

Until the manual statuses are completed, Phase 14 remains:

**MANUAL VERIFICATION PENDING**

<!-- PHASE14_CANONICAL_QA_START -->

# Phase 14 Manual UI QA — Canonical Evidence

This checklist is the required manual browser-review evidence for Phase 14.

Rules:

- Mark an item `[x]` only after visually verifying it in the running application.
- Leave failed or untested items as `[ ]`.
- Do not mark an item complete based only on automated tests.
- Record any defect under the relevant page before closing Phase 14.

## Automated prerequisites

[x] Presentation-contract regression passed.
[x] Full project regression passed.
[x] Streamlit local startup smoke passed.
[x] SQLite integrity check passed.
[x] SQLite foreign-key check passed.
[x] Presentation source-quality checks passed.
[x] Repository anchor was aligned before manual QA.
[x] No files were staged before manual QA.

## Home

[x] Page loads without exception.
[x] No raw traceback or red Streamlit error.
[x] Sidebar navigation works.
[x] Page title and header hierarchy look intentional.
[x] Intro/subtitle spacing is consistent.
[x] KPI or metric cards align correctly.
[x] Charts fit container width.
[x] Plot labels and titles are readable.
[x] No clipped legends.
[x] No horizontal overflow.
[x] Tables remain readable.
[x] Empty states look intentional where applicable.
[x] Methodology notes display correctly where applicable.
[x] Disclaimer appears where required.
[x] No duplicate page title.
[x] No legacy `use_container_width` warning is visible.
[x] No visibly broken HTML or CSS.
[x] Light/dark contrast is acceptable.
[x] Narrow-width resize does not catastrophically break layout.
[x] Displayed data looks plausible relative to labels and units.

## Main Dashboard / streamlit_app

[x] Page loads without exception.
[x] No raw traceback or red Streamlit error.
[x] Sidebar navigation works.
[x] Page title and header hierarchy look intentional.
[x] Intro/subtitle spacing is consistent.
[x] KPI or metric cards align correctly.
[x] Charts fit container width.
[x] Plot labels and titles are readable.
[x] No clipped legends.
[x] No horizontal overflow.
[x] Tables remain readable.
[x] Empty states look intentional where applicable.
[x] Methodology notes display correctly where applicable.
[x] Disclaimer appears where required.
[x] No duplicate page title.
[x] No legacy `use_container_width` warning is visible.
[x] No visibly broken HTML or CSS.
[x] Light/dark contrast is acceptable.
[x] Narrow-width resize does not catastrophically break layout.
[x] Displayed data looks plausible relative to labels and units.

## Market Overview

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] KPI cards align correctly.
[X] Charts fit container width.
[X] Plot labels and titles are readable.
[X] No clipped legends.
[X] No horizontal overflow.
[X] Tables remain readable.
[X] Date controls work.
[X] Curve controls work where present.
[X] Methodology notes display correctly.
[X] Disclaimer appears where required.
[X] Narrow-width resize remains usable.
[X] Displayed values look plausible relative to labels and units.

## Yield Curve Lab

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] Yield-curve chart fits container width.
[X] Tenor labels are readable.
[X] Curve legend is not clipped.
[X] Date controls work.
[X] Tenor controls work where present.
[X] Curve controls work.
[X] Tabs work where present.
[X] Expanders work where present.
[X] Download buttons work where present.
[X] Nelson-Siegel presentation looks intentional where present.
[X] Methodology notes display correctly.
[X] No horizontal overflow.
[X] Narrow-width resize remains usable.
[X] Displayed yields and units look plausible.

## Monetary Policy Lab

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] Policy-rate presentation looks intentional.
[X] Event-window charts fit container width.
[X] Plot labels and titles are readable.
[X] No clipped legends.
[X] Date controls work where present.
[X] Regime controls work where present.
[X] Tabs work where present.
[X] Expanders work where present.
[X] Methodology notes display correctly.
[X] Announcement/event labels look plausible.
[X] No horizontal overflow.
[X] Narrow-width resize remains usable.
[X] No causal wording is presented as established fact.

## Islamic vs Conventional

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] PKRV/PKISRV comparison charts fit container width.
[X] Plot labels and titles are readable.
[X] No clipped legends.
[X] Date controls work where present.
[X] Tenor controls work where present.
[X] Tabs work where present.
[X] Tables remain readable.
[X] Methodology notes display correctly.
[X] Disclaimer/boundary language appears where required.
[X] No horizontal overflow.
[X] Narrow-width resize remains usable.
[X] Numerical spreads look plausible relative to displayed yields.
[X] No unsupported premium/discount causal interpretation is shown.

## Fixed Income Risk

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] Calculator layout is aligned.
[X] Input controls accept valid values.
[X] Fixed-income calculators execute successfully.
[X] Output units are clear.
[X] Duration/convexity/risk results display cleanly.
[X] Tables remain readable.
[X] Charts fit container width where present.
[X] Methodology notes display correctly.
[X] Disclaimer appears where required.
[X] No horizontal overflow.
[X] Narrow-width resize remains usable.
[X] Calculated values look plausible for entered inputs.

## Research

[X] Page loads without exception.
[X] No raw traceback or red Streamlit error.
[X] Sidebar navigation works.
[X] Page title/header hierarchy looks intentional.
[X] Research controls work.
[X] Econometric controls work where present.
[X] Tabs work where present.
[X] Expanders work where present.
[X] Download buttons work where present.
[X] Tables remain readable.
[X] Charts fit container width.
[X] Plot labels and titles are readable.
[X] Methodology notes display correctly.
[X] Research/investment disclaimer is visible.
[X] No horizontal overflow.
[X] Narrow-width resize remains usable.
[X] No statistical result is presented with obviously mismatched labels/units.

## Cross-page interaction checks

[x] Sidebar navigation successfully reaches all eight surfaces.
[x] Date controls tested where available.
[X] Tenor controls tested where available.
[X] Curve controls tested where available.
[X] Regime controls tested where available.
[X] Tabs tested where available.
[X] Expanders tested where available.
[X] Download buttons tested where available.
[X] Research/econometric controls tested.
[X] Fixed-income calculators tested.
[X] Browser refresh does not break the active page.
[X] No obvious Streamlit runtime errors appear after interaction.

## Manual QA defects / notes

Record any observed issue below before marking its associated checklist item complete.

- None recorded yet.

<!-- PHASE14_CANONICAL_QA_END -->
