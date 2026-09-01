"""
SQLAlchemy ORM Model: RequestType (Auskunftsarten)
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from app.database.base import Base


class RequestType(Base):
    """
    Definiert die verschiedenen Auskunftsarten (Grundbuch, Bauakten, etc.).
    
    Primary Key: request_type_id (z.B. "GRUNDBUCH", "BAUAKTEN")
    """
    
    __tablename__ = "request_types"

    # Primary Key
    request_type_id = Column(String(50), primary_key=True, nullable=False)

    # Eindeutiger Code (Alternative zu request_type_id)
    code = Column(String(50), unique=True, nullable=False, index=True)

    # Anzeigetext
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Word-Vorlagenassoziation
    template_filename = Column(String(255), nullable=True)  # z.B. "grundbuch.docx"

    # Status
    active = Column(Boolean, default=True, index=True)

    # Audit-Felder
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Notizen
    notes = Column(Text, nullable=True)

    # Indizes
    __table_args__ = (
        Index('idx_request_types_active', 'active'),
        Index('idx_request_types_code', 'code'),
    )

    def __repr__(self):
        return f"<RequestType(request_type_id={self.request_type_id}, name={self.name}, active={self.active})>"

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "request_type_id": self.request_type_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "template_filename": self.template_filename,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }


# Standard Auskunftsarten (Konstanten für die Anwendung)
REQUEST_TYPE_GRUNDBUCH = "GRUNDBUCH"
REQUEST_TYPE_BAUAKTEN = "BAUAKTEN"
REQUEST_TYPE_BAULASTEN = "BAULASTEN"
REQUEST_TYPE_ALTLASTEN = "ALTLASTEN"
REQUEST_TYPE_ERSCHLIESSUNG = "ERSCHLIESSUNG"
REQUEST_TYPE_DENKMALSCHUTZ = "DENKMALSCHUTZ"
REQUEST_TYPE_BODENDENKMALSCHUTZ = "BODENDENKMALSCHUTZ"
REQUEST_TYPE_WASSERSCHUTZ = "WASSERSCHUTZ"
REQUEST_TYPE_HOCHWASSERSCHUTZ = "HOCHWASSERSCHUTZ"
REQUEST_TYPE_KAMPFMITTEL = "KAMPFMITTEL"
REQUEST_TYPE_KATASTER = "KATASTER"

STANDARD_REQUEST_TYPES = [
    REQUEST_TYPE_GRUNDBUCH,
    REQUEST_TYPE_BAUAKTEN,
    REQUEST_TYPE_BAULASTEN,
    REQUEST_TYPE_ALTLASTEN,
    REQUEST_TYPE_ERSCHLIESSUNG,
    REQUEST_TYPE_DENKMALSCHUTZ,
    REQUEST_TYPE_BODENDENKMALSCHUTZ,
    REQUEST_TYPE_WASSERSCHUTZ,
    REQUEST_TYPE_HOCHWASSERSCHUTZ,
    REQUEST_TYPE_KAMPFMITTEL,
    REQUEST_TYPE_KATASTER,
]
