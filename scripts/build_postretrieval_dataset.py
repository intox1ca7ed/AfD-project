from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd


def copy_if_exists(src: Path, dst: Path) -> tuple[bool, str]:
    if not src.exists():
        return False, f"missing source: {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True, f"copied {src} -> {dst}"


def sync_clean_layer(project_root: Path) -> list[str]:
    msgs: list[str] = []
    data_root = project_root / "data"
    corpus_dir = data_root / "corpus"
    indicators_dir = data_root / "indicators"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    indicators_dir.mkdir(parents=True, exist_ok=True)

    mappings = [
        (project_root / "archive_pipeline" / "master_tables" / "master_articles_all.parquet", corpus_dir / "master_articles.parquet"),
        (project_root / "archive_pipeline" / "monthly_tables" / "monthly_summary_main_corpus.parquet", corpus_dir / "monthly_summary.parquet"),
        (project_root / "archive_pipeline" / "monthly_tables" / "monthly_summary_main_corpus.csv", corpus_dir / "monthly_summary.csv"),
        (project_root / "archive_pipeline" / "descriptive_package" / "descriptive_statistics_report.md", project_root / "docs" / "descriptive_statistics_report.md"),
        (project_root / "archive_pipeline" / "freeze" / "retrieval_freeze_manifest.csv", project_root / "archive_pipeline" / "freeze" / "retrieval_freeze_manifest.csv"),
    ]
    for src, dst in mappings:
        ok, msg = copy_if_exists(src, dst) if src != dst else (src.exists(), f"verified {src}")
        msgs.append(msg)

    src_master_csv = project_root / "archive_pipeline" / "master_tables" / "master_articles_all.csv"
    out_light_csv = corpus_dir / "master_articles_light.csv"
    if src_master_csv.exists():
        df = pd.read_csv(src_master_csv, encoding="utf-8-sig", low_memory=False)
        if "text_body" in df.columns:
            df = df.drop(columns=["text_body"])
        out_light_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_light_csv, index=False, encoding="utf-8-sig")
        msgs.append(f"wrote light csv {out_light_csv} rows={len(df)} cols={len(df.columns)}")
    else:
        msgs.append(f"missing source: {src_master_csv}")

    src_desc_tables = project_root / "archive_pipeline" / "descriptive_package" / "tables"
    dst_desc_tables = project_root / "data" / "descriptive_tables"
    if src_desc_tables.exists():
        dst_desc_tables.mkdir(parents=True, exist_ok=True)
        for f in src_desc_tables.glob("*.csv"):
            shutil.copy2(f, dst_desc_tables / f.name)
        msgs.append(f"synced descriptive tables to {dst_desc_tables}")
    else:
        msgs.append(f"missing source dir: {src_desc_tables}")

    src_figs = project_root / "archive_pipeline" / "descriptive_package" / "figures"
    dst_figs = project_root / "figures"
    if src_figs.exists():
        dst_figs.mkdir(parents=True, exist_ok=True)
        for f in src_figs.glob("*.png"):
            shutil.copy2(f, dst_figs / f.name)
        msgs.append(f"synced figures to {dst_figs}")
    else:
        msgs.append(f"missing source dir: {src_figs}")

    return msgs


def run_archived_pipeline(project_root: Path) -> tuple[int, str]:
    script = project_root / "archive_pipeline" / "workflow" / "run_pipeline.py"
    if not script.exists():
        return 1, f"missing archived pipeline script: {script}"
    proc = subprocess.run(
        ["python", str(script)],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    msg = f"return_code={proc.returncode}\nstdout:\n{out}\nstderr:\n{err}"
    return proc.returncode, msg


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild or refresh clean post-retrieval research layer.")
    parser.add_argument(
        "--run-archived-pipeline",
        action="store_true",
        help="Run archived technical pipeline first before refreshing clean outputs.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    logs_dir = project_root / "archive_pipeline" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"build_postretrieval_dataset_{run_ts}.log"

    lines = [
        "Post-Retrieval Dataset Builder",
        f"timestamp={datetime.now().isoformat(timespec='seconds')}",
        f"project_root={project_root}",
        f"run_archived_pipeline={args.run_archived_pipeline}",
        "",
    ]

    if args.run_archived_pipeline:
        rc, msg = run_archived_pipeline(project_root)
        lines.append("[archived_pipeline_run]")
        lines.append(msg)
        lines.append("")
        if rc != 0:
            lines.append("status=failed")
            log_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"Wrote log: {log_path}")
            return rc

    lines.append("[sync_clean_layer]")
    for m in sync_clean_layer(project_root):
        lines.append(m)

    try:
        m = pd.read_parquet(project_root / "data" / "corpus" / "master_articles.parquet")
        mm = pd.read_parquet(project_root / "data" / "corpus" / "monthly_summary.parquet")
        lines.append("")
        lines.append(f"master_rows={len(m)}")
        lines.append(f"monthly_rows={len(mm)}")
    except Exception as exc:
        lines.append(f"validation_warning={exc}")

    lines.append("")
    lines.append("status=success")
    log_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote log: {log_path}")
    print("Refreshed clean layer in data/, figures/, docs/ from archive_pipeline outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
