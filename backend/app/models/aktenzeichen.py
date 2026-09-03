"""
SQLAlchemy ORM Models: Aktenzeichen-Schema

Vergibt jedem generierten Anschreiben ein eindeutiges, ableitbares
Aktenzeichen (z.B. "VNV-2026-0114-ALTLASTEN-3"), damit eine spätere Phase
eingehende Antwort-Mails deterministisch dem richtigen Vorgang zuordnen kann,
ohne zu raten. Drei eigene Seitentabellen statt neuer Spalten auf
requests/request_items – analog zu AuthorityLocation/RequestItemProgress,
damit bestehende Tabellen (inkl. Produktions-Datenbank) unangetastet bleiben.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database.base import Base


class AktenzeichenSequence(Base):
    """Reiner Jahres-Zähler-Pool für fortlaufende Nummern."""

    __tablename__ = "aktenzeichen_sequences"

    year = Column(Integer, primary_key=True)
    next_number = Column(Integer, nullable=False, default=1)


class RequestSequence(Base):
    """
    1:1-Seitentabelle zu Request: fortlaufende, jahresbezogene Nummer, die
    ein Request bei seiner Erzeugung einmalig bekommt (unabhängig davon, ob
    er später einem Case zugeordnet wird - das passiert oft erst nachträglich
    per link-request, eine Case-gebundene Nummer wäre dafür ungeeignet).
    """

    __tablename__ = "request_sequences"

    request_id = Column(String(50), ForeignKey("requests.request_id"), primary_key=True)
    sequence_number = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "sequence_number": self.sequence_number,
            "year": self.year,
        }


class RequestItemReference(Base):
    """
    1:1-Seitentabelle zu RequestItem: das fertige Aktenzeichen-String, einmalig
    vergeben bei der ERSTEN erfolgreichen Dokumentgenerierung für dieses Item
    (nicht beim Matching - viele Items erreichen nie MATCHED/ein echtes
    Schreiben, für die soll keine Nummer verbraucht werden).
    """

    __tablename__ = "request_item_references"

    request_item_id = Column(String(100), ForeignKey("request_items.request_item_id"), primary_key=True)
    aktenzeichen = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "request_item_id": self.request_item_id,
            "aktenzeichen": self.aktenzeichen,
        }
