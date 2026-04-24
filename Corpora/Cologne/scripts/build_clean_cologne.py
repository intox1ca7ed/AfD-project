from __future__ import annotations

import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
COLOGNE_DIR = SCRIPT_DIR.parent
SOURCE_DIR = COLOGNE_DIR / "raw_unarchive"
KEEP_DIR = COLOGNE_DIR / "clean_keep"
DROP_DIR = COLOGNE_DIR / "excluded_drop"
QC_DIR = COLOGNE_DIR / "qc"
QC_ARTICLES = QC_DIR / "qc_articles.csv"
EXCLUSION_LOG = QC_DIR / "exclusion_log.csv"
CLEAN_SUMMARY = QC_DIR / "clean_corpus_summary.md"


def read_qc_rows() -> list[dict[str, str]]:
    with QC_ARTICLES.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def choose_representatives(rows: list[dict[str, str]]) -> dict[str, str]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        duplicate_group = row["near_duplicate_group"] or row["repeated_variant_group"] or row["exact_duplicate_group"]
        if duplicate_group:
            groups[duplicate_group].append(row)

    representatives: dict[str, str] = {}
    for group_id, members in groups.items():
        def sort_key(row: dict[str, str]) -> tuple[int, int, int, str]:
            word_count = int(row.get("body_word_count") or 0)
            no_suffix = 1 if "(2).PDF" not in row["file_name"] else 0
            publication_bonus = 1 if row.get("publication") in {"Kölner Stadt-Anzeiger", "Kölnische Rundschau"} else 0
            return (word_count, no_suffix, publication_bonus, row["file_name"])

        representatives[group_id] = max(members, key=sort_key)["file_name"]
    return representatives


def decision_from_row(row: dict[str, str], representatives: dict[str, str]) -> dict[str, str]:
    file_name = row["file_name"]
    duplicate_group = row["near_duplicate_group"] or row["repeated_variant_group"] or row["exact_duplicate_group"] or ""
    reason = row["keep_drop_reason"]
    notes = ""
    decision = "keep"

    direct_drop_reasons = {
        "reader_letter": "reader_letter",
        "commentary_not_core_event_report": "commentary_not_core_event_report",
        "very_short_low_value": "very_short_low_value",
        "missing_title": "malformed",
        "missing_publication": "malformed",
        "missing_date": "malformed",
        "missing_body_marker": "malformed",
        "empty_body": "malformed",
        "exact_duplicate": "duplicate",
    }

    if reason in direct_drop_reasons:
        decision = "drop"
        reason = direct_drop_reasons[reason]
    elif row["empty_or_malformed"].lower() == "true":
        decision = "drop"
        reason = "malformed"
    elif duplicate_group:
        representative = representatives[duplicate_group]
        if file_name == representative:
            decision = "keep"
            reason = "core_event_report / representative_kept"
            notes = f"Representative kept for {duplicate_group}."
        else:
            decision = "drop"
            reason = "duplicate"
            notes = f"Dropped in favor of representative file: {representative} ({duplicate_group})."
    elif reason == "short_regional_variant":
        decision = "keep"
        reason = "core event report / uncertain regional relevance"
        notes = "Kept conservatively. QC flagged this as a short regional variant, but no confirmed duplicate pair was assigned."
    else:
        decision = "keep"
        reason = "core event report / useful analysis text"
        if row["low_value_flag"].lower() == "true":
            notes = f"Kept conservatively despite QC flag: {row['low_value_reason']}."

    return {
        "file_name": file_name,
        "decision": decision,
        "reason": reason,
        "duplicate_group": duplicate_group,
        "notes": notes,
    }


def ensure_clean_dirs() -> None:
    KEEP_DIR.mkdir(exist_ok=True)
    DROP_DIR.mkdir(exist_ok=True)
    for folder in (KEEP_DIR, DROP_DIR):
        for pdf in folder.glob("*.PDF"):
            pdf.unlink()


def copy_files(log_rows: list[dict[str, str]]) -> None:
    ensure_clean_dirs()
    for row in log_rows:
        source = SOURCE_DIR / row["file_name"]
        target_dir = KEEP_DIR if row["decision"] == "keep" else DROP_DIR
        shutil.copy2(source, target_dir / source.name)


def write_exclusion_log(log_rows: list[dict[str, str]]) -> None:
    fieldnames = ["file_name", "decision", "reason", "duplicate_group", "notes"]
    with EXCLUSION_LOG.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)


def write_summary(log_rows: list[dict[str, str]], representatives: dict[str, str]) -> None:
    decision_counts = Counter(row["decision"] for row in log_rows)
    grouped = defaultdict(list)
    for row in log_rows:
        if row["duplicate_group"]:
            grouped[row["duplicate_group"]].append(row)

    collapsed_groups = sum(
        1 for rows in grouped.values()
        if any(r["decision"] == "keep" for r in rows) and any(r["decision"] == "drop" for r in rows)
    )

    lines = [
        "# Clean Cologne Corpus Summary",
        "",
        f"- Total original files: {len(log_rows)}",
        f"- Kept files: {decision_counts.get('keep', 0)}",
        f"- Dropped files: {decision_counts.get('drop', 0)}",
        f"- Duplicate groups collapsed: {collapsed_groups}",
        "",
        "## Rules Used",
        "",
        "- `keep` = core event report or useful analysis text.",
        "- `drop` = reader letter, commentary not central to the event corpus, very short low-value item, malformed item, or duplicate/variant dropped in favor of one representative file.",
        "- For confirmed near-duplicate or regional-edition clusters, one representative file was kept and the others were dropped.",
        "- If the case was uncertain and not part of a confirmed duplicate cluster, the file was kept and the uncertainty was noted in `exclusion_log.csv`.",
        "",
        "## Collapsed Groups",
        "",
    ]

    if grouped:
        for group_id, rows in sorted(grouped.items()):
            kept = next((r["file_name"] for r in rows if r["decision"] == "keep"), "")
            dropped = [r["file_name"] for r in rows if r["decision"] == "drop"]
            lines.append(f"- {group_id}: kept `{kept}`; dropped {len(dropped)} related file(s).")
    else:
        lines.append("- None")

    CLEAN_SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    QC_DIR.mkdir(exist_ok=True)
    qc_rows = read_qc_rows()
    representatives = choose_representatives(qc_rows)
    log_rows = [decision_from_row(row, representatives) for row in qc_rows]
    write_exclusion_log(log_rows)
    copy_files(log_rows)
    write_summary(log_rows, representatives)
    print(f"Wrote {EXCLUSION_LOG.name} and {CLEAN_SUMMARY.name}")
    print(f"Copied {sum(row['decision'] == 'keep' for row in log_rows)} keep files to {KEEP_DIR}")
    print(f"Copied {sum(row['decision'] == 'drop' for row in log_rows)} drop files to {DROP_DIR}")


if __name__ == "__main__":
    main()
