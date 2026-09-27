"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
BRANDENBURG. Analog zu den anderen Bundeslaendern dieser Welle loesen
die "Aemter" (Verwaltungsgemeinschaften mehrerer amtsangehoeriger
Gemeinden) das Kernproblem dieser Auskunftsart. Nach § 135 Abs. 3 Satz
1-2 BbgKVerf (Kommunalverfassung des Landes Brandenburg vom 18.12.2007,
zuletzt geaendert, GVBl. I) "besorgt [das Amt] die Kassen- und
Rechnungsfuehrung ... fuer die amtsangehoerigen Gemeinden. Dazu gehoeren
auch die Veranschlagung und Erhebung der Gemeindeabgaben." -
Erschliessungs-/Strassenbaubeitraege sind Gemeindeabgaben im Sinne des
Kommunalabgabengesetzes Brandenburg (KAG Bbg) i.V.m. § 127 ff. BauGB.
Wortlaut per Live-Browser-Abruf direkt gegen die amtliche
bravors.brandenburg.de-Quelle verifiziert (Wort-fuer-Wort-
Uebereinstimmung).

Von den 52 gefundenen Verwaltungseinheiten sind 50 klassische "Aemter"
(direkt durch § 135 Abs. 3 BbgKVerf abgedeckt, Tier "stark"). Die
uebrigen 2 - "Verbandsgemeinde Liebenwerda" und die "Erfuellende
Gemeinde" Schwedt/Oder (die fuer mehrere amtsangehoerige Gemeinden mit
verwaltet) - tragen abweichende Bezeichnungen, deren genaue rechtliche
Grundlage (vermutlich GKGBbg statt BbgKVerf) in dieser Sitzung NICHT
einzeln verifiziert wurde; sie werden vorsichtshalber als "schwaecher"
(AUTO_IMPORTED statt VERIFIED) eingestuft, obwohl sie strukturell
dieselbe Funktion erfuellen.

Datenquelle: dasselbe amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026), das bereits fuer
Niedersachsen/Sachsen/Sachsen-Anhalt genutzt wurde - enthaelt fuer
Brandenburg alle 52 Einheiten mit vollstaendiger Anschrift UND alle 272
zugehoerigen Mitgliedsgemeinden mit AGS - keine zusaetzliche
Recherche-Agentenwelle fuer Adressen noetig.

Ausdruecklich NICHT abgedeckt: die uebrigen ca. 141 amtsfreien
Gemeinden/Staedte (inkl. kreisfreier Staedte) - diese verwalten sich
selbst und braeuchten Einzelrecherche, was nicht Teil dieser auf die
Aemter-Hebelwirkung fokussierten Welle ist.

52 neue Authorities, 272 neue MUNICIPALITY-Regeln (eine je
Mitgliedsgemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Brandenburg, amtliches Anschriftenverzeichnis)"
BBGKVERF_URL = "https://bravors.brandenburg.de/gesetze/bbgkverf#135"
QUOTE = ("§ 135 Abs. 3 BbgKVerf: 'Das Amt besorgt die Kassen- und Rechnungsführung und die "
         "Vorbereitung der Aufstellung der Haushaltspläne sowie deren Durchführung für die "
         "amtsangehörigen Gemeinden. Dazu gehören auch die Veranschlagung und Erhebung der "
         "Gemeindeabgaben.'")

