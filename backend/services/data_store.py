import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

PROCESSED = Path(__file__).parent.parent.parent / "data" / "processed"

BAD_VALUES = {-888888888, -666666666, -999999999}


def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(pd.notnull(df), other=None)


@lru_cache(maxsize=None)
def _load(filename: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / filename)


def _to_records(df: pd.DataFrame) -> list:
    return _sanitize(df).to_dict(orient="records")


def get_cities_master():
    df = _load("cities_master.parquet")
    df = df.sort_values("year").drop_duplicates(subset=["city"], keep="last")
    return _to_records(df)


def get_foreign_born(city: str = None, city_type: str = None):
    df = _load("foreign_born_core.parquet")
    if city:
        df = df[df["city"] == city]
    if city_type:
        df = df[df["city_type"] == city_type]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)

REGION_LABELS = {
    # Continents
    "Africa:", "Americas:", "Asia:", "Europe:", "Oceania:",
    "Latin America:", "South America:",
    # Subregions with colon
    "Caribbean:", "Central America:", "Northern America:",
    "Eastern Africa:", "Eastern Asia:", "Eastern Europe:",
    "Northern Africa:", "Northern Europe:", "Southern Africa:",
    "Southern Europe:", "Western Africa:", "Western Asia:", "Western Europe:",
    "South Central Asia:", "South Eastern Asia:", "Australia and New Zealand Subregion:",
    "Middle Africa:",
    # n.e.c. entries
    "Africa, n.e.c.", "Asia, n.e.c.", "Europe, n.e.c.", "Oceania, n.e.c.",
    # "Other ..." entries
    "Other Caribbean", "Other Central America", "Other Eastern Africa",
    "Other Eastern Asia", "Other Eastern Europe", "Other Middle Africa",
    "Other Northern Africa", "Other Northern America", "Other Northern Europe",
    "Other South America", "Other South Central Asia", "Other South Eastern Asia",
    "Other Southern Africa", "Other Southern Europe", "Other Western Africa",
    "Other Western Asia", "Other Western Europe",
    "Other Australian and New Zealand Subregion",
}


def get_country_of_origin(city: str = None):
    df = _load("country_of_origin.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    df = df[~df["country"].isin(REGION_LABELS)]
    cols = [c for c in ["city", "city_type", "country", "estimate"] if c in df.columns]
    return _to_records(df[cols])


def get_education(city: str = None):
    df = _load("education.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)


def get_homeownership(city: str = None):
    df = _load("homeownership.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)


def get_employment_income(city: str = None):
    df = _load("employment_income.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)


def get_poverty(city: str = None):
    df = _load("poverty_by_nativity.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)


def get_median_income(city: str = None):
    df = _load("median_income.parquet")
    if city:
        df = df[df["city"] == city]
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    return _to_records(df)


def get_map_stats():
    df = _load("foreign_born_core.parquet")
    if "year" in df.columns:
        df = df[df["year"] == df["year"].max()]
    cols = [c for c in ["city", "city_type", "fb_pct", "foreign_born", "total_pop"] if c in df.columns]
    return _to_records(df[cols].drop_duplicates(subset=["city"]))


def get_time_series(city: str = None, metric: str = "fb_pct"):
    METRIC_MAP = {
        "fb_pct":            ("foreign_born_core.parquet",    "fb_pct"),
        "unemployment_rate": ("employment_income.parquet",    "unemployment_rate"),
        "median_income":     ("employment_income.parquet",    "median_household_income"),
        "poverty_rate":      ("poverty_by_nativity.parquet",  "fb_poverty_pct"),
        "bachelors_pct":     ("education.parquet",            "bachelors_pct"),
        "homeownership_pct": ("homeownership.parquet",        "homeownership_pct"),
        "fb_income":         ("median_income.parquet",        "median_income_foreign_born"),
    }

    if metric not in METRIC_MAP:
        return []

    filename, col = METRIC_MAP[metric]
    df = _load(filename)

    if city:
        df = df[df["city"] == city]

    keep = [c for c in ["city", "city_type", "year", col] if c in df.columns]
    df = df[keep].copy()

    df[col] = pd.to_numeric(df[col], errors="coerce").replace(list(BAD_VALUES), np.nan)
    df = df.dropna(subset=[col])
    df = df.rename(columns={col: "value"})
    df["metric"] = metric

    return _to_records(df.sort_values(["city", "year"]))

