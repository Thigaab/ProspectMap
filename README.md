# LeadLocal (ProspectMap)

Outil de prospection de commerces locaux qui n'ont pas (ou peu) de site web.
Utilise l'API Google Places pour trouver les établissements autour d'une ville,
les score sur 100 et exporte les meilleurs leads en CSV ou JSON.

## Stack

- **CLI Python** (`cli/`) — première brique, fonctionnelle en autonomie
- **Frontend React/Next.js** — viendra dans un second temps

## Installation

```bash
# 1. Cloner et entrer dans le projet
git clone <repo> ProspectMap && cd ProspectMap

# 2. Créer un venv Python 3.11+
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la clé API
cp .env.example .env
# puis éditer .env et y coller votre GOOGLE_API_KEY
```

### Activer les API Google nécessaires

Dans la console Google Cloud, sur le projet où votre clé est créée, activez :

- **Places API** (Text Search, Nearby Search, Place Details)
- **Geocoding API** (conversion ville → coordonnées)

## Utilisation

```bash
python cli/main.py --ville "Cugnaux 31270" --type all --rayon 2000 --export prospects.csv
```

### Arguments

| Argument | Requis | Description |
| --- | --- | --- |
| `--ville` | oui | Ville ou adresse (ex. `"Cugnaux 31270"`) |
| `--type` | non | `restaurant`, `bar`, `commerce`, `service`, `all` (défaut : `all`) |
| `--rayon` | non | Rayon de recherche en mètres (défaut : `2000`) |
| `--export` | non | Chemin de sortie `.csv` ou `.json` |
| `--limit` | non | Limite le nombre de prospects affichés / exportés |
| `--min-score` | non | Filtre les prospects sous ce score (0-100) |

### Exemples

```bash
# Tous les commerces de Cugnaux dans un rayon de 2 km, export CSV
python cli/main.py --ville "Cugnaux 31270" --type all --rayon 2000 --export prospects.csv

# Seulement les restaurants prioritaires (>= 70/100)
python cli/main.py --ville "Toulouse" --type restaurant --min-score 70

# Top 20 services autour de Blagnac, export JSON
python cli/main.py --ville "Blagnac" --type service --rayon 3000 --limit 20 --export top.json
```

## Scoring

Chaque prospect est noté sur **100 points** :

| Critère | Points |
| --- | ---: |
| Pas de site web | +50 |
| Note ≥ 4.0 | +20 |
| Au moins 50 avis | +15 |
| Au moins 100 avis | +15 |

Les prospects sont ensuite répartis en trois priorités :

- **HAUTE** : score ≥ 70
- **MOYENNE** : score ≥ 40
- **BASSE** : score < 40

## Structure

```
ProspectMap/
├── cli/
│   ├── main.py        # Point d'entrée argparse
│   ├── places.py      # Wrapper Google Places API
│   ├── scorer.py      # Logique de scoring
│   ├── exporter.py    # Export CSV / JSON
│   └── config.py      # .env + constantes
├── .env.example
├── requirements.txt
└── README.md
```

## Roadmap

- [x] CLI Python (recherche, scoring, export)
- [ ] Frontend React/Next.js (carte interactive, filtres, suivi des leads)
