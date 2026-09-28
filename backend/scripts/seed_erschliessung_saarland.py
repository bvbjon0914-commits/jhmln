# -*- coding: utf-8 -*-
"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
SAARLAND - alle 52 Gemeinden (6 Landkreise/Regionalverband: Regionalverband
Saarbruecken, Merzig-Wadern, Neunkirchen, Saarlouis, Saarpfalz-Kreis,
St. Wendel; ags_land='10').

Anders als bei den Gemeindeverwaltungsverband-/Verbandsgemeinde-Wellen (BW,
RLP, Sachsen-Anhalt) gibt es im Saarland KEINE Verwaltungsverband-Struktur,
die Erschliessungsbeitraege buendelt und so mit wenigen Authorities viele
Gemeinden abdecken wuerde: jede der 52 Gemeinden erhebt Erschliessungs-
beitraege eigenstaendig ueber ihr eigenes Bauamt/ihre eigene Bauverwaltung
(vereinzelt abweichend - z. B. Puettlingen ueber den Eigenbetrieb "Techn.
Dienste", Lebach ueber die staedtische Gesellschaft LGG/Stadtwerke Lebach).
Kein Landkreis und auch der Regionalverband Saarbruecken selbst buendeln
diese Aufgabe fuer ihre Mitgliedsgemeinden - das wurde in allen 6 Teil-
recherchen unabhaengig bestaetigt (§ 127 BauGB macht die Erschliessungs-
traegerschaft zu einer originaeren Gemeindeaufgabe).

Datenquelle: sechs unabhaengige Recherche-Durchgaenge (einer je Landkreis/
Regionalverband), jeweils direkt gegen die amtliche .de-Webseite jeder
Gemeinde (Bauamt-/Fachbereichsseiten, "Was erledige ich wo?"-A-Z-
Verzeichnisse, Organigramme, Satzungen) sowie das Land-Saarland-
Serviceportal (service.saarland.de) recherchiert - NIE Wikipedia oder
Aggregatoren (kauperts.de, ortsdienst.de, Immobilienportale) als
Zitatquelle, sondern hoechstens als Rechercheleitfaden vor der Verifikation
an der amtlichen Quelle.

Beleglage ehrlich abgebildet ueber `verification_status` je Gemeinde:
- VERIFIED (19 von 52): die amtliche Quelle bestaetigt woertlich, dass die
  benannte Stelle Erschliessungsbeitraege (oder eine unmittelbar davon
  nicht sinnvoll trennbare Bezeichnung wie "Erschliessungskosten") bearbeitet.
- AUTO_IMPORTED (33 von 52): keine amtliche Seite benennt eine fuer genau
  diese Abgabe zustaendige Stelle woertlich; stattdessen wird das
  naheliegende allgemeine Bauamt/die Gemeindeverwaltung als Fallback
  gefuehrt, ausdruecklich OHNE vorgetaeuschte Spezifitaet.

52 neue Authorities (eine je Gemeinde-Beitragsstelle), 52 neue
MUNICIPALITY-Regeln (ags = jeweilige Gemeinde-AGS, priority=40 - identisch
mit allen bereits bestehenden aktiven ERSCHLIESSUNG-Regeln).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Erschliessungsbeitraege Saarland, Einzelrecherche je Gemeinde)"

FALLBACK_NOTE = (
    "Keine amtliche Seite benennt eine speziell fuer Erschliessungsbeitraege "
    "zustaendige Stelle woertlich; als Fallback wird das zustaendige allgemeine "
    "Bauamt/die Gemeindeverwaltung gefuehrt, ausdruecklich ohne vorgetaeuschte "
    "Spezifitaet - siehe source_url."
)

