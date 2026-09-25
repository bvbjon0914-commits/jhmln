"""
JurisdictionStagingService

Sicherer Aktualisierungsprozess für Zuständigkeitsregeln (Auftrag
Priorität 4): neue Daten aus Import oder Recherche landen zuerst als
JurisdictionStagingEntry, werden gegen den Bestand verglichen
(Konflikterkennung), und erst nach expliziter menschlicher Freigabe
(approve_entry) in die produktive jurisdictions-Tabelle übernommen.

Es gibt bewusst KEINEN Code-Pfad, der einen Staging-Eintrag automatisch
übernimmt. `stage_entries_from_source` erzeugt ausschließlich PENDING-
Einträge; jede Übernahme ist ein separater, expliziter Aufruf von
approve_entry() mit einem menschlichen Prüfer-Namen.

Historie: eine durch Freigabe ersetzte Regel wird NIE gelöscht oder
überschrieben, sondern zum Stichtag vor dem neuen Gültigkeitsbeginn
ausdrücklich ausgelaufen (valid_to gesetzt) - die alte Zuordnung bleibt
dadurch für Nachvollziehbarkeit und spätere Auswertungen erhalten (Auftrag:
"Bewahre frühere Regeln und ihre Gültigkeitszeiträume auf, um
Nachvollziehbarkeit zu erhalten").
"""

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.jurisdiction import Jurisdiction
from app.models.jurisdiction_staging import ConflictType, JurisdictionStagingEntry, StagingStatus


