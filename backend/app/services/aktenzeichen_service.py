"""
AktenzeichenService

Vergibt fortlaufende, jahresbezogene Nummern für das Aktenzeichen-Schema
(siehe app/models/aktenzeichen.py für den Hintergrund).
"""

from sqlalchemy.orm import Session

from app.models.aktenzeichen import AktenzeichenSequence


def next_year_number(db: Session, year: int) -> int:
    """
    Liefert die nächste fortlaufende Nummer für das gegebene Jahr und
    erhöht den Zähler atomar.

    with_for_update() sorgt auf Postgres/Neon (Produktion) für echtes
    Row-Locking gegen Nummern-Kollisionen bei gleichzeitigen Requests; auf
    SQLite (lokale Entwicklung) ist es ein No-Op, was dort unkritisch ist,
    da SQLite Schreibzugriffe ohnehin serialisiert (siehe der bestehende
    Kommentar zu SQLite-Nebenläufigkeit in database/engine.py).
    """
    seq = db.query(AktenzeichenSequence).filter(AktenzeichenSequence.year == year).with_for_update().first()
    if seq is None:
        seq = AktenzeichenSequence(year=year, next_number=1)
        db.add(seq)
        db.flush()
        seq = db.query(AktenzeichenSequence).filter(AktenzeichenSequence.year == year).with_for_update().first()

    number = seq.next_number
    seq.next_number += 1
    db.flush()
    return number
