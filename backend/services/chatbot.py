from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from . import data_store, rag_index

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    # Newer Gemini SDK (package: google-genai)
    from google import genai as genai_sdk  # type: ignore
except ImportError:
    genai_sdk = None

# ── Constants ─────────────────────────────────────────────────────────────────
TOP_K_FACTS = 5
PERIOD_LABEL = "2020–2024"
MIN_ORIGIN_ESTIMATE = 100

# ── Gateway Cities (short names) — used to filter rankings ───────────────────
GATEWAY_CITY_NAMES = {
    "Springfield", "Worcester", "Lowell", "Brockton", "New Bedford",
    "Lawrence", "Lynn", "Fall River", "Quincy", "Haverhill",
    "Malden", "Medford", "Chicopee", "Fitchburg", "Holyoke",
    "Leominster", "Chelsea", "Everett", "Revere", "Methuen",
    "Taunton", "Barnstable", "Pittsfield", "Attleboro", "Peabody", "Salem",
    "Boston", "Cambridge", "Somerville", "Weymouth", "Marlborough",
}

# ── B05006 variable code → real country name (verified from CSV labels) ───────
B05006_COUNTRIES = {
    "B05006_004E": "Denmark", "B05006_005E": "Ireland", "B05006_006E": "Norway",
    "B05006_007E": "Sweden", "B05006_009E": "United Kingdom (excl. England & Scotland)",
    "B05006_010E": "England", "B05006_011E": "Scotland", "B05006_012E": "Other Northern Europe",
    "B05006_014E": "Austria", "B05006_015E": "Belgium", "B05006_016E": "France",
    "B05006_017E": "Germany", "B05006_018E": "Netherlands", "B05006_019E": "Switzerland",
    "B05006_022E": "Greece", "B05006_023E": "Italy", "B05006_024E": "Portugal",
    "B05006_025E": "Azores Islands", "B05006_026E": "Spain",
    "B05006_029E": "Albania", "B05006_030E": "Belarus", "B05006_031E": "Bosnia and Herzegovina",
    "B05006_032E": "Bulgaria", "B05006_033E": "Croatia", "B05006_034E": "Czechoslovakia",
    "B05006_035E": "Hungary", "B05006_036E": "Latvia", "B05006_037E": "Lithuania",
    "B05006_038E": "Moldova", "B05006_039E": "North Macedonia", "B05006_040E": "Poland",
    "B05006_041E": "Romania", "B05006_042E": "Russia", "B05006_043E": "Serbia",
    "B05006_044E": "Ukraine",
    "B05006_050E": "China (excl. HK & Taiwan)", "B05006_051E": "Hong Kong",
    "B05006_052E": "Taiwan", "B05006_053E": "Japan", "B05006_054E": "Korea",
    "B05006_057E": "Afghanistan", "B05006_058E": "Bangladesh", "B05006_059E": "Bhutan",
    "B05006_060E": "India", "B05006_061E": "Iran", "B05006_062E": "Kazakhstan",
    "B05006_063E": "Nepal", "B05006_064E": "Pakistan", "B05006_065E": "Sri Lanka",
    "B05006_066E": "Uzbekistan", "B05006_069E": "Burma (Myanmar)", "B05006_070E": "Cambodia",
    "B05006_071E": "Indonesia", "B05006_072E": "Laos", "B05006_073E": "Malaysia",
    "B05006_074E": "Philippines", "B05006_076E": "Thailand", "B05006_077E": "Vietnam",
    "B05006_080E": "Armenia", "B05006_081E": "Azerbaijan", "B05006_083E": "Iraq",
    "B05006_084E": "Israel", "B05006_085E": "Jordan", "B05006_087E": "Lebanon",
    "B05006_089E": "Syria", "B05006_090E": "Turkey", "B05006_092E": "Yemen",
    "B05006_097E": "Eritrea", "B05006_098E": "Ethiopia", "B05006_099E": "Kenya",
    "B05006_100E": "Somalia", "B05006_101E": "Tanzania", "B05006_102E": "Uganda",
    "B05006_103E": "Zimbabwe", "B05006_106E": "Cameroon", "B05006_107E": "Congo",
    "B05006_108E": "DR Congo (Zaire)", "B05006_111E": "Algeria", "B05006_112E": "Egypt",
    "B05006_113E": "Morocco", "B05006_114E": "Sudan", "B05006_117E": "South Africa",
    "B05006_120E": "Cabo Verde", "B05006_121E": "Ghana", "B05006_122E": "Ivory Coast",
    "B05006_123E": "Liberia", "B05006_124E": "Nigeria", "B05006_125E": "Senegal",
    "B05006_126E": "Sierra Leone",
    "B05006_141E": "Bahamas", "B05006_142E": "Barbados", "B05006_143E": "Cuba",
    "B05006_144E": "Dominica", "B05006_145E": "Dominican Republic", "B05006_146E": "Grenada",
    "B05006_147E": "Haiti", "B05006_148E": "Jamaica", "B05006_151E": "Trinidad and Tobago",
    "B05006_152E": "West Indies", "B05006_153E": "Other Caribbean",
    "B05006_155E": "Belize", "B05006_156E": "Costa Rica", "B05006_157E": "El Salvador",
    "B05006_158E": "Guatemala", "B05006_159E": "Honduras", "B05006_160E": "Mexico",
    "B05006_161E": "Nicaragua", "B05006_162E": "Panama",
    "B05006_165E": "Argentina", "B05006_166E": "Bolivia", "B05006_167E": "Brazil",
    "B05006_168E": "Chile", "B05006_169E": "Colombia", "B05006_170E": "Ecuador",
    "B05006_171E": "Guyana", "B05006_172E": "Peru", "B05006_173E": "Uruguay",
    "B05006_174E": "Venezuela", "B05006_177E": "Canada", "B05006_178E": "Other Northern America",
}

