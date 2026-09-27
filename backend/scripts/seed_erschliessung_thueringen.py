"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
THUERINGEN. 79 Verwaltungseinheiten - 42 "Verwaltungsgemeinschaften"
und 37 "erfuellende Gemeinden" (eine Mitgliedsgemeinde mit mindestens
3000 Einwohnern und hauptamtlichem Buergermeister nimmt die Aufgaben
einer Verwaltungsgemeinschaft wahr) - decken zusammen 491 von 601
Gemeinden ab (82 %).

Rechtsgrundlage: § 47 Abs. 2 Satz 2-3 ThürKO (Thueringer Kommunalordnung)
- "Die Verwaltungsgemeinschaft fuehrt diese Aufgaben ... als Behoerde
der jeweiligen Mitgliedsgemeinde nach deren Weisung aus; ... Der
Verwaltungsgemeinschaft obliegt die verwaltungsmaessige Vorbereitung
und der verwaltungsmaessige Vollzug der Beschluesse der
Mitgliedsgemeinden sowie die Besorgung der laufenden
Verwaltungsangelegenheiten." Erschliessungsbeitraege (§ 127 ff. BauGB
i.V.m. ThürKAG) gehoeren zum eigenen Wirkungskreis der Gemeinde und
werden damit administrativ von der Verwaltungsgemeinschaft als deren
Behoerde bearbeitet. § 51 Abs. 1 Satz 2 ThürKO erstreckt dieselbe
Regelung ausdruecklich auf die "erfuellende Gemeinde" ("gelten die auf
die Verwaltungsgemeinschaft bezogenen Bestimmungen ... entsprechend").
Wortlaut vom Recherche-Agenten per Live-Abruf gegen die amtlichen
Permalinks von landesrecht.thueringen.de zitiert.

Datenquelle: dasselbe amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026), das bereits fuer die
anderen Laender dieser Welle genutzt wurde - keine zusaetzliche
Recherche-Agentenwelle fuer Adressen noetig.

Ausdruecklich NICHT abgedeckt: die uebrigen ca. 110 eigenstaendigen
Gemeinden/Staedte (inkl. kreisfreier Staedte) - diese verwalten sich
selbst und braeuchten Einzelrecherche, was nicht Teil dieser auf die
VG-Hebelwirkung fokussierten Welle ist.

79 neue Authorities, 491 neue MUNICIPALITY-Regeln (eine je
Mitgliedsgemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Thüringen, amtliches Anschriftenverzeichnis)"
THURKO_URL = "https://landesrecht.thueringen.de/perma?j=KomO_TH_!_47"
QUOTE = ("§ 47 Abs. 2 Satz 2-3 ThürKO: 'Die Verwaltungsgemeinschaft führt diese Aufgaben ... "
         "als Behörde der jeweiligen Mitgliedsgemeinde nach deren Weisung aus; ... Der "
         "Verwaltungsgemeinschaft obliegt die verwaltungsmäßige Vorbereitung und der "
         "verwaltungsmäßige Vollzug der Beschlüsse der Mitgliedsgemeinden sowie die Besorgung "
         "der laufenden Verwaltungsangelegenheiten, die für die Mitgliedsgemeinden keine "
         "grundsätzliche Bedeutung haben.' § 51 Abs. 1 Satz 2 ThürKO erstreckt dies auf die "
         "erfüllende Gemeinde.")

