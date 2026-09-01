# Authority Matching System – Projektstatus

**Projekt Start:** 2026-08-26  
**Aktueller Stand:** Phase 1 Abschluss ✅  

---

## 🎯 Projektübersicht

**Ziel:** Automatische Ermittlung zuständiger Behörden für Gebäudeadressen mit automatisierter Dokumentgenerierung

**Teknologie-Stack:**
- **Backend:** Python, FastAPI, SQLAlchemy
- **Datenbank:** SQLite (MVP), PostgreSQL (Production)
- **Dokumentgenerierung:** python-docx, docxtpl
- **Frontend:** React, TypeScript (später)

---

## ✅ Phase 1: Datenmodell & Architektur – ABGESCHLOSSEN

### Was wurde erstellt:

#### 📋 Datenmodelle (ORM mit SQLAlchemy)

| Modell | Datei | Status | Notizen |
|--------|-------|--------|---------|
| Building | `models/building.py` | ✅ | Gebäude mit Adressdaten, AGS |
| RequestType | `models/request_type.py` | ✅ | Auskunftsarten (Grundbuch, Bauakten, etc.) |
| Authority | `models/authority.py` | ✅ | Behörden-Verzeichnis |
| Jurisdiction | `models/jurisdiction.py` | ✅ | **Zentrale** Zuständigkeitsmatrix |
| Request | `models/request.py` | ✅ | Anfrage-Historie |
| RequestItem | `models/request.py` | ✅ | Einzelne Zuständigkeiten pro Anfrage |

#### 🏗️ Backend-Struktur

```
backend/
├── app/
│   ├── models/          ✅ ORM-Modelle
│   ├── schemas/         ✅ Pydantic Schemas
│   ├── database/        ✅ SQLAlchemy Engine
│   ├── services/        ⬜ (Phase 2+3)
│   ├── api/             ⬜ (Phase 4+)
│   ├── main.py          ✅ FastAPI App
│   └── ...
├── templates/           ⬜ (Phase 3)
├── generated/           ⬜ (Phase 3)
├── tests/               ⬜ (Phase 2)
├── requirements.txt     ✅
└── ...
```

#### 📚 Dokumentation

| Dokument | Status | Inhalt |
|----------|--------|--------|
| ARCHITECTURE.md | ✅ | Komplette Systemarchitektur, Datenbankschema, Datenflüsse |
| PHASE2_MATCHING_ENGINE.md | ✅ | Detaillierte Planung für Phase 2 |
| STATUS.md | ✅ | Dieses Dokument |

---

## 🔧 Phase 2: Matching-Engine – NÄCHSTE PHASE

### Was wird implementiert:

1. **AddressNormalizer Service**
   - Adressnormalisierung
   - Leerzeichen, Großschreibung, Umlaute
   - Hausnummer-Parsing
   - PLZ-Validierung

2. **JurisdictionMatchingService**
   - Hierarchisches Matching (7 Stufen)
   - Gebäude + Auskunftsart → Behörde
   - Handling von mehreren Matches
   - Nachvollziehbarkeit (reason-Field)

3. **Unit Tests** (mindestens 8 Test-Cases)
   - Eindeutige Zuständigkeit
   - Keine Zuständigkeit
   - Multiple Matches
   - Sonderregeln
   - Fallback-Logik
   - Multiple Auskunftsarten
   - Adressnormalisierung
   - Fehlende Daten

### Zeitschätzung: 1-2 Tage intensive Entwicklung

---

## 📊 Datenbankschema – ZUSAMMENFASSUNG

### Zentrale Tabellen

```
buildings (Gebäudedatenbank)
  ├─ building_id (PK)
  ├─ street, house_number, postal_code, city
  ├─ ags (AGS-Schlüssel)
  └─ ...

request_types (Auskunftsarten)
  ├─ request_type_id (PK)
  ├─ code (GRUNDBUCH, BAUAKTEN, etc.)
  ├─ template_filename
  └─ ...

authorities (Behörden)
  ├─ authority_id (PK)
  ├─ authority_name, department_name
  ├─ street, postal_code, city
  ├─ email, phone, website
  └─ ...

jurisdictions (ZENTRAL: Zuständigkeitsmatrix)
  ├─ jurisdiction_id (PK)
  ├─ request_type_id (FK)
  ├─ authority_id (FK)
  ├─ ags, street, district, postal_code
  ├─ priority, matching_level
  ├─ valid_from, valid_to
  └─ ... (Datenqualitäts-Metadaten)

requests (Anfrage-Historie)
  ├─ request_id (PK)
  ├─ building_id (FK)
  ├─ created_by, created_at
  ├─ status
  └─ items (relationship)

request_items (Einzelne Zuständigkeitsanfrage)
  ├─ request_item_id (PK)
  ├─ request_id (FK)
  ├─ request_type_id (FK)
  ├─ authority_id (FK)
  ├─ matching_status, matching_level, confidence
  ├─ document_path, document_status
  └─ manually_changed (für Audit)
```

