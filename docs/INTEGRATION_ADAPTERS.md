# Integrationsverträge: ERP/SAP, DMS/SharePoint, Microsoft 365/Outlook, GIS

**Stand:** 25.09.2026 — Ergänzung zum Auditbericht (Priorität 3: Integrationsvorbereitung).

**Wichtiger Rahmen:** Für keines der vier Systeme liegen konkrete Schnittstellenvorgaben, ein Pilotzugang oder eine Grundsatzentscheidung vor, welches konkrete Produkt (z. B. welches SAP-Modul, welche DMS-Instanz) angebunden werden soll. Dieses Dokument beschreibt deshalb **Adapterverträge auf Ebene der Datenflüsse und Schnittstellenform**, nicht eine konkrete Implementierung. Es wurde **kein Code für eine dieser vier Anbindungen geschrieben** — nur die in den vorherigen Commits umgesetzten neutralen Grundlagen (stabile externe Referenzen, `/api/v1`, API-Key-Zugang, konsistente Fehlerantworten) sind bereits vorhanden und werden hier als Ausgangspunkt referenziert.

---

## 1. ERP / Objektbestandssystem (z. B. SAP)

### Rolle im Gesamtbild
Das ERP/Objektbestandssystem wäre das **führende System für Objekt-Stammdaten** (Adresse, interne Kennung, Objektname). Civeloq würde von dort importieren, nicht umgekehrt — Civeloq erzeugt keine neuen "offiziellen" Objektdaten, es reichert sie um Behörden-Zuständigkeiten an.

### Adaptervertrag (Vorschlag)
| Aspekt | Vorschlag | Begründung / Bezug zum bestehenden Code |
|---|---|---|
| Richtung | ERP → Civeloq (Objektstammdaten), einseitig | Civeloq hat kein Konzept eines "zurückschreibenden" Objektdaten-Updates |
| Format | CSV/Excel-Batch (wiederverwendet den bestehenden Import) oder ein periodischer Datei-Export aus dem ERP | `ImportService.import_buildings()` existiert bereits, robust für mehrere tausend Zeilen |
| Objekt-Identität | `Building.internal_reference` = die ERP-eigene Objekt-ID; `Building.source_system` = z. B. `"SAP"` | Beide Felder wurden für genau diesen Zweck ergänzt (siehe Commit "Stabile externe Referenzen") |
| Wiederholbarkeit | Re-Import mit identischer `internal_reference` wird als Duplikat erkannt, nicht dupliziert; ohne Referenz greift der Adress-Fallback | Bereits umgesetzt und getestet |
| Zugriff | `/api/v1/import/buildings` mit `X-API-Key`-Header statt Login-Cookie | API-Key-Zugang wurde für genau diesen Fall ergänzt |
| Fehlerrückmeldung | `ImportSummary` (importiert/aktualisiert/Duplikate/zur Prüfung/Fehler je Zeile) | Bereits vorhanden, unverändert nutzbar |

### Offene Fragen (an IT/Fachbereich)
- Welches SAP-Modul/welche Objekt-ID gilt als kanonisch (Liegenschaftsverwaltung, Instandhaltung, etc.)?
- Batch-Export (Datei) oder Echtzeit-API (SAP OData/RFC)? Letzteres wäre ein separates, deutlich größeres Vorhaben (SAP-seitige Berechtigungen, Verbindungstyp).
- Soll ein Objekt, das im ERP gelöscht/deaktiviert wird, in Civeloq automatisch inaktiv gesetzt werden? (Heute: keine Lösch-Synchronisation vorgesehen.)
- Frequenz (täglich? wöchentlich? ereignisgesteuert?).

---

## 2. DMS / SharePoint

### Rolle im Gesamtbild
Ablage der generierten Anschreiben (`.docx`) und ggf. der eingegangenen Behördenantworten (`.pdf`) an einem Ort, der dem übrigen Unternehmen vertraut ist — statt im heutigen, bei Render flüchtigen Dateisystem bzw. als Datenbank-Blob.

### Adaptervertrag (Vorschlag)
| Aspekt | Vorschlag | Begründung / Bezug zum bestehenden Code |
|---|---|---|
| Richtung | Civeloq → DMS, einseitig (Ablage) | Civeloq bliebe Ersteller, DMS reines Archiv |
| Auslösepunkt | Nach erfolgreicher Dokumentgenerierung (`DocumentGenerationService.generate_document`) bzw. nach Antworteingang (`RequestItemProgress`) | Beide Stellen sind heute bereits klar abgegrenzte, testbare Funktionen |
| Ablagestruktur | Vorschlag: ein Ordner/eine Bibliothek je Aktenzeichen (`RequestItemReference.aktenzeichen`) | Aktenzeichen sind bereits eindeutig und menschenlesbar |
| Schnittstelle | Microsoft Graph API (`/sites/{site-id}/drive/items:/path:/content`) für SharePoint, oder ein generisches WebDAV/S3-kompatibles Ziel für ein anderes DMS | Kein Code hierfür vorhanden — bewusst nicht spekulativ implementiert |
| Rückkanal | Optional: DMS-Dokument-ID in einem neuen Feld an `RequestItemReference` oder `RequestItemProgress` speichern | Wäre eine kleine, additive Migration analog zu `message_id`/`source_system` |

### Offene Fragen
- Welches DMS ist tatsächlich im Einsatz (SharePoint Online, ein On-Prem-DMS, etwas anderes)? Ohne diese Angabe ist auch die Authentifizierungsart (App-Registrierung in Azure AD vs. Service-Account vs. API-Key) nicht festlegbar.
- Dürfen/sollen Behördenantworten (potenziell personenbezogene Daten, siehe Auditbericht Abschnitt Datenschutz) überhaupt in ein unternehmensweit zugängliches DMS abgelegt werden, oder nur in einen eingeschränkten Bereich?
- Wer erhält Lesezugriff auf die abgelegten Dokumente (nur Sachbearbeitung, oder unternehmensweit)?

---

## 3. Microsoft 365 / Outlook

### Rolle im Gesamtbild
Ersatz für den heutigen `mailto:`-Workaround (Wizard-Schritt 4: "E-Mail" öffnet einen vorausgefüllten `mailto:`-Link, der Nutzer muss die Datei manuell anhängen) durch echten Direktversand aus der Anwendung.

### Adaptervertrag (Vorschlag)
| Aspekt | Vorschlag | Begründung / Bezug zum bestehenden Code |
|---|---|---|
| Richtung | Civeloq → Outlook/Exchange, einseitig (Versand) | Kein Empfang über Outlook vorgesehen — Posteingang läuft bereits separat über Mailgun |
| Schnittstelle | Microsoft Graph API `/users/{id}/sendMail` mit Anhang, ODER weiterhin Mailgun (bereits vorhanden) als einheitlicher Versandweg für alle E-Mails | Zwei mögliche Wege — die Entscheidung "ein Versandweg (Mailgun) für alles" vs. "Outlook für Direktversand, Mailgun nur für automatisierten Bündel-Versand" ist eine Produktentscheidung, keine rein technische |
| Berechtigung | Delegierte Graph-Berechtigung `Mail.Send`, App-Registrierung in Azure AD | Kein Code hierfür vorhanden |
| Nachvollziehbarkeit | Aktenzeichen im Betreff (bereits Konvention bei Mailgun-Versand) beibehalten, damit eine Antwort weiterhin zuordenbar bleibt | `AKTENZEICHEN_RE`-Erkennung in `mailbox_inbound.py` bliebe unverändert nutzbar |

### Offene Fragen
- Soll der Versand über die individuelle Outlook-Identität der jeweiligen Sachbearbeitung laufen (persönlicher Absender) oder über ein zentrales Funktionspostfach (wie heute bei Mailgun)? Das ist eine organisatorische Entscheidung mit Compliance-Bezug (wer haftet/antwortet im Namen wessen).
- Falls Outlook zusätzlich zu Mailgun eingeführt wird: wie wird verhindert, dass ein- und dieselbe Anfrage über zwei unterschiedliche Wege doppelt versendet wird?

---

## 4. GIS (WFS/WMS, amtliche Geodaten)

### Rolle im Gesamtbild
Automatisierte Vorprüfung bestimmter Auskunftsarten (v. a. Hochwasserschutz, Wasserschutz) gegen amtliche Geodaten, als Ergänzung oder Vorstufe zur heutigen reinen Behördenanfrage. **Wichtig:** Der Katalog möglicher Quellen existiert bereits im Code (`DataSource`/`DataSourceRouting`, 34 Einträge), ist aber nachweislich mit keiner aktiven Logik verbunden (siehe Auditbericht).

### Adaptervertrag (Vorschlag)
| Aspekt | Vorschlag | Begründung / Bezug zum bestehenden Code |
|---|---|---|
| Richtung | Civeloq → amtliche WFS/WMS-Dienste, lesend | Rein informativ, keine Rückschreibung |
| Auswahl der Quelle | Über `DataSourceRouting` (Bundesland + Kategorie → `primary_source_id`/`fallback_source_id`) | Tabelle existiert bereits, nur ungenutzt |
| Abfrage | WFS `GetFeature`-Anfrage mit der Gebäude-Koordinate (bereits vorhanden über Geocoding) als räumlichem Filter | Geocoding-Infrastruktur (`geocoding.py`) ist vorhanden, aber für Punkt-Abfrage gegen Nominatim, nicht für WFS-Flächenabfragen — ein WFS-Client existiert nicht |
| Ergebnisverwendung | Vorschlag: als zusätzliches, klar gekennzeichnetes "Vorprüfungsergebnis" neben dem eigentlichen Behörden-Matching, NICHT als Ersatz dafür, solange keine rechtliche Bewertung vorliegt, ob eine automatisierte Geodaten-Prüfung eine Behördenauskunft ersetzen darf | Entspricht dem "nicht raten"-Grundprinzip der bestehenden Matching-Engine |

### Offene Fragen
- Ersetzt eine automatisierte Geodaten-Vorprüfung rechtlich eine Behördenanfrage, oder ergänzt sie diese nur (Nachweispflicht)? Das ist eine juristische Frage, keine technische.
- Datenqualität/Aktualität der 34 katalogisierten Quellen wurde nicht geprüft (nur ihre Existenz als Katalogeinträge) — vor einer Anbindung müsste jede Quelle einzeln auf Verfügbarkeit/Format geprüft werden.
- Welche Auskunftsart(en) zuerst pilotieren? (Vorschlag im Auditbericht: eine einzelne Quelle pilotweise anbinden, um den Aufwand für die übrigen realistisch einzuschätzen, statt alle 34 auf einmal.)

---

## Gemeinsame, bereits gelegte Grundlage für alle vier Anbindungen

Unabhängig vom konkreten Zielsystem stehen jetzt bereit:
- **`/api/v1`** als versionierte, dokumentierte Basis (siehe `main.py`)
- **API-Key-Zugang** (`X-API-Key`-Header) getrennt vom menschlichen Login (siehe `app/services/auth.py`)
- **Konsistente Fehlerantworten** mit `request_id` zur Diagnose (siehe globaler Exception-Handler in `main.py`)
- **Stabile externe Referenzen** (`Building.internal_reference` + `Building.source_system`)
- **Wiederholbare Importe ohne Dubletten** (Adress-Fallback in `import_buildings`)

Diese fünf Punkte wurden bewusst systemneutral gehalten, damit sie für **jede** der vier oben genannten Anbindungen (und für noch nicht benannte künftige Systeme) wiederverwendbar sind, ohne dass eine der vier Integrationen heute schon vorweggenommen oder bevorzugt wurde.
