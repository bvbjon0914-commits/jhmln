"""
JurisdictionMatchingService

Das Kernstück des Systems: ermittelt für ein Gebäude und eine Auskunftsart
die zuständige Behörde über eine hierarchische Matching-Logik.

WICHTIG: Es gibt KEINE hart codierten Zuständigkeitsregeln in diesem Modul.
Alle Regeln kommen ausschließlich aus der `jurisdictions`-Tabelle.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.building import Building
from app.models.jurisdiction import Jurisdiction
from app.services.address_normalizer import AddressNormalizer, NormalizedAddress


# ========== Status-Konstanten ==========

class MatchingStatus:
    MATCHED = "MATCHED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NO_MATCH = "NO_MATCH"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"


# ========== Matching-Stufen (Hierarchie) ==========
# Jede Stufe definiert: (Bezeichnung, Priorität, Filterfunktion)

class MatchingLevel:
    STREET_NUMBER = "STREET_NUMBER"
    STREET = "STREET"
    DISTRICT = "DISTRICT"
    MUNICIPALITY = "MUNICIPALITY"
    COUNTY = "COUNTY"
    STATE = "STATE"
    POSTAL_CODE = "POSTAL_CODE"


@dataclass
class MatchingResult:
    """Ergebnis eines einzelnen Matching-Vorgangs."""

    building_id: str
    request_type_id: str
    authority_id: Optional[str] = None
    matching_level: Optional[str] = None
    matching_status: str = MatchingStatus.NO_MATCH
    matching_confidence: float = 0.0
    reason: str = ""
    alternative_authorities: List[str] = field(default_factory=list)
    jurisdiction_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "building_id": self.building_id,
            "request_type_id": self.request_type_id,
            "authority_id": self.authority_id,
            "matching_level": self.matching_level,
            "matching_status": self.matching_status,
            "matching_confidence": self.matching_confidence,
            "reason": self.reason,
            "alternative_authorities": self.alternative_authorities,
            "jurisdiction_id": self.jurisdiction_id,
        }


class JurisdictionMatchingService:
    """
    Ermittelt zuständige Behörden für Gebäude + Auskunftsart.

    Die Matching-Hierarchie (von spezifisch nach allgemein):
        1. STREET_NUMBER  (Straße + Hausnummer)
        2. STREET         (nur Straße)
        3. DISTRICT       (Stadtteil / Bezirk)
        4. MUNICIPALITY   (Gemeinde / AGS)          <- Standardfall
        5. COUNTY         (Landkreis, über AGS-Präfix)
        6. STATE          (Bundesland)
        7. POSTAL_CODE    (PLZ, NUR Fallback)
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------
    # Öffentliche API
    # ---------------------------------------------------------------

    def match_authority(self, building: Building, request_type_id: str) -> MatchingResult:
        """Matcht eine einzelne Auskunftsart für ein Gebäude."""

        normalized = AddressNormalizer.normalize(
            street=building.street,
            house_number=building.house_number,
            city=building.city,
            postal_code=building.postal_code,
            district=building.district,
        )

        ags = building.ags  # Für's MVP: AGS muss im Gebäudedatensatz vorhanden sein.
        ags_kreis = ags[:5] if ags and len(ags) >= 5 else None
        ags_land = ags[:2] if ags and len(ags) >= 2 else None

        # Die Stufen werden in Reihenfolge abgefragt. Sobald eine Stufe
        # einen oder mehrere Treffer liefert, wird dort abgebrochen -
        # spezifischere Stufen haben immer Vorrang vor allgemeineren.
        stages = [
            (
                MatchingLevel.STREET_NUMBER,
                self._query_street_number(request_type_id, ags, normalized),
            ),
            (
                MatchingLevel.STREET,
                self._query_street(request_type_id, ags, normalized),
            ),
            (
                MatchingLevel.DISTRICT,
                self._query_district(request_type_id, ags, normalized),
            ),
            (
                MatchingLevel.MUNICIPALITY,
                self._query_municipality(request_type_id, ags),
            ),
            (
                MatchingLevel.COUNTY,
                self._query_county(request_type_id, ags_kreis),
            ),
            (
                MatchingLevel.STATE,
                self._query_state(request_type_id, building.state),
            ),
            (
                MatchingLevel.POSTAL_CODE,
                self._query_postal_code(request_type_id, normalized.postal_code),
            ),
        ]

        for level, query in stages:
            if query is None:
                continue

            candidates = [j for j in query.all() if j.is_valid_today()]

            if len(candidates) == 0:
                continue

            if len(candidates) == 1:
                jurisdiction = candidates[0]
                return MatchingResult(
                    building_id=building.building_id,
                    request_type_id=request_type_id,
                    authority_id=jurisdiction.authority_id,
                    matching_level=level,
                    matching_status=MatchingStatus.MATCHED,
                    matching_confidence=1.0,
                    reason=self._build_reason(level, jurisdiction, ags),
                    jurisdiction_id=jurisdiction.jurisdiction_id,
                )

            # Mehrere Kandidaten auf derselben Stufe -> nicht raten
            return MatchingResult(
                building_id=building.building_id,
                request_type_id=request_type_id,
                authority_id=None,
                matching_level=level,
                matching_status=MatchingStatus.MULTIPLE_MATCHES,
                matching_confidence=0.5,
                reason=(
                    f"{len(candidates)} gleichrangige Zuständigkeiten auf Ebene "
                    f"{level} gefunden - manuelle Auswahl erforderlich."
                ),
                alternative_authorities=[j.authority_id for j in candidates],
            )

        # Keine Stufe hat einen Treffer geliefert
        return MatchingResult(
            building_id=building.building_id,
            request_type_id=request_type_id,
            authority_id=None,
            matching_level=None,
            matching_status=MatchingStatus.NO_MATCH,
            matching_confidence=0.0,
            reason=self._build_no_match_reason(ags, normalized),
        )

    def match_authorities(self, building: Building, request_type_ids: List[str]) -> List[MatchingResult]:
        """Matcht mehrere Auskunftsarten unabhängig voneinander."""
        return [self.match_authority(building, rt_id) for rt_id in request_type_ids]

    # ---------------------------------------------------------------
    # Interne Query-Bausteine (eine Methode pro Matching-Stufe)
    # ---------------------------------------------------------------

    def _base_query(self, request_type_id: str):
        return self.db.query(Jurisdiction).filter(
            Jurisdiction.request_type_id == request_type_id,
            Jurisdiction.active.is_(True),
        )

    def _query_street_number(self, request_type_id: str, ags: Optional[str], addr: NormalizedAddress):
        if not ags or not addr.street or not addr.house_number:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.ags == ags,
            Jurisdiction.street == addr.street,
            Jurisdiction.house_number == addr.house_number,
        )

    def _query_street(self, request_type_id: str, ags: Optional[str], addr: NormalizedAddress):
        if not ags or not addr.street:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.ags == ags,
            Jurisdiction.street == addr.street,
            or_(Jurisdiction.house_number.is_(None), Jurisdiction.house_number == ""),
        )

    def _query_district(self, request_type_id: str, ags: Optional[str], addr: NormalizedAddress):
        if not ags or not addr.district:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.ags == ags,
            Jurisdiction.district == addr.district,
            or_(Jurisdiction.street.is_(None), Jurisdiction.street == ""),
        )

    def _query_municipality(self, request_type_id: str, ags: Optional[str]):
        if not ags:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.ags == ags,
            or_(Jurisdiction.district.is_(None), Jurisdiction.district == ""),
            or_(Jurisdiction.street.is_(None), Jurisdiction.street == ""),
        )

    def _query_county(self, request_type_id: str, ags_kreis: Optional[str]):
        if not ags_kreis:
            return None
        # Landkreis-Regeln werden über ein eigenes Feld (ags mit 5 Stellen
        # statt 8) abgebildet, um sie klar von Gemeinde-Regeln zu trennen.
        return self._base_query(request_type_id).filter(
            Jurisdiction.ags == ags_kreis,
        )

    def _query_state(self, request_type_id: str, state: Optional[str]):
        if not state:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.state == state,
            or_(Jurisdiction.ags.is_(None), Jurisdiction.ags == ""),
            or_(Jurisdiction.municipality.is_(None), Jurisdiction.municipality == ""),
        )

    def _query_postal_code(self, request_type_id: str, postal_code: Optional[str]):
        if not postal_code:
            return None
        return self._base_query(request_type_id).filter(
            Jurisdiction.postal_code == postal_code,
            or_(Jurisdiction.ags.is_(None), Jurisdiction.ags == ""),
        )

    # ---------------------------------------------------------------
    # Erklärungstexte (Nachvollziehbarkeit ist Pflicht, kein Extra)
    # ---------------------------------------------------------------

    @staticmethod
    def _build_reason(level: str, jurisdiction: Jurisdiction, ags: Optional[str]) -> str:
        explanations = {
            MatchingLevel.STREET_NUMBER: f"Sonderregel für Straße + Hausnummer (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.STREET: f"Sonderregel für die Straße (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.DISTRICT: f"Zuständigkeit auf Stadtteil-Ebene (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.MUNICIPALITY: f"Eindeutige Zuordnung über AGS {ags} (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.COUNTY: f"Zuordnung über Landkreis-Zuständigkeit (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.STATE: f"Landesweite Zuständigkeit (Regel-ID {jurisdiction.jurisdiction_id})",
            MatchingLevel.POSTAL_CODE: f"Fallback über Postleitzahl (Regel-ID {jurisdiction.jurisdiction_id}) - bitte prüfen",
        }
        return explanations.get(level, f"Zugeordnet über Regel {jurisdiction.jurisdiction_id}")

    @staticmethod
    def _build_no_match_reason(ags: Optional[str], addr: NormalizedAddress) -> str:
        if not ags:
            return "Kein AGS für dieses Gebäude hinterlegt - Zuständigkeit konnte nicht ermittelt werden."
        return f"Für AGS {ags} ({addr.city}) ist keine Zuständigkeit für diese Auskunftsart hinterlegt."