GATEWAY_CITIES = {
    "Springfield city, Massachusetts": "Springfield",
    "Worcester city, Massachusetts": "Worcester",
    "Lowell city, Massachusetts": "Lowell",
    "Brockton city, Massachusetts": "Brockton",
    "New Bedford city, Massachusetts": "New Bedford",
    "Lawrence city, Massachusetts": "Lawrence",
    "Lynn city, Massachusetts": "Lynn",
    "Fall River city, Massachusetts": "Fall River",
    "Quincy city, Massachusetts": "Quincy",
    "Haverhill city, Massachusetts": "Haverhill",
    "Malden city, Massachusetts": "Malden",
    "Medford city, Massachusetts": "Medford",
    "Chicopee city, Massachusetts": "Chicopee",
    "Fitchburg city, Massachusetts": "Fitchburg",
    "Holyoke city, Massachusetts": "Holyoke",
    "Leominster city, Massachusetts": "Leominster",
    "Chelsea city, Massachusetts": "Chelsea",
    "Everett city, Massachusetts": "Everett",
    "Revere city, Massachusetts": "Revere",
    "Methuen Town city, Massachusetts": "Methuen",
    "Taunton city, Massachusetts": "Taunton",
    "Barnstable Town city, Massachusetts": "Barnstable",
    "Pittsfield city, Massachusetts": "Pittsfield",
    "Attleboro city, Massachusetts": "Attleboro",
    "Peabody city, Massachusetts": "Peabody",
    "Salem city, Massachusetts": "Salem",
    "Boston city, Massachusetts": "Boston",
    "Cambridge city, Massachusetts": "Cambridge",
    "Somerville city, Massachusetts": "Somerville",
    "Weymouth Town city, Massachusetts": "Weymouth",
    "Marlborough city, Massachusetts": "Marlborough",
}


