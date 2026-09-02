"""
Geocoding über die öffentliche Nominatim-API (OpenStreetMap).

Nominatim-Nutzungsbedingungen: max. 1 Anfrage/Sekunde, aussagekräftiger
User-Agent, Ergebnisse cachen statt wiederholt dieselbe Adresse abzufragen.
Siehe https://operations.osmfoundation.org/policies/nominatim/
"""

import threading
import time
from typing import Optional

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Zustaendigkeitsfinder-Vonovia/1.0 (internes Tool zur Behoerdenzuordnung)"

_lock = threading.Lock()
_last_request_at = 0.0
_MIN_INTERVAL_SECONDS = 1.1


def _throttle() -> None:
    global _last_request_at
    with _lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < _MIN_INTERVAL_SECONDS:
            time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
        _last_request_at = time.monotonic()


def geocode_address(query: str) -> Optional[tuple[float, float]]:
    """
    Löst eine Adresse zu (latitude, longitude) auf. Gibt None zurück, wenn
    kein Treffer gefunden wurde oder die Anfrage fehlschlägt – es wird NICHT
    geraten.
    """
    if not query.strip():
        return None

    _throttle()
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "de"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None

    try:
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (KeyError, ValueError, TypeError):
        return None
