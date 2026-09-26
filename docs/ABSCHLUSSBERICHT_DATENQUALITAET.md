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
- **Fachlich verifizierte Regeln (Recherche, bestehende Behörden erweitert)**:
  die 48 neuen KATASTER-COUNTY-Regeln aus Abschnitt 9, die 4 neuen
  DENKMALSCHUTZ-COUNTY-Regeln (Nullscope-Fix, Abschnitt 10.2) und die 15
  neuen BODENDENKMALSCHUTZ-COUNTY-Regeln für Schleswig-Holstein (Abschnitt
  10.3) - externe Fundstelle je Regel, teils für neu angelegte, teils für
  bereits existierende, wiederverwendete Authority-Zeilen.
- **Bestehende Regel nachträglich verifiziert (keine neue Zeile)**: die
  eine Kampfmittel-SH-Regel aus Abschnitt 10.1, über
  `verify_existing_rule()` ohne Änderung von Geltungsbereich oder Behörde.
  Zusammen sind das 157 `VERIFIED`-Zeilen von inzwischen 16.446 Zeilen in
  `jurisdictions` (16.290 + 37 + 52 + 48 + 4 + 15 - vorher: 0 `VERIFIED`).
- **Bloße Datenkandidaten**: keine offenen/PENDING Staging-Einträge aus
  dieser Sitzung (alle wurden nach Prüfung freigegeben, keiner
  zurückgestellt).

## 7. Verifikation

- Vollständige Testsuite (155 Tests inkl. Staging-Pipeline-, Coverage-
  Filter-, Kreis-Scope-Fix-, Kataster-Mapping- und `verify_existing_rule`-
  Tests) läuft grün gegen die reale, migrierte lokale Datenbank.
- `python -m flake8 app` (CI-Gate) clean.
- Jede Änderung vorher gegen eine DB-Kopie dry-run-getestet, erst danach
  auf die echte lokale Datenbank angewendet.
- Backups der echten lokalen Datenbank vor jeder Änderung:
  `authority_matching.db.bak_pre_rlp_bodendenkmal_pilot`,
  `authority_matching.db.bak_pre_kreis_scope_fix`,
  `authority_matching.db.bak_pre_kataster_rlp_sh`,
  `authority_matching.db.bak_pre_kampfmittel_sh_verify`,
  `authority_matching.db.bak_pre_denkmalschutz_nullscope_fix`,
  `authority_matching.db.bak_pre_sh_bodendenkmal`.

## 8. Nächste sinnvolle Schritte (Empfehlung, keine Entscheidung)

1. ~~Kreisverwaltungs-Regeln von MUNICIPALITY- auf COUNTY-Ebene
   umstellen~~ - **erledigt, siehe Abschnitt 4.2 Update.**
2. Erschließungsbeiträge für weitere RLP-Gemeinden erfordert entweder eine
   VG250-Verbandsgemeinde-Zuordnung (großer Aufwand) oder Einzelrecherche
   pro Verbandsgemeinde - bewusst nicht in diesem Durchlauf begonnen.
3. Dieselbe Bodendenkmalschutz-Recherche für weitere Bundesländer
   wiederholen (Struktur/Ablauf jetzt als Vorlage vorhanden).

## 9. Liegenschaftskataster (KATASTER) - RLP und SH