# ── Load B05006 once ──────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _load_b05006() -> pd.DataFrame:
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "data" / "raw" / "ACSDT5Y2024.B05006-Data.csv",
        repo_root / "data" / "raw" / "ACSDT5Y2024_B05006-Data.csv",
        repo_root / "data" / "ACSDT5Y2024.B05006-Data.csv",
        repo_root / "data" / "ACSDT5Y2024_B05006-Data.csv",
    ]
    raw_path = next((p for p in candidates if p.exists()), None)
    if raw_path is None:
        print("[chatbot] WARNING: B05006 CSV not found.")
        return pd.DataFrame(columns=["city", "country", "estimate", "share_of_fb_pct", "total_fb"])

    df_raw = pd.read_csv(raw_path, header=0, skiprows=[1], encoding="utf-8-sig")
    df_raw.columns = df_raw.columns.astype(str).str.strip().str.replace('"', "")
    df_raw = df_raw[df_raw["NAME"].isin(GATEWAY_CITIES.keys())].copy()
    df_raw["city"] = df_raw["NAME"].map(GATEWAY_CITIES)
    df_raw["total_fb"] = pd.to_numeric(df_raw["B05006_001E"], errors="coerce")

    country_cols = {col: name for col, name in B05006_COUNTRIES.items() if col in df_raw.columns}
    rows = []
    for _, row in df_raw.iterrows():
        city = row["city"]
        total_fb = row["total_fb"]
        for col, country in country_cols.items():
            estimate = pd.to_numeric(row.get(col), errors="coerce")
            if pd.isna(estimate) or estimate < MIN_ORIGIN_ESTIMATE:
                continue
            share = (estimate / total_fb * 100) if (pd.notna(total_fb) and total_fb > 0) else None
            rows.append({
                "city": city,
                "country": country,
                "estimate": int(estimate),
                "share_of_fb_pct": round(share, 1) if share is not None else None,
                "total_fb": int(total_fb) if pd.notna(total_fb) else None,
            })

    df = pd.DataFrame(rows)
    print(f"[chatbot] B05006 loaded: {len(df)} rows, {df['city'].nunique()} cities")
    return df


def _get_top_origins(city: str, top_n: int = 3) -> list[dict]:
    df = _load_b05006()
    city_df = df[df["city"].str.lower() == city.lower()]
    if city_df.empty:
        return []
    return city_df.nlargest(top_n, "estimate").to_dict(orient="records")


# ── RAG helpers ───────────────────────────────────────────────────────────────
@dataclass
class ChatResponse:
    answer: str
    facts: List[Dict[str, Any]]


def _ensure_index_built() -> None:
    meta_path = rag_index.INDEX_DIR / "meta.jsonl"
    if not meta_path.exists():
        rag_index.build_index()


def _retrieve_facts(
    question: str,
    top_k: int = None,
    allowed_files: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    top_k = top_k if top_k is not None else TOP_K_FACTS
    _ensure_index_built()
    docs = rag_index.retrieve(question, top_k=max(top_k * 4, top_k))
    facts = [{"text": d.text, "meta": d.meta} for d in docs]
    if allowed_files:
        facts = [f for f in facts if f.get("meta", {}).get("file") in allowed_files]
    return facts[:top_k]


# ── FIX 1: Intent detection — homeownership checked BEFORE origins ────────────
def _detect_intent(question: str) -> str:
    q = question.lower()
    # Homeownership FIRST — "own" can appear in origin questions and cause wrong routing
    if any(kw in q for kw in ("homeownership", "home owner", "own home", "owner-occupied", "tenure", "renter")):
        return "homeownership"
    if any(kw in q for kw in ("origin", "origins", "country", "countries", "born in", "where from", "come from", "native country")):
        return "origins"
    if any(kw in q for kw in ("income", "median income", "earn", "salary", "wage")):
        return "income"
    if any(kw in q for kw in ("poverty", "poor", "below poverty", "poverty rate")):
        return "poverty"
    if any(kw in q for kw in ("education", "bachelor", "degree", "college", "schooling")):
        return "education"
    if any(kw in q for kw in ("unemployment", "unemployed", "employment", "jobs")):
        return "employment"
    if any(kw in q for kw in ("rent", "housing", "housing cost")):
        return "homeownership"
    # Open-ended "why/how" questions that don't clearly map to a numeric ACS slice
    if any(kw in q for kw in ("why ", "why are", "why is", "how come", "reasons for", "reason for")):
        return "qualitative"
    return "foreign_born"


# ── FIX 2: City detection against known list ──────────────────────────────────
def _detect_cities(question: str) -> List[str]:
    q = question.lower()
    matched = [c for c in GATEWAY_CITY_NAMES if c.lower() in q]
    # Also check data_store for any unlisted cities
    try:
        master = [r["city"] for r in data_store.get_cities_master() if r.get("city")]
        for c in master:
            if c.lower() in q and c not in matched:
                matched.append(c)
    except Exception:
        pass
    matched.sort(key=len, reverse=True)
    out: List[str] = []
    for c in matched:
        if c not in out:
            out.append(c)
    return out


def _detect_top_n(question: str) -> int:
    q = question.lower()
    if "top 10" in q or " ten " in q:
        return 10
    if "top 5" in q or " five " in q:
        return 5
    return 3


def _is_ranking_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in (
        "highest", "lowest", "most", "least", "top city", "which city",
        "ranking", "rank", "greatest", "compare all", "all cities",
        "most residents", "by count", "how many residents"
    ))


