from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import statistics
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None


MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
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
MOJIBAKE_REPAIRS = {
    "â€™": "'",
    "â€œ": '"',
    "â€": '"',
    "â€“": "-",
    "â€”": "-",
    "â€¦": "...",
    "Ã¤": "ä",
    "Ã¶": "ö",
    "Ã¼": "ü",
    "Ã„": "Ä",
    "Ã–": "Ö",
    "Ãœ": "Ü",
    "ÃŸ": "ß",
}

MASTER_COLUMNS = [
    "article_id",
    "date",
    "date_original",
    "year",
    "month",
    "source",
    "source_normalized",
    "title",
    "title_normalized",
    "byline",
    "section",
    "word_count",
    "language",
    "publication_type",
    "month_folder",
    "corpus_type",
    "source_file_path",
    "source_file_name",
    "source_archive",
    "keep_drop_status",
    "keep_drop_decision_raw",
    "exclusion_reason",
    "exclusion_reason_standardized",
    "duplicate_category",
    "duplicate_group_id",
    "query_version",
    "batch_id",
    "pdf_checksum_sha256",
    "text_checksum_sha1",
    "text_available",
    "notes",
]

TEXT_COLUMNS = [
    "article_id",
    "month",
    "source_file_name",
    "raw_text",
    "clean_text",
    "text_cleaning_flags",
    "text_checksum_sha1",
]

MONTHLY_COLUMNS = [
    "month",
    "year",
    "n_articles_kept",
    "n_articles_excluded",
    "n_articles_total",
    "n_unique_sources",
    "total_words",
    "mean_words",
    "median_words",
    "n_duplicate_exact",
    "n_duplicate_near",
    "n_regional_variants",
    "n_reader_letters",
    "n_commentary_noncore",
    "n_malformed",
    "n_review_pending",
]


@dataclass
class FreezeSummary:
    freeze_timestamp: str
    corpus_root: str
    month_folders: int
    zip_archives: int
    kept_files: int
    dropped_files: int
    qc_files: int
    raw_unarchive_pdfs: int
    script_path: str
    git_commit: str


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    main_corpus_root = script_dir.parent
    default_output = script_dir / "outputs"

    parser = argparse.ArgumentParser(description="Build post-retrieval freeze + master/monthly/descriptive datasets.")
    parser.add_argument("--main-corpus-root", type=Path, default=main_corpus_root)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--expected-start", default="2013-01")
    parser.add_argument("--expected-end", default="2025-12")
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--checksum-include-pdfs", action="store_true")
    parser.add_argument("--skip-checksums", action="store_true")
    return parser.parse_args()


def discover_month_dirs(main_root: Path) -> list[Path]:
    return sorted(
        p for p in main_root.iterdir() if p.is_dir() and MONTH_RE.match(p.name)
    )


def safe_read_csv_rows(path: Path) -> list[dict[str, str]]:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error: Exception | None = None
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as handle:
                return list(csv.DictReader(handle))
        except Exception as exc:  # pragma: no cover
            last_error = exc
    raise RuntimeError(f"Could not read CSV {path}: {last_error}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def normalize_text(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    if text is None:
        return "", flags

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = unicodedata.normalize("NFKC", cleaned)
    if normalized != cleaned:
        flags.append("unicode_nfkc")

    repaired = normalized
    for bad, good in MOJIBAKE_REPAIRS.items():
        if bad in repaired:
            repaired = repaired.replace(bad, good)
            flags.append("mojibake_repair")

    # Normalize whitespace while preserving paragraph boundaries.
    lines = [" ".join(line.split()) for line in repaired.split("\n")]
    collapsed = "\n".join(lines)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed).strip()
    if collapsed != repaired.strip():
        flags.append("whitespace_normalized")

    dedup_flags = sorted(set(flags))
    return collapsed, dedup_flags


def normalize_token(value: str) -> str:
    clean, _ = normalize_text(value or "")
    return " ".join(clean.lower().split())


def parse_date(date_raw: str, month_folder: str) -> str:
    date_raw = (date_raw or "").strip()
    if not date_raw:
        return ""

    # Pattern: Donnerstag 31. Januar 2013
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", date_raw)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        month_num = GERMAN_MONTHS.get(month_name)
        year = int(m.group(3))
        if month_num:
            try:
                return f"{year:04d}-{month_num:02d}-{day:02d}"
            except ValueError:
                return ""

    # Pattern: DD.MM.YYYY
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_raw)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            return ""

    # Conservative fallback: month start from folder.
    if MONTH_RE.match(month_folder):
        return f"{month_folder}-01"
    return ""


