"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
HESSEN - bislang 0 % Abdeckung (0 von 421 Gemeinden hatten eine aktive
ERSCHLIESSUNG-Zeile).

Dies ist eine ERSTE, bewusst kleine Teil-Welle (8 von 421 Gemeinden), nicht
der vollstaendige Hessen-Import. Hessen kennt - anders als z.B. Niedersachsen
(Samtgemeinde) oder Rheinland-Pfalz (Verbandsgemeinde) - grundsaetzlich KEIN
Verbandsgemeinde-Modell, das die Zahl der zu recherchierenden Einheiten
reduzieren wuerde: jede Gemeinde verwaltet sich (mit Ausnahme einzelner
Sonderkonstruktionen) selbst, Erschliessungsbeitraege muessen daher pro
Gemeinde einzeln recherchiert werden. Diese Welle deckt ab:

  - alle 5 kreisfreien Staedte (Darmstadt, Frankfurt am Main, Offenbach am
    Main, Wiesbaden, Kassel) sowie die Sonderstatusstadt Hanau (eigener
    AGS-Kreis-Schluessel 06415, amtlich wie eine kreisfreie Stadt gefuehrt) -
    6 Gemeinden mit klarer Amtszustaendigkeit,
  - 2 der 12 Gemeinden des Odenwaldkreises (Hoechst i. Odw., Breuberg), fuer
    die eine amtliche Quelle die Zustaendigkeit fuer "Erschliessungsbeitrag
    zahlen" wortwoertlich einem konkreten Amt zuordnet.

Die uebrigen 10 Odenwaldkreis-Gemeinden sowie alle 20 weiteren Land-/
Stadtkreise Hessens sind AUSDRUECKLICH NICHT Teil dieser Welle: fuer sie
wurde entweder keine amtliche Quelle mit woertlicher Bestaetigung gefunden,
oder die Recherche wurde noch nicht durchgefuehrt (Sitzung 2026-09-28 hat
ihr WebSearch-Budget erschoepft, bevor der Rest des Odenwaldkreises und die
uebrigen Landkreise bearbeitet werden konnten). Eine Folge-Sitzung sollte
Kreis fuer Kreis fortsetzen (sinnvollerweise nach Groesse aufsteigend, siehe
Main-Taunus-Kreis/Hochtaunuskreis/Gross-Gerau als naechste Kandidaten),
anstatt eine mechanische mit generischem "Bauamt" befuellte Vollabdeckung zu
erzwingen - das widerspraeche dem in diesem Projekt etablierten Qualitaets-
massstab (woertliches Zitat je Zeile, amtliche Quelle, kein Kauperts/
Ortsdienst/Immobilienportal als Beleg).

Alle Quellen sind amtliche .de-Webseiten der jeweiligen Kommune, mit
woertlichem Zitat je Zeile im `notes`-Feld (ueber `review_notes` an
approve_entry), abgerufen 2026-09-28.

Aufruf:
    venv/Scripts/python.exe scripts/seed_erschliessung_hessen.py
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = (
    "Claude (Recherche-Sitzung 2026-09-28, Erschliessungsbeiträge Hessen - "
    "kreisfreie Städte + Sonderstatusstadt Hanau + 2 Odenwaldkreis-Gemeinden)"
)
PRIORITY = 40  # entspricht allen bestehenden aktiven ERSCHLIESSUNG-Regeln

