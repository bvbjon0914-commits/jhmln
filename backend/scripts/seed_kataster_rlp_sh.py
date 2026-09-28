"""
Liegenschaftskataster (KATASTER) in Rheinland-Pfalz und Schleswig-Holstein
durch den sicheren Aktualisierungsprozess.

Fachliche Definition (aus templates/kataster.docx): Auskunft aus dem
Liegenschaftskataster (Flurstücksnachweis/Auszug aus der Liegenschaftskarte)
nach dem Vermessungs- und Katastergesetz DES JEWEILIGEN LANDES - wie
Bodendenkmalschutz Landesrecht, die Organisation unterscheidet sich je Land.

WICHTIGER UNTERSCHIED zum Bodendenkmalschutz-Piloten: hier existieren
bereits Authority-Zeilen für ALLE benötigten Stellen (mit korrekten Adressen,
durch unabhängige Web-Recherche gegenprüft - siehe Quellenangaben unten) -
sie werden WIEDERVERWENDET, nicht neu angelegt. Das Problem ist identisch
zum bereits behobenen Kreisebenen-Scope-Bug (BAUAKTEN/BAULASTEN, siehe
app/services/kreis_scope_fix.py): jede Stelle hat nur EINE MUNICIPALITY-
oder teilweise COUNTY-Regel für IHREN EIGENEN Sitz-Kreis, nicht für ihren
gesamten realen Zuständigkeitsbereich.

Quellen (alle amtlich, abgerufen 2026-09-26):

  Rheinland-Pfalz - Vermessungs- und Katasterverwaltung (VermKV), sechs
  Vermessungs- und Katasterämter:
    https://lvermgeo.rlp.de/service/vermessungsbehoerden-in-rheinland-pfalz
    (Rheinpfalz-Städte zusätzlich bestätigt über die Amtsseite
    vermka-rheinpfalz.rlp.de; Westpfalz-Städte über Web-Recherche zu
    "Vermessungs- und Katasteramt Westpfalz")

  Schleswig-Holstein - Landesamt für Vermessung und Geoinformation (LVermGeo
  SH), fünf Regionalstandorte mit Kreiszuordnung laut offizieller
  Kontaktseite:
    https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/LVERMGEOSH/Kontakt

Läuft über JurisdictionStagingService - Konfliktprüfung je Regel,
Freigabe durch benannten Prüfer mit Fundstelle.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, siehe source_url je Regel)"

RLP_SOURCE_URL = "https://lvermgeo.rlp.de/service/vermessungsbehoerden-in-rheinland-pfalz"
SH_SOURCE_URL = "https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/LVERMGEOSH/Kontakt"

# authority_name (muss exakt existieren) -> Liste zustaendiger ags_kreis-Werte
RLP_OFFICES = {
    "Katasteramt Osteifel-Hunsrück": ["07111", "07131", "07135", "07137", "07140"],
    "Katasteramt Rheinhessen-Nahe": ["07133", "07134", "07315", "07319", "07331", "07339"],
    "Katasteramt Rheinpfalz": ["07311", "07313", "07314", "07316", "07318", "07332", "07334", "07337", "07338"],
    "Katasteramt Westeifel-Mosel": ["07211", "07231", "07232", "07233", "07235"],
    "Katasteramt Westpfalz": ["07312", "07317", "07320", "07333", "07335", "07336", "07340"],
    "Katasteramt Westerwald-Taunus": ["07132", "07138", "07141", "07143"],
}

SH_OFFICES = {
    "Katasteramt Kiel": ["01002", "01004", "01057", "01058"],
    "Katasteramt Lübeck": ["01003", "01053", "01055", "01062"],
    "Katasteramt Flensburg": ["01001", "01059"],
    "Katasteramt Husum": ["01051", "01054"],
    "Katasteramt Elmshorn": ["01056", "01060", "01061"],
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"kataster-rlp-sh-{datetime.utcnow().strftime('%Y%m%d')}"

        offices = [(name, kreise, "Rheinland-Pfalz", RLP_SOURCE_URL) for name, kreise in RLP_OFFICES.items()]
        offices += [(name, kreise, "Schleswig-Holstein", SH_SOURCE_URL) for name, kreise in SH_OFFICES.items()]

        staged = []
        skipped_existing = 0
        missing_authorities = []
        for name, kreise, state, source_url in offices:
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                missing_authorities.append(name)
                continue
            for ags_kreis in kreise:
                existing_county = (
                    db.query(Jurisdiction)
                    .filter(
                        Jurisdiction.request_type_id == "KATASTER", Jurisdiction.ags == ags_kreis,
                        Jurisdiction.matching_level == "COUNTY", Jurisdiction.active.is_(True),
                    )
                    .first()
                )
                if existing_county:
                    skipped_existing += 1
                    continue
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label="Liegenschaftskataster RLP+SH - bestehende Stellen erweitert",
                    request_type_id="KATASTER", state=state, ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"Amtliche Kreiszuordnung fuer {name}",
                    source_url=source_url,
                    source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behoerdenseite)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        if missing_authorities:
            print(f"WARNUNG: {len(missing_authorities)} erwartete Authority-Namen nicht gefunden, uebersprungen:")
            for m in missing_authorities:
                print(f"  {m}")

        print(f"{len(staged)} neue Einträge gestaged ({skipped_existing} bereits vorhanden, überprungen).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts:
            print(f"  KONFLIKT #{c.id} ags={c.ags} conflict={c.conflict_type} - {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes="Bestehende Behörde um ihren vollständigen, amtlich belegten Zuständigkeitsbereich ergänzt.",
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
