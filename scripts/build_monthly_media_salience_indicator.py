from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_NEXIS_COLUMNS = ["month_id", "volume", "raw_article_count"]


def expected_month_ids(start: str = "2013-01", end: str = "2025-12") -> list[str]:
    periods = pd.period_range(start=start, end=end, freq="M")
    return [str(p) for p in periods]


def validate_nexis_volume(df: pd.DataFrame) -> None:
    missing_cols = [c for c in REQUIRED_NEXIS_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"monthly_nexis_volume.csv missing required columns: {missing_cols}")

    if len(df) != 156:
        raise ValueError(f"monthly_nexis_volume.csv must have exactly 156 rows; found {len(df)}")

    if df["month_id"].duplicated().any():
        dupes = df.loc[df["month_id"].duplicated(keep=False), "month_id"].tolist()
        raise ValueError(f"Duplicate month_id values in monthly_nexis_volume.csv: {sorted(set(dupes))}")

    expected = set(expected_month_ids())
    found = set(df["month_id"].astype(str))
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    if missing or extra:
        raise ValueError(
            "monthly_nexis_volume.csv month coverage mismatch. "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    for col in ["volume", "raw_article_count"]:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.isna().any():
            bad_months = df.loc[numeric.isna(), "month_id"].tolist()
            raise ValueError(f"Column '{col}' has non-numeric or missing values for months: {bad_months}")


def load_monthly_summary(corpus_dir: Path) -> pd.DataFrame:
    parquet_path = corpus_dir / "monthly_summary.parquet"
    csv_path = corpus_dir / "monthly_summary.csv"
    if parquet_path.exists():
        monthly = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        monthly = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError("Missing monthly summary: expected data/corpus/monthly_summary.parquet or .csv")
    if "month_id" not in monthly.columns:
        raise ValueError("monthly_summary is missing required 'month_id' column")
    return monthly


def build_indicator(monthly: pd.DataFrame, nexis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = monthly.copy()
    nexis = nexis.copy()

    nexis["volume"] = pd.to_numeric(nexis["volume"], errors="coerce")
    nexis["raw_article_count"] = pd.to_numeric(nexis["raw_article_count"], errors="coerce")
    nexis = nexis.rename(
        columns={
            "volume": "nexis_total_results",
            "raw_article_count": "raw_article_count_manual",
        }
    )

    if "raw_article_count" in monthly.columns:
        monthly = monthly.rename(columns={"raw_article_count": "raw_article_count_monthly"})
    else:
        monthly["raw_article_count_monthly"] = np.nan

    merged = monthly.merge(nexis, on="month_id", how="left", validate="one_to_one")
    merged["month_dt"] = pd.to_datetime(merged["month_id"] + "-01", errors="coerce")

    merged["raw_article_count_mismatch"] = (
        merged["raw_article_count_monthly"].notna()
        & merged["raw_article_count_manual"].notna()
        & (merged["raw_article_count_monthly"] != merged["raw_article_count_manual"])
    )

    merged["raw_article_count"] = merged["raw_article_count_manual"].where(
        merged["raw_article_count_manual"].notna(), merged["raw_article_count_monthly"]
    )

    merged["media_salience_volume_raw"] = merged["nexis_total_results"]
    merged["media_salience_volume_log1p"] = np.log1p(merged["nexis_total_results"])

    sal_mean = merged["nexis_total_results"].mean()
    sal_std = merged["nexis_total_results"].std(ddof=0)
    merged["media_salience_volume_z"] = (
        (merged["nexis_total_results"] - sal_mean) / sal_std
        if pd.notna(sal_std) and sal_std != 0
        else np.nan
    )

    merged["cleaned_sample_size"] = pd.to_numeric(merged["kept_article_count"], errors="coerce")
    merged["cleaned_sample_log1p"] = np.log1p(merged["cleaned_sample_size"])
    clean_mean = merged["cleaned_sample_size"].mean()
    clean_std = merged["cleaned_sample_size"].std(ddof=0)
    merged["cleaned_sample_z"] = (
        (merged["cleaned_sample_size"] - clean_mean) / clean_std
        if pd.notna(clean_std) and clean_std != 0
        else np.nan
    )

    valid_den = merged["nexis_total_results"].notna() & (merged["nexis_total_results"] > 0)
    merged["download_fraction"] = np.where(
        valid_den, merged["raw_article_count"] / merged["nexis_total_results"], np.nan
    )
    merged["cleaned_sample_fraction"] = np.where(
        valid_den, merged["kept_article_count"] / merged["nexis_total_results"], np.nan
    )

    merged["retrieval_mismatch_flag"] = merged["raw_article_count"] > merged["nexis_total_results"]
    merged["high_download_sample_flag"] = merged["raw_article_count"] > 50

    merged["month"] = merged["month_id"]
    merged["year_month"] = merged["month_id"]
    merged["year"] = merged["month_dt"].dt.year
    merged["month_num"] = merged["month_dt"].dt.month

    indicator_cols = [
        "month",
        "year_month",
        "year",
        "month_num",
        "nexis_total_results",
        "media_salience_volume_raw",
        "media_salience_volume_log1p",
        "media_salience_volume_z",
        "raw_article_count",
        "download_fraction",
        "retrieval_mismatch_flag",
        "high_download_sample_flag",
        "kept_article_count",
        "cleaned_sample_size",
        "cleaned_sample_fraction",
        "cleaned_sample_log1p",
        "cleaned_sample_z",
    ]
    indicator = merged[indicator_cols].sort_values("month").reset_index(drop=True)
    return merged, indicator


def run(data_dir: Path) -> None:
    corpus_dir = data_dir / "corpus"
    indicators_dir = data_dir / "indicators"
    indicators_dir.mkdir(parents=True, exist_ok=True)

    monthly = load_monthly_summary(corpus_dir)
    nexis_path = corpus_dir / "monthly_nexis_volume.csv"
    if not nexis_path.exists():
        raise FileNotFoundError(f"Missing required file: {nexis_path}")
    nexis = pd.read_csv(nexis_path)
    validate_nexis_volume(nexis)

    merged, indicator = build_indicator(monthly, nexis)

    if len(merged) != 156:
        raise ValueError(f"Merged monthly table must have 156 rows; found {len(merged)}")
    if merged["month_id"].duplicated().any():
        raise ValueError("Merged monthly table has duplicate months")
    if merged["nexis_total_results"].isna().any():
        missing = merged.loc[merged["nexis_total_results"].isna(), "month_id"].tolist()
        raise ValueError(f"Missing nexis_total_results after merge: {missing}")

    mismatches = merged.loc[
        merged["raw_article_count_mismatch"],
        ["month_id", "raw_article_count_monthly", "raw_article_count_manual"],
    ].sort_values("month_id")

    out_csv = indicators_dir / "monthly_media_salience_indicator.csv"
    out_parquet = indicators_dir / "monthly_media_salience_indicator.parquet"
    indicator.to_csv(out_csv, index=False, encoding="utf-8-sig")
    indicator.to_parquet(out_parquet, index=False)

    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_parquet}")
    print("z_standardization=population_sd_ddof0")
    print(f"rows={len(indicator)}")
    print(f"nexis_total_results_missing={int(indicator['nexis_total_results'].isna().sum())}")
    print(f"duplicate_month_rows={int(indicator['month'].duplicated().sum())}")
    print(f"raw_article_count_conflicts={len(mismatches)}")
    if not mismatches.empty:
        print("raw_article_count_conflict_rows:")
        print(mismatches.to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build monthly media salience indicators from manual Nexis total monthly results."
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Data directory containing corpus/ and indicators/ subfolders",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    run(data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
