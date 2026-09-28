"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
SACHSEN-ANHALT. Analog zu Rheinland-Pfalz (Vorbild) loesen die 18
"Verbandsgemeinden" (eigene Koerperschaft mehrerer Mitgliedsgemeinden)
das Kernproblem dieser Auskunftsart. Nach § 91 Abs. 2 Satz 1 KVG LSA
(Kommunalverfassungsgesetz Sachsen-Anhalt vom 17.06.2014, GVBl. LSA S.
288) "fuehrt [die Verbandsgemeindeverwaltung] die Verwaltungsgeschaefte
aller Aufgaben des eigenen Wirkungskreises der Mitgliedsgemeinden in
deren Namen und in deren Auftrag" - Erschliessungsbeitraege (Erlass der
Beitragsbescheide, Berechnung, Vollzug der Beitragssatzung) sind ein
solches Verwaltungsgeschaeft des eigenen Wirkungskreises und fallen
NICHT unter die in Satz 4 genannten Ausnahmen (Satzungsausfertigung,
Repraesentation nach aussen, Verpflichtungserklaerungen nach § 73). Der
Satzungsbeschluss selbst bleibt bei der Mitgliedsgemeinde (bindet die
VG-Verwaltung), die eigentliche Veranlagung/Bescheiderstellung erfolgt
aber durch die Verbandsgemeinde. Wortlaut unabhaengig direkt gegen die
offizielle Landesrecht-Datenbank (landesrecht.sachsen-anhalt.de, § 91
KVG LSA) im Browser verifiziert (Wort-fuer-Wort-Uebereinstimmung).

Datenquelle: dasselbe amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026), das bereits fuer
Niedersachsen und Sachsen genutzt wurde - enthaelt fuer Sachsen-Anhalt
exakt 18 Verbandsgemeinde-Zeilen (SATZART=50) mit vollstaendiger
Anschrift UND alle 114 zugehoerigen Mitgliedsgemeinden mit AGS
(SATZART=60) - keine zusaetzliche Recherche-Agentenwelle fuer Adressen
noetig.

Ausdruecklich NICHT abgedeckt: die uebrigen ca. 104 Einheitsgemeinden
und kreisfreien Staedte - diese verwalten sich selbst und braeuchten
Einzelrecherche, was nicht Teil dieser auf die Verbandsgemeinden-
Hebelwirkung fokussierten Welle ist.

18 neue Authorities (eine je Verbandsgemeinde), 114 neue MUNICIPALITY-
Regeln (eine je Mitgliedsgemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Sachsen-Anhalt, amtliches Anschriftenverzeichnis)"
KVG_LSA_URL = "https://www.landesrecht.sachsen-anhalt.de/bsst/document/jlr-NNLST00004167NN00000000173"
QUOTE = ("§ 91 Abs. 2 KVG LSA: 'Die Verbandsgemeindeverwaltung führt die Verwaltungsgeschäfte "
         "aller Aufgaben des eigenen Wirkungskreises der Mitgliedsgemeinden in deren Namen und "
         "in deren Auftrag, sofern diese der Verbandsgemeinde nicht nach § 90 Abs. 3 zur "
         "Erfüllung übertragen wurden.'")