# ── FIX 3: Ranking filtered to gateway cities only ────────────────────────────
def _get_ranking_lines(metric: str = "foreign_born") -> List[str]:
    q = (metric or "").lower()
    try:
        if any(kw in q for kw in ("homeownership", "home owner", "own home", "rent")):
            rows = data_store.get_homeownership(gateway_only=True)
            rows = [r for r in rows if r.get("homeownership_pct") is not None]
            reverse = "highest" in q
            rows.sort(key=lambda r: r.get("homeownership_pct", 0), reverse=reverse)
            label = "highest" if reverse else "lowest"
            lines = [f"Gateway Cities by homeownership rate — {label} ({PERIOD_LABEL}):"]
            for i, r in enumerate(rows[:5], 1):
                lines.append(f"  {i}. {r['city']}: {r['homeownership_pct']:.1f}%")
            return lines
        elif "poverty" in q:
            rows = data_store.get_poverty(gateway_only=True)
            cleaned = []
            for r in rows:
                val = r.get("fb_poverty_pct")
                if val is None:
                    continue
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    continue
                if pd.isna(v):
                    continue
                rr = dict(r)
                rr["fb_poverty_pct"] = v
                cleaned.append(rr)
            rows = cleaned
            reverse = "lowest" not in q
            rows.sort(key=lambda r: r.get("fb_poverty_pct", 0), reverse=reverse)
            label = "highest" if reverse else "lowest"
            lines = [f"Gateway Cities by foreign-born poverty rate — {label} ({PERIOD_LABEL}):"]
            for i, r in enumerate(rows[:5], 1):
                lines.append(f"  {i}. {r['city']}: {r['fb_poverty_pct']:.1f}%")
            return lines
        elif any(kw in q for kw in ("income", "salary", "wage", "earn")):
            rows = data_store.get_median_income(gateway_only=True)
            rows = [r for r in rows if r.get("median_income_foreign_born") is not None]
            reverse = "highest" in q
            rows.sort(key=lambda r: r.get("median_income_foreign_born", 0), reverse=reverse)
            label = "highest" if reverse else "lowest"
            lines = [f"Gateway Cities by foreign-born median income — {label} ({PERIOD_LABEL}):"]
            for i, r in enumerate(rows[:5], 1):
                lines.append(f"  {i}. {r['city']}: ${int(r['median_income_foreign_born']):,}")
            return lines
        else:
            # Default: foreign-born share (but allow ranking by count)
            rows = data_store.get_foreign_born(gateway_only=True)
            want_count = any(kw in q for kw in ("count", "number", "most residents", "by count", "how many"))

            if want_count:
                def _fb_count(row: dict) -> Optional[float]:
                    # Processed file uses `foreign_born`; some codepaths may use `fb_count`.
                    val = row.get("foreign_born", row.get("fb_count"))
                    try:
                        return float(val) if val is not None else None
                    except (TypeError, ValueError):
                        return None

                rows = [r for r in rows if _fb_count(r) is not None]
                reverse = ("highest" in q) or ("most" in q)
                rows.sort(key=lambda r: _fb_count(r) or 0, reverse=reverse)
                label = "most" if reverse else "fewest"
                lines = [f"Gateway Cities by foreign-born population count — {label} ({PERIOD_LABEL}):"]
                for i, r in enumerate(rows[:5], 1):
                    cnt = int(_fb_count(r) or 0)
                    lines.append(f"  {i}. {r['city']}: {cnt:,} residents")
                return lines
            else:
                rows = [r for r in rows if r.get("fb_pct") is not None]
                reverse = ("highest" in q) or ("most" in q)
                rows.sort(key=lambda r: r.get("fb_pct", 0), reverse=reverse)
                label = "highest" if reverse else "lowest"
                lines = [f"Gateway Cities by foreign-born share — {label} ({PERIOD_LABEL}):"]
                for i, r in enumerate(rows[:5], 1):
                    lines.append(f"  {i}. {r['city']}: {r['fb_pct']:.1f}%")
                return lines
    except Exception as e:
        print(f"[chatbot] Ranking error: {e}")
        return []


