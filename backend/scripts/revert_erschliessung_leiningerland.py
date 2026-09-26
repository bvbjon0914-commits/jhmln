"""
Rückt einen einzelnen Fall zurück: Verbandsgemeinde Leiningerland
(ERSCHLIESSUNG, 21 Regeln) wurde ohne offizielle Quelle gestaged/freigegeben
- die einzige Stütze war ein Zeitungsartikel (Die Rheinpfalz), keine
amtliche VG-Seite. Auf ausdrücklichen Nutzer-Entscheid ("Nein, keine
Zeitungsartikel - nur offizielle Quellen zählen") zurückgenommen.

Deaktiviert (active=False) statt zu löschen - dieselbe Historie-bewahren-
Logik wie beim Rest des sicheren Aktualisierungsprozesses: nachvollziehbar,
dass hier etwas versucht und korrekt zurückgenommen wurde, statt spurlos
zu verschwinden. Die Authority-Zeile selbst bleibt bestehen (reale
Organisation, reale Adresse aus dem Anschriftenverzeichnis) - nur die
ERSCHLIESSUNG-Zuständigkeitsregeln werden deaktiviert, falls später eine
echte amtliche Quelle für Leiningerland gefunden wird, kann eine neue,
korrekt belegte Regel ergänzt werden.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AUTHORITY_NAME = "Verbandsgemeindeverwaltung Leiningerland - Fachbereich Finanzen"
REASON = (
    "Zurückgenommen: die einzige Stütze für diese Regel war ein Zeitungsartikel "
    "(Die Rheinpfalz), keine amtliche VG-Quelle - entspricht nicht dem vom Nutzer "
    "bestätigten Sourcing-Standard ('Nein, keine Zeitungsartikel - nur offizielle "
    "Quellen zählen'). Deaktiviert statt gelöscht, um die Historie nachvollziehbar "
    "zu halten."
)


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction

    db = SessionLocal()
    try:
        authority = db.query(Authority).filter(Authority.authority_name == AUTHORITY_NAME).first()
        if authority is None:
            print(f"Authority '{AUTHORITY_NAME}' nicht gefunden - nichts zu tun.")
            return

        rules = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.authority_id == authority.authority_id,
                Jurisdiction.request_type_id == "ERSCHLIESSUNG",
                Jurisdiction.active.is_(True),
            )
            .all()
        )
        for rule in rules:
            rule.active = False
            rule.valid_to = rule.valid_to or datetime.utcnow().date()
            rule.notes = (rule.notes + " " if rule.notes else "") + REASON
        db.commit()
        print(f"{len(rules)} Regeln deaktiviert.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
