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
sind (rechtlich zudem nicht garantiert einheitlich: nach § 67 GemO RLP
kann, muss aber nicht, eine Verbandsgemeinde diese Aufgabe von ihren
Ortsgemeinden übernommen haben - deshalb bewusst KEINE pauschale
Übertragung auf alle 129 VGs ohne Einzelbeleg). Bislang recherchiert (14
von 129, aktiver Bestand - Leiningerland siehe Rücknahme-Hinweis unten):

| Verbandsgemeinde | Kreis | Gemeinden | Zuständige Stelle | Beleglage |
|---|---|---|---|---|
| Bitburger Land (größte VG in RLP) | Eifelkreis Bitburg-Prüm | 71 | Abt. 4 Bauen und Umwelt | schwächer (nur "Ausbaubeiträge" belegt) |
| Altenkirchen-Flammersfeld | Altenkirchen | 67 | Fachgebiet 3.2 (Beiträge für Verkehrsanlagen, Infrastruktur) | schwächer |
| Herrstein-Rhaunen | Birkenfeld | 50 | Fachbereich Finanzen, generisch "Abgaben" | schwächer |
| Wittlich-Land | Bernkastel-Wittlich | 45 | Fachbereich Finanzen/Abgaben | schwächer |
| Prüm | Eifelkreis Bitburg-Prüm | 44 | Abt. 2.9 "Erschließungs- u. Ausbaubeiträge" | **stark** |
| Simmern-Rheinböllen | Rhein-Hunsrück-Kreis | 44 | Finanzen, "Erschließungsbeiträge Verkehrsanlagen" wörtlich gelistet | **stark** |
| Arzfeld | Eifelkreis Bitburg-Prüm | 43 | Fachbereich Bauen & Umwelt, eigene Seite "Erschließungsbeiträge" | **stark** |
| Lauterecken-Wolfstein | Kusel | 41 | Fachbereich Finanzen, "Erschließungsbeiträge" wörtlich gelistet | **stark** |
| Kirchberg (Hunsrück) | Rhein-Hunsrück-Kreis | 40 | Bauen und Umwelt, "Erschließungs- oder Ausbaubeiträge" im FAQ | **stark** |
| Daun | Vulkaneifel | 38 | Sachgebiet 4.2 Abgaben, "Erschließungsbeitrag zahlen" explizit gelistet | **stark** |
| Gerolstein | Vulkaneifel | 38 | Sachgebiet 2.2 Bauleitplanung/Umwelt/Beiträge, "Anliegerbeiträge"-Seite nennt Erschließungsbeiträge | **stark** |
| Nordpfälzer Land | Donnersbergkreis | 36 | Abteilung 2 Finanzen, nur generisch "Abgaben" | schwächer |
| Kusel-Altenglan | Kusel | 34 | Verbandsgemeindeverwaltung insgesamt, Begriff wörtlich auf Amtsseite | **stark** |
| Betzdorf-Gebhardshain | Altenkirchen | 17 | Fachbereich Finanzen, generisch "Abgaben" | schwächer |

**608 neue MUNICIPALITY-Regeln, 0 Konflikte in allen 14 Durchläufen**,
jeweils dry-run-getestet vor Anwendung auf die echte Datenbank. Alle
Adressen wurden gegen das Destatis-Anschriftenverzeichnis (Abschnitt 13.1)
gegengeprüft - exakte Übereinstimmung in allen 14 Fällen. Bei Daun wurde
eine Verwechslungsgefahr aktiv vermieden: die zuerst gefundene Seite
"Erschließung von Grundstücken" betraf tatsächlich die Wasser-/Abwasser-
Erschließung (Wirtschaftsbetriebe), nicht die hier gesuchte
BauGB-Erschließungsbeiträge - erst die zweite, gezielt geprüfte Quelle
(Sachgebiet 4.2 Abgaben) bestätigte den richtigen Zusammenhang.

