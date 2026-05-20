from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class CheckResult:
    status: str
    messages: List[str]


def _find_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    manual_dir = project_root / "data" / "polling" / "manual"
    figure_dir = project_root / "figures" / "05a_historical_polling_sanity_check"
    report_path = manual_dir / "historical_manual_polling_sanity_check_report.md"

    poll_csv = manual_dir / "afd_polling_historical_manual_polllevel.csv"
    monthly_csv = manual_dir / "afd_polling_historical_manual_monthly.csv"
    monthly_parquet = manual_dir / "afd_polling_historical_manual_monthly.parquet"

    figure_dir.mkdir(parents=True, exist_ok=True)

    warnings: List[str] = []
    errors: List[str] = []
    lines: List[str] = []
    lines.append("# Historical Manual Polling Sanity Check Report")
    lines.append("")
    lines.append(f"- Validation timestamp: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Poll-level CSV: `{poll_csv}`")
    lines.append(f"- Monthly CSV: `{monthly_csv}`")
    lines.append(f"- Monthly parquet: `{monthly_parquet}`")
    lines.append("")

    if not poll_csv.exists():
        errors.append(f"Missing poll-level file: {poll_csv}")
    if not monthly_csv.exists():
        errors.append(f"Missing monthly csv file: {monthly_csv}")
    if not monthly_parquet.exists():
        warnings.append(f"Monthly parquet file not found: {monthly_parquet}")

    if errors:
        _write_report(report_path, lines, warnings, errors, final_status="FAIL")
        _print_summary(
            status="FAIL",
            poll_rows=0,
            monthly_rows=0,
            coverage="NA",
            cologne_covered=False,
            agg_ok=False,
            report_path=report_path,
        )
        return 1

    poll = pd.read_csv(poll_csv)
    monthly = pd.read_csv(monthly_csv)
    monthly_parquet_ok = False
    if monthly_parquet.exists():
        try:
            _ = pd.read_parquet(monthly_parquet)
            monthly_parquet_ok = True
        except Exception as exc:
            errors.append(f"Monthly parquet is not readable: {exc}")

    if poll.empty:
        errors.append("Poll-level CSV is empty.")
    if monthly.empty:
        errors.append("Monthly CSV is empty.")

    poll_required = {
        "poll_date": ["poll_date"],
        "year_month": ["year_month"],
        "pollster": ["pollster"],
        "afd_pct": ["afd_pct"],
        "source": ["source"],
        "source_url": ["source_url"],
        "series_type": ["series_type"],
        "collection_method": ["collection_method"],
        "notes": ["notes"],
    }
    monthly_required = {
        "year_month": ["year_month", "month"],
        "afd_poll_support_mean": ["afd_poll_support_mean"],
        "afd_poll_support_median": ["afd_poll_support_median"],
        "n_polls": ["n_polls"],
        "n_pollsters": ["n_pollsters"],
    }

    poll_map: Dict[str, str] = {}
    for k, v in poll_required.items():
        found = _find_column(poll, v)
        if found is None:
            errors.append(f"Poll-level missing required column: {k}")
        else:
            poll_map[k] = found

    monthly_map: Dict[str, str] = {}
    for k, v in monthly_required.items():
        found = _find_column(monthly, v)
        if found is None:
            errors.append(f"Monthly missing required column: {k}")
        else:
            monthly_map[k] = found

    if not errors:
        poll["_poll_date"] = pd.to_datetime(poll[poll_map["poll_date"]], errors="coerce")
        if poll["_poll_date"].isna().any():
            errors.append("poll_date has unparseable values.")

        poll["_year_month"] = poll[poll_map["year_month"]].astype(str)
        if not poll["_year_month"].str.match(r"^\d{4}-\d{2}$").all():
            errors.append("year_month has invalid format (expected YYYY-MM).")

        poll["_afd_pct"] = _safe_numeric(poll[poll_map["afd_pct"]])
        if poll["_afd_pct"].isna().any():
            errors.append("afd_pct has non-numeric or missing values.")

        monthly["_afd_mean"] = _safe_numeric(monthly[monthly_map["afd_poll_support_mean"]])
        monthly["_afd_median"] = _safe_numeric(monthly[monthly_map["afd_poll_support_median"]])
        monthly["_n_polls"] = _safe_numeric(monthly[monthly_map["n_polls"]])
        monthly["_n_pollsters"] = _safe_numeric(monthly[monthly_map["n_pollsters"]])

        for c in ["_afd_mean", "_afd_median", "_n_polls", "_n_pollsters"]:
            if monthly[c].isna().any():
                errors.append(f"Monthly column has non-numeric/missing values: {c}")
        if (monthly["_n_polls"] <= 0).any():
            errors.append("Monthly n_polls has non-positive values.")

    cologne_covered = False
    missing_full_months: List[str] = []
    if not errors:
        poll_start = poll["_poll_date"].min()
        poll_end = poll["_poll_date"].max()

        monthly["_month_dt"] = pd.to_datetime(
            monthly[monthly_map["year_month"]].astype(str).str[:7] + "-01",
            errors="coerce",
        )
        if monthly["_month_dt"].isna().any():
            errors.append("Monthly year_month could not be parsed to month_dt.")
        else:
            month_dup_count = int(monthly[monthly_map["year_month"]].duplicated().sum())
            if month_dup_count > 0:
                errors.append(f"Monthly file has duplicate months: {month_dup_count}")

            dup_exact = int(
                poll.duplicated(
                    subset=[
                        poll_map["poll_date"],
                        poll_map["pollster"],
                        poll_map["afd_pct"],
                        poll_map["source_url"],
                    ]
                ).sum()
            )
            if dup_exact > 0:
                warnings.append(f"Found duplicate poll-level exact rows: {dup_exact}")

            expected_cologne = pd.period_range("2015-07", "2016-06", freq="M")
            actual_months = pd.PeriodIndex(monthly["_month_dt"].dt.to_period("M").unique(), freq="M")
            missing_cologne = expected_cologne.difference(actual_months)
            cologne_covered = len(missing_cologne) == 0

            expected_full = pd.period_range("2013-09", "2016-12", freq="M")
            missing_full = expected_full.difference(actual_months)
            missing_full_months = [m.strftime("%Y-%m") for m in missing_full]
            if missing_full_months:
                warnings.append(
                    "Missing months in expected full historical range 2013-09..2016-12: "
                    + ", ".join(missing_full_months)
                )

    pollster_counts = pd.Series(dtype=int)
    unexpected_pollsters: List[str] = []
    if not errors:
        pollster_counts = poll[poll_map["pollster"]].value_counts(dropna=False)
        expected_pollsters = {"Politbarometer", "Infratest dimap", "GMS"}
        seen_pollsters = set(poll[poll_map["pollster"]].astype(str).unique().tolist())
        missing_expected = sorted(expected_pollsters.difference(seen_pollsters))
        unexpected_pollsters = sorted(seen_pollsters.difference(expected_pollsters))
        if missing_expected:
            warnings.append("Missing expected pollsters: " + ", ".join(missing_expected))
        if unexpected_pollsters:
            warnings.append("Unexpected pollster labels: " + ", ".join(unexpected_pollsters))

    plausible_ok = True
    poll_stats = {}
    monthly_stats = {}
    if not errors:
        poll_stats = {
            "min": float(poll["_afd_pct"].min()),
            "max": float(poll["_afd_pct"].max()),
            "mean": float(poll["_afd_pct"].mean()),
            "median": float(poll["_afd_pct"].median()),
        }
        monthly_stats = {
            "min": float(monthly["_afd_mean"].min()),
            "max": float(monthly["_afd_mean"].max()),
            "mean": float(monthly["_afd_mean"].mean()),
            "median": float(monthly["_afd_mean"].median()),
        }
        if (poll["_afd_pct"] < 0).any() or (poll["_afd_pct"] > 30).any():
            plausible_ok = False
            warnings.append("Found afd_pct values outside plausible range [0, 30].")

    agg_ok = True
    agg_diff_rows = pd.DataFrame()
    if not errors:
        poll_tmp = poll.copy()
        poll_tmp["_year_month"] = poll_tmp["_poll_date"].dt.strftime("%Y-%m")
        recomputed = (
            poll_tmp.groupby("_year_month", as_index=False)
            .agg(
                afd_poll_support_mean=("_afd_pct", "mean"),
                afd_poll_support_median=("_afd_pct", "median"),
                n_polls=("_afd_pct", "size"),
                n_pollsters=(poll_map["pollster"], "nunique"),
            )
            .rename(columns={"_year_month": "year_month"})
        )
        monthly_cmp = monthly.rename(columns={monthly_map["year_month"]: "year_month"}).copy()
        monthly_cmp["year_month"] = monthly_cmp["year_month"].astype(str).str[:7]

        merged = monthly_cmp.merge(
            recomputed,
            on="year_month",
            how="outer",
            suffixes=("_file", "_recomputed"),
        )
        tol = 1e-9
        cond_mean = (
            merged["afd_poll_support_mean_file"].sub(merged["afd_poll_support_mean_recomputed"]).abs() <= tol
        )
        cond_median = (
            merged["afd_poll_support_median_file"].sub(merged["afd_poll_support_median_recomputed"]).abs() <= tol
        )
        cond_n_polls = merged["n_polls_file"] == merged["n_polls_recomputed"]
        cond_n_pollsters = merged["n_pollsters_file"] == merged["n_pollsters_recomputed"]

        ok_mask = cond_mean & cond_median & cond_n_polls & cond_n_pollsters
        agg_diff_rows = merged.loc[~ok_mask].copy()
        if len(agg_diff_rows) > 0:
            agg_ok = False
            warnings.append(f"Aggregation consistency differences found in {len(agg_diff_rows)} months.")

    fig_path = figure_dir / "afd_polling_historical_manual_monthly.png"
    if not errors:
        fig_df = monthly.copy()
        fig_df = fig_df.sort_values("_month_dt")
        plt.figure(figsize=(10, 4.5))
        plt.plot(fig_df["_month_dt"], fig_df["_afd_mean"], marker="o", linewidth=1.8, color="#1f4e79")
        plt.axvline(pd.Timestamp("2016-01-01"), color="#b22222", linestyle="--", linewidth=1.2, label="Cologne (2016-01)")
        plt.title("Historical Manual AfD Polling Monthly Mean (2013-09 to 2016-12)")
        plt.xlabel("Month")
        plt.ylabel("AfD support mean (%)")
        plt.grid(alpha=0.25)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=150)
        plt.close()

    if not errors:
        poll_start = poll["_poll_date"].min()
        poll_end = poll["_poll_date"].max()
        month_start = monthly["_month_dt"].min()
        month_end = monthly["_month_dt"].max()

        lines.append("## Row Counts")
        lines.append(f"- Poll-level rows: {len(poll)}")
        lines.append(f"- Monthly rows: {len(monthly)}")
        lines.append("")
        lines.append("## Coverage")
        lines.append(f"- Poll-level date range: {poll_start.date()} to {poll_end.date()}")
        lines.append(f"- Monthly coverage range: {month_start.strftime('%Y-%m')} to {month_end.strftime('%Y-%m')}")
        lines.append(f"- Missing months in full expected range (2013-09..2016-12): {missing_full_months if missing_full_months else 'none'}")
        lines.append(f"- Cologne target window 2015-07..2016-06 fully covered: {'yes' if cologne_covered else 'no'}")
        lines.append("")
        lines.append("## Pollsters")
        for k, v in pollster_counts.items():
            lines.append(f"- {k}: {int(v)}")
        lines.append(f"- Unexpected pollster labels: {unexpected_pollsters if unexpected_pollsters else 'none'}")
        lines.append("")
        lines.append("## Value Ranges")
        lines.append(
            f"- Poll-level afd_pct: min={poll_stats['min']:.3f}, max={poll_stats['max']:.3f}, "
            f"mean={poll_stats['mean']:.3f}, median={poll_stats['median']:.3f}"
        )
        lines.append(
            f"- Monthly afd_poll_support_mean: min={monthly_stats['min']:.3f}, max={monthly_stats['max']:.3f}, "
            f"mean={monthly_stats['mean']:.3f}, median={monthly_stats['median']:.3f}"
        )
        lines.append(f"- Plausible range [0,30] check: {'pass' if plausible_ok else 'warning'}")
        lines.append("")
        lines.append("## Duplicate Check")
        dup_exact = int(
            poll.duplicated(
                subset=[
                    poll_map["poll_date"],
                    poll_map["pollster"],
                    poll_map["afd_pct"],
                    poll_map["source_url"],
                ]
            ).sum()
        )
        lines.append(f"- Exact duplicate count (poll_date + pollster + afd_pct + source_url): {dup_exact}")
        lines.append("")
        lines.append("## Aggregation Consistency")
        lines.append(f"- Result: {'passed' if agg_ok else 'differences found'}")
        if not agg_ok:
            lines.append("")
            lines.append("Months with differences:")
            lines.append("")
            lines.append(agg_diff_rows.to_markdown(index=False))
        lines.append("")
        lines.append("## Monthly Snapshot")
        lines.append("")
        monthly_view_cols = [c for c in monthly.columns if not c.startswith("_")]
        monthly_view = monthly[monthly_view_cols].copy()

        lines.append("First 10 monthly rows:")
        lines.append("")
        lines.append(monthly_view.sort_values("month_dt").head(10).to_markdown(index=False))
        lines.append("")
        lines.append("Last 10 monthly rows:")
        lines.append("")
        lines.append(monthly_view.sort_values("month_dt").tail(10).to_markdown(index=False))
        lines.append("")
        lines.append("Cologne-window monthly rows (2015-07..2016-06):")
        lines.append("")
        cologne_rows = monthly_view[
            (monthly["_month_dt"] >= pd.Timestamp("2015-07-01"))
            & (monthly["_month_dt"] <= pd.Timestamp("2016-06-30"))
        ].sort_values("month_dt")
        lines.append(cologne_rows.to_markdown(index=False))
        lines.append("")
        lines.append("## Output Artifacts")
        lines.append(f"- Figure: `{fig_path}`")

    if errors:
        status = "FAIL"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    _write_report(report_path, lines, warnings, errors, final_status=status)

    coverage = "NA"
    poll_rows = len(poll) if not poll.empty else 0
    monthly_rows = len(monthly) if not monthly.empty else 0
    if not errors and monthly_rows > 0:
        coverage = f"{monthly['_month_dt'].min().strftime('%Y-%m')} to {monthly['_month_dt'].max().strftime('%Y-%m')}"

    _print_summary(
        status=status,
        poll_rows=poll_rows,
        monthly_rows=monthly_rows,
        coverage=coverage,
        cologne_covered=cologne_covered,
        agg_ok=agg_ok,
        report_path=report_path,
    )
    return 0 if status != "FAIL" else 1


def _write_report(
    path: Path,
    base_lines: List[str],
    warnings: List[str],
    errors: List[str],
    final_status: str,
) -> None:
    lines = list(base_lines)
    lines.append("")
    lines.append("## Warnings")
    if warnings:
        for w in warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Errors")
    if errors:
        for e in errors:
            lines.append(f"- {e}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Final Status")
    lines.append(f"- {final_status}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_summary(
    status: str,
    poll_rows: int,
    monthly_rows: int,
    coverage: str,
    cologne_covered: bool,
    agg_ok: bool,
    report_path: Path,
) -> None:
    print("Historical manual polling sanity check complete.")
    print(f"Status: {status}")
    print(f"Poll-level rows: {poll_rows}")
    print(f"Monthly rows: {monthly_rows}")
    print(f"Coverage: {coverage}")
    print(f"Cologne target window 2015-07 to 2016-06 covered: {'yes' if cologne_covered else 'no'}")
    print(f"Aggregation consistency: {'passed' if agg_ok else 'failed'}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    raise SystemExit(main())
