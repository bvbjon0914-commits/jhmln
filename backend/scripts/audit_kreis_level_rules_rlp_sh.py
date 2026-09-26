"""
Zweiter, gezielterer Teil der Gebietszuordnungs-Prüfung für Rheinland-Pfalz
und Schleswig-Holstein (Ergänzung zu audit_area_assignment_rlp_sh.py, das
nur Namens-/Bundeslandabweichungen prüft).

Konkreter Verdacht, der sich aus einer manuellen Stichprobe ergab: mehrere
Auskunftsarten haben pro Landkreis nur EINE einzige MUNICIPALITY-Regel,
die auf eine willkürliche (meist alphabetisch erste) Ortsgemeinde-AGS
gepinnt ist, obwohl die Zielbehörde eine KREISVERWALTUNG ist, die
tatsächlich für ALLE Gemeinden des Kreises zuständig wäre. Das ist eine
fehlerhafte Gebietszuordnung im engeren Sinn: nicht "keine Regel"
(NO_MATCH wird bereits von CoverageAnalysisService gemessen) und nicht
"kein Prüfvermerk" (verification_status wird bereits gemessen), sondern
"Regel existiert, deckt aber aufgrund der falschen Ebene/AGS nur einen
winzigen Bruchteil des tatsächlich gemeinten Gebiets ab".

Heuristik: für jede (Auskunftsart, Landkreis)-Kombination in RLP/SH, bei der
die einzige/fast einzige zugeordnete Behörde eine "Kreisverwaltung"/
"Landkreis"-Behörde ist, aber die Anzahl der MUNICIPALITY-Regeln für diesen
Kreis winzig ist im Vergleich zur tatsächlichen Gemeindeanzahl (< 5%), wird
das als VERDACHT AUF FALSCHE EBENE gemeldet. Rein lesend, keine Korrektur.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATE_PREFIXES = {"07": "Rheinland-Pfalz", "01": "Schleswig-Holstein"}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.models.request_type import RequestType

    db = SessionLocal()
    try:
        kreis_sizes = {}
        for ags_kreis, _ags in (
            db.query(AdministrativeUnit.ags_kreis, AdministrativeUnit.ags)
            .filter(AdministrativeUnit.ags_land.in_(STATE_PREFIXES.keys()))
        ):
            kreis_sizes[ags_kreis] = kreis_sizes.get(ags_kreis, 0) + 1

        request_types = [rt.request_type_id for rt in db.query(RequestType).filter(RequestType.active.is_(True)).all()]

        findings = []
        for rt_id in request_types:
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
            by_kreis = {}
            for r in rules:
                if len(r.ags) < 5 or r.ags[:2] not in STATE_PREFIXES:
                    continue
                by_kreis.setdefault(r.ags[:5], []).append(r)

            for ags_kreis, kreis_rules in by_kreis.items():
                total_gemeinden = kreis_sizes.get(ags_kreis, 0)
                if total_gemeinden == 0:
                    continue
                coverage_fraction = len(kreis_rules) / total_gemeinden
                if coverage_fraction >= 0.05 or len(kreis_rules) > 3:
                    continue  # nicht auffällig - genug Einzelregeln für den Kreis vorhanden

                kreis_authorities = set()
                for r in kreis_rules:
                    a = db.query(Authority).filter(Authority.authority_id == r.authority_id).first()
                    if a:
                        kreis_authorities.add(a.authority_name)
                is_kreisweite_behoerde = any(
                    "kreisverwaltung" in name.lower() or "landkreis" in name.lower()
                    or name.lower().startswith("kreis ")
                    for name in kreis_authorities
                )
                if not is_kreisweite_behoerde:
                    continue  # z.B. Grundbuchamt - dort ist eine Gemeinde-genaue Regel oft tatsächlich beabsichtigt

                findings.append({
                    "request_type_id": rt_id,
                    "ags_kreis": ags_kreis,
                    "state": STATE_PREFIXES[ags_kreis[:2]],
                    "gemeinden_im_kreis": total_gemeinden,
                    "vorhandene_regeln": len(kreis_rules),
                    "ungedeckte_gemeinden": total_gemeinden - len(kreis_rules),
                    "authorities": "; ".join(kreis_authorities),
                    "beispiel_ags": kreis_rules[0].ags,
                })

        findings.sort(key=lambda f: -f["ungedeckte_gemeinden"])
        print(f"Verdachtsfälle 'falsche Ebene' (Kreisverwaltung-Behörde, aber fast keine Gemeinde erfasst): {len(findings)}")
        total_ungedeckt = sum(f["ungedeckte_gemeinden"] for f in findings)
        print(f"Dadurch potenziell betroffene Gemeinden (Summe, RLP+SH, über alle Auskunftsarten): {total_ungedeckt}")
        print()
        for f in findings[:20]:
            print(
                f"  {f['request_type_id']:14s} Kreis {f['ags_kreis']} ({f['state']}): "
                f"{f['vorhandene_regeln']}/{f['gemeinden_im_kreis']} Gemeinden erfasst, "
                f"{f['ungedeckte_gemeinden']} ungedeckt -> {f['authorities']}"
            )

        import csv
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "coverage_reports",
            "kreis_level_wrong_scope_rlp_sh.csv",
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "request_type_id", "ags_kreis", "state", "gemeinden_im_kreis",
                "vorhandene_regeln", "ungedeckte_gemeinden", "authorities", "beispiel_ags",
            ])
            writer.writeheader()
            for finding in findings:
                writer.writerow(finding)
        print(f"\nBericht geschrieben: {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
