# 🏛️ Authority Matching System

**Automatische Ermittlung zuständiger Behörden für Gebäudeadressen mit automatisierter Dokumentgenerierung**

---

## 📋 Übersicht

Dieses System ermöglicht es:

1. **Gebäudeadressen** aus einer Datenbank zu suchen
2. **Auskunftsarten** auszuwählen (Grundbuch, Bauakten, Altlasten, etc.)
3. **Zuständige Behörden** automatisch zu ermitteln
4. **Anschreiben als Word-Dokumente** zu generieren
5. **Dokumente** einzeln oder gesammelt herunterzuladen

Das System funktioniert perspektivisch deutschlandweit und mit sehr vielen Gebäuden.

---

## 🎯 Status & Roadmap

| Phase | Beschreibung | Status | ETA |
|-------|-------------|--------|-----|
| 1 | Datenmodell & Architektur | ✅ | 2026-08-26 |
| 2 | Matching-Engine | ⬜ | 2026-08-28 |
| 3 | Dokumentgenerator | ⬜ | 2026-08-30 |
| 4 | API Endpoints | ⬜ | 2026-09-02 |
| 5 | Frontend (React) | ⬜ | 2026-09-05 |
| 6 | Import & History | ⬜ | 2026-09-08 |

Detaillierte Status: Siehe [`STATUS.md`](STATUS.md)

---

## 🚀 Quick Start

### Voraussetzungen

- Python 3.10+
- Git

### Installation (Backend)

```bash
# Repository klonen
git clone <repo-url>
cd authority-matching/backend

# Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  (Windows)

# Dependencies
pip install -r requirements.txt

# Datenbank initialisieren
python -c "from app.database import init_db; init_db()"

# FastAPI starten
uvicorn app.main:app --reload
```

Die API ist dann unter http://localhost:8000 erreichbar.

API-Dokumentation: http://localhost:8000/docs

---

## 📚 Dokumentation

### Für Architekten & Entwickler

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** – Komplette Systemarchitektur
  - Datenbankschema
  - Matching-Algorithmus
  - Datenflüsse
  - Skalierbarkeit

- **[STATUS.md](STATUS.md)** – Aktueller Projektstatus
  - Was ist fertig
  - Was kommt als nächstes
  - Wichtige Designentscheidungen

### Für nächste Phase

- **[PHASE2_MATCHING_ENGINE.md](docs/PHASE2_MATCHING_ENGINE.md)** – Matching-Engine Implementierung
  - Detaillierte Tasks
  - Test-Cases
  - Testdaten

### Weitere Dokumente (in Arbeit)

- `docs/INSTALLATION.md` – Detaillierte Setup-Anleitung
- `docs/API_REFERENCE.md` – API-Dokumentation
- `docs/USER_GUIDE.md` – Benutzer-Handbuch
- `docs/DEVELOPER_GUIDE.md` – Entwickler-Leitfaden

---

## 🏗️ Projektstruktur

```
authority-matching/
│
├── backend/                           # Python FastAPI Backend
│   ├── app/
│   │   ├── models/                   # SQLAlchemy ORM-Modelle
│   │   │   ├── building.py
│   │   │   ├── authority.py
│   │   │   ├── jurisdiction.py       # ZENTRAL
│   │   │   ├── request_type.py
│   │   │   ├── request.py
│   │   │   └── __init__.py
│   │   ├── schemas/                  # Pydantic API-Schemas
│   │   ├── database/                 # SQLAlchemy Engine
│   │   ├── services/                 # Business Logic (Phase 2+3)
│   │   │   ├── address_normalizer.py (Phase 2)
│   │   │   ├── jurisdiction_matcher.py (Phase 2)
│   │   │   ├── document_generator.py (Phase 3)
│   │   │   └── import_service.py
│   │   ├── api/                      # FastAPI Route Handler (Phase 4+)
│   │   ├── utils/                    # Hilfsfunktionen
│   │   ├── main.py                   # FastAPI Application
│   │   └── config.py
│   ├── templates/                    # Word-Dokumentvorlagen
│   ├── generated/                    # Generierte Dokumente (temp)
│   ├── tests/                        # Unit- & Integration-Tests
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                          # React/TypeScript Frontend (Phase 4+)
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                              # Dokumentation
│   ├── ARCHITECTURE.md               # Systemarchitektur ✅
│   ├── PHASE2_MATCHING_ENGINE.md    # Phase 2 Plan ✅
│   ├── INSTALLATION.md               # Setup
│   ├── API_REFERENCE.md             # API-Docs
│   ├── USER_GUIDE.md                # Benutzer-Handbuch
│   └── DEVELOPER_GUIDE.md           # Entwickler-Leitfaden
│
├── STATUS.md                          # Aktueller Status ✅
├── README.md                          # Diese Datei
├── .gitignore
└── docker-compose.yml (optional)     # Docker-Setup (später)
```

---

## 🗄️ Datenbankschema – Übersicht

### Zentrale Tabellen

**buildings** (Gebäudedatenbank)
- `building_id` (PK), street, house_number, postal_code, city
- `ags` (Amtlicher Gemeindeschlüssel)
- latitude, longitude, property_name, internal_reference

**request_types** (Auskunftsarten)
- `request_type_id` (PK), code, name
- template_filename, active

**authorities** (Behörden)
- `authority_id` (PK), authority_name, department_name
- street, postal_code, city
- email, phone, website
- source, last_verified_at (Datenqualität)

