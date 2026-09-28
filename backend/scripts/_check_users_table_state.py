# -*- coding: utf-8 -*-
"""READ-ONLY: prueft, ob die bereits (unvollstaendig?) existierende
users-Tabelle in der Ziel-DB vollstaendig ist (alle Spalten + Indizes aus
der Migration f37109f1de46), bevor entschieden wird ob nur gestempelt
werden kann oder erst nachgebessert werden muss. Aendert nichts.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect  # noqa: E402

DATABASE_URL = os.environ["DATABASE_URL"]

EXPECTED_COLUMNS = {
    "user_id", "email", "password_hash", "full_name", "phone", "function",
    "street", "house_number", "postal_code", "city", "is_main", "active",
    "created_at", "updated_at", "last_login_at",
}
EXPECTED_INDEXES = {"idx_users_active", "ix_users_active", "ix_users_email"}


def main():
    engine = create_engine(DATABASE_URL)
    insp = inspect(engine)

    tables = set(insp.get_table_names())
    print(f"users-Tabelle vorhanden: {'JA' if 'users' in tables else 'NEIN'}")
    if "users" not in tables:
        return

    cols = {c["name"] for c in insp.get_columns("users")}
    print(f"\nSpalten vorhanden: {sorted(cols)}")
    missing_cols = EXPECTED_COLUMNS - cols
    extra_cols = cols - EXPECTED_COLUMNS
    print(f"Fehlende Spalten: {sorted(missing_cols) or 'keine'}")
    print(f"Unerwartete Spalten: {sorted(extra_cols) or 'keine'}")

    idx = {i["name"] for i in insp.get_indexes("users")}
    print(f"\nIndizes vorhanden: {sorted(idx)}")
    missing_idx = EXPECTED_INDEXES - idx
    print(f"Fehlende Indizes: {sorted(missing_idx) or 'keine'}")

    pk = insp.get_pk_constraint("users")
    print(f"\nPrimary Key: {pk}")

    print("\n--- Zeilenzahl ---")
    with engine.connect() as conn:
        from sqlalchemy import text
        n = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    print(f"{n} Zeilen (sollte 0 sein, falls noch nie erfolgreich genutzt)")

    if not missing_cols and not missing_idx:
        print("\n=> Tabelle ist VOLLSTAENDIG. Sicher nur zu stempeln (kein erneutes CREATE noetig).")
    else:
        print("\n=> Tabelle ist UNVOLLSTAENDIG. NICHT blind stempeln - erst nachbessern.")


if __name__ == "__main__":
    main()
