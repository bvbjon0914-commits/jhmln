"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
SCHLESWIG-HOLSTEIN. Analog zu Mecklenburg-Vorpommern und Rheinland-Pfalz
loest sich das Kernproblem dieser Auskunftsart (Erschliessungsbeitraege
werden grundsaetzlich von der einzelnen GEMEINDE erhoben, ~11.000
Gemeinden bundesweit) in SH ueber die 83 "AEMTER": nach § 3 Abs. 1 AO
(Amtsordnung fuer Schleswig-Holstein, Bekanntmachung vom 28.02.2003,
GVOBl. Schl.-H. S. 122) bereitet das Amt die Beschluesse der
Gemeindevertretung vor und "fuehrt nach diesen Beschluessen die
Selbstverwaltungsaufgaben der amtsangehoerigen Gemeinden durch" - die
inhaltliche Entscheidung (Satzungsbeschluss) bleibt bei der
Gemeindevertretung, Vorbereitung und Vollzug (Bescheiderlass,
Beitragsveranlagung) obliegen dem Amt. Wortlaut unabhaengig verifiziert
gegen gesetze.co/SH/AO/3 (deckt sich mit dem Original bei
gesetze-rechtsprechung.sh.juris.de).

Datenquellen (zwei komplementaere amtliche Quellen kombiniert, da SH -
anders als M-V - kein einzelnes Kommunalverzeichnis mit Adressen UND
Gemeinde-Zuordnung in einer Datei hat):
1. Destatis "Gemeinden in Deutschland nach Flaeche, Bevoelkerung und
   Postleitzahl am 31.12.2025" (amtlicher Regionalschluessel, Land/RB/
   Kreis/Verband/Gemeinde) - liefert die vollstaendige, maschinenlesbare
   Gemeinde-zu-Amt-Zuordnung inkl. AGS fuer alle 1018 amtsangehoerigen
   Gemeinden. Direktlink: https://www.destatis.de/DE/Themen/Laender-
   Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/
   GVAuszugJ/31122025_Auszug_GV.xlsx (selbst herunterladen, ZIP/XLSX
   validiert, Format durch direkte Byte-Pruefung selbst bestaetigt statt
   nur agentengestuetzt).
