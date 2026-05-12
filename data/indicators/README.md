# README Indicators

Last updated: 2026-05-11

## Purpose
- Stores indicator-stage outputs derived from the cleaned corpus and panel datasets.
- Includes both volume-based salience indicators and first-pass text/content indicators.

## Core Files
- Volume salience:
  - `data/indicators/monthly_media_salience_indicator.csv`
  - `data/indicators/monthly_media_salience_indicator.parquet`
- Text/content indicators:
  - `data/indicators/article_text_content_indicators.csv`
  - `data/indicators/article_text_content_indicators.parquet`
  - `data/indicators/monthly_text_content_indicators.csv`
  - `data/indicators/monthly_text_content_indicators.parquet`
  - `data/indicators/text_indicator_event_window_summary.csv`

## Method Notes (Text Indicators)
- Built only from kept articles in `data/corpus/master_articles.parquet`.
- Uses transparent dictionary-based German text normalization and term counting.
- Produces article-level counts, per-1000-word rates, binary flags, and simple composites.
- Monthly output is an aggregation of article-level indicators.
- Notebook 07 includes explicit German umlaut normalization assertions (`ä/ö/ü/ß` -> `ae/oe/ue/ss`).
- Monthly text indicator outputs are validated against full expected coverage `2013-01` through `2025-12` (156 months).

## Refresh Note
- A corrected `2019-09` archive replaced an earlier duplicated-month issue.
- Current indicator outputs were regenerated after the correction and are the authoritative working version.

## Limitations
- First-pass dictionary indicators are transparent but approximate.
- German inflection and compound forms can create false positives/negatives.
- Indicators are descriptive and exploratory; they are not causal evidence by themselves.
