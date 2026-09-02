"""
SQLAlchemy ORM Model: AuthorityLocation

Geocodierte Koordinaten für Behörden, in einer eigenen Tabelle statt als
zusätzliche Spalten auf Authority – so lässt sie sich per create_all() neu
anlegen, ohne bestehende Authority-Zeilen (inkl. Produktions-Datenbank)
per ALTER TABLE anfassen zu müssen.
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from app.database.base import Base


class AuthorityLocation(Base):
    __tablename__ = "authority_locations"

    authority_id = Column(String(50), ForeignKey("authorities.authority_id"), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geocoded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
