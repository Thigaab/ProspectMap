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
]

SCORING = {
    "no_website": 50,
    "rating_4_plus": 20,
    "reviews_50_plus": 15,
    "reviews_100_plus": 15,
}

PRIORITY_THRESHOLDS = {"HIGH": 70, "MEDIUM": 40}
