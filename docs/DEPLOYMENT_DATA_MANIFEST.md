# PakYield Deployment Data Manifest

## Purpose

This document records the application's known runtime data dependencies and
their delivery status. Local availability does not establish permission for
public redistribution.

## Presentation data

The application presentation service reads verified files from
`data/runtime/`. The following files are tracked in the repository:

- `yield_regime_analysis_panel.csv`
- `term_spread_regime_analysis_panel.csv`
- `cross_curve_regime_analysis_panel.csv`
- `mpc_event_window_panel.csv`
- `monthly_cpi_yield_panel.csv`
- `analysis_input_manifest.csv`
- `nelson_siegel_date_fits.csv`
- `nelson_siegel_fitted_yields.csv`

Artifact availability and integrity should be checked after deployment.
Missing observations must not be fabricated.

## Research data

The Research page reads verified econometric artifacts from
`data/interim/`. The repository tracks the following deployment artifacts:

- `inferential_diagnostics_manifest.csv`
- `phase10_correlation_diagnostics.csv`
- `phase10_adf_stationarity.csv`
- `inferential_vif_diagnostics.csv`
- `inferential_vif_manifest.csv`
- `phase10_regression_residual_diagnostics.csv`
- `inferential_yield_level_regime.csv`
- `inferential_yield_change_regime.csv`
- `inferential_term_spread_regime.csv`
- `inferential_cross_curve_zero.csv`
- `inferential_cross_curve_regime.csv`
- `inferential_mpc_event_windows.csv`
- `monthly_cpi_yield_panel.csv`

The directory's ignore rules still apply to other generated files. A tracked
file can remain tracked even when its directory has an ignore rule.

## Database

data/processed/pakyield.sqlite3 exists locally and passed integrity,
foreign-key, and duplicate-key checks. The database is ignored by Git.

## Deployment decisions still required

The public application is hosted on Streamlit Community Cloud:

https://pakyield-azfcfge3jymnrh7jkskn73.streamlit.app/

The configured entry point is `app/Home.py`. The repository supplies the
tracked runtime artifacts; `requirements.txt` installs the locked runtime
dependencies and the project package.

For each release, verify the deployed pages, artifact integrity, and
missing-data behavior. The local processed SQLite database and other ignored
research inputs are not assumed to exist in a fresh clone.

## Exclusions

project_context.zip is a local project handoff archive and is not a runtime
dependency. It must not be included in the release merely to make the app run.

No missing research observations may be replaced with fabricated or
synthetic values.