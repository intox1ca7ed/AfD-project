# README Data

Last updated: 2026-05-13

## Purpose
- Stores canonical analysis-ready datasets, indicators, polling/election inputs, and descriptive support tables.

## Current Structure
- `data/corpus/`: corpus-derived canonical tables.
- `data/indicators/`: finalized indicator outputs.
- `data/dictionaries/`: canonical grouped regex dictionaries for text-content indicators.
- `data/polling/raw/`: unchanged raw polling source files.
- `data/polling/processed/`: cleaned/aggregated monthly polling outputs.
- `data/polling/manual/`: manual historical polling supplement files (Wahlrecht-based pre-DAWUM).
- `data/panel/`: merged monthly descriptive panel outputs.
- `data/elections/`: election anchor benchmark files.
- `data/descriptive_tables/`: descriptive/QC support tables.

## Canonical/Key Files

| File | Row Unit | Purpose | Main Producer | Main Consumer |
| --- | --- | --- | --- | --- |
| `data/corpus/master_articles.parquet` | one article | Canonical article-level table (all keep/drop/review) | `scripts/build_postretrieval_dataset.py` | notebooks, downstream modeling |
| `data/corpus/master_articles_light.csv` | one article | Lightweight export without full text body | `scripts/build_postretrieval_dataset.py` | manual inspection |
| `data/corpus/monthly_summary.parquet` | one month | Canonical monthly corpus structure summary | `scripts/build_postretrieval_dataset.py` | notebooks, indicator workflows |
| `data/corpus/monthly_summary.csv` | one month | Lightweight monthly export | `scripts/build_postretrieval_dataset.py` | quick checks/spreadsheets |
| `data/corpus/monthly_nexis_volume.csv` | one month | Manual Nexis total monthly results + manual download counts | manual entry | salience indicator build |
| `data/indicators/monthly_media_salience_indicator.csv` | one month | Volume-based salience indicator + diagnostics | `scripts/build_monthly_media_salience_indicator.py` and Notebook 01 | polling merge stage |
| `data/indicators/monthly_media_salience_indicator.parquet` | one month | Parquet version of salience indicator table | same as above | analysis pipelines |
| `data/dictionaries/text_indicator_term_patterns.json` | one dictionary config | Grouped canonical regex dictionaries (`migration`, `security`, `afd_far_right`, `remigration_democracy`, `negative_threat`) used for Notebook 07 indicator construction | Notebook 07 (loaded config) | article/monthly text-content indicator build |
| `data/indicators/article_text_content_indicators.csv` | one kept article | Dictionary-based article-level text/content indicators | Notebook 07 | monthly content aggregation |
| `data/indicators/article_text_content_indicators.parquet` | one kept article | Parquet version of article-level text/content indicators | Notebook 07 | analysis pipelines |
| `data/indicators/monthly_text_content_indicators.csv` | one month | Monthly aggregated dictionary-based text/content indicators | Notebook 07 | later panel merge stage |
| `data/indicators/monthly_text_content_indicators.parquet` | one month | Parquet version of monthly text/content indicators | Notebook 07 | analysis pipelines |
| `data/indicators/text_indicator_event_window_summary.csv` | one shock-window-indicator row | Descriptive pre/post text-indicator summaries for Cologne, Chemnitz, Correctiv | Notebook 07 | shock-window diagnostics |
| `data/indicators/article_media_tone_indicators.csv` | one kept article | Supplementary lexicon-based media tone proxy (article level) | Notebook 10 | monthly tone aggregation |
| `data/indicators/article_media_tone_indicators.parquet` | one kept article | Parquet version of article-level supplementary tone indicators | Notebook 10 | analysis pipelines |
| `data/indicators/monthly_media_tone_indicators.csv` | one month | Monthly aggregated supplementary media tone indicators | Notebook 10 | tone-augmented panel merge |
| `data/indicators/monthly_media_tone_indicators.parquet` | one month | Parquet version of monthly supplementary tone indicators | Notebook 10 | analysis pipelines |
| `data/polling/raw/afd_polling_raw_dawum.csv` | one poll row | Raw DAWUM polling extract (no transformation) | Notebook 02/manual import | polling processing |
| `data/polling/processed/afd_bundestag_polls_dawum.csv` | one poll row | Filtered Bundestag AfD poll-level dataset | Notebook 02 | monthly aggregation + diagnostics |
| `data/polling/processed/afd_bundestag_polls_dawum.parquet` | one poll row | Parquet version of poll-level Bundestag AfD dataset | Notebook 02 | analysis pipelines |
| `data/polling/processed/afd_polling_monthly.csv` | one month | Monthly aggregated AfD polling support | Notebook 02 | merge-ready empirical stage |
| `data/polling/processed/afd_polling_monthly.parquet` | one month | Parquet version of monthly polling output | Notebook 02 | analysis pipelines |
| `data/polling/processed/afd_polling_monthly_2017_2025.csv` | one month | Analysis-window monthly polling panel aligned to media corpus end (2025-12) | Notebook 02 | salience merge-ready panel |
| `data/polling/processed/afd_polling_monthly_2017_2025.parquet` | one month | Parquet version of analysis-window polling panel | Notebook 02 | analysis pipelines |
| `data/polling/processed/afd_polling_monthly_combined_2013_2025.csv` | one month | Combined monthly polling panel (historical manual 2013-09..2016-12 + DAWUM 2017-01..2025-12) | Notebook 05 | extended descriptive/event-window diagnostics |
| `data/polling/processed/afd_polling_monthly_combined_2013_2025.parquet` | one month | Parquet version of combined monthly polling panel | Notebook 05 | analysis pipelines |
| `data/polling/manual/afd_polling_historical_manual_polllevel.csv` | one poll row | Manual historical AfD polling supplement from Wahlrecht (pre-DAWUM) | manual extraction workflow | Cologne-period descriptive checks |
| `data/polling/manual/afd_polling_historical_manual_monthly.csv` | one month | Monthly aggregation of manual historical supplement | manual extraction workflow | descriptive extensions before 2017 |
| `data/polling/manual/afd_polling_historical_manual_monthly.parquet` | one month | Parquet version of manual historical monthly supplement | manual extraction workflow | analysis pipelines |
| `data/panel/monthly_salience_polling_panel.csv` | one month | Descriptive merged panel (media salience + AfD polling) | Notebook 03 | pre-modeling analysis |
| `data/panel/monthly_salience_polling_panel.parquet` | one month | Parquet version of merged salience-polling panel | Notebook 03 | analysis pipelines |
| `data/panel/event_window_descriptive_summary.csv` | one shock-window summary row | Local pre/post descriptive summaries for Chemnitz and Correctiv (±3/±6) | Notebook 04 | event-window diagnostics |
| `data/panel/monthly_salience_polling_panel_combined_2013_2025.csv` | one month | Combined salience-polling panel extended to include pre-2017 historical polling supplement | Notebook 05 | Cologne+Chemnitz+Correctiv descriptive timeline |
| `data/panel/monthly_salience_polling_panel_combined_2013_2025.parquet` | one month | Parquet version of combined salience-polling panel | Notebook 05 | analysis pipelines |
| `data/panel/event_window_descriptive_summary_combined_2013_2025.csv` | one shock-window summary row | Combined-panel pre/post descriptive summaries for Cologne, Chemnitz, Correctiv (±3/±6) | Notebook 05 | event-window diagnostics |
| `data/panel/lag_diagnostics_descriptive_summary.csv` | one sample-lag-variable row | Descriptive lag-correlation diagnostics (lags 0..6; combined + source-block subsets) | Notebook 06 | exploratory timing diagnostics |
| `data/panel/monthly_full_analysis_panel_2013_2025.csv` | one month | Full monthly analysis panel merging combined polling-salience panel with monthly text/content indicators | Notebook 08 | integrated descriptive/model-prep panel |
| `data/panel/monthly_full_analysis_panel_2013_2025.parquet` | one month | Parquet version of full monthly analysis panel | Notebook 08 | analysis pipelines |
| `data/panel/full_panel_text_shock_window_summary.csv` | one shock-window-variable row | Compact descriptive pre/post table (±3/±6) for AfD support and key text indicators | Notebook 08 | shock-window diagnostics |
| `data/panel/final_descriptive_diagnostics.csv` | one shock | Thesis-ready compact shock diagnostics table with expected mechanism and interpretation labels | Notebook 09 | final results write-up |
| `data/panel/monthly_full_analysis_panel_with_tone_2013_2025.csv` | one month | Full analysis panel extended with supplementary monthly tone indicators | Notebook 10 | supplementary mechanism diagnostics |
| `data/panel/monthly_full_analysis_panel_with_tone_2013_2025.parquet` | one month | Parquet version of tone-extended full panel | Notebook 10 | analysis pipelines |
| `data/panel/thesis_master_shock_results_table.csv` | one shock | Final pre-writing master shock table combining expected mechanisms and descriptive +/-3/+/-6 changes | Notebook 11 | thesis results drafting |
| `data/panel/thesis_master_shock_results_table.parquet` | one shock | Parquet version of final pre-writing master shock table | Notebook 11 | analysis pipelines |
| `data/panel/thesis_dataset_counts_summary.csv` | one row | Compact final dataset counts summary for methods/data reporting | Notebook 11 | thesis methods write-up |
| `data/panel/supplementary_tone_shock_window_summary.csv` | one shock-window-variable row | Supplementary tone-focused pre/post summaries (±3/±6) with framing/polling context | Notebook 10 | supplementary shock interpretation |
| `data/elections/afd_election_anchors.csv` | one election | Bundestag AfD Zweitstimme benchmark anchors | manual + docs guidance | benchmark overlays/checks |
| `data/descriptive_tables/` | multiple | Supporting descriptive/QC tables | archived descriptive stage | descriptive reporting |

## How To Run
- Refresh corpus canonical files from archived pipeline artifacts:
  - `python scripts/build_postretrieval_dataset.py`
- Rebuild salience indicators from current corpus + Nexis volume:
  - `python scripts/build_monthly_media_salience_indicator.py`
- Build polling scaffold outputs:
  - run `notebooks/02_afd_polling_preparation.ipynb`

## Dependencies
- Upstream:
  - `archive_pipeline/master_tables/*`
  - `archive_pipeline/monthly_tables/*`
  - manual `data/corpus/monthly_nexis_volume.csv`
  - DAWUM polling source data
- Downstream:
  - notebooks
  - reporting figures
  - polling-salience merge stage

## Update Routine (Manual)
- If file names/locations/semantics in any data subfolder change, update this README table immediately.

## Notes
- Generated canonical files should be rebuilt via scripts/notebooks, not spreadsheet-edited.
- `2019-09` main-corpus archive correction has been integrated; current corpus/indicator outputs are post-correction refresh outputs.
