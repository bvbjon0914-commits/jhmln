"""
Wendet den bereits getesteten Kreisebenen-Scope-Fix (siehe
app/services/kreis_scope_fix.py, ursprünglich für RLP/SH entwickelt -
scripts/fix_kreis_level_scope_rlp_sh.py) BUNDESWEIT an, für alle 16
Bundesländer statt nur RLP/SH.

Befund (Auftrag: "konzentriere dich auf NO_MATCH deutschlandweit"):
außerhalb RLP/SH wurden 44 weitere Fälle desselben Musters gefunden -
eine Kreisverwaltung/ein Landkreis ist bereits als Behörde korrekt in der
Datenbank vorhanden, ihre einzige Regel ist aber fälschlich auf eine
einzelne, willkürliche Gemeinde-AGS gepinnt statt auf den Kreis-Schlüssel.
Betrifft Brandenburg, Mecklenburg-Vorpommern, Niedersachsen und
Sachsen-Anhalt, ausschließlich BAUAKTEN/BAULASTEN - 2.462 Gemeinden.

Keine neue externe Recherche nötig - dieselbe Behörde, nur die
Geltungsbereichs-EBENE der bestehenden Regel wird korrigiert (identischer
Mechanismus wie beim RLP/SH-Fix, nur bundesweit statt regional
eingegrenzt).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Struktur-Korrektur 2026-09-26, bundesweite Ausweitung des RLP/SH-Kreisebenen-Fixes)"
STATE_PREFIXES = {
    "01": "Schleswig-Holstein", "02": "Hamburg", "03": "Niedersachsen", "04": "Bremen",
    "05": "Nordrhein-Westfalen", "06": "Hessen", "07": "Rheinland-Pfalz", "08": "Baden-Württemberg",
    "09": "Bayern", "10": "Saarland", "11": "Berlin", "12": "Brandenburg",
    "13": "Mecklenburg-Vorpommern", "14": "Sachsen", "15": "Sachsen-Anhalt", "16": "Thüringen",
}
REQUEST_TYPES_DEFAULT = None  # None = alle aktiven Auskunftsarten prüfen


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.request_type import RequestType
    from app.services.kreis_scope_fix import apply_kreis_scope_fix, find_kreis_scope_bugs

    db = SessionLocal()
    try:
        request_types = REQUEST_TYPES_DEFAULT or [
            r.request_type_id for r in db.query(RequestType).filter(RequestType.active.is_(True)).all()
        ]
        findings = find_kreis_scope_bugs(db, request_types, STATE_PREFIXES)
        # RLP/SH wurden bereits in einem früheren Durchlauf behoben (idempotent-check
        # in find_kreis_scope_bugs schließt sie ohnehin aus, falls schon erledigt).
        print(f"{len(findings)} Kandidaten gefunden (alle 16 Länder).")
        by_state = {}
        for f in findings:
            by_state[f.state] = by_state.get(f.state, 0) + (f.total_gemeinden - f.existing_rule_count)
        for state, n in sorted(by_state.items(), key=lambda x: -x[1]):
            print(f"  {state}: {n} betroffene Gemeinden")

        if not findings:
            print("Nichts zu tun.")
            return

        result = apply_kreis_scope_fix(db, findings, reviewer=REVIEWER)
        db.commit()

        print(f"\nBatch: {result['batch_id']}")
        print(f"Gestaged: {len(result['staged'])}, freigegeben: {len(result['approved'])}, "
              f"Konflikte (blieben PENDING): {len(result['conflicts'])}")
        for entry, f in result["conflicts"]:
            print(f"  KONFLIKT #{entry.id} {f.request_type_id} Kreis {f.ags_kreis} ({f.state}): "
                  f"{entry.conflict_type} - {entry.conflict_reason}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
