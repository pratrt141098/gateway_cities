from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd

from . import data_store


@dataclass
class CityMetricRow:
    city: str
    year: int
    value: float
    city_type: str | None = None


def get_city_trend(city: str) -> List[Dict[str, Any]]:
    """
    Return time series of foreign-born % for a single city.
    Uses the same underlying table as /api/foreign-born.
    """
    df = pd.DataFrame(data_store.get_foreign_born(city=city))
    if "year" not in df.columns:
        return df.to_dict(orient="records")
    return df.sort_values("year").to_dict(orient="records")


def compare_cities(cities: List[str], metric: str = "fb_pct") -> List[Dict[str, Any]]:
    """
    Compare a metric across multiple cities (latest year only if year exists).
    """
    df = pd.DataFrame(data_store.get_foreign_born())
    if cities:
        df = df[df["city"].isin(cities)]
    if "year" in df.columns:
        # keep latest year per city
        df = df.sort_values(["city", "year"]).groupby("city").tail(1)
    cols = [c for c in ["city", "city_type", "year", metric] if c in df.columns]
    return df[cols].dropna(subset=[metric]).sort_values(metric, ascending=False).to_dict(orient="records")


def rank_cities(metric: str = "fb_pct", ascending: bool = False, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Rank cities by a metric (e.g., foreign-born %, median income).
    """
    df = pd.DataFrame(data_store.get_foreign_born())
    if "year" in df.columns:
        df = df.sort_values(["city", "year"]).groupby("city").tail(1)
    cols = [c for c in ["city", "city_type", "year", metric] if c in df.columns]
    df = df[cols].dropna(subset=[metric])
    return df.sort_values(metric, ascending=ascending).head(top_n).to_dict(orient="records")


def get_origins(city: str) -> List[Dict[str, Any]]:
    """
    Return detailed country-of-origin breakdown for a city.
    """
    df = pd.DataFrame(data_store.get_country_of_origin(city=city))
    if "estimate" in df.columns:
        df = df.sort_values("estimate", ascending=False)
    return df.to_dict(orient="records")


def get_income(city: str) -> List[Dict[str, Any]]:
    """
    Return median income and related metrics for a city.
    """
    df = pd.DataFrame(data_store.get_median_income(city=city))
    return df.to_dict(orient="records")

