# PakYield Lab — Portfolio and Launch Package

## Project title

**PakYield Lab — Pakistan Sovereign Fixed-Income Research Platform**

## Short portfolio description

An interactive financial-research platform for exploring Pakistan's
sovereign benchmark yield curves, monetary-policy environments, fixed-income
risk, and conventional versus Shariah-compliant benchmark comparisons.

## LinkedIn launch post

I built **PakYield Lab**, an interactive research platform for exploring
Pakistan's sovereign fixed-income market.

The project brings together benchmark yield curves, monetary-policy data,
inflation context, fixed-income risk calculations, and econometric research
in one application.

Some of the features I built include:

- Interactive PKRV and PKISRV yield-curve exploration.
- Monetary-policy announcement windows and regime comparisons.
- Exact-date, exact-maturity benchmark comparisons and rolling correlations.
- A fixed-rate bond risk simulator with duration, DV01, and convexity.
- Nelson–Siegel curve fits where the data meet the project's coverage rules.
- A research workbench with documented statistical results and limitations.

The project also includes a research paper and a concise evidence brief.
A key part of the work was making the limitations explicit: observational
relationships do not establish causality, and benchmark differences do not
automatically identify their economic causes.

Live application:
https://pakyield-azfcfge3jymnrh7jkskn73.streamlit.app/

GitHub:
https://github.com/Musa-faisal/PakYield

#Python #Streamlit #DataAnalytics #FixedIncome #FinTech #Pakistan

## CV project bullets

- Built and deployed a Streamlit research platform for exploring Pakistan's
  sovereign benchmark yields, monetary-policy regimes, and fixed-income risk.
- Developed interactive yield-curve, event-window, and matched benchmark
  comparisons using Python-based analytical pipelines and Plotly.
- Implemented bond valuation and interest-rate sensitivity metrics, with
  automated tests and documented analytical limitations.

## Technical architecture

1. **Data:** Source-observed benchmark yields, monetary-policy records, and
   CPI data are validated and organized into analytical artifacts.
2. **Research layer:** Python modules and scripts construct curve, regime,
   event-window, fixed-income risk, and econometric outputs.
3. **Application:** Streamlit pages and Plotly charts present verified
   artifacts and interactive calculations.
4. **Delivery:** Tests and source-quality checks support the GitHub
   repository and deployed Streamlit application.

## Interview explanation

PakYield Lab started with a research question about how Pakistan's sovereign
yield curve behaves across maturities and monetary-policy environments.
I built a pipeline to organize and validate the data, implemented analytical
modules, and connected the results to an interactive Streamlit dashboard.

A central design challenge was preserving the difference between observed
data, modeled values, and statistical interpretation. For example,
conventional and Shariah-compliant benchmarks are compared only when their
dates and maturities match, and announcement-window movements are not
presented as causal policy effects.

## Suggested carousel

1. Project introduction and dashboard.
2. Research question and why the yield curve matters.
3. Interactive yield-curve explorer.
4. Historical yield and maturity views.
5. Monetary-policy announcement windows.
6. PKRV versus PKISRV comparison.
7. Bond risk simulator.
8. Research results and their limitations.
9. Data-to-dashboard architecture.
10. Key takeaway, live application, and repository.

## Suggested screenshots

Capture the live application after the final visual QA pass:

- Home dashboard with a selected curve.
- Yield Curve Lab with an eligible model fit.
- Monetary Policy Lab.
- Islamic vs Conventional comparison and rolling correlation.
- Fixed-Income Risk Lab.
- Research workbench.

## Technical keywords

Python, Streamlit, Plotly, pandas, NumPy, SciPy, statsmodels, SQLite,
financial data analysis, yield curves, fixed-income analytics, econometrics,
data validation, pytest, Git, and GitHub.

## Publication status

This file contains draft portfolio and launch copy. Review the wording and
capture current screenshots before publishing. The Markdown research brief
still requires a rendered two-page layout check, and the recorded manual
application QA must be completed before final release.
