"""
SQLAlchemy ORM Model: AuthorityContactChannel

Trennt "Kontakt- und Übermittlungsweg" fachlich von der Dienststelle selbst
(Authority) - eine Behörde kann mehrere Wege akzeptieren (E-Mail, Online-
Portal, Post, Fax), mit unterschiedlicher Präferenz und unterschiedlichem
Beleg/Prüfstatus je Weg. Die bisherigen Flachfelder email/phone/website auf
Authority bleiben unverändert bestehen (keine Daten migriert, kein Risiko
für die 4.730 bestehenden Behörden-Zeilen) - dieses Modell ist rein additiv
für neu recherchierte oder differenzierte Kontaktwege gedacht, insbesondere
wenn eine Behörde für eine bestimmte Auskunftsart einen ANDEREN Weg verlangt
als für den allgemeinen Kontakt (z.B. ein dediziertes Grundbuch-Portal).
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Index
from app.database.base import Base


class ChannelType:
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    PORTAL = "PORTAL"
    POST = "POST"
    FAX = "FAX"
    OTHER = "OTHER"


class AuthorityContactChannel(Base):
    """Ein einzelner Kontakt-/Übermittlungsweg einer Behörde."""

    __tablename__ = "authority_contact_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    authority_id = Column(String(50), ForeignKey("authorities.authority_id"), nullable=False, index=True)

    channel_type = Column(String(20), nullable=False)  # siehe ChannelType
    value = Column(Text, nullable=False)  # E-Mail-Adresse, Telefonnummer, Portal-URL, Postanschrift-Text, ...

    # Optionale Einschränkung: gilt dieser Weg nur für eine bestimmte
    # Auskunftsart (z.B. ein separates Grundbuch-Einreichungsportal)? NULL =
    # allgemeiner Kontaktweg der Behörde, unabhängig von der Auskunftsart.
    request_type_id = Column(String(50), ForeignKey("request_types.request_type_id"), nullable=True, index=True)

    preferred = Column(Boolean, default=False, nullable=False)

    # Dieselbe Quellennachweis-Logik wie bei Jurisdiction, hier je Kontaktweg
    # statt je Zuständigkeitsregel - eine Telefonnummer kann veraltet sein,
    # während die E-Mail-Adresse derselben Behörde noch aktuell ist.
    source = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String(255), nullable=True)

    active = Column(Boolean, default=True, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_contact_channel_authority", "authority_id"),
        Index("idx_contact_channel_type", "channel_type"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "authority_id": self.authority_id,
            "channel_type": self.channel_type,
            "value": self.value,
            "request_type_id": self.request_type_id,
            "preferred": self.preferred,
            "source": self.source,
            "source_url": self.source_url,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verified_by": self.verified_by,
            "active": self.active,
            "notes": self.notes,
        }
