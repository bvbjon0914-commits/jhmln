"""
SQLAlchemy ORM Model: User (Nutzer-Accounts)

Persönliche Accounts fuer echte Mehrbenutzer-Anmeldung. Jeder Account trägt
seine eigenen Kontakt- und Adressdaten (z.B. bei unterschiedlichen
Standorten), die automatisch in Kopf- und Signaturzeile generierter
Dokumente einfliessen (siehe app/services/document_generator.py). NUR das
Firmen-Impressum (Sitz/Registergericht/HRB/Vorstand) bleibt statisch/
unveraendert - das ist Firmen-, nicht Personendaten.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index
from app.database.base import Base


class User(Base):
    """
    Repraesentiert einen individuellen Nutzer-Account.

    Primary Key: user_id
    """

    __tablename__ = "users"

    # Primary Key
    user_id = Column(String(50), primary_key=True, nullable=False)

    # Login
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Pflichtangaben fuer die Dokumentengenerierung (Kopf- und Signaturzeile)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(100), nullable=False)
    function = Column(String(255), nullable=False)
    street = Column(String(255), nullable=False)
    house_number = Column(String(20), nullable=False)
    postal_code = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)

    # Rolle / Rechte
    is_main = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)

    # Audit-Felder
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_users_active', 'active'),
    )

    def __repr__(self):
        return (
            f"<User(user_id={self.user_id}, email={self.email}, "
            f"is_main={self.is_main}, active={self.active})>"
        )

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary. Enthaelt NIEMALS password_hash."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "function": self.function,
            "street": self.street,
            "house_number": self.house_number,
            "postal_code": self.postal_code,
            "city": self.city,
            "is_main": self.is_main,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
