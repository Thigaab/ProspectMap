# ProspectMap

Lead generation tool for local businesses with no, or very little, web
presence. It uses the Google Places API to find businesses around a city,
scores them out of 100, and surfaces the best leads in a CLI, a CSV/JSON
export, **and** a web UI (map, table, kanban) for follow-up tracking.

## Stack

- **Python CLI** (`cli/`) — search, scoring, CSV/JSON export. Usable on its
  own. SQLite-backed cache so re-runs don't burn API quota.
- **FastAPI** (`api/`) — thin HTTP layer over the CLI modules; serves the
  frontend on `localhost:8000`.
- **Next.js 16** frontend (`web/`) — App Router, React 19, Tailwind v4,
  TanStack Query v5, react-leaflet, dnd-kit. Three views (map, table,
  kanban) plus a dashboard with a search form.

All three layers share the same `prospects.db` SQLite file at the repo root.

## Installation

```bash
git clone <repo> ProspectMap && cd ProspectMap

# Python 3.11+ venv
python3 -m venv .venv
source .venv/bin/activate          # bash / zsh
# source .venv/bin/activate.fish   # fish
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your GOOGLE_API_KEY
```

### Enable the required Google APIs

In the Google Cloud console, for the project that owns your key, enable:

- **Places API** (Text Search, Nearby Search, Place Details)
- **Geocoding API** (city → coordinates)

### Frontend dependencies (optional, only for the web UI)

```bash
cd web
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running

You can use any layer independently.

### CLI only

```bash
python cli/main.py --city "Cugnaux 31270" --type all --radius 2000 --export prospects.csv
```

### Full stack (CLI + API + frontend)

```bash
# Terminal 1 — backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — frontend
cd web && npm run dev
# open http://localhost:3000
```

The first run hits Google; subsequent runs read from the SQLite cache (TTL
30 days by default).

## CLI usage

```bash
python cli/main.py --city "Cugnaux 31270" --type all --radius 2000 --export prospects.csv
```

### Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--city` | yes | City or address (e.g. `"Cugnaux 31270"`) |
| `--type` | no | `restaurant`, `bar`, `retail`, `services`, `all` (default: `all`) |
| `--radius` | no | Search radius in meters (default: `2000`) |
| `--export` | no | Output path for `.csv` or `.json` |
| `--limit` | no | Limit the number of prospects displayed/exported |
| `--min-score` | no | Filter out prospects below this score (0-100) |
| `--refresh` | no | Bypass the cache and force a fresh API call |
| `--ttl-days` | no | Cache freshness window in days (default: `30`) |
| `--no-display` | no | Skip the rich table (handy with `--export`) |

Legacy French aliases are still accepted for `--city`, `--radius`, and the
`commerce` / `service` type values.

### Exemples

```bash
# All businesses in Cugnaux within a 2 km radius, export CSV
python cli/main.py --city "Cugnaux 31270" --type all --radius 2000 --export prospects.csv

# Only priority restaurants (>= 70/100)
python cli/main.py --city "Toulouse" --type restaurant --min-score 70

# Top 20 services around Blagnac, export JSON, no display
python cli/main.py --city "Blagnac" --type services --radius 3000 --limit 20 --export top.json --no-display

# Force a fresh API call (ignore cache)
python cli/main.py --city "Cugnaux 31270" --refresh
```

## Caching (`prospects.db`)

A local SQLite file at the repo root caches three things:

- `searches` — keyed by `(city, type, radius)` with a `fetched_at` timestamp.
- `prospects` — raw Place Details JSON keyed by `place_id`.
- `lead_status` — your follow-up data per prospect (status + notes), used by
  the web UI's kanban.

A search hit younger than `--ttl-days` (default 30) returns the cached
prospects with **zero API calls**. The CLI also runs without
`GOOGLE_API_KEY` when serving from cache. Override the path with
`PROSPECTMAP_DB=/some/other.db`.

## HTTP API

```bash
uvicorn api.main:app --reload --port 8000
# docs at http://localhost:8000/docs
```

| Method | Path                          | Notes |
| ------ | ----------------------------- | ----- |
| GET    | `/api/health`                 | Liveness |
| GET    | `/api/prospects`              | Filters: `status`, `priority`, `min_score` |
| GET    | `/api/prospects/{place_id}`   | 404 on unknown |
| PATCH  | `/api/prospects/{place_id}`   | Body `{status?, notes?}` — `null` clears, absent keeps |
| GET    | `/api/searches`               | Cached search history, newest first |
| POST   | `/api/searches`               | Trigger a search (cache-first then API) |

CORS is restricted to `http://localhost:3000`.

## Frontend

```bash
cd web
npm run dev      # http://localhost:3000
npm run build
npx tsc --noEmit
```

Four routes:

- **`/`** — Dashboard. Search form (POST `/api/searches`), priority counts,
  cached-search history.
- **`/map`** — Leaflet + OpenStreetMap, pins colored by priority, popup with
  contact info.
- **`/prospects`** — Filterable / sortable table.
- **`/kanban`** — Drag a card between status columns (NEW → CONTACTED →
  QUALIFIED → WON / LOST). Click the name to edit notes. Optimistic UI.

## Scoring

Each prospect is scored out of **100 points**:

| Criterion | Points |
| --- | ---: |
| No website | +50 |
| Rating >= 4.0 | +20 |
| At least 50 reviews | +15 |
| At least 100 reviews | +15 |

Buckets:

- **HIGH**: score >= 70
- **MEDIUM**: score >= 40
- **LOW**: score < 40

Thresholds and weights live in `cli/config.py` (`SCORING`,
`PRIORITY_THRESHOLDS`).

## Structure

```
ProspectMap/
├── cli/
│   ├── main.py        # argparse entry point, rich display
│   ├── places.py      # Google Places API wrapper
│   ├── cache.py       # SQLite cache (searches + prospects + lead_status)
│   ├── leads.py       # lead_status operations
│   ├── scorer.py      # 100-point scoring + normalization
│   ├── exporter.py    # CSV / JSON export
│   └── config.py      # .env loading + constants
├── api/
│   ├── main.py        # FastAPI app
│   ├── routes/        # prospects.py, searches.py
│   ├── schemas.py     # Pydantic models
│   ├── serializers.py # raw place + lead_status -> API dict
│   └── deps.py        # per-request SQLite connection
├── web/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # navbar, search-form, map-view, table, kanban, ui/
│   └── lib/           # api client, hooks, types
├── prospects.db       # SQLite cache (gitignored)
├── .env.example
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Python CLI (search, scoring, CSV/JSON export)
- [x] SQLite cache (avoid duplicate API calls, TTL-based)
- [x] FastAPI backend
- [x] Next.js frontend (dashboard, map, table, kanban)
- [ ] Polish: CSV export from the UI, dark-mode toggle, replay-able saved searches
