"""
CoverageAnalysisService

Macht die Abdeckung "AGS x Auskunftsart" messbar (Auftrag Priorität 1:
"zuerst bestehende Datenqualität und Abdeckung messbar machen").

Nutzt AUSSCHLIESSLICH die bestehende, getestete JurisdictionMatchingService -
es gibt hier KEINE zweite/parallele Matching-Logik. Jede Gemeinde
(AdministrativeUnit, die offizielle Destatis-Referenztabelle, nicht nur
Gemeinden mit importierten Gebäuden) wird für jede aktive Auskunftsart genau
einmal durch die reale Matching-Engine geschickt.

Klassifikation in exakt die vom Auftrag vorgegebenen fünf Kategorien:

    (a) VERIFIED             - eindeutig zugeordnet UND fachlich geprüft/
                                belegt (Jurisdiction.is_professionally_verified())
    (b) UNVERIFIED_OR_STALE  - eindeutig zugeordnet, aber Prüfung fehlt oder
                                ist abgelaufen
    (c) NO_MATCH             - kein Treffer
    (d) CONFLICTING          - mehrere widersprüchliche Treffer
                                (MatchingStatus.MULTIPLE_MATCHES)
    (e) FALLBACK_ONLY        - nur über eine allgemeine Fallback-Regel
                                zugeordnet (STATE oder POSTAL_CODE-Ebene)

WICHTIG - explizite Abgrenzung, die der Auftrag verlangt: "Zähle eine
vorhandene Behördenadresse nicht automatisch als nachgewiesene Zuständigkeit."
Eine Authority-Zeile mit Adresse sagt hier NICHTS aus - nur eine tatsächlich
existierende, aktive, zeitlich gültige Jurisdiction-Regel zählt überhaupt als
Treffer, und nur eine mit verification_status in (VERIFIED, CORRECTED) UND
nicht abgelaufenem last_verified_at zählt als Kategorie (a).

Einstufung COUNTY-Ebene (Landkreis, per AGS-Präfix): bewusst NICHT als
Fallback behandelt, sondern als reguläre Verwaltungshierarchie-Stufe
(Auftrag: "Nutze AGS/ARS und Verwaltungshierarchien als Basis"). Nur STATE
und POSTAL_CODE sind im Matcher selbst als "NUR Fallback" dokumentiert
(siehe JurisdictionMatchingService.MatchingLevel-Docstring) - diese Grenze
wird hier unverändert übernommen, nicht neu erfunden.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.administrative_unit import AdministrativeUnit
from app.models.building import Building
from app.models.jurisdiction import Jurisdiction
from app.models.request_type import RequestType
from app.services.jurisdiction_matcher import (
    JurisdictionMatchingService,
    MatchingLevel,
    MatchingStatus,
)

CATEGORY_VERIFIED = "VERIFIED"
CATEGORY_UNVERIFIED_OR_STALE = "UNVERIFIED_OR_STALE"
CATEGORY_NO_MATCH = "NO_MATCH"
CATEGORY_CONFLICTING = "CONFLICTING"
CATEGORY_FALLBACK_ONLY = "FALLBACK_ONLY"
# (f) NOT_APPLICABLE - explizit als "gibt es hier nicht" hinterlegt (siehe
#     MatchingStatus.NOT_APPLICABLE), unterscheidet sich bewusst von
#     NO_MATCH ("wir wissen es nicht") - kein Datenfehler.
CATEGORY_NOT_APPLICABLE = "NOT_APPLICABLE"

ALL_CATEGORIES = [
    CATEGORY_VERIFIED,
    CATEGORY_UNVERIFIED_OR_STALE,
    CATEGORY_NO_MATCH,
    CATEGORY_CONFLICTING,
    CATEGORY_FALLBACK_ONLY,
    CATEGORY_NOT_APPLICABLE,
]

# Nur diese beiden Matching-Level gelten hier als "allgemeine Fallback-Regel"
# - siehe Docstring oben für die Begründung dieser Grenze.
FALLBACK_LEVELS = {MatchingLevel.STATE, MatchingLevel.POSTAL_CODE}


@dataclass
class CoverageEntry:
    """Ergebnis der Klassifikation für genau ein (AGS, Auskunftsart)-Paar."""

    ags: str
    state_name: Optional[str]
    county_name: Optional[str]
    municipality_name: Optional[str]
    request_type_id: str
    request_type_name: str
    category: str
    matching_level: Optional[str]
    jurisdiction_id: Optional[str]
    reason: str
    portfolio_building_count: int = 0

    def to_dict(self) -> dict:
        return {
            "ags": self.ags,
            "state_name": self.state_name,
            "county_name": self.county_name,
            "municipality_name": self.municipality_name,
            "request_type_id": self.request_type_id,
            "request_type_name": self.request_type_name,
            "category": self.category,
            "matching_level": self.matching_level,
            "jurisdiction_id": self.jurisdiction_id,
            "reason": self.reason,
            "portfolio_building_count": self.portfolio_building_count,
        }


class CoverageAnalysisService:
    """Berechnet die AGS x Auskunftsart-Abdeckungsmatrix gegen den echten Bestand."""

    def __init__(self, db: Session):
        self.db = db
        self.matcher = JurisdictionMatchingService(db)

    def _building_counts_by_ags(self) -> Dict[str, int]:
        """
        Zählt ECHTE, tatsächlich importierte Gebäude je AGS (nie synthetisch
        erzeugt) - für die vom Auftrag verlangte Angabe, wie viele
        Portfolioobjekte von jeder Lücke betroffen sind. Aktuell (Stand dieser
        Analyse) sind 0 Gebäude importiert; diese Spalte ist dann für jede
        Zeile 0 und NICHT mit "keine Betroffenheit" zu verwechseln, sondern
        mit "noch kein Portfolio-Import erfolgt".
        """
        counts: Dict[str, int] = {}
        rows = (
            self.db.query(Building.ags, func.count(Building.building_id))
            .filter(Building.ags.isnot(None), Building.ags != "")
            .group_by(Building.ags)
            .all()
        )
        for ags, count in rows:
            counts[ags] = count
        return counts

    def _classify(self, result) -> tuple:
        """Liefert (Kategorie, Begründungstext) für ein einzelnes MatchingResult."""
        if result.matching_status == MatchingStatus.NOT_APPLICABLE:
            return CATEGORY_NOT_APPLICABLE, result.reason
        if result.matching_status == MatchingStatus.NO_MATCH:
            return CATEGORY_NO_MATCH, result.reason
        if result.matching_status == MatchingStatus.MULTIPLE_MATCHES:
            return CATEGORY_CONFLICTING, result.reason
        if result.matching_status == MatchingStatus.REVIEW_REQUIRED:
            # Aktuell erzeugt der Matcher diesen Status nirgends, aber falls
            # er es künftig tut: fachlich am nächsten zu "manuell prüfen".
            return CATEGORY_CONFLICTING, result.reason

        # MATCHED
        if result.matching_level in FALLBACK_LEVELS:
            return CATEGORY_FALLBACK_ONLY, result.reason

        jurisdiction = (
            self.db.query(Jurisdiction)
            .filter(Jurisdiction.jurisdiction_id == result.jurisdiction_id)
            .first()
        )
        if jurisdiction is not None and jurisdiction.is_professionally_verified():
            return CATEGORY_VERIFIED, result.reason
        return CATEGORY_UNVERIFIED_OR_STALE, result.reason

    def analyze(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        progress_every: int = 2000,
        state_names: Optional[List[str]] = None,
        request_type_ids: Optional[List[str]] = None,
    ) -> List[CoverageEntry]:
        """
        Prüft JEDE offizielle Gemeinde (AdministrativeUnit) gegen JEDE aktive
        Auskunftsart über die reale Matching-Engine. Baut dafür ein
        TRANSIENTES (nie an die Session gehängtes, nie committetes) Building-
        Objekt je Gemeinde - der Matcher liest davon ausschließlich Attribute,
        persistiert nichts.

        `state_names`/`request_type_ids` schränken den Lauf optional auf ein
        Teilgebiet bzw. bestimmte Auskunftsarten ein - für einen schnellen,
        gezielten Vorher-/Nachher-Vergleich nach einer einzelnen Änderung
        (z.B. nur Rheinland-Pfalz + eine neu recherchierte Auskunftsart),
        ohne den vollen bundesweiten Lauf (~60 Minuten) zu wiederholen. Ohne
        Angabe bleibt das Verhalten unverändert (voller bundesweiter Lauf).
        """
        units_query = self.db.query(AdministrativeUnit)
        if state_names:
            units_query = units_query.filter(AdministrativeUnit.state_name.in_(state_names))
        units = units_query.all()

        request_types_query = self.db.query(RequestType).filter(RequestType.active.is_(True))
        if request_type_ids:
            request_types_query = request_types_query.filter(RequestType.request_type_id.in_(request_type_ids))
        request_types = request_types_query.all()
        building_counts = self._building_counts_by_ags()

        results: List[CoverageEntry] = []
        total = len(units) * len(request_types)
        done = 0

        for unit in units:
            probe = Building(
                building_id="__coverage_probe__",
                street="",
                house_number="",
                city=unit.municipality_name,
                postal_code=unit.postal_code,
                district=None,
                state=unit.state_name,
                ags=unit.ags,
            )
            for rt in request_types:
                match_result = self.matcher.match_authority(probe, rt.request_type_id)
                category, reason = self._classify(match_result)
                results.append(
                    CoverageEntry(
                        ags=unit.ags,
                        state_name=unit.state_name,
                        county_name=unit.county_name,
                        municipality_name=unit.municipality_name,
                        request_type_id=rt.request_type_id,
                        request_type_name=rt.name,
                        category=category,
                        matching_level=match_result.matching_level,
                        jurisdiction_id=match_result.jurisdiction_id,
                        reason=reason,
                        portfolio_building_count=building_counts.get(unit.ags, 0),
                    )
                )
                done += 1
                if progress_callback and done % progress_every == 0:
                    progress_callback(done, total)

        if progress_callback:
            progress_callback(total, total)

        return results

    @staticmethod
    def summarize_by(entries: List[CoverageEntry], key: str) -> List[dict]:
        """
        Gruppiert Analyse-Ergebnisse nach einem Feld (z.B. "state_name",
        "request_type_name") und zählt jede Kategorie sowie die betroffenen
        Portfolioobjekte je Gruppe.
        """
        groups: Dict[str, dict] = {}
        for entry in entries:
            group_key = getattr(entry, key) or "(unbekannt)"
            group = groups.setdefault(
                group_key,
                {"group": group_key, "total": 0, "affected_buildings": 0,
                 **{c: 0 for c in ALL_CATEGORIES}},
            )
            group["total"] += 1
            group[entry.category] += 1
            gap_categories = (
                CATEGORY_NO_MATCH, CATEGORY_CONFLICTING,
                CATEGORY_FALLBACK_ONLY, CATEGORY_UNVERIFIED_OR_STALE,
            )
            if entry.category in gap_categories:
                group["affected_buildings"] += entry.portfolio_building_count
        return sorted(groups.values(), key=lambda g: g["group"])

    @staticmethod
    def overall_summary(entries: List[CoverageEntry]) -> dict:
        summary = {"total": len(entries), **{c: 0 for c in ALL_CATEGORIES}}
        for entry in entries:
            summary[entry.category] += 1
        return summary
