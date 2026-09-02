"""
SQLAlchemy ORM Model: Authority (Ämterdatenbank)
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from app.database.base import Base


class Authority(Base):
    """
    Repräsentiert eine öffentliche Behörde / Amt.
    
    Primary Key: authority_id (eindeutige ID der Behörde)
    """
    
    __tablename__ = "authorities"

    # Primary Key
    authority_id = Column(String(50), primary_key=True, nullable=False)

    # Behördentyp (veraltet, für Rückwärtskompatibilität)
    authority_type = Column(String(50), nullable=True)

    # Behördendaten
    authority_name = Column(String(255), nullable=False, index=True)
    department_name = Column(String(255), nullable=True)  # Abteilung / Referat

    # Adressdaten
    street = Column(String(255), nullable=True)
    house_number = Column(String(20), nullable=True)
    postal_code = Column(String(10), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True, index=True)

    # Kontaktdaten
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)

    # Metadaten zur Datenqualität
    source = Column(String(255), nullable=True)  # Woher stammen die Daten?
    last_verified_at = Column(DateTime, nullable=True)  # Wann wurde zuletzt verifiziert?
    verified_by = Column(String(255), nullable=True)  # Wer hat verifiziert?

    # Status
    active = Column(Boolean, default=True, index=True)

    # Audit-Felder
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Notizen / Zusatzinfo
    notes = Column(Text, nullable=True)

    # Indizes
    __table_args__ = (
        Index('idx_authorities_city_postal', 'city', 'postal_code'),
        Index('idx_authorities_state', 'state'),
        Index('idx_authorities_active', 'active'),
        Index('idx_authorities_name', 'authority_name'),
    )

    def __repr__(self):
        return (
            f"<Authority(authority_id={self.authority_id}, "
            f"name={self.authority_name}, city={self.city}, "
            f"active={self.active})>"
        )

    def full_address(self) -> str:
        """Gibt die vollständige Adresse als String zurück."""
        parts = []
        if self.street and self.house_number:
            parts.append(f"{self.street} {self.house_number}")
        elif self.street:
            parts.append(self.street)
        
        if self.postal_code:
            parts.append(self.postal_code)
        if self.city:
            parts.append(self.city)
        
        return ", ".join(parts) if parts else "Adresse nicht angegeben"

    def contact_info(self) -> dict:
        """Gibt Kontaktinformationen als Dictionary zurück."""
        return {
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
        }

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "authority_id": self.authority_id,
            "authority_type": self.authority_type,
            "authority_name": self.authority_name,
            "department_name": self.department_name,
            "street": self.street,
            "house_number": self.house_number,
            "postal_code": self.postal_code,
            "city": self.city,
            "state": self.state,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "source": self.source,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verified_by": self.verified_by,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }
