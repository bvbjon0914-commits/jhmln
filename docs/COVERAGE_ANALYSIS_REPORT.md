# Abdeckungsanalyse: AGS x Auskunftsart (Task 1)

**Wichtiger Geltungsbereich dieser Zahlen:** Diese Analyse lief gegen die
**lokale Entwicklungsdatenbank** (`backend/authority_matching.db`), NICHT
gegen die produktive Neon-Datenbank. Ein produktiver Lesezugriff war in
dieser Sitzung nicht verfügbar (kein `DATABASE_URL` für Neon in der lokalen
Umgebung konfiguriert — geprüft, nicht angenommen). **Alle Zahlen unten sind
für den lokalen Bestand verifiziert, für die Produktivdatenbank
UNVERIFIZIERT.** Sollte die Produktivdatenbank denselben oder einen
abweichenden Stand haben, ist das separat zu prüfen, sobald Lesezugriff
verfügbar ist.

- **Lauf-Zeitpunkt**: 2026-09-26
- **Methode**: `CoverageAnalysisService` (`backend/app/services/coverage_analysis.py`),
  ausgeführt über `backend/scripts/run_coverage_analysis.py`. Nutzt
  ausschließlich die reale, unveränderte `JurisdictionMatchingService` — keine
  eigene/zweite Matching-Logik.
- **Umfang**: 10.749 Gemeinden (`AdministrativeUnit`, Destatis-Stand vor
  dieser Sitzung — siehe [OFFICIAL_SOURCES.md](OFFICIAL_SOURCES.md) zum
  VG250-Abgleich: 190 aktuellere Gemeinden fehlen hier) × 11 aktive
  Auskunftsarten = **118.239 geprüfte Kombinationen**.
- **Laufzeit**: 3.770,7s (~63 Minuten) auf einer lokalen Datei-SQLite ohne
  Netzwerklatenz, mit anderen gleichzeitig laufenden Prozessen auf derselben
  Maschine (Testläufe) - kein belastbarer Produktions-Latenzwert, aber ein
  klares Signal: **diese Analyse gehört als Hintergrund-/Offline-Job
  ausgeführt, nicht als synchroner API-Call** (bereits so umgesetzt).

## Gesamtübersicht (bundesweit, alle 118.239 Kombinationen)

| Kategorie | Anzahl | Anteil |
|---|---|---|
| (a) VERIFIED — eindeutig zugeordnet UND fachlich geprüft/belegt | **0** | 0,0 % |
| (b) UNVERIFIED_OR_STALE — eindeutig zugeordnet, aber ungeprüft/veraltet | 64.066 | 54,2 % |
| (c) NO_MATCH — kein Treffer | 46.691 | 39,5 % |
| (d) CONFLICTING — mehrere widersprüchliche Treffer | 2.121 | 1,8 % |
| (e) FALLBACK_ONLY — nur über allgemeine Fallback-Regel (STATE/PLZ) | 5.361 | 4,5 % |

**Zentraler Befund**: Von den insgesamt gefundenen Zuordnungen (a+b+e =
69.427) ist **buchstäblich keine einzige fachlich geprüft und aktuell
belegt** (Kategorie a = 0). Das bestätigt auf Gesamtdatenebene, was die
Stichprobe vor dieser Analyse schon zeigte (0 % Verifizierung über alle
16.290 Jurisdiction-Zeilen) — hier jetzt aber als tatsächliche
Abdeckungs-AUSWIRKUNG ausgedrückt: 69.427 scheinbar funktionierende
Zuständigkeits-Zuordnungen beruhen ausschließlich auf automatisiertem
Import, keine wurde je fachlich bestätigt.

## Nach Auskunftsart

| Auskunftsart | Gesamt | UNVERIFIED | NO_MATCH | CONFLICTING | FALLBACK_ONLY |
|---|---|---|---|---|---|
| Bodendenkmalschutzauskunft | 10.749 | 0 | **10.749 (100 %)** | 0 | 0 |
| Erschließungsbeiträge / Anliegerbescheinigung | 10.749 | 0 | **10.749 (100 %)** | 0 | 0 |
| Grundbuchauskunft | 10.749 | **10.749 (100 %)** | 0 | 0 | 0 |
| Baulastenauskunft | 10.749 | 2.735 | 7.925 (73,7 %) | 89 | 0 |
| Liegenschaftskataster-Auskunft | 10.749 | 4.010 | 6.548 (60,9 %) | 191 | 0 |
| Bauaktenauskunft | 10.749 | 4.790 | 5.870 (54,6 %) | 89 | 0 |
| Kampfmittelauskunft | 10.749 | 911 | 4.375 (40,7 %) | 102 | 5.361 |
| Denkmalschutzauskunft | 10.749 | 10.392 | 357 | 0 | 0 |
| Wasserschutzgebietsauskunft | 10.749 | 9.982 | 32 | 735 | 0 |
| Hochwasserschutzauskunft | 10.749 | 9.982 | 32 | 735 | 0 |
| Altlastenauskunft | 10.749 | 10.515 | 54 | 180 | 0 |

Einordnung, ohne etwas hineinzuinterpretieren, was die Daten nicht zeigen:

- **Bodendenkmalschutz und Erschließungsbeiträge/Anliegerbescheinigung haben
  bundesweit KEINE einzige Regel** — nicht "lückenhaft", sondern komplett
  unbestückt. Für diese zwei Auskunftsarten würde JEDE reale Anfrage heute
  NO_MATCH liefern.