def standardize_reason(reason: str) -> str:
    raw = normalize_token(reason)
    if not raw:
        return ""
    if raw in {"duplicate_exact", "duplicate exact"}:
        return "duplicate_exact"
    if raw in {"duplicate_near", "duplicate near"}:
        return "duplicate_near"
    if raw in {"regional_variant", "regional variant", "repeated_variant", "repeated variant"}:
        return "regional_variant"
    if "reader_letter" in raw or "leserbrief" in raw:
        return "reader_letter_or_opinion"
    if "commentary_noncore" in raw or "kommentar" in raw or "opinion" in raw:
        return "commentary_noncore"
    if "very_short_low_value" in raw or "short" in raw:
        return "very_short_low_value"
    if "malformed" in raw or "placeholder" in raw or "missing_publication" in raw:
        return "malformed_or_unreadable"
    if "out_of_scope" in raw:
        return "out_of_scope"
    return "unknown_or_missing"


def status_from_decision(decision: str, reason_std: str) -> str:
    d = normalize_token(decision)
    if d == "keep":
        return "keep"
    if d == "review":
        return "review_pending"
    if d == "drop":
        if reason_std == "duplicate_exact":
            return "excluded_duplicate_exact"
        if reason_std == "duplicate_near":
            return "excluded_duplicate_near"
        if reason_std == "regional_variant":
            return "excluded_regional_variant"
        return "excluded_other"
    return "unknown"


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_table(base_path: Path, rows: list[dict[str, Any]], columns: list[str]) -> tuple[Path, Path | None]:
    csv_path = base_path.with_suffix(".csv")
    write_csv(csv_path, rows, columns)

    parquet_path: Path | None = None
    if pd is not None:
        parquet_path = base_path.with_suffix(".parquet")
        df = pd.DataFrame(rows)
        # Keep expected column order where present.
        ordered = [c for c in columns if c in df.columns]
        other = [c for c in df.columns if c not in ordered]
        df = df[ordered + other]
        df.to_parquet(parquet_path, index=False)
    return csv_path, parquet_path


def unique_glob(paths: list[Path]) -> list[Path]:
    unique: dict[str, Path] = {}
    for p in paths:
        unique[str(p.resolve()).lower()] = p
    return sorted(unique.values())


