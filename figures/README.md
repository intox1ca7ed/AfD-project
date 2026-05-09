# README Figures

Last updated: 2026-05-09

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
  - `figures/05a_historical_polling_sanity_check/`

## Figure Convention
- Each notebook writes to its own subfolder:
- `notebooks/01_corpus_descriptive_report.ipynb` -> `figures/01_notebook_figures/`
- `notebooks/02_afd_polling_preparation.ipynb` -> `figures/02_notebook_figures/`
- `notebooks/03_monthly_salience_polling_merge.ipynb` -> `figures/03_notebook_figures/`
- `notebooks/04_event_window_descriptive_diagnostics.ipynb` -> `figures/04_notebook_figures/`
- `notebooks/05_combined_polling_panel_and_cologne_extension.ipynb` -> `figures/05_notebook_figures/`
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
