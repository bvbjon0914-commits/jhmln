"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
SACHSEN. Analog zu Niedersachsen (Samtgemeinden), Mecklenburg-Vorpommern
und Schleswig-Holstein (jeweils Aemter) loest sich das Kernproblem
dieser Auskunftsart ueber die 64 "Verwaltungsgemeinschaften" (eine
Mitgliedsgemeinde - die "erfuellende Gemeinde" - verwaltet fuer die
anderen mit) und 6 "Verwaltungsverbaende" (eigene Koerperschaft mehrerer
Gemeinden) - zusammen 70 Einheiten. Rechtsgrundlage ist NICHT die
Saechsische Gemeindeordnung, sondern das eigenstaendige Saechsische
Gesetz ueber kommunale Zusammenarbeit (SaechsKomZG, Bekanntmachung vom
15.04.2019, SaechsGVBl. S. 270):
- § 8 Abs. 1 SaechsKomZG: der Verwaltungsverband erledigt fuer die
  Mitgliedsgemeinden u.a. "Vorbereitung und Vollzug der Beschluesse der
  Mitgliedsgemeinden" und "Geschaefte der laufenden Verwaltung".
- § 5 Abs. 4 SaechsKomZG: die gemeindlichen Vorschriften "ueber die
  Erhebung von Gebuehren und Beitraegen" finden auf den
  Verwaltungsverband entsprechende Anwendung.
- § 36 Abs. 3 SaechsKomZG: fuer Verwaltungsgemeinschaften gelten u.a.
  §§ 7 bis 10 SaechsKomZG entsprechend - die erfuellende Gemeinde wird
  fuer laufende Verwaltungsgeschaefte im Namen der jeweiligen
  Mitgliedsgemeinde taetig.
Alle Zitate direkt gegen die amtliche Quelle revosax.sachsen.de/
vorschrift/2649-SaechsKomZG geprueft.

Datenquelle: dasselbe amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026), das in dieser Sitzung
bereits fuer Niedersachsen (Samtgemeinden) und die Kreis-Adressen bei
BODENDENKMALSCHUTZ/KATASTER genutzt wurde. Enthaelt fuer Sachsen exakt
70 Verwaltungsgemeinschafts-/Verwaltungsverbands-Zeilen (SATZART=50)
mit vollstaendiger Anschrift UND alle zugehoerigen Mitgliedsgemeinden
mit AGS (SATZART=60) - keine zusaetzliche Recherche-Agentenwelle noetig.
Eine Dublette in der Rohdatei selbst wurde entdeckt und bereinigt (zwei
Gemeinden erschienen mit identischer ARS/AGS-Zeile zweifach) - nach
Bereinigung ergeben sich exakt 179 zugeordnete Gemeinden, was exakt der
unabhaengig recherchierten Sekundaerquellen-Schaetzung (158+21=179)
entspricht.

Ausdruecklich NICHT abgedeckt: die uebrigen ca. 239 Einheitsgemeinden
und kreisfreien Staedte - diese verwalten sich selbst und braeuchten
Einzelrecherche, was nicht Teil dieser auf die VG/VV-Hebelwirkung
fokussierten Welle ist.

70 neue Authorities (eine je VG/VV), 179 neue MUNICIPALITY-Regeln (eine
je Mitgliedsgemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Sachsen, amtliches Anschriftenverzeichnis)"
KOMZG_URL = "https://www.revosax.sachsen.de/vorschrift/2649-SaechsKomZG"
QUOTE = ("§ 8 Abs. 1 SächsKomZG: 'Der Verwaltungsverband erledigt folgende Aufgaben der "
         "Mitgliedsgemeinden nach deren Weisung: 1. Vorbereitung und Vollzug der Beschlüsse der "
         "Mitgliedsgemeinden, 2. Besorgung der Geschäfte, die für die Mitgliedsgemeinden keine "
         "grundsätzliche Bedeutung haben ... (Geschäfte der laufenden Verwaltung)'; § 5 Abs. 4: "
         "die Vorschriften über die Erhebung von Gebühren und Beiträgen finden entsprechende "
         "Anwendung. Für Verwaltungsgemeinschaften gilt dies über § 36 Abs. 3 entsprechend.")

