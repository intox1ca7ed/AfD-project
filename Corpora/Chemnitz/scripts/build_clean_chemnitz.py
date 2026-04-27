from __future__ import annotations

import csv
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CORPUS_DIR = SCRIPT_DIR.parent
QC_DIR = CORPUS_DIR / "qc"


def paths_for(dataset: str) -> dict[str, Path]:
    if dataset not in {"core", "extra"}:
        raise ValueError("Dataset must be 'core' or 'extra'")
    return {
        "source_dir": CORPUS_DIR / f"raw_unarchive_{dataset}",
        "dataset_qc_dir": QC_DIR / dataset,
        "qc_articles": QC_DIR / dataset / "qc_articles.csv",
        "article_registry": QC_DIR / dataset / "article_registry.csv",
        "exclusion_log": QC_DIR / dataset / "exclusion_log.csv",
        "summary_md": QC_DIR / dataset / "clean_corpus_summary.md",
        "keep_dir": CORPUS_DIR / f"clean_keep_{dataset}",
        "drop_dir": CORPUS_DIR / f"excluded_drop_{dataset}",
    }


def read_qc_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
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


def write_article_registry(path: Path, rows: list[dict[str, str]]) -> None:
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
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_exclusion_log(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file_name", "decision", "reason", "duplicate_group", "notes"])
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


def ensure_clean_dirs(keep_dir: Path, drop_dir: Path) -> None:
    keep_dir.mkdir(exist_ok=True)
    drop_dir.mkdir(exist_ok=True)
    for folder in (keep_dir, drop_dir):
        for pdf in folder.glob("*.PDF"):
            pdf.unlink()


def copy_files(source_dir: Path, keep_dir: Path, drop_dir: Path, rows: list[dict[str, str]]) -> None:
    ensure_clean_dirs(keep_dir, drop_dir)
    for row in rows:
        source = source_dir / row["file_name"]
        target_dir = keep_dir if row["keep_drop_review"] in {"keep", "review"} else drop_dir
        shutil.copy2(source, target_dir / source.name)


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
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
        f"# Clean {rows[0]['batch_id'] if rows else CORPUS_DIR.name} Corpus Summary",
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
        "- `article_registry.csv` is the canonical final article-level registry for this corpus batch.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    dataset = sys.argv[1] if len(sys.argv) > 1 else "core"
    cfg = paths_for(dataset)
    cfg["dataset_qc_dir"].mkdir(parents=True, exist_ok=True)
    resolved_rows = resolve_rows(read_qc_rows(cfg["qc_articles"]))
    write_article_registry(cfg["article_registry"], resolved_rows)
    write_exclusion_log(cfg["exclusion_log"], resolved_rows)
    copy_files(cfg["source_dir"], cfg["keep_dir"], cfg["drop_dir"], resolved_rows)
    write_summary(cfg["summary_md"], resolved_rows)
    print(f"Wrote {cfg['article_registry'].name}, {cfg['exclusion_log'].name}, and {cfg['summary_md'].name} for {dataset}")
    print(f"Copied {sum(row['keep_drop_review'] == 'keep' for row in resolved_rows)} keep files to {cfg['keep_dir']}")
    print(f"Copied {sum(row['keep_drop_review'] == 'drop' for row in resolved_rows)} drop files to {cfg['drop_dir']}")


if __name__ == "__main__":
    main()
