# PakYield Lab — Project State

## Project

**Name:** PakYield Lab
**Subtitle:** Pakistan Sovereign Fixed-Income & Monetary Policy Research Platform
**Research Subtitle:** An Empirical Study of Pakistan's Conventional and Shariah-Compliant Sovereign Yield Curves

---

## Current Status

**Current Phase:** Phase 5 — Cleaning & Validation
**Current Batch:** Phase 5A — Core Dataset Normalization Complete
**Overall Status:** IN PROGRESS

---

## Completed Phases

### Phase 0 — Computer & Tool Setup

**Status:** PASSED

Verified environment:

* macOS 14.4.1
* Apple Silicon arm64
* Python 3.12.10
* pip 25.0.1
* Git 2.39.3
* SQLite 3.43.2
* VS Code 1.132.0
* Python VS Code extension
* Jupyter VS Code extension
* Ruff VS Code extension
* Python virtual environments
* Jupyter runtime
* Streamlit runtime
* GitHub SSH authentication

Git identity:

* Name: Muhammad Musa Faisal
* Default branch: main
* GitHub SSH account: Musa-faisal

Homebrew was intentionally skipped after repeated installation stalls on macOS 14.4. It is not required for the current PakYield architecture.

### Phase 1 — Research Specification

**Status:** PASSED

Completed research-control documents:

- `docs/PROJECT_SPEC.md`
- `docs/RESEARCH_QUESTIONS.md`
- `docs/METHODOLOGY_DRAFT.md`
- `docs/DECISIONS.md`

Phase 1 established:

- central research question;
- RQ1–RQ4;
- H1–H4;
- analytical variables;
- yield and basis-point conventions;
- MPC announcement-window methodology;
- causality restrictions;
- PKRV/PKISRV spread conventions;
- econometric methodology;
- Nelson-Siegel scope;
- fixed-income risk scope;
- research-integrity rules;
- deferred data-dependent decisions.

No empirical findings were produced during Phase 1.

---

## Current Research Position

PakYield now contains real, provenance-controlled empirical source data for
PKRV, PKISRV, the SBP Policy (Target) Rate, SBP MPC events and PBS National
CPI.

Current normalized SQLite state includes:

- 22,800 source-observed PKRV benchmark-yield observations across 1,149
  accepted market dates from 2022-01-04 through 2026-09-28;
- 2,015 source-observed PKISRV benchmark-yield observations across 403
  accepted COMPLETE_5 market dates from 2025-02-03 through 2026-09-30;
- 57 monthly PBS National CPI observations from 2022-01 through 2026-09;
- 18 official SBP Policy (Target) Rate observations consisting of one
  pre-sample state anchor and 17 in-sample policy-rate changes;
- 39 validated SBP Monetary Policy Committee events from 2022-01-24 through
  2026-09-14.

Core normalization is complete for PKRV, PKISRV, the SBP policy-rate series,
SBP MPC events and PBS National CPI.

Therefore:

- source acquisition and validation findings exist;
- no substantive yield-curve, event-study or econometric findings have yet
  been declared;
- no hypothesis has been supported or rejected;
- no causal monetary-policy claim has been made;
- no synthetic observation has been inserted into the empirical dataset;
- core source normalization is complete; deterministic transformation, alignment and analytical processing remain in progress.

---

## Current Central Research Question

How does monetary policy transmit across Pakistan's sovereign yield curve, and how do conventional and Shariah-compliant sovereign benchmark rates behave across maturities and monetary-policy regimes?

This wording remains provisional until Phase 1 is formally completed.

---

## Research Integrity Status

The following rules are currently binding:

1. Do not manufacture findings.
2. Do not insert synthetic data into the empirical research dataset.
3. Synthetic fixtures may be used only for controlled software tests.
4. Do not describe announcement-window movements as causal effects without a valid identification strategy.
5. Do not describe an MPC decision as a monetary-policy surprise unless market expectations are explicitly measured.
6. Do not interpret correlation as causation.
7. Do not claim predictive ability without appropriate out-of-sample validation.
8. Do not call a PKISRV-PKRV difference an Islamic premium or discount unless evidence and definitions justify that language.
9. Do not finalize the sample period before the Phase 2 data-feasibility audit.
10. Do not finalize the maturity universe before actual PKRV/PKISRV coverage is inspected.