# VG/VV-Name -> dict(street, plz, city, email, gemeinden=[AGS, ...])
VG_VV = {
    'Verwaltungsgemeinschaft Altenberg': dict(street='Platz des Bergmanns 2', plz='01773', city='Altenberg',
                  email='post@altenberg.de', gemeinden=['14628010', '14628170']),
    'Verwaltungsgemeinschaft Bad Gottleuba-Berggießhübel': dict(street='Königstr. 5', plz='01816', city='Bad Gottleuba-Berggießhübel',
                  email='poststelle@stadt-bgb.de', gemeinden=['14628020', '14628040', '14628230']),
    'Verwaltungsgemeinschaft Bad Lausick': dict(street='Markt 1', plz='04651', city='Bad Lausick',
                  email='sekretariat@bad-lausick.de', gemeinden=['14729010', '14729330']),
    'Verwaltungsgemeinschaft Bad Muskau': dict(street='Berliner Str. 47', plz='02953', city='Bad Muskau',
                  email='stadtverwaltung@badmuskau.eu', gemeinden=['14626010', '14626100']),
    'Verwaltungsgemeinschaft Bad Schandau': dict(street='Dresdner Str. 3', plz='01814', city='Bad Schandau',
                  email='buergermeisteramt@stadt-badschandau.de', gemeinden=['14628030', '14628320', '14628330']),
    'Verwaltungsgemeinschaft Beilrode': dict(street='Bahnhofstr. 21', plz='04886', city='Beilrode',
                  email='gemeinde@beilrode.com', gemeinden=['14730010', '14730030']),
    'Verwaltungsgemeinschaft Bernstadt / Schönau-Berzdorf': dict(street='Bautzener Str. 21', plz='02748', city='Bernstadt',
                  email='info@stadt-bernstadt.de', gemeinden=['14626030', '14626500']),
    'Verwaltungsgemeinschaft Bischofswerda': dict(street='Altmarkt 1', plz='01877', city='Bischofswerda',
                  email='poststelle@bischofswerda.de', gemeinden=['14625040', '14625510']),
    'Verwaltungsgemeinschaft Burgstädt': dict(street='Brühl 1', plz='09217', city='Burgstädt',
                  email='stadt@stadt-burgstaedt.de', gemeinden=['14522060', '14522380', '14522550']),
    'Verwaltungsgemeinschaft Burkhardtsdorf': dict(street='Am Markt 8', plz='09235', city='Burkhardtsdorf',
                  email='rathaus@burkhardtsdorf.de', gemeinden=['14521040', '14521120', '14521230']),
    'Verwaltungsgemeinschaft Bärenstein-Königswalde': dict(street='Oberwiesenthaler Str. 14', plz='09471', city='Bärenstein',
                  email='gemeinde@baerenstein-erzgebirge.de', gemeinden=['14521060', '14521340']),
    'Verwaltungsgemeinschaft Crimmitschau-Dennheritz': dict(street='Markt 1', plz='08451', city='Crimmitschau',
                  email='stadt@crimmitschau.de', gemeinden=['14524030', '14524050']),
    'Verwaltungsgemeinschaft Dohna-Müglitztal': dict(street='Am Markt 11', plz='01809', city='Dohna',
                  email='info@stadt-dohna.de', gemeinden=['14628080', '14628250']),
    'Verwaltungsgemeinschaft Dommitzsch': dict(street='Markt 1', plz='04880', city='Dommitzsch',
                  email='rathaus@stadt-dommitzsch.de', gemeinden=['14730090', '14730120', '14730320']),
    'Verwaltungsgemeinschaft Falkenstein': dict(street='Willy-Rudert-Platz 1', plz='08223', city='Falkenstein/Vogtl.',
                  email='buergermeisteramt@stadt-falkenstein.de', gemeinden=['14523120', '14523130', '14523290']),
    'Verwaltungsgemeinschaft Geyer-Tannenberg': dict(street='Altmarkt 1', plz='09468', city='Geyer',
                  email='stadtverwaltung@stadt-geyer.com', gemeinden=['14521210', '14521610']),
    'Verwaltungsgemeinschaft Großharthau': dict(street='Wesenitzweg 6', plz='01909', city='Großharthau',
                  email='sekretariat@grossharthau.de', gemeinden=['14625140', '14625170']),
    'Verwaltungsgemeinschaft Großpostwitz/O.L.': dict(street='Bahnhofstr. 2', plz='02692', city='Großpostwitz/O.L.',
                  email='gemeinde@grosspostwitz.de', gemeinden=['14625190', '14625390']),
    'Verwaltungsgemeinschaft Großschönau-Hainewalde': dict(street='Hauptstr. 54', plz='02779', city='Großschönau',
                  email='info@grossschoenau.de', gemeinden=['14626140', '14626170']),
    'Verwaltungsgemeinschaft Kirchberg': dict(street='Neumarkt 2', plz='08107', city='Kirchberg',
                  email='stadt@kirchberg.de', gemeinden=['14524040', '14524100', '14524110', '14524130']),
    'Verwaltungsgemeinschaft Klingenberg': dict(street='Schulweg 1', plz='01774', city='Klingenberg',
                  email='post@gemeinde-klingenberg.de', gemeinden=['14628150', '14628205']),
    'Verwaltungsgemeinschaft Krostitz-Schönwölkau': dict(street='Dübener Straße 1', plz='04509', city='Krostitz',
                  email='info@krostitz.com', gemeinden=['14730150', '14730280']),
    'Verwaltungsgemeinschaft Kurort Seiffen - Deutschneudorf - Heidersdorf': dict(street='Am Rathaus 4', plz='09548', city='Kurort Seiffen/Erzgeb.',
                  email='gemeinde@seiffen.de', gemeinden=['14521140', '14521280', '14521570']),
    'Verwaltungsgemeinschaft Königsbrück': dict(street='Markt 20', plz='01936', city='Königsbrück',
                  email='stadt@koenigsbrueck.de', gemeinden=['14625270', '14625300', '14625370']),
    'Verwaltungsgemeinschaft Königstein/Sächs. Schw.': dict(street='Goethestr. 7', plz='01824', city='Königstein',
                  email='post@stadt-koenigstein.de', gemeinden=['14628140', '14628210', '14628310', '14628340', '14628390']),
    'Verwaltungsgemeinschaft Lichtenberg-Weißenborn': dict(street='Bahnhofstr. 3 A', plz='09638', city='Lichtenberg',
                  email='ch.guenther@lichtenberg-erzgebirge.de', gemeinden=['14522340', '14522590']),
    'Verwaltungsgemeinschaft Limbach-Oberfrohna': dict(street='Rathausplatz 1', plz='09212', city='Limbach-Oberfrohna',
                  email='post@limbach-oberfrohna.de', gemeinden=['14524180', '14524220']),
    'Verwaltungsgemeinschaft Lohmen/Stadt Wehlen': dict(street='Schloß Lohmen 1', plz='01847', city='Lohmen',
                  email='gemeindeamt@lohmen-sachsen.de', gemeinden=['14628240', '14628370']),
    'Verwaltungsgemeinschaft Lugau': dict(street='Obere Hauptstr. 26', plz='09385', city='Lugau',
                  email='info@stv.lugau.de', gemeinden=['14521380', '14521430']),
    'Verwaltungsgemeinschaft Löbau': dict(street='Altmarkt 1', plz='02708', city='Löbau',
                  email='info@loebau.de', gemeinden=['14626150', '14626270', '14626290', '14626470']),
    'Verwaltungsgemeinschaft Meerane-Schönberg': dict(street='Lörracher Platz 1', plz='08393', city='Meerane',
                  email='post@meerane.eu', gemeinden=['14524190', '14524270']),
    'Verwaltungsgemeinschaft Mittweida': dict(street='Markt 32', plz='09648', city='Mittweida',
                  email='stadtverwaltung@mittweida.de', gemeinden=['14522010', '14522360']),
    'Verwaltungsgemeinschaft Naunhof': dict(street='Markt 1', plz='04683', city='Naunhof',
                  email='info@naunhof.de', gemeinden=['14729020', '14729300', '14729340']),
    'Verwaltungsgemeinschaft Neschwitz': dict(street='Bahnhofstr. 1', plz='02699', city='Neschwitz',
                  email='sekretariat@neschwitz.de', gemeinden=['14625360', '14625460']),
    'Verwaltungsgemeinschaft Netzschkau-Limbach': dict(street='Markt 12', plz='08491', city='Netzschkau',
                  email='info@netzschkau.de', gemeinden=['14523190', '14523260']),
    'Verwaltungsgemeinschaft Neusalza-Spremberg': dict(street='Kirchstr. 17', plz='02742', city='Neusalza-Spremberg',
                  email='stadt@neusalza-spremberg.de', gemeinden=['14626070', '14626350', '14626510']),
    'Verwaltungsgemeinschaft Nünchritz': dict(street='Glaubitzer Str. 10', plz='01612', city='Nünchritz',
                  email='buergermeisterin@nuenchritz.de', gemeinden=['14627040', '14627190']),
    'Verwaltungsgemeinschaft Oelsnitz/Vogtl., Bösenbrunn, Eichigt und Triebel/Vogtl.': dict(street='Markt 1', plz='08606', city='Oelsnitz/Vogtl.',
                  email='ob@oelsnitz.de', gemeinden=['14523060', '14523080', '14523300', '14523440']),
    'Verwaltungsgemeinschaft Olbersdorf': dict(street='Oberer Viebig 2a', plz='02785', city='Olbersdorf',
                  email='info@olbersdorf.de', gemeinden=['14626050', '14626210', '14626400', '14626430']),
    'Verwaltungsgemeinschaft Oppach-Beiersdorf': dict(street='August-Bebel-Str. 32', plz='02736', city='Oppach',
                  email='rathaus@oppach.de', gemeinden=['14626020', '14626410']),
    'Verwaltungsgemeinschaft Pegau': dict(street='Markt 1', plz='04523', city='Pegau',
                  email='sekretariat@pegau.de', gemeinden=['14729100', '14729350']),
    'Verwaltungsgemeinschaft Pirna': dict(street='Am Markt 1/2', plz='01796', city='Pirna',
                  email='stadtverwaltung@pirna.de', gemeinden=['14628070', '14628270']),
    'Verwaltungsgemeinschaft Pulsnitz': dict(street='Am Markt 1', plz='01896', city='Pulsnitz',
                  email='post@pulsnitz.de', gemeinden=['14625180', '14625320', '14625410', '14625450', '14625580']),
    'Verwaltungsgemeinschaft Reichenbach im Vogtland': dict(street='Markt 1', plz='08468', city='Reichenbach im Vogtland',
                  email='stadt@reichenbach-vogtland.de', gemeinden=['14523150', '14523340']),
    'Verwaltungsgemeinschaft Reichenbach/O.L.': dict(street='Görlitzer Str. 4', plz='02894', city='Reichenbach/O.L.',
                  email='rathaus@reichenbach-ol.de', gemeinden=['14626240', '14626450', '14626570']),
    'Verwaltungsgemeinschaft Rietschen': dict(street='Forsthausweg 2', plz='02956', city='Rietschen',
                  email='post@rietschen.de', gemeinden=['14626260', '14626460']),
    'Verwaltungsgemeinschaft Rochlitz': dict(street='Markt 1', plz='09306', city='Rochlitz',
                  email='info@rochlitz.de', gemeinden=['14522280', '14522490', '14522530', '14522600']),
    'Verwaltungsgemeinschaft Rothenburg/O.L.': dict(street='Marktplatz 1', plz='02929', city='Rothenburg/O.L.',
                  email='stadt@rothenburg-ol.de', gemeinden=['14626160', '14626480']),
    'Verwaltungsgemeinschaft Rund um den Auersberg': dict(street='Badergasse 17', plz='09350', city='Lichtenstein/Sa.',
                  email='poststelle@lichtenstein-sachsen.de', gemeinden=['14524010', '14524160', '14524280']),
    'Verwaltungsgemeinschaft Röderaue-Wülknitz': dict(street='Radener Str. 2', plz='01609', city='Röderaue',
                  email='info@roederaue.de', gemeinden=['14627240', '14627340']),
    'Verwaltungsgemeinschaft Sayda/Dorfchemnitz': dict(street='Am Markt 1', plz='09619', city='Sayda',
                  email='info@sayda.de', gemeinden=['14522090', '14522520']),
    'Verwaltungsgemeinschaft Scheibenberg-Schlettau': dict(street='Rudolf-Breitscheid-Str. 35', plz='09481', city='Scheibenberg',
                  email='info@scheibenberg.de', gemeinden=['14521510', '14521520']),
    'Verwaltungsgemeinschaft Schleife': dict(street='Friedensstr. 83', plz='02959', city='Schleife',
                  email='post@schleife-slepo.de', gemeinden=['14626120', '14626490', '14626560']),
    'Verwaltungsgemeinschaft Schöneck/Mühlental': dict(street='Sonnenwirbel 3', plz='08261', city='Schöneck',
                  email='post@stadt-schoeneck.de', gemeinden=['14523230', '14523370']),
    'Verwaltungsgemeinschaft Schönfeld': dict(street='Straße der MTS 11', plz='01561', city='Schönfeld',
                  email='sekretariat@gemeinde-schoenfeld.de', gemeinden=['14627110', '14627250']),
    'Verwaltungsgemeinschaft Stollberg/Erzgeb.': dict(street='Hauptmarkt 1', plz='09366', city='Stollberg/Erzgeb.',
                  email='info@stollberg-erzgebirge.de', gemeinden=['14521420', '14521590']),
    'Verwaltungsgemeinschaft Tharandt': dict(street='Schillerstr. 5', plz='01737', city='Tharandt',
                  email='post@tharandt.de', gemeinden=['14628090', '14628400']),
    'Verwaltungsgemeinschaft Torgau': dict(street='Markt 1', plz='04860', city='Torgau',
                  email='sv_info@torgau.de', gemeinden=['14730100', '14730310']),
    'Verwaltungsgemeinschaft Treuen/Neuensalz': dict(street='Markt 7', plz='08233', city='Treuen',
                  email='stadtverwaltung@treuen.de', gemeinden=['14523270', '14523430']),
    'Verwaltungsgemeinschaft Waldenburg': dict(street='Markt 1', plz='08396', city='Waldenburg',
                  email='info@waldenburg.de', gemeinden=['14524240', '14524260', '14524290']),
    'Verwaltungsgemeinschaft Weißwasser/O.L.': dict(street='Marktplatz', plz='02943', city='Weißwasser/O.L.',
                  email='stadt@weisswasser.de', gemeinden=['14626590', '14626600']),
    'Verwaltungsgemeinschaft Zschopau': dict(street='Altmarkt 2', plz='09405', city='Zschopau',
                  email='stadtmarketing@zschopau.de', gemeinden=['14521220', '14521690']),
    'Verwaltungsgemeinschaft Zschorlau': dict(street='August-Bebel-Str. 78', plz='08321', city='Zschorlau',
                  email='sekretariat@zschorlau.de', gemeinden=['14521080', '14521700']),
    'Verwaltungsgemeinschaft Zwönitz': dict(street='Markt 6', plz='08297', city='Zwönitz',
                  email='verwaltung@zwoenitz.de', gemeinden=['14521180', '14521710']),
    'Verwaltungsverband Am Klosterwasser': dict(street='Poststr. 8', plz='01920', city='Panschwitz-Kuckau',
                  email='verwaltung@am-klosterwasser.de', gemeinden=['14625080', '14625350', '14625440', '14625470', '14625500']),
    'Verwaltungsverband Diehsa': dict(street='Kollmer Str. 1', plz='02906', city='Waldhufen',
                  email='post@vv-diehsa.de', gemeinden=['14626190', '14626320', '14626440', '14626580']),
    'Verwaltungsverband Eilenburg-West': dict(street='Torgauer Straße 38', plz='04838', city='Eilenburg',
                  email='info@vv-eilenburg-west.de', gemeinden=['14730140', '14730360']),
    'Verwaltungsverband Jägerswald': dict(street='Hauptstr. 41', plz='08606', city='Tirpersdorf',
                  email='kontakt@jaegerswald.de', gemeinden=['14523050', '14523410', '14523420', '14523460']),
    'Verwaltungsverband Weißer Schöps/Neiße': dict(street='Straße der Freundschaft 1', plz='02923', city='Kodersdorf',
                  email='sekretariat@vvwsn-mail.de', gemeinden=['14626200', '14626230', '14626330', '14626520']),
    'Verwaltungsverband Wildenstein': dict(street='Chemnitzer Str. 41', plz='09579', city='Grünhainichen',
                  email='info@wildenstein.ws', gemeinden=['14521090', '14521270']),
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
        batch_id = f"erschliessung-sn-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for vg_name, info in VG_VV.items():
            authority = db.query(Authority).filter(Authority.authority_name == vg_name).first()
            if authority is None:
                authority_type = ("Verwaltungsverband (SächsKomZG)" if vg_name.startswith("Verwaltungsverband")
                                   else "Verwaltungsgemeinschaft (SächsKomZG)")
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=vg_name,
                    authority_type=authority_type,
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Sachsen", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung SN - {vg_name}",
                    request_type_id="ERSCHLIESSUNG", state="Sachsen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{vg_name} - {QUOTE}", source_url=KOMZG_URL,
                    source_license="Amtliche Rechtsgrundlage (SächsKomZG) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(VG_VV)} VG/VV.")
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