# Einheiten-Name -> dict(typ, street, plz, city, email, gemeinden=[AGS, ...])
VG = {
    'EG Am Ettersberg': dict(typ='Erfüllende Gemeinde', street='Hauptstr. 23', plz='99439', city='Am Ettersberg',
                  email='info@am-ettersberg.de', gemeinden=['16071005', '16071017', '16071061', '16071102']),
    'EG An der Schmücke': dict(typ='Erfüllende Gemeinde', street='Am Bahnhof 43', plz='06577', city='An der Schmücke',
                  email='info@anderschmuecke.de', gemeinden=['16065016', '16065052', '16065088']),
    'EG Artern': dict(typ='Erfüllende Gemeinde', street='Brauereistraße 3', plz='06556', city='Artern',
                  email='info@artern.de', gemeinden=['16065008', '16065019', '16065042', '16065046', '16065056', '16065086']),
    'EG Auengrund': dict(typ='Erfüllende Gemeinde', street='Kirchweg 8', plz='98673', city='Crock',
                  email='buergermeister@gv-auengrund.de', gemeinden=['16069006', '16069058']),
    'EG Bad Klosterlausnitz': dict(typ='Erfüllende Gemeinde', street='Markt 3', plz='07639', city='Bad Klosterlausnitz',
                  email='info@bad-klosterlausnitz.de', gemeinden=['16074001', '16074003', '16074005', '16074082', '16074085', '16074086', '16074091', '16074098', '16074105', '16074109']),
    'EG Bad Köstritz': dict(typ='Erfüllende Gemeinde', street='Heinrich-Schütz-Str. 4', plz='07586', city='Bad Köstritz',
                  email='info@stadt-bad-koestritz.de', gemeinden=['16076003', '16076012']),
    'EG Bad Salzungen': dict(typ='Erfüllende Gemeinde', street='Ratsstr. 2', plz='36433', city='Bad Salzungen',
                  email='buero-buergermeister@badsalzungen.de', gemeinden=['16063003', '16063051']),
    'EG Bad Sulza': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='99518', city='Bad Sulza',
                  email='stadtverwaltung@bad-sulza.de', gemeinden=['16071004', '16071015', '16071022', '16071064', '16071069', '16071083']),
    'EG Bleicherode': dict(typ='Erfüllende Gemeinde', street='Hauptstr. 37', plz='99752', city='Bleicherode',
                  email='buergermeister@bleicherode.de', gemeinden=['16062009', '16062024', '16062026', '16062033', '16062037', '16062066']),
    'EG Breitungen/Werra': dict(typ='Erfüllende Gemeinde', street='Rathausstr. 24', plz='98597', city='Breitungen/Werra',
                  email='info@breitungen.de', gemeinden=['16066013', '16066022', '16066059', '16066061']),
    'EG Bürgel': dict(typ='Erfüllende Gemeinde', street='Am Markt 1', plz='07616', city='Bürgel',
                  email='buergermeister@stadt-buergel.de', gemeinden=['16074009', '16074028', '16074061', '16074068']),
    'EG Dermbach': dict(typ='Erfüllende Gemeinde', street='Hinter dem Schloß 1', plz='36466', city='Dermbach',
                  email='info@dermbach.de', gemeinden=['16063015', '16063023', '16063062', '16063084', '16063086']),
    'EG Drei Gleichen': dict(typ='Erfüllende Gemeinde', street='Schulstr. 1', plz='99869', city='Drei Gleichen',
                  email='sekretariat@gemeinde-drei-gleichen.de', gemeinden=['16067059', '16067089']),
    'EG Ebeleben': dict(typ='Erfüllende Gemeinde', street='Rathausstr. 2', plz='99713', city='Ebeleben',
                  email='stadtverwaltung@ebeleben.de', gemeinden=['16065001', '16065005', '16065014', '16065018', '16065038', '16065058']),
    'EG Eisenberg': dict(typ='Erfüllende Gemeinde', street='Markt 27', plz='07607', city='Eisenberg/Thür.',
                  email='kontakt@rathaus-eisenberg.de', gemeinden=['16074018', '16074025', '16074037', '16074055', '16074067', '16074073']),
    'EG Elxleben': dict(typ='Erfüllende Gemeinde', street='Gerhart-Hauptmann-Str. 1', plz='99189', city='Elxleben a. d. Gera',
                  email='info@gemeinde-elxleben.de', gemeinden=['16068009', '16068061']),
    'EG Geisa': dict(typ='Erfüllende Gemeinde', street='Marktplatz 27', plz='36419', city='Geisa',
                  email='info@geisa.de', gemeinden=['16063011', '16063032', '16063033', '16063068']),
    'EG Georgenthal': dict(typ='Erfüllende Gemeinde', street='Tambacher Str. 2', plz='99887', city='Georgenthal',
                  email='sekretariat@georgenthal.de', gemeinden=['16067013', '16067092']),
    'EG Gößnitz': dict(typ='Erfüllende Gemeinde', street='Freiheitsplatz 1', plz='04639', city='Gößnitz',
                  email='hauptamt@goessnitz.de', gemeinden=['16077012', '16077017', '16077039']),
    'EG Herbsleben': dict(typ='Erfüllende Gemeinde', street='Hauptstr. 52', plz='99955', city='Herbsleben',
                  email='sekretariat@gemeinde-herbsleben.de', gemeinden=['16064019', '16064022']),
    'EG Heringen/Helme': dict(typ='Erfüllende Gemeinde', street='Str. der Einheit 100', plz='99765', city='Heringen/Helme',
                  email='info@stadt-heringen.de', gemeinden=['16062008', '16062054', '16062064']),
    'EG Kaulsdorf': dict(typ='Erfüllende Gemeinde', street='Str. des Friedens 27', plz='07338', city='Kaulsdorf',
                  email='info@kaulsdorf-saale.de', gemeinden=['16073002', '16073035', '16073038', '16073107']),
    'EG Königsee': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='07426', city='Königsee',
                  email='stadt@koenigsee.de', gemeinden=['16073001', '16073006', '16073112']),
    'EG Langenwetzendorf': dict(typ='Erfüllende Gemeinde', street='Am Daßlitzer Kreuz 4', plz='07957', city='Langenwetzendorf',
                  email='info@langenwetzendorf.de', gemeinden=['16076029', '16076039']),
    'EG Meiningen': dict(typ='Erfüllende Gemeinde', street='Schlossplatz 1', plz='98617', city='Meiningen',
                  email='buergerbuero@meiningen.de', gemeinden=['16066042', '16066056', '16066076']),
    'EG Nessetal': dict(typ='Erfüllende Gemeinde', street='Hauptstr. 15', plz='99869', city='Nessetal',
                  email='info@gemeinde-nessetal.de', gemeinden=['16067063', '16067091']),
    'EG Neuhaus am Rennweg': dict(typ='Erfüllende Gemeinde', street='Kirchweg 2', plz='98724', city='Neuhaus am Rennweg',
                  email='rathaus@neuhaus-am-rennweg.de', gemeinden=['16072006', '16072013']),
    'EG Neustadt an der Orla': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='07806', city='Neustadt an der Orla',
                  email='info@neustadtanderorla.de', gemeinden=['16075051', '16075073']),
    'EG Nobitz': dict(typ='Erfüllende Gemeinde', street='Bachstr. 1', plz='04603', city='Nobitz',
                  email='post@nobitz.de', gemeinden=['16077011', '16077023', '16077036']),
    'EG Nottertal-Heilinger Höhen': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='99994', city='Nottertal-Heilinger Höhen',
                  email='post@stadt-nhh.de', gemeinden=['16064037', '16064043', '16064077']),
    'EG Ohrdruf': dict(typ='Erfüllende Gemeinde', street='Marktplatz 1', plz='99885', city='Ohrdruf',
                  email='poststelle@ohrdruf.de', gemeinden=['16067044', '16067053']),
    'EG Ruhla': dict(typ='Erfüllende Gemeinde', street='Carl-Gareis-Str. 16', plz='99842', city='Ruhla',
                  email='info@ruhla.de', gemeinden=['16063066', '16063071']),
    'EG Stadtroda': dict(typ='Erfüllende Gemeinde', street='Str. des Friedens 17', plz='07646', city='Stadtroda',
                  email='alleamtsleiter@stadtroda.de', gemeinden=['16074058', '16074081', '16074094']),
    'EG Vogtei': dict(typ='Erfüllende Gemeinde', street='Hanfsack 3', plz='99986', city='Vogtei',
                  email='info@gemeinde-vogtei.de', gemeinden=['16064032', '16064053', '16064075']),
    'EG Weida': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='07570', city='Weida',
                  email='info@weida.de', gemeinden=['16076014', '16076079']),
    'EG Zeulenroda-Triebes': dict(typ='Erfüllende Gemeinde', street='Markt 1', plz='07937', city='Zeulenroda-Triebes',
                  email='www.zeulenroda-triebes.de', gemeinden=['16076041', '16076081', '16076087']),
    'Uder': dict(typ='Erfüllende Gemeinde', street='Siedlung 14', plz='37318', city='Uder',
                  email='info@lg-uder.de', gemeinden=['16061002', '16061024', '16061119']),
    'VG Am Brahmetal': dict(typ='Verwaltungsgemeinschaft', street='Dorfstr. 17', plz='07580', city='Großenstein',
                  email='vg.brahmetal@t-online.de', gemeinden=['16076006', '16076008', '16076023', '16076028', '16076036', '16076058', '16076059', '16076067']),
    'VG Bad Tennstedt': dict(typ='Verwaltungsgemeinschaft', street='Markt 1', plz='99955', city='Bad Tennstedt',
                  email='post@vg.badtennstedt.de', gemeinden=['16064004', '16064005', '16064007', '16064009', '16064021', '16064027', '16064033', '16064038', '16064045', '16064061', '16064062', '16064064']),
    'VG Dolmar-Salzbrücke': dict(typ='Verwaltungsgemeinschaft', street='Zella-Meininger-Str. 6', plz='98547', city='Schwarza',
                  email='info@vg-ds.de', gemeinden=['16066005', '16066015', '16066016', '16066017', '16066018', '16066038', '16066039', '16066045', '16066049', '16066057', '16066058', '16066065', '16066079', '16066081']),
    'VG Dornburg-Camburg': dict(typ='Verwaltungsgemeinschaft', street='Rathausstr. 1', plz='07774', city='Dornburg-Camburg',
                  email='info@vg-dornburg-camburg.de', gemeinden=['16074011', '16074019', '16074026', '16074032', '16074036', '16074043', '16074051', '16074054', '16074063', '16074096', '16074099', '16074112', '16074113']),
    'VG Eichsfeld-Wipperaue': dict(typ='Verwaltungsgemeinschaft', street='Weststr. 2', plz='37339', city='Breitenworbis',
                  email='poststelle@eichsfeld-wipperaue.de', gemeinden=['16061017', '16061019', '16061037', '16061044', '16061058']),
    'VG Ershausen/Geismar': dict(typ='Verwaltungsgemeinschaft', street='Kreisstr. 4', plz='37308', city='Schimberg',
                  email='poststelle@ershausen-geismar.de', gemeinden=['16061023', '16061035', '16061056', '16061062', '16061075', '16061085', '16061086', '16061098', '16061105', '16061113']),
    'VG Fahner Höhe': dict(typ='Verwaltungsgemeinschaft', street='Markt 7', plz='99958', city='Tonna',
                  email='info@vg-fahner-hoehe.de', gemeinden=['16067009', '16067011', '16067026', '16067033', '16067067']),
    'VG Feldstein': dict(typ='Verwaltungsgemeinschaft', street='Markt 1', plz='98660', city='Themar',
                  email='info@vg-feldstein.de', gemeinden=['16069001', '16069003', '16069004', '16069008', '16069009', '16069011', '16069016', '16069017', '16069021', '16069025', '16069026', '16069028', '16069035', '16069037', '16069044', '16069047', '16069051']),
    'VG Gera-Aue': dict(typ='Verwaltungsgemeinschaft', street='Marktplatz 13', plz='99189', city='Gebesee',
                  email='info@vg-gera-aue.de', gemeinden=['16068002', '16068014', '16068045', '16068057']),
    'VG Geratal': dict(typ='Verwaltungsgemeinschaft', street='Zum Bahnhof 59 a', plz='99331', city='Geratal',
                  email='vg@geratal.de', gemeinden=['16070011', '16070034', '16070043']),
    'VG Gramme-Vippach': dict(typ='Verwaltungsgemeinschaft', street='Erfurter Str. 6', plz='99195', city='Schloßvippach',
                  email='poststelle@gramme-vippach.de', gemeinden=['16068001', '16068007', '16068017', '16068021', '16068032', '16068036', '16068037', '16068039', '16068048', '16068052', '16068055', '16068056']),
    'VG Greußen': dict(typ='Verwaltungsgemeinschaft', street='Bahnhofstr. 13 a', plz='99718', city='Greußen',
                  email='poststelle@vgem-greussen.de', gemeinden=['16065012', '16065048', '16065051', '16065074', '16065075', '16065077', '16065079']),
    'VG Hainich-Werratal': dict(typ='Verwaltungsgemeinschaft', street='Michael-Praetorius-Platz 2', plz='99831', city='Amt Creuzburg',
                  email='info@vg-hainich-werratal.de', gemeinden=['16063006', '16063008', '16063046', '16063049', '16063058', '16063104']),
    'VG Hanstein-Rusteberg': dict(typ='Verwaltungsgemeinschaft', street='Steingraben 49', plz='37318', city='Hohengandern',
                  email='info@vghr.de', gemeinden=['16061001', '16061014', '16061021', '16061032', '16061033', '16061036', '16061048', '16061057', '16061066', '16061069', '16061078', '16061082', '16061083', '16061102']),
    'VG Heideland-Elstertal-Schkölen': dict(typ='Verwaltungsgemeinschaft', street='Flemmingstr. 17', plz='07613', city='Crossen',
                  email='info@vg-hes.de', gemeinden=['16074012', '16074038', '16074039', '16074072', '16074092', '16074106', '16074116']),
    'VG Heldburger Unterland': dict(typ='Verwaltungsgemeinschaft', street='Häfenmarkt 164', plz='98663', city='Heldburg',
                  email='post@vg-heldburgerunterland.de', gemeinden=['16069041', '16069046', '16069049', '16069052', '16069056', '16069063']),
    'VG Hermsdorf': dict(typ='Verwaltungsgemeinschaft', street='Am Alten Versuchsfeld 1', plz='07629', city='Hermsdorf/Thür.',
                  email='info@vg-hermsdorf.de', gemeinden=['16074041', '16074059', '16074075', '16074084', '16074093']),
    'VG Hohe Rhön': dict(typ='Verwaltungsgemeinschaft', street='Hauptstr. 18', plz='36452', city='Kaltennordheim',
                  email='zentrale@vghoherhoen.de', gemeinden=['16066012', '16066019', '16066024', '16066052', '16066095']),
    'VG Hügelland/Täler': dict(typ='Verwaltungsgemeinschaft', street='Pfarrwinkel 10', plz='07646', city='Tröbnitz',
                  email='verwaltung@huegelland-taeler.de', gemeinden=['16074007', '16074017', '16074022', '16074024', '16074029', '16074045', '16074046', '16074047', '16074053', '16074056', '16074064', '16074066', '16074071', '16074074', '16074077', '16074097', '16074101', '16074102', '16074103', '16074107', '16074108']),
    'VG Kindelbrück': dict(typ='Verwaltungsgemeinschaft', street='Puschkinplatz 1', plz='99638', city='Kindelbrück',
                  email='poststelle@vg-kindelbrueck.de', gemeinden=['16068005', '16068015', '16068022', '16068064']),
    'VG Kranichfeld': dict(typ='Verwaltungsgemeinschaft', street='Alexanderstr. 7', plz='99448', city='Kranichfeld',
                  email='info@vg-kranichfeld.de', gemeinden=['16071032', '16071043', '16071046', '16071059', '16071079', '16071087']),
    'VG Kölleda': dict(typ='Verwaltungsgemeinschaft', street='Markt 24', plz='99625', city='Kölleda',
                  email='poststelle@vgem-koelleda.de', gemeinden=['16068019', '16068033', '16068041', '16068042']),
    'VG Leinetal': dict(typ='Verwaltungsgemeinschaft', street='Hauptstr. 73', plz='37308', city='Bodenrode-Westhausen',
                  email='poststelle@vg-leinetal.de', gemeinden=['16061012', '16061034', '16061047', '16061076', '16061089', '16061107']),
    'VG Lindenberg/Eichsfeld': dict(typ='Verwaltungsgemeinschaft', street='Hauptstr. 17', plz='37339', city='Teistungen',
                  email='info@lindenberg-eichsfeld.de', gemeinden=['16061003', '16061015', '16061026', '16061031', '16061094', '16061103', '16061114']),
    'VG Ländereck': dict(typ='Verwaltungsgemeinschaft', street='Ronneburger Str. 68 A', plz='07580', city='Seelingstädt',
                  email='vorsitzende@vg-laendereck.de', gemeinden=['16076009', '16076017', '16076019', '16076027', '16076034', '16076043', '16076055', '16076062', '16076069', '16076074']),
    'VG Mellingen': dict(typ='Verwaltungsgemeinschaft', street='Karl-Alexander-Str. 134 a', plz='99441', city='Mellingen',
                  email='info@vgem-mellingen.de', gemeinden=['16071009', '16071013', '16071019', '16071025', '16071027', '16071031', '16071037', '16071049', '16071053', '16071056', '16071071', '16071089', '16071093', '16071095']),
    'VG Münchenbernsdorf': dict(typ='Verwaltungsgemeinschaft', street='Karl-Marx-Platz 13', plz='07589', city='Münchenbernsdorf',
                  email='info@rathaus-muenchenbernsdorf.de', gemeinden=['16076007', '16076033', '16076042', '16076044', '16076049', '16076064', '16076068', '16076086']),
    'VG Nesseaue': dict(typ='Verwaltungsgemeinschaft', street='Dr.-Külz-Str. 4', plz='99869', city='Friemar',
                  email='info@vg-nesseaue.de', gemeinden=['16067004', '16067016', '16067022', '16067047', '16067052', '16067055', '16067068', '16067071', '16067082']),
    'VG Oberes Sprottental': dict(typ='Verwaltungsgemeinschaft', street='Burgberg 5', plz='04626', city='Posterstein',
                  email='info@vg-sprottental.de', gemeinden=['16077016', '16077018', '16077026', '16077041', '16077047', '16077049']),
    'VG Oppurg': dict(typ='Verwaltungsgemeinschaft', street='Am Türkenhof 5', plz='07381', city='Oppurg',
                  email='info@vg-oppurg.de', gemeinden=['16075006', '16075016', '16075031', '16075039', '16075054', '16075056', '16075074', '16075075', '16075077', '16075087', '16075105', '16075121', '16075124']),
    'VG Pleißenaue': dict(typ='Verwaltungsgemeinschaft', street='Breite Str. 2', plz='04617', city='Treben',
                  email='info@vg-pleissenaue.de', gemeinden=['16077005', '16077007', '16077015', '16077048', '16077052']),
    'VG Ranis-Ziegenrück': dict(typ='Verwaltungsgemeinschaft', street='Pößnecker Str. 2', plz='07389', city='Ranis',
                  email='info@vg-ranis-ziegenrueck.de', gemeinden=['16075023', '16075035', '16075047', '16075069', '16075079', '16075081', '16075088', '16075101', '16075102', '16075103', '16075125', '16075127', '16075129']),
    'VG Riechheimer Berg': dict(typ='Verwaltungsgemeinschaft', street='Am Flugplatz 10', plz='99310', city='Osthausen-Wülfershausen',
                  email='info@vg-riechheimer-berg.de', gemeinden=['16070001', '16070006', '16070008', '16070012', '16070013', '16070041', '16070054']),
    'VG Rositz': dict(typ='Verwaltungsgemeinschaft', street='Altenburger Str. 48 b', plz='04617', city='Rositz',
                  email='sekretariat@vg-rositz.de', gemeinden=['16077008', '16077009', '16077022', '16077027', '16077031', '16077034', '16077042', '16077044']),
    'VG Schiefergebirge': dict(typ='Verwaltungsgemeinschaft', street='Markt 8', plz='07330', city='Probstzella',
                  email='info@vg-schiefergebirge.de', gemeinden=['16073028', '16073046', '16073067']),
    'VG Schwarzatal': dict(typ='Verwaltungsgemeinschaft', street='Markt 5', plz='98744', city='Schwarzatal',
                  email='poststelle@vg-schwarzatal.de', gemeinden=['16073013', '16073014', '16073017', '16073037', '16073055', '16073074', '16073082', '16073084', '16073094', '16073113']),
    'VG Seenplatte': dict(typ='Verwaltungsgemeinschaft', street='Schleizer Str. 17', plz='07907', city='Oettersdorf',
                  email='info@vg-seenplatte.de', gemeinden=['16075014', '16075033', '16075034', '16075048', '16075063', '16075068', '16075072', '16075076', '16075083', '16075084', '16075109', '16075119']),
    'VG Straußfurt': dict(typ='Verwaltungsgemeinschaft', street='Bahnhofstr. 13', plz='99634', city='Straußfurt',
                  email='post@vgstraussfurt.de', gemeinden=['16068013', '16068025', '16068044', '16068049', '16068053', '16068059', '16068062']),
    'VG Südliches Saaletal': dict(typ='Verwaltungsgemeinschaft', street='Bahnhofstr. 23', plz='07768', city='Kahla/Thür.',
                  email='vorsitzender@vg-suedliches-saaletal.de', gemeinden=['16074002', '16074004', '16074008', '16074016', '16074021', '16074031', '16074033', '16074034', '16074042', '16074048', '16074049', '16074052', '16074057', '16074065', '16074076', '16074079', '16074087', '16074089', '16074095', '16074104', '16074114']),
    'VG Triptis': dict(typ='Verwaltungsgemeinschaft', street='Markt 1', plz='07819', city='Triptis',
                  email='info@triptis.de', gemeinden=['16075019', '16075029', '16075057', '16075065', '16075066', '16075093', '16075099', '16075114', '16075116']),
    'VG Wasungen-Amt Sand': dict(typ='Verwaltungsgemeinschaft', street='Markt 9 - 11', plz='98634', city='Wasungen',
                  email='info@vg-wasungen.de', gemeinden=['16066025', '16066041', '16066064', '16066086']),
    'VG Westerwald-Obereichsfeld': dict(typ='Verwaltungsgemeinschaft', street='Neue Str. 16', plz='37359', city='Küllstedt',
                  email='info@westerwald-obereichsfeld.de', gemeinden=['16061018', '16061027', '16061041', '16061063', '16061101']),
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
        batch_id = f"erschliessung-th-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for name, info in VG.items():
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type=f"{info['typ']} (ThürKO)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Thüringen", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung TH - {name}",
                    request_type_id="ERSCHLIESSUNG", state="Thüringen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{name} - {QUOTE}", source_url=THURKO_URL,
                    source_license="Amtliche Rechtsgrundlage (ThürKO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(VG)} VG.")
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
