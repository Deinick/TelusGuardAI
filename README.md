# TelusGuardAI

An AI-powered platform for analyzing TELUS network service disruptions during natural and infrastructure events. The system uses a multi-agent orchestration pipeline to interpret natural language queries, gather intelligence from web and weather sources, and produce geospatial impact assessments with TELUS tower-level KPIs.

---

## Overview

The TELUS Network Impact Analyzer helps TELUS operations teams assess where and how strongly network outages or degradations occur in response to events such as ice storms, floods, power outages, or large-scale gatherings. Users ask questions in plain language (e.g., *"What areas were affected by the ice storm in Toronto?"*), and the system returns structured events, affected geographic areas, severity, confidence scores, and suggested mitigation actions—all visualized on an interactive map with TELUS tower coverage and KPI overlays.

**Note:** This system is specifically designed for and limited to **TELUS network infrastructure** (MCC 302, MNC 720) in Canada.

---

## Live Demo

**[deinick.github.io/TelusGuardAI](https://deinick.github.io/TelusGuardAI/)**

The hosted version is a **static frontend-only demo**: the full TELUS coverage map (all ~17,000 towers), live-simulated per-tower KPIs, and the impact-area visualization all run entirely in the browser — no backend required. The "Load demo analysis" button loads a bundled sample scenario (an ice storm in Toronto + a concert at BC Place) rather than calling a live AI backend.

This is intentional: the real natural-language analysis pipeline calls TELUS's internal AI model gateway, which is not something that should be exposed to public internet traffic from a personal portfolio site. See **[Run the full AI pipeline locally](#run-the-full-ai-pipeline-locally)** below to try the real multi-agent reasoning.

---

## Architecture

The backend is built around a **three-agent orchestration** model:

| Agent | Role |
|-------|------|
| **Event Intelligence** | Parses the user query to extract event types, locations, timeframes, and search keywords. |
| **Web Intelligence** | Runs web searches and (when relevant) fetches weather data to support impact reasoning. |
| **Geospatial Reasoning** | Analyzes gathered data and LLM knowledge to produce events with affected areas, lat/long bounds, severity, and confidence for TELUS towers. |

Results are cached, filtered by confidence and `max_areas`, and returned as structured JSON. The frontend consumes this API to drive an interactive **React + Leaflet** dashboard with:

- **Event Analysis** — Natural language input and analysis triggers
- **TELUS Network Coverage Map** — TELUS towers, heatmaps, and impact zones with selection
- **Details & Impact Panels** — TELUS tower-level KPIs (traffic, latency, packet loss, energy) and area-level reports

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3, Flask, Flask-CORS, aiohttp, BeautifulSoup |
| **AI / LLMs** | Gemma, DeepSeek, GPT (configurable endpoints) |
| **Data** | OpenWeather API, custom web search, Canada city coordinates, Zenodo KPI time series, TELUS tower CSVs |
| **Frontend** | React 19, Vite, React Router, Leaflet, Leaflet.heat |

---

## Datasets & data files

### Zenodo: Network operator KPIs time series dataset

The project uses the **[Network operator KPIs time series dataset](https://zenodo.org)** from Zenodo. The backend provides:

- **`zenodo_loader`** (`backend/services/zenodo_loader.py`) — loads time-series files in `r1.txt` format (`time_in_seconds value` per line).
- **`ZenodoStream`** (`backend/services/kpi_stream.py`) — consumes loaded values for KPI-style streams (e.g. baseline metrics).

Place Zenodo-derived `r1.txt` (or compatible) files where the loader expects them and wire them into the KPI pipeline as needed. *(Add the specific Zenodo record URL or DOI here when available.)*

### TELUS Tower data (`frontend/public/` + `frontend/src/data/`)

The project uses TELUS tower data derived from the **OpenCellID API**, a global open database of cellular infrastructure. This data is **filtered exclusively for TELUS towers** in Canada, providing:

- **TELUS tower geographic coordinates** (latitude, longitude)  
- **Network type / radio technology** (e.g., LTE, NR)  
- **Mobile Country Code (MCC) 302** (Canada) and **Mobile Network Code (MNC) 720** (TELUS)
- **Coverage range estimates**  
- **Sample counts** indicating data reliability
  
| File | Description |
|------|-------------|
| **`src/data/302.csv`** | Raw cell/tower data (MCC 302 = Canada). Contains all Canadian carriers. |
| **`public/telus_towers.json`** | **TELUS-only towers** (MNC 720) derived from `302.csv`. Fetched at runtime by the coverage map (not bundled into the JS build, so it stays out of the main chunk). |

To regenerate `public/telus_towers.json` from `302.csv`:

```bash
cd frontend
python convert_csv_to_json.py
```

`convert_csv_to_json.py` filters `302.csv` to `mcc=302` and `mnc=720` (TELUS only) and writes `id`, `lat`, `lon`, `radio`, `mcc`, `mnc`, `range`, `samples` per tower.

**Important:** The system only analyzes and displays TELUS network infrastructure. Other carriers (Rogers, Bell, Shaw) are filtered out.

---

## Getting Started

### Prerequisites

- **Python 3.9+** (uses `python3`; macOS/Linux don't ship a bare `python` command by default)
- **Node.js 18+** and npm
- Frontend: `VITE_API_BASE_URL` pointing at the backend (default: `http://127.0.0.1:5001`)

### Backend

```bash
git clone https://github.com/Deinick/TelusGuardAI.git
cd TelusGuardAI/backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py   # venv's `python` now points at python3
```

The API runs at **http://127.0.0.1:5001** by default.

### Frontend

```bash
cd TelusGuardAI/frontend   # from repo root; adjust path if you're already in backend/
npm install
npm run dev
```

The app is served by Vite (typically **http://localhost:5173**). Ensure the backend is running and `VITE_API_BASE_URL` matches it if you change the host or port.

### Run the full AI pipeline locally

`backend/config.py` reads all AI model tokens/endpoints from environment variables — nothing is hardcoded, and there are no bundled credentials. You have two options:

1. **No credentials at all** — just run the backend as-is. Every agent (`event_intelligence.py`, `geospatial_reasoning.py`) has a built-in fallback path: if a model call fails or returns nothing, it automatically falls back to deterministic keyword parsing and pattern-based area recommendations. You'll still get a full, structured response from `/api/analyze-network-impact` — it just won't be LLM-reasoned.
2. **Bring your own model** — `services/ai_client.py` POSTs to any OpenAI-compatible `/v1/chat/completions` endpoint. Set `GEMMA_ENDPOINT`/`GEMMA_TOKEN`, `DEEPSEEK_ENDPOINT`/`DEEPSEEK_TOKEN`, and `GPT_ENDPOINT`/`GPT_TOKEN` (see `.env.example`) to point at your own provider to get real LLM-reasoned results end to end.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info and endpoint list |
| `GET` | `/health` | Health check and config summary |
| `POST` | `/api/analyze-network-impact` | Run analysis from a natural language `question` (TELUS network only) |
| `POST` | `/api/kpis` | Fetch KPIs for given TELUS `tower_ids` |
| `GET` | `/api/cache-stats` | Cache statistics |
| `GET` | `/api/cached-queries` | List cached analysis queries |
| `POST` | `/api/clear-cache` | Clear analysis cache |
| `GET` | `/api/docs` | Structured API documentation and data models |

Example analysis request:

```json
{
  "question": "What TELUS coverage areas were affected by the ice storm in Toronto?",
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
│   ├── convert_csv_to_json.py   # 302.csv → public/telus_towers.json (TELUS only)
│   ├── public/
│   │   └── telus_towers.json   # Tower dataset, fetched at runtime (not bundled)
│   ├── src/
│   │   ├── main.jsx
│   │   ├── pages/           # CoverageMapPage (the app)
│   │   ├── components/      # CoverageMap (Leaflet map, KPI popups, impact areas)
│   │   ├── lib/              # simulateKpi (client-side KPI simulation), leafletIcons
│   │   └── data/            # 302.csv (raw source data for the conversion script)
│   └── vite.config.js
├── .github/workflows/deploy-pages.yml   # Builds & deploys frontend/ to GitHub Pages
└── README.md
```

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `OPENWEATHER_API_KEY` | OpenWeather API key for weather-driven impact analysis |
| `GEMMA_ENDPOINT` / `GEMMA_TOKEN` | Model used by the Event Intelligence agent |
| `DEEPSEEK_ENDPOINT` / `DEEPSEEK_TOKEN` | Model used by the Web Intelligence agent |
| `GPT_ENDPOINT` / `GPT_TOKEN` | Model used by the Geospatial Reasoning agent |
| `VITE_API_BASE_URL` | Backend base URL for the frontend (default: `http://127.0.0.1:5001`) |
| `VITE_DEMO_MODE` | When `true`, the frontend never calls a backend — "Run analysis" loads a bundled sample scenario instead. Set for the GitHub Pages build (`frontend/.env.production`). |

None of the AI model tokens have defaults or fallback values in `backend/config.py` — they must be set via environment variables or a `.env` file. Without them, agents automatically use their built-in fallback logic (see [Run the full AI pipeline locally](#run-the-full-ai-pipeline-locally)).

---

## Data Models (High Level)

- **Event** — `event_id`, `event_name`, `event_type`, `timeframe`, `affected_areas[]`
- **AffectedArea** — `area_name`, `severity`, `lat_range`, `long_range`, `center`, `reasoning`, `estimated_impact`, `confidence`, `data_points`
- **AnalysisResult** — `query`, `timestamp`, `summary`, `events`, `total_events`, `total_affected_areas`, `analysis_metadata`

Severity: `critical` | `high` | `moderate` | `low`. See `/api/docs` for full field definitions.

---

## Network Scope

This platform is designed exclusively for **TELUS network infrastructure** analysis:
- **MCC (Mobile Country Code):** 302 (Canada)
- **MNC (Mobile Network Code):** 720 (TELUS)
- **Coverage:** TELUS towers across Canada
- **Data Source:** OpenCellID database, filtered for TELUS only

Other Canadian carriers (Rogers MNC 720, Bell MNC 610, Shaw, etc.) are not included in this analysis platform.

---

## License

See the repository for license details.
