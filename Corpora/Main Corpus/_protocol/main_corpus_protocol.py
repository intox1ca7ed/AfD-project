from __future__ import annotations

import csv
import hashlib
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
from rapidfuzz import fuzz


BODY_END_MARKERS = (
    "\nClassification\n",
    "\nLoad-Date:",
    "\nEnd of Document",
)

DATE_LINE_RE = re.compile(
    r"^(?:(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+)?\d{1,2}\.\s+[A-Z\u00c4\u00d6\u00dca-z\u00e4\u00f6\u00fc\u00df]+\s+\d{4}(?:\s+(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag))?$"
)

PLACEHOLDER_TITLES = {
    "no headline in original",
}

PROTOCOL_OUTPUT_RELATIVE_PATHS = (
    Path("qc") / "qc_articles.csv",
    Path("qc") / "duplicate_groups.csv",
    Path("qc") / "qc_summary.md",
    Path("qc") / "article_registry.csv",
    Path("qc") / "exclusion_log.csv",
    Path("qc") / "clean_corpus_summary.md",
)


@dataclass(frozen=True)
class MonthPaths:
    month_dir: Path
    raw_unarchive: Path
    qc_dir: Path
    clean_keep: Path
    excluded_drop: Path
    qc_articles: Path
    duplicate_groups: Path
    qc_summary: Path
    article_registry: Path
    exclusion_log: Path
    clean_summary: Path


@dataclass
class ArticleRecord:
    batch_id: str
    corpus_name: str
    source_archive: str
    file_name: str
    file_path: str
    title_original: str
    title_normalized: str
    publication: str
    publication_normalized: str
    date: str
    byline: str
    section: str
    word_count: int
    body_char_count: int
    body_hash_exact: str
    duplicate_group_id: str
    duplicate_category: str
    keep_drop_review: str
    drop_reason: str
    kept_representative_of_group: str
    representative_selection_reason: str
    malformed_flag: str
    malformed_reason: str
    notes: str
    raw_text_chars: int
    low_value_flag: str
    low_value_reason: str
    exact_duplicate_group: str
    near_duplicate_group: str
    repeated_variant_group: str
    body_text: str


@dataclass(frozen=True)
class ProtocolResult:
    pdf_count: int
    kept_count: int
    dropped_count: int
    review_count: int


def build_month_paths(month_dir: Path) -> MonthPaths:
    qc_dir = month_dir / "qc"
    return MonthPaths(
        month_dir=month_dir,
        raw_unarchive=month_dir / "raw_unarchive",
        qc_dir=qc_dir,
        clean_keep=month_dir / "clean_keep",
        excluded_drop=month_dir / "excluded_drop",
        qc_articles=qc_dir / "qc_articles.csv",
        duplicate_groups=qc_dir / "duplicate_groups.csv",
        qc_summary=qc_dir / "qc_summary.md",
        article_registry=qc_dir / "article_registry.csv",
        exclusion_log=qc_dir / "exclusion_log.csv",
        clean_summary=qc_dir / "clean_corpus_summary.md",
    )


def ensure_month_dirs(paths: MonthPaths) -> None:
    paths.raw_unarchive.mkdir(parents=True, exist_ok=True)
    paths.qc_dir.mkdir(parents=True, exist_ok=True)
    paths.clean_keep.mkdir(parents=True, exist_ok=True)
    paths.excluded_drop.mkdir(parents=True, exist_ok=True)


def protocol_outputs_exist(month_dir: Path) -> bool:
    return all((month_dir / rel_path).exists() for rel_path in PROTOCOL_OUTPUT_RELATIVE_PATHS)


def list_month_pdfs(raw_unarchive_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_unarchive_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )


def read_registry_counts(month_dir: Path) -> tuple[int, int, int]:
    registry_path = month_dir / "qc" / "article_registry.csv"
    if not registry_path.exists():
        return 0, 0, 0

    with registry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    decisions = Counter((row.get("keep_drop_review") or "").strip().lower() for row in rows)
    return decisions.get("keep", 0), decisions.get("drop", 0), decisions.get("review", 0)


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)


