# README Scripts

Last updated: 2026-05-07

## Purpose
- Stores project-level helper scripts for rebuilding or refreshing post-retrieval outputs.

## Current Snapshot
- `scripts/build_postretrieval_dataset.py`
  - Refreshes clean layer in `data/`, `figures/`, `docs/` from `archive_pipeline/`.
  - Optional flag `--run-archived-pipeline` runs `archive_pipeline/workflow/run_pipeline.py` first.
- `scripts/build_monthly_media_salience_indicator.py`
  - Builds monthly salience indicators from `monthly_summary` + `monthly_nexis_volume`.
  - Writes `data/monthly_media_salience_indicator.csv/.parquet`.

## How To Run
- Refresh clean layer only:
  - `python scripts/build_postretrieval_dataset.py`
- Full archived pipeline + refresh:
  - `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`
- Rebuild salience indicator only:
  - `python scripts/build_monthly_media_salience_indicator.py`

## Dependencies
- Upstream:
  - `archive_pipeline/*` for refresh script
  - `data/monthly_summary.*` and `data/monthly_nexis_volume.csv` for salience builder
- Downstream:
  - `data/*`, `figures/*`, `docs/*` outputs depending on script

## Update Routine (Manual)
- If script names, arguments, or output targets change, update this file immediately.

## Notes
- Scripts are intended to regenerate outputs; avoid manual editing of generated files.