Auf ausdrücklichen Wunsch als nächster Auskunftsart-Durchlauf recherchiert
(gleiches Muster wie Bodendenkmalschutz: "Nutze denselben realen Prozess
für den nächsthöchsten Hebel").

**Fachliche Definition** (aus `templates/kataster.docx`): Auskunft aus dem
Liegenschaftskataster (Flurstücksnachweis/Auszug aus der Liegenschaftskarte)
nach dem **Vermessungs- und Katastergesetz DES LANDES** - wie
Bodendenkmalschutz Landesrecht mit landesspezifischer Organisation.

**Besonderheit gegenüber dem Bodendenkmalschutz-Piloten**: hier existierten
bereits Authority-Zeilen für ALLE benötigten Stellen - alle 6
rheinland-pfälzischen Vermessungs- und Katasterämter (VermKÄ) und alle 5
schleswig-holsteinischen Katasteramt-Standorte, mit korrekten Adressen
(unabhängig recherchiert und gegen die Datenbank abgeglichen - Übereinstimmung
bestätigt, keine Abweichung gefunden). Das Problem war identisch zum bereits
behobenen Kreisebenen-Scope-Bug: jede Stelle hatte nur eine Regel für ihren
eigenen Sitz-Kreis/ihre eigene Sitz-Gemeinde, nicht für ihren tatsächlichen,
mehrere Kreise umfassenden Zuständigkeitsbereich.

**Quellen** (amtlich, abgerufen 2026-09-26):
[LVermGeo RLP - Vermessungsbehörden](https://lvermgeo.rlp.de/service/vermessungsbehoerden-in-rheinland-pfalz)
(Kreiszuordnung je der 6 VermKÄ, zusätzlich gegen die Amtsseiten der Ämter
Rheinpfalz und Westpfalz einzeln gegengeprüft für die dort genannten "X
weitere Städte"), [LVermGeo SH - Kontakt](https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/LVERMGEOSH/Kontakt)
(explizite Kreiszuordnung je der 5 Regionalstandorte Kiel, Lübeck,
Flensburg, Husum, Elmshorn).

**Durchlauf**: `backend/scripts/seed_kataster_rlp_sh.py`, eigener Test
(`tests/test_seed_kataster_rlp_sh_mapping.py`) sichert die 36+15-Kreis-Zuordnung
gegen Duplikate/Lücken ab. Dry-Run gegen eine DB-Kopie, danach auf die echte
lokale Datenbank angewendet (Backup: `authority_matching.db.bak_pre_kataster_rlp_sh`).
**48 neue COUNTY-Regeln gestaged** (36 RLP + 12 SH; 3 SH-Kreise - Flensburg,
Kiel, Lübeck selbst - hatten bereits eine korrekt skalierte COUNTY-Regel und
wurden nicht dupliziert), **0 Konflikte**, alle freigegeben. Volle Testsuite
(152 Tests) und `flake8`-Gate weiterhin grün.

**Wirkung** (RLP+SH, nur KATASTER, 3.404 Proben):

| | Vorher | Nachher |
|---|---|---|
| VERIFIED | 0 | **3.393 (99,7 %)** |
| UNVERIFIED_OR_STALE | 11 | 11 (unverändert) |
| NO_MATCH | 3.393 | **0** |

Die 11 unverändert `UNVERIFIED_OR_STALE` sind kein Fehler: es sind exakt die
11 Gemeinden, für die schon VOR dieser Korrektur eine (teils richtig, teils
falsch skalierte) Regel auf genau diese eine Gemeinde-AGS existierte - der
Matcher prüft MUNICIPALITY/die eigene Kreis-AGS vor der neuen, allgemeineren
COUNTY-Regel und trifft dort weiterhin zuerst die alte, nie geprüfte Zeile.
Die zugeordnete Behörde ist in allen 11 Fällen dieselbe wie über die neue
Regel - **kein Korrektheitsproblem**, nur eine noch nicht nachgezogene
Prüfmarkierung an den ursprünglichen 11 Zeilen selbst (nicht in dieser
Sitzung angefasst, da das ein Update bestehender statt nur das Ergänzen
neuer Zeilen wäre - bewusst außerhalb des in Abschnitt 4 etablierten
"nur ergänzen, nie überschreiben"-Musters).

## 10. Kampfmittelauskunft, ein dritter Fehlerpattern (Nullscope) und Bodendenkmalschutz für Schleswig-Holstein

Fortsetzung auf ausdrücklichen Wunsch, "die übrigen Auskunftsarten in
RLP/SH" zu bearbeiten.

### 10.1 Kampfmittelauskunft

**Fachliche Definition** (`templates/kampfmittel.docx`): Auskunft über eine
mögliche Kampfmittelbelastung nach den Vorschriften zur
Kampfmittelräumung DES LANDES.

**Schleswig-Holstein**: Es existierte bereits eine korrekt zugeordnete
STATE-Regel (Landeskriminalamt Schleswig-Holstein - Kampfmittelräumdienst,
Lärchenweg 17, 24242 Felde), aber nie geprüft. Recherche bestätigt: die
Landesbauordnung SH verpflichtet Bauherren zur kostenpflichtigen Auskunft
beim LKA vor Bauvorhaben/Tiefbauarbeiten - das LKA ist die tatsächliche
gesetzliche Auskunftsstelle, die hinterlegte Adresse stimmt exakt mit der
[amtlichen Kontaktseite](https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/POLIZEI/DasSindWir/LKA/Kampfmittelraeumdienst/kampfmittelraeumdienst.html)
überein. Über die neue Methode `JurisdictionStagingService.verify_existing_rule()`
als `VERIFIED` markiert - **ohne** Geltungsbereich oder Behörde zu ändern.

**Rheinland-Pfalz - bewusst KEINE Regel angelegt**: die zuständige
Landesbehörde (ADD - Aufsichts- und Dienstleistungsdirektion,
Kampfmittelräumdienst) erklärt auf ihrer
[eigenen Amtsseite](https://add.rlp.de/themen/kommunales-und-sicherheit/kampfmittelraeumdienst)
ausdrücklich: *"Mangels konkretem Gefahrenverdacht gehört es auch nicht zu
den Aufgaben des Kampfmittelräumdienstes, die Kampfmittelbelastung bzw. -
freiheit von Grundstücken im Vorfeld von Baumaßnahmen zu beurteilen oder zu
bescheinigen."* Sie verweist stattdessen auf private
Luftbildauswertungs-Unternehmen. Eine Jurisdiction-Regel für RLP würde der
ADD eine Zuständigkeit zuschreiben, die sie selbst ausdrücklich verneint -
das widerspricht dem Auftrag, keine Zuständigkeiten zu erfinden. Für RLP
bleibt diese Auskunftsart deshalb ehrlich unbeantwortet, statt eine falsche
Zuständigkeit zu behaupten.

**Wichtige Einschränkung der Kennzahl**: Da Kampfmittelauskunft in SH über
eine `matching_level=STATE`-Regel läuft, klassifiziert
`CoverageAnalysisService` sie unabhängig vom Prüfstatus immer als
`FALLBACK_ONLY` (siehe Abschnitt 1 - STATE/PLZ gelten dort bewusst als
Fallback-Ebene, nicht als "eindeutig zugeordnet"). Die Verifikation ändert
deshalb NICHTS an der `FALLBACK_ONLY`-Zahl im Gesamtbild unten - sie ist
trotzdem real und im `jurisdictions`-Datensatz selbst
(`verification_status`, `source_url`) nachprüfbar. Bekannte Grenze der
5-Kategorien-Vereinfachung aus Task 1, nicht neu für diese Regel erfunden.

### 10.2 Denkmalschutz: ein dritter, bisher nicht dokumentierter Fehlerpattern

Bei der Suche nach schnell schließbaren Denkmalschutz-Lücken (301 von 3.404
RLP+SH-Fällen NO_MATCH) gefunden: der bereits behobene Kreisebenen-Scope-Bug
(Abschnitt 4.2) lag hier NICHT vor (`find_kreis_scope_bugs` fand 0 Fälle).
Stattdessen: **drei, später vier aktive Jurisdiction-Zeilen ohne
JEDEN Geltungsbereich** - `ags`, `municipality`, `district`, `postal_code`,
`street` UND `state` sind bei allen vieren `None`. Eine solche Zeile matcht
in KEINER der sieben Matching-Stufen jemals, für keine Anfrage - sie ist
technisch inert, aber täuscht in der Datenbank eine bestehende Zuständigkeit
vor. Laut `source`-Feld ("Denkmalschutzbehoerden Deutschland AGS-Matching")
ist beim Import der AGS-Abgleich für genau diese Landkreise fehlgeschlagen,
statt die Zeile zu überspringen oder einen Fehler zu melden.

Betroffen: Kreisverwaltung Rhein-Hunsrück (137 Gemeinden), Kreisverwaltung
Rhein-Lahn (137), Kreisverwaltung Rhein-Pfalz (25), Stadtverwaltung
Ludwigshafen (kreisfreie Stadt, 1) - zusammen 300 der 301 NO_MATCH-Fälle.
Für alle vier existierte die richtige Behörde bereits korrekt benannt in
der Datenbank - ergänzt wurde nur die fehlende COUNTY-Regel, über denselben
getesteten `apply_kreis_scope_fix()`-Mechanismus wie beim Bauakten/
Baulasten-Fix.

**Bewusst NICHT angefasst**: "Stadtverwaltung Neustadt - Untere
Denkmalschutzbehörde" - Adresse (Asbach) und bestehende Regel (Kreis
Neuwied) zeigen, dass dies tatsächlich "Neustadt (Wied)" ist, ein anderer
Ort als das gesuchte "Neustadt an der Weinstraße" (kreisfreie Stadt). Für
Neustadt an der Weinstraße existiert keine erkennbare Behörde in der
Datenbank - diese eine Gemeinde bleibt eine echte, ungeschlossene Lücke,
keine Verwechslung wurde in Kauf genommen.

**Bundesweiter Befund, nicht behoben**: derselbe Nullscope-Fehler existiert
noch 64-mal weitere Male außerhalb RLP/SH (v.a. ALTLASTEN in Berlin,
WASSERSCHUTZ/HOCHWASSERSCHUTZ in Hamburg/Saarland/Bayern) - dokumentiert,
aber nicht Teil dieses RLP/SH-fokussierten Durchlaufs.

### 10.3 Bodendenkmalschutz Schleswig-Holstein

Fortsetzung des RLP-Piloten (Abschnitt 3.1) für ein zweites Bundesland.

**Quellen** (drei unabhängige, übereinstimmende Quellen abgerufen
2026-09-26 - bewusst mehrfach abgesichert, da alle sekundär/Wikipedia sind,
nicht der DSchG-SH-Originaltext selbst):
[Wikipedia: Archäologisches Landesamt SH](https://de.wikipedia.org/wiki/Arch%C3%A4ologisches_Landesamt_Schleswig-Holstein),
[Wikipedia: Bereich Archäologie und Denkmalpflege der Hansestadt Lübeck](https://de.wikipedia.org/wiki/Bereich_Arch%C3%A4ologie_und_Denkmalpflege_der_Hansestadt_L%C3%BCbeck),
[Verband der Landesarchäologien - SH](https://www.landesarchaeologien.de/die-laender/schleswig-holstein/denkmalschutzbehoerden).

Struktur: **Archäologisches Landesamt Schleswig-Holstein (ALSH)**,
Brockdorff-Rantzau-Straße 70, 24837 Schleswig - obere Denkmalschutzbehörde
für archäologische Kulturdenkmale im GANZEN Land AUSSER Lübeck (14 der 15
Kreise/Städte). **Hansestadt Lübeck** ist eine bundesweite Besonderheit:
der "Bereich Archäologie und Denkmalpflege der Hansestadt Lübeck",
Königstraße 21, 23552 Lübeck, ist zugleich obere UND untere
Denkmalschutzbehörde für Lübeck, unabhängig von den Landesämtern.

15 neue COUNTY-Regeln (14 ALSH + 1 Lübeck), 2 neue Authority-Zeilen, 0
Konflikte (SH hatte zuvor 0 BODENDENKMALSCHUTZ-Regeln). Dry-Run-verifiziert:
korrektes Matching für beide Zuständigkeitsbereiche, RLPs bereits
bestehende Regeln bleiben unberührt.

**Wirkung**: Bodendenkmalschutzauskunft ist damit für RLP+SH zusammen zu
**100 % VERIFIED** (3.404/3.404) - die erste und bislang einzige
Auskunftsart, für die das in diesem Durchlauf für beide Bundesländer
zutrifft.

### 10.4 Geprüft und sauber befunden: keine weiteren billigen Treffer

Für die übrigen Auskunftsarten (Altlasten, Grundbuch, Hochwasserschutz,
Wasserschutzgebiet, Erschließungsbeiträge) wurden dieselben zwei
Fehlermuster (Kreisebenen-Scope-Bug, Nullscope-Bug) systematisch mit den
bestehenden Werkzeugen geprüft: **0 Funde in RLP/SH für alle fünf**. Das
heißt nicht, dass diese Auskunftsarten fehlerfrei sind - es heißt, dass die
verbleibenden Lücken dort NICHT über einen günstigen Struktur-Fix zu
schließen sind:

- **Altlasten/Grundbuch/Hochwasserschutz/Wasserschutzgebiet**: nominell
  0 % NO_MATCH, aber 100 % `UNVERIFIED_OR_STALE` - jede einzelne Regel
  wäre für sich zu prüfen (mutmaßlich hunderte verschiedene
  Gemeinde-/Kreisbehörden, kein kleiner Kreis von Landesämtern wie bei
  Kataster/Bodendenkmalschutz) - keine Massenverifikation ohne echte
  Einzelprüfung.
- **Erschließungsbeiträge**: strukturell Gemeinde-/Verbandsgemeinde-Ebene
  (siehe Abschnitt 3.2) - eine Ausweitung über den Trier-Einzelfall hinaus
  bräuchte eine VG250-Verbandsgemeinde-Zuordnung und Einzelrecherche für
  vermutlich 150+ Verbandsgemeinden allein in RLP.

## 11. Warum "100 % Abdeckung" nach diesem Durchlauf NICHT erreicht ist - und was das tatsächlich bräuchte

Stand nach allen Korrekturen dieser Sitzung (Bodendenkmalschutz RLP+SH,
Kreis-Scope-Fix, Liegenschaftskataster, Denkmalschutz-Nullscope-Fix,
Kampfmittel-SH-Verifikation; RLP+SH, alle 11 Auskunftsarten, 37.444 Proben):

| Kategorie | Vorher (Sitzungsbeginn) | Nachher |
|---|---|---|
| VERIFIED | 0 | **12.672** |
| UNVERIFIED_OR_STALE | 16.828 | 16.828 (unverändert) |
| NO_MATCH | 19.480 (RLP 14.021 + SH 5.459) | **6.808** |
| CONFLICTING | 32 | 32 (unverändert) |
| FALLBACK_ONLY | 1.104 | 1.104 (unverändert) |

NO_MATCH sank um exakt 12.672 - genau die Zahl der neu `VERIFIED`-Regeln
(2.301 Bodendenkmalschutz-Pilot RLP + 5.574 Kreis-Scope-Fix + 3.393
Liegenschaftskataster + 300 Denkmalschutz-Nullscope-Fix + 1.104
Bodendenkmalschutz SH). Die anderen drei Kategorien sind rechnerisch
unverändert (alle Korrekturen wandelten ausschließlich vorherige
NO_MATCH-Fälle um, nichts sonst) - ein Beleg, dass keine Nebenwirkungen in
andere Kategorien "durchgesickert" sind. RLP+SH liegen damit bei **33,9 %
echt verifizierter Abdeckung** (von 0 % bei Sitzungsbeginn), NO_MATCH sank
von 52,0 % auf 18,2 %.

Pro Auskunftsart (RLP+SH, 3.404 je Auskunftsart): **Bodendenkmalschutz
100 % VERIFIED** (3.404/3.404, einzige vollständig verifizierte
Auskunftsart), Liegenschaftskataster 99,7 %, Bauakten/Baulasten je 81,9 %,
Denkmalschutz 8,8 % VERIFIED + 91,2 % UNVERIFIED (nur noch 1 NO_MATCH-Fall:
Neustadt an der Weinstraße). Altlasten/Grundbuch/Hochwasserschutz/
Wasserschutzgebiet unverändert bei 0 % VERIFIED/100 % UNVERIFIED (kein
günstiger Struktur-Fix gefunden, siehe Abschnitt 10.4). Kampfmittel: RLP
weiterhin 0/2.300 (bewusst, siehe Abschnitt 10.1), SH weiterhin als
`FALLBACK_ONLY` klassifiziert trotz jetzt echter Verifikation (Grenze der
5-Kategorien-Metrik, kein Fehler). Erschließungsbeiträge: 1/3.404 (Trier).

**Warum das nicht "100 %" ist, und warum ich das nicht einfach behaupte:**

Von den verbleibenden 18,2 % NO_MATCH und 44,9 % UNVERIFIED_OR_STALE (RLP+SH)
ist KEIN einziger Fall mit den Mitteln schließbar, die in diesem Durchlauf
funktioniert haben (eine echte amtliche Quelle recherchieren, oder einen
bereits vorhandenen, aber falsch skalierten/ungescopten Datensatz
korrigieren) - hier fehlt tatsächlich sowohl die Regel als auch das Wissen,
wer zuständig ist, UND es wurde bereits systematisch nach den bekannten,
günstigen Fehlermustern gesucht (Abschnitt 10.4):

- **NO_MATCH (6.808 Fälle)**: für jeden davon müsste ich eine echte,
  bislang nicht recherchierte Behörde finden und belegen - genau der
  Rechercheaufwand aus Abschnitt 3/9/10, aber für Erschließungsbeiträge in
  voller Breite (3.403 der 6.808) und Kampfmittel in RLP (2.300, siehe
  Abschnitt 10.1 warum bewusst offen), plus die übrigen 14 Bundesländer,
  falls "100 %" bundesweit gemeint ist. Das ist keine Korrektur mehr,
  sondern Neuaufbau - realistisch Wochen bis Monate an Einzelrecherche,
  nicht in einem weiteren Durchlauf zu erledigen.
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
sofort wieder zerstören - für alle 16.446 Regeln, nicht nur für RLP/SH.

**Was ich statt "100 % per Behauptung" anbiete**: denselben realen Prozess
(Definition klären -> amtliche Quelle recherchieren -> Staging ->
Konfliktprüfung -> Freigabe -> Matching-Test), gezielt auf den nächsten
größten Hebel angewendet - siehe Abschnitt 12 für den konkreten nächsten
Schritt (Erschließungsbeiträge über VG250-Verbandsgemeinde-Zuordnung) und
die ehrliche Aufwandseinordnung, warum "ganz Deutschland, 100 %" auf
diesem Weg Wochen bis Monate weiterer, einzeln benannter
Recherche-Durchläufe braucht - keinen Knopfdruck.

## 12. Erschließungsbeiträge: VG250-Verbandsgemeinde-Ausweitung (Anfang)

Auf ausdrücklichen Wunsch begonnen, den Trier-Einzelfall (Abschnitt 3.2)
über die amtliche BKG-VG250-Gemeinde-zu-Verbandsgemeinde-Zuordnung
(Sheet `VGTB_VZ_GEM`, Spalten `ARS_V`/`GEN_V`/`BEZ_V` - dieselbe
VG250-Ausgabe, die bereits für den AdministrativeUnit-Abgleich in
Abschnitt 3 heruntergeladen wurde) auf weitere Verbandsgemeinden
auszuweiten.

**Tatsächliche Größenordnung, real gemessen**: Rheinland-Pfalz hat **129
Verbandsgemeinden plus 41 verbandsfreie Gemeinden/kreisfreie Städte** (170
insgesamt), die zusammen alle 2.300 RLP-Gemeinden abdecken. Jede einzelne
braucht dieselbe Art Einzelrecherche wie beim Trier-Fall - es gibt keinen
Landesamt-artigen Abkürzungsweg wie bei Bodendenkmalschutz/Kataster, weil
Erschließungsbeiträge strukturell IMMER auf VG-/Gemeinde-Ebene organisiert
sind. Von den 129 RLP-Verbandsgemeinden wurden bislang recherchiert:

- **Verbandsgemeinde Bitburger Land** (71 Gemeinden, größte VG in RLP,
  liegt im NO_MATCH-stärksten Kreis Eifelkreis Bitburg-Prüm): zuständig
  ist Abt. 4 "Bauen und Umwelt", Hubert-Prim-Straße 7, 54634 Bitburg.
- **Verbandsgemeinde Altenkirchen-Flammersfeld** (67 Gemeinden): zuständig
  ist Fachgebiet 3.2 "Beiträge für Verkehrsanlagen, Infrastruktur",
  Rathausstraße 13, 57610 Altenkirchen.
- **Verbandsgemeinde Südeifel** (65 Gemeinden) geprüft, aber
  zurückgestellt: die amtliche Organigramm-Seite ist clientseitig
  gerendert (JavaScript) und lieferte über WebFetch/Browser keine
  auslesbare Abteilungsangabe - keine Vermutung als Fundstelle
  ausgegeben.

138 neue MUNICIPALITY-Regeln, 0 Konflikte, dry-run-getestet vor Anwendung
auf die echte Datenbank (Backup:
`authority_matching.db.bak_pre_erschliessung_vg_rlp`).

**Beleglage bewusst niedriger markiert als beim Trier-Fall**: Trier nannte
"Ausbaubeiträge UND Erschließungsbeiträge" explizit kombiniert. Für
Bitburger Land und Altenkirchen-Flammersfeld bestätigen die amtlichen
Quellen die genannte Abteilung nur für "Ausbaubeiträge" bzw. "Beiträge für
Verkehrsanlagen/Infrastruktur" - nicht wörtlich für "Erschließungsbeiträge"
(§ 127 ff. BauGB, rechtlich eine andere Grundlage als das kommunale
Ausbaubeitragsrecht). In der Praxis bearbeitet fast immer dieselbe Stelle
beides, das ist hier aber NICHT wörtlich einzeln belegt - in jeder Regel
(`notes`-Feld) und im Skript-Docstring
(`scripts/seed_erschliessung_vg_rlp.py`) explizit vermerkt, keine
gleichwertige Beleglage vorgetäuscht.

**Realistischer Restaufwand**: 126 von 129 RLP-Verbandsgemeinden bleiben
offen, plus die strukturell entsprechenden "Amtsverwaltungen" in
Schleswig-Holstein (SH nennt seine Verbandsgemeinde-Entsprechung "Amt")
und alle Verbandsgemeinde-/Amt-Äquivalente der übrigen 14 Bundesländer.
Bei einer Recherchedauer von real 1-3 Suchanfragen pro Einheit (wie hier
demonstriert) ist das kein Fix, sondern ein mehrwöchiges
Recherchevorhaben allein für RLP - der Nutzer hat dies nach Rückfrage
ausdrücklich bestätigt (gleiches Tempo/gleiche Sorgfalt fortsetzen, kein
verkürztes Verfahren).
