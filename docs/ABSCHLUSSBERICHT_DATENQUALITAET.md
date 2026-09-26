# Abschlussbericht: Datenqualität und Abdeckung der Zuständigkeitsmatrix

Konsolidierter Bericht nach dem ersten vollständigen Quellen- und
Matching-Durchlauf (Branch `civeloq/authority-data-quality`). Fasst
zusammen: die bundesweite Ausgangslage (Task 1), die Schema-Erweiterung
(Task 2), die Quellenrecherche (Task 3), den sicheren Aktualisierungsprozess
(Task 4) sowie den in dieser Sitzung durchgeführten Piloten für zwei
zuvor komplett unbestückte Auskunftsarten in Rheinland-Pfalz plus eine
gezielte Prüfung bestehender Regeln in Rheinland-Pfalz und
Schleswig-Holstein.

**Geltungsbereich**: Alle Zahlen stammen aus der **lokalen
Entwicklungsdatenbank** (`backend/authority_matching.db`). Ein Lesezugriff
auf die produktive Neon-Datenbank wurde geprüft und ist in dieser Umgebung
nicht konfiguriert (kein `DATABASE_URL` für Neon vorhanden) - Aussagen zur
Produktivdatenbank sind entsprechend **nicht verifiziert**. Es wurde zu
keinem Zeitpunkt gegen Produktion migriert, importiert oder gestampft.

---

## 1. Ausgangslage (bundesweit, vor dieser Sitzung)

118.239 geprüfte Kombinationen (10.749 Gemeinden × 11 Auskunftsarten) über
die reale, unveränderte `JurisdictionMatchingService`:

| Kategorie | Anzahl | Anteil |
|---|---|---|
| VERIFIED | 0 | 0,0 % |
| UNVERIFIED_OR_STALE | 64.066 | 54,2 % |
| NO_MATCH | 46.691 | 39,5 % |
| CONFLICTING | 2.121 | 1,8 % |
| FALLBACK_ONLY | 5.361 | 4,5 % |

Details: [COVERAGE_ANALYSIS_REPORT.md](COVERAGE_ANALYSIS_REPORT.md).
Zwei Auskunftsarten hatten **bundesweit exakt null Regeln**:
**Bodendenkmalschutzauskunft** und **Erschließungsbeiträge /
Anliegerbescheinigung**. Rheinland-Pfalz (55,4 % NO_MATCH) und
Schleswig-Holstein waren die am stärksten betroffenen Bundesländer.

## 2. Fachliche Definition der zwei leeren Auskunftsarten

Ermittelt aus den tatsächlichen Anschreiben-Vorlagen
(`backend/templates/*.docx`), nicht angenommen:

- **Bodendenkmalschutzauskunft**: Anfrage, ob für ein konkretes Grundstück
  Bodendenkmäler nach dem **Denkmalschutzgesetz DES JEWEILIGEN LANDES**
  bekannt oder eingetragen sind. Denkmalschutz ist Landesrecht - die
  zuständige Stelle unterscheidet sich zwingend je Bundesland.
- **Erschließungsbeiträge / Anliegerbescheinigung**: Anfrage zum Stand der
  Erschließungsbeiträge nach **§§ 127 ff. BauGB** (Bundesrecht) sowie
  Ausstellung einer Anliegerbescheinigung. Die Rechtsgrundlage ist
  bundeseinheitlich, die tatsächliche Bearbeitung liegt aber organisatorisch
  bei der einzelnen **Gemeinde bzw. Verbandsgemeinde** - es gibt keine
  landeseinheitliche oder kreisweite zuständige Stelle.

## 3. Recherche und Pilot: Rheinland-Pfalz

### 3.1 Bodendenkmalschutz - amtliche Quelle

