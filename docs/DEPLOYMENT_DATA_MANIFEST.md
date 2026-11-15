# PakYield Deployment Data Manifest

## Purpose

This document records the application's known runtime data dependencies and
their delivery status. Local availability does not establish permission for
public redistribution.

## Presentation data

The app's presentation service reads verified files from data/runtime:

- yield_regime_analysis_panel.csv
- term_spread_regime_analysis_panel.csv
- cross_curve_regime_analysis_panel.csv
- mpc_event_window_panel.csv
- monthly_cpi_yield_panel.csv
- analysis_input_manifest.csv
- nelson_siegel_date_fits.csv
- nelson_siegel_fitted_yields.csv

At the last Git audit, the first six files were tracked. The two Nelson-Siegel
files were present locally but untracked.

## Research data

The Research page reads verified econometric artifacts from data/interim,
including:

- inferential_diagnostics_manifest.csv
- phase10_correlation_diagnostics.csv
- phase10_adf_stationarity.csv
- inferential_vif_diagnostics.csv
- inferential_vif_manifest.csv
- phase10_regression_residual_diagnostics.csv

The inferential manifest references additional family-specific files under
data/interim. That directory is ignored by Git at the audit checkpoint.

## Database

data/processed/pakyield.sqlite3 exists locally and passed integrity,
foreign-key, and duplicate-key checks. The database is ignored by Git.

## Deployment decisions still required

1. Confirm the applicable publication and redistribution rights for source
   data and derived artifacts.
2. Decide how the required artifacts will be supplied to the deployed app.
3. Preserve artifact integrity checks and missing-data behavior.
4. Test every page from a clean deployment environment.
5. Document the selected entry point and exact delivery procedure.

The current local app was verified with app/Home.py. Earlier deployment
documentation names app/streamlit_app.py; the final deployment entry point
must be reconciled before release.

## Exclusions

project_context.zip is a local project handoff archive and is not a runtime
dependency. It must not be included in the release merely to make the app run.

No missing research observations may be replaced with fabricated or
synthetic values.