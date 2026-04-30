"""Score prospects on a 100-point scale and normalize them for export."""
from typing import Optional

import config
import web_audit


def _website_score(place: dict, audit: Optional[dict], audited: bool) -> tuple[int, list[str]]:
    """Return (points, reasons) for the web-presence sub-score.

    `audited=True` means we ran (or at least cached) the audit step, so
    `audit` reflects reality. `audited=False` means we skipped the web
    check — fall back to the binary "has a website field" heuristic.
    """
    has_url = bool(place.get("website"))
    if not audited:
        if not has_url:
            return config.SCORING["no_website_max"], ["no website"]
        return 0, []

    # audited path: audit is None when there's no website at all
    audit_for_score = audit if has_url else None
    points = web_audit.quality_score(audit_for_score)
    reasons = web_audit.quality_reasons(audit_for_score) if points > 0 else []
    return points, reasons


def score_prospect(
    place: dict,
    audit: Optional[dict] = None,
    audited: bool = False,
) -> dict:
    """Compute the score, priority, and reasons for a place."""
    score = 0
    reasons: list[str] = []

    web_pts, web_reasons = _website_score(place, audit, audited)
    score += web_pts
    reasons.extend(web_reasons)

    rating = place.get("rating") or 0
    if rating >= 4.0:
        score += config.SCORING["rating_4_plus"]
        reasons.append(f"rating {rating}")

    reviews = place.get("user_ratings_total") or 0
    if reviews >= 50:
        score += config.SCORING["reviews_50_plus"]
        reasons.append(f"{reviews} reviews")
    if reviews >= 100:
        score += config.SCORING["reviews_100_plus"]

    if score >= config.PRIORITY_THRESHOLDS["HIGH"]:
        priority = "HIGH"
    elif score >= config.PRIORITY_THRESHOLDS["MEDIUM"]:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {"score": score, "priority": priority, "reasons": reasons}


def to_prospect(
    place: dict,
    audit: Optional[dict] = None,
    audited: bool = False,
) -> dict:
    """Convert a raw Place Details dict into a normalized, scored prospect."""
    scoring = score_prospect(place, audit=audit, audited=audited)
    hours = (place.get("opening_hours") or {}).get("weekday_text") or []
    location = (place.get("geometry") or {}).get("location") or {}
    return {
        "place_id": place.get("place_id"),
        "name": place.get("name"),
        "address": place.get("formatted_address"),
        "phone": place.get("formatted_phone_number")
        or place.get("international_phone_number"),
        "website": place.get("website"),
        "rating": place.get("rating"),
        "review_count": place.get("user_ratings_total") or 0,
        "hours": hours,
        "google_url": place.get("url"),
        "types": place.get("types") or [],
        "lat": location.get("lat"),
        "lng": location.get("lng"),
        "score": scoring["score"],
        "priority": scoring["priority"],
        "reasons": scoring["reasons"],
        "web_audit": audit if audited else None,
    }


def enrich(
    places: list[dict],
    audits: Optional[dict[str, Optional[dict]]] = None,
) -> list[dict]:
    """Score and sort by descending score.

    `audits` maps `place_id -> audit dict (or None)`. When provided, the
    web-presence sub-score uses it; when omitted, we fall back to the
    binary "has a website" heuristic so callers can opt out cheaply.
    """
    audited = audits is not None
    audits = audits or {}
    prospects = [
        to_prospect(p, audit=audits.get(p.get("place_id")), audited=audited)
        for p in places
    ]
    prospects.sort(key=lambda x: (x["score"], x["review_count"]), reverse=True)
    return prospects
