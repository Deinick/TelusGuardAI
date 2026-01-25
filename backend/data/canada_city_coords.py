"""
Canada-wide city → (latitude, longitude) mapping.

Used for lightweight geolocation when no external geocoding
service is available.

Covers major population centers across all provinces & territories.
"""

from typing import Dict, Tuple
import unicodedata


# -------------------------
# City coordinates
# -------------------------

CANADA_CITY_COORDS: Dict[str, Tuple[float, float]] = {

    # =====================
    # Ontario
    # =====================
    "toronto": (43.6532, -79.3832),
    "mississauga": (43.5890, -79.6441),
    "brampton": (43.7315, -79.7624),
    "hamilton": (43.2557, -79.8711),
    "ottawa": (45.4215, -75.6972),
    "london": (42.9849, -81.2453),
    "kitchener": (43.4516, -80.4925),
    "waterloo": (43.4643, -80.5204),
    "cambridge": (43.3616, -80.3144),
    "guelph": (43.5448, -80.2482),
    "windsor": (42.3149, -83.0364),
    "kingston": (44.2312, -76.4860),
    "barrie": (44.3894, -79.6903),
    "oshawa": (43.8971, -78.8658),
    "peterborough": (44.3091, -78.3197),
    "sudbury": (46.4917, -80.9930),
    "thunder bay": (48.3809, -89.2477),
    "sault ste marie": (46.5219, -84.3461),
    "north bay": (46.3091, -79.4608),

    # =====================
    # Quebec
    # =====================
    "montreal": (45.5017, -73.5673),
    "quebec city": (46.8139, -71.2080),
    "laval": (45.6066, -73.7124),
    "gatineau": (45.4765, -75.7013),
    "longueuil": (45.5312, -73.5180),
    "sherbrooke": (45.4042, -71.8929),
    "trois-rivieres": (46.3430, -72.5430),
    "saguenay": (48.4284, -71.0686),
    "levis": (46.8033, -71.1779),
    "drummondville": (45.8834, -72.4824),
    "rimouski": (48.4488, -68.5230),

    # =====================
    # British Columbia
    # =====================
    "vancouver": (49.2827, -123.1207),
    "burnaby": (49.2488, -122.9805),
    "surrey": (49.1913, -122.8490),
    "richmond": (49.1666, -123.1336),
    "coquitlam": (49.2838, -122.7932),
    "new westminster": (49.2057, -122.9110),
    "victoria": (48.4284, -123.3656),
    "nanaimo": (49.1659, -123.9401),
    "kelowna": (49.8880, -119.4960),
    "kamloops": (50.6745, -120.3273),
    "prince george": (53.9171, -122.7497),
    "abbotsford": (49.0504, -122.3045),
    "chilliwack": (49.1579, -121.9515),

    # =====================
    # Alberta
    # =====================
    "calgary": (51.0447, -114.0719),
    "edmonton": (53.5461, -113.4938),
    "red deer": (52.2681, -113.8112),
    "lethbridge": (49.6956, -112.8451),
    "medicine hat": (50.0405, -110.6776),
    "fort mcmurray": (56.7264, -111.3803),
    "grand prairie": (55.1707, -118.7947),
    "aerdrie": (51.2917, -114.0144),

    # =====================
    # Manitoba
    # =====================
    "winnipeg": (49.8951, -97.1384),
    "brandon": (49.8485, -99.9501),
    "steinbach": (49.5258, -96.6840),
    "thompson": (55.7435, -97.8558),

    # =====================
    # Saskatchewan
    # =====================
    "saskatoon": (52.1579, -106.6702),
    "regina": (50.4452, -104.6189),
    "moose jaw": (50.3933, -105.5519),
    "prince albert": (53.2033, -105.7531),

    # =====================
    # Atlantic Canada
    # =====================
    "halifax": (44.6488, -63.5752),
    "dartmouth": (44.6667, -63.5667),
    "moncton": (46.0878, -64.7782),
    "fredericton": (45.9636, -66.6431),
    "saint john": (45.2733, -66.0633),
    "st johns": (47.5615, -52.7126),
    "corner brook": (48.9520, -57.9527),
    "charlottetown": (46.2382, -63.1311),
    "summerside": (46.3959, -63.7902),

    # =====================
    # Territories
    # =====================
    "whitehorse": (60.7212, -135.0568),
    "yellowknife": (62.4540, -114.3718),
    "iqaluit": (63.7467, -68.5169),
    "hay river": (60.8158, -115.7999),
    "inuvik": (68.3607, -133.7230),
}


# -------------------------
# Helpers
# -------------------------

def normalize_location(text: str) -> str:
    """
    Normalize location text:
    - lowercase
    - strip whitespace
    - remove accents (Montréal → montreal)
    """
    text = text.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