---

## Architecture Decisions Currently in Force

* Primary programming language: Python 3.12
* Database: SQLite unless later evidence justifies a change
* Application framework: Streamlit
* Interactive charts: Plotly
* Statistical/econometric package: statsmodels
* Numerical optimization: SciPy where appropriate
* Development environment: macOS + Terminal + VS Code
* Repository hosting: GitHub
* Main Git branch: main
* Research workflow: raw → interim → processed → database → analytics

These decisions may change only when a documented technical, data, or methodological reason exists.

---

## Sample Period

**Status:** NOT YET DETERMINED

Target to investigate during Phase 2:

* approximately 2013–2026 if sufficiently reliable;
* preferred working range approximately 2015–2026;
* approximately 2020–2026 remains acceptable if earlier observations are not consistently usable.

The actual final sample must be chosen from observed data availability rather than portfolio aesthetics.

---

## Final Tenor Universe

**Status:** NOT YET DETERMINED

Potential maturities may include short-, medium-, and long-term benchmark points, but no maturity is considered mandatory until actual source coverage is audited.

---

## Core Datasets Under Consideration

Mandatory candidates:

* PKRV benchmark yields
* PKISRV benchmark yields
* SBP Monetary Policy Committee events
* SBP policy-rate history
* Pakistan CPI/inflation data

Conditional or optional candidates:

* PKR/USD exchange-rate series
* government-security auction data
* government-security trading information

The Phase 2 feasibility audit will determine the final dataset set.

---

## Repository Status

**Final Git repository:** NOT YET CREATED
**Repository initialization phase:** Phase 3
**Current workspace:** Temporary Phase 1 research-specification workspace

---

## Git Status

Not applicable yet.

The Phase 1 workspace is intentionally not being initialized as the final Git repository.

---

## Current Issues

No blocking technical issues.

---

## Current Files

Expected during Phase 1:

* PROJECT_STATE.md
* docs/PROJECT_SPEC.md
* docs/RESEARCH_QUESTIONS.md
* docs/METHODOLOGY_DRAFT.md
* docs/DECISIONS.md

---

## Next Action

Begin the next Phase 5 transformation and cross-dataset alignment batch.

Before substantive empirical analysis, construct and validate the derived
analytical states required by the methodology, including:

- daily policy-rate state from the official change observations;
- previous-available-market-observation yield changes by curve and tenor;
- same-date PKRV/PKISRV matching for 1M, 3M, 6M, 9M and 1Y;
- explicit preservation of unmatched or missing observations;
- lower-frequency yield alignment required for monthly CPI analysis.

Do not begin hypothesis evaluation, MPC event-study aggregation, regression
estimation or economic interpretation until the required derived datasets have
their own deterministic validation contracts.

## Phase 1 Acceptance Criteria

Phase 1 passes only when the project has clearly documented:

* central research question;
* supporting research questions;
* hypotheses;
* dependent variables;
* explanatory/context variables;
* units;
* proposed methodology;
* event-study interpretation;
* research boundaries;
* causal-language restrictions;
* limitations;
* mandatory versus optional scope.

No empirical analysis may begin merely because these documents exist. Phase 2 must first verify the real data.

### Phase 2 — Data Feasibility Audit

**Status:** PASSED

Confirmed feasible core datasets:

- PKRV;
- standardized PKISRV;
- SBP Policy (Target) Rate;
- SBP MPC event archive;
- Pakistan National CPI inflation.

Accepted analytical samples:

- Sample A — PKRV / MPC / conventional curve: January 29, 2020 onward;
- Sample B — PKRV / PKISRV comparison: February 3, 2025 onward;
- Sample C — monthly macroeconomic analysis: 2020 onward.

Accepted comparative PKRV/PKISRV tenors:

- 1M;
- 3M;
- 6M;
- 9M;
- 1Y.

Optional PKR/USD and auction/trading datasets were excluded from the required
v1 scope.

No production ingestion pipeline or empirical analysis was created during
Phase 2.

## Phase 4.5 — SBP MPC Events