2. 11 parallele Recherche-Agenten ermittelten die Amtssitzadresse
   (Strasse, PLZ, Ort, E-Mail) fuer jedes der 83 Aemter einzeln von der
   jeweiligen offiziellen Amts-Website (bzw. dem "Zustaendigkeitsfinder
   Schleswig-Holstein", zufish.schleswig-holstein.de) - da keine
   zentrale Adressliste existiert.

Alle 83 Adressen konnten eindeutig 1:1 den 83 Destatis-Amtsnamen
zugeordnet werden (3 Sonderfaelle mit abweichender amtlicher
Kurzbezeichnung: "Burg-St. Michaelisdonn" = Amt Burg-Sankt
Michaelisdonn, "Heider Umland" = Amt Kirchspielslandgemeinde Heider
Umland, "Eider" = Amt Kirchspielslandgemeinden Eider - jeweils die im
Destatis-Verzeichnis gefuehrte Kurzform als Schluessel verwendet).

Ausdruecklich NICHT abgedeckt: die 4 kreisfreien Staedte (Flensburg,
Kiel, Luebeck, Neumuenster) und die amtsfreien Gemeinden/Staedte - diese
verwalten sich selbst und brauchten Einzelrecherche, was nicht Teil
dieser auf die Aemter-Hebelwirkung fokussierten Welle ist.

83 neue Authorities (eine je Amt), 1018 neue MUNICIPALITY-Regeln (eine
je amtsangehoeriger Gemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Schleswig-Holstein, 11 parallele Recherche-Agenten + Destatis-Gemeindeverzeichnis)"
AO_SH_URL = "https://gesetze.co/SH/AO/3"
QUOTE = ("§ 3 Abs. 1 AO: 'Das Amt bereitet im Einvernehmen mit der Bürgermeisterin oder dem "
         "Bürgermeister die Beschlüsse der Gemeinde vor und führt nach diesen Beschlüssen die "
         "Selbstverwaltungsaufgaben der amtsangehörigen Gemeinden durch.'")

# Amtsname -> dict(kreis, street, plz, city, email, url, tier, gemeinden=[AGS, ...])
AEMTER = {
    'Achterwehr': dict(kreis='Rendsburg-Eckernförde', street='Inspektor-Weimar-Weg 17', plz='24239', city='Achterwehr',
                  email='info@amt-achterwehr.de', url='https://www.amt-achterwehr.de/impressum/', tier='stark', gemeinden=['01058001', '01058028', '01058050', '01058093', '01058104', '01058126', '01058130', '01058171']),
    'Lütjenburg': dict(kreis='Plön', street='Neverstorfer Straße 7', plz='24321', city='Lütjenburg',
                  email='verwaltung@amt-luetjenburg.de', url='https://www.amt-luetjenburg.de/index.php/kontakt.html', tier='stark', gemeinden=['01057004', '01057007', '01057013', '01057021', '01057026', '01057027', '01057029', '01057030', '01057034', '01057035', '01057038', '01057048', '01057055', '01057076', '01057082']),
    'Mittelangeln': dict(kreis='Schleswig-Flensburg', street='Bahnhofstraße 1', plz='24986', city='Mittelangeln (Ortsteil Satrup)',
                  email='info@amt-mittelangeln.de', url='https://www.amt-mittelangeln.de/kontakt/index.php?dynamisch=1', tier='stark', gemeinden=['01059076', '01059161', '01059185']),
    'Arensharde': dict(kreis='Schleswig-Flensburg', street='Hauptstraße 41', plz='24887', city='Silberstedt',
                  email='amtsverwaltung@amt-arensharde.de', url='https://www.amt-arensharde.de/kontakt', tier='stark', gemeinden=['01059010', '01059023', '01059039', '01059041', '01059044', '01059057', '01059077', '01059079', '01059092']),
    'Auenland Südholstein': dict(kreis='Segeberg', street='Kirchenweg 11', plz='24568', city='Nützen',
                  email='info@auenland-suedholstein.de', url='https://www.auenland-suedholstein.de/', tier='stark', gemeinden=['01060002', '01060034', '01060036', '01060054', '01060064', '01060073']),
    'Bad Bramstedt-Land': dict(kreis='Segeberg', street='König-Christian-Straße 6', plz='24576', city='Bad Bramstedt',
                  email='info@amt-bad-bramstedt-land.de', url='https://www.amt-bad-bramstedt-land.de/', tier='stark', gemeinden=['01060003', '01060009', '01060013', '01060021', '01060023', '01060027', '01060031', '01060033', '01060035', '01060037', '01060040', '01060056', '01060095', '01060099']),
    'Bad Oldesloe-Land': dict(kreis='Stormarn', street='Louise-Zietz-Straße 4', plz='23843', city='Bad Oldesloe',
                  email='zentrale@amt-bad-oldesloe-land.de', url='https://www.amt-bad-oldesloe-land.de/kontakt', tier='stark', gemeinden=['01062019', '01062046', '01062050', '01062056', '01062062', '01062065', '01062089', '01062091', '01062092']),
    'Bargteheide-Land': dict(kreis='Stormarn', street='Eckhorst 34', plz='22941', city='Bargteheide',
                  email='info@bargteheide-land.de', url='https://www.bargteheide-land.de/Amt/Amtsverwaltung/', tier='stark', gemeinden=['01062005', '01062014', '01062016', '01062027', '01062036', '01062051', '01062078', '01062081']),
    'Berkenthin': dict(kreis='Herzogtum Lauenburg', street='Am Schart 16', plz='23919', city='Berkenthin',
                  email='info@amt-berkenthin.de', url='https://berkenthin-amt.de/verwaltung/', tier='stark', gemeinden=['01053008', '01053009', '01053011', '01053024', '01053034', '01053061', '01053067', '01053075', '01053094', '01053103', '01053120']),
    'Bokhorst-Wankendorf': dict(kreis='Plön', street='Kampstraße 1', plz='24601', city='Wankendorf',
                  email='post@amt-bokhorst-wankendorf.de', url='https://amt-bokhorst-wankendorf.de/erreichbarkeit-der-amtsverwaltung/', tier='stark', gemeinden=['01057005', '01057024', '01057068', '01057069', '01057071', '01057080', '01057083', '01057085']),
    'Boostedt-Rickling': dict(kreis='Segeberg', street='Twiete 9', plz='24598', city='Boostedt',
                  email='info@amt-boostedt-rickling.de', url='https://www.amt-boostedt-rickling.de/', tier='stark', gemeinden=['01060011', '01060016', '01060028', '01060038', '01060052', '01060068']),
    'Bordesholm': dict(kreis='Rendsburg-Eckernförde', street='Mühlenstraße 7', plz='24582', city='Bordesholm',
                  email='amt@bordesholm.de', url='https://www.bordesholm.de/impressum', tier='stark', gemeinden=['01058016', '01058022', '01058033', '01058063', '01058064', '01058076', '01058098', '01058108', '01058109', '01058133', '01058143', '01058144', '01058153', '01058170']),
    'Bornhöved': dict(kreis='Segeberg', street='Am Markt 3', plz='24610', city='Trappenkamp',
                  email='info@amt-bornhoeved.de', url='https://www.amt-bornhoeved.de/', tier='stark', gemeinden=['01060012', '01060017', '01060026', '01060072', '01060080', '01060086', '01060087', '01060089']),
    'Breitenburg': dict(kreis='Steinburg', street='Osterholz 5', plz='25524', city='Breitenburg',
                  email='info@amt-breitenburg.de', url='https://www.amt-breitenburg.de/', tier='stark', gemeinden=['01061005', '01061016', '01061017', '01061053', '01061058', '01061061', '01061068', '01061072', '01061079', '01061109', '01061115']),
    'Breitenfelde': dict(kreis='Herzogtum Lauenburg', street='Wasserkrüger Weg 16', plz='23879', city='Mölln',
                  email='info@amt-breitenfelde.de', url='https://amt-breitenfelde.de/kontakt.html', tier='stark', gemeinden=['01053002', '01053005', '01053013', '01053014', '01053037', '01053056', '01053084', '01053095', '01053113', '01053125', '01053134']),
    'Burg-St. Michaelisdonn': dict(kreis='Dithmarschen', street='Holzmarkt 7', plz='25712', city='Burg (Dithmarschen)',
                  email=None, url='https://www.amt-burg-st-michaelisdonn.de/', tier='stark', gemeinden=['01051003', '01051010', '01051012', '01051016', '01051022', '01051024', '01051026', '01051032', '01051037', '01051051', '01051064', '01051089', '01051097', '01051110']),
    'Büchen': dict(kreis='Herzogtum Lauenburg', street='Amtsplatz 1', plz='21514', city='Büchen',
                  email='info@amt-buechen.de', url='https://www.amt-buechen.de/service/amtsverwaltung', tier='stark', gemeinden=['01053010', '01053015', '01053020', '01053029', '01053035', '01053046', '01053048', '01053064', '01053080', '01053092', '01053104', '01053115', '01053119', '01053126', '01053132']),
    'Büsum-Wesselburen': dict(kreis='Dithmarschen', street='Kaiser-Wilhelm-Platz 1', plz='25761', city='Büsum',
                  email='info@amt-buesum-wesselburen.de', url='https://www.amt-buesum-wesselburen.de/', tier='stark', gemeinden=['01051013', '01051014', '01051033', '01051043', '01051045', '01051050', '01051079', '01051084', '01051093', '01051105', '01051108', '01051109', '01051121', '01051127', '01051128', '01051129', '01051132', '01051140']),
    'Dänischenhagen': dict(kreis='Rendsburg-Eckernförde', street='Sturenhagener Weg 14', plz='24229', city='Dänischenhagen',
                  email=None, url='https://www.amt-daenischenhagen.de/amt_daenischenhagen/Kontakt/', tier='stark', gemeinden=['01058037', '01058116', '01058150', '01058157']),
    'Dänischer Wohld': dict(kreis='Rendsburg-Eckernförde', street='Karl-Kolbe-Platz 1', plz='24214', city='Gettorf',
                  email='poststelle@amtdw.landsh.de', url='https://www.amt-daenischer-wohld.de/kontakt-anfahrt/', tier='stark', gemeinden=['01058051', '01058058', '01058096', '01058110', '01058112', '01058121', '01058142', '01058165']),
    'Eggebek': dict(kreis='Schleswig-Flensburg', street='Hauptstraße 2', plz='24852', city='Eggebek',
                  email='info@amt-eggebek.de', url='https://www.amteggebek.de/kontakt', tier='stark', gemeinden=['01059107', '01059128', '01059131', '01059132', '01059138', '01059162', '01059169', '01059174']),
    'Eider': dict(kreis='Dithmarschen', street='Kirchspielsschreiber-Schmidt-Straße 1', plz='25779', city='Hennstedt',
                  email='info@amt-eider.de', url='https://www.amt-eider.de/impressum', tier='stark', gemeinden=['01051005', '01051008', '01051019', '01051020', '01051023', '01051030', '01051035', '01051036', '01051038', '01051047', '01051049', '01051052', '01051053', '01051058', '01051060', '01051061', '01051065', '01051068', '01051071', '01051080', '01051088', '01051092', '01051096', '01051100', '01051102', '01051114', '01051117', '01051120', '01051125', '01051131', '01051133', '01051136', '01051139', '01051141']),
    'Eiderkanal': dict(kreis='Rendsburg-Eckernförde', street='Schulstraße 36', plz='24783', city='Osterrönfeld',
                  email='info@amt-eiderkanal.de', url='https://www.amt-eiderkanal.de/impressum', tier='stark', gemeinden=['01058026', '01058073', '01058122', '01058124', '01058132', '01058140', '01058146']),
    'Eiderstedt': dict(kreis='Nordfriesland', street='Welter Straße 1', plz='25836', city='Garding',
                  email='info@amt-eiderstedt.de', url='https://www.amt-eiderstedt.de/', tier='stark', gemeinden=['01054035', '01054036', '01054040', '01054063', '01054072', '01054090', '01054095', '01054100', '01054104', '01054113', '01054134', '01054135', '01054140', '01054145', '01054148', '01054150']),
    'Eidertal': dict(kreis='Rendsburg-Eckernförde', street='Heitmannskamp 2', plz='24220', city='Flintbek',
                  email=None, url='https://www.amt-eidertal.de/seite/716075/standorte.html', tier='stark', gemeinden=['01058018', '01058019', '01058053', '01058105', '01058107', '01058138', '01058139', '01058141', '01058145', '01058160']),
    'Elmshorn-Land': dict(kreis='Pinneberg', street='Lornsenstraße 52', plz='25335', city='Elmshorn',
                  email='poststelle@elmshorn-land.de', url='https://www.elmshorn-land.de/kontakt/', tier='stark', gemeinden=['01056029', '01056030', '01056031', '01056033', '01056042', '01056045', '01056046']),
    'Fockbek': dict(kreis='Rendsburg-Eckernförde', street='Rendsburger Straße 42', plz='24787', city='Fockbek',
                  email='info@fockbek.de', url='https://www.fockbek.de/kontakt', tier='stark', gemeinden=['01058003', '01058054', '01058118', '01058136']),
    'Föhr-Amrum': dict(kreis='Nordfriesland', street='Hafenstraße 23', plz='25938', city='Wyk auf Föhr',
                  email='info@amtfa.de', url='https://www.amtfa.de/seite/324308/Kontakt.html', tier='stark', gemeinden=['01054005', '01054015', '01054025', '01054083', '01054085', '01054087', '01054089', '01054094', '01054098', '01054129', '01054143', '01054158', '01054160', '01054163', '01054164']),
    'Geest und Marsch Südholstein': dict(kreis='Pinneberg', street='Wedeler Chaussee 21', plz='25492', city='Heist',
                  email='info@amt-gums.de', url='https://www.amt-geest-und-marsch-suedholstein.de/', tier='stark', gemeinden=['01056001', '01056016', '01056019', '01056020', '01056023', '01056024', '01056027', '01056028', '01056036', '01056037']),
    'Geltinger Bucht': dict(kreis='Schleswig-Flensburg', street='Holmlück 2', plz='24972', city='Steinbergkirche',
                  email='info@amt-geltingerbucht.de', url='https://www.amt-geltingerbucht.de/impressum', tier='stark', gemeinden=['01059102', '01059109', '01059112', '01059121', '01059136', '01059142', '01059147', '01059148', '01059152', '01059154', '01059155', '01059163', '01059164', '01059167', '01059168', '01059186']),
    'Großer Plöner See': dict(kreis='Plön', street='Heinrich-Rieper-Straße 8', plz='24306', city='Plön',
                  email='info@amt-gps.de', url='https://www.amt-gps.de/kontakt', tier='stark', gemeinden=['01057015', '01057017', '01057022', '01057032', '01057045', '01057053', '01057065', '01057067', '01057089']),
    'Haddeby': dict(kreis='Schleswig-Flensburg', street='Panellenweg 5', plz='24866', city='Busdorf',
                  email='info@amt-haddeby.de', url='https://www.haddeby.de/seite/178730/kontaktdaten-oeffnungszeiten.html', tier='stark', gemeinden=['01059012', '01059018', '01059019', '01059026', '01059032', '01059043', '01059056', '01059078']),
    'Heider Umland': dict(kreis='Dithmarschen', street='Kirchspielsweg 6', plz='25746', city='Heide',
                  email='info@amt-heider-umland.de', url='https://www.amt-heider-umland.de/impressum.html', tier='stark', gemeinden=['01051048', '01051067', '01051069', '01051075', '01051081', '01051082', '01051087', '01051107', '01051113', '01051122', '01051130']),
    'Hohe Elbgeest': dict(kreis='Herzogtum Lauenburg', street='Christa-Höppner-Platz 1', plz='21521', city='Dassendorf',
                  email=None, url='https://www.amt-hohe-elbgeest.de/Kurzmenü/Kontakt/', tier='stark', gemeinden=['01053003', '01053012', '01053023', '01053028', '01053050', '01053053', '01053072', '01053131', '01053133', '01053135']),
    'Hohner Harde': dict(kreis='Rendsburg-Eckernförde', street='Rendsburger Straße 42', plz='24787', city='Fockbek',
                  email='info@fockbek.de', url='https://www.rathaus-fockbek.de/herzlich-willkommen/amt-hohner-harde/portrait', tier='stark', gemeinden=['01058010', '01058029', '01058036', '01058047', '01058055', '01058056', '01058070', '01058078', '01058089', '01058097', '01058129', '01058154']),
    'Horst-Herzhorn': dict(kreis='Steinburg', street='Elmshorner Straße 27', plz='25358', city='Horst (Holst.)',
                  email='info@amt-horst-herzhorn.de', url='https://www.amt-horst-herzhorn.de/', tier='stark', gemeinden=['01061004', '01061012', '01061015', '01061027', '01061037', '01061041', '01061044', '01061050', '01061054', '01061074', '01061101', '01061118']),
    'Hörnerkirchen': dict(kreis='Pinneberg', street='Am Markt 1', plz='25355', city='Barmstedt',
                  email='info@stadt-barmstedt.de', url='https://www.vg-barmstedt-hoernerkirchen.de/amt-hoernerkirchen', tier='stark', gemeinden=['01056006', '01056010', '01056038', '01056051']),
    'Hürup': dict(kreis='Schleswig-Flensburg', street='Schulstraße 1', plz='24975', city='Hürup',
                  email='info@amt-huerup.de', url='https://www.amt-huerup.de/kontakt/index.php', tier='stark', gemeinden=['01059103', '01059116', '01059126', '01059127', '01059182']),
    'Hüttener Berge': dict(kreis='Rendsburg-Eckernförde', street='Mühlenstraße 8', plz='24361', city='Groß Wittensee',
                  email='info@amt-huettener-berge.de', url='https://www.holtsee.de/politik/amt-huettener-berge', tier='stark', gemeinden=['01058008', '01058024', '01058030', '01058035', '01058039', '01058066', '01058069', '01058080', '01058081', '01058083', '01058088', '01058111', '01058123', '01058127', '01058152', '01058175']),
    'Itzehoe-Land': dict(kreis='Steinburg', street='Margarete-Steiff-Weg 3', plz='25524', city='Itzehoe',
                  email='mailbox@amtitzehoe-land.de', url='https://www.amt-itzehoe-land.de/kontakt', tier='stark', gemeinden=['01061008', '01061010', '01061024', '01061034', '01061035', '01061039', '01061040', '01061045', '01061047', '01061052', '01061059', '01061065', '01061067', '01061070', '01061082', '01061083', '01061084', '01061098', '01061100', '01061114']),
    'Itzstedt': dict(kreis='Segeberg', street='Segeberger Straße 41', plz='23845', city='Itzstedt',
                  email='info@amt-itzstedt.de', url='https://www.amt-itzstedt.de/', tier='stark', gemeinden=['01060043', '01060046', '01060058', '01060065', '01060076', '01060085']),
    'Jevenstedt': dict(kreis='Rendsburg-Eckernförde', street='Meiereistraße 5', plz='24808', city='Jevenstedt',
                  email='info@amt-jevenstedt.de', url='https://www.amt-jevenstedt.de/amt/adresseoeffnungszeiten-amtsverwaltung/', tier='stark', gemeinden=['01058031', '01058048', '01058068', '01058071', '01058075', '01058086', '01058101', '01058148', '01058155', '01058172']),
    'Kappeln-Land': dict(kreis='Schleswig-Flensburg', street='Reeperbahn 2', plz='24376', city='Kappeln',
                  email='info@stadt-kappeln.de', url='https://www.kappeln.de/Amt-Kappeln-Land/', tier='stark', gemeinden=['01059002', '01059034', '01059067', '01059068']),
    'Kellinghusen': dict(kreis='Steinburg', street='Hauptstraße 14', plz='25548', city='Kellinghusen',
                  email='info@amt-kellinghusen.de', url='https://www.amt-kellinghusen.de/', tier='stark', gemeinden=['01061019', '01061028', '01061036', '01061038', '01061042', '01061049', '01061064', '01061071', '01061080', '01061086', '01061088', '01061089', '01061093', '01061096', '01061103', '01061111', '01061112', '01061116', '01061117']),
    'Kisdorf': dict(kreis='Segeberg', street='Winsener Straße 2', plz='24568', city='Kattendorf',
                  email='info@amt-kisdorf.de', url='https://www.amt-kisdorf.de/', tier='stark', gemeinden=['01060042', '01060045', '01060047', '01060066', '01060077', '01060082', '01060084', '01060094', '01060100']),
    'Krempermarsch': dict(kreis='Steinburg', street='Birkenweg 29', plz='25361', city='Krempe',
                  email=None, url='https://www.amt-krempermarsch.de/kontakt/', tier='stark', gemeinden=['01061006', '01061022', '01061026', '01061030', '01061055', '01061056', '01061057', '01061073', '01061092', '01061104']),
    'Kropp-Stapelholm': dict(kreis='Schleswig-Flensburg', street='Am Markt 10', plz='24848', city='Kropp',
                  email='info@kropp-stapelholm.de', url='https://www.kropp.de/Kurzmenü/Kontakt/', tier='stark', gemeinden=['01059001', '01059005', '01059009', '01059020', '01059024', '01059035', '01059050', '01059051', '01059053', '01059058', '01059087', '01059088', '01059096', '01059188']),
    'Landschaft Sylt': dict(kreis='Nordfriesland', street='Andreas-Nielsen-Straße 1', plz='25980', city='Westerland (Gemeinde Sylt)',
                  email=None, url='https://www.amtlandschaftsylt.de/kontakt.html', tier='stark', gemeinden=['01054046', '01054061', '01054078', '01054149']),
    'Langballig': dict(kreis='Schleswig-Flensburg', street='Süderende 1', plz='24977', city='Langballig',
                  email='amt.langballig@langballig.de', url='https://www.amt-langballig.de/kontakt', tier='stark', gemeinden=['01059106', '01059118', '01059137', '01059145', '01059157', '01059176', '01059178']),
    'Lauenburgische Seen': dict(kreis='Herzogtum Lauenburg', street='Fünfhausen 1', plz='23909', city='Ratzeburg',
                  email='kontakt@amt-lauenburgische-seen.de', url='https://amt-lauenburgische-seen.de/amtsverwaltung.html', tier='stark', gemeinden=['01053001', '01053004', '01053016', '01053018', '01053026', '01053030', '01053033', '01053040', '01053041', '01053043', '01053051', '01053054', '01053057', '01053062', '01053066', '01053078', '01053088', '01053093', '01053098', '01053102', '01053107', '01053110', '01053117', '01053123', '01053136']),
    'Leezen': dict(kreis='Segeberg', street='Hamburger Straße 28', plz='23816', city='Leezen',
                  email='info@amt-leezen.de', url='https://www.amt-leezen.de/', tier='stark', gemeinden=['01060007', '01060008', '01060022', '01060029', '01060041', '01060051', '01060053', '01060057', '01060062', '01060074', '01060088', '01060101']),
    'Lensahn': dict(kreis='Ostholstein', street='Eutiner Straße 2', plz='23738', city='Lensahn',
                  email='amt-lensahn@amt-lensahn.de', url='https://www.lensahn.de/willkommen-im-amt-lensahn', tier='stark', gemeinden=['01055006', '01055011', '01055020', '01055023', '01055027', '01055029', '01055036']),
    'Lütau': dict(kreis='Herzogtum Lauenburg', street='Amtsplatz 6', plz='21481', city='Lauenburg/Elbe',
                  email='info@amt-luetau.de', url='https://www.amt-luetau.de/kontakt/', tier='stark', gemeinden=['01053006', '01053019', '01053022', '01053058', '01053073', '01053074', '01053082', '01053087', '01053111', '01053128']),
    'Marne-Nordsee': dict(kreis='Dithmarschen', street='Alter Kirchhof 4-5', plz='25709', city='Marne',
                  email='info@amt-marne-nordsee.de', url='https://www.amt-marne-nordsee.de/kontakt', tier='stark', gemeinden=['01051021', '01051034', '01051046', '01051057', '01051062', '01051072', '01051073', '01051076', '01051077', '01051090', '01051103', '01051118', '01051119']),
    'Mitteldithmarschen': dict(kreis='Dithmarschen', street='Roggenstraße 14', plz='25704', city='Meldorf',
                  email='info@mitteldithmarschen.de', url='https://www.mitteldithmarschen.de/', tier='stark', gemeinden=['01051001', '01051002', '01051004', '01051006', '01051015', '01051017', '01051027', '01051028', '01051039', '01051054', '01051063', '01051074', '01051078', '01051083', '01051085', '01051086', '01051098', '01051099', '01051104', '01051126', '01051134', '01051135', '01051137', '01051138']),
    'Mittelholstein': dict(kreis='Rendsburg-Eckernförde', street='Am Markt 15', plz='24594', city='Hohenwestedt',
                  email='info@amt-mittelholstein.de', url='https://www.amt-mittelholstein.de/impressum', tier='stark', gemeinden=['01058007', '01058009', '01058013', '01058014', '01058015', '01058025', '01058044', '01058061', '01058062', '01058072', '01058074', '01058077', '01058085', '01058100', '01058103', '01058106', '01058113', '01058115', '01058119', '01058125', '01058128', '01058131', '01058134', '01058151', '01058156', '01058158', '01058159', '01058161', '01058164', '01058167']),
    'Mittleres Nordfriesland': dict(kreis='Nordfriesland', street='Theodor-Storm-Straße 2', plz='25821', city='Bredstedt',
                  email='info@amnf.de', url='https://www.amnf.de/', tier='stark', gemeinden=['01054002', '01054006', '01054010', '01054012', '01054014', '01054019', '01054020', '01054024', '01054037', '01054038', '01054045', '01054059', '01054071', '01054075', '01054080', '01054093', '01054121', '01054128', '01054146']),
    'Nordsee-Treene': dict(kreis='Nordfriesland', street='Schulweg 19', plz='25866', city='Mildstedt',
                  email='info@amt-nordsee-treene.de', url='https://www.amt-nordsee-treene.de/', tier='stark', gemeinden=['01054007', '01054023', '01054026', '01054032', '01054042', '01054043', '01054052', '01054054', '01054070', '01054084', '01054091', '01054096', '01054097', '01054099', '01054105', '01054106', '01054116', '01054119', '01054120', '01054130', '01054132', '01054141', '01054156', '01054157', '01054159', '01054161', '01054162']),
    'Nordstormarn': dict(kreis='Stormarn', street='Am Schiefen Kamp 10', plz='23858', city='Reinfeld (Holstein)',
                  email=None, url='https://www.amt-nordstormarn.de/Amt/Amtsverwaltung/', tier='stark', gemeinden=['01062003', '01062008', '01062025', '01062031', '01062032', '01062039', '01062048', '01062059', '01062083', '01062087', '01062093', '01062094']),
    'Nortorfer  Land': dict(kreis='Rendsburg-Eckernförde', street='Niedernstraße 6', plz='24589', city='Nortorf',
                  email='info@amt-nortorfer-land.de', url='https://www.amt-nortorfer-land.de/kontakt', tier='stark', gemeinden=['01058011', '01058021', '01058023', '01058027', '01058038', '01058045', '01058046', '01058049', '01058059', '01058065', '01058091', '01058094', '01058117', '01058120', '01058147', '01058163', '01058168']),
    'Oeversee': dict(kreis='Schleswig-Flensburg', street='Tornschauer Straße 3-5', plz='24963', city='Tarp',
                  email='info@amt-oeversee.de', url='https://www.amtoeversee.de/verwaltung-politik/adresse-und-oeffnungszeiten/', tier='stark', gemeinden=['01059159', '01059171', '01059184']),
    'Oldenburg-Land': dict(kreis='Ostholstein', street='Hinter den Höfen 2', plz='23758', city='Oldenburg in Holstein',
                  email='info@amt-oldenburg-land.de', url='https://www.amt-oldenburg-land.de/', tier='stark', gemeinden=['01055014', '01055015', '01055017', '01055022', '01055031', '01055043']),
    'Ostholstein-Mitte': dict(kreis='Ostholstein', street='Am Ruhsal 2', plz='23744', city='Schönwalde am Bungsberg',
                  email='info@amt-ostholstein-mitte.landsh.de', url='https://www.amt-ostholstein-mitte.de/impressum', tier='stark', gemeinden=['01055002', '01055024', '01055037', '01055038', '01055039']),
    'Pellworm': dict(kreis='Nordfriesland', street='Uthlandestraße 1', plz='25849', city='Pellworm',
                  email='info@amt-pellworm.de', url='https://www.gemeinde-pellworm.de/von-a-z/', tier='stark', gemeinden=['01054039', '01054050', '01054074', '01054103']),
    'Pinnau': dict(kreis='Pinneberg', street='Hauptstraße 60', plz='25462', city='Rellingen',
                  email='info@amt-pinnau.de', url='https://www.amt-pinnau.de/', tier='stark', gemeinden=['01056009', '01056013', '01056032', '01056040', '01056047']),
    'Preetz-Land': dict(kreis='Plön', street='Am Berg 2', plz='24211', city='Schellhorn',
                  email='info@amtpreetzland.de', url='https://www.amtpreetzland.de/kontakt', tier='stark', gemeinden=['01057002', '01057010', '01057011', '01057023', '01057031', '01057033', '01057037', '01057042', '01057046', '01057047', '01057054', '01057058', '01057059', '01057066', '01057070', '01057084', '01057086']),
    'Probstei': dict(kreis='Plön', street='Knüll 4', plz='24217', city='Schönberg (Holstein)',
                  email='info@amt-probstei.de', url='https://www.amt-probstei.de/', tier='stark', gemeinden=['01057003', '01057006', '01057012', '01057018', '01057020', '01057028', '01057039', '01057040', '01057041', '01057043', '01057049', '01057056', '01057060', '01057063', '01057073', '01057078', '01057079', '01057081', '01057087', '01057088']),
    'Rantzau': dict(kreis='Pinneberg', street='Chemnitzstraße 30', plz='25355', city='Barmstedt',
                  email='info@amt-rantzau.de', url='https://www.amt-rantzau.de/', tier='stark', gemeinden=['01056003', '01056004', '01056008', '01056011', '01056014', '01056017', '01056022', '01056026', '01056034', '01056035']),
    'Sandesneben-Nusse': dict(kreis='Herzogtum Lauenburg', street='Am Amtsgraben 4', plz='23898', city='Sandesneben',
                  email='info@amt-sn.de', url='https://www.amt-sn.de/', tier='stark', gemeinden=['01053025', '01053038', '01053039', '01053044', '01053068', '01053069', '01053077', '01053079', '01053081', '01053085', '01053086', '01053096', '01053097', '01053099', '01053101', '01053108', '01053109', '01053112', '01053114', '01053118', '01053121', '01053122', '01053124', '01053127', '01053130']),
    'Schafflund': dict(kreis='Schleswig-Flensburg', street='Tannenweg 1', plz='24980', city='Schafflund',
                  email='info@amt-schafflund.de', url='https://www.amt-schafflund.de/kontakt', tier='stark', gemeinden=['01059105', '01059115', '01059123', '01059124', '01059129', '01059143', '01059144', '01059149', '01059151', '01059158', '01059173', '01059177', '01059179']),
    'Schenefeld': dict(kreis='Steinburg', street='Holstenstraße 42-48', plz='25560', city='Schenefeld',
                  email='info@amt-schenefeld.de', url='https://www.amt-schenefeld.de/', tier='stark', gemeinden=['01061001', '01061003', '01061011', '01061013', '01061014', '01061021', '01061031', '01061033', '01061043', '01061048', '01061066', '01061076', '01061078', '01061081', '01061085', '01061087', '01061091', '01061097', '01061105', '01061106', '01061107', '01061108']),
    'Schlei-Ostsee': dict(kreis='Rendsburg-Eckernförde', street='Holm 13', plz='24340', city='Eckernförde',
                  email='mail@amt-schlei-ostsee.de', url='https://www.amt-schlei-ostsee.de/impressum/', tier='stark', gemeinden=['01058004', '01058012', '01058032', '01058040', '01058042', '01058052', '01058057', '01058067', '01058082', '01058084', '01058087', '01058090', '01058099', '01058102', '01058137', '01058162', '01058166', '01058173', '01058174']),
    'Schrevenborn': dict(kreis='Plön', street='Dorfplatz 2', plz='24226', city='Heikendorf',
                  email='info@amt-schrevenborn.de', url='https://www.amt-schrevenborn.de/', tier='stark', gemeinden=['01057025', '01057051', '01057074']),
    'Schwarzenbek-Land': dict(kreis='Herzogtum Lauenburg', street='Gülzower Straße 1', plz='21493', city='Schwarzenbek',
                  email='info@amt-schwarzenbek-land.de', url='https://www.amt-schwarzenbek-land.de/Amtsverwaltung/Adressen/', tier='stark', gemeinden=['01053007', '01053017', '01053021', '01053027', '01053031', '01053036', '01053042', '01053045', '01053047', '01053049', '01053052', '01053059', '01053060', '01053070', '01053071', '01053076', '01053089', '01053091', '01053106']),
    'Selent/ Schlesen': dict(kreis='Plön', street='Kieler Straße 18', plz='24238', city='Selent',
                  email='info@amt-selent-schlesen.de', url='https://www.amt-selent-schlesen.de/', tier='stark', gemeinden=['01057016', '01057044', '01057050', '01057052', '01057072', '01057077', '01057090']),
    'Siek': dict(kreis='Stormarn', street='Hauptstraße 49', plz='22962', city='Siek',
                  email='info@amtsiek.de', url='https://www.amtsiek.de/', tier='stark', gemeinden=['01062011', '01062035', '01062069', '01062071', '01062088']),
    'Südangeln': dict(kreis='Schleswig-Flensburg', street='Toft 7', plz='24860', city='Böklund',
                  email='info@amt-suedangeln.de', url='https://www.amt-suedangeln.de/', tier='stark', gemeinden=['01059008', '01059037', '01059042', '01059049', '01059062', '01059073', '01059081', '01059082', '01059084', '01059086', '01059090', '01059093', '01059097', '01059098', '01059189']),
    'Süderbrarup': dict(kreis='Schleswig-Flensburg', street='Königstraße 5', plz='24392', city='Süderbrarup',
                  email='verwaltung@amt-suederbrarup.de', url='https://ratsinfo.amt-suederbrarup.de/', tier='schwaecher', gemeinden=['01059006', '01059055', '01059060', '01059063', '01059065', '01059070', '01059072', '01059074', '01059080', '01059083', '01059094', '01059095', '01059187']),
    'Südtondern': dict(kreis='Nordfriesland', street='Marktstraße 12', plz='25899', city='Niebüll',
                  email='info@amt-suedtondern.de', url='https://www.amt-suedtondern.de/', tier='stark', gemeinden=['01054001', '01054009', '01054016', '01054017', '01054018', '01054022', '01054027', '01054034', '01054048', '01054055', '01054062', '01054065', '01054068', '01054073', '01054076', '01054077', '01054086', '01054088', '01054109', '01054110', '01054124', '01054125', '01054126', '01054131', '01054136', '01054142', '01054154', '01054165', '01054166', '01054167']),
    'Trave-Land': dict(kreis='Segeberg', street='Waldemar-von-Mohl-Straße 10', plz='23795', city='Bad Segeberg',
                  email='info@amt-trave-land.de', url='https://www.amt-trave-land.de/amtsverwaltung/kontakt/', tier='stark', gemeinden=['01060006', '01060010', '01060015', '01060018', '01060020', '01060024', '01060025', '01060030', '01060048', '01060049', '01060050', '01060059', '01060060', '01060061', '01060067', '01060069', '01060070', '01060071', '01060075', '01060079', '01060081', '01060090', '01060091', '01060093', '01060096', '01060097', '01060098']),
    'Trittau': dict(kreis='Stormarn', street='Europaplatz 5', plz='22946', city='Trittau',
                  email='info@trittau.de', url='https://www.amt-trittau.de/', tier='stark', gemeinden=['01062020', '01062021', '01062022', '01062026', '01062033', '01062040', '01062045', '01062058', '01062082', '01062086']),
    'Viöl': dict(kreis='Nordfriesland', street='Westerende 41', plz='25884', city='Viöl',
                  email='info@amt-vioel.de', url='https://www.amt-vioel.de/', tier='stark', gemeinden=['01054003', '01054004', '01054011', '01054013', '01054041', '01054057', '01054079', '01054092', '01054101', '01054118', '01054123', '01054144', '01054152']),
    'Wilstermarsch': dict(kreis='Steinburg', street='Kohlmarkt 25', plz='25554', city='Wilster',
                  email='amt@wilstermarsch.de', url='https://www.wilster.de/', tier='stark', gemeinden=['01061002', '01061007', '01061018', '01061020', '01061023', '01061025', '01061060', '01061062', '01061063', '01061077', '01061095', '01061102', '01061110', '01061119']),
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
        batch_id = f"erschliessung-sh-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for amt_name, info in AEMTER.items():
            authority_name = f"Amt {amt_name}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Amt (Verwaltungsgemeinschaft nach AO SH)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Schleswig-Holstein", phone=None, email=info["email"],
                    source=f"Amtliche Amts-Website, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            is_stark = info.get("tier") == "stark"
            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung SH - {amt_name}",
                    request_type_id="ERSCHLIESSUNG", state="Schleswig-Holstein", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE}", source_url=AO_SH_URL,
                    source_license="Amtliche Rechtsgrundlage (Amtsordnung SH) + Amts-Website",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append((entry, is_stark))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(AEMTER)} Ämter.")
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
