# Reproducibility Readme

## 1) Project Structure and Roles
- `Corpora/`: raw and protocol-level corpus assets.
  - `Corpora/Main Corpus/`: monthly main corpus folders (`2013-01` ... `2025-12`) and per-month QC/clean outputs.
  - `Corpora/Cologne`, `Corpora/Chemnitz`, `Corpora/Corrective Revelation`: shock corpora and their QC assets.
  - `Corpora/corpora-protocol.md`: protocol version reference (`v2`).
- `freeze/`: retrieval freeze stage outputs and freeze script.
- `master_tables/`: article-level master tables (all + kept), dictionary, and build log.
- `monthly_tables/`: monthly summary dataset, dictionary, and build log.
- `descriptive_package/`: descriptive report, QC log, tables, and figures.
- `indicator_prep/`: indicator blueprint/schema and indicator-ready placeholder tables.
- `workflow/`: pipeline configuration and runner.
- `logs/`: centralized run logs from pipeline execution.

## 2) Raw vs Frozen vs Derived
- Raw/Source (must remain untouched):
  - ZIP archives in corpus folders.
  - Source PDF copies as originally retrieved (including `raw_unarchive*` where retained).
- Frozen stage artifacts:
  - `freeze/retrieval_freeze_note.txt`
  - `freeze/retrieval_freeze_manifest.csv`
  - `freeze/retrieval_freeze_checks.txt`
- Derived analytical outputs (script-generated only):
  - `master_tables/*`
  - `monthly_tables/*`
  - `descriptive_package/*`
  - `indicator_prep/*`

## 3) Script-to-Output Mapping
- `freeze/build_retrieval_freeze.py`:
  - `freeze/retrieval_freeze_note.txt`
  - `freeze/retrieval_freeze_manifest.csv`
  - `freeze/retrieval_freeze_checks.txt`
- `master_tables/build_master_articles.py`:
  - `master_articles_all(.csv/.parquet)`
  - `master_articles_kept(.csv/.parquet)`
  - `master_articles_data_dictionary.txt`
  - `master_articles_build_log.txt`
- `monthly_tables/build_monthly_summary_main.py`:
  - `monthly_summary_main_corpus(.csv/.parquet)`
  - `monthly_summary_data_dictionary.txt`
  - `monthly_summary_build_log.txt`
- `descriptive_package/build_descriptive_qc.py`:
  - `descriptive_statistics_report.md`
  - `descriptive_qc_log.txt`
  - `descriptive_package/tables/*.csv`
  - `descriptive_package/figures/*.png`
- `indicator_prep/build_indicator_prep.py`:
  - `indicator_blueprint.txt`
  - `indicator_ready_schema.txt`
  - `*_indicator_ready(.csv/.parquet)`
  - `indicator_prep_build_log.txt`
- `workflow/run_pipeline.py`:
  - centralized run logs in `logs/`

## 4) Canonical Outputs
- Freeze stage canonical: `freeze/retrieval_freeze_manifest.csv`
- Article stage canonical: `master_tables/master_articles_all.parquet` (CSV as compatibility export)
- Monthly stage canonical: `monthly_tables/monthly_summary_main_corpus.parquet` (CSV as compatibility export)
- Descriptive stage canonical memo: `descriptive_package/descriptive_statistics_report.md`
- Indicator design canonical docs: `indicator_prep/indicator_blueprint.txt`, `indicator_prep/indicator_ready_schema.txt`

## 5) What Must Never Be Manually Edited
- Any source ZIP/PDF corpus file.
- `freeze/retrieval_freeze_manifest.csv` after freeze publication (unless creating a new documented freeze version).
- Core analytical tables (`master_articles_*`, `monthly_summary_main_corpus*`) by manual spreadsheet edits.
- Placeholder indicator columns should remain null until real modeling scripts populate them.

## 6) Workflow Discipline
- Always regenerate derived outputs via scripts.
- Do not use ad hoc notebook-only transformations for canonical outputs unless exported and script-equivalent.
- Keep naming stable and explicit (`master_articles_all`, `monthly_summary_main_corpus`, etc.).
- Preserve `article_id` and `month_id` semantics across versions.

## 7) Logging Convention
- Per-stage build logs remain in each stage folder.
- Centralized pipeline logs are written to `logs/`:
  - `pipeline_run_YYYYMMDD_HHMMSS.log`
  - `pipeline_latest.log`
  - `pipeline_runs_summary.csv`
- Each run log records:
  - start/end time
  - script path
  - input paths
  - expected output paths
  - stdout/stderr
  - status and warnings/failures

## 8) Recommended Single-Command Rebuild
From project root:
- `python workflow/run_pipeline.py`

This executes the full post-retrieval pipeline in order using `workflow/pipeline_config.json`.
