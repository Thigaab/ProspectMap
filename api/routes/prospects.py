"""Prospect listing, detail, and lead-status updates."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from .. import _bootstrap  # noqa: F401
from ..deps import get_cache
from ..schemas import Prospect, StatusUpdate
from ..serializers import load_all_prospects, serialize_places

from cache import Cache  # type: ignore
import leads  # type: ignore
from scorer import to_prospect  # type: ignore

router = APIRouter(prefix="/api/prospects", tags=["prospects"])


@router.get("", response_model=list[Prospect])
def list_prospects(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    min_score: int = 0,
    cache: Cache = Depends(get_cache),
):
    raw_places = load_all_prospects(cache)
    prospects = serialize_places(raw_places, cache)

    if min_score:
        prospects = [p for p in prospects if p["score"] >= min_score]
    if priority:
        prospects = [p for p in prospects if p["priority"] == priority.upper()]
    if status:
        prospects = [p for p in prospects if p["status"] == status.upper()]
    return prospects


@router.get("/{place_id}", response_model=Prospect)
def get_prospect(place_id: str, cache: Cache = Depends(get_cache)):
    row = cache.conn.execute(
        "SELECT raw FROM prospects WHERE place_id = ?", (place_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, f"Prospect '{place_id}' not found")

    raw = json.loads(row["raw"])
    base = to_prospect(raw)
    s = leads.get_status(cache.conn, place_id)
    return {
        **base,
        "status": s["status"] if s else "NEW",
        "notes": s["notes"] if s else None,
        "updated_at": s["updated_at"] if s else None,
    }


@router.patch("/{place_id}", response_model=Prospect)
def update_prospect(
    place_id: str,
    update: StatusUpdate,
    cache: Cache = Depends(get_cache),
):
    row = cache.conn.execute(
        "SELECT raw FROM prospects WHERE place_id = ?", (place_id,)
    ).fetchone()
    if not row:
        raise HTTPException(404, f"Prospect '{place_id}' not found")

    current = leads.get_status(cache.conn, place_id) or {
        "status": "NEW",
        "notes": None,
    }
    fields = update.model_fields_set  # which keys the client actually sent
    new_status = (
        update.status.upper()
        if "status" in fields and update.status
        else current["status"]
    )
    # Distinguish "field absent" (keep current) from "field = null" (clear).
    new_notes = update.notes if "notes" in fields else current["notes"]

    try:
        s = leads.set_status(cache.conn, place_id, new_status, new_notes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    raw = json.loads(row["raw"])
    base = to_prospect(raw)
    return {**base, **s}


@router.delete("/{place_id}", status_code=204)
def delete_prospect(place_id: str, cache: Cache = Depends(get_cache)):
    """Hard-delete a prospect (and its lead status / search links)."""
    if not cache.delete_prospect(place_id):
        raise HTTPException(404, f"Prospect '{place_id}' not found")
    return Response(status_code=204)
