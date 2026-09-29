# -*- coding: utf-8 -*-
"""
Legt GENAU EINE Jurisdiction-Zeile an, die BAULASTEN fuer ganz Bayern
explizit als "nicht vorhanden" markiert (authority_id=NULL, matching_level=
STATE) - siehe MatchingStatus.NOT_APPLICABLE in
app/services/jurisdiction_matcher.py.

Root Cause / Beleg (siehe auch docs/ABSCHLUSSBERICHT_DATENQUALITAET.md):
Bayern kennt laut Art. 53 BayBO (Bayerische Bauordnung) ueberhaupt kein
Baulastenverzeichnis-Konzept - eine echte, bundeslandweite strukturelle
Nicht-Existenz, keine Datenluecke. Der volle nationale Coverage-Report
(118.239 Gemeinde x Auskunftsart-Kombinationen) zeigte dafuer exakt 2055
NO_MATCH-Faelle (alle 2056 bayerischen Gemeinden ausser Monheim, das bereits
eine eigene, korrekte MUNICIPALITY-Ausnahme-Regel hat - diese bleibt
unangetastet, da MUNICIPALITY vor STATE geprueft wird).

STATE ist die vorletzte Matching-Stufe (vor POSTAL_CODE) - diese eine Zeile
deckt automatisch alle betroffenen Gemeinden ab, ohne 2055 Einzelzeilen
anzulegen.

Idempotent: bricht ab, wenn bereits eine aktive BAULASTEN/Bayern/STATE-Regel
existiert (auch eine MATCHED-Regel mit echter Behoerde - dann waere diese
Zeile falsch und muesste manuell geprueft werden statt hier automatisch
angelegt zu werden).
"""
import os
import sys
import uuid
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.jurisdiction import Jurisdiction  # noqa: E402

REQUEST_TYPE_ID = "BAULASTEN"
STATE = "Bayern"
PRIORITY = 60  # gleiche Prioritaet wie bestehende STATE-Fallback-Regeln (z.B. Kampfmittelraeumdienst-Landesregeln)
NOTES = (
    "NOT_APPLICABLE: Bayern kennt gemaess Art. 53 BayBO (Bayerische Bauordnung) "
    "kein Baulastenverzeichnis - strukturell nicht vorhanden, keine Datenluecke. "
    "Siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md. Die einzige Ausnahme "
    "(Monheim, ags=09779186) hat eine eigene, unveraenderte MUNICIPALITY-Regel."
)


def main() -> None:
    db = SessionLocal()
    try:
        existing = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == REQUEST_TYPE_ID,
                Jurisdiction.state == STATE,
                Jurisdiction.matching_level == "STATE",
                Jurisdiction.active.is_(True),
            )
            .first()
        )
        if existing:
            print(
                f"Bereits vorhanden: jurisdiction_id={existing.jurisdiction_id} "
                f"(authority_id={existing.authority_id}) - Abbruch, nichts angelegt."
            )
            return

        row = Jurisdiction(
            jurisdiction_id=str(uuid.uuid4()),
            request_type_id=REQUEST_TYPE_ID,
            authority_id=None,
            country="DE",
            state=STATE,
            ags=None,
            municipality=None,
            matching_level="STATE",
            priority=PRIORITY,
            valid_from=date.today(),
            valid_to=None,
            source="Interne Struktur-Korrektur: NOT_APPLICABLE-Feature",
            verification_status="VERIFIED",
            last_verified_at=datetime.utcnow(),
            verified_by="Claude (Struktur-Korrektur, Art. 53 BayBO)",
            active=True,
            notes=NOTES,
        )
        db.add(row)
        db.commit()
        print(f"Angelegt: jurisdiction_id={row.jurisdiction_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
