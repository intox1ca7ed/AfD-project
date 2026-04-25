from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
from rapidfuzz import fuzz


SCRIPT_DIR = Path(__file__).resolve().parent
CORPUS_DIR = SCRIPT_DIR.parent
SOURCE_DIR = CORPUS_DIR / "raw_unarchive"
QC_DIR = CORPUS_DIR / "qc"
ARTICLES_CSV = QC_DIR / "qc_articles.csv"
DUPLICATES_CSV = QC_DIR / "duplicate_groups.csv"
SUMMARY_MD = QC_DIR / "qc_summary.md"


BODY_END_MARKERS = (
    "\nClassification\n",
    "\nLoad-Date:",
    "\nEnd of Document",
)

DATE_LINE_RE = re.compile(
    r"^(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)?\s*\d{1,2}\.\s+[A-ZÄÖÜa-zäöüß]+\s+\d{4}$"
)


@dataclass
class ArticleRecord:
    file_name: str
    file_path: str
    title: str | None
    publication: str | None
    date: str | None
    byline: str | None
    section: str | None
    length_words_header: int | None
    body_text: str
    body_word_count: int
    raw_text_chars: int
    empty_or_malformed: bool
    malformed_reason: str
    low_value_flag: bool
    low_value_reason: str
    keep_drop_flag: str
    keep_drop_reason: str
    exact_duplicate_group: str
    near_duplicate_group: str
    repeated_variant_group: str
    body_hash: str


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
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


def normalize_for_similarity(text: str) -> str:
    text = text.lower()
    text = text.replace("ß", "ss")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def parse_article(path: Path) -> ArticleRecord:
    raw = clean_whitespace(pdf_text(path))
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    title = lines[0] if lines else None
    publication = None
    date = None
    byline = None
    section = None
    length_words_header = None
    body = ""
    malformed_reason = ""

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
            norm = normalize_for_similarity(line)
            if not norm or norm in seen:
                continue
            if line.startswith("Copyright ") or line.startswith("Section:") or line.startswith("Length:"):
                continue
            seen.add(norm)
            title_candidates.append(line)
        if title_candidates:
            preferred = [line for line in title_candidates if "..." not in line and "...." not in line]
            title = max(preferred or title_candidates, key=len)

    section_match = re.search(r"(?m)^Section:\s*(.+)$", raw)
    if section_match:
        section = section_match.group(1).strip()

    length_match = re.search(r"(?m)^Length:\s*(\d+)\s+words?$", raw)
    if length_match:
        length_words_header = int(length_match.group(1))

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
        malformed_reason = "missing_body_marker"

    if title and body.startswith(title):
        body = body[len(title) :].strip()

    body = re.sub(r"\n{2,}", "\n\n", body).strip()
    body_word_count = len(re.findall(r"\b\w+\b", body, flags=re.UNICODE))

    if not title:
        malformed_reason = malformed_reason or "missing_title"
    if not publication:
        malformed_reason = malformed_reason or "missing_publication"
    if not date:
        malformed_reason = malformed_reason or "missing_date"
    if not body:
        malformed_reason = malformed_reason or "empty_body"

    low_value_reasons = []
    title_lc = (title or "").lower()
    section_lc = (section or "").lower()

    opinion_markers = [
        "kommentar",
        "meinung",
        "analyse",
        "leitartikel",
        "essay",
        "kolumne",
        "glosse",
    ]
    letter_markers = [
        "leserbrief",
        "briefe an die redaktion",
        "leser",
    ]

    if any(marker in section_lc for marker in opinion_markers) or any(marker in title_lc for marker in opinion_markers):
        low_value_reasons.append("opinion_or_commentary")
    if any(marker in section_lc for marker in letter_markers) or title_lc.startswith("leser"):
        low_value_reasons.append("reader_letter")
    if body_word_count and body_word_count < 120:
        low_value_reasons.append("very_short")
    if not body:
        low_value_reasons.append("empty_or_malformed")

    keep_drop_flag = "keep"
    keep_drop_reason = "core_event_or_context"
    if malformed_reason:
        keep_drop_flag = "drop"
        keep_drop_reason = malformed_reason
    elif "reader_letter" in low_value_reasons:
        keep_drop_flag = "drop"
        keep_drop_reason = "reader_letter"
    elif "opinion_or_commentary" in low_value_reasons and body_word_count < 700:
        keep_drop_flag = "drop"
        keep_drop_reason = "commentary_not_core_event_report"
    elif "very_short" in low_value_reasons:
        keep_drop_flag = "drop"
        keep_drop_reason = "very_short_low_value"

    body_hash = hashlib.sha1(normalize_for_similarity(body).encode("utf-8")).hexdigest()

    return ArticleRecord(
        file_name=path.name,
        file_path=str(path.resolve()),
        title=title,
        publication=publication,
        date=date,
        byline=byline,
        section=section,
        length_words_header=length_words_header,
        body_text=body,
        body_word_count=body_word_count,
        raw_text_chars=len(raw),
        empty_or_malformed=bool(malformed_reason),
        malformed_reason=malformed_reason,
        low_value_flag=bool(low_value_reasons),
        low_value_reason="; ".join(dict.fromkeys(low_value_reasons)),
        keep_drop_flag=keep_drop_flag,
        keep_drop_reason=keep_drop_reason,
        exact_duplicate_group="",
        near_duplicate_group="",
        repeated_variant_group="",
        body_hash=body_hash,
    )


