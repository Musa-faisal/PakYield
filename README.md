# PakYield Lab

**Pakistan Sovereign Fixed-Income & Monetary Policy Research Platform**

[Live application](https://pakyield-azfcfge3jymnrh7jkskn73.streamlit.app/) · [Research paper](docs/ACADEMIC_RESEARCH_PAPER.md) · [Research brief](docs/RESEARCH_BRIEF.md) · [Methodology](docs/METHODOLOGY_DRAFT.md)

PakYield Lab is an interactive research platform for exploring Pakistan's sovereign benchmark yield curves, monetary-policy environments, inflation context, and fixed-income risk. It connects a documented analytical pipeline to a Streamlit dashboard and an evidence-grounded research paper.

## Research questions

How do benchmark yields vary across maturities and monetary-policy environments? How do yields move around MPC announcements? How do conventional PKRV and Shariah-compliant PKISRV benchmark rates compare at the same date and maturity?

## Explore the application

- **Home and Market Overview:** historical market metrics and interactive benchmark views.
- **Yield Curve Lab:** observed curves and Nelson–Siegel fits for dates meeting coverage requirements.
- **Monetary Policy Lab:** policy history, regimes and observation-based MPC announcement windows.
- **Islamic vs Conventional:** exact-date, exact-maturity benchmark comparisons and rolling correlations.
- **Fixed-Income Risk:** a generic fixed-rate bullet bond calculator with price, duration, DV01 and convexity.
- **Research:** inferential results and diagnostic evidence, with methodology and limitations.

## Data and selected findings

The research paper reports 22,800 observed PKRV yields across 1,149 accepted dates (4 January 2022–28 September 2026), 2,015 PKISRV yields across 403 accepted dates (3 February 2025–30 September 2026), and 39 validated MPC meetings. Sources include the Mutual Funds Association of Pakistan (MUFAP), State Bank of Pakistan (SBP), and Pakistan Bureau of Statistics (PBS).

The frozen analysis reports multiplicity-adjusted rejections in 24 of 25 yield-level regime tests and 0 of 54 MPC announcement-window groups. These counts do not establish economic significance or causality. See the [paper](docs/ACADEMIC_RESEARCH_PAPER.md) and [research brief](docs/RESEARCH_BRIEF.md) for sample definitions, other test families, interpretation, and source references.

## Method and limitations

Observations are matched by date and maturity for cross-curve comparison; missing benchmark observations are not silently invented. Regime classifications and announcement windows are observational: they do not identify causal policy effects or monetary-policy surprises. PKISRV-minus-PKRV differences do not, on their own, identify liquidity, credit, religious, or other structural premia. Model fits are estimates, not additional observed yields; they are unavailable when maturity coverage is insufficient.

The CPI/yield evidence in the frozen research layer is descriptive. Separately documented exploratory macro analysis is not part of the frozen inferential findings. Data are historical research observations, not live quotes or investment advice.

## Architecture

Validated source data → analytical panels and statistical artifacts → Python service layer → Streamlit and Plotly dashboard. The project also includes SQLite-based research data, tests, reproducibility documentation, and artifact integrity checks.

Primary tools include Python 3.12, pandas, NumPy, SciPy, statsmodels, Plotly, Streamlit, SQLite, pytest and Ruff.

## Run locally

Use Python 3.12:

```bash
git clone https://github.com/Musa-faisal/PakYield.git
cd PakYield
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
streamlit run app/Home.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead. For deployment details, see [the deployment guide](docs/DEPLOYMENT.md).

## Test and reproduce

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

Selected runtime artifacts are tracked under `data/runtime/` and `data/interim/`; other generated research data and the processed SQLite database may be ignored. A clean clone may therefore require additional inputs to regenerate every research artifact or run all research checks. The [deployment data manifest](docs/DEPLOYMENT_DATA_MANIFEST.md) records an earlier audit checkpoint and should be read alongside the current tracked files and application service definitions.

The [publication source packet](docs/RESEARCH_PUBLICATION_SOURCE_PACKET.md), [research questions](docs/RESEARCH_QUESTIONS.md), and [methodology](docs/METHODOLOGY_DRAFT.md) describe the evidence and research boundaries.

## Project status

The dashboard is deployed and the research paper, brief, and portfolio draft are in the repository. Final recorded visual QA, rendered two-page brief verification, and portfolio screenshots remain to be completed before a final release.