# ags, muni (amtlicher Gemeindename lt. administrative_units), authority_name,
# department_name, street, plz, city, source_url, woertliches Zitat
ENTRIES = [
    dict(
        ags="06411000", muni="Darmstadt, Wissenschaftsstadt",
        authority_name="Wissenschaftsstadt Darmstadt – Finanzverwaltung (Stadtkasse und kommunale Steuern)",
        department_name="Abteilung Stadtkasse und kommunale Steuern, Teilbereich Steuern",
        street=None, plz=None, city="Darmstadt", email=None, phone=None,
        source_url="https://digitales-rathaus.darmstadt.de/lebensbereiche/steuern-gebuehren-beitraege/"
                   "dienstleistungen/erschliessungs-strassen-und-abwasserbeitraege",
        quote="Finanzverwaltung, Abteilung Stadtkasse und kommunale Steuern, Teilbereich Steuern",
    ),
    dict(
        ags="06412000", muni="Frankfurt am Main, Stadt",
        authority_name="Stadt Frankfurt am Main – Amt für Straßenbau und Erschließung",
        department_name="Amt 66 - Erschließungsrecht",
        street=None, plz=None, city="Frankfurt am Main", email="info21.amt66@stadt-frankfurt.de", phone=None,
        source_url="https://frankfurt.de/service-und-rathaus/verwaltung/aemter-und-institutionen/"
                   "amt-fuer-strassenbau-und-erschliessung/erschliessung/erschliessungsbeitrag",
        quote="Amt für Straßenbau und Erschließung; info21.amt66@stadt-frankfurt.de; "
              "„Ihre fachkundigen Ansprechpartner/innen finden Sie unter 'Erschließungsrecht'“",
    ),
    dict(
        ags="06413000", muni="Offenbach am Main, Stadt",
        authority_name="Stadt Offenbach am Main – Amt für Stadtplanung, Verkehrs- und Baumanagement",
        department_name=None,
        street="Berliner Straße 60", plz="63065", city="Offenbach am Main",
        email="bauverwaltung@offenbach.de", phone="069 8065-2699",
        source_url="https://www.offenbach.de/vv/produkte/tsabus/anliegerbescheinigung_8960274.php",
        quote="Amt für Stadtplanung, Verkehrs- und Baumanagement, Berliner Straße 60, 63065 Offenbach am Main "
              "(Stadthaus, 14.-16. OG) - zuständig für die Anliegerbescheinigung u.a. zu Erschließungsbeiträgen, "
              "Straßenausbaubeiträgen und Kanalanschlussbeiträgen",
    ),
    dict(
        ags="06414000", muni="Wiesbaden, Landeshauptstadt",
        authority_name="Landeshauptstadt Wiesbaden – Tiefbau- und Vermessungsamt",
        department_name="Tiefbau- und Vermessungsamt & Straßenverkehrsbehörde",
        street="Gustav-Stresemann-Ring 15", plz="65189", city="Wiesbaden",
        email=None, phone="0611 312730",
        source_url="https://wiesbaden.de/vv/produkte/66/141010100000008569.php",
        quote="Tiefbau- und Vermessungsamt & Straßenverkehrsbehörde - Ausstellung schriftlicher Bescheinigungen über "
              "Erschließungsbeiträge und andere öffentlich-rechtliche Abgaben",
    ),
    dict(
        ags="06415000", muni="Hanau, Brüder-Grimm-Stadt",
        authority_name="Stadt Hanau – Stadtkasse (Sachgebiet Sachbuchhaltung)",
        department_name="Sachgebiet Sachbuchhaltung",
        street=None, plz=None, city="Hanau", email=None, phone="06181-295-981",
        source_url="https://www.hanau.de/rathaus/lebenslagen/finanzen-steuern-gebuehren/index.html",
        quote="Dieses Sachgebiet ist zuständig für Einmalzahlungen wie z.B. Erschließungskosten, VHS-Gebühren, "
              "Auskunftsgebühren",
    ),
    dict(
        ags="06611000", muni="Kassel, documenta-Stadt",
        authority_name="Stadt Kassel – Bauverwaltungsamt",
        department_name="Bauverwaltung",
        street="Friedrich-Ebert-Straße 160 (Rathaus 2)", plz="34119", city="Kassel",
        email="bauverwaltungsamt@kassel.de", phone=None,
        source_url="https://www.kassel.de/service/produkte/kassel/Bauverwaltungsamt/erschliessungsbeitraege.php",
        quote="Seite 'Erschließungsbeiträge' im Bereich Bauverwaltungsamt; Kontakt: Bauverwaltung, Rathaus 2, "
              "Friedrich-Ebert-Straße 160, 34119 Kassel (bauverwaltungsamt@kassel.de)",
    ),
    dict(
        ags="06437009", muni="Höchst i. Odw.",
        authority_name="Gemeinde Höchst i. Odw. – FB 4.4 (Allg. Bauverwaltung, Beitragsrecht, Bauantragswesen)",
        department_name="FB 4.4 - Allg. Bauverwaltung, Beitragsrecht, Bauantragswesen",
        street="Montmelianer Platz 4", plz="64739", city="Höchst i. Odw.",
        email=None, phone="06163 708-50",
        source_url="https://www.hoechst-i-odw.de/buergerservice/abteilungen/HES:department:5207/"
                   "fb-4-4-allg-bauverwaltung-beitragsrecht-bauantragswesen/",
        quote="FB 4.4 - Allg. Bauverwaltung, Beitragsrecht, Bauantragswesen - Leistungen u.a. 'Erschließungsbeitrag "
              "zahlen'",
    ),
    dict(
        ags="06437004", muni="Breuberg, Stadt",
        authority_name="Stadt Breuberg – Bau- und Liegenschaftsverwaltung",
        department_name="Bau- und Liegenschaftsverwaltung",
        street="Ernst-Ludwig-Straße 2-4", plz="64747", city="Breuberg",
        email="bauverwaltung@breuberg.de", phone="06163 709-0",
        source_url="https://www.breuberg.de/buergerservice/abteilungen/HES:department:5216/bau-und-liegenschaftsverwaltung/",
        quote="Bau- und Liegenschaftsverwaltung - Leistungen u.a. 'Erschließungsbeitrag zahlen'",
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
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"erschliessung-hessen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for item in ENTRIES:
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == item["authority_name"], Authority.city == item["city"])
                .first()
            )
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=item["authority_name"],
                    authority_type="Kommunale Beitragsstelle",
                    department_name=item["department_name"],
                    street=item["street"], house_number=None, postal_code=item["plz"], city=item["city"],
                    state="Hessen", phone=item["phone"], email=item["email"],
                    source="Hessen ERSCHLIESSUNG-Import 2026-09, amtliche Webseite: " + item["source_url"],
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Erschliessung Hessen - {item['authority_name']}",
                request_type_id="ERSCHLIESSUNG", state="Hessen", ags=item["ags"], municipality=item["muni"],
                matching_level=MatchingLevel.MUNICIPALITY, priority=PRIORITY,
                proposed_authority_id=authority.authority_id,
                source=f"{item['authority_name']} - {item['quote']}", source_url=item["source_url"],
                source_license="Amtliche Webseite der jeweiligen Kommune",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, item["quote"]))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [(e, n) for e, n in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c, _ in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, quote in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=quote,
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
