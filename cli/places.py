"""Wrapper around the Google Places API (Text Search, Nearby Search, Place Details)."""
import time
from typing import Callable, Optional

import requests

import config


class PlacesAPIError(Exception):
    """Error returned by the Google Places API."""


class PlacesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GOOGLE_API_KEY
        if not self.api_key:
            raise PlacesAPIError(
                "GOOGLE_API_KEY is missing - set it in a .env file"
            )
        self.session = requests.Session()

    def geocode(self, address: str) -> tuple[float, float]:
        """Convert a text address into coordinates (lat, lng)."""
        data = self._get(config.GEOCODE_URL, {"address": address, "key": self.api_key})
        results = data.get("results", [])
        if not results:
            raise PlacesAPIError(f"No coordinates found for '{address}'")
        loc = results[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    def nearby_search(
        self, lat: float, lng: float, radius: int, place_type: str
    ) -> list[dict]:
        """Paginated nearby search for a given Google Places type."""
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": place_type,
            "key": self.api_key,
        }
        return self._paginate(config.NEARBY_SEARCH_URL, params)

    def text_search(self, query: str) -> list[dict]:
        """Paginated text search."""
        params = {"query": query, "key": self.api_key}
        return self._paginate(config.TEXT_SEARCH_URL, params)

    def place_details(self, place_id: str) -> dict:
        """Fetch enriched details for a place."""
        params = {
            "place_id": place_id,
            "fields": ",".join(config.DETAIL_FIELDS),
            "language": "fr",
            "key": self.api_key,
        }
        data = self._get(config.PLACE_DETAILS_URL, params)
        return data.get("result", {})

    def search_prospects(
        self,
        city: str,
        type_filter: str,
        radius: int,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> list[dict]:
        """Full pipeline: geocode -> nearby for each type -> deduplicated details."""
        normalized_type = config.TYPE_ALIASES.get(type_filter, type_filter)
        types = config.TYPE_MAPPING.get(normalized_type, [normalized_type])
        latitude, longitude = self.geocode(city)

        seen: set[str] = set()
        raw_places: list[dict] = []
        for t in types:
            if on_progress:
                on_progress(f"Searching {t}", 0, 0)
            for raw in self.nearby_search(latitude, longitude, radius, t):
                pid = raw.get("place_id")
                if pid and pid not in seen and not config.is_chain(raw.get("name", "")):
                    seen.add(pid)
                    raw_places.append(raw)

        prospects: list[dict] = []
        total = len(raw_places)
        for idx, raw in enumerate(raw_places, 1):
            if on_progress:
                on_progress("Details", idx, total)
            time.sleep(config.DETAIL_DELAY)
            details = self.place_details(raw["place_id"])
            if details and details.get("business_status", "OPERATIONAL") == "OPERATIONAL":
                prospects.append(details)
        return prospects

    def _paginate(self, url: str, params: dict) -> list[dict]:
        results: list[dict] = []
        current_params = dict(params)
        while True:
            data = self._get(url, current_params)
            results.extend(data.get("results", []))
            next_token = data.get("next_page_token")
            if not next_token:
                break
            time.sleep(config.RATE_LIMIT_DELAY)
            current_params = {"pagetoken": next_token, "key": self.api_key}
        return results

    def _get(self, url: str, params: dict) -> dict:
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            raise PlacesAPIError(f"Network error: {e}") from e

        data = response.json()
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            error_msg = data.get("error_message", "")
            raise PlacesAPIError(f"Google API status={status} {error_msg}".strip())
        return data
