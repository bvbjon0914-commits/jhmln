# 🏗️ Authority Matching System – Visuelle Architektur-Übersicht

---

## 🎯 Komplett-Überblick

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     USER INTERFACE (Frontend – React/TypeScript)               │
│     ┌──────────────────────────────────────────────────────┐   │
│     │  1. Building Search    → Gebäude suchen             │   │
│     │  2. Building Details   → Gebäudedaten anzeigen      │   │
│     │  3. Request Types      → Auskunftsarten wählen      │   │
│     │  4. Matching Results   → Behörden anzeigen          │   │
│     │  5. Documents          → Dateien herunterladen      │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    REST API (HTTP JSON)
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                                                                 │
│     BACKEND (Python/FastAPI)                                  │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ API Layer (Route Handlers)                           │   │
│     │  /buildings  /authorities  /matching  /documents     │   │
│     │  /requests   /imports      /health                   │   │
│     └──────────────────────────────────────────────────────┘   │
│                             ↓                                   │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ Service Layer (Business Logic)                       │   │
│     │                                                      │   │
│     │  1. AddressNormalizer              (Phase 2)         │   │
│     │     "Musterstraße" → normalisieren                   │   │
│     │                                                      │   │
│     │  2. JurisdictionMatcher            (Phase 2)         │   │
│     │     Gebäude + Auskunft → Behörde                     │   │
│     │     Hierarchisches Matching (7 Stufen)              │   │
│     │                                                      │   │
│     │  3. DocumentGenerator              (Phase 3)         │   │
│     │     Behörde + Vorlage → DOCX                         │   │
│     │                                                      │   │
│     │  4. ImportService                  (Phase 3)         │   │
│     │     CSV/Excel → Datenbank                            │   │
│     │                                                      │   │
│     └──────────────────────────────────────────────────────┘   │
│                             ↓                                   │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ Repository/DAO Layer (Data Access)                   │   │
│     │                                                      │   │
│     │  BuildingRepository                                 │   │
│     │  AuthorityRepository                                │   │
│     │  JurisdictionRepository                             │   │
│     │  RequestTypeRepository                              │   │
│     │  RequestRepository                                  │   │
│     │                                                      │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    SQLAlchemy ORM
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                                                                 │
│     DATABASE (SQLite / PostgreSQL)                            │
│     ┌──────────────────────────────────────────────────────┐   │
│     │                                                      │   │
│     │  MAIN TABLES:                                        │   │
│     │  ├─ buildings           (Gebäudedatenbank)           │   │
│     │  ├─ authorities         (Behörden)                   │   │
│     │  ├─ request_types       (Auskunftsarten)             │   │
│     │  ├─ jurisdictions       (⭐ ZENTRALE Zuständigkeit)  │   │
│     │  ├─ requests            (Anfrage-Historie)           │   │
│     │  └─ request_items       (Einzelne Zuständigkeiten)   │   │
│     │                                                      │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Datenfluss – Beispiel: Gebäude + Auskunft → Behörde

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ USER:  "Musterstraße 12, 44787 Bochum"                     │
│ USER:  "Ich brauche: Grundbuch, Bauakten, Altlasten"       │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
    ┌───────────────────────────────────────┐
    │  1. GEBÄUDE SUCHEN                    │
    │     BuildingSearch Component          │
    │     GET /api/buildings?search=...     │
    └───────────────────────────────────────┘
                         │
                         ↓
    ┌───────────────────────────────────────────────────┐
    │  2. BUILDING REPOSITORY                           │
    │     DB Query: buildings WHERE ...                 │
    │     Result: Building{building_id: 100234, ags...}│
    └───────────────────────────────────────────────────┘
                         │
                         ↓
    ┌────────────────────────────────────────────┐
    │  3. MATCHING STARTEN                       │
    │     POST /api/matching                     │
    │     {                                      │
    │       building_id: "100234",               │
    │       request_type_ids: [                  │
    │         "GRUNDBUCH",                       │
    │         "BAUAKTEN",                        │
    │         "ALTLASTEN"                        │
    │       ]                                    │
    │     }                                      │
    └────────────────────────────────────────────┘
                         │
                         ↓
    ┌────────────────────────────────────────────────────┐
    │  4. JURISDICTION MATCHING SERVICE                  │
    │                                                    │
    │  Für jede RequestType:                             │
    │  ┌──────────────────────────────────────────────┐  │
    │  │ a) AddressNormalizer:                        │  │
    │  │    "Musterstraße 12" → "Musterstraße", "12"  │  │
    │  │                                              │  │
    │  │ b) AGS auslesen:                             │  │
    │  │    ags = "05911000" ✓                        │  │
    │  │                                              │  │
    │  │ c) Hierarchisches Matching:                  │  │
    │  │                                              │  │
    │  │    Stufe 1 (STREET_NUMBER):                  │  │
    │  │    WHERE ags=05911000                        │  │
    │  │      AND street="Musterstraße"               │  │
    │  │      AND house_number="12"                   │  │
    │  │      AND request_type="GRUNDBUCH"            │  │
    │  │    → Kein Match                              │  │
    │  │                                              │  │
    │  │    Stufe 2 (STREET):                         │  │
    │  │    WHERE ags=05911000                        │  │
    │  │      AND street="Musterstraße"               │  │
    │  │      AND request_type="GRUNDBUCH"            │  │
    │  │    → Kein Match                              │  │
    │  │                                              │  │
    │  │    Stufe 3 (DISTRICT):                       │  │
    │  │    WHERE ags=05911000                        │  │
    │  │      AND district=[...]                      │  │
    │  │      AND request_type="GRUNDBUCH"            │  │
    │  │    → Kein Match                              │  │
    │  │                                              │  │
    │  │    Stufe 4 (MUNICIPALITY) ← STANDARD:        │  │
    │  │    WHERE ags=05911000                        │  │
    │  │      AND request_type="GRUNDBUCH"            │  │
    │  │      AND priority=40                         │  │
    │  │    → MATCH! Authority: AG_BOCHUM_001 ✓       │  │
    │  │      Status: MATCHED                         │  │
    │  │      Confidence: 1.0                         │  │
    │  │      Reason: "Eindeutige Zuordnung           │  │
    │  │                über AGS 05911000"            │  │
    │  └──────────────────────────────────────────────┘  │
    │                                                    │
    │  Gleiches für BAUAKTEN und ALTLASTEN              │
    │                                                    │
    └────────────────────────────────────────────────────┘
                         │
                         ↓
    ┌────────────────────────────────────────────────┐
    │  5. MATCHING RESULTS                           │
    │                                                │
    │  Request ID: REQ_20260826_001                  │
    │                                                │
    │  ┌──────────────────────────────────────────┐  │
    │  │ GRUNDBUCH                                │  │
    │  │ Authority: AG_BOCHUM_001                 │  │
    │  │ Level: MUNICIPALITY                      │  │
    │  │ Status: ✓ MATCHED                        │  │
    │  │ Confidence: 1.0                          │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │
    │  ┌──────────────────────────────────────────┐  │
    │  │ BAUAKTEN                                 │  │
    │  │ Authority: BAUAMT_BOCHUM_001             │  │
    │  │ Level: MUNICIPALITY                      │  │
    │  │ Status: ✓ MATCHED                        │  │
    │  │ Confidence: 1.0                          │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │
    │  ┌──────────────────────────────────────────┐  │
    │  │ ALTLASTEN                                │  │
    │  │ Authority: UBB_BOCHUM_001                │  │
    │  │ Level: MUNICIPALITY                      │  │
    │  │ Status: ✓ MATCHED                        │  │
    │  │ Confidence: 1.0                          │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │
    └────────────────────────────────────────────────┘
                         │
                         ↓
    ┌──────────────────────────────────────────┐
    │  6. MATCHING RESULTS ANZEIGEN            │
    │     MatchingResults Component            │
    │                                          │
    │     Tabelle mit:                         │
    │     │ Auskunft │ Behörde       │ Status │
    │     │ Grundb.  │ Amtsgericht.. │ ✓✓✓    │
    │     │ Bauakten │ Bauordnungsamt│ ✓✓✓    │
    │     │ Altlasten│ UBB Bochum    │ ✓✓✓    │
    │                                          │
    │  USER prüft die Zuordnungen              │
    │                                          │
    └──────────────────────────────────────────┘
                         │
                         ↓
    ┌──────────────────────────────────────────────────────┐
    │  7. DOKUMENTGENERIERUNG                            │
    │     POST /api/documents/generate                    │
    │     { request_id: "REQ_20260826_001" }              │
    │                                                    │
    │  Für jedes request_item:                            │
    │  ┌──────────────────────────────────────────────┐  │
    │  │ a) Template laden (grundbuch.docx)           │  │
    │  │                                              │  │
    │  │ b) Kontext zusammenstellen:                  │  │
    │  │    authority_name: "Amtsgericht Bochum"      │  │
    │  │    authority_street: "Kortumstraße 42"       │  │
    │  │    building_street: "Musterstraße"           │  │
    │  │    building_house_number: "12"               │  │
    │  │    current_date: "26.08.2026"                │  │
    │  │    ... (weitere Felder)                      │  │
    │  │                                              │  │
    │  │ c) docxtpl.render(context)                   │  │
    │  │                                              │  │
    │  │ d) Speichern:                                │  │
    │  │    "100234_GRUNDBUCH_Bochum_20260826.docx"  │  │
    │  │                                              │  │
    │  └──────────────────────────────────────────────┘  │
    │                                                    │
    │  Parallel für alle 3 Auskünfte                     │
    │                                                    │
    └──────────────────────────────────────────────────────┘
                         │
                         ↓
    ┌──────────────────────────────────────────────────┐
    │  8. DOKUMENTE ANZEIGEN & HERUNTERLADEN          │
    │     GeneratedDocuments Component                │
    │                                                │
    │  ✓ 100234_GRUNDBUCH_Bochum_20260826.docx      │
    │    [Herunterladen]                             │
    │                                                │
    │  ✓ 100234_BAUAKTEN_Bochum_20260826.docx       │
    │    [Herunterladen]                             │
    │                                                │
    │  ✓ 100234_ALTLASTEN_Bochum_20260826.docx      │
    │    [Herunterladen]                             │
    │                                                │
    │  [Alle als ZIP herunterladen]                  │
    │                                                │
    └──────────────────────────────────────────────────┘
                         │
                         ↓
    ┌──────────────────────────────────────────────┐
    │  ✅ SUCCESS!                                  │
    │  USER hat alle 3 Dokumente                   │
    │  mit korrekten Behördendaten               │
    └──────────────────────────────────────────────┘
