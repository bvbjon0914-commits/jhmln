"""
SQLAlchemy ORM Models: Case, CaseBuilding, CaseRequest

Ein "Auftrag" bündelt mehrere Gebäude und die zu ihnen gehörenden Requests,
damit der Fortschritt (was wurde beantragt, was fehlt noch) über mehrere
Gebäude/Behörden hinweg an einem Ort sichtbar ist. Bewusst als eigene,
zusätzliche Tabellen umgesetzt statt als Spalten auf bestehenden Tabellen
(buildings/requests) – so bleiben Wizard und Historie unverändert nutzbar,
und es ist kein manuelles ALTER TABLE auf Produktion nötig.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.database.base import Base


class Case(Base):
    """Ein Auftrag/Fall, der mehrere Gebäude und deren Anfragen bündelt."""

    __tablename__ = "cases"

    case_id = Column(String(50), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    # OPEN, CLOSED
    status = Column(String(20), default="OPEN", nullable=False, index=True)

    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "notes": self.notes,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CaseBuilding(Base):
    """Verknüpft ein Gebäude mit einem Auftrag (reine Zuordnung, kein Besitz)."""

    __tablename__ = "case_buildings"

    case_id = Column(String(50), ForeignKey("cases.case_id"), primary_key=True)
    building_id = Column(String(50), ForeignKey("buildings.building_id"), primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CaseRequest(Base):
    """Verknüpft einen (über /matching erzeugten) Request mit einem Auftrag."""

    __tablename__ = "case_requests"

    case_id = Column(String(50), ForeignKey("cases.case_id"), primary_key=True)
    request_id = Column(String(50), ForeignKey("requests.request_id"), primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
