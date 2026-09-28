# PakYield Raw Data Contract

## Purpose

This document defines the rules governing production raw data acquired for
PakYield Lab.

Raw data are evidence. They must remain distinguishable from transformed,
cleaned, normalized, interpolated, or analytically derived data.

## 1. Raw Data Immutability

Files placed under `data/raw/` must be preserved in the form obtained from the
source.

Do not manually:

- edit cells;
- rename columns inside source files;
- remove rows;
- fill missing values;
- change dates;
- convert yields or rates;
- interpolate observations;
- replace apparent errors;
- overwrite source values.

If a source file must be converted for analysis, the converted file belongs in
`data/interim/` or `data/processed/`, not `data/raw/`.

## 2. Required Production Datasets

The Phase 4 required datasets are:

- PKRV sovereign benchmark yields;
- PKISRV Shariah-compliant benchmark rates;
- SBP policy-rate history;
- SBP MPC event history;
- PBS national headline CPI.

FX and auction/trading datasets are not required for the initial PakYield
research release.

## 3. Provenance

Every production acquisition must be traceable to its source.

At minimum, record:

- dataset identifier;
- source authority;
- acquisition source;
- source URL or source reference where available;
- retrieval timestamp;
- raw filename;
- local raw path;
- file format;
- SHA-256 checksum;
- acquisition status;
- notes on known source or schema issues.

## 4. Dataset Identifiers

The accepted identifiers are:

- `PKRV`
- `PKISRV`
- `SBP_POLICY_RATE`
- `SBP_MPC_EVENTS`
- `PBS_CPI`

## 5. Raw File Naming

Source filenames should be preserved when practical.

If a deterministic local filename is required, it must not imply information
that was not supplied by the source.

Never silently overwrite an existing raw file.

## 6. Checksums

Production raw files should receive a SHA-256 checksum after acquisition.

The checksum records the exact byte-level version of the acquired artifact and
supports later reproducibility checks.

## 7. Missing Data

Missing observations must remain missing at the raw stage.

Missing yields, rates, CPI observations, event dates, or maturities must never
be represented as zero unless the source itself reports zero.

## 8. Source Changes

Historical files may differ in:

- column names;
- tenor coverage;
- date representation;
- workbook structure;
- HTML structure;
- PDF structure;
- file format.

These differences must be recorded and handled later by explicit cleaning or
normalization logic.

Raw files must not be altered to hide schema drift.

## 9. Research Integrity

Raw-data acquisition must not create or imply empirical findings.

The raw stage does not establish:

- causality;
- monetary-policy surprises;
- Islamic premiums or discounts;
- predictive relationships;
- economic significance.

Those questions belong to later validated analytical phases.

## 10. Git Policy

Production raw market and macroeconomic files remain outside Git unless a
later documented decision explicitly changes this policy.

Tracked manifests, metadata schemas, acquisition code, and documentation may
be committed.

## 11. Phase 4 Acceptance Principle

Phase 4 is accepted only when the required raw datasets and their provenance
records exist in reproducible form without manual corruption of source data.