```

---

## 🗂️ Matching-Hierarchie (7 Stufen)

```
                            SPEZIFISCH
                                ▲
                                │
                Stufe 1:    Straße + Hausnummer
                            (priority: 10)
                                │
                Stufe 2:    Straße
                            (priority: 20)
                                │
                Stufe 3:    Stadtteil / Bezirk
                            (priority: 30)
                                │
                Stufe 4:    Gemeinde / AGS  ← STANDARD
                            (priority: 40)
                                │
                Stufe 5:    Landkreis
                            (priority: 50)
                                │
                Stufe 6:    Bundesland
                            (priority: 60)
                                │
                Stufe 7:    Postleitzahl
                            (priority: 70)
                                │
                                ▼
                         ALLGEMEIN
```

**Matching-Regel:**
- Abfrage startet bei Stufe 1
- Wenn Match gefunden → return MATCHED
- Wenn kein Match → weiter zu Stufe 2
- Wenn keine Stufe matched → return NO_MATCH
- Wenn mehrere gleichrangige Matches → return MULTIPLE_MATCHES

---

## 🗄️ Zentrale Tabelle: jurisdictions

```
jurisdictions (Die ZENTRALE Tabelle für alle Regeln)

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  jurisdiction_id (PK)                                       │
│  request_type_id (FK) ──→ request_types                     │
│  authority_id (FK) ───────→ authorities                     │
│                                                             │
│  GEOGRAFISCHE ZUORDNUNG:                                    │
│  ├─ country: "DE"                                           │
│  ├─ state: "Nordrhein-Westfalen"  (optional)               │
│  ├─ ags: "05911000"                (Gemeindeschlüssel)     │
│  ├─ municipality: "Bochum"         (optional)              │
│  ├─ district: "Gerthe"             (optional)              │
│  ├─ street: "Musterstraße"         (optional)              │
│  ├─ house_number: "12"             (optional)              │
│  └─ postal_code: "44787"           (optional)              │
│                                                             │
│  HIERARCHIE & PRIORISIERUNG:                                │
│  ├─ priority: 10-70                (niedrig = höher Priorität)
│  ├─ matching_level: "MUNICIPALITY" (Text zur Dokumentation)
│  ├─ valid_from: 2026-01-01        (zeitliche Gültigkeit)   │
│  └─ valid_to: 2030-12-31          (zeitliche Gültigkeit)   │
│                                                             │
│  DATENQUALITÄT:                                             │
│  ├─ source: "Behördenverzeichnis NRW 2026"                 │
│  ├─ last_verified_at: 2026-08-15  (zuletzt verifiziert)   │
│  ├─ verified_by: "Max Müller"     (wer hat verifiziert)    │
│  └─ active: true                  (noch gültig)            │
│                                                             │
│  NOTIZEN:                                                   │
│  └─ notes: "Zivil- und Handelsregister zuständig"         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

