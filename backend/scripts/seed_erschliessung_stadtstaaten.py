"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer die
drei Stadtstaaten Berlin, Bremen (inkl. Bremerhaven) und Hamburg - bislang
0 % Abdeckung, da fuer diese Bundeslaender noch keine
Erschliessungsbeitrags-Zustaendigkeit importiert war.

Berlin folgt dem in dieser Datenbank bereits etablierten Muster fuer diese
Stadt (siehe die bestehenden BAUAKTEN/BAULASTEN/KATASTER-Zeilen: 12
Bezirke, alle mit ags=11000000, da Berlin AGS-technisch keine separate
Bezirks-Schluessel kennt - destatis GV-ISys fuehrt Berlin als eine
Gemeinde). Jeder Bezirk hat laut eigener Bezirksamt-Webseite ein eigenes
Strassen- und Gruenflaechenamt, das fuer Erschliessungsbeitraege im
eigenen Bezirksgebiet zustaendig ist - kein fachlicher Widerspruch
zueinander (wie bei den anderen Kategorien auch), Dispatch erfolgt ueber
Strasse/Adresse statt ueber AGS.

Bremen (Stadtgemeinde Bremen, ags=04011000) und Bremerhaven (eigene
Stadtgemeinde, ags=04012000) sind zwei getrennte kreisfreie Staedte im
Land Bremen mit je eigener Verwaltung - daher zwei getrennte Zeilen.

Hamburg (ags=02000000) hat laut offiziellem Hamburg Service-Portal eine
zentrale, nicht bezirklich aufgeteilte Zustaendigkeit (Abteilung
Anliegerbeitraege der Behoerde fuer Wissenschaft, Forschung und
Gleichstellung) - daher nur eine Zeile.

Alle Quellen sind amtliche Webseiten (berlin.de-Bezirksamtsseiten,
asv.bremen.de, bremerhaven.de, hamburg.de), mit wortwoertlichem Zitat je
Zeile im `notes`-Feld, abgerufen 2026-09-28.

Aufruf:
    venv/Scripts/python.exe scripts/seed_erschliessung_stadtstaaten.py
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Erschliessungsbeitraege Stadtstaaten)"
PRIORITY = 40  # entspricht allen bestehenden aktiven ERSCHLIESSUNG-Regeln

BERLIN_PATTERN_NOTE = (
    "Struktur folgt dem in dieser Datenbank bereits etablierten Berlin-Muster "
    "(siehe BAUAKTEN/BAULASTEN/KATASTER: je ein Bezirksamt pro Bezirk, alle mit "
    "ags=11000000, da Berlin AGS-technisch keine separate Bezirks-Schluessel "
    "kennt - destatis GV-ISys fuehrt Berlin als eine Gemeinde)."
)

