from typing import Any, Dict, List
import os
from pathlib import Path

from google import genai

from . import data_store
from .rag import RagIndex, retrieve


INDEX_PATH = Path(__file__).parent.parent / "rag_index" / "index.json"

METRIC_HELP = {
  "fb_pct": "Foreign-born share of total population (percent).",
  "unemployment_rate": "Unemployment rate (percent).",
  "median_income": "Median household income (USD).",
  "poverty_rate": "Foreign-born poverty rate (percent).",
  "bachelors_pct": "Share with a bachelor's degree or higher (percent).",
  "homeownership_pct": "Homeownership rate (percent).",
  "fb_income": "Median income for foreign-born (USD).",
}


def _gemini_client() -> genai.Client:
  api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
  if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY).")
  return genai.Client(api_key=api_key)


def _gateway_cities_set() -> set[str]:
  """
  Derive the set of Gateway Cities from the processed cities_master data.
  Falls back to an empty set if the data isn't available.
  """
  try:
    rows = data_store.get_cities_master()
  except Exception:
    rows = []

  # Prefer explicit gateway flag from data if present.
  from_data = {
    r["city"]
    for r in rows
    if isinstance(r.get("city"), str) and r.get("city_type") == "gateway"
  }

  if from_data:
    return from_data

  # Fallback: hard-coded Gateway Cities list aligned with frontend.
  return {
    "Attleboro",
    "Barnstable",
    "Brockton",
    "Chelsea",
    "Chicopee",
    "Everett",
    "Fall River",
    "Fitchburg",
    "Framingham",
    "Haverhill",
    "Holyoke",
    "Lawrence",
    "Leominster",
    "Lowell",
    "Lynn",
    "Malden",
    "Methuen",
    "New Bedford",
    "Peabody",
    "Pittsfield",
    "Quincy",
    "Revere",
    "Salem",
    "Springfield",
    "Taunton",
    "Worcester",
  }


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

  analysis = {
    "type": "trend",
    "city": city,
    "start_year": start_year,
    "end_year": end_year,
    "start_value": start_val,
    "end_value": end_val,
    "direction": direction,
  }

  return {"answer": answer, "chart": chart, "analysis": analysis}


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

  analysis = {
    "type": "snapshot",
    "city": city,
    "foreign_born_pct": fb.get("fb_pct"),
    "median_household_income": emp.get("median_household_income"),
    "unemployment_rate": emp.get("unemployment_rate"),
    "bachelors_pct": edu.get("bachelors_pct"),
    "homeownership_pct": own.get("homeownership_pct"),
  }

  return {"answer": answer, "chart": None, "analysis": analysis}


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
  analysis = {
    "type": "origins",
    "city": city,
    "top5": top,
  }
  return {"answer": answer, "chart": None, "analysis": analysis}


def _lowest_poverty_cities(limit: int = 5) -> Dict[str, Any]:
  """
  Find Gateway Cities with the lowest foreign-born poverty rates using
  the time-series metric 'poverty_rate' (fb_poverty_pct).
  """
  rows = data_store.get_time_series(metric="poverty_rate")
  if not rows:
    return {
      "answer": (
        "I couldn't find foreign-born poverty rate data across Gateway Cities. "
        "Try focusing on a specific city in the dashboard.\n\n"
        "Source: American Community Survey 5-year estimates, 2010–2024."
      ),
      "chart": None,
    }

  gateway = _gateway_cities_set()

  latest_by_city: dict[str, Dict[str, Any]] = {}
  for r in rows:
    city = r.get("city")
    year = r.get("year")
    if not city or year is None:
      continue
    if gateway and city not in gateway:
      continue
    prev = latest_by_city.get(city)
    if prev is None or year > prev.get("year", -1):
      latest_by_city[city] = r

  clean = [
    (city, r["year"], r.get("value"))
    for city, r in latest_by_city.items()
    if r.get("value") is not None
  ]
  if not clean:
    return {
      "answer": (
        "I couldn't find usable foreign-born poverty rates for Gateway Cities.\n\n"
        "Source: American Community Survey 5-year estimates, 2010–2024."
      ),
      "chart": None,
    }

  clean.sort(key=lambda x: x[2])  # sort by poverty rate ascending
  top = clean[: max(1, limit)]

  lines = [
    "Gateway Cities with the lowest foreign-born poverty rates (latest ACS period):"
  ]
  for city, year, value in top:
    lines.append(f"- {city} ({year}): {_format_pct(value)}")

  answer = "\n".join(lines) + (
    "\n\nSource: American Community Survey 5-year estimates, 2010–2024."
  )
  analysis = {
    "type": "poverty_ranking",
    "cities": [
      {"city": city, "year": year, "poverty_rate": value} for city, year, value in top
    ],
  }
  return {"answer": answer, "chart": None, "analysis": analysis}


