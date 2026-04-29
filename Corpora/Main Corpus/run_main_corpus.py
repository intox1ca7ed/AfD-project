from __future__ import annotations

import argparse
import csv
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from _protocol.main_corpus_protocol import (
    build_month_paths,
    ensure_month_dirs,
    list_month_pdfs,
    protocol_outputs_exist,
    read_registry_counts,
    run_month_protocol,
)


MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
RUN_LOG_FIELDS = [
    "batch_id",
    "month_folder",
    "archive_found",
    "archive_name",
    "pdf_count",
    "processed",
    "kept_count",
    "dropped_count",
    "review_count",
    "status",
    "error_message",
    "run_timestamp",
]


@dataclass
class RunLogRow:
    batch_id: str
    month_folder: str
    archive_found: str
    archive_name: str
    pdf_count: int
    processed: str
    kept_count: int
    dropped_count: int
    review_count: int
    status: str
    error_message: str
    run_timestamp: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the centralized Main Corpus protocol across month folders."
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Process only specific month(s), e.g. --only 2021-09 (can be repeated or comma-separated).",
    )
    parser.add_argument("--start", help="Start month (inclusive), format YYYY-MM.")
    parser.add_argument("--end", help="End month (inclusive), format YYYY-MM.")
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Re-run months even if protocol outputs already exist.",
    )
    parser.add_argument(
        "--reextract",
        action="store_true",
        help="Re-extract archive PDFs into raw_unarchive before processing.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Explicitly skip months that already have protocol outputs (default behavior).",
    )
    return parser.parse_args()


def parse_only_tokens(tokens: list[str]) -> set[str]:
    selected: set[str] = set()
    for token in tokens:
        for part in token.split(","):
            month = part.strip()
            if not month:
                continue
            if not MONTH_RE.match(month):
                raise ValueError(f"Invalid --only month '{month}', expected YYYY-MM.")
            selected.add(month)
    return selected


def validate_month_label(label: str | None, flag_name: str) -> str | None:
    if label is None:
        return None
    if not MONTH_RE.match(label):
        raise ValueError(f"Invalid {flag_name} value '{label}', expected YYYY-MM.")
    return label


def discover_month_dirs(main_corpus_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in main_corpus_dir.iterdir()
        if path.is_dir() and MONTH_RE.match(path.name)
    )


def filter_month_dirs(
    month_dirs: list[Path],
    selected_months: set[str],
    start: str | None,
    end: str | None,
) -> list[Path]:
    filtered = []
    for month_dir in month_dirs:
        month = month_dir.name
        if selected_months and month not in selected_months:
            continue
        if start and month < start:
            continue
        if end and month > end:
            continue
        filtered.append(month_dir)
    return filtered


def find_month_archive(month_dir: Path) -> tuple[Path | None, str]:
    archives = sorted(
        path
        for path in month_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".zip"
    )
    if not archives:
        return None, ""
    warning = ""
    if len(archives) > 1:
        warning = f"multiple_archives_found={len(archives)}; using={archives[0].name}"
    return archives[0], warning


def clear_raw_unarchive_for_reextract(raw_dir: Path) -> None:
    for path in sorted(raw_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file() and path.suffix.lower() == ".pdf":
            path.unlink()
        elif path.is_dir():
            try:
                next(path.iterdir())
            except StopIteration:
                path.rmdir()


def extract_archive_if_needed(raw_dir: Path, archive_path: Path, reextract: bool) -> int:
    if reextract:
        clear_raw_unarchive_for_reextract(raw_dir)

    existing = list_month_pdfs(raw_dir)
    if existing and not reextract:
        return len(existing)

    with zipfile.ZipFile(archive_path, "r") as archive:
        archive.extractall(raw_dir)
    return len(list_month_pdfs(raw_dir))


def write_run_log(log_path: Path, rows: list[RunLogRow]) -> None:
    if not rows:
        return

    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_LOG_FIELDS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def effective_skip_existing(args: argparse.Namespace) -> bool:
    if args.rerun and args.skip_existing:
        raise ValueError("--rerun and --skip-existing cannot be used together.")
    if args.reextract and args.skip_existing:
        raise ValueError("--reextract and --skip-existing cannot be used together.")
    if args.rerun or args.reextract:
        return False
    return True


def process_month(
    month_dir: Path,
    skip_existing: bool,
    reextract: bool,
) -> RunLogRow:
    run_timestamp = datetime.now().isoformat(timespec="seconds")
    row = RunLogRow(
        batch_id=month_dir.name,
        month_folder=month_dir.name,
        archive_found="no",
        archive_name="",
        pdf_count=0,
        processed="no",
        kept_count=0,
        dropped_count=0,
        review_count=0,
        status="pending",
        error_message="",
        run_timestamp=run_timestamp,
    )

    try:
        paths = build_month_paths(month_dir)
        ensure_month_dirs(paths)

        archive_path, archive_warning = find_month_archive(month_dir)
        row.archive_found = "yes" if archive_path else "no"
        row.archive_name = archive_path.name if archive_path else ""

        existing_keep, existing_drop, existing_review = read_registry_counts(month_dir)
        if existing_keep or existing_drop or existing_review:
            row.kept_count = existing_keep
            row.dropped_count = existing_drop
            row.review_count = existing_review

        if skip_existing and protocol_outputs_exist(month_dir):
            row.pdf_count = len(list_month_pdfs(paths.raw_unarchive))
            row.status = "skipped_existing"
            row.error_message = archive_warning
            return row

        if archive_path is None:
            row.pdf_count = len(list_month_pdfs(paths.raw_unarchive))
            row.status = "no_archive"
            row.error_message = archive_warning
            return row

        row.pdf_count = extract_archive_if_needed(paths.raw_unarchive, archive_path, reextract=reextract)
        result = run_month_protocol(month_dir, source_archive=archive_path.name)
        row.pdf_count = result.pdf_count
        row.kept_count = result.kept_count
        row.dropped_count = result.dropped_count
        row.review_count = result.review_count
        row.processed = "yes"
        row.status = "success"
        row.error_message = archive_warning
    except Exception as exc:
        row.status = "error"
        row.error_message = str(exc)
    return row


def main() -> int:
    args = parse_args()
    try:
        selected_months = parse_only_tokens(args.only)
        start = validate_month_label(args.start, "--start")
        end = validate_month_label(args.end, "--end")
        if start and end and start > end:
            raise ValueError("--start must be <= --end.")
        skip_existing = effective_skip_existing(args)
    except ValueError as exc:
        raise SystemExit(f"Argument error: {exc}")

    main_corpus_dir = Path(__file__).resolve().parent
    month_dirs = discover_month_dirs(main_corpus_dir)
    target_month_dirs = filter_month_dirs(month_dirs, selected_months, start, end)

    if not target_month_dirs:
        raise SystemExit("No month folders matched the requested filters.")

    run_rows: list[RunLogRow] = []
    total_months = len(target_month_dirs)
    print(f"Starting Main Corpus run for {total_months} month folder(s)...", flush=True)
    for idx, month_dir in enumerate(target_month_dirs, start=1):
        row = process_month(month_dir, skip_existing=skip_existing, reextract=args.reextract)
        run_rows.append(row)
        print(
            f"[{idx}/{total_months}] [{row.month_folder}] status={row.status} processed={row.processed} "
            f"pdf_count={row.pdf_count} keep={row.kept_count} drop={row.dropped_count} review={row.review_count}",
            flush=True,
        )

    log_path = main_corpus_dir / "main_corpus_run_log.csv"
    write_run_log(log_path, run_rows)
    print(f"Wrote run log: {log_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
