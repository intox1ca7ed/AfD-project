# README Figures

Last updated: 2026-05-07

## Purpose
- Stores generated figures for descriptive reporting and diagnostics.

## Current Snapshot
- Root-level figures: synced from archived descriptive stage.
- Notebook-specific figures: `figures/01_notebook_figures/`.

## Figure Convention
- Each notebook writes to its own subfolder:
  - `notebooks/01_corpus_descriptive_report.ipynb` -> `figures/01_notebook_figures/`
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
