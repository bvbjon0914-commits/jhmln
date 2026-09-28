"""
SQLAlchemy ORM Model: Jurisdiction (Zuständigkeitsmatrix)

Dies ist die ZENTRALE Tabelle für alle Zuständigkeitsregeln.
Sie verbindet Auskunftsarten mit Behörden auf Basis geografischer Kriterien.
"""

from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Text, Index, ForeignKey
)
from app.database.base import Base


class MatchingLevel(str, Enum):
    """
    Enum für die Hierarchie-Ebenen des Matchings.
    Kleinere Zahlen = höhere Spezifität.
    """
    STREET_NUMBER = "STREET_NUMBER"      # Straße + Hausnummer (Stufe 1)
    STREET = "STREET"                    # Nur Straße (Stufe 2)
    DISTRICT = "DISTRICT"                # Stadtteil / Bezirk (Stufe 3)
    MUNICIPALITY = "MUNICIPALITY"        # Gemeinde / AGS (Stufe 4)
    COUNTY = "COUNTY"                    # Landkreis (Stufe 5)
    STATE = "STATE"                      # Bundesland (Stufe 6)
    POSTAL_CODE = "POSTAL_CODE"          # PLZ (Stufe 7)


class Jurisdiction(Base):
    """
    Zuständigkeitsmatrix: Verbindet Auskunftsarten mit Behörden
    über geografische Kriterien.

    Primary Key: jurisdiction_id
    """

    __tablename__ = "jurisdictions"

    # Primary Key
    jurisdiction_id = Column(String(100), primary_key=True, nullable=False)

    # Foreign Keys
    request_type_id = Column(String(50), ForeignKey("request_types.request_type_id"), nullable=False, index=True)
    authority_id = Column(String(50), ForeignKey("authorities.authority_id"), nullable=False, index=True)

    # ========== Geografische Zuordnung (hierarchisch) ==========

    # Ländercode (zur Zukunftssicherung, initial nur DE)
    country = Column(String(2), default="DE", nullable=False)

    # Bundesland
    state = Column(String(50), nullable=True, index=True)

    # Amtlicher Gemeindeschlüssel (AGS) – Schlüsselattribut
    ags = Column(String(12), nullable=True, index=True)

    # Gemeinde-/Stadtname
    municipality = Column(String(100), nullable=True, index=True)

    # Stadtteil / Bezirk
    district = Column(String(100), nullable=True, index=True)

    # PLZ (fallback)
    postal_code = Column(String(10), nullable=True, index=True)

    # Straßenname
    street = Column(String(255), nullable=True, index=True)

    # Hausnummer (für sehr spezifische Regeln)
    house_number = Column(String(20), nullable=True)

    # ========== Zeitliche Gültigkeit ==========

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    # ========== Priorisierung & Matching-Level ==========

    # Priority: kleinere Zahlen haben Vorrang
    # 10 = STREET_NUMBER
    # 20 = STREET
    # 30 = DISTRICT
    # 40 = MUNICIPALITY (Standard)
    # 50 = COUNTY
    # 60 = STATE
    # 70 = POSTAL_CODE
    priority = Column(Integer, default=100, nullable=False, index=True)

    # Matching-Level (für Audit & Nachvollziehbarkeit)
    matching_level = Column(String(50), nullable=True)

    # ========== Metadaten zur Datenqualität ==========

    # Woher stammt die Regel? HISTORISCH oft ein interner Verarbeitungs-
    # vermerk (z.B. "GrundEngine ... FINAL V14"), keine echte Fundstelle -
    # source_url/source_license unten sind der Versuch, das nachzuholen.
    # Feld bewusst nicht umbenannt/entfernt (bestehende 16.290 Zeilen sind
    # zu 100% befüllt), nur um die fehlenden Angaben ergänzt.
    source = Column(String(255), nullable=True)

    # Konkrete Fundstelle: URL/Aktenzeichen der amtlichen Quelle, aus der
    # diese Regel stammt (z.B. ein Landesjustizportal, eine Landesverordnung
    # zur gerichtlichen Zuständigkeit). Getrennt von "source" (das bleibt der
    # eher grobe/interne Herkunftsvermerk), damit eine echte Fundstelle nicht
    # mit einem internen Batch-Namen verwechselt wird.
    source_url = Column(Text, nullable=True)

    # Lizenz-/Nutzungsbedingungen der Quelle (z.B. "Datenlizenz Deutschland -
    # Zero 2.0", "GeoNutzV", oder ein Hinweis auf fehlende/unklare Lizenz) -
    # Voraussetzung für eine spätere kommerzielle Nutzung, siehe
    # docs/COMMERCIALIZATION_DEPLOYMENT_MODELS.md.
    source_license = Column(String(255), nullable=True)

    # Wann wurde diese Regel zuletzt aus der Quelle ABGERUFEN (kann vor der
    # fachlichen Prüfung liegen - ein automatischer Import ruft eine Quelle
    # ab, ohne dass damit schon jemand die fachliche Richtigkeit bestätigt
    # hätte). Getrennt von last_verified_at (= wann fachlich BESTÄTIGT).
    source_retrieved_at = Column(DateTime, nullable=True)

    # Wann wurde diese Regel zuletzt fachlich als korrekt VERIFIZIERT?
    last_verified_at = Column(DateTime, nullable=True)

    # Wer hat diese Regel fachlich verifiziert?
    verified_by = Column(String(255), nullable=True)

    # Ausdrücklicher Prüfstatus - trennt "automatisch gefunden/importiert"
    # von "fachlich bestätigt", statt das implizit aus last_verified_at
    # NULL-oder-nicht abzuleiten. Werte: AUTO_IMPORTED (Default - Zeile kam
    # aus einem automatisierten Import/einer Recherche ohne anschließende
    # menschliche Bestätigung), VERIFIED (fachlich bestätigt), CORRECTED
    # (nach Prüfung manuell korrigiert), NEEDS_REVIEW (bekannter Zweifel/
    # Widerspruch, siehe Konfliktbehandlung in der Staging-Pipeline).
    verification_status = Column(String(30), nullable=False, default="AUTO_IMPORTED", index=True)

    # ========== Status ==========

    active = Column(Boolean, default=True, index=True)

    # ========== Audit-Felder ==========

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ========== Notizen ==========

    notes = Column(Text, nullable=True)

    # ========== Indizes für Performance ==========

    __table_args__ = (
        # Häufigste Abfragen: Kombinationen von Auskunftsart + geografischem Kriterium
        Index('idx_jurisdiction_request_type_ags', 'request_type_id', 'ags', 'priority'),
        Index('idx_jurisdiction_request_type_municipality', 'request_type_id', 'municipality', 'priority'),
        Index('idx_jurisdiction_request_type_street', 'request_type_id', 'street', 'priority'),
        Index('idx_jurisdiction_request_type_district', 'request_type_id', 'district', 'priority'),
        Index('idx_jurisdiction_request_type_state', 'request_type_id', 'state', 'priority'),

        # Weitere Indizes
        Index('idx_jurisdiction_active', 'active'),
        Index('idx_jurisdiction_priority', 'priority'),
        Index('idx_jurisdiction_ags', 'ags'),
    )

    def __repr__(self):
        return (
            f"<Jurisdiction(jurisdiction_id={self.jurisdiction_id}, "
            f"request_type={self.request_type_id}, "
            f"authority={self.authority_id}, "
            f"level={self.matching_level})>"
        )

    def is_valid_today(self) -> bool:
        """Prüft, ob diese Regel heute gültig ist."""
        today = date.today()

        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False

        return self.active

    def is_professionally_verified(self, stale_after_days: int = 365) -> bool:
        """
        True, wenn diese Regel fachlich bestätigt UND diese Bestätigung noch
        nicht abgelaufen ist. Bewusst UND-verknüpft: ein "VERIFIED"-Status
        mit einem sehr alten last_verified_at gilt nicht mehr als aktuell
        belegt (dieselbe 365-Tage-Konvention wie die bestehende
        Authority-Verifizierungsablauf-Prüfung in data_quality.py).
        """
        if self.verification_status not in ("VERIFIED", "CORRECTED"):
            return False
        if not self.last_verified_at:
            return False
        return (datetime.utcnow() - self.last_verified_at).days <= stale_after_days

    def get_specificity_score(self) -> int:
        """
        Gibt einen Spezifitätsscore basierend auf filling details zurück.
        Je höher, desto spezifischer die Regel.

        Wird verwendet, um bei mehreren Matches die spezifischste zu wählen.
        """
        score = 0
        if self.street and self.house_number:
            score += 8  # Höchste Spezifität
        elif self.street:
            score += 6
        if self.district:
            score += 5
        if self.ags:
            score += 4
        if self.municipality:
            score += 3
        if self.postal_code:
            score += 2
        if self.state:
            score += 1
        return score

    def to_dict(self) -> dict:
        """Konvertiert das Modell zu einem Dictionary."""
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "request_type_id": self.request_type_id,
            "authority_id": self.authority_id,
            "country": self.country,
            "state": self.state,
            "ags": self.ags,
            "municipality": self.municipality,
            "district": self.district,
            "postal_code": self.postal_code,
            "street": self.street,
            "house_number": self.house_number,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "priority": self.priority,
            "matching_level": self.matching_level,
            "source": self.source,
            "source_url": self.source_url,
            "source_license": self.source_license,
            "source_retrieved_at": self.source_retrieved_at.isoformat() if self.source_retrieved_at else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verified_by": self.verified_by,
            "verification_status": self.verification_status,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }
