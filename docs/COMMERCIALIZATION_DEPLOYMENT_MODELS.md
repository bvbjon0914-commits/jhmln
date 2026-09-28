# Kommerzialisierung: Betriebsmodell-Vergleich (Entscheidungsgrundlage)

**Stand:** 25.09.2026 — Ergänzung zum Auditbericht.

**Ausdrücklicher Rahmen dieses Dokuments:** Es wird **keine Empfehlung für eine sofortige Umsetzung** ausgesprochen und **keine `tenant_id`-Umstellung im Code vorgenommen**. Der Auftrag war explizit, vor einer solchen Grundsatzentscheidung zwei realistische Betriebsmodelle gegenüberzustellen. Diese Entscheidung sollte von Produktverantwortlichen gemeinsam mit IT, Vertrieb und ggf. Rechtsabteilung getroffen werden, nicht einseitig technisch vorweggenommen werden.

---

## Ausgangslage (Ist-Zustand, siehe Auditbericht)

Civeloq ist heute **vollständig Single-Tenant**: keine der 14 Datenbanktabellen enthält eine Mandanten-Spalte, ein Service (Render) bedient eine Datenbank (Neon), Konfiguration (Absenderidentität, Aktenzeichen-Präfix "VNV-") ist teilweise hartcodiert auf einen Kunden. Für **jedes** der beiden unten diskutierten Modelle ist der derzeitige Stand der Ausgangspunkt — beide erfordern Arbeit, aber unterschiedlich viel und unterschiedlich verteilt.

---

## Modell A: Getrennte Instanz je Kunde

Jeder Kunde bekommt eine eigene, vollständig separate Bereitstellung: eigener Render-Service, eigene Neon-Datenbank, eigene Umgebungsvariablen (eigene Passwörter, eigene Mailgun-Domain, eigene Absenderidentität).

### Vorteile
- **Datenisolation ist strukturell garantiert**, nicht durch Anwendungscode erzwungen — kein Query kann versehentlich Daten eines anderen Kunden zurückgeben, weil es die Daten des anderen Kunden in dieser Instanz schlicht nicht gibt.
- **Kein Code-Umbau am Datenmodell nötig.** Der heutige Single-Tenant-Code kann nahezu unverändert je Kunde dupliziert werden — passt zur Vorgabe "kein Rewrite".
- **Individuelle Konfiguration pro Kunde** (Absenderidentität, Aktenzeichen-Präfix, eigene Auskunftsarten/Vorlagen falls gewünscht) ist automatisch möglich, da jede Instanz ohnehin unabhängig konfiguriert wird.
- Ein fehlerhaftes Update kann kundenweise ausgerollt werden (Canary), ein Fehler bei einem Kunden betrifft nicht automatisch alle anderen.

### Nachteile
- **Betriebsaufwand skaliert linear mit der Kundenzahl**: jede Instanz braucht eigenes Hosting, eigenes Monitoring, eigene Backups, eigene Migrationen (`alembic upgrade head` muss pro Instanz ausgeführt werden).
- **Keine geteilte, wachsende Behörden-/Zuständigkeitsdatenbank** über Kunden hinweg — die heute schon vorhandenen 16.290 Zuständigkeitsregeln müssten je Instanz gepflegt oder aufwendig synchronisiert werden, was den heutigen strategischen Wert der zentralen Datenbank pro Kunde neu aufbaut statt ihn zu teilen.
- Provisionierung eines neuen Kunden erfordert Infrastruktur-Automatisierung (IaC), die heute nicht existiert (nur eine einzelne `render.yaml`).
- Höhere Grenzkosten pro zusätzlichem Kunden (jede Instanz kostet Hosting unabhängig von der tatsächlichen Auslastung).

### Wann sinnvoll
- Wenige, große Kunden mit hohen Compliance-/Datenisolations-Anforderungen (z. B. Konzerne, die eine physische Trennung vertraglich verlangen).
- Frühe Vermarktungsphase mit wenigen Piloten, bei der Betriebsaufwand pro Kunde noch tragbar ist.

---

## Modell B: Gemeinsame Plattform mit strikter Mandantentrennung

Ein Service, eine Datenbank, alle Kunden teilen sich die Infrastruktur; jede Tabelle bekommt eine `tenant_id`, jede Query wird um einen Mandantenfilter erweitert, Datei-/Blob-Ablagen werden mandantengetrennt.

