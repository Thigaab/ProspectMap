"""Export des prospects au format CSV ou JSON."""
import csv
import json
from pathlib import Path

CSV_FIELDS = [
    "nom",
    "adresse",
    "telephone",
    "site_web",
    "note",
    "nb_avis",
    "score",
    "priorite",
    "raisons",
    "google_url",
    "place_id",
]


def export(prospects: list[dict], path: str) -> str:
    """Exporte la liste de prospects vers un fichier .csv ou .json."""
    target = Path(path)
    suffix = target.suffix.lower()
    if suffix == ".json":
        return _export_json(prospects, target)
    if suffix == ".csv":
        return _export_csv(prospects, target)
    raise ValueError(
        f"Format non supporté: '{suffix}'. Utilisez .csv ou .json."
    )


def _export_csv(prospects: list[dict], path: Path) -> str:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for p in prospects:
            writer.writerow({k: _flatten(p.get(k)) for k in CSV_FIELDS})
    return str(path)


def _export_json(prospects: list[dict], path: Path) -> str:
    with path.open("w", encoding="utf-8") as f:
        json.dump(prospects, f, ensure_ascii=False, indent=2)
    return str(path)


def _flatten(value):
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    if value is None:
        return ""
    return value