**Zurückgenommen: Leiningerland** (Donnersbergkreis, 21 Gemeinden) - die
einzige gefundene Stütze war ein Zeitungsartikel (Die Rheinpfalz), keine
amtliche VG-Quelle. Auf ausdrücklichen Nutzer-Entscheid ("Nein, keine
Zeitungsartikel - nur offizielle Quellen zählen") vollständig
zurückgenommen: alle 21 Regeln deaktiviert (nicht gelöscht, Historie
bleibt nachvollziehbar), die betroffenen Gemeinden fallen wieder korrekt
auf NO_MATCH zurück. Der Sourcing-Standard ("source_url MUSS eine
amtliche Quelle sein, NIE ein Zeitungsartikel") ist seither explizit im
Docstring von `scripts/seed_erschliessung_vg_rlp.py` verankert.

**Prüfstatus nach Beleglage getrennt, direkt aus der Datenbank abgefragt**
(siehe Abschnitt 13.3 für die Code-Korrektur): **323 Regeln `VERIFIED`**
(Prüm, Simmern-Rheinböllen, Arzfeld, Kirchberg, Daun, Gerolstein,
Kusel-Altenglan, Lauterecken-Wolfstein + Trier), **286 Regeln
`AUTO_IMPORTED`** (Bitburger Land, Altenkirchen-Flammersfeld,
Nordpfälzer Land, Herrstein-Rhaunen, Wittlich-Land,
Betzdorf-Gebhardshain) - technisch nutzbar (benannte Organisation,
belegter Geltungsbereich, echte Kontaktdaten), aber bewusst NICHT als
fachlich verifiziert gezählt, weil die Quelle nur eine eng verwandte
Zuständigkeit oder nur die generische Abgaben-Kategorie wörtlich
bestätigt, nicht "Erschließungsbeiträge" selbst. (323 + 286 = 609 aktive
Regeln = 608 neue aus diesem Abschnitt + 1 bereits bestehende
Trier-Regel; Leiningerlands 21 deaktivierte Regeln nicht mitgezählt.)

**Zurückgestellt**: Verbandsgemeinde Südeifel (65 Gemeinden) - Adresse aus
dem Anschriftenverzeichnis bekannt (Pestalozzistr. 7, 54673 Neuerburg),
aber die amtliche Organigramm-Seite ist clientseitig gerendert (JavaScript)
und lieferte über WebFetch/Browser/Browser-Rendering keine auslesbare
Abteilungsangabe für Erschließungsbeiträge - eine Adresse allein erfüllt
NICHT die Anforderung "konkret benannte zuständige Organisation" für diese
Auskunftsart, deshalb keine Regel angelegt.

### 12.1 Welle 2: 102 weitere Verbandsgemeinden (auf Nutzerauftrag "so viele Agenten wie möglich")

Auf ausdrücklichen Nutzerauftrag ("starte so viele Agenten wie möglich um
die NO_MATCH Fälle so schnell wie möglich zu vervollständigen") wurden 19
parallele Recherche-Agenten für die verbleibenden 115 RLP-Verbandsgemeinden
eingesetzt. Bewusstes Sicherheits-Design: die Agenten recherchierten
AUSSCHLIESSLICH (Web-Suche, keine Code-/Datenbankzugriffe) und lieferten
strukturierte Funde mit Quellenangabe zurück - jede Freigabe/jeder
Datenbank-Schreibzugriff blieb seriell bei einer einzigen Instanz, um
SQLite-Schreibkonflikte bei paralleler Nutzung zu vermeiden und die
Sourcing-Qualitätsprüfung nicht auf viele Instanzen zu verteilen.

**Ergebnis: 102 von 115 recherchierten Verbandsgemeinden mit amtlicher
Quelle belegt** (72 stark, 30 schwächer), **1390 neue MUNICIPALITY-Regeln,
0 Konflikte**. Damit sind jetzt **116 von 129 RLP-Verbandsgemeinden
abgedeckt** (vorher 14) - **1999 aktive ERSCHLIESSUNG-Regeln in RLP
insgesamt** (1578 `VERIFIED`, 421 `AUTO_IMPORTED`, direkt aus der
Datenbank abgefragt).

**12 Fälle blieben ehrlich als OFFEN gemeldet statt geraten** (keine
amtliche Quelle mit konkreter Abteilungszuordnung auffindbar, trotz
gründlicher Recherche inkl. Organigramm-PDFs, Telefonverzeichnissen,
Mitarbeiterseiten und - wo zugänglich - dem Landesportal service.rlp.de):
Adenau, Birkenfeld, Cochem, Selters (Westerwald), **Leiningerland**
(erneut geprüft - weiterhin ausschließlich ein Zeitungsartikel als einzige
gefundene Stütze, Sourcing-Standard bleibt konsequent angewendet),
Brohltal, Hermeskeil, Landstuhl, Hauenstein, Lambsheim-Heßheim, Bad
Breisig, Unkel. Zusammen mit Südeifel bleiben damit **13 von 129 RLP-VGs
offen** - realistischer, ehrlich ausgewiesener Rest statt erfundener
100 %.

**Eigenständige Nachprüfung statt blindes Übernehmen**: bei vier Fällen,
deren Beleglage von den Recherche-Agenten selbst als unsicher markiert
wurde, wurde die Quelle zusätzlich selbst abgerufen (curl/pdftotext) und
geprüft, bevor sie übernommen wurde:
- **Sprendlingen-Gensingen**: Quelle trägt den Titel "Erschließung von
  Grundstücken" - dieselbe Formulierung, die beim Daun-Fall (Abschnitt 12)
  ursprünglich eine Wasser-/Abwasser-Verwechslung ausgelöst hatte. Eigene
  Prüfung bestätigt: die Seite nennt "Erschließungsbeiträge" wörtlich UND
  den für § 129 BauGB charakteristischen "Gemeindeanteil von mindestens
  10 %" - eindeutig die richtige Rechtsgrundlage. Übernommen als stark.
- **Weilerbach**: Beleg war ein PDF, das für den Agenten nicht
  volltextdurchsuchbar war (Bild-Rendering-Verdacht) - eigene
  `pdftotext`-Extraktion bestätigt "Sachgebiet 3.1.4 - Erschließungs- und
  Ausbaubeiträge" wörtlich. Übernommen als stark.
- **Herxheim**: Beleg war nur ein Suchmaschinen-Snippet - eigener
  PDF-Abruf bestätigt eine amtliche "Beitragsrechtliche Stellungnahme in
  Bezug auf Erschließungsbeiträge" von Fachbereich 2, sogar eindeutiger
  als ursprünglich berichtet. Übernommen als stark.
- **Oberes Glantal**: einzige Quelle war das Landesportal service.rlp.de,
  das per ALTCHA-Bot-Schutz blockiert ist - weder der Agent noch die
  eigene Nachprüfung (curl, VG-eigene Seite ist rein JavaScript-basiert)
  konnte den Wortlaut selbst einsehen, nur mehrfach übereinstimmende
  Suchergebnis-Snippets. Da nicht selbst verifizierbar, bewusst auf
  **schwächer** herabgestuft statt mit derselben Sicherheit wie ein
  selbst gelesener Beleg übernommen zu werden.

Umgesetzt in `scripts/seed_erschliessung_vg_rlp_wave2.py`. AGS-Zuordnung
wird zur Laufzeit aus den amtlichen VG250-Rohdaten (`rlp_gemeinde_vg_map.csv`,
jetzt versioniert) nachgeschlagen statt (wie in der ersten Welle) je VG
händisch als Konstante gepflegt - sicherer bei 102 statt 14 Einheiten.
Dry-Run-Stichproben (u.a. Kirchheimbolanden-Stadt korrekt von der
Nachbar-VG Nordpfälzer Land unterschieden) und volle Testsuite (159 Tests)
grün vor Anwendung auf die echte Datenbank.

**Realistischer Restaufwand**: 119 von 129 RLP-Verbandsgemeinden bleiben
offen, plus die strukturell entsprechenden "Amtsverwaltungen" in
Schleswig-Holstein (SH nennt seine Verbandsgemeinde-Entsprechung "Amt")
und alle Verbandsgemeinde-/Amt-Äquivalente der übrigen 14 Bundesländer.
Bei einer Recherchedauer von real 1-2 Suchanfragen pro Einheit (Adresse
jetzt aus dem Anschriftenverzeichnis, nur noch die fachliche Zuständigkeit
einzeln zu prüfen) ist das kein Fix, sondern ein mehrwöchiges
Recherchevorhaben allein für RLP - der Nutzer hat dies nach Rückfrage
ausdrücklich bestätigt (gleiches Tempo/gleiche Sorgfalt fortsetzen, kein
verkürztes Verfahren).

## 13. Erweiterte Methodik auf ausdrücklichen Wunsch: Anschriftenverzeichnis, PVOG-API-Befund, Prüfstatus-Trennung

### 13.1 Destatis-Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen

Vom Nutzer bereitgestellt: `20260131_Anschriften_der_Gemeinde_und_
Stadtverwaltungen.xlsx` - das amtliche Destatis-Verzeichnis mit ARS/AGS,
Adresse und allgemeiner E-Mail für JEDE deutsche Gemeinde-/Stadtverwaltung,
jeden Landkreis und jede Verbandsgemeinde/jedes Amt/jede Samtgemeinde
(13.750 Zeilen, Stand 31.01.2026).

**Explizit beachtet** (Auftrag: "Die allgemeine Verwaltungs-E-Mail darf
nicht automatisch zum bestätigten Fachamtkontakt werden"):
`app/services/address_directory.py` liefert AUSSCHLIESSLICH
Organisationsname/Adresse/allgemeine E-Mail über den Amtlichen
Regionalschlüssel (ARS) - nie eine fachliche Zuständigkeitsaussage. Jede
Verwendung im Projekt kombiniert diese Adressdaten mit einer SEPARAT
belegten fachlichen Quelle (siehe Abschnitt 12).

**Kreuzvalidierung**: die Adressen für alle 5 in Abschnitt 12 recherchierten
Verbandsgemeinden stimmen exakt mit der unabhängigen Web-Recherche überein
- ein starker Beleg für die Zuverlässigkeit beider Quellen. Das Verzeichnis
beschleunigt künftige Durchläufe erheblich: die Adress-Recherche (bisher
~1 Suchanfrage je Einheit) entfällt, es bleibt nur noch die fachliche
Zuständigkeitsprüfung.

Getestet mit einer synthetischen Mini-Fixture (`tests/fixtures/
mini_anschriften.xlsx`) - die echte, große Datei wird NICHT in Tests
eingebunden und NICHT ins Repository übernommen (Destatis-Werk, wie auch
die VG250-Rohdaten).

### 13.2 PVOG-Bereitstelldienst-API: definitiver Befund

Auf Hinweis des Nutzers ("pvog.fitko.de - auch hier kannst du per API
suchen") die tatsächliche OpenAPI-Spezifikation direkt abgerufen
(`https://pvog.fitko.net/bereitstelldienst/api/v3/api-docs/
Datenbestandabruf`, Lizenz der API selbst: CC BY-SA 4.0). Ergebnis:

- **Genau ein Endpunkt** (`/v3/verwaltungsobjekte/xzufi-2-3-1`), der exakt
  liefert, was gesucht wird: "Leistungen, Leistungsspezialisierungen,
  Organisationseinheiten, Onlinedienste, Formulare und Zuständigkeiten"
  als XZuFi-Nachrichten, einschränkbar nach Amtlichem Regionalschlüssel.
- **Erfordert zwingend OAuth2** (`"security":[{"OAUTH2":[]}]`) mit einem
  echten Keycloak-Authorization-Code-Flow bei
  `pvog.fitko.net/auth/realms/pvog/...` - keine anonyme Nutzung möglich.

Das ist jetzt ein **definitiver, belegter Befund statt einer offenen
Frage** (vorheriger Stand: "Zugang unklar"). Eine Nutzung setzt voraus,
dass sich eine Organisation (z.B. civeloq) bei der FITKO als Konsument
registriert und OAuth2-Client-Credentials erhält - das kann nur der Nutzer
selbst veranlassen, keine KI-Sitzung. Auf Wunsch kann ein Registrierungs-
/Anfrage-Text dafür entworfen werden.

### 13.3 Prüfstatus-Trennung: "technisch abgedeckt" vs. "fachlich verifiziert" jetzt im Schema selbst

Der Auftrag definiert beide als getrennte Kennzahlen. Bisher setzte
`approve_entry()` bei JEDER Freigabe pauschal `verification_status=
VERIFIED` - unabhängig davon, ob die Quelle die Zuständigkeit wörtlich für
GENAU diese Auskunftsart bestätigt oder nur für eine eng verwandte
Leistung. Das hätte die 138 Bitburger-Land-/Altenkirchen-Flammersfeld-
Regeln (Abschnitt 12) fälschlich als "fachlich verifiziert" ausgewiesen.

**Korrektur**: `approve_entry()` hat jetzt einen
`resulting_verification_status`-Parameter (Standard weiterhin `VERIFIED`,
keine Verhaltensänderung für bereits bestehende Aufrufer). Bei schwächerer
Beleglage kann der Aufrufer `AUTO_IMPORTED` übergeben - die Regel bleibt
"technisch abgedeckt" (benannte Organisation + belegter Geltungsbereich +
nutzbarer Kontaktweg), zählt aber nicht als "fachlich verifiziert". Die
Begründung wird jetzt zusätzlich ins `notes`-Feld der Regel selbst
übernommen, nicht nur auf den Staging-Eintrag - sichtbar auch bei direkter
Abfrage von `jurisdictions`. Die 138 bereits (vor dieser Korrektur)
freigegebenen Regeln wurden rückwirkend korrigiert
(`scripts/fix_erschliessung_vg_verification_status.py`) - keine Änderung
an Geltungsbereich oder Behörde, nur am Prüfstatus.

Eigener Test (`test_approve_entry_with_weaker_evidence_does_not_get_
marked_verified`) sichert dieses Verhalten ab. Volle Testsuite (159 Tests)
weiterhin grün.

## 14. Strategiewechsel auf ausdrücklichen Wunsch: voller Fokus auf NO_MATCH bundesweit

Nutzer-Auftrag: "ich möchte das du dich voll auf die NO_MATCH
deutschlandweit konzentrierst" - statt der Land-für-Land-Recherche neuer
Auskunftsarten (Abschnitt 12) wurden ab hier gezielt zwei bereits in RLP/SH
diagnostizierte STRUKTURELLE Fehlermuster bundesweit gesucht und behoben,
da sie ohne neue externe Recherche auskommen (dieselbe, bereits real und
korrekt in der Datenbank vorhandene Behörde - nur ihr Geltungsbereich war
technisch falsch kodiert).

### 14.1 Kreisebenen-Scope-Fix bundesweit ausgeweitet

Das in RLP/SH gefundene Muster (eine Kreisverwaltung ist bereits korrekt
als Behörde vorhanden, ihre einzige Regel ist aber fälschlich auf eine
einzelne, willkürliche Gemeinde-AGS gepinnt statt auf den Kreis-Schlüssel)
wurde mit `app/services/kreis_scope_fix.py` (bereits getestet, 4 eigene
Tests) auf alle 16 Bundesländer angewendet
(`scripts/fix_kreis_level_scope_nationwide.py`). Befund außerhalb RLP/SH:
**44 weitere Fälle**, ausschließlich BAUAKTEN/BAULASTEN, in Brandenburg,
Mecklenburg-Vorpommern, Niedersachsen und Sachsen-Anhalt - **2.462
betroffene Gemeinden**. Dry-Run-verifiziert (0 Konflikte), auf die lokale
Dev-DB angewendet, per Stichprobe an 6 repräsentativen Gemeinden
nachverifiziert, volle Testsuite grün (159 Tests).

### 14.2 Nullscope-Fix bundesweit (12 weitere Fälle außerhalb RLP)

Das zweite in RLP gefundene Muster (eine Regel mit
ags/municipality/district/postal_code/street/state ALLE `None` - dadurch
technisch nie erreichbar, obwohl die Behörde real und korrekt benannt in
der Datenbank existiert) wurde bundesweit abgefragt: 68 aktive Regeln
betroffen. Davon **12 Fälle direkt und sicher behoben**
(`scripts/fix_nullscope_nationwide.py`, siehe Abschnitt dort für die
vollständige Liste): Saarland (4 Landesbehörden, STATE-Ebene - bestehende
Zeile direkt gepatcht statt eine neue zu staged, weil die
Konflikterkennung `state`/`matching_level` nicht prüft und eine neue
STATE-Regel dieselben `None`-Schlüsselfelder hätte wie die kaputte
Vorgänger-Zeile selbst), Bremen/Bremerhaven (3 Fälle, Stadtgemeinde-Trennung
per AGS verifiziert), Hamburg (1 zentrale Denkmalschutz-Behörde), Limburg
an der Lahn und Neustadt a. Rbge. (je 1, MUNICIPALITY-Ebene), Landkreis
Mühldorf a. Inn (2 Fälle, COUNTY-Ebene). Dry-Run-Stichprobe bestätigte u.a.
die korrekte Bremen-Stadt-vs.-Bremerhaven-Trennung und dass in Saarland
alle 52 Gemeinden für ALTLASTEN/DENKMALSCHUTZ jetzt matchen (vorher
NO_MATCH, da keine andere Regel existierte). Volle Testsuite grün (159
Tests).

**Bewusst zurückgestellt** (verbleibende 56 der 68 Nullscope-Fälle):

- **Berlins 12 Bezirksamt-Fälle** (DENKMALSCHUTZ + ALTLASTEN) und
  **Hamburgs 7 Bezirksamt-Fälle** (WASSERSCHUTZ/HOCHWASSERSCHUTZ) - beide
  Stadtstaaten haben in `AdministrativeUnit` nur EINE AGS
  (Berlin=11000000, Hamburg=02000000). Mehrere gleichrangige Bezirksämter
  können deshalb nicht je eine eigene MUNICIPALITY/COUNTY-Regel erhalten,
  ohne dass der Matcher `MULTIPLE_MATCHES` meldet - korrekt wäre eine
  DISTRICT-Ebene-Regel pro Bezirk, was voraussetzt, dass echte
  Gebäudedaten ein befülltes `district`-Feld mit dem exakten Bezirksnamen
  haben. Da aktuell 0 Gebäude importiert sind und beide Stadtstaaten in
  der 118.239-Kombinationen-Kennzahl ohnehin nur je 1 AGS-Einheit
  ausmachen, ist der Effekt auf die bundesweite NO_MATCH-Quote
  vernachlässigbar - technisch korrekt lösbar, aber unwirtschaftlich vor
  echten Gebäude-/Portfoliodaten.
- **Baden-Württembergs 11 GVV/VVG-Fälle** (DENKMALSCHUTZ) - jede
  Gemeindeverwaltungsgemeinschaft deckt eine SPEZIFISCHE, kleine Menge von
  Gemeinden ab (nicht einen ganzen Kreis wie beim Kreisebenen-Fix) und
  erfordert eine echte Mitgliedsgemeinden-Zuordnung pro GVV, die (anders
  als RLPs VG250-Verbandsgemeinde-Daten) nicht ohne Weiteres vorliegt -
  würde neue, gezielte Recherche pro GVV erfordern statt eines
  strukturellen Fixes.
- Ein Sonderfall ("Stiftung Preußische Schlösser und Gärten
  Berlin-Brandenburg") wurde geprüft und bewusst NICHT behoben: ein
  Sondervermögen für konkrete Schloss-/Parkanlagen hat keine
  flächendeckende Gebietszuständigkeit - eine Kreis-/Gemeinde-Zuordnung
  wäre erfunden, nicht belegt.

### 14.3 Verbleibender Umfang

Alle Zahlen aus Abschnitt 1-13 gelten mit den in 14.1/14.2 beschriebenen
Korrekturen als Delta, nicht als vollständige Neuberechnung - eine frische
bundesweite Kennzahl (118.239 Kombinationen) nach diesen Fixes ist im
Anschluss an diesen Bericht separat abgefragt worden, siehe Gesprächsverlauf
für den aktuellen Stand. Der weit überwiegende Teil des bundesweiten
NO_MATCH-Bestands bleibt strukturell auf echte, noch nicht recherchierte
externe Quellen angewiesen (Land-für-Land-Recherche wie in Abschnitt 12) -
die hier behobenen Fälle sind bewusst nur die kostenlos (ohne neue externe
Quelle) erreichbaren Strukturfehler.

## 15. Paralleler Multi-Agenten-Durchlauf auf ausdrücklichen Nutzerauftrag ("so viele Agenten wie möglich")

Auftrag: "starte so viele Agenten wie möglich um die NO_MATCH Fälle so
schnell wie möglich zu vervollständigen". Sicherheits-Design (unverändert
gegenüber Abschnitt 14 beibehalten): Agenten recherchieren AUSSCHLIESSLICH
(Web-Suche, kein Code-/Datenbankzugriff); jede Freigabe/jeder
Datenbank-Schreibzugriff blieb seriell bei einer einzigen Instanz, um
SQLite-Schreibkonflikte zu vermeiden und die Sourcing-Qualitätsprüfung
nicht auf viele Instanzen zu verteilen. Insgesamt liefen in diesem
Durchlauf 31 parallele Recherche-Agenten in mehreren Wellen.

### 15.1 Erschließungsbeiträge RLP - Welle 2 (102 weitere Verbandsgemeinden)

Siehe Abschnitt 12.1 für die vollständige Darstellung. Kurzfassung: 19
Agenten, 115 der verbleibenden 129 RLP-Verbandsgemeinden recherchiert,
102 mit amtlicher Quelle belegt (1390 neue Regeln), 13 ehrlich offen
(inkl. Südeifel). RLP-Erschließungsbeiträge damit von 14 auf 116 von 129
Verbandsgemeinden abgedeckt.

### 15.2 KAMPFMITTEL: fehlende Bundesländer ergänzt

Ein Recherche-Agent stellte fest, dass KAMPFMITTEL (Kampfmittelräumung)
bereits für 11 von 16 Bundesländern als zentrale Landesbehörde vorlag,
für Rheinland-Pfalz, Bayern, Sachsen und Sachsen-Anhalt aber komplett
fehlte - eine echte Lücke im ursprünglichen Datenbestand. Ergebnis:
- **Rheinland-Pfalz**: ADD - Kampfmittelräumdienst (KMRD), STATE-Ebene.
- **Sachsen**: PPSI - Kampfmittelbeseitigungsdienst (KMBD), STATE-Ebene.
- **Bayern**: KEINE einzige zentrale Stelle, sondern genau 2
  Sprengkommandos (München, Nürnberg), deren Zuständigkeit an
  Landkreisgrenzen verläuft (Ausnahme: Eichstätt und Donau-Ries gehen an
  Nürnberg trotz Regierungsbezirk-Zugehörigkeit zu München-Gebieten) - 96
  COUNTY-Regeln.
- **Sachsen-Anhalt**: bewusst NICHT behoben - der KBD ist organisatorisch
  identifiziert, aber die amtliche Seite veröffentlicht keine Adresse/
  Telefonnummer und verweist Bürger stattdessen an ihre örtliche
  Sicherheitsbehörde - kein amtlich belegter "verwendbarer Kontakt- oder
  Einreichungsweg" im Sinne des Auftrags.

Alle Quellen (RLP, Sachsen, Bayern-Telefonnummern) wurden eigenständig per
`curl` gegen die amtlichen Originalseiten nachverifiziert, nicht nur die
Agenten-Aussage übernommen.

**Bug gefunden und behoben**: beim Versuch, die RLP-Regel zu stagen, wurde
sie fälschlich als Konflikt mit der bereits bestehenden, völlig
unabhängigen Schleswig-Holstein-Regel gemeldet. Ursache:
`_find_matching_existing()` in `JurisdictionStagingService` verglich
ags/municipality/district/postal_code/street/house_number, aber NICHT
`state` - bei einer reinen STATE-Ebene-Regel sind alle diese Felder
IMMER None, wodurch jede neue STATE-Regel fälschlich mit der STATE-Regel
JEDES ANDEREN Bundeslands kollidierte. Behoben (state jetzt Teil des
Vergleichs), Regressionstest ergänzt, volle Testsuite grün (160 Tests).
Dieser Fix wirkt sich auf JEDE künftige STATE-Ebene-Regel aus, nicht nur
auf die vier hier ergänzten.

### 15.3 BODENDENKMALSCHUTZ Bayern: die auffälligste bundesweite Einzellücke

Vor diesem Durchlauf: 0 % Abdeckung in Bayern (2.056 von 2.056 Gemeinden
NO_MATCH) - der größte einzelne Cluster bundesweit. Ein Recherche-Agent
klärte zunächst die Verwaltungsstruktur: nach Art. 10 BayDSchG ist die
jeweilige Kreisverwaltungsbehörde (Landratsamt/kreisfreie Stadt) die
"Untere Denkmalschutzbehörde" - 96 COUNTY-Regeln decken damit ALLE
bayerischen Gemeinden ab (Faktor-~21-Hebel), keine Gemeinde-
Einzelrecherche nötig. (Derselbe Agent stellte außerdem fest: BAULASTEN
existiert in Bayern strukturell NICHT - amtlich bestätigt durch die
Bauordnungsamt-FAQ der Stadt Nürnberg - und KATASTER läuft über 51 Ämter
für Digitalisierung, Breitband und Vermessung, AEDBV, nicht über die
Landratsämter; beides bewusst nicht in diesem Durchlauf behoben, siehe
15.4.)

9 parallele Recherche-Agenten (8 Batches × 12 Kreise + 1 Nachtrag für
Garmisch-Partenkirchen, das im ursprünglichen Batch-Split versehentlich
ausgelassen wurde - selbst entdeckt durch einen programmatischen
Vollständigkeits-Abgleich gegen die echten 96 `AdministrativeUnit`-Kreise,
nicht durch manuelles Nachzählen). Ergebnis: **90 von 96
Kreisverwaltungen mit amtlicher Quelle belegt** (73 stark, 17
schwächer), **6 ehrlich als OFFEN gemeldet** statt geraten: Amberg
(kreisfreie Stadt - einzige gefundene Stütze war ein Zeitungsartikel,
bewusst nicht übernommen), Dillingen a.d.Donau, Neumarkt i.d.OPf.,
Neustadt a.d.Aisch-Bad Windsheim, Pfaffenhofen a.d.Ilm, Straubing-Bogen
(zwei konkurrierende, gleichrangige Organisationseinheiten ohne
eindeutige amtliche Zuordnung).

**Zweiter Bug gefunden und behoben** (vor Anwendung auf die echte DB):
eine Namens-Heuristik zur Unterscheidung Landkreis/kreisfreie Stadt hätte
mehreren kreisfreien Städten ohne "kreisfreie"/"Landkreis" im Namen
(München, Ingolstadt, Erlangen, Nürnberg, Kaufbeuren, Kempten, Memmingen,
Schwabach, Straubing, Weiden) fälschlich ein "Landratsamt"-Präfix
vorangestellt. Durch die tatsächliche `AdministrativeUnit`-Struktur
ersetzt (kreisfreie Stadt = ein Kreis, der aus genau einer Gemeinde
besteht - `ags_gemeinde="000"`), keine Namens-Heuristik mehr. Vor dem Fix
wären z.B. München-Stadt und München-Landkreis zwar nicht kollidiert
(unterschiedliche Namen im Skript), aber die Stadt-Behörde hätte
fälschlich "Landratsamt" im Namen getragen.

Dry-Run mehrfach verifiziert (u.a. München-Stadt vs. München-Landkreis,
Bayreuth-Stadt vs. -Landkreis, alle Namenskollisionsfälle korrekt
unterschieden, Garmisch-Partenkirchen), auf lokale Dev-DB angewendet,
volle Testsuite grün (160 Tests).

### 15.4 Bewusst zurückgestellt

- **Bayern BAULASTEN**: existiert strukturell nicht (s.o.) - sollte in
  einer künftigen Kennzahl-Betrachtung als "entfällt", nicht als
  NO_MATCH gezählt werden; das erfordert ggf. eine kleine
  Schema-Erweiterung (aktuell gibt es keine "nicht anwendbar"-Kategorie
  in `CoverageAnalysisService`), wurde in diesem Durchlauf bewusst nicht
  umgesetzt, um keine ungeprüfte Schemaänderung "nebenbei" einzuführen.
- **Bayern ERSCHLIESSUNG**: laut Recherche-Agent echte Gemeinde-/VGem-
  Ebene wie in RLP - kein struktureller Shortcut, müsste analog zu
  Abschnitt 12/15.1 Gemeinde für Gemeinde bzw. Verwaltungsgemeinschaft
  für Verwaltungsgemeinschaft recherchiert werden.

## 16. Fortsetzung desselben Durchlaufs: Kataster Bayern und Bodendenkmalschutz bundesweit

### 16.1 Kataster Bayern (Fortsetzung von 15.4)

Bayern führt das amtliche Liegenschaftskataster nicht über die 96
Landkreise/kreisfreien Städte, sondern über **51 Ämter für
Digitalisierung, Breitband und Vermessung (AEDBV)**, von denen jedes oft
mehrere Landkreise gemeinsam abdeckt. Ein Recherche-Agent erstellte die
vollständige Zuordnung anhand der rechtsverbindlichen VermBezV
(Verordnung über die Bezeichnung, den Sitz und die Bezirke der AEDBV in
Bayern) - eine noch belastbarere Quelle als eine reine Amtsseite, da
geltendes Recht statt einer Verwaltungsauskunft. **Alle 96 Landkreise
sind zugeordnet, keine offenen Fälle bei dieser Auskunftsart.** 96 neue
COUNTY-Regeln umgesetzt (`scripts/seed_kataster_bayern.py`); zwei bereits
bestehende MUNICIPALITY-Regeln (München, Augsburg) nehmen wie erwartet
weiterhin Vorrang.

### 16.2 Bodendenkmalschutz: 6 weitere Bundesländer

Zwei Recon-Agenten klärten die Struktur in 6 weiteren Bundesländern.
Ergebnis: **5 Länder zentralisieren die eigentliche Grabungs-/
Nachforschungsgenehmigung bei EINER Landesbehörde** - ein noch größerer
Hebel als Bayerns Kreismuster (`scripts/
fix_bodendenkmalschutz_zentrale_laender.py`):

| Bundesland | Zentrale Behörde | Rechtsgrundlage |
|---|---|---|
| Baden-Württemberg | Landesamt für Denkmalpflege im RP Stuttgart | § 21 DSchG BW |
| Mecklenburg-Vorpommern | Landesamt für Kultur und Denkmalpflege (LAKD) | § 12 DSchG M-V |
| Thüringen | Thüringisches Landesamt für Denkmalpflege und Archäologie (TLDA) | § 18 ThürDSchG |
| Hessen | Landesamt für Denkmalpflege Hessen / hessenARCHÄOLOGIE | § 22 HDSchG |
| Sachsen | Landesamt für Archäologie Sachsen | § 14 Abs. 2 SächsDSchG |

Bei Sachsen betrifft die Landesregel ausdrücklich NUR die Nachforschungs-
/Grabungsgenehmigung (§ 14 Abs. 2) - Erdarbeiten an bereits bekannten
Fundstellen (§ 14 Abs. 1) blieben bewusst unberührt, dort bliebe die
Kreis-Ebene zuständig. Alle 5 Adressen von einem zweiten Agenten gegen
die jeweilige amtliche Kontakt-/Impressumsseite verifiziert; Hessen
zusätzlich eigenständig per curl gegen denkmal.hessen.de/impressum
bestätigt.

**Niedersachsen** erwies sich als strukturell deutlich komplexer als
Bayern: nach § 19 Abs. 1 NDSchG ist der Landkreis untere
Denkmalschutzbehörde, ABER Gemeinden mit eigener unterer
Bauaufsichtsbehörde sind für ihr Gebiet SELBST zuständig. 8 parallele
Recherche-Agenten deckten dabei zwei Ausnahme-Kategorien auf
(`scripts/seed_bodendenkmalschutz_niedersachsen.py`):
1. Die abschließende gesetzliche Liste der "großen selbständigen
   Städte" (§ 14 Abs. 5 NKomVG): Celle, Cuxhaven, Goslar, Hameln,
   Hildesheim, Lingen (Ems), Lüneburg.
2. Weitere Städte OHNE diesen gesetzlichen Status, die laut eigener/
   Landkreis-Website trotzdem eigenständig zuständig sind (vermutlich
   individuelle Übertragung nach § 57 NBauO): Wolfenbüttel, Peine,
   Göttingen, Einbeck, Melle, Winsen (Luhe).

Sonderfall Region Hannover: **keine pauschale Kreis-Regel**, da die
Region nur für 8 namentlich amtlich bestätigte Mitgliedskommunen
zuständig ist; für die übrigen Mitgliedskommunen war das nicht amtlich
verifizierbar und bleibt bewusst offen statt geraten. Ergebnis: 41
Landkreis-/kreisfreie-Stadt-Regeln + 22 Sonderstadt-Regeln. 3 Landkreise
blieben ehrlich offen (Grafschaft Bentheim, Harburg, Heidekreis).

**Bodendenkmalschutz ist damit jetzt in 7 von 16 Bundesländern
strukturell abgedeckt** (Bayern, Baden-Württemberg, Mecklenburg-
Vorpommern, Thüringen, Hessen, Sachsen, Niedersachsen) - die übrigen 9
Länder (Berlin, Brandenburg, Bremen, Hamburg, Nordrhein-Westfalen,
Rheinland-Pfalz, Saarland, Sachsen-Anhalt, Schleswig-Holstein) sind für
diese Auskunftsart noch nicht systematisch untersucht.

### 16.3 Weiterer Bug-Fix mit bundesweiter Wirkung

Beim Versuch, die erste zentrale Landesregel zu stagen, wurde ein
bereits in Abschnitt 15.2 dokumentierter, aber erst dort für KAMPFMITTEL
gefundener Bug erneut relevant: `_find_matching_existing()` prüfte
`state` nicht mit, wodurch jede neue STATE-Ebene-Regel fälschlich mit
JEDER anderen STATE-Regel kollidiert wäre. Der bereits in Abschnitt 15.2
beschriebene Fix (state jetzt Teil des Vergleichs) griff hier korrekt
(0 Konflikte beim Dry-Run) - ein Beleg dafür, dass der Fix tatsächlich
für alle künftigen STATE-Ebene-Regeln wirkt, nicht nur für den
ursprünglichen KAMPFMITTEL-Fall.

## 17. Bodendenkmalschutz: Brandenburg, Bremen, Hamburg, Sachsen-Anhalt, NRW

### 17.1 Drei weitere zentrale Landesbehörden

Analog zu Abschnitt 16.2 zentralisieren auch Brandenburg, Bremen und
Hamburg die Nachforschungs-/Grabungsgenehmigung bei einer einzigen
Landesbehörde (`scripts/fix_bodendenkmalschutz_zentrale_laender_2.py`),
jeweils per curl gegen die amtliche Impressum-/Kontaktseite
selbstständig verifiziert:

| Bundesland | Zentrale Behörde |
|---|---|
| Brandenburg | Brandenburgisches Landesamt für Denkmalpflege und Archäologisches Landesmuseum (BLDAM), Wünsdorf |
| Bremen | Landesamt für Denkmalpflege Bremen - Landesarchäologie (Bremen UND Bremerhaven) |
| Hamburg | Archäologisches Museum Hamburg (Helms-Museum) |

Bremens neue Regel ist bewusst eine eigene, von der bereits bestehenden
(Abschnitt 10) Bremen-Stadt-only-Regel für die allgemeine
Denkmalschutzbehörde getrennte Authority, da die Bodendenkmalpflege
anders als die allgemeine Baudenkmalpflege für beide Städte (Bremen und
Bremerhaven) zentral beim Landesamt liegt. 3 neue STATE-Regeln, 0
Konflikte - erneute Bestätigung des Abschnitt-15.2/16.3-Fixes.

### 17.2 Sachsen-Anhalt: Kreis-Ebene mit 2 Sonderstädten

Nach § 9 Abs. 3 DenkmSchG LSA ist die untere Denkmalschutzbehörde
(Landkreis/kreisfreie Stadt) zuständig; das Landesamt für Denkmalpflege
und Archäologie (LDA, Halle) ist reine Fachbehörde ohne
Genehmigungskompetenz. 3 parallele Recherche-Agenten belegten **alle 14
Landkreise/kreisfreien Städte** mit amtlicher Quelle (meist über die
einheitliche Leistungsseite "Bodendenkmalpflege" des
Bürgerservice-Portals Sachsen-Anhalt) - keine offenen Fälle
(`scripts/seed_bodendenkmalschutz_sachsenanhalt.py`). Zusätzlich 2
kreisangehörige Städte mit eigener, vom Landkreis getrennter unterer
Denkmalschutzbehörde identifiziert: Köthen (Anhalt) (Landkreis
Anhalt-Bitterfeld) und Hansestadt Stendal (Landkreis Stendal - dort mit
explizitem Hinweis, dass das Bauordnungsamt des Landkreises für das
Gebiet der Hansestadt NICHT zuständig ist). Ergebnis: 14 COUNTY- + 2
MUNICIPALITY-Regeln, 0 Konflikte.

### 17.3 Nordrhein-Westfalen: gespaltenes System nach Gemeindetyp

NRW hat als einziges bisher untersuchtes Bundesland eine echte
Zweiteilung nach § 15 i.V.m. § 21 DSchG NRW: für kreisangehörige
Gemeinden ist der Landrat als "untere staatliche Verwaltungsbehörde"
Obere Denkmalbehörde (wie ein normales Kreismuster), für kreisfreie
Städte dagegen NICHT die Stadt selbst, sondern die zuständige
Bezirksregierung (5 in NRW: Arnsberg, Detmold, Düsseldorf, Köln,
Münster) - landeseinheitlich organisiert als "Dezernat 35". 10 parallele
Recherche-Agenten (`scripts/seed_bodendenkmalschutz_nrw.py`):

- **25 von 31 Landkreisen** mit amtlicher Quelle belegt (COUNTY-Ebene).
  6 blieben ehrlich offen (Borken, Düren, Herford, Höxter,
  Rhein-Erft-Kreis, Soest - keine amtliche Quelle mit konkreter
  Organisationseinheit auffindbar).
- **Alle 5 Bezirksregierungen** amtlich belegt und jeweils allen ihren
  kreisfreien Städten zugeordnet - diese Zuordnung wurde NICHT vom
  Agenten übernommen, sondern direkt aus der echten
  `AdministrativeUnit.ags_regierungsbezirk`-Struktur abgeleitet und
  stichprobenartig gegen die Agenten-Aussagen verifiziert (Bielefeld →
  Detmold, Bonn/Köln/Leverkusen → Köln - beide bestätigt).

Ergebnis: 25 COUNTY- + 22 COUNTY-Regeln (kreisfreie Städte, matching
level COUNTY da Regierungsbezirks-weit) = 47 neue Regeln, 0 Konflikte.
Matching stichprobenartig verifiziert: Bielefeld (kreisfrei) → BezReg
Detmold, Bonn (kreisfrei) → BezReg Köln, Borken (offen) → korrekt
NO_MATCH.

### 17.4 Zwischenstand Bodendenkmalschutz

**Bodendenkmalschutz ist damit jetzt in 12 von 16 Bundesländern
strukturell abgedeckt** (Bayern, Baden-Württemberg, Mecklenburg-
Vorpommern, Thüringen, Hessen, Sachsen, Niedersachsen, Brandenburg,
Bremen, Hamburg, Sachsen-Anhalt, Nordrhein-Westfalen) sowie zusätzlich
Rheinland-Pfalz und Schleswig-Holstein aus früheren Sitzungen (macht 14
von 16). Offen bleiben: Berlin (strukturell blockiert - Bezirksdaten auf
Gebäude-Ebene fehlen) und Saarland (Landesbehörde identifiziert, aber
Adresse wegen Bot-Schutz auf saarland.de noch nicht unabhängig
verifizierbar).

## 18. Liegenschaftskataster (KATASTER): zweite Welle, 11 von 16 Ländern neu abgedeckt

Nach Abschluss der aktuellen Bodendenkmalschutz-Welle wurde die
NO_MATCH-Analyse auf andere Auskunftsarten ausgeweitet. Eine
state-gescopte Auszählung ergab: KATASTER war nach Bayern/RLP/SH nur in
3 von 16 Ländern abgedeckt, mit 91 von 401 Landkreisen/kreisfreien
Städten bundesweit ohne COUNTY-Regel - der größte verbleibende
strukturelle Nationwide-NO_MATCH-Block. 6 parallele Recherche-Agenten
(je ein Batch für Hessen, Thüringen, Niedersachsen, Sachsen-Anhalt,
Baden-Württemberg/Saarland/Mecklenburg-Vorpommern, sowie einen
Kleinstlücken-Batch für NRW/Sachsen/Hamburg/Berlin) deckten sechs
unterschiedliche Organisationsmuster ab (`scripts/seed_kataster_wave2.py`):

| Bundesland | Muster |
|---|---|
| Sachsen-Anhalt | Zentral: LVermGeo, 4 "Geokompetenz-Center" (Magdeburg, Stendal, Dessau-Roßlau, Halle) |
| Niedersachsen | LGLN, Regionaldirektionen mit einzelnen Katasterämtern je Kreisstadt |
| Baden-Württemberg | Jeder Land-/Stadtkreis führt sein Kataster selbst |
| Saarland | Zentral: LVGL, eine "Zentrale Außenstelle" (Saarlouis) für alle Kreise |
| Mecklenburg-Vorpommern | Untere Vermessungs- und Geoinformationsbehörden je Landkreis/kreisfreier Stadt |
| Hessen | HVBG, 7 "Ämter für Bodenmanagement" (ÄfB) |
| Thüringen | TLBG, 8 Zweigstellen je nach Kreisstadt |
| NRW/Sachsen | städtische Vermessungsämter für einzelne Restlücken |

Wichtiger Zwischenschritt: Von den 91 zunächst als fehlend markierten
Kreisen erwiesen sich **9 als Scheinlücken** (Freiburg, Stadtkreis
Heilbronn, Stadtkreis Karlsruhe, Oldenburg-Stadt, Osnabrück-Stadt,
Rostock-Stadt, Mülheim an der Ruhr, Solingen, Leipzig-Stadt sowie
Hamburg) - die reine COUNTY-Auszählung hatte jeweils eine bereits
bestehende, höher priorisierte MUNICIPALITY-Regel übersehen; eine neue
COUNTY/STATE-Regel wäre dort wirkungslos (toter Code) gewesen und wurde
deshalb nicht angelegt. Dabei wurde zusätzlich ein Datenfehler im
ersten Skriptentwurf gefunden und korrigiert: die AGS von Stadtkreis
und Landkreis Heilbronn (08121 vs. 08125) bzw. Stadtkreis und Landkreis
Karlsruhe (08212 vs. 08215) waren zunächst vertauscht (beide Male
identischer `county_name` "Heilbronn"/"Karlsruhe" ohne Kreis-/
Stadt-Unterscheidung in den Rohdaten) - richtiggestellt anhand der
tatsächlichen Gemeinde-Anzahl je AGS.

Ein weiterer Nebenfund: Hessens neue kreisfreie Stadt Hanau (AGS 06415,
"Hanau-Auskreisungsgesetz", ausgegliedert aus dem Main-Kinzig-Kreis
zum 1.1.2026) wurde unabhängig über die offizielle Pressemitteilung
des Hessischen Innenministeriums verifiziert. Die Datenbank enthält
aktuell 0 Gebäude mit dieser neuen AGS oder mit der alten
Main-Kinzig-Kreis-AGS und Stadt Hanau - die Kreisreform hat also noch
keine aktive Auswirkung auf bestehende Zuordnungen, sollte aber bei
künftigen Adressimporten beachtet werden.

Berlin bleibt strukturell offen: es existieren bereits 12 bezirkliche
MUNICIPALITY-Regeln (aus einer früheren Sitzung), die wegen fehlender
Bezirks-Granularität in den Gebäudedaten alle gleichzeitig zutreffen
und korrekt `MULTIPLE_MATCHES` statt eines geratenen Einzeltreffers
ergeben - derselbe strukturelle Engpass wie bei BODENDENKMALSCHUTZ.

**Ergebnis: 80 neue COUNTY-Regeln, 0 Konflikte.** Matching
stichprobenartig verifiziert (Köthen/Anhalt-Bitterfeld, Gera/TLBG
Zeulenroda-Triebes, Main-Kinzig-Kreis/Hanau, Landkreis Heilbronn/
Karlsruhe nach Korrektur, Schwerin/Ludwigslust-Parchim). KATASTER ist
damit strukturell in 11 von 16 Bundesländern neu abgedeckt (zusammen
mit Bayern/RLP/SH: 14 von 16) - offen bleiben nur noch Berlin
(strukturell, s.o.) und ein kleiner Rest einzelner Landkreise ohne
auffindbare amtliche Quelle.

## 19. Erschließungsbeiträge: Mecklenburg-Vorpommern und Schleswig-Holstein

Erschließungsbeiträge (§ 127 ff. BauGB) werden bundesweit grundsätzlich
von der einzelnen GEMEINDE selbst erhoben - mit ca. 11.000 Gemeinden
deutschlandweit das strukturell schwierigste Feld dieser Mandats. In
Rheinland-Pfalz (frühere Sitzung) löste sich das über die
Verbandsgemeinden. Eine Strukturrecherche in 8 weiteren Bundesländern
ergab: Mecklenburg-Vorpommern (76 Ämter decken 684 von 724 Gemeinden ab,
-84 % Rechercheaufwand) und Schleswig-Holstein (83 Ämter decken 1018
von ca. 1104 Gemeinden ab, >92 %) haben die beste Hebelwirkung;
Niedersachsen und Sachsen sind mittelgut, Hessen und Saarland praktisch
nicht hebelbar (fast nur Einheitsgemeinden).

### 19.1 Mecklenburg-Vorpommern

Nach § 127 Abs. 2 KV M-V (Kommunalverfassung M-V) "besorgt das Amt ...
die Veranlagung und Erhebung der Gemeindeabgaben für die
amtsangehörigen Gemeinden" - Erschließungsbeiträge sind Gemeindeabgaben
im Sinne des KAG M-V. Ein Recherche-Agent fand zusätzlich eine einzige
offizielle XLSX-Datei des Ministeriums für Inneres, Bau und
Digitalisierung M-V ("Kommunalverzeichnis"), die sowohl alle 76
Amtsadressen ALS AUCH die vollständige Gemeinde-AGS-Zuordnung enthält -
selbst heruntergeladen und geparst (kein externer Kreuzreferenz-Bedarf
wie noch bei RLP). Ergebnis: 76 neue Authorities, 684 neue
MUNICIPALITY-Regeln (`scripts/seed_erschliessung_mv.py`), 0 Konflikte.

### 19.2 Schleswig-Holstein

Nach § 3 Abs. 1 AO (Amtsordnung SH) "führt [das Amt] nach [den]
Beschlüssen die Selbstverwaltungsaufgaben der amtsangehörigen Gemeinden
durch" - unabhängig gegen den Gesetzestext verifiziert. Anders als M-V
gibt es in SH keine einzelne Datei mit Amtsadressen UND
Gemeinde-Zuordnung zugleich - daher wurden zwei komplementäre Quellen
kombiniert:
- Die amtliche Destatis-Datei "Gemeinden in Deutschland ... am
  31.12.2025" (Amtlicher Regionalschlüssel mit Gemeindeverband-Spalte)
  wurde selbst heruntergeladen und geparst - liefert die vollständige
  Gemeinde-zu-Amt-Zuordnung (1018 Gemeinden in 83 Ämtern) inkl. AGS.
- 11 parallele Recherche-Agenten ermittelten für jedes der 83 Ämter
  einzeln die Amtssitzadresse von dessen offizieller Website (keine
  zentrale Adressliste vorhanden).

Alle 83 recherchierten Adressen konnten eindeutig den 83
Destatis-Amtsnamen zugeordnet werden (3 Sonderfälle mit abweichender
amtlicher Kurzbezeichnung im Destatis-Verzeichnis: "Burg-St.
Michaelisdonn", "Heider Umland", "Eider"). Ergebnis: 83 neue
Authorities, 1018 neue MUNICIPALITY-Regeln
(`scripts/seed_erschliessung_sh.py`), 0 Konflikte.

### 19.3 Niedersachsen und Sachsen: keine Adress-Recherche mehr nötig

Bei der Strukturrecherche zu Niedersachsen fiel auf, dass das amtliche
Anschriftenverzeichnis "Anschriften der Gemeinde- und Stadtverwaltungen"
(Statistische Ämter des Bundes und der Länder), das in dieser Sitzung
bereits für Kreis-Adressen bei BODENDENKMALSCHUTZ und KATASTER genutzt
wurde (`app/services/address_directory.py`), auch eine eigene Satzart
für die Verwaltungsgemeinschafts-Ebene führt (`SATZART_VERBANDSGEMEINDE
= 50`, Kommentar im Modul: "Verwaltungsgemeinschaft/Verbandsgemeinde/
Amt/Samtgemeinde"). Ein direkter Blick in die bereits lokal vorliegende
Datei bestätigte: sowohl Niedersachsens 114 Samtgemeinden als auch
Sachsens 70 Verwaltungsgemeinschaften/-verbände sind darin mit
vollständiger Anschrift UND der kompletten Mitgliedsgemeinden-Zuordnung
(inkl. amtlichem Gemeindeschlüssel) enthalten - für beide Länder war
dadurch KEINE zusätzliche Recherche-Agentenwelle für Adressen nötig
(anders als noch bei Schleswig-Holstein), nur eine Rechtsgrundlagen-
Recherche pro Land.

**Niedersachsen**: § 98 Abs. 5 Satz 1 NKomVG (unabhängig über zwei
Quellen bestätigt) - die Samtgemeinde "führt die Kassengeschäfte der
Mitgliedsgemeinden und veranlagt und erhebt für diese die
Gemeindeabgaben". 114 neue Authorities, 650 neue MUNICIPALITY-Regeln
(`scripts/seed_erschliessung_ni.py`), 0 Konflikte.

**Sachsen**: die Rechtsgrundlage liegt - anders als ursprünglich
angenommen - nicht in der SächsGemO, sondern im eigenständigen
Sächsischen Gesetz über kommunale Zusammenarbeit (SächsKomZG): § 8
Abs. 1 (Verwaltungsverband erledigt "Vorbereitung und Vollzug der
Beschlüsse der Mitgliedsgemeinden" und "Geschäfte der laufenden
Verwaltung"), § 5 Abs. 4 (Vorschriften über Gebühren/Beiträge gelten
entsprechend), § 36 Abs. 3 (gilt für Verwaltungsgemeinschaften
entsprechend). Beim Parsen der Datei wurde eine echte Dublette in der
Rohdatei selbst entdeckt (zwei Gemeinden mit identischer ARS/AGS-Zeile
zweifach gelistet) und bereinigt - danach exakt 179 zugeordnete
Gemeinden, was exakt der unabhängig recherchierten
Sekundärquellen-Schätzung (158+21) entspricht. 70 neue Authorities, 179
neue MUNICIPALITY-Regeln (`scripts/seed_erschliessung_sn.py`), 0
Konflikte.

### 19.4 Sachsen-Anhalt und Brandenburg: dieselbe Adress-Abkürzung

Nachdem sich das bundesweite Anschriftenverzeichnis bereits für
Niedersachsen und Sachsen als vollständige Adress- UND
Gemeinde-Zuordnungsquelle erwiesen hatte, wurde direkt geprüft, ob es
auch die beiden anderen bereits als hebelbar identifizierten Länder
(Sachsen-Anhalt: 18 Verbandsgemeinden, Brandenburg: ca. 50 Ämter)
abdeckt - beide Male ja, exakt mit der erwarteten Anzahl (18 bzw. 52
Einheiten). Für beide Länder war daher nur noch eine fokussierte
Rechtsgrundlagen-Recherche pro Land nötig, keine Adress-Agentenwelle.

**Sachsen-Anhalt**: § 91 Abs. 2 Satz 1 KVG LSA - "Die
Verbandsgemeindeverwaltung führt die Verwaltungsgeschäfte aller
Aufgaben des eigenen Wirkungskreises der Mitgliedsgemeinden in deren
Namen und in deren Auftrag." Wortlaut per Live-Browser-Abruf direkt
gegen die amtliche Landesrecht-Datenbank
(landesrecht.sachsen-anhalt.de) wort-für-wort verifiziert (die
JS-basierte "Bürgerservice"-Anwendung ließ sich per Browser, aber nicht
per curl rendern). 18 neue Authorities, 114 neue MUNICIPALITY-Regeln
(`scripts/seed_erschliessung_sachsenanhalt.py`), 0 Konflikte.

**Brandenburg**: § 135 Abs. 3 BbgKVerf - "Das Amt besorgt die Kassen-
und Rechnungsführung ... für die amtsangehörigen Gemeinden. Dazu
gehören auch die Veranschlagung und Erhebung der Gemeindeabgaben."
Ebenfalls per Live-Browser-Abruf direkt gegen bravors.brandenburg.de
wort-für-wort verifiziert. Von 52 gefundenen Verwaltungseinheiten sind
50 klassische "Ämter" (direkt durch die verifizierte Vorschrift
gedeckt, Tier "stark"/VERIFIED); 2 Sonderfälle mit abweichender
Bezeichnung ("Verbandsgemeinde Liebenwerda", "Erfüllende Gemeinde"
Schwedt/Oder) wurden vorsichtshalber als "schwächer"/AUTO_IMPORTED
eingestuft, da ihre genaue Rechtsgrundlage (vermutlich GKGBbg statt
BbgKVerf) nicht einzeln verifiziert wurde. 52 neue Authorities, 272
neue MUNICIPALITY-Regeln (`scripts/seed_erschliessung_brandenburg.py`),
0 Konflikte.

### 19.5 Baden-Württemberg, Thüringen, Bayern: dieselbe Adress-Abkürzung, deutlich größerer Massstab

Ein direkter Blick in dieselbe bundesweite Anschriftendatei zeigte, dass
noch drei weitere, bisher nicht als "RLP-artig hebelbar" identifizierte
Länder eine sehr grosse Verwaltungsgemeinschafts-Struktur besitzen -
alle drei bereits mit vollständiger Adresse UND Mitgliedsgemeinden-
Zuordnung in der Datei enthalten:

| Land | Einheiten | Abgedeckte Gemeinden | Anteil |
|---|---|---|---|
| Baden-Württemberg | 270 (156 GVV + 114 vereinbarte VG) | 911 von 1101 | 83 % |
| Thüringen | 79 (42 VG + 37 erfüllende Gemeinden) | 491 von 601 | 82 % |
| Bayern | 311 Verwaltungsgemeinschaften | 982 von 2056 | 48 % |

Bayern hat trotz des niedrigeren Prozentsatzes (viele grosse
eigenständige Städte/Gemeinden zusätzlich) mit 982 Gemeinden die
grösste absolute Einzel-Länder-Ergänzung dieser gesamten Welle.

**Rechtsgrundlagen** (jeweils per Live-Browser-Abruf direkt gegen die
amtliche Quelle wort-für-wort verifiziert):
- **Baden-Württemberg**: § 61 Abs. 3 Nr. 4 GemO BW zählt "die Abgaben-,
  Kassen- und Rechnungsgeschäfte" explizit als sog. "Erledigungsaufgabe"
  des Gemeindeverwaltungsverbands auf; Abs. 7 erstreckt dies
  ausdrücklich auf die vereinbarte Verwaltungsgemeinschaft.
- **Thüringen**: § 47 Abs. 2 Satz 2-3 ThürKO - die Verwaltungsgemeinschaft
  "führt diese Aufgaben ... als Behörde der jeweiligen Mitgliedsgemeinde
  nach deren Weisung aus"; § 51 Abs. 1 Satz 2 ThürKO erstreckt dies auf
  die erfüllende Gemeinde.
- **Bayern**: Art. 4 Abs. 2 VGemO - dieselbe "als Behörde ... nach deren
  Weisung"-Formulierung wie in Thüringen (beide Länder haben historisch
  denselben Vorschriftentyp).

**Datenqualitätsfund**: Beim Parsen der Bayern-Daten wurden 946 echte
Dubletten in der Rohdatei selbst entdeckt (identische ARS/AGS-Zeile
mehrfach gelistet, dasselbe Muster wie bereits bei Sachsen und
Brandenburg) und bereinigt. Zusätzlich wurden 3 echte Namenskollisionen
gefunden (zwei bayerische Verwaltungsgemeinschaften heissen jeweils
"Altenstadt", "Velden" bzw. "Rain", liegen aber in verschiedenen
Landkreisen) - ohne Behebung hätte die zweite Zeile beim Aufbau des
Python-Dictionarys die erste stillschweigend überschrieben und deren
Gemeinden verloren (von flake8 automatisch als F601 "dictionary key
repeated" erkannt). Behoben durch Anhängen der Postleitzahl an den
Namen zur Disambiguierung, verifiziert dass beide Einheiten korrekt als
getrennte Authorities mit ihren jeweiligen Mitgliedsgemeinden bestehen.

Ergebnis: 270 + 79 + 311 = 660 neue Authorities, 911 + 491 + 982 = 2384
neue MUNICIPALITY-Regeln (`scripts/seed_erschliessung_bw.py`,
`scripts/seed_erschliessung_thueringen.py`,
`scripts/seed_erschliessung_bayern.py`), 0 Konflikte. Matching
stichprobenartig verifiziert inkl. der beiden disambiguierten
Bayern-Kollisionsfälle.

### 19.6 Zwischenstand

**Erschließungsbeiträge sind damit jetzt in 10 von 16 Bundesländern
strukturell abgedeckt** (Rheinland-Pfalz, Mecklenburg-Vorpommern,
Schleswig-Holstein, Niedersachsen, Sachsen, Sachsen-Anhalt,
Brandenburg, Baden-Württemberg, Thüringen, Bayern) - zusammen 5301 neue
MUNICIPALITY-Regeln in dieser Sitzung. In allen Ländern bewusst NICHT
abgedeckt: die kreisfreien Städte und amtsfreien/eigenständigen
Gemeinden, die sich selbst verwalten und Einzelrecherche bräuchten -
das bleibt für eine spätere Sitzung offen, ebenso wie die übrigen 6
Länder (Berlin, Bremen, Hamburg - Stadtstaaten ohne
Verbandsgemeinde-Konzept; Hessen, NRW, Saarland - laut Strukturrecherche
kaum bzw. keine Hebelwirkung vorhanden).

## 20. Bauakten-/Baulastenauskunft: von 6 auf praktisch alle 16 Bundesländer

Eine frische Bestandsaufnahme zeigte: BAUAKTEN und BAULASTEN waren nach
der `state`-Spalte nur in 6 Ländern "abgedeckt" - eine
`ags`-basierte Nachzählung ergab aber, dass tatsächlich schon 210 von
401 Kreisen (BAUAKTEN) bzw. 139 von 401 (BAULASTEN) durch ältere,
nicht `state`-getaggte Massenimport-Regeln abgedeckt waren. Damit war
der wirkliche Umfang dieser Welle von Anfang an kleiner als die reine
`state`-Zählung vermuten liess - aber immer noch der mit Abstand
grösste verbleibende Bauakten-Baulasten-Block.

### 20.1 Ein zweiter echter Bug in der Konflikterkennung

Beim ersten Anwenden von BAUAKTEN Bayern fiel auf, dass 80 von 106
neuen Regeln als "NEW" durchgingen, obwohl fuer denselben AGS schon
eine `state=NULL`-Altregel existierte - ein sofortiger Nachtest zeigte,
dass `_find_matching_existing()` in `jurisdiction_staging.py` einen
strikten `state`-Abgleich verlangte, der `NULL != 'Bayern'` nie als
Treffer wertete. Ein zweiter, verwandter Bug betraf 8 von 10
Bayern-Ausnahmegemeinden: eine Altregel hatte zusaetzlich zum AGS auch
das Textfeld `municipality` befuellt, waehrend die neue Regel dieses
redundante Anzeigefeld nicht setzte - wieder ein exakter
Textvergleich, der zwei echte Duplikate als "verschieden" behandelte.

**Sofort behoben** (`app/services/jurisdiction_staging.py`): sobald
`ags` gesetzt ist, bestimmt es die Geografie bereits eindeutig - `state`
und `municipality` werden dann nicht mehr als hartes Vergleichsfeld
verlangt (district/postal_code/street/house_number bleiben unveraendert
Teil des Vergleichs, damit unterschiedliche Strassen/Bezirke innerhalb
desselben AGS weiterhin getrennt bleiben). 2 Regressionstests ergaenzt.
Die zuerst fehlerhaft angewendete Bayern-Charge wurde vor dem Fix aus
der echten Datenbank zurueckgerollt (Backup-Wiederherstellung) und nach
dem Fix sauber neu angewendet.

**Wichtiger Nebenfund:** eine systematische Pruefung zeigte ~374
vorbestehende (nicht in dieser Sitzung entstandene) Paare aktiver
Regeln mit identischem (request_type, matching_level, ags) quer durch
ALTLASTEN, BAUAKTEN, BAULASTEN, GRUNDBUCH, HOCHWASSERSCHUTZ,
KAMPFMITTEL, KATASTER und WASSERSCHUTZ. Da jedes Paar eine
Einzelfallentscheidung braucht (welche der beiden Regeln ist korrekt?),
wurde dies als eigene Aufgabe fuer eine spaetere Sitzung vorgemerkt statt
im Vorbeigehen "geloest".

### 20.2 Acht Bundesländer mit demselben Muster: Kreis + benannte Ausnahmeliste

Fuer BAUAKTEN und (meist) BAULASTEN gilt bundesweit fast durchgaengig
dasselbe Muster: Landkreise/kreisfreie Staedte sind untere
Bauaufsichtsbehoerde, mit einer geschlossenen, amtlich benannten Liste
von Ausnahme-Gemeinden, die trotz Kreisangehoerigkeit eine eigene
Bauaufsichtsbehoerde fuehren. Jede Rechtsgrundlage wurde per
Live-Browser-Abruf direkt gegen das amtliche Landesrecht-Portal
wort-fuer-wort verifiziert:

| Land | Kreis-Norm | Ausnahmen |
|---|---|---|
| Bayern | Art. 53 BayBO | 10 Kommunen (ZustVBau) - **kein Baulastenverzeichnis in Bayern ueberhaupt** |
| Sachsen | §§ 57/83 SächsBO | 4 eingekreiste Staedte (Görlitz, Hoyerswerda, Plauen, Zwickau) |
| Thüringen | §§ 60/90 ThürBO | 5 Grosse kreisangehoerige Staedte |
| Saarland | §§ 58/83 LBO | 6 Staedte (ZustV-LBO), inkl. Landeshauptstadt Saarbrücken |
| Hessen | §§ 60/85 HBO | 6 Sonderstatus-Staedte (§ 4a HGO) + Hanau als 6. kreisfreie Stadt seit 1.1.2026 |
| Bremen | - | Bremen-Stadt/Bremerhaven getrennt (wie bei anderen Auskunftsarten) |
| Hamburg | - | nur BAULASTEN (zentral beim LGV) - BAUAKTEN bleibt bewusst offen (bezirklich wie Berlin) |
| Baden-Württemberg | § 46 LBO/§ 15 LVG | 96 Grosse Kreisstädte (Quelle: Wikipedia-Kategorie, daher Tier "schwächer") - **BAULASTEN bewusst NICHT bearbeitet**, da § 72 Abs. 3 LBO die Verzeichnisfuehrung ausdruecklich der GEMEINDE zuweist, nicht dem Kreis (ein Kreis-Ebene-Skript waere dort schlicht falsch; braeuchte eine eigene Gemeinde-Ebene-Kampagne wie ERSCHLIESSUNG) |
| Nordrhein-Westfalen | § 57/85 BauO NRW | 167 Grosse/Mittlere kreisangehoerige Staedte (amtliche Verordnung nach § 4 GO NRW, direkt per Live-Abruf gelesen) |

Ergebnis: 26+26+44+24+64+4+1+140+440 = 769 neue Regeln ueber die 9
bearbeiteten Laender, abzueglich der jeweils schon per Altregeln
abgedeckten Faelle (von der Konfliktpruefung korrekt erkannt und
uebersprungen). Matching stichprobenartig verifiziert je Land,
inklusive der neuen kreisfreien Stadt Hanau.

### 20.3 Zwischenstand

**BAUAKTEN ist damit von 401 auf nur noch 78 offene Kreise gesunken**
(NI 30, RLP 18, Sachsen-Anhalt 11, Brandenburg 8, SH 7, MV 2, plus
Hamburg/Berlin je 1 bewusst offen wegen bezirklicher Struktur) -
**BAULASTEN von 401 auf 182** (dieselben 76 plus die bewusst
unbearbeiteten 96 Bayern + 9 Baden-Württemberg + 1 Berlin). Fuer die
verbleibenden 6 "einfachen" Laender (Niedersachsen, Rheinland-Pfalz,
Sachsen-Anhalt, Brandenburg, Schleswig-Holstein, Mecklenburg-
Vorpommern) laeuft bereits eine weitere Recherche-Welle nach demselben
Muster.

### 20.4 Abschluss der Welle: alle 6 verbleibenden Länder

Die 6 verbleibenden Länder wurden nach demselben Muster fertiggestellt
(je Kreis-Regel + benannte Ausnahmeliste, jede Rechtsgrundlage per
Live-Browser-Abruf direkt gegen das amtliche Landesrecht-Portal
wort-fuer-wort verifiziert):

| Land | Kreis-Norm | Ausnahmen | Neue Regeln |
|---|---|---|---|
| Niedersachsen | § 57 Abs. 1 / § 81 Abs. 4 NBauO | 7 grosse selbstaendige Staedte (§ 14 Abs. 5 NKomVG) | 104 |
| Mecklenburg-Vorpommern | § 57 Abs. 1 / § 83 Abs. 4 LBauO M-V | 4 grosse kreisangehoerige Staedte (§ 7 Abs. 2 KV M-V) | 4 (Rest bereits durch die frühere "Struktur-Korrektur 2026-09-26" VERIFIED) |
| Schleswig-Holstein | § 57 Abs. 1 / § 83 Abs. 4 LBO SH | 18 beliehene Staedte (§ 1 BauAufsÜV SH vom 3.6.2022) | 14 (Rest bereits durch dieselbe frühere Struktur-Korrektur VERIFIED) |
| Sachsen-Anhalt | § 56 Abs. 1 / § 82 Abs. 4 BauO LSA | 5 Bestandsschutz-Staedte (§ 87 Abs. 3 BauO LSA, Koethen/Naumburg/Stendal/Weissenfels/Zeitz) | 22 |
| Brandenburg | § 57 Abs. 1 / § 84 Abs. 4 BbgBO | 2 tatsaechlich beliehene Grosse kreisangehoerige Staedte (Eberswalde, Schwedt/Oder - NICHT Bernau/Falkensee/Oranienburg, die zwar den Status tragen, denen die Aufgabe aber laut amtlicher MIL-Liste nicht uebertragen wurde) | 18 |
| Rheinland-Pfalz | § 58 Abs. 1 Nr. 3 / § 86 Abs. 3 LBauO | 8 grosse kreisangehoerige Staedte (§ 6 GemO + 3 einzelne Landesverordnungen von 1960/1969/1972/1975) | 36 |

Bemerkenswert: fuer MV und SH war der grösste Teil der Kreis-Ebene
bereits durch eine fruehere, in dieser Sitzung erst nachtraeglich
entdeckte Kampagne ("Struktur-Korrektur 2026-09-26, bundesweite
Ausweitung des RLP/SH-Kreisebenen-Fixes") als VERIFIED angelegt worden
- die Konfliktpruefung erkannte dies korrekt und liess nur echte
Luecken (v. a. kreisfreie Staedte) neu durch, was fuer beide Laender
die tatsaechlich neu angelegte Regelzahl deutlich unter die urspruenglich
grob geschaetzte Zahl drueckte.

**Endstand (ags-basierte COUNTY-Abdeckung, bundesweit 401 Kreise):**
BAUAKTEN 399/401 (nur Hamburg und Berlin bewusst offen, beide
strukturell durch Bezirksverwaltung blockiert - identisches Muster wie
bei Bodendenkmalschutz/Kataster). BAULASTEN 295/401 (die Luecke
entspricht im Kern den 96 bayerischen Kreisen, in denen es gar kein
Baulastenverzeichnis gibt, plus Berlin plus einem kleinen Rest in
Baden-Württemberg, wo die Verzeichnisfuehrung nach § 72 Abs. 3 LBO BW
der Gemeinde statt dem Kreis obliegt und daher bewusst nicht ueber
diese Kreis-Ebene-Kampagne abgedeckt wurde). Damit ist die
Bauakten-/Baulastenauskunft-Welle fachlich abgeschlossen; alle
verbleibenden Luecken sind dokumentierte, bewusste Ausnahmen und keine
stillen Fehlstellen.

## 21. Nachtrag: falscher Alarm bei 12 kreisfreien Staedten (Messfehler in der Luecken-Query) - und ein echter Fund

Im Anschluss an Kapitel 20 wurde eine bundesweite ags-basierte
Luecken-Analyse ueber ALLE Auskunftsarten hinweg gefahren, um das
naechste sinnvolle Ziel zu finden. Eine erste Abfrage (COUNTY-Level
distinct ags) zeigte scheinbare Luecken bei KATASTER (9 kreisfreie
Staedte) und, in einem zweiten Schritt, bei DENKMALSCHUTZ,
BODENDENKMALSCHUTZ, ALTLASTEN, HOCHWASSERSCHUTZ und WASSERSCHUTZ fuer
insgesamt 12 kreisfreie Staedte (Darmstadt, Hanau, Kassel, Heilbronn,
Karlsruhe, Freiburg im Breisgau, Rostock, Leipzig, Oldenburg,
Osnabrueck, Muelheim an der Ruhr, Solingen). Drei parallele
Recherche-Agenten wurden losgeschickt und lieferten sauber belegte,
amtlich verifizierte Rechtsgrundlagen fuer alle 5 betroffenen
Bundeslaender.

**Der Fund war jedoch grossteils ein Messfehler:** die Lueckenanalyse
verglich fuer kreisfreie Staedte durchgaengig nur die 5-stellige
`ags_kreis` gegen `matching_level='COUNTY'` - und uebersah dabei
systematisch bereits bestehende `MUNICIPALITY`-Level-Regeln, die auf
die 8-stellige AGS (ags_kreis + "000") verweisen und wegen ihrer
hoeheren Prioritaet die fehlende COUNTY-Regel ohnehin korrekt
ersetzen. Ein Hinweis einer parallel arbeitenden Session (die
unabhaengig an BW-Kataster-AGS-Dubletten arbeitete) zeigte, dass
Heilbronn und Karlsruhe laengst korrekt abgedeckt waren - das war der
Ausloeser fuer eine Nachpruefung. Nach Korrektur der Abfrage (beide
AGS-Formen + beide Matching-Level pruefen, plus STATE-Level-Regeln mit
`ags IS NULL` separat beruecksichtigen) loesten sich KATASTER,
DENKMALSCHUTZ und BODENDENKMALSCHUTZ vollstaendig in Luft auf - alle
12 Staedte waren fuer diese drei Auskunftsarten bereits abgedeckt.

**Einziger echter Fund:** Kassel (als einzige der drei hessischen
kreisfreien Staedte) fehlten tatsaechlich ALTLASTEN, HOCHWASSERSCHUTZ
und WASSERSCHUTZ - eine isolierte historische Import-Luecke. Gefixt
mit `seed_altlasten_wasser_kassel.py` (3 neue Regeln, § 15 Abs. 3
HAltBodSchG / § 64 Abs. 3 HWG, gegen rv.hessenrecht.hessen.de
verifiziert).

**Zweiter, groesserer und noch offener Fund (unabhaengig vom
Messfehler, ueber eine gesonderte Pruefung bestaetigt):**
Nordrhein-Westfalen hat aktuell **ueberhaupt keine KAMPFMITTEL-
Abdeckung** - weder eine STATE-Level-Regel (anders als 13 der uebrigen
15 Laender) noch auch nur eine einzige COUNTY-Regel fuer irgendeinen
der ca. 53 Kreise/kreisfreien Staedte. Das ist keine Verwechslung,
sondern ein echter, substanzieller Fund, der aber eine eigene
Rechercheentscheidung braucht (vermutlich Bezirksregierungs-Ebene statt
Kreis-Ebene) und daher bewusst NICHT in dieser Sitzung bearbeitet,
sondern als eigene Aufgabe fuer eine kuenftige Sitzung vorgemerkt
wurde.

**Lehre fuer kuenftige Luecken-Analysen dieser Art:** bei kreisfreien
Staedten immer sowohl die 5-stellige `ags_kreis` (COUNTY) als auch die
8-stellige AGS (MUNICIPALITY) pruefen, sowie STATE-Level-Regeln (mit
`ags IS NULL`) separat gegenchecken, bevor eine vermeintliche Luecke
als echter Rechercheauftrag an Agenten weitergegeben wird - sonst
droht wie hier erheblicher Rechercheaufwand fuer nicht-existente
Luecken.

## 22. Erschließungsbeiträge "Phase 2": eigenständige Gemeinden bundesweit (7300 → 10749 von 10749, 100 %)

Bei derselben Gelegenheit fiel eine viel groessere, echte Luecke auf:
eine bundesweite ags-basierte Abdeckungspruefung fuer ERSCHLIESSUNG
zeigte nur 7300 von 10749 Gemeinden abgedeckt. Grund: die urspruengliche
Erschliessungsbeitraege-Kampagne (Kapitel 12/19) erfasste durchgaengig
nur Gemeinden, die einer Verbandsgemeinde/einem Amt/einer Verwaltungs-
gemeinschaft-aequivalenten Struktur angehoeren, ueber deren amtliche
Anschriftenliste (Satzart 50). Eigenstaendige ("amtsfreie") Gemeinden -
inklusive aller kreisfreien Staedte - blieben dabei durchgaengig
aussen vor; im BW-Skript sogar ausdruecklich so dokumentiert ("~190
eigenstaendige Gemeinden ... braeuchten Einzelrecherche").

Diese "Einzelrecherche" erwies sich als unnoetig: die Zustaendigkeits-
frage ist BUNDESRECHT und damit fuer alle 16 Laender identisch - § 127
Abs. 1 BauGB: "Die Gemeinden erheben zur Deckung ihres anderweitig
nicht gedeckten Aufwands fuer Erschliessungsanlagen einen
Erschliessungsbeitrag." (Wortlaut gegen gesetze-im-internet.de,
Bundesministerium der Justiz, verifiziert - Fundort ueber die korrekte
Ordner-URL `bbaug` statt der nahliegenden aber falschen Vermutung
`baugb` per Websuche ermittelt.) Jede eigenstaendige Gemeinde ist damit
schlicht ihre eigene Erschliessungsbehoerde - keine landesspezifische
Ausnahmeliste noetig, keine Agenten-Rechercheswelle wie bei Bauakten/
Baulasten, da die Adressdaten bereits im amtlichen Anschriften-
verzeichnis (Satzart 60) fuer jede Gemeinde vorliegen.

Umgesetzt fuer alle 13 Laender mit tatsaechlicher Restluecke (Berlin/
Bremen/Hamburg wurden parallel von einer anderen Sitzung importiert):

| Land | neue Regeln |
|---|---|
| Bayern | 1074 |
| Hessen | 421 |
| Rheinland-Pfalz | 301 |
| Niedersachsen | 291 |
| Sachsen | 239 |
| Nordrhein-Westfalen | 396 |
| Brandenburg | 141 |
| Baden-Württemberg | 190 |
| Thüringen | 110 |
| Sachsen-Anhalt | 104 |
| Schleswig-Holstein | 86 |
| Saarland | 52 |
| Mecklenburg-Vorpommern | 40 |

**3445 neue Regeln, alle mit identischem Konfliktergebnis
NEW=erwartete Zahl / andere=0** (kein einziger unerwarteter Konflikt
ueber alle 13 Laender hinweg - starkes Signal, dass die Analyse und
die Ausfuehrung korrekt waren). Bundesweite ERSCHLIESSUNG-Abdeckung
damit von 7300 auf 10745 von 10749 Gemeinden gestiegen (99,96 %).

Die letzten 4 fehlenden Gemeinden waren die 3 Stadtstaaten (Berlin,
Hamburg sowie die beiden bremischen Stadtgemeinden Bremen und
Bremerhaven) - keine "Sonderfaelle" im Sinne von Datenfehlern, sondern
schlicht ausserhalb des "eigenstaendige Flaechenland-Gemeinde"-Musters
der 13 vorherigen Skripte. Nachtraeglich mit
`seed_erschliessung_stadtstaaten.py` ergaenzt (4 Regeln, dieselbe
Rechtsgrundlage § 127 Abs. 1 BauGB, zentrale Senats-/Stadtverwaltungs-
adresse aus dem amtlichen Anschriftenverzeichnis - keine Hinweise auf
eine bezirkliche Aufspaltung der Erschliessungsbeitrags-Erhebung,
anders als bei Bauaufsicht/Bodendenkmalschutz). **Damit ist die
bundesweite ERSCHLIESSUNG-Abdeckung vollstaendig: 10749 von 10749
Gemeinden (100 %).**

## 23. Merge einer parallelen Session + eine echte, kleine DENKMALSCHUTZ-Luecke

Eine parallel arbeitende Session (eigener Branch
`claude/youthful-wozniak-d0a66f`) hatte unabhaengig an Saarlouis-
Bauakten/-Baulasten, 9 BW-Kataster-AGS-Ambiguitaeten sowie einer
alternativen, deutlich praeziseren ERSCHLIESSUNG-Recherche fuer
Stadtstaaten (12 einzeln recherchierte Berliner Bezirksaemter statt
einer generischen Sammelzeile) und Teilen von Hessen/NRW/Saarland
gearbeitet. Gemerged (Commit 9ca366b): der einzige echte Dateikonflikt
(`seed_erschliessung_stadtstaaten.py`, beide Branches hatten
unabhaengig Berlin/Bremen/Hamburg ergaenzt) wurde zugunsten der
praeziseren Peer-Version aufgeloest, danach per
`reconcile_erschliessung_stadtstaaten.py` auch die bereits angewendete
eigene DB nachgezogen (die 4 generischen Regeln liefen per `valid_to`
aus, die 15 praeziseren Regeln wurden freigegeben - Standard-
Staging-Mechanismus, auch ueber einen bewussten
CONTRADICTS_VERIFIED-Konflikt hinweg). Die inhaltliche Ueberschneidung
bei Hessen/NRW/Saarland (eigene vollstaendige aber generische
"§127 BauGB"-Abdeckung vs. Peer-Version mit praeziserer aber nur
teilweiser Einzelrecherche) wurde bewusst NICHT selbst aufgeloest,
sondern als eigene Aufgabe vorgemerkt (spawn_task, siehe
Session-Memory) - ein sorgfaeltiger Pro-Gemeinde-Abgleich braucht mehr
Zeit, als im Vorbeigehen sinnvoll waere.

Bei derselben Gelegenheit wurde die DENKMALSCHUTZ-Abdeckung bundesweit
mit der (aus Kapitel 21 gelernten) korrekten Zwei-Ebenen-Methodik neu
geprueft: 15 von 16 Laendern vollstaendig abgedeckt (Berlin strukturell
offen wie ueberall sonst; Saarland ueber eine STATE-Level-Regel
abgedeckt; Nordrhein-Westfalen zunaechst faelschlich als "31 Kreise
fehlen" markiert, aber bei Nachpruefung stellte sich heraus, dass NRW
DENKMALSCHUTZ grundsaetzlich auf GEMEINDE-Ebene organisiert - jede der
396 Gemeinden ist ihre eigene untere Denkmalbehoerde, der Kreis ist nur
Aufsichts-/Beratungsinstanz fuer kleinere Gemeinden - und alle 374
betroffenen Gemeinden bereits korrekt einzeln abgedeckt waren, wieder
kein echter Fund). Die einzige echte Luecke: **Neustadt an der
Weinstrasse** (kreisfreie Stadt, Rheinland-Pfalz) hatte ueberhaupt
keine DENKMALSCHUTZ-Regel. Gefixt mit
`seed_denkmalschutz_neustadt_weinstrasse.py` (1 Regel, Quelle: die
amtliche, aktuelle Liste der unteren Denkmalschutzbehoerden der
Generaldirektion Kulturelles Erbe Rheinland-Pfalz, gdke.rlp.de, per
Live-Browser-Abruf verifiziert).

## 24. Abgleich Erschließungsbeiträge: generische vs. präzise Regeln nach Merge (Hessen/NRW/Saarland)

Eine parallele Session hatte, unabhängig von Kapitel 22, für Teile von
Hessen (8 Gemeinden), Nordrhein-Westfalen (64 Gemeinden) und dem
Saarland (alle 52 Gemeinden) je Gemeinde einzeln das konkrete
Bauamt/die Bauverwaltung bzw. einen Eigenbetrieb recherchiert und
wörtlich zitiert (`seed_erschliessung_{hessen,nrw,saarland}.py`), statt
wie Kapitel 22 pauschal nur „§ 127 Abs. 1 BauGB" und eine generische
„Gemeindeverwaltung (Erschließungsbeiträge)" zu hinterlegen. Nach dem
Merge dieser Session (civeloq/authority-data-quality, commit 9ca366b)
standen damit für dieselben 124 AGS zwei fachlich richtige, aber
unterschiedlich präzise Regelsätze nebeneinander: die generische
Sammelregel war bereits produktiv in der echten DB angewendet
(Hessen 421/421, NRW 396/396, Saarland 52/52 – vollständige Abdeckung),
die präziseren Skripte lagen dagegen nur als Code vor und wurden nie
ausgeführt.

Analog zum bereits früher durchgeführten Abgleich für die Stadtstaaten
(Berlin/Bremen/Bremerhaven/Hamburg, `reconcile_erschliessung_stadtstaaten.py`,
commit 4adbcc4 – dort ersetzte die je Bezirksamt/Amt recherchierte
Fassung die pauschale Sammelregel) wurde ein neues Abgleichsskript
`reconcile_erschliessung_hessen_nrw_saarland.py` gebaut: es importiert
`ENTRIES`/`GEMEINDEN` direkt aus den drei präzisen Skripten (keine
Datenduplizierung), staged jeden Eintrag über
`JurisdictionStagingService.stage_entry()` und gibt ihn anschließend
**bewusst auch bei einem `CONTRADICTS_VERIFIED`-Konflikt** frei (nicht
nur bei `NEW`, wie es die präzisen Skripte selbst täten) – genau dieser
Konfliktfall war für alle 124 AGS erwartet, weil die generische Regel
für jede von ihnen bereits als VERIFIED aktiv war.
`approve_entry()` setzt dabei automatisch `valid_to` auf der alten
generischen Regel (Historie bleibt erhalten, kein Datenverlust, siehe
`app/services/jurisdiction_staging.py` Zeile ~228–245); AGS, die nur in
der generischen Kampagne vorkommen (der Großteil von Hessen/NRW), bleiben
unverändert – dafür existiert keine bessere Alternative.

Ablauf: Dry-Run gegen eine Kopie der echten SQLite-Dev-DB (124/124
Einträge, ausnahmslos `CONTRADICTS_VERIFIED`, keine unerwarteten
`DUPLICATE_EXACT`), danach Backup der echten DB
(`authority_matching.db.bak_pre_erschliessung_reconcile_hessen_nrw_saarland_<Zeitstempel>`),
danach derselbe Lauf gegen die echte DB. Ergebnis: **124 generische
Regeln durch die präziseren Einzelrecherche-Regeln abgelöst** – Hessen
8 (alle VERIFIED), NRW 64 (48 VERIFIED / 16 AUTO_IMPORTED, gestaffelt
nach tatsächlicher Beleglage), Saarland 52 (19 VERIFIED / 33
AUTO_IMPORTED). Die bundesweite ERSCHLIESSUNG-Abdeckung bleibt
unverändert bei 10749 von 10749 Gemeinden (100 %) – dies ist eine reine
Qualitätsverbesserung (benannte Fachbehörde statt pauschaler
„Gemeindeverwaltung", ehrliche `verification_status`-Differenzierung
bei NRW/Saarland), keine Abdeckungsänderung. `flake8 app/` und die
volle Testsuite blieben grün.

*Nachtrag:* der Code dieser Abgleichs-Session lag zunaechst auf einem
separaten Branch (`claude/silly-noyce-994922`) und wurde per
`git merge` in `civeloq/authority-data-quality` nachgezogen (Commit
afb0558, ein Konflikt in diesem Dokument durch Beibehaltung beider
Kapitel geloest). Ein Dry-Run des Abgleichsskripts gegen die
Haupt-Checkout-DB ergab fuer alle 124 Eintraege `DUPLICATE_EXACT` -
die DB-Aenderung war bereits vorher direkt uebernommen worden, keine
weitere Anwendung noetig.