BEISPIEL-EINTRÄGE:

┌──────────────────────────────────────────────────────┐
│ Regel 1: Standard Gemeinde-Zuständigkeit             │
│                                                      │
│ request_type_id: GRUNDBUCH                          │
│ authority_id: AG_BOCHUM_001                         │
│ ags: 05911000                                       │
│ priority: 40                                        │
│ matching_level: MUNICIPALITY                        │
│                                                      │
│ → Alle Grundbuchangfragen aus Bochum                │
│   gehen an Amtsgericht Bochum                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Regel 2: Spezialregel (Straße)                      │
│                                                      │
│ request_type_id: GRUNDBUCH                          │
│ authority_id: SPECIAL_AUTHORITY                     │
│ ags: 05911000                                       │
│ street: "Spezialstraße"                             │
│ priority: 20                                        │
│ matching_level: STREET                              │
│                                                      │
│ → Grundbuchangfragen aus der                        │
│   "Spezialstraße" in Bochum                         │
│   gehen an die Spezial-Behörde                      │
│   (höhere Priorität als Regel 1!)                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Regel 3: Landkreis-Fallback                         │
│                                                      │
│ request_type_id: ALTLASTEN                          │
│ authority_id: KREIS_BOCHUM_ALT                      │
│ (county code): 054...                               │
│ priority: 50                                        │
│ matching_level: COUNTY                              │
│                                                      │
│ → Wenn Gemeinde nicht zustellen kann,               │
│   Altlasten zum Landkreis                           │
└──────────────────────────────────────────────────────┘
```

---

## 📝 Matching-Ergebnis (MatchingResult)

```python
{
    "building_id": "100234",
    "request_type_id": "GRUNDBUCH",
    "authority_id": "AG_BOCHUM_001",
    
    # Matching-Details
    "matching_level": "MUNICIPALITY",
    "matching_status": "MATCHED",
    "matching_confidence": 1.0,
    
    # Nachvollziehbarkeit
    "reason": "Eindeutige Zuordnung über AGS 05911000",
    
    # Alternativen (bei MULTIPLE_MATCHES)
    "alternative_authorities": []
}
```

---

## 🔧 Services-Übersicht (Phase 2+3)

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  AddressNormalizer (Phase 2)                    │
│  ├─ normalize(address_data)                     │
│  └─ split_house_number(number)                  │
│                                                 │
│  JurisdictionMatchingService (Phase 2)          │
│  ├─ match_authority(building, request_type_id) │
│  └─ match_authorities(building, request_types) │
│                                                 │
│  DocumentGenerationService (Phase 3)            │
│  ├─ generate_document(building, req_type, auth)│
│  └─ generate_batch(request_id)                  │
│                                                 │
│  ImportService (Phase 3)                        │
│  ├─ import_buildings(file)                      │
│  ├─ import_authorities(file)                    │
│  └─ import_jurisdictions(file)                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📊 Matching-Statusse

```
┌──────────────────────────────────┐
│                                  │
│  MATCHED ✓✓✓                     │
│  ────────────────────────────    │
│  Status: Eindeutig               │
│  Confidence: 1.0                 │
│  Farbe: Grün                      │
│                                  │
│  → Eine Behörde gefunden          │
│  → Dokumentgenerierung möglich    │
│                                  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│                                  │
│  REVIEW_REQUIRED ⚠                │
│  ────────────────────────────    │
│  Status: Mehrere Optionen         │
│  Confidence: 0.5                  │
│  Farbe: Gelb                      │
│                                  │
│  → Mehrere Behörden möglich       │
│  → Nutzer muss auswählen          │
│  → Danach Dokumentgenerierung     │
│                                  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│                                  │
│  NO_MATCH ✗                       │
│  ────────────────────────────    │
│  Status: Nicht gefunden           │
│  Confidence: 0.0                  │
│  Farbe: Rot                       │
│                                  │
│  → Keine Behörde zuständig        │
│  → Manuelle Prüfung notwendig     │
│  → Ggfs. Regel hinzufügen         │
│                                  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│                                  │
│  MULTIPLE_MATCHES ✗ CONFLICT      │
│  ────────────────────────────    │
│  Status: Konfliktierende Regeln   │
│  Confidence: 0.0                  │
│  Farbe: Rot                       │
│                                  │
│  → 2+ gleichrangige Regeln        │
│  → Datenbankfehler (sollte nicht  │
│     vorkommen, wenn richtig       │
│     konfiguriert)                │
│                                  │
└──────────────────────────────────┘
```

---

## 🔐 Sicherheitsarchitektur

```
┌─────────────────┐
│  Frontend       │
│  (React)        │
└────────┬────────┘
         │
         ├─ CORS Check ✓
         │
         ├─ Input Validation ✓
         │  (Pydantic Schemas)
         │
         ├─ API Authentication ⬜
         │  (später: JWT Tokens)
         │
         ├─ Rate Limiting ⬜
         │  (später: Pro IP)
         │
         └─ Logging ✓
            (Request/Response)

         │
         ↓
    
    Database

         │
         ├─ SQL Injection Prevention ✓
         │  (SQLAlchemy ORM)
         │
         ├─ Data Encryption ⬜
         │  (später: für sensible Daten)
         │
         └─ Audit Trail ✓
            (requests, request_items)
```

---

## 📈 Skalierungsstrategie

```
MVP (jetzt):
├─ SQLite
├─ Single Server
├─ ~100-1000 Gebäude
└─ ~100 Behörden

Phase 2 (später):
├─ PostgreSQL
├─ Caching (Redis)
├─ Indexing Optimization
├─ ~1M Gebäude
└─ ~50k Behörden

Phase 3 (Zukunft):
├─ Horizontal Scaling
├─ Load Balancing
├─ Database Replication
├─ Batch Processing
├─ Async Job Queue
├─ Microservices
└─ Full Deutschland Coverage
```

---

**Diese Übersicht sollte dir ein visuelles Verständnis des Systems geben!**

Bei Fragen zu spezifischen Komponenten → siehe `ARCHITECTURE.md`
