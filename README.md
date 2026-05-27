# AfD Project

## Project Purpose
This repository contains the thesis workflow on AfD polling support, media salience, framing/content indicators, and a supplementary media tone layer.

## Minimal Navigation
- Primary project guide: `README.md` (this file)
- Data map and canonical files: `data/README.md`
- Notebook map and outputs: `notebooks/README.md`

Key thesis-facing notes:
- `docs/final_empirical_results_summary.md`
- `docs/supplementary_media_tone_results_note.md`
- `docs/pre_writing_empirical_synthesis_note.md`

## Main Structure
- `Corpora/`: source corpus layer (monthly main corpus + shock corpora)
- `archive_pipeline/`: archived post-retrieval technical pipeline stages
- `data/`: canonical analysis-ready tables and panel outputs
- `notebooks/`: analysis/reporting notebooks
- `figures/`: notebook-generated figure outputs
- `docs/`: interpretation and methods notes
- `scripts/`: rebuild helpers

## Canonical Final Outputs
- Main panel:
  - `data/panel/monthly_full_analysis_panel_2013_2025.parquet`
  - `data/panel/monthly_full_analysis_panel_with_tone_2013_2025.parquet`
- Synthesis tables:
  - `data/panel/thesis_master_shock_results_table.csv`
  - `data/panel/thesis_dataset_counts_summary.csv`
- Synthesis note:
  - `docs/pre_writing_empirical_synthesis_note.md`

## Rebuild Commands
Clean layer refresh:
- `python scripts/build_postretrieval_dataset.py`
- `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`

Salience rebuild:
- `python scripts/build_monthly_media_salience_indicator.py`

Main corpus processing (only when corpus batches change):
- `python "Corpora/Main Corpus/run_main_corpus.py"`
- full reprocess: `python "Corpora/Main Corpus/run_main_corpus.py" --rerun --reextract`
- target month example: `python "Corpora/Main Corpus/run_main_corpus.py" --only 2021-09 --rerun --reextract`

Note:
- Corpus scripts read source PDFs from `raw_unarchive` folders.
- Shock-specific corpora (for example Cologne) also read only from `raw_unarchive`; run their local `audit_*.py` then `build_clean_*.py` scripts after archive updates.

## Polling Provenance Boundary
- DAWUM is the primary source from `2017-01` onward.
- Historical manual supplement (Wahlrecht-based) covers `2013-09` to `2016-12`.
