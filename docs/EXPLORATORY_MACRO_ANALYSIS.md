# Exploratory Monthly Macro Analysis

## Status

Exploratory only. The results in this analysis are not part of the frozen
research evidence and are not approved as final paper or application findings.

## Specification

The exploratory model relates monthly PKRV yield changes, measured in basis
points, to:

- the change in the SBP policy rate between calendar month-ends, measured in
  percentage points; and
- National CPI year-over-year inflation, measured in percent.

The model uses OLS with HAC standard errors. The initial specification used
three HAC lags. Sensitivity checks used one, three, and six lags.

## Sample

A common-sample check used 37 consecutive months, from September 2023 through
September 2026, for the 3M, 1Y, 5Y, and 10Y PKRV maturities.

An earlier exploration used 56 consecutive months for 1Y, 5Y, and 10Y. Its
sample differs from the 3M sample, so coefficients from those earlier models
should not be directly compared across maturities.

## Timing and missingness

The CPI variable is aligned to its reference month. Publication timing is not
modeled; the specification is not a real-time forecasting exercise.

The policy-rate variable uses calendar month-end states. A date-alignment
audit identified one difference outside the selected 3M consecutive model
sample: June 2023. No missing yield observations were filled.

## Interpretation and limitations

The estimates are observational associations, not identified causal effects.

Some confidence intervals changed materially with the HAC lag choice. The
small common sample, limited number of policy-change months, potential
persistence, multiple comparisons, and sample sensitivity limit inference.

Further work is required before these exploratory results can be incorporated
into the app or paper as final findings.