def group_exact_duplicates(records: list[ArticleRecord]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, rec in enumerate(records):
        key = rec.body_hash if rec.body_text else f"empty::{rec.file_name}"
        groups[key].append(idx)
    return {k: v for k, v in groups.items() if len(v) > 1}


def same_story_candidate(a: ArticleRecord, b: ArticleRecord) -> bool:
    if not a.body_text or not b.body_text:
        return False
    if a.date and b.date and a.date != b.date:
        return False
    title_sim = fuzz.token_set_ratio(a.title or "", b.title or "")
    body_sim = fuzz.token_set_ratio(
        normalize_for_similarity(a.body_text[:5000]),
        normalize_for_similarity(b.body_text[:5000]),
    )
    len_ratio = min(a.body_word_count, b.body_word_count) / max(a.body_word_count, b.body_word_count)
    return body_sim >= 90 and title_sim >= 65 and len_ratio >= 0.6


def repeated_variant_candidate(a: ArticleRecord, b: ArticleRecord) -> bool:
    if not a.body_text or not b.body_text:
        return False
    if a.publication != b.publication or a.date != b.date:
        return False
    title_sim = fuzz.token_set_ratio(a.title or "", b.title or "")
    body_sim = fuzz.token_set_ratio(
        normalize_for_similarity(a.body_text[:5000]),
        normalize_for_similarity(b.body_text[:5000]),
    )
    return body_sim >= 82 and title_sim >= 85


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
        "titles": " | ".join(records[idx].title or "" for idx in indexes),
        "publications": " | ".join(records[idx].publication or "" for idx in indexes),
        "dates": " | ".join(records[idx].date or "" for idx in indexes),
    }


def assign_group_labels(records: list[ArticleRecord]) -> tuple[list[dict[str, str]], dict[str, int]]:
    duplicate_rows: list[dict[str, str]] = []
    exact_groups = group_exact_duplicates(records)
    exact_counter = 0
    near_counter = 0
    variant_counter = 0

    for indexes in exact_groups.values():
        exact_counter += 1
        gid = f"exact_{exact_counter:03d}"
        for idx in indexes:
            records[idx].exact_duplicate_group = gid
        duplicate_rows.append(build_group_row(records, gid, "exact_duplicate", indexes))

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
        gid = f"near_{near_counter:03d}"
        for idx in indexes:
            records[idx].near_duplicate_group = gid
        duplicate_rows.append(build_group_row(records, gid, "near_duplicate", indexes))

    for indexes in connected_components(variant_edges, len(records)):
        variant_counter += 1
        gid = f"variant_{variant_counter:03d}"
        for idx in indexes:
            records[idx].repeated_variant_group = gid
        duplicate_rows.append(build_group_row(records, gid, "regional_variant", indexes))

    for rec in records:
        if rec.exact_duplicate_group and rec.keep_drop_flag != "drop":
            rec.keep_drop_flag = "drop"
            rec.keep_drop_reason = "exact_duplicate"
        elif rec.near_duplicate_group and rec.keep_drop_flag == "keep":
            rec.keep_drop_flag = "review"
            rec.keep_drop_reason = "possible_near_duplicate"
        elif rec.repeated_variant_group and rec.keep_drop_flag == "keep":
            rec.keep_drop_flag = "review"
            rec.keep_drop_reason = "possible_regional_variant"

    return duplicate_rows, {
        "exact_groups": exact_counter,
        "near_groups": near_counter,
        "variant_groups": variant_counter,
    }


