"""
Repliziert in die Ziel-DB (z.B. den Hauptcheckout) den Saarlouis-Fix, der
in einem anderen, parallelen Worktree (.claude/worktrees/youthful-wozniak-
d0a66f) bereits recherchiert, angewendet und dort per Cross-Session-
Nachricht bestaetigt wurde. Kein eigenstaendiger neuer Fund - die
inhaltliche Pruefung/Quellenarbeit fuer diesen Fall liegt in jener
Session, hier wird nur derselbe, bereits abgeschlossene Fix in eine zweite
lokale DB-Kopie uebertragen (authority_matching.db ist pro Checkout
gitignored, keine automatische Synchronisation).

Bestaetigter Inhalt der anderen Session (Nachricht vom 2026-09-28):
- jurisdiction_id 7aeee253-12a2-41df-aeca-93d3b3ceba9d (BAUAKTEN) und
  d203c96f-e809-4dc1-a389-bcb602df53d2 (BAULASTEN): "Landkreis Saarlouis
  - Untere Bauaufsichtsbehoerde" (authority_id a67bc5f9), faelschlich auf
  MUNICIPALITY/10044115 (AGS der Kreisstadt) gepinnt statt auf die
  bereits vorhandene COUNTY-Regel (ags=10044, authority_id 24a9ff6b,
  Quelle "Amtliches Anschriftenverzeichnis der Gemeinde- und
  Stadtverwaltungen"). valid_to=2026-09-27 gesetzt, active bleibt True
  (Abloese-Konvention, siehe jurisdiction_staging.py) - identischer
  Bugtyp wie beim hier parallel bearbeiteten Neunkirchen/Merzig-Wadern/
  St.-Wendel-Fix (fix_saarland_bauaufsicht_kreisweite_duplikate.py).
- Kreisstadt Saarlouis (217c6f3e.../6baee516..., MUNICIPALITY/10044115)
  unangetastet - korrekt, bleibt aktiv.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "claude-data-quality-session (Replikat aus Peer-Worktree youthful-wozniak-d0a66f)"
EXPIRY = date(2026, 9, 27)

JURISDICTION_IDS_TO_EXPIRE = {
    "7aeee253-12a2-41df-aeca-93d3b3ceba9d": (
        "Abgeloest (repliziert aus Peer-Worktree youthful-wozniak-d0a66f, dort am 2026-09-28 "
        "angewendet): kreisweite Behoerde 'Landkreis Saarlouis - Untere Bauaufsichtsbehoerde' "
        "(authority_id a67bc5f9) war faelschlich auf die Gemeinde-AGS der Kreisstadt (10044115) "
        "statt auf die Kreis-AGS (10044, matching_level=COUNTY) gescoped. Die korrekte COUNTY-Regel "
        "existiert bereits (authority_id 24a9ff6b, Quelle Amtliches Anschriftenverzeichnis)."
    ),
    "d203c96f-e809-4dc1-a389-bcb602df53d2": (
        "Abgeloest: siehe Begruendung fuer BAUAKTEN-Regel 7aeee253 (identischer Fall, BAULASTEN "
        "statt BAUAKTEN)."
    ),
}


def main(dry_run: bool = True):
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")
    print(f"Modus: {'DRY-RUN (keine Aenderungen werden gespeichert)' if dry_run else 'APPLY'}")

    from sqlalchemy import text
    from app.database.engine import SessionLocal
    from app.models.jurisdiction import Jurisdiction

    db = SessionLocal()
    # Ziel-DB wird gerade parallel von anderen Sessions beschrieben - statt beim
    # ersten Lock-Konflikt sofort zu scheitern, bis zu 30s auf die Sperre warten.
    db.execute(text("PRAGMA busy_timeout=30000"))
    try:
        found = 0
        for jurisdiction_id, reason in JURISDICTION_IDS_TO_EXPIRE.items():
            rule = db.query(Jurisdiction).filter(
                Jurisdiction.jurisdiction_id == jurisdiction_id
            ).first()
            if rule is None:
                print(f"WARNUNG: Regel {jurisdiction_id} nicht gefunden - uebersprungen.")
                continue
            if rule.valid_to is not None and rule.valid_to <= EXPIRY:
                print(f"WARNUNG: Regel {jurisdiction_id} ist bereits abgelaufen - uebersprungen.")
                continue
            found += 1
            print(
                f"  {rule.request_type_id:9} ags={rule.ags:10} lvl={rule.matching_level} "
                f"authority_id={rule.authority_id} -> wird abgeloest (valid_to={EXPIRY})"
            )
            rule.valid_to = EXPIRY
            rule.notes = (rule.notes + " " if rule.notes else "") + reason
            rule.verified_by = REVIEWER

        if dry_run:
            db.rollback()
            print(f"\nDRY-RUN: {found} Regel(n) waeren abgeloest worden. Keine Aenderung gespeichert.")
        else:
            db.commit()
            print(f"\n{found} Regel(n) abgeloest und gespeichert.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(dry_run=not apply_changes)
