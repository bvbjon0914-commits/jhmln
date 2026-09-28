"""
Einfacher In-Memory-Ratenbegrenzer für Login-Versuche.

Schützt /api/auth/login vor massenhaften Rateversuchen (Brute-Force). Bewusst
kein externer Dienst (Redis o.ä.): konsistent mit dem übrigen
Architekturstand, in dem auch der Nominatim-Rate-Limiter in geocoding.py rein
prozesslokal ist. Für den aktuellen Single-Prozess-Betrieb (ein Uvicorn-
Worker, siehe render.yaml) ausreichend; bei echtem Mehrprozess- oder
Mehrinstanzbetrieb müsste der Zähler durch einen gemeinsamen Speicher (z.B.
die Datenbank) ersetzt werden, da jeder Prozess sonst seinen eigenen,
unabhängigen Zähler führt.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from app.config import LOGIN_RATE_LIMIT_MAX_ATTEMPTS, LOGIN_RATE_LIMIT_WINDOW_SECONDS

_lock = threading.Lock()
_failed_attempts: Dict[str, Deque[float]] = defaultdict(deque)


def _prune(bucket: Deque[float], now: float) -> None:
    cutoff = now - LOGIN_RATE_LIMIT_WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.popleft()


def is_blocked(client_key: str) -> bool:
    """True, wenn client_key innerhalb des Zeitfensters bereits zu oft fehlgeschlagen ist."""
    now = time.monotonic()
    with _lock:
        bucket = _failed_attempts[client_key]
        _prune(bucket, now)
        return len(bucket) >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def record_failure(client_key: str) -> None:
    now = time.monotonic()
    with _lock:
        bucket = _failed_attempts[client_key]
        _prune(bucket, now)
        bucket.append(now)


def record_success(client_key: str) -> None:
    """Setzt den Zähler nach einem erfolgreichen Login zurück."""
    with _lock:
        _failed_attempts.pop(client_key, None)


def reset_all() -> None:
    """Nur für Tests: leert den gesamten Zustand zwischen Testfällen."""
    with _lock:
        _failed_attempts.clear()
