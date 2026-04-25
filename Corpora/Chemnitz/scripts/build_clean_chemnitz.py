from __future__ import annotations

import csv
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CHEMNITZ_DIR = SCRIPT_DIR.parent
QC_DIR = CHEMNITZ_DIR / "qc"


def paths_for(dataset: str) -> dict[str, Path]:
    if dataset not in {"core", "extra"}:
        raise ValueError("Dataset must be 'core' or 'extra'")
    return {
        "source_dir": CHEMNITZ_DIR / f"raw_unarchive_{dataset}",
        "dataset_qc_dir": QC_DIR / dataset,
        "qc_articles": QC_DIR / dataset / "qc_articles.csv",
        "exclusion_log": QC_DIR / dataset / "exclusion_log.csv",
        "summary_md": QC_DIR / dataset / "clean_corpus_summary.md",
        "keep_dir": CHEMNITZ_DIR / f"clean_keep_{dataset}",
        "drop_dir": CHEMNITZ_DIR / f"excluded_drop_{dataset}",
    }


def read_qc_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def choose_representatives(rows: list[dict[str, str]]) -> dict[str, str]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        for duplicate_group in (
            row["exact_duplicate_group"],
            row["near_duplicate_group"],
            row["repeated_variant_group"],
        ):
            if duplicate_group:
                groups[duplicate_group].append(row)

    representatives: dict[str, str] = {}
    for group_id, members in groups.items():
        def sort_key(row: dict[str, str]) -> tuple[int, int, int, str]:
            word_count = int(row.get("body_word_count") or 0)
            no_suffix = 1 if "(2).PDF" not in row["file_name"] and "(3).PDF" not in row["file_name"] else 0
            publication_bonus = 1 if row.get("publication") not in {"Welt kompakt"} else 0
            return (word_count, publication_bonus, no_suffix, row["file_name"])

        representatives[group_id] = max(members, key=sort_key)["file_name"]
    return representatives


def decision_from_row(row: dict[str, str], representatives: dict[str, str]) -> dict[str, str]:
    file_name = row["file_name"]
    duplicate_group = row["near_duplicate_group"] or row["repeated_variant_group"] or row["exact_duplicate_group"] or ""
    qc_reason = row["keep_drop_reason"]
    decision = "keep"
    reason = "core_event_or_useful_analysis"
    notes = ""

    malformed_reasons = {"missing_title", "missing_publication", "missing_date", "missing_body_marker", "empty_body"}

    if qc_reason in malformed_reasons or row["empty_or_malformed"].lower() == "true":
        decision = "drop"
        reason = "malformed"
    elif qc_reason == "reader_letter":
        decision = "drop"
        reason = "reader_letter"
    elif qc_reason == "commentary_not_core_event_report":
        decision = "drop"
        reason = "commentary_noncore"
    elif qc_reason == "very_short_low_value":
        decision = "drop"
        reason = "very_short_low_value"
    elif row["exact_duplicate_group"]:
        representative = representatives[row["exact_duplicate_group"]]
        if file_name == representative:
            notes = f"Representative kept for {row['exact_duplicate_group']}."
        else:
            decision = "drop"
            reason = "duplicate_exact"
            notes = f"Dropped in favor of representative file: {representative} ({row['exact_duplicate_group']})."
    elif row["near_duplicate_group"]:
        representative = representatives[row["near_duplicate_group"]]
        if file_name == representative:
            notes = f"Representative kept for {row['near_duplicate_group']}."
        else:
            decision = "drop"
            reason = "duplicate_near"
            notes = f"Dropped in favor of representative file: {representative} ({row['near_duplicate_group']})."
    elif row["repeated_variant_group"]:
        representative = representatives[row["repeated_variant_group"]]
        if file_name == representative:
            notes = f"Representative kept for {row['repeated_variant_group']}."
        else:
            decision = "drop"
            reason = "regional_variant"
            notes = f"Dropped in favor of representative file: {representative} ({row['repeated_variant_group']})."
    else:
        if row["low_value_flag"].lower() == "true":
            notes = f"Kept conservatively despite QC flag: {row['low_value_reason']}."

    return {
        "file_name": file_name,
        "decision": decision,
        "reason": reason,
        "duplicate_group": duplicate_group,
        "notes": notes,
    }


def ensure_clean_dirs(keep_dir: Path, drop_dir: Path) -> None:
    keep_dir.mkdir(exist_ok=True)
    drop_dir.mkdir(exist_ok=True)
    for folder in (keep_dir, drop_dir):
        for pdf in folder.glob("*.PDF"):
            pdf.unlink()


def copy_files(source_dir: Path, keep_dir: Path, drop_dir: Path, log_rows: list[dict[str, str]]) -> None:
    ensure_clean_dirs(keep_dir, drop_dir)
    for row in log_rows:
        source = source_dir / row["file_name"]
        target_dir = keep_dir if row["decision"] == "keep" else drop_dir
        shutil.copy2(source, target_dir / source.name)


def write_exclusion_log(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "decision", "reason", "duplicate_group", "notes"])
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, dataset: str, rows: list[dict[str, str]]) -> None:
    decision_counts = Counter(row["decision"] for row in rows)
    grouped = defaultdict(list)
    for row in rows:
        if row["duplicate_group"]:
            grouped[row["duplicate_group"]].append(row)

    collapsed_groups = sum(
        1 for members in grouped.values()
        if any(m["decision"] == "keep" for m in members) and any(m["decision"] == "drop" for m in members)
    )

    lines = [
        f"# Clean Chemnitz {dataset.capitalize()} Corpus Summary",
        "",
        f"- Total original files: {len(rows)}",
        f"- Kept files: {decision_counts.get('keep', 0)}",
        f"- Dropped files: {decision_counts.get('drop', 0)}",
        f"- Duplicate groups collapsed: {collapsed_groups}",
        "",
        "## Rules Used",
        "",
        "- `keep` = core event report or useful analysis text.",
        "- `drop` = `duplicate_exact`, `duplicate_near`, `regional_variant`, `reader_letter`, `commentary_noncore`, `very_short_low_value`, or `malformed`.",
        "- For confirmed duplicate or variant clusters, one representative file was kept and the others were dropped.",
        "- If the case was uncertain and not part of a confirmed duplicate cluster, the file was kept.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    dataset = sys.argv[1] if len(sys.argv) > 1 else "core"
    cfg = paths_for(dataset)
    cfg["dataset_qc_dir"].mkdir(parents=True, exist_ok=True)
    qc_rows = read_qc_rows(cfg["qc_articles"])
    representatives = choose_representatives(qc_rows)
    log_rows = [decision_from_row(row, representatives) for row in qc_rows]
    write_exclusion_log(cfg["exclusion_log"], log_rows)
    copy_files(cfg["source_dir"], cfg["keep_dir"], cfg["drop_dir"], log_rows)
    write_summary(cfg["summary_md"], dataset, log_rows)
    print(f"Wrote {cfg['exclusion_log'].name} and {cfg['summary_md'].name} for {dataset}")
    print(f"Copied {sum(row['decision'] == 'keep' for row in log_rows)} keep files to {cfg['keep_dir']}")
    print(f"Copied {sum(row['decision'] == 'drop' for row in log_rows)} drop files to {cfg['drop_dir']}")


if __name__ == "__main__":
    main()