def clean_whitespace(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("\u00df", "ss")
    text = text.replace("\u00c3\u0178", "ss")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def parse_article(path: Path, batch_id: str, corpus_name: str, source_archive: str) -> ArticleRecord:
    raw = clean_whitespace(pdf_text(path))
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    title = lines[0] if lines else ""
    publication = ""
    date = ""
    byline = ""
    section = ""
    body = ""

    malformed_reasons: list[str] = []

    date_idx = None
    for i, line in enumerate(lines):
        if DATE_LINE_RE.match(line):
            date = line
            date_idx = i
            break

    if date_idx is not None and date_idx > 0:
        publication = lines[date_idx - 1]
        title_candidates: list[str] = []
        seen = set()
        for line in lines[: date_idx - 1]:
            norm = normalize_text(line)
            if not norm or norm in seen:
                continue
            if line.startswith(("Copyright ", "Section:", "Length:", "Byline:", "Highlight:")):
                continue
            seen.add(norm)
            title_candidates.append(line)
        if title_candidates:
            preferred = [line for line in title_candidates if "..." not in line and "...." not in line]
            title = max(preferred or title_candidates, key=len)

    section_match = re.search(r"(?m)^Section:\s*(.+)$", raw)
    if section_match:
        section = section_match.group(1).strip()

    byline_match = re.search(r"(?m)^Byline:\s*(.+)$", raw)
    if byline_match:
        byline = byline_match.group(1).strip()

    body_match = re.search(r"\nBody\n", raw)
    if body_match:
        body_start = body_match.end()
        body_end = len(raw)
        for marker in BODY_END_MARKERS:
            marker_idx = raw.find(marker, body_start)
            if marker_idx != -1:
                body_end = min(body_end, marker_idx)
        body = raw[body_start:body_end].strip()
    else:
        malformed_reasons.append("missing_body_marker")

    if title and body.startswith(title):
        body = body[len(title) :].strip()

    body = re.sub(r"\n{2,}", "\n\n", body).strip()
    word_count = len(re.findall(r"\b\w+\b", body, flags=re.UNICODE))
    body_char_count = len(body)

    title_normalized = normalize_text(title)
    publication_normalized = normalize_text(publication)

    if not title:
        malformed_reasons.append("missing_title")
    if title_normalized in PLACEHOLDER_TITLES:
        malformed_reasons.append("placeholder_title")
    if not publication:
        malformed_reasons.append("missing_publication")
    if not date:
        malformed_reasons.append("missing_date")
    if not body:
        malformed_reasons.append("empty_body")
    if body_char_count < 80 or word_count < 15:
        malformed_reasons.append("body_too_short_to_use")

    low_value_reasons: list[str] = []
    title_lc = title.lower()
    section_lc = section.lower()

    opinion_markers = [
        "kommentar",
        "meinung",
        "gott und die welt",
        "standpunkt",
        "leitartikel",
        "analyse",
        "essay",
        "kolumne",
        "glosse",
        "zippert zappt",
        "zwischenruf",
        "positionen",
    ]
    letter_markers = [
        "leserbrief",
        "briefe an die redaktion",
        "brief",
        "for the editor",
    ]

    if any(marker in section_lc for marker in opinion_markers) or any(marker in title_lc for marker in opinion_markers):
        low_value_reasons.append("commentary_noncore")
    if any(marker in section_lc for marker in letter_markers) or any(marker in title_lc for marker in letter_markers):
        low_value_reasons.append("reader_letter")
    if word_count and word_count < 120:
        low_value_reasons.append("very_short_low_value")
    if word_count and word_count < 220 and any(
        marker in section_lc for marker in ["lokales", "vermischtes", "service", "szene", "stadtteile"]
    ):
        low_value_reasons.append("regional_variant_review")

    keep_drop_review = "keep"
    drop_reason = ""
    notes = ""

    if malformed_reasons:
        keep_drop_review = "drop"
        drop_reason = "malformed"
    elif "reader_letter" in low_value_reasons:
        keep_drop_review = "drop"
        drop_reason = "reader_letter"
    elif "commentary_noncore" in low_value_reasons and word_count < 700:
        keep_drop_review = "drop"
        drop_reason = "commentary_noncore"
    elif "very_short_low_value" in low_value_reasons:
        keep_drop_review = "drop"
        drop_reason = "very_short_low_value"
    elif "regional_variant_review" in low_value_reasons:
        keep_drop_review = "review"
        notes = "Short local brief kept for review."

    return ArticleRecord(
        batch_id=batch_id,
        corpus_name=corpus_name,
        source_archive=source_archive,
        file_name=path.name,
        file_path=str(path.resolve()),
        title_original=title,
        title_normalized=title_normalized,
        publication=publication,
        publication_normalized=publication_normalized,
        date=date,
        byline=byline,
        section=section,
        word_count=word_count,
        body_char_count=body_char_count,
        body_hash_exact=hashlib.sha1(normalize_text(body).encode("utf-8")).hexdigest(),
        duplicate_group_id="",
        duplicate_category="unique",
        keep_drop_review=keep_drop_review,
        drop_reason=drop_reason,
        kept_representative_of_group="no",
        representative_selection_reason="",
        malformed_flag="yes" if malformed_reasons else "no",
        malformed_reason="; ".join(dict.fromkeys(malformed_reasons)),
        notes=notes,
        raw_text_chars=len(raw),
        low_value_flag="yes" if low_value_reasons else "no",
        low_value_reason="; ".join(dict.fromkeys(low_value_reasons)),
        exact_duplicate_group="",
        near_duplicate_group="",
        repeated_variant_group="",
        body_text=body,
    )


def group_exact_duplicates(records: list[ArticleRecord]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, rec in enumerate(records):
        key = rec.body_hash_exact if rec.body_text else f"empty::{rec.file_name}"
        groups[key].append(idx)
    return {key: indexes for key, indexes in groups.items() if len(indexes) > 1}


def same_story_candidate(a: ArticleRecord, b: ArticleRecord) -> bool:
    if not a.body_text or not b.body_text:
        return False
    if a.date and b.date and a.date != b.date:
        return False
    title_sim = fuzz.token_set_ratio(a.title_normalized, b.title_normalized)
    body_sim = fuzz.token_set_ratio(normalize_text(a.body_text[:5000]), normalize_text(b.body_text[:5000]))
    len_ratio = min(a.word_count, b.word_count) / max(a.word_count, b.word_count)
    return body_sim >= 90 and title_sim >= 65 and len_ratio >= 0.6


def repeated_variant_candidate(a: ArticleRecord, b: ArticleRecord) -> bool:
    if not a.body_text or not b.body_text:
        return False
    if a.publication != b.publication or a.date != b.date:
        return False
    title_sim = fuzz.token_set_ratio(a.title_normalized, b.title_normalized)
    body_sim = fuzz.token_set_ratio(normalize_text(a.body_text[:5000]), normalize_text(b.body_text[:5000]))
    if body_sim < 82:
        return False
    if title_sim >= 85:
        return True
    shared = set((a.section or "").split(";")) & set((b.section or "").split(";"))
    return bool(shared)


def connected_components(edges: Iterable[tuple[int, int]], n_items: int) -> list[list[int]]:
    parent = list(range(n_items))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in edges:
        union(a, b)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n_items):
        groups[find(i)].append(i)
    return [group for group in groups.values() if len(group) > 1]


def build_group_row(records: list[ArticleRecord], group_id: str, group_type: str, indexes: list[int]) -> dict[str, str]:
    return {
        "group_id": group_id,
        "group_type": group_type,
        "item_count": str(len(indexes)),
        "files": " | ".join(records[idx].file_name for idx in indexes),
        "titles": " | ".join(records[idx].title_original for idx in indexes),
        "publications": " | ".join(records[idx].publication for idx in indexes),
        "dates": " | ".join(records[idx].date for idx in indexes),
    }


def assign_group_labels(records: list[ArticleRecord]) -> list[dict[str, str]]:
    duplicate_rows: list[dict[str, str]] = []
    exact_groups = group_exact_duplicates(records)
    exact_counter = 0
    near_counter = 0
    variant_counter = 0

    for indexes in exact_groups.values():
        exact_counter += 1
        group_id = f"exact_{exact_counter:03d}"
        for idx in indexes:
            records[idx].exact_duplicate_group = group_id
        duplicate_rows.append(build_group_row(records, group_id, "duplicate_exact", indexes))

    near_edges = []
    variant_edges = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if records[i].exact_duplicate_group and records[i].exact_duplicate_group == records[j].exact_duplicate_group:
                continue
            if same_story_candidate(records[i], records[j]):
                near_edges.append((i, j))
            if repeated_variant_candidate(records[i], records[j]):
                variant_edges.append((i, j))

    for indexes in connected_components(near_edges, len(records)):
        near_counter += 1
        group_id = f"near_{near_counter:03d}"
        for idx in indexes:
            records[idx].near_duplicate_group = group_id
        duplicate_rows.append(build_group_row(records, group_id, "duplicate_near", indexes))

    for indexes in connected_components(variant_edges, len(records)):
        variant_counter += 1
        group_id = f"variant_{variant_counter:03d}"
        for idx in indexes:
            records[idx].repeated_variant_group = group_id
        duplicate_rows.append(build_group_row(records, group_id, "regional_variant", indexes))

    for rec in records:
        if rec.exact_duplicate_group:
            rec.duplicate_category = "duplicate_exact"
            rec.duplicate_group_id = rec.exact_duplicate_group
            if rec.keep_drop_review == "keep":
                rec.keep_drop_review = "review"
        elif rec.repeated_variant_group:
            rec.duplicate_category = "regional_variant"
            rec.duplicate_group_id = rec.repeated_variant_group
            if rec.keep_drop_review == "keep":
                rec.keep_drop_review = "review"
        elif rec.near_duplicate_group:
            rec.duplicate_category = "duplicate_near"
            rec.duplicate_group_id = rec.near_duplicate_group
            if rec.keep_drop_review == "keep":
                rec.keep_drop_review = "review"

    return duplicate_rows


def write_qc_articles(paths: MonthPaths, records: list[ArticleRecord]) -> None:
    fieldnames = [
        "batch_id",
        "corpus_name",
        "source_archive",
        "file_name",
        "file_path",
        "title_original",
        "title_normalized",
        "publication",
        "publication_normalized",
        "date",
        "byline",
        "section",
        "word_count",
        "body_char_count",
        "body_hash_exact",
        "duplicate_group_id",
        "duplicate_category",
        "keep_drop_review",
        "drop_reason",
        "kept_representative_of_group",
        "representative_selection_reason",
        "malformed_flag",
        "malformed_reason",
        "notes",
        "raw_text_chars",
        "low_value_flag",
        "low_value_reason",
        "exact_duplicate_group",
        "near_duplicate_group",
        "repeated_variant_group",
        "body_text",
    ]
    with paths.qc_articles.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec.__dict__)


