from __future__ import annotations

import csv
import re
from calendar import monthrange
from datetime import datetime
from pathlib import Path
from typing import Any

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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def count_pdfs(path: Path) -> int:
    if not path.exists():
        return 0
    return len({str(p.resolve()).lower() for p in path.glob("*.pdf")}.union({str(p.resolve()).lower() for p in path.glob("*.PDF")}))

def unique_paths(paths: list[Path]) -> list[Path]:
    keep: dict[str, Path] = {}
    for p in paths:
        keep[str(p.resolve()).lower()] = p
    return sorted(keep.values())


def parse_german_date(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", value)
    if m:
        d = int(m.group(1))
        month = m.group(2).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        y = int(m.group(3))
        mo = GERMAN_MONTHS.get(month)
        if mo:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def iso_min_max_from_registry(registry_path: Path) -> tuple[str, str]:
    rows = read_csv_rows(registry_path)
    dates = []
    for r in rows:
        parsed = parse_german_date(r.get("date", ""))
        if parsed:
            dates.append(parsed)
    if not dates:
        return "", ""
    dates.sort()
    return dates[0], dates[-1]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in columns})


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def detect_protocol_version(corpora_root: Path) -> str:
    protocol = corpora_root / "corpora-protocol.md"
    text = protocol.read_text(encoding="utf-8", errors="ignore") if protocol.exists() else ""
    m = re.search(r"protocol_version\s*=\s*(\S+)", text)
    return m.group(1) if m else "unknown"


