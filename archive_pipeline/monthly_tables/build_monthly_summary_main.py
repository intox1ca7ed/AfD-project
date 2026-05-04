from __future__ import annotations

import csv
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None

REQUIRED_COLUMNS = [
    "month_id",
    "year",
    "month",
    "batch_id",
    "raw_article_count",
    "kept_article_count",
    "dropped_article_count",
    "keep_share",
    "unique_source_count",
    "total_word_count_kept",
    "mean_word_count_kept",
    "median_word_count_kept",
    "duplicate_exact_count",
    "duplicate_near_count",
    "regional_variant_count",
    "malformed_count",
    "reader_letter_drop_count",
    "commentary_noncore_drop_count",
    "very_short_low_value_drop_count",
    "source_top1",
    "source_top1_count",
    "source_top2",
    "source_top2_count",
    "source_top3",
    "source_top3_count",
    "freeze_status",
    "notes",
]

OPTIONAL_COLUMNS = [
    "kept_share_of_raw",
    "duplicate_burden",
    "dropped_share",
    "shock_month_flag",
    "shock_window_flag_placeholder",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})


def month_iter(start: str, end: str) -> list[str]:
    sy, sm = [int(x) for x in start.split("-")]
    ey, em = [int(x) for x in end.split("-")]
    out = []
    y, m = sy, sm
    while (y < ey) or (y == ey and m <= em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def to_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return 0


def normalize_token(s: str) -> str:
    return " ".join((s or "").strip().split())


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    master_path = project_root / "master_tables" / "master_articles_all.csv"
    freeze_manifest_path = project_root / "freeze" / "retrieval_freeze_manifest.csv"

    out_dir = project_root / "monthly_tables"
    out_csv = out_dir / "monthly_summary_main_corpus.csv"
    out_parquet = out_dir / "monthly_summary_main_corpus.parquet"
    out_dict = out_dir / "monthly_summary_data_dictionary.txt"
    out_log = out_dir / "monthly_summary_build_log.txt"

    master_rows = read_csv_rows(master_path)
    manifest_rows = read_csv_rows(freeze_manifest_path)

    if not master_rows:
        raise SystemExit(f"Master table missing/unreadable: {master_path}")
    if not manifest_rows:
        raise SystemExit(f"Freeze manifest missing/unreadable: {freeze_manifest_path}")

    main_rows = [r for r in master_rows if r.get("corpus_name", "") == "Main Corpus"]

    freeze_by_batch = {
        r.get("batch_id", ""): {
            "status": r.get("status", ""),
            "notes": r.get("notes", ""),
        }
        for r in manifest_rows
        if r.get("corpus_name", "") == "Main Corpus" and r.get("corpus_type", "") == "main_monthly"
    }

    expected_months = month_iter("2013-01", "2025-12")

    # Group rows by month based on batch_id (canonical monthly key for main corpus).
    rows_by_month: dict[str, list[dict[str, str]]] = {m: [] for m in expected_months}
    for r in main_rows:
        batch = r.get("batch_id", "")
        if batch in rows_by_month:
            rows_by_month[batch].append(r)

    shock_months = {"2016-01", "2018-08", "2024-01"}

    monthly_rows: list[dict[str, Any]] = []
    for month_id in expected_months:
        rows = rows_by_month.get(month_id, [])

        raw_count = len(rows)
        kept_rows = [r for r in rows if (r.get("keep_drop_review", "").strip().lower() == "keep")]
        dropped_rows = [r for r in rows if (r.get("keep_drop_review", "").strip().lower() == "drop")]

        kept_count = len(kept_rows)
        dropped_count = len(dropped_rows)

        keep_share = (kept_count / raw_count) if raw_count else 0.0
        dropped_share = (dropped_count / raw_count) if raw_count else 0.0

        # Publication/source stats from kept rows for analysis-facing summary.
        source_counts = Counter(normalize_token(r.get("publication", "")) for r in kept_rows if normalize_token(r.get("publication", "")))
        unique_source_count = len(source_counts)
        top3 = sorted(source_counts.items(), key=lambda x: (-x[1], x[0]))[:3]

        def top_value(idx: int) -> tuple[str, int]:
            if idx < len(top3):
                return top3[idx][0], top3[idx][1]
            return "", 0

        source_top1, source_top1_count = top_value(0)
        source_top2, source_top2_count = top_value(1)
        source_top3, source_top3_count = top_value(2)

        kept_word_counts = [to_int(r.get("word_count", "")) for r in kept_rows if to_int(r.get("word_count", "")) > 0]
        total_word_count_kept = sum(kept_word_counts)
        mean_word_count_kept = round(statistics.mean(kept_word_counts), 3) if kept_word_counts else 0
        median_word_count_kept = round(statistics.median(kept_word_counts), 3) if kept_word_counts else 0

        # Duplicate burden from dropped rows by reason/category.
        duplicate_exact_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "duplicate_exact"))
        duplicate_near_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "duplicate_near"))
        regional_variant_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "regional_variant"))

        malformed_count = sum(1 for r in rows if (r.get("malformed_flag", "").strip().lower() == "yes"))
        reader_letter_drop_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "reader_letter"))
        commentary_noncore_drop_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "commentary_noncore"))
        very_short_low_value_drop_count = sum(1 for r in dropped_rows if (r.get("drop_reason", "").strip().lower() == "very_short_low_value"))

        duplicate_burden = (
            (duplicate_exact_count + duplicate_near_count + regional_variant_count) / raw_count
            if raw_count
            else 0.0
        )

        freeze_info = freeze_by_batch.get(month_id, {"status": "", "notes": ""})

        monthly_rows.append(
            {
                "month_id": month_id,
                "year": int(month_id[:4]),
                "month": int(month_id[5:7]),
                "batch_id": month_id,
                "raw_article_count": raw_count,
                "kept_article_count": kept_count,
                "dropped_article_count": dropped_count,
                "keep_share": round(keep_share, 6),
                "unique_source_count": unique_source_count,
                "total_word_count_kept": total_word_count_kept,
                "mean_word_count_kept": mean_word_count_kept,
                "median_word_count_kept": median_word_count_kept,
                "duplicate_exact_count": duplicate_exact_count,
                "duplicate_near_count": duplicate_near_count,
                "regional_variant_count": regional_variant_count,
                "malformed_count": malformed_count,
                "reader_letter_drop_count": reader_letter_drop_count,
                "commentary_noncore_drop_count": commentary_noncore_drop_count,
                "very_short_low_value_drop_count": very_short_low_value_drop_count,
                "source_top1": source_top1,
                "source_top1_count": source_top1_count,
                "source_top2": source_top2,
                "source_top2_count": source_top2_count,
                "source_top3": source_top3,
                "source_top3_count": source_top3_count,
                "freeze_status": freeze_info.get("status", ""),
                "notes": freeze_info.get("notes", ""),
                "kept_share_of_raw": round(keep_share, 6),
                "duplicate_burden": round(duplicate_burden, 6),
                "dropped_share": round(dropped_share, 6),
                "shock_month_flag": 1 if month_id in shock_months else 0,
                "shock_window_flag_placeholder": "",
            }
        )

    final_columns = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    write_csv(out_csv, monthly_rows, final_columns)

    wrote_parquet = False
    if pd is not None:
        pd.DataFrame(monthly_rows)[final_columns].to_parquet(out_parquet, index=False)
        wrote_parquet = True

    # Validation checks for build log.
    month_ids = [r["month_id"] for r in monthly_rows]
    month_counter = Counter(month_ids)
    duplicate_month_rows = [m for m, c in month_counter.items() if c > 1]
    missing_months = [m for m in expected_months if m not in month_counter]

    sum_raw = sum(to_int(r["raw_article_count"]) for r in monthly_rows)
    sum_kept = sum(to_int(r["kept_article_count"]) for r in monthly_rows)
    sum_drop = sum(to_int(r["dropped_article_count"]) for r in monthly_rows)

    master_raw = len(main_rows)
    master_kept = sum(1 for r in main_rows if (r.get("keep_drop_review", "").strip().lower() == "keep"))
    master_drop = sum(1 for r in main_rows if (r.get("keep_drop_review", "").strip().lower() == "drop"))

    suspicious_zero_or_near_zero = [
        r["month_id"]
        for r in monthly_rows
        if to_int(r["raw_article_count"]) == 0 or to_int(r["raw_article_count"]) <= 5
    ]

    # Unusually high duplicate burden: threshold max(0.35, p90).
    dup_burdens = [float(r["duplicate_burden"]) for r in monthly_rows]
    p90 = 0.0
    if dup_burdens:
        ordered = sorted(dup_burdens)
        p90 = ordered[min(len(ordered) - 1, int(0.9 * (len(ordered) - 1)))]
    threshold = max(0.35, p90)
    high_dup_months = [r["month_id"] for r in monthly_rows if float(r["duplicate_burden"]) > threshold]

    log_lines = [
        "Monthly Summary Build Log",
        f"build_timestamp={datetime.now().isoformat(timespec='seconds')}",
        f"input_master_table={master_path}",
        f"input_freeze_manifest={freeze_manifest_path}",
        "",
        f"all_156_months_present_exactly_once={'YES' if len(monthly_rows)==156 and not duplicate_month_rows and not missing_months else 'NO'}",
        f"missing_months={'none' if not missing_months else ', '.join(missing_months)}",
        f"duplicate_month_rows={'none' if not duplicate_month_rows else ', '.join(duplicate_month_rows)}",
        "",
        "Monthly sum-back checks to master table:",
        f"- raw_article_count_sum={sum_raw} | master_main_rows={master_raw} | match={'YES' if sum_raw==master_raw else 'NO'}",
        f"- kept_article_count_sum={sum_kept} | master_main_keep_rows={master_kept} | match={'YES' if sum_kept==master_kept else 'NO'}",
        f"- dropped_article_count_sum={sum_drop} | master_main_drop_rows={master_drop} | match={'YES' if sum_drop==master_drop else 'NO'}",
        "",
        f"suspicious_zero_or_near_zero_months={'none' if not suspicious_zero_or_near_zero else ', '.join(suspicious_zero_or_near_zero)}",
        f"unusually_high_duplicate_burden_threshold={round(threshold,6)}",
        f"unusually_high_duplicate_burden_months={'none' if not high_dup_months else ', '.join(high_dup_months)}",
        "",
        f"rows_written={len(monthly_rows)}",
        f"parquet_written={'YES' if wrote_parquet else 'NO'}",
    ]
    out_log.write_text("\n".join(log_lines), encoding="utf-8")

    dict_lines = [
        "Monthly Summary Data Dictionary",
        "",
        "Dataset purpose:",
        "- One-row-per-month structural summary for Main Corpus (2013-01 to 2025-12).",
        "- Time-series-ready table for later merge with AfD polling and later indicator construction.",
        "",
        "Count definitions:",
        "- raw_article_count: all rows from master_articles_all for the month (keep + drop + review).",
        "- kept_article_count: rows where keep_drop_review == keep.",
        "- dropped_article_count: rows where keep_drop_review == drop.",
        "- keep_share / kept_share_of_raw: kept_article_count / raw_article_count.",
        "- dropped_share: dropped_article_count / raw_article_count.",
        "",
        "Source-top fields:",
        "- source_top1/2/3 and counts are computed from kept rows only.",
        "- Ties are broken lexicographically by publication name.",
        "",
        "Duplicate-related fields:",
        "- duplicate_exact_count, duplicate_near_count, regional_variant_count are drop_reason-based counts from dropped rows.",
        "- duplicate_burden = (duplicate_exact_count + duplicate_near_count + regional_variant_count) / raw_article_count.",
        "",
        "Shock placeholders:",
        "- shock_month_flag is 1 for 2016-01, 2018-08, 2024-01; else 0.",
        "- shock_window_flag_placeholder reserved for later custom window definitions.",
        "",
        "Columns:",
    ]

    column_desc = {
        "month_id": "Month key in YYYY-MM format.",
        "year": "Calendar year integer extracted from month_id.",
        "month": "Calendar month integer (1-12) extracted from month_id.",
        "batch_id": "Main corpus batch identifier (same as month_id).",
        "raw_article_count": "All master rows in month (keep + drop + review).",
        "kept_article_count": "Count of keep rows in month.",
        "dropped_article_count": "Count of drop rows in month.",
        "keep_share": "kept_article_count divided by raw_article_count.",
        "unique_source_count": "Number of distinct publications among kept rows.",
        "total_word_count_kept": "Sum of word_count over kept rows.",
        "mean_word_count_kept": "Mean word_count over kept rows.",
        "median_word_count_kept": "Median word_count over kept rows.",
        "duplicate_exact_count": "Dropped rows with drop_reason=duplicate_exact.",
        "duplicate_near_count": "Dropped rows with drop_reason=duplicate_near.",
        "regional_variant_count": "Dropped rows with drop_reason=regional_variant.",
        "malformed_count": "Rows with malformed_flag=yes (all row types).",
        "reader_letter_drop_count": "Dropped rows with drop_reason=reader_letter.",
        "commentary_noncore_drop_count": "Dropped rows with drop_reason=commentary_noncore.",
        "very_short_low_value_drop_count": "Dropped rows with drop_reason=very_short_low_value.",
        "source_top1": "Most frequent kept-row publication in month.",
        "source_top1_count": "Count for source_top1.",
        "source_top2": "Second most frequent kept-row publication in month.",
        "source_top2_count": "Count for source_top2.",
        "source_top3": "Third most frequent kept-row publication in month.",
        "source_top3_count": "Count for source_top3.",
        "freeze_status": "Batch freeze status from retrieval_freeze_manifest.",
        "notes": "Batch notes from retrieval_freeze_manifest.",
        "kept_share_of_raw": "Alias of keep_share for explicit naming.",
        "duplicate_burden": "Share of raw rows dropped for duplicate reasons.",
        "dropped_share": "Share of raw rows with keep_drop_review=drop.",
        "shock_month_flag": "Flag for designated shock months.",
        "shock_window_flag_placeholder": "Reserved placeholder for future shock-window variables.",
    }

    for c in final_columns:
        dict_lines.append(f"- {c}: {column_desc.get(c, 'No description available.')}")

    out_dict.write_text("\n".join(dict_lines), encoding="utf-8")

    print(f"Wrote: {out_csv}")
    if wrote_parquet:
        print(f"Wrote: {out_parquet}")
    print(f"Wrote: {out_dict}")
    print(f"Wrote: {out_log}")
    print(f"rows={len(monthly_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
