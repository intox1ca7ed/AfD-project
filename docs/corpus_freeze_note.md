# Corpus Freeze Note

Updated: 2026-05-04T14:38:30

## Freeze Summary
- Retrieval stage status: frozen for downstream analysis (with documented warnings).
- Corpus root path: `C:\PythonProjects\AfD-project\Corpora`
- Main monthly batches: 156
- Main period covered: 2013-01 to 2025-12
- Main kept articles: 8909
- Main dropped/excluded articles: 1632
- All 156 months present: YES

## Shock Corpora Status
- Chemnitz / chemnitz_core: frozen
- Chemnitz / chemnitz_extra: needs_manual_check
- Cologne / cologne: frozen_with_warning
- Corrective Revelation / corrective_revelation: frozen_with_warning

## Known Warnings / Manual Checks
- Shock cologne: frozen_with_warning (warnings=raw_unarchive_empty)
- Shock corrective_revelation: frozen_with_warning (warnings=raw_unarchive_empty)
- Shock chemnitz_extra: needs_manual_check (missing=Corpora\Chemnitz\qc\extra\article_registry.csv; warnings=raw_unarchive_empty)

## Detailed Freeze Artifacts
Detailed technical freeze files are archived in:
- `archive_pipeline/freeze/retrieval_freeze_manifest.csv`
- `archive_pipeline/freeze/retrieval_freeze_checks.txt`
- `archive_pipeline/freeze/retrieval_freeze_note.txt`