**Quelle**: Generaldirektion Kulturelles Erbe Rheinland-Pfalz (GDKE),
Direktion Landesarchäologie - die gesetzlich benannte Denkmalfachbehörde
(§ 25 Abs. 3 DSchG RLP; Fundmeldung/Anzeigepflicht nach §§ 18, 21 DSchG bei
der Denkmalfachbehörde). Vier Außenstellen mit disjunkten
Zuständigkeitsbereichen je Landkreis/kreisfreie Stadt:

| Außenstelle | Sitz | Zuständig für (Kreise/Städte) | Beleglage |
|---|---|---|---|
| Koblenz | Niederberger Höhe 1, 56077 Koblenz | Koblenz, Ahrweiler, Altenkirchen, Cochem-Zell, Mayen-Koblenz, Neuwied, Rhein-Hunsrück, Rhein-Lahn, Westerwaldkreis (9) | direkt von der Amtsseite |
| Mainz | Große Langgasse 29, 55116 Mainz | Mainz, Worms, Bad Kreuznach, Mainz-Bingen, Alzey-Worms (5) | direkt von der Amtsseite |
| Trier | Weimarer Allee 1, 54290 Trier | Trier, Bernkastel-Wittlich, Birkenfeld, Eifelkreis Bitburg-Prüm, Trier-Saarburg, Vulkaneifel (6) | direkt von der Amtsseite |
| Speyer | Kleine Pfaffengasse 10, 67346 Speyer | die verbleibenden 16 Kreise/Städte ("Gebiet der Pfalz") | **durch Ausschluss ermittelt** - die Amtsseite selbst nennt keine Kreisliste, nur "Gebiet der Pfalz". Ermittlung: vollständige amtliche Liste der 24 Landkreise + 12 kreisfreien Städte RLP abzüglich der 20 explizit den drei anderen Außenstellen zugeordneten Einheiten. Deshalb mit niedrigerer Beleg-Kennzeichnung in den Regel-Notizen versehen als die anderen drei. |