def collect_freeze_artifacts(
    main_root: Path,
    month_dirs: list[Path],
    freeze_date: str,
    output_dir: Path,
    include_pdf_checksums: bool,
    skip_checksums: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], FreezeSummary]:
    manifest_rows: list[dict[str, Any]] = []
    checksum_rows: list[dict[str, Any]] = []

    total_zip = 0
    total_keep = 0
    total_drop = 0
    total_qc_files = 0
    total_raw = 0

    for month_dir in month_dirs:
        zips = unique_glob(list(month_dir.glob("*.zip")) + list(month_dir.glob("*.ZIP")))
        keep_files = unique_glob(
            list((month_dir / "clean_keep").glob("*.pdf")) + list((month_dir / "clean_keep").glob("*.PDF"))
        )
        drop_files = unique_glob(
            list((month_dir / "excluded_drop").glob("*.pdf")) + list((month_dir / "excluded_drop").glob("*.PDF"))
        )
        raw_files = unique_glob(
            list((month_dir / "raw_unarchive").glob("*.pdf")) + list((month_dir / "raw_unarchive").glob("*.PDF"))
        )

        qc_paths = sorted((month_dir / "qc").glob("*")) if (month_dir / "qc").exists() else []
        qc_files = [p for p in qc_paths if p.is_file()]

        total_zip += len(zips)
        total_keep += len(keep_files)
        total_drop += len(drop_files)
        total_qc_files += len(qc_files)
        total_raw += len(raw_files)

        reg_rows = 0
        excl_rows = 0
        qc_rows = 0
        reg_path = month_dir / "qc" / "article_registry.csv"
        excl_path = month_dir / "qc" / "exclusion_log.csv"
        qca_path = month_dir / "qc" / "qc_articles.csv"
        if reg_path.exists():
            reg_rows = len(safe_read_csv_rows(reg_path))
        if excl_path.exists():
            excl_rows = len(safe_read_csv_rows(excl_path))
        if qca_path.exists():
            qc_rows = len(safe_read_csv_rows(qca_path))

        manifest_rows.append(
            {
                "month_folder": month_dir.name,
                "zip_archives": len(zips),
                "zip_names": ";".join(p.name for p in zips),
                "kept_pdf_count": len(keep_files),
                "dropped_pdf_count": len(drop_files),
                "raw_unarchive_pdf_count": len(raw_files),
                "qc_file_count": len(qc_files),
                "article_registry_rows": reg_rows,
                "exclusion_log_rows": excl_rows,
                "qc_articles_rows": qc_rows,
            }
        )

        if not skip_checksums:
            for z in zips:
                checksum_rows.append(
                    {
                        "month_folder": month_dir.name,
                        "file_type": "zip_archive",
                        "relative_path": str(z.relative_to(main_root)),
                        "size_bytes": z.stat().st_size,
                        "sha256": sha256_file(z),
                    }
                )

            for qcf in qc_files:
                checksum_rows.append(
                    {
                        "month_folder": month_dir.name,
                        "file_type": "qc_file",
                        "relative_path": str(qcf.relative_to(main_root)),
                        "size_bytes": qcf.stat().st_size,
                        "sha256": sha256_file(qcf),
                    }
                )

            if include_pdf_checksums:
                for pdf in keep_files + drop_files:
                    checksum_rows.append(
                        {
                            "month_folder": month_dir.name,
                            "file_type": "final_pdf",
                            "relative_path": str(pdf.relative_to(main_root)),
                            "size_bytes": pdf.stat().st_size,
                            "sha256": sha256_file(pdf),
                        }
                    )

    git_commit = ""
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=main_root.parent)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_commit = "unknown"

    freeze_summary = FreezeSummary(
        freeze_timestamp=datetime.now().isoformat(timespec="seconds"),
        corpus_root=str(main_root),
        month_folders=len(month_dirs),
        zip_archives=total_zip,
        kept_files=total_keep,
        dropped_files=total_drop,
        qc_files=total_qc_files,
        raw_unarchive_pdfs=total_raw,
        script_path=str(Path(__file__).resolve()),
        git_commit=git_commit,
    )

    summary_md = output_dir / f"corpus_freeze_summary_{freeze_date}.md"
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text(
        "\n".join(
            [
                f"# Corpus Freeze Summary ({freeze_date})",
                "",
                f"- freeze_timestamp: {freeze_summary.freeze_timestamp}",
                f"- corpus_root: `{freeze_summary.corpus_root}`",
                f"- month_folders: {freeze_summary.month_folders}",
                f"- zip_archives: {freeze_summary.zip_archives}",
                f"- kept_files: {freeze_summary.kept_files}",
                f"- dropped_files: {freeze_summary.dropped_files}",
                f"- qc_files: {freeze_summary.qc_files}",
                f"- raw_unarchive_pdfs: {freeze_summary.raw_unarchive_pdfs}",
                f"- git_commit: {freeze_summary.git_commit}",
                f"- script_path: `{freeze_summary.script_path}`",
                "",
                "Freeze rule: retrieval outputs (`clean_keep`, `excluded_drop`, `qc/*`) are immutable unless a new dated freeze is created.",
            ]
        ),
        encoding="utf-8",
    )

    manifest_path = output_dir / f"corpus_freeze_manifest_{freeze_date}.csv"
    write_csv(manifest_path, manifest_rows)

    if not skip_checksums:
        checksums_path = output_dir / f"corpus_freeze_checksums_{freeze_date}.csv"
        write_csv(
            checksums_path,
            checksum_rows,
            ["month_folder", "file_type", "relative_path", "size_bytes", "sha256"],
        )

    return manifest_rows, checksum_rows, freeze_summary


