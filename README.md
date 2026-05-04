# AfD Project

## Project Overview
This repository supports the empirical thesis workflow on media shocks and AfD support in Germany.

## Main Folders
- `Corpora/`: immutable source corpus layer (main monthly corpus + shock corpora).
- `data/`: analysis-ready canonical datasets and descriptive tables.
- `figures/`: research-facing descriptive figures.
- `docs/`: research-facing documentation and summaries.
- `scripts/`: single-entry rebuild/refresh scripts.
- `notebooks/`: analysis notebook workspace.
- `archive_pipeline/`: archived technical pipeline artifacts for audit/reproducibility.

## Main Datasets
- `data/master_articles.parquet` (canonical article-level)
- `data/master_articles_light.csv` (light inspection export)
- `data/monthly_summary.parquet` (canonical monthly-level)
- `data/monthly_summary.csv` (light inspection export)

## Reproducibility
- Technical post-retrieval artifacts are preserved under `archive_pipeline/`.
- To refresh clean outputs from archived artifacts:
  - `python scripts/build_postretrieval_dataset.py`
- To run archived technical pipeline first, then refresh:
  - `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`

## Important Rules
- Do not manually edit raw corpus files in `Corpora/`.
- Do not manually edit canonical derived datasets in `data/`.
- Regenerate outputs via scripts.

## Archive Location
- Original post-retrieval build folders/logs are intentionally preserved in `archive_pipeline/`.