**Status:** COMPLETE / ACCEPTED  
**Completed:** 2026-10-01

SBP Monetary Policy Committee raw acquisition, semantic validation and
decision extraction are complete.

Validated state:

- 39 canonical MPC events from 2022 through 2026-09-14.
- Event distribution: 2022 = 8, 2023 = 9, 2024 = 8, 2025 = 8, 2026 = 6.
- 39 accepted Monetary Policy Statement PDFs.
- 4 preserved same-day wrong-document exclusions.
- 43 physical MPC raw PDFs.
- 43 `SBP_MPC_EVENTS` provenance rows.
- Decision classification: 22 HOLD, 9 RAISE, 8 CUT.
- 17 rate-changing MPC events.
- 10 statement-explicit effective dates.
- 17/17 rate-changing events reconcile to the official SBP EasyData policy
  target-rate series.
- 2025-12-15 explicitly states a 50 bps cut effective 2025-12-16 but does not
  explicitly state the resulting rate; 10.5 percent is retained only as a
  sequence-derived validation value.
- Raw MPC files remain outside Git under the existing raw-data policy.
- Acquisition, resolution, decision extraction, validation manifests and
  integration tests are tracked.

Decision reference: D083.

## Phase 4.6 — PBS National CPI

**Status:** COMPLETE

**Accepted:** 2026-10-05

Official PBS National CPI acquisition, source-transition validation,
deterministic extraction and normalized SQLite loading are complete.

Frozen empirical state:

- authoritative raw PBS artifacts: 4
- PBS CPI provenance rows: 4
- validated monthly observations: 57
- analytical period: 2022-01 through 2026-09
- historical-series observations: 54
- monthly-review observations: 3
- historical source precision: 1 decimal place
- current monthly-review source precision: 2 decimal places
- source-explicit MoM observations retained in manifest: 3
- cross-publication prior-year diagnostics: 3
- normalized SQLite CPI observations: 57
- base year: 2015-16
- primary inflation variable: National headline CPI YoY

Historical observations are not retroactively replaced by differing prior-year
comparison columns in later PBS monthly reviews.

No CPI values are interpolated or silently inferred.

Relevant tracked artifacts:

- `data/manifests/pbs_cpi_acquisition_plan.csv`
- `data/manifests/pbs_cpi_monthly_validated.csv`
- `data/manifests/pbs_cpi_cross_publication_diagnostic.csv`
- `scripts/acquire_pbs_cpi.py`
- `scripts/build_pbs_cpi_monthly.py`
- `scripts/load_pbs_cpi_database.py`
- `tests/integration/test_pbs_cpi_monthly.py`
- `tests/integration/test_pbs_cpi_database_load.py`

Decision reference: D084.

## Phase 5A2 — SBP Policy Rate Normalization

**Status:** COMPLETE

**Accepted:** 2026-10-05

Official SBP Policy (Target) Rate normalization is complete.

Validated normalized state:

- authoritative structural source observations: 39;
- source series key: `TS_GP_IR_SIRPR_AH.SBPOL0030`;
- official in-sample changes, 2022-2026: 17;
- official pre-sample state anchors: 1;
- normalized SQLite policy-rate observations: 18;
- normalized coverage: 2021-12-15 through 2026-04-28;
- anchor observation: 2021-12-15 at 9.75 percent;
- first in-sample change: 2022-04-08 at 12.25 percent;
- last normalized observation: 2026-04-28 at 11.5 percent.

The 2021-12-15 observation is retained because it is the latest official
policy-rate observation preceding the 2022 analytical period and is required
to establish the policy-rate state at the beginning of that period.

It is an official source observation, not an interpolated or synthetic value.

The normalized source table remains a policy-rate change-observation table.
Daily policy-rate state construction is deferred to a later processing step.

Production loading is:

- conflict rejecting;
- source-lineage preserving;
- uniqueness constrained by effective date;
- idempotent on matching reruns.

Relevant tracked artifacts:

- `data/manifests/sbp_policy_rate_structural_census.csv`
- `scripts/build_sbp_policy_rate_structural_census.py`
- `scripts/load_sbp_policy_rate_database.py`
- `tests/integration/test_sbp_policy_rate_database_load.py`

