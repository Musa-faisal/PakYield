# PakYield Lab — Data Dictionary

## 1. Purpose

This document defines the canonical meaning, storage type, unit, frequency,
allowed values, and transformation rules for PakYield's core research data.

The purpose is to ensure that ingestion, SQLite, Python analytics, notebooks,
tests, and Streamlit all interpret the same values in the same way.

This document describes normalized research-ready fields.

Raw source files remain preserved separately under `data/raw`.

---

# 2. Global Storage Conventions

## 2.1 Percentage Values

Interest rates, sovereign yields, and inflation rates are stored in
percentage-point form.

Example:

`12.50`

means:

`12.50%`

It does NOT mean:

`0.125`

Any formula requiring a decimal rate must explicitly divide by 100.

Example:

`12.50%`

becomes:

`0.125`

for a calculation requiring decimal form.

---

## 2.2 Basis Points

One percentage point equals:

`100 basis points`

Therefore:

`0.50 percentage points = 50 basis points`

and:

`1 basis point = 0.01 percentage points`

PakYield displays many yield changes and spreads in basis points.

---

## 2.3 Dates

Normalized daily/event dates are stored in ISO format:

`YYYY-MM-DD`

Example:

`2026-04-28`

Monthly CPI periods represent calendar months and will use the canonical
normalized form:

`YYYY-MM`

Example:

`2026-04`

Raw source date formatting may differ but must be normalized during ingestion.

---

## 2.4 Missing Values

Missing observations are not interpreted as zero.

PakYield will not manufacture an observation merely because another maturity
or adjacent date exists.

Interpolation may only occur inside an explicitly documented analytical model
where the methodology requires it.

Raw missing values remain missing.

---

# 3. Tenor Convention

PakYield uses standardized benchmark tenor labels.

Canonical PKRV tenors:

- 1W
- 2W
- 1M
- 2M
- 3M
- 4M
- 6M
- 9M
- 1Y
- 2Y
- 3Y
- 4Y
- 5Y
- 6Y
- 7Y
- 8Y
- 9Y
- 10Y
- 15Y
- 20Y

Tenor coordinates used for generic yield-curve analysis are:

| Tenor | Years |
|---|---:|
| 1W | 7 / 365 |
| 2W | 14 / 365 |
| 1M | 1 / 12 |
| 2M | 2 / 12 |
| 3M | 3 / 12 |
| 4M | 4 / 12 |
| 6M | 6 / 12 |
| 9M | 9 / 12 |
| 1Y | 1.0 |
| 2Y | 2.0 |
| 3Y | 3.0 |
| 4Y | 4.0 |
| 5Y | 5.0 |
| 6Y | 6.0 |
| 7Y | 7.0 |
| 8Y | 8.0 |
| 9Y | 9.0 |
| 10Y | 10.0 |
| 15Y | 15.0 |
| 20Y | 20.0 |

These values represent standardized generic maturity coordinates.

They do not represent the exact remaining maturity of a specific security.

---

# 4. Table — ingestion_runs

Purpose:

Tracks provenance and execution information for source ingestion.

| Field | Type | Unit / Format | Definition |
|---|---|---|---|
| ingestion_run_id | INTEGER | identifier | Unique ingestion-run identifier |
| dataset | TEXT | categorical | Dataset being ingested |
| source_organization | TEXT | text | Organization responsible for the source data |
| source_url | TEXT | URL | Source location when applicable |
| source_file | TEXT | filename/path reference | Raw source file used |
| retrieved_at | TEXT | timestamp | Time the source was retrieved |
| status | TEXT | categorical | Ingestion execution status |
| records_read | INTEGER | rows | Number of source observations read |
| records_written | INTEGER | rows | Number of normalized observations written |
| sha256 | TEXT | hexadecimal hash | Optional content hash of raw source evidence |
| notes | TEXT | text | Additional provenance or ingestion notes |
| created_at | TEXT | timestamp | SQLite record-creation timestamp |

Allowed `dataset` values:

- PKRV
- PKISRV
- SBP_POLICY_RATE
- SBP_MPC_EVENTS
- PBS_CPI

Allowed `status` values:

- STARTED
- SUCCESS
- FAILED

---

# 5. Table — yield_observations

Purpose:

Stores normalized PKRV and standardized PKISRV benchmark observations.

Natural observation key:

`observation_date + curve_type + tenor`

| Field | Type | Unit / Format | Definition |
|---|---|---|---|
| yield_observation_id | INTEGER | identifier | Internal unique row identifier |
| observation_date | TEXT | YYYY-MM-DD | Published/normalized benchmark observation date |
| curve_type | TEXT | categorical | Sovereign benchmark curve |
| tenor | TEXT | standardized tenor | Maturity label |
| tenor_years | REAL | years | Canonical numeric maturity coordinate |
| yield_pct | REAL | percent | Benchmark yield/rate |
| source_organization | TEXT | text | Organization responsible for source |
| source_file | TEXT | filename/path reference | Raw source evidence |
| ingestion_run_id | INTEGER | foreign key | Associated ingestion run |
| created_at | TEXT | timestamp | SQLite record-creation timestamp |

Allowed `curve_type` values:

- PKRV
- PKISRV

Example:

