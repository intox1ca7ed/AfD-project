# Clean 2022-07 Corpus Summary

- Total original files: 78
- Kept files: 57
- Dropped files: 21
- Review files: 0
- Duplicate groups collapsed: 17

## Representative Selection Rule

- Priority order: complete metadata, then longest usable body text, then cleanest parsed version, then lexical file-name order.

## Malformed Criteria

- Missing or empty title, publication, or date.
- Missing or empty body text.
- Placeholder-like title such as `No Headline In Original`.
- Extremely short extracted body that is clearly unusable.

## Canonical CSV

- `article_registry.csv` is the canonical final article-level registry for this corpus.