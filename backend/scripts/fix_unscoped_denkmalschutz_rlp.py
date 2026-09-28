"""
Behebt einen dritten, gefundenen Fehlerpattern für DENKMALSCHUTZ in
Rheinland-Pfalz (neben dem bereits behobenen Kreisebenen-Scope-Bug und den
Namensabweichungen): drei aktive Jurisdiction-Zeilen haben ÜBERHAUPT KEINEN
Geltungsbereich (ags, municipality, district, postal_code, street, state
sind ALLE None) - sie matchen dadurch NIEMALS, für keine Anfrage, in keiner
Matching-Stufe. Ursache laut `source`-Feld: "Denkmalschutzbehoerden
Deutschland AGS-Matching" - der AGS-Abgleich ist beim Import für genau
diese drei Landkreise fehlgeschlagen, statt die Zeile zu überspringen oder
einen Fehler zu melden.

Betrifft (identifiziert per Handauswahl, NICHT per automatischer
Namens-Fuzzy-Suche - bei so wenigen Fällen ist die manuelle, geprüfte
Zuordnung sicherer als ein generisches Namens-Matching, das sich leicht
vertun könnte):

  - "Kreisverwaltung Rhein-Hunsrück - Untere Denkmalschutzbehörde" -> Landkreis Rhein-Hunsrück-Kreis (07140)
  - "Kreisverwaltung Rhein-Lahn - Untere Denkmalschutzbehörde"     -> Landkreis Rhein-Lahn-Kreis (07141)
  - "Kreisverwaltung Rhein-Pfalz - Untere Denkmalschutzbehörde"    -> Rhein-Pfalz-Kreis (07338)
  - "Stadtverwaltung Ludwigshafen - Untere Denkmalschutzbehörde"   -> Stadt Ludwigshafen am Rhein (07314,
    kreisfreie Stadt - COUNTY-Ebene hier äquivalent zu MUNICIPALITY, da die Stadt ihr eigener Kreis ist)

Bewusst NICHT einbezogen: "Stadtverwaltung Neustadt - Untere
Denkmalschutzbehörde" - deren bestehende Regel (ags=07138044, Kreis
Neuwied) und Authority.city="Asbach" zeigen, dass dies tatsächlich
"Neustadt (Wied)" ist, ein anderer Ort als das gesuchte "Neustadt an der
Weinstraße" (kreisfreie Stadt, ags 07316000) - für Letzteres existiert
keine erkennbare bestehende Behörde, das bleibt eine echte, ungeschlossene
Lücke (keine Verwechslungsgefahr in Kauf genommen).

Bundesweit gibt es denselben Nullscope-Fehler noch weitere Male
(DENKMALSCHUTZ, WASSERSCHUTZ, HOCHWASSERSCHUTZ, ALTLASTEN, außerhalb RLP/SH)
- NICHT Teil dieses Fixes, siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md für
den vollständigen Befund.

Ergänzt für jede der drei bestehenden, bereits korrekt benannten Behörden
eine neue COUNTY-Regel (die kaputte Nullscope-Zeile bleibt unverändert
liegen - inert, richtet keinen Schaden an, wird hier bewusst nicht gelöscht).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, Korrektur eines Nullscope-Importfehlers)"

# authority_id (die Variante MIT der bestehenden, aber nullscope-defekten Regel) -> (ags_kreis, Kreisname, Gemeindenanzahl laut AdministrativeUnit)
CASES = [
    ("78c72d08-4a17-4bd2-b685-15567fd5bf14", "07140", "Rhein-Hunsrück-Kreis", 137),
    ("d37826cb-7d99-4514-b67e-6dca4eea76d5", "07141", "Rhein-Lahn-Kreis", 137),
    ("faab2688-225b-4969-a264-8317837ae3b4", "07314", "Ludwigshafen am Rhein", 1),
    ("416beb44-6c0c-462a-9c18-ee56ee3ae0d8", "07338", "Rhein-Pfalz-Kreis", 25),
]


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.services.kreis_scope_fix import KreisScopeFinding, apply_kreis_scope_fix

    db = SessionLocal()
    try:
        findings = []
        for authority_id, ags_kreis, kreis_name, total_gemeinden in CASES:
            authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
            if authority is None:
                print(f"WARNUNG: Authority {authority_id} ({kreis_name}) nicht gefunden - übersprungen.")
                continue
            old_rule = (
                db.query(Jurisdiction)
                .filter(Jurisdiction.authority_id == authority_id, Jurisdiction.request_type_id == "DENKMALSCHUTZ")
                .first()
            )
            if old_rule is None:
                print(f"WARNUNG: keine bestehende DENKMALSCHUTZ-Regel für {authority_id} - übersprungen.")
                continue
            existing_county = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.request_type_id == "DENKMALSCHUTZ", Jurisdiction.ags == ags_kreis,
                    Jurisdiction.matching_level == "COUNTY", Jurisdiction.active.is_(True),
                )
                .first()
            )
            if existing_county:
                print(f"Bereits vorhanden für {kreis_name} - übersprungen (idempotent).")
                continue
            findings.append(KreisScopeFinding(
                request_type_id="DENKMALSCHUTZ", ags_kreis=ags_kreis, state="Rheinland-Pfalz",
                authority_id=authority.authority_id, authority_name=authority.authority_name,
                old_rule_jurisdiction_id=old_rule.jurisdiction_id,
                total_gemeinden=total_gemeinden, existing_rule_count=0,
            ))

        if not findings:
            print("Nichts zu tun.")
            return

        result = apply_kreis_scope_fix(db, findings, reviewer=REVIEWER)
        db.commit()
        print(f"\nBatch: {result['batch_id']}")
        print(f"Gestaged: {len(result['staged'])}, freigegeben: {len(result['approved'])}, "
              f"Konflikte: {len(result['conflicts'])}")
        for entry, f in result["conflicts"]:
            print(f"  KONFLIKT #{entry.id} Kreis {f.ags_kreis}: {entry.conflict_type} - {entry.conflict_reason}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
