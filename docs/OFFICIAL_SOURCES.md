# Amtliche Quellen für Verwaltungsgebiete, Zuständigkeiten und Organisationsdaten

Stand dieser Recherche: 2026-09-26. Prüfstatus und Aussagen zu Aktualität
gelten für diesen Zeitpunkt und müssen vor kommerzieller Nutzung erneut
geprüft werden (Lizenzbedingungen und Datenstände können sich ändern).

Grundsatz für alle unten genannten Quellen: **keine wurde automatisch in die
produktive Zuständigkeitsmatrix (`jurisdictions`) übernommen.** Jede
tatsächliche Übernahme läuft über `JurisdictionStagingService`
(`backend/app/services/jurisdiction_staging.py`) mit expliziter menschlicher
Freigabe (siehe Abschnitt "Sicherer Aktualisierungsprozess" im
Abschlussbericht).

## 1. Destatis Gemeindeverzeichnis (GV-ISys) — bereits im Einsatz

- **Was**: Amtliches Verzeichnis aller politisch selbstständigen Gemeinden
  Deutschlands mit AGS (Amtlicher Gemeindeschlüssel) und ARS (Amtlicher
  Regionalschlüssel), Bundesland-/Kreiszuordnung, Einwohnerzahl, Fläche.
- **Verwendung im System**: Basis der bestehenden `AdministrativeUnit`-Tabelle
  (`backend/app/models/administrative_unit.py`), 10.749 Zeilen im lokalen
  Bestand (Stand vor dieser Sitzung).
- **Lizenz**: Datenlizenz Deutschland – Namensnennung – Version 2.0
  (dl-de/by-2-0) — Attributionspflicht, kommerzielle Nutzung ausdrücklich
  erlaubt.
- **Aktualität**: Wird von Destatis laufend fortgeführt; welcher konkrete
  Stichtag dem aktuellen lokalen Bestand zugrunde liegt, ist NICHT aus der
  Datenbank selbst ablesbar (`AdministrativeUnit.data_stand` ist in der
  Praxis nicht durchgängig befüllt — siehe Befund unten).
- **Prüfstatus dieser Angabe**: RECHERCHIERT (Web), nicht durch direkten
  Kontakt mit Destatis verifiziert.
- **Grenzen**: Enthält AUSSCHLIESSLICH die geografische Struktur (welche
  Gemeinde gehört zu welchem Kreis/Land) — KEINE Information darüber, welche
  Behörde für welche Auskunftsart zuständig ist. Trägt nichts zur
  eigentlichen Zuständigkeitsermittlung bei, nur zur AGS-Hierarchie-Basis.

## 2. BKG VG250 (Verwaltungsgebiete 1:250.000) — als Pilot angebunden

- **Was**: Amtliche Verwaltungsgrenzen (Land → Regierungsbezirk → Kreis →
  Gemeinde) des Bundesamts für Kartographie und Geodäsie (BKG), inklusive
  AGS und ARS je Ebene.
- **Pilot durchgeführt in dieser Sitzung**: Herunterladen der
  Attributtabelle (`vg250_01-01.ee.excel.ebenen.zip`, Stand 01.01.2026, ca.
  5,3 MB, mit Nutzer-Zustimmung) von
  `https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/aktuell/vg250_01-01.ee.excel.ebenen.zip`
  und Abgleich der Gemeinde-Ebene (Sheet `VGTB_VZ_GEM`, 10.939 Zeilen) gegen
  die bestehende `AdministrativeUnit`-Tabelle
  (`backend/scripts/compare_administrative_units_vs_vg250.py`,
  Ergebnis: `backend/coverage_reports/administrative_unit_vs_vg250_diff.csv`).