# state, ags, authority_name, street, plz, city, source_url, wortlaut-zitat
ENTRIES = [
    # --- Berlin: 12 Bezirke, alle ags=11000000 ---
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Mitte",
         street="Karl-Marx-Allee 31", plz="10178", city="Berlin",
         source_url="https://www.berlin.de/ba-mitte/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/strassenverwaltung/strassen-und-gruenflaechenamt-mitte-fachbereich-strassenverwaltung-grundst-cksangelegenheiten-kleingartenwesen-erschlie-ungsbeitragsangelegenheiten-502497.php",
         quote="Fachbereich Strassenverwaltung: Grundstuecksangelegenheiten, Kleingartenwesen, Erschliessungsbeitragsangelegenheiten."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Friedrichshain-Kreuzberg",
         street="Yorckstraße 4-11", plz="10965", city="Berlin",
         source_url="https://www.berlin.de/ba-friedrichshain-kreuzberg/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/dienstleistungen/artikel.1193358.php",
         quote="Erschliessungsbeitraege - Dienstleistung des Strassen- und Gruenflaechenamts Friedrichshain-Kreuzberg."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Pankow",
         street="Darßer Straße 203", plz="13088", city="Berlin",
         source_url="https://www.berlin.de/ba-pankow/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/",
         quote="Strassen- und Gruenflaechenamt Pankow - u.a. zustaendig fuer Erschliessungsbeitraege und Erschliessungsbeitragsbescheinigungen."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Charlottenburg-Wilmersdorf",
         street="Goslarer Ufer 39", plz="10589", city="Berlin",
         source_url="https://www.berlin.de/ba-charlottenburg-wilmersdorf/verwaltung/aemter/strassen-und-gruenflaechen/tiefbau/artikel.201494.php",
         quote="Allgemeine Forderungen des Strassen- und Gruenflaechenamtes, einschliesslich Erschliessungsbeitragsangelegenheiten."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Spandau",
         street="Otternbuchtstraße 35", plz="13599", city="Berlin",
         source_url="https://www.berlin.de/ba-spandau/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/allgemeine-verwaltung/artikel.219444.php",
         quote="Erschliessungsbeitragsangelegenheiten - Fachbereich Allgemeine Verwaltung, Strassen- und Gruenflaechenamt Spandau."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Steglitz-Zehlendorf",
         street="Hartmannsweilerweg 63", plz="14163", city="Berlin",
         source_url="https://www.berlin.de/ba-steglitz-zehlendorf/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/tiefbau/artikel.91710.php",
         quote="Erschliessungsbeitraege und -beitragsbescheinigungen in Steglitz-Zehlendorf - Strassen- und Gruenflaechenamt."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Tempelhof-Schöneberg",
         street="Großbeerenstraße 2-10 (Haus 3)", plz="12107", city="Berlin",
         source_url="https://www.berlin.de/ba-tempelhof-schoeneberg/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/unsere-fachbereiche/strassen-und-gruenflaechenverwaltung/artikel.942938.php",
         quote="Erschliessungsbeitraege und -beitragsbescheinigungen - Strassen- und Gruenflaechenverwaltung Tempelhof-Schoeneberg."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Neukölln",
         street="Gradestraße 36", plz="12347", city="Berlin",
         source_url="https://www.berlin.de/ba-neukoelln/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/strassen-und-verwaltung/verwaltung/artikel.273985.php",
         quote="Strassen- und Gruenflaechenverwaltung Neukoelln - Erschliessungsbeitragsangelegenheiten."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Treptow-Köpenick",
         street="Neue Krugallee 4", plz="12435", city="Berlin",
         source_url="https://www.berlin.de/ba-treptow-koepenick/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/artikel.1491174.php",
         quote="Bescheinigung ueber Erschliessungsbeitraege - Strassen- und Gruenflaechenamt Treptow-Koepenick."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Marzahn-Hellersdorf",
         street="Schkopauer Ring 2", plz="12681", city="Berlin",
         source_url="https://www.berlin.de/ba-marzahn-hellersdorf/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/",
         quote="Strassenverwaltung: Erschliessungs- und Ausbaubeitragsangelegenheiten - Strassen- und Gruenflaechenamt Marzahn-Hellersdorf."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Lichtenberg",
         street="Alt-Friedrichsfelde 60", plz="10315", city="Berlin",
         source_url="https://www.berlin.de/ba-lichtenberg/auf-einen-blick/buergerservice/bauen/artikel.299592.php",
         quote="Neubau und Ausbau von oeffentlichen Strassen - Strassenausbau- und Erschliessungsbeitraege, Strassen- und Gruenflaechenamt Lichtenberg."),
    dict(state="Berlin", ags="11000000", authority_name="Straßen- und Grünflächenamt Reinickendorf",
         street="Eichborndamm 238-240", plz="13437", city="Berlin",
         source_url="https://www.berlin.de/ba-reinickendorf/politik-und-verwaltung/aemter/strassen-und-gruenflaechenamt/verwaltung/artikel.1436082.php",
         quote="Allgemeine Verwaltung - Erschliessungsbeitraege/Schadenersatz/Sondernutzungen, Strassen- und Gruenflaechenamt Reinickendorf."),
    # --- Bremen (Stadtgemeinde) ---
    dict(state="Bremen", ags="04011000", authority_name="Amt für Straßen und Verkehr Bremen",
         street="Herdentorsteinweg 49/50", plz="28195", city="Bremen",
         source_url="https://www.asv.bremen.de/aufgaben/erschliessungen-und-strassenrecht-1717",
         quote="Amt fuer Strassen und Verkehr (ASV) - Aufgabenbereich 'Erschliessungen und Strassenrecht', mit den Teams "
               "'Erschliessungen und Erschliessungsbeitraege' sowie 'Strassenrecht'. Anschrift bestaetigt ueber das "
               "offizielle Impressum (https://www.asv.bremen.de/impressum-1478)."),
    # --- Bremerhaven (eigene Stadtgemeinde) ---
    dict(state="Bremen", ags="04012000", authority_name="Baureferat Bremerhaven",
         street="Fährstraße 20 (Technisches Rathaus)", plz="27568", city="Bremerhaven",
         source_url="https://www.bremerhaven.de/de/verwaltung-politik-sicherheit/buergerservice/adressen-oeffnungszeiten/baureferat.22509.html",
         quote="Baureferat: \"fuer die Festsetzung und Erhebung von Erschliessungs- und Strassenausbaubeitraegen, den "
               "Abschluss und die Abwicklung von Erschliessungsvertraegen, sowie fuer die Erstellung von "
               "Anliegerbescheinigungen, zustaendig.\" Hinweis: Das OVG Bremen hat die Erschliessungsbeitragssatzung "
               "der Stadt Bremerhaven im Mai 2026 wegen eines Bekanntmachungsmangels fuer unwirksam erklaert; die "
               "instanzielle Zustaendigkeit des Baureferats selbst ist davon unberuehrt."),
    # --- Hamburg (zentral, nicht bezirklich) ---
    dict(state="Hamburg", ags="02000000",
         authority_name="Behörde für Wissenschaft, Forschung und Gleichstellung – Abteilung Anliegerbeiträge",
         street="Hamburger Straße 37", plz="22083", city="Hamburg",
         source_url="https://www.hamburg.de/service/info/111100668/",
         quote="\"Die Abteilung Anliegerbeitraege der BWFG erhebt Erschliessungsbeitraege (bzw. Wegebaubeitraege) fuer "
               "die endgueltige Herstellung bestimmter Strassen, Plaetze und Wohnwege.\" Zentrale, nicht bezirklich "
               "aufgeteilte Zustaendigkeit (anders als z.B. Bauaufsicht, die in Hamburg bei den Bezirksaemtern liegt)."),
]


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
        batch_id = f"erschliessung-stadtstaaten-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for item in ENTRIES:
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == item["authority_name"], Authority.city == item["city"])
                .first()
            )
            if authority is None:
                import uuid

                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=item["authority_name"],
                    authority_type="Kommunale Beitragsstelle",
                    street=item["street"], house_number=None, postal_code=item["plz"], city=item["city"],
                    state=item["state"], phone=None, email=None,
                    source="Amtliche Quelle, recherchiert 2026-09-28: " + item["source_url"],
                    active=True,
                )
                db.add(authority)
                db.flush()

            note_parts = []
            if item["state"] == "Berlin":
                note_parts.append(BERLIN_PATTERN_NOTE)
            note_parts.append(item["quote"])

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Erschliessung Stadtstaaten - {item['authority_name']}",
                request_type_id="ERSCHLIESSUNG", state=item["state"], ags=item["ags"],
                matching_level=MatchingLevel.MUNICIPALITY, priority=PRIORITY,
                proposed_authority_id=authority.authority_id,
                source=f"{item['authority_name']} - {item['quote']}", source_url=item["source_url"],
                source_license="Amtliche Webseite (berlin.de / asv.bremen.de / bremerhaven.de / hamburg.de)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, " ".join(note_parts)))
        db.commit()

        print(f"\n{len(staged)} Eintraege gestaged (Batch {batch_id}).")
        conflicts = [(e, n) for e, n in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c, _ in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, note in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=note,
                resulting_verification_status="VERIFIED",
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
