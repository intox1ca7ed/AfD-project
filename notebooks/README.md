# README Notebooks

Last updated: 2026-05-08

## Purpose
- Stores analysis and reporting notebooks.
- Keeps notebook work in the post-retrieval layer (no corpus rebuilding from PDFs here).

## Current Snapshot
- Main notebook: `notebooks/01_corpus_descriptive_report.ipynb`.
- Polling-stage notebook: `notebooks/02_afd_polling_preparation.ipynb`.
- Merge notebook: `notebooks/03_monthly_salience_polling_merge.ipynb`.
- Event-window diagnostics notebook: `notebooks/04_event_window_descriptive_diagnostics.ipynb`.
- Combined polling/panel extension notebook: `notebooks/05_combined_polling_panel_and_cologne_extension.ipynb`.
- Exported PDF snapshot exists: `notebooks/01_corpus_descriptive_report.pdf`.
- Notebook-specific figure output folders:
  - `figures/01_notebook_figures/`
  - `figures/02_notebook_figures/`
  - `figures/03_notebook_figures/`
  - `figures/04_notebook_figures/`
  - `figures/05_notebook_figures/`

## How To Run
- Open and run in Jupyter/VS Code using the `ds_env` kernel.
- Current reporting notebook can be executed top-to-bottom; it writes:
  - `data/indicators/monthly_media_salience_indicator.csv`
  - `data/indicators/monthly_media_salience_indicator.parquet`
  - figures under `figures/01_notebook_figures/`
- Polling preparation notebook writes:
  - `data/polling/raw/afd_polling_raw_dawum.csv`
  - `data/polling/processed/afd_bundestag_polls_dawum.csv`
  - `data/polling/processed/afd_bundestag_polls_dawum.parquet`
  - `data/polling/processed/afd_polling_monthly.csv`
  - `data/polling/processed/afd_polling_monthly.parquet`
  - `data/polling/processed/afd_polling_monthly_2017_2025.csv`
  - `data/polling/processed/afd_polling_monthly_2017_2025.parquet`
  - figures under `figures/02_notebook_figures/`
- Merge notebook writes:
  - `data/panel/monthly_salience_polling_panel.csv`
  - `data/panel/monthly_salience_polling_panel.parquet`
  - figures under `figures/03_notebook_figures/`
- Event-window notebook writes:
  - `data/panel/event_window_descriptive_summary.csv`
  - figures under `figures/04_notebook_figures/`
- Combined extension notebook writes:
  - `data/polling/processed/afd_polling_monthly_combined_2013_2025.csv`
  - `data/polling/processed/afd_polling_monthly_combined_2013_2025.parquet`
  - `data/panel/monthly_salience_polling_panel_combined_2013_2025.csv`
  - `data/panel/monthly_salience_polling_panel_combined_2013_2025.parquet`
  - `data/panel/event_window_descriptive_summary_combined_2013_2025.csv`
  - figures under `figures/05_notebook_figures/`

## Dependencies
- Upstream inputs:
  - `data/corpus/master_articles.parquet`
  - `data/corpus/monthly_summary.csv` or `.parquet`
  - `data/corpus/monthly_nexis_volume.csv`
- Downstream outputs:
  - indicator files, polling files, and notebook figures

## Update Routine (Manual)
- If notebook logic, outputs, or figure names change:
  - update this file's snapshot section
  - confirm output paths still match current practice

## Notes
- Treat notebooks as reporting/analysis layer, not canonical corpus-construction pipeline.
