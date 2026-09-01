# Phase 2: Matching-Engine Implementierung

## Übersicht

Nach erfolgreicher Implementierung der Datenmodelle (Phase 1) beginnen wir nun mit der **Matching-Engine** – dem Herzstück des Systems.

Die Matching-Engine ist verantwortlich dafür, für eine gegebene Gebäudeadresse und Auskunftsart die richtige Behörde zu ermitteln.

---

## Ziele dieser Phase

1. ✅ AddressNormalizer implementieren und testen
2. ✅ JurisdictionMatchingService implementieren
3. ✅ Matching-Hierarchie korrekt abbilden
4. ✅ Unit Tests für alle Matching-Szenarien
5. ✅ Manuelles Testen mit Testdaten
6. ✅ Fehlerbehandlung und Status-Codes

---

## Was wird implementiert

### 1. AddressNormalizer Service

**Datei:** `backend/app/services/address_normalizer.py`

**Aufgaben:**
- Leerzeichen normalisieren (leading/trailing)
- Straßenabkürzungen aufgelösen (Str. → Straße)
- Großschreibung standardisieren
- Umlaute behandeln
- Hausnummer und Zusätze trennen (12a → 12, a)
- PLZ validieren
- Stadtteil / Bezirk normalisieren

**Input:**
```python
{
    "street": "  musterstraße   ",
    "house_number": "12 a",
    "city": "bochum",
    "postal_code": "44787",
}
```

**Output:**
```python
{
    "street": "Musterstraße",
    "house_number": "12",
    "house_number_suffix": "a",
    "city": "Bochum",
    "postal_code": "44787",
    "quality_flags": ["COMPLETE"],
}
```

---

### 2. JurisdictionMatchingService

**Datei:** `backend/app/services/jurisdiction_matcher.py`

**Hauptfunktionen:**

```python
class JurisdictionMatchingService:
    
    def match_authority(
        self,
        building: Building,
        request_type_id: str,
    ) -> MatchingResult:
        """
        Matcht eine Behörde für ein Gebäude und Auskunftsart.
        """
        pass
    
    def match_authorities(
        self,
        building: Building,
        request_type_ids: List[str],
    ) -> List[MatchingResult]:
        """
        Matcht mehrere Behörden für mehrere Auskunftsarten.
        """
        pass
```

**Matching-Algorithmus:**

```
1. Adresse normalisieren
2. AGS bestimmen (vorhanden oder vom System)
3. Für jede Matching-Stufe (nach Priorität):
   
   a) Query Jurisdictions mit aktueller Stufe
   b) Filter: request_type_id, active=True, valid_from ≤ today ≤ valid_to
   c) Order by: priority, created_at
   
   d) Evaluate Treffer:
      - 0 Treffer: continue to next level
      - 1 Treffer: return MATCHED
      - >1 Treffer on same level: return MULTIPLE_MATCHES
      
4. Wenn kein Match auf allen Stufen: return NO_MATCH
```

---

### 3. Matching-Ergebnis (MatchingResult)

**Datenstruktur:**

```python
@dataclass
class MatchingResult:
    building_id: str
    request_type_id: str
    authority_id: Optional[str]
    
    # Matching-Details
    matching_level: Optional[str]  # STREET_NUMBER, STREET, DISTRICT, etc.
    matching_status: str            # MATCHED, REVIEW_REQUIRED, NO_MATCH, MULTIPLE_MATCHES
    matching_confidence: float      # 0.0 - 1.0
    reason: str                     # Erklärung des Ergebnisses
    
    # Alternative bei MULTIPLE_MATCHES
    alternative_authorities: List[str]
```

---

## Testfälle (Unit Tests)

Folgende Testfälle müssen implementiert werden:

### Test 1: Eindeutige Gemeinde-Zuständigkeit
```
Input:
  - Building: Musterstraße 12, 44787 Bochum, ags=05911000
  - RequestType: GRUNDBUCH

Erwartet:
  - Status: MATCHED
  - Authority: AG_BOCHUM_001
  - Level: MUNICIPALITY
  - Confidence: 1.0
```