- **Befund des Pilotvergleichs** (rein lesend, keine Datenbankänderung):
  - **190 AGS** stehen im aktuellen VG250-Stand (01.01.2026), fehlen aber in
    der lokalen `AdministrativeUnit`-Tabelle vollständig — ein echter
    Aktualitäts-Rückstand der Geo-Basis (~1,7 % der Gemeinden). Betrifft NUR
    die Vollständigkeit dieser Referenztabelle und der darauf aufbauenden
    Task-1-Abdeckungsanalyse, NICHT das Live-Matching realer Gebäude (das
    Matching liest `ags`/`state` direkt vom `Building`, nicht von
    `AdministrativeUnit`).
  - Nach Korrektur eines Normalisierungsfehlers im ersten Vergleichslauf
    (Destatis hängt bei Städten mit Titel den Zusatz an den Namen an, z.B.
    "Kiel, Landeshauptstadt"; VG250 führt Name und Typ in getrennten
    Feldern) verbleiben **243 Namens-/Kreis-Abweichungen**, davon die
    überwiegende Mehrheit reine Schreibweisen-/Abkürzungsunterschiede (z.B.
    "Rade b. Hohenwestedt" vs. "Rade b.Hohenwestedt") — KEINE echten
    Gebietsänderungen. Eine Handvoll Fälle (z.B. AGS 06415000: Kreisname bei
    uns `NULL`, laut VG250 "Hanau") sind isolierte Datenlücken im
    informativen `county_name`-Feld, ohne Auswirkung auf das Matching.
- **Lizenz**: Datenlizenz Deutschland – Namensnennung – Version 2.0 (wie
  Destatis) — Attributionspflicht, kommerzielle Nutzung erlaubt.
- **Aktualität**: Jährlicher Fortführungszyklus, Stichtage 01.01. bzw. 31.12.
  Aktuellster geprüfter Stand: 01.01.2026.
- **Prüfstatus**: TATSÄCHLICH HERUNTERGELADEN UND VERGLICHEN (nicht nur
  recherchiert) — der bisher einzige Datenpunkt in dieser Liste mit realem
  Datenabgleich statt reiner Quellenbeschreibung.
- **Formate**: Shapefile (GK3/TM32/UTM32s), GeoPackage, Excel (nur
  Attributtabelle, ohne Geometrie — für diesen Zweck ausreichend und ohne
  GIS-Bibliotheken auswertbar).
- **Grenzen**: Wie Destatis — reine Geo-/Verwaltungsstruktur, KEINE
  Behörden-Zuständigkeitsdaten. Löst keine der Task-1-Lücken (NO_MATCH,
  CONFLICTING) direkt, verbessert nur die Vollständigkeit/Aktualität der
  Geo-Basis, auf der Fallback-Matching (COUNTY/STATE) aufbaut.

## 3. BKG BZB-Open (Behördenzuständigkeitsbereiche Open)

- **Was**: Bundesweite Zuständigkeitsbereiche von Jobcentern, Agenturen für
  Arbeit UND drei Gerichtstypen: Amtsgerichte, Landgerichte,
  Oberlandesgerichte. Grundlage: VG250-Verwaltungsgrenzen, Stand der
  zugrunde liegenden Gebietsstände laut Dokumentation 31.12.2023 (der
  Gerichtsbezirks-Zuschnitt selbst wird jährlich fortgeführt, Stand der
  Produktseite: 03.2026).
- **Lizenz**: Datenlizenz Deutschland – Namensnennung – Version 2.0.
- **Prüfstatus**: RECHERCHIERT (Web), NICHT heruntergeladen — siehe
  Begründung unten, warum ein Download für dieses Projekt aktuell keinen
  konkreten Nutzen hätte.
- **Kritischer Befund (direkt aus dem Auftrag validiert)**: BZB-Open enthält
  **AUSDRÜCKLICH KEINE Grundbuchamt-Zuständigkeiten** — nur die
  Amtsgerichts-/Landgerichts-/OLG-Zuständigkeit allgemein. Der Auftrag warnt
  explizit davor, aus einem Amtsgerichtsbezirk ungeprüft die konkrete
  Grundbuch-Dienststelle abzuleiten — dieser Befund BESTÄTIGT, dass diese
  Warnung hier konkret zutrifft: viele Bundesländer haben ihre Grundbuchämter
  im Zuge von Justizreformen von den Amtsgerichtssitzen GETRENNT bzw.
  zentralisiert (z.B. NRW). Ein Amtsgerichtsbezirk aus BZB-Open zu nehmen und
  daraus direkt eine GRUNDBUCH-Jurisdiction-Regel abzuleiten, wäre exakt der
  im Auftrag verbotene Fehlschluss.
