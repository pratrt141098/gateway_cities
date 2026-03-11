import pandas as pd
from pathlib import Path
from functools import lru_cache

PROCESSED = Path(__file__).parent.parent.parent / "data" / "processed"

GATEWAY_CITIES = {
    "Springfield", "Worcester", "Lowell", "Brockton", "New Bedford",
    "Lawrence", "Lynn", "Fall River", "Quincy", "Haverhill",
    "Malden", "Medford", "Chicopee", "Fitchburg", "Holyoke",
    "Leominster", "Chelsea", "Everett", "Revere", "Methuen",
    "Taunton", "Barnstable", "Pittsfield", "Attleboro", "Peabody", "Salem",
}

@lru_cache(maxsize=None)
def _load(filename: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / filename)

def get_cities_master():
    return _load("cities_master.parquet").to_dict(orient="records")

def get_foreign_born(city: str = None, city_type: str = None, gateway_only: bool = False):
    df = _load("foreign_born_core.parquet")
    # De-dupe repeated rows (can occur if interim pipeline is re-run and appended)
    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if city_type:
        df = df[df["city_type"] == city_type]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]
    return df.to_dict(orient="records")

def get_country_of_origin(city: str = None):
    df = _load("country_of_origin.parquet")
    subset = [c for c in ["city", "year", "country"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    return df.to_dict(orient="records")

def get_education(city: str = None, gateway_only: bool = False):
    df = _load("education.parquet")
    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]
    return df.to_dict(orient="records")

def get_homeownership(city: str = None, gateway_only: bool = False):
    df = _load("homeownership.parquet")
    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]
    return df.to_dict(orient="records")

def get_employment_income(city: str = None, gateway_only: bool = False):
    df = _load("employment_income.parquet")
    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]
    return df.to_dict(orient="records")

def get_poverty(city: str = None, gateway_only: bool = False):
    # Use S0501 "Selected Characteristics of the Native and Foreign-Born Populations"
    # for nativity poverty rates.
    #
    # Note: In our interim `s0501.parquet`, the "_104E" fields for "Below 100 percent
    # of the poverty level" are stored as *percent values* (0–100), not raw counts.
    # So we use them directly as poverty percentages.
    interim_path = Path(__file__).parent.parent.parent / "data" / "interim" / "s0501.parquet"
    if interim_path.exists():
        df = pd.read_parquet(interim_path)
    else:
        # Back-compat: fall back to previous processed file if interim not available.
        df = _load("poverty_by_nativity.parquet")

    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]

    if "S0501_C03_104E" in df.columns:
        df = df.copy()
        df["fb_poverty_pct"] = pd.to_numeric(df["S0501_C03_104E"], errors="coerce")
    if "S0501_C02_104E" in df.columns:
        df = df.copy()
        df["native_poverty_pct"] = pd.to_numeric(df["S0501_C02_104E"], errors="coerce")
    return df.to_dict(orient="records")

def get_median_income(city: str = None, gateway_only: bool = False):
    df = _load("median_income.parquet")
    subset = [c for c in ["city", "year"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    if city:
        df = df[df["city"] == city]
    if gateway_only:
        df = df[df["city"].isin(GATEWAY_CITIES)]
    return df.to_dict(orient="records")

def get_map_stats():
    df = _load("foreign_born_core.parquet")
    cols = [c for c in ["city", "geoid", "fb_pct", "fb_count", "total_pop", "city_type"] if c in df.columns]
    return df[cols].drop_duplicates(subset=["city"]).to_dict(orient="records")