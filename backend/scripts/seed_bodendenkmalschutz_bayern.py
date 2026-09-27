"""
BODENDENKMALSCHUTZ (Bodendenkmalpflege, Genehmigung von Grabungen nach
Art. 7 BayDSchG) für Bayern - bislang bundesweit die auffälligste Lücke
(2.056 von 2.056 Gemeinden NO_MATCH, siehe Recherche-Agent
"Bayern-Verwaltungsstruktur-Recherche": in Bayern ist die jeweilige
Kreisverwaltungsbehörde (Landratsamt bzw. kreisfreie Stadt) nach Art. 10
Abs. 1 BayDSchG die "Untere Denkmalschutzbehörde" - das bedeutet 96
COUNTY-Regeln (71 Landkreise + 25 kreisfreie Städte) decken ALLE 2.056
bayerischen Gemeinden ab, keine einzelne Gemeinde-Recherche nötig
(Faktor-~21-Hebel).

Auf Nutzerauftrag ("starte so viele Agenten wie möglich um die NO_MATCH
Fälle so schnell wie möglich zu vervollständigen") wurden 8 parallele
Recherche-Agenten eingesetzt (reine Web-Recherche, keine Datenbank-
Schreibzugriffe - alle Schreibvorgänge blieben seriell bei mir). Ergebnis:
89 von 96 Kreisverwaltungen mit amtlicher Quelle belegt, 7 blieben
ehrlich als OFFEN gemeldet statt geraten: Amberg (kreisfreie Stadt - nur
ein Zeitungsartikel als Beleg gefunden, bewusst NICHT übernommen),
Dillingen a.d.Donau, Neumarkt i.d.OPf., Neustadt a.d.Aisch-Bad Windsheim,
Pfaffenhofen a.d.Ilm, Straubing-Bogen (zwei konkurrierende, gleichrangige
Organisationseinheiten ohne eindeutige amtliche Zuordnung).

SOURCING-STANDARD (wie in allen vorherigen Durchläufen): `source_url`
MUSS eine amtliche Quelle sein (Landkreis-/Stadt-Website, offizielles
bayerisches Landesportal/BayernPortal). NIEMALS ein Zeitungsartikel.

AGS-Kreis-Zuordnung: jede der 96 Regeln ist eine COUNTY-Ebene-Regel
(matching_level=COUNTY, ags=ags_kreis). Adressen werden zur Laufzeit aus
dem amtlichen Destatis-Anschriftenverzeichnis nachgeschlagen (siehe
app/services/address_directory.py) - AUSSCHLIESSLICH für Adresse/
allgemeine E-Mail, NIE für die fachliche Zuständigkeitsaussage selbst.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, 8 parallele Recherche-Agenten, Bodendenkmalschutz Bayern)"

DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"

# ags_kreis (5-stellig) -> dict(name, dept, tier, quote, url)
KREISE = {
    "09771": dict(name="Aichach-Friedberg", dept="Sachgebiet 41 - Bauordnung, Bauleitplanung, Denkmalschutz", tier="stark",
                  quote="'Bauordnung, Bauleitplanung, Denkmalschutz' (Aufgabenbereich von Sachgebiet 41 im Geschäftsverteilungsplan)",
                  url="https://lra-aic-fdb.de/wp-content/uploads/2026/03/gvpl.pdf"),
    "09171": dict(name="Altötting", dept="Sachgebiet Denkmalschutz (Abteilung Bauen & Wohnen)", tier="stark",
                  quote="'Vollzug des Bayerischen Denkmalschutzgesetzes, insbesondere' Bearbeitung von Anträgen für Bau- und Bodendenkmäler",
                  url="https://www.lra-aoe.de/themen/bauen-wohnen/denkmalschutz/"),
    "09361": None,  # Amberg (kreisfreie Stadt) - OFFEN, nur Zeitungsartikel gefunden
    "09371": dict(name="Amberg-Sulzbach", dept="Bauamt Verwaltung, Denkmalschutz, Wohnraumförderung/sozialer Wohnungsbau", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde ist beim Landratsamt Amberg-Sulzbach angesiedelt.'",
                  url="https://www.kreis-as.de/Bauen-Gewerbe/Bauen-und-Wohnen/Denkmalschutz/"),
    "09561": dict(name="Ansbach (kreisfreie Stadt)", dept="Amt für Stadtentwicklung und Klimaschutz - Untere Denkmalschutzbehörde", tier="stark",
                  quote="Kopfzeile bezeichnet die Dienststelle wörtlich als 'Untere Denkmalschutzbehörde'",
                  url="https://www.ansbach.de/B%C3%BCrger/Bauen-Wohnen/Denkmalschutz/index.php?ModID=9&object=tx%7C2595.2&FID=2595.1762.1&NavID=2595.323&La=1"),
    "09571": dict(name="Ansbach (Landkreis)", dept="Sachgebiet 41 - Bauamt (Abteilung 4 - Bau und Umwelt)", tier="stark",
                  quote="'Denkmalschutz; Beantragung einer Erlaubnis für Maßnahmen an Bau- und Bodendenkmälern' als Leistung von Sachgebiet 41 - Bauamt",
                  url="https://www.landkreis-ansbach.de/Landratsamt/Organigramm/index.php?object=tx,3797.1.1&ModID=9&FID=3797.38.1"),
    "09661": dict(name="Aschaffenburg (kreisfreie Stadt)", dept="Bauordnungsamt, Sachgebiet Denkmalschutz/Denkmalpflege", tier="stark",
                  quote="'Die Denkmalschutzbehörde der Stadt Aschaffenburg im Bauordnungsamt ist für den Vollzug des Denkmalschutzgesetzes zuständig'",
                  url="https://www.aschaffenburg.de/Leben-in-Aschaffenburg/Umzug-Wohnen-Bauen/Bauen/Denkmalschutz/"),
    "09671": dict(name="Aschaffenburg (Landkreis)", dept="Arbeitsbereich 14.2 - Baurecht, sozialer Wohnungsbau, Denkmalschutz, Gutachterausschuss", tier="stark",
                  quote="'Baurecht, sozialer Wohnungsbau, Denkmalschutz, Gutachterausschuss' (Bezeichnung des Arbeitsbereichs 14.2)",
                  url="https://www.landkreis-aschaffenburg.de/index.php?object=tx,3984.2.1&ModID=10&FID=3984.3385.1"),
    "09761": dict(name="Augsburg (kreisfreie Stadt)", dept="Bauordnungsamt mit Unterer Denkmalschutzbehörde", tier="stark",
                  quote="Amtsbezeichnung: 'Bauordnungsamt mit Unterer Denkmalschutzbehörde'; zuständig u.a. für Grabungserlaubnis gem. Art. 7 BayDSchG",
                  url="https://www.augsburg.de/buergerservice-rathaus/buergerservice/aemter-behoerden/staedtische-dienststellen/b/bauordnungsamt-mit-unterer-denkmalschutzbehoerde/untere-denkmalschutzbehoerde"),
    "09772": dict(name="Augsburg (Landkreis)", dept="Fachbereich Bauleitplanung, Bauordnung - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Sie erteilt Baugenehmigungen ... sowie Grabungserlaubnisse für Eingriffe im Bereich von Bodendenkmälern.'",
                  url="https://www.landkreis-augsburg.de/service-amt/bauen/bauen-rechtlich/bauleitplanung-bauordnung-rechtlich/denkmalschutz/"),
    "09672": dict(name="Bad Kissingen", dept="Bauservice - Denkmalschutz", tier="stark",
                  quote="'Landratsamt Bad Kissingen, Bauservice - Denkmalschutz' als zuständige Organisationseinheit u.a. für Bodendenkmalpflege",
                  url="https://www.landkreis-badkissingen.de/buerger--politik/buergerservice/fachbereiche-und-abteilungen/bauen--umwelt/bauen/denkmalschutz/1378.Denkmalschutz.html"),
    "09180": dict(name="Garmisch-Partenkirchen", dept="Sachgebiet 31 Bauverwaltung (Bereich Bauen)", tier="stark",
                  quote="'Sie müssen die Erlaubnis für Maßnahmen an Bau- und Bodendenkmälern bei der zuständigen Unteren Denkmalschutzbehörde ... beantragen.' - zuständige Stelle: 'Landratsamt Garmisch-Partenkirchen - Sg. 31 Bauverwaltung'",
                  url="https://www.bayernportal.de/dokumente/leistung/82442934325?plz=82487&behoerde=03774718660&gemeinde=040746809668"),
    "09173": dict(name="Bad Tölz-Wolfratshausen", dept="Sachgebiet 22 - Kreisbauamt Verwaltung", tier="stark",
                  quote="'The district building authority is the building permit and monument protection authority' / 'Monument protection; application for permission for measures on architectural and ground monuments'",
                  url="https://www.lra-toelz.de/:translation/en/site-wurzel/de/buergerservice-views/abteilungen/BAY:department:51280/sachgebiet-22-kreisbauamt-verwaltung/"),
    "09461": dict(name="Bamberg (kreisfreie Stadt)", dept="Bauordnungsamt / Denkmalpflege", tier="stark",
                  quote="'Neben der Wahrnehmung der fachlichen Belange als Untere Denkmalschutzbehörde werden von der städtischen Denkmalpflege zudem die stadteigenen Denkmäler unterhalten und instandgesetzt.'",
                  url="https://www.stadt.bamberg.de/denkmalpflege"),
    "09471": dict(name="Bamberg (Landkreis)", dept="Fachbereich 41.2 - Bauleitplanung", tier="stark",
                  quote="'Untere Denkmalschutzbehörde am Landratsamt' (zuständig für denkmalschutzrechtliche Erlaubnisse und Grabungserlaubnisse)",
                  url="https://www.landkreis-bamberg.de/Landratsamt/Verwaltung/Landratsamt-A-Z/Bauen/Bauen-im-Landkreis-Bamberg/Denkmalschutz.php?object=tx,2892.2&ModID=10&FID=2892.69.1&NavID=2892.170&La=1"),
    "09462": dict(name="Bayreuth (kreisfreie Stadt)", dept="Bauordnungsamt, Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Bauordnungsamt, Untere Denkmalschutzbehörde' (Formular BOA_Antrag auf denkmalschutzrechtliche Erlaubnis)",
                  url="https://online-dienste.bayreuth.de/frontend-server/form/provide/502/"),
    "09472": dict(name="Bayreuth (Landkreis)", dept="Sachgebiet Bauleitplanung, Städtebauförderung, Denkmalschutz, Abgeschl.-bescheinigungen", tier="stark",
                  quote="'Bauleitplanung, Städtebauförderung, Denkmalschutz, Abgeschl.-bescheinigungen'",
                  url="https://www.landkreis-bayreuth.de/buergerservice/bauen/bauleitplanung-staedtebaufoerderung-denkmalschutz"),
    "09172": dict(name="Berchtesgadener Land", dept="Fachbereich 31 - Planen, Bauen, Wohnen", tier="schwaecher",
                  quote="Zuständige Organisationseinheit für die Leistung 'Denkmalschutz; Beratung von Denkmaleigentümern' laut BayernPortal",
                  url="https://www.bayernportal.de/dokumente/leistung/94996885671?plz=83486&behoerde=05663477688&gemeinde=601080070669"),
    "09372": dict(name="Cham", dept="Sachgebiet 504.03.02 - Denkmalschutz / Erlaubnisse", tier="stark",
                  quote="'504.03.02 Denkmalschutz / Erlaubnisse - Geschäftsverteilung | Landkreis Cham'",
                  url="https://www.landkreis-cham.de/landkreis-landratsamt/geschaeftsverteilung/?5040302-denkmalschutz-erlaubnisse&orga=76484"),
    "09463": dict(name="Coburg (kreisfreie Stadt)", dept="Stadtbauamt - Denkmalschutz / Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Denkmalschutz / Untere Denkmalschutzbehörde' (Seitentitel, Stadtbauamt Coburg)",
                  url="https://www.coburg.de/vv/oe/Stadtbauamt-Denkmalschutz-Untere-Denkmalschutzbehoerde.php"),
    "09473": dict(name="Coburg (Landkreis)", dept="Untere Denkmalschutzbehörde", tier="stark",
                  quote="'... mit der Unteren Denkmalschutzbehörde des Landratsamtes Coburg Kontakt aufzunehmen ...' (Antrag auf Grabungserlaubnis nach Art. 7 DSchG)",
                  url="https://www.landkreis-coburg.de/fileadmin/3_Landratsamt/antrag_auf_grabungserlaubnis_nach_art._7_dschg.pdf"),
    "09174": dict(name="Dachau", dept="Sachgebiet 40 - Bauleitplanung, Denkmalschutz, Wohnungsbau (Abteilung 4 - Baurecht)", tier="stark",
                  quote="'Sachgebiet 40: Bauleitplanung, Denkmalschutz, Wohnungsbau'",
                  url="https://www.landratsamt-dachau.de/Verwaltung-Landkreis-Kultur/Verwaltung/Unsere-Fachbereiche/Abteilung-4-Baurecht/Sachgebiet-40-Bauleitplanung-Denkmalschutz-Wohnungsbau/"),
    "09271": dict(name="Deggendorf", dept="Bauamt, Sachgebiet Baurecht, Denkmalschutz, Wohnraumförderung, Gutachterausschuss, Bautechnik", tier="stark",
                  quote="'Baurecht, Denkmalschutz, Wohnraumförderung, Geschäftsstelle/Gutachterausschuss, Bautechnik'",
                  url="https://www.landkreis-deggendorf.de/leben-arbeiten/bauen/denkmalschutz/"),
    "09773": None,  # Dillingen a.d.Donau - OFFEN
    "09279": dict(name="Dingolfing-Landau", dept="Sachgebiet 40 - Bauwesen, Denkmalschutz, Wohnraumförderung, Wohnungsbindung (Abteilung IV)", tier="stark",
                  quote="'Sachgebiet 40 - Bauwesen, Denkmalschutz, Wohnraumförderung, Wohnungsbindung'",
                  url="https://dingolfing-landau.de/service-und-verwaltung/verwaltung/fachbereiche-und-personen/abteilung-iv-bau-umwelt-natur/sachgebiet-40-bauwesen-denkmalschutz-wohnraumfoerderung-wohnungsbindung/"),
    "09779": dict(name="Donau-Ries", dept="Untere Denkmalschutzbehörde (Bereich Bauen/Denkmalschutz)", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde im Landratsamt ist Ihr erster Ansprechpartner zu Fragen des Denkmalschutzes.'",
                  url="https://www.donau-ries.de/bauen-wohnen/denkmalschutz"),
    "09175": dict(name="Ebersberg", dept="Bauamt, Sachgebiet 42 (Abteilung 4: Bau und Umwelt)", tier="stark",
                  quote="'Näheres hierzu können Sie bei der Unteren Denkmalschutzbehörde erfragen.' (Anträge postalisch an die Untere Denkmalschutzbehörde)",
                  url="https://www.lra-ebe.de/bauen-wohnen/denkmalschutz/"),
    "09176": dict(name="Eichstätt", dept="Sachgebiet 41 - Technischer Hochbau (Bezirk Nord) / Sachgebiet 43 - Bauverwaltung, Wohnungswesen (Bezirk Süd)", tier="schwaecher",
                  quote="'Bezirk Nord: SG 41 - Technischer Hochbau [...] Anträge auf Erlaubnis nach Art. 7 Denkmalschutzgesetz an denkmalschutz@lra-ei.bayern.de'",
                  url="https://www.landkreis-eichstaett.de/buergerservice/themen/bauwesen-und-denkmalschutz/denkmalschutz-bodendenkmalpflege"),
    "09177": dict(name="Erding", dept="Bauamt / Abteilung 4, Sachgebiet Bauen und Planungsrecht, Denkmalschutz", tier="stark",
                  quote="'Das Landratsamt Erding ist als Kreisverwaltungsbehörde untere Denkmalschutzbehörde.'",
                  url="https://www.landkreis-erding.de/buerger-verwaltung/bauen-wohnen/bauen-bauamt/bauen-und-planungsrecht-denkmalschutz/denkmalschutz/"),
    "09562": dict(name="Erlangen", dept="Untere Denkmalschutzbehörde (eigenständiges Amt)", tier="stark",
                  quote="Amtsseite trägt wörtlich den Titel 'Untere Denkmalschutzbehörde'; zuständig u.a. für Maßnahmen an Bau- und Bodendenkmälern",
                  url="https://erlangen.de/amt/306010"),
    "09572": dict(name="Erlangen-Höchstadt", dept="Bauamt I", tier="stark",
                  quote="'Als untere Denkmalschutzbehörde ist das Landratsamt Erlangen-Höchstadt für den Vollzug des Denkmalschutzgesetzes im Landkreis zuständig.'",
                  url="https://www.erlangen-hoechstadt.de/buergerservice/a-bis-z/denkmalpflege/"),
    "09474": dict(name="Forchheim", dept="Fachbereich 41 (Bauwesen rechtlich) - Denkmalschutz", tier="stark",
                  quote="'Das Landratsamt Forchheim hat als Untere Denkmalschutzbehörde ... folgende Aufgaben' / 'ZUSTÄNDIGE STELLE: Landratsamt Forchheim, Denkmalschutz'",
                  url="https://lra-fo.de/Aufgabenbereiche/Bauen/Denkmalschutz/"),
    "09178": dict(name="Freising", dept="Bauamt (Bereich Denkmalschutz)", tier="stark",
                  quote="'Das Landratsamt Freising ist untere Denkmalschutzbehörde und zuständig für die Erlaubnisverfahren.'",
                  url="https://www.kreis-freising.de/buergerservice/abteilungen-und-sachgebiete/bauamt/denkmalschutz.html"),
    "09272": dict(name="Freyung-Grafenau", dept="Sachgebiet 41 - Bauwesen technisch", tier="schwaecher",
                  quote="'städtebaufachliche Beratung der Kommunen, ... Beratung und Prüfung Denkmalschutz' - Begriff 'Untere Denkmalschutzbehörde' nicht wörtlich auf dieser Seite",
                  url="https://www.freyung-grafenau.de/leben-und-wohnen/bauen/technisches-bauamt"),
    "09179": dict(name="Fürstenfeldbruck", dept="Bauamt - Untere Denkmalschutzbehörde", tier="stark",
                  quote="Seitenbezeichnung 'Bauamt Untere Denkmalschutzbehörde'; Formular 'Erlaubnisantrag Bodendenkmal'",
                  url="https://www.lra-ffb.de/bau-umwelt/denkmalschutz/bau-und-bodendenkmaeler"),
    "09563": dict(name="Fürth (kreisfreie Stadt)", dept="Referat V - Bauwesen, Bauaufsicht (BaF) - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Untere Denkmalschutzbehörde: Nach telefonischer Vereinbarung unter den Rufnummern (0911) 974-3151 sowie (0911) 974-3167'",
                  url="https://services.fuerth.de/referat-v-bauwesen/bauaufsicht-baf/"),
    "09573": dict(name="Fürth (Landkreis)", dept="Untere Denkmalschutzbehörde im Bauamt", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde am Landratsamt Fürth ist für den Vollzug des Denkmalschutzgesetzes im Landkreis Fürth verantwortlich.'",
                  url="https://www.landkreis-fuerth.de/mein-landratsamt/umwelt-bauen-wohnen/bauen-sanieren/denkmalschutz"),
    "09774": dict(name="Günzburg", dept="Untere Denkmalschutzbehörde (Bereich Bauen und Wohnen)", tier="stark",
                  quote="'Die Koordination der Denkmalpflege obliegt somit im Bereich des Landkreises Günzburg der Unteren Denkmalschutzbehörde im Landratsamt Günzburg.'",
                  url="https://www.landkreis-guenzburg.de/amt-und-verwaltung/bauen-und-wohnen/denkmalschutz-und-dorfentwicklung/"),
    "09674": dict(name="Haßberge", dept="FB 32 - Bauamt, Denkmalpflege, Geschäftsstelle Gutachterausschuss", tier="stark",
                  quote="'Landratsamt Haßberge / FB 32 Bauamt, Denkmalpflege, Geschäftsstelle Gutachterausschuss'",
                  url="https://www.bayernportal.de/dokumente/behoerde/010743519739"),
    "09464": dict(name="Hof (kreisfreie Stadt)", dept="Sachgebiet Baurecht und Bauordnung", tier="schwaecher",
                  quote="'Stadt Hof - Sachgebiet Baurecht und Bauordnung' als zuständige Stelle für 'Denkmalschutz; Beratung von Denkmaleigentümern'",
                  url="https://www.hof.de/dienstleistungen/denkmalschutz-beratung-von-denkmaleigentuemern"),
    "09475": dict(name="Hof (Landkreis)", dept="Fachbereich 401 (Bauordnung)", tier="stark",
                  quote="'... sowie Untere Denkmalschutzbehörde'; BayernPortal: 'Landratsamt Hof / Fachbereich 401 Bauordnung' mit 'Untere Denkmalschutzbehörde' als Aufgabe",
                  url="https://www.landkreis-hof.de/dienstleistungen/denkmalschutz/"),
    "09161": dict(name="Ingolstadt", dept="Stadtplanungsamt - Denkmalschutz und Stadtsanierung", tier="stark",
                  quote="'Stadtplanungsamt - Denkmalschutz und Stadtsanierung'",
                  url="https://www.ingolstadt.de/denkmalschutz"),
    "09762": dict(name="Kaufbeuren", dept="Bauverwaltung", tier="schwaecher",
                  quote="Seite 'Denkmalrechtliche Erlaubnis' nennt 'Bauverwaltung' als Ansprechstelle - Begriff 'Untere Denkmalschutzbehörde' nicht wörtlich verwendet",
                  url="https://www.kaufbeuren.de/desktopdefault.aspx/tabid-1923/2759_read-19053/categories-581/"),
    "09273": dict(name="Kelheim", dept="Sachgebiet 42 - Bautechnik, Denkmalschutz, Gutachterausschuss, Wohnungsbauförderung, Kreisarchäologie", tier="stark",
                  quote="'... Wohnungsbauförderung, Gutachterausschuss, Denkmalschutz, Kreisarchäologie'",
                  url="https://www.landkreis-kelheim.de/landratsamt/landratsamt/geschaeftsverteilung/?42-staedtebauliche-und-technische-beurteilung-von-bauleitplanungs-und-bauordnungsrechtlichen-angelegenheiten-sowie-in-sonstigen-verwaltungsverfahren-bauueberwachung-wohnungsbaufoerderung-gutachterausschuss-denkmalschutz-kreisarchaeologie=&orga=b3e3078a5776c76585d4189fc687381d"),
    "09763": dict(name="Kempten (Allgäu)", dept="Bauordnungsamt - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Stadt Kempten (Allgäu) / Bauordnungsamt / Untere Denkmalschutzbehörde' (Briefkopf des offiziellen Merkblatts)",
                  url="https://www.kempten.de/file/2022_07_15_Merkblatt%20Denkmalschutz_2022.pdf"),
    "09675": dict(name="Kitzingen", dept="Sachgebiet 61 - Bauamt / Gutachterausschuss / Wohnraumförderung / Zuschüsse / Denkmalpflege", tier="stark",
                  quote="'Bauamt / Gutachten / Wohnraumförderung / Zuschüsse / Denkmalpflege'",
                  url="https://www.kitzingen.de/digitales-buergerbuero/bauamt-gutachten-wohnraumfoerderung-zuschuesse-denkmalpflege/denkmalpflege/"),
    "09476": dict(name="Kronach", dept="Sachgebiet 30 - Bauen (Abteilung 3 - Bauen und Verkehr)", tier="stark",
                  quote="'das Landratsamt Kronach als untere Denkmalschutzbehörde zuständig'",
                  url="https://www.landkreis-kronach.de/buergerservice-landratsamt/behoerdenwegweiser/?denkmalschutz=&orga=4d1649a0b36dcc89f1efc4d30e90457a"),
    "09477": dict(name="Kulmbach", dept="Fachbereich 33 - Baurecht (Bauleitplanung, Bauordnung und Denkmalpflege)", tier="stark",
                  quote="'33 Baurecht (Bauleitplanung, Bauordnung und Denkmalpflege)'",
                  url="https://www.landkreis-kulmbach.de/service-verwaltung/buergerservice/abteilungen-sachgebiete/abteilung-3-oeffentliche-sicherheit-bauwesen-natur-und-umweltschutz/33-baurecht-bauleitplanung-bauordnung-und-denkmalpflege"),
    "09181": dict(name="Landsberg am Lech", dept="Fachbereich Baurecht und Baurechtplanung", tier="schwaecher",
                  quote="Aufgabe 'Vollzug des Denkmalschutzgesetzes' - keine eigenständige, explizit 'Denkmalschutz' benannte Organisationseinheit ausgewiesen",
                  url="https://www.landkreis-landsberg.de/komxpress/baurecht-und-baurechtplanung/"),
    "09261": dict(name="Landshut (kreisfreie Stadt)", dept="Amt für Bauaufsicht (Referat 5) - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Untere Denkmalschutzbehörde | Stadt Landshut'; BayernPortal: 'Ihre Untere Denkmalschutzbehörde berät Sie gern.'",
                  url="https://landshut.de/leben/planen-bauen-wohnen/untere-denkmalschutzbehoerde"),
    "09274": dict(name="Landshut (Landkreis)", dept="Sachgebiet 44 - Bauleitplanung, Denkmalschutz, Gutachterausschuss, Wohnungsbauförderung", tier="stark",
                  quote="'44 Bauleitplanung, Denkmalschutz, Gutachterausschuss, Wohnungsbauförderung'",
                  url="https://www.landkreis-landshut.de/landratsamt/aufgaben-und-organisation/?denkmalschutz-bautechnische-abwicklung-und-betreuung-von-massnahmen=&orga=d3ff1ab8859786d48f53773a7403ff31"),
    "09478": dict(name="Lichtenfels", dept="Bauamt/Bauwesen - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Zuständig für die Erteilung der Erlaubnis ist die Untere Denkmalschutzbehörde beim Landratsamt.'",
                  url="https://www.lkr-lif.de/landratsamt/bauwesen/bauamt/bauwesen/175.Denkmalschutz---Beratungen-Landkreis.html"),
    "09776": dict(name="Lindau (Bodensee)", dept="Bauen und Umwelt - untere Bauaufsichtsbehörde, zugleich untere Denkmalschutzbehörde", tier="stark",
                  quote="'Die untere Bauaufsichtsbehörde des Landkreises Lindau (Bodensee) ... ist gleichzeitig untere Denkmalschutzbehörde.'",
                  url="https://www.landkreis-lindau.de/Wir-für-Sie/Dienstleistungen-und-Formulare/Bauwesen-beim-Landratsamt-Lindau-Bodensee-.php?ModID=10&FID=2846.5.1"),
    "09677": dict(name="Main-Spessart", dept="Sachgebiet Denkmalschutz (Bauverwaltung)", tier="stark",
                  quote="'Die Denkmalbehörden, insbesondere die Unteren Denkmalschutzbehörden (Landratsämter, kreisfreie Städte und Große Kreisstädte) ... haben die Aufgabe, Sie umfassend zu beraten.'",
                  url="https://www.main-spessart.de/buergerservice/sachgebiete-fachbereiche/bw_/Denkmalschutz_Beratung_von_Denkmaleigentuemern/34.Abteilungen-und-Sachgebiete.html?catID=187&detID=1689"),
    "09764": dict(name="Memmingen", dept="51 Stadtplanung - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Die Stadt Memmingen nimmt nach Art. 11 Abs. 1 des Denkmalschutzgesetzes (DSchG) die Aufgaben der Unteren Denkmalschutzbehörde (UDB) wahr'",
                  url="https://www.memmingen.de/digitales-amt/anliegen-a-z/dienstleistung/show/denkmalschutz.html"),
    "09182": dict(name="Miesbach", dept="FB 52 - Architektur, Denkmalschutz und Gutachterausschuss", tier="stark",
                  quote="'Als Untere Denkmalschutzbehörde entscheiden wir - mit Unterstützung des bayerischen Landesamtes für Denkmalpflege ...'",
                  url="https://www.landkreis-miesbach.de/Bauen-Umwelt/Staatliches-Bauamt/Architektur-und-Denkmalschutz/"),
    "09676": dict(name="Miltenberg", dept="Untere Denkmalschutzbehörde im Fachbereich Bauwesen", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde begleitet Eingriffe in geschützte Bodendenkmale und erteilt die hierfür notwendigen Grabungserlaubnisse.'",
                  url="https://www.landkreis-miltenberg.de/themen/bauen-und-planen/denkmalschutz.html"),
    "09183": dict(name="Mühldorf a.Inn", dept="Bau- und Planungsrecht (Bereich Bauen, Verkehr, Sicherheit) - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Das Landratsamt Mühldorf a. Inn ist untere Denkmalschutzbehörde und zuständig für die Erlaubnisverfahren.'",
                  url="https://www.lra-mue.de/bauen-verkehr-sicherheit/bau-und-planungsrecht/denkmalschutz/"),
    "09184": dict(name="München (Landkreis)", dept="Fachbereich 4.1.1 - Baurecht (Referat 4.1 Bauen, Geschäftsbereich 4)", tier="stark",
                  quote="Zuständige Stelle für die Denkmalschutzerlaubnis: Landratsamt München, Fachbereich 4.1.1 - Baurecht",
                  url="https://www.landkreis-muenchen.de/buergerservice/dienstleistung/denkmalschutzerlaubnis-beantragen/"),
    "09162": dict(name="München, Landeshauptstadt", dept="Lokalbaukommission (LBK) im Referat für Stadtplanung und Bauordnung", tier="stark",
                  quote="'Der LBK sind die Untere Bauaufsichtsbehörde, die Baumschutzbehörde und die Untere Denkmalschutzbehörde zugeordnet.'",
                  url="https://stadt.muenchen.de/infos/portrait-referat-stadtplanung-bauordnung.html"),
    "09775": dict(name="Neu-Ulm", dept="Fachbereich 31 - Bauordnung und Bauleitplanung (Untere Denkmalschutzbehörde)", tier="stark",
                  quote="'Auch das Graben nach Bodendenkmälern ... ist nach Art. 7 Abs. 1 DSchG erlaubnispflichtig.'",
                  url="https://www.landkreis-nu.de/de/Service-Verwaltung/Buergerservice-A-Z/Dienstleistungen-A-Z/Dienstleistung?view=publish&item=service&id=448"),
    "09185": dict(name="Neuburg-Schrobenhausen", dept="Bauamt (Fachbereich Bauwesen und Umweltschutz)", tier="stark",
                  quote="'Das Landesamt für Denkmalpflege (Abteilung Bodenfunde) oder die untere Denkmalschutzbehörde beim Landratsamt ist frühzeitig zu benachrichtigen.'",
                  url="https://neuburg-schrobenhausen.de/Bürgerservice/Fachbereiche/Bauwesen-Umweltschutz/Bauamt/Denkmalschutz/"),
    "09373": None,  # Neumarkt i.d.OPf. - OFFEN
    "09575": None,  # Neustadt a.d.Aisch-Bad Windsheim - OFFEN
    "09374": dict(name="Neustadt a.d.Waldnaab", dept="Bauamt (rechtlich), Wohnungs- und Planungswesen und Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Wer auf einem Grundstück nach Bodendenkmälern graben will ... muss vor Durchführung der Erdarbeiten eine entsprechende Erlaubnis einholen.'",
                  url="https://www.neustadt.de/landratsamt/abteilungen-und-sachgebiete/bauamt-rechtlich-wohnungs-und-planungswesen-und-untere-denkmalschutzbehoerde/denkmalschutz/"),
    "09564": dict(name="Nürnberg", dept="Bauordnungsbehörde - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Bauordnungsbehörde - Untere Denkmalschutzbehörde' (Seitentitel); eigene Unterseite 'Antragstellung bei Bodendenkmälern'",
                  url="https://www.nuernberg.de/internet/bauen/denkmalschutz.html"),
    "09574": dict(name="Nürnberger Land", dept="Bauamt - Untere staatliche Bauaufsichtsbehörde - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Bodendenkmal: Erteilung einer Erlaubnis nach Art. 7 Denkmalschutzgesetz'",
                  url="https://www.nuernberger-land.de/landratsamt/aufgaben-organisation/organigramm/das-bauamt/die-untere-staatliche-bauaufsichtsbehoerde/die-untere-denkmalschutzbehoerde"),
    "09780": dict(name="Oberallgäu", dept="SG 21 Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                  quote="'Grabarbeiten im Bereich von Bodendenkmälern bedürfen der Erlaubnis nach § 7 des Denkmalschutzgesetzes.'",
                  url="https://www.oberallgaeu.org/bauen-und-wohnen/denkmalschutz"),
    "09777": dict(name="Ostallgäu", dept="Sachgebiet 40 (Bauen/Denkmalschutz)", tier="schwaecher",
                  quote="'Denkmalschutz - Beantragung einer Erlaubnis für Maßnahmen an Bau- und Bodendenkmälern' - genaue Sachgebietszuordnung nicht auf derselben Seite verifizierbar",
                  url="https://www.ostallgaeu.de/bauamt.html"),
    "09262": dict(name="Passau (kreisfreie Stadt)", dept="Bauordnungsamt - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Das Bauordnungsamt als Untere Denkmalschutzbehörde erteilt denkmalschutzrechtliche Erlaubnisse ... bedarf ebenfalls der Erlaubnis (Art. 7 Abs. 1 Satz 1 DSchG).'",
                  url="https://www.passau.de/rathaus-buergerservice/dienstleistungen/a-z/denkmalschutz/"),
    "09275": dict(name="Passau (Landkreis)", dept="Sachgebiet 61 - Baugenehmigung (Abteilung 6 - Bauwesen rechtlich)", tier="schwaecher",
                  quote="'Denkmalschutzrechtliche Erlaubnisse für Bau- und Bodendenkmäler' - wörtliche Bezeichnung 'Untere Denkmalschutzbehörde' nicht auf derselben Seite bestätigt",
                  url="https://www.landkreis-passau.de/landkreis-verwaltung-politik/behoerdenwegweiser/aufgaben-und-zustaendigkeiten/?denkmalschutz=&orga=61305"),
    "09186": None,  # Pfaffenhofen a.d.Ilm - OFFEN
    "09276": dict(name="Regen", dept="Bereich Bauen / Wohnen / Denkmalschutz", tier="stark",
                  quote="'Das Landratsamt als Untere Denkmalschutzbehörde ist für den Vollzug des Denkmalschutzgesetzes zuständig bei Bau- und Bodendenkmälern.'",
                  url="https://www.landkreis-regen.de/bauen-wohnen-denkmalschutz/denkmalschutz/"),
    "09362": dict(name="Regensburg (kreisfreie Stadt)", dept="Amt für kulturelles Erbe - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Amt für kulturelles Erbe - Untere Denkmalschutzbehörde'",
                  url="https://www.regensburg.de/rathaus/aemteruebersicht/kulturreferat/amt-fuer-kulturelles-erbe/untere-denkmalschutzbehoerde"),
    "09375": dict(name="Regensburg (Landkreis)", dept="Sachgebiet L 18 - Kultur, Heimat- und Denkmalpflege", tier="stark",
                  quote="'Der Antrag auf Erteilung der Erlaubnis nach Art. 7 BayDSchG ist bei der Unteren Denkmalschutzbehörde (Landratsamt) einzureichen.'",
                  url="https://www.landkreis-regensburg.de/index.php?object=tx%2C3987.2.1&ModID=10&FID=3987.5990.1&kuo=1"),
    "09673": dict(name="Rhön-Grabfeld", dept="SG 4.1 Bauen und Denkmalschutz", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde stellt hierbei grundsätzlich die Genehmigungsbehörde dar und ist für den Landkreis Rhön-Grabfeld im Landratsamt verortet.'",
                  url="https://www.rhoen-grabfeld.de/themen/wohnen/denkmalschutz-1"),
    "09163": dict(name="Rosenheim (kreisfreie Stadt)", dept="Bauordnungsamt", tier="stark",
                  quote="'Untere Denkmalschutzbehörde' als Zuständigkeit des Bauordnungsamts; Antrag auf Erlaubnis nach Art. 7 BayDSchG für Bodendenkmäler",
                  url="https://www.rosenheim.de/politik-verwaltung/aemter-dienststellen/"),
    "09187": dict(name="Rosenheim (Landkreis)", dept="Sachgebiet 31 - Kreisbauamt", tier="stark",
                  quote="'Sie müssen die Erlaubnis für Maßnahmen an Bau- und Bodendenkmälern bei der zuständigen Unteren Denkmalschutzbehörde schriftlich oder über das bereitgestellte Online-Verfahren beantragen.'",
                  url="https://www.bayernportal.de/dokumente/leistung/82442934325?plz=83512&behoerde=36775537483&gemeinde=634635624669"),
    "09576": dict(name="Roth", dept="Untere Denkmalschutzbehörde (Bauverwaltung)", tier="stark",
                  quote="'Erteilung von denkmalrechtlichen Erlaubnissen für Maßnahmen an oder in der Nähe von Bau- und Bodendenkmälern'",
                  url="https://www.landratsamt-roth.de/themen/bauen-wohnen/bauen-eigenheim/denkmalpflege"),
    "09277": dict(name="Rottal-Inn", dept="Untere Denkmalschutzbehörde (im Bauamt)", tier="stark",
                  quote="'Das Landratsamt ist Untere Denkmalschutzbehörde im Landkreis Rottal-Inn.'",
                  url="https://www.rottal-inn.de/buergerservice-formulare/bauen-wohnen/denkmalschutz/"),
    "09565": dict(name="Schwabach", dept="Denkmalpflege (Referat 4, Stadtplanung und Bauwesen)", tier="stark",
                  quote="'Sie benötigen eine denkmalschutzrechtliche Erlaubnis, wenn Sie gezielt nach Bodendenkmälern graben wollen.'",
                  url="https://www.bayernportal.de/dokumente/leistung/82442934325?plz=91126&behoerde=57331532388&gemeinde=519968360682"),
    "09376": dict(name="Schwandorf", dept="Sachgebiet 3.2 - Bauaufsicht, Bauleitplanung, Denkmalschutz", tier="stark",
                  quote="'Das Landratsamt Schwandorf ist in seiner Funktion als Untere Denkmalschutzbehörde zuständig für die Erteilung denkmalrechtlicher Erlaubnisse im Landkreisgebiet.'",
                  url="https://www.landkreis-schwandorf.de/B%C3%BCrgerservice/Bauamt/Denkmalschutz.php?object=tx%2C3300.5&ModID=7&FID=3300.13567.1&NavID=3300.28&La=1"),
    "09662": dict(name="Schweinfurt (kreisfreie Stadt)", dept="Sanierungsstelle - Untere Denkmalschutzbehörde in Schweinfurt", tier="stark",
                  quote="'Untere Denkmalschutzbehörde in Schweinfurt' (Bezeichnung der zuständigen Stelle, geführt durch die Sanierungsstelle)",
                  url="https://www.schweinfurt.de/leben-freizeit/bauen-wohnen/stadtsanierung-denkmalschutz/5174.Untere-Denkmalschutzbehoerde-in-Schweinfurt.html"),
    "09678": dict(name="Schweinfurt (Landkreis)", dept="Bauamt SG 40 - Denkmalschutz / Grundstücksverkehr / Abgeschlossenheitsbescheinigung", tier="stark",
                  quote="'die Untere Denkmalschutzbehörde (Landkreise, kreisfreie Städte und Große Kreisstädte)' / 'Sie benötigen eine denkmalschutzrechtliche Erlaubnis, wenn Sie gezielt nach Bodendenkmälern graben wollen.'",
                  url="https://www.landkreis-schweinfurt.de/landratsamt/serviceleistungen-informationen/details/detail/denkmalschutz-beantragung-einer-erlaubnis-fuer-massnahmen-an-bau-und-bodendenkmaelern-942"),
    "09188": dict(name="Starnberg", dept="Untere Denkmalschutzbehörde (Fachbereich Bauen und Wohnen/Bauwesen)", tier="stark",
                  quote="'Landratsamt Starnberg / Untere Denkmalschutzbehörde / Strandbadstr. 2 / 82319 Starnberg' (Adressfeld im offiziellen Formblatt form00027)",
                  url="https://www.lk-starnberg.de/media/custom/613_12073_1.PDF"),
    "09263": dict(name="Straubing", dept="Baugenehmigungen / Denkmalschutz", tier="stark",
                  quote="'Sie benötigen eine denkmalschutzrechtliche Erlaubnis, wenn Sie gezielt nach Bodendenkmälern graben wollen.' - Amtsbezeichnung 'Stadt Straubing - Baugenehmigungen / Denkmalschutz'",
                  url="https://www.straubing.de/rathaus-verwaltung/verwaltung/aemter-und-dienststellen/index.html?detID=18456&catID=1201"),
    "09278": None,  # Straubing-Bogen - OFFEN
    "09377": dict(name="Tirschenreuth", dept="Bauen und Wohnen", tier="stark",
                  quote="Beratung von Denkmaleigentümern als Aufgabe 'des Landratsamtes als untere Denkmalschutzbehörde'",
                  url="https://www.kreis-tir.de/landratsamt/bauen-und-wohnen-1/denkmalschutz"),
    "09189": dict(name="Traunstein", dept="Bauamt (Funktion 'Untere Denkmalschutzbehörde')", tier="schwaecher",
                  quote="'Technische Mitarbeiterin / Untere Denkmalschutzbehörde' - kein expliziter Bezug zu Bodendenkmal/Art. 7 BayDSchG auf derselben Seite",
                  url="https://www.traunstein.com/buergerservice/bauamt/ansprechpartner-bauamt"),
    "09778": dict(name="Unterallgäu", dept="Bauverwaltung / Sachgebiet Bauen und Wohnen (Denkmalpflege)", tier="schwaecher",
                  quote="'Für alle Erdarbeiten auf einem Grundstück im Bereich eines Bodendenkmals benötigen Sie eine Erlaubnis nach dem Denkmalschutzgesetz.' - keine explizite Sachgebietsnummer genannt",
                  url="https://www.landratsamt-unterallgaeu.de/buergerservice/bauen-und-wohnen/denkmalpflege"),
    "09363": dict(name="Weiden i.d.OPf.", dept="Abteilung Bauaufsicht und Wohnraumförderung / Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Abteilung Bauaufsicht und Wohnraumförderung Untere Denkmalschutzbehörde'; eigenes Formular 'Grabungserlaubnis Bodendenkmalpflege'",
                  url="https://www.weiden.de/wirtschaft/bauen-und-wohnen/denkmalschutz"),
    "09190": dict(name="Weilheim-Schongau", dept="Sg. 40 - Bauen und Planungsrecht (Abt. 4 - Bauen und Umwelt)", tier="stark",
                  quote="Geschäftsverteilungsplan: 'Denkmalschutz' als Aufgabe dem Sachgebiet 'Sg. 40 - Bauen und Planungsrecht' zugeordnet",
                  url="https://www.weilheim-schongau.de/landratsamt/geschaeftsverteilungsplan/?view=org&orgid=80acbc9f-8f78-4be7-bf6e-c41db872a130"),
    "09577": dict(name="Weißenburg-Gunzenhausen", dept="Sachgebiet 41 - Bauverwaltung, Wohnungswesen (Fachbereich 2)", tier="schwaecher",
                  quote="'Sachgebiet 41 - Bauverwaltung, Wohnungswesen' mit 'Fachbereich 2 - Bauordnungsrecht, Abgrabungsrecht, Denkmalerlaubnisse' - kein expliziter Bodendenkmal-Bezug auf derselben Seite",
                  url="https://www.landkreis-wug.de/sachgebiete/"),
    "09479": dict(name="Wunsiedel i.Fichtelgebirge", dept="FB 41 - Bauen und Wohnraumförderung", tier="stark",
                  quote="Zuständige Organisationseinheit für 'Denkmalschutz; Beratung von Denkmaleigentümern' laut BayernPortal; Landkreis-Seite nennt zusätzlich 'Antrag auf Grabungserlaubnis'",
                  url="https://www.bayernportal.de/dokumente/leistung/94996885671?plz=95632&behoerde=01219997480&gemeinde=442301187693"),
    "09663": dict(name="Würzburg (kreisfreie Stadt)", dept="Fachabteilung Bauaufsicht (FA Bauaufsicht)", tier="stark",
                  quote="'Die Bearbeitung der Anträge durch die Untere Denkmalschutzbehörde (FA Bauaufsicht) erfolgt unter Beteiligung des Bayer. Landesamtes für Denkmalpflege.'",
                  url="https://www.wuerzburg.de/themen/bauen-planen/bauantrag--baugenehmigung/denkmalschutz"),
    "09679": dict(name="Würzburg (Landkreis)", dept="Bauamt - Verwaltung und Wohnraumförderung (FB 22)", tier="stark",
                  quote="'Das Landratsamt als Untere Denkmalschutzbehörde und das Landesamt für Denkmalpflege' - Formulare 'Antrag auf Grabungserlaubnis nach Art. 7 BayDSchG'",
                  url="https://www.landkreis-wuerzburg.de/Denkmal-+und+Heimatpflege"),
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

    df = load_address_directory(DESTATIS_PATH)
    ars_index = build_ars_index(df[df["Satzart"] == SATZART_KREIS])

    db = SessionLocal()
    try:
        bayern_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Bayern").all()
        all_kreise = {u.ags_kreis for u in bayern_units}
        missing_from_script = sorted(all_kreise - set(KREISE.keys()))
        if missing_from_script:
            print(f"WARNUNG: {len(missing_from_script)} Kreise fehlen komplett im Skript (auch nicht als OFFEN vermerkt): {missing_from_script}")

        # Kreisfreie Stadt = Kreis besteht aus genau einer Gemeinde (ags_gemeinde
        # "000") - zuverlässiger als eine Namens-Heuristik (die für "München,
        # Landeshauptstadt", "Ingolstadt", "Erlangen" etc. fälschlich "Landratsamt"
        # vorangestellt hätte, weil diese Namen nicht wörtlich "Landkreis"/
        # "kreisfreie" enthalten).
        gemeinden_pro_kreis = {}
        for u in bayern_units:
            gemeinden_pro_kreis.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        ist_kreisfreie_stadt = {k: len(v) == 1 for k, v in gemeinden_pro_kreis.items()}

        staging = JurisdictionStagingService(db)
        batch_id = f"bodendenkmalschutz-bayern-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []
        offen_count = 0

        for ags_kreis, info in KREISE.items():
            if info is None:
                offen_count += 1
                continue
            addr = ars_index.get(ags_kreis)
            prefix = "" if ist_kreisfreie_stadt.get(ags_kreis) else "Landratsamt "
            authority_name = f"{prefix}{info['name']} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Kreisverwaltungsbehörde)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Bayern", phone=None, email=addr.email if addr else None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz Bayern - Kreisebene",
                request_type_id="BODENDENKMALSCHUTZ", state="Bayern", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))
        db.commit()

        print(f"\n{offen_count} Kreise bewusst offen gelassen (keine amtliche Quelle mit konkreter Zuordnung).")
        print(f"{len(staged)} Einträge gestaged (Batch {batch_id}).")
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
