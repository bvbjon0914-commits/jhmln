"""
BAUAKTENAUSKUNFT fuer BAYERN. Nach Art. 53 Abs. 1 BayBO (Bayerische
Bauordnung) sind "untere Bauaufsichtsbehoerden ... die
Kreisverwaltungsbehoerden" - das ist ueber Art. 9 GO Bayern das
Landratsamt fuer die Landkreise bzw. die kreisfreie Gemeinde/Stadt
selbst fuer ihr Gebiet ("sie ist insoweit Kreisverwaltungsbehoerde").
Wortlaut per Live-Browser-Abruf direkt gegen gesetze-bayern.de
wort-fuer-wort verifiziert.

WICHTIGER NEBENFUND dieser Recherche: Bayern hat KEIN
Baulastenverzeichnis (anders als praktisch alle anderen Bundeslaender) -
grundstuecksbezogene Verpflichtungen werden dort zivilrechtlich ueber
eine im Grundbuch eingetragene Grunddienstbarkeit gesichert, nicht
oeffentlich-rechtlich ueber eine Baulast. Die BayBO (Art. 1-84) enthaelt
keinen einzigen Baulasten-Artikel (Art. 83-84 sind reine
Uebergangs-/Schlussvorschriften). Fuer BAULASTEN wird daher bewusst
KEIN Bayern-Skript erstellt - eine Zuordnung wuerde eine nicht
existierende Zustaendigkeit vortaeuschen; Bayern bleibt fuer diese
Auskunftsart korrekt strukturell "nicht anwendbar" statt eines
geratenen NO_MATCH-Luecke.

Ausnahmen von der Landratsamt-Regel (Art. 53 Abs. 2 BayBO i.V.m. § 5
Zustaendigkeitsverordnung im Bauwesen, ZustVBau vom 5.7.1994, BayRS
2130-3-B - wortgleich gegen gesetze-bayern.de verifiziert): 10
kreisangehoerige Kommunen mit eigener unterer Bauaufsichtsbehoerde
(nicht das Landratsamt):
- Volle Uebertragung (Art. 53 Abs. 2 Satz 1 BayBO): Burghausen,
  Feuchtwangen, Friedberg, Sulzbach-Rosenberg, Waldkraiburg,
  Alzenau i.UFr., Markt Garmisch-Partenkirchen, Vaterstetten.
- Eingeschraenkte/historische Uebertragung (Art. 83 Abs. 9 BayBO):
  Pfaffenhofen a.d.Ilm, Waldsassen.

96 neue COUNTY-Regeln (eine je Landkreis/kreisfreier Stadt) + 10 neue
MUNICIPALITY-Regeln (die genannten Ausnahme-Kommunen, nehmen automatisch
Vorrang vor der COUNTY-Regel ihres Landkreises).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauaktenauskunft Bayern)"
BAYBO_URL = "https://www.gesetze-bayern.de/Content/Document/BayBO-53"
ZUSTVBAU_URL = "https://www.gesetze-bayern.de/Content/Document/BayBauGBZustV-5"
QUOTE_KREIS = ("Art. 53 Abs. 1 BayBO: 'Untere Bauaufsichtsbehörden sind die Kreisverwaltungsbehörden ... "
               "Für den Vollzug dieses Gesetzes ... ist die untere Bauaufsichtsbehörde zuständig.' "
               "Art. 9 Abs. 1 GO Bayern: 'Die kreisfreie Gemeinde erfüllt im übertragenen Wirkungskreis "
               "alle Aufgaben, die sonst vom Landratsamt als der unteren staatlichen Verwaltungsbehörde "
               "wahrzunehmen sind ... sie ist insoweit Kreisverwaltungsbehörde.'")
QUOTE_AUSNAHME = ("§ 5 ZustVBau: 'Die Aufgaben der unteren Bauaufsichtsbehörde im Sinn von Art. 53 Abs. 2 "
                   "Satz 1 BayBO werden den Städten Burghausen, Feuchtwangen, Friedberg, "
                   "Sulzbach-Rosenberg, Waldkraiburg und Alzenau i. UFr. sowie dem Markt "
                   "Garmisch-Partenkirchen und der Gemeinde Vaterstetten übertragen. Die Aufgaben der "
                   "unteren Bauaufsichtsbehörde im Sinn von Art. 83 Abs. 9 BayBO sind den Städten "
                   "Pfaffenhofen a.d.Ilm und Waldsassen übertragen.'")

# Ausnahme-Kommune -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Burghausen": "09171112",
    "Feuchtwangen": "09571145",
    "Friedberg": "09771130",
    "Sulzbach-Rosenberg": "09371151",
    "Waldkraiburg": "09183148",
    "Alzenau i.UFr.": "09671111",
    "Garmisch-Partenkirchen": "09180117",
    "Vaterstetten": "09175132",
    "Pfaffenhofen a.d.Ilm": "09186143",
    "Waldsassen": "09377158",
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_GEMEINDE, SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    by = df[df["Land_name"] == "Bayern"]
    kreis_ars_index = build_ars_index(by[by["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(by[by["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Bayern").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-bayern-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, kreis_name in kreis_names.items():
            addr = kreis_ars_index.get(str(int(ags_kreis)))
            authority_name = f"Landratsamt {kreis_name}" if "Landkreis" not in kreis_name else f"Landratsamt {kreis_name}"
            authority_name = f"Kreisverwaltungsbehörde {kreis_name} - Bauamt"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Bauaufsichtsbehörde (Kreisverwaltungsbehörde)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Bayern", phone=None, email=addr.email if addr else None,
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bauakten Bayern - Kreise",
                request_type_id="BAUAKTEN", state="Bayern", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE_KREIS}", source_url=BAYBO_URL,
                source_license="Amtliche Rechtsgrundlage (BayBO/GO Bayern) + amtliches Anschriftenverzeichnis",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)

        for name, ags in AUSNAHMEN_AGS.items():
            gem_entry = ags_to_gem_entry.get(ags)
            authority_name = f"Stadt {name} - Bauamt (eigene untere Bauaufsichtsbehörde)"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Bauaufsichtsbehörde (kreisangehörige Gemeinde, ZustVBau)",
                    street=gem_entry.strasse if gem_entry else None, house_number=None,
                    postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                    state="Bayern", phone=None, email=gem_entry.email if gem_entry else None,
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bauakten Bayern - Ausnahmen",
                request_type_id="BAUAKTEN", state="Bayern", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=ZUSTVBAU_URL,
                source_license="Amtliche Rechtsgrundlage (ZustVBau) + amtliches Anschriftenverzeichnis",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
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
