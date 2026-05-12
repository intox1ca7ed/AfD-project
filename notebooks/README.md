# README Notebooks

Last updated: 2026-05-11

## Purpose
- Stores analysis and reporting notebooks.
- Keeps notebook work in the post-retrieval layer (no corpus rebuilding from PDFs here).

## Current Snapshot
- Main notebook: `notebooks/01_corpus_descriptive_report.ipynb`.
- Polling-stage notebook: `notebooks/02_afd_polling_preparation.ipynb`.
- Merge notebook: `notebooks/03_monthly_salience_polling_merge.ipynb`.
- Event-window diagnostics notebook: `notebooks/04_event_window_descriptive_diagnostics.ipynb`.
- Combined polling/panel extension notebook: `notebooks/05_combined_polling_panel_and_cologne_extension.ipynb`.
- Lag diagnostics notebook: `notebooks/06_lag_diagnostics_descriptive.ipynb`.
- Text-content indicator construction notebook: `notebooks/07_text_content_indicator_construction.ipynb`.
- Full panel + text indicator analysis notebook: `notebooks/08_full_panel_text_indicator_analysis.ipynb`.
- Final descriptive diagnostics notebook: `notebooks/09_final_descriptive_diagnostics.ipynb`.
- Exported PDF snapshot exists: `notebooks/01_corpus_descriptive_report.pdf`.
- Notebook-specific figure output folders:
  - `figures/01_notebook_figures/`
  - `figures/02_notebook_figures/`
  - `figures/03_notebook_figures/`
  - `figures/04_notebook_figures/`
  - `figures/05_notebook_figures/`
  - `figures/06_notebook_figures/`
  - `figures/07_notebook_figures/`
  - `figures/08_notebook_figures/`
  - `figures/09_notebook_figures/`

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
- Lag diagnostics notebook writes:
  - `data/panel/lag_diagnostics_descriptive_summary.csv`
  - figures under `figures/06_notebook_figures/`
- Text-content indicator notebook writes:
  - `data/indicators/article_text_content_indicators.csv`
  - `data/indicators/article_text_content_indicators.parquet`
  - `data/indicators/monthly_text_content_indicators.csv`
  - `data/indicators/monthly_text_content_indicators.parquet`
  - `data/indicators/text_indicator_event_window_summary.csv`
  - figures under `figures/07_notebook_figures/`
  - includes explicit German umlaut normalization validation and monthly coverage checks for `2013-01`..`2025-12`
- Full panel + text indicator analysis notebook writes:
  - `data/panel/monthly_full_analysis_panel_2013_2025.csv`
  - `data/panel/monthly_full_analysis_panel_2013_2025.parquet`
  - `data/panel/full_panel_text_shock_window_summary.csv`
  - figures under `figures/08_notebook_figures/`
- Final descriptive diagnostics notebook writes:
  - `data/panel/final_descriptive_diagnostics.csv`
  - figures under `figures/09_notebook_figures/`
  - supports thesis-facing note: `docs/final_empirical_results_summary.md`

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
