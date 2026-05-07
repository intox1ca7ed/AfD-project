# README Corpora

Last updated: 2026-05-07

## Purpose
- Source corpus layer for main monthly corpus and shock corpora.

## Current Snapshot
- Main corpus: `Corpora/Main Corpus/` with monthly folders `2013-01` to `2025-12`.
- Shock corpora:
  - `Corpora/Cologne/`
  - `Corpora/Chemnitz/`
  - `Corpora/Corrective Revelation/`
- Protocol reference: `Corpora/corpora-protocol.md`.

## How To Run
- Main monthly corpus processing runner:
  - `python "Corpora/Main Corpus/run_main_corpus.py"`
- Typical forced full reprocess:
  - `python "Corpora/Main Corpus/run_main_corpus.py" --rerun --reextract`
- Targeted month rerun example:
  - `python "Corpora/Main Corpus/run_main_corpus.py" --only 2021-09 --rerun --reextract`

## Dependencies
- Upstream:
  - Nexis ZIP exports and local retrieval assets
- Downstream:
  - `archive_pipeline/freeze/*`
  - all post-retrieval derived tables

## Update Routine (Manual)
- If folder structure, processing commands, or protocol version changes, update this file.

## Notes
- This layer is not general analysis workspace; changes here affect all downstream outputs.