def _offline_chat(message: str) -> Dict[str, Any]:
  """
  Deterministic intent + analysis without LLM.
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

  # 2b) Poverty ranking across Gateway Cities.
  if ("poverty" in lower or "poor" in lower) and (
    "lowest" in lower or "low" in lower
  ):
    # Question like: "Which Gateway Cities have the lowest foreign-born poverty rates?"
    return _lowest_poverty_cities()

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


def _llm_rewrite(message: str, base_answer: str, analysis: Dict[str, Any]) -> str:
  """
  Uses Gemini to rewrite/expand the deterministic answer in a more natural way,
  without changing any numeric values.
  """
  try:
    client = _gemini_client()
  except Exception:
    return base_answer

  model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

  # Retrieve RAG context about metrics / tools / project rules.
  try:
    index = RagIndex(INDEX_PATH)
    docs = retrieve(index=index, query=message, metric_help=METRIC_HELP, k=4)
    rag_context = "\n\n".join(f"[{d.id}]\n{d.text}" for d in docs)
  except Exception:
    rag_context = ""

  system = (
    "You are helping Massachusetts journalists interpret ACS data about Gateway Cities.\n"
    "You are given:\n"
    "- The user's original question.\n"
    "- A structured analysis dictionary (JSON).\n"
    "- A baseline answer string.\n\n"
    "You may also see RAG context describing the available metrics and tools.\n\n"
    "Rewrite the answer to be clear and journalistic, but DO NOT change any numeric values, years, or city names.\n"
    "Keep it concise (2–4 sentences) and always keep the ACS source line verbatim at the end.\n"
  )

  prompt = (
    f"User question:\n{message}\n\n"
    f"RAG context:\n{rag_context}\n\n"
    f"Analysis JSON:\n{analysis}\n\n"
    f"Baseline answer:\n{base_answer}\n\n"
    "Now rewrite the answer as instructed."
  )

  try:
    resp = client.models.generate_content(
      model=model,
      contents=[
        {"role": "user", "parts": [{"text": system}]},
        {"role": "user", "parts": [{"text": prompt}]},
      ],
    )
    text = (resp.text or "").strip()  # type: ignore[attr-defined]
    # Add a small marker so we can verify Gemini is active.
    if text:
      return f"Interpretation:\n\n{text}"
    return base_answer
  except Exception as e:
    # For now, surface Gemini errors in the answer so we can debug setup.
    return base_answer + f"\n\n[Gemini error: {e}]"


def _llm_general_answer(message: str, fallback: str) -> str:
  """
  Use Gemini to answer a general knowledge question scoped to ACS / Gateway Cities.
  Falls back to *fallback* if Gemini is unavailable.
  """
  try:
    client = _gemini_client()
  except Exception:
    return fallback

  model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

  try:
    index = RagIndex(INDEX_PATH)
    docs = retrieve(index=index, query=message, metric_help=METRIC_HELP, k=4)
    rag_context = "\n\n".join(f"[{d.id}]\n{d.text}" for d in docs)
  except Exception:
    rag_context = ""

  system = (
    "You are a helpful assistant for Massachusetts journalists working with "
    "American Community Survey (ACS) data about Gateway Cities.\n"
    "Answer the user's question clearly and concisely (one short paragraph).\n"
    "If the question is unrelated to ACS data, demographics, or Gateway Cities, "
    "politely say you can only help with those topics.\n"
  )

  prompt = (
    f"User question:\n{message}\n\n"
    f"RAG context:\n{rag_context}\n\n"
    "Answer the question as instructed."
  )

  try:
    resp = client.models.generate_content(
      model=model,
      contents=[
        {"role": "user", "parts": [{"text": system}]},
        {"role": "user", "parts": [{"text": prompt}]},
      ],
    )
    text = (resp.text or "").strip()  # type: ignore[attr-defined]
    if text:
      return text
    return fallback
  except Exception:
    return fallback


def _is_general_question(text: str) -> bool:
  """Return True when the message looks like a general/informational question
  rather than a data query about a specific city."""
  lower = text.lower()
  signals = [
    "what is", "what are", "what's", "explain", "define", "definition",
    "why do", "why are", "why is", "how do", "how does", "how is",
    "tell me about", "describe", "meaning of",
  ]
  return any(s in lower for s in signals)


def chat(message: str) -> Dict[str, Any]:
  """
  Main entrypoint: run deterministic analysis, then (optionally) let Gemini
  rewrite the answer in natural language if a valid API key/model are set.
  """
  base = _offline_chat(message)
  analysis = base.get("analysis")

  # If we have structured analysis, let Gemini rewrite it.
  if isinstance(analysis, dict):
    answer = _llm_rewrite(
      message=message,
      base_answer=base.get("answer", ""),
      analysis=analysis,
    )
    return {
      "answer": answer,
      "chart": base.get("chart"),
    }

  # No structured analysis — if it looks like a general question, ask Gemini directly.
  if _is_general_question(message):
    answer = _llm_general_answer(message, fallback=base.get("answer", ""))
    return {
      "answer": answer,
      "chart": base.get("chart"),
    }

  # Otherwise return the deterministic offline answer.
  return {
    "answer": base.get("answer", ""),
    "chart": base.get("chart"),
  }

