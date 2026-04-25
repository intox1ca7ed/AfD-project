Corpus protocol

Required corpus metadata

corpus_name =
protocol_version = v1
date_built =

Required search provenance

For each corpus, save:
- query
- date window
- source basket
- Nexis filters

Core workflow

1. Keep the original archive file unchanged.

2. Unpack source files only into a temporary source folder such as `raw_unarchive/`.

3. Extract from every file the core fields needed for analysis:
title, publication, date, byline, section, length, full body text.

4. Build a QC table for the whole dataset before filtering anything.

5. Check systematically for:
exact duplicates,
near-duplicates,
regional-edition variants,
reader letters,
commentary/opinion,
very short low-value items,
empty or malformed records.

6. Apply a conservative decision rule:
keep if the item is a factual event report, a directly relevant contextual report, or a clearly useful analysis text for understanding the event sequence, institutional response, public reaction, or immediate political consequences;
drop only if it fits one of the standardized exclusion categories below;
if uncertain, keep and note the uncertainty.

Standardized drop categories

- duplicate_exact
- duplicate_near
- regional_variant
- reader_letter
- commentary_noncore
- very_short_low_value
- malformed

Operational rule for commentary_noncore

Use `commentary_noncore` only when the item is primarily opinion, column, editorial, commentary, or essay and does not add unique factual reporting or uniquely useful analytical content needed for the event corpus.

Representative file rule

For each confirmed duplicate or variant group:
- keep the file with the most complete body text;
- if length is effectively the same, keep the more general edition or main outlet version rather than the regional or edition variant;
- drop the remaining files with the appropriate standardized category.

Preservation rule

Never delete originals automatically.
Create derived folders such as `clean_keep/` and `excluded_drop/` and copy files there.

Required outputs per corpus

Save all QC outputs inside the corpus folder:
- QC table
- duplicate table
- exclusion log
- short summary of rules and counts
- search provenance record

Reproducibility rule

Store the scripts inside the corpus folder so the dataset can be rebuilt from the archive and `raw_unarchive/` at any time.
