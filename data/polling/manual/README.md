# README Manual Polling Supplement

Last updated: 2026-05-08

## Purpose
- This folder stores a manually collected historical AfD polling supplement from Wahlrecht.de.
- It is intended to cover the pre-DAWUM period for Cologne-window descriptive diagnostics.
- DAWUM remains the main polling source from 2017 onward.

## Files
- `data/polling/manual/afd_polling_historical_manual_polllevel.csv`
- `data/polling/manual/afd_polling_historical_manual_monthly.csv`
- `data/polling/manual/afd_polling_historical_manual_monthly.parquet`

## Source Scope
- Source website: Wahlrecht.de.
- Source pages used:
  - `https://www.wahlrecht.de/umfragen/politbarometer/politbarometer-2017.htm`
  - `https://www.wahlrecht.de/umfragen/dimap.htm`
  - `https://www.wahlrecht.de/umfragen/gms/projektion-2017.htm`
- Rows are labeled with `source_url` and `pollster`.

## Method Notes
- This supplement uses voting-intention/projection-style AfD values where available.
- `collection_method` is fixed to `manual_wahlrecht_historical_supplement`.
- Wahlrecht.de is an aggregator, not the original pollster publication source.
- Keep source labels visible and do not silently merge with DAWUM outputs.

## Coverage and Role
- Historical supplement coverage in current file: 2013-09 to 2016-12.
- This includes the minimum Cologne-relevant target window 2015-07 to 2016-06.
- Intended use: descriptive pre-DAWUM context, not replacement of the DAWUM series.
