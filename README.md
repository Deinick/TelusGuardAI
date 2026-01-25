# Network Impact Analyzer

An AI-powered platform for analyzing network service disruptions during natural and infrastructure events. The system uses a multi-agent orchestration pipeline to interpret natural language queries, gather intelligence from web and weather sources, and produce geospatial impact assessments with tower-level KPIs.

---

## Overview

The Network Impact Analyzer helps operations teams assess where and how strongly network outages or degradations occur in response to events such as ice storms, floods, power outages, or large-scale gatherings. Users ask questions in plain language (e.g., *"What areas were affected by the ice storm in Toronto?"*), and the system returns structured events, affected geographic areas, severity, confidence scores, and suggested mitigation actions—all visualized on an interactive map with tower coverage and KPI overlays.

---

## Architecture

The backend is built around a **three-agent orchestration** model:

| Agent | Role |
|-------|------|
| **Event Intelligence** | Parses the user query to extract event types, locations, timeframes, and search keywords. |
| **Web Intelligence** | Runs web searches and (when relevant) fetches weather data to support impact reasoning. |
| **Geospatial Reasoning** | Analyzes gathered data and LLM knowledge to produce events with affected areas, lat/long bounds, severity, and confidence. |

Results are cached, filtered by confidence and `max_areas`, and returned as structured JSON. The frontend consumes this API to drive an interactive **React + Leaflet** dashboard with:

- **Event Analysis** — Natural language input and analysis triggers
- **Network Coverage Map** — Towers, heatmaps, and impact zones with selection
- **Details & Impact Panels** — Tower-level KPIs (traffic, latency, packet loss, energy) and area-level reports

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3, Flask, Flask-CORS, aiohttp, BeautifulSoup |
| **AI / LLMs** | Gemma, DeepSeek, GPT (configurable endpoints) |
| **Data** | OpenWeather API, custom web search, Canada city coordinates, Zenodo KPI time series, tower CSVs |
| **Frontend** | React 19, Vite, React Router, Leaflet, Leaflet.heat |

---

## Datasets & data files

### Zenodo: Network operator KPIs time series dataset

The project uses the **[Network operator KPIs time series dataset](https://zenodo.org)** from Zenodo. The backend provides:

- **`zenodo_loader`** (`backend/services/zenodo_loader.py`) — loads time-series files in `r1.txt` format (`time_in_seconds value` per line).
- **`ZenodoStream`** (`backend/services/kpi_stream.py`) — consumes loaded values for KPI-style streams (e.g. baseline metrics).

Place Zenodo-derived `r1.txt` (or compatible) files where the loader expects them and wire them into the KPI pipeline as needed. *(Add the specific Zenodo record URL or DOI here when available.)*

### Tower data (`frontend/src/data/`)

The project uses tower data derived from the **OpenCellID API**, a global open database of cellular infrastructure. This data provides:

- **Tower geographic coordinates** (latitude, longitude)  
- **Network type / radio technology** (e.g., LTE, NR)  
- **Mobile Country Code (MCC)** and **Mobile Network Code (MNC)** for operator identification (e.g., TELUS)  
- **Coverage range estimates**  
- **Sample counts** indicating data reliability
  
| File | Description |
|------|-------------|
| **`302.csv`** | Raw cell/tower data (MCC 302 = Canada). Columns include `radio`, `mcc`, `mnc`, `cell_id`, `lon`, `lat`, `range`, `samples`. |
| **`telus_towers.json`** | TELUS towers (MNC 720) derived from `302.csv`. Used by the coverage map and KPI views. |

To regenerate `telus_towers.json` from `302.csv`:

```bash
cd frontend
python convert_csv_to_json.py
```

`convert_csv_to_json.py` filters `302.csv` to `mcc=302` and `mnc=720` (TELUS) and writes `id`, `lat`, `lon`, `radio`, `mcc`, `mnc`, `range`, `samples` per tower.

---

## Getting Started

> **Note:** Clone the repository with the `integrate/frontend-into-layout` branch:
> ```bash
> git clone -b integrate/frontend-into-layout <repository-url>
> ```
> Or, if you’ve already cloned: `git checkout integrate/frontend-into-layout`

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- Backend: AI model endpoints and (optionally) `OPENWEATHER_API_KEY` configured
- Frontend: `VITE_API_BASE_URL` pointing at the backend (default: `http://127.0.0.1:5001`)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure via `config.py` or environment variables (e.g. `OPENWEATHER_API_KEY`). Then:

```bash
python app.py
```

The API runs at **http://127.0.0.1:5001** by default.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is served by Vite (typically **http://localhost:5173**). Ensure the backend is running and `VITE_API_BASE_URL` matches it if you change the host or port.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info and endpoint list |
| `GET` | `/health` | Health check and config summary |
| `POST` | `/api/analyze-network-impact` | Run analysis from a natural language `question` |
| `POST` | `/api/kpis` | Fetch KPIs for given `tower_ids` |
| `GET` | `/api/cache-stats` | Cache statistics |
| `GET` | `/api/cached-queries` | List cached analysis queries |
| `POST` | `/api/clear-cache` | Clear analysis cache |
| `GET` | `/api/docs` | Structured API documentation and data models |

Example analysis request:

```json
{
  "question": "What areas were affected by the ice storm in Toronto?",
  "options": {
    "max_areas": 10,
    "min_confidence": 0.7,
    "include_reasoning": true
  }
}
```

Full request/response schemas and `AffectedArea` / `Event` structures are described at `GET /api/docs`.

---

## Project Structure

```
├── backend/
│   ├── app.py              # Flask app and routes
│   ├── orchestrator.py     # Multi-agent orchestration
│   ├── config.py           # Config and AI/API endpoints
│   ├── agents/
│   │   ├── event_intelligence.py
│   │   ├── web_intelligence.py
│   │   └── geospatial_reasoning.py
│   ├── models/             # Data models (Event, AffectedArea, etc.)
│   ├── services/           # AI client, web search, weather, KPI, zenodo_loader, tower_loader
│   ├── data/               # Canada city coordinates and related
│   └── utils/              # Logger, cache
├── frontend/
│   ├── convert_csv_to_json.py   # 302.csv → telus_towers.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/          # DashboardPage, CoverageMapPage
│   │   ├── components/     # EventPanel, CoverageMap, DetailsPanel, etc.
│   │   └── data/           # 302.csv, telus_towers.json
│   └── vite.config.js
└── README.md
```

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `OPENWEATHER_API_KEY` | OpenWeather API key for weather-driven impact analysis |
| `VITE_API_BASE_URL` | Backend base URL for the frontend (default: `http://127.0.0.1:5001`) |

AI model endpoints and tokens are defined in `backend/config.py`; use environment variables or a `.env` file as needed for your environment.

---

## Data Models (High Level)

- **Event** — `event_id`, `event_name`, `event_type`, `timeframe`, `affected_areas[]`
- **AffectedArea** — `area_name`, `severity`, `lat_range`, `long_range`, `center`, `reasoning`, `estimated_impact`, `confidence`, `data_points`
- **AnalysisResult** — `query`, `timestamp`, `summary`, `events`, `total_events`, `total_affected_areas`, `analysis_metadata`

Severity: `critical` \| `high` \| `moderate` \| `low`. See `/api/docs` for full field definitions.

---

## License

See the repository for license details.