# ── Real data builder ─────────────────────────────────────────────────────────
def _get_real_data(question: str) -> str:
    q = question.lower()
    cities = _detect_cities(question)
    intent = _detect_intent(question)
    city = cities[0] if cities else None

    lines = []

    # Ranking questions — always filter to gateway cities
    if _is_ranking_question(question) and not city:
        ranking = _get_ranking_lines(question)
        if ranking:
            return "\n".join(ranking)

    # Foreign-born share (only when intent is foreign_born)
    if intent == "foreign_born":
        rows = data_store.get_foreign_born(city=city)
        if city is None:
            rows = [r for r in rows if r.get("city") in GATEWAY_CITY_NAMES]
        for r in rows:
            parts = [f"{r.get('city', '')} ({PERIOD_LABEL} ACS 5-year estimate)"]
            if r.get("fb_pct") is not None:
                parts.append(f"foreign-born share {r['fb_pct']:.1f}%")
            # Use `foreign_born` count from processed foreign_born_core.parquet
            fb_count = r.get("foreign_born", r.get("fb_count"))
            if fb_count is not None and r.get("total_pop") is not None:
                parts.append(f"({int(fb_count):,} of {int(r['total_pop']):,} residents)")
            if len(parts) > 1:
                lines.append(" ".join(parts))

    # Origins — direct B05006 lookup
    if intent == "origins":
        top_n = _detect_top_n(question)
        target_cities = cities[:2] if len(cities) >= 2 else ([city] if city else [])
        for cty in target_cities:
            top_origins = _get_top_origins(cty, top_n=top_n)
            if not top_origins:
                lines.append(f"{cty}: no origin data available.")
                continue
            for r in top_origins:
                share_str = f" ({r['share_of_fb_pct']:.1f}% of foreign-born)" if r.get("share_of_fb_pct") else ""
                lines.append(
                    f"{cty} ({PERIOD_LABEL} ACS 5-year estimate): "
                    f"{r['estimate']:,} from {r['country']}{share_str}."
                )

    # FIX 4: Income — query BOTH cities for comparison
    if intent == "income":
        target_cities = cities[:2] if len(cities) >= 2 else ([city] if city else [None])
        for cty in target_cities:
            rows = data_store.get_median_income(city=cty)
            for r in rows:
                cty_name = r.get("city")
                fb_inc = r.get("median_income_foreign_born")
                tot_inc = r.get("median_income_total")
                if cty_name:
                    bits = [f"{cty_name} ({PERIOD_LABEL} ACS 5-year estimate)"]
                    if fb_inc is not None:
                        bits.append(f"foreign-born median income ${int(fb_inc):,}")
                    if tot_inc is not None:
                        bits.append(f"overall median ${int(tot_inc):,}")
                    if len(bits) > 1:
                        lines.append(" ".join(bits))

    # Poverty
    if intent == "poverty":
        target_cities = cities[:2] if len(cities) >= 2 else ([city] if city else [None])
        for cty in target_cities:
            rows = data_store.get_poverty(city=cty)
            for r in rows:
                cty_name = r.get("city")
                fb_pov = r.get("fb_poverty_pct")
                nat_pov = r.get("native_poverty_pct")
                if cty_name and fb_pov is not None:
                    line = (
                        f"{cty_name} ({PERIOD_LABEL} ACS 5-year estimate): "
                        f"foreign-born poverty rate {fb_pov:.1f}%"
                    )
                    if nat_pov is not None:
                        line += f", native-born {nat_pov:.1f}%"
                    lines.append(line)

    # FIX 5: Education — now actually queries get_education()
    if intent == "education":
        target_cities = cities[:2] if len(cities) >= 2 else ([city] if city else [None])
        for cty in target_cities:
            rows = data_store.get_education(city=cty)
            if not rows:
                lines.append(f"(Education data not yet available for {cty or 'this city'}.)")
                continue
            for r in rows:
                cty_name = r.get("city")
                bach = r.get("bachelors_pct")
                if cty_name and bach is not None:
                    lines.append(
                        f"{cty_name} ({PERIOD_LABEL} ACS 5-year estimate): "
                        f"{bach:.1f}% of adults have a bachelor's degree or higher"
                    )

    # FIX 1: Homeownership — only runs when intent is homeownership (no conflict with origins)
    if intent == "homeownership":
        target_cities = cities[:2] if len(cities) >= 2 else ([city] if city else [None])
        for cty in target_cities:
            rows = data_store.get_homeownership(city=cty)
            for r in rows:
                cty_name = r.get("city")
                pct = r.get("homeownership_pct")
                if cty_name and pct is not None:
                    lines.append(
                        f"{cty_name} ({PERIOD_LABEL} ACS 5-year estimate): "
                        f"homeownership rate {pct:.1f}%"
                    )

    if not lines:
        return "(No matching rows from our tables for this question.)"
    return "\n".join(lines)


