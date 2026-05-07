# README Notebooks

Last updated: 2026-05-07

## Purpose
- Stores analysis and reporting notebooks.
- Keeps notebook work in the post-retrieval layer (no corpus rebuilding from PDFs here).

## Current Snapshot
- Main notebook: `notebooks/01_corpus_descriptive_report.ipynb`.
- Exported PDF snapshot exists: `notebooks/01_corpus_descriptive_report.pdf`.
- Notebook-specific figure output folder: `figures/01_notebook_figures/`.

## How To Run
- Open and run in Jupyter/VS Code using the `ds_env` kernel.
- Current reporting notebook can be executed top-to-bottom; it writes:
  - `data/monthly_media_salience_indicator.csv`
  - `data/monthly_media_salience_indicator.parquet`
  - figures under `figures/01_notebook_figures/`

## Dependencies
- Upstream inputs:
  - `data/master_articles.parquet`
  - `data/monthly_summary.csv` or `.parquet`
  - `data/monthly_nexis_volume.csv`
- Downstream outputs:
  - indicator files and notebook figures

## Update Routine (Manual)
- If notebook logic, outputs, or figure names change:
  - update this file's snapshot section
  - confirm output paths still match current practice

## Notes
- Treat notebooks as reporting/analysis layer, not canonical corpus-construction pipeline.
