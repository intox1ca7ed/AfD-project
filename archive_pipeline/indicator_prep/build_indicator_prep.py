from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


ARTICLE_PLACEHOLDER_COLS = [
    "ind_sentiment_score",
    "ind_negative_tone_score",
    "ind_migration_tone_score",
    "ind_security_tone_score",
    "ind_topic_label",
    "ind_topic_confidence",
    "ind_shock_window_flag",
    "ind_shock_name",
    "ind_source_family",
    "ind_regional_flag",
]

MONTHLY_PLACEHOLDER_COLS = [
    "ind_article_count_indicator",
    "ind_log_article_count",
    "ind_standardized_salience",
    "ind_negative_share",
    "ind_migration_share",
    "ind_security_share",
    "ind_mean_sentiment",
    "ind_source_concentration_index",
    "ind_shock_month_dummy",
    "ind_post_shock_window_dummy",
]


def column_block(columns: list[str]) -> str:
    return "\n".join([f"- {c}" for c in columns])


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]

    master_path = project_root / "master_tables" / "master_articles_all.csv"
    monthly_path = project_root / "monthly_tables" / "monthly_summary_main_corpus.csv"
    descriptive_report_path = project_root / "descriptive_package" / "descriptive_statistics_report.md"

    out_dir = project_root / "indicator_prep"
    out_dir.mkdir(parents=True, exist_ok=True)

    master = pd.read_csv(master_path, encoding="utf-8-sig", low_memory=False)
    monthly = pd.read_csv(monthly_path, encoding="utf-8-sig", low_memory=False)

    # Optional indicator-ready tables: append documented null placeholders only.
    master_ready = master.copy()
    for col in ARTICLE_PLACEHOLDER_COLS:
        if col not in master_ready.columns:
            master_ready[col] = pd.NA

    monthly_ready = monthly.copy()
    for col in MONTHLY_PLACEHOLDER_COLS:
        if col not in monthly_ready.columns:
            monthly_ready[col] = pd.NA

    master_ready_csv = out_dir / "master_articles_all_indicator_ready.csv"
    master_ready_parquet = out_dir / "master_articles_all_indicator_ready.parquet"
    monthly_ready_csv = out_dir / "monthly_summary_main_corpus_indicator_ready.csv"
    monthly_ready_parquet = out_dir / "monthly_summary_main_corpus_indicator_ready.parquet"

    master_ready.to_csv(master_ready_csv, index=False, encoding="utf-8-sig")
    monthly_ready.to_csv(monthly_ready_csv, index=False, encoding="utf-8-sig")
    master_ready.to_parquet(master_ready_parquet, index=False)
    monthly_ready.to_parquet(monthly_ready_parquet, index=False)

    # Blueprint.
    blueprint = f"""Indicator Blueprint

Build timestamp: {datetime.now().isoformat(timespec='seconds')}

Purpose:
- Define future indicator variable structure without performing sentiment/topic modeling or causal estimation.
- Keep backward compatibility with Worktodo 1-4 outputs.

Current base tables:
- Article level: master_tables/master_articles_all.csv
- Monthly level: monthly_tables/monthly_summary_main_corpus.csv
- Descriptive reference: descriptive_package/descriptive_statistics_report.md

Design principles:
- Keep core IDs stable: article_id, batch_id, month_id.
- Add future model outputs with an `ind_` prefix.
- Keep placeholders null until a real modeling stage is run.
- Never overwrite structural source/QC columns with derived model outputs.

A) Article-level future variables (placeholders)
{column_block(ARTICLE_PLACEHOLDER_COLS)}

Recommended semantics:
- ind_sentiment_score: continuous sentiment output (e.g., -1 to +1 or model-native scale).
- ind_negative_tone_score: probability or intensity of negative tone.
- ind_migration_tone_score: migration-related tone signal.
- ind_security_tone_score: security/crime/public-order tone signal.
- ind_topic_label: categorical topic class for article body.
- ind_topic_confidence: confidence/probability for chosen topic label.
- ind_shock_window_flag: article-level window membership relative to a shock event date.
- ind_shock_name: categorical shock name when in a defined window.
- ind_source_family: optional grouped source class (national, regional, tabloid, public-service, etc.).
- ind_regional_flag: optional regional metadata when source geocoding is later available.

B) Monthly-level future variables (placeholders)
{column_block(MONTHLY_PLACEHOLDER_COLS)}

Recommended semantics:
- ind_article_count_indicator: selected volume signal for modeling (typically from kept rows).
- ind_log_article_count: log transform of article count indicator.
- ind_standardized_salience: z-scored salience metric over a reference period.
- ind_negative_share: share of articles above a negative-tone threshold.
- ind_migration_share: share of articles assigned migration topic/tone.
- ind_security_share: share of articles assigned security topic/tone.
- ind_mean_sentiment: monthly mean sentiment across eligible kept articles.
- ind_source_concentration_index: monthly source concentration (e.g., HHI or top-k share metric).
- ind_shock_month_dummy: equals 1 in designated shock month(s).
- ind_post_shock_window_dummy: equals 1 in chosen post-shock window definition.

Implementation note:
- Placeholder columns are intentionally null in indicator-ready tables created in this task.
- No fake values are generated.
"""

    write_text(out_dir / "indicator_blueprint.txt", blueprint)

    schema_doc = f"""Indicator-Ready Schema Specification

Build timestamp: {datetime.now().isoformat(timespec='seconds')}

1) Recommended join keys
- Article-level primary key: article_id
- Article-to-month key: month (YYYY-MM in master table) joined to monthly month_id
- Monthly primary key: month_id
- Batch traceability key: batch_id (equal to month_id for Main Corpus monthly panel)

2) Recommended polling merge keys
- Poll merge key: month_id (YYYY-MM)
- Suggested polling columns (future): poll_date, poll_month_id, afd_support_percent, poll_source
- Merge mode recommendation: left join from monthly_summary_main_corpus to polling table on month_id

3) Date standardization rules
- Article date must be ISO YYYY-MM-DD in `date` where parseable.
- Monthly key must remain YYYY-MM in `month_id` and `month` (article-level month).
- Keep original raw date text in `date_raw` for auditability.
- Never use locale-formatted strings as join keys.

4) Naming conventions
- Structural/raw variables: keep current names unchanged (e.g., raw_article_count, kept_article_count, drop_reason).
- Model-derived future variables: prefix with `ind_`.
- Binary dummies: suffix `_dummy` or `_flag`.
- Shares/rates: suffix `_share`.
- Score/probability outputs: suffix `_score`.

5) Structural vs model-derived distinction
Structural/raw variables (already populated):
- IDs and join keys: article_id, batch_id, month_id, month
- Corpus/process metadata: corpus_name, corpus_type, protocol_version, freeze_status
- QC and filtering fields: keep_drop_review, drop_reason, duplicate_category, malformed_flag
- Core volume/length fields: raw_article_count, kept_article_count, dropped_article_count, word_count

Model-derived variables (currently placeholders only):
{column_block(ARTICLE_PLACEHOLDER_COLS + MONTHLY_PLACEHOLDER_COLS)}

6) Backward-compatibility rules
- Do not rename article_id, month_id, batch_id, or keep_drop_review.
- New model columns must be additive only.
- Existing structural columns must retain type/meaning across versions.
- If a future indicator definition changes, add version metadata instead of reusing a column with different semantics.

7) Output files produced in this task
- indicator_prep/indicator_blueprint.txt
- indicator_prep/indicator_ready_schema.txt
- indicator_prep/master_articles_all_indicator_ready.csv
- indicator_prep/master_articles_all_indicator_ready.parquet
- indicator_prep/monthly_summary_main_corpus_indicator_ready.csv
- indicator_prep/monthly_summary_main_corpus_indicator_ready.parquet
"""

    write_text(out_dir / "indicator_ready_schema.txt", schema_doc)

    log_text = f"""Indicator Prep Build Log
build_timestamp={datetime.now().isoformat(timespec='seconds')}
input_master={master_path}
input_monthly={monthly_path}
input_descriptive_report_exists={descriptive_report_path.exists()}

master_rows={len(master_ready)}
monthly_rows={len(monthly_ready)}
article_placeholders_added={len(ARTICLE_PLACEHOLDER_COLS)}
monthly_placeholders_added={len(MONTHLY_PLACEHOLDER_COLS)}

outputs:
- {master_ready_csv}
- {master_ready_parquet}
- {monthly_ready_csv}
- {monthly_ready_parquet}
- {out_dir / 'indicator_blueprint.txt'}
- {out_dir / 'indicator_ready_schema.txt'}
"""
    write_text(out_dir / "indicator_prep_build_log.txt", log_text)

    print(f"Wrote: {out_dir / 'indicator_blueprint.txt'}")
    print(f"Wrote: {out_dir / 'indicator_ready_schema.txt'}")
    print(f"Wrote: {master_ready_csv}")
    print(f"Wrote: {master_ready_parquet}")
    print(f"Wrote: {monthly_ready_csv}")
    print(f"Wrote: {monthly_ready_parquet}")
    print(f"Wrote: {out_dir / 'indicator_prep_build_log.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
