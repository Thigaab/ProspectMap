"""Helpers that turn raw Place Details + lead status into API-ready dicts."""
import json
from typing import Iterable

from . import _bootstrap  # noqa: F401

from cache import Cache  # type: ignore  # from cli/
import leads  # type: ignore  # from cli/
from scorer import enrich  # type: ignore  # from cli/


def _attach_status(prospect: dict, statuses: dict[str, dict]) -> dict:
    s = statuses.get(prospect["place_id"])
    return {
        **prospect,
        "status": s["status"] if s else "NEW",
        "notes": s["notes"] if s else None,
        "updated_at": s["updated_at"] if s else None,
    }


def serialize_places(raw_places: Iterable[dict], cache: Cache) -> list[dict]:
    """Score + sort raw places, then merge user-owned status/notes."""
    enriched = enrich(list(raw_places))
    statuses = leads.list_statuses(cache.conn)
    return [_attach_status(p, statuses) for p in enriched]


def load_all_prospects(cache: Cache) -> list[dict]:
    rows = cache.conn.execute("SELECT raw FROM prospects").fetchall()
    return [json.loads(r["raw"]) for r in rows]
