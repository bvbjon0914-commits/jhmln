"""
Seed-Daten für Entwicklung und Demo.

Erzeugt ein realistisches Testszenario rund um Bochum:
- Mehrere Gebäude (inkl. eines mit Sonderregel und eines ohne Zuständigkeit)
- Behörden für alle 10 Auskunftsarten
- Zuständigkeitsregeln auf unterschiedlichen Hierarchie-Stufen
  (Gemeinde-Standard, Straßen-Sonderregel, Landkreis-Fallback,
  bewusst ein Konfliktfall für MULTIPLE_MATCHES)

WICHTIG: Dies sind Testdaten zur Demonstration der Matching-Logik,
keine echten, verifizierten Behördendaten!
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, init_db, drop_all_tables
from app.models import Building, RequestType, Authority, Jurisdiction, STANDARD_REQUEST_TYPES


REQUEST_TYPE_DEFINITIONS = [
    ("GRUNDBUCH", "Grundbuchauskunft", "grundbuch.docx"),
    ("BAUAKTEN", "Bauaktenauskunft", "bauakten.docx"),
    ("BAULASTEN", "Baulastenauskunft", "baulasten.docx"),
    ("ALTLASTEN", "Altlastenauskunft", "altlasten.docx"),
    ("ERSCHLIESSUNG", "Erschließungsbeiträge / Anliegerbescheinigung", "erschliessung.docx"),
    ("DENKMALSCHUTZ", "Denkmalschutzauskunft", "denkmalschutz.docx"),
    ("BODENDENKMALSCHUTZ", "Bodendenkmalschutzauskunft", "bodendenkmalschutz.docx"),
    ("WASSERSCHUTZ", "Wasserschutzgebietsauskunft", "wasserschutz.docx"),
    ("HOCHWASSERSCHUTZ", "Hochwasserschutzauskunft", "hochwasserschutz.docx"),
    ("KAMPFMITTEL", "Kampfmittelauskunft", "kampfmittel.docx"),
]


def seed():
    print("⚠ Lösche bestehende Tabellen und baue sie neu auf ...")
    drop_all_tables()
    init_db()

    db = SessionLocal()

    try:
        # ============ Request Types ============
        print("→ Lege Auskunftsarten an ...")
        for code, name, template in REQUEST_TYPE_DEFINITIONS:
            db.add(RequestType(
                request_type_id=code,
                code=code,
                name=name,
                description=f"Auskunft: {name}",
                template_filename=template,
                active=True,
            ))
        db.commit()

        # ============ Buildings ============
        print("→ Lege Testgebäude an ...")
        buildings = [
            Building(
                building_id="100234",
                street="Musterstraße",
                house_number="12",
                postal_code="44787",
                city="Bochum",
                district="Innenstadt",
                state="Nordrhein-Westfalen",
                ags="05911000",
                property_name="Geschäftshaus Musterstraße",
                internal_reference="OBJ-A-001",
            ),
            Building(
                building_id="100235",
                street="Spezialstraße",
                house_number="5",
                postal_code="44787",
                city="Bochum",
                district="Innenstadt",
                state="Nordrhein-Westfalen",
                ags="05911000",
                property_name="Wohnhaus Spezialstraße",
                internal_reference="OBJ-A-002",
            ),
            Building(
                building_id="100236",
                street="Konfliktweg",
                house_number="8",
                postal_code="44789",
                city="Bochum",
                district="Wattenscheid",
                state="Nordrhein-Westfalen",
                ags="05911000",
                property_name="Testobjekt Konfliktfall",
                internal_reference="OBJ-A-003",
            ),
            Building(
                building_id="100237",
                street="Unbekannte Allee",
                house_number="1",
                postal_code="99999",
                city="Niemandsdorf",
                state="Nordrhein-Westfalen",
                ags="05999999",
                property_name="Testobjekt ohne Zuständigkeit",
                internal_reference="OBJ-A-004",
            ),
            Building(
                building_id="100238",
                street="Kortumstraße",
                house_number="100",
                postal_code="44787",
                city="Bochum",
                district="Innenstadt",
                state="Nordrhein-Westfalen",
                ags="05911000",
                property_name="Bürogebäude Kortumstraße",
                internal_reference="OBJ-A-005",
            ),
            Building(
                building_id="100239",
                street="Herner Straße",
                house_number="45",
                postal_code="44653",
                city="Herne",
                state="Nordrhein-Westfalen",
                ags="05916000",
                property_name="Lagerhalle Herne",
                internal_reference="OBJ-A-006",
            ),
        ]
        db.add_all(buildings)
        db.commit()

        # ============ Authorities ============
        print("→ Lege Behörden an ...")
        authorities = [
            Authority(
                authority_id="AG_BOCHUM_001",
                authority_name="Amtsgericht Bochum",
                department_name="Grundbuchamt",
                street="Josef-Neuberger-Straße",
                house_number="1",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="grundbuch@ag-bochum.nrw.de",
                phone="0234 / 130-0",
                website="https://www.ag-bochum.nrw.de",
                source="NRW-Justizportal (Test)",
                active=True,
            ),
            Authority(
                authority_id="AG_BOCHUM_SPEZIAL",
                authority_name="Amtsgericht Bochum (Sonderzuständigkeit)",
                department_name="Grundbuchamt - Sonderbezirk Spezialstraße",
                street="Josef-Neuberger-Straße",
                house_number="1",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="grundbuch-sonder@ag-bochum.nrw.de",
                phone="0234 / 130-100",
                source="Manuell erfasst (Test)",
                active=True,
            ),
            Authority(
                authority_id="BAUAMT_BOCHUM_001",
                authority_name="Stadt Bochum",
                department_name="Bauordnungsamt",
                street="Willy-Brandt-Platz",
                house_number="2-4",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="bauordnungsamt@bochum.de",
                phone="0234 / 910-0",
                website="https://www.bochum.de",
                source="Stadt Bochum Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="UBB_BOCHUM_001",
                authority_name="Stadt Bochum",
                department_name="Untere Bodenschutzbehörde",
                street="Willy-Brandt-Platz",
                house_number="2-4",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="bodenschutz@bochum.de",
                phone="0234 / 910-101",
                source="Stadt Bochum Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="DENKMAL_LWL_001",
                authority_name="LWL - Amt für Denkmalpflege Westfalen",
                department_name="Denkmalschutz",
                street="Fürstenbergstraße",
                house_number="15",
                postal_code="48147",
                city="Münster",
                state="Nordrhein-Westfalen",
                email="denkmalpflege@lwl.org",
                source="LWL Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="BODENDENKMAL_LWL_001",
                authority_name="LWL - Archäologie für Westfalen",
                department_name="Bodendenkmalpflege",
                street="Fürstenbergstraße",
                house_number="15",
                postal_code="48147",
                city="Münster",
                state="Nordrhein-Westfalen",
                email="archaeologie@lwl.org",
                source="LWL Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="WASSER_KREIS_BOCHUM",
                authority_name="Stadt Bochum",
                department_name="Untere Wasserbehörde",
                street="Willy-Brandt-Platz",
                house_number="2-4",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="wasserbehoerde@bochum.de",
                source="Stadt Bochum Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="KAMPFMITTEL_NRW",
                authority_name="Bezirksregierung Arnsberg",
                department_name="Kampfmittelbeseitigungsdienst NRW",
                street="Seibertzstraße",
                house_number="1",
                postal_code="59821",
                city="Arnsberg",
                state="Nordrhein-Westfalen",
                email="kampfmittelbeseitigung@bezreg-arnsberg.nrw.de",
                website="https://www.bezreg-arnsberg.nrw.de",
                source="Landesweite Zuständigkeit NRW (Test)",
                active=True,
            ),
            Authority(
                authority_id="ERSCHLIESSUNG_BOCHUM",
                authority_name="Stadt Bochum",
                department_name="Tiefbauamt - Erschließungsbeiträge",
                street="Willy-Brandt-Platz",
                house_number="2-4",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="tiefbauamt@bochum.de",
                source="Stadt Bochum Website (Test)",
                active=True,
            ),
            Authority(
                authority_id="BAULASTEN_BOCHUM",
                authority_name="Stadt Bochum",
                department_name="Baulastenstelle",
                street="Willy-Brandt-Platz",
                house_number="2-4",
                postal_code="44787",
                city="Bochum",
                state="Nordrhein-Westfalen",
                email="baulasten@bochum.de",
                source="Stadt Bochum Website (Test)",
                active=True,
            ),
            # Konflikt-Beispiel für MULTIPLE_MATCHES
            Authority(
                authority_id="KONFLIKT_AMT_A",
                authority_name="Amt A (Testkonflikt)",
                street="Teststraße",
                house_number="1",
                postal_code="44789",
                city="Bochum",
                state="Nordrhein-Westfalen",
                source="Testdaten - absichtlicher Konflikt",
                active=True,
            ),
            Authority(
                authority_id="KONFLIKT_AMT_B",
                authority_name="Amt B (Testkonflikt)",
                street="Teststraße",
                house_number="2",
                postal_code="44789",
                city="Bochum",
                state="Nordrhein-Westfalen",
                source="Testdaten - absichtlicher Konflikt",
                active=True,
            ),
            # Amt in Herne, für Kreis/Nachbarstadt-Beispiel
            Authority(
                authority_id="AG_HERNE_001",
                authority_name="Amtsgericht Herne",
                department_name="Grundbuchamt",
                street="Bahnhofstraße",
                house_number="20",
                postal_code="44623",
                city="Herne",
                state="Nordrhein-Westfalen",
                email="grundbuch@ag-herne.nrw.de",
                source="NRW-Justizportal (Test)",
                active=True,
            ),
        ]
        db.add_all(authorities)
        db.commit()

        # ============ Jurisdictions ============
        print("→ Lege Zuständigkeitsregeln an ...")
        jurisdictions = [
            # --- Standard Gemeinde-Zuständigkeit für Bochum (AGS 05911000) ---
            Jurisdiction(
                jurisdiction_id="JUR_001",
                request_type_id="GRUNDBUCH",
                authority_id="AG_BOCHUM_001",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_002",
                request_type_id="BAUAKTEN",
                authority_id="BAUAMT_BOCHUM_001",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_003",
                request_type_id="ALTLASTEN",
                authority_id="UBB_BOCHUM_001",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_004",
                request_type_id="BAULASTEN",
                authority_id="BAULASTEN_BOCHUM",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_005",
                request_type_id="ERSCHLIESSUNG",
                authority_id="ERSCHLIESSUNG_BOCHUM",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_006",
                request_type_id="WASSERSCHUTZ",
                authority_id="WASSER_KREIS_BOCHUM",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_007",
                request_type_id="HOCHWASSERSCHUTZ",
                authority_id="WASSER_KREIS_BOCHUM",
                ags="05911000",
                municipality="Bochum",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),

            # --- Landesweite Zuständigkeiten (Bundesland-Ebene) ---
            Jurisdiction(
                jurisdiction_id="JUR_008",
                request_type_id="DENKMALSCHUTZ",
                authority_id="DENKMAL_LWL_001",
                state="Nordrhein-Westfalen",
                priority=60,
                matching_level="STATE",
                source="Testdaten - Landesweit",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_009",
                request_type_id="BODENDENKMALSCHUTZ",
                authority_id="BODENDENKMAL_LWL_001",
                state="Nordrhein-Westfalen",
                priority=60,
                matching_level="STATE",
                source="Testdaten - Landesweit",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_010",
                request_type_id="KAMPFMITTEL",
                authority_id="KAMPFMITTEL_NRW",
                state="Nordrhein-Westfalen",
                priority=60,
                matching_level="STATE",
                source="Testdaten - Landesweit",
                active=True,
            ),

            # --- Sonderregel auf Straßenebene (überschreibt Gemeinde-Regel!) ---
            # Für die Spezialstraße in Bochum ist beim Grundbuch NICHT das
            # normale Amtsgericht zuständig, sondern eine Sonderstelle.
            Jurisdiction(
                jurisdiction_id="JUR_011",
                request_type_id="GRUNDBUCH",
                authority_id="AG_BOCHUM_SPEZIAL",
                ags="05911000",
                street="Spezialstraße",
                priority=20,
                matching_level="STREET",
                source="Testdaten - Sonderregel Straße",
                notes="Demonstriert: Sonderregel überschreibt Gemeinde-Standardregel",
                active=True,
            ),

            # --- Bewusster Konfliktfall für MULTIPLE_MATCHES (Konfliktweg) ---
            Jurisdiction(
                jurisdiction_id="JUR_012",
                request_type_id="BAUAKTEN",
                authority_id="KONFLIKT_AMT_A",
                ags="05911000",
                street="Konfliktweg",
                priority=20,
                matching_level="STREET",
                source="Testdaten - absichtlicher Konflikt",
                notes="Demonstriert MULTIPLE_MATCHES zusammen mit JUR_013",
                active=True,
            ),
            Jurisdiction(
                jurisdiction_id="JUR_013",
                request_type_id="BAUAKTEN",
                authority_id="KONFLIKT_AMT_B",
                ags="05911000",
                street="Konfliktweg",
                priority=20,
                matching_level="STREET",
                source="Testdaten - absichtlicher Konflikt",
                notes="Demonstriert MULTIPLE_MATCHES zusammen mit JUR_012",
                active=True,
            ),

            # --- Herne: eigene Gemeinde-Zuständigkeit ---
            Jurisdiction(
                jurisdiction_id="JUR_014",
                request_type_id="GRUNDBUCH",
                authority_id="AG_HERNE_001",
                ags="05916000",
                municipality="Herne",
                priority=40,
                matching_level="MUNICIPALITY",
                source="Testdaten - Gemeinde-Standard",
                active=True,
            ),
        ]
        db.add_all(jurisdictions)
        db.commit()

        print("\n✅ Seed-Daten erfolgreich angelegt:")
        print(f"   {len(REQUEST_TYPE_DEFINITIONS)} Auskunftsarten")
        print(f"   {len(buildings)} Testgebäude")
        print(f"   {len(authorities)} Behörden")
        print(f"   {len(jurisdictions)} Zuständigkeitsregeln")
        print("\nTestszenarien:")
        print("   100234 (Musterstraße 12)   -> GRUNDBUCH sollte MATCHED (Gemeinde) sein")
        print("   100235 (Spezialstraße 5)   -> GRUNDBUCH sollte MATCHED (Sonderregel Straße) sein")
        print("   100236 (Konfliktweg 8)     -> BAUAKTEN sollte MULTIPLE_MATCHES sein")
        print("   100237 (Unbekannte Allee)  -> alles sollte NO_MATCH sein")
        print("   100238 (Kortumstraße 100)  -> GRUNDBUCH sollte MATCHED (Gemeinde) sein")
        print("   100239 (Herne)             -> GRUNDBUCH sollte MATCHED (eigenes Amtsgericht) sein")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
