# PakYield Lab — Deployment Guide

## Purpose

This document defines the deployment and delivery requirements for the
PakYield Lab Streamlit research application.

Deployment is a presentation and delivery activity. It must not alter the
frozen research methodology, transformation contracts, analytical evidence,
or eligibility rules.

---

## Runtime

PakYield Lab currently targets:

- Python 3.12
- Streamlit
- SQLite
- the Python dependencies declared in `pyproject.toml`

The canonical application entrypoint is:

```text
app/Home.py
```

The repository's Streamlit configuration is:

```text
.streamlit/config.toml
```

---

## Local installation

Create a Python 3.12 virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the application:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and validation:

```bash
python -m pip install -e ".[dev]"
```

---

## Local execution

Start PakYield Lab with:

```bash
streamlit run app/Home.py
```

A headless smoke test can be performed with:

```bash
streamlit run app/Home.py \
  --server.headless true \
  --server.port 8765
```

A successful boot must reach the Streamlit ready state without an import or
runtime-data exception.

---

## Pre-deployment validation

Before deployment, run:

```bash
pytest -q
```

Then:

```bash
ruff check .
ruff format --check .
```

Validate SQLite:

```bash
sqlite3 data/processed/pakyield.sqlite3 \
  "PRAGMA integrity_check;"
```

Expected result:

```text
ok
```

Then:

```bash
sqlite3 data/processed/pakyield.sqlite3 \
  "SELECT COUNT(*) FROM pragma_foreign_key_check;"
```

Expected result:

```text
0
```

The application should also pass a headless Streamlit boot test before a
release is considered deployable.

---

## Runtime research data

PakYield Lab depends on validated research data. Selected runtime
artifacts under `data/runtime/` and `data/interim/` are tracked in the
repository for the deployed dashboard.

Other generated files under `data/interim/` and the local processed SQLite
database can remain ignored. Do not assume that every research input needed
to rebuild the complete analytical pipeline is present in a fresh clone.

See `docs/DEPLOYMENT_DATA_MANIFEST.md` and the application services for the
tracked runtime dependencies. Verify artifact availability and integrity after
deployment.

---

## Frozen research boundary

Deployment must not alter frozen research evidence simply to make the
dashboard easier to host.

In particular, deployment code must not:

- interpolate missing benchmark yields;
- substitute nearby dates;
- substitute nearby maturities;
- forward-fill or backfill analytical observations unless an existing frozen
  contract explicitly allows it;
- manufacture missing PKISRV maturities;
- convert missing analytical values to zero;
- relabel same-day MPC observations as post-announcement without compatible
  timestamp evidence;
- collapse daily, event-study, and monthly analytical grains into one
  universal table;
- infer policy surprise without expectations data;
- convert numerical PKRV/PKISRV differences into unsupported premium or
  causal claims.

---

## Secrets

The current application-layer preflight detected no obvious credential files,
hardcoded credential tokens, or external-service imports.

If credentials are introduced later:

- never commit them to Git;
- use the hosting platform's secret-management mechanism;
- keep local secret files ignored;
- document each required environment variable without recording its secret
  value.

---

## Network dependencies

The current presentation layer does not require external network-service
libraries during normal application operation.

A production deployment should therefore prefer deterministic local research
data rather than downloading analytical evidence dynamically at page load.

Any future runtime network dependency must receive an explicit reproducibility
and failure-mode review.

---

## Deployment acceptance checklist

A release is ready for hosting only when all of the following pass:

- canonical entrypoint exists;
- application imports resolve;
- required runtime research data exists;
- complete project test suite passes;
- dashboard-specific tests pass;
- Ruff passes;
- format check passes;
- SQLite integrity returns `ok`;
- SQLite foreign-key check returns zero rows;
- no obvious secrets are tracked;
- no temporary `.part` files remain;
- Streamlit boots successfully in headless mode;
- frozen evidence hashes required by the application remain unchanged;
- deployment does not modify research methodology or analytical outputs.

---

## Hosting target

The public application is hosted on Streamlit Community Cloud:

https://pakyield-azfcfge3jymnrh7jkskn73.streamlit.app/

The configured entry point is `app/Home.py`. The repository's
`requirements.txt` installs the locked runtime dependencies and the project
package. Selected runtime artifacts are tracked in Git; see
`docs/DEPLOYMENT_DATA_MANIFEST.md`.

After a deployment, open the public application and check the pages,
interactive controls, artifact-backed results, and error states. A successful
application boot alone does not establish that every analytical feature works.