# Einheiten-Name -> dict(typ, street, plz, city, email, gemeinden=[AGS, ...])
AEMTER = {
    'Amt Altdöbern': dict(typ='Amt', street='Marktstraße 1', plz='03229', city='Altdöbern',
                  email='info@amt-altdoebern.de', gemeinden=['12066008', '12066041', '12066202', '12066226', '12066228']),
    'Amt Bad Wilsnack/Weisen': dict(typ='Amt', street='Am Markt 1', plz='19336', city='Bad Wilsnack',
                  email='info(at)amtbww.de', gemeinden=['12070008', '12070052', '12070241', '12070348', '12070416']),
    'Amt Barnim-Oderbruch': dict(typ='Amt', street='Freienwalder Straße 48', plz='16269', city='Wriezen',
                  email='stadtverwaltung@wriezen.de', gemeinden=['12064061', '12064349', '12064365', '12064371', '12064393', '12064417']),
    'Amt Beetzsee': dict(typ='Amt', street='Chausseestraße 33b', plz='14778', city='Beetzsee OT Brielow',
                  email='info@amt-beetzsee.de', gemeinden=['12069018', '12069019', '12069270', '12069460', '12069541']),
    'Amt Biesenthal-Barnim': dict(typ='Amt', street='Berliner Straße 1', plz='16359', city='Biesenthal',
                  email='info@amt-biesenthal-barnim.de', gemeinden=['12060024', '12060034', '12060154', '12060161', '12060192', '12060250']),
    'Amt Brieskow-Finkenheerd': dict(typ='Amt', street='August-Bebel-Straße 18a', plz='15295', city='Brieskow-Finkenheerd',
                  email='kontakt@amt-b-f.de', gemeinden=['12067076', '12067180', '12067508', '12067528', '12067552']),
    'Amt Britz-Chorin-Oderberg': dict(typ='Amt', street='Eisenwerkstraße 11', plz='16230', city='Britz',
                  email='post@amt-bco.de', gemeinden=['12060036', '12060045', '12060092', '12060128', '12060149', '12060172', '12060176', '12060185']),
    'Amt Brück': dict(typ='Amt', street='Ernst-Thälmann-Straße 59', plz='14822', city='Brück',
                  email='info@amt-brueck.de', gemeinden=['12069052', '12069056', '12069076', '12069216', '12069345', '12069470']),
    'Amt Brüssow (Uckermark)': dict(typ='Amt', street='Prenzlauer Straße 8', plz='17326', city='Brüssow',
                  email='info@amt-bruessow.de', gemeinden=['12073085', '12073093', '12073216', '12073490', '12073520']),
    'Amt Burg (Spreewald)': dict(typ='Amt', street='Hauptstraße 46', plz='03096', city='Burg (Spreewald)',
                  email=' info@amt-burg-spreewald.de', gemeinden=['12071028', '12071032', '12071041', '12071164', '12071341', '12071412']),
    'Amt Dahme/Mark': dict(typ='Amt', street='Hauptstraße 48-49', plz='15936', city='Dahme/Mark',
                  email='amt@dahme.de', gemeinden=['12072053', '12072055', '12072157', '12072298']),
    'Amt Döbern-Land': dict(typ='Amt', street='Forster Straße 8', plz='03159', city='Döbern',
                  email='post@amt-doebern-land.de', gemeinden=['12071044', '12071074', '12071153', '12071189', '12071294', '12071392', '12071414']),
    'Amt Elsterland': dict(typ='Amt', street='Kindergartenstraße 2a', plz='03253', city='Schönborn',
                  email='amt@elsterland.de', gemeinden=['12062219', '12062417', '12062440', '12062453', '12062492']),
    'Amt Falkenberg-Höhe': dict(typ='Amt', street='Karl-Marx-Straße 2', plz='16259', city='Falkenberg',
                  email='info@amt-fahoe.de', gemeinden=['12064053', '12064125', '12064205', '12064222']),
    'Amt Friesack': dict(typ='Amt', street='Marktstraße 22', plz='14662', city='Friesack',
                  email='info@amt-friesack.de', gemeinden=['12063088', '12063142', '12063202', '12063228', '12063240', '12063256']),
    'Amt Gartz (Oder)': dict(typ='Amt', street='Kleine Klosterstraße 153', plz='16307', city='Gartz (Oder)',
                  email='info@gartz.de', gemeinden=['12073097', '12073189', '12073309', '12073393', '12073565']),
    'Amt Gerswalde': dict(typ='Amt', street='Dorfmitte 14a', plz='17268', city='Gerswalde',
                  email=' info@amt-gerswalde.de', gemeinden=['12073157', '12073201', '12073396', '12073404', '12073569']),
    'Amt Golzow': dict(typ='Amt', street='Seelower Straße 14', plz='15328', city='Golzow',
                  email='sekretariat@amt-golzow.de', gemeinden=['12064009', '12064057', '12064172', '12064266', '12064538']),
    'Amt Gramzow': dict(typ='Amt', street='Poststraße 25', plz='17291', city='Gramzow',
                  email='info@amtgramzow.de', gemeinden=['12073225', '12073261', '12073430', '12073458', '12073578', '12073645']),
    'Amt Gransee und Gemeinden': dict(typ='Amt', street='Baustraße 56', plz='16775', city='Gransee',
                  email='abgeordnete@gransee.de', gemeinden=['12065100', '12065117', '12065276', '12065301', '12065310']),
    'Amt Joachimsthal(Schorfheide)': dict(typ='Amt', street='Joachimsplatz 1-3', plz='16247', city='Joachimsthal',
                  email='sekretariat@amt-joachimsthal.de', gemeinden=['12060012', '12060068', '12060100', '12060296']),
    'Amt Kleine Elster(Niederlausitz)': dict(typ='Amt', street='Turmstraße 5', plz='03238', city='Massen-Niederlausitz',
                  email='info@amt-kleine-elster.de', gemeinden=['12062088', '12062293', '12062333', '12062425']),
    'Amt Lebus': dict(typ='Amt', street='Breite Straße 1', plz='15326', city='Lebus',
                  email='buerodesamtsdirektors@amt-lebus.de', gemeinden=['12064268', '12064388', '12064420', '12064480', '12064539']),
    'Amt Lenzen-Elbtalaue': dict(typ='Amt', street='Kellerstraße 4', plz='19309', city='Lenzen',
                  email='mail@amtlenzen.de', gemeinden=['12070060', '12070236', '12070244', '12070246']),
    'Amt Lieberose/Oberspreewald': dict(typ='Amt', street='Kirchstraße 11', plz='15913', city='Straupitz (Spreewald)',
                  email='amt@lieberose-oberspreewald.de', gemeinden=['12061005', '12061061', '12061224', '12061308', '12061352', '12061450', '12061470', '12061476']),
    'Amt Lindow (Mark)': dict(typ='Amt', street='Straße des Friedens 20', plz='16835', city='Lindow (Mark)',
                  email='webmaster@amt-lindow-mark.de', gemeinden=['12068188', '12068280', '12068372', '12068437']),
    'Amt Meyenburg': dict(typ='Amt', street='Freyensteiner Straße 42', plz='16945', city='Meyenburg',
                  email='mail@amtmeyenburg.de', gemeinden=['12070096', '12070153', '12070222', '12070266', '12070280']),
    'Amt Märkische Schweiz': dict(typ='Amt', street='Hauptstraße 1', plz='15377', city='Buckow (Märkische Schweiz)',
                  email='amtsverwaltung@amt-maerkische-schweiz.de', gemeinden=['12064084', '12064153', '12064303', '12064370', '12064408', '12064484']),
    'Amt Nennhausen': dict(typ='Amt', street='Fouqué-Platz 3', plz='14715', city='Nennhausen',
                  email='info@amt-nennhausen.de', gemeinden=['12063165', '12063186', '12063212', '12063293']),
    'Amt Neustadt (Dosse)': dict(typ='Amt', street='Bahnhofstraße 6', plz='16845', city='Neustadt (Dosse)',
                  email='amt@neustadt-dosse.de', gemeinden=['12068052', '12068109', '12068324', '12068409', '12068417', '12068501']),
    'Amt Neuzelle': dict(typ='Amt', street='Lindenpark 6', plz='15898', city='Neuzelle',
                  email='amt@neuzelle.de', gemeinden=['12067292', '12067338', '12067357']),
    'Amt Niemegk': dict(typ='Amt', street='Großstraße 6', plz='14823', city='Niemegk',
                  email='post@amt-niemegk.de', gemeinden=['12069402', '12069448', '12069474', '12069485']),
    'Amt Odervorland': dict(typ='Amt', street='Bahnhofstraße 3-4', plz='15518', city='Briesen (Mark)',
                  email='info@amt-odervorland.de', gemeinden=['12067040', '12067072', '12067237', '12067473']),
    'Amt Ortrand': dict(typ='Amt', street='Altmarkt 1', plz='01990', city='Ortrand',
                  email='post@amt-ortrand.de', gemeinden=['12066064', '12066104', '12066168', '12066188', '12066240', '12066316']),
    'Amt Peitz': dict(typ='Amt', street='Schulstraße 6', plz='03185', city='Peitz',
                  email='peitz@peitz.de', gemeinden=['12071052', '12071060', '12071176', '12071193', '12071304', '12071384', '12071386', '12071401']),
    'Amt Plessa': dict(typ='Amt', street='Steinweg 6', plz='04928', city='Plessa',
                  email='amtplessa@t-online.de', gemeinden=['12062177', '12062240', '12062372', '12062464']),
    'Amt Putlitz-Berge': dict(typ='Amt', street='Zur Burghofwiese 2', plz='16949', city='Putlitz',
                  email='mail@amtputlitz-berge.de', gemeinden=['12070028', '12070145', '12070300', '12070325', '12070393']),
    'Amt Rhinow': dict(typ='Amt', street='Lilienthalstraße 3', plz='14728', city='Rhinow',
                  email='amtsdirektor@rhinow.de', gemeinden=['12063094', '12063112', '12063134', '12063161', '12063260', '12063274']),
    'Amt Ruhland': dict(typ='Amt', street='Rudolf-Breitscheid-Straße 4', plz='01945', city='Ruhland',
                  email='amt@amt-ruhland.de', gemeinden=['12066116', '12066120', '12066124', '12066132', '12066272', '12066292']),
    'Amt Scharmützelsee': dict(typ='Amt', street='Forsthausstraße 4', plz='15526', city='Bad Saarow',
                  email='post@amt-scharmuetzelsee.de', gemeinden=['12067024', '12067112', '12067288', '12067413', '12067520']),
    'Amt Schenkenländchen': dict(typ='Amt', street='Markt 9', plz='15755', city='Teupitz',
                  email='service@amt-schenkenlaendchen.de', gemeinden=['12061192', '12061216', '12061328', '12061344', '12061448', '12061492']),
    'Amt Schlaubetal': dict(typ='Amt', street='Bahnhofstraße 40', plz='15299', city='Müllrose',
                  email='post@amt-schlaubetal.de', gemeinden=['12067205', '12067324', '12067336', '12067397', '12067438', '12067458']),
    'Amt Schlieben': dict(typ='Amt', street='Herzberger Straße 7', plz='04936', city='Schlieben',
                  email='amt-schlieben@t-online.de', gemeinden=['12062134', '12062237', '12062282', '12062289', '12062445']),
    'Amt Schradenland': dict(typ='Amt', street='Großenhainer Straße 25', plz='04932', city='Gröden',
                  email='info@amt-schradenland.de', gemeinden=['12062196', '12062208', '12062232', '12062336']),
    'Amt Seelow-Land': dict(typ='Amt', street='Küstriner Straße 67', plz='15306', city='Seelow',
                  email='info@amt-seelow-land.de', gemeinden=['12064128', '12064130', '12064190', '12064288', '12064290', '12064340', '12064482']),
    'Amt Spreenhagen': dict(typ='Amt', street='Hauptstraße 13', plz='15528', city='Spreenhagen',
                  email='post@amt-spreenhagen.de', gemeinden=['12067173', '12067408', '12067469']),
    'Amt Temnitz': dict(typ='Amt', street='Bergstraße 2', plz='16818', city='Walsleben',
                  email='info@amt-temnitz.de', gemeinden=['12068072', '12068306', '12068413', '12068425', '12068426', '12068452']),
    'Amt Unterspreewald': dict(typ='Amt', street='Markt 1', plz='15938', city='Golßen',
                  email='info@golssen.de', gemeinden=['12061017', '12061097', '12061164', '12061244', '12061265', '12061405', '12061428', '12061435', '12061471', '12061510']),
    'Amt Wusterwitz': dict(typ='Amt', street='August-Bebel-Straße 10', plz='14789', city='Wusterwitz',
                  email='info@amt-wusterwitz.de', gemeinden=['12069028', '12069537', '12069688']),
    'Amt Ziesar': dict(typ='Amt', street='Mühlentor 15A', plz='14793', city='Ziesar',
                  email='amt@amt-ziesar.de', gemeinden=['12069089', '12069224', '12069232', '12069648', '12069680', '12069696']),
    'Schwedt/Oder, Stadt': dict(typ='Erfüllende Gemeinde', street='Dr. Theodor-Neubauer-Straße 5', plz='16303', city='Schwedt/Oder',
                  email='stadt@schwedt.de', gemeinden=['12073440', '12073532']),
    'Verbandsgemeinde Liebenwerda': dict(typ='Verbandsgemeinde', street='Markt 1', plz='04924', city='Bad Liebenwerda',
                  email='zentrale@vg-liebenwerda.de', gemeinden=['12062024', '12062128', '12062341', '12062500']),
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
        batch_id = f"erschliessung-bb-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for name, info in AEMTER.items():
            is_stark = info["typ"] == "Amt"
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type=f"{info['typ']} (BbgKVerf)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Brandenburg", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung BB - {name}",
                    request_type_id="ERSCHLIESSUNG", state="Brandenburg", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{name} - {QUOTE}", source_url=BBGKVERF_URL,
                    source_license="Amtliche Rechtsgrundlage (BbgKVerf) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append((entry, is_stark))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(AEMTER)} Einheiten.")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, is_stark in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=QUOTE,
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
