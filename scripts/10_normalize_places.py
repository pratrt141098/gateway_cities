import pandas as pd
from pathlib import Path
from city_config import CITY_FIPS, CITY_TYPE

RAW     = Path("data/raw")
INTERIM = Path("data/interim")
INTERIM.mkdir(exist_ok=True)

FILES = {
    "dp03":   "ACSDP5Y2024.DP03-Data.csv",
    "b05001": "ACSDT5Y2024.B05001-Data.csv",
    "b05002": "ACSDT5Y2024.B05002-Data.csv",
    "b05003": "ACSDT5Y2024.B05003-Data.csv",
    "b05006": "ACSDT5Y2024.B05006-Data.csv",
    "b05010": "ACSDT5Y2024.B05010-Data.csv",
    "b06011": "ACSDT5Y2024.B06011-Data.csv",
    "b15002": "ACSDT5Y2024.B15002-Data.csv",
    "b25003": "ACSDT5Y2024.B25003-Data.csv",
    "s0501":  "ACSST5Y2024.S0501-Data.csv",
}

fips_to_city = {v: k for k, v in CITY_FIPS.items()}
target_fips  = set(CITY_FIPS.values())

for table, fname in FILES.items():
    df = pd.read_csv(RAW / fname, header=0, skiprows=[1], encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.replace('"', '')
    df["GEO_ID"] = df["GEO_ID"].str.strip()
    df = df[df["GEO_ID"].isin(target_fips)].copy()
    margin_cols = [c for c in df.columns if c.endswith("M") and c != "NAME"]
    df = df.drop(columns=margin_cols)
    df["city"]      = df["GEO_ID"].map(fips_to_city)
    df["city_type"] = df["city"].map(CITY_TYPE)
    df["year"]      = 2024
    out = INTERIM / f"{table}.parquet"
    df.to_parquet(out, index=False)
    print(f"✓ {table}: {len(df)} cities → {out}")
    print(f"  cities: {sorted(df['city'].dropna().tolist())}")

print("\nDone. Check data/interim/")
