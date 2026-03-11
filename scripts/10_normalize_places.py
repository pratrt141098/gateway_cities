import pandas as pd
from pathlib import Path

RAW     = Path("data/raw")
INTERIM = Path("data/interim")
INTERIM.mkdir(exist_ok=True)

CITY_YEARS = [2020, 2021, 2022, 2023, 2024]

CITY_FIPS = {
    "Attleboro":   "1600000US2502690",
    "Barnstable":  "1600000US2503690",
    "Brockton":    "1600000US2509000",
    "Chelsea":     "1600000US2513205",
    "Chicopee":    "1600000US2513660",
    "Everett":     "1600000US2521990",
    "Fall River":  "1600000US2523000",
    "Fitchburg":   "1600000US2523875",
    "Framingham":  "1600000US2524960",
    "Haverhill":   "1600000US2529405",
    "Holyoke":     "1600000US2530840",
    "Lawrence":    "1600000US2534550",
    "Leominster":  "1600000US2535075",
    "Lowell":      "1600000US2537000",
    "Lynn":        "1600000US2537490",
    "Malden":      "1600000US2537875",
    "Methuen":     "1600000US2540675",
    "New Bedford": "1600000US2545000",
    "Peabody":     "1600000US2552490",
    "Pittsfield":  "1600000US2553960",
    "Quincy":      "1600000US2555745",
    "Revere":      "1600000US2556585",
    "Salem":       "1600000US2559105",
    "Springfield": "1600000US2567000",
    "Taunton":     "1600000US2569170",
    "Westfield":   "1600000US2576030",
    "Worcester":   "1600000US2582000",
    "Somerville":  "1600000US2562535",
    "Weymouth":    "1600000US2578972",
    "Marlborough": "1600000US2538715",
    "Boston":      "1600000US2507000",
    "Cambridge":   "1600000US2511000",
}

CITY_TYPE = {
    name: (
        "benchmark" if name in ["Boston", "Cambridge"]
        else "comparison" if name in ["Somerville", "Weymouth", "Marlborough"]
        else "gateway"
    )
    for name in CITY_FIPS
}

FILES = {
    "dp03":   "ACSDP5Y{year}.DP03-Data.csv",
    "b05001": "ACSDT5Y{year}.B05001-Data.csv",
    "b05002": "ACSDT5Y{year}.B05002-Data.csv",
    "b05003": "ACSDT5Y{year}.B05003-Data.csv",
    "b05006": "ACSDT5Y{year}.B05006-Data.csv",
    "b05010": "ACSDT5Y{year}.B05010-Data.csv",
    "b06011": "ACSDT5Y{year}.B06011-Data.csv",
    "b15002": "ACSDT5Y{year}.B15002-Data.csv",
    "b25003": "ACSDT5Y{year}.B25003-Data.csv",
    "s0501":  "ACSST5Y{year}.S0501-Data.csv",
}

fips_to_city = {v: k for k, v in CITY_FIPS.items()}
target_fips  = set(CITY_FIPS.values())

for year in CITY_YEARS:
    print(f"\n=== Processing ACS 5-year data for {year} ===")
    for table, template in FILES.items():
        fname = template.format(year=year)
        csv_path = RAW / fname
        if not csv_path.exists():
            print(f"  ⚠ Skipping {table} for {year}: {csv_path} not found")
            continue
        df = pd.read_csv(csv_path, header=0, skiprows=[1], encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.replace('"', '')
        df["GEO_ID"] = df["GEO_ID"].str.strip()
        df = df[df["GEO_ID"].isin(target_fips)].copy()
        margin_cols = [c for c in df.columns if c.endswith("M") and c != "NAME"]
        df = df.drop(columns=margin_cols)
        df["city"]      = df["GEO_ID"].map(fips_to_city)
        df["city_type"] = df["city"].map(CITY_TYPE)
        df["year"]      = year

        out = INTERIM / f"{table}.parquet"
        if out.exists():
            existing = pd.read_parquet(out)
            df = pd.concat([existing, df], ignore_index=True)

        df.to_parquet(out, index=False)
        print(f"  ✓ {table} {year}: {len(df)} rows → {out}")
        print(f"    cities: {sorted(df['city'].dropna().unique().tolist())}")

print("\nDone. Check data/interim/ for multi-year tables.")