### Vorteile
- **Bessere Skaleneffekte**: ein Betrieb, ein Deployment, eine Migration bedient alle Kunden — Grenzkosten pro zusätzlichem Kunden sinken mit der Kundenzahl.
- **Eine gemeinsame Basis-Datenbank denkbar**: die bundesweite Zuständigkeitsmatrix (Behörden, AGS-Zuordnungen) könnte als geteilte, mandantenübergreifende Referenzdatenbank gepflegt werden, während nur objektbezogene Daten (Gebäude, Anfragen, Antworten) je Mandant getrennt sind — das wäre ein echter Netzwerkeffekt, den Modell A nicht bietet.
- Ein Feature-Update erreicht alle Kunden gleichzeitig, ohne pro Instanz ausgerollt werden zu müssen.
- Zentrales Monitoring/Betrieb statt N-facher Betriebsaufwand.

### Nachteile
- **Grundlegendes Redesign, kein inkrementeller Schritt** (siehe Auditbericht): `tenant_id` auf jeder Tabelle, jede der heute ungefilterten Queries (bestätigt an mehreren Beispiel-Endpunkten) muss angepasst werden, Datei-/Blob-Speicher (heute ein gemeinsames Verzeichnis bzw. DB-Bytea ohne Mandantenschlüssel) muss umgebaut werden.
- **Isolationsfehler sind Anwendungsfehler, keine strukturelle Unmöglichkeit** — ein vergessener Mandantenfilter in einer einzigen Query kann Daten eines Kunden einem anderen zeigen. Erfordert danach systematische Tests (z. B. ein dedizierter Penetrationstest auf Mandantentrennung, wie im Auditbericht als Freigabekriterium genannt) und durchgängige Code-Disziplin (z. B. über eine ORM-Middleware, die den Mandantenfilter automatisch erzwingt, statt ihn an jeder Stelle manuell zu wiederholen).
- Ein Ausfall/Bug betrifft potenziell **alle** Kunden gleichzeitig (kein "Blast Radius"-Vorteil wie bei getrennten Instanzen).
- Rechtlich ggf. anspruchsvoller: manche Kunden könnten eine physische Datentrennung vertraglich fordern, die eine geteilte Datenbank grundsätzlich ausschließt.

### Wann sinnvoll
- Viele, eher kleinere/mittlere Kunden, bei denen Betriebskosten pro Kunde kritisch für die Wirtschaftlichkeit sind.
- Ein Geschäftsmodell, das gerade von der geteilten, wachsenden Behörden-Datenbank als Netzwerkeffekt lebt.

---

## Kriterien-Gegenüberstellung

| Kriterium | Modell A (Instanz je Kunde) | Modell B (geteilte Plattform) |
|---|---|---|
| Integrationsaufwand (Umsetzung) | Gering (kaum Codeänderung) | Hoch (grundlegendes Redesign) |
| Datenschutz/Isolation | Strukturell garantiert | Muss durch Code + Tests erzwungen werden |
| Betriebskosten bei wenigen Kunden | Vertretbar | Tendenziell overengineered |
| Betriebskosten bei vielen Kunden | Steigen linear, ungünstig | Skaliert deutlich besser |
| Updates/Migrationen | Pro Instanz wiederholen | Einmal für alle |
| Geteilte Behörden-Datenbank als Netzwerkeffekt | Nicht ohne Zusatzaufwand möglich | Möglich, aber selbst ein Teilprojekt |
| Individuelle Kundenkonfiguration | Automatisch gegeben | Muss explizit gebaut werden |
| Risiko bei Fehlern/Ausfall | Pro Kunde isoliert | Potenziell alle Kunden betroffen |
| Vertragliche Sonderanforderungen (physische Trennung) | Erfüllbar | Nicht erfüllbar ohne Ausnahme |

---

## Ein möglicher, hier NICHT beschlossener Mittelweg

Denkbar (nur als Diskussionsanstoß, nicht als Empfehlung): **Start mit Modell A** für die ersten Pilotkunden, da es zur "kein Rewrite"-Vorgabe passt und schnell umsetzbar ist, mit einer **bewussten Entscheidung, den Wechsel zu Modell B erst zu vollziehen, wenn die Kundenzahl den Betriebsaufwand von Modell A unwirtschaftlich macht**. Das verschiebt die teure Grundlagenentscheidung, ohne sie zu verhindern — verlangt aber Disziplin, damit kundenspezifische Anpassungen in Modell A nicht so weit auseinanderlaufen, dass eine spätere Konsolidierung in Modell B noch schwerer wird.

---

## Für die Entscheidung benötigte Informationen (nicht Teil dieses Dokuments)

- Erwartete Kundenzahl in den ersten 12–24 Monaten (bestimmt, wie schnell Modell A unwirtschaftlich würde).
- Ob vertragliche/regulatorische Anforderungen bestimmter Zielkunden physische Datentrennung verlangen.
- Verfügbares Entwicklungsbudget für ein Mandantenfähigkeits-Redesign (Modell B) versus Infrastruktur-Automatisierung (Modell A).
- Strategische Bedeutung einer geteilten, kundenübergreifenden Behörden-Datenbank für das Geschäftsmodell.
