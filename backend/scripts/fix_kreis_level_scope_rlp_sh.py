"""
CLI-Wrapper um app.services.kreis_scope_fix - behebt den in dieser Sitzung
diagnostizierten Kreisebenen-Scope-Bug für BAUAKTEN/BAULASTEN in
Rheinland-Pfalz und Schleswig-Holstein.

Siehe app/services/kreis_scope_fix.py für die fachliche Begründung und
tests/test_kreis_scope_fix.py für den Nachweis der Logik an synthetischen
Daten.

Aufruf:
    venv/Scripts/python.exe scripts/fix_kreis_level_scope_rlp_sh.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Struktur-Korrektur 2026-09-26, siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md #4.2)"
STATE_PREFIXES = {"07": "Rheinland-Pfalz", "01": "Schleswig-Holstein"}
REQUEST_TYPES = ["BAUAKTEN", "BAULASTEN"]


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.services.kreis_scope_fix import apply_kreis_scope_fix, find_kreis_scope_bugs

    db = SessionLocal()
    try:
        findings = find_kreis_scope_bugs(db, REQUEST_TYPES, STATE_PREFIXES)
        print(f"{len(findings)} fehlende COUNTY-Regeln identifiziert.")
        for f in findings:
            print(
                f"  {f.request_type_id:10s} Kreis {f.ags_kreis} ({f.state}): "
                f"{f.existing_rule_count}/{f.total_gemeinden} erfasst -> {f.authority_name}"
            )

        if not findings:
            print("Nichts zu tun (bereits behoben oder keine Kandidaten gefunden).")
            return

        result = apply_kreis_scope_fix(db, findings, reviewer=REVIEWER)
        db.commit()

        print(f"\nBatch: {result['batch_id']}")
        print(f"Gestaged: {len(result['staged'])}, freigegeben: {len(result['approved'])}, "
              f"Konflikte (blieben PENDING): {len(result['conflicts'])}")
        for entry, f in result["conflicts"]:
            print(f"  KONFLIKT #{entry.id} {f.request_type_id} Kreis {f.ags_kreis}: "
                  f"{entry.conflict_type} - {entry.conflict_reason}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