### Matching-Hierarchie (Priorität)

```
10 – STREET_NUMBER (Straße + Hausnummer)
20 – STREET (nur Straße)
30 – DISTRICT (Stadtteil/Bezirk)
40 – MUNICIPALITY (Gemeinde/AGS) ← STANDARD
50 – COUNTY (Landkreis)
60 – STATE (Bundesland)
70 – POSTAL_CODE (PLZ, Fallback)
```

---

## 🚀 Nächste Konkrete Schritte

### Sofort (heute/morgen):

1. ✅ **Phase 1 Datenmodelle fertig**
   - ✅ Alle ORM-Klassen
   - ✅ Pydantic Schemas
   - ✅ Database Engine

2. ⬜ **Phase 2 starten: AddressNormalizer**
   ```bash
   # Dateien erstellen:
   backend/app/services/address_normalizer.py
   backend/tests/test_address_normalizer.py
   ```

3. ⬜ **Testdaten generieren**
   ```bash
   backend/tests/fixtures.py
   backend/tests/seed_test_data.py
   ```

### Diese Woche:

4. ⬜ **JurisdictionMatchingService implementieren & testen**
   ```bash
   backend/app/services/jurisdiction_matcher.py
   backend/tests/test_jurisdiction_matcher.py
   ```

5. ⬜ **Alle 8 Unit Tests grün**

6. ⬜ **Manuelles Testen mit Testdaten**

### Folgende Woche:

7. ⬜ **Phase 3: DocumentGenerationService**

8. ⬜ **Phase 4: API-Endpoints**

9. ⬜ **Phase 5: Frontend (minimal)**

---

## 📋 Wichtige Designentscheidungen

### ✅ Zuständigkeitsmatrix (Jurisdictions)

**Prinzip:** Nicht direkt `Gebäude → Behörde`, sondern:

```
Gebäudeadresse
    ↓
Normalisierung
    ↓
AGS / Gebiet ermitteln
    ↓
Auskunftstyp wählen
    ↓
Zuständigkeitsmatrix abfragen
    ↓
Behörde ermitteln
```

**Vorteil:** Regeln sind zentral in der DB, nicht im Code!

### ✅ Matching-Hierarchie

**Prinzip:** Spezifische Regeln haben Vorrang vor allgemeinen.

- Straße + Hausnummer > Straße > Distrikt > AGS > Landkreis > Bundesland > PLZ

**Beispiel:**
```
Spezialstraße 5, Bochum
  ├─ Match auf STREET_NUMBER: "Spezialamt" (priority 10)
  ├─ Match auf MUNICIPALITY: "Standardamt" (priority 40)
  ├─ Winner: "Spezialamt" (spezifischer)
```

### ✅ Fehlerbehandlung

**Prinzip:** Lieber "REVIEW_REQUIRED" als falsch-positive Matches.

```
0 Treffer    → NO_MATCH
1 Treffer    → MATCHED (confidence: 1.0)
>1 Treffer   → MULTIPLE_MATCHES (confidence: 0.5) + Nutzerprompt
```

### ✅ Datenqualität

**Prinzip:** Nachvollziehbarkeit vor Automatismus.

Jede Zuständigkeitsregel hat:
- `source` (woher stammt die Regel?)
- `last_verified_at` (wann verifiziert?)
- `verified_by` (wer verifiziert?)

---

## 🎓 Lessons Learned & Best Practices

### Architektur

1. **Modulare Schichten-Struktur**
   - DB-Modelle getrennt von Business-Logic
   - Services getrennt von API
   - Schemas getrennt von Modellen

2. **Zentrale Datenbank für Regeln**
   - Keine Hard-Coded Zuständigkeitsregeln
   - Änderungen ohne Code-Änderung möglich

3. **Hierarchisches Matching**
   - Nicht nur PLZ-basiert
   - Granulare Kontrolle durch Prioritäten

### Datenbank

1. **Indizes auf häufige Abfragen**
   - `jurisdictions(request_type_id, ags, priority)`
   - `jurisdictions(request_type_id, street, priority)`
   - Performance auch bei Millionen Einträgen

