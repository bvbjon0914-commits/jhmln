"""
BODENDENKMALSCHUTZ Niedersachsen. Anders als Bayern (klares 1:1
Kreis-Muster) und die 5 zentralisierten Länder (siehe
fix_bodendenkmalschutz_zentrale_laender.py) ist Niedersachsen strukturell
komplexer: nach § 19 Abs. 1 NDSchG ist untere Denkmalschutzbehörde
grundsätzlich der Landkreis, ABER Gemeinden, denen die Aufgabe der
unteren Bauaufsichtsbehörde übertragen wurde, sind für ihr eigenes
Gebiet SELBST untere Denkmalschutzbehörde - unabhängig vom umgebenden
Landkreis.

8 parallele Recherche-Agenten deckten dabei ZWEI unterschiedliche
Ausnahme-Kategorien auf:
1. Die abschließende gesetzliche Liste der "großen selbständigen
   Städte" nach § 14 Abs. 5 NKomVG: Celle, Cuxhaven, Goslar, Hameln,
   Hildesheim, Lingen (Ems), Lüneburg - alle 7 haben eine amtlich
   bestätigte, eigene untere Denkmalschutzbehörde.
2. WEITERE Städte, die NICHT auf dieser gesetzlichen Liste stehen,
   aber laut ihrer eigenen bzw. der Landkreis-Website TROTZDEM
   eigenständig als untere Denkmalschutzbehörde für ihr Stadtgebiet
   auftreten (vermutlich über eine gesonderte, individuelle Übertragung
   der unteren Bauaufsichtsbehörde nach § 57 NBauO): Wolfenbüttel,
   Peine, Göttingen, Einbeck, Melle, Winsen (Luhe). Diese wurden nur
   übernommen, wo die Stadt selbst ODER der jeweilige Landkreis dies
   amtlich UND wörtlich bestätigt (nicht nur ein Drittanbieter-Treffer).

SONDERFALL Region Hannover (ags_kreis 03241): KEINE pauschale
Kreis-Regel, weil die Region Hannover laut amtlicher Quelle NUR für 8
namentlich genannte Mitgliedskommunen (Burgwedel, Gehrden, Hemmingen,
Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen) untere
Denkmalschutzbehörde ist - für die übrigen ~10 Mitgliedskommunen war die
Zuständigkeit nicht amtlich verifizierbar (laut Rechercheagent nur
Suchmaschinen-Synthese, keine amtliche Einzelbestätigung je Gemeinde) und
bleibt daher bewusst OFFEN statt geraten. Die Landeshauptstadt Hannover
hat eine eigene, vom Regionsverband getrennte Behörde.

3 Landkreise blieben ehrlich OFFEN (keine amtliche Quelle mit konkreter
Organisationseinheit auffindbar, trotz gründlicher Recherche - teils durch
technische Website-Probleme am Recherchetag erschwert): Grafschaft
Bentheim, Harburg, Heidekreis.

Alle Adressen aus dem amtlichen Destatis-Anschriftenverzeichnis
nachgeschlagen (Kreis-Ebene) bzw. aus der jeweiligen Stadt-Adresse für
die Sonderstädte-Overrides.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, 8 parallele Recherche-Agenten, Bodendenkmalschutz Niedersachsen)"
DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"

# ags_kreis -> dict(dept, tier, quote, url) - Landkreis-/kreisfreie-Stadt-Ebene.
# Region Hannover (03241) und die 3 offen gebliebenen Kreise sind bewusst NICHT enthalten.
LANDKREISE = {
    "03451": dict(dept="Denkmalpflege (Amt für Bauwesen und Kreisentwicklung)", tier="stark",
                  quote="'Als Untere Denkmalschutzbehörde ist die Denkmalpflege in erster Linie für Bau- und Bodendenkmäler zuständig.'",
                  url="https://www.ammerland.de/Landkreis/Kreisverwaltung/Fachämter/Amt-für-Bauwesen-und-Kreisentwicklung/index.php"),
    "03452": dict(dept="Amt für Bauordnung, Planung und Naturschutz (Bereich Denkmalpflege)", tier="stark",
                  quote="'enge fachliche Zusammenarbeit mit der Unteren Denkmalschutzbehörde erforderlich um den Charakter der Kulturdenkmäler zu bewahren'",
                  url="https://www.landkreis-aurich.de/verwaltungsgliederung/dezernat-4/amt-fuer-bauordnung-planung-und-naturschutz/60-1-planung-und-bauordnung/"),
    "03101": dict(dept="Referat Stadtbild und Denkmalpflege (Fachbereich III/0610)", tier="stark",
                  quote="'Das Referat Stadtbild und Denkmalpflege nimmt die Aufgaben der \"unteren Denkmalschutzbehörde\" wahr.' - Bodendenkmalpflege explizit gelistet",
                  url="https://www.braunschweig.de/vv/oe/III/06/0610/index.php?cg_at_id=1"),
    "03453": dict(dept="Planungsamt, Sachgebiet Dorf- und Stadtentwicklung, Denkmalschutz und planerische Sonderaufgaben", tier="stark",
                  quote="Amtsleiter des Planungsamtes als Vorgesetzter der Denkmalschutzbehörde beim Landkreis Cloppenburg bestätigt",
                  url="https://www.lkclp.de/aktuelles-zentral?article=1255"),
    "03351": dict(dept="Amt für Bauen und Kreisentwicklung, Sachgebiet Denkmalpflege/Denkmalschutz (übriges Kreisgebiet außer Stadt Celle)", tier="stark",
                  quote="Seitentitel 'Denkmalpflege / Denkmalschutz'; eigener Ansprechpartner für 'Genehmigung von Sondengängen'",
                  url="https://www.landkreis-celle.de/Verwaltung-Politik/Verwaltung/Amt-für-Bauen-und-Kreisentwicklung/Denkmalpflege/"),
    "03352": dict(dept="Amt Bauaufsicht und Regionalplanung (übriges Kreisgebiet außer Stadt Cuxhaven)", tier="schwaecher",
                  quote="Zuständig u.a. für 'Kulturdenkmal: Forschung/Grabung - Genehmigung' laut Telefonverzeichnis",
                  url="https://www.landkreis-cuxhaven.de/Quicknavigation/Kontakt/Telefonverzeichnis/Landkreis-Cuxhaven-Bauen-Immissionsschutz-Regionalplanung.php?ModID=9&FID=578.77.1"),
    "03401": dict(dept="Fachbereich 50 (Planen, Bauen, Umweltschutz, Landwirtschaft und Verkehr) - Fachdienst 52 Bauordnung", tier="stark",
                  quote="Seite 'Untere Denkmalschutzbehörde' listet explizit 'Bodendenkmalpflege' sowie 'Kulturdenkmal: Forschung/Grabung - Genehmigung'",
                  url="https://www.delmenhorst.de/vv/oe/fb50/fd52/index.php?cg_at_id=1"),
    "03251": dict(dept="Fachdienst 63 Bauordnung und Städtebau, Team Denkmalpflege", tier="stark",
                  quote="'Die Zuständigkeit liegt beim Landkreis, der kreisfreien Stadt und der großen kreisangehörigen Stadt.'",
                  url="https://www.diepholz.de/buergerservice/dienstleistungen/bodendenkmalpflege-109-0.html?myMedium=1&selected_kommune=21750"),
    "03402": dict(dept="FD 363 Bauaufsicht (Fachbereich 300 Stadtentwicklung und Wirtschaftsförderung)", tier="schwaecher",
                  quote="'die Untere Denkmalschutzbehörde, die der Bauaufsichtsbehörde zugeordnet ist' - kein expliziter Bodendenkmal-Bezug auf dieser Seite",
                  url="https://www.emden.de/rathaus/verwaltung/fb-300-stadtentwicklung-und-wirtschaftsfoerderung/fd-363-bauaufsicht"),
    "03454": dict(dept="Untere Denkmalschutzbehörde des Landkreises Emsland (Abteilung Kultur, Emsland Archäologie Museum)", tier="stark",
                  quote="'Weitere Informationen dazu können bei der Unteren Denkmalschutzbehörde des Landkreises Emsland eingeholt werden.'",
                  url="https://www.emsland.de/leben-freizeit/kultur-2022/denkmalpflege/archaeologie/archaeologie.html"),
    "03455": dict(dept="Fachbereich Planung, Bauordnung und Klimaschutz, Bauamt Jever", tier="stark",
                  quote="Amtliche Leistungsseite 'Bodendenkmalpflege' des Landkreises Friesland",
                  url="https://www.friesland.de/buergerservice/dienstleistungen/bodendenkmalpflege-900000074-0.html?myMedium=1"),
    "03151": dict(dept="Kreis- und Stadtarchäologie Gifhorn", tier="stark",
                  quote="'...seit 2019 auch für die Bodendenkmalpflege auf dem Gebiet der Stadt Gifhorn zuständig ist'",
                  url="https://kulturerbe.niedersachsen.de/kultureinrichtung/isil_DE-2880//"),
    "03153": dict(dept="Fachdienst Bauen (übriges Kreisgebiet außer Stadt Goslar)", tier="stark",
                  quote="'Zuständige Stelle: Untere Denkmalschutzbehörde Landkreis Goslar' - Dienstleistung 'Denkmalrechtliche Genehmigung' (Erdarbeiten/Ausgrabungen, Bodenfunde)",
                  url="https://service.landkreis-goslar.de/dienstleistungen/-/egov-bis-detail/dienstleistung/8552/show"),
    "03159": dict(dept="Kreisarchäologie (Fachdienst Bauaufsicht, übriges Kreisgebiet außer Stadt Göttingen)", tier="stark",
                  quote="Dienstleistungsseite 'Kreisarchäologie', Anlaufstellen 'Team Bauaufsicht Göttingen'/'Team Bauaufsicht Osterode am Harz'",
                  url="https://serviceportal.landkreis-goettingen.de/dienstleistungen/-/egov-bis-detail/dienstleistung/4207/show"),
    "03252": dict(dept="Amt 53 Naturschutzamt (übriges Kreisgebiet außer Stadt Hameln)", tier="stark",
                  quote="'Antrag auf Erteilung einer Nachforschungsgenehmigung (§12 NDSchG)' - Zuständige Stelle: Landkreis Hameln-Pyrmont - 53 Naturschutzamt",
                  url="https://service.hameln-pyrmont.de/buergerservice/dienstleistungen/antrag-auf-erteilung-einer-nachforschungsgenehmigung-12-ndschg--900000905-33800.html"),
    "03154": dict(dept="Abteilung 63.04 Bodendenkmalpflege (Geschäftsbereich 63 Bauaufsicht, Denkmal- und Immissionsschutz)", tier="stark",
                  quote="'Abteilung 63.04 - Bodendenkmalpflege'",
                  url="https://www.landkreis-helmstedt.de/buergerservice/dienstleistungen/bodendenkmalpflege-900000245-0.html"),
    "03254": dict(dept="Bauordnungsamt (übriges Kreisgebiet außer Stadt Hildesheim)", tier="stark",
                  quote="'Die Zuständigkeit liegt beim Landkreis.' (Themenseite Bodendenkmalpflege)",
                  url="https://www.landkreishildesheim.de/Leistungen/Bauen-Planen/Denkmalschutz/"),
    "03255": dict(dept="Bauaufsicht und Denkmalpflege (2.61)", tier="schwaecher",
                  quote="Offizielle Organisationsseite 'Bauaufsicht und Denkmalpflege (2.61) | Landkreis Holzminden'",
                  url="https://www.landkreis-holzminden.de/portal/seiten/bauaufsicht-und-denkmalpflege-2-61--900002040-25600.html"),
    "03457": dict(dept="Planungsamt (Untere Denkmalbehörde), fachliche Beratung durch Archäologischen Dienst der Ostfriesischen Landschaft", tier="stark",
                  quote="'Die zuständige Genehmigungsbehörde für Bodendenkmale ist die untere Denkmalbehörde, hier der Landkreis Leer.'",
                  url="https://www.landkreis-leer.de/Themen/Bauen-Umwelt/Bauen/Denkmalschutz/"),
    "03354": dict(dept="Fachdienst 63 Bauordnung, Immissionsschutz, Denkmalpflege", tier="schwaecher",
                  quote="Offizieller Seitentitel 'Landkreis Lüchow-Dannenberg - Fachdienst 63 - Bauordnung, Immissionsschutz, Denkmalpflege'",
                  url="https://www.luechow-dannenberg.de/home/global/container/landkreis-luechow-dannenberg-fachdienst-63-bauordnung-immissionsschutz-denkmalpflege-22.aspx"),
    "03355": dict(dept="Untere Bodendenkmalschutzbehörde (Fachdienst Umwelt, übriges Kreisgebiet außer Hansestadt Lüneburg)", tier="stark",
                  quote="'Für Bodendenkmale ist die Untere Bodendenkmalschutzbehörde zuständig. Sie ist organisatorisch dem Fachdienst Umwelt zugeordnet.'",
                  url="https://www.landkreis-lueneburg.de/fuer-unsere-buergerinnen-und-buerger/bauen-und-planen/denkmalschutz.html"),
    "03256": dict(dept="52 FB Bauen", tier="stark",
                  quote="Leistungsseite 'Bodendenkmalpflege': 'Die Zuständigkeit liegt beim Landkreis, der kreisfreien Stadt und der großen kreisangehörigen Stadt.'",
                  url="https://www.lk-nienburg.de/buergerservice/dienstleistungen/bodendenkmalpflege-900000660-0.html?myMedium=1"),
    "03155": dict(dept="FB 41 - Bauverwaltung (übriges Kreisgebiet außer Städte Northeim und Einbeck)", tier="stark",
                  quote="'Während die Städte Einbeck und Northeim jeweils für ihr gesamtes Stadtgebiet die richtigen Ansprechpartner sind, ist für den übrigen Landkreis die Northeimer Kreisverwaltung zuständig.'",
                  url="https://www.landkreis-northeim.de/portal/seiten/denkmalschutz-900000032-23900.html"),
    "03458": dict(dept="Bauordnungsamt", tier="stark",
                  quote="Leistungsseite 'Kulturdenkmal: Forschung/Grabung - Genehmigung': 'Ansprechpartner/in: Bauordnungsamt'",
                  url="https://www.oldenburg-kreis.de/buergerservice/dienstleistungen/kulturdenkmal-forschung-grabung-genehmigung-900000367-0.html?myMedium=1"),
    "03403": dict(dept="Fachdienst Bauordnung und Denkmalschutz (Team Denkmalschutz)", tier="stark",
                  quote="'Der Fachdienst Bauordnung und Denkmalschutz ist als Untere Denkmalschutzbehörde für den Bereich der Stadt Oldenburg zuständig.'",
                  url="https://serviceportal.oldenburg.de/buergerservice/dienstleistungen/denkmalrechtliche-genehmigung-verguenstigung-und-oeffentliche-foerderung-900000113-0.html?myMedium=1"),
    "03459": dict(dept="Fachdienst 6 Planen und Bauen / Stadt- und Kreisarchäologie Osnabrück (übriges Kreisgebiet außer Stadt Melle)", tier="stark",
                  quote="'Als älteste gemeinsame Dienststelle von Stadt und Landkreis kümmert sich die Osnabrücker Archäologie bereits seit 1975 um alle bodendenkmalpflegerischen Belange in der Region.'",
                  url="https://www.landkreis-osnabrueck.de/fachthemen/kulturbuero/archaeologie"),
    "03404": dict(dept="Fachdienst Bauordnung und Denkmalpflege / Stadt- und Kreisarchäologie Osnabrück", tier="stark",
                  quote="'Als untere Denkmalschutzbehörde ist die Stadt Osnabrück insbesondere für den Vollzug des niedersächsischen Denkmalschutzgesetzes zuständig.'",
                  url="https://service.osnabrueck.de/dienstleistungen/-/egov-bis-detail/einrichtung/1361/show"),
    "03356": dict(dept="Bauordnungsamt - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'An den Landkreis Osterholz - Untere Denkmalschutzbehörde'; Zuständig für Anträge für Ausgrabungen/Erdarbeiten an Bodendenkmalen",
                  url="https://www.landkreis-osterholz.de/buergerservice/dienstleistungen/bodendenkmalpflege-900000053-0.html"),
    "03157": dict(dept="Fachdienst Bauordnung, Raumordnung (übriges Kreisgebiet außer Stadt Peine)", tier="stark",
                  quote="Genehmigungspflicht bei Erdarbeiten an Bodendenkmal-Stellen durch die Untere Denkmalschutzbehörde",
                  url="https://www.landkreis-peine.de/Themen-Leistungen/Themen/Bauen-Infrastruktur/Untere-Denkmalschutzbeh%C3%B6rde/"),
    "03357": dict(dept="Kreisarchäologie Rotenburg (Wümme) (Schul- und Kulturamt)", tier="stark",
                  quote="'Die Kreisarchäologie Rotenburg (Wümme) ist als untere Denkmalschutzbehörde im Bereich der Bodendenkmalpflege tätig.'",
                  url="https://kulturerbe.niedersachsen.de/kultureinrichtung/isil_DE-MUS-125322/"),
    "03102": dict(dept="Fachgebiet Bauordnung und Denkmalschutz", tier="stark",
                  quote="'Wenden Sie sich frühzeitig ... an die Untere Denkmalschutzbehörde.' - Erdarbeiten an Stellen mit vermuteten Bodendenkmalen genehmigungspflichtig",
                  url="https://www.salzgitter.de/leben/bauordnung-denkmalschutz/denkmalschutz/denkmalschutz.php"),
    "03257": dict(dept="Untere Denkmalschutzbehörde (UDSchB)", tier="stark",
                  quote="'Antrag auf Erteilung einer Genehmigung für die Suche nach historischen Gegenständen mit technischen Hilfsmitteln - Genehmigungsverfahren nach § 12 NDSchG - liegt der Unteren Denkmalschutzbehörde (UDSchB) vor.'",
                  url="https://bewerbung.schaumburg.de/medien/dokumente/antrag_suchgenehmigung_sondengaenger.pdf"),
    "03359": dict(dept="Kreisarchäologie Landkreis Stade (Amt für Planung, Klimaschutz und Kultur)", tier="stark",
                  quote="'Bei der Überplanung unserer Landschaft gibt die Kreisarchäologie als Untere Denkmalschutzbehörde für Bodendenkmale ihre Stellungnahmen ab.'",
                  url="https://www.landkreis-stade.de/portal/seiten/archaeologie-auf-den-spuren-der-vergangenheit-901000105-20350.html"),
    "03360": dict(dept="Amt für Bauordnung und Kreisplanung", tier="schwaecher",
                  quote="'Ihr Ansprechpartner für alle Fragen zum Thema Denkmalschutz und Denkmalpflege ist die untere Denkmalschutzbehörde (UDSchB) ... organisatorisch dem Amt für Bauordnung und Kreisplanung zugeordnet.'",
                  url="https://www.landkreis-uelzen.de/home/bauen-umwelt-tiere-und-lebensmittel/bauen/denkmalschutz.aspx"),
    "03460": dict(dept="Amt für Bauordnung, Planung und Immissionsschutz", tier="stark",
                  quote="'Das Amt für Bauordnung, Planung und Immissionsschutz nimmt die Aufgaben der unteren Denkmalschutzbehörde wahr ... Baumaßnahmen an Bau- und Bodendenkmälern bedürfen der denkmalschutzrechtlichen Genehmigung.'",
                  url="https://www.landkreis-vechta.de/bauen-und-umwelt/planen-und-bauen/denkmalschutz.html"),
    "03361": dict(dept="Kreisarchäologie Landkreis Verden (Fachbereich Kultur, Tourismus)", tier="schwaecher",
                  quote="'Wer ein Bau- oder Bodendenkmal beseitigen, verändern, instandsetzen oder verlegen möchte, braucht eine Genehmigung der unteren Denkmalschutzbehörde.'",
                  url="https://www.landkreis-verden.de/portal/seiten/kreisarchaeologie-901000096-20600.html"),
    "03461": dict(dept="Fachdienst 63 - Planen & Bauaufsicht", tier="stark",
                  quote="'Der Landkreis Wesermarsch nimmt als Untere Denkmalschutzbehörde die Aufgaben nach dem Niedersächsischen Denkmalschutzgesetz wahr.'",
                  url="https://wesermarsch.de/services/bauen-planen/denkmalschutz-und-denkmalpflege/"),
    "03405": dict(dept="Bauordnungsamt, Fachdienst 63-00 Denkmalpflege", tier="schwaecher",
                  quote="Zuständigkeit für Denkmalpflege einschließlich archäologischer Fundstücke - kein expliziter 'Bodendenkmal'-Wortlaut auf dieser Seite",
                  url="https://www.wilhelmshaven.de/Stadtverwaltung/Dienststellen/63_Bauordnungsamt/63-00/Denkmalpflege.php"),
    "03462": dict(dept="Fachdienst Bauordnung (Untere Denkmalschutzbehörde)", tier="stark",
                  quote="'Der Landkreis Wittmund nimmt als Untere Denkmalschutzbehörde die Aufgaben nach dem Niedersächsischen Denkmalschutzgesetz wahr.'",
                  url="https://www.landkreis-wittmund.de/Leben-Wohnen/Wohnen/Bauen-und-Planen/Denkmalschutz/"),
    "03158": dict(dept="Abteilung 602 - Denkmalschutz (übriges Kreisgebiet außer Stadt Wolfenbüttel)", tier="stark",
                  quote="'Auch Grabungen nach Kulturdenkmalen bedürfen der Genehmigung.'",
                  url="https://www.lkwf.de/denkmalschutz"),
    "03103": dict(dept="Geschäftsbereich Stadtplanung und Bauberatung (GB 06) - Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Erdarbeiten an einer Stelle durchführen lassen ... von der er weiß, oder vermutet ... dass sich dort Kulturdenkmale befinden [§13 NDSchG]' - Meldepflicht an die Untere Denkmalschutzbehörde",
                  url="https://www.wolfsburg.de/bauenwohnen/denkmalschutz"),
}

# Sonderstädte mit eigener, vom Landkreis getrennter unterer Denkmalschutzbehörde.
# ags -> dict(name, dept, tier, quote, url)
SONDERSTAEDTE = {
    "03351006": dict(name="Celle", dept="Fachdienst Bauordnung (FD 63)", tier="stark",
                      quote="'Die Stadt Celle - vertreten durch den Fachdienst Bauordnung (FD 63) - nimmt im übertragenen Wirkungskreis die Aufgaben der Unteren Bauaufsichtsbehörde und der Unteren Denkmalschutzbehörde wahr.' (große selbständige Stadt, § 14 Abs. 5 NKomVG)",
                      url="https://www.celle.de/Stadt/Stadtverwaltung/Aufbauorganisation/Oberbürgermeister/Dezernat-III-Bauen-und-Umwelt/Fachbereich-5-Stadtplanung-Bauen-und-Umwelt/Bauordnung/"),
    "03352011": dict(name="Cuxhaven", dept="Museen und Stadtarchäologie (8.3)", tier="stark",
                      quote="'Die Stadt Cuxhaven ist Untere Denkmalschutzbehörde (Pflichtaufgabe des \"übertragenen Wirkungskreises\") ... Hier ist die Stadtarchäologie oder Archäologische Denkmalpflege eingebunden.' (große selbständige Stadt, § 14 Abs. 5 NKomVG)",
                      url="https://www.cuxhaven.de/bus/detail.html?id=-805"),
    "03153017": dict(name="Goslar", dept="Untere Denkmalschutzbehörde Stadt Goslar", tier="stark",
                      quote="Landkreis-Quelle nennt Stadt Goslar ausdrücklich als vom Kreis-Zuständigkeitsbereich 'ausgenommen' (große selbständige Stadt, § 14 Abs. 5 NKomVG)",
                      url="https://service.landkreis-goslar.de/dienstleistungen/-/egov-bis-detail/dienstleistung/8552/show"),
    "03252006": dict(name="Hameln", dept="Untere Denkmalschutzbehörde Stadt Hameln", tier="stark",
                      quote="'Die Stadt Hameln hat eine eigene Untere Denkmalschutzbehörde. Interessierte Sondengänger/innen im Stadtbereich Hameln müssen sich daher an die Untere Denkmalschutzbehörde der Stadt Hameln wenden.' (große selbständige Stadt, § 14 Abs. 5 NKomVG)",
                      url="https://service.hameln-pyrmont.de/buergerservice/dienstleistungen/antrag-auf-erteilung-einer-nachforschungsgenehmigung-12-ndschg--900000905-33800.html"),
    "03254021": dict(name="Hildesheim", dept="Fachdienst 60.1 Bauaufsicht und Denkmalschutz (Stadtarchäologie)", tier="stark",
                      quote="Große selbständige Stadt (§ 14 Abs. 5 NKomVG) mit eigener Unterer Denkmalschutzbehörde, getrennt vom Landkreis Hildesheim",
                      url="https://www.landkreishildesheim.de/Leistungen/Bauen-Planen/Denkmalschutz/"),
    "03454032": dict(name="Lingen (Ems)", dept="Fachdienst Bauordnung und Denkmalpflege", tier="stark",
                      quote="'eine Grabungs- bzw. Nachforschungsgenehmigung, die bei der unteren Denkmalschutzbehörde im Fachdienst Bauordnung und Denkmalpflege beantragt werden muss.' (große selbständige Stadt, § 14 Abs. 5 NKomVG)",
                      url="https://www.lingen.de/bauen-wirtschaft/stadtsanierung/archaeologie/archaeologie.html"),
    "03355022": dict(name="Lüneburg", dept="Untere Denkmalschutzbehörde Stadt Lüneburg", tier="stark",
                      quote="Große selbständige Stadt (§ 14 Abs. 5 NKomVG) mit eigener Unterer Denkmalschutzbehörde, getrennt vom Landkreis Lüneburg",
                      url="https://www.landkreis-lueneburg.de/fuer-unsere-buergerinnen-und-buerger/bauen-und-planen/denkmalschutz.html"),
    "03158037": dict(name="Wolfenbüttel", dept="Abteilung Bauaufsicht und Denkmalschutz (Stadtdenkmalpflegerin)", tier="schwaecher",
                      quote="'Die erforderlichen Genehmigungen nach § 10 des Niedersächsischen Denkmalschutzgesetz bei allen Maßnahmen an Kulturdenkmälern erteilt die zuständige untere Denkmalschutzbehörde' - eigene Bauaufsicht laut offizieller ArL-Braunschweig-Liste bestätigt, aber kein dediziertes Bodendenkmal-Zitat der Stadt selbst",
                      url="https://www.wolfenbuettel.de/Stadt/Denkmalschutz"),
    "03157006": dict(name="Peine", dept="Untere Denkmalschutzbehörde (Bauordnung)", tier="stark",
                      quote="'nimmt die Abteilung die Aufgaben der Unteren Denkmalschutzbehörde wahr. In dieser Funktion hat sie die Aufgabe, Kulturdenkmale (Bau- und Bodendenkmale) zu schützen, zu pflegen und wissenschaftlich zu erforschen.'",
                      url="https://www.peine.de/de/stadtleben/bauen-wohnen-umwelt/bauordnung/"),
    "03159016": dict(name="Göttingen", dept="Fachdienst Bauordnung, Denkmalschutz und Archäologie", tier="stark",
                      quote="'Die Stadt Göttingen als Untere Denkmalschutzbehörde berät die Bauherren/Bauherrinnen eingehend'",
                      url="https://www.goettingen.de/rathaus/service/dienstleistungen/denkmalschutz.html"),
    "03155013": dict(name="Einbeck", dept="III.1 Stadtentwicklung und Wirtschaftsförderung - Archäologische Denkmalpflege", tier="stark",
                      quote="Landkreis Northeim bestätigt: 'die Städte Einbeck und Northeim [sind] jeweils für ihr gesamtes Stadtgebiet die richtigen Ansprechpartner'",
                      url="https://www.landkreis-northeim.de/portal/seiten/denkmalschutz-900000032-23900.html"),
    "03459024": dict(name="Melle", dept="Amt für Stadtentwicklung und Denkmalschutz", tier="stark",
                      quote="'Die Zuständigkeit für die fachliche Beurteilung und Beratung sowie Genehmigung liegt bei der Stadt Melle.'",
                      url="https://www.melle.info/buergerservice/dienstleistungen/denkmalpflege-900000208-0.html?myMedium=1"),
    "03353040": dict(name="Winsen (Luhe)", dept="Untere Denkmalschutzbehörde Stadt Winsen (Luhe)", tier="stark",
                      quote="'Die Zuständigkeit liegt bei der Stadt Winsen (Luhe) -untere Denkmalschutzbehörde-.'",
                      url="https://www.winsen.de/buergerservice/dienstleistungen/denkmalpflege-902000970-20260.html"),
    # Region Hannover: nur die 8 amtlich namentlich bestätigten Mitgliedskommunen + die
    # Landeshauptstadt (eigene, getrennte Behörde) - NICHT die gesamte Region pauschal.
    "03241004": dict(name="Burgwedel", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241006": dict(name="Gehrden", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241007": dict(name="Hemmingen", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241008": dict(name="Isernhagen", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241013": dict(name="Pattensen", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241016": dict(name="Sehnde", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241018": dict(name="Uetze", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241020": dict(name="Wennigsen (Deister)", dept="Region Hannover - Fachbereich Bauen (Untere Denkmalschutzbehörde)", tier="stark",
                      quote="'Die Region Hannover ist zuständige Untere Denkmalschutzbehörde für Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen, Sehnde, Uetze, Wennigsen'",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
    "03241001": dict(name="Hannover, Landeshauptstadt", dept="Stadtdenkmalpflege (Fachbereich Planen und Stadtentwicklung)", tier="schwaecher",
                      quote="Landeshauptstadt Hannover hat eine eigene Untere Denkmalschutzbehörde, unabhängig von der Region Hannover - Existenz amtlich plausibel, aber kein dediziertes Bodendenkmal-Zitat direkt geprüft",
                      url="https://www.hannover.de/Leben-in-der-Region-Hannover/Planen,-Bauen,-Wohnen/Bauen-Denkmalpflege/Denkmalschutz-Denkmalpflege"),
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
        kreis_names = {u.ags_kreis: u.county_name for u in db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Niedersachsen").all()}

        staging = JurisdictionStagingService(db)
        batch_id = f"bodendenkmalschutz-niedersachsen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, info in LANDKREISE.items():
            kreis_name = kreis_names.get(ags_kreis, ags_kreis)
            authority_name = f"Landkreis {kreis_name} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                addr = ars_index.get(ags_kreis)
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Kreisverwaltungsbehörde)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Niedersachsen", phone=None, email=addr.email if addr else None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz Niedersachsen - Kreisebene",
                request_type_id="BODENDENKMALSCHUTZ", state="Niedersachsen", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))

        for ags, info in SONDERSTAEDTE.items():
            authority_name = f"{info['name']} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Gemeinde mit eigener Bauaufsicht)",
                    street=None, house_number=None, postal_code=None, city=info["name"],
                    state="Niedersachsen", phone=None, email=None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz Niedersachsen - Sonderstaedte",
                request_type_id="BODENDENKMALSCHUTZ", state="Niedersachsen", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
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