class JurisdictionStagingService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Konflikterkennung
    # ------------------------------------------------------------------

    def _find_matching_existing(
        self, *, request_type_id, ags, municipality, district, postal_code, street, house_number,
    ) -> List[Jurisdiction]:
        """
        Bestehende Regeln mit demselben fachlichen Geltungsbereich (dieselben
        geografischen Schlüsselfelder wie im Matcher selbst) für dieselbe
        Auskunftsart - unabhängig von deren Gültigkeitszeitraum, damit auch
        eine bereits abgelaufene Regel als Historie erkannt wird.
        """
        return (
            self.db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == request_type_id,
                Jurisdiction.active.is_(True),
                Jurisdiction.ags == ags,
                Jurisdiction.municipality == municipality,
                Jurisdiction.district == district,
                Jurisdiction.postal_code == postal_code,
                Jurisdiction.street == street,
                Jurisdiction.house_number == house_number,
            )
            .all()
        )

    def _detect_conflict(
        self, *, request_type_id, ags, municipality, district, postal_code,
        street, house_number, proposed_authority_id,
    ):
        existing = self._find_matching_existing(
            request_type_id=request_type_id, ags=ags, municipality=municipality,
            district=district, postal_code=postal_code, street=street, house_number=house_number,
        )
        if not existing:
            return ConflictType.NEW, None, None

        for ex in existing:
            if proposed_authority_id and ex.authority_id == proposed_authority_id:
                return (
                    ConflictType.DUPLICATE_EXACT, ex,
                    f"Identischer Geltungsbereich und identische Behörde bereits vorhanden "
                    f"(jurisdiction_id={ex.jurisdiction_id}).",
                )

        verified = [ex for ex in existing if ex.is_professionally_verified()]
        if verified:
            ex = verified[0]
            return (
                ConflictType.CONTRADICTS_VERIFIED, ex,
                f"Widerspricht einer fachlich bestätigten Regel (jurisdiction_id={ex.jurisdiction_id}, "
                f"Behörde {ex.authority_id}, zuletzt geprüft {ex.last_verified_at} von {ex.verified_by}).",
            )

        ex = existing[0]
        return (
            ConflictType.CONTRADICTS_UNVERIFIED, ex,
            f"Widerspricht einer bislang unbestätigten Regel (jurisdiction_id={ex.jurisdiction_id}, "
            f"Behörde {ex.authority_id}, verification_status={ex.verification_status}).",
        )

    # ------------------------------------------------------------------
    # Staging
    # ------------------------------------------------------------------

    def stage_entry(
        self, *, batch_id: str, request_type_id: str, batch_label: Optional[str] = None,
        state: Optional[str] = None, ags: Optional[str] = None, municipality: Optional[str] = None,
        district: Optional[str] = None, postal_code: Optional[str] = None, street: Optional[str] = None,
        house_number: Optional[str] = None, priority: Optional[int] = None,
        matching_level: Optional[str] = None,
        proposed_authority_id: Optional[str] = None, proposed_authority_name: Optional[str] = None,
        proposed_authority_city: Optional[str] = None,
        source: Optional[str] = None, source_url: Optional[str] = None,
        source_license: Optional[str] = None, source_retrieved_at: Optional[datetime] = None,
        valid_from: Optional[date] = None, valid_to: Optional[date] = None,
    ) -> JurisdictionStagingEntry:
        """Legt EINEN Staging-Eintrag an und berechnet dessen Konflikt-Status. Kein Commit hier -
        der Aufrufer entscheidet, ob mehrere stage_entry()-Aufrufe als ein Batch committet werden."""
        if proposed_authority_id is None and not proposed_authority_name:
            raise ValueError(
                "Weder proposed_authority_id noch proposed_authority_name gesetzt - "
                "ein Staging-Eintrag muss auf eine bestehende oder eine benannte, noch "
                "anzulegende Behörde verweisen, sonst könnte approve_entry() später keine "
                "Behörde bestimmen."
            )

        conflict_type, conflict_jurisdiction, conflict_reason = self._detect_conflict(
            request_type_id=request_type_id, ags=ags, municipality=municipality, district=district,
            postal_code=postal_code, street=street, house_number=house_number,
            proposed_authority_id=proposed_authority_id,
        )
        entry = JurisdictionStagingEntry(
            batch_id=batch_id, batch_label=batch_label, request_type_id=request_type_id,
            state=state, ags=ags, municipality=municipality, district=district, postal_code=postal_code,
            street=street, house_number=house_number, priority=priority, matching_level=matching_level,
            proposed_authority_id=proposed_authority_id, proposed_authority_name=proposed_authority_name,
            proposed_authority_city=proposed_authority_city,
            source=source, source_url=source_url, source_license=source_license,
            source_retrieved_at=source_retrieved_at, valid_from=valid_from, valid_to=valid_to,
            status=StagingStatus.PENDING,
            conflict_type=conflict_type,
            conflicts_with_jurisdiction_id=conflict_jurisdiction.jurisdiction_id if conflict_jurisdiction else None,
            conflict_reason=conflict_reason,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    # ------------------------------------------------------------------
    # Freigabe / Ablehnung
    # ------------------------------------------------------------------

    def approve_entry(
        self, staging_id: int, *, reviewer: str, review_notes: Optional[str] = None,
    ) -> Jurisdiction:
        """
        Übernimmt EINEN geprüften Staging-Eintrag als neue, fachlich bestätigte
        Jurisdiction-Zeile. Erfordert einen expliziten Prüfer-Namen (reviewer) -
        es gibt keinen Aufruf ohne menschlichen Namen.
        """
        entry = self._require_pending_entry(staging_id)

        if entry.conflict_type == ConflictType.DUPLICATE_EXACT:
            raise ValueError(
                f"Staging-Eintrag {staging_id} ist ein exaktes Duplikat einer bestehenden Regel "
                f"(jurisdiction_id={entry.conflicts_with_jurisdiction_id}) - eine Übernahme würde nur "
                "eine redundante Zeile erzeugen. Bitte stattdessen reject_entry() mit Begründung "
                "'bereits vorhanden' aufrufen."
            )
        if entry.proposed_authority_id is None:
            raise ValueError(
                f"Staging-Eintrag {staging_id} hat kein proposed_authority_id - eine neue Behörde "
                f"('{entry.proposed_authority_name}', {entry.proposed_authority_city}) muss VOR der "
                "Freigabe explizit und geprüft als Authority-Zeile angelegt werden (nie automatisch "
                "aus Rohdaten erzeugt), und die entstandene authority_id muss auf diesem Eintrag "
                "gesetzt werden."
            )

        # Historie bewahren statt überschreiben: die widersprochene Regel läuft
        # exakt einen Tag vor der neuen Gültigkeit aus, damit sich beide Regeln
        # niemals überlappen (sonst würde der Matcher am Übergangstag fälschlich
        # MULTIPLE_MATCHES melden) und dennoch keine Lücke entsteht.
        if entry.conflicts_with_jurisdiction_id:
            old_rule = (
                self.db.query(Jurisdiction)
                .filter(Jurisdiction.jurisdiction_id == entry.conflicts_with_jurisdiction_id)
                .first()
            )
            if old_rule is not None and old_rule.active:
                new_valid_from = entry.valid_from or date.today()
                old_rule.valid_to = new_valid_from - timedelta(days=1)
                old_rule.notes = (
                    (old_rule.notes + " | " if old_rule.notes else "")
                    + f"Abgelöst durch Staging-Batch {entry.batch_id} (Eintrag #{entry.id}), "
                    f"freigegeben von {reviewer} am {date.today().isoformat()}."
                )

        new_rule = Jurisdiction(
            jurisdiction_id=str(uuid.uuid4()),
            request_type_id=entry.request_type_id,
            authority_id=entry.proposed_authority_id,
            state=entry.state, ags=entry.ags, municipality=entry.municipality, district=entry.district,
            postal_code=entry.postal_code, street=entry.street, house_number=entry.house_number,
            valid_from=entry.valid_from or date.today(), valid_to=entry.valid_to,
            priority=entry.priority if entry.priority is not None else 100,
            matching_level=entry.matching_level,
            source=entry.source, source_url=entry.source_url, source_license=entry.source_license,
            source_retrieved_at=entry.source_retrieved_at,
            last_verified_at=datetime.utcnow(), verified_by=reviewer,
            verification_status="VERIFIED",
            active=True,
            notes=f"Übernommen aus Staging-Batch {entry.batch_id} (Eintrag #{entry.id}).",
        )
        self.db.add(new_rule)
        self.db.flush()

        entry.status = StagingStatus.APPROVED
        entry.reviewed_by = reviewer
        entry.reviewed_at = datetime.utcnow()
        entry.review_notes = review_notes
        entry.resulting_jurisdiction_id = new_rule.jurisdiction_id

        return new_rule

    def reject_entry(self, staging_id: int, *, reviewer: str, reason: str) -> JurisdictionStagingEntry:
        entry = self._require_pending_entry(staging_id)
        entry.status = StagingStatus.REJECTED
        entry.reviewed_by = reviewer
        entry.reviewed_at = datetime.utcnow()
        entry.review_notes = reason
        return entry

    def _require_pending_entry(self, staging_id: int) -> JurisdictionStagingEntry:
        entry = (
            self.db.query(JurisdictionStagingEntry)
            .filter(JurisdictionStagingEntry.id == staging_id)
            .first()
        )
        if entry is None:
            raise ValueError(f"Staging-Eintrag {staging_id} nicht gefunden.")
        if entry.status != StagingStatus.PENDING:
            raise ValueError(
                f"Staging-Eintrag {staging_id} ist bereits {entry.status} - keine erneute Entscheidung möglich."
            )
        return entry

    # ------------------------------------------------------------------
    # Übersicht
    # ------------------------------------------------------------------

    def batch_summary(self, batch_id: str) -> dict:
        entries = (
            self.db.query(JurisdictionStagingEntry)
            .filter(JurisdictionStagingEntry.batch_id == batch_id)
            .all()
        )
        by_status: dict = {}
        by_conflict: dict = {}
        for e in entries:
            by_status[e.status] = by_status.get(e.status, 0) + 1
            by_conflict[e.conflict_type] = by_conflict.get(e.conflict_type, 0) + 1
        return {
            "batch_id": batch_id, "total": len(entries),
            "by_status": by_status, "by_conflict_type": by_conflict,
        }

    def pending_conflicts(self, batch_id: Optional[str] = None) -> List[JurisdictionStagingEntry]:
        """Alle PENDING-Einträge, die NICHT konfliktfrei (NEW) sind - die Prüfliste für einen Menschen."""
        query = self.db.query(JurisdictionStagingEntry).filter(
            JurisdictionStagingEntry.status == StagingStatus.PENDING,
            JurisdictionStagingEntry.conflict_type != ConflictType.NEW,
        )
        if batch_id:
            query = query.filter(JurisdictionStagingEntry.batch_id == batch_id)
        return query.all()
