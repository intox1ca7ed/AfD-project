# Scripts Overview

## Main entrypoint
- `python scripts/build_postretrieval_dataset.py`

This refreshes the clean research-facing layer from archived pipeline artifacts:
- `data/`
- `figures/`
- `docs/`

## Optional full rebuild + refresh
- `python scripts/build_postretrieval_dataset.py --run-archived-pipeline`

This first runs the archived pipeline script (`archive_pipeline/workflow/run_pipeline.py`), then refreshes clean outputs.

## Logging
- Script writes run logs to `logs/build_postretrieval_dataset_*.log`.

## Notes
- Raw corpora in `Corpora/` are not modified by this script.
- Core technical pipeline assets are read from `archive_pipeline/`.
