"""
BODENDENKMALSCHUTZ Nordrhein-Westfalen. Anders als Bayern (Kreis-Ebene
für ALLE Einheiten) hat NRW eine Zweiteilung nach Gemeindetyp (§ 15 i.V.m.
§ 21 DSchG NRW): für KREISANGEHÖRIGE Gemeinden ist der Landrat (als
"untere staatliche Verwaltungsbehörde") die Obere Denkmalbehörde und
damit für Grabungserlaubnisse zuständig; für KREISFREIE Städte dagegen
NICHT die Stadt selbst, sondern die zuständige BEZIRKSREGIERUNG (5:
Arnsberg, Detmold, Düsseldorf, Köln, Münster).

10 parallele Recherche-Agenten (6 Batches für die 31 Landkreise, 1 für
die 5 Bezirksregierungen): 25 von 31 Landkreisen mit amtlicher Quelle
belegt, 6 blieben ehrlich OFFEN (Borken, Düren, Herford, Höxter,
Rhein-Erft-Kreis, Soest - keine amtliche Quelle mit konkreter
Organisationseinheit auffindbar, teils durch Bot-Schutz/technische
Probleme erschwert). Alle 5 Bezirksregierungen mit amtlicher Quelle
belegt (landeseinheitlich "Dezernat 35/35.4 - Denkmalangelegenheiten").

Die Zuordnung Regierungsbezirk -> kreisfreie Städte wurde NICHT vom
Agenten übernommen, sondern direkt aus der echten AdministrativeUnit-
Struktur (ags_regierungsbezirk) abgeleitet und stichprobenartig gegen
die Agenten-Aussagen geprüft (Bielefeld ausschließlich Detmold, Bonn/
Köln/Leverkusen ausschließlich Köln - beide Übereinstimmungen bestätigt).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, 10 parallele Recherche-Agenten, Bodendenkmalschutz NRW)"

# ags_kreis (Landkreis) -> dict(dept, tier, quote, url)
LANDKREISE = {
    "05558": dict(dept="Abteilung 63.1 - Bauaufsicht (Fachbereich 63)", tier="stark",
                  quote="'Grabungserlaubnisse nach § 13 DSchG für die Suche nach Bodendenkmälern (sog. Sondengehen) für Flächen im Kreis Coesfeld werden Ihnen von der Kreisverwaltung ausgestellt.'",
                  url="https://www.kreis-coesfeld.de/kreisverwaltung/organisation-abteilungen/63-bauen-wohnen-und-immissionsschutz"),
    "05954": dict(dept="Fachaufsicht Obere Denkmalbehörde (Kataster & Umwelt > Bauen & Wohnen > Bauaufsicht)", tier="stark",
                  quote="Offizielle Seite 'Fachaufsicht Obere Denkmalbehörde - Ennepe Ruhr Kreis'",
                  url="https://www.enkreis.de/kataster-umwelt/bauenwohnen/bauaufsicht/fachaufsicht-obere-denkmalbehoerde"),
    "05366": dict(dept="Amt 63 - Bauen und Wohnen", tier="schwaecher",
                  quote="Themenseite 'Denkmalschutz' strukturell unter 'Bauen + Wohnen' eingeordnet; Amt 63 als Fachbereich für Bauen/Wohnen bestätigt - kein direktes Zitat mit 'Bodendenkmal' auf derselben Seite",
                  url="https://www.kreis-euskirchen.de/themen/bauen-geoinformation/bauen-wohnen/themen-projekte/denkmalschutz/"),
    "05754": dict(dept="Untere Bauaufsicht / Obere Denkmalbehörde (4.2.1)", tier="stark",
                  quote="'Bauen: Untere Bauaufsicht / Obere Denkmalbehörde (4.2.1)'",
                  url="https://www.kreis-guetersloh.de/buergerservice-2/abteilungen/NRW:department:474/4-2-1-untere-bauaufsicht-obere-denkmalbehoerde/"),
    "05370": dict(dept="Amt für Schule, Kultur und Sport (Denkmalangelegenheiten)", tier="stark",
                  quote="'Der Kreis Heinsberg ist als obere Denkmalbehörde zuständig für die Erteilung von Grabungserlaubnissen nach § 15 DSchG.'",
                  url="https://service.kreis-heinsberg.de/dienstleistungen-a-z/-/egov-bis-detail/dienstleistung/14676/show"),
    "05958": dict(dept="Fachdienst 41 - Bauaufsicht, Wohnen, Immissionsschutz (Denkmalschutz-Team)", tier="stark",
                  quote="'Der Hochsauerlandkreis ist Obere Denkmalbehörde für das gesamte Kreisgebiet.' - Aufgabenbereich 'Grabungserlaubnisse'",
                  url="https://www.hochsauerlandkreis.de/hochsauerlandkreis/buergerservice/bauen/wohnen/kataster/bauen/wohnen/denkmalschutz"),
    "05154": dict(dept="Obere Denkmalbehörde des Kreises Kleve", tier="stark",
                  quote="'Der Kreis Kleve nimmt die Aufgaben der Oberen Denkmalbehörde als untere staatliche Verwaltungsbehörde wahr.'",
                  url="https://www.kreis-kleve.de/aufgaben/ordnungsaufgaben/denkmalwesen"),
    "05766": dict(dept="Obere Denkmalbehörde des Kreises Lippe (Fachbereich Technische Bauaufsicht)", tier="stark",
                  quote="'Obere Denkmalbehörde des Kreises Lippe – zuständig für alle Städte und Gemeinden des Kreises' (§ 15 DSchG NRW)",
                  url="https://www.kreis-lippe.de/kreis-lippe/optigov/?ansicht=dienstleistung&eintrag=135"),
    "05158": dict(dept="Obere Denkmalbehörde (Untere Naturschutzbehörde und Obere Bauaufsicht)", tier="stark",
                  quote="'Sie können uns als Obere Denkmalbehörde kontaktieren, wenn Sie eine Grabungserlaubnis benötigen, weil im Boden liegende, denkmalgeschützte Relikte betroffen sind.'",
                  url="https://www.kreis-mettmann.de/Quickmenu/Denkmalschutz-und-Grabungserlaubnisse.php?object=tx%2C2023.1049.1"),
    "05770": dict(dept="Bau- und Planungsamt", tier="schwaecher",
                  quote="'Weitere Aufgaben des Bau- und Planungsamtes liegen in den Bereichen ... Denkmalschutz ...' - keine gesonderte Organisationseinheit für Bodendenkmalschutz konkret auffindbar",
                  url="https://www.minden-luebbecke.de/Verwaltung/Verwaltung/Dezernate/Dezernat-4-Bauen-und-Umwelt/index.php?La=1&object=tx,2832.564.1&kuo=2&sub=0"),
    "05962": dict(dept="SG 461 - Bauaufsicht (Obere Denkmalbehörde)", tier="stark",
                  quote="'Grabungserlaubnis durch die Obere Denkmalbehörde für die beabsichtigte Grabung oder Bergung von Bodendenkmälern.' (§ 15 DSchG)",
                  url="https://www.maerkischer-kreis.de/service/dienstleistungen-a-z/detailseite/dienstleistung/show/grabungserlaubnis-obere-denkmalbehoerde"),
    "05374": dict(dept="Kreisbauamt, Abteilung 65/1 (Planungsrecht, Obere Bauaufsicht, Obere Denkmalbehörde, Bauverwaltung)", tier="stark",
                  quote="'Planungsrecht, Obere Bauaufsicht, Obere Denkmalbehörde, Bauverwaltung' - Leistung 'Denkmalförderung' nennt u.a. 'Bodendenkmale'",
                  url="https://service.obk.de/detail/-/vr-bis-detail/dienstleistung/26046/show"),
    "05966": dict(dept="Fachdienst Bauordnung und Wohnbauförderung", tier="stark",
                  quote="'Der Kreis Olpe ist in seiner Funktion als Obere Denkmalbehörde für die Erteilung dieser Genehmigung zuständig.' (§ 15 DSchG NRW, im Benehmen mit LWL-Archäologie)",
                  url="https://kreis-olpe.de/index.php?object=tx,3123.2&ModID=10&FID=3125.8223.1"),
    "05774": dict(dept="Amt für Bauen und Wohnen (Obere Denkmalbehörde)", tier="stark",
                  quote="'Sie ist gem. § 15 DSchG NRW zuständig für die Erteilung von Erlaubnissen für Sondengänge, Grabungen und Bergungen von Bodendenkmälern.'",
                  url="https://www.kreis-paderborn.de/kreis_paderborn/buergerservice/lebenslagen/dienstleistungen/63-obere-denkmalbehoerde.php"),
    "05562": dict(dept="Obere Denkmalbehörde (Ressort Planung und ÖPNV)", tier="stark",
                  quote="'Das Verwenden von Mess- und Suchgeräten ..., das Graben nach Bodendenkmälern und die Bergung von Bodendenkmälern bedürfen der Erlaubnis der Oberen Denkmalbehörde (§ 15 Abs. 1 DSchG NRW).'",
                  url="https://www.kreis-re.de/Inhalte/Buergerservice/Bauen_und_Grundstueck/Obere_Denkmalbehoerde.asp"),
    "05162": dict(dept="Amt 61.2 der Kreisverwaltung (Landrat als Untere staatliche Verwaltungsbehörde)", tier="stark",
                  quote="'Obere Denkmalbehörde ist der Landrat als Untere staatliche Verwaltungsbehörde (Amt 61.2 der Kreisverwaltung).'",
                  url="https://session.rhein-kreis-neuss.de/bi/vo0050.asp?__kvonr=11154"),
    "05382": dict(dept="Amt für Schule, Bildung, Kultur und Sport (Amt 40, Abteilung 40-RBB, Bereich Denkmalschutz)", tier="stark",
                  quote="'Wer nach Bodendenkmälern graben oder Bodendenkmäler bergen will, braucht hierzu eine Erlaubnis, die die Obere Denkmalbehörde erteilt.'",
                  url="https://www.rhein-sieg-kreis.de/vv/produkte/Amt_40/Abteilung_40-RBB/Denkmalschutz.php"),
    "05378": dict(dept="Bauaufsicht und Brandschutzdienststelle", tier="schwaecher",
                  quote="Dienstleistungsseite 'Denkmalschutz und Bauen' mit Broschürenverweis 'Grabungserlaubnis - Sondengehen' (LWL-Archäologie) - kein direktes wörtliches Zitat der Abteilung mit Bodendenkmal-Bezug",
                  url="https://www.rbk-direkt.de/dienstleistung.aspx?dlid=2337"),
    "05970": dict(dept="Amt für Bauen, Wohnen und Immissionsschutz", tier="stark",
                  quote="'Erteilung einer Grabungserlaubnis durch die Obere Denkmalbehörde für die beabsichtigte Grabung oder Bergung von Bodendenkmälern.'",
                  url="https://www.siegen-wittgenstein.de/Kurzmenü/A-bis-Z/index.php?object=tx|3417.2&ModID=10&FID=2171.928.1"),
    "05566": dict(dept="Bauamt - Obere Denkmalbehörde", tier="stark",
                  quote="'Formlose Anträge ... können gerne per Mail bei der Oberen Denkmalbehörde des Kreis Steinfurt eingereicht werden.'",
                  url="https://www.kreis-steinfurt.de/kv_steinfurt/Kreisverwaltung/%C3%84mter/Bauamt/Aufgaben%20und%20Dienstleistungen/Denkmalschutz/Bodendenkm%C3%A4ler/"),
    "05334": dict(dept="Amt für Bauaufsicht und Wohnraumförderung (A 63) - Obere Denkmalbehörde", tier="stark",
                  quote="'Die StädteRegion Aachen ... ist für die Erteilung von Nachforschungs- und Grabungserlaubnissen zuständig.'",
                  url="https://www.staedteregion-aachen.de/de/navigation/aemter/amt-fuer-bauaufsicht-und-wohnraumfoerderung-a-63/obere-denkmalbehoerde"),
    "05978": dict(dept="Bauordnungsangelegenheiten", tier="stark",
                  quote="Leistung 'Denkmalschutz – Grabungserlaubnis und Grabungsgenehmigung' - Zuständige Stelle: 'Bauordnungsangelegenheiten'",
                  url="https://www.kreis-unna.de/Serviceportal/index.php?&object=tx,3674.2.1&ModID=10&FID=3674.772.1&La=1"),
    "05166": dict(dept="60/3 Rechtliche Bauaufsicht, Wohnraumförderung", tier="stark",
                  quote="'Die Kreisverwaltung Viersen ist als Obere Denkmalbehörde für die Erteilung von Grabungserlaubnissen ... zuständig. Im Erlaubnisverfahren muss das Rheinische Amt für Bodendenkmalpflege beteiligt werden.'",
                  url="https://www.kreis-viersen.de/service/dienstleistungen/grabungserlaubnis-denkmalschutz"),
    "05570": dict(dept="Bauamt", tier="stark",
                  quote="'Der Kreis Warendorf in seiner Funktion als Obere Denkmalbehörde stellt diese Erlaubnis - im Benehmen mit der LWL-Archäologie für Westfalen - aus.'",
                  url="https://serviceportal.kreis-warendorf.de/detail/-/vr-bis-detail/dienstleistung/94310/show"),
    "05170": dict(dept="63 Bauen und Planen", tier="stark",
                  quote="'Der Kreis Wesel ist als Untere staatliche Verwaltungsbehörde (Obere Denkmalbehörde) für alle Städte und Gemeinden im Kreis Wesel als Aufsichtsbehörde in Denkmalangelegenheiten zuständig.'",
                  url="https://www.kreis-wesel.de/leben-arbeiten/bauen-wohnen-kataster/denkmalschutz-im-kreis-wesel"),
}

# Regierungsbezirk-Ziffer -> dict(name, dept, tier, quote, url, street, postal_code, city, email)
# Zuständig für ALLE kreisfreien Städte des jeweiligen Regierungsbezirks (§ 21 DSchG NRW).
BEZIRKSREGIERUNGEN = {
    "9": dict(name="Bezirksregierung Arnsberg", dept="Dezernat 35.4 (Denkmalangelegenheiten/Denkmalpflege)", tier="stark",
              quote="'Für Grabungen, die das Gebiet kreisfreier Städte im Regierungsbezirk berühren, ist die Bezirksregierung zuständig.'",
              url="https://www.bra.nrw.de/kultur-sport/kultur/grabung-nach-bodendenkmaelern",
              street="Seibertzstraße 1", postal_code="59821", city="Arnsberg", email="poststelle@bra.nrw.de"),
    "7": dict(name="Bezirksregierung Detmold", dept="Dezernat 35 - Städtebau, Bauaufsicht und Bau-, Wohnungs- und Denkmalangelegenheiten sowie -förderung", tier="stark",
              quote="'Obere Denkmalbehörde sind ... die Bezirksregierungen für die kreisfreien Städte, im Regierungsbezirk Detmold also lediglich Bielefeld.'",
              url="https://www.bezreg-detmold.nrw.de/wir-ueber-uns/organisationsstruktur/abteilung-3/dezernat-35/denkmalschutz-und-denkmalfoerderung",
              street="Leopoldstraße 15", postal_code="32756", city="Detmold", email=None),
    "1": dict(name="Bezirksregierung Düsseldorf", dept="Dezernat 35.4 - Denkmalschutz und -förderung", tier="stark",
              quote="'Diese wird bei kreisfreien Städten durch die Bezirksregierung im Benehmen mit dem LVR-Amt für Bodendenkmalpflege im Rheinland erteilt.'",
              url="https://www.brd.nrw.de/themen/planen-bauen/denkmalschutz/bodendenkmalschutz",
              street="Cecilienallee 2", postal_code="40474", city="Düsseldorf", email="denkmalschutz@brd.nrw.de"),
    "3": dict(name="Bezirksregierung Köln", dept="Dezernat 35 - Städtebau, Bauaufsicht und Bau-, Wohnungs- und Denkmalangelegenheiten sowie -förderung", tier="stark",
              quote="'Grabungserlaubnisse werden von den Oberen Denkmalbehörden erteilt. ... für die kreisfreien Städte ist es die Bezirksregierung.'",
              url="https://www.bezreg-koeln.nrw.de/themen/kommunales-planung-bauen-und-verkehr/bauen-und-baufoerderung/denkmalschutz-und-foerderung",
              street="Zeughausstraße 2-10", postal_code="50667", city="Köln", email="poststelle@bezreg-koeln.nrw.de"),
    "5": dict(name="Bezirksregierung Münster", dept="Dezernat 35 - Denkmalangelegenheiten", tier="stark",
              quote="'Diese wird im Gebiet der kreisfreien Städte im Regierungsbezirk Münster auf Antrag von der Oberen Denkmalbehörde der Bezirksregierung Münster in Abstimmung mit der LWL-Archäologie für Westfalen erteilt.'",
              url="https://www.brms.nrw.de/themen/bauen-planen-und-verkehr/denkmalschutz-und-denkmalpflege",
              street="Domplatz 1-3", postal_code="48143", city="Münster", email="denkmal@bezreg-muenster.nrw.de"),
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
    from app.services.address_directory import SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    ars_index = build_ars_index(df[df["Satzart"] == SATZART_KREIS])

    db = SessionLocal()
    try:
        nrw_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Nordrhein-Westfalen").all()
        kreis_names = {u.ags_kreis: u.county_name for u in nrw_units}
        gpk = {}
        for u in nrw_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreisfreie_staedte = {u.ags_kreis: u.ags_regierungsbezirk for u in nrw_units if len(gpk[u.ags_kreis]) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bodendenkmalschutz-nrw-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, info in LANDKREISE.items():
            kreis_name = kreis_names.get(ags_kreis, ags_kreis)
            authority_name = f"Landkreis {kreis_name} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                addr = ars_index.get(ags_kreis)
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Obere Denkmalbehörde (Landrat als untere staatliche Verwaltungsbehörde)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Nordrhein-Westfalen", phone=None, email=addr.email if addr else None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz NRW - Landkreise",
                request_type_id="BODENDENKMALSCHUTZ", state="Nordrhein-Westfalen", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))

        bez_authorities = {}
        for bez, info in BEZIRKSREGIERUNGEN.items():
            authority_name = f"{info['name']} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Obere Denkmalbehörde (Bezirksregierung)",
                    street=info["street"], house_number=None, postal_code=info["postal_code"],
                    city=info["city"], state="Nordrhein-Westfalen", phone=None, email=info["email"],
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")
            bez_authorities[bez] = authority

        for ags_kreis, bez in kreisfreie_staedte.items():
            info = BEZIRKSREGIERUNGEN.get(bez)
            authority = bez_authorities.get(bez)
            if info is None or authority is None:
                print(f"WARNUNG: kein Bezirksregierung-Eintrag fuer Regierungsbezirk {bez} (Kreis {ags_kreis})")
                continue
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz NRW - kreisfreie Staedte",
                request_type_id="BODENDENKMALSCHUTZ", state="Nordrhein-Westfalen", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority.authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, info in staged:
            if entry.conflict_type != "NEW":
                continue
            is_stark = info.get("tier") == "stark"
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=info["quote"],
                resulting_verification_status="VERIFIED" if is_stark else "AUTO_IMPORTED",
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
