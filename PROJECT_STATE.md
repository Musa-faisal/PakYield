# PakYield Lab — Project State

## Project

**Name:** PakYield Lab
**Subtitle:** Pakistan Sovereign Fixed-Income & Monetary Policy Research Platform
**Research Subtitle:** An Empirical Study of Pakistan's Conventional and Shariah-Compliant Sovereign Yield Curves

---

## Current Status

**Current Phase:** Phase 4 — Raw Data Acquisition
**Current Batch:** Batch 4.5 — SBP MPC Events Raw Acquisition
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

The project has not yet collected, transformed, analyzed, or modeled any empirical financial-market data.

Therefore:

* no empirical findings exist;
* no hypothesis has been supported or rejected;
* no causal claims have been made;
* no final sample period has been selected;
* no final tenor universe has been selected;
* no production database exists;
* no production code exists.

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

Complete Batch 4.2C2 — Resumable PKRV Bulk Acquisition.

Acquire the approved 1,159-date PKRV universe from MUFAP using byte-preserving,
atomic and resumable downloads. Verify existing artifacts against provenance,
record SHA-256 and file size for every successful acquisition, refuse silent
overwrites, and reconcile raw storage against the approved acquisition plan.
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

