Corpus protocol

Protocol version

protocol_version = v2

Required corpus metadata

Each corpus or batch must record:
- corpus_name
- batch_id
- source_archive
- date_built

Core workflow

1. Keep the original archive unchanged.

2. Unpack source files only into `raw_unarchive/` or the corpus-specific raw unpack folder already used by the workflow.

3. Parse every file and extract at minimum:
- title
- publication
- date
- byline
- body text
- body length

4. Write an intermediate parsed QC table automatically.

5. Detect duplication explicitly with the following controlled categories:
- unique
- duplicate_exact
- duplicate_near
- regional_variant

6. Assign stable duplicate-group IDs such as:
- exact_001
- near_001
- variant_001

7. Detect malformed files automatically before substantive cleaning.

Malformed-file criteria

Flag a file as malformed when relevant, including:
- missing or empty title
- missing or empty publication
- missing or empty date
- body text extraction failed
- empty body
- placeholder title such as `No Headline In Original`
- body text so short that the parsed record is clearly unusable

Malformed files remain logged and originals remain untouched.

8. Build one canonical final article-level CSV per corpus or batch.

This CSV is the central structured registry and must contain one row per parsed file.

Required columns

- batch_id
- corpus_name
- source_archive
- file_name
- file_path
- title_original
- title_normalized
- publication
- publication_normalized
- date
- byline
- word_count
- body_char_count
- body_hash_exact
- duplicate_group_id
- duplicate_category
- keep_drop_review
- drop_reason
- kept_representative_of_group
- representative_selection_reason
- malformed_flag
- malformed_reason
- notes

Some workflows may also keep a few additional columns such as `section` or low-value flags, but the registry should stay compact and readable.

9. Use a fixed drop-reason vocabulary.

Allowed primary drop labels:
- duplicate_exact
- duplicate_near
- regional_variant
- reader_letter
- commentary_noncore
- very_short_low_value
- malformed

Rules:
- every dropped item must have exactly one primary `drop_reason`
- kept items must have blank `drop_reason`
- review items may keep blank `drop_reason` until resolution

10. Apply a conservative decision rule.

Keep if the item is a factual event report, directly relevant contextual report, or useful analysis text.

Drop only when it clearly fits one of the controlled exclusion categories.

If uncertain, default to keep or review rather than aggressive dropping.

11. Use one deterministic representative-selection rule for duplicate groups.

For each `duplicate_exact`, `duplicate_near`, or `regional_variant` group:
- first prefer the record with the most complete metadata
- then prefer the longest usable body text
- then prefer the cleanest parsed version
- if still tied, choose deterministically by lexical file-name order

The final registry must record:
- whether a file is the kept representative of a duplicate group
- why that file was selected

12. Preserve source integrity.

Never delete originals automatically.

Create derived folders such as:
- `clean_keep/`
- `excluded_drop/`

Files placed there must be copies, not the source originals.

13. Required outputs per corpus or batch

At minimum keep:
- intermediate parsed QC table
- duplicate group table
- canonical final article-level CSV
- exclusion log
- short QC summary
- short clean-corpus summary

14. Reproducibility rule

Scripts must stay inside the corpus folder structure and the corpus must remain reproducible from:
- the original archive
- the unpacked raw source folder
- the local scripts
