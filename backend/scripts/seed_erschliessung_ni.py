"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
NIEDERSACHSEN. Analog zu Mecklenburg-Vorpommern und Schleswig-Holstein
loest sich das Kernproblem dieser Auskunftsart ueber die 114
"Samtgemeinden" (Verwaltungsgemeinschaften mehrerer Mitgliedsgemeinden).
Nach § 98 Abs. 5 Satz 1 NKomVG (Niedersaechsisches Kommunalverfassungs-
gesetz) "fuehren [die Samtgemeinden] die Kassengeschaefte der
Mitgliedsgemeinden und veranlagen und erheben fuer diese die
Gemeindeabgaben" - Erschliessungsbeitraege sind Gemeindeabgaben in
diesem Sinne (kommunale Geldleistungspflicht der Mitgliedsgemeinde
gegenueber Anliegern; § 1 Abs. 2 NKAG bestaetigt, dass auch auf anderer
gesetzlicher Grundlage wie dem BauGB erhobene Beitraege erfasst werden,
soweit das Spezialgesetz keine eigene innerkommunale Zustaendigkeits-
regelung trifft - das BauGB regelt nur die materielle Beitragspflicht,
nicht die Verwaltungskompetenz zwischen Samtgemeinde und Mitglieds-
gemeinde). Zitat unabhaengig ueber zwei Quellen bestaetigt (NI-VORIS
sowie eine Fachkommentierung).

Datenquelle: das amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026) - dieselbe Datei, die in
dieser Sitzung bereits fuer die Kreis-Adressen bei BODENDENKMALSCHUTZ
und KATASTER genutzt wurde (`app/services/address_directory.py`,
SATZART_VERBANDSGEMEINDE=50 fuer die Samtgemeinde-Ebene selbst).
Dadurch war - anders als bei Schleswig-Holstein - KEINE zusaetzliche
Recherche-Agentenwelle fuer Adressen noetig: alle 114 Samtgemeinden
sind darin mit vollstaendiger Anschrift (Strasse, PLZ, Ort, E-Mail)
UND alle 650 zugehoerigen Mitgliedsgemeinden mit amtlichem
Gemeindeschluessel (AGS) erfasst (Zuordnung ueber den Amtlichen
Regionalschluessel-Praefix, da eine Mitgliedsgemeinde denselben
9-stelligen Land/RB/Kreis/Samtgemeinde-Praefix wie ihre Samtgemeinde
teilt).

Ausdruecklich NICHT abgedeckt: die uebrigen ca. 291 Einheitsgemeinden
und kreisfreien Staedte (inkl. Region Hannover als Sonderfall) - diese
verwalten sich selbst und braeuchten Einzelrecherche wie eine normale
Grossstadt, was nicht Teil dieser auf die Samtgemeinden-Hebelwirkung
fokussierten Welle ist.

114 neue Authorities (eine je Samtgemeinde), 650 neue MUNICIPALITY-
Regeln (eine je Mitgliedsgemeinde, ags = die jeweilige Gemeinde-AGS).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, Erschliessungsbeitraege Niedersachsen, amtliches Anschriftenverzeichnis)"
NKOMVG_URL = "https://voris.wolterskluwer-online.de/browse/document/2d981e3d-ddcf-3a20-b0e2-26c5cad7bd21"
QUOTE = ("§ 98 Abs. 5 Satz 1 NKomVG: 'Die Samtgemeinden führen die Kassengeschäfte der "
         "Mitgliedsgemeinden und veranlagen und erheben für diese die Gemeindeabgaben und "
         "die privatrechtlichen Entgelte.'")

