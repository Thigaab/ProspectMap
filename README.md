# ProspectMap

Lead generation tool for local businesses that do not have, or have very little,
web presence. It uses the Google Places API to find businesses around a city,
scores them out of 100, and exports the best leads to CSV or JSON.

## Stack

- **Python CLI** (`cli/`) - first building block, already usable on its own
- **React/Next.js frontend** - planned for a later phase

## Installation

```bash
# 1. Clone and enter the project
git clone <repo> ProspectMap && cd ProspectMap

# 2. Create a Python 3.11+ virtual environment
python3 -m venv .venv

# Activation depends on your shell:
source .venv/bin/activate.fish   # fish
# source .venv/bin/activate       # bash / zsh
# .venv\Scripts\activate          # Windows (cmd) / .ps1 for PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the API key
cp .env.example .env
# then edit .env and paste your GOOGLE_API_KEY
```

### Enable the required Google APIs

In the Google Cloud console, for the project where your key was created, enable:

- **Places API** (Text Search, Nearby Search, Place Details)
- **Geocoding API** (city to coordinates)

## Usage

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

Legacy French aliases are still accepted for `--city`, `--radius`, and the
`commerce` / `service` type values.

### Exemples

```bash
# All businesses in Cugnaux within a 2 km radius, export CSV
python cli/main.py --city "Cugnaux 31270" --type all --radius 2000 --export prospects.csv

# Only priority restaurants (>= 70/100)
python cli/main.py --city "Toulouse" --type restaurant --min-score 70

# Top 20 services around Blagnac, export JSON
python cli/main.py --city "Blagnac" --type services --radius 3000 --limit 20 --export top.json
```

## Scoring

Each prospect is scored out of **100 points**:

| Criterion | Points |
| --- | ---: |
| No website | +50 |
| Rating >= 4.0 | +20 |
| At least 50 reviews | +15 |
| At least 100 reviews | +15 |

Prospects are then split into three priorities:

- **HIGH**: score >= 70
- **MEDIUM**: score >= 40
- **LOW**: score < 40

## Structure

```
ProspectMap/
├── cli/
│   ├── main.py        # argparse entry point
│   ├── places.py      # Google Places API wrapper
│   ├── scorer.py      # scoring logic
│   ├── exporter.py    # CSV / JSON export
│   └── config.py      # .env + constants
├── .env.example
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Python CLI (search, scoring, export)
- [ ] React/Next.js frontend (interactive map, filters, lead tracking)
