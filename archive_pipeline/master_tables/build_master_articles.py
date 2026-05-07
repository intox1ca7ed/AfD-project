from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None

MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

REQUIRED_COLUMNS = [
    "article_id",
    "corpus_type",
    "corpus_name",
    "batch_id",
    "source_archive",
    "date",
    "year",
    "month",
    "publication",
    "publication_normalized",
    "title_original",
    "title_normalized",
    "byline",
    "section",
    "word_count",
    "body_char_count",
    "text_body",
    "body_hash_exact",
    "duplicate_group_id",
    "duplicate_category",
    "keep_drop_review",
    "drop_reason",
    "kept_representative_of_group",
    "representative_selection_reason",
    "malformed_flag",
    "malformed_reason",
    "source_file_name",
    "source_file_path",
    "protocol_version",
    "notes",
]

OPTIONAL_COLUMNS = [
    "query_version",
    "source_basket_version",
    "language",
    "publication_type",
    "date_raw",
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


def normalize_token(s: str) -> str:
    return " ".join((s or "").strip().lower().split())

def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Corpora").exists():
            return candidate
    raise RuntimeError("Could not locate repository root containing 'Corpora/'")


def parse_date_to_iso(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""

    # ISO-like existing.
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # German text date, e.g. Donnerstag 31. Januar 2013
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", raw)
    if m:
        d = int(m.group(1))
        month_name = (
            m.group(2).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        )
        mo = GERMAN_MONTHS.get(month_name)
        y = int(m.group(3))
        if mo:
            return f"{y:04d}-{mo:02d}-{d:02d}"

    # DD.MM.YYYY
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", raw)
    if m:
        d = int(m.group(1))
        mo = int(m.group(2))
        y = int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"

    return ""


def build_article_id(
    corpus_name: str,
    batch_id: str,
    title_normalized: str,
    date_iso: str,
    body_hash_exact: str,
    source_file_name: str,
) -> str:
    payload = "||".join(
        [
            normalize_token(corpus_name),
            normalize_token(batch_id),
            normalize_token(title_normalized),
            normalize_token(date_iso),
            normalize_token(body_hash_exact),
            normalize_token(source_file_name),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def to_int_or_blank(value: str) -> int | str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return int(float(value))
    except Exception:
        return ""


def find_qc_articles_path(registry_path: Path) -> Path:
    return registry_path.with_name("qc_articles.csv")


def main() -> int:
    stage_root = Path(__file__).resolve().parents[1]
    project_root = find_repo_root(stage_root)
    freeze_manifest = stage_root / "freeze" / "retrieval_freeze_manifest.csv"
    out_dir = stage_root / "master_tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not freeze_manifest.exists():
        raise SystemExit(f"Missing freeze manifest: {freeze_manifest}")

    manifest_rows = read_csv_rows(freeze_manifest)
    if not manifest_rows:
        raise SystemExit("Freeze manifest is empty or unreadable.")

    all_rows: list[dict[str, Any]] = []
    failed_batches: list[str] = []
    processed_batches: list[str] = []

    for m in manifest_rows:
        batch_id = m.get("batch_id", "")
        corpus_name = m.get("corpus_name", "")
        corpus_type = m.get("corpus_type", "")

        registry_rel = m.get("article_registry_path", "")
        if not registry_rel:
            failed_batches.append(f"{corpus_name}::{batch_id} | missing registry path in manifest")
            continue

        registry_path = project_root / registry_rel
        if not registry_path.exists():
            failed_batches.append(f"{corpus_name}::{batch_id} | missing registry file: {registry_rel}")
            continue

        registry_rows = read_csv_rows(registry_path)
        if not registry_rows:
            failed_batches.append(f"{corpus_name}::{batch_id} | registry unreadable/empty: {registry_rel}")
            continue

        qc_articles_path = find_qc_articles_path(registry_path)
        qc_rows = read_csv_rows(qc_articles_path) if qc_articles_path.exists() else []

        # Map text by strong key first, fallback by file_name.
        text_by_path_name: dict[tuple[str, str], str] = {}
        text_by_name: dict[str, str] = {}
        for qr in qc_rows:
            fname = qr.get("file_name", "")
            fpath = qr.get("file_path", "")
            body = qr.get("body_text", "")
            text_by_path_name[(fname, fpath)] = body
            if fname and fname not in text_by_name:
                text_by_name[fname] = body

        for r in registry_rows:
            source_file_name = r.get("file_name", "")
            source_file_path = r.get("file_path", "")

            date_raw = r.get("date", "")
            date_iso = parse_date_to_iso(date_raw)

            month_manifest = m.get("batch_id", "")
            year_from_batch = ""
            month_from_batch = ""
            if MONTH_RE.match(month_manifest):
                year_from_batch = month_manifest.split("-")[0]
                month_from_batch = month_manifest

            year = date_iso[:4] if date_iso else year_from_batch
            month = date_iso[:7] if date_iso else month_from_batch

            title_norm = r.get("title_normalized", "")
            body_hash = r.get("body_hash_exact", "")

            article_id = build_article_id(
                corpus_name=corpus_name,
                batch_id=batch_id,
                title_normalized=title_norm,
                date_iso=date_iso,
                body_hash_exact=body_hash,
                source_file_name=source_file_name,
            )

            text_body = text_by_path_name.get((source_file_name, source_file_path), "")
            if not text_body:
                text_body = text_by_name.get(source_file_name, "")

            row = {
                "article_id": article_id,
                "corpus_type": corpus_type,
                "corpus_name": corpus_name,
                "batch_id": batch_id,
                "source_archive": m.get("source_archive", "") or r.get("source_archive", ""),
                "date": date_iso,
                "year": year,
                "month": month,
                "publication": r.get("publication", ""),
                "publication_normalized": r.get("publication_normalized", ""),
                "title_original": r.get("title_original", ""),
                "title_normalized": title_norm,
                "byline": r.get("byline", ""),
                "section": r.get("section", ""),
                "word_count": to_int_or_blank(r.get("word_count", "")),
                "body_char_count": to_int_or_blank(r.get("body_char_count", "")),
                "text_body": text_body,
                "body_hash_exact": body_hash,
                "duplicate_group_id": r.get("duplicate_group_id", ""),
                "duplicate_category": r.get("duplicate_category", ""),
                "keep_drop_review": r.get("keep_drop_review", ""),
                "drop_reason": r.get("drop_reason", ""),
                "kept_representative_of_group": r.get("kept_representative_of_group", ""),
                "representative_selection_reason": r.get("representative_selection_reason", ""),
                "malformed_flag": r.get("malformed_flag", ""),
                "malformed_reason": r.get("malformed_reason", ""),
                "source_file_name": source_file_name,
                "source_file_path": source_file_path,
                "protocol_version": m.get("protocol_version", ""),
                "notes": r.get("notes", ""),
                "query_version": "",
                "source_basket_version": "",
                "language": "de",
                "publication_type": "news",
                "date_raw": date_raw,
            }

            all_rows.append(row)

        processed_batches.append(f"{corpus_name}::{batch_id}")

    # Keep-only analytical subset.
    kept_rows = [r for r in all_rows if normalize_token(str(r.get("keep_drop_review", ""))) == "keep"]

    # Ensure consistent column set/order.
    final_columns = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    all_csv = out_dir / "master_articles_all.csv"
    kept_csv = out_dir / "master_articles_kept.csv"
    write_csv(all_csv, all_rows, final_columns)
    write_csv(kept_csv, kept_rows, final_columns)

    wrote_parquet = False
    all_parquet = out_dir / "master_articles_all.parquet"
    kept_parquet = out_dir / "master_articles_kept.parquet"
    if pd is not None:
        pd.DataFrame(all_rows)[final_columns].to_parquet(all_parquet, index=False)
        pd.DataFrame(kept_rows)[final_columns].to_parquet(kept_parquet, index=False)
        wrote_parquet = True

    # Validation checks.
    req_missing = [c for c in REQUIRED_COLUMNS if c not in final_columns]
    id_counter = Counter(r["article_id"] for r in all_rows)
    duplicate_ids = [k for k, v in id_counter.items() if v > 1]
    id_unique = len(duplicate_ids) == 0

    # Batch kept-count comparison against manifest kept_count_if_available.
    expected_kept_by_batch: dict[str, int] = {}
    for m in manifest_rows:
        key = f"{m.get('corpus_name','')}::{m.get('batch_id','')}"
        val = str(m.get("kept_count_if_available", "")).strip()
        if val:
            try:
                expected_kept_by_batch[key] = int(float(val))
            except Exception:
                pass

    actual_kept_by_batch: dict[str, int] = defaultdict(int)
    actual_non_drop_by_batch: dict[str, int] = defaultdict(int)
    for r in kept_rows:
        key = f"{r.get('corpus_name','')}::{r.get('batch_id','')}"
        actual_kept_by_batch[key] += 1
    for r in all_rows:
        key = f"{r.get('corpus_name','')}::{r.get('batch_id','')}"
        if normalize_token(str(r.get("keep_drop_review", ""))) != "drop":
            actual_non_drop_by_batch[key] += 1

    kept_mismatches = []
    nondrop_mismatches = []
    for key, expected in sorted(expected_kept_by_batch.items()):
        actual_keep = actual_kept_by_batch.get(key, 0)
        actual_nondrop = actual_non_drop_by_batch.get(key, 0)
        if expected != actual_keep:
            kept_mismatches.append((key, expected, actual_keep))
        if expected != actual_nondrop:
            nondrop_mismatches.append((key, expected, actual_nondrop))

    # Data dictionary.
    dict_lines = [
        "Master Articles Data Dictionary",
        "",
        "Tables:",
        "- master_articles_all: canonical audit table (kept + dropped + review).",
        "- master_articles_kept: analytical subset where keep_drop_review == keep.",
        "",
        "ID logic:",
        "- article_id is deterministic SHA1 over: corpus_name + batch_id + normalized_title + date + body_hash_exact + source_file_name.",
        "- This makes IDs stable across rebuilds and independent of row order.",
        "",
        "Categorical labels:",
        "- duplicate_category usually: unique, duplicate_exact, duplicate_near, regional_variant.",
        "- keep_drop_review usually: keep, drop, review.",
        "- drop_reason expected primary values: duplicate_exact, duplicate_near, regional_variant, reader_letter, commentary_noncore, very_short_low_value, malformed.",
        "",
        "Columns:",
    ]

    col_desc = {
        "article_id": "Stable deterministic article identifier.",
        "corpus_type": "Corpus grouping label from freeze manifest (e.g., main_monthly, shock).",
        "corpus_name": "Human-readable corpus name (e.g., Main Corpus, Cologne).",
        "batch_id": "Batch identifier (monthly YYYY-MM or shock batch id).",
        "source_archive": "Source archive file name(s) from manifest or registry.",
        "date": "Standardized ISO date (YYYY-MM-DD) parsed from registry date field where possible.",
        "year": "Year used for aggregation (from standardized date or batch fallback).",
        "month": "Month key (YYYY-MM) used for aggregation.",
        "publication": "Original publication/source name.",
        "publication_normalized": "Normalized publication string from registry.",
        "title_original": "Original title text.",
        "title_normalized": "Normalized title text.",
        "byline": "Byline/author when available.",
        "section": "Section metadata when available.",
        "word_count": "Word count from registry.",
        "body_char_count": "Character count of body text from registry.",
        "text_body": "Body text from corresponding qc_articles row (if available).",
        "body_hash_exact": "Exact-body hash from registry.",
        "duplicate_group_id": "Duplicate-group ID when applicable.",
        "duplicate_category": "Duplicate category label.",
        "keep_drop_review": "Manual/automatic disposition label (keep/drop/review).",
        "drop_reason": "Drop reason for excluded rows.",
        "kept_representative_of_group": "Whether row is kept representative for its duplicate group.",
        "representative_selection_reason": "Reason label for representative choice.",
        "malformed_flag": "Malformed record indicator.",
        "malformed_reason": "Reason for malformed flag.",
        "source_file_name": "Source PDF filename.",
        "source_file_path": "Source PDF path recorded in registry.",
        "protocol_version": "Corpus protocol version from freeze manifest.",
        "notes": "Registry notes field.",
        "query_version": "Optional placeholder for query version metadata.",
        "source_basket_version": "Optional placeholder for source-basket version metadata.",
        "language": "Language tag (set to de).",
        "publication_type": "Publication type placeholder (set to news).",
        "date_raw": "Original unparsed registry date string.",
    }

    for c in final_columns:
        dict_lines.append(f"- {c}: {col_desc.get(c, 'No description available.')}")

    (out_dir / "master_articles_data_dictionary.txt").write_text("\n".join(dict_lines), encoding="utf-8")

    # Build log.
    log_lines = [
        "Master Articles Build Log",
        f"build_timestamp={datetime.now().isoformat(timespec='seconds')}",
        f"freeze_manifest={freeze_manifest}",
        "",
        f"source_batch_files_processed={len(processed_batches)}",
        f"source_batch_files_failed={len(failed_batches)}",
        f"total_rows_master_articles_all={len(all_rows)}",
        f"total_rows_master_articles_kept={len(kept_rows)}",
        f"article_id_unique={'YES' if id_unique else 'NO'}",
        f"required_columns_present={'YES' if not req_missing else 'NO'}",
        f"parquet_written={'YES' if wrote_parquet else 'NO'}",
        "",
        "Failed batches:",
    ]
    if failed_batches:
        log_lines.extend([f"- {x}" for x in failed_batches])
    else:
        log_lines.append("- none")

    log_lines.append("")
    log_lines.append("Required-column check:")
    if req_missing:
        log_lines.extend([f"- missing: {c}" for c in req_missing])
    else:
        log_lines.append("- all required columns present")

    log_lines.append("")
    log_lines.append("Kept-count comparison vs manifest kept_count_if_available:")
    log_lines.append("- Comparison A (strict keep only, keep_drop_review == keep):")
    if kept_mismatches:
        for key, expected, actual in kept_mismatches:
            log_lines.append(f"  mismatch {key}: expected={expected} actual={actual}")
    else:
        log_lines.append("  all matched")
    log_lines.append("- Comparison B (non-drop rows, keep or review):")
    if nondrop_mismatches:
        for key, expected, actual in nondrop_mismatches:
            log_lines.append(f"  mismatch {key}: expected={expected} actual={actual}")
    else:
        log_lines.append("  all matched")

    if not id_unique:
        log_lines.append("")
        log_lines.append("Duplicate article_id values (sample up to 20):")
        for aid in duplicate_ids[:20]:
            log_lines.append(f"- {aid} (count={id_counter[aid]})")

    (out_dir / "master_articles_build_log.txt").write_text("\n".join(log_lines), encoding="utf-8")

    print(f"Wrote: {all_csv}")
    print(f"Wrote: {kept_csv}")
    if wrote_parquet:
        print(f"Wrote: {all_parquet}")
        print(f"Wrote: {kept_parquet}")
    print(f"Wrote: {out_dir / 'master_articles_data_dictionary.txt'}")
    print(f"Wrote: {out_dir / 'master_articles_build_log.txt'}")
    print(f"rows_all={len(all_rows)} rows_kept={len(kept_rows)}")
    print(f"batches_processed={len(processed_batches)} batches_failed={len(failed_batches)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
