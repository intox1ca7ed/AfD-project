from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def exists_all(root: Path, rel_paths: list[str]) -> tuple[bool, list[str]]:
    missing = []
    for rel in rel_paths:
        if not (root / rel).exists():
            missing.append(rel)
    return (len(missing) == 0, missing)


def append_line(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "workflow" / "pipeline_config.json"
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    steps = config.get("steps", [])
    py_cmd = config.get("python_executable", "python")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log = logs_dir / f"pipeline_run_{ts}.log"
    latest_log = logs_dir / "pipeline_latest.log"
    summary_csv = logs_dir / "pipeline_runs_summary.csv"

    append_line(run_log, "Pipeline Run Log")
    append_line(run_log, f"run_timestamp={now_iso()}")
    append_line(run_log, f"project_root={project_root}")
    append_line(run_log, f"config={config_path}")
    append_line(run_log, "")

    results = []
    overall_status = "success"

    for idx, step in enumerate(steps, start=1):
        name = step["name"]
        script_rel = step["script"]
        inputs = step.get("inputs", [])
        outputs = step.get("outputs", [])

        script_path = project_root / script_rel
        step_start = time.time()
        step_start_iso = now_iso()

        append_line(run_log, f"[{idx}/{len(steps)}] step={name}")
        append_line(run_log, f"start={step_start_iso}")
        append_line(run_log, f"script={script_rel}")
        append_line(run_log, f"inputs={'; '.join(inputs)}")
        append_line(run_log, f"expected_outputs={'; '.join(outputs)}")

        if not script_path.exists():
            status = "failed_missing_script"
            append_line(run_log, f"status={status}")
            append_line(run_log, "")
            results.append((name, status, 0.0, "script_not_found", ""))
            overall_status = "failed"
            break

        cmd = [py_cmd, str(script_path)]
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        duration = round(time.time() - step_start, 3)
        step_end_iso = now_iso()

        append_line(run_log, f"end={step_end_iso}")
        append_line(run_log, f"duration_seconds={duration}")
        append_line(run_log, f"return_code={proc.returncode}")

        if proc.stdout.strip():
            append_line(run_log, "stdout_begin")
            append_line(run_log, proc.stdout.rstrip())
            append_line(run_log, "stdout_end")

        if proc.stderr.strip():
            append_line(run_log, "stderr_begin")
            append_line(run_log, proc.stderr.rstrip())
            append_line(run_log, "stderr_end")

        output_ok, missing_outputs = exists_all(project_root, outputs)

        if proc.returncode != 0:
            status = "failed_step_error"
            overall_status = "failed"
        elif not output_ok:
            status = "warning_missing_outputs"
            if overall_status != "failed":
                overall_status = "warning"
        else:
            status = "success"

        append_line(run_log, f"status={status}")
        if missing_outputs:
            append_line(run_log, f"missing_outputs={'; '.join(missing_outputs)}")
        append_line(run_log, "")

        results.append((name, status, duration, str(proc.returncode), ";".join(missing_outputs)))

        if status == "failed_step_error":
            break

    append_line(run_log, f"pipeline_status={overall_status}")
    append_line(run_log, f"pipeline_end_timestamp={now_iso()}")

    latest_log.write_text(run_log.read_text(encoding="utf-8"), encoding="utf-8")

    header_needed = not summary_csv.exists()
    with summary_csv.open("a", encoding="utf-8", newline="") as f:
        if header_needed:
            f.write("run_timestamp,pipeline_status,step_name,step_status,duration_seconds,return_code,missing_outputs\n")
        for step_name, step_status, duration, return_code, missing in results:
            f.write(f"{ts},{overall_status},{step_name},{step_status},{duration},{return_code},{missing}\n")

    print(f"Wrote: {run_log}")
    print(f"Wrote: {latest_log}")
    print(f"Wrote: {summary_csv}")
    print(f"pipeline_status={overall_status}")
    return 0 if overall_status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
