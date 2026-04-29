# ProspectMap — Context for Claude

Lead-generation tool for local businesses with no/weak web presence. Uses
Google Places API to find businesses, scores them out of 100, and exports the
best leads to CSV or JSON.

## Stack

- **Python CLI** (`cli/`) — done first, must stay usable standalone.
- **React/Next.js frontend** — planned, not started. Do **not** scaffold the
  frontend until the user explicitly asks for it.

## Conventions

- **Code, identifiers, docstrings, comments, and CLI flags are in English.**
  An earlier draft was in French; everything was rewritten to English. Stay
  consistent — do not reintroduce French names.
- **Legacy French aliases are kept on purpose** in `cli/main.py`:
  - `--ville` is an alias for `--city`
  - `--rayon` is an alias for `--radius`
  - `--type commerce` and `--type service` map to `retail` / `services` via
    `config.TYPE_ALIASES`
  Do not remove these; they preserve backward compatibility with the original
  brief.
- README and user-facing strings are in English. Section titles like
  "Exemples" that remain in French in the README are intentional flavor —
  leave them unless asked.

## Project structure

```
ProspectMap/
├── cli/
│   ├── main.py        # argparse entry point, rich display
│   ├── places.py      # Google Places API wrapper (geocode, nearby, details)
│   ├── cache.py       # SQLite cache (searches + prospects, TTL-based)
│   ├── scorer.py      # 100-point scoring + normalization
│   ├── exporter.py    # CSV / JSON export
│   └── config.py      # .env loading + constants (URLs, type mapping, scoring)
├── prospects.db       # local SQLite cache (gitignored)
├── .env.example
├── requirements.txt
├── README.md
└── CLAUDE.md          # this file
```

No `__init__.py` — `main.py` is run directly with `python cli/main.py`, which
puts `cli/` on `sys.path` so flat `import config` / `from places import ...`
work.

## Scoring (business rule, do not silently change)

Per prospect, out of 100:

| Criterion              | Points |
| ---------------------- | -----: |
| No website             |    +50 |
| Rating ≥ 4.0           |    +20 |
| ≥ 50 reviews           |    +15 |
| ≥ 100 reviews          |    +15 |

Priority buckets: `HIGH ≥ 70`, `MEDIUM ≥ 40`, else `LOW`.
All thresholds and weights live in `cli/config.py` (`SCORING`,
`PRIORITY_THRESHOLDS`).

## Caching (avoid duplicate API calls)

`cli/cache.py` is a SQLite layer (`prospects.db` at the repo root, gitignored
via `*.db`). Three tables:

- `searches` — keyed by `(city, type_filter, radius)`, stores `fetched_at`.
- `prospects` — keyed by `place_id`, stores the **raw** Place Details JSON.
- `search_results` — link table between the two (a place can belong to
  several searches).

Flow in `main.py`:

1. Open the cache.
2. If `--refresh` is **not** set, look up `(city, type_filter, radius)` and
   compare `fetched_at` against `--ttl-days` (default 30).
3. **Hit** → rehydrate the prospect list from SQLite, no API call, no
   `GOOGLE_API_KEY` required.
4. **Miss / stale / `--refresh`** → run the full pipeline in `places.py` and
   `cache.save_search(...)` upserts the search and all prospects.

Saving a search re-creates the `search_results` rows for that search but
keeps existing `prospects` entries (so place data survives across searches
and keeps its own `fetched_at`).

Relevant flags:
- `--refresh` — force a fresh API call (still updates the cache).
- `--ttl-days N` — override the freshness window.
- `--no-display` — skip the rich table (handy with `--export`).

## Google Places integration — gotchas

- Uses the **legacy Places API** (`maps.googleapis.com/maps/api/place/...`),
  not the new `places.googleapis.com/v1/...`. Both Places API **and**
  Geocoding API must be enabled on the GCP project.
- `next_page_token` returned by Google is only valid after ~2 seconds — see
  `config.RATE_LIMIT_DELAY` and `PlacesClient._paginate`. Do not lower this.
- Pipeline in `PlacesClient.search_prospects`:
  1. geocode the city to lat/lng
  2. for each Google type in `TYPE_MAPPING[type_filter]`, paginated nearby
     search
  3. dedupe by `place_id` **before** calling Place Details (paid endpoint)
  4. fetch details, drop entries where `business_status != OPERATIONAL`
- Place Details fields requested are listed in `config.DETAIL_FIELDS`. Adding
  a typo there will cause `INVALID_REQUEST` from Google.

## Running it

User shell is **fish** (`/bin/fish`). Activate the venv with:

```fish
source .venv/bin/activate.fish
```

Typical run:

```bash
python cli/main.py --city "Cugnaux 31270" --type all --radius 2000 --export prospects.csv
```

Useful flags: `--limit N`, `--min-score N` (filter before display/export).

Exit codes: `0` ok, `1` config error (missing key), `2` API error,
`3` export error, `130` Ctrl+C.

## Dependencies

Python 3.11+. `requirements.txt`:
- `requests` — HTTP
- `python-dotenv` — `.env` loading
- `rich` — table + progress display

No test suite yet.

## Roadmap

- [x] Python CLI (search, scoring, CSV/JSON export)
- [ ] Next.js frontend: interactive map, filters, lead-tracking UI
  (kanban / status per prospect). To be discussed before scaffolding.

## Working with the user

- User: Thibaut, French speaker, comfortable in English code.
- Do not commit unless explicitly asked.
- Do not push, force-push, or open PRs unless explicitly asked.
- `.env` is gitignored; never commit it. `*.csv` / `*.json` are gitignored
  too (see `.gitignore`) — they're treated as local exports.
