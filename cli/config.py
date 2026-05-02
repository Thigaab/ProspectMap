"""Configuration loading and shared constants."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"
TEXT_SEARCH_URL = f"{PLACES_BASE_URL}/textsearch/json"
NEARBY_SEARCH_URL = f"{PLACES_BASE_URL}/nearbysearch/json"
PLACE_DETAILS_URL = f"{PLACES_BASE_URL}/details/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

TYPE_MAPPING = {
    "restaurant": ["restaurant"],
    "bar": ["bar", "cafe"],
    "retail": [
        "store",
        "clothing_store",
        "shoe_store",
        "florist",
        "bakery",
        "book_store",
        "jewelry_store",
    ],
    "services": [
        "beauty_salon",
        "hair_care",
        "plumber",
        "electrician",
        "car_repair",
        "laundry",
    ],
    "all": [
        "restaurant",
        "bar",
        "cafe",
        "store",
        "bakery",
        "beauty_salon",
        "hair_care",
        "florist",
    ],
}

TYPE_ALIASES = {
    "commerce": "retail",
    "service": "services",
}

DEFAULT_RADIUS = 2000
RATE_LIMIT_DELAY = 2.0  # Google's next_page_token is only valid after ~2s
DETAIL_DELAY = 0.05

DB_PATH = "prospects.db"
DEFAULT_TTL_DAYS = 30

DETAIL_FIELDS = [
    "name",
    "formatted_address",
    "formatted_phone_number",
    "international_phone_number",
    "website",
    "rating",
    "user_ratings_total",
    "opening_hours",
    "place_id",
    "url",
    "types",
    "business_status",
    "geometry/location",
]

SCORING = {
    # Web-presence sub-score (0–70). 70 = no site or effectively absent;
    # individual weak-site penalties stack but are capped at no_website_max
    # so a healthy site never beats a missing one.
    # Raising this cap makes "no website" businesses HIGH priority by default.
    "no_website_max": 70,
    "weak_web_social_only": 55,
    "weak_web_no_https": 12,
    "weak_web_no_viewport": 12,
    "weak_web_free_hosting": 20,
    "rating_4_plus": 15,
    "reviews_50_plus": 8,
    "reviews_100_plus": 7,
    # max total: 70 + 15 + 8 + 7 = 100
}

PRIORITY_THRESHOLDS = {"HIGH": 70, "MEDIUM": 35}

# Keywords (lowercase) that identify chain stores / franchises to exclude.
# Matching is partial and case-insensitive: "Carrefour City" is excluded
# because it contains "carrefour".
CHAIN_BLOCKLIST: frozenset[str] = frozenset({
    # Grande distribution alimentaire
    "carrefour", "leclerc", "intermarché", "intermarch",
    "auchan", "lidl", "aldi", "super u", "hyper u",
    "monoprix", "franprix", "picard", "biocoop", "naturalia",
    "système u", "systeme u", "netto", "leader price",
    "casino supermarché", "vival", "spar",
    # Bricolage / jardinage
    "leroy merlin", "castorama", "brico dépôt", "brico depot",
    "bricorama", "mr bricolage", "weldom", "jardiland", "truffaut",
    # Ameublement / déco
    "ikea", "maisons du monde", "but", "conforama", "fly", "atlas",
    # Vêtements / mode
    "zara", "h&m", "uniqlo", "primark", "kiabi",
    "jules", "celio", "promod", "jennyfer", "mango",
    "pull&bear", "bershka", "stradivarius", "gap",
    # Chaussures
    "chaussea", "andre ", "bata ", "eram ", "minelli",
    "san marina", "bocage",
    # Sport
    "decathlon", "go sport", "sport 2000", "intersport",
    # Electronique / télécom
    "fnac", "darty", "boulanger", "orange store",
    "sfr ", "bouygues telecom", "free mobile", "sosh",
    # Restauration rapide
    "mcdonald", "burger king", "kfc ", "subway", "quick ",
    "five guys", "domino", "pizza hut", "flunch",
    "hippopotamus", "courtepaille", "starbucks",
    "columbus café", "brioche dorée", "paul ",
    "la mie câline", "pomme de pain",
    # Beauté / hygiène chaînes
    "yves rocher", "l'occitane", "nocibé", "sephora",
    "marionnaud", "body shop", "the body shop",
    # Optique chaînes
    "krys ", "alain afflelou", "atol ", "grand optical",
    "générale d'optique", "optical center",
    # Automobile
    "norauto", "midas ", "speedy ", "feu vert", "euromaster",
    "point s ", "renault ", "peugeot ", "citroën ", "volkswagen ",
    # Banques (rarement remontées mais au cas où)
    "bnp paribas", "société générale", "crédit agricole",
    "caisse d'épargne", "banque populaire", "crédit mutuel",
    # Hôtels chaînes
    "ibis ", "novotel", "mercure ", "sofitel",
    "b&b hotel", "premiere classe", "campanile", "kyriad",
    "formule 1", "holiday inn",
})


def is_chain(name: str) -> bool:
    """Return True if the business name matches a known chain keyword."""
    lowered = name.lower()
    return any(keyword in lowered for keyword in CHAIN_BLOCKLIST)

WEB_AUDIT_TIMEOUT = 5.0
WEB_AUDIT_WORKERS = 10
WEB_AUDIT_TTL_DAYS = 30