def build_master_and_text(
    main_root: Path,
    month_dirs: list[Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    master_rows: list[dict[str, Any]] = []
    text_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []

    for month_dir in month_dirs:
        month = month_dir.name
        qc_dir = month_dir / "qc"
        reg_path = qc_dir / "article_registry.csv"
        excl_path = qc_dir / "exclusion_log.csv"
        qca_path = qc_dir / "qc_articles.csv"

        if not (reg_path.exists() and excl_path.exists() and qca_path.exists()):
            continue

        registry_rows = safe_read_csv_rows(reg_path)
        exclusion_rows = safe_read_csv_rows(excl_path)
        qc_rows = safe_read_csv_rows(qca_path)

        exclusion_by_file: dict[str, dict[str, str]] = {r.get("file_name", ""): r for r in exclusion_rows}
        qc_by_file: dict[str, dict[str, str]] = {r.get("file_name", ""): r for r in qc_rows}

        for reg in registry_rows:
            file_name = reg.get("file_name", "")
            excl = exclusion_by_file.get(file_name, {})
            qca = qc_by_file.get(file_name, {})

            raw_text = qca.get("body_text", "")
            clean_text, clean_flags = normalize_text(raw_text)

            reason_candidates = [
                excl.get("reason", ""),
                reg.get("drop_reason", ""),
                reg.get("low_value_reason", ""),
                reg.get("malformed_reason", ""),
                reg.get("duplicate_category", ""),
            ]
            raw_reason = next((x for x in reason_candidates if (x or "").strip()), "")
            reason_std = standardize_reason(raw_reason)

            decision_raw = (excl.get("decision") or reg.get("keep_drop_review") or "").strip()
            keep_drop_status = status_from_decision(decision_raw, reason_std)

            date_original = reg.get("date", "")
            parsed_date = parse_date(date_original, month)
            source = reg.get("publication", "")
            source_norm = reg.get("publication_normalized", "") or normalize_token(source)
            title = reg.get("title_original", "")
            title_norm = reg.get("title_normalized", "") or normalize_token(title)

            id_payload = "||".join(
                [
                    normalize_token(parsed_date),
                    source_norm,
                    title_norm,
                    normalize_token(clean_text),
                ]
            )
            article_id = hashlib.sha1(id_payload.encode("utf-8", errors="ignore")).hexdigest()

            source_file_path = reg.get("file_path", "")
            pdf_hash = ""
            path_obj = Path(source_file_path)
            if source_file_path and path_obj.exists() and path_obj.is_file():
                try:
                    pdf_hash = sha256_file(path_obj)
                except Exception:
                    pdf_hash = ""

            wc_raw = reg.get("word_count", "")
            try:
                wc = int(float(wc_raw))
            except Exception:
                wc = ""

            text_checksum = sha1_text(clean_text) if clean_text else ""
            mapping_rows.append(
                {
                    "month_folder": month,
                    "source_file_name": file_name,
                    "raw_exclusion_reason": raw_reason,
                    "standardized_exclusion_reason": reason_std,
                }
            )

            master_rows.append(
                {
                    "article_id": article_id,
                    "date": parsed_date,
                    "date_original": date_original,
                    "year": month.split("-")[0],
                    "month": month,
                    "source": source,
                    "source_normalized": source_norm,
                    "title": title,
                    "title_normalized": title_norm,
                    "byline": reg.get("byline", ""),
                    "section": reg.get("section", ""),
                    "word_count": wc,
                    "language": "de",
                    "publication_type": "news",
                    "month_folder": month,
                    "corpus_type": "main_corpus",
                    "source_file_path": source_file_path,
                    "source_file_name": file_name,
                    "source_archive": reg.get("source_archive", ""),
                    "keep_drop_status": keep_drop_status,
                    "keep_drop_decision_raw": decision_raw,
                    "exclusion_reason": raw_reason,
                    "exclusion_reason_standardized": reason_std,
                    "duplicate_category": reg.get("duplicate_category", ""),
                    "duplicate_group_id": reg.get("duplicate_group_id", ""),
                    "query_version": "main_corpus_v1",
                    "batch_id": reg.get("batch_id", month),
                    "pdf_checksum_sha256": pdf_hash,
                    "text_checksum_sha1": text_checksum,
                    "text_available": "yes" if clean_text else "no",
                    "notes": reg.get("notes", ""),
                }
            )

            text_rows.append(
                {
                    "article_id": article_id,
                    "month": month,
                    "source_file_name": file_name,
                    "raw_text": raw_text,
                    "clean_text": clean_text,
                    "text_cleaning_flags": ";".join(clean_flags),
                    "text_checksum_sha1": text_checksum,
                }
            )

    return master_rows, text_rows, mapping_rows


def build_monthly_summary(master_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in master_rows:
        by_month[row["month"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    for month in sorted(by_month):
        rows = by_month[month]
        words = [r["word_count"] for r in rows if isinstance(r.get("word_count"), int)]
        sources = {normalize_token(r.get("source", "")) for r in rows if r.get("source", "").strip()}

        def count_status(prefix: str) -> int:
            return sum(1 for r in rows if str(r.get("keep_drop_status", "")).startswith(prefix))

        excluded_rows = [r for r in rows if str(r.get("keep_drop_status", "")).startswith("excluded_")]
        reason_counter = Counter(r.get("exclusion_reason_standardized", "") for r in excluded_rows)

        summary_rows.append(
            {
                "month": month,
                "year": month.split("-")[0],
                "n_articles_kept": sum(1 for r in rows if r.get("keep_drop_status") == "keep"),
                "n_articles_excluded": len(excluded_rows),
                "n_articles_total": len(rows),
                "n_unique_sources": len([s for s in sources if s]),
                "total_words": sum(words) if words else 0,
                "mean_words": round(statistics.mean(words), 3) if words else 0,
                "median_words": round(statistics.median(words), 3) if words else 0,
                "n_duplicate_exact": sum(1 for r in rows if r.get("keep_drop_status") == "excluded_duplicate_exact"),
                "n_duplicate_near": sum(1 for r in rows if r.get("keep_drop_status") == "excluded_duplicate_near"),
                "n_regional_variants": sum(1 for r in rows if r.get("keep_drop_status") == "excluded_regional_variant"),
                "n_reader_letters": reason_counter.get("reader_letter_or_opinion", 0),
                "n_commentary_noncore": reason_counter.get("commentary_noncore", 0),
                "n_malformed": reason_counter.get("malformed_or_unreadable", 0),
                "n_review_pending": sum(1 for r in rows if r.get("keep_drop_status") == "review_pending"),
            }
        )

    return summary_rows


def build_descriptive_outputs(
    master_rows: list[dict[str, Any]],
    monthly_rows: list[dict[str, Any]],
    output_dir: Path,
    expected_start: str,
    expected_end: str,
) -> None:
    desc_dir = output_dir / "descriptive"
    desc_dir.mkdir(parents=True, exist_ok=True)

    # 1) By year.
    by_year_counter = Counter(row["year"] for row in master_rows)
    by_year_rows = [{"year": y, "n_articles_total": c} for y, c in sorted(by_year_counter.items())]
    write_csv(desc_dir / "articles_by_year.csv", by_year_rows, ["year", "n_articles_total"])

    # 2) By month from summary.
    write_csv(desc_dir / "articles_by_month.csv", monthly_rows, MONTHLY_COLUMNS)

    # 3) Top sources.
    src_counter = Counter(normalize_token(r.get("source", "")) for r in master_rows if r.get("source", "").strip())
    source_rows = [
        {"source_normalized": src, "n_articles": n}
        for src, n in src_counter.most_common(100)
    ]
    write_csv(desc_dir / "top_sources.csv", source_rows, ["source_normalized", "n_articles"])

    # 4) Word distribution bins.
    bins = [(0, 199), (200, 399), (400, 799), (800, 1199), (1200, 1000000)]
    bin_counts = Counter()
    for row in master_rows:
        wc = row.get("word_count")
        if not isinstance(wc, int):
            continue
        for low, high in bins:
            if low <= wc <= high:
                label = f"{low}-{high if high < 1000000 else 'plus'}"
                bin_counts[label] += 1
                break
    word_rows = [{"word_count_bin": k, "n_articles": v} for k, v in bin_counts.items()]
    write_csv(desc_dir / "word_count_distribution.csv", word_rows, ["word_count_bin", "n_articles"])

    # 5) Exclusion reasons.
    excl_counter = Counter(
        row.get("exclusion_reason_standardized", "")
        for row in master_rows
        if str(row.get("keep_drop_status", "")).startswith("excluded_")
    )
    excl_rows = [{"exclusion_reason_standardized": k, "n_articles": v} for k, v in excl_counter.items()]
    write_csv(desc_dir / "exclusion_reason_counts.csv", excl_rows, ["exclusion_reason_standardized", "n_articles"])

    # 6) Duplicate categories.
    dup_counter = Counter(row.get("duplicate_category", "") for row in master_rows)
    dup_rows = [{"duplicate_category": k, "n_articles": v} for k, v in dup_counter.items()]
    write_csv(desc_dir / "duplicate_category_counts.csv", dup_rows, ["duplicate_category", "n_articles"])

    # 7) Suspicious months.
    month_totals = [int(r["n_articles_total"]) for r in monthly_rows]
    suspicious_rows: list[dict[str, Any]] = []

    if month_totals:
        q1 = statistics.quantiles(month_totals, n=4)[0]
        q3 = statistics.quantiles(month_totals, n=4)[2]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        for row in monthly_rows:
            n_total = int(row["n_articles_total"])
            issue = ""
            if n_total < lower:
                issue = "low_outlier"
            elif n_total > upper:
                issue = "high_outlier"
            if n_total == 0:
                issue = "zero_articles"
            if issue:
                suspicious_rows.append({"month": row["month"], "n_articles_total": n_total, "issue": issue})

    # Detect missing expected months.
    def month_iter(start: str, end: str) -> list[str]:
        out = []
        sy, sm = map(int, start.split("-"))
        ey, em = map(int, end.split("-"))
        y, m = sy, sm
        while (y < ey) or (y == ey and m <= em):
            out.append(f"{y:04d}-{m:02d}")
            m += 1
            if m == 13:
                m = 1
                y += 1
        return out

    observed = {r["month"] for r in monthly_rows}
    expected = set(month_iter(expected_start, expected_end))
    for missing in sorted(expected - observed):
        suspicious_rows.append({"month": missing, "n_articles_total": "", "issue": "missing_month"})

    write_csv(desc_dir / "suspicious_months.csv", suspicious_rows, ["month", "n_articles_total", "issue"])

    report_lines = [
        "# Corpus Descriptive Statistics",
        "",
        f"- total_articles: {len(master_rows)}",
        f"- total_months_in_master: {len(monthly_rows)}",
        f"- kept_articles: {sum(1 for r in master_rows if r.get('keep_drop_status') == 'keep')}",
        f"- excluded_articles: {sum(1 for r in master_rows if str(r.get('keep_drop_status','')).startswith('excluded_'))}",
        f"- review_pending_articles: {sum(1 for r in master_rows if r.get('keep_drop_status') == 'review_pending')}",
        "",
        "See CSV outputs in this folder for month/year/source/distribution details.",
    ]
    (desc_dir / "descriptive_report.md").write_text("\n".join(report_lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    main_root = args.main_corpus_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    month_dirs = discover_month_dirs(main_root)
    if not month_dirs:
        print("No month directories found.", file=sys.stderr)
        return 1

    freeze_date = datetime.now().strftime("%Y-%m-%d")
    manifest_rows, checksum_rows, freeze_summary = collect_freeze_artifacts(
        main_root=main_root,
        month_dirs=month_dirs,
        freeze_date=freeze_date,
        output_dir=output_dir,
        include_pdf_checksums=args.checksum_include_pdfs,
        skip_checksums=args.skip_checksums,
    )

    print(
        f"Freeze complete: months={freeze_summary.month_folders} zips={freeze_summary.zip_archives} "
        f"keep={freeze_summary.kept_files} drop={freeze_summary.dropped_files}",
        flush=True,
    )

    if args.freeze_only:
        return 0

    master_rows, text_rows, mapping_rows = build_master_and_text(main_root, month_dirs)
    monthly_rows = build_monthly_summary(master_rows)

    datasets_dir = output_dir / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)

    master_csv, master_parquet = write_table(datasets_dir / "master_articles", master_rows, MASTER_COLUMNS)
    text_csv, text_parquet = write_table(datasets_dir / "article_texts", text_rows, TEXT_COLUMNS)
    monthly_csv, monthly_parquet = write_table(datasets_dir / "monthly_summary", monthly_rows, MONTHLY_COLUMNS)

    map_rows_unique = {}
    for row in mapping_rows:
        key = (row["raw_exclusion_reason"], row["standardized_exclusion_reason"])
        map_rows_unique[key] = row
    map_rows = sorted(map_rows_unique.values(), key=lambda r: (r["standardized_exclusion_reason"], r["raw_exclusion_reason"]))
    write_csv(
        datasets_dir / "exclusion_reason_mapping.csv",
        map_rows,
        ["month_folder", "source_file_name", "raw_exclusion_reason", "standardized_exclusion_reason"],
    )

    build_descriptive_outputs(
        master_rows=master_rows,
        monthly_rows=monthly_rows,
        output_dir=output_dir,
        expected_start=args.expected_start,
        expected_end=args.expected_end,
    )

    run_log = output_dir / "post_retrieval_run_log.txt"
    with run_log.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{datetime.now().isoformat(timespec='seconds')} | "
            f"master_rows={len(master_rows)} text_rows={len(text_rows)} months={len(monthly_rows)} "
            f"parquet={'yes' if pd is not None else 'no'}\n"
        )

    print(f"master_csv={master_csv}")
    print(f"article_texts_csv={text_csv}")
    print(f"monthly_summary_csv={monthly_csv}")
    if pd is None:
        print("Parquet not written because pandas/pyarrow is unavailable.")
    else:
        print(f"master_parquet={master_parquet}")
        print(f"article_texts_parquet={text_parquet}")
        print(f"monthly_summary_parquet={monthly_parquet}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
