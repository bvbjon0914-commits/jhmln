"""
DENKMALSCHUTZ fuer die kreisfreie Stadt NEUSTADT AN DER WEINSTRASSE
(Rheinland-Pfalz). Eine bundesweite ags-basierte Luecken-Analyse (Kreis-
Ebene, unter Beruecksichtigung sowohl 5-stelliger ags_kreis/COUNTY als
auch 8-stelliger AGS/MUNICIPALITY sowie STATE-Level-Regeln) zeigte:
Rheinland-Pfalz ist bei DENKMALSCHUTZ mit 35 von 36 Kreisen/kreisfreien
Staedten abgedeckt - die einzige Luecke ist Neustadt an der
Weinstrasse.

Rechtsgrundlage: das Denkmalschutzgesetz RLP (DSchG) weist die untere
Denkmalschutzbehoerde den Kreisverwaltungen bzw. den Stadtverwaltungen
der kreisfreien Staedte zu. Die amtliche, aktuelle Liste der unteren
Denkmalschutzbehoerden der Generaldirektion Kulturelles Erbe
Rheinland-Pfalz (GDKE, gdke.rlp.de) bestaetigt konkret: "Stadtverwaltung
Neustadt, Untere Denkmalschutzbehoerde, Rathausstrasse 4, 67434
Neustadt a.d.W." - direkt per Live-Browser-Abruf verifiziert.

1 neue MUNICIPALITY-Regel.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Denkmalschutz-Lücke Neustadt an der Weinstraße)"
NEUSTADT_AGS = "07316000"
GDKE_URL = "https://gdke.rlp.de/wer-wir-sind/landesdenkmalpflege/untere-denkmalschutzbehoerden"
QUOTE = ("Generaldirektion Kulturelles Erbe Rheinland-Pfalz (GDKE), amtliche Liste der unteren "
         "Denkmalschutzbehörden: 'Stadtverwaltung Neustadt, Untere Denkmalschutzbehörde, "
         "Rathausstraße 4, 67434 Neustadt a.d.W.' - das Denkmalschutzgesetz RLP weist die untere "
         "Denkmalschutzbehörde den Kreisverwaltungen bzw. den Stadtverwaltungen der kreisfreien "
         "Städte zu.")


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        authority_name = "Stadtverwaltung Neustadt an der Weinstraße - Untere Denkmalschutzbehörde"
        authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
        if authority is None:
            authority = Authority(
                authority_id=str(uuid.uuid4()), authority_name=authority_name,
                authority_type="Untere Denkmalschutzbehörde (kreisfreie Stadt)",
                street="Rathausstraße 4", house_number=None, postal_code="67434",
                city="Neustadt an der Weinstraße", state="Rheinland-Pfalz", phone=None,
                email="denkmalschutz@neustadt.eu",
                source="Generaldirektion Kulturelles Erbe Rheinland-Pfalz (GDKE), amtliche Liste der "
                       "unteren Denkmalschutzbehörden, " + GDKE_URL,
                active=True,
            )
            db.add(authority)
            db.flush()

        staging = JurisdictionStagingService(db)
        batch_id = f"denkmalschutz-neustadt-weinstrasse-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        entry = staging.stage_entry(
            batch_id=batch_id, batch_label="DENKMALSCHUTZ Neustadt an der Weinstraße",
            request_type_id="DENKMALSCHUTZ", state="Rheinland-Pfalz", ags=NEUSTADT_AGS,
            matching_level=MatchingLevel.MUNICIPALITY, priority=40,
            proposed_authority_id=authority.authority_id,
            source=f"{authority_name} - {QUOTE}", source_url=GDKE_URL,
            source_license="Amtliche Rechtsgrundlage (DSchG RLP) + amtliche GDKE-Liste",
            source_retrieved_at=datetime.utcnow(),
        )
        db.commit()

        print(f"\n1 Eintrag gestaged (Batch {batch_id}).")
        print(f"Konflikt-Typ: {entry.conflict_type}")
        if entry.conflict_type != "NEW":
            print(f"  KONFLIKT #{entry.id} - {entry.conflict_reason}")
            print("\n0 Regeln freigegeben (Konflikt, keine automatische Freigabe).")
        else:
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status="VERIFIED",
            )
            db.commit()
            print("\n1 Regel freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
