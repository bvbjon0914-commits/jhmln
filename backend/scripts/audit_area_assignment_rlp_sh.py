"""
Prüft bestehende Jurisdiction-Regeln in Rheinland-Pfalz und Schleswig-
Holstein gezielt auf FEHLERHAFTE GEBIETSZUORDNUNG - getrennt von fehlenden
Regeln (das misst bereits CoverageAnalysisService/NO_MATCH) und fehlendem
Prüfvermerk (das misst bereits verification_status/UNVERIFIED_OR_STALE).

"Fehlerhafte Gebietszuordnung" heißt hier konkret, unabhängig von Prüfstatus
oder Vorhandensein einer Regel:

  1. INVALID_AGS: die Regel referenziert einen AGS/AGS-Kreis, der in der
     amtlichen AdministrativeUnit-Referenztabelle GAR NICHT existiert.
  2. STATE_MISMATCH: die Regel gibt ein `state` an, das nicht zum
     tatsächlichen Bundesland des referenzierten AGS passt.
  3. MUNICIPALITY_NAME_MISMATCH: die Regel gibt einen `municipality`-Namen
     an, der nicht zum amtlichen Namen für diesen AGS passt (Namensdrift,
     z.B. nach Gebietsreform oder Tippfehler).

Rein LESEND. Ergebnis ist eine Liste zur menschlichen Prüfung - keine
automatische Korrektur (dieselbe Vorsicht wie beim gesamten sicheren
Aktualisierungsprozess: eine falsche Gebietszuordnung wird angezeigt, nicht
selbständig "repariert").
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATES = ["Rheinland-Pfalz", "Schleswig-Holstein"]


def _norm(value):
    if value is None:
        return ""
    return str(value).split(",")[0].strip().lower().replace("ß", "ss")


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.jurisdiction import Jurisdiction

    db = SessionLocal()
    try:
        units_by_ags = {u.ags: u for u in db.query(AdministrativeUnit).all()}
        units_by_kreis = {}
        for u in units_by_ags.values():
            units_by_kreis.setdefault(u.ags_kreis, u)

        rules = (
            db.query(Jurisdiction)
            .filter(Jurisdiction.active.is_(True), Jurisdiction.state.in_(STATES))
            .all()
        )
        # Auch Regeln ohne `state`, aber mit RLP/SH-AGS-Präfix erfassen (state ist bei
        # manchen älteren Importzeilen nicht durchgängig befüllt - siehe Befund unten).
        rules_by_ags_prefix = (
            db.query(Jurisdiction)
            .filter(Jurisdiction.active.is_(True), Jurisdiction.state.is_(None), Jurisdiction.ags.isnot(None))
            .filter(Jurisdiction.ags.like("07%") | Jurisdiction.ags.like("01%"))
            .all()
        )
        all_rules = {r.jurisdiction_id: r for r in rules + rules_by_ags_prefix}.values()

        findings = []
        for rule in all_rules:
            if not rule.ags:
                continue
            ags = rule.ags
            unit = units_by_ags.get(ags)
            if unit is None and len(ags) == 5:
                unit = units_by_kreis.get(ags)
            if unit is None and len(ags) == 8:
                unit = units_by_kreis.get(ags[:5])

            if unit is None:
                findings.append({
                    "jurisdiction_id": rule.jurisdiction_id, "type": "INVALID_AGS",
                    "request_type_id": rule.request_type_id, "ags": ags,
                    "rule_state": rule.state, "rule_municipality": rule.municipality,
                    "detail": f"AGS/AGS-Kreis '{ags}' existiert nicht in AdministrativeUnit.",
                })
                continue

            if rule.state and unit.state_name and rule.state != unit.state_name:
                findings.append({
                    "jurisdiction_id": rule.jurisdiction_id, "type": "STATE_MISMATCH",
                    "request_type_id": rule.request_type_id, "ags": ags,
                    "rule_state": rule.state, "rule_municipality": rule.municipality,
                    "detail": f"Regel state='{rule.state}', tatsächliches Bundesland laut AGS: '{unit.state_name}'.",
                })

            if rule.municipality and len(ags) == 8 and _norm(rule.municipality) != _norm(unit.municipality_name):
                findings.append({
                    "jurisdiction_id": rule.jurisdiction_id, "type": "MUNICIPALITY_NAME_MISMATCH",
                    "request_type_id": rule.request_type_id, "ags": ags,
                    "rule_state": rule.state, "rule_municipality": rule.municipality,
                    "detail": f"Regel municipality='{rule.municipality}', amtlicher Name laut AGS: '{unit.municipality_name}'.",
                })

        print(f"Geprüfte Regeln (state in {STATES} oder AGS-Präfix 07/01 ohne state): {len(all_rules)}")
        print(f"Gefundene Gebietszuordnungs-Auffälligkeiten: {len(findings)}")
        by_type = {}
        for f in findings:
            by_type[f["type"]] = by_type.get(f["type"], 0) + 1
        for k, v in by_type.items():
            print(f"  {k}: {v}")

        import csv
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "coverage_reports",
            "area_assignment_audit_rlp_sh.csv",
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "jurisdiction_id", "type", "request_type_id", "ags", "rule_state", "rule_municipality", "detail",
            ])
            writer.writeheader()
            for finding in sorted(findings, key=lambda x: (x["type"], x["ags"])):
                writer.writerow(finding)
        print(f"\nBericht geschrieben: {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