### Test 2: Keine Zuständigkeit vorhanden
```
Input:
  - Building: Unbekannte Straße 99, 99999 Nullstadt, ags=99999999
  - RequestType: GRUNDBUCH

Erwartet:
  - Status: NO_MATCH
  - Authority: None
  - Reason: "Für AGS 99999999 keine Zuständigkeit"
```

### Test 3: Mehrere gleichwertige Zuständigkeiten
```
Input:
  - Building: Musterstraße 12, 44787 Bochum
  - RequestType: SONDERFALL (mit 2 Regeln auf gleicher Stufe)

Erwartet:
  - Status: MULTIPLE_MATCHES
  - Authority: None
  - Alternatives: [AUTH_001, AUTH_002]
  - Reason: "2 gleichwertige Behörden gefunden"
```

### Test 4: Sonderregel überschreibt Gemeinde-Regel
```
Input:
  - Building: Spezialstraße 5, 44787 Bochum (ags=05911000)
  - RequestType: GRUNDBUCH
  - Jurisdictions:
    * Rule 1: street=Spezialstraße, authority=SPECIAL_AUTHORITY (priority=10)
    * Rule 2: ags=05911000, authority=NORMAL_AUTHORITY (priority=40)

Erwartet:
  - Status: MATCHED
  - Authority: SPECIAL_AUTHORITY
  - Level: STREET
```

### Test 5: PLZ stimmt, AGS aber nicht
```
Input:
  - Building: Straße X, 44787 Bochum, ags=05911000
  - RequestType: GRUNDBUCH
  - Jurisdictions:
    * Rule 1: ags=05911000, authority=CORRECT_AUTH (priority=40)
    * Rule 2: postal_code=44787, authority=WRONG_AUTH (priority=70)

Erwartet:
  - Status: MATCHED
  - Authority: CORRECT_AUTH
  - Level: MUNICIPALITY
  - (Falback-Rule wird NICHT verwendet!)
```

### Test 6: Mehrere Auskunftsarten
```
Input:
  - Building: Musterstraße 12, 44787 Bochum
  - RequestTypes: [GRUNDBUCH, BAUAKTEN, ALTLASTEN]

Erwartet:
  - 3 separate Matching Results
  - Jeder mit eigenem Authority (können unterschiedlich sein!)
  - Alle sollten MATCHED sein
```

### Test 7: Adressnormalisierung
```
Input:
  - street: "Musterstr.  "
  - house_number: "12a"
  - city: "BOCHUM"

Erwartet:
  - Normalisiert zu: "Musterstraße", "12", "Bochum"
  - Match gegen DB gefunden
```

### Test 8: Fehlende Daten
```
Input:
  - Building ohne AGS
  - System muss trotzdem versuchen zu matchen

Erwartet:
  - Entweder MATCHED oder NO_MATCH
  - Nie: Exception
```

---

## Implementierungsreihenfolge

### Schritt 1: AddressNormalizer
```python
# Datei: backend/app/services/address_normalizer.py

class AddressNormalizer:
    
    @staticmethod
    def normalize(address_data: dict) -> dict:
        # 1. Leerzeichen entfernen
        # 2. Großschreibung
        # 3. Straßenabkürzungen
        # 4. Hausnummer splitten
        # 5. PLZ validieren
        pass
    
    @staticmethod
    def split_house_number(house_number: str) -> tuple:
        # "12a" → ("12", "a")
        # "12-14" → ("12-14", "")
        pass
```

### Schritt 2: Matching Service
```python
# Datei: backend/app/services/jurisdiction_matcher.py

class JurisdictionMatchingService:
    
    def __init__(self, db_session):
        self.db = db_session
    
    def match_authority(self, building, request_type_id):
        # Hauptmatch-Logik
        pass
    
    def match_authorities(self, building, request_type_ids):
        # Mehrere Types auf einmal
        pass
```

