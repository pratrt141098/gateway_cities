# Setup
1.⁠ ⁠Clone & enter the repo
```bash
git clone https://github.com/pratrt141098/gateway_cities.git
cd gateway_cities
```
2.⁠ ⁠Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
3.⁠ ⁠Frontend setup
```bash
cd ../frontend
npm install
```
Running Locally
You need two terminals open simultaneously.

Terminal 1 — Backend (Flask)
```bash
cd /path/to/gateway_cities
source backend/.venv/bin/activate
python backend/app.py
```
# Runs at http://localhost:3000
Terminal 2 — Frontend (Vite)
```bash
cd /path/to/gateway_cities/frontend
npm run dev
```

# Runs at http://localhost:5173

Open http://localhost:5173 in your browser.

gateway_cities/
├── backend/
│   ├── app.py                  # Flask API routes
│   ├── requirements.txt
│   └── services/
│       └── data_store.py       # Parquet data loaders
├── data/
│   ├── raw/                    # Original ACS CSV downloads
│   ├── interim/                # Intermediate parquet files
│   └── processed/              # Final parquet files consumed by API
├── frontend/
│   ├── public/data/
│   │   └── gateway_cities.geojson   # City boundary polygons
│   └── src/
│       ├── App.jsx             # Root component, tab navigation
‎Read more
[3/10/26, 10:53:29 AM] Pratik: Data Pipeline
Run these in order from the repo root if you need to rebuild processed data:

```bash
source backend/.venv/bin/activate
python scripts/00_validate_raw.py
python scripts/10_normalize_places.py
python scripts/20_build_per_capita_metrics.py
```