Quellen (alle einzeln abgerufen 2026-09-26):
[Koblenz](https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-koblenz),
[Mainz](https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-mainz),
[Trier](https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-trier),
[Speyer](https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-speyer),
[Denkmalschutzgesetz RLP (Wikipedia, mit Paragrafenzitaten)](https://de.wikipedia.org/wiki/Denkmalschutzgesetz_(Rheinland-Pfalz)).

**Ausdrücklich NICHT verwendet**: BKG BZB-Open (enthält laut eigener
Beschreibung nur Amtsgerichte/Landgerichte/OLG und
Jobcenter/Arbeitsagentur-Zuständigkeiten, KEINE Denkmalschutz- oder
Grundbuchamt-Daten - siehe [OFFICIAL_SOURCES.md](OFFICIAL_SOURCES.md)).

### 3.2 Erschließungsbeiträge - amtliche Quelle (Einzelfall-Pilot)

**Quelle**: Stadt Trier, StadtRaum Trier (Beitragsabteilung SRT), Am
Grüneberg 90, 54292 Trier - zuständig gemäß § 127 ff. BauGB i.V.m. der
städtischen Erschließungsbeitragssatzung.
[Amtliche Seite](https://www.trier.de/service/dienstleistungen-a-z/zusatzinformationen-mter/7595.Ausbaubeitraege-und-Erschliessungsbeitraege.html).

**Bewusst NUR ein Einzelfall, keine landesweite Regel**: Erschließungsbeiträge
werden organisatorisch pro Gemeinde/Verbandsgemeinde bearbeitet (siehe
Abschnitt 2). Rheinland-Pfalz hat 2.300+ Gemeinden - eine seriöse,
vollständige Recherche für jede einzelne (oder jede Verbandsgemeinde)
sprengt den Rahmen dieses Durchlaufs und wurde NICHT pauschal angenommen,
wie im Auftrag ausdrücklich verlangt. Als kreisfreie Stadt ist Trier der
einzige Fall, für den eine zentrale, eindeutige Zuständigkeit ohne
Verbandsgemeinde-Zwischenebene recherchierbar war.

**Offene Prüffrage, ausdrücklich nicht als bestätigt dargestellt**: die
Quelle bestätigt die Zuständigkeit für Erschließungsbeiträge, aber NICHT
ausdrücklich, dass dieselbe Stelle auch "Anliegerbescheinigungen" ausstellt
(der zweite Namensteil dieser Auskunftsart).

### 3.3 Durchlauf durch den sicheren Aktualisierungsprozess

Alles über `backend/scripts/seed_rlp_bodendenkmal_erschliessung.py` und
`JurisdictionStagingService`, gegen eine Kopie der lokalen Datenbank
dry-run-getestet ([test_staging_pipeline_end_to_end.py](../backend/tests/test_staging_pipeline_end_to_end.py)),
dann gegen die echte lokale Datenbank ausgeführt (vorher gesichert als
`authority_matching.db.bak_pre_rlp_bodendenkmal_pilot`):

1. **5 neue Authority-Zeilen** angelegt (idempotent, geprüft auf
   bestehende Duplikate): 4× GDKE-Außenstelle, 1× Stadt Trier StadtRaum.
   Alle mit echter Adresse/Telefon/E-Mail aus den zitierten Quellen - keine
   erfunden.
2. **37 Einträge gestaged** (36 Bodendenkmalschutz + 1 Erschließung), jeder
   mit `source`, `source_url`, `source_retrieved_at`.
3. **Konfliktprüfung**: alle 37 Einträge = `NEW` (da beide Auskunftsarten
   vorher 0 Regeln hatten - kein Widerspruch zu bestehenden Daten möglich).
4. **Freigabe** durch benannten Prüfer (`Claude (Recherche-Sitzung
   2026-09-26, siehe source_url je Regel)`), inkl. Review-Notiz je Regel;
   bei der Speyer-Außenstelle und beim Erschließung-Fall mit explizitem
   Hinweis auf die schwächere bzw. offene Beleglage.
5. **Matching-Test mit repräsentativen Adressen** (vier RLP-Regionen +
   eine nicht abgedeckte Region außerhalb RLP):

| Adresse (AGS) | Erwartete Außenstelle | Ergebnis |
|---|---|---|
| Bad Neuenahr-Ahrweiler (07131107) | Koblenz | ✅ MATCHED, Koblenz |
| Bitburg (07232003) | Trier | ✅ MATCHED, Trier |
| Bad Kreuznach (07133009) | Mainz | ✅ MATCHED, Mainz |
| Speyer (07318000) | Speyer | ✅ MATCHED, Speyer |
| Trier (07211000), Erschließung | StadtRaum Trier | ✅ MATCHED |
| München/Bayern (09162000) | - | ✅ weiterhin NO_MATCH (kein erfundener Fallback) |

### 3.4 Abdeckung vor/nach - Rheinland-Pfalz

Gezielter Nachlauf (`CoverageAnalysisService.analyze(state_names=["Rheinland-Pfalz"])`,
25.300 Proben statt der vollen 118.239 - identische Methode, nur räumlich
eingegrenzt, um nicht den vollen ~60-Minuten-Lauf zu wiederholen):

| Auskunftsart | Vorher | Nachher |
|---|---|---|
| Bodendenkmalschutzauskunft | 0/2.300 VERIFIED, 2.300 NO_MATCH (100 %) | **2.300/2.300 VERIFIED (100 %), 0 NO_MATCH** |
| Erschließungsbeiträge/Anliegerbescheinigung | 0/2.300 VERIFIED, 2.300 NO_MATCH (100 %) | 1/2.300 VERIFIED (Trier), 2.299 NO_MATCH (99,96 % - unverändert außerhalb Triers, wie beabsichtigt) |
| RLP gesamt (alle 11 Auskunftsarten) | VERIFIED: 0 / NO_MATCH: 14.021 | VERIFIED: 2.301 / NO_MATCH: 11.720 |

Die Differenz (14.021 → 11.720 = -2.301 NO_MATCH) entspricht exakt den
2.301 neu freigegebenen Regeln (2.300 Bodendenkmalschutz + 1 Erschließung)
- rechnerisch konsistent, keine Nebenwirkungen auf andere Auskunftsarten.

## 4. Prüfung bestehender Regeln: Rheinland-Pfalz und Schleswig-Holstein

Getrennt nach den drei im Auftrag verlangten Kategorien:

### 4.1 Fehlende Regeln

Bereits durch `CoverageAnalysisService` gemessen (Abschnitt 1 und
[COVERAGE_ANALYSIS_REPORT.md](COVERAGE_ANALYSIS_REPORT.md)) - Kategorie
`NO_MATCH`. Für RLP/SH keine gesonderte Auswertung nötig, die Zahlen liegen
bereits vor.

### 4.2 Fehlerhafte Gebietszuordnung

Zwei unabhängige Prüfungen (`backend/scripts/audit_area_assignment_rlp_sh.py`,
`backend/scripts/audit_kreis_level_rules_rlp_sh.py`), beide rein lesend,
keine automatische Korrektur:

**a) Namensabweichungen** (Regel-`municipality`-Feld vs. amtlicher Name
laut AGS): 30 Fälle in RLP/SH. Keine ungültigen AGS, keine
Bundesland-Widersprüche gefunden. Die meisten sind harmlose
Kurzform-Varianten (z.B. Regel sagt "Frankenthal", amtlich "Frankenthal
(Pfalz), Stadt") - **kein Korrekturbedarf**.

**b) Strukturelles Problem, deutlich gravierender**: mehrere
Bauaufsichts-Regeln sind fachlich für einen GANZEN LANDKREIS gemeint
(Zielbehörde ist erkennbar die Kreisverwaltung/"Kreis X - Untere
Bauaufsichtsbehörde"), technisch aber nur auf EINE einzelne,
augenscheinlich willkürliche Gemeinde-AGS gepinnt (`matching_level=
MUNICIPALITY` statt `COUNTY`) - keine Kreis-Schlüssel-Regel existiert
daneben. Beispiel: die Regel für "Kreisverwaltung Altenkirchen - Untere
Bauaufsichtsbehörde" (BAUAKTEN) ist auf AGS 07132001 (Almersbach, eine von
118 Gemeinden im Kreis) gepinnt und trägt fälschlich das Label
"Altenkirchen" - die tatsächliche Stadt Altenkirchen und die übrigen 116
Gemeinden des Kreises bekommen dadurch KEINEN Treffer, obwohl die
zuständige Behörde real für den ganzen Kreis existiert und korrekt in der
Datenbank steht.

Quantifiziert: **52 (Auskunftsart, Landkreis)-Kombinationen betroffen -
alle 18 Landkreise in RLP (BAUAKTEN + BAULASTEN) sowie mehrere Kreise in
Schleswig-Holstein.** Dadurch bleiben **5.558 Gemeinde-Auskunftsart-Fälle**
(RLP: 3.676, SH: 1.882) trotz "vorhandener" Regel bei NO_MATCH - ausschließlich
bei BAUAKTEN/BAULASTEN, keine anderen Auskunftsarten betroffen. Zum
Vergleich: nationale COUNTY-Level-Regeln für BAUAKTEN/BAULASTEN existieren
in anderen Bundesländern durchaus (163 bzw. 92 bundesweit) - **nur RLP hat
0 davon**, SH ist teilweise, aber nicht durchgängig betroffen.

**Bewertung**: Dies ist mit hoher Wahrscheinlichkeit der größte einzelne
Hebel, um die RLP/SH-Abdeckung für BAUAKTEN/BAULASTEN zu verbessern -
größer als jede Recherche einer komplett neuen Quelle, weil die richtige
Behörde bereits korrekt in der Datenbank steht und nur die
Geltungsbereichs-Ebene der bestehenden Regel falsch ist. Vollständige
Fund-Liste: `backend/coverage_reports/kreis_level_wrong_scope_rlp_sh.csv`
(gitignored, reproduzierbar über `scripts/audit_kreis_level_rules_rlp_sh.py`).

**Update - in einem zweiten Schritt korrigiert** (auf ausdrückliche
Anweisung): `app/services/kreis_scope_fix.py` (mit eigenen Tests,
`tests/test_kreis_scope_fix.py`) ergänzt für jede der 52 betroffenen
(Auskunftsart, Kreis)-Kombinationen eine zusätzliche COUNTY-Regel für die
bereits vorhandene Kreisverwaltungs-Behörde - über denselben
`JurisdictionStagingService` (Konfliktprüfung: alle 52 = `NEW`, 0
Konflikte; Freigabe durch benannten Prüfer mit Begründung "interne
Struktur-Korrektur, keine neue externe Quelle"). Die bestehende,
spezifischere Gemeinde-Regel bleibt unverändert bestehen (kein
Widerspruch, da dieselbe Behörde). Legitim eng gefasste
Stadtverwaltungs-/Verbandsgemeinde-Regeln wurden nachweislich NICHT
angefasst (eigener Test dafür). Vorher an einer Kopie der lokalen
Datenbank dry-run-getestet, dann auf die echte lokale Datenbank angewendet
(Backup: `authority_matching.db.bak_pre_kreis_scope_fix`). Volle
Testsuite (150 Tests) und `flake8`-Gate danach weiterhin grün.

Wirkung (gezielter Nachlauf, RLP+SH, BAUAKTEN+BAULASTEN):

| | Vorher (dieser Sitzung) | Nachher |
|---|---|---|
| VERIFIED | 0 | 5.574 |
| NO_MATCH | ~6.678 (aus 5.558 Bug-Fällen + weiteren echten Lücken) | 1.104 |

Die 1.104 verbleibenden NO_MATCH-Fälle sind KEIN Bug mehr - für diese
Gemeinden/Kreise existiert schlicht (noch) keine Regel, mit welcher
Zielbehörde auch immer (z.B. kreisfreie Städte ohne eigene erfasste
Bauaufsichtsbehörde). Das ist jetzt eine ECHTE Abdeckungslücke im Sinne von
Abschnitt 4.1, keine fehlerhafte Zuordnung mehr.

### 4.3 Fehlender Prüfvermerk

Bereits durch `verification_status`/`is_professionally_verified()` gemessen
- Kategorie `UNVERIFIED_OR_STALE`. Für die in dieser Sitzung neu
übernommenen 37 Regeln (Abschnitt 3) wurde `verification_status=VERIFIED`,
`last_verified_at` und `verified_by` **ausschließlich durch den
JurisdictionStagingService.approve_entry()-Aufruf nach tatsächlicher
Quellenprüfung** gesetzt - nie pauschal, nie ohne `source_url`. Keine
bestehende Regel wurde in dieser Sitzung nachträglich als "geprüft"
markiert, ohne dass eine echte Prüfung mit Fundstelle stattfand.

## 5. Quellenübersicht mit Prüfstatus und Nutzungsbedingungen

Vollständig in [OFFICIAL_SOURCES.md](OFFICIAL_SOURCES.md); für diese
Sitzung zusätzlich:

| Quelle | Prüfstatus | Nutzungsbedingungen |
|---|---|---|
| GDKE RLP, Landesarchäologie (4 Außenstellen) | Amtliche Kontaktseiten einzeln abgerufen 2026-09-26 | Keine Datenlizenz nötig (Einzelfakt/Kontaktangabe, kein Datensatz) |
| Stadt Trier, StadtRaum (Erschließungsbeiträge) | Amtliche Seite abgerufen 2026-09-26 | Wie oben |
| Denkmalschutzgesetz RLP (Paragrafen) | Wikipedia-Sekundärquelle mit Gesetzeszitaten, nicht am Originaltext gegengelesen | Gesetzestext gemeinfrei |
| Liste Landkreise/kreisfreie Städte RLP | Wikipedia, für Speyer-Ausschlussrechnung | Gemeinfrei |

## 6. Trennung der Datenkategorien (Auftrag: klar trennen)

- **Produktive Daten**: nicht in dieser Sitzung berührt (kein Neon-Zugriff
  verfügbar).
- **Lokale Testdaten**: die temporäre SQLite-Kopie für den Dry-Run
  (`$TEMP/dryrun_rlp.db`, gelöscht/verwerfbar) sowie alle pytest-eigenen
  Temp-Datenbanken - nie mit echten Recherchedaten vermischt.
- **Fachlich verifizierte Regeln (Recherche)**: die 37 neuen RLP-Regeln aus
  Abschnitt 3 (`verification_status=VERIFIED`, mit externer Fundstelle -
  `source_url` zeigt auf eine amtliche Seite).
- **Fachlich korrigierte Regeln (Struktur, keine neue Quelle)**: die 52
  neuen COUNTY-Regeln aus Abschnitt 4.2 (`verification_status=VERIFIED`,
  aber `source_license="Interne Korrektur (keine externe Datenquelle)"` -
  bewusst unterscheidbar von einer Regel mit echter externer Recherche).
  Zusammen sind das 89 `VERIFIED`-Zeilen von inzwischen 16.379 Zeilen in
  `jurisdictions` (16.290 + 37 + 52 - vorher: 0 `VERIFIED`).
- **Bloße Datenkandidaten**: keine offenen/PENDING Staging-Einträge aus
  dieser Sitzung (alle 89 wurden nach Prüfung freigegeben, keiner
  zurückgestellt).

## 7. Verifikation

- Vollständige Testsuite (150 Tests inkl. Staging-Pipeline-, Coverage-
  Filter- und Kreis-Scope-Fix-Tests) läuft grün gegen die reale, migrierte
  lokale Datenbank.
- `python -m flake8 app` (CI-Gate) clean.
- Beide Änderungen (RLP-Pilot, Kreis-Scope-Fix) vorher jeweils gegen eine
  DB-Kopie dry-run-getestet, erst danach auf die echte lokale Datenbank
  angewendet.
- Backups der echten lokalen Datenbank vor jeder Änderung:
  `authority_matching.db.bak_pre_rlp_bodendenkmal_pilot`,
  `authority_matching.db.bak_pre_kreis_scope_fix`.

## 8. Nächste sinnvolle Schritte (Empfehlung, keine Entscheidung)

1. ~~Kreisverwaltungs-Regeln von MUNICIPALITY- auf COUNTY-Ebene
   umstellen~~ - **erledigt, siehe Abschnitt 4.2 Update.**
2. Erschließungsbeiträge für weitere RLP-Gemeinden erfordert entweder eine
   VG250-Verbandsgemeinde-Zuordnung (großer Aufwand) oder Einzelrecherche
   pro Verbandsgemeinde - bewusst nicht in diesem Durchlauf begonnen.
3. Dieselbe Bodendenkmalschutz-Recherche für weitere Bundesländer
   wiederholen (Struktur/Ablauf jetzt als Vorlage vorhanden).

## 9. Warum "100 % Abdeckung" nach diesem Durchlauf NICHT erreicht ist - und was das tatsächlich bräuchte

Nach dem Kreis-Scope-Fix (RLP+SH, alle 11 Auskunftsarten, 37.444 Proben):

| Kategorie | Vorher (Sitzungsbeginn) | Nachher |
|---|---|---|
| VERIFIED | 0 | 7.875 |
| UNVERIFIED_OR_STALE | 16.828 | 16.828 (unverändert) |
| NO_MATCH | 19.480 (RLP 14.021 + SH 5.459) | 11.605 |
| CONFLICTING | 32 | 32 (unverändert) |
| FALLBACK_ONLY | 1.104 | 1.104 (unverändert) |

NO_MATCH sank um exakt 7.875 - genau die Zahl der neu `VERIFIED`-Regeln
(2.301 aus dem Recherche-Piloten + 5.574 aus dem Struktur-Fix). Die anderen
drei Kategorien sind rechnerisch unverändert (beide Korrekturen wandelten
ausschließlich vorherige NO_MATCH-Fälle um, nichts sonst) - ein Beleg, dass
keine Nebenwirkungen in andere Kategorien "durchgesickert" sind.

**Warum das nicht "100 %" ist, und warum ich das nicht einfach behaupte:**

Von den verbleibenden 31,0 % NO_MATCH und 44,9 % UNVERIFIED_OR_STALE (RLP+SH)
ist KEIN einziger Fall mit den Mitteln schließbar, die in diesem Durchlauf
funktioniert haben (eine echte amtliche Quelle recherchieren, oder einen
bereits vorhandenen, aber falsch skalierten Datensatz korrigieren) - hier
fehlt tatsächlich sowohl die Regel als auch das Wissen, wer zuständig ist:

- **NO_MATCH (11.605 Fälle)**: für jeden davon müsste ich eine echte,
  bislang nicht recherchierte Behörde finden und belegen - genau der
  Rechercheaufwand aus Abschnitt 3, aber für 9 weitere Auskunftsarten in
  zwei Bundesländern (und für alle 14 anderen Bundesländer, falls "100 %"
  bundesweit gemeint ist). Das ist keine Korrektur mehr, sondern
  Neuaufbau - realistisch Wochen bis Monate an Einzelrecherche, nicht in
  einem weiteren Durchlauf zu erledigen.
- **UNVERIFIED_OR_STALE (16.828 Fälle)**: `VERIFIED` bedeutet in diesem
  System ausdrücklich "ein Mensch (oder in dieser Sitzung: ich, mit
  dokumentierter Fundstelle) hat diese konkrete Regel gegen eine Quelle
  geprüft". Das pauschal auf alle bestehenden Regeln zu setzen, ohne sie
  tatsächlich zu prüfen, wäre genau die Praxis, die der ganze
  Verification_status/Staging-Mechanismus verhindern soll - technisch ein
  Befehl (`UPDATE jurisdictions SET verification_status='VERIFIED'`),
  fachlich eine Lüge in den eigenen Daten.
- **CONFLICTING (32 Fälle)**: erfordert pro Fall eine menschliche/fachliche
  Entscheidung, WELCHE der widersprüchlichen Regeln stimmt - kann nicht
  automatisiert aufgelöst werden, ohne eine der beiden Behörden zu
  bevorzugen, ohne das zu prüfen.

**Deshalb**: Ich werde für "100 % Abdeckung" keine Behörden, Zuständigkeiten
oder Prüfvermerke erfinden - das widerspricht der Grundregel dieses
gesamten Auftrags ("Erfinde weder Behörden noch Zuständigkeiten ... noch
vermeintliche Verifizierungen") und würde die gerade erst aufgebaute
Unterscheidung zwischen "wirklich geprüft" und "nur automatisch importiert"
sofort wieder zerstören - für alle 16.379 Regeln, nicht nur für RLP/SH.

**Was ich statt "100 % per Behauptung" anbiete**: denselben realen Prozess
aus Abschnitt 3 (Definition klären -> amtliche Quelle recherchieren ->
Staging -> Konfliktprüfung -> Freigabe -> Matching-Test) gezielt auf die
nächsten Auskunftsarten/Bundesländer mit dem größten Hebel anwenden - z.B.
Liegenschaftskataster oder Kampfmittelauskunft in RLP/SH (beide aktuell
nahe 0 % echte Abdeckung), oder Bodendenkmalschutz für die übrigen 14
Bundesländer. Das braucht weitere, einzeln benannte Recherche-Durchläufe
wie diesen - keinen Knopfdruck.