**jurisdictions** ⭐ (ZENTRALE Zuständigkeitsmatrix)
- `jurisdiction_id` (PK)
- `request_type_id` (FK), `authority_id` (FK)
- ags, street, district, postal_code
- priority (10-70), matching_level
- valid_from, valid_to
- source, last_verified_at, verified_by

**requests** (Anfrage-Historie)
- `request_id` (PK), `building_id` (FK)
- created_by, created_at, status

**request_items** (Einzelne Zuständigkeiten)
- `request_item_id` (PK)
- `request_id` (FK), `request_type_id` (FK), `authority_id` (FK)
- matching_status, matching_level, matching_confidence
- document_path, document_status
- manually_changed (für Audit)

---

## 🔄 Zuständigkeitsmatch-Hierarchie

Das Matching erfolgt hierarchisch nach Spezifität:

```
Level 1:  Straße + Hausnummer     (priority 10)  ← Höchste Spezifität
Level 2:  Nur Straße             (priority 20)
Level 3:  Stadtteil/Bezirk       (priority 30)
Level 4:  Gemeinde (AGS)         (priority 40)  ← Standard
Level 5:  Landkreis              (priority 50)
Level 6:  Bundesland             (priority 60)
Level 7:  PLZ (Fallback)         (priority 70)  ← Fallback
```

**Wichtig:** Regeln sind zentral in der Datenbank, nicht im Code!

---

## 🔧 Tech Stack

### Backend

```
Python 3.10+
├─ FastAPI 0.104+          (Web Framework)
├─ SQLAlchemy 2.0+         (ORM)
├─ Pydantic 2.5+           (Data Validation)
├─ python-docx 0.8+        (Word Generation)
├─ docxtpl 0.16+           (Template Engine)
├─ pandas 2.1+             (Data Processing)
└─ pytest 7.4+             (Testing)
```

### Datenbank

```
Entwicklung:  SQLite
Production:   PostgreSQL
```

### Frontend (Phase 4+)

```
React 18+
├─ TypeScript
├─ Vite
├─ Axios (API Client)
└─ TailwindCSS (Styling)
```

---

## 📖 Wichtige Konzepte

### 1. Zentrale Zuständigkeitsmatrix

Statt direkter Zuordnung `Gebäude → Behörde`:

```
Gebäudeadresse
    ↓ (Normalisierung)
AGS / Gemeinde
    ↓ (Auskunftstyp wählen)
Jurisdictions-Abfrage
    ↓ (Hierarchisches Matching)
Zuständige Behörde
```

### 2. Matching-Statusse

```
MATCHED            ← Eindeutige Behörde gefunden (confidence: 1.0)
REVIEW_REQUIRED    ← Mehrere Behörden möglich (confidence: 0.5)
NO_MATCH          ← Keine Behörde gefunden
MULTIPLE_MATCHES  ← Konfliktierende Regeln
```

### 3. Adressnormalisierung

Alle Adressen werden standardisiert:
- Leerzeichen entfernen
- Großschreibung normalisieren
- Umlaute konsistent behandeln
- Straßenabkürzungen aufgelösen
- Hausnummer und Suffix trennen

### 4. Datenqualität

Jede Zuständigkeitsregel hat:
- `source` – Woher stammt die Regel?
- `last_verified_at` – Wann verifiziert?
- `verified_by` – Wer hat verifiziert?

→ Nachvollziehbarkeit und Nachkontrolle möglich

---

## 🧪 Testing

### Unit Tests (Phase 2)

```bash
cd backend
pytest tests/ -v
```

Getestete Szenarien:
- ✅ Eindeutige Zuständigkeit
- ✅ Keine Zuständigkeit
- ✅ Multiple Matches
- ✅ Sonderregeln überschreiben Standardregeln
- ✅ Adressnormalisierung
- ✅ Mehrere Auskunftsarten
- ✅ Fehlende Daten

### Integration Tests (Phase 3+)

```bash
pytest tests/integration/ -v
```

---

## 🚀 Deployment

### Docker (optional, später)

```bash
docker-compose up
```

### Manual (lokal)

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production (mit Gunicorn)

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

---

## 📋 Checkliste für MVP

- [ ] Phase 1: Datenmodelle ✅
- [ ] Phase 2: Matching-Engine
- [ ] Phase 3: Dokumentgenerator
- [ ] Phase 4: API Endpoints
- [ ] Phase 5: Frontend (minimal)
- [ ] End-to-End Test
- [ ] Dokumentation
- [ ] Deployment

---

## 🎓 Getting Help

### Fragen zur Architektur?
→ Lese `docs/ARCHITECTURE.md`

### Fragen zur nächsten Phase?
→ Lese `docs/PHASE2_MATCHING_ENGINE.md`

### Fragen zum Status?
→ Lese `STATUS.md`

### API-Dokumentation?
→ Starte Backend und öffne http://localhost:8000/docs

---

## 📄 Lizenz

[Lizenztyp TBD]

---

## 👥 Team

- Architecture & Design: [Team]
- Backend Development: [Team]
- Frontend Development: [Team, später]

---

## 📝 Changelog

### 2026-08-26
- ✅ Projektinitialisierung
- ✅ Datenmodelle (Building, Authority, Jurisdiction, Request)
- ✅ SQLAlchemy ORM
- ✅ Pydantic Schemas
- ✅ FastAPI Grundgerüst
- ✅ Architektur-Dokumentation
- ✅ Phase 2 Planung

---

**Nächste Milestone:** Phase 2 Abschluss (Matching-Engine)  
**Zieldatum:** 2026-08-28

**Status:** 🟢 On Track