def write_duplicate_groups(paths: MonthPaths, rows: list[dict[str, str]]) -> None:
    with paths.duplicate_groups.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["group_id", "group_type", "item_count", "files", "titles", "publications", "dates"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_qc_summary(paths: MonthPaths, records: list[ArticleRecord], duplicate_rows: list[dict[str, str]]) -> None:
    total = len(records)
    unique_count = sum(1 for rec in records if rec.duplicate_category == "unique") + len(
        {rec.duplicate_group_id for rec in records if rec.duplicate_group_id}
    )
    malformed = [rec for rec in records if rec.malformed_flag == "yes"]
    keep_counts = Counter(rec.keep_drop_review for rec in records)
    outlets = Counter(rec.publication or "UNKNOWN" for rec in records)

    lines = [
        f"# {records[0].batch_id if records else paths.month_dir.name} QC Summary",
        "",
        "## Overall",
        "",
        f"- Total file count: {total}",
        f"- Unique article count after duplicate collapse: {unique_count}",
        f"- Exact duplicate groups: {sum(row['group_type'] == 'duplicate_exact' for row in duplicate_rows)}",
        f"- Suspicious near-duplicate groups: {sum(row['group_type'] == 'duplicate_near' for row in duplicate_rows)}",
        f"- Repeated regional-edition variant groups: {sum(row['group_type'] == 'regional_variant' for row in duplicate_rows)}",
        f"- Malformed records: {len(malformed)}",
        f"- Keep: {keep_counts.get('keep', 0)}",
        f"- Review: {keep_counts.get('review', 0)}",
        f"- Drop: {keep_counts.get('drop', 0)}",
        "",
        "## Outlet Frequency",
        "",
        "| Publication | Count |",
        "| --- | ---: |",
    ]
    for publication, count in outlets.most_common():
        lines.append(f"| {publication} | {count} |")

    for section_title, group_type in [
        ("Duplicate Groups", "duplicate_exact"),
        ("Suspicious Near-Duplicate Groups", "duplicate_near"),
        ("Repeated Regional Variants", "regional_variant"),
    ]:
        lines.extend([f"## {section_title}", ""])
        group_rows = [row for row in duplicate_rows if row["group_type"] == group_type]
        if group_rows:
            for row in group_rows:
                lines.append(f"- {row['group_id']} ({row['item_count']} items): {row['files']}")
        else:
            lines.append("- None")
        lines.append("")

    if malformed:
        lines.extend(["## Malformed Records", ""])
        for rec in malformed:
            lines.append(f"- {rec.file_name}: {rec.malformed_reason}")
        lines.append("")

    paths.qc_summary.write_text("\n".join(lines), encoding="utf-8")


def read_qc_rows(paths: MonthPaths) -> list[dict[str, str]]:
    with paths.qc_articles.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def final_duplicate_category(row: dict[str, str]) -> tuple[str, str]:
    if row["exact_duplicate_group"]:
        return "duplicate_exact", row["exact_duplicate_group"]
    if row["repeated_variant_group"]:
        return "regional_variant", row["repeated_variant_group"]
    if row["near_duplicate_group"]:
        return "duplicate_near", row["near_duplicate_group"]
    return "unique", ""


def has_numeric_suffix(file_name: str) -> bool:
    return bool(re.search(r"\(\d+\)\.PDF$", file_name, flags=re.IGNORECASE))


def completeness_score(row: dict[str, str]) -> int:
    return sum(
        1
        for field in ("title_original", "publication", "date", "body_text")
        if (row.get(field) or "").strip()
    ) + (1 if row.get("malformed_flag") == "no" else 0)


def clean_parse_score(row: dict[str, str]) -> int:
    return (
        (1 if row.get("malformed_flag") == "no" else 0)
        + (1 if not has_numeric_suffix(row["file_name"]) else 0)
        + (1 if not row.get("low_value_reason") else 0)
    )


def representative_reason(group_rows: list[dict[str, str]], selected: dict[str, str]) -> str:
    completeness_values = [completeness_score(row) for row in group_rows]
    if completeness_score(selected) == max(completeness_values) and completeness_values.count(max(completeness_values)) == 1:
        return "most_complete_metadata"

    word_counts = [int(row.get("word_count") or 0) for row in group_rows]
    if int(selected.get("word_count") or 0) == max(word_counts) and word_counts.count(max(word_counts)) == 1:
        return "longest_usable_body"

    clean_values = [clean_parse_score(row) for row in group_rows]
    if clean_parse_score(selected) == max(clean_values) and clean_values.count(max(clean_values)) == 1:
        return "cleanest_parsed_version"

    return "lexical_filename_tiebreak"


def choose_representatives(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        category, group_id = final_duplicate_category(row)
        if category != "unique":
            grouped[group_id].append(row)

    representatives: dict[str, str] = {}
    reasons: dict[str, str] = {}

    for group_id, group_rows in grouped.items():
        ordered = sorted(
            group_rows,
            key=lambda row: (
                -completeness_score(row),
                -int(row.get("word_count") or 0),
                -clean_parse_score(row),
                row["file_name"],
            ),
        )
        selected = ordered[0]
        representatives[group_id] = selected["file_name"]
        reasons[group_id] = representative_reason(group_rows, selected)

    return representatives, reasons


def resolve_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    representatives, rep_reasons = choose_representatives(rows)
    resolved: list[dict[str, str]] = []

    for row in rows:
        category, group_id = final_duplicate_category(row)
        keep_drop_review = row["keep_drop_review"] or "keep"
        drop_reason = ""
        kept_representative = "no"
        representative_selection_reason = ""
        notes = row.get("notes", "")

        if row["malformed_flag"] == "yes":
            keep_drop_review = "drop"
            drop_reason = "malformed"
        elif category != "unique":
            representative = representatives[group_id]
            if row["file_name"] == representative:
                keep_drop_review = "keep"
                kept_representative = "yes"
                representative_selection_reason = rep_reasons[group_id]
                if notes:
                    notes = f"{notes} Representative kept for {group_id}."
                else:
                    notes = f"Representative kept for {group_id}."
            else:
                keep_drop_review = "drop"
                drop_reason = category
                notes = f"Dropped in favor of representative file: {representative} ({group_id})."
        elif keep_drop_review == "drop":
            drop_reason = row.get("drop_reason", "")
        else:
            keep_drop_review = "review" if row.get("keep_drop_review") == "review" else "keep"

        resolved.append(
            {
                "batch_id": row["batch_id"],
                "corpus_name": row["corpus_name"],
                "source_archive": row["source_archive"],
                "file_name": row["file_name"],
                "file_path": row["file_path"],
                "title_original": row["title_original"],
                "title_normalized": row["title_normalized"],
                "publication": row["publication"],
                "publication_normalized": row["publication_normalized"],
                "date": row["date"],
                "byline": row["byline"],
                "word_count": row["word_count"],
                "body_char_count": row["body_char_count"],
                "body_hash_exact": row["body_hash_exact"],
                "duplicate_group_id": group_id,
                "duplicate_category": category,
                "keep_drop_review": keep_drop_review,
                "drop_reason": drop_reason if keep_drop_review == "drop" else "",
                "kept_representative_of_group": kept_representative,
                "representative_selection_reason": representative_selection_reason,
                "malformed_flag": row["malformed_flag"],
                "malformed_reason": row["malformed_reason"],
                "notes": notes,
                "section": row.get("section", ""),
                "low_value_flag": row.get("low_value_flag", ""),
                "low_value_reason": row.get("low_value_reason", ""),
            }
        )

    return resolved


def write_article_registry(paths: MonthPaths, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "batch_id",
        "corpus_name",
        "source_archive",
        "file_name",
        "file_path",
        "title_original",
        "title_normalized",
        "publication",
        "publication_normalized",
        "date",
        "byline",
        "word_count",
        "body_char_count",
        "body_hash_exact",
        "duplicate_group_id",
        "duplicate_category",
        "keep_drop_review",
        "drop_reason",
        "kept_representative_of_group",
        "representative_selection_reason",
        "malformed_flag",
        "malformed_reason",
        "notes",
        "section",
        "low_value_flag",
        "low_value_reason",
    ]
    with paths.article_registry.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_exclusion_log(paths: MonthPaths, rows: list[dict[str, str]]) -> None:
    fieldnames = ["file_name", "decision", "reason", "duplicate_group", "notes"]
    with paths.exclusion_log.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "file_name": row["file_name"],
                    "decision": row["keep_drop_review"],
                    "reason": row["drop_reason"],
                    "duplicate_group": row["duplicate_group_id"],
                    "notes": row["notes"],
                }
            )


