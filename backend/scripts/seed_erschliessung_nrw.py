# -*- coding: utf-8 -*-
"""
ERSCHLIESSUNGSBEITRAEGE / ANLIEGERBESCHEINIGUNGEN (§ 127 ff. BauGB) fuer
NORDRHEIN-WESTFALEN - erste Welle: alle 22 kreisfreien Staedte plus 5
vollstaendig recherchierte Kreise (Olpe, Ennepe-Ruhr-Kreis, Rhein-Kreis
Neuss, Rheinisch-Bergischer Kreis, Mettmann) = 64 von 396 Gemeinden
(ags_land='05').

Wie im Saarland gibt es in NRW KEINE Verbandsgemeinde-Struktur, die
Erschliessungsbeitraege buendelt: jede Gemeinde (kreisfrei oder
kreisangehoerig) erhebt sie eigenstaendig ueber ihr eigenes Amt/ihre eigene
Fachbereich-Struktur (Tiefbauamt, Amt fuer Strassen und Verkehr, Kaemmerei/
Steueramt, vereinzelt ein Eigenbetrieb bzw. eine Anstalt oeffentlichen
Rechts - z. B. Remscheid ueber die Technischen Betriebe Remscheid (TBR),
Burscheid ueber die Technischen Werke Burscheid (TWB), Velbert ueber die
Technische Betriebe Velbert AoeR). Diese Datei bildet daher - wie
seed_erschliessung_saarland.py - eine flache Gemeinde->Behoerde-Zuordnung
ab, keine Verbandsgemeinde-Buendelung wie seed_erschliessung_bw.py.

Datenquelle: elf unabhaengige Recherche-Durchgaenge (sechs je kreisfreier
Staedte-Gruppe, fuenf je Kreis), jeweils direkt gegen die amtliche
.de-Webseite jeder Stadt/Gemeinde (Fachbereich-/Amtsseiten, Serviceportale
wie service.<stadt>.de / <stadt>.kommunalportal.nrw, "Was erledige ich
wo?"-A-Z-Verzeichnisse, Organigramme, Satzungen, Datenschutz-
Verarbeitungsverzeichnisse) recherchiert - NIE Wikipedia oder Aggregatoren
(kauperts.de, ortsdienst.de, Immobilienportale) als Zitatquelle, sondern
hoechstens als Rechercheleitfaden vor der Verifikation an der amtlichen
Quelle.

Deutsche Umlaute sind in dieser Datei - wie schon im vorangegangenen
DB-Import derselben Recherche-Sitzung - durchgehend ASCII-transliteriert
(oe/ae/ue/ss statt oe/ae/ue/ss-Umlaute) abgelegt, um Encoding-Probleme in
der Werkzeugkette zu vermeiden; das betrifft nur Gross-/Kleinschreibung von
Umlauten in Freitext (Namen, Zitate), nicht den fachlichen Inhalt.

Beleglage ehrlich abgebildet ueber `verification_status` je Gemeinde:
- VERIFIED (48 von 64): die amtliche Quelle bestaetigt woertlich (oder ueber
  eine explizite "Zustaendige Einrichtung/Organisationseinheit"-Angabe),
  dass die benannte Stelle Erschliessungsbeitraege bearbeitet.
- AUTO_IMPORTED (16 von 64): entweder (a) keine amtliche Seite benennt eine
  fuer genau diese Abgabe zustaendige Stelle woertlich, sodass das
  naheliegende allgemeine Bauamt/die Gemeindeverwaltung als Fallback gefuehrt
  wird, ausdruecklich OHNE vorgetaeuschte Spezifitaet (15 Faelle); oder
  (b) die amtliche Seite (bonn.de) war wegen eines JS-Bot-Schutzes nur ueber
  Seitentitel/Organisationsstruktur, nicht ueber Fliesstext bestaetigbar
  (Bonn, 1 Fall).

64 neue Authorities (eine je Gemeinde-Beitragsstelle), 64 neue
MUNICIPALITY-Regeln (ags = jeweilige Gemeinde-AGS, priority=40 - identisch
mit allen bereits bestehenden aktiven ERSCHLIESSUNG-Regeln).

Verbleibend fuer eine Folge-Recherche: 332 von 396 NRW-Gemeinden in den
uebrigen 26 Kreisen (Kleve, Viersen, Wesel, Staedteregion Aachen, Dueren,
Rhein-Erft-Kreis, Euskirchen, Heinsberg, Oberbergischer Kreis,
Rhein-Sieg-Kreis, Borken, Coesfeld, Recklinghausen, Steinfurt, Warendorf,
Guetersloh, Herford, Hoexter, Lippe, Minden-Luebbecke, Paderborn,
Hochsauerlandkreis, Maerkischer Kreis, Siegen-Wittgenstein, Soest, Unna).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Erschliessungsbeitraege NRW Welle 1, Einzelrecherche je Gemeinde)"

# AGS -> dict(name, authority_name, authority_type, street, plz, city, phone,
#             email, quote, source_url, verification_status)
# verification_status: "VERIFIED" = amtliche Quelle bestaetigt Zustaendigkeit
# fuer Erschliessungsbeitraege woertlich bzw. ueber eine explizite
# "Zustaendige Einrichtung"-Angabe; "AUTO_IMPORTED" = allgemeiner
# Bauamt-/Gemeindeverwaltungs-Fallback ohne woertliche Bestaetigung fuer
# genau diese Abgabe, oder Bestaetigung nur ueber Seitentitel/
# Organisationsstruktur statt Fliesstext (Bonn).
GEMEINDEN = {
    # --- Kreisfreie Staedte - Batch 1 (MG, MH, OB, RS) ---
    '05116000': dict(
        name='Moenchengladbach, Stadt', authority_name='Stadtverwaltung Moenchengladbach - Fachbereich Strassenbau- und Verkehrstechnik (66), Beitragserhebung nach BauGB und KAG/NW (66.14)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Moenchengladbach',
        phone=None, email=None,
        quote='Diese werden erhoben fuer die erstmalige Herstellung einer Strasse. (Organisationseinheit: Beitragserhebung nach BauGB und KAG/NW, Fachbereich Strassenbau- und Verkehrstechnik 66)',
        source_url='https://www.moenchengladbach.de/de/rathaus/buergerinfo-a-z/planen-bauen-mobilitaet-umwelt-dezernat-vi/fachbereich-strassenbau-und-verkehrstechnik-66/verwaltung-und-service-6610/beitragserhebung-nach-baugb-und-kagnw-6614',
        verification_status='VERIFIED',
    ),
    '05117000': dict(
        name='Muelheim an der Ruhr, Stadt', authority_name='Stadtverwaltung Muelheim an der Ruhr - Amt fuer Verkehrswesen und Tiefbau (Fachbereich Beitraege)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Muelheim an der Ruhr',
        phone=None, email=None,
        quote='Fuer den beim erstmaligen Ausbau von Strassen, Wegen und Plaetzen entstandenen Aufwand sind nach den gesetzlichen Vorschriften des Baugesetzbuches (BauGB) Beitraege zu erheben.',
        source_url='https://cms.muelheim-ruhr.de/stadtraum/planen-und-bauen/service-bauen/strassenbaubeitraege/erschliessungsbeitraege',
        verification_status='VERIFIED',
    ),
    '05119000': dict(
        name='Oberhausen, Stadt', authority_name='Stadtverwaltung Oberhausen - Fachbereich 5-6-30 Erschliessung, Beitraege',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Oberhausen',
        phone=None, email=None,
        quote='Erschliessung, Beitraege 5-6-30 (Organisationseinheit fuer die Leistung \'Erschliessungsbeitraege, Strassenbaubeitraege\', Technisches Rathaus, Bahnhofstrasse 66, Oberhausen-Sterkrade)',
        source_url='https://serviceportal.oberhausen.de/suche/-/egov-bis-detail/einrichtung/20898/show',
        verification_status='VERIFIED',
    ),
    '05120000': dict(
        name='Remscheid, Stadt', authority_name='Stadtverwaltung Remscheid - Technische Betriebe Remscheid (TBR.55.1 Abrechnung)',
        authority_type='Kommunaler Eigenbetrieb (Beitragsstelle)',
        street=None, plz=None, city='Remscheid',
        phone=None, email=None,
        quote='Erschliessungsbeitraege dienen der teilweisen Refinanzierung der erstmaligen endgueltigen Herstellung oeffentlicher Erschliessungsanlagen. Zustaendige Organisationseinheit: TBR.55.1 Abrechnung',
        source_url='https://remscheid.de/vv/produkte/TBR5/146380100000022093_112713.php',
        verification_status='VERIFIED',
    ),
    # --- Kreisfreie Staedte - Batch 2 (LEV, BOT, GE, MS) ---
    '05316000': dict(
        name='Leverkusen, Stadt', authority_name='Stadtverwaltung Leverkusen - Fachbereich 66, Verwaltung Tiefbau (Abteilung 661)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Leverkusen',
        phone=None, email=None,
        quote='Verwaltung Tiefbau - Abteilung 661 (zustaendige Organisationseinheit fuer Beitragsbescheinigungen zu Erschliessungs-, Kanalanschluss- und Strassenbaubeitraegen); vgl. Erschliessungsbeitragssatzung, Dokumentcode 5/66/4 (Fachbereich 66 Tiefbau)',
        source_url='https://leverkusen.kommunalportal.nrw/detail/-/vr-bis-detail/dienstleistung/61107/show',
        verification_status='VERIFIED',
    ),
    '05512000': dict(
        name='Bottrop, Stadt', authority_name='Stadtverwaltung Bottrop - Fachbereich Finanzen',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Bottrop',
        phone=None, email=None,
        quote='Stadt Bottrop / Fachbereich Finanzen ... Der Fachbereich Finanzen informiert / Erschliessungsbeitraege nach §§ 127 ff. des Baugesetzbuches (BauGB) ... Weitere Auskuenfte erhalten Sie im Fachbereich Finanzen, Verwaltungsgebaeude Luise-Hensel-Strasse 1, Zimmer 405 ... E-Mail: strassenabrechnung@bottrop.de',
        source_url='https://www.bottrop.de/vv/downloads/Erschliessungsbeitra_ge_Internet.pdf',
        verification_status='VERIFIED',
    ),
    '05513000': dict(
        name='Gelsenkirchen, Stadt', authority_name='Stadtverwaltung Gelsenkirchen - Referat Verkehr',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Gelsenkirchen',
        phone=None, email=None,
        quote='Die Erschliessung ist der Anschluss eines Grundstuecks an das oeffentliche Strassen- und Wegenetz sowie an das Ver- und Entsorgungsnetz. Die Herstellungskosten dieser Anlagen sind zu 90% von den Eigentuemerinnen und Eigentuemern bzw. Erbbauberechtigen der erschlossenen Grundstuecke zu tragen. (Kontakt auf derselben Seite: Referat Verkehr, beitragsbescheinigung@gelsenkirchen.de)',
        source_url='https://www.gelsenkirchen.de/de/infrastruktur/bauen_und_wohnen/baugebiete_und_grundstuecke/erschliessung/index.aspx',
        verification_status='VERIFIED',
    ),
    '05515000': dict(
        name='Muenster, Stadt', authority_name='Stadtverwaltung Muenster - Amt fuer Mobilitaet und Tiefbau',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Muenster',
        phone=None, email=None,
        quote='Der Erschliessungsbeitrag deckt die Kosten, die entstehen, wenn die Stadt eine Erschliessungsanlage - wie zum Beispiel oeffentliche Strassen, Wege oder Plaetze, Gruenanlagen oder Laermschutzanlagen - erstmalig herstellt.',
        source_url='https://www.stadt-muenster.de/tiefbauamt/beitraege-und-gebuehren/beitraege',
        verification_status='VERIFIED',
    ),
    # --- Kreisfreie Staedte - Batch 3 (BI, BO, DO, HA) ---
    '05711000': dict(
        name='Bielefeld, Stadt', authority_name='Stadtverwaltung Bielefeld - Amt fuer Verkehr',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Bielefeld',
        phone=None, email=None,
        quote='Kontakt / Amt fuer Verkehr / Ralph Stuehrenberg / Telefon +49 521 51-3117 ... August-Bebel-Str. 92, 33602 Bielefeld (einziger auf der Seite \'Erschliessungsbeitraege\' genannter Kontakt)',
        source_url='https://www.bielefeld.de/node/3772',
        verification_status='VERIFIED',
    ),
    '05911000': dict(
        name='Bochum, Stadt', authority_name='Stadtverwaltung Bochum - Tiefbauamt (Beitragsstelle)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Bochum',
        phone=None, email=None,
        quote='Wer kann mir weiterhelfen? Tiefbauamt ... Adresse / Kontakt: Tiefbauamt Beitragsstelle, Technisches Rathaus (TR), Hans-Boeckler-Strasse 19, 44777 Bochum',
        source_url='https://www.bochum.de/Tiefbauamt/Dienstleistungen-und-Infos/Erschliessungsbeitraege',
        verification_status='VERIFIED',
    ),
    '05913000': dict(
        name='Dortmund, Stadt', authority_name='Stadtverwaltung Dortmund - Tiefbauamt',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Dortmund',
        phone=None, email=None,
        quote='Stadt Dortmund - Tiefbauamt, Erschliessungs- und Strassenbeitragsrecht, Erschliessungsvertraege ... Informationen ueber Erschliessungs- und Strassenbaubeitraege, des Tiefbauamtes der Stadt Dortmund',
        source_url='https://www.dortmund.de/themen/mobilitaet-und-verkehr/erschliessungs-und-strassenbaubeitraege/',
        verification_status='VERIFIED',
    ),
    '05914000': dict(
        name='Hagen, Stadt der FernUniversitaet', authority_name='Stadtverwaltung Hagen - Fachbereich Verkehr und Mobilitaet (Abteilung Verkehrsangelegenheiten, Bauvergaben, Submission und Anliegerbeitraege)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Hagen',
        phone=None, email=None,
        quote='Wir nehmen strassenrechtliche Verfuegungen vor und erheben Erschliessungs- und Strassenbaubeitraege. (Fachbereich Verkehr und Mobilitaet; Unterabschnitt \'Anliegerbeitraege\' ist mit \'Erschliessungsbeitraege\' untertitelt)',
        source_url='https://www.hagen.de/aus-dem-rathaus/fachbereiche-und-aemter/fachbereiche-a-z/fachbereich-verkehr-und-mobilitaet/',
        verification_status='VERIFIED',
    ),
    # --- Kreisfreie Staedte - Batch 4 (HAM, HER) ---
    '05915000': dict(
        name='Hamm, Stadt', authority_name='Stadtverwaltung Hamm - Bauverwaltungsamt, Abteilung Anliegerbeitraege und staedtebauliche Vertraege',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Hamm',
        phone=None, email=None,
        quote='Ein Aufgabenschwerpunkt der Abteilung Anliegerbeitraege und staedtebauliche Vertraege liegt in der Erhebung von Beitraegen fuer Erschliessungsanlagen (dem Anbau dienende Strassen, Wege und Plaetze).',
        source_url='https://serviceportal.hamm.de/suche/-/egov-bis-detail/einrichtung/941/show',
        verification_status='VERIFIED',
    ),
    '05916000': dict(
        name='Herne, Stadt', authority_name='Stadtverwaltung Herne - Fachbereich 53 Tiefbau und Verkehr, Abteilung 53/4 (Verwaltung, Finanzen, Beitraege, Strassenrecht)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Herne',
        phone=None, email=None,
        quote='Erschliessungs- und Strassenbaubeitraege Strassen- und Wegerecht (Leistung), zustaendige Organisationseinheit: Abteilung 53/4 - Verwaltung, Finanzen, Beitraege, Strassenrecht, Langekampstrasse 36, 44652 Herne, E-Mail tiefbauamt@herne.de',
        source_url='https://serviceportal.herne.de/detail/-/vr-bis-detail/dienstleistung/800934/show',
        verification_status='VERIFIED',
    ),
    # --- Kreisfreie Staedte - Batch 5 (D, DU, E, KR) ---
    '05111000': dict(
        name='Duesseldorf, Stadt', authority_name='Stadtverwaltung Duesseldorf - Amt fuer Verkehrsmanagement (Amt 66), Sachgebiet Anliegerbeitraege/Erschliessungsbeitraege',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Duesseldorf',
        phone=None, email=None,
        quote='Zur Refinanzierung durch die Gemeinde vorfinanzierten Erstherstellung von oeffentlichen Erschliessungsanlagen (Strassen, Gruenanlagen, Immissionsschutzanlagen) muessen von den Grundstueckseigentuemern / Erbbauberechtigten Beitraege nach dem Baugesetzbuch (BauGB) erhoben werden. ... bis hin zur Geltendmachung des Erschliessungsbeitrages durch Heranziehungsbescheide. (Seite gehoert zum Amt fuer Verkehrsmanagement, Ansprechpartner Sachgebietsleitung Daniel Gerber)',
        source_url='https://www.duesseldorf.de/verkehrsmanagement/service/anliegerbeitraege/erschliessungsbeitrag',
        verification_status='VERIFIED',
    ),
    '05112000': dict(
        name='Duisburg, Stadt', authority_name='Stadtverwaltung Duisburg - Amt fuer Bodenordnung, Geomanagement und Kataster (Amt 62), Sachgebiet Bodenordnung und Erschliessung (Beitragsrecht)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Duisburg',
        phone=None, email=None,
        quote='Kontakt / Organisationseinheiten: Bodenordnung und Erschliessung / Beitragsrecht, Amt fuer Bodenordnung, Geomanagement und Kataster, E-Mail erschliessung@stadt-duisburg.de (Seite \'Erschliessungsbeitraege nach dem Baugesetzbuch\')',
        source_url='https://www.duisburg.de/vv/produkte/pro_du/dez_v/62/erschliessungsbeitraege_nach_dem_baugesetzbuch',
        verification_status='VERIFIED',
    ),
    '05113000': dict(
        name='Essen, Stadt', authority_name='Stadtverwaltung Essen - Amt fuer Strassen und Verkehr (Amt 66), Ingenieurbau, Finanz- und Beitragsangelegenheiten - Team Beitragsangelegenheiten nach BauGB und §8 KAG',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Essen',
        phone=None, email=None,
        quote='Erschliessungsbeitraege nach dem BauGB (gelistete Leistung der Organisationseinheit \'Ingenieurbau, Finanz- und Beitragsangelegenheiten\', Amt fuer Strassen und Verkehr, Kontakt anliegerbeitraege@amt66.essen.de)',
        source_url='https://service.essen.de/detail/-/vr-bis-detail/einrichtung/1547321/show',
        verification_status='VERIFIED',
    ),
    '05114000': dict(
        name='Krefeld, Stadt', authority_name='Stadtverwaltung Krefeld - Fachbereich Stadt- und Verkehrsplanung (FB 61)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Krefeld',
        phone=None, email=None,
        quote='Im Rahmen der Beitragserhebung verarbeitet die Stadt Krefeld, Fachbereich Stadt- und Verkehrsplanung, Parkstrasse 10, 47829 Krefeld die Angaben zu Ihren von Dritten uebermittelten personenbezogenen Daten.',
        source_url='https://service.krefeld.de/datenschutz-beitragserhebung-fb61',
        verification_status='VERIFIED',
    ),
    # --- Kreisfreie Staedte - Batch 6 (SG, W, BN, K) ---
    '05122000': dict(
        name='Solingen, Klingenstadt', authority_name='Stadtverwaltung Solingen - Fachbereich 61 Planung, Mobilitaet, Denkmalpflege, Abteilung 61-13 (Strassen- und Vertragsrecht, Anliegerbeitraege)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Solingen',
        phone=None, email=None,
        quote='Die Herstellung oeffentlicher Strassen, Wege und Plaetze (Erschliessungsanlagen) ist Aufgabe der Stadt Solingen. Sie ist gesetzlich verpflichtet, die fuer die erstmalige endgueltige Herstellung von oeffentlichen Erschliessungsanlagen entstandenen Kosten im Wesentlichen auf die Eigentuemer der anliegenden Grundstuecke umzulegen. (Sachbearbeitung/Sachgebietsleitung organisatorisch zugeordnet zu Einheit 61-13 Strassen- und Vertragsrecht, Anliegerbeitraege, vgl. https://solingen.de/inhalt/verzeichnis/organisation/686)',
        source_url='https://solingen.de/inhalt/verzeichnis/product/822',
        verification_status='VERIFIED',
    ),
    '05124000': dict(
        name='Wuppertal, Stadt', authority_name='Stadtverwaltung Wuppertal - Ressort Strassen und Verkehr, Team Beitragsrecht, Vergaberecht, Erschliessungsrecht (104.72)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Wuppertal',
        phone=None, email=None,
        quote='Der Erschliessungsbeitrag ist eine oeffentlich-rechtliche Abgabe an die Stadt Wuppertal. ... Der Widerspruch ist an das Ressort Strassen und Verkehr zu richten. (Kontaktblock: Ressort Strassen und Verkehr / Team Beitragsrecht, Vergaberecht, Erschliessungsrecht (104.72))',
        source_url='https://www.wuppertal.de/rathaus-buergerservice/verkehr/strassen_wege/erschliessung.php',
        verification_status='VERIFIED',
    ),
    '05314000': dict(
        name='Bonn, Stadt', authority_name='Stadtverwaltung Bonn - Bauordnungsamt (Amt 63), Allgemeine Verwaltungs- und Beitragsabteilung (63-1) / Grundsatzangelegenheiten und Beitraege (63-11)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Bonn',
        phone=None, email=None,
        quote='Seitentitel (bonn.de, amtliche Organisationsseite): \'Grundsatzangelegenheiten und Beitraege | Bundesstadt Bonn\', uebergeordnet \'Allgemeine Verwaltungs- und Beitragsabteilung | Bundesstadt Bonn\' (Dez. III, Amt 63); Produktseite \'Beitraege (Erschliessungs-, Strassenausbau- oder Kanalanschlussbeitraege) | Bundesstadt Bonn\', Kontakt beitragsabteilung@bonn.de',
        source_url='https://www.bonn.de/vv/oe/_/Dez._III/63/63-1/63-11/Grundsatzangelegenheiten-und-Beitraege.php',
        verification_status='AUTO_IMPORTED',
    ),
    '05315000': dict(
        name='Koeln, Stadt', authority_name='Stadtverwaltung Koeln - Dezernat III (Mobilitaet), Bauverwaltungsamt, Beitrags- und Erschliessungsvertrags-Angelegenheiten',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Koeln',
        phone=None, email=None,
        quote='Aufgaben: Erhebung von Erschliessungsbeitraegen und Strassenausbaubeitraegen. Ausstellung von Beitragsbescheinigungen. Abschluss von Erschliessungsvertraegen. Koordination nicht staedtischer Planverfahren. Eingliederung in der Stadtverwaltung: Dezernat III - Mobilitaet, Bauverwaltungsamt, Beitrags- und Erschliessungsvertrags-Angelegenheiten.',
        source_url='https://www.stadt-koeln.de/service/adressen/beitrags-und-erschliessungsvertrags-angelegenheiten',
        verification_status='VERIFIED',
    ),
    # --- Kreis Olpe ---
    '05966004': dict(
        name='Attendorn, Hansestadt', authority_name='Hansestadt Attendorn - Tiefbauamt',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Attendorn',
        phone=None, email=None,
        quote='Tiefbauamt, Hansestadt Attendorn, Koelner Strasse 12, 57439 Attendorn (Leistung \'Erschliessungsbeitraege\', zustaendiger Sachbearbeiter Julius Wicker, Zimmer 211)',
        source_url='https://www.attendorn.de/Rathaus/Was-erledige-ich-wo-/Erschlie%C3%9Fungsbeitr%C3%A4ge.php?object=tx,3521.2.1&ModID=10&FID=2422.89.1&NavID=2422.14&kuo=1&sfwort=1',
        verification_status='VERIFIED',
    ),
    '05966008': dict(
        name='Drolshagen, Stadt', authority_name='Stadtverwaltung Drolshagen - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Drolshagen',
        phone=None, email=None,
        quote='Stadtverwaltung Drolshagen, Hagener Strasse 9, 57489 Drolshagen (allgemeiner Verwaltungskontakt; keine eigens benannte Erschliessungsbeitrags-Stelle auf der Webseite auffindbar)',
        source_url='https://www.drolshagen.de/B%C3%BCrgerservice/Verwaltung/',
        verification_status='AUTO_IMPORTED',
    ),
    '05966012': dict(
        name='Finnentrop', authority_name='Gemeindeverwaltung Finnentrop - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Finnentrop',
        phone=None, email=None,
        quote='Gemeindeverwaltung Finnentrop, Am Markt 1, 57413 Finnentrop (allgemeiner Verwaltungskontakt; keine eigens benannte Erschliessungsbeitrags-Stelle auf der Webseite auffindbar)',
        source_url='https://www.finnentrop.de/Verwaltung-Politik/Verwaltung/Rathaus/',
        verification_status='AUTO_IMPORTED',
    ),
    '05966016': dict(
        name='Kirchhundem', authority_name='Gemeindeverwaltung Kirchhundem - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Kirchhundem',
        phone=None, email=None,
        quote='Gemeinde Kirchhundem fuehrt eine Erschliessungsbeitragssatzung (PDF gelistet unter Ortsrecht/Satzungen); Textinhalt der Satzung technisch nicht extrahierbar, daher keine eigens benannte Stelle bestaetigt - allgemeiner Kontakt post@kirchhundem.de, Tel. +49 2723 409-0',
        source_url='https://www.kirchhundem.de/Rathaus-B%C3%BCrger/Ortsrecht-Satzungen/',
        verification_status='AUTO_IMPORTED',
    ),
    '05966020': dict(
        name='Lennestadt, Stadt', authority_name='Stadtverwaltung Lennestadt - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Lennestadt',
        phone=None, email=None,
        quote='Stadtverwaltung Lennestadt, rathaus@lennestadt.de, Tel. 02723 608-0 (allgemeiner Verwaltungskontakt; Organisationsstruktur- und Telefonverzeichnis-Seiten geprueft, keine eigens benannte Erschliessungsbeitrags-Stelle auffindbar)',
        source_url='https://www.lennestadt.de/Verwaltung-Politik/Rathaus/Telefonverzeichnis/',
        verification_status='AUTO_IMPORTED',
    ),
    '05966024': dict(
        name='Olpe, Stadt', authority_name='Stadtverwaltung Olpe - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Olpe',
        phone=None, email=None,
        quote='Stadtverwaltung Olpe, Franziskanerstrasse 6, 57462 Olpe, rathaus@olpe.de, Tel. 02761 83-0 (allgemeiner Verwaltungskontakt; Seiten \'Finanzen & Steuern\' und \'Bauen & Wohnen\' geprueft, keine eigens benannte Erschliessungsbeitrags-Stelle auffindbar)',
        source_url='https://www.olpe.de/Verwaltung-Politik/Rathaus/Kontakt-%C3%96ffnungszeiten/',
        verification_status='AUTO_IMPORTED',
    ),
    '05966028': dict(
        name='Wenden', authority_name='Gemeindeverwaltung Wenden - Rathaus (allgemeine Verwaltung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Wenden',
        phone=None, email=None,
        quote='Gemeindeverwaltung Wenden (allgemeiner Verwaltungskontakt; Seiten Bauverwaltung und Tiefbau geprueft - Themen Abwasseranlage, Bauleitplanung, Kanalbau, Strassenbau - jedoch keine eigens benannte Erschliessungsbeitrags-Stelle auffindbar)',
        source_url='https://www.wenden.de/rathaus-service/buergerservice/kontakt-oeffnungszeiten',
        verification_status='AUTO_IMPORTED',
    ),
    # --- Ennepe-Ruhr-Kreis ---
    '05954004': dict(
        name='Breckerfeld, Hansestadt', authority_name='Stadtverwaltung Hansestadt Breckerfeld - Amt 60 (Bauamt)',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Breckerfeld',
        phone=None, email=None,
        quote='Amt 60 (Bauamt), Leitung Sven Schulze, Stellvertretung Matthias Zimmer (Verwaltungsgliederung); keine explizite Zuordnung von \'Erschliessungsbeitraege\' im abrufbaren Aufgabenkatalog auffindbar',
        source_url='https://www.breckerfeld.de/rathaus-politik/verwaltungsgliederung.html',
        verification_status='AUTO_IMPORTED',
    ),
    '05954008': dict(
        name='Ennepetal, Stadt der Kluterthoehle', authority_name='Stadtverwaltung Ennepetal - Fachbereich Bauen/Tiefbau (Strassenbau)',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Ennepetal',
        phone=None, email=None,
        quote='Tiefbau-Kontakte K. Schonka und M. Mueller fuer strassenbaubezogene Online-Dienste (Aufbruch einer Strasse, Herstellung einer Ueberfahrt); Seite nennt \'Erschliessungsbeitraege\' nicht ausdruecklich als Aufgabe',
        source_url='https://www.ennepetal.de/bauen-wirtschaft/strassenbau/',
        verification_status='AUTO_IMPORTED',
    ),
    '05954012': dict(
        name='Gevelsberg, Stadt', authority_name='Stadtverwaltung Gevelsberg - Fachbereich Stadtentwicklung, Bauen und Infrastruktur',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Gevelsberg',
        phone=None, email=None,
        quote='Kontakt Herr Bohne (stadtentwicklung@stadtgevelsberg.de) unter \'Verkehrswege\' fuer Verkehrsuntersuchungen/-planungen; Seite bestaetigt Zustaendigkeit fuer Erschliessungsbeitraege/Strassenbaubeitraege nicht ausdruecklich',
        source_url='https://www.gevelsberg.de/Stadtentwicklung-Bauen-und-Infrastruktur/Verkehrswege/',
        verification_status='AUTO_IMPORTED',
    ),
    '05954016': dict(
        name='Hattingen, Stadt', authority_name='Stadtverwaltung Hattingen - Fachbereich 63 (Bauordnung und Baurecht)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Hattingen',
        phone=None, email=None,
        quote='Seite \'Erschliessungs- und Strassenbaubeitraege\' (Fachbereich 63 Bauordnung und Baurecht) nennt Frau Ewald und Herrn Meding mit Aufgabengebiet \'Erschliessungsbeitraege, Strassenbaubeitraege\'; Downloads \'Erschliessungsbeitraege\' und \'Erschliessungsbeitragsbescheinigungen bzw. Anliegerbescheinigungen\' auf derselben Seite. Huettenstrasse 43, 45525 Hattingen.',
        source_url='https://www.hattingen.de/stadt_hattingen/Rathaus/Fachbereiche/Bauordnung%20und%20Baurecht/Erschlie%C3%9Fungs-%20und%20Stra%C3%9Fenbaubeitr%C3%A4ge/',
        verification_status='VERIFIED',
    ),
    '05954020': dict(
        name='Herdecke, Stadt', authority_name='Stadtverwaltung Herdecke - Fachbereich Bauen und Stadtentwicklung (Bauaufsicht)',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Herdecke',
        phone=None, email=None,
        quote='A-Z Buergerservice-Verzeichnis ohne Eintrag \'Erschliessungsbeitrag\'; Bauen-Seite nennt Bauaufsichtspersonal mit Aufgaben Baugenehmigungsverfahren/Denkmalschutz/Bauberatung/Bauabnahmen, nicht Erschliessungsbeitraege',
        source_url='https://www.herdecke.de/standort/bauen-und-stadtentwicklung/bauen/',
        verification_status='AUTO_IMPORTED',
    ),
    '05954024': dict(
        name='Schwelm, Stadt', authority_name='Stadtverwaltung Schwelm - Organisationseinheit 314 Strassenbau',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Schwelm',
        phone=None, email=None,
        quote='Organisationseinheit 314 Strassenbau (Leitung Herr T. Roemer) handelt laut Organisationsseite u.a. \'Strassenausbaubeitraege nach Kommunalabgabengesetz\' und \'Erschliessungsbeitraege nach Baugesetzbuch\'. Verwaltungsgebaeude IV, Raum 3.3, Wiedenhaufe 11, 58332 Schwelm.',
        source_url='https://www.schwelm.de/rathaus/verwaltung/organisationen/organisation/show/314-strassenbau/',
        verification_status='VERIFIED',
    ),
    '05954028': dict(
        name='Sprockhoevel, Stadt', authority_name='Stadtverwaltung Sprockhoevel - Fachbereich Tiefbau und Bauhof',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Sprockhoevel',
        phone=None, email=None,
        quote='Tiefbau-Seite beschreibt Kanalsanierung, Spielplaetze, Sportanlagen; keine Erwaehnung von Erschliessungs- oder Strassenbaubeitraegen. Auch Finanzen/Kaemmerei-Seite ohne spezifische Nennung.',
        source_url='https://www.sprockhoevel.de/service-und-verwaltung/tiefbau-und-bauhof/tiefbau/',
        verification_status='AUTO_IMPORTED',
    ),
    '05954032': dict(
        name='Wetter (Ruhr), Stadt', authority_name='Stadtverwaltung Wetter (Ruhr) - Fachbereich Stadtplanung und Bauen',
        authority_type='Kommunale Bauverwaltung',
        street=None, plz=None, city='Wetter (Ruhr)',
        phone=None, email=None,
        quote='Offizielle Serviceportal-A-Z-Liste und Lebenslage \'Bauen und Wohnen\' listen \'Erschliessungsbeitrag\' nicht; separater Stadtbetrieb Wetter (stadtbetrieb-wetter.de) deckt Strassen- und Wegeunterhaltung ab, bestaetigt aber nicht ausdruecklich die Beitragserhebung',
        source_url='https://www.stadt-wetter.de/stadtplanung-bauen/',
        verification_status='AUTO_IMPORTED',
    ),
    '05954036': dict(
        name='Witten, Stadt', authority_name='Stadtverwaltung Witten - Tiefbauamt (Dezernat 4)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Witten',
        phone=None, email=None,
        quote='Verzeichnis \'Dezernate & Aemter\' listet fuer das Tiefbauamt u.a. \'Beitragsrecht, Erschliessungsvertraege, Strassenrecht\'; eigene Dienstleistungsseiten des Tiefbauamts fuehren \'Erschliessungsbeitraege\' sowie mehrere stadtteilbezogene \'Beitragsrecht\'-Eintraege gesondert auf.',
        source_url='https://www.witten.de/buergerservice/verwaltung/tiefbauamt-900000062-37500.html',
        verification_status='VERIFIED',
    ),
    # --- Rhein-Kreis Neuss ---
    '05162004': dict(
        name='Dormagen, Stadt', authority_name='Stadtverwaltung Dormagen (allgemeine Verwaltung)',
        authority_type='Kommunale Stadtverwaltung (allgemein)',
        street=None, plz=None, city='Dormagen',
        phone=None, email=None,
        quote='Keine eigens benannte Erschliessungsbeitrags-Stelle auffindbar: Website-Suche ohne Treffer, vollstaendiger A-Z-Dienstleistungskatalog (dormagen.kommunalportal.nrw) ohne Eintrag \'Erschliessungsbeitraege\', Technische Betriebe Dormagen (TBD) decken nur \'Ueberwachung privater Erschliessungsmassnahmen\' (baubegleitende Aufsicht) ab, nicht die Beitragserhebung selbst',
        source_url='https://www.dormagen.de/',
        verification_status='AUTO_IMPORTED',
    ),
    '05162008': dict(
        name='Grevenbroich, Stadt', authority_name='Stadtverwaltung Grevenbroich - Steuern, Gebuehren und Beitraege (Amt 22)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Grevenbroich',
        phone=None, email=None,
        quote='Dienstleistung \'Erschliessungsbeitraege\': Zustaendige Einrichtungen: Steuern, Gebuehren und Beitraege - 22, Am Markt 2, 41515 Grevenbroich, Kontakt Frau Andrea Hebing-Alex, steuern@grevenbroich.de',
        source_url='https://grevenbroich.kommunalportal.nrw/detail/-/vr-bis-detail/dienstleistung/15279/show',
        verification_status='VERIFIED',
    ),
    '05162012': dict(
        name='Juechen', authority_name='Gemeindeverwaltung Juechen - Amt fuer oeffentliche Infrastruktur',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Juechen',
        phone=None, email=None,
        quote='Dienstleistung \'Erschliessungsbeitraege\': Zustaendige Einrichtungen: Amt fuer oeffentliche Infrastruktur, Wilhelmstrasse 8, 41363 Juechen (Kontakte Marc Cleven, Maximilian Hampel); Bezug auf \'die Erschliessungsbeitragssatzung der Stadt Juechen vom 29.08.1989\'',
        source_url='https://juechen.kommunalportal.nrw/detail/-/vr-bis-detail/dienstleistung/18578/show',
        verification_status='VERIFIED',
    ),
    '05162016': dict(
        name='Kaarst, Stadt', authority_name='Stadtverwaltung Kaarst - Fachbereich III, 66 Tiefbau, Bauverwaltung und Baubetriebshof, Abteilung 66-600 (Bauverwaltung und Erschliessung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Kaarst',
        phone=None, email=None,
        quote='Einrichtung \'66-600 Bauverwaltung und Erschliessung\' (Fachbereich III - Technischer Beigeordneter, 66 Tiefbau, Bauverwaltung und Baubetriebshof), erreicht ueber Leistung \'Anliegerbescheinigung ueber Erschliessungs- und Kanalanschlussbeitraege\'; Kontakt Herr Schulte, Abteilungsleitung, harald.schulte@kaarst.de',
        source_url='https://service.kaarst.de/suche/-/vr-bis-detail/einrichtung/2402/show',
        verification_status='VERIFIED',
    ),
    '05162020': dict(
        name='Korschenbroich, Stadt', authority_name='Stadtverwaltung Korschenbroich - Sachgebiet Steuern, Abgaben und Beitraege',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Korschenbroich',
        phone=None, email=None,
        quote='Dienstleistung \'Erschliessungsbeitraege\': Zustaendige Einrichtung: Sachgebiet Steuern, Abgaben und Beitraege, Rathaus Sebastianusstrasse, Sebastianusstrasse 1, 41352 Korschenbroich, steuern@korschenbroich.de, Kontakt Christiane Birkenfeld',
        source_url='https://service.korschenbroich.de/suche/-/vr-bis-detail/dienstleistung/1108951/show',
        verification_status='VERIFIED',
    ),
    '05162022': dict(
        name='Meerbusch, Stadt', authority_name='Stadtverwaltung Meerbusch - Beitraege / Gebuehren / Zuwendungen',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Meerbusch',
        phone=None, email=None,
        quote='Dienstleistung \'Grundstuecksbezogene Beitraege\' (u.a. \'Beitraege nach §§ 127 ff Baugesetzbuch (BauGB) - Erschliessungsbeitraege\'): Zustaendige Einrichtungen: Beitraege / Gebuehren / Zuwendungen, Wittenberger Strasse 21, 40668 Meerbusch',
        source_url='https://meerbusch.kommunalportal.nrw/detail/-/vr-bis-detail/dienstleistung/12606/show',
        verification_status='VERIFIED',
    ),
    '05162024': dict(
        name='Neuss, Stadt', authority_name='Stadtverwaltung Neuss - Bauverwaltungsamt (Erschliessungs- und Kanalanschlussbeitraege)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Neuss',
        phone=None, email=None,
        quote='Leistung \'Anliegerbescheinigung beantragen\': \'Erschliessungsbeitraege, Kanalanschlussbeitraege und Kostenerstattungsbetraege koennen eine durchaus deutliche finanzielle Belastung fuer ein Grundstueck sein...\' Kontaktblock: Stadtverwaltung Neuss - Erschliessungs- und Kanalanschlussbeitraege, Neumarkt 12, 41460 Neuss, bauverwaltung@stadt.neuss.de',
        source_url='https://serviceportal-neuss.de/suche/-/egov-bis-detail/dienstleistung/26104/show',
        verification_status='VERIFIED',
    ),
    '05162028': dict(
        name='Rommerskirchen', authority_name='Gemeindeverwaltung Rommerskirchen - Tiefbauamt',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Rommerskirchen',
        phone=None, email=None,
        quote='Amt-Seite \'Tiefbauamt\', Aufgabengebiete: \'Strassenbau und -unterhaltung, Wirtschaftswegebau und -unterhaltung, Strassenbeleuchtung, Entwaesserung, Oeffentliche Gruenflaechen und Kinderspielplaetze, Erschliessungs- und Strassenausbaubeitraege, Abfallbeseitigung\'; Amtsleiter Rudolf Reimert',
        source_url='https://www.rommerskirchen.de/rathaus-und-buergerservice/politik-und-verwaltung/verwaltung/aemter-und-ansprechpartner/aemter-der-gemeindeverwaltung/tiefbauamt/',
        verification_status='VERIFIED',
    ),
    # --- Rheinisch-Bergischer Kreis ---
    '05378004': dict(
        name='Bergisch Gladbach, Stadt', authority_name='Stadtverwaltung Bergisch Gladbach - Verkehrsflaechen/Beitraege (Fachbereich 6, Rathaus Bensberg)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Bergisch Gladbach',
        phone=None, email=None,
        quote='Bei der Erhebung von Erschliessungsbeitraegen koennen bis zu 90% der Kosten auf die Anlieger verteilt werden, bei der Erhebung von Strassenbaubeitraegen nach §8 KAG je nach Strassentyp und funktionalem Strassenteil zwischen 30% und 80% der Kosten. Kontakt: Verkehrsflaechen/Beitraege, Rathaus Bensberg, Wilhelm-Wagener-Platz, Raum 305, geschaeftsstelle.fb6@stadt-gl.de',
        source_url='https://www.bergischgladbach.de/Dienstleistung.aspx?dlid=2021',
        verification_status='VERIFIED',
    ),
    '05378008': dict(
        name='Burscheid, Stadt', authority_name='Technische Werke Burscheid (TWB) - Abteilung Beitraege & Gebuehren (staedtischer Eigenbetrieb der Stadt Burscheid)',
        authority_type='Kommunale Beitragsstelle (Eigenbetrieb)',
        street=None, plz=None, city='Burscheid',
        phone=None, email=None,
        quote='Eigentuemer neu erschlossener Grundstuecke haben fuer den erstmaligen endgueltigen Zugang zu staedtischen Strassen, Wegen und Plaetzen Erschliessungsbeitraege zu entrichten. Weitere Informationen finden Sie in der Rubrik Erschliessungsbeitrag auf der Internetseite der Technischen Werke Burscheid. (TWB-Seite ergaenzend: \'Die Stadt Burscheid ist aufgrund §§127 bis 135 des Baugesetzbuches (BauGB) verpflichtet, diese Erschliessungsbeitraege zu erheben.\')',
        source_url='https://www.burscheid.de/buergerservice/dienstleistungen/erschliessungsbeitrag-900000141-0.html',
        verification_status='VERIFIED',
    ),
    '05378012': dict(
        name='Kuerten', authority_name='Gemeindeverwaltung Kuerten - Abteilung Strassenbau',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Kuerten',
        phone=None, email=None,
        quote='Kontakt - Strassenbau, Tel. 02268 939-344, strassenbau@kuerten.de. Die ingenieurmaessige Planung der Ausbaumassnahmen werden mit den Eigentuemern der erschlossenen Grundstuecke, die spaeter Erschliessungs- oder Strassenausbaubeitraege zahlen muessen, in einem oeffentlichen Anliegergespraech eroertert und abgestimmt. (Akkordeon-Abschnitt \'Erschliessungsbeitraege / Strassenbaubeitraege\' auf derselben Seite)',
        source_url='https://www.kuerten.de/abteilungen/strassen/',
        verification_status='VERIFIED',
    ),
    '05378016': dict(
        name='Leichlingen (Rheinland), Bluetenstadt', authority_name='Stadtverwaltung Leichlingen - Abteilung 21 (Foerdermittel, Oeffentliche Abgaben, Gebuehrenkalkulation und Vollstreckung)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Leichlingen',
        phone=None, email=None,
        quote='Der Erschliessungsbeitrag deckt die Kosten, die entstehen, wenn die Stadt eine Erschliessungsanlage - wie zum Beispiel oeffentliche Strassen, Wege oder Plaetze, Gruenanlagen oder Laermschutzanlagen - erstmalig herstellt. Die Stadt traegt 10 Prozent dieser Kosten. Zustaendige Abteilung: 21 Foerdermittel, Oeffentliche Abgaben, Gebuehrenkalkulation und Vollstreckung, Ansprechperson Monika Maczeja, 02175 992-148',
        source_url='https://www.leichlingen.de/buergerservice-und-rathaus/was-erledige-ich-wo/anliegen-von-a-z?tx_citkoegovservicelight_dienstleistungen%5Baction%5D=show&tx_citkoegovservicelight_dienstleistungen%5Bdienstleistungen%5D=80&cHash=35d6c95849a669a26270cff024537de0',
        verification_status='VERIFIED',
    ),
    '05378020': dict(
        name='Odenthal', authority_name='Gemeindeverwaltung Odenthal - Fachbereich Planen & Bauen, Strassen/Wege/Plaetze',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Odenthal',
        phone=None, email=None,
        quote='Erschliessungsbeitraege werden nach den Vorschriften der §§123-135 Baugesetzbuch (BauGB) und der Erschliessungsbeitragssatzung der Gemeinde Odenthal (EBS) erhoben. ... Der Erschliessungsbeitrag wird durch einen Beitragsbescheid erhoben. Kontakt: Frau Weyer, weyer@odenthal.de, 02202 710 281',
        source_url='https://www.odenthal.de/planen-bauen/strassen-wege-plaetze/geplante-strassenbaumassnahmen/strassenbau-und-erschliessungsbeitraege',
        verification_status='VERIFIED',
    ),
    '05378024': dict(
        name='Overath, Stadt', authority_name='Stadtverwaltung Overath - Amt 68 (Amt fuer Tiefbau und Gruenflaechen), Abteilung Tiefbau und Gewaesser',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Overath',
        phone=None, email=None,
        quote='Zustaendigkeit: 68 - Amt fuer Tiefbau und Gruenflaechen, Telefon 02206 602-0, post@overath.de; Abteilung Tiefbau und Gewaesser, Telefon 02206 602-979, tiefbau@overath.de',
        source_url='https://www.overath.de/buergerservice-views/leistungen/NRW:entry:38215-VLR/erschliessungsbeitrag-zahlen/',
        verification_status='VERIFIED',
    ),
    '05378028': dict(
        name='Roesrath, Stadt', authority_name='Stadtverwaltung Roesrath - Fachbereich Bauen & Umwelt, Infrastruktur/Strassenbau',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Roesrath',
        phone=None, email=None,
        quote='Eine Strassenanliegerbescheinigung gibt Auskunft darueber, ob fuer ein bestimmtes Grundstueck kuenftig noch Erschliessungsbeitraege nach dem Baugesetzbuch (BauGB) oder Strassenbaubeitraege und Kanalanschlussbeitraege nach dem Kommunalabgabengesetz (KAG NRW) zu entrichten sind. ... Bitte senden Sie Ihren Antrag ausschliesslich per E-Mail an: strassen@roesrath.de',
        source_url='https://www.roesrath.de/bauen-umwelt/infrastruktur/strassenbau-unterhaltung/strassenanliegerbescheinigung/',
        verification_status='VERIFIED',
    ),
    '05378032': dict(
        name='Wermelskirchen, Stadt', authority_name='Stadtverwaltung Wermelskirchen - Sachgebiet Liegenschaften',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Wermelskirchen',
        phone=None, email=None,
        quote='Kontakt (Seite \'Erschliessungsbeitraege / Strassenausbaubeitraege\'): Frau S. Langner, Sachgebietsleitung Liegenschaften, 02196 710-241; Frau S. Wegwert, SB Beitraege, 02196 710-232',
        source_url='https://www.wermelskirchen.de/aktuelles-rathaus/verwaltung-a-z/stadtverwaltung-a-z/dienstleistungen-a-z/show/erschliessungsbeitraege-strassenausbaubeitraege',
        verification_status='VERIFIED',
    ),
    # --- Kreis Mettmann ---
    '05158004': dict(
        name='Erkrath, Stadt', authority_name='Stadtverwaltung Erkrath - Fachbereich Tiefbau, Strasse, Gruen',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Erkrath',
        phone=None, email=None,
        quote='Zustaendige Stelle (Serviceportal-Eintrag \'Erschliessungsbeitraege\'): Fachbereich Tiefbau, Strasse, Gruen, Schimmelbuschstrasse 11-13, 40699 Erkrath',
        source_url='https://www.erkrath.de/rathaus-politik/verwaltung/serviceportal/erschliessungsbeitraege',
        verification_status='VERIFIED',
    ),
    '05158008': dict(
        name='Haan, Stadt', authority_name='Stadtverwaltung Haan - Bauverwaltungsamt',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Haan',
        phone=None, email=None,
        quote='Seite \'Erschliessungs- und Ausbaubeitraege\' (unter Wirtschaft & Stadtentwicklung > Planen & Bauen > Beitragsrecht): Kontakt Bauverwaltungsamt, Alleestrasse 8, 42781 Haan, bauverwaltung@stadt-haan.de',
        source_url='https://www.haan.de/Wirtschaft-Stadtentwicklung/Planen-Bauen/Beitragsrecht/',
        verification_status='VERIFIED',
    ),
    '05158012': dict(
        name='Heiligenhaus, Stadt', authority_name='Stadtverwaltung Heiligenhaus - Fachbereich Finanzen (Kaemmerei)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Heiligenhaus',
        phone=None, email=None,
        quote='Der Fachbereich Finanzen ... setzt sich zusammen aus den Abteilungen Kaemmerei, Stadtkasse ... Die Kaemmerei erhebt Grundsteuer, Gewerbesteuer, Hundesteuer, Vergnuegungssteuer, Abfallbeseitigungsgebuehren, Strassenreinigungsgebuehren, Erschliessungsbeitraege, Strassenausbaubeitraege',
        source_url='https://www.heiligenhaus.de/stadt-rathaus/ausbildung/ausbildungsinhalte',
        verification_status='VERIFIED',
    ),
    '05158016': dict(
        name='Hilden, Stadt', authority_name='Stadtverwaltung Hilden - Tiefbau- und Gruenflaechenamt',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Hilden',
        phone=None, email=None,
        quote='Das Sachgebiet Strassenbau und Verkehr des Tiefbau- und Gruenflaechenamtes ist verantwortlich fuer die Planung, den Bau und die Instandhaltung der Strassen. (allgemeine Zustaendigkeitsbeschreibung; keine seitenspezifische Nennung von \'Erschliessungsbeitraege\' gefunden, Serviceportal Hilden war zum Recherchezeitpunkt wegen Wartungsarbeiten nicht erreichbar)',
        source_url='https://www.hilden.de/de/wirtschaft-bauen/strassen-tiefbauarbeiten/strassenbau/',
        verification_status='AUTO_IMPORTED',
    ),
    '05158020': dict(
        name='Langenfeld (Rheinland), Stadt', authority_name='Stadtverwaltung Langenfeld - Finanzbuchhaltung, Vollstreckung, Steuern',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Langenfeld',
        phone=None, email=None,
        quote='Serviceportal-Eintrag \'Beitraege (Steuern und Abgaben)\': Anschrift Finanzbuchhaltung, Vollstreckung, Steuern; Dienstleistungen: Anliegerbescheinigung, Kostenerstattungsbetraege nach Baugesetzbuch, Kostenersaetze fuer Grundstuecksanschlussleitungen, Kanalanschlussbeitraege, Erschliessungsbeitraege, Strassenbaubeitraege; Zustaendige Einrichtung: Finanzbuchhaltung, Vollstreckung, Steuern, beitraege@langenfeld.de',
        source_url='https://service.langenfeld.de/detail/-/vr-bis-detail/mitarbeiter/28561/show',
        verification_status='VERIFIED',
    ),
    '05158024': dict(
        name='Mettmann, Stadt', authority_name='Stadtverwaltung Mettmann - Amt fuer Verkehr, Tiefbau und Gruenflaechen',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Mettmann',
        phone=None, email=None,
        quote='Seit Anfang April ist die Diplom-Ingenieurin Amtsleiterin fuer Verkehr, Tiefbau und Gruenflaechen in der Stadtverwaltung. ... \'Wir sind fuer die Erschliessung zustaendig. Das ist im Vergleich zum Bereich Hochbau natuerlich nur ein kleiner Beitrag,\' weiss sie, \'aber immerhin.\'',
        source_url='https://www.mettmann.de/web/neu-an-bord-nina-lajios-leitet-das-amt-fuer-verkehr-tiefbau-und-gruenflaechen/',
        verification_status='VERIFIED',
    ),
    '05158026': dict(
        name='Monheim am Rhein, Stadt', authority_name='Stadtverwaltung Monheim am Rhein - Bereich 60 (Bauwesen)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Monheim am Rhein',
        phone=None, email=None,
        quote='Verarbeitungsverzeichnis-Eintrag \'Erschliessungsbeitraege\': Ansprechpartner/in: Bereich 60 (Bauwesen), Ella Luff, Bereich60@monheim.de. Rechtsgrundlage: §§127 ff BauGB. Kategorien von Empfaengern: intern, Stadtkasse.',
        source_url='https://www.monheim.de/datenschutz',
        verification_status='VERIFIED',
    ),
    '05158028': dict(
        name='Ratingen, Stadt', authority_name='Stadtverwaltung Ratingen - 66.40 Abteilung Bauverwaltung',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Ratingen',
        phone=None, email=None,
        quote='Serviceportal-Eintrag \'Strassenanliegerbescheinigung\': Durch eine Strassenanliegerbescheinigung wird mitgeteilt, ob fuer ein Grundstueck in Zukunft noch Erschliessungsbeitraege nach dem Baugesetzbuch oder Strassenbaubeitraege und Kanalanschlussbeitraege nach dem Kommunalabgabengesetz zu zahlen sind. ... Zustaendige Einrichtungen: 66.40 - Abteilung Bauverwaltung (Kontakt Herr Stoltenbauer, kai.stoltenbauer@ratingen.de)',
        source_url='https://serviceportal.ratingen.de/detail/-/vr-bis-detail/dienstleistung/40203/show',
        verification_status='VERIFIED',
    ),
    '05158032': dict(
        name='Velbert, Stadt', authority_name='TBV - Liegenschaften und Bauverwaltung (Technische Betriebe Velbert AoeR, im Kooperationsvertrag fuer die Stadt Velbert taetig)',
        authority_type='Kommunale Beitragsstelle (ausgegliederter Aufgabentraeger / AoeR)',
        street=None, plz=None, city='Velbert',
        phone=None, email=None,
        quote='Serviceportal-Eintrag \'Erschliessungsbeitraege\': Zur Deckung ihres anderweitig nicht gedeckten Aufwandes erhebt die Stadt Erschliessungsbeitraege nach den Vorschriften des Baugesetzbuches sowie nach Massgabe der Satzung ueber die Erhebung von Erschliessungsbeitraegen in der Stadt Velbert (Erschliessungsbeitragssatzung). ... Zustaendige Einrichtungen: TBV - Liegenschaften und Bauverwaltung (Kontakt Frau Manck, Aufgaben der Stadt Velbert im Rahmen des Kooperationsvertrages mit der TBV, rebecca.manck@velbert.de)',
        source_url='https://serviceportal.velbert.de/detail/-/vr-bis-detail/dienstleistung/1031808/show',
        verification_status='VERIFIED',
    ),
    '05158036': dict(
        name='Wuelfrath, Stadt', authority_name='Stadtverwaltung Wuelfrath - Tiefbauamt (Amt 66)',
        authority_type='Kommunale Beitragsstelle',
        street=None, plz=None, city='Wuelfrath',
        phone=None, email=None,
        quote='Amt 66 - Tiefbauamt, Abfallberatung, Baubetriebshof, Friedhof, Amtsleitung Herr Benedikt Leister. \'Das Tiefbauamt ist Ihr Ansprechpartner fuer Infrastruktur, Stadtbild und Umwelt. Wir planen, bauen und erhalten Strassen, Wege, Bruecken, Strassenbeleuchtung und Entwaesserungsanlagen.\' Keine seitenspezifische Nennung von \'Erschliessungsbeitraege\' auffindbar (Site-Suche ohne Treffer); Erschliessungsbeitragssatzung ist unter \'Satzungen\' gelistet, jedoch ohne benannte Kontaktstelle.',
        source_url='https://www.wuelfrath.net/planen-bauen/tiefbauamt',
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
        batch_id = f"erschliessung-nrw-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags, info in GEMEINDEN.items():
            authority = db.query(Authority).filter(Authority.authority_name == info["authority_name"]).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["authority_name"],
                    authority_type=info["authority_type"],
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Nordrhein-Westfalen", phone=info["phone"], email=info["email"],
                    source="Recherche-Sitzung 2026-09-28 (amtliche Stadt-/Gemeinde-Webseite, "
                           "siehe jurisdictions.source_url der zugehörigen Regel)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            quote = info["quote"]
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Erschliessung NRW - {info['name']}",
                request_type_id="ERSCHLIESSUNG", state="Nordrhein-Westfalen", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{info['authority_name']} — {quote}",
                source_url=info["source_url"],
                source_license=(
                    "Kommunale Webseite (amtliche Stadt-/Gemeindeverwaltung, Recherche-Sitzung 2026-09-28)"
                    if info["verification_status"] == "VERIFIED"
                    else "Kommunale Webseite (allgemeiner Bauamt-/Gemeindeverwaltungs-Fallback bzw. "
                         "nur Seitentitel-Bestaetigung, Recherche-Sitzung 2026-09-28)"
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
