# README Polling

Last updated: 2026-05-09

## Source
- Primary raw source: DAWUM API (`https://api.dawum.de/`).
- Attribution note: DAWUM publishes Open Data under ODC-ODbL; thesis/report outputs that use this data should include DAWUM attribution.

## Outputs
- Raw flattened survey-party rows:
  - `data/polling/raw/afd_polling_raw_dawum.csv`
- Processed Bundestag AfD poll-level rows:
  - `data/polling/processed/afd_bundestag_polls_dawum.csv`
  - `data/polling/processed/afd_bundestag_polls_dawum.parquet`
- Full monthly AfD polling series (latest available DAWUM coverage):
  - `data/polling/processed/afd_polling_monthly.csv`
  - `data/polling/processed/afd_polling_monthly.parquet`
- Analysis-window monthly AfD polling series (aligned to media corpus window end):
  - `data/polling/processed/afd_polling_monthly_2017_2025.csv`
  - `data/polling/processed/afd_polling_monthly_2017_2025.parquet`
- Combined monthly polling series (historical manual + DAWUM):
  - `data/polling/processed/afd_polling_monthly_combined_2013_2025.csv`
  - `data/polling/processed/afd_polling_monthly_combined_2013_2025.parquet`
- Manual historical supplement (pre-DAWUM, Wahlrecht-based):
  - `data/polling/manual/afd_polling_historical_manual_polllevel.csv`
  - `data/polling/manual/afd_polling_historical_manual_monthly.csv`
  - `data/polling/manual/afd_polling_historical_manual_monthly.parquet`

## Full vs Trimmed
- Full DAWUM files preserve the complete available DAWUM pull for reproducibility.
- `afd_polling_monthly_2017_2025.*` is the analysis-ready version for merge work with media-corpus indicators because the media corpus ends at `2025-12`.
- `afd_polling_monthly_combined_2013_2025.*` extends coverage using a documented source boundary:
  - 2013-09..2016-12: manual historical Wahlrecht supplement
  - 2017-01..2025-12: DAWUM

## Date Logic
- `poll_date` is built with fallback order:
  - midpoint of `fieldwork_start` and `fieldwork_end` (preferred),
  - else `fieldwork_end`,
  - else `published_date`.

## Monthly Aggregation
- Current monthly aggregation is intentionally simple and transparent:
  - unweighted mean and median (`afd_poll_support_mean`, `afd_poll_support_median`),
  - plus min, max, standard deviation, `n_polls`, and `n_pollsters`.

## Limitations
- DAWUM monthly coverage starts later than the media corpus (which starts in 2013-01).
- Current DAWUM-based monthly polling series starts in 2017-01.
- The DAWUM-based series therefore does not cover the Cologne 2016 shock period.
- Cologne-period interpretation can rely on media/shock corpus evidence unless a separate historical polling supplement is added.
- Historical supplement may be required later for 2013-2016 analyses.
- Historical supplement rows should keep source labels and should not be silently mixed with DAWUM without explicit provenance fields.
