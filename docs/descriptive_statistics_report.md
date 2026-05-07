# Descriptive Statistics and QC Diagnostics

## Scope
- Inputs: freeze manifest (Worktodo 1), master_articles_all (Worktodo 2), monthly_summary_main_corpus (Worktodo 3).
- Focus: Main Corpus monthly structure and QC diagnostics only (no sentiment/topic/causal modeling).

## A) Volume Over Time
- Coverage: 2013-01 to 2025-12 with 156 monthly rows.
- Main monthly salience volume is based on manual Nexis monthly totals (`nexis_total_results`), not on kept downloaded counts.
- Downloaded and cleaned monthly counts remain diagnostic sample-size series.
- Totals shown below refer to downloaded/cleaned corpus structure, not absolute Nexis salience volume:
  - downloaded (raw) total=10402
  - cleaned kept total=8772
  - dropped total=1614
- Median cleaned kept count per month: 46.0.

Shock-month sample-size check (cleaned kept counts):
- 2016-01: kept=79, relative_to_median=1.72x
- 2018-08: kept=82, relative_to_median=1.78x
- 2024-01: kept=42, relative_to_median=0.91x

## B) Article Length Distribution
- Kept-article word counts: mean=642.1, median=544.0, q1=363.0, q3=776.0, p95=1425.0, p99=2134.1.
- Potential extremes: >p99 count=88, very short count=86.

## C) Source Structure
- Distinct kept-row sources overall: 10.
- Top source share overall: 0.197 of kept corpus.

## D) Exclusion Structure
- Dominant drop reasons: duplicate_exact=740, commentary_noncore=485, regional_variant=337, reader_letter=33, duplicate_near=11.
- Duplicate burden change (first 24 months vs last 24 months): 0.049 -> 0.134.

## E) Missing/Suspicious Periods
- Missing months: none.
- High-count outlier months: none.
- Low-count outlier months: none.
- High duplicate-burden months: 2018-11, 2018-12, 2019-01.

## F) General Anomaly Scan
- Empty text_body rows: 0 (0.000%).
- Unexpected publication values (blank/placeholder): 0.

## Readiness Interpretation
- Temporal structure appears coherent: full 156-month coverage and exact sum-back to master table.
- Nexis-based salience volume is now separated from downloaded/cleaned sample-size dynamics.
- Duplicate burden is concentrated in specific months rather than universally high; flagged months should be documented in thesis QC notes.
- Source mix is concentrated but not single-source dominated to an implausible level; concentration metrics are included for transparency.
- No blocking structural anomalies were found for proceeding to indicator-construction stage.
