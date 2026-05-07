# AfD Project

## Project Overview
This repository supports the empirical thesis workflow on media shocks and AfD support in Germany.

## Section Navigation
- `notebooks/README.md`
- `scripts/README.md`
- `data/README.md`
- `archive_pipeline/README.md`
- `Corpora/README.md`
- `docs/README.md`
- `figures/README.md`

## Main Folders
- `Corpora/`: source corpus layer (main monthly corpus + shock corpora).
- `data/`: analysis-ready canonical datasets and descriptive tables.
- `figures/`: research-facing descriptive figures.
- `docs/`: research-facing documentation and summaries.
- `scripts/`: project-level helper/rebuild scripts.
- `notebooks/`: analysis notebook workspace.
- `archive_pipeline/`: archived technical pipeline artifacts for audit/reproducibility.

## Main Datasets
- `data/master_articles.parquet` (canonical article-level table)
- `data/master_articles_light.csv` (light inspection export)
- `data/monthly_summary.parquet` (canonical monthly structure)
- `data/monthly_summary.csv` (light inspection export)
- `data/monthly_nexis_volume.csv` (manual monthly Nexis totals + download counts)
- `data/monthly_media_salience_indicator.csv` (volume-based salience indicators)

## Reproducibility
- Refresh clean outputs from archived artifacts:
  - `python scripts/build_postretrieval_dataset.py`
- Run archived technical pipeline first, then refresh:
  - `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`

## Important Rules
- Do not manually edit source corpus files in `Corpora/` unless intentionally reprocessing corpus batches.
- Do not manually edit canonical derived datasets in `data/`.
- Regenerate outputs via scripts/notebooks designed for that layer.
