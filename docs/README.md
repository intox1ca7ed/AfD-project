# README Docs

Last updated: 2026-05-11

## Purpose
- Research-facing and technical documentation layer.

## Current Snapshot
- `docs/corpus_freeze_note.md`: high-level freeze status summary.
- `docs/corpus_protocol.md`: protocol and parsing/cleaning rules.
- `docs/data_dictionary.md`: dataset definitions.
- `docs/descriptive_statistics_report.md`: descriptive findings memo.
- `docs/project_notes.md`: reproducibility and pipeline mapping notes.
- `docs/post_deletion_salience_correction_note.md`: corrected post-deletion salience baseline note.
- `docs/polling_and_election_data_plan.md`: polling/election stage plan and source boundaries.
- `docs/descriptive_event_window_results_note.md`: thesis-facing descriptive pre/post event-window note for Cologne, Chemnitz, Correctiv.
- `docs/final_empirical_results_summary.md`: final descriptive thesis-ready empirical summary (Milestone 4).
- `docs/supplementary_media_tone_results_note.md`: supplementary media-tone diagnostic note (Milestone 5 supplementary layer).

## How To Use
- Read `data_dictionary.md` before adding or renaming dataset columns.
- Read `project_notes.md` for stage/output mapping.
- Keep documentation aligned with current scripts and datasets.

## Dependencies
- Upstream:
  - `archive_pipeline/*` outputs
  - `data/*` canonical files
- Downstream:
  - human interpretation
  - LLM context bootstrapping

## Update Routine (Manual)
- Update relevant docs when:
  - dataset semantics change
  - indicator definitions change
  - workflow commands or stage outputs change

## Notes
- Docs are navigational/technical context, not immutable governance artifacts.