- **Tatsächlicher Nutzen für dieses Projekt**: Keiner der 11 Standard-
  Auskunftsarten (`STANDARD_REQUEST_TYPES`) bildet einen Amtsgerichts-,
  Landgerichts- oder Jobcenter-/Arbeitsagentur-Bezug direkt ab. BZB-Open
  wäre nur relevant, falls künftig eine eigene Auskunftsart "Amtsgericht"
  o.ä. eingeführt würde — dann aber weiterhin nur als GEOGRAFISCHE
  Abgrenzung, nicht als Ersatz für eine fachlich geprüfte
  Grundbuchamt-Zuständigkeitsquelle.

## 4. PVOG / LeiKa (Portalverbund Online-Gateway / Leistungskatalog)

- **Was**: LeiKa ist der bundesweite Leistungskatalog der öffentlichen
  Verwaltung (>8.000 Leistungen). PVOG ist die technische Infrastruktur, die
  Leistungsbeschreibungen UND Zuständigkeiten (welche Organisationseinheit
  bietet welche Leistung räumlich an) über die Portale von Bund und Ländern
  bündelt und per REST-API (OpenAPI 3.0) sowie weiteren Schnittstellen
  (XZufi-Webservice, SOAP) bereitstellt.
- **Fachliche Relevanz**: Von den drei recherchierten Quellen die EINZIGE,
  die konzeptionell tatsächlich Leistungs-zu-Zuständigkeit-Zuordnungen
  enthält — also genau die Art Information, die `jurisdictions` abbildet.
- **Prüfstatus**: RECHERCHIERT (Web), **NICHT verifizierbar innerhalb dieser
  Sitzung**. Weder die konkrete Zugangsvoraussetzung (offen nutzbar vs.
  Registrierung/Vereinbarung mit der FITKO nötig) noch das exakte
  Datenschema (insbesondere: liegt der räumliche Geltungsbereich als
  AGS/Gemeinde vor, oder nur als Text/Landesebene?) ließen sich über die
  öffentlich zugänglichen Dokumentationsseiten abschließend klären. Die
  API-Referenzseite (`pvog.fitko.de/api/bereitstelldienst/`) liefert nur ein
  Gerüst ohne die tatsächlichen Endpunkt-Details in einer für automatisierten
  Abruf lesbaren Form.
- **Nächster konkreter Schritt** (nicht in dieser Sitzung durchgeführt, um
  nichts zu erfinden oder ungeprüft zu behaupten): Direkter Kontakt
  `pvog@fitko.de`, um Zugangsweg, Datenschema und Lizenzbedingungen der
  Zuständigkeits-/Organisationsdaten zu klären. Erst danach lässt sich
  seriös einschätzen, ob PVOG echte Task-1-Lücken (NO_MATCH) schließen kann.
- **Lizenz**: Für die Website selbst CC BY 4.0 dokumentiert; die Lizenz der
  über die API bezogenen FACHDATEN ist NICHT dokumentiert gefunden worden —
  vor Nutzung zu klären.

## Priorisierung für die nächsten Schritte (Empfehlung, keine Entscheidung)

1. **AdministrativeUnit-Nachpflege**: die 190 bei VG250 gefundenen, lokal
   fehlenden AGS ergänzen (reine Geo-Stammdaten, kein
   Zuständigkeits-Fachwissen nötig, geringes Risiko) — verbessert die
   Vollständigkeit der Task-1-Abdeckungsanalyse selbst.
2. **PVOG-Zugang klären**: einziger recherchierter Kandidat, der tatsächlich
   Zuständigkeits- statt nur Geo-Daten liefert. Ohne Klärung von Zugang und
   Datenschema keine seriöse Aussage möglich, ob/wie er NO_MATCH-Lücken
   schließen kann.
3. **BZB-Open**: zurückstellen, bis eine Auskunftsart mit echtem
   Amtsgerichts-/Arbeitsagentur-Bezug existiert; für GRUNDBUCH ausdrücklich
   NICHT verwenden ohne separate, landesspezifische Verifikation der
   tatsächlichen Grundbuchamt-Organisation.
