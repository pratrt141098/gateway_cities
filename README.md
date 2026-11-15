# Massachusetts Gateway Cities Dashboard

**An interactive data analytics platform for exploring immigration and socioeconomic patterns across Massachusetts communities using U.S. Census American Community Survey (ACS) data.**

The project brings together a Python data pipeline, a Flask API, a React dashboard, and a Gemini-assisted chatbot to make local demographic data easier to explore and compare. It was developed for a journalism and research use case, in partnership with GBH Boston and with support from MassMutual Boston, as described in the original project documentation.

**[Live Dashboard](https://dd4g-gatewayscities.up.railway.app/)** · **[Source Code](https://github.com/pratrt141098/gateway_cities)** · **[Data Source](https://www.census.gov/programs-surveys/acs)**

## Project Highlights

- **End-to-end data pipeline:** Retrieve ACS tables from the Census API, standardize geographic identifiers, and generate analysis-ready Parquet datasets.
- **Interactive analytics:** Compare foreign-born population shares, country-of-origin profiles, education, employment, income, poverty, and housing indicators.
- **Geographic exploration:** Visualize city-level differences on an interactive Leaflet map.
- **Historical exploration:** Examine estimates from ACS 5-year releases labeled **2012–2024**, with appropriate caution about overlapping survey periods.
- **AI-assisted queries:** Combine deterministic calculations from the project's datasets with Gemini-generated natural-language explanations.
- **Data export and testing:** Download data from dashboard views and run backend API tests with `pytest`.

## Dashboard Features

| View | What it provides |
| --- | --- |
| **Overview** | A quick comparison of foreign-born population shares across selected cities. |
| **Per Capita Comparison** | Side-by-side comparisons of demographic and socioeconomic indicators. |
| **City Profile** | A detailed look at an individual city's population, income, education, and housing data. |
| **Country of Origins** | Foreign-born population estimates organized by origin country and region. |
| **Map View** | Interactive geographic visualization of city-level statistics. |
| **Trends** | Time-series charts for selected indicators and cities. |
| **AI Chatbot** | Natural-language questions supported by data-driven calculations and Gemini-assisted responses. |

For example, the chatbot can help users explore questions such as:

- How has the foreign-born share changed across ACS releases for Lowell?
- Which Gateway Cities have the highest foreign-born population shares?
- How do education or income indicators compare between two cities?

## Data Scope and Methodology

The current geography configuration targets **32 Massachusetts places**:

| Group | Places | Purpose |
| --- | ---: | --- |
| Gateway Cities | 26 | The Massachusetts-designated Gateway Cities. |
| Comparison Cities | 4 | Framingham, Marlborough, Somerville, and Weymouth. |
| Benchmark Cities | 2 | Boston and Cambridge. |

The Gateway Cities are **Attleboro, Barnstable, Brockton, Chelsea, Chicopee, Everett, Fall River, Fitchburg, Haverhill, Holyoke, Lawrence, Leominster, Lowell, Lynn, Malden, Methuen, New Bedford, Peabody, Pittsfield, Quincy, Revere, Salem, Springfield, Taunton, Westfield, and Worcester**. Geographic classifications are maintained in [`scripts/city_config.py`](scripts/city_config.py).

The project uses **ACS 5-year estimate releases labeled 2012–2024**. Each release summarizes a rolling five-year period; for example, the release labeled 2024 represents 2020–2024, **not** a single-year measurement for 2024. Consecutive 5-year releases overlap substantially and should not be interpreted as independent annual observations or used alone to infer statistically significant changes. The Census Bureau recommends comparisons between nonoverlapping periods.

Other methodological considerations:

- Metrics are derived from ACS estimates, not a complete census of every resident.
- ACS table definitions, geographic availability, and missing-value codes should be checked when comparing releases.
- The current extraction pipeline does not retain ACS margins of error in its intermediate output, so the dashboard should be treated as an **exploratory analysis tool**, not a statistical-significance testing system.
- A mean across cities is not necessarily a population-weighted Massachusetts statewide estimate.

**References:** [U.S. Census ACS](https://www.census.gov/programs-surveys/acs) · [ACS comparison guidance](https://www.census.gov/programs-surveys/acs/guidance/comparing-acs-data.html) · [Massachusetts Gateway Cities designation](https://www.mass.gov/info-details/ffio-technical-assistance-guidance)

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Data processing | Python, Pandas, NumPy, PyArrow, Census API |
| Backend | Flask, REST endpoints |
| Frontend | React 19, Vite 7, Recharts |
| Geospatial | Leaflet, React-Leaflet, GeoJSON |
| AI | Google Gemini API, data-grounded response logic |
| Tests | pytest, Flask test client |
| Deployment | Railway (live dashboard) |

## Repository Structure

```text
gateway_cities/
├── backend/
│   ├── app.py                       # Flask API routes
│   ├── rag_index/                    # Retrieval index for chatbot context
│   └── services/                     # Data access, chatbot, retrieval helpers
├── data/
│   ├── raw/                          # Optional manually downloaded ACS files
│   ├── interim/                      # ACS Parquet files organized by year
│   └── processed/                    # Analytics-ready Parquet datasets
├── frontend/
│   ├── public/data/                  # Geographic data, including GeoJSON
│   └── src/                          # React views, components and API client
├── scripts/
│   ├── city_config.py                # Geography and city classifications
│   ├── fetch_acs_data.py             # Census API extraction
│   ├── 20_build_per_capita_metrics.py # Metric transformations
│   ├── 00_validate_raw.py            # Legacy CSV validation
│   └── 10_normalize_places.py        # Legacy CSV normalization
├── tests/                            # Backend API tests
├── .env.example                      # Safe environment-variable template
├── requirements.txt                  # Runtime Python dependencies
├── requirements-dev.txt              # Test dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python **3.12** (recommended for this project)
- Node.js **20.19+ or 22.12+** and npm (for Vite 7)
- A [Gemini API key](https://aistudio.google.com/api-keys) to enable Gemini-powered responses
- A [Census API key](https://api.census.gov/data/key_signup.html) if rebuilding data from the Census API

### 1. Clone and install backend dependencies

```bash
git clone https://github.com/pratrt141098/gateway_cities.git
cd gateway_cities
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit the local `.env` to supply your API keys where needed. **Never commit `.env` or real credentials.** The processed datasets are included in the repository for local exploration without rerunning the Census extraction pipeline.

### 3. Install frontend dependencies

```bash
cd frontend
npm ci
```

### 4. Run locally

Run the backend from the repository root in one terminal:

```bash
source .venv/bin/activate
python backend/app.py
```

The backend serves `http://127.0.0.1:3000/api/health` by default.

In a second terminal, start the frontend:

```bash
cd frontend
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The Vite configuration proxies `/api` requests to the local Flask backend.

## Rebuild the ACS Datasets

The **primary data pipeline** uses the Census API and does **not** require the legacy CSV scripts:

```bash
# From the repository root, after configuring CENSUS_API_KEY
python scripts/fetch_acs_data.py
python scripts/20_build_per_capita_metrics.py
```

Intermediate files are written to `data/interim/{year}/{table}.parquet`; derived datasets are written to `data/processed/` and read by the Flask API. Full regeneration overwrites processed files: back up existing Parquet data before rebuilding and verify completeness of the requested tables and years.

For a smaller extraction or a preview of planned requests:

```bash
python scripts/fetch_acs_data.py --dry-run
python scripts/fetch_acs_data.py --year 2024 --table b05002
```

The separate `00_validate_raw.py` and `10_normalize_places.py` scripts support an earlier, manually downloaded CSV workflow. They are not sequential steps of the Census API pipeline.

## API Overview

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/health` | GET | Service health check |
| `/api/cities` | GET | Current city list and metadata |
| `/api/foreign-born` | GET | Foreign-born population estimates |
| `/api/country-of-origin` | GET | Foreign-born population by origin |
| `/api/education` | GET | Education indicators |
| `/api/homeownership` | GET | Housing tenure indicators |
| `/api/employment-income` | GET | Employment and income indicators |
| `/api/poverty` | GET | Poverty indicators |
| `/api/median-income` | GET | Median income by nativity |
| `/api/map-stats` | GET | Geographic visualization data |
| `/api/time-series` | GET | Historical estimates for a selected metric |
| `/api/chat` | POST | Chatbot request, with JSON `{"message":"..."}` |

Some GET endpoints accept query parameters such as `city`, `city_type`, or `metric`. See [`backend/app.py`](backend/app.py) for the route definitions.

## Tests and Quality Checks

```bash
# From the repository root
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v

# Frontend checks
cd frontend
npm run lint
npm run build
```

The backend tests cover basic health, data API behavior, chat input validation, successful responses, and error handling using mocks. These commands are provided for verification; passing results are not asserted here.

## Acknowledgments and Attribution

Project documentation describes collaboration with **GBH Boston** and support from **MassMutual Boston**. The underlying demographic datasets are sourced from the **U.S. Census Bureau's American Community Survey**. This repository is an independent software project and is not a Census Bureau publication.

**License:** No explicit software license is specified in this repository. Public visibility does not by itself grant permission to reuse or redistribute the code; project maintainers and collaborators should agree on a license before one is added.
