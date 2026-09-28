"""
KATASTER (amtliches Liegenschaftskataster) - zweite Welle, 90 der 91
nach Bayern/RLP/SH bundesweit noch offenen Landkreise/kreisfreien
Städte. Sechs parallele Recherche-Agenten (5 Detail-Batches + 1
Kleinstlücken-Batch) deckten dabei sechs unterschiedliche
Organisationsmuster ab:

- SACHSEN-ANHALT: zentral beim Landesamt für Vermessung und
  Geoinformation (LVermGeo), 4 "Geokompetenz-Center" (Magdeburg,
  Stendal, Dessau-Roßlau, Halle), jeweils mehrere Landkreise gemeinsam.
  Wörtlich per Live-Abruf der offiziellen Zuständigkeitstabelle
  verifiziert - alle 10 Kreise "stark".
- NIEDERSACHSEN: Landesamt für Geoinformation und Landesvermessung
  (LGLN), organisiert in Regionaldirektionen mit einzelnen
  Katasterämtern je (Kreis-)Stadt. Das LGLN befindet sich aktuell
  (2025/2026) in einer laufenden Standortreform (mehrere Katasterämter
  wurden erst wenige Tage/Wochen vor dieser Recherche zusammengelegt) -
  es wurden die JEWEILS AKTUELLEN Zuständigkeiten nach den bereits
  vollzogenen Fusionen verwendet. 6 Kreise "stark" (explizite
  Pressemitteilung/Amtsseite nennt den Kreis wörtlich), 12 "schwächer"
  (Zuordnung über Amtssitz-Ort = Kreisstadt, keine wörtliche
  Kreis-Nennung auf einer offiziellen Seite gefunden).
- BADEN-WÜRTTEMBERG / SAARLAND / MECKLENBURG-VORPOMMERN: in BW führt
  jeder Land-/Stadtkreis sein Kataster selbst (untere
  Vermessungsbehörde), im Saarland ist es zentral beim Landesamt für
  Vermessung, Geoinformation und Landentwicklung (LVGL) mit einer
  "Zentralen Außenstelle" in Saarlouis (landesweite gesetzliche
  Zuständigkeit ohne Kreis-Ausnahme, § 2 Abs. 2 SVermKatG - daher
  "schwächer", da kein Kreisname wörtlich genannt wird), in MV bei den
  jeweiligen unteren Vermessungs- und Geoinformationsbehörden
  (Landkreis/kreisfreie Stadt, laut offizieller LAiV-M-V-Liste).
- HESSEN: Hessische Verwaltung für Bodenmanagement und Geoinformation
  (HVBG), 7 "Ämter für Bodenmanagement" (ÄfB), jedes für mehrere
  Landkreise. 24 von 26 Kreisen "stark" (wörtliches Amtszitat), 2
  "schwächer": Stadt Kassel (nur Sekundärquelle) und der Sonderfall AGS
  06415 = Hanau, das zum 1.1.2026 per "Hanau-Auskreisungsgesetz" aus
  dem Main-Kinzig-Kreis als 6. kreisfreie Stadt Hessens ausgegliedert
  wurde (Gesetz unabhängig verifiziert; das Kataster bleibt laut
  Sekundärquelle weiterhin beim AfB Büdingen). WICHTIG: zum Zeitpunkt
  dieser Recherche gibt es in der Datenbank noch KEINE Gebäude mit
  AGS 06415 oder mit Main-Kinzig-Kreis-AGS und Stadt Hanau - die neue
  Kreisfreiheit hat also aktuell noch keine Auswirkung auf bestehende
  Zuordnungen, ist aber für künftige Datenimporte zu beachten.
- THÜRINGEN: Thüringer Landesamt für Bodenmanagement und Geoinformation
  (TLBG), 8 Zweigstellen, jede für mehrere Kreisstädte. Die
  Zuordnung wurde über den amtlichen "Zuständigkeitsfinder" je
  Kreisstadt ermittelt (technisch ortsbezogen, nicht wörtlich
  kreisbezogen) - als "stark" eingestuft, da die Zuordnung amtlich
  und eindeutig ist.
- NRW/SACHSEN (Kleinstlücken): 2 einzelne kreisfreie Städte in NRW
  (Mülheim an der Ruhr, Solingen - eigenes städtisches Amt), Landkreis
  Leipzig + Stadt Leipzig in Sachsen (jeweils eigenes Vermessungsamt).
  HAMBURG stellte sich als Scheinlücke heraus: die reine COUNTY-Suche
  hatte eine bereits bestehende, aber nur als MUNICIPALITY (statt
  COUNTY) klassifizierte AUTO_IMPORTED-Regel ("Katasteramt Hamburg")
  übersehen, die wegen ihrer höheren Prioritätsstufe ohnehin vor jeder
  neuen COUNTY/STATE-Regel gegriffen hätte - eine neue Regel wäre toter
  Code gewesen und wurde daher NICHT angelegt (die vom Agenten
  gefundene, besser belegte LGV-Quelle bleibt als Verbesserungsidee für
  eine spätere, gezielte Qualitäts-Aktualisierung der bestehenden Regel
  festgehalten, aber nicht Teil dieser NO_MATCH-fokussierten Welle).
  BERLIN bleibt bewusst offen bzw. ungeändert: es existieren bereits 12
  bezirkliche MUNICIPALITY-Regeln (vermutlich aus einer früheren
  Sitzung), die wegen fehlender Bezirks-Granularität in den
  Gebäudedaten alle gleichzeitig zutreffen und daher korrekt
  MULTIPLE_MATCHES statt eines falschen Einzeltreffers ergeben -
  derselbe strukturelle Engpass wie beim bereits dokumentierten
  Berlin-Fall bei BODENDENKMALSCHUTZ.

Von den 90 ursprünglich als fehlend identifizierten Kreisen erwiesen
sich 9 als Scheinlücken (Freiburg, Stadtkreis Heilbronn, Stadtkreis
Karlsruhe, Oldenburg-Stadt, Osnabrück-Stadt, Rostock-Stadt, Mülheim an
der Ruhr, Solingen, Leipzig-Stadt, Hamburg) - jeweils bereits über eine
bestehende, höher priorisierte MUNICIPALITY-Regel abgedeckt, die eine
neue COUNTY/STATE-Regel wirkungslos gemacht hätte. Zusätzlich wurde
dabei ein Datenfehler im ersten Entwurf dieses Skripts gefunden und
korrigiert: die AGS von Stadtkreis und Landkreis Heilbronn (08121 vs.
08125) bzw. Stadtkreis und Landkreis Karlsruhe (08212 vs. 08215) waren
vertauscht (Verwechslung von "Heilbronn"/"Karlsruhe" als county_name
ohne Kreis-/Stadt-Unterscheidung) - richtiggestellt anhand der
tatsächlichen Gemeinde-Anzahl je AGS in AdministrativeUnit.

Damit bleiben netto 80 neue COUNTY-Regeln - 1 Fall (Berlin) bleibt
strukturell unklar (MULTIPLE_MATCHES statt eines geratenen
Einzeltreffers). 0 Konflikte erwartet (alle Ziel-Kreise waren zuvor
komplett ohne Kataster-Regel).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, 6 parallele Recherche-Agenten, Kataster Welle 2)"

# ags_kreis -> dict(authority_name, dept, street, postal_code, city, email, tier, quote, url)
# Mehrere ags_kreis koennen dieselbe authority_name teilen (regionale Aemter).
KREISE = {
    # --- Sachsen-Anhalt: LVermGeo, 4 Standorte ---
    "15081": dict(auth="LVermGeo Sachsen-Anhalt - Standort Stendal", street="Scharnhorststraße 89", plz="39576", city="Stendal",
                  email="poststelle.stendal.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Die Zuständigkeitsbezirke gliedern sich wie folgt: Standort Stendal ... Altmarkkreis Salzwedel Landkreis Jerichower Land Landkreis Stendal'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15086": dict(auth="LVermGeo Sachsen-Anhalt - Standort Stendal", street="Scharnhorststraße 89", plz="39576", city="Stendal",
                  email="poststelle.stendal.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Die Zuständigkeitsbezirke gliedern sich wie folgt: Standort Stendal ... Altmarkkreis Salzwedel Landkreis Jerichower Land Landkreis Stendal'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15082": dict(auth="LVermGeo Sachsen-Anhalt - Standort Dessau-Roßlau", street="Kühnauer Straße 164 a-b", plz="06846", city="Dessau-Roßlau",
                  email="poststelle.dessau-rosslau.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Die Zuständigkeitsbezirke gliedern sich wie folgt: Standort Dessau-Roßlau ... Landkreis Anhalt-Bitterfeld Landkreis Wittenberg kreisfreie Stadt Dessau-Roßlau'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15091": dict(auth="LVermGeo Sachsen-Anhalt - Standort Dessau-Roßlau", street="Kühnauer Straße 164 a-b", plz="06846", city="Dessau-Roßlau",
                  email="poststelle.dessau-rosslau.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Die Zuständigkeitsbezirke gliedern sich wie folgt: Standort Dessau-Roßlau ... Landkreis Anhalt-Bitterfeld Landkreis Wittenberg kreisfreie Stadt Dessau-Roßlau'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15084": dict(auth="LVermGeo Sachsen-Anhalt - Standort Halle (Saale)", street="Neustädter Passage 15", plz="06122", city="Halle (Saale)",
                  email="poststelle.halle.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Halle (Saale) ... Burgenlandkreis Saalekreis Landkreis Mansfeld-Südharz kreisfreie Stadt Halle (Saale)'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15088": dict(auth="LVermGeo Sachsen-Anhalt - Standort Halle (Saale)", street="Neustädter Passage 15", plz="06122", city="Halle (Saale)",
                  email="poststelle.halle.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Halle (Saale) ... Burgenlandkreis Saalekreis Landkreis Mansfeld-Südharz kreisfreie Stadt Halle (Saale)'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15087": dict(auth="LVermGeo Sachsen-Anhalt - Standort Halle (Saale)", street="Neustädter Passage 15", plz="06122", city="Halle (Saale)",
                  email="poststelle.halle.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Halle (Saale) ... Burgenlandkreis Saalekreis Landkreis Mansfeld-Südharz kreisfreie Stadt Halle (Saale)'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15083": dict(auth="LVermGeo Sachsen-Anhalt - Standort Magdeburg", street="Otto-von-Guericke-Straße 15", plz="39104", city="Magdeburg",
                  email="poststelle.magdeburg.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Magdeburg Landkreis Börde Landkreis Harz Salzlandkreis kreisfreie Stadt Magdeburg'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15085": dict(auth="LVermGeo Sachsen-Anhalt - Standort Magdeburg", street="Otto-von-Guericke-Straße 15", plz="39104", city="Magdeburg",
                  email="poststelle.magdeburg.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Magdeburg Landkreis Börde Landkreis Harz Salzlandkreis kreisfreie Stadt Magdeburg'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),
    "15089": dict(auth="LVermGeo Sachsen-Anhalt - Standort Magdeburg", street="Otto-von-Guericke-Straße 15", plz="39104", city="Magdeburg",
                  email="poststelle.magdeburg.lvermgeo@sachsen-anhalt.de", tier="stark",
                  quote="'Standort Magdeburg Landkreis Börde Landkreis Harz Salzlandkreis kreisfreie Stadt Magdeburg'",
                  url="https://www.lvermgeo.sachsen-anhalt.de/de/gdp-organisation.html"),

    # --- Niedersachsen: LGLN, diverse Katasteraemter ---
    "03451": dict(auth="LGLN - Katasteramt Westerstede", street="Wilhelm-Geiler-Straße 11", plz="26655", city="Westerstede",
                   email="Katasteramt-WST@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Katasteramt Westerstede als eines der Katasterämter der RD Oldenburg-Cloppenburg; Landkreis Ammerland nur in Sekundärquellen als Zuständigkeitsgebiet genannt",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_oldenburg_cloppenburg/katasteramt_westerstede/katasteramt-westerstede-51059.html"),
    "03352": dict(auth="LGLN - Katasteramt Otterndorf", street="Am Großen Specken 7", plz="21762", city="Otterndorf",
                   email=None, tier="stark",
                   quote="'Behörde für Geoinformation, Landentwicklung und Liegenschaften Otterndorf - Katasteramt Otterndorf / Landkreis Cuxhaven' (Telefonverzeichnis Landkreis Cuxhaven)",
                   url="https://www.landkreis-cuxhaven.de/Quicknavigation/Kontakt/Telefonverzeichnis/Beh%C3%B6rde-f%C3%BCr-Geoinformation-Landentwicklung-und-Liegenschaften-Otterndorf-Katasteramt-Otterndorf.php"),
    "03251": dict(auth="LGLN - Katasteramt Sulingen", street="Galtener Str. 16", plz="27232", city="Sulingen",
                   email="katasteramt-sul@lgln.niedersachsen.de", tier="stark",
                   quote="'LGLN ... Regionaldirektion Sulingen-Verden, Katasteramt Sulingen' (Behördennavigator Landkreis Diepholz)",
                   url="https://navigator.diepholz.de/inhaltsverzeichnis/details/poi-5000230-21790-LGLN_Landesamt_fuer_Geoinformation_und_Landvermessung_Niedersachsen_-_Regionaldirektion_Sulingen-Verden,_Katasteramt_Sulingen.html"),
    "03454": dict(auth="LGLN - Katasteramt Meppen", street="Obergerichtsstr. 18", plz="49716", city="Meppen",
                   email="katasteramt-mep@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz Meppen (Landkreis Emsland) und Zugehoerigkeit zur RD Osnabrueck-Meppen, keine woertliche Kreis-Nennung gefunden",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_osnabruck_meppen/katasteramt_meppen/katasteramt-meppen-218999.html"),
    "03455": dict(auth="LGLN - Katasteramt Varel", street="Oldenburger Straße 4", plz="26316", city="Varel",
                   email="katasteramt-var@lgln.niedersachsen.de", tier="stark",
                   quote="'Der Standort Wilhelmshaven verlor ... die Gemeinden Wangerooge, Wangerland, Jever, Schortens und Sande des heutigen Landkreises Friesland an das Katasteramt in Varel.'",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/presse_amp_broschuren/katasteramter-wilhelmshaven-und-varel-werden-zusammengelegt-246538.html"),
    "03456": dict(auth="LGLN - Katasteramt Nordhorn", street="Schilfstraße 6", plz="48529", city="Nordhorn",
                   email="katasteramt-noh@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz Nordhorn (Kreisstadt der Grafschaft Bentheim), keine woertliche Kreis-Nennung auf offizieller Seite gefunden",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_osnabruck_meppen/katasteramt_nordhorn/katasteramt-nordhorn-51205.html"),
    "03252": dict(auth="LGLN - Katasteramt Hameln", street="Falkestraße 11", plz="31785", city="Hameln",
                   email="katasteramt-hm@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz Hameln (Kreisstadt Hameln-Pyrmont), keine woertliche Kreis-Nennung auf offizieller Seite gefunden",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_hameln_hannover/katasteramt_hameln/katasteramt-hameln-51091.html"),
    "03353": dict(auth="LGLN - Katasteramt Winsen (Luhe)", street="Von-Somnitz-Ring 3", plz="21423", city="Winsen (Luhe)",
                   email="Katasteramt-WL@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Landkreis-Harburg-Seite verweist nur allgemein auf 'das oertlich zustaendige Katasteramt des LGLN'; Zuordnung ueber Amtssitz Winsen (Luhe) = Kreisstadt",
                   url="https://www.landkreis-harburg.de/buergerservice/dienstleistungen/liegenschaftskataster-auskunft-amtliche-grenzauskunft-einholen-901002524-0.html"),
    "03358": dict(auth="LGLN - Katasteramt Soltau", street="Birkenstraße 15", plz="29614", city="Soltau",
                   email=None, tier="stark",
                   quote="'Beschlossen wurde jetzt, dass alle Anfragen und Auskünfte für Bürgerinnen und Bürger im Landkreis Heidekreis bereits ab dem 1. Januar 2026 vom Katasteramt Soltau aus erledigt werden.'",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/presse_amp_broschuren/katasteramt-fallingbostel-schliesst-zum-1-januar-2026-die-tur-247244.html"),
    "03354": dict(auth="LGLN - Katasteramt Lüchow", street="Seerauer Straße 42", plz="29439", city="Lüchow",
                   email="Katasteramt-lUE@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz Luechow (Kreisstadt Luechow-Dannenberg), keine woertliche Kreis-Nennung auf offizieller Seite gefunden",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_luneburg/katasteramt_luchow/katasteramt-luchow-51099.html"),
    "03458": dict(auth="LGLN - Katasteramt Oldenburg", street="Stau 3", plz="26122", city="Oldenburg (Oldb)",
                   email="Katasteramt-OL@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Landkreis Oldenburg verweist per Serviceseite auf das LGLN-Katasterkartensystem, keine woertliche Amtsnennung extrahiert",
                   url="https://www.oldenburg-kreis.de/buergerservice/dienstleistungen/katasterkarten-online-900002246-0.html"),
    # HINWEIS: Oldenburg-Stadt (03403) und Osnabrück-Stadt (03404) wurden
    # NICHT gestaged - beide kreisfreien Städte haben bereits eine
    # bestehende (höher priorisierte) MUNICIPALITY-Regel; nur der jeweilige
    # LANDKREIS (03458 Oldenburg, 03459 Osnabrück) ist eine echte Lücke.
    "03459": dict(auth="LGLN - Katasteramt Osnabrück", street="Mercatorstraße 4 und 6", plz="49080", city="Osnabrück",
                   email="katasteramt-os@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz Osnabrueck und Bestaetigung, dass das Amt sowohl Stadt als auch Landkreis Osnabrueck bedient",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_osnabruck_meppen/katasteramt_osnabruck/katasteramt-osnabruck-50989.html"),
    "03356": dict(auth="LGLN - Katasteramt Osterholz-Scharmbeck", street="Pappstraße 4", plz="27711", city="Osterholz-Scharmbeck",
                   email="katasteramt-ohz@lgln.niedersachsen.de", tier="schwaecher",
                   quote="'Katasterämter Osterholz und Rotenburg' als Kurzbezeichnung auf offizieller LGLN-RD-Otterndorf-Seite, keine woertliche Kreis-Nennung",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_otterndorf/regionaldirektion-otterndorf-101419.html"),
    "03241": dict(auth="LGLN - Katasteramt Hannover", street="Dorfstraße 19", plz="30519", city="Hannover",
                   email="postfach-hm-h@lgln.niedersachsen.de", tier="schwaecher",
                   quote="Zuordnung ueber Amtssitz und RD-Beschreibung, keine woertliche Nennung 'Region Hannover' gefunden",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/organisation_amp_kontakt/rd_hameln_hannover/katasteramt_hannover/katasteramt-hannover-51050.html"),
    "03257": dict(auth="LGLN - Katasteramt Hameln", street="Falkestraße 11", plz="31785", city="Hameln",
                   email="katasteramt-hm@lgln.niedersachsen.de", tier="stark",
                   quote="'Ab dem 21. September 2026 werden alle Bürgerinnen und Bürger des Landkreises Schaumburg durch das Katasteramt Hameln betreut.'",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/presse_amp_broschuren/katasteramt-rinteln-schliesst-und-zieht-nach-hameln-253476.html"),
    "03461": dict(auth="LGLN - Katasteramt Oldenburg", street="Stau 3", plz="26122", city="Oldenburg (Oldb)",
                   email="Katasteramt-OL@lgln.niedersachsen.de", tier="stark",
                   quote="'Und das Katasteramt Oldenburg ist nicht zuletzt zukünftig Ansprechpartner für die Bürgerinnen und Bürger des Landkreises Wesermarsch.'",
                   url="https://www.lgln.niedersachsen.de/startseite/wir_uber_uns_amp_organisation/presse_amp_broschuren/katasteramt-brake-schliesst-nach-150-jahren-247742.html"),

    # --- Baden-Wuerttemberg: eigene Aemter pro Kreis ---
    # HINWEIS: Freiburg (08311), Stadtkreis Heilbronn (08121) und Stadtkreis
    # Karlsruhe (08212) wurden NICHT gestaged, obwohl der Agent sie belegt
    # hat - eine Pruefung ergab, dass fuer diese drei kreisfreien Staedte
    # bereits bestehende MUNICIPALITY-Regeln existieren (aeltere, generisch
    # importierte Eintraege), die wegen hoeherer Prioritaet ohnehin vor
    # jeder neuen COUNTY-Regel greifen wuerden - eine neue Regel waere toter
    # Code gewesen. Nur die tatsaechlich offenen LANDKREISE (Heilbronn und
    # Karlsruhe, jeweils mit vielen Gemeinden, KEINE eigene
    # MUNICIPALITY-Abdeckung) werden ergaenzt.
    "08125": dict(auth="Landratsamt Heilbronn - Vermessungsamt", street="Lerchenstraße 40", plz="74072", city="Heilbronn",
                   email="Vermessungsamt@landratsamt-heilbronn.de", tier="stark",
                   quote="'Die Ergebnisse fließen in das landesweit einheitliche Liegenschaftskataster ein, dessen Fortführung ... zu den Hauptaufgaben des Vermessungsamtes gehören.'",
                   url="https://www.landkreis-heilbronn.de/vermessungsamt.5366.htm"),
    "08215": dict(auth="Landratsamt Karlsruhe - Amt für Vermessung, Geoinformation und Flurneuordnung", street="Kriegsstraße 100", plz="76133", city="Karlsruhe",
                   email="vermessung@landratsamt-karlsruhe.de", tier="stark",
                   quote="Aufgabenbereich 'Führung des Liegenschaftskatasters'; 'Das Liegenschaftskataster stellt den einzigen flächendeckenden und aktuellen Nachweis der Flurstücke dar.'",
                   url="https://www.landkreis-karlsruhe.de/Service-Verwaltung/Verwaltung/Dezernate-%C3%84mter/Umwelt-Technik/Amt-f%C3%BCr-Vermessung-Geoinformation-und-Flurneuordnung/"),

    # --- Saarland: zentral beim LVGL ---
    "10042": dict(auth="LVGL Saarland - Zentrale Außenstelle (Katasteramt)", street="Kaibelstraße 4-6", plz="66740", city="Saarlouis",
                   email="poststelle.zas@lvgl.saarland.de", tier="schwaecher",
                   quote="§ 2 Abs. 2 SVermKatG: 'obliegen die Landesvermessung und die Führung des Liegenschaftskatasters dem Landesamt für Kataster-, Vermessungs- und Kartenwesen' (landesweit, ohne Kreis-Ausnahme)",
                   url="https://www.saarland.de/lvgl/DE/themen-aufgaben/themen/kataster/kataster_node.html"),
    "10041": dict(auth="LVGL Saarland - Zentrale Außenstelle (Katasteramt)", street="Kaibelstraße 4-6", plz="66740", city="Saarlouis",
                   email="poststelle.zas@lvgl.saarland.de", tier="schwaecher",
                   quote="§ 2 Abs. 2 SVermKatG: 'obliegen die Landesvermessung und die Führung des Liegenschaftskatasters dem Landesamt für Kataster-, Vermessungs- und Kartenwesen' (landesweit, ohne Kreis-Ausnahme)",
                   url="https://www.saarland.de/lvgl/DE/themen-aufgaben/themen/kataster/kataster_node.html"),
    "10045": dict(auth="LVGL Saarland - Zentrale Außenstelle (Katasteramt)", street="Kaibelstraße 4-6", plz="66740", city="Saarlouis",
                   email="poststelle.zas@lvgl.saarland.de", tier="schwaecher",
                   quote="§ 2 Abs. 2 SVermKatG: 'obliegen die Landesvermessung und die Führung des Liegenschaftskatasters dem Landesamt für Kataster-, Vermessungs- und Kartenwesen' (landesweit, ohne Kreis-Ausnahme)",
                   url="https://www.saarland.de/lvgl/DE/themen-aufgaben/themen/kataster/kataster_node.html"),

    # --- Mecklenburg-Vorpommern ---
    "13072": dict(auth="Landkreis Rostock - Kataster- und Vermessungsamt", street="August-Bebel-Straße 3", plz="18209", city="Bad Doberan",
                   email="Katasteramt@Lkros.de", tier="stark",
                   quote="Offizielle Liste des LAiV M-V: 'Landkreis Rostock / Kataster- und Vermessungsamt - Der Landrat - / August-Bebel-Straße 3 / 18209 Bad Doberan'",
                   url="https://www.laiv-mv.de/Geoinformation/katasteraemter%E2%80%93mv/"),
    # HINWEIS: Rostock-Stadt (13003) wurde NICHT gestaged - bereits eine
    # bestehende (höher priorisierte) MUNICIPALITY-Regel vorhanden.
    "13004": dict(auth="Landkreis Ludwigslust-Parchim - Fachdienst Vermessung und Geoinformation (auch für Landeshauptstadt Schwerin)", street="Garnisonsstraße 1", plz="19288", city="Ludwigslust",
                   email="FD62@kreis-lup.de", tier="stark",
                   quote="'Der Landrat des Landkreises Ludwigslust-Parchim als untere Vermessungs- und Geoinformationsbehörde des Landkreises Ludwigslust-Parchim und der Landeshauptstadt Schwerin'",
                   url="https://www.laiv-mv.de/Geoinformation/katasteraemter%E2%80%93mv/"),

    # --- Hessen: 7 Aemter fuer Bodenmanagement ---
    "06431": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'the districts of Bergstraße, Darmstadt-Dieburg, Groß-Gerau, Offenbach and Odenwaldkreis'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-heppenheim"),
    "06411": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'This office serves the following regions: Darmstadt (city), Landkreis Bergstraße, Landkreis Darmstadt-Dieburg, Landkreis Groß-Gerau, Landkreis Odenwaldkreis, Landkreis Offenbach, and Offenbach am Main (city).'",
                   url="https://verwaltungsportal.hessen.de/behoerde?org_id=L100001_9718920"),
    "06432": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'the districts of Bergstraße, Darmstadt-Dieburg, Groß-Gerau, Offenbach and Odenwaldkreis'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-heppenheim"),
    "06412": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'Der Zuständigkeitsbereich des Amtes für Bodenmanagement Limburg a. d. Lahn ... erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06531": dict(auth="Amt für Bodenmanagement Marburg", street="Robert-Koch-Straße 17", plz="35037", city="Marburg",
                   email="info.afb-marburg@hvbg.hessen.de", tier="stark",
                   quote="'die Landkreise Gießen, Marburg-Biedenkopf und des Lahn-Dill-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-marburg"),
    "06433": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'the districts of Bergstraße, Darmstadt-Dieburg, Groß-Gerau, Offenbach and Odenwaldkreis'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-heppenheim"),
    "06632": dict(auth="Amt für Bodenmanagement Homberg (Efze)", street="Hans-Scholl-Straße 6", plz="34576", city="Homberg (Efze)",
                   email="info.afb-homberg@hvbg.hessen.de", tier="stark",
                   quote="'Landkreises Hersfeld-Rotenburg, des Schwalm-Eder-Kreises und des Werra-Meißner-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-homberg-efze"),
    "06434": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06633": dict(auth="Amt für Bodenmanagement Korbach", street="Medebacher Landstraße 27", plz="34497", city="Korbach",
                   email="info.afb-korbach@hvbg.hessen.de", tier="stark",
                   quote="'den Bereich der Landkreise Kassel und Waldeck-Frankenberg'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-korbach"),
    "06611": dict(auth="Amt für Bodenmanagement Korbach", street="Medebacher Landstraße 27", plz="34497", city="Korbach",
                   email="info.afb-korbach@hvbg.hessen.de", tier="schwaecher",
                   quote="'jurisdiction extends to the Waldeck-Frankenberg district, the Kassel district, and the city of Kassel' (Aggregator-Zusammenfassung, keine wörtliche Amtsformulierung mit Stadt Kassel gefunden)",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-korbach"),
    "06532": dict(auth="Amt für Bodenmanagement Marburg", street="Robert-Koch-Straße 17", plz="35037", city="Marburg",
                   email="info.afb-marburg@hvbg.hessen.de", tier="stark",
                   quote="'die Landkreise Gießen, Marburg-Biedenkopf und des Lahn-Dill-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-marburg"),
    "06533": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06435": dict(auth="Amt für Bodenmanagement Büdingen", street="Bahnhofstraße 33", plz="63654", city="Büdingen",
                   email="info.afb-buedingen@hvbg.hessen.de", tier="stark",
                   quote="'den Bereich des Main-Kinzig-Kreises und des Wetteraukreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-buedingen"),
    "06436": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06534": dict(auth="Amt für Bodenmanagement Marburg", street="Robert-Koch-Straße 17", plz="35037", city="Marburg",
                   email="info.afb-marburg@hvbg.hessen.de", tier="stark",
                   quote="'die Landkreise Gießen, Marburg-Biedenkopf und des Lahn-Dill-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-marburg"),
    "06437": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'the districts of Bergstraße, Darmstadt-Dieburg, Groß-Gerau, Offenbach and Odenwaldkreis'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-heppenheim"),
    "06438": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'This office serves the following regions: ... Landkreis Offenbach, and Offenbach am Main (city).'",
                   url="https://verwaltungsportal.hessen.de/behoerde?org_id=L100001_9718920"),
    "06413": dict(auth="Amt für Bodenmanagement Heppenheim", street="Odenwaldstraße 6", plz="64646", city="Heppenheim",
                   email="info.afb-heppenheim@hvbg.hessen.de", tier="stark",
                   quote="'This office serves the following regions: ... Landkreis Offenbach, and Offenbach am Main (city).'",
                   url="https://verwaltungsportal.hessen.de/behoerde?org_id=L100001_9718920"),
    "06439": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06634": dict(auth="Amt für Bodenmanagement Homberg (Efze)", street="Hans-Scholl-Straße 6", plz="34576", city="Homberg (Efze)",
                   email="info.afb-homberg@hvbg.hessen.de", tier="stark",
                   quote="'Landkreises Hersfeld-Rotenburg, des Schwalm-Eder-Kreises und des Werra-Meißner-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-homberg-efze"),
    "06535": dict(auth="Amt für Bodenmanagement Fulda", street="Washingtonallee 1", plz="36041", city="Fulda",
                   email="info.afb-fulda@hvbg.hessen.de", tier="stark",
                   quote="'Der Zuständigkeitsbereich des AfB Fulda umfasst den Vogelsbergkreis und den Landkreis Fulda.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-fulda"),
    "06635": dict(auth="Amt für Bodenmanagement Korbach", street="Medebacher Landstraße 27", plz="34497", city="Korbach",
                   email="info.afb-korbach@hvbg.hessen.de", tier="stark",
                   quote="'den Bereich der Landkreise Kassel und Waldeck-Frankenberg'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-korbach"),
    "06636": dict(auth="Amt für Bodenmanagement Homberg (Efze)", street="Hans-Scholl-Straße 6", plz="34576", city="Homberg (Efze)",
                   email="info.afb-homberg@hvbg.hessen.de", tier="stark",
                   quote="'Landkreises Hersfeld-Rotenburg, des Schwalm-Eder-Kreises und des Werra-Meißner-Kreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-homberg-efze"),
    "06440": dict(auth="Amt für Bodenmanagement Büdingen", street="Bahnhofstraße 33", plz="63654", city="Büdingen",
                   email="info.afb-buedingen@hvbg.hessen.de", tier="stark",
                   quote="'den Bereich des Main-Kinzig-Kreises und des Wetteraukreises'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-buedingen"),
    "06414": dict(auth="Amt für Bodenmanagement Limburg a. d. Lahn", street="Berner Straße 11", plz="65552", city="Limburg a. d. Lahn",
                   email="info.afb-limburg@hvbg.hessen.de", tier="stark",
                   quote="'erstreckt sich auf den Landkreis Limburg-Weilburg, den Rheingau-Taunus-Kreis, den Hochtaunuskreis, den Main-Taunus-Kreis und die Städte Wiesbaden und Frankfurt am Main.'",
                   url="https://hvbg.hessen.de/ueber-uns/dienststellen/amt-fuer-bodenmanagement-limburg-a-d-lahn"),
    "06415": dict(auth="Amt für Bodenmanagement Büdingen", street="Bahnhofstraße 33", plz="63654", city="Büdingen",
                   email="info.afb-buedingen@hvbg.hessen.de", tier="schwaecher",
                   quote="Hanau (AGS 06415) wurde zum 1.1.2026 per Hanau-Auskreisungsgesetz aus dem Main-Kinzig-Kreis ausgegliedert (unabhängig verifiziert); Kataster bleibt laut Sekundärquelle weiterhin beim AfB Büdingen - keine woertliche Landesbehoerden-Bestaetigung gefunden",
                   url="https://innen.hessen.de/presse/gesetz-ueber-die-ausgliederung-hanaus-aus-dem-main-kinzig-kreis-beschlossen"),

    # --- Thueringen: TLBG, 8 Zweigstellen ---
    "16077": dict(auth="TLBG - Zweigstelle Zeulenroda-Triebes", street="Heinrich-Heine-Straße 41", plz="07937", city="Zeulenroda-Triebes",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Zeulenroda-Triebes' fuer Ort Altenburg",
                   url="https://buerger.thueringen.de/detail?areaId=13004&pstId=729511"),
    "16061": dict(auth="TLBG - Zweigstelle Leinefelde-Worbis", street="Franz-Weinrich-Straße 24", plz="37339", city="Leinefelde-Worbis",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Leinefelde-Worbis' fuer Ort Heilbad Heiligenstadt",
                   url="https://buerger.thueringen.de/detail?areaId=12284&pstId=729511"),
    "16052": dict(auth="TLBG - Zweigstelle Zeulenroda-Triebes", street="Heinrich-Heine-Straße 41", plz="07937", city="Zeulenroda-Triebes",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Zeulenroda-Triebes' fuer Ort Gera",
                   url="https://buerger.thueringen.de/detail?areaId=13068&pstId=729511&ouId=868752"),
    "16076": dict(auth="TLBG - Zweigstelle Zeulenroda-Triebes", street="Heinrich-Heine-Straße 41", plz="07937", city="Zeulenroda-Triebes",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Zeulenroda-Triebes' fuer Ort Greiz",
                   url="https://buerger.thueringen.de/detail?areaId=11955&pstId=729511"),
    "16069": dict(auth="TLBG - Zweigstelle Schmalkalden", street="Hoffnung 30", plz="98574", city="Schmalkalden",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Schmalkalden' fuer Ort Hildburghausen",
                   url="https://buerger.thueringen.de/detail?areaId=12749&pstId=729511"),
    "16070": dict(auth="TLBG - Zweigstelle Saalfeld", street="Albrecht-Dürer-Straße 3", plz="07318", city="Saalfeld/Saale",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Saalfeld' fuer Ort Arnstadt",
                   url="https://buerger.thueringen.de/detail?areaId=14124&pstId=729511"),
    "16053": dict(auth="TLBG - Zweigstelle Pößneck", street="Rosa-Luxemburg-Straße 7", plz="07381", city="Pößneck",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Pößneck' fuer Ort Jena",
                   url="https://buerger.thueringen.de/detail?areaId=12803&pstId=729511"),
    "16065": dict(auth="TLBG - Zweigstelle Artern", street="Alte Poststraße 10", plz="06556", city="Artern",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Artern' fuer Ort Sondershausen",
                   url="https://buerger.thueringen.de/detail?areaId=13462&pstId=729511&ouId=866691"),
    "16062": dict(auth="TLBG - Zweigstelle Artern", street="Alte Poststraße 10", plz="06556", city="Artern",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Artern' fuer Ort Nordhausen",
                   url="https://buerger.thueringen.de/detail?areaId=14025&pstId=729511&ouId=866691"),
    "16074": dict(auth="TLBG - Zweigstelle Pößneck", street="Rosa-Luxemburg-Straße 7", plz="07381", city="Pößneck",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Pößneck' fuer Ort Eisenberg",
                   url="https://buerger.thueringen.de/detail?areaId=12452&pstId=729511"),
    "16075": dict(auth="TLBG - Zweigstelle Pößneck", street="Rosa-Luxemburg-Straße 7", plz="07381", city="Pößneck",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Pößneck' fuer Ort Schleiz",
                   url="https://buerger.thueringen.de/detail?areaId=13656&pstId=729511"),
    "16073": dict(auth="TLBG - Zweigstelle Saalfeld", street="Albrecht-Dürer-Straße 3", plz="07318", city="Saalfeld/Saale",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Saalfeld' fuer Ort Saalfeld/Saale",
                   url="https://buerger.thueringen.de/detail?areaId=13188&pstId=729511"),
    "16066": dict(auth="TLBG - Zweigstelle Schmalkalden", street="Hoffnung 30", plz="98574", city="Schmalkalden",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Schmalkalden' fuer Ort Meiningen",
                   url="https://buerger.thueringen.de/detail?areaId=13806&pstId=729511&ouId=868712"),
    "16072": dict(auth="TLBG - Zweigstelle Saalfeld", street="Albrecht-Dürer-Straße 3", plz="07318", city="Saalfeld/Saale",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Saalfeld' fuer Ort Sonneberg",
                   url="https://buerger.thueringen.de/detail?areaId=11742&pstId=729511"),
    "16054": dict(auth="TLBG - Zweigstelle Schmalkalden", street="Hoffnung 30", plz="98574", city="Schmalkalden",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Schmalkalden' fuer Ort Suhl",
                   url="https://buerger.thueringen.de/detail?areaId=13132&pstId=729511&ouId=868712"),
    "16068": dict(auth="TLBG - Zweigstelle Erfurt", street="Hohenwindenstraße 14", plz="99086", city="Erfurt",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Erfurt' fuer Ort Sömmerda",
                   url="https://buerger.thueringen.de/detail?areaId=12630&pstId=729511"),
    "16064": dict(auth="TLBG - Zweigstelle Leinefelde-Worbis", street="Franz-Weinrich-Straße 24", plz="37339", city="Leinefelde-Worbis",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Leinefelde-Worbis' fuer Ort Mühlhausen/Thüringen",
                   url="https://buerger.thueringen.de/detail?areaId=12101&pstId=729511&ouId=868725"),
    "16063": dict(auth="TLBG - Zweigstelle Gotha", street="Schloßberg 1", plz="99867", city="Gotha",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Gotha' fuer Ort Bad Salzungen",
                   url="https://buerger.thueringen.de/detail?areaId=14390&pstId=729511"),
    "16055": dict(auth="TLBG - Zweigstelle Erfurt", street="Hohenwindenstraße 14", plz="99086", city="Erfurt",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Erfurt' fuer Ort Weimar",
                   url="https://buerger.thueringen.de/detail?areaId=13117&pstId=729511&ouId=866677"),
    "16071": dict(auth="TLBG - Zweigstelle Erfurt", street="Hohenwindenstraße 14", plz="99086", city="Erfurt",
                   email="kataster@tlbg.thueringen.de", tier="stark",
                   quote="Amtlicher Zustaendigkeitsfinder Thueringen: 'TLBG - Zweigstelle Erfurt' fuer Ort Apolda",
                   url="https://buerger.thueringen.de/detail?areaId=13857&pstId=729511&ouId=866677"),

    # --- Kleinstluecken: Sachsen ---
    # HINWEIS: Mülheim an der Ruhr (05117), Solingen (05122) und
    # Leipzig-Stadt (14713) wurden NICHT gestaged - alle drei haben
    # bereits eine bestehende (höher priorisierte) MUNICIPALITY-Regel;
    # nur der Landkreis Leipzig ist eine echte Lücke.
    "14729": dict(auth="Landratsamt Landkreis Leipzig - Vermessungsamt", street="Stauffenbergstraße 4", plz="04552", city="Borna",
                   email=None, tier="stark",
                   quote="'Im Freistaat Sachsen gibt es 13 untere Vermessungsbehörden (10 Landkreise und 3 Kreisfreie Städte). Die unteren Vermessungsbehörden sind für die Führung der Daten des Liegenschaftskatasters ihres Gebietes ... zuständig.' (Landkreis Leipzig namentlich gelistet)",
                   url="https://geosn.sachsen.de/untere-vermessungsbehoerden-4549.html"),
}

STATE_BY_AGS_PREFIX = {
    "15": "Sachsen-Anhalt", "03": "Niedersachsen", "08": "Baden-Württemberg",
    "10": "Saarland", "13": "Mecklenburg-Vorpommern", "06": "Hessen",
    "16": "Thüringen", "05": "Nordrhein-Westfalen", "14": "Sachsen",
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
        batch_id = f"kataster-welle2-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, info in KREISE.items():
            authority = db.query(Authority).filter(Authority.authority_name == info["auth"]).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["auth"],
                    authority_type="Untere/zentrale Katasterbehörde",
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state=STATE_BY_AGS_PREFIX[ags_kreis[:2]], phone=None, email=info["email"],
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {info['auth']}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Kataster Welle 2",
                request_type_id="KATASTER", state=STATE_BY_AGS_PREFIX[ags_kreis[:2]], ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{info['auth']} - {info['quote']}", source_url=info["url"],
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
