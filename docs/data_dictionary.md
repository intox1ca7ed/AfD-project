# Data Dictionary (Research-Facing)

Updated: 2026-05-07T00:00:00

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
- Notes:
  - `kept_article_count` is the cleaned downloaded sample size, not the final monthly salience volume measure.

## 4) `data/monthly_summary.csv`
- Purpose: Lightweight inspection/export version of monthly summary.
- Row unit: One month.

## 5) Descriptive Tables
- Folder: `data/descriptive_tables/`
- Purpose: Supporting descriptive/QC tables used in reporting and figure generation.

## 6) `data/monthly_media_salience_indicator.csv` and `.parquet`
- Purpose: Monthly salience and sample-size diagnostics with manual Nexis totals.
- Row unit: One month (`2013-01` to `2025-12`).
- Primary salience columns:
- `nexis_total_results`: monthly Nexis total results for final query + source basket + filters.
- `media_salience_volume_raw`: direct copy of `nexis_total_results`.
- `media_salience_volume_log1p`: `log(1 + nexis_total_results)`.
- `media_salience_volume_z`: z-score of `nexis_total_results` (population SD, `ddof=0`).
- Sample-size diagnostic columns:
- `raw_article_count`: downloaded monthly sample size (manual authoritative count after merge).
- `kept_article_count`: cleaned downloaded sample size from corpus QC/dedup output.
- `cleaned_sample_size`: alias of `kept_article_count` for clarity.
- `cleaned_sample_log1p`: `log(1 + cleaned_sample_size)`.
- `cleaned_sample_z`: z-score of `cleaned_sample_size` (population SD, `ddof=0`).
- Retrieval and coverage diagnostics:
- `download_fraction`: `raw_article_count / nexis_total_results` (NaN when denominator is 0/missing).
- `cleaned_sample_fraction`: `kept_article_count / nexis_total_results` (NaN when denominator is 0/missing).
- `retrieval_mismatch_flag`: `raw_article_count > nexis_total_results`.
- `high_download_sample_flag`: `raw_article_count > 50`.
