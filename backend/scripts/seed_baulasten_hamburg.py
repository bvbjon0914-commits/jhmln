"""
BAULASTENAUSKUNFT fuer HAMBURG. Anders als die allgemeine
Bauaktenauskunft (die in Hamburg bezirklich bei den 7 Bezirksaemtern
liegt und - wie bei Berlin - strukturell nicht ohne Bezirks-Granularitaet
in den Gebaeudedaten sauber zugeordnet werden kann, daher bewusst OHNE
Skript) ist die Baulastenverzeichnis-Auskunft in Hamburg ZENTRALISIERT
beim Landesbetrieb Geoinformation und Vermessung (LGV), unabhaengig von
der bezirklichen Bauaufsichtsstruktur. Rechtsgrundlage: § 83
Hamburgische Bauordnung (HBauO) - Baulasten, Baulastenverzeichnis;
amtlich bestaetigt ueber die offizielle Hamburg-Serviceseite
(hamburg.de/service/info/111092794/). Eintragung/Loeschung von
Baulasten bleibt zwar bei der Bauprruefstelle des jeweiligen
Bezirksamts, die AUSKUNFT aus dem Verzeichnis erfolgt aber zentral
beim LGV.

1 neue STATE-Regel (Hamburg als Ganzes, kein Landkreis-Konzept im
Stadtstaat).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Baulastenauskunft Hamburg)"
LGV_URL = "https://www.hamburg.de/service/info/111092794/"
QUOTE = ("§ 83 HBauO (Baulasten, Baulastenverzeichnis). Offizielle Serviceseite hamburg.de: die "
         "Baulastenverzeichnis-Auskunft wird zentral beim Landesbetrieb Geoinformation und "
         "Vermessung (LGV), Abteilung 'B 3 Liegenschaftsdaten', erteilt - unabhängig von der "
         "bezirklichen Bauaufsichtsstruktur. Eintragung/Löschung bleibt bei der Bauprüfstelle des "
         "jeweiligen Bezirksamts.")
LGV_NAME = "Landesbetrieb Geoinformation und Vermessung (LGV) - Abteilung B3 Liegenschaftsdaten (Baulastenverzeichnis)"


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
        authority = db.query(Authority).filter(Authority.authority_name == LGV_NAME).first()
        if authority is None:
            authority = Authority(
                authority_id=str(uuid.uuid4()), authority_name=LGV_NAME,
                authority_type="Zentrale Baulastenbehörde (Stadtstaat)",
                street="Neuenfelder Straße 19", house_number=None, postal_code="21109", city="Hamburg",
                state="Hamburg", phone="040 42826-5720", email="lgvalkis-hilfe@gv.hamburg.de",
                source=f"Amtliche Quelle, recherchiert 2026-09-28: {LGV_URL}",
                active=True,
            )
            db.add(authority)
            db.flush()

        staging = JurisdictionStagingService(db)
        batch_id = f"baulasten-hamburg-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        entry = staging.stage_entry(
            batch_id=batch_id, batch_label="Baulasten Hamburg",
            request_type_id="BAULASTEN", state="Hamburg", ags="02000",
            matching_level=MatchingLevel.COUNTY, priority=50,
            proposed_authority_id=authority.authority_id,
            source=f"{LGV_NAME} - {QUOTE}", source_url=LGV_URL,
            source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
            source_retrieved_at=datetime.utcnow(),
        )
        db.commit()

        print(f"\n1 Eintrag gestaged (Batch {batch_id}).")
        print(f"Konflikt-Typ: {entry.conflict_type}")
        if entry.conflict_type != "NEW":
            print(f"  KONFLIKT: {entry.conflict_reason}")
            return

        staging.approve_entry(
            entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
            resulting_verification_status="VERIFIED",
        )
        db.commit()
        print("1 Regel freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