# Samtgemeinde-Name -> dict(street, plz, city, email, gemeinden=[AGS, ...])
SAMTGEMEINDEN = {
    'Samtgemeinde Ahlden': dict(street='Bahnhofstraße 30', plz='29693', city='Hodenhagen',
                  email='samtgemeinde@ahlden.eu', gemeinden=['03358001', '03358006', '03358011', '03358012', '03358014']),
    'Samtgemeinde Altes Amt Lemförde': dict(street='Hauptstr. 80', plz='49448', city='Lemförde',
                  email='rathaus@lemfoerde.de', gemeinden=['03251009', '03251020', '03251022', '03251023', '03251025', '03251029', '03251036']),
    'Samtgemeinde Amelinghausen': dict(street='Lüneburger Straße 50', plz='21385', city='Amelinghausen',
                  email='rathaus@samtgemeinde-amelinghausen.de', gemeinden=['03355002', '03355008', '03355027', '03355029', '03355034']),
    'Samtgemeinde Apensen': dict(street='Buxtehuder Straße 27', plz='21641', city='Apensen',
                  email='samtgemeinde@apensen.de', gemeinden=['03359003', '03359006', '03359037']),
    'Samtgemeinde Artland': dict(street='Markt 1', plz='49610', city='Quakenbrück',
                  email='info@artland.de', gemeinden=['03459007', '03459025', '03459028', '03459030']),
    'Samtgemeinde Aue': dict(street='Langdoren 4', plz='29559', city='Wrestedt',
                  email='info@sg-aue.de', gemeinden=['03360005', '03360013', '03360020', '03360030']),
    'Samtgemeinde Baddeckenstedt': dict(street='Heerer Straße 28', plz='38271', city='Baddeckenstedt',
                  email='info@baddeckenstedt.de', gemeinden=['03158002', '03158004', '03158011', '03158016', '03158018', '03158028']),
    'Samtgemeinde Bardowick': dict(street='Schulstraße 12', plz='21357', city='Bardowick',
                  email='info@bardowick.de', gemeinden=['03355004', '03355007', '03355017', '03355023', '03355028', '03355039', '03355042']),
    'Samtgemeinde Barnstorf': dict(street='Am Markt 4', plz='49406', city='Barnstorf',
                  email='rathaus@barnstorf.de', gemeinden=['03251005', '03251013', '03251014', '03251017']),
    'Samtgemeinde Bersenbrück': dict(street='Lindenstraße 2', plz='49593', city='Bersenbrück',
                  email='info@bersenbrueck.de', gemeinden=['03459001', '03459002', '03459010', '03459016', '03459018', '03459023', '03459031']),
    'Samtgemeinde Bevensen-Ebstorf': dict(street='Lindenstraße 12', plz='29549', city='Bad Bevensen',
                  email='info@bevensen-ebstorf.de', gemeinden=['03360001', '03360002', '03360003', '03360006', '03360008', '03360010', '03360011', '03360012', '03360014', '03360017', '03360019', '03360026', '03360029']),
    'Samtgemeinde Bevern': dict(street='Angerstraße 13 a', plz='37639', city='Bevern',
                  email='samtgemeinde@bevern.de', gemeinden=['03255002', '03255015', '03255021', '03255030']),
    'Samtgemeinde Bodenwerder-Polle': dict(street='Münchhausenplatz 1', plz='37619', city='Bodenwerder',
                  email='info@bodenwerder-polle.de', gemeinden=['03255003', '03255005', '03255016', '03255017', '03255019', '03255020', '03255025', '03255031', '03255032', '03255033', '03255035']),
    'Samtgemeinde Boffzen': dict(street='Heinrich-Ohm-Straße 21', plz='37691', city='Boffzen',
                  email='samtgemeinde@boffzen.de', gemeinden=['03255004', '03255009', '03255014', '03255026']),
    'Samtgemeinde Boldecker Land': dict(street='Eichenweg 1', plz='38554', city='Weyhausen',
                  email='post@boldecker-land.de', gemeinden=['03151002', '03151004', '03151014', '03151020', '03151030', '03151039']),
    'Samtgemeinde Bothel': dict(street='Horstweg 17', plz='27386', city='Bothel',
                  email='samtgemeinde@bothel.de', gemeinden=['03357006', '03357009', '03357024', '03357025', '03357031', '03357054']),
    'Samtgemeinde Brome': dict(street='Bahnhofstraße 36', plz='38465', city='Brome',
                  email='rathaus@samtgemeinde-brome.de', gemeinden=['03151003', '03151005', '03151008', '03151021', '03151024', '03151031', '03151032']),
    'Samtgemeinde Brookmerland': dict(street='Am Markt 10', plz='26529', city='Marienhafe',
                  email='rathaus@marienhafe.de', gemeinden=['03452015', '03452017', '03452021', '03452022', '03452024', '03452026']),
    'Samtgemeinde Bruchhausen-Vilsen': dict(street='Lange Straße 11', plz='27305', city='Bruchhausen-Vilsen',
                  email='info@bruchhausen-vilsen.de', gemeinden=['03251002', '03251026', '03251033', '03251049']),
    'Samtgemeinde Börde Lamstedt': dict(street='Schützenstraße 20', plz='21769', city='Lamstedt',
                  email='rathaus@boerde-lamstedt.de', gemeinden=['03352002', '03352024', '03352029', '03352036', '03352052']),
    'Samtgemeinde Dahlenburg': dict(street='Am Markt 17', plz='21368', city='Dahlenburg',
                  email='samtgemeinde@dahlenburg.de', gemeinden=['03355010', '03355012', '03355013', '03355025', '03355037']),
    'Samtgemeinde Dransfeld': dict(street='Kirchplatz 1', plz='37127', city='Dransfeld',
                  email='rathaus@dransfeld.de', gemeinden=['03159008', '03159009', '03159021', '03159024', '03159031']),
    'Samtgemeinde Dörpen': dict(street='Hauptstraße 25', plz='26892', city='Dörpen',
                  email='samtgemeinde@doerpen.de', gemeinden=['03454007', '03454008', '03454020', '03454025', '03454030', '03454037', '03454038', '03454056', '03454060']),
    'Samtgemeinde Eilsen': dict(street='Bückeburger Straße 4', plz='31707', city='Bad Eilsen',
                  email='info@sg-eilsen.de', gemeinden=['03257001', '03257005', '03257008', '03257012', '03257022']),
    'Samtgemeinde Elbmarsch': dict(street='Elbuferstraße 98', plz='21436', city='Marschacht',
                  email='poststelle@sg-elbmarsch.de', gemeinden=['03353007', '03353023', '03353033']),
    'Samtgemeinde Elbtalaue': dict(street='Rosmarienstraße 3', plz='29451', city='Dannenberg (Elbe)',
                  email='info@elbtalaue.de', gemeinden=['03354003', '03354004', '03354006', '03354008', '03354009', '03354011', '03354012', '03354014', '03354019', '03354027']),
    'Samtgemeinde Elm-Asse': dict(street='Markt 3', plz='38170', city='Schöppenstedt',
                  email='rathaus@elm-asse.de', gemeinden=['03158007', '03158008', '03158017', '03158021', '03158022', '03158025', '03158027', '03158031', '03158032', '03158035', '03158036', '03158040']),
    'Samtgemeinde Emlichheim': dict(street='Hauptstraße 24', plz='49824', city='Emlichheim',
                  email='info@emlichheim.de', gemeinden=['03456002', '03456009', '03456012', '03456019']),
    'Samtgemeinde Eschershausen-Stadtoldendorf': dict(street='Kirchstraße 4', plz='37627', city='Stadtoldendorf',
                  email='info@eschershausen-stadtoldendorf.de', gemeinden=['03255001', '03255007', '03255010', '03255012', '03255013', '03255018', '03255022', '03255027', '03255028', '03255034', '03255036']),
    'Samtgemeinde Esens': dict(street='Am Markt 2', plz='26427', city='Esens',
                  email='rathaus@esens.de', gemeinden=['03462002', '03462003', '03462006', '03462008', '03462010', '03462015', '03462017']),
    'Samtgemeinde Fintel': dict(street='Berliner Straße 3', plz='27389', city='Lauenbrück',
                  email='kontakt@sgfintel.de', gemeinden=['03357015', '03357023', '03357033', '03357046', '03357049']),
    'Samtgemeinde Flotwedel': dict(street='Am Alten Bahnhof 3', plz='29342', city='Wienhausen',
                  email='info@flotwedel.de', gemeinden=['03351005', '03351007', '03351017', '03351022']),
    'Samtgemeinde Fredenbeck': dict(street='Schwingestraße 1', plz='21717', city='Fredenbeck',
                  email='info@fredenbeck.de', gemeinden=['03359011', '03359017', '03359031']),
    'Samtgemeinde Freren': dict(street='Markt 1', plz='49832', city='Freren',
                  email='ritz@freren.de', gemeinden=['03454001', '03454003', '03454012', '03454036', '03454053']),
    'Samtgemeinde Fürstenau': dict(street='Schloßplatz 1', plz='49584', city='Fürstenau',
                  email='info@fuerstenau.de', gemeinden=['03459009', '03459011', '03459017']),
    'Samtgemeinde Gartow': dict(street='Springstraße 14', plz='29471', city='Gartow',
                  email='samtgemeinde@gartow.de', gemeinden=['03354005', '03354007', '03354010', '03354020', '03354021']),
    'Samtgemeinde Geestequelle': dict(street='Bohlenstraße 10', plz='27432', city='Oerel',
                  email='samtgemeinde@geestequelle.de', gemeinden=['03357002', '03357004', '03357012', '03357027', '03357035']),
    'Samtgemeinde Gellersen': dict(street='Dachtmisser Straße 1', plz='21391', city='Reppenstedt',
                  email='rathaus@gellersen.de', gemeinden=['03355020', '03355031', '03355035', '03355041']),
    'Samtgemeinde Gieboldehausen': dict(street='Hahlestraße 1', plz='37434', city='Gieboldehausen',
                  email='rathaus@sg-gieboldehausen.de', gemeinden=['03159005', '03159006', '03159014', '03159022', '03159025', '03159027', '03159028', '03159030', '03159037', '03159038']),
    'Samtgemeinde Grafschaft Hoya': dict(street='Schloßplatz 2', plz='27318', city='Hoya (Weser)',
                  email='rathaus@hoya-weser.de', gemeinden=['03256003', '03256007', '03256008', '03256009', '03256010', '03256013', '03256014', '03256015', '03256028', '03256035']),
    'Samtgemeinde Grasleben': dict(street='Bahnhofstraße 4', plz='38368', city='Grasleben',
                  email='grasleben@grasleben.de', gemeinden=['03154008', '03154015', '03154016', '03154018']),
    'Samtgemeinde Hage': dict(street='Hauptstraße 81', plz='26524', city='Hage',
                  email='rathaus@sg-hage.de', gemeinden=['03452003', '03452008', '03452009', '03452010', '03452016']),
    'Samtgemeinde Hambergen': dict(street='Bremer Straße 2', plz='27729', city='Hambergen',
                  email='rathaus@hambergen.de', gemeinden=['03356001', '03356003', '03356004', '03356006', '03356010']),
    'Samtgemeinde Hankensbüttel': dict(street='Goethestraße 2', plz='29386', city='Hankensbüttel',
                  email='info@sg-hankensbuettel.de', gemeinden=['03151007', '03151011', '03151019', '03151028', '03151029']),
    'Samtgemeinde Hanstedt': dict(street='Rathausstraße 1', plz='21271', city='Hanstedt',
                  email='samtgemeinde@hanstedt.de', gemeinden=['03353002', '03353004', '03353009', '03353016', '03353024', '03353036']),
    'Samtgemeinde Harpstedt': dict(street='Amtsfreiheit 1', plz='27243', city='Harpstedt',
                  email='Samtgemeinde@Harpstedt.de', gemeinden=['03458001', '03458002', '03458004', '03458006', '03458008', '03458011', '03458012', '03458015']),
    'Samtgemeinde Harsefeld': dict(street='Herrenstraße 25', plz='21698', city='Harsefeld',
                  email='samtgemeinde@harsefeld.de', gemeinden=['03359002', '03359005', '03359008', '03359023']),
    'Samtgemeinde Hattorf am Harz': dict(street='Otto-Escher-Straße 12', plz='37197', city='Hattorf am Harz',
                  email='samtgemeinde@hattorf-am-harz.de', gemeinden=['03159012', '03159018', '03159020', '03159039']),
    'Samtgemeinde Heemsen': dict(street='Wilhelmstraße 4', plz='31627', city='Rohrsen',
                  email='info@heemsen.de', gemeinden=['03256005', '03256011', '03256012', '03256027']),
    'Samtgemeinde Heeseberg': dict(street='Helmstedter Straße 17', plz='38381', city='Jerxheim',
                  email='samtgemeinde@heeseberg.de', gemeinden=['03154002', '03154006', '03154012', '03154027']),
    'Samtgemeinde Hemmoor': dict(street='Rathausplatz 5', plz='21745', city='Hemmoor',
                  email='stadt@hemmoor.de', gemeinden=['03352020', '03352022', '03352044']),
    'Samtgemeinde Herzlake': dict(street='Neuer Markt 4', plz='49770', city='Herzlake',
                  email='samtgemeinde@herzlake.de', gemeinden=['03454009', '03454021', '03454026']),
    'Samtgemeinde Hesel': dict(street='Rathausstraße 14', plz='26835', city='Hesel',
                  email='info@hesel.de', gemeinden=['03457003', '03457009', '03457010', '03457011', '03457015', '03457019']),
    'Samtgemeinde Hollenstedt': dict(street='Hauptstraße 15', plz='21279', city='Hollenstedt',
                  email='samtgemeinde@hollenstedt.de', gemeinden=['03353001', '03353008', '03353014', '03353019', '03353025', '03353028', '03353039']),
    'Samtgemeinde Holtriem': dict(street='Auricher Straße 9', plz='26556', city='Westerholt',
                  email='info@holtriem.de', gemeinden=['03462001', '03462004', '03462009', '03462011', '03462012', '03462013', '03462016', '03462018']),
    'Samtgemeinde Horneburg': dict(street='Lange Straße 47 - 49', plz='21640', city='Horneburg',
                  email='info@horneburg.de', gemeinden=['03359001', '03359007', '03359012', '03359027', '03359034']),
    'Samtgemeinde Ilmenau': dict(street='Am Diemel 2', plz='21406', city='Melbeck',
                  email='info@samtgemeinde-ilmenau.de', gemeinden=['03355006', '03355014', '03355016', '03355024']),
    'Samtgemeinde Isenbüttel': dict(street='Gutsstraße 11', plz='38550', city='Isenbüttel',
                  email='info@isenbuettel.de', gemeinden=['03151006', '03151013', '03151022', '03151037']),
    'Samtgemeinde Jesteburg': dict(street='Niedersachsenplatz 5', plz='21266', city='Jesteburg',
                  email='rathaus-jesteburg@lkharburg.de', gemeinden=['03353003', '03353017', '03353020']),
    'Samtgemeinde Jümme': dict(street='Rathausring 8 - 12', plz='26849', city='Filsum',
                  email='gemeinde@juemme.de', gemeinden=['03457006', '03457008', '03457016']),
    'Samtgemeinde Kirchdorf': dict(street='Rathausstraße 12', plz='27245', city='Kirchdorf',
                  email='info@kirchdorf.de', gemeinden=['03251003', '03251004', '03251018', '03251021', '03251043', '03251045']),
    'Samtgemeinde Lachendorf': dict(street='Oppershäuser Straße 1', plz='29331', city='Lachendorf',
                  email='Poststelle@lachendorf.de', gemeinden=['03351002', '03351003', '03351008', '03351015', '03351016']),
    'Samtgemeinde Land Hadeln': dict(street='Marktstraße 21', plz='21762', city='Otterndorf',
                  email='zentrale@land.hadeln.de', gemeinden=['03352004', '03352008', '03352025', '03352038', '03352039', '03352041', '03352042', '03352043', '03352045', '03352046', '03352051', '03352055', '03352056', '03352063']),
    'Samtgemeinde Lathen': dict(street='Erna-de-Vries-Platz 7', plz='49762', city='Lathen',
                  email='info@lathen.de', gemeinden=['03454013', '03454029', '03454039', '03454040', '03454043', '03454052']),
    'Samtgemeinde Leinebergland': dict(street='Blanke Straße 16', plz='31028', city='Gronau (Leine)',
                  email='info@sg-leinebergland.de', gemeinden=['03254013', '03254041', '03254043']),
    'Samtgemeinde Lengerich': dict(street='Mittelstraße 15', plz='49838', city='Lengerich',
                  email='info@lengerich-emsland.de', gemeinden=['03454002', '03454015', '03454017', '03454028', '03454031', '03454059']),
    'Samtgemeinde Lindhorst': dict(street='Bahnhofstraße 55 a', plz='31698', city='Lindhorst',
                  email='info@sg-lindhorst.de', gemeinden=['03257007', '03257015', '03257020', '03257021']),
    'Samtgemeinde Lüchow (Wendland)': dict(street='Amtsweg 4', plz='29439', city='Lüchow (Wendland)',
                  email='samtgemeinde@luechow-wendland.de', gemeinden=['03354001', '03354002', '03354013', '03354015', '03354016', '03354017', '03354018', '03354022', '03354023', '03354024', '03354025', '03354026']),
    'Samtgemeinde Lühe': dict(street='Alter Marktplatz 1 a', plz='21720', city='Steinkirchen',
                  email='info@luehe-online.de', gemeinden=['03359020', '03359021', '03359026', '03359032', '03359033', '03359039']),
    'Samtgemeinde Meinersen': dict(street='Hauptstraße 1', plz='38536', city='Meinersen',
                  email='info@sg-meinersen.de', gemeinden=['03151012', '03151015', '03151017', '03151018']),
    'Samtgemeinde Mittelweser': dict(street='Am Markt 4', plz='31592', city='Stolzenau',
                  email='info@sg-mittelweser.de', gemeinden=['03256006', '03256016', '03256017', '03256018', '03256032']),
    'Samtgemeinde Nenndorf': dict(street='Rodenberger Allee 13', plz='31542', city='Bad Nenndorf',
                  email='info@?bad-nenndorf.de', gemeinden=['03257006', '03257011', '03257016', '03257036']),
    'Samtgemeinde Neuenhaus': dict(street='Veldhausener Straße 26', plz='49828', city='Neuenhaus',
                  email='rathaus@neuenhaus.de', gemeinden=['03456004', '03456005', '03456013', '03456014', '03456017']),
    'Samtgemeinde Neuenkirchen': dict(street='Alte Poststraße 5 - 7', plz='49586', city='Neuenkirchen',
                  email='info@neuenkirchen-os.de', gemeinden=['03459026', '03459027', '03459032']),
    'Samtgemeinde Niedernwöhren': dict(street='Hauptstraße 46', plz='31712', city='Niedernwöhren',
                  email='info@sg-niedernwoehren.de', gemeinden=['03257019', '03257023', '03257025', '03257027', '03257030', '03257037']),
    'Samtgemeinde Nienstädt': dict(street='Bahnhofstraße 7', plz='31691', city='Helpsen',
                  email='samtgemeinde@sg-nienstaedt.de', gemeinden=['03257013', '03257014', '03257026', '03257034']),
    'Samtgemeinde Nord-Elm': dict(street='Steinweg 15', plz='38373', city='Süpplingen',
                  email='verwaltung@samtgemeinde-nord-elm.de', gemeinden=['03154005', '03154017', '03154021', '03154022', '03154025', '03154026']),
    'Samtgemeinde Nordhümmling': dict(street='Poststraße 13', plz='26897', city='Esterwegen',
                  email='info@nordhuemmling.de', gemeinden=['03454004', '03454006', '03454011', '03454022', '03454051']),
    'Samtgemeinde Nordkehdingen': dict(street='Hauptstraße 31', plz='21729', city='Freiburg (Elbe)',
                  email='samtgemeinde@nordkehdingen.de', gemeinden=['03359004', '03359018', '03359030', '03359035', '03359040']),
    'Samtgemeinde Oderwald': dict(street='Bahnhofstraße 6', plz='38312', city='Börßum',
                  email='posteingang@sg-oderwald.de', gemeinden=['03158005', '03158010', '03158014', '03158019', '03158023', '03158038']),
    'Samtgemeinde Oldendorf-Himmelpforten': dict(street='Mittelweg 2', plz='21709', city='Himmelpforten',
                  email='info@oldendorf-himmelpforten.de', gemeinden=['03359009', '03359014', '03359015', '03359016', '03359019', '03359022', '03359024', '03359025', '03359029', '03359036']),
    'Samtgemeinde Ostheide': dict(street='Schulstraße 2', plz='21397', city='Barendorf',
                  email='rathaus@ostheide.de', gemeinden=['03355005', '03355026', '03355030', '03355036', '03355038', '03355040']),
    'Samtgemeinde Papenteich': dict(street='Hauptstraße 15', plz='38527', city='Meine',
                  email='info@papenteich.de', gemeinden=['03151001', '03151016', '03151023', '03151027', '03151034', '03151041']),
    'Samtgemeinde Radolfshausen': dict(street='Vöhreweg 10', plz='37136', city='Ebergötzen',
                  email='rathaus@radolfshausen.de', gemeinden=['03159011', '03159023', '03159032', '03159033', '03159035']),
    'Samtgemeinde Rehden': dict(street='Schulstraße 20', plz='49453', city='Rehden',
                  email='info@rehden.de', gemeinden=['03251006', '03251011', '03251019', '03251030', '03251046']),
    'Samtgemeinde Rethem (Aller)': dict(street='Lange Straße 4', plz='27336', city='Rethem (Aller)',
                  email='rathaus@rethem.de', gemeinden=['03358003', '03358009', '03358013', '03358018']),
    'Samtgemeinde Rodenberg': dict(street='Amtsstraße 5', plz='31552', city='Rodenberg',
                  email='info@rodenberg.de', gemeinden=['03257002', '03257017', '03257018', '03257024', '03257029', '03257032']),
    'Samtgemeinde Rosche': dict(street='Lüchower Straße 15', plz='29571', city='Rosche',
                  email='info@samtgemeinde-rosche.de', gemeinden=['03360015', '03360016', '03360018', '03360022', '03360024']),
    'Samtgemeinde Sachsenhagen': dict(street='Markt 1', plz='31553', city='Sachsenhagen',
                  email='info@sachsenhagen.de', gemeinden=['03257004', '03257010', '03257033', '03257038']),
    'Samtgemeinde Salzhausen': dict(street='Rathausplatz 1', plz='21376', city='Salzhausen',
                  email='info@rathaus-salzhausen.de', gemeinden=['03353010', '03353011', '03353012', '03353013', '03353030', '03353034', '03353037', '03353042']),
    'Samtgemeinde Scharnebeck': dict(street='Marktplatz 1', plz='21379', city='Scharnebeck',
                  email='rathaus@scharnebeck.de', gemeinden=['03355003', '03355011', '03355015', '03355018', '03355019', '03355021', '03355032', '03355033']),
    'Samtgemeinde Schwaförden': dict(street='Poststraße 157', plz='27252', city='Schwaförden',
                  email='info@schwafoerden.de', gemeinden=['03251001', '03251015', '03251028', '03251031', '03251032', '03251038']),
    'Samtgemeinde Schwarmstedt': dict(street='Am Markt 1', plz='29690', city='Schwarmstedt',
                  email='rathaus@schwarmstedt.de', gemeinden=['03358005', '03358007', '03358010', '03358015', '03358020']),
    'Samtgemeinde Schüttorf': dict(street='Markt 2', plz='48465', city='Schüttorf',
                  email='info@schuettorf.de', gemeinden=['03456003', '03456010', '03456016', '03456018', '03456020', '03456027']),
    'Samtgemeinde Selsingen': dict(street='Hauptstr. 30', plz='27446', city='Selsingen',
                  email='samtgemeinde@selsingen.de', gemeinden=['03357003', '03357011', '03357014', '03357036', '03357038', '03357040', '03357042', '03357043']),
    'Samtgemeinde Sickte': dict(street='Am Kamp 12', plz='38173', city='Sickte',
                  email='info@sickte.de', gemeinden=['03158009', '03158012', '03158013', '03158030', '03158033']),
    'Samtgemeinde Siedenburg': dict(street='Allee 4', plz='27254', city='Siedenburg',
                  email='kontakt@siedenburg-online.de', gemeinden=['03251008', '03251024', '03251027', '03251034', '03251035']),
    'Samtgemeinde Sittensen': dict(street='Am Markt 11', plz='27419', city='Sittensen',
                  email='info@sg.sittensen.de', gemeinden=['03357017', '03357019', '03357029', '03357032', '03357034', '03357044', '03357048', '03357050', '03357056']),
    'Samtgemeinde Sottrum': dict(street='Am Eichkamp 12', plz='27367', city='Sottrum',
                  email='samtgemeinde@sottrum.de', gemeinden=['03357001', '03357005', '03357020', '03357022', '03357028', '03357037', '03357045']),
    'Samtgemeinde Spelle': dict(street='Hauptstraße 43', plz='48480', city='Spelle',
                  email='Samtgemeinde@spelle.de', gemeinden=['03454034', '03454046', '03454049']),
    'Samtgemeinde Steimbke': dict(street='Kirchstraße 4', plz='31634', city='Steimbke',
                  email='rathaus@steimbke.de', gemeinden=['03256020', '03256026', '03256029', '03256031']),
    'Samtgemeinde Suderburg': dict(street='Bahnhofstraße 54', plz='29556', city='Suderburg',
                  email='info@suderburg.de', gemeinden=['03360007', '03360009', '03360023']),
    'Samtgemeinde Sögel': dict(street='Ludmillenhof 1', plz='49751', city='Sögel',
                  email='samtgemeinde@soegel.de', gemeinden=['03454005', '03454016', '03454023', '03454024', '03454047', '03454048', '03454050', '03454058']),
    'Samtgemeinde Tarmstedt': dict(street='Hepstedter Straße 9', plz='27412', city='Tarmstedt',
                  email='info@tarmstedt.de', gemeinden=['03357007', '03357010', '03357026', '03357030', '03357047', '03357052', '03357053', '03357055']),
    'Samtgemeinde Thedinghausen': dict(street='Braunschweiger Straße 10', plz='27321', city='Thedinghausen',
                  email='info@thedinghausen.de', gemeinden=['03361002', '03361004', '03361010', '03361013']),
    'Samtgemeinde Tostedt': dict(street='Schützenstraße 24', plz='21255', city='Tostedt',
                  email='info@tostedt.de', gemeinden=['03353006', '03353015', '03353018', '03353021', '03353022', '03353027', '03353035', '03353038', '03353041']),
    'Samtgemeinde Uchte': dict(street='Balkenkamp 1', plz='31600', city='Uchte',
                  email='rathaus@sg-uchte.de', gemeinden=['03256004', '03256024', '03256033', '03256034']),
    'Samtgemeinde Uelsen': dict(street='Itterbecker Straße 11', plz='49843', city='Uelsen',
                  email='info@uelsen.de', gemeinden=['03456006', '03456007', '03456008', '03456011', '03456023', '03456024', '03456026']),
    'Samtgemeinde Velpke': dict(street='Grafhorster Straße 6', plz='38458', city='Velpke',
                  email='samtgemeinde@velpke.de', gemeinden=['03154001', '03154004', '03154007', '03154009', '03154024']),
    'Samtgemeinde Wathlingen': dict(street='Am Schmiedeberg 1', plz='29339', city='Wathlingen',
                  email='info@wathlingen.de', gemeinden=['03351001', '03351018', '03351021']),
    'Samtgemeinde Werlte': dict(street='Marktstraße 1', plz='49757', city='Werlte',
                  email='info@werlte.de', gemeinden=['03454027', '03454033', '03454042', '03454055', '03454057']),
    'Samtgemeinde Wesendorf': dict(street='Alte Heerstraße 20', plz='29392', city='Wesendorf',
                  email='info@sg-wesendorf.de', gemeinden=['03151010', '03151026', '03151033', '03151035', '03151036', '03151038']),
    'Samtgemeinde Weser- Aue': dict(street='Rathausstraße 14', plz='31608', city='Marklohe',
                  email='info@weser-aue.de', gemeinden=['03256001', '03256002', '03256019', '03256021', '03256023', '03256036']),
    'Samtgemeinde Zeven': dict(street='Am Markt 4', plz='27404', city='Zeven',
                  email='samtgemeinde@zeven.de', gemeinden=['03357013', '03357018', '03357021', '03357057']),
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
        batch_id = f"erschliessung-ni-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for sg_name, info in SAMTGEMEINDEN.items():
            authority = db.query(Authority).filter(Authority.authority_name == sg_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=sg_name,
                    authority_type="Samtgemeinde (Verwaltungsgemeinschaft nach NKomVG)",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Niedersachsen", phone=None, email=info["email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for ags in info["gemeinden"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"Erschliessung NI - {sg_name}",
                    request_type_id="ERSCHLIESSUNG", state="Niedersachsen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{sg_name} - {QUOTE}", source_url=NKOMVG_URL,
                    source_license="Amtliche Rechtsgrundlage (NKomVG) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(SAMTGEMEINDEN)} Samtgemeinden.")
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
