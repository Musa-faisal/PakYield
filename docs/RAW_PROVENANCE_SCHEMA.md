# PakYield Raw Provenance Schema

Each acquired raw artifact should have one provenance record.

## Required Fields

| Field | Meaning |
|---|---|
| `dataset_id` | PakYield dataset identifier |
| `source_authority` | Organization responsible for the source |
| `acquisition_source` | Website, service, archive, or provider used |
| `source_reference` | Source URL or equivalent reference |
| `retrieved_at_utc` | UTC acquisition timestamp |
| `raw_file_name` | Original or deterministic stored filename |
| `raw_relative_path` | Repository-relative raw path |
| `file_format` | xlsx, csv, pdf, html, json, etc. |
| `sha256` | SHA-256 checksum of stored artifact |
| `file_size_bytes` | Stored artifact size |
| `status` | SUCCESS or FAILED |
| `notes` | Known acquisition or source issues |

## Rules

1. A successful provenance record must refer to a real local artifact.
2. A checksum must be calculated from the stored raw artifact.
3. Retrieval timestamps must not be invented retroactively.
4. URLs or references must not be fabricated.
5. Schema changes belong in notes or later validation records.
6. Failed acquisitions may be recorded without pretending that a raw artifact
   exists.
