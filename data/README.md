# README Data

Last updated: 2026-05-07

## Purpose
- Canonical analysis-ready datasets and supporting descriptive tables.

## Current Snapshot
- Main monthly coverage: `2013-01` to `2025-12` (156 months).
- Contains both corpus-structure datasets and salience indicator outputs.

## Canonical/Key Files

| File | Row Unit | Purpose | Main Producer | Main Consumer |
| --- | --- | --- | --- | --- |
| `data/master_articles.parquet` | one article | Canonical article-level table (all keep/drop/review) | `scripts/build_postretrieval_dataset.py` (from archive pipeline) | notebooks, downstream modeling |
| `data/master_articles_light.csv` | one article | Lightweight export without full text body | `scripts/build_postretrieval_dataset.py` | manual inspection |
| `data/monthly_summary.parquet` | one month | Canonical monthly corpus structure summary | `scripts/build_postretrieval_dataset.py` | notebooks, indicator prep |
| `data/monthly_summary.csv` | one month | Lightweight monthly export | `scripts/build_postretrieval_dataset.py` | quick checks/spreadsheets |
| `data/monthly_nexis_volume.csv` | one month | Manual Nexis total monthly results + manual download counts | manual entry | salience indicator build |
| `data/monthly_media_salience_indicator.csv` | one month | Volume-based salience indicators and retrieval diagnostics | `scripts/build_monthly_media_salience_indicator.py` (and notebook export) | merge-ready indicator workflows |
| `data/monthly_media_salience_indicator.parquet` | one month | Parquet version of salience indicator table | same as above | analysis pipelines |
| `data/descriptive_tables/` | multiple | Supporting descriptive/QC tables | archived descriptive stage | descriptive reporting |

## How To Run
- Refresh canonical data from archived pipeline artifacts:
  - `python scripts/build_postretrieval_dataset.py`
- Rebuild only salience indicator outputs:
  - `python scripts/build_monthly_media_salience_indicator.py`

## Dependencies
- Upstream:
  - `archive_pipeline/master_tables/*`
  - `archive_pipeline/monthly_tables/*`
  - manual `data/monthly_nexis_volume.csv`
- Downstream:
  - notebooks
  - reporting figures
  - indicator merge workflows

## Update Routine (Manual)
- When any canonical file is added/renamed/repurposed:
  - update this file's table
  - keep row-unit and producer/consumer fields accurate

## Notes
- Generated canonical files should be rebuilt via scripts, not manually edited.
