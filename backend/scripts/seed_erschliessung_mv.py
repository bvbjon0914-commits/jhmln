"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
MECKLENBURG-VORPOMMERN. Erschliessungsbeitraege werden grundsaetzlich von
der jeweiligen GEMEINDE selbst als Erschliessungstraeger erhoben - das
ist bundesweit das Kernproblem bei dieser Auskunftsart (~11.000
Gemeinden deutschlandweit). In M-V loest sich das analog zu Rheinland-
Pfalz (Verbandsgemeinden) ueber die 76 "AEMTER": nach § 127 Abs. 2 KV
M-V (Kommunalverfassung Mecklenburg-Vorpommern, Bekanntmachung vom
16.05.2024, GVOBl. M-V 2024 S. 270) besorgt das Amt "die Kassengeschaefte
... sowie die Veranlagung und Erhebung der Gemeindeabgaben fuer die
amtsangehoerigen Gemeinden" - Erschliessungs-/Strassenbaubeitraege sind
Gemeindeabgaben im Sinne des KAG M-V, damit ist deren Veranlagung und
Erhebung gesetzlich dem AMT zugewiesen, nicht der einzelnen
amtsangehoerigen Gemeinde. Flankierend § 125 Abs. 1 KV M-V: "Die AEmter
treten als Traeger von Aufgaben der oeffentlichen Verwaltung an die
Stelle der amtsangehoerigen Gemeinden, soweit dieses Gesetz es bestimmt
oder zulaesst." Zitat unabhaengig vom Recherche-Agenten bestaetigt.

Datenquelle: offizielles "Kommunalverzeichnis aktuell mit AGS und
Bezeichnungen" (XLSX) des Ministeriums fuer Inneres, Bau und
Digitalisierung M-V (https://www.regierung-mv.de/serviceassistent/
download?id=1687478, selbst herunterladen und geparst) - enthaelt fuer
jedes der 76 AEmter die Amtssitzadresse UND fuer jede der 684
amtsangehoerigen Gemeinden ihren amtlichen Gemeindeschlüssel (AGS), d.h.
keine externe Kreuzreferenz-Tabelle noetig (anders als bei der RLP-Welle,
wo eine separate VG250-Zuordnungsdatei erforderlich war).

Ausdruecklich NICHT abgedeckt durch dieses Skript: die 2 kreisfreien
Staedte (Rostock, Schwerin) und die 32-38 amtsfreien Gemeinden - diese
verwalten sich selbst und brauchten Einzelrecherche wie eine normale
Grossstadt, was nicht Teil dieser auf die AEmter-Hebelwirkung
fokussierten Welle ist.

76 neue Authorities (eine je Amt), 684 neue MUNICIPALITY-Regeln (eine je
amtsangehoeriger Gemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Mecklenburg-Vorpommern, Kommunalverzeichnis-Auswertung)"
KV_URL = "https://www.regierung-mv.de/serviceassistent/download?id=1674185"
KOMMUNALVERZEICHNIS_URL = "https://www.regierung-mv.de/serviceassistent/download?id=1687478"
QUOTE = ("§ 127 Abs. 2 KV M-V: 'Das Amt besorgt die Kassengeschäfte und führt das "
         "Rechnungswesen sowie die Veranlagung und Erhebung der Gemeindeabgaben für "
         "die amtsangehörigen Gemeinden.'")

