from typing import Any, Dict, List

from . import data_store


def _find_cities_in_text(text: str) -> List[str]:
  """
  Very simple city-name matcher based on exact substring.
  """
  try:
    cities_master = data_store.get_cities_master()
  except Exception:
    return []

  text_lower = text.lower()
  names = sorted({(row.get("city") or "") for row in cities_master})
  mentioned: List[str] = []
  for name in names:
    n_lower = name.lower()
    if n_lower and n_lower in text_lower:
      mentioned.append(name)
  return mentioned


def _format_pct(v: Any) -> str:
  try:
    return f"{float(v):.1f}%"
  except Exception:
    return "N/A"


def _format_dollar(v: Any) -> str:
  try:
    return f"${int(round(float(v))):,}"
  except Exception:
    return "N/A"


def _foreign_born_trend(city: str) -> Dict[str, Any]:
  rows = data_store.get_time_series(city=city, metric="fb_pct")
  if not rows:
    return {
      "answer": (
        f"I couldn't find a foreign-born time series for {city}. "
        "Try selecting this city in the Trends tab to confirm data availability.\n\n"
        "Source: American Community Survey 5-year estimates, 2010–2024."
      ),
      "chart": None,
    }

  norm = [
    {
      "city": r.get("city"),
      "year": r.get("year"),
      "metric": r.get("metric"),
      "value": r.get("value"),
    }
    for r in rows
    if r.get("year") is not None and r.get("value") is not None
  ]
  norm = sorted(norm, key=lambda r: r["year"])

  start_year = norm[0]["year"]
  end_year = norm[-1]["year"]
  start_val = norm[0]["value"]
  end_val = norm[-1]["value"]

  if end_val > start_val:
    direction = "increased"
  elif end_val < start_val:
    direction = "decreased"
  else:
    direction = "remained roughly flat"

  answer = (
    f"In {city}, the foreign-born share {direction} from "
    f"{_format_pct(start_val)} in {start_year} to {_format_pct(end_val)} in {end_year}.\n\n"
    "You can see the full year-by-year trend in the chart below.\n\n"
    "Source: American Community Survey 5-year estimates, 2010–2024."
  )

  chart = {
    "type": "time_series",
    "title": f"Foreign-born share in {city}, {start_year}–{end_year}",
    "metric": "fb_pct",
    "city": city,
    "data": norm,
  }

  return {"answer": answer, "chart": chart}


def _latest_snapshot(city: str) -> Dict[str, Any]:
  fb_rows = data_store.get_foreign_born(city=city)
  emp_rows = data_store.get_employment_income(city=city)
  edu_rows = data_store.get_education(city=city)
  own_rows = data_store.get_homeownership(city=city)

  fb = fb_rows[0] if fb_rows else {}
  emp = emp_rows[0] if emp_rows else {}
  edu = edu_rows[0] if edu_rows else {}
  own = own_rows[0] if own_rows else {}

  parts = [f"**{city} (latest ACS period)**"]
  if "fb_pct" in fb:
    parts.append(f"Foreign-born share: {_format_pct(fb['fb_pct'])}")
  if "median_household_income" in emp:
    parts.append(
      f"Median household income: {_format_dollar(emp['median_household_income'])}"
    )
  if "unemployment_rate" in emp:
    parts.append(f"Unemployment rate: {_format_pct(emp['unemployment_rate'])}")
  if "bachelors_pct" in edu:
    parts.append(f"Bachelor's degree or higher: {_format_pct(edu['bachelors_pct'])}")
  if "homeownership_pct" in own:
    parts.append(f"Homeownership rate: {_format_pct(own['homeownership_pct'])}")

  answer = "\n".join(parts) + (
    "\n\nSource: American Community Survey 5-year estimates, 2010–2024."
  )

  return {"answer": answer, "chart": None}


def _top_origins(city: str) -> Dict[str, Any]:
  rows = data_store.get_country_of_origin(city=city)
  rows = [r for r in rows if r.get("estimate") is not None]
  rows.sort(key=lambda r: r["estimate"], reverse=True)
  top = rows[:5]

  if not top:
    return {
      "answer": (
        f"I couldn't find detailed country-of-origin data for {city}.\n\n"
        "Source: American Community Survey 5-year estimates, 2010–2024."
      ),
      "chart": None,
    }

  lines = [f"Top foreign-born origins in {city} (latest ACS period):"]
  total = sum(r["estimate"] for r in top)
  for r in top:
    pct = (r["estimate"] / total) * 100 if total else 0
    country = (r.get("country") or "").rstrip(":")
    lines.append(f"- {country}: {r['estimate']:,} ({pct:.1f}% of top 5)")

  answer = "\n".join(lines) + (
    "\n\nSource: American Community Survey 5-year estimates, 2010–2024."
  )
  return {"answer": answer, "chart": None}


def chat(message: str) -> Dict[str, Any]:
  """
  Deterministic chatbot that answers a small set of common questions
  using the existing data_store APIs. No external LLM needed.
  """
  text = (message or "").strip()
  if not text:
    return {
      "answer": "Please enter a question about Massachusetts Gateway Cities.",
      "chart": None,
    }

  lower = text.lower()
  cities = _find_cities_in_text(lower)

  # 1) Trend questions.
  if cities and ("trend" in lower or "over time" in lower or "since" in lower):
    city = cities[0]
    return _foreign_born_trend(city)

  # 2) Country-of-origin questions.
  if cities and ("origin" in lower or "origins" in lower or "country" in lower):
    city = cities[0]
    return _top_origins(city)

  # 3) Single-city snapshot.
  if cities:
    city = cities[0]
    return _latest_snapshot(city)

  # 4) General overview: top foreign-born cities.
  fb_rows = data_store.get_foreign_born()
  if fb_rows:
    avg = sum((r.get("fb_pct") or 0) for r in fb_rows) / max(len(fb_rows), 1)
    top = sorted(
      fb_rows,
      key=lambda r: (r.get("fb_pct") or 0),
      reverse=True,
    )[:5]
    lines = [
      f"Across {len(fb_rows)} Massachusetts places, the average foreign-born share is {_format_pct(avg)}.",
      "Top 5 by foreign-born share:",
    ]
    for r in top:
      lines.append(f"- {r.get('city')}: {_format_pct(r.get('fb_pct'))}")
    lines.append(
      "\nSource: American Community Survey 5-year estimates, 2010–2024."
    )
    return {"answer": "\n".join(lines), "chart": None}

  # Fallback.
  return {
    "answer": (
      "I couldn't load the ACS data. Please make sure the backend can read "
      "the processed parquet files in data/processed."
    ),
    "chart": None,
  }

