"""
SQLAlchemy ORM Model: Building (Gebäudedatenbank)
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Index
from app.database.base import Base


class Building(Base):
    """
    Repräsentiert ein Gebäude mit Adressdaten und Metainformationen.
    
    Primary Key: building_id (interne eindeutige ID)
    """
    
    __tablename__ = "buildings"

    # Primary Key
    building_id = Column(String(50), primary_key=True, nullable=False)

    # Adressdaten
    street = Column(String(255), nullable=False, index=True)
    house_number = Column(String(20), nullable=False)
    postal_code = Column(String(10), nullable=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    
    # Geografische Identifikatoren
    district = Column(String(100), nullable=True)  # Stadtteil / Bezirk
    state = Column(String(50), nullable=True)      # Bundesland
    ags = Column(String(12), unique=False, nullable=True, index=True)  # Amtlicher Gemeindeschlüssel (mehrere Gebäude teilen sich eine Gemeinde)
    
    # Koordinaten (für zukünftige Geocoding-Integration)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Metadaten des Gebäudes
    property_name = Column(String(255), nullable=True)  # Name des Objekts
    internal_reference = Column(String(100), unique=True, nullable=True, index=True)  # Interne Referenz
    
    # Audit-Felder
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Notizen / Zusatzinfo
    notes = Column(Text, nullable=True)

    # Indizes für häufige Abfragen
    __table_args__ = (
        Index('idx_buildings_ags', 'ags'),
        Index('idx_buildings_postal_city', 'postal_code', 'city'),
        Index('idx_buildings_street', 'street'),
        Index('idx_buildings_internal_ref', 'internal_reference'),
    )

    def __repr__(self):
        return (
            f"<Building(building_id={self.building_id}, "
            f"street={self.street} {self.house_number}, "
            f"{self.postal_code} {self.city}, ags={self.ags})>"
        )

    def full_address(self) -> str:
        """Gibt die vollständige Adresse als String zurück."""
        return f"{self.street} {self.house_number}, {self.postal_code} {self.city}"

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "building_id": self.building_id,
            "street": self.street,
            "house_number": self.house_number,
            "postal_code": self.postal_code,
            "city": self.city,
            "district": self.district,
            "state": self.state,
            "ags": self.ags,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "property_name": self.property_name,
            "internal_reference": self.internal_reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }
