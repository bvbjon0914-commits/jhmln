# Kontaktprüfung mit Civeloq und Kontaktbot 2.6

Neue Rechercheergebnisse werden zunächst als eigene Vorschläge gespeichert.
Der bisherige Versandresolver erhält einen Kontakt erst nach einer bewussten
Prüfentscheidung. Die Tabelle `contact_review_proposals` ergänzt das Schema;
die Migration `b8d2f6e47a10` verändert keine bestehenden Behörden, Regeln oder
Kontaktkanäle.

## Arbeitsablauf

1. Datenqualitäts-Export in Civeloq herunterladen. Im Blatt „Fachkontakte
   prüfen“ steht nun auch die stabile Behörden-ID.
2. Export im Kontaktbot 2.6 recherchieren. Er erstellt zusätzlich
   `civeloq_pruefung.json`. Größere Ergebnisse werden in nummerierte Dateien
   unter 8 MB aufgeteilt; jede Datei einzeln laden.
3. Im Haupt-Account **Verwaltung → Kontaktprüfung → Prüfdatei laden** wählen.
4. Behörde, Auskunftsart, Bestandskontakt und Originalausschnitt vergleichen.
   Quelle öffnen und die ausdrückliche Zuständigkeit bzw. den Einreichungsweg
   prüfen. „Bestätigen“ erfordert eine separate Bestätigung dieser Prüfung.
5. „Ablehnen“ schließt den Vorschlag. „Weitere Recherche“ merkt ihn vor.
   Über „Nachrecherche exportieren“ entsteht ein neuer Excel-Bedarf für den
   Bot. Dieser Schritt startet keinen serverseitigen Crawler.

Die Prüfung unterstützt E-Mail und Portal-/Formularwege. Die Bestätigung
eines Portals aktiviert keinen E-Mail-Versand. Ein persönliches oder zentrales
Postfach kann nach ausdrücklich belegter Zuordnung bestätigt werden.
„Bevorzugen“ gilt nur für dieselbe Behörde, Auskunftsart und Kontaktart.

## Sicherung des Bestands

- Der Prüfimport erzeugt ausschließlich Vorschläge. Behörden, Adressen,
  Zuständigkeitsregeln und vorhandene geprüfte Kontaktkanäle bleiben erhalten.
- Jede Kombination wird über Behörden-ID und unveränderten Namen/Ort geprüft;
  ohne ID muss Name/Ort eindeutig sein. Auskunftsart und AGS benötigen eine
  vorhandene aktive, zeitlich gültige Zuständigkeitsregel.
- Ein zweiter Import derselben Quelle erzeugt keine neuen Vorschläge und öffnet
  abgelehnte oder bestätigte Vorschläge nicht erneut.
- Importdateien dürfen höchstens 8 MB und 2.000 Vorschläge enthalten. Eine
  Datei kann keine automatische Verifikation oder Bevorzugung anfordern.
- Nur der Haupt-Account kann die Prüfansicht und die API verwenden. Entscheidungen
  sind versioniert; veraltete oder gleichzeitige Entscheidungen werden mit 409
  abgewiesen. Ein Verlauf dokumentiert Zeitpunkt, Prüfer und Entscheidung.
- Die Freigabe prüft die aktuelle Bestandszuordnung erneut. PostgreSQL sperrt
  die Behördenzeile während des Abgleichs vorhandener Kontaktkanäle.
- Behörden mit Prüfbelegen werden bei automatischer Duplikatbereinigung
  ausgespart und lassen sich nicht versehentlich unter Verlust ihrer Belege löschen.

## API

Alle Routen sind auch unter `/api/v1` verfügbar:

| Route | Funktion |
|---|---|
| `POST /api/contact-reviews/import` | Multipart-Datei `file`, JSON aus Bot 2.6 |
| `GET /api/contact-reviews` | Paginierte Vorschläge, Status-/Typ-/Textfilter |
| `POST /api/contact-reviews/{id}/decision` | CONFIRM, REJECT oder RESEARCH mit aktueller Version |
| `GET /api/contact-reviews/export-needs` | Excel-Bedarf für vorgemerkte Nachrecherchen |

Der Vorschlagsschlüssel berücksichtigt Behörde, Auskunftsart, Kontaktart,
Kontaktwert, Quellen-URL und Originalhash. Die Quellenausschnitte sind
Recherchebelege; die menschliche Prüfung muss die aktuelle Originalquelle
einbeziehen. Der Server ruft keine beliebigen URLs aus Importdateien ab.

## Prüfung der Implementierung

Die Backend-Tests prüfen den echten HTTP-Import, Rollenrechte, Größenlimits,
Bestandsbezug, unveränderte Stammdaten, fehlende Quellenbestätigung,
Versionskonflikte, Nachrecherche-Export, Portalbestätigung und erneuten Import.
Alembic-Tests prüfen Upgrade, Downgrade und erneutes Upgrade gegen temporäre
SQLite-Datenbanken. Die PostgreSQL-Tabellendefinition wird zusätzlich offline
aus der Migration erzeugt. Produktive Datenbankänderungen erfolgen bei dieser
Vorbereitung nicht.

Frontend-Typecheck und Produktionsbuild prüfen die neue Ansicht. Eine visuelle
Browserprüfung des lokalen Servers war in der Ausführungsumgebung nicht möglich,
weil der bereitgestellte Browser den lokalen Server nicht erreichen konnte.
Die Oberfläche sollte im Review insbesondere bei schmalen Bildschirmbreiten
und mit langen Quellen-URLs betrachtet werden.
