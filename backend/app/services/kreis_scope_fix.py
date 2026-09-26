"""
Struktur-Korrektur: findet und behebt den in dieser Sitzung diagnostizierten
Kreisebenen-Scope-Bug (siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md #4.2 und
scripts/audit_kreis_level_rules_rlp_sh.py).

Befund: eine Jurisdiction-Regel ist fachlich für einen GANZEN Landkreis
gemeint (die Zielbehörde ist erkennbar eine Kreisverwaltung/"Kreis X" -
"Untere Bauaufsichtsbehörde"), aber technisch auf EINE einzelne,
augenscheinlich willkürliche Gemeinde-AGS gepinnt (matching_level=
MUNICIPALITY statt COUNTY). Dadurch bekommen alle anderen Gemeinden des
Kreises fälschlich NO_MATCH, obwohl die zuständige Behörde bereits korrekt
in der Datenbank steht.

Die Korrektur ergänzt eine ZUSÄTZLICHE COUNTY-Regel für dieselbe, bereits
vorhandene Behörde - die bestehende Gemeinde-Regel bleibt unverändert (sie
ist spezifischer und liefert für ihre eine Gemeinde ohnehin dieselbe
Behörde, kein Widerspruch). Läuft über JurisdictionStagingService -
Konfliktprüfung, benannter Prüfer, dokumentierte Begründung (interne
Korrektur, keine neue externe Quelle).
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.administrative_unit import AdministrativeUnit
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.services.jurisdiction_matcher import MatchingLevel
from app.services.jurisdiction_staging import JurisdictionStagingService


@dataclass
class KreisScopeFinding:
    request_type_id: str
    ags_kreis: str
    state: str
    authority_id: str
    authority_name: str
    old_rule_jurisdiction_id: str
    total_gemeinden: int
    existing_rule_count: int


def _is_kreisweite_behoerde_name(name: str) -> bool:
    lname = name.lower()
    if "stadtverwaltung" in lname or "verbandsgemeindeverwaltung" in lname or "stadt " in lname:
        return False
    return "kreisverwaltung" in lname or "landkreis" in lname or lname.startswith("kreis ")


def find_kreis_scope_bugs(
    db: Session, request_type_ids: List[str], state_prefixes: Dict[str, str],
    max_coverage_fraction: float = 0.05,
) -> List[KreisScopeFinding]:
    """Liest nur - findet Kandidaten für die Korrektur, ohne etwas zu ändern."""
    kreis_sizes: Dict[str, int] = {}
    for ags_kreis, _ags in (
        db.query(AdministrativeUnit.ags_kreis, AdministrativeUnit.ags)
        .filter(AdministrativeUnit.ags_land.in_(state_prefixes.keys()))
    ):
        kreis_sizes[ags_kreis] = kreis_sizes.get(ags_kreis, 0) + 1

    findings: List[KreisScopeFinding] = []
    for rt_id in request_type_ids:
        rules = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == rt_id,
                Jurisdiction.active.is_(True),
                Jurisdiction.matching_level == "MUNICIPALITY",
                Jurisdiction.ags.isnot(None),
            )
            .all()
        )
        by_kreis: Dict[str, List[Jurisdiction]] = {}
        for r in rules:
            if len(r.ags) < 5 or r.ags[:2] not in state_prefixes:
                continue
            by_kreis.setdefault(r.ags[:5], []).append(r)

        for ags_kreis, kreis_rules in by_kreis.items():
            total_gemeinden = kreis_sizes.get(ags_kreis, 0)
            if total_gemeinden == 0 or len(kreis_rules) / total_gemeinden >= max_coverage_fraction:
                continue

            kreisweite_rule = None
            for r in kreis_rules:
                a = db.query(Authority).filter(Authority.authority_id == r.authority_id).first()
                if a and _is_kreisweite_behoerde_name(a.authority_name):
                    kreisweite_rule = (r, a)
                    break
            if kreisweite_rule is None:
                continue
            rule, authority = kreisweite_rule

            existing_county = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.request_type_id == rt_id, Jurisdiction.ags == ags_kreis,
                    Jurisdiction.matching_level == "COUNTY", Jurisdiction.active.is_(True),
                )
                .first()
            )
            if existing_county:
                continue  # bereits korrigiert - idempotent

            findings.append(KreisScopeFinding(
                request_type_id=rt_id, ags_kreis=ags_kreis, state=state_prefixes[ags_kreis[:2]],
                authority_id=authority.authority_id, authority_name=authority.authority_name,
                old_rule_jurisdiction_id=rule.jurisdiction_id,
                total_gemeinden=total_gemeinden, existing_rule_count=len(kreis_rules),
            ))
    return findings


def apply_kreis_scope_fix(
    db: Session, findings: List[KreisScopeFinding], reviewer: str, batch_id: Optional[str] = None,
) -> dict:
    """
    Staged und gibt für jeden Fund eine neue COUNTY-Regel frei - über den
    normalen JurisdictionStagingService, inklusive Konfliktprüfung. Gibt
    ein Ergebnis-Dict mit gestageten/freigegebenen/übersprungenen Einträgen.
    """
    batch_id = batch_id or f"fix-kreis-scope-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    staging = JurisdictionStagingService(db)

    staged = []
    for f in findings:
        entry = staging.stage_entry(
            batch_id=batch_id,
            batch_label="Struktur-Korrektur: Kreisebenen-Scope",
            request_type_id=f.request_type_id, state=f.state, ags=f.ags_kreis,
            matching_level=MatchingLevel.COUNTY, priority=50,
            proposed_authority_id=f.authority_id,
            source=(
                f"Interne Struktur-Korrektur: Authority '{f.authority_name}' war bereits vor dieser "
                f"Korrektur als Untere Bauaufsichtsbehoerde fuer diesen Kreis in der Datenbank vorhanden "
                f"(Regel {f.old_rule_jurisdiction_id}, faelschlich auf eine einzelne Gemeinde-AGS statt auf "
                f"den Kreis-Schluessel {f.ags_kreis} skaliert). Keine neue externe Quelle - Korrektur der "
                f"Geltungsbereichs-EBENE einer bereits belegten Zuordnung."
            ),
            source_license="Interne Korrektur (keine externe Datenquelle)",
            source_retrieved_at=datetime.utcnow(),
        )
        staged.append((entry, f))

    approved = []
    conflicts = []
    for entry, f in staged:
        if entry.conflict_type != "NEW":
            conflicts.append((entry, f))
            continue
        staging.approve_entry(
            entry.id, reviewer=reviewer,
            review_notes=(
                f"Kreisweite Regel ergaenzt fuer {f.ags_kreis}: {f.existing_rule_count} von "
                f"{f.total_gemeinden} Gemeinden hatten zuvor eine Einzelregel, die uebrigen "
                f"{f.total_gemeinden - f.existing_rule_count} waren NO_MATCH obwohl die zustaendige "
                f"Behoerde bereits bekannt war."
            ),
        )
        approved.append((entry, f))

    return {"batch_id": batch_id, "staged": staged, "approved": approved, "conflicts": conflicts}
