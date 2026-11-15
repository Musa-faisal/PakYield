# PakYield Lab — Research Brief

## Research questions

How do Pakistan's sovereign benchmark yields differ across maturities and
monetary-policy environments? How do yields move around MPC announcements?
How do conventional PKRV and Shariah-compliant PKISRV benchmarks compare
when observations match exactly by date and maturity?

## Data and scope

- **PKRV:** 22,800 observed yields across 1,149 accepted market dates,
  4 January 2022 to 28 September 2026.
- **PKISRV:** 2,015 observed yields across 403 accepted market dates,
  3 February 2025 to 30 September 2026.
- **Monetary policy:** 39 validated State Bank of Pakistan MPC meetings.
- **Macroeconomic context:** Pakistan Bureau of Statistics CPI observations.

The samples have different coverage. Cross-curve comparisons use eligible
same-date, same-maturity observations rather than substituted maturities or
filled-in missing values.

## Findings from the frozen inferential evidence

| Test family | Rejections after the project's multiplicity adjustment |
| --- | ---: |
| Yield levels across policy regimes | 24 of 25 |
| Yield changes across policy regimes | 10 of 25 |
| Term spreads across policy regimes | 4 of 4 |
| MPC announcement-window zero-mean tests | 0 of 54 |
| Cross-curve zero-mean tests | 5 of 5 |
| Cross-curve comparisons across regimes | 4 of 5 |

These counts summarize the project's frozen tests. They do not measure the
size or economic importance of every difference. No rejection in the MPC
window tests is not proof that policy announcements have no effect.

## Interpretation and limitations

The regime classifications are observational. The tests do not identify
causal monetary-policy transmission or isolate unexpected policy decisions.
Announcement windows use available observation positions; compatible
intraday timing and a complete policy-expectations series are unavailable.

PKISRV-minus-PKRV differences are numerical benchmark comparisons. The
analysis does not identify their structural causes and does not label them
as a particular liquidity, credit, or religious premium. The frozen CPI
research evidence is descriptive; the separately documented exploratory
macro analysis is not part of the frozen inferential findings.

## Implications for research and market users

Examine maturities and time periods separately, check observation coverage,
and interpret any model fit alongside the recorded data. The dashboard
supports exploration of the historical evidence; it does not provide live
quotes, investment advice, or causal policy estimates.

## Sources and reproducibility

The full methodology, individual findings, references, and artifact hashes
are in [the academic paper](ACADEMIC_RESEARCH_PAPER.md). The evidence
register is documented in
[the publication source packet](RESEARCH_PUBLICATION_SOURCE_PACKET.md).

- Repository: https://github.com/Musa-faisal/PakYield
- Application: https://pakyield-azfcfge3jymnrh7jkskn73.streamlit.app/
