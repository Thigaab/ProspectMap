"""Scoring des prospects sur 100 points + transformation en lignes exploitables."""
import config


def score_prospect(place: dict) -> dict:
    """Calcule le score, la priorité et les raisons pour un établissement."""
    score = 0
    reasons: list[str] = []

    if not place.get("website"):
        score += config.SCORING["no_website"]
        reasons.append("pas de site web")

    rating = place.get("rating") or 0
    if rating >= 4.0:
        score += config.SCORING["rating_4_plus"]
        reasons.append(f"note {rating}")

    reviews = place.get("user_ratings_total") or 0
    if reviews >= 50:
        score += config.SCORING["reviews_50_plus"]
        reasons.append(f"{reviews} avis")
    if reviews >= 100:
        score += config.SCORING["reviews_100_plus"]

    if score >= config.PRIORITY_THRESHOLDS["HAUTE"]:
        priority = "HAUTE"
    elif score >= config.PRIORITY_THRESHOLDS["MOYENNE"]:
        priority = "MOYENNE"
    else:
        priority = "BASSE"

    return {"score": score, "priorite": priority, "raisons": reasons}


def to_prospect(place: dict) -> dict:
    """Convertit un dict Place Details brut en prospect normalisé et scoré."""
    s = score_prospect(place)
    horaires = (place.get("opening_hours") or {}).get("weekday_text") or []
    return {
        "place_id": place.get("place_id"),
        "nom": place.get("name"),
        "adresse": place.get("formatted_address"),
        "telephone": place.get("formatted_phone_number")
        or place.get("international_phone_number"),
        "site_web": place.get("website"),
        "note": place.get("rating"),
        "nb_avis": place.get("user_ratings_total") or 0,
        "horaires": horaires,
        "google_url": place.get("url"),
        "types": place.get("types") or [],
        "score": s["score"],
        "priorite": s["priorite"],
        "raisons": s["raisons"],
    }


def enrich(places: list[dict]) -> list[dict]:
    """Score puis trie par score décroissant."""
    prospects = [to_prospect(p) for p in places]
    prospects.sort(key=lambda x: (x["score"], x["nb_avis"]), reverse=True)
    return prospects
