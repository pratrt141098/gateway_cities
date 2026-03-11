"""
Generate human-readable fact sentences from processed data.
Fixed: origins_facts() now correctly parses B05006 wide format CSV,
maps variable codes to real country names, and filters tiny populations.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data"          # where ACSDT5Y2024_B05006-Data.csv lives
OUT_DIR = BASE_DIR / "data" / "facts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIOD_LABEL = "2020–2024"

# ── Minimum population to include in origin facts ─────────────────────────────
MIN_ESTIMATE = 100   # filters out Scotland=3, Denmark=7, etc.

# ── Gateway Cities: Census NAME → short name ──────────────────────────────────
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

# ── B05006 variable code → real country name ──────────────────────────────────
B05006_COUNTRIES = {
    "B05006_004E": "Denmark",
    "B05006_005E": "Ireland",
    "B05006_006E": "Norway",
    "B05006_007E": "Sweden",
    "B05006_009E": "UK (excl. England & Scotland)",
    "B05006_010E": "England",
    "B05006_011E": "Scotland",
    "B05006_013E": "Other Northern Europe",
    "B05006_015E": "Austria",
    "B05006_016E": "Belgium",
    "B05006_017E": "France",
    "B05006_018E": "Germany",
    "B05006_019E": "Netherlands",
    "B05006_020E": "Switzerland",
    "B05006_021E": "Other Western Europe",
    "B05006_023E": "Greece",
    "B05006_024E": "Italy",
    "B05006_025E": "Portugal",
    "B05006_026E": "Azores Islands",
    "B05006_027E": "Spain",
    "B05006_028E": "Other Southern Europe",
    "B05006_030E": "Albania",
    "B05006_031E": "Belarus",
    "B05006_032E": "Bosnia and Herzegovina",
    "B05006_033E": "Bulgaria",
    "B05006_034E": "Croatia",
    "B05006_035E": "Czechoslovakia",
    "B05006_036E": "Hungary",
    "B05006_037E": "Latvia",
    "B05006_038E": "Lithuania",
    "B05006_039E": "Moldova",
    "B05006_040E": "North Macedonia",
    "B05006_041E": "Poland",
    "B05006_042E": "Romania",
    "B05006_043E": "Russia",
    "B05006_044E": "Serbia",
    "B05006_045E": "Ukraine",
    "B05006_046E": "Other Eastern Europe",
    "B05006_052E": "China (excl. HK & Taiwan)",
    "B05006_053E": "Hong Kong",
    "B05006_054E": "Taiwan",
    "B05006_055E": "Japan",
    "B05006_056E": "Korea",
    "B05006_059E": "Afghanistan",
    "B05006_060E": "Bangladesh",
    "B05006_061E": "Bhutan",
    "B05006_062E": "India",
    "B05006_063E": "Iran",
    "B05006_064E": "Kazakhstan",
    "B05006_065E": "Nepal",
    "B05006_066E": "Pakistan",
    "B05006_067E": "Sri Lanka",
    "B05006_068E": "Uzbekistan",
    "B05006_071E": "Burma (Myanmar)",
    "B05006_072E": "Cambodia",
    "B05006_073E": "Indonesia",
    "B05006_074E": "Laos",
    "B05006_075E": "Malaysia",
    "B05006_076E": "Philippines",
    "B05006_077E": "Singapore",
    "B05006_078E": "Thailand",
    "B05006_079E": "Vietnam",
    "B05006_082E": "Armenia",
    "B05006_083E": "Azerbaijan",
    "B05006_084E": "Georgia",
    "B05006_085E": "Iraq",
    "B05006_086E": "Israel",
    "B05006_087E": "Jordan",
    "B05006_088E": "Kuwait",
    "B05006_089E": "Lebanon",
    "B05006_090E": "Saudi Arabia",
    "B05006_091E": "Syria",
    "B05006_092E": "Turkey",
    "B05006_093E": "United Arab Emirates",
    "B05006_094E": "Yemen",
    "B05006_099E": "Eritrea",
    "B05006_100E": "Ethiopia",
    "B05006_101E": "Kenya",
    "B05006_102E": "Somalia",
    "B05006_103E": "Tanzania",
    "B05006_104E": "Uganda",
    "B05006_105E": "Zimbabwe",
    "B05006_108E": "Cameroon",
    "B05006_109E": "Congo",
    "B05006_110E": "DR Congo",
    "B05006_113E": "Algeria",
    "B05006_114E": "Egypt",
    "B05006_115E": "Morocco",
    "B05006_116E": "Sudan",
    "B05006_119E": "South Africa",
    "B05006_122E": "Cabo Verde",
    "B05006_123E": "Ghana",
    "B05006_124E": "Ivory Coast",
    "B05006_125E": "Liberia",
    "B05006_126E": "Nigeria",
    "B05006_127E": "Senegal",
    "B05006_128E": "Sierra Leone",
    "B05006_136E": "Bahamas",
    "B05006_137E": "Barbados",
    "B05006_138E": "Cuba",
    "B05006_139E": "Dominica",
    "B05006_140E": "Dominican Republic",
    "B05006_141E": "Grenada",
    "B05006_142E": "Haiti",
    "B05006_143E": "Jamaica",
    "B05006_146E": "Trinidad and Tobago",
    "B05006_148E": "Other Caribbean",
    "B05006_150E": "Belize",
    "B05006_151E": "Costa Rica",
    "B05006_152E": "El Salvador",
    "B05006_153E": "Guatemala",
    "B05006_154E": "Honduras",
    "B05006_155E": "Mexico",
    "B05006_156E": "Nicaragua",
    "B05006_157E": "Panama",
    "B05006_160E": "Argentina",
    "B05006_161E": "Bolivia",
    "B05006_162E": "Brazil",
    "B05006_163E": "Chile",
    "B05006_164E": "Colombia",
    "B05006_165E": "Ecuador",
    "B05006_166E": "Guyana",
    "B05006_167E": "Peru",
    "B05006_168E": "Uruguay",
    "B05006_169E": "Venezuela",
    "B05006_172E": "Canada",
}


# ─────────────────────────────────────────────────────────────────────────────
# FIXED origins_facts() — reads raw B05006 CSV directly
# ─────────────────────────────────────────────────────────────────────────────

def origins_facts() -> None:
    """
    Read ACSDT5Y2024_B05006-Data.csv (wide format) directly.
    Map variable codes to real country names.
    Filter out populations under MIN_ESTIMATE (no more Scotland=3).
    Write one fact line per city-country pair above the threshold.
    """
    # Try raw CSV first, fall back to processed parquet
    raw_csv = RAW_DIR / "ACSDT5Y2024_B05006-Data.csv"
    processed_csv = PROCESSED / "country_of_origin.csv"

    if raw_csv.exists():
        source_path = raw_csv
        # B05006 has 2-row header: row 0 = variable codes, row 1 = labels
        df_raw = pd.read_csv(source_path, header=[0, 1])
        # Flatten to variable codes only
        df_raw.columns = [col[0] for col in df_raw.columns]
    elif processed_csv.exists():
        # Already long format — use as-is if it has country column
        df_long = pd.read_csv(processed_csv)
        if "country" in df_long.columns and "estimate" in df_long.columns:
            _write_origins_from_long(df_long)
            return
        # Otherwise treat as raw wide
        df_raw = df_long
    else:
        print("WARNING: No B05006 source found. Skipping origins facts.")
        (OUT_DIR / "country_of_origin.txt").write_text("", encoding="utf-8")
        return

    # Filter to Gateway Cities only
    df_raw = df_raw[df_raw["NAME"].isin(GATEWAY_CITIES.keys())].copy()
    df_raw["city"] = df_raw["NAME"].map(GATEWAY_CITIES)

    # Total foreign-born for share calculation
    df_raw["total_fb"] = pd.to_numeric(df_raw.get("B05006_001E", 0), errors="coerce")

    # Only use country columns we have a name mapping for
    country_cols = {col: name for col, name in B05006_COUNTRIES.items() if col in df_raw.columns}

    lines = []
    for _, row in df_raw.iterrows():
        city = row["city"]
        total_fb = row["total_fb"]

        # Collect all countries for this city above threshold
        city_origins = []
        for col, country in country_cols.items():
            estimate = pd.to_numeric(row.get(col), errors="coerce")
            if pd.isna(estimate) or estimate < MIN_ESTIMATE:
                continue
            city_origins.append((country, int(estimate)))

        # Sort by estimate descending
        city_origins.sort(key=lambda x: x[1], reverse=True)

        # Write one line per country
        for country, estimate in city_origins:
            share = (estimate / total_fb * 100) if (pd.notna(total_fb) and total_fb > 0) else None
            text = (
                f"{city} ({PERIOD_LABEL} ACS 5-year estimate): "
                f"{estimate:,} foreign-born residents from {country}"
            )
            if share is not None:
                text += f" ({share:.1f}% of city's foreign-born population)."
            else:
                text += "."
            text += " Source: ACS 5-year estimates, B05006."
            lines.append(text)

    (OUT_DIR / "country_of_origin.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ origins_facts: wrote {len(lines)} lines (MIN_ESTIMATE={MIN_ESTIMATE})")

    # Also save clean long-format CSV for data_store to use
    _save_clean_origins_csv(df_raw, country_cols)


def _save_clean_origins_csv(df_raw: pd.DataFrame, country_cols: dict) -> None:
    """Save a clean long-format country_of_origin.csv for data_store."""
    rows = []
    for _, row in df_raw.iterrows():
        city = row["city"]
        total_fb = row["total_fb"]
        for col, country in country_cols.items():
            estimate = pd.to_numeric(row.get(col), errors="coerce")
            if pd.isna(estimate) or estimate < MIN_ESTIMATE:
                continue
            share = (estimate / total_fb * 100) if (pd.notna(total_fb) and total_fb > 0) else None
            rows.append({
                "city": city,
                "country": country,
                "estimate": int(estimate),
                "share_of_fb_pct": round(share, 1) if share is not None else None,
                "total_fb": int(total_fb) if pd.notna(total_fb) else None,
                "year_label": f"{PERIOD_LABEL} ACS 5-year estimate",
                "year": 2024,
            })

    df_clean = pd.DataFrame(rows).sort_values(["city", "estimate"], ascending=[True, False])
    out_path = PROCESSED / "country_of_origin_clean.csv"
    df_clean.to_csv(out_path, index=False)
    print(f"✓ Saved clean origins CSV: {out_path} ({len(df_clean)} rows)")


def _write_origins_from_long(df: pd.DataFrame) -> None:
    """Fallback: write facts from already-long-format CSV."""
    df["estimate"] = pd.to_numeric(df["estimate"], errors="coerce")
    df = df[df["estimate"] >= MIN_ESTIMATE]
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        country = row.get("country")
        estimate = row.get("estimate")
        share = row.get("share_of_fb_pct") or row.get("share_pct")
        if not city or not country or pd.isna(estimate):
            continue
        text = (
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): "
            f"{int(estimate):,} foreign-born residents from {country}"
        )
        if pd.notna(share):
            text += f" ({float(share):.1f}% of city's foreign-born population)."
        else:
            text += "."
        text += " Source: ACS 5-year estimates, B05006."
        lines.append(text)
    (OUT_DIR / "country_of_origin.txt").write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# All other fact generators (unchanged except PERIOD_LABEL already fixed)
# ─────────────────────────────────────────────────────────────────────────────

def foreign_born_facts() -> None:
    df = pd.read_parquet(PROCESSED / "foreign_born_core.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        fb_pct = row.get("fb_pct")
        fb_count = row.get("fb_count")
        total_pop = row.get("total_pop")
        if city is None or fb_pct is None:
            continue
        text = f"{city} ({PERIOD_LABEL} ACS 5-year estimate): foreign-born share is {fb_pct:.1f}%"
        if pd.notna(fb_count) and pd.notna(total_pop):
            text += f" ({int(fb_count):,} of {int(total_pop):,} residents)."
        text += " Source: ACS 5-year estimates, S0501."
        lines.append(text)
    (OUT_DIR / "foreign_born.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ foreign_born_facts: {len(lines)} lines")


def median_income_facts() -> None:
    df = pd.read_parquet(PROCESSED / "median_income.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        income = row.get("median_income_foreign_born") or row.get("median_income_total")
        if city is None or income is None:
            continue
        lines.append(
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): median income for foreign-born "
            f"residents was ${int(income):,}. Source: ACS 5-year estimates, B06011."
        )
    (OUT_DIR / "median_income.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ median_income_facts: {len(lines)} lines")


def education_facts() -> None:
    df = pd.read_parquet(PROCESSED / "education.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        bachelors = row.get("bachelors_pct")
        if city is None or bachelors is None:
            continue
        lines.append(
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): {bachelors:.1f}% of adults had "
            f"at least a bachelor's degree. Source: ACS 5-year estimates, B15002."
        )
    (OUT_DIR / "education.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ education_facts: {len(lines)} lines")


def homeownership_facts() -> None:
    df = pd.read_parquet(PROCESSED / "homeownership.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        own = row.get("homeownership_pct")
        if city is None or own is None:
            continue
        lines.append(
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): {own:.1f}% of households were "
            f"owner-occupied. Source: ACS 5-year estimates, B25003."
        )
    (OUT_DIR / "homeownership.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ homeownership_facts: {len(lines)} lines")


def employment_income_facts() -> None:
    df = pd.read_parquet(PROCESSED / "employment_income.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        unemp = row.get("unemployment_rate")
        med_inc = row.get("median_household_income")
        if city is None:
            continue
        bits = []
        if pd.notna(unemp):
            bits.append(f"unemployment rate was {unemp:.1f}%")
        if pd.notna(med_inc):
            bits.append(f"median household income was ${int(med_inc):,}")
        if not bits:
            continue
        text = (
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): "
            + " and ".join(bits)
            + ". Source: ACS 5-year estimates, DP03."
        )
        lines.append(text)
    (OUT_DIR / "employment_income.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ employment_income_facts: {len(lines)} lines")


def poverty_facts() -> None:
    df = pd.read_parquet(PROCESSED / "poverty_by_nativity.parquet")
    lines = []
    for _, row in df.iterrows():
        city = row.get("city")
        fb_pov = row.get("fb_poverty_pct")
        nat_pov = row.get("native_poverty_pct")
        if city is None or fb_pov is None:
            continue
        text = (
            f"{city} ({PERIOD_LABEL} ACS 5-year estimate): {fb_pov:.1f}% of foreign-born "
            f"residents were below the poverty line"
        )
        if pd.notna(nat_pov):
            text += f", compared with {nat_pov:.1f}% of native-born residents."
        text += " Source: ACS 5-year estimates, B05010."
        lines.append(text)
    (OUT_DIR / "poverty.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ poverty_facts: {len(lines)} lines")


def main() -> None:
    foreign_born_facts()
    median_income_facts()
    education_facts()
    homeownership_facts()
    employment_income_facts()
    poverty_facts()
    origins_facts()   # Fixed last — most complex
    print(f"\n✓ All fact files written to {OUT_DIR}")
    print("Next: delete data/rag_index/meta.jsonl and restart backend to rebuild index.")


if __name__ == "__main__":
    main()