# ── Gemini writer ─────────────────────────────────────────────────────────────
def _call_gemini(question: str, real_data: str, facts: List[Dict[str, Any]]) -> Optional[str]:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    debug = os.environ.get("CHATBOT_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    # High-level trace for when Gemini is invoked and with which intent.
    if debug:
        intent_dbg = _detect_intent(question)
        print(f"[chatbot] Gemini called, intent={intent_dbg}, api_key={'SET' if api_key else 'MISSING'}")
    if (genai is None and genai_sdk is None) or not api_key:
        if debug:
            import sys
            reason_parts = []
            if not api_key:
                reason_parts.append("missing GOOGLE_API_KEY/GEMINI_API_KEY")
            if genai is None and genai_sdk is None:
                reason_parts.append("no Gemini SDK installed (google-genai or google-generativeai)")
            reason = ", ".join(reason_parts) if reason_parts else "unknown"
            print(f"[chatbot] Gemini disabled: {reason}", file=sys.stderr)
        return None

    verified = "\n".join(f"- {f['text']}" for f in facts) if facts else "(No RAG facts retrieved.)"

    intent = _detect_intent(question)

    # Two prompt modes:
    # 1) Data-driven ACS answers (origins, income, poverty, etc.)
    # 2) Qualitative "why/how" questions that don't have direct table rows
    if intent == "qualitative":
        prompt = (
            "CONTEXT FACTS (you may or may not need these):\n"
            f"{verified}\n\n"
            f"QUESTION: {question}\n\n"
            "ROLE:\n"
            "- You are a local reporter explaining possible reasons or context for this question.\n"
            "- You do NOT have structured data for this question, only general background knowledge and the context facts above.\n\n"
            "RULES:\n"
            "- Give 2–4 short paragraphs explaining plausible reasons and context.\n"
            "- Do NOT invent exact statistics or percentages.\n"
            "- You may explain patterns and context but NEVER invent statistics, percentages, or citations.\n"
            "- If you reference a number, it must come from the RAG facts provided above.\n"
            "- Do NOT fabricate specific study names, years, or made-up reports.\n"
            "- It is OK to speak in general terms (e.g., immigration patterns, neighborhood demographics, restaurant clustering).\n"
            "- Do NOT add any 'Source:' line at the end.\n"
        )
    else:
        # FIX 5: single correct source table per intent
        source_table = {
            "origins": "B05006",
            "income": "B06011",
            "poverty": "S0501",
            "education": "B15002",
            "homeownership": "B25003",
            "employment": "DP03",
        }.get(intent, "S0501")

        prompt = (
            "REAL DATA (from our ACS CSV — use these numbers only):\n"
            f"{real_data}\n\n"
            "VERIFIED CONTEXT (RAG facts for additional context):\n"
            f"{verified}\n\n"
            f"QUESTION: {question}\n\n"
            "RULES:\n"
            "- Only use numbers from REAL DATA above. Never invent or estimate.\n"
            f"- Never say 'in 2024'. Say 'based on the {PERIOD_LABEL} ACS 5-year estimate'.\n"
            "- State the ACS period ONCE at the start only. Do NOT repeat it on every line.\n"
            "- For comparisons: write one short paragraph per city.\n"
            "- Write in journalist-friendly prose, not a raw data list.\n"
            f"- End with EXACTLY ONE line: 'Source: ACS 5-year estimates, {source_table}.'\n"
            "- Do NOT add any other 'Source:' lines anywhere in the response.\n"
            "- If data is missing say: 'I don't have that data yet.' Do not guess.\n"
        )

    def _norm_model_name(name: str) -> str:
        # google-genai typically uses "models/<id>" while older SDK uses "<id>"
        return name if name.startswith("models/") else name

    preferred_models = (
        # Newer commonly-available families first
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    )

    not_found_count = 0
    last_err: Optional[Exception] = None

    for model_name in preferred_models:
        # Prefer newer SDK if available.
        if genai_sdk is not None:
            try:
                client = genai_sdk.Client(api_key=api_key)
                resp = client.models.generate_content(model=_norm_model_name(model_name), contents=prompt)
                text = getattr(resp, "text", None)
                if text and str(text).strip():
                    return str(text).strip()
            except Exception as e:
                import sys
                last_err = e
                print(f"[chatbot] Gemini {model_name} failed: {e}", file=sys.stderr)
                # Track NOT_FOUND so we can fall back to ListModels.
                if "NOT_FOUND" in str(e) or "not found" in str(e).lower():
                    not_found_count += 1
        if genai is not None:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                text = getattr(resp, "text", None)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                import sys
                last_err = e
                print(f"[chatbot] Gemini {model_name} failed: {e}", file=sys.stderr)
                continue

    # If all preferred models are missing, ask the API what *is* available.
    if genai_sdk is not None and not_found_count >= max(1, len(preferred_models) - 1):
        try:
            import sys
            client = genai_sdk.Client(api_key=api_key)
            models = list(client.models.list())
            # Pick models that support generateContent
            candidates = []
            for m in models:
                name = getattr(m, "name", None) or ""
                methods = getattr(m, "supported_generation_methods", None) or []
                if "generateContent" not in methods:
                    continue
                # Heuristic preference: gemini + flash first, then gemini.
                score = 0
                lname = name.lower()
                if "gemini" in lname:
                    score += 10
                if "flash" in lname:
                    score += 5
                if "pro" in lname:
                    score += 3
                # Avoid embeddings/image-only models
                if "embedding" in lname or "vision" in lname:
                    score -= 5
                candidates.append((score, name))
            candidates.sort(reverse=True)
            if debug:
                top_names = [n for _, n in candidates[:10]]
                print(f"[chatbot] Gemini available models (top picks): {top_names}", file=sys.stderr)
            for _, model_full_name in candidates[:10]:
                try:
                    resp = client.models.generate_content(model=_norm_model_name(model_full_name), contents=prompt)
                    text = getattr(resp, "text", None)
                    if text and str(text).strip():
                        if debug:
                            print(f"[chatbot] Gemini selected model: {model_full_name}", file=sys.stderr)
                        return str(text).strip()
                except Exception as e:
                    last_err = e
                    print(f"[chatbot] Gemini {model_full_name} failed: {e}", file=sys.stderr)
        except Exception as e:
            last_err = e
            if debug:
                import sys
                print(f"[chatbot] Gemini ListModels failed: {e}", file=sys.stderr)

    if debug and last_err is not None:
        import sys
        print(f"[chatbot] Gemini exhausted model options; last error: {last_err}", file=sys.stderr)
    return None


def _format_origins_answer(cities: List[str], top_n: int) -> str:
    if not cities:
        return "I don't have that data yet."
    blocks = [f"Based on the {PERIOD_LABEL} ACS 5-year estimates:"]
    for cty in cities:
        rows = _get_top_origins(cty, top_n=top_n)
        if not rows:
            blocks.append(f"\n{cty}: no origin data available.")
            continue
        parts = []
        for r in rows:
            share = r.get("share_of_fb_pct")
            parts.append(
                f"{r['country']} ({r['estimate']:,}" +
                (f", {share:.1f}%" if share is not None else "") + ")"
            )
        blocks.append(f"\n{cty}: " + ", ".join(parts) + ".")
    blocks.append("\nSource: ACS 5-year estimates, B05006.")
    return "\n".join(blocks).strip()


# ── Main pipeline ─────────────────────────────────────────────────────────────
def answer_question(question: str) -> ChatResponse:
    question = (question or "").strip()
    if not question:
        return ChatResponse(
            answer="Please ask a question about Massachusetts gateway cities.",
            facts=[],
        )

    intent = _detect_intent(question)
    real_data = _get_real_data(question)

    allowed_files = {
        "origins":       ["country_of_origin.txt"],
        "income":        ["median_income.txt", "employment_income.txt"],
        "poverty":       ["poverty.txt", "employment_income.txt"],
        "education":     ["education.txt"],
        "homeownership": ["homeownership.txt"],
        "employment":    ["employment_income.txt"],
    }.get(intent, ["foreign_born.txt"])

    facts = _retrieve_facts(question, allowed_files=allowed_files)

    llm_answer = _call_gemini(question, real_data, facts)
    if llm_answer:
        return ChatResponse(answer=llm_answer, facts=facts)

    # Fallback when Gemini unavailable
    if "(No matching rows" not in real_data:
        # If Pandas truth has an answer, use it even if retrieval returned 0 facts
        # (common when user wording doesn't overlap with fact wording).
        fallback = real_data
    elif "(No matching rows" in real_data and not facts:
        fallback = (
            "I don't have data for that question yet. "
            "I can answer about foreign-born share, origins, income, "
            "poverty, education, and homeownership for Gateway Cities."
        )
    elif intent == "origins":
        cities = _detect_cities(question)[:2]
        top_n = _detect_top_n(question)
        fallback = _format_origins_answer(cities, top_n=top_n)
    elif (
        any(kw in question.lower() for kw in ("compare", " vs ", "versus", "highest", "lowest", "rank", "ranking", "top"))
        and "(No matching rows" not in real_data
    ):
        # For ranking/compare questions, prefer Pandas truth over a single retrieved fact.
        fallback = real_data
    elif facts:
        top = facts[0]["text"].rstrip(".")
        # Fact lines already include a "Source:".
        fallback = f"Based on our ACS 5-year data: {top}."
    else:
        fallback = "I don't have that data yet."

    return ChatResponse(answer=fallback, facts=facts)