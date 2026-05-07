# README Archive Pipeline

Last updated: 2026-05-07

## Purpose
- Stores archived technical post-retrieval pipeline stages for reproducibility and audit.

## Current Snapshot
- Stage folders:
  - `archive_pipeline/freeze/`
  - `archive_pipeline/master_tables/`
  - `archive_pipeline/monthly_tables/`
  - `archive_pipeline/descriptive_package/`
  - `archive_pipeline/indicator_prep/`
  - `archive_pipeline/workflow/`
  - `archive_pipeline/logs/`
- Pipeline orchestrator: `archive_pipeline/workflow/run_pipeline.py`
- Pipeline config: `archive_pipeline/workflow/pipeline_config.json`

## How To Run
- Full archived pipeline:
  - `python archive_pipeline/workflow/run_pipeline.py`
- Or via wrapper refresh script:
  - `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`

## Dependencies
- Upstream:
  - `Corpora/` retrieval/QC outputs
- Downstream:
  - `data/` canonical clean layer (via refresh script)
  - `docs/descriptive_statistics_report.md`
  - `figures/` synchronized outputs

## Update Routine (Manual)
- If stage scripts, output names, or pipeline step order change, update this file.

## Notes
- Treat archived pipeline outputs as script-generated artifacts.
