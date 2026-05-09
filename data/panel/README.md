# README Panel

Last updated: 2026-05-09

## Purpose
- Stores merged monthly descriptive panel files combining media salience and AfD polling.
- This is a pre-modeling/descriptive integration layer.

## Main Files
- `data/panel/monthly_salience_polling_panel.csv`
- `data/panel/monthly_salience_polling_panel.parquet`
- `data/panel/event_window_descriptive_summary.csv`
- `data/panel/monthly_salience_polling_panel_combined_2013_2025.csv`
- `data/panel/monthly_salience_polling_panel_combined_2013_2025.parquet`
- `data/panel/event_window_descriptive_summary_combined_2013_2025.csv`

## Inputs Used
- `data/indicators/monthly_media_salience_indicator.parquet` (fallback: `.csv`)
- `data/polling/processed/afd_polling_monthly_2017_2025.parquet` (fallback: `.csv`)
- `data/polling/processed/afd_polling_monthly_combined_2013_2025.parquet` for the extended panel stage

## Coverage
- DAWUM-only monthly panel range: `2017-01` to `2025-12` (108 rows).
- DAWUM-only event-window summary includes Chemnitz and Correctiv local pre/post descriptive windows (±3 and ±6 months).
- Combined monthly panel range: `2013-09` to `2025-12` (148 rows), with explicit historical-manual vs DAWUM source boundary.

## Key Variables
- Polling side:
  - `afd_poll_support_mean`, `afd_poll_support_median`, `afd_poll_support_sd`
  - `n_polls`, `n_pollsters`
  - `afd_poll_support_z` (DAWUM-only panel) and `afd_poll_support_z_combined` (combined panel)
- Media side:
  - `nexis_total_results`
  - `media_salience_volume_raw`, `media_salience_volume_log1p`, `media_salience_volume_z`
  - sample/retrieval diagnostics (`raw_article_count`, `download_fraction`, `kept_article_count`, etc.)

## Interpretation Notes
- Panels are descriptive only and do not imply causal effects.
- Media salience is volume-based (Nexis monthly total results).
- DAWUM coverage begins in 2017, so Cologne/2016 is outside the DAWUM-only panel.
- Combined panel outputs include Cologne 2016 descriptively via the manual historical supplement segment.
- Event-window outputs are exploratory diagnostics and are not event-study estimators.