- **Grundbuchauskunft ist nominell zu 100 % abgedeckt**, aber zu 100 % nie
  fachlich geprüft — genau der im Auftrag benannte Risikofall ("eindeutig
  zugeordnet, aber Prüfung fehlt").
- **Kampfmittelauskunft ist die einzige Auskunftsart mit Fallback-Nutzung**
  (5.361 FALLBACK_ONLY über STATE-Ebene) — plausibel, da
  Kampfmittelräumdienste in mehreren Bundesländern tatsächlich
  landesweit organisiert sind, aber diese Vermutung wurde NICHT gegen eine
  amtliche Quelle verifiziert und ist deshalb hier bewusst nur als Beobachtung,
  nicht als Bestätigung formuliert.
- **Wasserschutzgebiets- und Hochwasserschutzauskunft** haben mit je 735
  Fällen die meisten CONFLICTING-Fälle unter den Nicht-Kataster-Arten — ein
  konkreter Kandidat für die nächste Prüfrunde.

## Nach Bundesland (Auszug — vollständige Tabelle: `coverage_by_state.csv`)

| Bundesland | Gesamt | NO_MATCH | Anteil NO_MATCH | CONFLICTING | FALLBACK_ONLY |
|---|---|---|---|---|---|
| Rheinland-Pfalz | 25.300 | **14.021** | **55,4 %** | 18 | 0 |
| Bayern | 22.616 | 9.668 | 42,7 % | 1.056 | 0 |
| Schleswig-Holstein | 12.144 | 5.459 | 45,0 % | 14 | 1.104 |
| Baden-Württemberg | 12.111 | 2.280 | 18,8 % | 190 | 1.101 |
| Niedersachsen | 10.351 | 3.505 | 33,9 % | 516 | 941 |
| Mecklenburg-Vorpommern | 7.964 | 2.986 | 37,5 % | 2 | 724 |
| Thüringen | 6.611 | 1.767 | 26,7 % | 0 | 601 |
| Hessen | 4.631 | 1.397 | 30,2 % | 116 | 421 |
| Brandenburg | 4.543 | 1.614 | 35,5 % | 2 | 413 |
| Sachsen | 4.598 | 1.521 | 33,1 % | 114 | 0 |
| Nordrhein-Westfalen | 4.356 | 1.139 | 26,1 % | 40 | 0 |
| Sachsen-Anhalt | 2.398 | 1.028 | 42,9 % | 4 | 0 |
| Saarland | 572 | 291 | 50,9 % | 44 | 52 |
| Bremen | 22 | 6 | 27,3 % | 0 | 2 |
| Berlin | 11 | 4 | 36,4 % | 3 | 1 |
| Hamburg | 11 | 5 | 45,5 % | 2 | 1 |

**Rheinland-Pfalz hat mit Abstand die meisten NO_MATCH-Fälle absolut UND
relativ** (55,4 %) — erklärbar durch die für RLP typische kleinteilige
Gemeindestruktur (Verbandsgemeinden mit sehr vielen, sehr kleinen
Ortsgemeinden). Die am stärksten betroffenen Landkreise (aus
`coverage_by_county.csv`) sind:

| Landkreis | Bundesland | Gesamt | NO_MATCH |
|---|---|---|---|
| Eifelkreis Bitburg-Prüm | RLP | 2.563 | 1.396 |
| Westerwaldkreis | RLP | 2.112 | 1.149 |
| Rhein-Hunsrück-Kreis | RLP | 1.507 | 957 |
| Rhein-Lahn-Kreis | RLP | 1.507 | 953 |
| Rendsburg-Eckernförde | S-H | 1.815 | 821 |
| Altenkirchen (Westerwald) | RLP | 1.298 | 706 |
| Bad Kreuznach | RLP | 1.298 | 706 |
| Nordfriesland | S-H | 1.463 | 660 |
| Herzogtum Lauenburg | S-H | 1.452 | 656 |
| Vulkaneifel | RLP | 1.199 | 652 |

9 der 10 am stärksten betroffenen Landkreise liegen in Rheinland-Pfalz und
Schleswig-Holstein.

## Auswirkung auf das reale Portfolio

**0 betroffene Gebäude** — in der lokalen Datenbank sind aktuell **0
Gebäude importiert** (`buildings`-Tabelle leer). Jede der obigen Lücken ist
deshalb heute noch ohne konkrete geschäftliche Auswirkung, wird aber bei
JEDEM künftigen Portfolio-Import in einer betroffenen Gemeinde sofort zu
NO_MATCH/CONFLICTING/unbelegten Zuordnungen führen. Die Kreuzreferenz-Logik
(`portfolio_building_count` in `CoverageEntry`) ist fertig implementiert und
wird beim nächsten echten Import automatisch aussagekräftig, ohne
Codeänderung.

## Was diese Analyse NICHT sagt

- Nichts über die Produktivdatenbank (siehe Geltungsbereich oben).
- Nichts über die fachliche RICHTIGKEIT bestehender Zuordnungen — nur über
  deren Prüfstatus. Eine UNVERIFIED_OR_STALE-Zuordnung kann fachlich richtig
  sein, ist nur nie bestätigt worden.
- Keine Vermutung über WARUM eine Auskunftsart komplett unbestückt ist (z.B.
  Bodendenkmalschutz) — könnte an fehlendem Datenimport für genau diese Art
  liegen, nicht notwendigerweise an einer echten fachlichen Lücke.

## Rohdaten

Alle Zahlen sind aus `backend/coverage_reports/*.csv` reproduzierbar
(gitignored, da Analyseergebnis über den jeweils aktuellen lokalen
Datenbestand, nicht Quellcode):

```bash
venv/Scripts/python.exe scripts/run_coverage_analysis.py
```

- `coverage_detail.csv` — alle 118.239 Einzelergebnisse
- `coverage_by_state.csv`, `coverage_by_county.csv`, `coverage_by_municipality.csv`, `coverage_by_request_type.csv` — Gruppierungen
