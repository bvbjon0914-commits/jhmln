"""
Setzt die Datenbank zurück und legt NUR die Auskunftsarten (request_types)
neu an - keine Testgebäude, keine Test-Behörden, keine Test-Zuständigkeiten.
Wird einmalig ausgeführt, bevor echte Daten importiert werden.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, init_db, drop_all_tables
from app.models import RequestType

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
    ("KATASTER", "Liegenschaftskataster-Auskunft", "kataster.docx"),
]


def main():
    print("Loesche bestehende Tabellen und baue sie neu auf ...")
    drop_all_tables()
    init_db()

    db = SessionLocal()
    try:
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
        print(f"OK: {len(REQUEST_TYPE_DEFINITIONS)} Auskunftsarten angelegt, keine Testdaten.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
