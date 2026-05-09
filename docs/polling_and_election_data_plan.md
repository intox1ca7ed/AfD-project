# Polling and Election Data Plan

Last updated: 2026-05-08

## Scope
This note defines the next empirical data stage after corpus and salience preparation.

## Polling Source Strategy
- Main monthly dynamic outcome source: **DAWUM** Bundestag polling data.
- DAWUM provides poll-level party support observations that can be aggregated to monthly AfD support.
- Raw polling files are stored unchanged under `data/polling/raw/`.
- Processed monthly polling series are stored under `data/polling/processed/`.

## Benchmark Source Positioning
- Politico Poll of Polls may be used as a public-facing benchmark/sanity check.
- It is **not** the primary raw empirical polling dataset for this project stage.

## Election Anchor Strategy
- Official election-result anchors come from **regionalstatistik.de** (e.g., table `14111-01-04-4`).
- Relevant measure: **Bundestag Zweitstimme** AfD percentage.
- Election results are anchor benchmark points, not monthly public-opinion dynamics.
- Anchor scaffold file: `data/elections/afd_election_anchors.csv`.

## Next Merge Stage
- The next empirical merge should combine:
  - volume-based media salience indicators (`data/indicators/monthly_media_salience_indicator.*`)
  - monthly AfD polling support (`data/polling/processed/afd_polling_monthly.*`)
- No causal/event-study modeling is included in this stage note.
