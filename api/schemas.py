"""Pydantic schemas for the HTTP API."""
from typing import List, Optional

from pydantic import BaseModel, Field

from . import _bootstrap  # noqa: F401

import config  # type: ignore  # from cli/
from leads import VALID_STATUSES  # type: ignore  # from cli/


class Prospect(BaseModel):
    place_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: int = 0
    score: int
    priority: str
    reasons: List[str] = []
    google_url: Optional[str] = None
    types: List[str] = []
    hours: List[str] = []
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: str = "NEW"
    notes: Optional[str] = None
    updated_at: Optional[str] = None


class StatusUpdate(BaseModel):
    status: Optional[str] = Field(default=None, description=f"One of: {VALID_STATUSES}")
    notes: Optional[str] = None


class SearchRequest(BaseModel):
    city: str
    type_filter: str = "all"
    radius: int = config.DEFAULT_RADIUS
    refresh: bool = False
    ttl_days: int = config.DEFAULT_TTL_DAYS


class SearchResponse(BaseModel):
    cached: bool
    fetched_at: str
    prospects: List[Prospect]


class CachedSearch(BaseModel):
    id: int
    city: str
    type_filter: str
    radius: int
    fetched_at: str
    prospect_count: int
