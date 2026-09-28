"""
Einmaliger Abgleich: ersetzt die generischen ERSCHLIESSUNG-Regeln fuer
Berlin/Bremen/Bremerhaven/Hamburg (aus dem fruaeheren, in dieser
Sitzung committeten seed_erschliessung_stadtstaaten.py, das nur § 127
BauGB pauschal zitierte) durch die von einer parallelen Session
individuell je Bezirksamt/Amt recherchierten, praeziseren Regeln aus
dem GEMERGTEN seed_erschliessung_stadtstaaten.py (12 Berliner
Bezirksaemter mit wortwoertlichem Zitat je Amt, Bremen/Bremerhaven mit
konkretem Amt, Hamburg mit konkreter Abteilung).

Beide Regelwerke sind fachlich richtig (§ 127 BauGB gilt so oder so),
aber die neue Fassung ist praeziser (benannte Fachbehoerde statt
"Gemeindeverwaltung") und fuer Berlin konsistent mit dem in dieser DB
bereits etablierten 12-Bezirke-Muster (BAUAKTEN/BAULASTEN/KATASTER).
Die alten Regeln werden NICHT geloescht, sondern regulaer ueber
JurisdictionStagingService.approve_entry() abgeloest (valid_to wird
gesetzt, Historie bleibt erhalten) - identisch zum Standard-Konflikt-
Mechanismus dieser Codebase, nur dass hier bewusst auch
CONTRADICTS_VERIFIED-Konflikte freigegeben werden (nicht nur NEW),
weil dies eine reviewte, gewollte Ablösung ist, keine versehentliche
Ueberschreibung.

Importiert die ENTRIES-Liste direkt aus seed_erschliessung_stadtstaaten.py,
um keine Daten zu duplizieren.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Abgleich Erschließung Stadtstaaten nach Merge)"


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
    from seed_erschliessung_stadtstaaten import BERLIN_PATTERN_NOTE, ENTRIES

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"reconcile-erschliessung-stadtstaaten-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for item in ENTRIES:
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == item["authority_name"], Authority.city == item["city"])
                .first()
            )
            if authority is None:
                import uuid
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=item["authority_name"],
                    authority_type="Kommunale Beitragsstelle",
                    street=item["street"], house_number=None, postal_code=item["plz"], city=item["city"],
                    state=item["state"], phone=None, email=None,
                    source="Amtliche Quelle, recherchiert 2026-09-28: " + item["source_url"],
                    active=True,
                )
                db.add(authority)
                db.flush()

            note_parts = []
            if item["state"] == "Berlin":
                note_parts.append(BERLIN_PATTERN_NOTE)
            note_parts.append(item["quote"])

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Abgleich Erschließung Stadtstaaten - {item['authority_name']}",
                request_type_id="ERSCHLIESSUNG", state=item["state"], ags=item["ags"],
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{item['authority_name']} - {item['quote']}", source_url=item["source_url"],
                source_license="Amtliche Webseite (berlin.de / asv.bremen.de / bremerhaven.de / hamburg.de)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, " ".join(note_parts)))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        for c, _ in staged:
            print(f"  #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        # Bewusst ALLE Eintraege freigeben (auch CONTRADICTS_VERIFIED) - reviewte
        # Ablösung der generischen §127-BauGB-Sammelregel durch die praeziseren,
        # einzeln recherchierten Regeln. DUPLICATE_EXACT waere ein Fehler hier,
        # da die Authority-Namen sich unterscheiden - wird also nicht erwartet.
        approved = 0
        for entry, note in staged:
            if entry.conflict_type == "DUPLICATE_EXACT":
                print(f"  ÜBERSPRUNGEN (exaktes Duplikat) #{entry.id}")
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=note,
                resulting_verification_status="VERIFIED",
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben (alte widersprochene Regeln automatisch abgelöst/valid_to gesetzt).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
