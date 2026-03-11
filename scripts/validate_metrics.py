"""
Lightweight data validation checks for processed metrics.

Run with:
  python scripts/validate_metrics.py
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed"


def check_percent_bounds(df: pd.DataFrame, col: str, label: str) -> None:
  if col not in df.columns:
    print(f"[SKIP] {label}: column {col} not in dataframe")
    return
  bad = df[(df[col] < 0) | (df[col] > 100)]
  if bad.empty:
    print(f"[OK] {label}: all values between 0 and 100")
  else:
    print(f"[WARN] {label}: {len(bad)} rows outside [0,100]")


def main() -> None:
  fb = pd.read_parquet(PROCESSED / "foreign_born_core.parquet")
  check_percent_bounds(fb, "fb_pct", "Foreign-born share %")

  edu = pd.read_parquet(PROCESSED / "education.parquet")
  check_percent_bounds(edu, "bachelors_pct", "Bachelor's degree %")

  own = pd.read_parquet(PROCESSED / "homeownership.parquet")
  check_percent_bounds(own, "homeownership_pct", "Homeownership %")


if __name__ == "__main__":
  main()

