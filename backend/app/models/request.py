"""
SQLAlchemy ORM Models: Request & RequestItem (Historie & Audit-Trail)
"""

from datetime import datetime
import json
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index, Float
from app.database.base import Base
from sqlalchemy.orm import relationship


class Request(Base):
    """
    Repräsentiert eine komplette Anfrage für ein Gebäude.
    Dient als Audit-Trail und ermöglicht Historiensuche.
    
    Primary Key: request_id
    """
    
    __tablename__ = "requests"

    # Primary Key
    request_id = Column(String(50), primary_key=True, nullable=False)

    # Foreign Key
    building_id = Column(String(50), ForeignKey("buildings.building_id"), nullable=False, index=True)

    # Benutzer & Zeitstempel
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Status der Gesamtanfrage
    # PENDING, COMPLETED, PARTIALLY_COMPLETED, FAILED
    status = Column(String(50), default="PENDING", nullable=False, index=True)

    # Notizen
    notes = Column(Text, nullable=True)

    # Relationship zu RequestItems
    items = relationship("RequestItem", back_populates="request", cascade="all, delete-orphan")

    # Indizes
    __table_args__ = (
        Index('idx_requests_building', 'building_id'),
        Index('idx_requests_created_at', 'created_at'),
        Index('idx_requests_status', 'status'),
    )

    def __repr__(self):
        return (
            f"<Request(request_id={self.request_id}, "
            f"building_id={self.building_id}, status={self.status})>"
        )

    def get_completion_status(self) -> dict:
        """Gibt den Abschluss-Status der Anfrage zurück."""
        if not self.items:
            return {"total": 0, "completed": 0, "failed": 0, "pending": 0}

        completed = sum(1 for item in self.items if item.document_status == "GENERATED")
        failed = sum(1 for item in self.items if item.document_status == "FAILED")
        pending = sum(1 for item in self.items if item.document_status == "PENDING")

        return {
            "total": len(self.items),
            "completed": completed,
            "failed": failed,
            "pending": pending,
        }

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "request_id": self.request_id,
            "building_id": self.building_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "completion_status": self.get_completion_status(),
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }


class RequestItem(Base):
    """
    Repräsentiert eine einzelne Auskunftsanfrage für eine Behörde.
    Speichert Matching-Details, Dokumentpfad und Änderungshistorie.
    
    Primary Key: request_item_id
    """
    
    __tablename__ = "request_items"

    # Primary Key
    request_item_id = Column(String(100), primary_key=True, nullable=False)

    # Foreign Keys
    request_id = Column(String(50), ForeignKey("requests.request_id"), nullable=False, index=True)
    request_type_id = Column(String(50), ForeignKey("request_types.request_type_id"), nullable=False, index=True)
    authority_id = Column(String(50), ForeignKey("authorities.authority_id"), nullable=True, index=True)

    # ========== Matching-Details ==========

    # Auf welcher Ebene wurde gematcht?
    # STREET_NUMBER, STREET, DISTRICT, MUNICIPALITY, COUNTY, STATE, POSTAL_CODE
    matching_level = Column(String(50), nullable=True)

    # Status des Matching
    # MATCHED, REVIEW_REQUIRED, NO_MATCH, MULTIPLE_MATCHES
    matching_status = Column(String(50), default="PENDING", nullable=False, index=True)

    # Konfidenzwert (0.0 - 1.0)
    matching_confidence = Column(Float, default=0.0, nullable=False)

    # JSON Liste alternativer Behörden bei MULTIPLE_MATCHES
    # z.B. '["AUTH_001", "AUTH_002"]'
    alternative_authorities = Column(Text, nullable=True)

    # ========== Manuelle Anpassungen ==========

    # Wurde die Zuordnung manuell geändert?
    manually_changed = Column(Boolean, default=False, index=True)

    # Grund der manuellen Änderung
    manual_change_reason = Column(Text, nullable=True)

    # ========== Dokumentgenerierung ==========

    # Pfad zur generierten Datei
    document_path = Column(String(500), nullable=True)

    # Status der Dokumentgenerierung
    # PENDING, GENERATED, FAILED
    document_status = Column(String(50), default="PENDING", nullable=False, index=True)

    # ========== Audit-Felder ==========

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    request = relationship("Request", back_populates="items")

    # Indizes
    __table_args__ = (
        Index('idx_request_items_request', 'request_id'),
        Index('idx_request_items_matching_status', 'matching_status'),
        Index('idx_request_items_document_status', 'document_status'),
    )

    def __repr__(self):
        return (
            f"<RequestItem(request_item_id={self.request_item_id}, "
            f"request_type={self.request_type_id}, "
            f"status={self.matching_status})>"
        )

    def get_alternative_authorities_list(self) -> list:
        """Konvertiert alternative_authorities JSON zu Python-Liste."""
        if not self.alternative_authorities:
            return []
        try:
            return json.loads(self.alternative_authorities)
        except json.JSONDecodeError:
            return []

    def set_alternative_authorities(self, authorities: list) -> None:
        """Setzt alternative_authorities als JSON."""
        self.alternative_authorities = json.dumps(authorities) if authorities else None

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "request_item_id": self.request_item_id,
            "request_id": self.request_id,
            "request_type_id": self.request_type_id,
            "authority_id": self.authority_id,
            "matching_level": self.matching_level,
            "matching_status": self.matching_status,
            "matching_confidence": self.matching_confidence,
            "alternative_authorities": self.get_alternative_authorities_list(),
            "manually_changed": self.manually_changed,
            "manual_change_reason": self.manual_change_reason,
            "document_path": self.document_path,
            "document_status": self.document_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
