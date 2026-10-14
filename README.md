# PakYield Lab

**Pakistan Sovereign Fixed-Income & Monetary Policy Research Platform**

PakYield Lab is an empirical financial-market research project examining
Pakistan's conventional and Shariah-compliant sovereign benchmark curves,
monetary-policy announcements, inflation, fixed-income risk, and yield-curve
behavior.

## Central Research Question

> How does monetary policy transmit across Pakistan's sovereign yield curve,
> and how do conventional and Shariah-compliant sovereign benchmark rates
> behave across maturities and monetary-policy regimes?

## Core Research Areas

- Pakistan PKRV yield-curve evolution
- SBP MPC announcement-window analysis
- PKRV versus PKISRV comparison
- PKISRV-PKRV spreads
- monetary-policy regime analysis
- CPI and sovereign-yield relationships
- fixed-income risk analytics
- Nelson-Siegel yield-curve modeling

## Planned Technology

- Python 3.12
- pandas
- NumPy
- SciPy
- statsmodels
- SQLite
- SQL
- Plotly
- Streamlit
- Jupyter
- pytest
- Ruff
- Git / GitHub

## Research Data

Primary authorities include:

- Mutual Funds Association of Pakistan (MUFAP)
- State Bank of Pakistan (SBP)
- Pakistan Bureau of Statistics (PBS)

See:

- `docs/PROJECT_SPEC.md`
- `docs/RESEARCH_QUESTIONS.md`
- `docs/METHODOLOGY_DRAFT.md`
- `docs/DATA_FEASIBILITY_AUDIT.md`
- `docs/DATA_COVERAGE_MATRIX.md`
- `docs/DECISIONS.md`

for the controlling research specification and feasibility findings.

## Project Status

Phase 3 — Repository & Architecture

Production analysis is complete through the frozen Phase 6 research outputs, and the Phase 7 Streamlit presentation and delivery layers are complete.

## Running PakYield Lab

PakYield Lab uses Python 3.12 and Streamlit.

### 1. Create and activate a virtual environment

On macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install the project

Install the application and research dependencies from the project metadata:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and testing tools:

```bash
python -m pip install -e ".[dev]"
```

### 3. Run the dashboard

The canonical Streamlit entrypoint is:

```text
app/streamlit_app.py
```

Start the application with:

```bash
streamlit run app/streamlit_app.py
```

Streamlit configuration is stored in:

```text
.streamlit/config.toml
```

### 4. Verify the project before delivery

Run the complete automated test suite:

```bash
pytest -q
```

Check Python source quality:

```bash
ruff check .
ruff format --check .
```

Check the production research database:

```bash
sqlite3 data/processed/pakyield.sqlite3 "PRAGMA integrity_check;"
sqlite3 data/processed/pakyield.sqlite3   "SELECT COUNT(*) FROM pragma_foreign_key_check;"
```

Expected database-health results are:

```text
ok
0
```

### Research-data boundary

The dashboard presents deterministic research outputs produced by the PakYield
research pipeline.

Generated analytical artifacts under `data/interim/` are intentionally
Git-ignored. Deployment must therefore provide every runtime data dependency
required by the application through the approved delivery mechanism rather
than assuming ignored local files are present automatically.

Do not replace missing research data with interpolation, fabricated values,
nearest-date matches, or silent fallbacks.

### Deployment

See:

```text
docs/DEPLOYMENT.md
```

for the delivery contract, deployment prerequisites, verification procedure,
and runtime-data requirements.
