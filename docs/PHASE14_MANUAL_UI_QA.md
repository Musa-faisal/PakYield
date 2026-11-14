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

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title and header hierarchy look intentional.
[ ] Intro/subtitle spacing is consistent.
[ ] KPI or metric cards align correctly.
[ ] Charts fit container width.
[ ] Plot labels and titles are readable.
[ ] No clipped legends.
[ ] No horizontal overflow.
[ ] Tables remain readable.
[ ] Empty states look intentional where applicable.
[ ] Methodology notes display correctly where applicable.
[ ] Disclaimer appears where required.
[ ] No duplicate page title.
[ ] No legacy `use_container_width` warning is visible.
[ ] No visibly broken HTML or CSS.
[ ] Light/dark contrast is acceptable.
[ ] Narrow-width resize does not catastrophically break layout.
[ ] Displayed data looks plausible relative to labels and units.

## Main Dashboard / streamlit_app

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title and header hierarchy look intentional.
[ ] Intro/subtitle spacing is consistent.
[ ] KPI or metric cards align correctly.
[ ] Charts fit container width.
[ ] Plot labels and titles are readable.
[ ] No clipped legends.
[ ] No horizontal overflow.
[ ] Tables remain readable.
[ ] Empty states look intentional where applicable.
[ ] Methodology notes display correctly where applicable.
[ ] Disclaimer appears where required.
[ ] No duplicate page title.
[ ] No legacy `use_container_width` warning is visible.
[ ] No visibly broken HTML or CSS.
[ ] Light/dark contrast is acceptable.
[ ] Narrow-width resize does not catastrophically break layout.
[ ] Displayed data looks plausible relative to labels and units.

## Market Overview

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] KPI cards align correctly.
[ ] Charts fit container width.
[ ] Plot labels and titles are readable.
[ ] No clipped legends.
[ ] No horizontal overflow.
[ ] Tables remain readable.
[ ] Date controls work.
[ ] Curve controls work where present.
[ ] Methodology notes display correctly.
[ ] Disclaimer appears where required.
[ ] Narrow-width resize remains usable.
[ ] Displayed values look plausible relative to labels and units.

## Yield Curve Lab

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] Yield-curve chart fits container width.
[ ] Tenor labels are readable.
[ ] Curve legend is not clipped.
[ ] Date controls work.
[ ] Tenor controls work where present.
[ ] Curve controls work.
[ ] Tabs work where present.
[ ] Expanders work where present.
[ ] Download buttons work where present.
[ ] Nelson-Siegel presentation looks intentional where present.
[ ] Methodology notes display correctly.
[ ] No horizontal overflow.
[ ] Narrow-width resize remains usable.
[ ] Displayed yields and units look plausible.

## Monetary Policy Lab

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] Policy-rate presentation looks intentional.
[ ] Event-window charts fit container width.
[ ] Plot labels and titles are readable.
[ ] No clipped legends.
[ ] Date controls work where present.
[ ] Regime controls work where present.
[ ] Tabs work where present.
[ ] Expanders work where present.
[ ] Methodology notes display correctly.
[ ] Announcement/event labels look plausible.
[ ] No horizontal overflow.
[ ] Narrow-width resize remains usable.
[ ] No causal wording is presented as established fact.

## Islamic vs Conventional

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] PKRV/PKISRV comparison charts fit container width.
[ ] Plot labels and titles are readable.
[ ] No clipped legends.
[ ] Date controls work where present.
[ ] Tenor controls work where present.
[ ] Tabs work where present.
[ ] Tables remain readable.
[ ] Methodology notes display correctly.
[ ] Disclaimer/boundary language appears where required.
[ ] No horizontal overflow.
[ ] Narrow-width resize remains usable.
[ ] Numerical spreads look plausible relative to displayed yields.
[ ] No unsupported premium/discount causal interpretation is shown.

## Fixed Income Risk

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] Calculator layout is aligned.
[ ] Input controls accept valid values.
[ ] Fixed-income calculators execute successfully.
[ ] Output units are clear.
[ ] Duration/convexity/risk results display cleanly.
[ ] Tables remain readable.
[ ] Charts fit container width where present.
[ ] Methodology notes display correctly.
[ ] Disclaimer appears where required.
[ ] No horizontal overflow.
[ ] Narrow-width resize remains usable.
[ ] Calculated values look plausible for entered inputs.

## Research

[ ] Page loads without exception.
[ ] No raw traceback or red Streamlit error.
[ ] Sidebar navigation works.
[ ] Page title/header hierarchy looks intentional.
[ ] Research controls work.
[ ] Econometric controls work where present.
[ ] Tabs work where present.
[ ] Expanders work where present.
[ ] Download buttons work where present.
[ ] Tables remain readable.
[ ] Charts fit container width.
[ ] Plot labels and titles are readable.
[ ] Methodology notes display correctly.
[ ] Research/investment disclaimer is visible.
[ ] No horizontal overflow.
[ ] Narrow-width resize remains usable.
[ ] No statistical result is presented with obviously mismatched labels/units.

## Cross-page interaction checks

[ ] Sidebar navigation successfully reaches all eight surfaces.
[ ] Date controls tested where available.
[ ] Tenor controls tested where available.
[ ] Curve controls tested where available.
[ ] Regime controls tested where available.
[ ] Tabs tested where available.
[ ] Expanders tested where available.
[ ] Download buttons tested where available.
[ ] Research/econometric controls tested.
[ ] Fixed-income calculators tested.
[ ] Browser refresh does not break the active page.
[ ] No obvious Streamlit runtime errors appear after interaction.

## Manual QA defects / notes

Record any observed issue below before marking its associated checklist item complete.

- None recorded yet.

<!-- PHASE14_CANONICAL_QA_END -->