Decision reference: D085.

## Phase 5A3 — SBP MPC Events Normalization

**Status:** COMPLETE

**Accepted:** 2026-10-05

Official SBP MPC event normalization is complete.

Validated normalized state:

- canonical MPC events: 39;
- normalized coverage: 2022-01-24 through 2026-09-14;
- HOLD decisions: 22;
- HIKE decisions: 9;
- CUT decisions: 8;
- rate-changing events: 17;
- statement-explicit effective dates: 10;
- normalized SQLite MPC rows: 39.

Source decision label `RAISE` is normalized to schema-canonical `HIKE`.

The normalized database preserves statement-explicit values separately from
chronology-derived analytical state.

In particular, the 2025-12-15 statement records:

- CUT;
- -50 basis points;
- effective date 2025-12-16;
- no explicitly announced resulting policy rate.

Therefore `announced_rate_pct` remains NULL for that event.

The resulting 10.5 percent rate is used only for sequence continuity and
policy-rate validation. It is not represented as statement-announced.

The subsequent 2026-01-26 HOLD statement explicitly states 10.5 percent.

Production loading is:

- conflict rejecting;
- event-date uniqueness constrained;
- source-lineage preserving;
- statement-semantics preserving;
- idempotent on matching reruns.

Production verification confirmed:

- initial production load inserted all 39 canonical events;
- immediate rerun inserted zero duplicates and validated all 39;
- the full project test suite passed with 68 tests.

Relevant tracked artifacts:

- `data/manifests/sbp_mpc_event_universe.csv`
- `data/manifests/sbp_mpc_acquisition_plan.csv`
- `data/manifests/sbp_mpc_decisions_validated.csv`
- `data/manifests/sbp_mpc_policy_rate_crosscheck.csv`
- `scripts/build_sbp_mpc_decisions.py`
- `scripts/load_sbp_mpc_database.py`
- `tests/integration/test_sbp_mpc_decisions.py`
- `tests/integration/test_sbp_mpc_database_load.py`

Decision reference: D086.

## Phase 5A4 — PKRV Normalization

**Status:** COMPLETE

**Accepted:** 2026-10-06

Deterministic PKRV normalization and production SQLite ingestion are complete.

Frozen accepted source universe:

- accepted PKRV observation dates: 1,149;
- accepted coverage: 2022-01-04 through 2026-09-28;
- FULL_20 observations: 1,119;
- PARTIAL_14 observations: 30;
- source-observed normalized date-tenor rows: 22,800;
- unique normalized date-tenor keys: 22,800;
- FULL_20 normalized rows: 22,380;
- PARTIAL_14 normalized rows: 420.

The 30 PARTIAL_14 observations consistently retain 14 canonical maturities.

The following six canonical monthly maturities remain unavailable on those
dates:

- 1M;
- 2M;
- 3M;
- 4M;
- 6M;
- 9M.

No missing maturity was interpolated, zero-filled, forward-filled, copied from
another date or otherwise manufactured.

The normalization layer deterministically supports the accepted historical
source representations:

- `CSV_DIRECT_RATE`: 1,003 source files;
- `CSV_PUBLISHED_BENCHMARK`: 139;
- `FIXED_WIDTH_AVG_RATE`: 3;
- `FIXED_WIDTH_FMAP`: 2;
- `XLSX_MID_RATE`: 1;
- `XML_SPREADSHEETML`: 1.

Four accepted 2022 source artifacts contain repeated canonical-tenor rows.
Every repeated row was independently verified to be an exact repeated source
row with identical tenor, benchmark value and source content.

The parser collapses only those explicitly audited exact repetitions and
remains fail-closed for conflicting duplicate-tenor content.

Historical comma exports that split the published `Avg Rate` heading into
adjacent `Avg,Rate` fields use the terminal published `Rate` position.

Noncanonical legacy labels such as `1s`, `2s`, `3s`, `4s`, `6s` and `9s` are
not coerced into monthly maturities.

The deterministic normalized artifact is:

`data/interim/pkrv_normalized_long.csv`

with frozen SHA-256:

`e2f968f4e295d1e1c6c3b6934bf504018c66dd58376b543d18185840ba297d5c`

