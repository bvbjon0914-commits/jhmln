# -*- coding: utf-8 -*-
"""
ALTLASTEN (untere Bodenschutzbehoerde) fuer BERLIN - alle 12 Bezirke.
Bislang die einzige verbleibende echte Luecke bei ALTLASTEN bundesweit
(alle anderen 15 Laender vollstaendig abgedeckt, siehe
docs/ABSCHLUSSBERICHT_DATENQUALITAET.md).

Berlin ist in dieser Datenbank fuer die meisten Auskunftsarten
(BAUAKTEN, BAULASTEN, KATASTER, ERSCHLIESSUNG) bereits bezirklich
modelliert: 12 einzeln recherchierte Bezirksamt-Zeilen, alle mit
ags=11000000 (Berlin hat destatis-technisch keine eigene Bezirks-AGS -
Dispatch erfolgt ueber Strasse/Adresse). ALTLASTEN folgt demselben
Muster: in allen 12 Bezirken liegt die untere Bodenschutzbehoerde
(BBodSchG + Berliner Ausfuehrungsgesetz) beim "Umwelt- und
Naturschutzamt" des jeweiligen Bezirksamts, Sachgebiet "Bodenschutz/
Altlasten" bzw. "Boden- und Grundwasserschutz" - Tempelhof-Schoeneberg
bestaetigt den Rechtsbegriff "untere Bodenschutzbehoerde" sogar
woertlich.

11 von 12 Bezirken mit direktem woertlichem Aufgaben-Zitat von der
amtlichen berlin.de-Bezirksseite belegt. Marzahn-Hellersdorf ist nur
ueber Kontakt-/Organigrammdaten (Sachgebiet "Boden- und Gewaesserschutz"
im Umwelt- und Naturschutzamt, E-Mail umweltschutz@ba-mh.berlin.de)
bestaetigt, kein laengerer Aufgaben-Fließtext gefunden - daher mit
verification_status=AUTO_IMPORTED statt VERIFIED angelegt (ehrliche
Beleglage-Differenzierung, analog zum Vorgehen bei anderen Laendern
in dieser Kampagne).

12 neue MUNICIPALITY-Regeln (ags=11000000, Dispatch ueber Strasse).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Altlasten Berlin je Bezirk)"
BERLIN_AGS = "11000000"

# Bezirk -> (Amtsname, Strasse, PLZ, Quelle-URL, Zitat, verification_status)
BEZIRKE = {
    "Mitte": (
        "Umwelt- und Naturschutzamt Mitte", "Karl-Marx-Allee 31", "10178",
        "https://www.berlin.de/ba-mitte/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/umweltschutz/bodenschutz-altlasten-grundwasserbelastungen-247081.php",
        "Zu den Aufgaben des Umwelt- und Naturschutzamtes gehört die Untersuchung und Bewertung von "
        "Schadstoffgehalten von Boden und Grundwasser (nachsorgender Bodenschutz).",
        "VERIFIED",
    ),
    "Friedrichshain-Kreuzberg": (
        "Umwelt- und Naturschutzamt Friedrichshain-Kreuzberg", "Yorckstraße 4-11", "10965",
        "https://www.berlin.de/ba-friedrichshain-kreuzberg/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/bodenschutz-und-altlasten/",
        "Bodenschutz, Altlasten und Grundwasserbelastungen - Auskünfte über Boden- und "
        "Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
    "Pankow": (
        "Umwelt- und Naturschutzamt Pankow", "Tino-Schwierzina-Str. 32", "13089",
        "https://www.berlin.de/ba-pankow/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/umweltschutz/artikel.231437.php",
        "Zu den Aufgaben des Umwelt- und Naturschutzamtes gehört die Untersuchung und Bewertung von "
        "Schadstoffbelastungen in Boden und Grundwasser.",
        "VERIFIED",
    ),
    "Charlottenburg-Wilmersdorf": (
        "Umwelt- und Naturschutzamt Charlottenburg-Wilmersdorf", "Rudolf-Mosse-Str. 9", "14197",
        "https://www.berlin.de/ba-charlottenburg-wilmersdorf/verwaltung/aemter/umwelt-und-naturschutz/umweltschutz/boden-altlasten-geologie/",
        "Bodenschutz, Altlasten und Grundwasserbelastungen; Meldungen über Boden- und "
        "Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
    "Spandau": (
        "Umwelt- und Naturschutzamt Spandau", "Otternbuchtstr. 35", "13599",
        "https://www.berlin.de/ba-spandau/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/umweltschutz/artikel.275648.php",
        "Bodenschutz, Altlasten und Grundwasserbelastungen - Entgegennahme von Meldungen über Boden- und "
        "Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
    "Steglitz-Zehlendorf": (
        "Umwelt- und Naturschutzamt Steglitz-Zehlendorf", "Hartmannsweilerweg 63", "14163",
        "https://www.berlin.de/ba-steglitz-zehlendorf/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/boden-und-altlasten/artikel.26137.php",
        "Entgegennahme von Meldungen bei Unfällen und beim Auffinden von Boden- und "
        "Grundwasserverunreinigungen, z. B. bei Baumaßnahmen (Meldepflicht!).",
        "VERIFIED",
    ),
    "Tempelhof-Schöneberg": (
        "Umwelt- und Naturschutzamt Tempelhof-Schöneberg", "Tempelhofer Damm 165", "12099",
        "https://www.berlin.de/ba-tempelhof-schoeneberg/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/naturschutz/artikel.1344642.php",
        "Zur Aufgabenwahrnehmung der unteren Bodenschutzbehörde gehört das Führen sowie das "
        "Fortschreiben des Bodenbelastungskatasters (BBK) des Landes Berlin.",
        "VERIFIED",
    ),
    "Neukölln": (
        "Umwelt- und Naturschutzamt Neukölln", "Gradestr. 36", "12347",
        "https://www.berlin.de/ba-neukoelln/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/boden-und-grundwasserschutz/",
        "Sachgebiet Boden- und Grundwasserschutz: u.a. Altlastensanierungen, Altlastenerkundungen, "
        "Bewerten von Boden- und Grundwassergutachten.",
        "VERIFIED",
    ),
    "Treptow-Köpenick": (
        "Umwelt- und Naturschutzamt Treptow-Köpenick", "Neue Krugallee 4", "12435",
        "https://www.berlin.de/ba-treptow-koepenick/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/artikel.120097.php",
        "Bodenschutz, Altlasten und Grundwasserbelastungen - Auskünfte über Boden- und "
        "Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
    "Marzahn-Hellersdorf": (
        "Umwelt- und Naturschutzamt Marzahn-Hellersdorf", "Alte Rhinstraße 4", "12681",
        "https://www.berlin.de/ba-marzahn-hellersdorf/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/artikel.260959.php",
        "Amtliche Kontakt-/Organigrammseite listet das Sachgebiet 'Boden- und Gewässerschutz' explizit "
        "unter dem Umwelt- und Naturschutzamt (umweltschutz@ba-mh.berlin.de); kein längerer "
        "Aufgaben-Fließtext auf den geprüften Seiten gefunden - daher AUTO_IMPORTED statt VERIFIED.",
        "AUTO_IMPORTED",
    ),
    "Lichtenberg": (
        "Umwelt- und Naturschutzamt Lichtenberg", "Alt-Friedrichsfelde 60", "10315",
        "https://www.berlin.de/ba-lichtenberg/politik-und-verwaltung/behoerdenwegweiser/artikel.1391385.php",
        "Erfassen und Überwachen von Flächen mit schädlichen Bodenverunreinigungen; Entgegennahme von "
        "Meldungen über Boden- und Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
    "Reinickendorf": (
        "Umwelt- und Naturschutzamt Reinickendorf", "Eichborndamm 215", "13437",
        "https://www.berlin.de/ba-reinickendorf/politik-und-verwaltung/aemter/umwelt-und-naturschutzamt/kontakt/telefonverzeichnis-1415426.php",
        "Altlasten und Bodenschutz, Grundwasserverunreinigungen.",
        "VERIFIED",
    ),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"altlasten-berlin-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for bezirk, (amtsname, strasse, plz, source_url, quote, verif) in BEZIRKE.items():
            authority = db.query(Authority).filter(Authority.authority_name == amtsname).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=amtsname,
                    authority_type="Untere Bodenschutzbehörde (Bezirksamt Berlin)",
                    street=strasse, house_number=None, postal_code=plz, city="Berlin",
                    state="Berlin", phone=None, email=None,
                    source=f"Amtliche Webseite (berlin.de), {source_url}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"ALTLASTEN Berlin - {bezirk}",
                request_type_id="ALTLASTEN", state="Berlin", ags=BERLIN_AGS,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{amtsname} - {quote}", source_url=source_url,
                source_license="Amtliche Webseite (berlin.de)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, verif))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [(e, v) for e, v in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c, _ in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, verif in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status=verif,
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
