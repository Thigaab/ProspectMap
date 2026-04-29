"""Search history + trigger a new search (cache-first, then API)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from .. import _bootstrap  # noqa: F401
from ..deps import get_cache
from ..schemas import CachedSearch, SearchRequest, SearchResponse
from ..serializers import serialize_places

from cache import Cache  # type: ignore
import config  # type: ignore
from places import PlacesAPIError, PlacesClient  # type: ignore

router = APIRouter(prefix="/api/searches", tags=["searches"])


@router.get("", response_model=list[CachedSearch])
def list_searches(cache: Cache = Depends(get_cache)):
    rows = cache.conn.execute(
        "SELECT s.city, s.type_filter, s.radius, s.fetched_at, "
        "       COUNT(sr.place_id) AS prospect_count "
        "FROM searches s "
        "LEFT JOIN search_results sr ON sr.search_id = s.id "
        "GROUP BY s.id "
        "ORDER BY s.fetched_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=SearchResponse)
def create_search(req: SearchRequest, cache: Cache = Depends(get_cache)):
    type_filter = config.TYPE_ALIASES.get(req.type_filter, req.type_filter)
    if type_filter not in config.TYPE_MAPPING:
        raise HTTPException(400, f"Unknown type_filter '{req.type_filter}'")

    if not req.refresh:
        cached = cache.get_search(req.city, type_filter, req.radius, req.ttl_days)
        if cached is not None:
            raw, fetched_at = cached
            return SearchResponse(
                cached=True,
                fetched_at=fetched_at.isoformat(),
                prospects=serialize_places(raw, cache),
            )

    if not config.GOOGLE_API_KEY:
        raise HTTPException(
            500, "GOOGLE_API_KEY is missing — set it in the server's .env file."
        )

    try:
        client = PlacesClient()
        raw = client.search_prospects(req.city, type_filter, req.radius)
    except PlacesAPIError as e:
        raise HTTPException(502, f"Google Places API error: {e}")

    cache.save_search(req.city, type_filter, req.radius, raw)
    return SearchResponse(
        cached=False,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        prospects=serialize_places(raw, cache),
    )