### Schritt 3: Unit Tests
```python
# Datei: backend/tests/test_jurisdiction_matcher.py

class TestJurisdictionMatcher:
    
    def test_matched_municipality_level(self):
        # Test 1
        pass
    
    def test_no_match(self):
        # Test 2
        pass
    
    def test_multiple_matches(self):
        # Test 3
        pass
    
    # ... etc.
```

### Schritt 4: Testdaten-Loader
```python
# Datei: backend/tests/fixtures.py

def create_test_buildings():
    # 10 Testgebäude
    pass

def create_test_authorities():
    # 20 Test-Behörden
    pass

def create_test_jurisdictions():
    # Zuständigkeitsregeln für alle Tests
    pass
```

---

## Testdaten (Beispiel)

### Buildings
```
ID: B001
Street: Musterstraße
House: 12
PostalCode: 44787
City: Bochum
AGS: 05911000

ID: B002
Street: Spezialstraße
House: 5
PostalCode: 44787
City: Bochum
AGS: 05911000
```

### Authorities
```
ID: AG_BOCHUM_001
Name: Amtsgericht Bochum
City: Bochum
Email: grundbuch@ag-bochum.de

ID: BAUAMT_BOCHUM_001
Name: Bauordnungsamt Bochum
City: Bochum
Email: bauamt@bochum.de
```

### Jurisdictions
```
# Standard Gemeinde-Zuständigkeit
request_type: GRUNDBUCH
ags: 05911000
authority: AG_BOCHUM_001
priority: 40
matching_level: MUNICIPALITY

# Sonderregel
request_type: GRUNDBUCH
street: Spezialstraße
ags: 05911000
authority: SPECIAL_AUTHORITY
priority: 10
matching_level: STREET
```

---

## Definition of Done – Phase 2

Die Matching-Engine ist fertig, wenn:

1. ✅ AddressNormalizer existiert und alle Tests bestehen
2. ✅ JurisdictionMatchingService existiert
3. ✅ Alle 8 Unit Tests erfolgreich
4. ✅ Matching-Hierarchie ist korrekt abgebildet
5. ✅ Mehrere Auskunftsarten können parallel gematcht werden
6. ✅ Sonderfälle (MULTIPLE_MATCHES, NO_MATCH) werden korrekt behandelt
7. ✅ Fehlende Daten führen nicht zu Exceptions
8. ✅ Jedes Matching kann mit Grund nachvollzogen werden

---

## Nächste Schritte danach

Nach Phase 2 (Matching) wird Phase 3 implementiert:

**Phase 3: Dokumentengenerator**
- DocumentGenerationService
- Word-Template mit Platzhaltern
- Kontext-Zusammenstellung
- DOCX-Generierung
- Dateinamen-Generierung

---

## Wichtige Regeln

1. **Keine Hard-Coded Regeln**
   - Alle Zuständigkeitsregeln MÜSSEN aus der DB kommen
   - Kein `if city == "Bochum": return AUTHORITY`

2. **Reproduzierbarkeit**
   - Jedes Matching muss erklärbar sein
   - `reason` muss aussagekräftig sein

3. **Fehlertoleranz**
   - Keine unsicheren Automatismen
   - `MULTIPLE_MATCHES` lieber als falsch-positives Match

4. **Tests First**
   - Tests MÜSSEN vor der Implementierung geschrieben werden
   - Mindestens 8 Test-Cases

---

## Kontrollpunkte

| Schritt | Status | Bemerkung |
|---------|--------|-----------|
| AddressNormalizer implementiert | ⬜ | |
| AddressNormalizer Tests grün | ⬜ | |
| JurisdictionMatchingService implementiert | ⬜ | |
| Matching Tests 1-8 grün | ⬜ | |
| Manuelle Verifikation mit Testdaten | ⬜ | |
| Code-Review & Refactoring | ⬜ | |

---

**Stand:** 2026-08-26  
**Nächstes Review:** Nach Implementierung aller Tests
