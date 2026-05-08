# Post-Deletion Salience Correction Note

Last updated: 2026-05-08

## Scope
This note documents the finalized descriptive-stage salience setup after the early-2013 deletion correction and rebuild.

## Indicator Definition
- Main monthly media salience indicator: `nexis_total_results` (manual monthly Nexis total results).
- `raw_article_count`: downloaded sample size / retrieval effort.
- `kept_article_count` (aliased as `cleaned_sample_size`): cleaned downloaded text sample size.

## Correction Status
- Excess downloaded articles in mismatch months were removed.
- Monthly post-retrieval outputs and indicator outputs were rebuilt from the corrected state.
- The current post-deletion dataset state is the authoritative working baseline.

## Validation Field
- `retrieval_mismatch_flag` is retained as a structural validation field.
- Under the corrected baseline it should be `False` for all months.

## Notebook 01 Boundary
- `notebooks/01_corpus_descriptive_report.ipynb` remains descriptive/validation-only.
- No polling merge, sentiment modeling, topic modeling, causal modeling, or event-study estimation is included at this stage.