```text
observation_date = 2026-09-17
curve_type       = PKRV
tenor            = 1Y
tenor_years      = 1.0
yield_pct        = 10.86

means:

The normalized one-year PKRV benchmark observation is 10.86%.

6. Table — policy_rate_observations

Purpose:

Stores official SBP Policy (Target) Rate change observations.

Field	Type	Unit / Format	Definition
policy_rate_id	INTEGER	identifier	Unique policy-rate record
effective_date	TEXT	YYYY-MM-DD	Date the recorded policy rate becomes effective
rate_pct	REAL	percent	Official SBP Policy (Target) Rate
series_key	TEXT	identifier	SBP EasyData series identifier
observation_status	TEXT	source metadata	Official observation status
observation_status_comment	TEXT	text	Associated SBP status comment
source_organization	TEXT	text	Source institution
source_file	TEXT	filename/path reference	Source evidence
ingestion_run_id	INTEGER	foreign key	Associated ingestion run
created_at	TEXT	timestamp	SQLite record-creation timestamp

Important:

This table represents policy-rate observations.

It is not itself the complete MPC-meeting calendar.

HOLD meetings are represented separately in mpc_events.

7. Table — mpc_events

Purpose:

Stores SBP monetary-policy announcement events.

Field	Type	Unit / Format	Definition
mpc_event_id	INTEGER	identifier	Unique monetary-policy event
event_date	TEXT	YYYY-MM-DD	Monetary Policy Statement announcement date
decision_type	TEXT	categorical	HIKE, CUT, or HOLD
previous_rate_pct	REAL	percent	Policy rate before decision where available
announced_rate_pct	REAL	percent	Policy rate announced in event
change_bps	INTEGER	basis points	Signed policy-rate change
effective_date	TEXT	YYYY-MM-DD	Effective date where separately identified
statement_title	TEXT	text	Official statement title
statement_url	TEXT	URL	Official statement location
source_organization	TEXT	text	Source institution
ingestion_run_id	INTEGER	foreign key	Associated ingestion run
notes	TEXT	text	Event-specific notes
created_at	TEXT	timestamp	SQLite record-creation timestamp

Allowed decision_type values:

HIKE
CUT
HOLD

Direction convention:

HIKE → positive change_bps
CUT → negative change_bps
HOLD → zero change_bps

Example:

A 100-basis-point increase is stored as:

+100

A 100-basis-point reduction is stored as:

-100

8. Table — cpi_observations

Purpose:

Stores monthly Pakistan National CPI and headline year-on-year inflation.

Field	Type	Unit / Format	Definition
cpi_observation_id	INTEGER	identifier	Unique monthly CPI observation
period	TEXT	YYYY-MM	Calendar month
national_cpi_index	REAL	index points	National CPI index
cpi_inflation_yoy_pct	REAL	percent	National headline CPI year-on-year inflation
base_year	TEXT	base convention	CPI base year
source_organization	TEXT	text	Source institution
source_file	TEXT	filename/path reference	PBS source evidence
ingestion_run_id	INTEGER	foreign key	Associated ingestion run
created_at	TEXT	timestamp	SQLite record-creation timestamp

Primary CPI base:

2015-16

Primary inflation variable:

cpi_inflation_yoy_pct

The National CPI index is retained both as a research variable and as a
validation input for year-on-year calculations.

9. Derived Variables

Derived analytical variables must not overwrite source observations.

Examples include:

term spreads;
PKISRV-PKRV spreads;
daily policy-rate state;
yield changes;
event-window changes;
rolling correlations;
Nelson-Siegel parameters;
duration;
modified duration;
DV01;
convexity.

These are produced from normalized source observations and may later be stored
in analytical tables or calculated dynamically.

10. Term Spread Convention

For two yields quoted in percentage points:

term_spread_bps = (long_yield_pct - short_yield_pct) * 100

Example:

10Y PKRV = 12.00
2Y PKRV  = 10.50

Then:

12.00 - 10.50 = 1.50 percentage points
1.50 × 100 = 150 basis points

Therefore:

10Y-2Y spread = +150 bps

11. PKISRV-PKRV Spread Convention

For matching dates and maturities:

pkisrv_pkrv_spread_bps = (PKISRV_pct - PKRV_pct) * 100

Example:

PKISRV = 12.20
PKRV   = 12.00

Then:

PKISRV-PKRV spread = +20 bps

A positive value only means that the observed PKISRV benchmark is numerically
above the matched PKRV benchmark.

PakYield will not automatically label this an Islamic premium or discount.

12. Frequency Summary
Dataset	Frequency
PKRV	Daily / available market observation
PKISRV	Daily / available market observation
SBP policy rate	Event-based
SBP MPC events	Event-based
CPI	Monthly

Different frequencies must be explicitly aligned for empirical analysis.

They must not be naïvely merged as though every dataset were daily.

13. Source Authority Summary
Dataset	Primary Authority	Acquisition Route
PKRV	MUFAP	MUFAP
PKISRV	MUFAP	PakDataHub acquisition with MUFAP validation
Policy Rate	SBP	SBP EasyData
MPC Events	SBP	Monetary Policy Statements
CPI	PBS	PBS publications
14. Research Integrity Rules

PakYield follows these data rules:

Missing observations are not zero.
Raw source values are not silently overwritten.
Synthetic values are not inserted into empirical research datasets.
Historical PKISRV maturities are not manufactured.
Percentage values and decimal values must never be silently mixed.
Comparable PKRV/PKISRV analysis requires matching tenor definitions.
Derived variables must remain distinguishable from source observations.
Source provenance must be retained.
Unusual observations are investigated before removal.
Transformations must be documented and reproducible.

Save.

---