def clear_pdf_files(folder: Path) -> None:
    for path in folder.iterdir():
        if path.is_file() and path.suffix.lower() == ".pdf":
            path.unlink()


def copy_files(paths: MonthPaths, rows: list[dict[str, str]]) -> None:
    clear_pdf_files(paths.clean_keep)
    clear_pdf_files(paths.excluded_drop)
    for row in rows:
        source = paths.raw_unarchive / row["file_name"]
        if row["keep_drop_review"] == "drop":
            target_dir = paths.excluded_drop
        else:
            target_dir = paths.clean_keep
        shutil.copy2(source, target_dir / source.name)


def write_clean_summary(paths: MonthPaths, rows: list[dict[str, str]]) -> None:
    decision_counts = Counter(row["keep_drop_review"] for row in rows)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["duplicate_group_id"]:
            grouped[row["duplicate_group_id"]].append(row)

    collapsed_groups = sum(
        1
        for members in grouped.values()
        if any(member["kept_representative_of_group"] == "yes" for member in members)
        and any(member["keep_drop_review"] == "drop" for member in members)
    )

    lines = [
        f"# Clean {rows[0]['batch_id'] if rows else paths.month_dir.name} Corpus Summary",
        "",
        f"- Total original files: {len(rows)}",
        f"- Kept files: {decision_counts.get('keep', 0)}",
        f"- Dropped files: {decision_counts.get('drop', 0)}",
        f"- Review files: {decision_counts.get('review', 0)}",
        f"- Duplicate groups collapsed: {collapsed_groups}",
        "",
        "## Representative Selection Rule",
        "",
        "- Priority order: complete metadata, then longest usable body text, then cleanest parsed version, then lexical file-name order.",
        "",
        "## Malformed Criteria",
        "",
        "- Missing or empty title, publication, or date.",
        "- Missing or empty body text.",
        "- Placeholder-like title such as `No Headline In Original`.",
        "- Extremely short extracted body that is clearly unusable.",
        "",
        "## Canonical CSV",
        "",
        "- `article_registry.csv` is the canonical final article-level registry for this corpus.",
    ]
    paths.clean_summary.write_text("\n".join(lines), encoding="utf-8")


def run_month_protocol(month_dir: Path, source_archive: str) -> ProtocolResult:
    paths = build_month_paths(month_dir)
    ensure_month_dirs(paths)

    batch_id = month_dir.name
    corpus_name = month_dir.parent.name
    pdf_paths = list_month_pdfs(paths.raw_unarchive)

    records = [parse_article(path, batch_id, corpus_name, source_archive) for path in pdf_paths]
    duplicate_rows = assign_group_labels(records)
    write_qc_articles(paths, records)
    write_duplicate_groups(paths, duplicate_rows)
    write_qc_summary(paths, records, duplicate_rows)

    resolved_rows = resolve_rows(read_qc_rows(paths))
    write_article_registry(paths, resolved_rows)
    write_exclusion_log(paths, resolved_rows)
    copy_files(paths, resolved_rows)
    write_clean_summary(paths, resolved_rows)

    decision_counts = Counter(row["keep_drop_review"] for row in resolved_rows)
    return ProtocolResult(
        pdf_count=len(pdf_paths),
        kept_count=decision_counts.get("keep", 0),
        dropped_count=decision_counts.get("drop", 0),
        review_count=decision_counts.get("review", 0),
    )