# AGS -> dict(name, authority_name, authority_type, street, plz, city, phone,
#             email, quote, source_url, verification_status)
# verification_status: "VERIFIED" = amtliche Quelle bestaetigt Zustaendigkeit
# fuer Erschliessungsbeitraege woertlich; "AUTO_IMPORTED" = allgemeiner
# Bauamt-/Gemeindeverwaltungs-Fallback ohne woertliche Bestaetigung fuer
# genau diese Abgabe.
GEMEINDEN = {
    '10041100': dict(
        name='Saarbrücken, Landeshauptstadt', authority_name='Landeshauptstadt Saarbrücken - Amt für Straßenbau und Verkehrsinfrastruktur',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Bahnhofstraße 31', plz='66111', city='Saarbrücken',
        phone='+49 681 905-4007', email='strassenamt@saarbruecken.de',
        quote='ERSCHLIESSUNGS- UND STRASSENAUSBAUBEITRÄGE — Amt für Straßenbau und Verkehrsinfrastruktur',
        source_url='https://www.saarbruecken.de/rathaus/was_erledige_ich_wo/index-e',
        verification_status='VERIFIED',
    ),
    '10041511': dict(
        name='Friedrichsthal, Stadt', authority_name='Stadt Friedrichsthal - Bauamt (Fachbereich IV Bauen und Umwelt)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Schmidtbornstraße 12a', plz='66299', city='Friedrichsthal',
        phone='+49 6897 8568-303', email=None,
        quote=None,
        source_url='https://www.friedrichsthal.de/rathaus-service/service/buergerservice',
        verification_status='AUTO_IMPORTED',
    ),
    '10041512': dict(
        name='Großrosseln', authority_name='Gemeinde Großrosseln - Fachbereich 3 Bauen, Wohnen, Umwelt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Klosterplatz 2', plz='66352', city='Großrosseln',
        phone='+49 6898 449-134', email=None,
        quote=None,
        source_url='https://service.saarland.de',
        verification_status='AUTO_IMPORTED',
    ),
    '10041513': dict(
        name='Heusweiler', authority_name='Gemeinde Heusweiler - Bauverwaltung',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Saarbrücker Straße 35', plz='66265', city='Heusweiler',
        phone='06806 911-125', email=None,
        quote='Erschließungsbeiträge — Ihre Ansprechpartner: Bauverwaltung — Rathaus 2.06 und 2.12 — 06806 911 125, -171 und -105',
        source_url='https://www.heusweiler.de/rathaus-service/buergerservice/buergerdienste-von-a-z/',
        verification_status='VERIFIED',
    ),
    '10041514': dict(
        name='Kleinblittersdorf', authority_name='Gemeinde Kleinblittersdorf - Fachbereich 3 Bauen, Wohnen, Umwelt',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Rathausstraße 16-18', plz='66271', city='Kleinblittersdorf',
        phone='06805 2008-704', email=None,
        quote='Erschließungsbeiträge — 06805 2 008 -704 / -707 — Rathaus, Zimmer 2.6; sowie offizielle Stellenausschreibung Fachbereich 3: "Die Aufgaben umfassen schwerpunktmäßig: ... Abrechnungen im Rahmen des Erschließungs- und Beitragsrecht"',
        source_url='https://www.kleinblittersdorf.de/rathaus-service/was-erledige-ich-wo',
        verification_status='VERIFIED',
    ),
    '10041515': dict(
        name='Püttlingen, Stadt', authority_name='Stadt Püttlingen - Eigenbetrieb "Techn. Dienste" (Fachbereich 6 Technische Dienste, Tiefbau und Abwasser)',
        authority_type='Kommunale Beitragsstelle (Eigenbetrieb der Gemeindeverwaltung)',
        street='In der Schäferei 8', plz='66346', city='Püttlingen',
        phone='06898 691-260', email='stadtverwaltung@puettlingen.de',
        quote='Erschließungsbeiträge — 06898691260 — Eigenbetrieb "Techn. Dienste" (K); Fachbereich 6 – Technische Dienste ... Tiefbau und Abwasser ... zuständig u.a. für "Erschließungsbeiträge" und "Ausbaubeiträge"',
        source_url='https://www.puettlingen.de/rathaus-service/stadtverwaltung/was-erledige-ich-wo',
        verification_status='VERIFIED',
    ),
    '10041516': dict(
        name='Quierschied', authority_name='Gemeinde Quierschied - Gemeindeverwaltung (Rathaus Zimmer 3.05)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Rathausstraße 9', plz='66287', city='Quierschied',
        phone='06897 961-142', email=None,
        quote='Erschließungskosten — 961-142 — Rathaus 3.05 (keine Amtsbezeichnung auf der Seite genannt)',
        source_url='https://www.quierschied.de/rathaus-service/was-erledige-ich-wo',
        verification_status='AUTO_IMPORTED',
    ),
    '10041517': dict(
        name='Riegelsberg', authority_name='Gemeinde Riegelsberg - Bauverwaltung',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Saarbrücker Straße 31', plz='66292', city='Riegelsberg',
        phone='06806 930-156', email='t.sand@riegelsberg.de',
        quote='[Bauverwaltung] ... Erschließungsbeiträge, Sanierungsgenehmigungen, Vorkaufsrecht',
        source_url='https://www.riegelsberg.eu/fragen-antworten/was-erledige-ich-wo/bauverwaltung',
        verification_status='VERIFIED',
    ),
    '10041518': dict(
        name='Sulzbach/Saar, Stadt', authority_name='Stadt Sulzbach/Saar - Bau- und Umweltamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Sulzbachtalstraße 81', plz='66280', city='Sulzbach/Saar',
        phone='+49 6897 508-410', email='bauamt@stadt-sulzbach.de',
        quote=None,
        source_url='https://www.stadt-sulzbach.de/Verwaltung/Ansprechpartner/',
        verification_status='AUTO_IMPORTED',
    ),
    '10041519': dict(
        name='Völklingen, Stadt', authority_name='Stadt Völklingen - Gemeindeverwaltung (Rathaus Zimmer 7.07/7.08)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Rathausplatz', plz='66333', city='Völklingen',
        phone='06898 13-2571', email=None,
        quote='Erschließungsbeiträge — Telefon: 13-2571, 13-2579 — Zimmer Nr.: 7.07, 7.08 (keine Amtsbezeichnung in dieser Zeile; Fachdienst-54-Zuordnung nur über Organigramm erschlossen, nicht direkt bestätigt)',
        source_url='https://www.voelklingen.de/service/rathaus-a-z-was-erledige-ich-wo',
        verification_status='AUTO_IMPORTED',
    ),
    '10042111': dict(
        name='Beckingen', authority_name='Gemeinde Beckingen - Abteilung IV Bauen, Umwelt und Liegenschaften',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Bergstraße 48', plz='66701', city='Beckingen',
        phone='06835/55-0', email=None,
        quote=None,
        source_url='https://www.beckingen.de/rathaus/gemeindeverwaltung/',
        verification_status='AUTO_IMPORTED',
    ),
    '10042112': dict(
        name='Losheim am See', authority_name='Gemeinde Losheim am See - Bürgerdienstleistungszentrum (Zimmer 2.07)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Merziger Straße 3', plz='66679', city='Losheim am See',
        phone='06872 609-145', email=None,
        quote='Erschließungsbeiträge | 2.07 | 06872609-145 (Zeile aus der offiziellen Zuständigkeiten-Tabelle)',
        source_url='https://www.losheim.de/rathaus-service/buergerdienstleistungszentrum/zustaendigkeiten/',
        verification_status='VERIFIED',
    ),
    '10042113': dict(
        name='Merzig, Kreisstadt', authority_name='Kreisstadt Merzig - Fachbereich 313 Tiefbau',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Brauerstraße 5', plz='66663', city='Merzig',
        phone='06861/85-480', email='tiefbau@merzig.de',
        quote=None,
        source_url='https://www.merzig.de/rathaus-buergerservice/dienststellen/stadtentwicklung-bauwesen-und-umwelt/tiefbau/',
        verification_status='AUTO_IMPORTED',
    ),
    '10042114': dict(
        name='Mettlach', authority_name='Gemeinde Mettlach - Fachbereich 2 Bauen und technische Dienste (Bauverwaltung/-planung, Tiefbau)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Freiherr-vom-Stein-Straße 64', plz='66693', city='Mettlach',
        phone='06864/83-0', email=None,
        quote=None,
        source_url='https://www.mettlach.de/wp-content/uploads/Organigramm_Mettlach_04_2025.pdf',
        verification_status='AUTO_IMPORTED',
    ),
    '10042115': dict(
        name='Perl', authority_name='Gemeinde Perl - Abteilung IV.1 Bauverwaltung & technische Dienste, Tiefbau/Straßenbau',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Trierer Straße 28', plz='66706', city='Perl',
        phone='+49 (0) 6867 / 66 143', email='a.becker@perl-mosel.de',
        quote=None,
        source_url='https://perl.saarland/verwaltung.html',
        verification_status='AUTO_IMPORTED',
    ),
    '10042116': dict(
        name='Wadern, Stadt', authority_name='Stadt Wadern - Bauverwaltung (Tiefbau/Stadtplanung, Zi. C104/C204)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Marktplatz 13', plz='66687', city='Wadern',
        phone='06871-507-452', email=None,
        quote='Erschließungskosten | | C204/C104 | 507-456/452 sowie Straßenausbaubeiträge | | C204 | 507-456 (Zeilen aus der offiziellen "Was erledige ich wo"-Tabelle)',
        source_url='https://ssl.wadern.de/c-d-e',
        verification_status='VERIFIED',
    ),
    '10042117': dict(
        name='Weiskirchen', authority_name='Gemeinde Weiskirchen - Bauverwaltung (Klaus Barth)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Kirchenweg 2', plz='66709', city='Weiskirchen',
        phone='06876 709-531', email='bauverwaltung@weiskirchen.de',
        quote='Erschließungsbeiträge / Klaus Barth / 06876 709-531 (Zeile aus der offiziellen "Was erledige ich wo?"-A-Z-Tabelle, Buchstabe E)',
        source_url='https://www.weiskirchen.de/rathaus-service/gemeindeverwaltung/was-erledige-ich-wo',
        verification_status='VERIFIED',
    ),
    '10043111': dict(
        name='Eppelborn', authority_name='Gemeinde Eppelborn - FG 3.01 Baugenehmigungen und Bauverwaltung',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Rathausstraße 27', plz='66571', city='Eppelborn',
        phone='06881/969-252', email=None,
        quote='Erteilung von Ausnahmen/Befreiungen von der Festsetzung eines Bebauungsplans, Bearbeitung von Anträgen auf Verfahrensfreistellung bzw. Genehmigungsfreistellung, Städtebauliche Sanierungsmaßnahmen, Wirtschaftsförderung, Erhebung von Straßenausbau- und Erschließungsbeiträgen, Beschwerdemanagement, Bürgerservice und Regelung von Versicherungsangelegenheiten für den Bereich der öffentlichen Wege und Plätze, Submissionsverfahren',
        source_url='https://www.eppelborn.de/fachgebiete/',
        verification_status='VERIFIED',
    ),
    '10043112': dict(
        name='Illingen', authority_name='Gemeinde Illingen - Technisches Bauamt (FB 3 Bauen und Wohnen)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Hauptstraße 86', plz='66557', city='Illingen',
        phone='06825 409-161', email='bauverwaltung@illingen.de',
        quote=None,
        source_url='https://www.illingen.de/rathaus-und-service/verwaltung/',
        verification_status='AUTO_IMPORTED',
    ),
    '10043113': dict(
        name='Merchweiler', authority_name='Gemeinde Merchweiler - Geschäftsbereich 4 (Bauen, Wohnen, Umwelt)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Hauptstraße 82', plz='66589', city='Merchweiler',
        phone='06825 955-261', email=None,
        quote=None,
        source_url='https://www.merchweiler.de/politik-verwaltung/unsere-verwaltung/',
        verification_status='AUTO_IMPORTED',
    ),
    '10043114': dict(
        name='Neunkirchen, Kreisstadt', authority_name='Kreisstadt Neunkirchen - Abt. 600 Bau- und Friedhofsverwaltung',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Oberer Markt 16', plz='66538', city='Neunkirchen',
        phone='06821/202-680', email=None,
        quote='Erhebung von Erschließungsbeiträgen (BauGB), Straßenausbaubeiträgen, Kanalkostenbeiträgen(KAG) und Ausgleichsbeiträgen (AB)',
        source_url='https://www.neunkirchen.de/index.php?id=2038',
        verification_status='VERIFIED',
    ),
    '10043115': dict(
        name='Ottweiler, Stadt', authority_name='Stadt Ottweiler - Amt 60 Bauverwaltung und Immobilienmanagement',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Goethestraße 13a', plz='66564', city='Ottweiler',
        phone='06824 3008-35', email='bauverwaltung@ottweiler.de',
        quote=None,
        source_url='https://www.ottweiler.de/rathaus-service/rathaus/aemter/',
        verification_status='AUTO_IMPORTED',
    ),
    '10043116': dict(
        name='Schiffweiler', authority_name='Gemeinde Schiffweiler - Bau- und Umweltamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Rathausstraße 7-11', plz='66578', city='Schiffweiler',
        phone='06821 678-24', email=None,
        quote=None,
        source_url='https://www.schiffweiler.de/rathaus-service/wegweiser-und-dienstleistungen/bauen-und-sanieren',
        verification_status='AUTO_IMPORTED',
    ),
    '10043117': dict(
        name='Spiesen-Elversberg', authority_name='Gemeinde Spiesen-Elversberg - Abt. IV Bau- und Umweltamt/Bauverwaltung',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Hauptstraße 116', plz='66583', city='Spiesen-Elversberg',
        phone='06821 791-221', email='bauamt-verwaltung@spiesen-elversberg.de',
        quote=None,
        source_url='https://www.spiesen-elversberg.de/kontakt/',
        verification_status='AUTO_IMPORTED',
    ),
    '10044111': dict(
        name='Dillingen/Saar, Stadt', authority_name='Stadt Dillingen/Saar - Bauamt',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Merziger Straße', plz='66763', city='Dillingen/Saar',
        phone='06831 709-280', email='bauamt@dillingen-saar.de',
        quote='Erschließungsbeiträge/Gehwegausbaubeiträge — Bauamt, Telefon: 06831 709-280, E-Mail: bauamt@dillingen-saar.de',
        source_url='https://www.dillingen-saar.de/rathaus/wo-finde-ich-was/',
        verification_status='VERIFIED',
    ),
    '10044112': dict(
        name='Lebach, Stadt', authority_name='Stadt Lebach - LGG (Lebacher Grundstücksgesellschaft, c/o Stadtwerke Lebach)',
        authority_type='Kommunale Beitragsstelle (städtische Gesellschaft)',
        street=None, plz=None, city='Lebach',
        phone='06881 96167-22', email='info@stadtwerke-lebach.de',
        quote='Erschließungsbeiträge / LGG / 96167 -22 / info@stadtwerke-lebach.de (Zeile aus der offiziellen A-Z-Dienstleistungstabelle)',
        source_url='https://www.lebach.de/buergerservice/dienstleistungen-a-z',
        verification_status='VERIFIED',
    ),
    '10044113': dict(
        name='Nalbach', authority_name='Gemeinde Nalbach - Amt IV Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Rathausplatz 1', plz='66809', city='Nalbach',
        phone='06838 9002-160', email='bauamt@nalbach.de',
        quote=None,
        source_url='https://www.nalbach.de/buergerservice/wegweiser-a-z',
        verification_status='AUTO_IMPORTED',
    ),
    '10044114': dict(
        name='Rehlingen-Siersburg', authority_name='Gemeinde Rehlingen-Siersburg - Abteilung Nachhaltige Entwicklung und Bauordnungswesen',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Bouzonviller Platz', plz='66780', city='Rehlingen-Siersburg',
        phone='06835 508-415', email='liegenschaften@rehlingen-siersburg.de',
        quote='Erschließungsbeiträge — Abteilung Nachhaltige Entwicklung und Bauordnungswesen — 06835 508-415 / -414 — liegenschaften@rehlingen-siersburg.de',
        source_url='https://www.rehlingen-siersburg.de/service/buergerservice',
        verification_status='VERIFIED',
    ),
    '10044115': dict(
        name='Saarlouis, Kreisstadt', authority_name='Kreisstadt Saarlouis - Amt für Tiefbauwesen und Vermessung (Amt 66)',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Großer Markt 1', plz='66740', city='Saarlouis',
        phone='06831/443-296', email='amtsleiter66@saarlouis.de',
        quote=None,
        source_url='https://www.saarlouis.de/rathaus/stadtverwaltung/amter/amt-fur-tiefbauwesen-und-vermessung/',
        verification_status='AUTO_IMPORTED',
    ),
    '10044116': dict(
        name='Saarwellingen', authority_name='Gemeinde Saarwellingen - Amt 60 Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Schloßplatz 1', plz='66793', city='Saarwellingen',
        phone='06838 9007-140', email=None,
        quote=None,
        source_url='https://www.saarwellingen.de/fileadmin/user_upload/1_Rathaus_und_Buergerdienste/Service_und_Info/Ortsrechtsammlung/Bauverwaltung/Erschliessungsbeitragssatzung.pdf',
        verification_status='AUTO_IMPORTED',
    ),
    '10044117': dict(
        name='Schmelz', authority_name='Gemeinde Schmelz - Fachbereich 4 Bauen (Roman Weber)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Rathausplatz 1', plz='66839', city='Schmelz',
        phone='06887/301-112', email=None,
        quote='Roman Weber / 06887/301-112 / 1.09 / Erschließungs- und Ausbaubeiträge (Aufgabenzeile: Zuschusswesen, Erschließungsbeiträge, Ausbaubeiträge)',
        source_url='https://www.schmelz.de/rathaus-verwaltung/fachbereiche/fb-4-bauen',
        verification_status='VERIFIED',
    ),
    '10044118': dict(
        name='Schwalbach', authority_name='Gemeinde Schwalbach - Fachbereich 4 Bauen, Wohnen, Umwelt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Hauptstraße 92', plz='66773', city='Schwalbach',
        phone='06834 5710', email=None,
        quote=None,
        source_url='https://www.schwalbach-saar.de/de/rathaus-politik/gemeindeverwaltung/fachbereiche/fachbereich-4/',
        verification_status='AUTO_IMPORTED',
    ),
    '10044119': dict(
        name='Überherrn', authority_name='Gemeinde Überherrn - Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Rathausstraße 101', plz='66802', city='Überherrn',
        phone='06836 909-129', email='bauamt@ueberherrn.de',
        quote=None,
        source_url='https://ueberherrn.de/rathaus/was-erledige-ich-wo/',
        verification_status='AUTO_IMPORTED',
    ),
    '10044120': dict(
        name='Wadgassen', authority_name='Gemeinde Wadgassen - Bauamt / Kämmerei-Steueramt',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung, verwandte Beitragsart bestätigt)',
        street='Lindenstraße 114', plz='66787', city='Wadgassen',
        phone='06834 944-0', email='info@wadgassen.de',
        quote='Für Fragen zur Grundstücksangelegenheit (Größe und Berechnung) wenden Sie sich an die Mitarbeiter/innen des Bauamtes. Für Fragen zur Eigentümerangelegenheit (als Beitragspflichtiger)... oder zur Satzung... an die Mitarbeiter/innen der Kämmerei – Steueramt. (Quelle betrifft "Wiederkehrende Beiträge", eine verwandte, aber von klassischen Erschließungsbeiträgen § 127ff BauGB zu unterscheidende KAG-Beitragsart; nicht wortwörtlich für Erschließungsbeiträge bestätigt.)',
        source_url='https://www.wadgassen.de/Rathaus/buergerservice/Wiederkehrende-Beitraege',
        verification_status='AUTO_IMPORTED',
    ),
    '10044121': dict(
        name='Wallerfangen', authority_name='Gemeinde Wallerfangen - Bauordnung',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Fabrikplatz', plz='66798', city='Wallerfangen',
        phone='06831 6809-31', email=None,
        quote=None,
        source_url='https://www.wallerfangen.de/rathaus/ansprechpartner/',
        verification_status='AUTO_IMPORTED',
    ),
    '10044122': dict(
        name='Bous', authority_name='Gemeinde Bous - Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Saarbrücker Straße 120', plz='66359', city='Bous',
        phone='06834 83-230', email=None,
        quote=None,
        source_url='https://service.saarland.de',
        verification_status='AUTO_IMPORTED',
    ),
    '10044123': dict(
        name='Ensdorf', authority_name='Gemeinde Ensdorf - Fachbereich III Bauverwaltung, Liegenschaften',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Provinzialstraße 101a', plz='66806', city='Ensdorf',
        phone='06831 504-151', email='bauamt@gemeinde-ensdorf.de',
        quote=None,
        source_url='https://www.gemeinde-ensdorf.de/Rathaus-Service/B%C3%BCrgerservice/Was-erledige-ich-wo-/Bauverwaltung.php',
        verification_status='AUTO_IMPORTED',
    ),
    '10045111': dict(
        name='Bexbach, Stadt', authority_name='Stadt Bexbach - Stadtentwicklung (Rathaus II)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Rathaus II', plz='66450', city='Bexbach',
        phone='06826 529 200', email='stadtentwicklung@bexbach.de',
        quote='Erschließungsbeiträge / Gebäude/Zimmer Nr.: Rathaus II / Telefon: 06826 529200 / E-Mail: stadtentwicklung@bexbach.de',
        source_url='https://www.bexbach.de/rathaus/verwaltung/was-erledige-ich-wo',
        verification_status='VERIFIED',
    ),
    '10045112': dict(
        name='Blieskastel, Stadt', authority_name='Stadt Blieskastel - Rathaus II Zimmer 215 (Erschließungsbeiträge)',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Rathaus II', plz='66440', city='Blieskastel',
        phone='06842 926-1200', email='tobias.kohl@blieskastel.de',
        quote='Erschließungsbeiträge / Zimmer Nr.: 215 / Telefon: 06842 926-1200 / Email: tobias.kohl@blieskastel.de',
        source_url='https://www.blieskastel.de/rathaus/buerger-info/was-erledige-ich-wo',
        verification_status='VERIFIED',
    ),
    '10045113': dict(
        name='Gersheim', authority_name='Gemeinde Gersheim - Abteilung IV Bauen, Umwelt, Verkehr',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street=None, plz='66453', city='Gersheim',
        phone=None, email=None,
        quote=None,
        source_url='https://gersheim.de/anliegen/bautraege/',
        verification_status='AUTO_IMPORTED',
    ),
    '10045114': dict(
        name='Homburg, Kreisstadt', authority_name='Kreisstadt Homburg - Kämmerei, Sachgebiet Gebühren und Beiträge',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Am Forum 5', plz='66424', city='Homburg',
        phone='06841 101 309', email='kaemmerei@homburg.de',
        quote='Erschließungsbeiträge (gelistet unter Sachgebiet Gebühren und Beiträge der Kämmerei)',
        source_url='https://www.homburg.de/rathaus/stadtverwaltung/amter/kammerei/',
        verification_status='VERIFIED',
    ),
    '10045115': dict(
        name='Kirkel', authority_name='Gemeinde Kirkel - Fachbereich 3 Bauen und Umwelt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Hauptstraße 10', plz='66459', city='Kirkel',
        phone='+49 6841 8098-35', email=None,
        quote=None,
        source_url='https://service.saarland.de/detail?ouId=100081388&infotype=1',
        verification_status='AUTO_IMPORTED',
    ),
    '10045116': dict(
        name='Mandelbachtal', authority_name='Gemeinde Mandelbachtal - Fachbereich 3 Bauen, Umwelt, Technische Dienste',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Theo-Carlen-Platz 2', plz='66399', city='Mandelbachtal',
        phone='06893 8090', email=None,
        quote='Dedizierte Leistungsseite "Erschließungsbeiträge", Ansprechpartner: Fachbereich 3: Bauen, Umwelt, Technische Dienste, Theo-Carlen-Platz 2, 66399 Mandelbachtal',
        source_url='https://www.mandelbachtal.de/dienstleistung/anzeigen/id/34956/erschlie%C3%9Fungsbeitr%C3%A4ge.html',
        verification_status='VERIFIED',
    ),
    '10045117': dict(
        name='St. Ingbert, Stadt', authority_name='Stadt St. Ingbert - Geschäftsbereich 6 Stadtentwicklung, Umwelt u. Bauen',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Am Markt 12', plz='66386', city='St. Ingbert',
        phone='+49 6894 13-330', email='stadtundbauen@st-ingbert.de',
        quote=None,
        source_url='https://www.st-ingbert.de/rathaus/stadtverwaltung/geschaeftsbereiche/stadtentwicklung-umwelt-bauen/',
        verification_status='AUTO_IMPORTED',
    ),
    '10046111': dict(
        name='Freisen', authority_name='Gemeinde Freisen - Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Schulstraße 60', plz='66629', city='Freisen',
        phone='06855/9729', email='rathaus@freisen.de',
        quote='Für nähere Informationen wenden Sie sich bitte an Frau Lucille Alles, vom Bauamt, unter der Durchwahl 06855/9729. (Kontext: gemeindliche Grundstücksverkäufe inkl. Erschließungskosten/Ablösebetrag, keine formale Zuständigkeitsseite für die Beitragsart selbst.)',
        source_url='https://www.freisen.de/bauen-wohnen-umwelt/',
        verification_status='AUTO_IMPORTED',
    ),
    '10046112': dict(
        name='Marpingen', authority_name='Gemeinde Marpingen - Gemeindeverwaltung (Bauamt/Rathaus)',
        authority_type='Bauamt (Gemeindeverwaltung, eigene Satzung bestätigt)',
        street='Urexweilerstraße 11', plz='66646', city='Marpingen',
        phone='+49 6853 9116 0', email=None,
        quote='Die Gemeinde Marpingen erhebt Erschließungsbeiträge nach den Vorschriften des Baugesetzbuches (§§ 127 ff) sowie nach Maßgabe dieser Satzung. (§1, Satzung über die Erhebung von Erschließungsbeiträgen innerhalb der Gemeinde Marpingen, i.d.F. v. 05.02.1994; kein internes Fachamt namentlich benannt.)',
        source_url='https://marpingen.de/wp-content/uploads/2023/07/Erschiessungsbeitragssatzungrechtsrkraeftig.pdf',
        verification_status='AUTO_IMPORTED',
    ),
    '10046113': dict(
        name='Namborn', authority_name='Gemeinde Namborn - Gemeindeverwaltung',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street=None, plz=None, city='Namborn',
        phone='06857 90030', email='rathaus@namborn.de',
        quote=None,
        source_url='https://www.namborn.de/Verwaltung-Politik/Verwaltung/Was-erledige-ich-wo-/',
        verification_status='AUTO_IMPORTED',
    ),
    '10046114': dict(
        name='Nohfelden', authority_name='Gemeinde Nohfelden - Gemeindeverwaltung',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='An der Burg', plz='66625', city='Nohfelden',
        phone='(0 68 52) 885-0', email='info@nohfelden.de',
        quote='Für Rückfragen bzgl. zum Verkauf stehender gemeindlicher Grundstücke, Kaufpreisen, Erschließungskosten usw. steht Ihnen v. g. Ansprechpartner/-in zur Verfügung. (betrifft gemeindliche Grundstücksverkäufe, nicht eindeutig die allgemeine §127ff BauGB-Beitragserhebung.)',
        source_url='https://www.nohfelden.de/rathaus-service/',
        verification_status='AUTO_IMPORTED',
    ),
    '10046115': dict(
        name='Nonnweiler', authority_name='Gemeinde Nonnweiler - Fachbereich IV Technische Dienste, Bauen, Wohnen und Verkehr',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Trierer Straße 5', plz='66620', city='Nonnweiler',
        phone='06873/660-0', email='rathaus@nonnweiler.de',
        quote=None,
        source_url='https://www.nonnweiler.de/rathaus-gemeinde/verwaltung/fachbereich-iv-technische-dienste-bauen-wohnen-und-verkehr/',
        verification_status='AUTO_IMPORTED',
    ),
    '10046116': dict(
        name='Oberthal', authority_name='Gemeinde Oberthal - Fachbereich 4.1 Allgemeine Bauverwaltung, Bauleitplanung',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Poststraße 20', plz='66649', city='Oberthal',
        phone='+49 6854 9017-40', email='rathaus@oberthal.de',
        quote=None,
        source_url='https://service.saarland.de/detail?ouId=100087972',
        verification_status='AUTO_IMPORTED',
    ),
    '10046117': dict(
        name='St. Wendel, Kreisstadt', authority_name='Kreisstadt St. Wendel - Stadtbauamt, Abteilung Bauverwaltung',
        authority_type='Kommunale Beitragsstelle (Gemeindeverwaltung)',
        street='Marienstraße 20', plz='66606', city='St. Wendel',
        phone='06851/809-1924', email='stadtbauamt@sankt-wendel.de',
        quote='Bauverwaltung (Erschließungsbeiträge, Kanalkostenbeiträge, Ausbaubeiträge, Ablösung von Stellplätzen, Genehmigungsfreistellung gem. § 63 LBO)',
        source_url='https://www.sankt-wendel.de/buergerservice-rathaus/planen-bauen/',
        verification_status='VERIFIED',
    ),
    '10046118': dict(
        name='Tholey', authority_name='Gemeinde Tholey - Bauamt',
        authority_type='Bauamt (Gemeindeverwaltung, allgemeiner Fallback)',
        street='Im Kloster 1', plz='66636', city='Tholey',
        phone='(06853) 508-0', email='gemeinde@tholey.de',
        quote=None,
        source_url='https://www.tholey.de/bauen/',
        verification_status='AUTO_IMPORTED',
    ),
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
        batch_id = f"erschliessung-saarland-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags, info in GEMEINDEN.items():
            authority = db.query(Authority).filter(Authority.authority_name == info["authority_name"]).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["authority_name"],
                    authority_type=info["authority_type"],
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Saarland", phone=info["phone"], email=info["email"],
                    source="Recherche-Sitzung 2026-09-28 (amtliche Gemeinde-Webseite bzw. service.saarland.de, "
                           "siehe jurisdictions.source_url der zugehörigen Regel)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            quote = info["quote"] or FALLBACK_NOTE
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Erschliessung Saarland - {info['name']}",
                request_type_id="ERSCHLIESSUNG", state="Saarland", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{info['authority_name']} — {quote}",
                source_url=info["source_url"],
                source_license=(
                    "Kommunale Webseite (amtliche Gemeinde-/Stadtverwaltung, Recherche-Sitzung 2026-09-28)"
                    if info["verification_status"] == "VERIFIED"
                    else "Kommunale Webseite (allgemeiner Bauamt-/Gemeindeverwaltungs-Fallback, "
                         "Recherche-Sitzung 2026-09-28)"
                ),
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info, quote))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(GEMEINDEN)} Gemeinden.")
        conflicts = [(e, i, q) for (e, i, q) in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c, _, _ in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        verified_count = 0
        auto_imported_count = 0
        for entry, info, quote in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=quote,
                resulting_verification_status=info["verification_status"],
            )
            approved += 1
            if info["verification_status"] == "VERIFIED":
                verified_count += 1
            else:
                auto_imported_count += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben (VERIFIED={verified_count}, AUTO_IMPORTED={auto_imported_count}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
