"""
Prozess-lokaler Cache für die Datenqualitäts-Übersicht (app/api/data_quality.py).

Hintergrund: die Übersicht rechnet viele Prüfungen über (fast) alle Stamm-
daten und ist auf der Produktion (entfernte Neon-Datenbank, 1 Worker) die
mit Abstand teuerste Abfrage. Das Ergebnis ändert sich aber nur, wenn
Stammdaten geschrieben werden - deshalb wird es kurz zwischengespeichert
(Standard 300 s, per Umgebungsvariable DQ_CACHE_TTL_SECONDS einstellbar,
`0` schaltet den Cache ab).

Eigenschaften:
- thread-sicher (FastAPI führt synchrone Endpunkte in einem Thread-Pool aus),
- kein "Thundering Herd": gleichzeitige Kalt-Anfragen für denselben Schlüssel
  rechnen nur einmal, die anderen warten und nehmen das Ergebnis,
- Invalidierung: explizit über `clear_data_quality_cache()` (alle schreiben-
  den Endpunkte in data_quality.py) UND automatisch über SQLAlchemy-Events
  nach jedem Commit, der Stammdaten (Behörden, Zuständigkeiten, Gebäude,
  Anfragen ...) verändert hat - so bleibt der Cache auch nach Imports und
  Änderungen aus anderen Modulen nicht veraltet. Ein Ergebnis, das während
  einer solchen Invalidierung noch berechnet wurde, wird nicht mehr abgelegt
  (Generationszähler).
- unter pytest standardmäßig AUS, damit der Cache keine Tests beeinflusst
  (conftest.py legt die DB je Test neu an). Tests, die den Cache prüfen,
  schalten ihn explizit über `TTL_OVERRIDE` (siehe unten) ein.
"""

import os
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.authority import Authority
from app.models.building import Building
from app.models.case import CaseBuilding, CaseRequest
from app.models.jurisdiction import Jurisdiction
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.request_type import RequestType

DEFAULT_TTL_SECONDS = 300.0
TTL_ENV_VAR = "DQ_CACHE_TTL_SECONDS"

# Explizite Vorgabe (Sekunden). None = Umgebungsvariable/Default bzw. unter
# pytest "aus". Tests, die den Cache prüfen wollen, setzen hier einen Wert
# (z.B. monkeypatch.setattr(dq_cache, "TTL_OVERRIDE", 60.0)); 0 = aus.
TTL_OVERRIDE: Optional[float] = None

_lock = threading.Lock()  # schützt _store, _key_locks, _generation
_store: Dict[str, Tuple[float, Any]] = {}
_key_locks: Dict[str, threading.Lock] = {}
_generation = 0


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules


def effective_ttl() -> float:
    """Aktuell gültige TTL in Sekunden (<= 0 bedeutet: Cache inaktiv)."""
    if TTL_OVERRIDE is not None:
        return float(TTL_OVERRIDE)
    if _running_under_pytest():
        return 0.0
    raw = os.getenv(TTL_ENV_VAR)
    if raw is None or not raw.strip():
        return DEFAULT_TTL_SECONDS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TTL_SECONDS


def clear_data_quality_cache() -> None:
    """Verwirft alle zwischengespeicherten Ergebnisse (und laufende Berechnungen)."""
    global _generation
    with _lock:
        _store.clear()
        _generation += 1


_MISS = object()


def _lookup(key: str, ttl: float) -> Any:
    """Zwischengespeicherter Wert oder _MISS (so kann auch None gecacht werden)."""
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return _MISS
        stored_at, value = entry
        if time.monotonic() - stored_at > ttl:
            _store.pop(key, None)
            return _MISS
        return value


def get_or_compute(key: str, compute: Callable[[], Any], refresh: bool = False) -> Any:
    """
    Liefert das zwischengespeicherte Ergebnis für `key` oder berechnet es.

    refresh=True umgeht den Cache (rechnet neu und legt das frische Ergebnis
    ab). Ist der Cache inaktiv (TTL <= 0), wird immer direkt berechnet.
    """
    ttl = effective_ttl()
    if ttl <= 0:
        return compute()

    if not refresh:
        hit = _lookup(key, ttl)
        if hit is not _MISS:
            return hit

    with _lock:
        key_lock = _key_locks.setdefault(key, threading.Lock())

    with key_lock:
        if not refresh:
            # Ein anderer Thread kann das Ergebnis erzeugt haben, während wir
            # auf den Schlüssel-Lock gewartet haben.
            hit = _lookup(key, ttl)
            if hit is not _MISS:
                return hit
        with _lock:
            generation = _generation
        value = compute()
        with _lock:
            # Wurde währenddessen invalidiert (Schreibzugriff), ist das
            # Ergebnis evtl. veraltet - dann nicht ablegen.
            if generation == _generation:
                _store[key] = (time.monotonic(), value)
        return value


# ---------------------------------------------------------------------------
# Automatische Invalidierung bei Schreibzugriffen auf relevante Stammdaten
# ---------------------------------------------------------------------------

_RELEVANT_MODELS = (
    Authority, Building, CaseBuilding, CaseRequest, Jurisdiction,
    Request, RequestItem, RequestItemProgress, RequestType,
)
_DIRTY_FLAG = "dq_cache_dirty"


def _is_relevant(instance: Any) -> bool:
    return isinstance(instance, _RELEVANT_MODELS)


@event.listens_for(Session, "after_flush")
def _mark_dirty_after_flush(session: Session, flush_context) -> None:
    if session.info.get(_DIRTY_FLAG):
        return
    for collection in (session.new, session.dirty, session.deleted):
        if any(_is_relevant(obj) for obj in collection):
            session.info[_DIRTY_FLAG] = True
            return


@event.listens_for(Session, "after_bulk_update")
def _mark_dirty_after_bulk_update(update_context) -> None:
    if issubclass(update_context.mapper.class_, _RELEVANT_MODELS):
        update_context.session.info[_DIRTY_FLAG] = True


@event.listens_for(Session, "after_bulk_delete")
def _mark_dirty_after_bulk_delete(delete_context) -> None:
    if issubclass(delete_context.mapper.class_, _RELEVANT_MODELS):
        delete_context.session.info[_DIRTY_FLAG] = True


@event.listens_for(Session, "after_commit")
def _clear_after_commit(session: Session) -> None:
    if session.info.pop(_DIRTY_FLAG, False):
        clear_data_quality_cache()


@event.listens_for(Session, "after_rollback")
def _reset_flag_after_rollback(session: Session) -> None:
    session.info.pop(_DIRTY_FLAG, None)