def evaluate_status(missing: list[str], warnings: list[str]) -> str:
    if missing:
        return "needs_manual_check"
    if warnings:
        return "frozen_with_warning"
    return "frozen"


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    corpora_root = project_root / "Corpora"
    freeze_dir = project_root / "freeze"
    freeze_dir.mkdir(parents=True, exist_ok=True)

    protocol_version = detect_protocol_version(corpora_root)
    freeze_date = datetime.now().strftime("%Y-%m-%d")
    freeze_ts = datetime.now().isoformat(timespec="seconds")

    main_root = corpora_root / "Main Corpus"
    month_dirs = sorted([p for p in main_root.iterdir() if p.is_dir() and MONTH_RE.match(p.name)])

    manifest_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    blockers: list[str] = []

    for mdir in month_dirs:
        month = mdir.name
        y, mo = [int(x) for x in month.split("-")]
        date_start = f"{y:04d}-{mo:02d}-01"
        date_end = f"{y:04d}-{mo:02d}-{monthrange(y, mo)[1]:02d}"

        zips = unique_paths(list(mdir.glob("*.ZIP")) + list(mdir.glob("*.zip")))
        zip_names = ";".join(sorted({p.name for p in zips}))

        qc = mdir / "qc"
        qc_summary = qc / "qc_summary.md"
        clean_summary = qc / "clean_corpus_summary.md"
        registry = qc / "article_registry.csv"
        exclusion = qc / "exclusion_log.csv"

        required_missing = []
        for p in [qc_summary, clean_summary, registry, exclusion]:
            if not p.exists():
                required_missing.append(rel(p, project_root))

        registry_rows = read_csv_rows(registry)
        exclusion_rows = read_csv_rows(exclusion)

        raw_count = count_pdfs(mdir / "raw_unarchive")
        kept_count = count_pdfs(mdir / "clean_keep")
        dropped_count = count_pdfs(mdir / "excluded_drop")

        row_warnings = []
        if len(registry_rows) == 0:
            row_warnings.append("empty_article_registry")
        if len(exclusion_rows) == 0:
            row_warnings.append("empty_exclusion_log")
        if len(registry_rows) != len(exclusion_rows) and len(exclusion_rows) > 0:
            row_warnings.append("registry_exclusion_row_mismatch")
        if len(zips) != 1:
            row_warnings.append(f"zip_archive_count={len(zips)}")

        status = evaluate_status(required_missing, row_warnings)
        note_parts = []
        if required_missing:
            note_parts.append("missing=" + "|".join(required_missing))
        if row_warnings:
            note_parts.append("warnings=" + "|".join(row_warnings))

        manifest_rows.append(
            {
                "corpus_type": "main_monthly",
                "corpus_name": "Main Corpus",
                "batch_id": month,
                "date_start": date_start,
                "date_end": date_end,
                "source_archive": zip_names,
                "protocol_version": protocol_version,
                "raw_count_if_available": raw_count,
                "kept_count_if_available": kept_count,
                "dropped_count_if_available": dropped_count,
                "qc_summary_path": rel(qc_summary, project_root),
                "clean_summary_path": rel(clean_summary, project_root),
                "article_registry_path": rel(registry, project_root),
                "status": status,
                "notes": "; ".join(note_parts),
            }
        )

        if status != "frozen":
            issue = f"Main {month}: {status} ({'; '.join(note_parts)})"
            if status == "needs_manual_check":
                blockers.append(issue)
            else:
                warnings.append(issue)

    shock_defs = [
        {
            "corpus_name": "Cologne",
            "folder": corpora_root / "Cologne",
            "batch_id": "cologne",
            "raw_dir": "raw_unarchive",
            "keep_dir": "clean_keep",
            "drop_dir": "excluded_drop",
            "qc_subdir": "qc",
            "registry": "qc/article_registry.csv",
            "qc_summary": "qc/qc_summary.md",
            "clean_summary": "qc/clean_corpus_summary.md",
            "fallback_dates": ("2015-12-31", "2016-01-31"),
        },
        {
            "corpus_name": "Chemnitz",
            "folder": corpora_root / "Chemnitz",
            "batch_id": "chemnitz_core",
            "raw_dir": "raw_unarchive_core",
            "keep_dir": "clean_keep_core",
            "drop_dir": "excluded_drop_core",
            "qc_subdir": "qc/core",
            "registry": "qc/core/article_registry.csv",
            "qc_summary": "qc/core/qc_summary.md",
            "clean_summary": "qc/core/clean_corpus_summary.md",
            "fallback_dates": ("2018-08-01", "2018-09-30"),
        },
        {
            "corpus_name": "Chemnitz",
            "folder": corpora_root / "Chemnitz",
            "batch_id": "chemnitz_extra",
            "raw_dir": "raw_unarchive_extra",
            "keep_dir": "clean_keep_extra",
            "drop_dir": "excluded_drop_extra",
            "qc_subdir": "qc/extra",
            "registry": "qc/extra/article_registry.csv",
            "qc_summary": "qc/extra/qc_summary.md",
            "clean_summary": "qc/extra/clean_corpus_summary.md",
            "fallback_dates": ("2018-08-01", "2018-09-30"),
        },
        {
            "corpus_name": "Corrective Revelation",
            "folder": corpora_root / "Corrective Revelation",
            "batch_id": "corrective_revelation",
            "raw_dir": "raw_unarchive",
            "keep_dir": "clean_keep",
            "drop_dir": "excluded_drop",
            "qc_subdir": "qc",
            "registry": "qc/article_registry.csv",
            "qc_summary": "qc/qc_summary.md",
            "clean_summary": "qc/clean_corpus_summary.md",
            "fallback_dates": ("2024-01-01", "2024-01-31"),
        },
    ]

    expected_shocks = {"Cologne", "Chemnitz", "Corrective Revelation"}
    present_shocks = {d["corpus_name"] for d in shock_defs if d["folder"].exists()}

    for sd in shock_defs:
        folder = sd["folder"]
        qc_summary = folder / sd["qc_summary"]
        clean_summary = folder / sd["clean_summary"]
        registry = folder / sd["registry"]
        exclusion = folder / sd["qc_subdir"] / "exclusion_log.csv"

        zips = unique_paths(list(folder.glob("*.ZIP")) + list(folder.glob("*.zip")))
        zip_names = ";".join(sorted({z.name for z in zips}))

        required_missing = []
        for p in [qc_summary, clean_summary, registry, exclusion]:
            if not p.exists():
                required_missing.append(rel(p, project_root))

        raw_count = count_pdfs(folder / sd["raw_dir"])
        kept_count = count_pdfs(folder / sd["keep_dir"])
        dropped_count = count_pdfs(folder / sd["drop_dir"])

        date_start, date_end = iso_min_max_from_registry(registry)
        if not date_start:
            date_start, date_end = sd["fallback_dates"]

        row_warnings = []
        if len(zips) == 0:
            row_warnings.append("no_source_archive")
        if raw_count == 0:
            row_warnings.append("raw_unarchive_empty")

        status = evaluate_status(required_missing, row_warnings)
        note_parts = []
        if required_missing:
            note_parts.append("missing=" + "|".join(required_missing))
        if row_warnings:
            note_parts.append("warnings=" + "|".join(row_warnings))

        manifest_rows.append(
            {
                "corpus_type": "shock",
                "corpus_name": sd["corpus_name"],
                "batch_id": sd["batch_id"],
                "date_start": date_start,
                "date_end": date_end,
                "source_archive": zip_names,
                "protocol_version": protocol_version,
                "raw_count_if_available": raw_count,
                "kept_count_if_available": kept_count,
                "dropped_count_if_available": dropped_count,
                "qc_summary_path": rel(qc_summary, project_root),
                "clean_summary_path": rel(clean_summary, project_root),
                "article_registry_path": rel(registry, project_root),
                "status": status,
                "notes": "; ".join(note_parts),
            }
        )

        if status != "frozen":
            issue = f"Shock {sd['batch_id']}: {status} ({'; '.join(note_parts)})"
            if status == "needs_manual_check":
                blockers.append(issue)
            else:
                warnings.append(issue)

    manifest_columns = [
        "corpus_type",
        "corpus_name",
        "batch_id",
        "date_start",
        "date_end",
        "source_archive",
        "protocol_version",
        "raw_count_if_available",
        "kept_count_if_available",
        "dropped_count_if_available",
        "qc_summary_path",
        "clean_summary_path",
        "article_registry_path",
        "status",
        "notes",
    ]
    write_csv(freeze_dir / "retrieval_freeze_manifest.csv", manifest_rows, manifest_columns)

    note_lines = [
        "Retrieval Freeze Note",
        "",
        "Project: Master's thesis empirical corpus preparation (AfD support and exogenous political/media shocks)",
        f"Freeze date: {freeze_date}",
        f"Freeze timestamp: {freeze_ts}",
        f"Protocol version: {protocol_version}",
        "",
        "Corpus scope summary:",
        "- Main corpus period: 2013-01 to 2025-12",
        f"- Number of monthly batches: {len(month_dirs)}",
        "- Shock corpora included: Cologne, Chemnitz (core + extra), Corrective Revelation",
        "",
        "Final retrieval assumptions:",
        "- German-language main corpus",
        "- Monthly main corpus design",
        "- Controlled source basket",
        "- Baseline query treated as frozen",
        "",
        "Explicit freeze rule:",
        "- No further corpus changes except serious documented corrections.",
        "- No routine additions, deletions, or silent replacements are allowed.",
        "",
        "Serious correction definition:",
        "- broken archive",
        "- malformed export",
        "- missing batch",
        "- corrupted parsing output",
        "- duplicated month folder",
        "- obviously wrong source contents",
        "",
        "Downstream requirement:",
        "- Downstream master tables and monthly summary datasets must use this frozen version only.",
    ]
    (freeze_dir / "retrieval_freeze_note.txt").write_text("\n".join(note_lines), encoding="utf-8")

    expected_months = 156
    month_names = [m.name for m in month_dirs]
    duplicate_month_names = sorted({x for x in month_names if month_names.count(x) > 1})
    malformed_month_names = [m for m in month_names if not MONTH_RE.match(m)]

    missing_required_main = [
        r["batch_id"] for r in manifest_rows if r["corpus_type"] == "main_monthly" and r["status"] == "needs_manual_check"
    ]
    missing_shocks = sorted(expected_shocks - present_shocks)

    empty_registry_rows = [
        f"{r['corpus_name']}::{r['batch_id']}"
        for r in manifest_rows
        if str(r.get("article_registry_path", "")).strip()
        and len(read_csv_rows(project_root / r["article_registry_path"])) == 0
    ]

    checks = [
        "Retrieval Freeze Checks",
        f"freeze_date={freeze_date}",
        "",
        f"1) Are all 156 monthly batches present? {'YES' if len(month_dirs) == expected_months else 'NO'} (found={len(month_dirs)})",
        f"2) Are all expected shock corpora present? {'YES' if not missing_shocks else 'NO'} (missing={','.join(missing_shocks) if missing_shocks else 'none'})",
        f"3) Are any monthly folders missing required outputs? {'none' if not missing_required_main else ', '.join(missing_required_main)}",
        f"4) Are there duplicate month folders? {'none' if not duplicate_month_names else ', '.join(duplicate_month_names)}",
        f"5) Are there naming inconsistencies? {'none' if not malformed_month_names else ', '.join(malformed_month_names)}",
        f"6) Any obvious broken paths / empty registries? {'none' if not empty_registry_rows else ', '.join(empty_registry_rows)}",
        "",
        "Warnings (non-blocking):",
    ]

    if warnings:
        checks.extend([f"- {w}" for w in warnings])
    else:
        checks.append("- none")

    checks.append("")
    checks.append("Items requiring manual check (blockers):")
    if blockers:
        checks.extend([f"- {b}" for b in blockers])
    else:
        checks.append("- none")

    (freeze_dir / "retrieval_freeze_checks.txt").write_text("\n".join(checks), encoding="utf-8")

    print(f"Wrote: {freeze_dir / 'retrieval_freeze_note.txt'}")
    print(f"Wrote: {freeze_dir / 'retrieval_freeze_manifest.csv'}")
    print(f"Wrote: {freeze_dir / 'retrieval_freeze_checks.txt'}")
    print(f"main_batches_found={len(month_dirs)}")
    print(f"warnings={len(warnings)} blockers={len(blockers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
