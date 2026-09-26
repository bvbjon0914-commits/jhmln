"""
Behebt einen weiteren Satz des Nullscope-Fehlerpatterns (siehe
scripts/fix_unscoped_denkmalschutz_rlp.py für die ursprüngliche RLP-Version)
außerhalb RLP - Regeln mit ags/municipality/district/postal_code/street/
state ALLE None, die dadurch nie matchen, obwohl die Behörde bereits real
und korrekt benannt in der Datenbank existiert.

Anders als beim RLP-Fix (immer COUNTY-Ebene) sind hier UNTERSCHIEDLICHE
Ebenen richtig, je nachdem wofür die Behörde tatsächlich zuständig ist:

  - STATE-Ebene: Saarland ist klein genug, dass zwei Landesämter
    (Umwelt/Arbeitsschutz, Denkmalpflege) zentral für das GANZE Land
    zuständig sind - Name "Landesamt"/"Landesdenkmalamt" bestätigt das.
  - MUNICIPALITY-Ebene: einzelne, eindeutig benannte Städte (Limburg an der
    Lahn, Neustadt am Rübenberge, Bremen, Bremerhaven, Hamburg) - jeweils
    per AGS aus AdministrativeUnit verifiziert, nicht geraten.
  - COUNTY-Ebene: Landkreis Mühldorf am Inn (Bayern).

Technischer Sonderfall STATE-Ebene: die Konflikterkennung in
JurisdictionStagingService._find_matching_existing() vergleicht NUR
ags/municipality/district/postal_code/street/house_number - nicht state
oder matching_level. Eine neue STATE-Regel hat aber (korrekt) exakt
dieselben None-Werte in all diesen Feldern wie die kaputte Nullscope-
Zeile selbst - der Staging-Weg würde sie deshalb fälschlich als exaktes
Duplikat der eigenen kaputten Vorgänger-Zeile ablehnen. Für die 4
Saarland-Fälle wird die bestehende Zeile daher DIREKT gepatcht (state +
matching_level + priority gesetzt, Begründung an notes angehängt) statt
über staging.stage_entry()/approve_entry() eine neue Zeile zu erzeugen -
es ist ohnehin dieselbe Regel, nur mit vorher fehlendem Geltungsbereich.

BEWUSST NICHT in diesem Durchlauf behoben (siehe
docs/ABSCHLUSSBERICHT_DATENQUALITAET.md für die Begründung):
  - Berlins 12 Bezirksämter (DENKMALSCHUTZ) und Hamburgs 7 Bezirksämter
    (WASSERSCHUTZ/HOCHWASSERSCHUTZ) - alle teilen sich dieselbe
    Stadtstaat-AGS (11000000 bzw. 02000000). Eine COUNTY/MUNICIPALITY-Regel
    pro Bezirk würde die Bezirke gegeneinander in Konflikt setzen
    (MULTIPLE_MATCHES) - korrekt wäre eine DISTRICT-Ebene-Regel pro Bezirk,
    was voraussetzt, dass echte Gebäudedaten ein befülltes district-Feld
    mit dem exakten Bezirksnamen haben. Da aktuell 0 Gebäude importiert
    sind und Berlin/Hamburg als Stadtstaat ohnehin nur 1 AGS-Einheit in der
    118.239-Kombinationen-Kennzahl ausmachen, ist der Effekt auf die
    bundesweite NO_MATCH-Quote vernachlässigbar - zurückgestellt für einen
    Durchlauf mit echten Portfoliodaten.
  - Baden-Württembergs 11 GVV/VVG-Fälle (DENKMALSCHUTZ) - jede
    Gemeindeverwaltungsgemeinschaft deckt eine SPEZIFISCHE, kleine Menge
    von Gemeinden ab (nicht einen ganzen Kreis) - erfordert eine echte
    Mitgliedsgemeinden-Zuordnung pro GVV, die (anders als RLPs VG250-
    Verbandsgemeinde-Daten) hier nicht ohne Weiteres vorliegt.
  - "Stiftung Preußische Schlösser und Gärten Berlin-Brandenburg" - ein
    Sondervermögen für konkrete Schloss-/Parkanlagen, KEINE
    flächendeckende Gebietszuständigkeit - eine Kreis-/Gemeinde-Zuordnung
    wäre erfunden, nicht belegt.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Struktur-Korrektur 2026-09-26, bundesweiter Nullscope-Fix)"

# (authority_name, request_type_id, alter_jurisdiction_id, neue Regel-Felder)
CASES = [
    dict(
        authority_name="Die Senatorin für Umwelt, Klima und Wissenschaft – Referat 24, Außenstelle Bremerhaven",
        request_type_id="ALTLASTEN", state="Bremen", ags="04012000", matching_level="MUNICIPALITY", priority=40,
        begruendung="Name nennt ausdrücklich 'Außenstelle Bremerhaven' - Zuständigkeit auf Bremerhaven "
        "begrenzt, nicht auf ganz Bremen.",
    ),
    dict(
        authority_name="Landesamt für Umwelt- und Arbeitsschutz (LUA) – Untere Bodenschutzbehörde",
        request_type_id="ALTLASTEN", state="Saarland", ags=None, matching_level="STATE", priority=60,
        begruendung="Landesamt = zentrale Landesbehörde, Saarland klein genug für zentrale Zuständigkeit.",
    ),
    dict(
        authority_name="Landesamt für Umwelt- und Arbeitsschutz (LUA) – Untere Wasserbehörde",
        request_type_id="WASSERSCHUTZ", state="Saarland", ags=None, matching_level="STATE", priority=60,
        begruendung="Landesamt = zentrale Landesbehörde, Saarland klein genug für zentrale Zuständigkeit.",
    ),
    dict(
        authority_name="Landesamt für Umwelt- und Arbeitsschutz (LUA) – Untere Wasserbehörde",
        request_type_id="HOCHWASSERSCHUTZ", state="Saarland", ags=None, matching_level="STATE", priority=60,
        begruendung="Landesamt = zentrale Landesbehörde, Saarland klein genug für zentrale Zuständigkeit.",
    ),
    dict(
        authority_name="Landesdenkmalamt Saarland",
        request_type_id="DENKMALSCHUTZ", state="Saarland", ags=None, matching_level="STATE", priority=60,
        begruendung="Name 'Landesdenkmalamt' - zentrale Landesbehörde für ganz Saarland.",
    ),
    dict(
        authority_name="Stadt Limburg an der Lahn – Untere Denkmalschutzbehörde",
        request_type_id="DENKMALSCHUTZ", state="Hessen", ags="06533009", matching_level="MUNICIPALITY", priority=40,
        begruendung="Eindeutig eine Stadt - AGS aus AdministrativeUnit verifiziert (Limburg a. d. Lahn, Kreisstadt).",
    ),
    dict(
        authority_name="Stadt Neustadt a. Rbge. – Untere Denkmalschutzbehörde",
        request_type_id="DENKMALSCHUTZ", state="Niedersachsen", ags="03241012", matching_level="MUNICIPALITY", priority=40,
        begruendung="Eindeutig eine Stadt (Region Hannover) - AGS aus AdministrativeUnit verifiziert.",
    ),
    dict(
        authority_name="Landratsamt Mühldorf a. Inn – Untere Wasserrechtsbehörde",
        request_type_id="WASSERSCHUTZ", state="Bayern", ags="09183", matching_level="COUNTY", priority=50,
        begruendung="Landratsamt = Kreisbehörde, ags_kreis aus AdministrativeUnit verifiziert.",
    ),
    dict(
        authority_name="Landratsamt Mühldorf a. Inn – Untere Wasserrechtsbehörde",
        request_type_id="HOCHWASSERSCHUTZ", state="Bayern", ags="09183", matching_level="COUNTY", priority=50,
        begruendung="Landratsamt = Kreisbehörde, ags_kreis aus AdministrativeUnit verifiziert.",
    ),
    dict(
        authority_name="Landesamt für Denkmalpflege Bremen – Denkmalschutzbehörde für die Stadtgemeinde Bremen",
        request_type_id="DENKMALSCHUTZ", state="Bremen", ags="04011000", matching_level="MUNICIPALITY", priority=40,
        begruendung="Name nennt ausdrücklich 'für die Stadtgemeinde Bremen' - nicht Bremerhaven.",
    ),
    dict(
        authority_name="Magistrat der Stadt Bremerhaven – Untere Denkmalschutzbehörde",
        request_type_id="DENKMALSCHUTZ", state="Bremen", ags="04012000", matching_level="MUNICIPALITY", priority=40,
        begruendung="Eindeutig Bremerhaven, eigene AGS getrennt von Bremen-Stadt.",
    ),
    dict(
        authority_name="Denkmalschutzamt Hamburg",
        request_type_id="DENKMALSCHUTZ", state="Hamburg", ags="02000000", matching_level="MUNICIPALITY", priority=40,
        begruendung="EINE zentrale Behörde für ganz Hamburg (anders als die bezirksweise gesplitteten Wasserbehörden).",
    ),
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
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"nullscope-fix-nationwide-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []
        patched = []

        for case in CASES:
            authority = db.query(Authority).filter(Authority.authority_name == case["authority_name"]).first()
            if authority is None:
                print(f"WARNUNG: Authority nicht gefunden - übersprungen: {case['authority_name']}")
                continue
            old_rule = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.authority_id == authority.authority_id,
                    Jurisdiction.request_type_id == case["request_type_id"],
                )
                .first()
            )
            if old_rule is None:
                print(
                    f"WARNUNG: keine bestehende Regel für {case['authority_name']} / "
                    f"{case['request_type_id']} - übersprungen."
                )
                continue

            if case["matching_level"] == "STATE" and case["ags"] is None:
                # Siehe Docstring: dieselbe Zeile wird direkt gepatcht statt eine
                # (aus Sicht der Konflikterkennung identische) neue Zeile zu staged.
                if old_rule.state == case["state"] and old_rule.matching_level == "STATE":
                    print(f"Bereits korrigiert - übersprungen: {case['authority_name']} / {case['request_type_id']}")
                    continue
                old_rule.state = case["state"]
                old_rule.matching_level = case["matching_level"]
                old_rule.priority = case["priority"]
                old_rule.notes = (
                    (old_rule.notes + " | " if old_rule.notes else "")
                    + f"Nullscope-Korrektur ({batch_id}) von {REVIEWER} am {datetime.utcnow().date().isoformat()}: "
                    f"{case['begruendung']}"
                )
                patched.append((old_rule, case))
                continue

            # Idempotenz: existiert schon eine korrekt gescopte Regel?
            existing_correct = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.request_type_id == case["request_type_id"],
                    Jurisdiction.authority_id == authority.authority_id,
                    Jurisdiction.matching_level == case["matching_level"],
                    Jurisdiction.ags == case["ags"],
                    Jurisdiction.active.is_(True),
                )
                .first()
            )
            if existing_correct:
                print(f"Bereits korrigiert - übersprungen: {case['authority_name']} / {case['request_type_id']}")
                continue

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Nullscope-Fix bundesweit (außerhalb RLP)",
                request_type_id=case["request_type_id"], state=case["state"], ags=case["ags"],
                matching_level=case["matching_level"], priority=case["priority"],
                proposed_authority_id=authority.authority_id,
                source=(
                    f"Interne Struktur-Korrektur: {case['begruendung']} "
                    f"(alte Regel {old_rule.jurisdiction_id} war komplett ungescopt)"
                ),
                source_license="Interne Korrektur (keine externe Datenquelle)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, case))
        db.commit()

        print(f"\n{len(patched)} bestehende Regeln direkt gepatcht (STATE-Ebene).")
        print(f"{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts:
            print(f"  KONFLIKT #{c.id} {c.request_type_id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, case in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(entry.id, reviewer=REVIEWER, review_notes=case["begruendung"])
            approved += 1
        db.commit()
        print(f"\n{approved} neue Regeln freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