def write_articles_csv(records: list[ArticleRecord]) -> None:
    fieldnames = [
        "file_name",
        "file_path",
        "title",
        "publication",
        "date",
        "byline",
        "section",
        "length_words_header",
        "body_word_count",
        "raw_text_chars",
        "empty_or_malformed",
        "malformed_reason",
        "low_value_flag",
        "low_value_reason",
        "exact_duplicate_group",
        "near_duplicate_group",
        "repeated_variant_group",
        "keep_drop_flag",
        "keep_drop_reason",
        "body_hash",
        "body_text",
    ]
    with ARTICLES_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec.__dict__)


def write_duplicates_csv(rows: list[dict[str, str]]) -> None:
    with DUPLICATES_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["group_id", "group_type", "item_count", "files", "titles", "publications", "dates"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_summary(records: list[ArticleRecord], group_counts: dict[str, int], duplicate_rows: list[dict[str, str]]) -> None:
    total = len(records)
    exact_dupe_members = {rec.file_name for rec in records if rec.exact_duplicate_group}
    unique_count = total - len(exact_dupe_members) + group_counts["exact_groups"]
    malformed = [rec for rec in records if rec.empty_or_malformed]
    low_value = [rec for rec in records if rec.low_value_flag]
    keep_counts = Counter(rec.keep_drop_flag for rec in records)
    outlets = Counter(rec.publication or "UNKNOWN" for rec in records)

    lines = [
        "# Corrective Revelation QC Summary",
        "",
        "## Overall",
        "",
        f"- Total file count: {total}",
        f"- Unique article count after exact-duplicate collapse: {unique_count}",
        f"- Exact duplicate groups: {group_counts['exact_groups']}",
        f"- Suspicious near-duplicate groups: {group_counts['near_groups']}",
        f"- Repeated regional-edition variant groups: {group_counts['variant_groups']}",
        f"- Empty or malformed records: {len(malformed)}",
        f"- Low-value / commentary / reader-letter / very short items flagged: {len(low_value)}",
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

    for title, gtype in [
        ("Duplicate Groups", "exact_duplicate"),
        ("Suspicious Near-Duplicate Groups", "near_duplicate"),
        ("Repeated Regional Variants", "regional_variant"),
    ]:
        rows = [row for row in duplicate_rows if row["group_type"] == gtype]
        lines.extend([f"## {title}", ""])
        if rows:
            for row in rows:
                lines.append(f"- {row['group_id']} ({row['item_count']} items): {row['files']}")
        else:
            lines.append("- None")
        lines.append("")

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    QC_DIR.mkdir(exist_ok=True)
    paths = sorted(SOURCE_DIR.glob("*.PDF"))
    records = [parse_article(path) for path in paths]
    duplicate_rows, group_counts = assign_group_labels(records)
    write_articles_csv(records)
    write_duplicates_csv(duplicate_rows)
    write_summary(records, group_counts, duplicate_rows)
    print(f"Processed {len(records)} files")
    print(f"Wrote {ARTICLES_CSV.name}, {DUPLICATES_CSV.name}, {SUMMARY_MD.name}")


if __name__ == "__main__":
    main()
