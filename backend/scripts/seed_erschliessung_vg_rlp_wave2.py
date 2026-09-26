"""
Erschließungsbeiträge / Anliegerbescheinigung RLP - zweite große
Ausweitungswelle (Fortsetzung von seed_erschliessung_vg_rlp.py, das die
ersten 14 von 129 Verbandsgemeinden abgedeckt hat).

Auf Nutzerauftrag ("starte so viele Agenten wie möglich um die NO_MATCH
Fälle so schnell wie möglich zu vervollständigen") wurden 19 parallele
Recherche-Agenten eingesetzt (reine Web-Recherche, kein Datenbankzugriff -
alle Schreibzugriffe blieben bei mir gebündelt, um SQLite-Schreibkonflikte
und eine Aufweichung der Quellenprüfung zu vermeiden). Ergebnis: 102 von
115 in diesem Durchlauf recherchierten Verbandsgemeinden konnten mit einer
amtlichen Quelle belegt werden, 12 blieben ehrlich als OFFEN gemeldet
(keine amtliche Quelle mit konkreter Abteilungszuordnung auffindbar) und
sind bewusst NICHT in diesem Skript enthalten:
  Adenau, Birkenfeld, Cochem, Selters (Westerwald), Leiningerland
  (erneut geprüft, weiterhin nur Zeitungsartikel auffindbar - siehe
  scripts/revert_erschliessung_leiningerland.py), Brohltal, Hermeskeil,
  Landstuhl, Hauenstein, Lambsheim-Heßheim, Bad Breisig, Unkel.
Verbandsgemeinde Südeifel bleibt ebenfalls offen (bereits in der ersten
Welle als JS-Organigramm-Fall zurückgestellt).

SOURCING-STANDARD (wie im Vorgänger-Skript, ausdrücklich vom Nutzer
bestätigt): `source_url` MUSS eine amtliche Quelle sein (VG-eigene
Amtsseite oder offizielles Landes-/Bundesportal service.rlp.de). NIEMALS
ein Zeitungsartikel oder eine sonstige Drittquelle.

Nachträgliche Eigenprüfung (nicht nur Agentenaussage übernommen): bei vier
Fällen, deren Beleglage von den Recherche-Agenten selbst als unsicher
markiert wurde, wurde die Quelle zusätzlich selbst abgerufen und
geprüft:
  - Sprendlingen-Gensingen: Seite "Erschließung von Grundstücken" -
    Verwechslungsgefahr mit Wasser/Abwasser-Erschließung (bekanntes
    Muster aus dem Daun-Fall der ersten Welle) aktiv geprüft und
    ausgeschlossen - Seite nennt "Erschließungsbeiträge" wörtlich UND den
    für § 129 BauGB charakteristischen "Gemeindeanteil von mindestens
    10 %" - eindeutig die richtige Rechtsgrundlage. Bestätigt: stark.
  - Weilerbach: Geschäftsverteilungsplan-PDF war für den Agenten nicht
    volltextdurchsuchbar (Bild-Rendering-Verdacht) - eigene
    pdftotext-Extraktion bestätigt "Sachgebiet 3.1.4 - Erschließungs- und
    Ausbaubeiträge" wörtlich. Bestätigt: stark.
  - Herxheim: Beleg war nur ein Suchmaschinen-Snippet - eigener PDF-Abruf
    bestätigt eine amtliche "Beitragsrechtliche Stellungnahme in Bezug
    auf Erschließungsbeiträge" von Fachbereich 2 (Jutta Merz) - sogar
    eindeutiger als ursprünglich berichtet. Bestätigt: stark.
  - Oberes Glantal: Quelle war ausschließlich service.rlp.de, das per
    ALTCHA-Bot-Schutz blockiert - weder der Agent noch die eigene
    Nachprüfung (curl, VG-eigene Seite ist rein JavaScript-basiert) konnte
    den Wortlaut selbst einsehen, nur die Konsistenz mehrerer
    Suchergebnis-Snippets. Da NICHT selbst am Wortlaut verifizierbar,
    bewusst auf "schwaecher" herabgestuft (technisch abgedeckt, aber
    nicht mit derselben Sicherheit wie ein selbst gelesener Beleg).

Adressen/E-Mails für alle Verbandsgemeinden stammen aus dem amtlichen
Destatis-Anschriftenverzeichnis (siehe app/services/address_directory.py)
- AUSSCHLIESSLICH für Adresse/allgemeine E-Mail, NIE für die fachliche
Zuständigkeitsaussage selbst.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26/27, 19 parallele Recherche-Agenten, siehe source_url je Regel)"

# name -> dict(street, postal_code, city, email, dept, tier, quote, url)
# ags_liste wird zur Laufzeit aus rlp_gemeinde_vg_map.csv nachgeschlagen
# (GEN_V-Spalte), nicht händisch abgeschrieben - sicherer bei 102 VGs.
VERBANDSGEMEINDEN = {
    "Nahe-Glan": dict(
        street="Marktplatz", postal_code="55566", city="Bad Sobernheim", email="poststelle@vg-nahe-glan.de",
        dept="Abteilung 3 Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Zuständigkeit/Leistung der Abteilung '3 Bauen' gelistet",
        url="https://www.vg-nahe-glan.de/buergerservice/abteilungen/RLP:department:269101/3-natuerliche-lebensgrundlagen-und-bauen/",
    ),
    "Hunsrück-Mittelrhein": dict(
        street="Rathausstraße", postal_code="56281", city="Emmelshausen", email="rathaus@vg-hm.de",
        dept="Abteilung 4-Finanzen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Zuständigkeit/Leistung der Abteilung '4-Finanzen' gelistet",
        url="https://www.hunsrueckmittelrhein.de/buergerservice/abteilungen/RLP:department:316/4-finanzen/",
    ),
    "Hachenburg": dict(
        street="Gartenstraße", postal_code="57627", city="Hachenburg", email="info@hachenburg-vg.de",
        dept="Fachbereich 5 - Bauen und Regionalentwicklung, Sachgebiet 5.1", tier="stark",
        quote="'Sachgebiet 5.1 Bauleitplanung und Siedlungsstruktur ... Erschließungs- und Ausbaubeiträge', zusätzlich 'Erschließungsbeitrag zahlen' als Zuständigkeit des Fachbereichs 5",
        url="https://www.hachenburg-vg.de/buergerservice/abteilungen/RLP:department:263666/fachbereich-5-bauen-und-regionalentwicklung/",
    ),
    "Kelberg": dict(
        street="Dauner Straße", postal_code="53539", city="Kelberg", email="rathaus@vgv-kelberg.de",
        dept="Erschließungs- und Ausbaubeiträge (Fachbereich 1 - Organisation und Bauen)", tier="stark",
        quote="Abteilungstitel wörtlich 'Erschließungs- und Ausbaubeiträge'; zugehörige Zuständigkeit 'Erschließungsbeitrag zahlen'",
        url="https://www.vgv-kelberg.de/buergerservice-ansichten/abteilungen/RLP:department:373417/erschliessungs-und-ausbaubeitraege/",
    ),
    "Rüdesheim": dict(
        street="Nahestraße", postal_code="55593", city="Rüdesheim", email="post@vg-ruedesheim.de",
        dept="Abteilung 3: Finanzen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Zuständigkeit/Leistung der Abteilung '3: Finanzen' gelistet",
        url="https://www.vg-ruedesheim.de/buergerservice/abteilungen/RLP:department:170438/3-finanzen/",
    ),
    "Nastätten": dict(
        street="Bahnhofstraße", postal_code="56355", city="Nastätten", email="post@vg-nastaetten.de",
        dept="Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - als eigener Leistungspunkt in der Liste der Zuständigkeiten der Abteilung 'Bauen' aufgeführt",
        url="https://www.vgnastaetten.de/buergerservice/abteilungen/RLP:department:349429/bauen/",
    ),
    "Aar-Einrich": dict(
        street="Burgstraße", postal_code="56368", city="Katzenelnbogen", email="post@vg-aar-einrich.de",
        dept="Bauabteilung", tier="stark",
        quote="Seite trägt den Titel 'Erschließungsbeiträge', Ansprechpartner 'Carmen Runkel -Bauabteilung-' / 'Jutta Rohde -Bauabteilung-'",
        url="https://www.vg-aar-einrich.de/rathaus-vg/bauen-wohnen/beitragsveranlagung/erschliessungsbeitraege/",
    ),
    "Saarburg-Kell": dict(
        street="Schlossberg", postal_code="54439", city="Saarburg", email="buergertelefon@saarburg-kell.de",
        dept="Fachbereich Kommunale Betriebe - Verbandsgemeindewerke", tier="stark",
        quote="Mitarbeiterprofil Günter Reiter, Zuständigkeitsliste enthält wörtlich 'Erschließungsbeitrag zahlen'",
        url="https://www.saarburg-kell.de/buergerservice/mitarbeiter/RLP:employee:11968/reiter-guenter/",
    ),
    "Bad Ems-Nassau": dict(
        street="Bleichstraße", postal_code="56130", city="Bad Ems", email="poststelle@vgben.de",
        dept="GB 3 Bauwesen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', Zuständige Abteilungen: 'GB 3 Bauwesen'",
        url="https://www.vgben.de/buergerservice/leistungen/RLP:entry:221141/erschliessungsbeitrag-zahlen/",
    ),
    "Vordereifel": dict(
        street="Kelberger Straße", postal_code="56727", city="Mayen", email="verbandsgemeinde@vordereifel.de",
        dept="Fachbereich 4 - Kommunale Infrastruktur", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als eigenständiger Punkt in der Leistungsliste des Fachbereichs 4",
        url="https://www.vordereifel.de/buergerservice-views/abteilungen/RLP:department:346072/fachbereich-4-kommunale-infrastruktur/",
    ),
    "Kaisersesch": dict(
        street="Am Römerturm", postal_code="56759", city="Kaisersesch", email="info@vg.kaisersesch.de",
        dept="Fachbereich 3 - Bauen / Sachgebiet 5.2 - Entgelte, Beiträge", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen': zuständige Abteilungen Fachbereich 3 - Bauen, Fachbereich 5 - Abwasserwerk und Tiefbau, Sachgebiet 5.2 - Entgelte/Beiträge",
        url="https://www.ikzportal.de/buergerservice/leistungen/RLP:entry:231079/erschliessungsbeitrag-zahlen",
    ),
    "Montabaur": dict(
        street="Konrad-Adenauer-Platz", postal_code="56410", city="Montabaur", email="info@montabaur.de",
        dept="Sachgebiet 3.1 - Buchhaltung, Rechnungswesen, Controlling, Beiträge", tier="stark",
        quote="'Sachgebiet - 3.1 Buchhaltung, Rechnungswesen, Controlling, Beiträge' als zuständige Stelle auf der Leistungsseite 'Erschließungsbeiträge erheben'",
        url="https://www.vg-montabaur.de/buergerservice/leistungen/RLP:entry:67255:ANLR-VLR/erschliessungsbeitraege-erheben/",
    ),
    "Alzey-Land": dict(
        street="Weinrufstraße", postal_code="55232", city="Alzey", email="info@alzey-land.de",
        dept="Fachbereich II - Bauen und Umwelt", tier="stark",
        quote="'Erschließungs- und Ausbaubeiträge' als Aufgabenblock im amtlichen Telefonverzeichnis unter Fachbereich II - Bauen und Umwelt",
        url="https://www.alzey-land.de/vg-wAssets/docs/rathaus-buergerservice/2023_TelefonverzeichnisVG_01_11_2023.doc.pdf",
    ),
    "Zell (Mosel)": dict(
        street="Schloßstraße", postal_code="56856", city="Zell (Mosel)", email="vgzell@vg-zell.de",
        dept="Sachgebiet 3.1 - Allg. Bauverwaltung, Klimaschutz, Infrastruktur", tier="stark",
        quote="Leistungsseite 'Anliegerbeiträge' nennt Erschließungsbeiträge wörtlich, zuständige Stelle Sachgebiet 3.1",
        url="https://www.zell-mosel.de/buergerservice/leistungen/RLP:entry:214659/anliegerbeitraege/",
    ),
    "Westerburg": dict(
        street="Neumarkt", postal_code="56457", city="Westerburg", email="poststelle@vg-westerburg.de",
        dept="4 - Bauabteilung", tier="stark",
        quote="'Straßen- und Wegeunterhaltung, Festsetzung und Erhebung von Erschließungs- und Straßenausbaubeiträgen' als Aufgabe der '4 - Bauabteilung'",
        url="https://www.vg-westerburg.de/buergerservice/abteilungen/RLP:department:493/4-bauabteilung/",
    ),
    "Diez": dict(
        street="Louise-Seher-Straße", postal_code="65582", city="Diez", email="verwaltung@vgdiez.de",
        dept="Fachbereich 3 - Planen, Bauen, Umwelt (Sachgebiet Ausbau- und Erschließungsrecht)", tier="schwaecher",
        quote="'Bauleitplanung, Raumordnung, Verkehrsplanung, Ausbau- und Erschließungsrecht' als Sachgebiete des Fachbereichs 3 - Begriff lautet 'Erschließungsrecht', nicht wörtlich 'Erschließungsbeiträge'",
        url="https://www.vgdiez.de/vg_diez/Verwaltung/Unsere%20Fachbereiche/Planen,%20Bauen,%20Umwelt/",
    ),
    "Oberes Glantal": dict(
        street="Rathausstraße", postal_code="66901", city="Schönenberg-Kübelberg", email="poststelle@vgog.de",
        dept="Sachgebiet 1 B 2.3 - Erschließungs- und Ausbaubeiträge", tier="schwaecher",
        quote="'Sachgebiet 1 B 2.3 Erschließungs- und Ausbaubeiträge' - Quelle service.rlp.de per Bot-Schutz blockiert, nur über Suchindex-Snippets konsistent reproduziert, nicht selbst am Wortlaut verifizierbar",
        url="https://service.rlp.de/detail?areaId=36978&ouId=208958593&pstId=202043647",
    ),
    "Bernkastel-Kues": dict(
        street="Gestade", postal_code="54470", city="Bernkastel-Kues", email="info@bernkastel-kues.de",
        dept="FB II Finanzen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Leistung/Zuständigkeit unter Fachbereich 'FB II Finanzen'",
        url="https://www.bernkastel-kues.de/buergerservice/leistungen/RLP:entry:221717/erschliessungsbeitrag-zahlen/",
    ),
    "Rennerod": dict(
        street="Hauptstraße", postal_code="56477", city="Rennerod", email="info@rennerod.rlp.de",
        dept="Bauabteilung", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Zuständigkeit der Bauabteilung",
        url="https://www.rennerod.de/buergerservice-views/abteilungen/RLP:department:406/bauabteilung/",
    ),
    "Loreley": dict(
        street="Dolkstraße", postal_code="56346", city="Sankt Goarshausen", email="rathaus@vg-loreley.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen & Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Zuständigkeit des Fachbereichs 2",
        url="https://www.vg-loreley.de/buergerservice-modul/abteilungen/RLP:department:351013/fachbereich-2-natuerliche-lebensgrundlagen-bauen/",
    ),
    "Kirner Land": dict(
        street="Bahnhofstraße", postal_code="55606", city="Kirn", email="verwaltung@kirner-land.de",
        dept="Fachbereich 4 - Bauen und Soziales, Sachgebiet 4.11 Ausbau- und Erschließungsbeiträge", tier="stark",
        quote="'Fachbereich 4 - Bauen und Soziales ... 4.11 Ausbau- und Erschließungsbeiträge'",
        url="https://www.kirner-land.de/verwaltung/fachbereiche",
    ),
    "Bad Bergzabern": dict(
        street="Königstraße", postal_code="76887", city="Bad Bergzabern", email="info@vgbza.de",
        dept="Abteilung 4 - Finanzen", tier="stark",
        quote="'Erschließungsbeiträge' als separater Eintrag in der vollständigen Zuständigkeiten-Liste der Abteilung 4 - Finanzen (Sachgebietsleitung Axel Hofmann)",
        url="https://www.vg-bad-bergzabern.de/buergerservice-views/abteilungen/RLP:department:213162/abteilung-4-finanzen/",
    ),
    "Thalfang am Erbeskopf": dict(
        street="Saarstraße", postal_code="54424", city="Thalfang", email="info@rathaus-thalfang.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Telefonverzeichnis: 'Traudt, Alexandra ... Ausbau- u. Erschließungsbeiträge', Fachbereich 2",
        url="https://www.erbeskopf.de/telefonverzeichnis.html",
    ),
    "Wallmerod": dict(
        street="Gerichtsstraße", postal_code="56414", city="Wallmerod", email="poststelle@wallmerod.de",
        dept="4.3 - Abgaben (Fachbereich 4 - Finanzen)", tier="schwaecher",
        quote="'Anliegerbeiträge' in der Zuständigkeiten-Liste von 4.3 - Abgaben, exakter Begriff 'Erschließungsbeiträge' nicht wörtlich genannt",
        url="https://www.wallmerod.de/buergerservice-views/abteilungen/RLP:department:339397/4-3-abgaben/",
    ),
    "Rengsdorf-Waldbreitbach": dict(
        street="Westerwaldstraße", postal_code="56579", city="Rengsdorf", email="info@vg-rw.de",
        dept="Fachbereich Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als eigener Punkt in der Zuständigkeiten-Liste der Abteilung 'Bauen' (Fachbereichsleiter Diethelm Stein)",
        url="https://www.rengsdorf-waldbreitbach.de/buergerservice/abteilungen/RLP:department:400/bauen/",
    ),
    "Rhein-Selz": dict(
        street="Santé Ambrogio-Ring", postal_code="55276", city="Oppenheim", email="info@vg-rhein-selz.de",
        dept="Sachgebiet 3.1.4 - Erschließungs- und Ausbaubeiträge", tier="stark",
        quote="'3.1.4 - Erschließungs- und Ausbaubeiträge' (Sachgebietsbezeichnung, u.a. 'Erschließungsbeitrag zahlen')",
        url="https://www.vg-rhein-selz.de/buergerservice/mitarbeiter/RLP:employee:11340/bucher-sandra/",
    ),
    "Thaleischweiler-Wallhalben": dict(
        street="Hauptstraße", postal_code="66987", city="Thaleischweiler-Fröschen", email="info@vgtw.de",
        dept="Fachdienst III.2 - Bauverwaltung", tier="stark",
        quote="'Erschließungsbeitrag zahlen' gelistet unter Fachdienst III.2 - Bauverwaltung",
        url="https://www.vgtw.de/buergerservice/abteilungen/RLP:department:348358/fachdienst-iii-2-bauverwaltung/",
    ),
    "Ruwer": dict(
        street="Untere Kirchstraße", postal_code="54320", city="Waldrach", email="info@ruwer.de",
        dept="Fachbereich 3 - Natürl. Lebensraum und Bauen", tier="stark",
        quote="'Erschließungs- und Ausbaubeiträge - Satzungen, Veranlagungen, Stundungen, Rechtsstreitigkeiten' als Aufgabe Michael Schmitt, Fachbereich 3",
        url="https://www.ruwer.de/buergerservice/mitarbeiter/RLP:employee:48535/schmitt-michael/",
    ),
    "Schweich an der Römischen Weinstraße": dict(
        street="Brückenstraße", postal_code="54338", city="Schweich", email="info@schweich.de",
        dept="Sachgebiet 2.5.2 - Erschließungs- und Ausbaubeiträge, wiederkehrende Beiträge", tier="stark",
        quote="'2.5.2 Erschließungs- und Ausbaubeiträge, wiederkehrende Beiträge' (Sachgebietstitel, Fachbereich 2.5 Abgaben)",
        url="https://www.schweich.de/buergerservice/abteilungen/RLP:department:368998/2-5-2-erschliessungs-und-ausbaubeitraege-wiederkehrende-beitraege/",
    ),
    "Kastellaun": dict(
        street="Kirchstraße", postal_code="56288", city="Kastellaun", email="info@kastellaun.de",
        dept="Fachbereich 3 - Bauen, Sachgebiet Erschließungs- und Ausbaubeiträge", tier="stark",
        quote="'Erschließungs- und Ausbaubeiträge' im amtlichen Telefonverzeichnis, Fachbereich 3 - Bauen (Heidrun Bernd)",
        url="https://www.kastellaun.de/rathaus/verwaltung/telefonverzeichnis/",
    ),
    "Rhein-Mosel": dict(
        street="Bahnhofstraße", postal_code="56330", city="Kobern-Gondorf", email="info@vgrm.de",
        dept="Fachbereich 3 - Natürliche Lebensgrundlagen und Bauen, Teilbereich 3.1 - Bauverwaltung", tier="stark",
        quote="'Erschließungsbeitrag zahlen' unter Thomas Zils, Teilbereichsleitung 3.1 - Bauverwaltung",
        url="https://www.vg-rhein-mosel.de/vgrm/Rathaus%20u.%20Gemeinden/Ansprechpartner/?bsinst=0&bstype=a_get&bsparam=RLP%3Adepartment%3A268861",
    ),
    "Maifeld": dict(
        street="Marktplatz", postal_code="56751", city="Polch", email="info@maifeld.de",
        dept="Fachbereich 4 - Bauen und Umwelt, Teilgebiet 4.1 Bauverwaltung", tier="stark",
        quote="'Ausbau- und Erschließungsbeiträge' unter Fachbereich 4 - Bauen und Umwelt (Fachbereich 2 - Finanzen listet Gemeindeabgaben 'ausgenommen Ausbau- und Erschließungsbeiträge')",
        url="https://www.maifeld.de/rathaus-buergerservice/organigramm-geschaeftsverteilungsplan/geschaeftsverteilungsplan-2024.pdf?cid=qdj",
    ),
    "Bad Marienberg (Westerwald)": dict(
        street="Kirburger Straße", postal_code="56470", city="Bad Marienberg (Westerwald)", email="verbandsgemeinde@bad-marienberg.de",
        dept="Fachbereich 5 - Finanzen - Haushalt", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen' nennt 'Fachbereich 5 - Finanzen - Haushalt' als zuständigen Fachbereich",
        url="https://www.bad-marienberg.de/buergerservice/leistungen/RLP:entry:202065479:071435001:ANLR/erschliessungsbeitrag-zahlen/",
    ),
    "Zweibrücken-Land": dict(
        street="Landauer Straße", postal_code="66482", city="Zweibrücken", email="info@vgzwland.de",
        dept="Bauverwaltung und öffentliche Einrichtungen", tier="stark",
        quote="Abteilungsseite listet wörtlich 'Erschließungsbeitrag zahlen'",
        url="https://www.vgzwland.de/buergerservice-1/abteilungen/RLP:department:348317/bauverwaltung-und-oeffentliche-einrichtungen/",
    ),
    "Langenlonsheim-Stromberg": dict(
        street="Naheweinstraße", postal_code="55450", city="Langenlonsheim", email="rathaus@vg-ls.de",
        dept="Fachbereich 3 - Bauen", tier="stark",
        quote="Abteilungsseite führt wörtlich die Leistung 'Erschließungsbeitrag zahlen' auf",
        url="https://www.langenlonsheim-stromberg.de/verbandsgemeinde-langenlonsheim-stromberg/buergerservice/abteilungen/RLP:department:346277/fachbereich-3-bauen/",
    ),
    "Kirchheimbolanden": dict(
        street="Neue Allee", postal_code="67292", city="Kirchheimbolanden", email="vg@kirchheimbolanden.de",
        dept="Finanzverwaltung - Abgaben", tier="schwaecher",
        quote="Leistungsseite 'Erschließungsbeiträge erheben' + offizielles Organigramm: Sachgebiet 'Abgaben' der Abteilung Finanzverwaltung - Zuordnung ergibt sich aus Zusammenführung zweier Quellen, nicht direkt verknüpft",
        url="https://www.kirchheimbolanden.de/de/bolanden-rathaus-leistungen-detail/leistung/439/wohnort/231/zustaendigestellen/299/erschliessungsbeitraege_erheben.html",
    ),
    "Ulmen": dict(
        street="Marktplatz", postal_code="56766", city="Ulmen", email="info@ulmen.de",
        dept="FB 2: Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Anliegerbeiträge' nennt Erschließungsbeiträge wörtlich, zuständige Abteilung FB 2",
        url="https://www.ulmen.de/buergerservice-1/leistungen/RLP:entry:246708/anliegerbeitraege/",
    ),
    "Traben-Trarbach": dict(
        street="Am Markt", postal_code="56841", city="Traben-Trarbach", email="rathaus@vgtt.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilung Fachbereich 2",
        url="https://www.vgtt.de/buergerservice2/leistungen/RLP:entry:251838/erschliessungsbeitrag-zahlen/",
    ),
    "Puderbach": dict(
        street="Hauptstraße", postal_code="56305", city="Puderbach", email="rathaus@puderbach.de",
        dept="Fachbereich 3 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilung Fachbereich 3",
        url="https://www.puderbach.de/buergerservice/leistungen/RLP:entry:36000/erschliessungsbeitrag-zahlen/",
    ),
    "Edenkoben": dict(
        street="Poststraße", postal_code="67480", city="Edenkoben", email="info@vg-edenkoben.de",
        dept="Fachbereich 2 - Finanzen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilungen Fachbereich 2 - Finanzen (Verbandsgemeindewerke nur für Kanal/Wasser)",
        url="https://www.vg-edenkoben.de/buergerservice/leistungen/RLP:entry:69023:ANLR-VLR/erschliessungsbeitrag-zahlen/",
    ),
    "Dahner Felsenland": dict(
        street="Schulstraße", postal_code="66994", city="Dahn", email="info@dahner-felsenland.de",
        dept="Finanzen / Kommunale Abgaben", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zugeordnete Abteilungen 'Finanzen' und 'Kommunale Abgaben'",
        url="https://www.dahner-felsenland.net/vg_dahner_felsenland/Verwaltung/Verwaltungsleistungen%20von%20A-Z/?bsinst=0&bstype=l_get&bsparam=524c503a656e7472793a323235333735343a414e4c522d564c52",
    ),
    "Landau-Land": dict(
        street="An 44 Nr.31", postal_code="76829", city="Landau in der Pfalz", email="info@landau-land.de",
        dept="Fachbereich Planen, Bauen und Umwelt", tier="schwaecher",
        quote="'Beitragsveranlagung im Rahmen von Erschließungs- und Ausbaumaßnahmen von Verkehrsanlagen' - nicht wörtlich 'Erschließungsbeitrag'",
        url="https://www.landau-land.de/politik-verwaltung/bauen/",
    ),
    "Baumholder": dict(
        street="Am Weiherdamm", postal_code="55774", city="Baumholder", email="verwaltung@vgv-baumholder.de",
        dept="Planung und Bauwesen (Fachbereich 3)", tier="stark",
        quote="Leistungsseite 'Erschließung von Grundstücken': 'Zuständige Abteilungen: Planung und Bauwesen', Link 'siehe auch Erschließungsbeiträge'",
        url="https://www.vgv-baumholder.de/de/buergerservice/leistungen/RLP:entry:20478/erschliessung-von-grundstuecken/",
    ),
    "Bad Kreuznach": dict(
        street="Rheingrafenstraße", postal_code="55583", city="Bad Kreuznach", email="info@vgvkh.de",
        dept="Bauverwaltung", tier="stark",
        quote="'Ausbau- und Erschließungsbeiträge' unter den Zuständigkeiten der Abteilung Bauverwaltung",
        url="https://www.vg-badkreuznach.de/vg_bad_kreuznach/Verwaltung/Mitarbeiterliste/?bsinst=0&bstype=a_get&bsparam=RLP%3Adepartment%3A269035",
    ),
    "Annweiler am Trifels": dict(
        street="Meßplatz", postal_code="76855", city="Annweiler am Trifels", email="info@annweiler.rlp.de",
        dept="Fachbereich III - Bauen", tier="stark",
        quote="Leistungsseite 'Anliegerbeiträge' nennt Erschließungsbeiträge wörtlich, zuständige Abteilung Fachbereich III - Bauen",
        url="https://www.vg-annweiler.de/buergerservice-2/leistungen/RLP:entry:165798/anliegerbeitraege/",
    ),
    "Wörrstadt": dict(
        street="Zum Römergrund", postal_code="55286", city="Wörrstadt", email="info@vgwoerrstadt.de",
        dept="Fachbereich Bauen und Umwelt (Sachgebiet Beitragswesen)", tier="stark",
        quote="Seite 'Beitragswesen': 'Erschließungsbeiträge werden für die erstmalige Herstellung von Erschließungsanlagen ... erhoben.'",
        url="https://www.vgwoerrstadt.de/Bauen-Umwelt-Wirtschaft/Bauen-Umwelt/Beitragswesen/",
    ),
    "Göllheim": dict(
        street="Freiherr-vom-Stein-Straße", postal_code="67307", city="Göllheim", email="info@vg-goellheim.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' unter den Zuständigkeiten des Fachbereichs 2",
        url="https://www.vg-goellheim.de/buergerservice/abteilungen/RLP:department:93385/fachbereich-2-natuerliche-lebensgrundlagen-und-bauen/",
    ),
    "Winnweiler": dict(
        street="Jakobstraße", postal_code="67722", city="Winnweiler", email="info@winnweiler-vg.de",
        dept="Bauverwaltung, Öffentliche Einrichtungen und Technische Dienste", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilung wörtlich genannt",
        url="https://www.winnweiler-vg.de/buergerservice/leistungen/RLP:entry:69271:ANLR-VLR/erschliessungsbeitrag-zahlen/",
    ),
    "Wirges": dict(
        street="Bahnhofstraße", postal_code="56422", city="Wirges", email="info@wirges.de",
        dept="Fachbereich 4 - Verbandsgemeindewerke und Tiefbau", tier="stark",
        quote="Zuständigkeitenliste: 'Abwasser beseitigen, ..., Erschließungsbeitrag zahlen, 9 weitere'",
        url="https://www.wirges.de/buergerservice-views/abteilungen/RLP:department:219025/fachbereich-4-verbandsgemeindewerke-und-tiefbau/",
    ),
    "Hamm (Sieg)": dict(
        street="Lindenallee", postal_code="57577", city="Hamm (Sieg)", email="rathaus@hamm-sieg.de",
        dept="FB 2 - Bauen", tier="schwaecher",
        quote="Leistungsseite 'Wiederkehrende Beiträge für Verkehrsanlagen zahlen', zuständige Abteilung FB 2 - Bauen - exakter Begriff 'Erschließungsbeitrag' nicht als eigene Leistung gefunden",
        url="https://www.hamm-sieg.de/de/buergerservice/leistungen/RLP:entry:8934/wiederkehrende-beitraege-fuer-verkehrsanlagen-zahlen/",
    ),
    "Altenahr": dict(
        street="Roßberg", postal_code="53505", city="Altenahr", email="info@altenahr.de",
        dept="Finanzabteilung (Abteilung 5)", tier="stark",
        quote="'Was erledige ich wo': 'Erschließungsbeiträge: Herr Wasserzier' - laut Organigramm Abteilungsleiter der Finanzabteilung",
        url="https://www.altenahr.de/rathaus/buergerservice/was-erledige-ich-wo",
    ),
    "Otterbach-Otterberg": dict(
        street="Hauptstraße", postal_code="67697", city="Otterberg", email="postfach@otterbach-otterberg.de",
        dept="Fachbereich 4 - Finanzen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilungen Fachbereich 4 - Finanzen",
        url="https://www.otterbach-otterberg.de/buergerservice/leistungen/RLP:entry:225487/erschliessungsbeitrag-zahlen/",
    ),
    "Konz": dict(
        street="Am Markt", postal_code="54329", city="Konz", email="rathaus@konz.de",
        dept="Fachbereich 2 - Finanzen", tier="stark",
        quote="'... so werden keine wiederkehrenden Beiträge, sondern Erschließungsbeiträge gemäß den Vorschriften des Baugesetzbuches erhoben.' (Seite 'Ausbaubeiträge', Finanzen)",
        url="https://www.konz.de/de/verwaltung-politik/finanzen/ausbaubeitraege/",
    ),
    "Wonnegau": dict(
        street="Am Schneller", postal_code="67574", city="Osthofen", email="post@vg-wonnegau.de",
        dept="Fachbereich 3 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="'Erschließungs-/ Ausbaubeiträge, Stundung/ Verrentung Beiträge, wiederkehrende Beiträge Verkehrsanlagen' (Achim Wiener, Fachbereich 3)",
        url="https://www.vg-wonnegau.de/Service/index.php?object=tx,3899.1.1&ModID=9&FID=3899.87.1&NavID=3899.7",
    ),
    "Trier-Land": dict(
        street="Gartenfeldstr.", postal_code="54295", city="Trier", email="rathaus@trier-land.de",
        dept="Fachbereich 2 - Finanzen (Sachgebiet Abgaben)", tier="stark",
        quote="Leistung 'Erschließungsbeitrag zahlen' zugeordnet zu 'Fachbereich 2 - Finanzen', Ansprechpartner Sachgebietsleiter Abgaben",
        url="https://www.trier-land.de/buergerservice/leistungen/RLP:entry:120553:ANLR-VLR/erschliessungsbeitrag-zahlen/",
    ),
    "Ransbach-Baumbach": dict(
        street="Rheinstraße", postal_code="56235", city="Ransbach-Baumbach", email="info@ransbach-baumbach.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="schwaecher",
        quote="'Anliegerbeiträge, Wiederkehrende Beiträge, ...' - exakter Begriff 'Erschließungsbeitrag' nicht gefunden, nur verwandte Begriffe",
        url="https://www.ransbach-baumbach.de/B%C3%BCrger-Einwohner/Verwaltung/Dienstleistungen/index.php?object=tx,3768.1.1&ModID=9&FID=3768.81.1&NavID=3768.14.1",
    ),
    "Daaden-Herdorf": dict(
        street="Bahnhofstraße", postal_code="57567", city="Daaden", email="info@daaden-herdorf.de",
        dept="Fachbereich 3 - Bauen und Umwelt", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Stelle Fachbereich 3 - Bauen und Umwelt",
        url="https://www.daaden-herdorf.de/buergerservice-1/leistungen/RLP:entry:202065479:071325003:ANLR/erschliessungsbeitrag-zahlen/",
    ),
    "Sprendlingen-Gensingen": dict(
        street="Elisabethenstraße", postal_code="55576", city="Sprendlingen", email="info@vg-sg.de",
        dept="Planen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließung von Grundstücken' (BauGB-Zufahrt), zuständige Abteilung 'Planen und Bauen', nennt zusätzlich 'Erschließungsbeiträge' wörtlich mit Gemeindeanteil von mind. 10% - eigenständig nachverifiziert",
        url="https://www.sprendlingen-gensingen.de/buergerservice/leistungen/RLP:entry:196296/erschliessung-von-grundstuecken/",
    ),
    "Pirmasens-Land": dict(
        street="Bahnhofstraße", postal_code="66953", city="Pirmasens", email="info@pirmasens-land.de",
        dept="3.7 Beiträge (Fachbereich 3 - Bauliche Infrastruktur)", tier="stark",
        quote="Mitarbeiterseite Jasmin Stranz, Abteilung 3.7 Beiträge, listet 'Erschließungsbeitrag zahlen'",
        url="https://www.pirmasens-land.de/buergerservice/mitarbeiter/RLP:employee:88570/stranz-jasmin/",
    ),
    "Rhein-Nahe": dict(
        street="Koblenzer Straße", postal_code="55411", city="Bingen-Bingerbrück", email="verwaltung@vgrn.de",
        dept="Sachgebiet 2.1 Finanzen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' unter den Zuständigkeiten von Sachgebiet 2.1 Finanzen",
        url="https://www.vgrn.de/buergerservice-2/abteilungen/RLP:department:340491/sachgebiet-2-1-finanzen/",
    ),
    "Speicher": dict(
        street="Bahnhofstraße", postal_code="54662", city="Speicher", email="rathaus@vg-speicher.de",
        dept="Abteilung 02 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Anliegerbeiträge' nennt Erschließungsbeiträge wörtlich, zuständige Stelle Abteilung 02",
        url="https://www.vg-speicher.de/buergerservice-1/leistungen/RLP:entry:62958/anliegerbeitraege/",
    ),
    "Nieder-Olm": dict(
        street="Pariser Straße", postal_code="55268", city="Nieder-Olm", email="rathaus@vg-nieder-olm.de",
        dept="Bauen, Umwelt und Verkehr", tier="schwaecher",
        quote="Leistung 'Wiederkehrende Beiträge für Verkehrsanlagen zahlen' und 'Einmalige und wiederkehrende Straßenbeiträge' - exakter Begriff 'Erschließungsbeitrag' nicht wörtlich gefunden",
        url="https://www.vg-nieder-olm.de/buergerservice/leistungen/RLP:entry:194613/wiederkehrende-beitraege-fuer-verkehrsanlagen-zahlen/",
    ),
    "Weilerbach": dict(
        street="Rummelstraße", postal_code="67685", city="Weilerbach", email="info@vg-weilerbach.de",
        dept="Sachgebiet 3.1.4 - Erschließungs- und Ausbaubeiträge", tier="stark",
        quote="Geschäftsverteilungsplan: 'Sachgebiet 3.1.4 - Erschließungs- und Ausbaubeiträge' - eigenständig per PDF-Volltext nachverifiziert",
        url="https://www.weilerbach.de/rathaus/geschaeftsverteilungsplan/geschaeftsverteilungsplan-vg-weilerbach.pdf",
    ),
    "Waldfischbach-Burgalben": dict(
        street="Friedhofstraße", postal_code="67714", city="Waldfischbach-Burgalben", email="info@waldfischbach-burgalben.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständig Fachbereich 2",
        url="https://www.vgwaldfischbach-burgalben.de/buergerservice/leistungen/RLP:entry:199311/erschliessungsbeitrag-zahlen/",
    ),
    "Gau-Algesheim": dict(
        street="Hospitalstraße", postal_code="55435", city="Gau-Algesheim", email="info@vg-gau-algesheim.de",
        dept="Fachbereich 2 - Finanzen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen' nennt Ansprechpartnerin 'Frau Tanja May', Abteilung '2 - Finanzen'",
        url="https://www.vg-gau-algesheim.de/vg_gau_algesheim/Rathaus/Leistungen%20A-Z/?bsinst=0&bstype=l_get&bsparam=524c503a656e7472793a323139343230",
    ),
    "Enkenbach-Alsenborn": dict(
        street="Hauptstraße", postal_code="67677", city="Enkenbach-Alsenborn", email="info@enkenbach-alsenborn.de",
        dept="Abt. 4 - Bauabteilung", tier="stark",
        quote="Abteilungsseite 'Abt. 4 - Bauabteilung' listet 'Erschließungsbeitrag zahlen'",
        url="https://www.enkenbach-alsenborn.de/buergerservice/abteilungen/RLP:department:346129/abt-4-bauabteilung/",
    ),
    "Freinsheim": dict(
        street="Bahnhofstraße", postal_code="67251", city="Freinsheim", email="verwaltung@vg-freinsheim.de",
        dept="Fachbereich 3 - Finanzen, Sachgebiet 3.4 Ausbau- und Erschließungsbeiträge", tier="stark",
        quote="Verwaltungsgliederungsplan: 'Fachbereich 3 Finanzen' - Sachgebiet '3.4 Ausbau- und Erschließungsbeiträge'",
        url="https://www.vg-freinsheim.de/rathaus-politik/verwaltung/verwaltungsgliederung/2026-03-01-verwaltungsgliederungsplan.pdf",
    ),
    "Wöllstein": dict(
        street="Bahnhofstraße", postal_code="55597", city="Wöllstein", email="info@vg-woellstein.org",
        dept="FB III - Bauen und natürliche Lebensgrundlagen", tier="stark",
        quote="Fachbereichsseite listet Sachgebiet 'Bauleitplanung, Ausbau- und Erschließungsbeiträge'",
        url="https://www.woellstein.de/verwaltung/ansprechpartner-und-zustaendigkeiten/fachbereiche/fb-iii-bauen-und-natuerliche-lebensgrundlagen/",
    ),
    "Monsheim": dict(
        street="Alzeyer Straße", postal_code="67590", city="Monsheim", email="info@vg-monsheim.de",
        dept="Fachbereich 1 - Finanzen, Sachgebiet 1.7 Erschließungs- und Ausbaubeiträge", tier="stark",
        quote="Abteilungsseite 'Fachbereich 1 - Finanzen' führt 'Sachgebiet 1.7 - Erschließungs- und Ausbaubeiträge' auf",
        url="https://www.vg-monsheim.de/buergerservice/abteilungen/RLP:department:339818/fachbereich-1-finanzen/",
    ),
    "Linz am Rhein": dict(
        street="Am Schoppbüchel", postal_code="53545", city="Linz am Rhein", email="info@vg-linz.de",
        dept="Fachbereich Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - 'Ihre zuständige Stelle: Verbandsgemeinde Linz am Rhein - Bauen'",
        url="https://service.rlp.de/detail?areaId=40842&ags=07&area=&pstId=202065479&searchtext=Erschlie%C3%9Fungsbeitrag%20zahlen&infotype=0",
    ),
    "Kandel": dict(
        street="Gartenstraße", postal_code="76870", city="Kandel", email="info@vg-kandel.de",
        dept="Fachbereich 4 - Finanzen, Sachgebiet 4.5 Erschließung und Ausbaubeiträge", tier="stark",
        quote="'4.5 Erschließung und Ausbaubeiträge' mit Leistung 'Erschließungsbeitrag zahlen' unter Fachbereich 4 - Finanzen",
        url="https://www.vg-kandel.de/vg_kandel/Verwaltung/B%C3%BCrgerservice/Fachbereiche/?bsinst=0&bstype=a_get&bsparam=RLP%3Adepartment%3A352",
    ),
    "Lambrecht (Pfalz)": dict(
        street="Sommerbergstraße", postal_code="67466", city="Lambrecht (Pfalz)", email="info@vg-lambrecht.de",
        dept="Fachbereich 3 - Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - 'Ihre zuständige Stelle: Verbandsgemeinde Lambrecht (Pfalz) - Fachbereich 3 - Bauen'",
        url="https://service.rlp.de/detail?areaId=38510&ags=07332032&area=Lambrecht%20(Pfalz)%20(674...)&pstId=202065479&searchtext=Erschlie%C3%9Fungsbeitrag%20zahlen&infotype=0",
    ),
    "Weißenthurm": dict(
        street="Kärlicher Straße", postal_code="56575", city="Weißenthurm", email="info@vgwthurm.de",
        dept="Fachbereich 6 - Kommunale Betriebe", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - 'Ihre zuständige Stelle: Verbandsgemeinde Weißenthurm - Fachbereich 6 - Kommunale Betriebe'",
        url="https://service.rlp.de/detail?areaId=40369&ags=07&area=&pstId=202065479&searchtext=Erschlie%C3%9Fungsbeitrag%20zahlen&infotype=0",
    ),
    "Dierdorf": dict(
        street="Neuwieder Straße", postal_code="56269", city="Dierdorf", email="info@vg-dierdorf.de",
        dept="Sachgebiet 2.6 - Erschließungs- & Ausbaubeiträge, Konzessionsabgaben, Jagd, Zuwendungsanträge", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - 'Ihre zuständige Stelle: Verbandsgemeinde Dierdorf - 2.6 Erschließungs- & Ausbaubeiträge, ...'",
        url="https://service.rlp.de/detail?areaId=40785&area=Dierdorf&ags=07138&searchtext=Erschlie%C3%9Fungsbeitrag&infotype=0&sort=&pstId=202065479",
    ),
    "Wissen": dict(
        street="Rathausstr.", postal_code="57537", city="Wissen", email="info@rathaus-wissen.de",
        dept="Sachgebiet Beiträge", tier="stark",
        quote="'Erschließungsbeitrag zahlen' - 'Die für Sie nächstgelegene zuständige Stelle: Verbandsgemeindeverwaltung Wissen ... Sachgebiet Beiträge'",
        url="https://service.rlp.de/detail?areaId=43347&ags=07132117&area=Wissen%20(575...)&pstId=202065479&searchtext=Erschlie%C3%9Fungsbeitrag%20zahlen&infotype=0",
    ),
    "Kirchen (Sieg)": dict(
        street="Lindenstraße", postal_code="57548", city="Kirchen (Sieg)", email="vg-kirchen@kirchen-sieg.de",
        dept="Bereich Beiträge (Sachgebiet Abgaben)", tier="stark",
        quote="'Der Bereich Beiträge ist zuständig für die Erhebung von Ausbau- und Erschließungsbeiträgen in den 5 Ortsgemeinden und der Stadt Kirchen.'",
        url="https://www.kirchen-sieg.de/verbandsgemeinde-stadt-ortsgemeinden/verbandsgemeinde/rathaus/abgaben",
    ),
    "Lingenfeld": dict(
        street="Hauptstraße", postal_code="67360", city="Lingenfeld", email="info@vg-lingenfeld.de",
        dept="Bauabteilung (Fachbereich 2 - Bauen und natürliche Lebensgrundlagen)", tier="stark",
        quote="'Erschließungs - und Ausbaubeitragsrecht' (Bauabteilung)",
        url="https://www.vg-lingenfeld.de/buergerservice/abteilungen/RLP:department:356038/bauabteilung/",
    ),
    "Rodalben": dict(
        street="Am Rathaus", postal_code="66976", city="Rodalben", email="info@rodalben.de",
        dept="Steuern und Abgaben", tier="stark",
        quote="'Ausbau- und Erschließungsbeiträge' (Zimmer 131, Frau Bold)",
        url="https://www.rodalben.de/vg_rodalben/Verwaltung/B%C3%BCrgerservice/Was%20erledige%20ich%20wo%3F/",
    ),
    "Mendig": dict(
        street="Marktplatz", postal_code="56743", city="Mendig", email="info@mendig.de",
        dept="Fachbereich 4 - Bauwesen, Wasser & Abwasser", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Leistung Nr. 14 von 29 unter Fachbereich 4",
        url="https://www.mendig.de/buergerservice/abteilungen/RLP:department:263657/fachbereich-4-bauwesen-wasser-abwasser/",
    ),
    "Pellenz": dict(
        street="Rathausstr.", postal_code="56637", city="Plaidt", email="verbandsgemeinde@pellenz.de",
        dept="Fachbereich 2.1 - Hochbau", tier="stark",
        quote="'Erschließungsbeiträge' als verlinkte Leistung auf der Abteilungsseite Fachbereich 2.1 - Hochbau",
        url="https://www.pellenz.de/buergerservice-schablonen/abteilungen/RLP:department:390/fachbereich-2-1-hochbau/",
    ),
    "Bodenheim": dict(
        street="Am Dollesplatz", postal_code="55294", city="Bodenheim", email="verwaltung@vg-bodenheim.de",
        dept="Organisation und Finanzen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' unter 'Organisation und Finanzen', bestätigt über service.rlp.de",
        url="https://www.vg-bodenheim.de/buergerservice/abteilungen/RLP:department:53/organisation-und-finanzen/",
    ),
    "Ramstein-Miesenbach": dict(
        street="Am Neuen Markt", postal_code="66877", city="Ramstein-Miesenbach", email="info@ramstein.de",
        dept="Bauabteilung (Abt. IV - Bauverwaltung)", tier="stark",
        quote="Amtliche Stellenausschreibung: 'Mitarbeiter/in in der Bauabteilung / Bereich Erschließungsbeiträge ... Gesamtkalkulation, Festsetzung und Erhebung von Beiträgen (Erschließungsbeiträge, ...)'",
        url="https://www.ramstein-miesenbach.de/de/aktuelles/2025/dezember-2025/mitarbeiter-in-fuer-erschliessungsbeitraege-in-der-bauabteilung-gesucht/",
    ),
    "Bruchmühlbach-Miesau": dict(
        street="Am Rathaus", postal_code="66892", city="Bruchmühlbach-Miesau", email="info@bruchmuehlbach-miesau.de",
        dept="Fachbereich II - Natürliche Lebensgrundlagen und Bauen, Sachgebiet 1.4", tier="stark",
        quote="'1.4 Ausbau- / Erschließungsbeiträge' (Verwaltungsgliederungsplan, Fachbereichsgruppe Verwaltung und Recht II.1)",
        url="https://www.bruchmuehlbach-miesau.de/rathaus/behoerdenwegweiser/verwaltungsgliederungs-und-geschaeftsverteilungsplan/januar-2026-verwaltungsgliederungsplan.pdf?cid=r4a",
    ),
    "Deidesheim": dict(
        street="Am Bahnhof", postal_code="67146", city="Deidesheim", email="verwaltung@vg-deidesheim.rlp.de",
        dept="Fachbereich 5 - Finanzen", tier="stark",
        quote="'Zuständig für: Deidesheim (Verbandsgemeinde): Erschließungsbeitrag zahlen' (Fachbereich 5 - Finanzen)",
        url="https://service.rlp.de/detail?areaId=38352&ags=07332009&area=Deidesheim%20(671...)&pstId=202065479&searchtext=Erschlie%C3%9Fungsbeitrag%20zahlen&infotype=0",
    ),
    "Eich": dict(
        street="Hauptstraße", postal_code="67575", city="Eich", email="poststelle@vg-eich.de",
        dept="Fachbereich III - Natürliche Grundlagen und Bauen", tier="stark",
        quote="'Erschließungs- / Ausbaubeiträge, Naturschutz' (Telefonverzeichnis, Celina Welker)",
        url="https://www.vg-eich.de/verwaltung/verwaltung/mitarbeitende/telefonverzeichnis-vg-eich.pdf",
    ),
    "Vallendar": dict(
        street="Rathausplatz", postal_code="56179", city="Vallendar", email="rathaus@vg-vallendar.de",
        dept="Fachbereich 2 Bauen und Umwelt", tier="stark",
        quote="'Erschließungsbeitrag zahlen' als Leistung unter Fachbereich 2 Bauen und Umwelt",
        url="https://www.vg-vallendar.de/buergerservice-views/abteilungen/RLP:department:346066/fachbereich-2-bauen-und-umwelt/",
    ),
    "Asbach": dict(
        street="Flammersfelder Straße", postal_code="53567", city="Asbach", email="rathaus@vg-asbach.de",
        dept="Bau- und Rechtsamt", tier="stark",
        quote="'Erschließungsbeitrag zahlen' in der Zuständigkeitenliste des Bau- und Rechtsamts",
        url="https://www.vg-asbach.de/buergerservice/abteilungen/RLP:department:346793/bau-und-rechtsamt/",
    ),
    "Höhr-Grenzhausen": dict(
        street="Rathausstraße", postal_code="56203", city="Höhr-Grenzhausen", email="poststelle@hoehr-grenzhausen.de",
        dept="Fachbereich V - Verbandsgemeindewerke", tier="stark",
        quote="'Erschließungsbeitrag zahlen' explizit in der Zuständigkeitenliste dieses (sonst wasser-/abwasserbezogenen) Fachbereichs, zusätzlich über Mitarbeiterseite bestätigt",
        url="https://www.hoehr-grenzhausen.de/buergerservice-views/abteilungen/RLP:department:335/fachbereich-v-verbandsgemeindewerke/",
    ),
    "Bad Hönningen": dict(
        street="Marktstraße", postal_code="53557", city="Bad Hönningen", email="info@bad-hoenningen-vg.de",
        dept="Finanzverwaltung", tier="stark",
        quote="'Erschließungsbeitrag zahlen' und 'Erschließungsverträge' unter Zuständigkeiten der Finanzverwaltung",
        url="https://www.bad-hoenningen-vg.de/verwaltung-politik/buergerservice/fachabteilungen/department-list.html",
    ),
    "Rülzheim": dict(
        street="Am Deutschordensplatz", postal_code="76761", city="Rülzheim", email="info@ruelzheim.de",
        dept="Fachbereich 2 - Finanzen", tier="stark",
        quote="Seite 'Erschließungsbeiträge' (Haushalt & Finanzen > Abgaben), Ansprechpartner Fachbereich 2 - Finanzen",
        url="https://www.ruelzheim.de/vg_ruelzheim/de/Verwaltung%20&%20Gemeinden/Haushalt%20&%20Finanzen/Abgaben/Erschlie%C3%9Fungsbeitr%C3%A4ge/",
    ),
    "Wachenheim an der Weinstraße": dict(
        street="Weinstraße", postal_code="67157", city="Wachenheim an der Weinstraße", email="info@vg-wachenheim.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen' unter Fachbereich 2",
        url="https://www.vg-wachenheim.de/buergerservice-1/leistungen/RLP:entry:208680/erschliessungsbeitrag-zahlen/",
    ),
    "Jockgrim": dict(
        street="Untere Buchstraße", postal_code="76751", city="Jockgrim", email="Info@vg-jockgrim.de",
        dept="Fachbereich 2 - Finanzen", tier="schwaecher",
        quote="'Im Fachbereich Finanzen dreht sich alles rund um die Themen Finanzen, Haushalt, Steuern, Gebühren und Beiträge.' - dedizierte Anliegerbeiträge-Seite war nicht abrufbar (404)",
        url="https://www.vg-jockgrim.de/Verwaltung-Rat/Verbandsgemeindeverwaltung/",
    ),
    "Hagenbach": dict(
        street="Ludwigstraße", postal_code="76767", city="Hagenbach", email="info@vg-hagenbach.de",
        dept="Erschließungs- und Ausbaubeiträge", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', Zuständige Abteilungen: 'Erschließungs- und Ausbaubeiträge'",
        url="https://www.vg-hagenbach.de/buergerservice/leistungen/RLP:entry:86913/erschliessungsbeitrag-zahlen/",
    ),
    "Bellheim": dict(
        street="Schubertstraße", postal_code="76756", city="Bellheim", email="verbandsgemeinde@vg-bellheim.de",
        dept="Finanzabteilung", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Abteilung 'Finanzabteilung'",
        url="https://www.bellheim.de/vg_bellheim/Verwaltung/B%C3%BCrgerservice/Informationen%20von%20A%20bis%20Z/?bsinst=0&bstype=l_get&bsparam=524c503a656e7472793a3836373237",
    ),
    "Rheinauen": dict(
        street="Ludwigstraße", postal_code="67165", city="Waldsee", email="info@vg-rheinauen.de",
        dept="Fachbereich 4 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="Leistungsseite 'Erschließung von Grundstücken' (BauGB-Straßenerschließung), Querverweis 'siehe auch Erschließungsbeiträge', zuständig Fachbereich 4",
        url="https://www.vg-rheinauen.de/buergerservice/leistungen/RLP:entry:229117/erschliessung-von-grundstuecken/",
    ),
    "Herxheim": dict(
        street="Obere Hauptstraße", postal_code="76863", city="Herxheim", email="info@herxheim.de",
        dept="Fachbereich 2 - Finanzen", tier="stark",
        quote="Amtliche 'Beitragsrechtliche Stellungnahme in Bezug auf Erschließungsbeiträge' von Fachbereich 2 (Jutta Merz) - eigenständig per PDF-Volltext nachverifiziert",
        url="https://www.vg-herxheim.de/verwaltung/verbandsgemeindeverwaltung/oeffentliche-bekanntmachungen/sonstige/2025/bplan-eisenbahnstrasse-imkalkofen-ambahnhof/13-umweltrelevante-stellungnahmen-voeern.pdf?cid=1r6s",
    ),
    "Römerberg-Dudenhofen": dict(
        street="Konrad-Adenauer-Platz", postal_code="67373", city="Dudenhofen", email="info@vgrd.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen, Sachgebiet 2.1.4", tier="stark",
        quote="Organisationsplan: '2.1.4 Erschließungs- und Ausbaubeiträge' als eigenes Sachgebiet",
        url="https://www.vgrd.de/rathaus/ansprechpartner-a-z/organigramm-vgrd-2023-11-01.pdf?cid=fxv",
    ),
    "Offenbach an der Queich": dict(
        street="Konrad-Lerch-Ring", postal_code="76877", city="Offenbach an der Queich", email="rathaus@offenbach-queich.de",
        dept="Fachbereich 3 - Bauen", tier="stark",
        quote="Leistungsseite 'Erschließungsbeitrag zahlen', zuständige Stelle Fachbereich 3 - Bauen",
        url="https://www.offenbach-queich.de/buergerservice/leistungen/RLP:entry:117970:ANLR-VLR/erschliessungsbeitrag-zahlen/",
    ),
    "Eisenberg (Pfalz)": dict(
        street="Hauptstraße", postal_code="67304", city="Eisenberg (Pfalz)", email="info@vg-eisenberg.de",
        dept="Fachbereich 2 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' in der Aufgabenliste des Fachbereich 2",
        url="https://www.vg-eisenberg.de/buergerservice/abteilungen/RLP:department:311/fachbereich-2-natuerliche-lebensgrundlagen-und-bauen/",
    ),
    "Maxdorf": dict(
        street="Hauptstraße", postal_code="67133", city="Maxdorf", email="willkommen@vg-maxdorf.de",
        dept="Fachbereich 4 - Natürliche Lebensgrundlagen und Bauen", tier="stark",
        quote="'Erschließungsbeitrag zahlen' in der Aufgabenliste des Fachbereich 4",
        url="https://www.vg-maxdorf.de/buergerservice/abteilungen/RLP:department:346616/fachbereich-4-natuerliche-lebensgrundlagen-und-bauen/",
    ),
    "Maikammer": dict(
        street="Immengartenstr.", postal_code="67487", city="Maikammer", email="poststelle@vg-maikammer.de",
        dept="Fachbereich 4 - Finanzen", tier="stark",
        quote="'Ausbaubeiträge, Baugrundstücke, Bauplätze, Erschließungsbeiträge, Fachbereich 4: Finanzen, ...' (Sandra Utech)",
        url="https://vg-maikammer.de/buergerservice/was-erledige-ich-wo/name/sandra-utech/",
    ),
    "Dannstadt-Schauernheim": dict(
        street="Am Rathausplatz", postal_code="67125", city="Dannstadt-Schauernheim", email="info@vgds.de",
        dept="Fachbereich 5 - Kommunale Betriebe", tier="schwaecher",
        quote="'Wiederkehrende Ausbaubeiträge für Verkehrsanlagen' (Frau Kruse) - der dortige wörtliche 'Erschließungsbeiträge'-Eintrag betrifft ausdrücklich Abwasseranlagen (Eigenbetrieb Abwasser), daher bewusst nicht als Treffer verwendet",
        url="https://www.vg-dannstadt-schauernheim.de/rathaus/verbandsgemeindeverwaltung/organisationsplan/2026_Organigramm_01092026.pdf",
    ),
}

# Deckt exakt die von den Recherche-Agenten für die AGS-Zuordnung
# verwendeten VG250-Namen ab (siehe rlp_gemeinde_vg_map.csv, Spalte GEN_V).
GEN_V_OVERRIDES = {
    "Weißenthurm": "Weißenthurm",
}

BELEGLAGE_HINWEIS_SCHWAECHER = (
    "Quelle bestätigt die Zuständigkeit dieser Organisationseinheit ausdrücklich für eine eng "
    "verwandte Funktion, NICHT wörtlich für 'Erschließungsbeiträge' (§ 127 ff. BauGB) - beide "
    "Beitragsarten werden in der kommunalen Praxis nahezu durchgängig von derselben Stelle "
    "bearbeitet, das ist hier aber nicht wörtlich einzeln belegt. Schwächere Beleglage, explizit "
    "als solche markiert. Beleg: {quote}"
)
BELEGLAGE_HINWEIS_STARK = (
    "Quelle bestätigt die Zuständigkeit wörtlich für Erschließungsbeiträge / eine unmittelbar "
    "gleichbedeutende Formulierung. Beleg: {quote}"
)


def _load_ags_lookup():
    import pandas as pd

    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rlp_gemeinde_vg_map.csv")
    df = pd.read_csv(csv_path, dtype=str)
    lookup = {}
    for gen_v, group in df.groupby("GEN_V"):
        lookup[gen_v] = sorted(group["ags8"].tolist())
    return lookup


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

    ags_lookup = _load_ags_lookup()

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"erschliessung-vg-rlp-wave2-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []
        missing_ags = []

        for vg_name, info in VERBANDSGEMEINDEN.items():
            lookup_name = GEN_V_OVERRIDES.get(vg_name, vg_name)
            ags_liste = ags_lookup.get(lookup_name)
            if not ags_liste:
                missing_ags.append(vg_name)
                continue

            authority_name = f"Verbandsgemeindeverwaltung {vg_name} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Kommunale Beitragsstelle (Verbandsgemeinde)",
                    street=info["street"], house_number=None,
                    postal_code=info["postal_code"], city=info["city"], state="Rheinland-Pfalz",
                    phone=None, email=info["email"],
                    source=f"Amtliche Quelle, recherchiert 2026-09-26/27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")
            else:
                print(f"Authority bereits vorhanden, wird wiederverwendet: {authority_name}")

            for ags in ags_liste:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label="Erschließungsbeiträge - VG250-Ausweitung RLP Welle 2",
                    request_type_id="ERSCHLIESSUNG", state="Rheinland-Pfalz", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"Verbandsgemeindeverwaltung {vg_name} - {info['dept']}",
                    source_url=info["url"],
                    source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append((entry, info))
        db.commit()

        if missing_ags:
            print(f"\nWARNUNG: keine AGS-Liste gefunden für: {missing_ags}")

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(VERBANDSGEMEINDEN) - len(missing_ags)} VGs.")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} conflict={c.conflict_type} - {c.conflict_reason}")

        approved = 0
        for entry, info in staged:
            if entry.conflict_type != "NEW":
                continue
            is_stark = info.get("tier") == "stark"
            hinweis = BELEGLAGE_HINWEIS_STARK if is_stark else BELEGLAGE_HINWEIS_SCHWAECHER
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes=hinweis.format(quote=info["quote"]),
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
