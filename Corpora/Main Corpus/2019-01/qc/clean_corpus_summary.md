# Clean 2019-01 Corpus Summary

- Total original files: 150
- Kept files: 42
- Dropped files: 108
- Review files: 0
- Duplicate groups collapsed: 10

## Representative Selection Rule

- Priority order: complete metadata, then longest usable body text, then cleanest parsed version, then lexical file-name order.

## Malformed Criteria

- Missing or empty title, publication, or date.
- Missing or empty body text.
- Placeholder-like title such as `No Headline In Original`.
- Extremely short extracted body that is clearly unusable.

## Canonical CSV

- `article_registry.csv` is the canonical final article-level registry for this corpus.