# Amtsname -> dict(kreis, street, plz, city, email, gemeinden=[AGS, ...])
AEMTER = {
    'Altenpleen': dict(kreis='Vorpommern-Rügen', street='Parkstr. 2', plz='18445', city='Altenpleen',
                  email='info@altenpleen.de', gemeinden=['13073005', '13073037', '13073044', '13073046', '13073066', '13073068']),
    'Am Peenestrom': dict(kreis='Vorpommern-Greifswald', street='Burgstr. 6', plz='17438', city='Wolgast',
                  email='info@wolgast.de', gemeinden=['13075021', '13075072', '13075074', '13075087', '13075124', '13075144', '13075147']),
    'Am Stettiner Haff': dict(kreis='Vorpommern-Greifswald', street='Stettiner Str. 1', plz='17367', city='Eggesin',
                  email='rathaus@eggesin.de', gemeinden=['13075001', '13075003', '13075031', '13075037', '13075051', '13075075', '13075078', '13075084', '13075085', '13075089', '13075093', '13075139']),
    'Anklam-Land': dict(kreis='Vorpommern-Greifswald', street='Rebelower Damm 2', plz='17392', city='Spantekow',
                  email='info@amt-anklam-land.de', gemeinden=['13075007', '13075013', '13075015', '13075020', '13075022', '13075029', '13075053', '13075068', '13075073', '13075088', '13075155', '13075101', '13075098', '13075110', '13075116', '13075122', '13075127', '13075128']),
    'Bad Doberan-Land': dict(kreis='Rostock', street='Kammerhof 3', plz='18209', city='Bad Doberan',
                  email='info@doberan-land.de', gemeinden=['13072001', '13072007', '13072017', '13072047', '13072075', '13072083', '13072086', '13072099', '13072117']),
    'Barth': dict(kreis='Vorpommern-Rügen', street='Teergang 2', plz='18356', city='Barth',
                  email='info@amt-barth.de', gemeinden=['13073009', '13073018', '13073025', '13073042', '13073043', '13073051', '13073053', '13073069', '13073077', '13073094']),
    'Bergen auf Rügen': dict(kreis='Vorpommern-Rügen', street='Markt 5- 6', plz='18528', city='Bergen auf Rügen',
                  email='info@stadt-bergen-auf-ruegen.de', gemeinden=['13073010', '13073014', '13073027', '13073038', '13073049', '13073063', '13073064', '13073065', '13073072', '13073074', '13073083']),
    'Boizenburg-Land': dict(kreis='Ludwigslust-Parchim', street='Fritz-Reuter-Str. 3', plz='19258', city='Boizenburg/Elbe',
                  email='info@amtboizenburgland.de', gemeinden=['13076009', '13076010', '13076016', '13076030', '13076054', '13076055', '13076102', '13076106', '13076122', '13076136', '13076138']),
    'Bützow-Land': dict(kreis='Rostock', street='Am Markt 1', plz='18246', city='Bützow',
                  email='verwaltung@buetzow.de', gemeinden=['13072009', '13072013', '13072020', '13072028', '13072050', '13072053', '13072078', '13072089', '13072101', '13072104', '13072114', '13072120']),
    'Carbäk': dict(kreis='Rostock', street='Moorweg 5', plz='18184', city='Broderstorf',
                  email='poststelle@amtcarbaek.de', gemeinden=['13072019', '13072081', '13072087', '13072108']),
    'Crivitz': dict(kreis='Ludwigslust-Parchim', street='Amtsstr. 5', plz='19089', city='Crivitz',
                  email='info@amt-crivitz.de', gemeinden=['13076005', '13076007', '13076023', '13076024', '13076025', '13076029', '13076033', '13076038', '13076044', '13076080', '13076082', '13076112', '13076113', '13076117', '13076133', '13076140', '13076158']),
    'Darß/Fischland': dict(kreis='Vorpommern-Rügen', street='Chausseestr. 68a', plz='18375', city='Born a. Darß',
                  email='info@darss-fischland.de', gemeinden=['13073002', '13073012', '13073017', '13073067', '13073100', '13073103']),
    'Demmin-Land': dict(kreis='Mecklenburgische Seenplatte', street='Goethestr. 43', plz='17109', city='Demmin',
                  email='info@amt-demmin-land.de', gemeinden=['13071008', '13071014', '13071064', '13071065', '13071072', '13071076', '13071089', '13071096', '13071112', '13071128', '13071131', '13071136', '13071139', '13071148', '13071150', '13071157']),
    'Dorf Mecklenburg-Bad Kleinen': dict(kreis='Nordwestmecklenburg', street='Am Wehberg 17', plz='23972', city='Dorf Mecklenburg',
                  email='info@amt-dorfmecklenburg-badkleinen.de', gemeinden=['13074002', '13074003', '13074008', '13074019', '13074030', '13074031', '13074047', '13074053', '13074082']),
    'Dömitz-Malliß': dict(kreis='Ludwigslust-Parchim', street='Slüterplatz 2', plz='19303', city='Dömitz',
                  email='mail@amtdoemitz-malliss.de', gemeinden=['13076034', '13076053', '13076067', '13076093', '13076094', '13076103', '13076143']),
    'Eldenburg Lübz': dict(kreis='Ludwigslust-Parchim', street='Am Markt 22', plz='19386', city='Lübz',
                  email='info@amt-eldenburg-luebz.de', gemeinden=['13076040', '13076165', '13076051', '13076075', '13076077', '13076089', '13076109', '13076168', '13076125', '13076151']),
    'Franzburg-Richtenberg': dict(kreis='Vorpommern-Rügen', street='Garthofstr.  18', plz='18461', city='Franzburg',
                  email='info@amt-franzburg-richtenberg.de', gemeinden=['13073024', '13073029', '13073034', '13073057', '13073062', '13073076', '13073086', '13073096', '13073097', '13073098']),
    'Friedland': dict(kreis='Mecklenburgische Seenplatte', street='Riemannstr. 42', plz='17098', city='Friedland',
                  email='stadt@friedland-mecklenburg.de', gemeinden=['13071028', '13071035', '13071037']),
    'Gadebusch': dict(kreis='Nordwestmecklenburg', street='Am Markt 1', plz='19205', city='Gadebusch',
                  email='hauptamt@gadebusch.info', gemeinden=['13074020', '13074021', '13074040', '13074043', '13074054', '13074068', '13074070', '13074081']),
    'Gnoien': dict(kreis='Rostock', street='Teterower Str. 11a', plz='17179', city='Gnoien',
                  email='info@amt-gnoien.de', gemeinden=['13072004', '13072010', '13072031', '13072035', '13072111']),
    'Goldberg-Mildenitz': dict(kreis='Ludwigslust-Parchim', street='Lange Str. 67', plz='19399', city='Goldberg',
                  email='info@amt-goldberg-mildenitz.de', gemeinden=['13076032', '13076048', '13076096', '13076104', '13076135']),
    'Grabow': dict(kreis='Ludwigslust-Parchim', street='Am Markt 1', plz='19300', city='Grabow',
                  email='info@grabow.de', gemeinden=['13076003', '13076021', '13076027', '13076037', '13076049', '13076050', '13076069', '13076076', '13076097', '13076098', '13076100', '13076115', '13076161']),
    'Grevesmühlen-Land': dict(kreis='Nordwestmecklenburg', street='Rathausplatz 1', plz='23936', city='Grevesmühlen',
                  email='info@grevesmuehlen.de', gemeinden=['13074005', '13074022', '13074069', '13074071', '13074093', '13074077', '13074079', '13074085']),
    'Güstrow-Land': dict(kreis='Rostock', street='Haselstr. 4', plz='18273', city='Güstrow',
                  email='info@amt-guestrow-land.de', gemeinden=['13072033', '13072039', '13072042', '13072044', '13072055', '13072061', '13072067', '13072069', '13072071', '13072073', '13072079', '13072084', '13072092', '13072119']),
    'Hagenow-Land': dict(kreis='Ludwigslust-Parchim', street='Bahnhofstr. 25', plz='19230', city='Hagenow',
                  email='info@amt-hagenow-land.de', gemeinden=['13076002', '13076004', '13076008', '13076013', '13076019', '13076041', '13076057', '13076064', '13076065', '13076070', '13076079', '13076099', '13076110', '13076111', '13076116', '13076119', '13076131', '13076169', '13076145']),
    'Jarmen-Tutow': dict(kreis='Vorpommern-Greifswald', street='Dr.Georg-Kohnert-Str. 5', plz='17126', city='Jarmen',
                  email='svjarmen@amt-jarmen-tutow.de', gemeinden=['13075002', '13075009', '13075023', '13075054', '13075070', '13075134', '13075140']),
    'Klützer Winkel': dict(kreis='Nordwestmecklenburg', street='Schloßstr. 1', plz='23948', city='Klütz',
                  email='poststelle@kluetzer-winkel.de', gemeinden=['13074010', '13074016', '13074032', '13074037', '13074039', '13074089']),
    'Krakow am See': dict(kreis='Rostock', street='Markt 2', plz='18292', city='Krakow am See',
                  email='amtsleitung@krakow-am-see.de', gemeinden=['13072026', '13072048', '13072056', '13072059', '13072063']),
    'Laage': dict(kreis='Rostock', street='Am Markt 7', plz='18299', city='Laage',
                  email='info@stadt-laage.de', gemeinden=['13072027', '13072046', '13072062', '13072112']),
    'Landhagen': dict(kreis='Vorpommern-Greifswald', street='Theodor-Körner-Str. 36', plz='17498', city='Neuenkirchen',
                  email='post@amt-landhagen.de', gemeinden=['13075008', '13075025', '13075027', '13075050', '13075076', '13075091', '13075102', '13075141', '13075142']),
    'Lubmin': dict(kreis='Vorpommern-Greifswald', street='Geschwister-Scholl-Weg 15', plz='17509', city='Lubmin',
                  email='info@amtlubmin.de', gemeinden=['13075018', '13075046', '13075059', '13075060', '13075069', '13075081', '13075083', '13075097', '13075120', '13075146']),
    'Ludwigslust-Land': dict(kreis='Ludwigslust-Parchim', street='Wöbbeliner Str. 5', plz='19288', city='Ludwigslust',
                  email='info@amt-ludwigslust-land.de', gemeinden=['13076001', '13076018', '13076046', '13076058', '13076086', '13076087', '13076118', '13076134', '13076141', '13076146', '13076156']),
    'Löcknitz-Penkun': dict(kreis='Vorpommern-Greifswald', street='Chausseestr. 30', plz='17321', city='Löcknitz',
                  email='amt@amt-lp.de', gemeinden=['13075011', '13075012', '13075016', '13075035', '13075038', '13075067', '13075079', '13075095', '13075107', '13075108', '13075113', '13075117', '13075119']),
    'Lützow-Lübstorf': dict(kreis='Nordwestmecklenburg', street='Dorfmitte 24', plz='19209', city='Lützow',
                  email='kontakt@luetzow-luebstorf.de', gemeinden=['13074001', '13074012', '13074014', '13074015', '13074024', '13074025', '13074038', '13074048', '13074050', '13074061', '13074062', '13074064', '13074072', '13074075', '13074088']),
    'Malchin am Kummerower See': dict(kreis='Mecklenburgische Seenplatte', street='Am Markt  1', plz='17139', city='Malchin',
                  email='stadt.malchin@t-online.de', gemeinden=['13071007', '13071032', '13071039', '13071084', '13071092', '13071109']),
    'Malchow': dict(kreis='Mecklenburgische Seenplatte', street='Alter Markt 1', plz='17213', city='Malchow',
                  email='info@inselstadt-malchow.de', gemeinden=['13071001', '13071036', '13071043', '13071093', '13071113', '13071138', '13071155', '13071171']),
    'Mecklenburgische Kleinseenplatte': dict(kreis='Mecklenburgische Seenplatte', street='Rudolph-Breitscheid-Str. 24', plz='17252', city='Mirow',
                  email='sekretariat@amt-mecklenburgische-kleinseenplatte.de', gemeinden=['13071099', '13071119', '13071159', '13071167']),
    'Mecklenburgische Schweiz': dict(kreis='Rostock', street='Von-Pentz-Allee 7', plz='17166', city='Teterow',
                  email='info@amt-ms.de', gemeinden=['13072003', '13072023', '13072024', '13072038', '13072040', '13072041', '13072045', '13072049', '13072066', '13072082', '13072094', '13072096', '13072103', '13072109', '13072113']),
    'Miltzow': dict(kreis='Vorpommern-Rügen', street='Bahnhofsallee 8a', plz='18519', city='Sundhagen, OT Miltzow',
                  email='info@amt-miltzow.de', gemeinden=['13073023', '13073090', '13073102']),
    'Mönchgut-Granitz': dict(kreis='Vorpommern-Rügen', street='Göhrener Weg 1', plz='18586', city='Baabe',
                  email='info@amt-mg.de', gemeinden=['13073006', '13073031', '13073048', '13073107', '13073084', '13073106']),
    'Neubukow-Salzhaff': dict(kreis='Rostock', street='Panzower Landweg 1', plz='18233', city='Neubukow',
                  email='amt@neubukow-salzhaff.de', gemeinden=['13072002', '13072005', '13072008', '13072014', '13072022', '13072085']),
    'Neuburg': dict(kreis='Nordwestmecklenburg', street='Hauptstr. 10a', plz='23974', city='Neuburg',
                  email='zentrale@amt-neuburg.eu', gemeinden=['13075010', '13074007', '13074009', '13074034', '13074044', '13074056']),
    'Neukloster-Warin': dict(kreis='Nordwestmecklenburg', street='Haupstr. 27', plz='23992', city='Neukloster',
                  email='info@amt-neukloster-warin.de', gemeinden=['13074006', '13074023', '13074036', '13074046', '13074057', '13074060', '13074084', '13074090', '13074091']),
    'Neustadt-Glewe': dict(kreis='Ludwigslust-Parchim', street='Markt 1', plz='19306', city='Neustadt-Glewe',
                  email='info@neustadt-glewe.de', gemeinden=['13076012', '13076017', '13076105']),
    'Neustrelitz-Land': dict(kreis='Mecklenburgische Seenplatte', street='Marienstr. 5', plz='17235', city='Neustrelitz',
                  email='info@amtneustrelitz-land.de', gemeinden=['13071011', '13071012', '13071025', '13071042', '13071058', '13071066', '13071075', '13071080', '13071100', '13071147', '13071162']),
    'Neverin': dict(kreis='Mecklenburgische Seenplatte', street='Dorfstr. 36', plz='17039', city='Neverin',
                  email='info@amtneverin.de', gemeinden=['13071009', '13071010', '13071019', '13071104', '13071108', '13071111', '13071140', '13071141', '13071145', '13071161', '13071166', '13071170']),
    'Niepars': dict(kreis='Vorpommern-Rügen', street='Gartenstr. 69b', plz='18442', city='Niepars',
                  email='info@amt-niepars.de', gemeinden=['13073036', '13073041', '13073054', '13073060', '13073061', '13073087', '13073099', '13073104']),
    'Nord-Rügen': dict(kreis='Vorpommern-Rügen', street='Ernst-Thälmann-Str. 37', plz='18551', city='Sagard',
                  email='office@amt-nord-ruegen.de', gemeinden=['13073004', '13073013', '13073019', '13073030', '13073052', '13073071', '13073078', '13073101']),
    'Parchimer Umland': dict(kreis='Ludwigslust-Parchim', street='Walter-Hase-Str. 42', plz='19370', city='Parchim',
                  email='info@amtpu.de', gemeinden=['13076035', '13076056', '13076068', '13076085', '13076164', '13076120', '13076126', '13076129', '13076160', '13076162']),
    'Peenetal/Loitz': dict(kreis='Vorpommern-Greifswald', street='Lange Straße 83', plz='17121', city='Loitz',
                  email='stadtloitz@loitz.de', gemeinden=['13075036', '13075082', '13075123']),
    'Penzliner Land': dict(kreis='Mecklenburgische Seenplatte', street='Warener Chaussee 55a', plz='17217', city='Penzlin',
                  email='buergermeister@penzlin.de', gemeinden=['13071005', '13071173', '13071101', '13071115']),
    'Plau am See': dict(kreis='Ludwigslust-Parchim', street='Markt 2', plz='19395', city='Plau am See',
                  email='info@amtplau.de', gemeinden=['13076006', '13076166', '13076114']),
    'Recknitz-Trebeltal': dict(kreis='Vorpommern-Rügen', street='Karl-Marx-Str. 18', plz='18465', city='Tribsees',
                  email='amt@recknitz-trebeltal.de', gemeinden=['13073007', '13073015', '13073016', '13073020', '13073022', '13073032', '13073033', '13073039', '13073050', '13073093']),
    'Rehna': dict(kreis='Nordwestmecklenburg', street='Freiheitsplatz 1', plz='19217', city='Rehna',
                  email='amt@rehna.de', gemeinden=['13074013', '13074018', '13074028', '13074033', '13074042', '13074065', '13074066', '13074073', '13074078', '13074080', '13074092']),
    'Ribnitz-Damgarten': dict(kreis='Vorpommern-Rügen', street='Am Markt 1', plz='18311', city='Ribnitz-Damgarten',
                  email='stadt@ribnitz-damgarten.de', gemeinden=['13073001', '13073075', '13073082', '13073085']),
    'Rostocker Heide': dict(kreis='Rostock', street='Eichenallee 20a', plz='18182', city='Gelbensande',
                  email='info@amt-rostocker-heide.de', gemeinden=['13072012', '13072015', '13072032', '13072072', '13072088']),
    'Röbel-Müritz': dict(kreis='Mecklenburgische Seenplatte', street='Marktplatz 1', plz='17207', city='Röbel/Müritz',
                  email='post@amt-roebel-mueritz.de', gemeinden=['13071003', '13071013', '13071020', '13071023', '13071175', '13071034', '13071045', '13071053', '13071073', '13071087', '13071088', '13071097', '13071118', '13071122', '13071124', '13071133', '13071137', '13071143', '13071176']),
    'Schwaan': dict(kreis='Rostock', street='Pferdemarkt 2', plz='18258', city='Schwaan',
                  email='stadt-schwaan@mvnet.de', gemeinden=['13072011', '13072018', '13072051', '13072090', '13072095', '13072110', '13072116']),
    'Schönberger Land': dict(kreis='Nordwestmecklenburg', street='Am Markt 15', plz='23923', city='Schönberg',
                  email='info@schoenberger-land.de', gemeinden=['13074017', '13074027', '13074049', '13074052', '13074067', '13074074', '13074076', '13074094']),
    'Seenlandschaft Waren': dict(kreis='Mecklenburgische Seenplatte', street='Warendorfer Str. 4', plz='17192', city='Waren (Müritz)',
                  email='poststelle@amt-slw.de', gemeinden=['13071047', '13071056', '13071063', '13071069', '13071071', '13071077', '13071078', '13071103', '13071172', '13071174', '13071144', '13071154']),
    'Stargarder Land': dict(kreis='Mecklenburgische Seenplatte', street='Mühlenstr. 30', plz='17094', city='Burg Stargard',
                  email='amt@stargarder-land.de', gemeinden=['13071021', '13071026', '13071055', '13071067', '13071090', '13071117']),
    'Stavenhagen': dict(kreis='Mecklenburgische Seenplatte', street='Schloß 1', plz='17153', city='Stavenhagen',
                  email='buergermeister@stavenhagen.de', gemeinden=['13071015', '13071018', '13071048', '13071060', '13071068', '13071070', '13071074', '13071079', '13071102', '13071123', '13071127', '13071142', '13071169']),
    'Sternberger Seenlandschaft': dict(kreis='Ludwigslust-Parchim', street='Am Markt 1', plz='19406', city='Sternberg',
                  email='buergermeister@stadt-sternberg.de', gemeinden=['13076011', '13076015', '13076020', '13076026', '13076062', '13076167', '13076072', '13076078', '13076101', '13076128', '13076148', '13076155']),
    'Stralendorf': dict(kreis='Ludwigslust-Parchim', street='Dorfstr. 30', plz='19073', city='Stralendorf',
                  email='amt@amt-stralendorf.de', gemeinden=['13076036', '13076063', '13076071', '13076107', '13076121', '13076130', '13076147', '13076154', '13076163']),
    'Tessin': dict(kreis='Rostock', street='Alter Markt 1', plz='18195', city='Tessin',
                  email='buergermeister@tessin.de', gemeinden=['13072021', '13072034', '13072037', '13072076', '13072097', '13072102', '13072105', '13072107', '13072118']),
    'Torgelow-Ferdinandshof': dict(kreis='Vorpommern-Greifswald', street='Bahnhofstr. 2', plz='17358', city='Torgelow',
                  email='info@torgelow.de', gemeinden=['13075004', '13075033', '13075045', '13075048', '13075118', '13075131', '13075143']),
    'Treptower Tollensewinkel': dict(kreis='Mecklenburgische Seenplatte', street='Rathausstr. 1', plz='17087', city='Altentreptow',
                  email='info@altentreptow.de', gemeinden=['13071002', '13071004', '13071006', '13071016', '13071022', '13071041', '13071044', '13071049', '13071050', '13071057', '13071059', '13071081', '13071120', '13071125', '13071135', '13071146', '13071158', '13071160', '13071163']),
    'Uecker-Randow-Tal': dict(kreis='Vorpommern-Greifswald', street='Haußmannstr. 85', plz='17309', city='Pasewalk',
                  email='stadt.pasewalk@pasewalk.de', gemeinden=['13075017', '13075032', '13075042', '13075055', '13075063', '13075071', '13075103', '13075104', '13075109', '13075115', '13075126', '13075138', '13075149']),
    'Usedom-Nord': dict(kreis='Vorpommern-Greifswald', street='Möwenstr. 1', plz='17454', city='Zinnowitz',
                  email='info@amtusedomnord.de', gemeinden=['13075058', '13075092', '13075106', '13075133', '13075151']),
    'Usedom-Süd': dict(kreis='Vorpommern-Greifswald', street='Markt 7', plz='17406', city='Usedom',
                  email='info@amtusedom.de', gemeinden=['13074004', '13075026', '13075034', '13075056', '13075065', '13075066', '13075080', '13075090', '13075111', '13075114', '13075129', '13075135', '13075137', '13075148', '13075152']),
    'Warnow-West': dict(kreis='Rostock', street='Schulweg 1a', plz='18198', city='Kritzmow',
                  email='amt@warnow-west.de', gemeinden=['13072030', '13072057', '13072064', '13072077', '13072080', '13072098', '13072121']),
    'West-Rügen': dict(kreis='Vorpommern-Rügen', street='Dorfplatz 2', plz='18573', city='Samtens',
                  email='sekretariat@amt-westruegen.de', gemeinden=['13073003', '13073021', '13073028', '13073040', '13073045', '13073059', '13073073', '13073079', '13073081', '13073092', '13073095']),
    'Wittenburg': dict(kreis='Ludwigslust-Parchim', street='Molkereistr. 4', plz='19243', city='Wittenburg',
                  email='info@stadt-wittenburg.de', gemeinden=['13076152', '13076153']),
    'Woldegk': dict(kreis='Mecklenburgische Seenplatte', street='Karl-Liebknecht-Platz 1', plz='17348', city='Woldegk',
                  email='amt-woldegk@amt-woldegk.de', gemeinden=['13071054', '13071083', '13071105', '13071130', '13071132', '13071153', '13071164']),
    'Zarrentin': dict(kreis='Ludwigslust-Parchim', street='Kirchplatz 8', plz='19246', city='Zarrentin am Schaalsee',
                  email='amt@zarrentin.de', gemeinden=['13076039', '13076073', '13076092', '13076142', '13076159']),
    'Züssow': dict(kreis='Vorpommern-Greifswald', street='Dorfstr. 6', plz='17495', city='Züssow',
                  email='info@amt-zuessow.de', gemeinden=['13075006', '13075040', '13075041', '13075043', '13075044', '13075156', '13075061', '13075094', '13075121', '13075125', '13075145', '13075150', '13075154']),
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
        batch_id = f"erschliessung-mv-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for amt_name, info in AEMTER.items():
            authority_name = f"Amt {amt_name}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Amt (Verwaltungsgemeinschaft nach KV M-V)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Mecklenburg-Vorpommern", phone=None, email=info["email"],
                    source=f"Amtliches Kommunalverzeichnis M-V: {KOMMUNALVERZEICHNIS_URL}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung MV - {amt_name}",
                    request_type_id="ERSCHLIESSUNG", state="Mecklenburg-Vorpommern", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE}", source_url=KV_URL,
                    source_license="Amtliche Rechtsgrundlage (Kommunalverfassung M-V) + amtliches Kommunalverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(AEMTER)} Ämter.")
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
