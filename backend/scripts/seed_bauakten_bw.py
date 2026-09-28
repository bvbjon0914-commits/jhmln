"""
BAUAKTENAUSKUNFT fuer BADEN-WUERTTEMBERG. Nach § 46 Abs. 1 Nr. 3 LBO BW
(Landesbauordnung) i.V.m. § 15 Abs. 1 LVG BW (Landesverwaltungsgesetz)
sind untere Baurechtsbehoerden "in den Landkreisen die Landratsaemter
sowie nach Massgabe des § 19 die Grossen Kreisstaedte ... [und] in den
Stadtkreisen die Gemeinden". Wortlaut per Live-Browser-Abruf indirekt
(landesrecht-bw.de ist JS-gerendert) gegen dejure.org als Wortlaut-
Spiegel geprueft, Fundstellen-URLs sind aber die amtlichen
landesrecht-bw.de-Dokument-IDs.

BAULASTEN wird fuer Baden-Wuerttemberg bewusst NICHT in diesem Skript
behandelt: § 72 Abs. 3 LBO BW bestimmt ausdruecklich "Das
Baulastenverzeichnis wird von der GEMEINDE gefuehrt" - anders als in
allen anderen bisher bearbeiteten Laendern (wo dieselbe Kreis-Ebene
sowohl Bauaufsicht als auch Baulastenverzeichnis fuehrt) liegt die
Verzeichnisfuehrung in BW bei JEDER einzelnen Gemeinde, nicht beim
Landkreis - das Kreis-Ebene-Muster dieses Skripts waere fuer
BAULASTEN schlicht falsch. Eine korrekte Abdeckung braeuchte eine
Gemeinde-Ebene-Kampagne wie bei ERSCHLIESSUNG (ca. 1100 Gemeinden
individuell), was den Rahmen dieser Sitzung sprengt - absichtlich
offen gelassen statt falsch zugeordnet.

Baden-Wuerttemberg hat 9 Stadtkreise (kreisfreie Staedte: Stuttgart,
Heilbronn, Baden-Baden, Karlsruhe, Heidelberg, Mannheim, Pforzheim,
Freiburg im Breisgau, Ulm) und 35 Landkreise - insgesamt 44 "Kreise" in
AdministrativeUnit, alle nach § 46 Abs. 1 Nr. 3 LBO untere
Baurechtsbehoerde fuer ihr Gebiet (Landratsamt bzw. die Stadt selbst).

Ausnahme (§ 15 Abs. 1 Nr. 1 LVG i.V.m. § 19 LVG): 96 "Grosse
Kreisstaedte" sind trotz Kreisangehoerigkeit selbst untere
Baurechtsbehoerde fuer ihr Gebiet. Die vollstaendige Namensliste stammt
aus der Wikipedia-Kategorie "Grosse Kreisstadt in Baden-Wuerttemberg"
(keine amtliche Primaerquelle mit einer einzigen konsolidierten Liste
gefunden) - daher als Tier "schwaecher" (AUTO_IMPORTED) eingestuft,
waehrend die zugrunde liegende Rechtsnorm selbst "stark" (VERIFIED)
bleibt.

44 neue COUNTY-Regeln (9 Stadtkreise + 35 Landkreise) + 96 neue
MUNICIPALITY-Regeln (Grosse Kreisstaedte, nehmen automatisch Vorrang
vor der COUNTY-Regel ihres Landkreises) = 140 Regeln insgesamt
(abzueglich etwaiger bereits bestehender Alt-Abdeckung, die der
Konfliktpruefung korrekt als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauaktenauskunft Baden-Württemberg)"
LBO_URL = "https://www.landesrecht-bw.de/jportal/?quelle=jlink&query=BauO+BW+%C2%A7+46&psml=bsbawueprod.psml&max=true"
QUOTE_KREIS = ("§ 46 Abs. 1 LBO BW: 'Baurechtsbehörden sind ... 3. die unteren Verwaltungsbehörden und "
               "die in Absatz 2 genannten Gemeinden und Verwaltungsgemeinschaften als untere "
               "Baurechtsbehörden.' § 15 Abs. 1 LVG BW: 'Untere Verwaltungsbehörden sind 1. in den "
               "Landkreisen die Landratsämter sowie nach Maßgabe des § 19 die Großen Kreisstädte und "
               "die Verwaltungsgemeinschaften nach § 17, 2. in den Stadtkreisen die Gemeinden.'")
QUOTE_AUSNAHME = ("§ 15 Abs. 1 Nr. 1 LVG BW i.V.m. § 19 LVG BW: Große Kreisstädte sind nach Maßgabe "
                   "des § 19 LVG untere Verwaltungsbehörde (Baurecht ist nicht im Ausnahmekatalog des "
                   "§ 19 LVG genannt, verbleibt also bei der Großen Kreisstadt selbst). Liste: "
                   "Wikipedia-Kategorie 'Große Kreisstadt in Baden-Württemberg' (96 Einträge).")

# Grosse-Kreisstadt-Name -> dict(ags, street, plz, city, email)
GROSSE_KREISSTAEDTE_AGS = {
    'Aalen': dict(ags='08136088', street='Marktplatz 30', plz='73430', city='Aalen', email=None),
    'Achern': dict(ags='08317001', street='Rathausplatz 1', plz='77855', city='Achern', email=None),
    'Albstadt': dict(ags='08417079', street='Marktstraße 35', plz='72458', city='Albstadt', email=None),
    'Backnang': dict(ags='08119008', street='Am Rathaus 1', plz='71522', city='Backnang', email=None),
    'Bad Krozingen': dict(ags='08315006', street='Basler Straße 30', plz='79189', city='Bad Krozingen', email=None),
    'Bad Mergentheim': dict(ags='08128007', street='Marktplatz 1', plz='97980', city='Bad Mergentheim', email=None),
    'Bad Rappenau': dict(ags='08125006', street='Kirchplatz 4', plz='74906', city='Bad Rappenau', email=None),
    'Bad Waldsee': dict(ags='08436009', street='Hauptstraße 29', plz='88339', city='Bad Waldsee', email=None),
    'Balingen': dict(ags='08417002', street='Färberstraße 2', plz='72336', city='Balingen', email=None),
    'Biberach an der Riß': dict(ags='08426021', street='Matthias-Erzberger-Platz 1', plz='88400', city='Biberach an der Riß', email=None),
    'Bietigheim-Bissingen': dict(ags='08118079', street='Marktplatz 8', plz='74321', city='Bietigheim-Bissingen', email=None),
    'Bretten': dict(ags='08215007', street='Untere Kirchgasse 9', plz='75015', city='Bretten', email=None),
    'Bruchsal': dict(ags='08215009', street='Kaiserstraße 66', plz='76646', city='Bruchsal', email=None),
    'Böblingen': dict(ags='08115003', street='Marktplatz 16', plz='71032', city='Böblingen', email='stadt@boeblingen.de'),
    'Bühl': dict(ags='08216007', street='Hauptstraße 47', plz='77815', city='Bühl', email=None),
    'Calw': dict(ags='08235085', street='Marktplatz 9', plz='75365', city='Calw', email=None),
    'Crailsheim': dict(ags='08127014', street='Marktplatz 1', plz='74564', city='Crailsheim', email=None),
    'Ditzingen': dict(ags='08118011', street='Am Laien 1', plz='71254', city='Ditzingen', email='info@ditzingen.de'),
    'Donaueschingen': dict(ags='08326012', street='Villinger Straße 1', plz='78166', city='Donaueschingen', email=None),
    'Ehingen (Donau)': dict(ags='08425033', street='Marktplatz 1', plz='89584', city='Ehingen (Donau)', email=None),
    'Eislingen/Fils': dict(ags='08117019', street='Schlossplatz 1', plz='73054', city='Eislingen/Fils', email=None),
    'Ellwangen (Jagst)': dict(ags='08136019', street='Spitalstraße 4', plz='73479', city='Ellwangen (Jagst)', email=None),
    'Emmendingen': dict(ags='08316011', street='Rathaus', plz='79312', city='Emmendingen', email=None),
    'Eppingen': dict(ags='08125026', street='Rathausstraße 14', plz='75031', city='Eppingen', email=None),
    'Esslingen am Neckar': dict(ags='08116019', street='Rathausplatz 2', plz='73728', city='Esslingen am Neckar', email='stadt@esslingen.de'),
    'Ettlingen': dict(ags='08215017', street='Marktplatz 2', plz='76275', city='Ettlingen', email='hauptamt@ettlingen.de'),
    'Fellbach': dict(ags='08119020', street='Marktplatz 1', plz='70734', city='Fellbach', email='rathaus@fellbach.de'),
    'Filderstadt': dict(ags='08116077', street='Aicher Straße 9', plz='70794', city='Filderstadt', email='stadt@filderstadt.de'),
    'Freudenstadt': dict(ags='08237028', street='Marktplatz 1', plz='72250', city='Freudenstadt', email=None),
    'Friedrichshafen': dict(ags='08435016', street='Adenauerplatz 1', plz='88045', city='Friedrichshafen', email=None),
    'Gaggenau': dict(ags='08216015', street='Hauptstraße 71', plz='76571', city='Gaggenau', email='gaggenau.stadt@gaggenau.de'),
    'Geislingen an der Steige': dict(ags='08117024', street='Hauptstraße 1', plz='73312', city='Geislingen an der Steige', email=None),
    'Giengen an der Brenz': dict(ags='08135016', street='Marktstraße 11', plz='89537', city='Giengen an der Brenz', email=None),
    'Göppingen': dict(ags='08117026', street='Hauptstraße 1', plz='73033', city='Göppingen', email=None),
    'Heidenheim an der Brenz': dict(ags='08135019', street='Grabenstraße 15', plz='89522', city='Heidenheim an der Brenz', email=None),
    'Herrenberg': dict(ags='08115021', street='Marktplatz 5', plz='71083', city='Herrenberg', email=None),
    'Hockenheim': dict(ags='08226032', street='Rathausstraße 1', plz='68766', city='Hockenheim', email=None),
    'Horb am Neckar': dict(ags='08237040', street='Marktplatz 8', plz='72160', city='Horb am Neckar', email=None),
    'Kehl': dict(ags='08317057', street='Hauptstraße 85', plz='77694', city='Kehl', email='info@stadt-kehl.de'),
    'Kirchheim unter Teck': dict(ags='08116033', street='Marktstraße 14', plz='73230', city='Kirchheim unter Teck', email=None),
    'Konstanz': dict(ags='08335043', street='Kanzleistraße 13', plz='78462', city='Konstanz', email=None),
    'Kornwestheim': dict(ags='08118046', street='Jakob-Sigle-Platz 1', plz='70806', city='Kornwestheim', email='office@kornwestheim.de'),
    'Lahr/Schwarzwald': dict(ags='08317065', street='Rathausplatz 4', plz='77933', city='Lahr/Schwarzwald', email=None),
    'Laupheim': dict(ags='08426070', street='Marktplatz 1', plz='88471', city='Laupheim', email=None),
    'Leimen (Baden)': dict(ags='08226041', street='Rathausstraße 8', plz='69181', city='Leimen', email='stadt@leimen.de'),
    'Leinfelden-Echterdingen': dict(ags='08116078', street='Marktplatz 1', plz='70771', city='Leinfelden-Echterdingen', email='info@le-mail.de'),
    'Leonberg': dict(ags='08115028', street='Belforter Platz 1', plz='71229', city='Leonberg', email='info@leonberg.de'),
    'Leutkirch im Allgäu': dict(ags='08436055', street='Marktstraße 26', plz='88299', city='Leutkirch im Allgäu', email=None),
    'Ludwigsburg': dict(ags='08118048', street='Wilhelmstraße 11', plz='71638', city='Ludwigsburg', email='rathaus@ludwigsburg.de'),
    'Lörrach': dict(ags='08336050', street='Luisenstraße 16', plz='79539', city='Lörrach', email=None),
    'Metzingen': dict(ags='08415050', street='Stuttgarter Straße 2 - 4', plz='72555', city='Metzingen', email=None),
    'Mosbach': dict(ags='08225058', street='Hauptstraße 29', plz='74821', city='Mosbach', email=None),
    'Mössingen': dict(ags='08416025', street='Freiherr-Vom-Stein-Straße 20', plz='72116', city='Mössingen', email=None),
    'Mühlacker': dict(ags='08236040', street='Kelterplatz 7', plz='75417', city='Mühlacker', email=None),
    'Nagold': dict(ags='08235046', street='Marktstraße 27', plz='72202', city='Nagold', email=None),
    'Neckarsulm': dict(ags='08125065', street='Marktstraße 18', plz='74172', city='Neckarsulm', email=None),
    'Nürtingen': dict(ags='08116049', street='Marktstraße 7', plz='72622', city='Nürtingen', email=None),
    'Oberkirch (Baden)': dict(ags='08317089', street='Eisenbahnstraße 1', plz='77704', city='Oberkirch', email=None),
    'Offenburg': dict(ags='08317096', street='Hauptstraße 90', plz='77652', city='Offenburg', email=None),
    'Ostfildern': dict(ags='08116080', street='Klosterhof 10', plz='73760', city='Ostfildern', email='stadt@ostfildern.de'),
    'Radolfzell am Bodensee': dict(ags='08335063', street='Marktplatz 2', plz='78315', city='Radolfzell am Bodensee', email='stadt@radolfzell.de'),
    'Rastatt': dict(ags='08216043', street='Kaiserstraße 91', plz='76437', city='Rastatt', email=None),
    'Ravensburg': dict(ags='08436064', street='Salamanderweg 22', plz='88212', city='Ravensburg', email=None),
    'Remseck am Neckar': dict(ags='08118081', street='Marktplatz 1', plz='71686', city='Remseck am Neckar', email='info@remseck.de'),
    'Reutlingen': dict(ags='08415061', street='Marktplatz 22', plz='72764', city='Reutlingen', email='stadt@reutlingen.de'),
    'Rheinfelden (Baden)': dict(ags='08336069', street='Kirchplatz 2', plz='79618', city='Rheinfelden (Baden)', email=None),
    'Rheinstetten': dict(ags='08215108', street='Rappenwörthstraße 49', plz='76287', city='Rheinstetten', email='rathaus@rheinstetten.de'),
    'Rottenburg am Neckar': dict(ags='08416036', street='Marktplatz 18', plz='72108', city='Rottenburg am Neckar', email=None),
    'Rottweil': dict(ags='08325049', street='Hauptstraße 21 - 23', plz='78628', city='Rottweil', email=None),
    'Schorndorf': dict(ags='08119067', street='Marktplatz 1', plz='73614', city='Schorndorf', email=None),
    'Schramberg': dict(ags='08325053', street='Hauptstraße 25', plz='78713', city='Schramberg', email=None),
    'Schwetzingen': dict(ags='08226084', street='Hebelstraße 1', plz='68723', city='Schwetzingen', email='info@schwetzingen.de'),
    'Schwäbisch Gmünd': dict(ags='08136065', street='Marktplatz 1', plz='73525', city='Schwäbisch Gmünd', email=None),
    'Schwäbisch Hall': dict(ags='08127076', street='Am Markt 4', plz='74523', city='Schwäbisch Hall', email=None),
    'Sindelfingen': dict(ags='08115045', street='Rathausplatz 1', plz='71063', city='Sindelfingen', email='stadt@sindelfingen.de'),
    'Singen (Hohentwiel)': dict(ags='08335075', street='Hohgarten 2', plz='78224', city='Singen (Hohentwiel)', email=None),
    'Sinsheim': dict(ags='08226085', street='Wilhelmstraße 14 - 18', plz='74889', city='Sinsheim', email=None),
    'Stutensee': dict(ags='08215109', street='Rathausstraße 3', plz='76297', city='Stutensee', email='rathaus@stutensee.de'),
    'Tuttlingen': dict(ags='08327050', street='Rathausstraße 1', plz='78532', city='Tuttlingen', email=None),
    'Tübingen': dict(ags='08416041', street='Am Markt 1', plz='72070', city='Tübingen', email='stadt@tuebingen.de'),
    'Vaihingen an der Enz': dict(ags='08118073', street='Marktplatz 1', plz='71665', city='Vaihingen an der Enz', email=None),
    'Villingen-Schwenningen': dict(ags='08326074', street='Münsterplatz 7/8', plz='78050', city='Villingen-Schwenningen', email=None),
    'Waghäusel': dict(ags='08215106', street='Gymnasiumstraße 1', plz='68753', city='Waghäusel', email='stadtverwaltung@waghaeusel.de'),
    'Waiblingen': dict(ags='08119079', street='Kurze Straße 33', plz='71332', city='Waiblingen', email='rathaus@waiblingen.de'),
    'Waldkirch': dict(ags='08316056', street='Marktplatz 1 - 5', plz='79183', city='Waldkirch', email=None),
    'Waldshut-Tiengen': dict(ags='08337126', street='Kaiserstraße 28 - 32', plz='79761', city='Waldshut-Tiengen', email=None),
    'Wangen im Allgäu': dict(ags='08436081', street='Marktplatz 1', plz='88239', city='Wangen im Allgäu', email=None),
    'Weil am Rhein': dict(ags='08336091', street='Rathausplatz 1', plz='79576', city='Weil am Rhein', email='stadt@weil-am-rhein.de'),
    'Weingarten (Württemberg)': dict(ags='08436082', street='Kirchstraße 1', plz='88250', city='Weingarten', email='info@stadt-weingarten.de'),
    'Weinheim': dict(ags='08226096', street='Obertorstraße 9', plz='69469', city='Weinheim', email='rathaus@weinheim.de'),
    'Weinstadt': dict(ags='08119091', street='Marktplatz 1', plz='71384', city='Weinstadt', email='info@weinstadt.de'),
    'Wertheim': dict(ags='08128131', street='Mühlenstraße 26', plz='97877', city='Wertheim', email='stadtverwaltung@wertheim.de'),
    'Wiesloch': dict(ags='08226098', street='Marktstraße 13', plz='69168', city='Wiesloch', email=None),
    'Winnenden': dict(ags='08119085', street='Wiesenstraße 10', plz='71364', city='Winnenden', email=None),
    'Öhringen': dict(ags='08126066', street='Marktplatz 15', plz='74613', city='Öhringen', email=None),
    'Überlingen': dict(ags='08435059', street='Münsterstraße 15 - 17', plz='88662', city='Überlingen', email=None),
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
    bw = df[df["Land_name"] == "Baden-Württemberg"]
    kreis_ars_index = build_ars_index(bw[bw["Satzart"] == SATZART_KREIS])

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Baden-Württemberg").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        stadtkreise = {"08111", "08121", "08211", "08212", "08221", "08222", "08231", "08311", "08421"}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-bw-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, kreis_name in kreis_names.items():
            addr = kreis_ars_index.get(str(int(ags_kreis)))
            authority_name = f"Stadtkreis {kreis_name} - Baurechtsbehörde" if ags_kreis in stadtkreise \
                else f"Landkreis {kreis_name} - Baurechtsbehörde"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Baurechtsbehörde (Landratsamt/Stadtkreis)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Baden-Württemberg", phone=None, email=addr.email if addr else None,
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bauakten BW - Kreise",
                request_type_id="BAUAKTEN", state="Baden-Württemberg", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE_KREIS}", source_url=LBO_URL,
                source_license="Amtliche Rechtsgrundlage (LBO/LVG BW) + amtliches Anschriftenverzeichnis",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, True))

        for name, info in GROSSE_KREISSTAEDTE_AGS.items():
            authority_name = f"Stadt {name} - Baurechtsbehörde (Große Kreisstadt)"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Baurechtsbehörde (Große Kreisstadt, § 15 Abs. 1 Nr. 1 LVG BW)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Baden-Württemberg", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bauakten BW - Große Kreisstädte",
                request_type_id="BAUAKTEN", state="Baden-Württemberg", ags=info["ags"],
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=LBO_URL,
                source_license="Amtliche Rechtsgrundlage (LVG BW) + Wikipedia-Liste (Sekundärquelle)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, False))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, is_stark in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
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
