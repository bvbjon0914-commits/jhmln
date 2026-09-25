"""
SQLAlchemy ORM Model: JurisdictionStagingEntry

Staging-Bereich für neu recherchierte/importierte Zuständigkeitsregeln, BEVOR
sie die produktive `jurisdictions`-Tabelle verändern (sicherer
Aktualisierungsprozess, siehe Auftrag: "Neue Daten gehen zuerst in einen
Staging-Bereich... Automatische Aktualisierungen dürfen fachlich bestätigte
oder manuell korrigierte Werte nicht ungeprüft überschreiben").

Es gibt bewusst KEINEN Code-Pfad, der eine JurisdictionStagingEntry
automatisch in `jurisdictions` übernimmt - jede Übernahme ist ein expliziter
Aufruf von JurisdictionStagingService.approve_entry() durch einen Menschen,
der den zuvor berechneten Konflikt-Status gesehen hat (siehe
app/services/jurisdiction_staging.py).
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey, Index
from app.database.base import Base


class StagingStatus:
    PENDING = "PENDING"        # wartet auf Entscheidung
    APPROVED = "APPROVED"      # übernommen nach app/services/jurisdiction_staging.py:approve_entry
    REJECTED = "REJECTED"      # bewusst verworfen
    SUPERSEDED = "SUPERSEDED"  # durch einen neueren Staging-Eintrag desselben Batches ersetzt


class ConflictType:
    NEW = "NEW"                                # kein bestehender Treffer für diesen Geltungsbereich
    DUPLICATE_EXACT = "DUPLICATE_EXACT"        # identischer Geltungsbereich + identische Behörde bereits vorhanden
    CONTRADICTS_VERIFIED = "CONTRADICTS_VERIFIED"      # widerspricht einer fachlich bestätigten/korrigierten Regel
    CONTRADICTS_UNVERIFIED = "CONTRADICTS_UNVERIFIED"  # widerspricht einer noch unbestätigten Regel


class JurisdictionStagingEntry(Base):
    """Ein einzelner, noch nicht übernommener Zuständigkeits-Vorschlag."""

    __tablename__ = "jurisdiction_staging_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Gruppiert alle Einträge EINES Imports/EINER Recherche-Sitzung, damit
    # ein ganzer Lauf gemeinsam betrachtet/verworfen werden kann.
    batch_id = Column(String(100), nullable=False, index=True)
    batch_label = Column(String(255), nullable=True)  # z.B. "BKG VG250 Pilot 2026-09-26"

    # ========== Vorgeschlagener Geltungsbereich (spiegelt Jurisdiction) ==========
    request_type_id = Column(String(50), ForeignKey("request_types.request_type_id"), nullable=False, index=True)
    country = Column(String(2), default="DE", nullable=False)
    state = Column(String(50), nullable=True)
    ags = Column(String(12), nullable=True, index=True)
    municipality = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    street = Column(String(255), nullable=True)
    house_number = Column(String(20), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    priority = Column(Integer, nullable=True)
    matching_level = Column(String(50), nullable=True)

    # ========== Vorgeschlagene Behörde ==========
    # Entweder ein Verweis auf eine BESTEHENDE Behörde (Normalfall) ...
    proposed_authority_id = Column(String(50), ForeignKey("authorities.authority_id"), nullable=True)
    # ... oder Rohdaten für eine NEU zu recherchierende Behörde (noch nicht in
    # `authorities` vorhanden) - wird erst bei approve_entry() zu einer
    # echten Authority-Zeile, nicht schon beim Anlegen des Staging-Eintrags.
    proposed_authority_name = Column(String(255), nullable=True)
    proposed_authority_city = Column(String(100), nullable=True)

    # ========== Quellennachweis ==========
    source = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    source_license = Column(String(255), nullable=True)
    source_retrieved_at = Column(DateTime, nullable=True)

    # ========== Konflikt- und Review-Status ==========
    status = Column(String(20), nullable=False, default=StagingStatus.PENDING, index=True)
    conflict_type = Column(String(30), nullable=False, default=ConflictType.NEW, index=True)
    # Falls conflict_type auf einen bestehenden Konflikt hinweist: WELCHE
    # bestehende Regel betroffen ist (für die Konfliktliste im UI/Review).
    conflicts_with_jurisdiction_id = Column(
        String(100), ForeignKey("jurisdictions.jurisdiction_id"), nullable=True
    )
    conflict_reason = Column(Text, nullable=True)

    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Wird beim Übernehmen (approve_entry) gesetzt: welche NEUE Jurisdiction-
    # Zeile aus diesem Vorschlag entstanden ist (Nachvollziehbarkeit).
    resulting_jurisdiction_id = Column(String(100), ForeignKey("jurisdictions.jurisdiction_id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_staging_batch", "batch_id"),
        Index("idx_staging_status", "status"),
        Index("idx_staging_ags_request_type", "ags", "request_type_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "batch_label": self.batch_label,
            "request_type_id": self.request_type_id,
            "state": self.state,
            "ags": self.ags,
            "municipality": self.municipality,
            "district": self.district,
            "postal_code": self.postal_code,
            "street": self.street,
            "house_number": self.house_number,
            "priority": self.priority,
            "matching_level": self.matching_level,
            "proposed_authority_id": self.proposed_authority_id,
            "proposed_authority_name": self.proposed_authority_name,
            "proposed_authority_city": self.proposed_authority_city,
            "source": self.source,
            "source_url": self.source_url,
            "source_license": self.source_license,
            "status": self.status,
            "conflict_type": self.conflict_type,
            "conflicts_with_jurisdiction_id": self.conflicts_with_jurisdiction_id,
            "conflict_reason": self.conflict_reason,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "resulting_jurisdiction_id": self.resulting_jurisdiction_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
