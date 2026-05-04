# Data Dictionary (Research-Facing)

Updated: 2026-05-04T14:38:31

## 1) `data/master_articles.parquet`
- Purpose: Canonical article-level audit dataset for post-retrieval analysis.
- Row unit: One parsed article record (keep/drop/review).
- Typical use: QC checks, filtered subsets, aggregation to monthly indicators.
- Key columns:
- `article_id`
- `corpus_name`
- `batch_id`
- `date`
- `month`
- `publication`
- `title_original`
- `word_count`
- `keep_drop_review`
- `drop_reason`
- `duplicate_category`
- `malformed_flag`
- Notes:
  - Includes full text body column (`text_body`) for advanced text workflows.
  - Stable ID: `article_id` is deterministic and script-built.

## 2) `data/master_articles_light.csv`
- Purpose: Lightweight inspection/export table.
- Row unit: Same as master table.
- Typical use: quick inspection, spreadsheet-safe checks.
- Notes:
  - Derived from canonical master table.
  - Full text column removed to keep file lighter.

## 3) `data/monthly_summary.parquet`
- Purpose: Canonical one-row-per-month structural summary (Main Corpus).
- Row unit: One month (`2013-01` to `2025-12`).
- Typical use: time-series analysis, merge-ready base for polling linkage.
- Key columns:
- `month_id`
- `raw_article_count`
- `kept_article_count`
- `dropped_article_count`
- `keep_share`
- `duplicate_burden`
- `source_top1`
- `source_top1_count`
- `freeze_status`

## 4) `data/monthly_summary.csv`
- Purpose: Lightweight inspection/export version of monthly summary.
- Row unit: One month.

## 5) Descriptive Tables
- Folder: `data/descriptive_tables/`
- Purpose: Supporting descriptive/QC tables used in reporting and figure generation.
