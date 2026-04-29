"""Score prospects on a 100-point scale and normalize them for export."""
import config


def score_prospect(place: dict) -> dict:
    """Compute the score, priority, and reasons for a place."""
    score = 0
    reasons: list[str] = []

    if not place.get("website"):
        score += config.SCORING["no_website"]
        reasons.append("no website")

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


def to_prospect(place: dict) -> dict:
    """Convert a raw Place Details dict into a normalized, scored prospect."""
    scoring = score_prospect(place)
    hours = (place.get("opening_hours") or {}).get("weekday_text") or []
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
        "score": scoring["score"],
        "priority": scoring["priority"],
        "reasons": scoring["reasons"],
    }


def enrich(places: list[dict]) -> list[dict]:
    """Score and sort by descending score."""
    prospects = [to_prospect(p) for p in places]
    prospects.sort(key=lambda x: (x["score"], x["review_count"]), reverse=True)
    return prospects