# Verbandsgemeinde-Name -> dict(street, plz, city, email, gemeinden=[AGS, ...])
VERBANDSGEMEINDEN = {
    'Verbandsgemeinde An der Finne': dict(street='Auenstraße 15', plz='06647', city='Bad Bibra',
                  email='info@vgem-finne.de', gemeinden=['15084012', '15084015', '15084125', '15084132', '15084133', '15084246', '15084282']),
    'Verbandsgemeinde Arneburg-Goldbeck': dict(street='An der Zuckerfabrik 1', plz='39596', city='Goldbeck',
                  email='kontakt@arneburg-goldbeck.de', gemeinden=['15090010', '15090135', '15090180', '15090220', '15090245', '15090270', '15090435', '15090610']),
    'Verbandsgemeinde Beetzendorf-Diesdorf': dict(street='Marschweg 3', plz='38489', city='Beetzendorf',
                  email='info@vg-beetzendorf.de', gemeinden=['15081026', '15081045', '15081095', '15081105', '15081225', '15081290', '15081440', '15081545']),
    'Verbandsgemeinde Droyßiger-Zeitzer Forst': dict(street='Zeitzer Straße 15', plz='06722', city='Droyßig',
                  email='info@vgem-dzf.de', gemeinden=['15084115', '15084207', '15084275', '15084442', '15084565']),
    'Verbandsgemeinde Egelner Mulde': dict(street='Markt 18', plz='39435', city='Egeln',
                  email='post@egelnermulde.de', gemeinden=['15089041', '15089043', '15089045', '15089075', '15089365']),
    'Verbandsgemeinde Elbe-Havel-Land': dict(street='Bismarckstraße 12', plz='39524', city='Schönhausen (Elbe)',
                  email='amt@elbe-havel-land.de', gemeinden=['15090285', '15090310', '15090445', '15090485', '15090500', '15090631']),
    'Verbandsgemeinde Elbe-Heide': dict(street='Magdeburger Straße 40', plz='39326', city='Rogätz',
                  email='poststelle@elbe-heide.de', gemeinden=['15083030', '15083120', '15083130', '15083361', '15083440', '15083557', '15083580']),
    'Verbandsgemeinde Flechtingen': dict(street='Lindenplatz 11-15', plz='39345', city='Flechtingen',
                  email='info@vg-flechtingen.de', gemeinden=['15083020', '15083060', '15083115', '15083125', '15083205', '15083230', '15083323']),
    'Verbandsgemeinde Goldene Aue': dict(street='Lange Straße 8', plz='06537', city='Kelbra (Kyffhäuser)',
                  email='info@vwg-goldene-aue.de', gemeinden=['15087055', '15087101', '15087125', '15087250', '15087440']),
    'Verbandsgemeinde Mansfelder Grund-Helbra': dict(street='An der Hütte 1', plz='06311', city='Helbra',
                  email='info@verwaltungsamt-helbra.de', gemeinden=['15087010', '15087045', '15087070', '15087075', '15087205', '15087210', '15087260', '15087470']),
    'Verbandsgemeinde Obere Aller': dict(street='Zimmermannplatz 2', plz='39365', city='Eilsleben',
                  email='info@obere-aller.de', gemeinden=['15083190', '15083275', '15083320', '15083485', '15083505', '15083515', '15083535']),
    'Verbandsgemeinde Saale-Wipper': dict(street='Platz der Freundschaft 1', plz='39439', city='Güsten',
                  email='info@saale-wipper.de', gemeinden=['15089005', '15089130', '15089165', '15089185', '15089245']),
    'Verbandsgemeinde Seehausen (Altmark)': dict(street='Große Brüderstraße 1', plz='39615', city='Hansestadt Seehausen (Altmark)',
                  email='info@vgem-seehausen.de', gemeinden=['15090003', '15090007', '15090008', '15090520', '15090635']),
    'Verbandsgemeinde Unstruttal': dict(street='Markt 1', plz='06632', city='Freyburg (Unstrut)',
                  email='hauptamt@verbgem-unstruttal.de', gemeinden=['15084025', '15084135', '15084150', '15084170', '15084250', '15084285', '15084360']),
    'Verbandsgemeinde Vorharz': dict(street='Markt 7', plz='38828', city='Wegeleben',
                  email='info@vorharz.net', gemeinden=['15085090', '15085125', '15085140', '15085160', '15085285', '15085287', '15085365']),
    'Verbandsgemeinde Weida-Land': dict(street='Hauptstraße 43', plz='06268', city='Nemsdorf-Göhrendorf',
                  email='service@vg-weida-land.de', gemeinden=['15088030', '15088100', '15088250', '15088265', '15088340', '15088355']),
    'Verbandsgemeinde Westliche Börde': dict(street='Marktstraße 7', plz='39397', city='Gröningen',
                  email='post@westlicheboerde.de', gemeinden=['15083025', '15083035', '15083245', '15083355']),
    'Verbandsgemeinde Wethautal': dict(street='Corseburger Weg 11', plz='06721', city='Osterfeld',
                  email='info@vgem-wethautal.de', gemeinden=['15084013', '15084335', '15084341', '15084375', '15084445', '15084470', '15084560']),
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
        batch_id = f"erschliessung-lsa-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for vg_name, info in VERBANDSGEMEINDEN.items():
            authority = db.query(Authority).filter(Authority.authority_name == vg_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=vg_name,
                    authority_type="Verbandsgemeinde (KVG LSA)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Sachsen-Anhalt", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung LSA - {vg_name}",
                    request_type_id="ERSCHLIESSUNG", state="Sachsen-Anhalt", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{vg_name} - {QUOTE}", source_url=KVG_LSA_URL,
                    source_license="Amtliche Rechtsgrundlage (KVG LSA) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(VERBANDSGEMEINDEN)} Verbandsgemeinden.")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=QUOTE,
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