Byte-for-byte regeneration produced the same SHA-256.

Production SQLite verification confirmed:

- first production load inserted all 22,800 PKRV observations;
- immediate production rerun inserted zero observations and validated all
  22,800 existing rows;
- all 22,800 production date-tenor keys reconcile to the normalized artifact;
- 1,149 distinct raw `source_file` values remain represented;
- production yield rows retain ingestion-run lineage to the original write;
- the idempotency run does not rewrite existing yield observations;
- SQLite integrity check returned `ok`;
- foreign-key validation reported zero issues;
- non-PKRV production state remained unchanged.

The final Phase 5A4 project test suite contains 77 passing tests.

Relevant tracked artifacts:

- `scripts/build_pkrv_normalized_long.py`
- `scripts/load_pkrv_database.py`
- `tests/integration/test_pkrv_normalized_long.py`
- `tests/integration/test_pkrv_database_load.py`

The normalized CSV and production SQLite database remain outside Git according
to the existing data-storage policy.

Decision reference: D087.

## Phase 5A5 — PKISRV Normalization

**Status:** COMPLETE

**Accepted:** 2026-10-07

Deterministic PKISRV normalization and production SQLite ingestion are
complete.

Frozen source universe:

- MUFAP PKISRV source-publication records: 407;
- accepted COMPLETE_5 observation dates: 403;
- source-level ABSENT dates: 4;
- accepted coverage: 2025-02-03 through 2026-09-30;
- canonical comparable tenors: 1M, 3M, 6M, 9M and 1Y;
- normalized source-observed date-tenor rows: 2,015;
- unique normalized date-tenor keys: 2,015.

The four source-level ABSENT dates are:

- 2025-03-07;
- 2025-08-20;
- 2026-03-18;
- 2026-03-27.

Those dates remain absent from normalized PKISRV output.

No benchmark value was interpolated, forward-filled, backward-filled,
recovered from another source, copied from another date or otherwise
manufactured.

All 403 accepted COMPLETE_5 source artifacts are UTF-8 CSV files.

The accepted benchmark block uses the source labels:

- `1 - Month`;
- `3 - Month`;
- `6 - Month`;
- `9 - Month`;
- `1 - Year`.

The published value field is:

`PKISRV Rates (Yields)`

Nine audited physical source-layout signatures occur across the accepted
archive. Although their absolute CSV column positions and row widths differ,
all preserve the same deterministic semantic structure:

- five contiguous benchmark-tenor rows;
- one unique canonical tenor per row;
- the published yield immediately adjacent to the tenor;
- `Tenor` and `PKISRV Rates (Yields)` headers directly above the benchmark
  block.

The parser fails closed when those publication semantics change.

The deterministic normalized artifact is:

`data/interim/pkisrv_normalized_long.csv`

with frozen SHA-256:

`b581918c66e3d867f17d3f81672c665ab843196be7e2a5764189738c8d193b98`

Independent validation reconciled all 2,015 normalized values directly to the
raw MUFAP source files.

Byte-for-byte regeneration produced the same SHA-256.

Production SQLite verification confirmed:

- first production load inserted all 2,015 PKISRV observations;
- production ingestion run 13 wrote the 2,015 observations;
- immediate production rerun inserted zero observations;
- production ingestion run 14 validated all 2,015 existing observations;
- all production PKISRV rows retain ingestion-run lineage to run 13;
- 403 distinct raw source files remain represented;
- all four source-level ABSENT dates remain absent;
- PKRV and PKISRV observations may coexist on identical date-tenor pairs
  because curve type remains part of the natural key;
- all non-PKISRV production datasets remained byte-semantically unchanged
  against the pre-load snapshot;
- SQLite integrity validation returned `ok`;
- foreign-key validation returned zero issues.

The final Phase 5A5 project test suite contains 87 passing tests.

Relevant tracked artifacts:

- `scripts/build_pkisrv_normalized_long.py`
- `scripts/load_pkisrv_database.py`
- `tests/integration/test_pkisrv_normalized_long.py`
- `tests/integration/test_pkisrv_database_load.py`

The normalized CSV and production SQLite database remain outside Git according
to the existing data-storage policy.

Decision reference: D088.

