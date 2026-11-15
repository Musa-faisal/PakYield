# PakYield Lab Phase 15 Release Audit

## Current status

Phase 15 is in progress. The local application has connected Home, Market
Overview, Yield Curve Lab, Monetary Policy Lab, Islamic vs Conventional,
Fixed-Income Risk, and Research pages.

A preliminary browser review was completed by the project owner. The full
manual checklist has not yet been marked complete against every guide
requirement.

## Automated baseline

The full current project suite passed 286 tests. Repository-wide Ruff lint
passed, and Ruff formatting reported 157 files already formatted.

All registered presentation, econometric, and inferential-family runtime
dependencies were present on the project owner's Mac at the audit checkpoint.
Their presence locally does not establish availability in a clean deployment
or permission to redistribute them publicly.

## Database

The production SQLite database previously passed:

- SQLite integrity check;
- foreign-key check;
- yield natural-key duplicate check.

Observed production counts at that checkpoint:

- PKRV: 22,800 observations across 1,149 dates;
- PKISRV: 2,015 observations across 403 dates;
- MPC events: 39;
- policy-rate observations: 18;
- CPI observations: 57.

## Frozen analytical artifacts

Registered presentation and econometric artifacts passed the project's
recorded hash and row-count checks at the previous audit checkpoint.

A matching hash verifies that a file matches its recorded version. It does
not by itself prove the validity of the methodology or publication rights.

## Research scope

The existing event study describes observed changes around MPC announcements.
It does not by itself identify policy surprises or causal effects.

The PKISRV-minus-PKRV difference is a numerical benchmark comparison.
It is not automatically an Islamic, Sukuk, liquidity, or credit premium.

The separate monthly macro model remains exploratory. Its results are not
part of the frozen research evidence or approved final publication findings.
See EXPLORATORY_MACRO_ANALYSIS.md.

## Known release work

- Verify the app against the remaining Master Prompt features, including
  rolling correlations, heatmaps, and event-study comparison requirements.
- Complete a recorded page-by-page manual QA pass.
- Establish a reproducible clean-checkout and deployment procedure.
- Resolve publication and redistribution rights for source-derived data.
- Resolve Research-page dependencies under data/interim.
- Resolve delivery of the untracked Nelson-Siegel runtime artifacts.
- Review the research paper, references, and two-page brief.
- Update the README and project-state documentation.
- Verify the deployed app from an independent browser or device.
- Prepare the GitHub and LinkedIn launch package.

## Git checkpoint

The application and analytical code were checkpointed locally in commit
4840121. The exploratory macro script, tests, and note were checkpointed
locally in commit 1142999.

The project_context.zip file and two Nelson-Siegel runtime CSV files were
untracked at the last reported checkpoint. Ignored research artifacts under
data/interim are not included in those commits.

## Release decision

NOT READY FOR PUBLIC DEPLOYMENT.

The application must not be declared complete until the remaining critical
checks, data-publication decisions, and release steps are resolved.