2. **Zeitliche Gültigkeit**
   - `valid_from`, `valid_to` für Regel-Lebenszyklen
   - Automatische Ungültigkeitsprüfung

3. **Audit-Trail**
   - Requests & RequestItems für komplette Historie
   - `manually_changed` Flag für Nachvollziehbarkeit

---

## 📦 Projektstruktur (Aktuell)

```
authority-matching/
├── .git                    (Version Control)
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  ✅ FastAPI App
│   │   ├── models/
│   │   │   ├── __init__.py          ✅
│   │   │   ├── building.py          ✅
│   │   │   ├── request_type.py      ✅
│   │   │   ├── authority.py         ✅
│   │   │   ├── jurisdiction.py      ✅ (zentral)
│   │   │   └── request.py           ✅
│   │   ├── schemas/
│   │   │   └── __init__.py          ✅
│   │   ├── database/
│   │   │   ├── __init__.py          ✅
│   │   │   └── engine.py            ✅
│   │   ├── services/                ⬜ (Phase 2+3)
│   │   ├── api/                     ⬜ (Phase 4+)
│   │   └── utils/
│   ├── templates/                   ⬜ (Phase 3)
│   ├── generated/                   ⬜ (Phase 3)
│   ├── tests/                       ⬜ (Phase 2)
│   ├── requirements.txt             ✅
│   └── README.md                    ⬜
├── frontend/
│   └── src/                         ⬜ (Phase 4+)
├── docs/
│   ├── ARCHITECTURE.md              ✅
│   ├── PHASE2_MATCHING_ENGINE.md    ✅
│   └── ...
├── STATUS.md                        ✅
└── README.md                        ⬜
```

---

## 🔗 Dependencies

Alle notwendigen Python-Packages in `requirements.txt` definiert:
- FastAPI, Uvicorn
- SQLAlchemy, Alembic
- python-docx, docxtpl
- pandas, openpyxl
- pytest, httpx
- black, mypy, isort

---

## ⚠️ Bekannte Einschränkungen (MVP)

1. **Noch keine Geodaten-Integration**
   - AGS muss in Gebäude-DB vorhanden sein
   - Später: Über Geocoding-Service ergänzbar

2. **Noch keine E-Mail-Integration**
   - Dokumente werden nur generiert
   - Später: Automatischer E-Mail-Versand

3. **Noch kein Frontend**
   - Wird in Phase 4 implementiert
   - Vorerst: API-Tests über Swagger/FastAPI

4. **Noch keine Portfolio-Funktion**
   - Nur Einzelgebäude
   - Batch-Verarbeitung kommt später

---

## 🎯 Definition of Done – Ganzes Projekt

Das Projekt ist fertig, wenn:

```
USER ÖFFNET ANWENDUNG
    ↓
BENUTZER SUCHT: Musterstraße 12, 44787 Bochum
    ↓
BENUTZER WÄHLT: ✓ Grundbuch, ✓ Bauakten, ✓ Altlasten
    ↓
BENUTZER KLICKT: "Zuständige Ämter ermitteln"
    ↓
SYSTEM ZEIGT: 3 nachvollziehbare Zuständigkeiten
    ↓
BENUTZER PRÜFT ERGEBNISSE
    ↓
BENUTZER KLICKT: "Schreiben generieren"
    ↓
SYSTEM ERSTELLT:
    100234_GRUNDBUCH_Bochum_20260826.docx
    100234_BAUAKTEN_Bochum_20260826.docx
    100234_ALTLASTEN_Bochum_20260826.docx
    ↓
BENUTZER LÄDT DOKUMENTE HERUNTER
    ↓
✅ ALLE DATEN KORREKT IN DOKUMENTEN EINGESETZT
```

---

## 📞 Support & Fragen

Bei Fragen zur Architektur:
→ Siehe `ARCHITECTURE.md` (Kapitel 2-9)

Bei Fragen zur Phase 2:
→ Siehe `PHASE2_MATCHING_ENGINE.md`

---

**Nächste große Meile:** Phase 2 Matching-Engine  
**Geschätzte Dauer:** 2-3 Tage  
**Kritischer Erfolg-Faktor:** Tests müssen ALLE grün sein

---

**Status Update: 2026-08-26**  
Datenmodelle & Architektur: ✅ KOMPLETT  
Phase 2 Planung: ✅ KOMPLETT  
Bereit für Implementierung: ✅ JA
