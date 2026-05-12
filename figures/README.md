# README Figures

Last updated: 2026-05-12

## Purpose
- Stores generated figures for descriptive reporting and diagnostics.

## Current Snapshot
- Root-level figures: synced from archived descriptive stage.
- Notebook-specific figures:
  - `figures/01_notebook_figures/`
  - `figures/02_notebook_figures/`
  - `figures/03_notebook_figures/`
  - `figures/04_notebook_figures/`
  - `figures/05_notebook_figures/`
  - `figures/06_notebook_figures/`
  - `figures/07_notebook_figures/`
  - `figures/08_notebook_figures/`
  - `figures/09_notebook_figures/`
  - `figures/10_notebook_figures/`
  - `figures/05a_historical_polling_sanity_check/`

## Figure Convention
- Each notebook writes to its own subfolder:
- `notebooks/01_corpus_descriptive_report.ipynb` -> `figures/01_notebook_figures/`
- `notebooks/02_afd_polling_preparation.ipynb` -> `figures/02_notebook_figures/`
- `notebooks/03_monthly_salience_polling_merge.ipynb` -> `figures/03_notebook_figures/`
- `notebooks/04_event_window_descriptive_diagnostics.ipynb` -> `figures/04_notebook_figures/`
- `notebooks/05_combined_polling_panel_and_cologne_extension.ipynb` -> `figures/05_notebook_figures/`
- `notebooks/06_lag_diagnostics_descriptive.ipynb` -> `figures/06_notebook_figures/`
- `notebooks/07_text_content_indicator_construction.ipynb` -> `figures/07_notebook_figures/`
- `notebooks/08_full_panel_text_indicator_analysis.ipynb` -> `figures/08_notebook_figures/`
- `notebooks/09_final_descriptive_diagnostics.ipynb` -> `figures/09_notebook_figures/`
- `notebooks/10_supplementary_media_tone_indicator.ipynb` -> `figures/10_notebook_figures/`
- `scripts/check_historical_manual_polling.py` -> `figures/05a_historical_polling_sanity_check/`
- Use descriptive filenames that encode metric/context.

## How To Regenerate
- Archived descriptive figures refresh:
  - `python scripts/build_postretrieval_dataset.py`
- Notebook figures refresh:
  - rerun notebook cells that create and save figures

## Dependencies
- Upstream:
  - `data/*` and/or `archive_pipeline/descriptive_package/*`
- Downstream:
  - report writing
  - presentation artifacts

## Update Routine (Manual)
- If figure naming conventions or notebook figure folders change, update this file.

## Notes
- Treat figure files as generated artifacts; regenerate when data/logic changes.
