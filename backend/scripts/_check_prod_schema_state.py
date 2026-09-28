# -*- coding: utf-8 -*-
"""READ-ONLY: inspects the live DATABASE_URL schema (columns/tables) to
determine which Alembic revision it actually matches, so we know where to
`alembic stamp` before running `alembic upgrade head`. Does NOT modify
anything - only SELECT/information_schema queries via SQLAlchemy inspect().
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text  # noqa: E402

DATABASE_URL = os.environ["DATABASE_URL"]


def main():
    engine = create_engine(DATABASE_URL)
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    print(f"Tabellen gesamt: {len(tables)}")

    def cols(table):
        if table not in tables:
            return None
        return {c["name"] for c in insp.get_columns(table)}

    # Checks in Reihenfolge der Migrationskette:
    print("\n--- ab0d36228547 (baseline): erwartete Kern-Tabellen vorhanden? ---")
    for t in ["administrative_units", "authorities", "buildings", "jurisdictions",
              "requests", "request_items", "inbound_emails", "cases"]:
        print(f"  {t}: {'OK' if t in tables else 'FEHLT'}")

    print("\n--- 53a6c1a1c9f7 (inbound_emails.message_id fuer Webhook) ---")
    ie_cols = cols("inbound_emails")
    if ie_cols is not None:
        print(f"  message_id vorhanden: {'JA' if 'message_id' in ie_cols else 'NEIN'}")
    else:
        print("  inbound_emails Tabelle fehlt komplett")

    print("\n--- 8bf5a88f4024 (buildings.source_system) ---")
    b_cols = cols("buildings")
    if b_cols is not None:
        print(f"  source_system vorhanden: {'JA' if 'source_system' in b_cols else 'NEIN'}")
    else:
        print("  buildings Tabelle fehlt komplett")

    print("\n--- 30bb4888018f (Quellennachweis/Kontaktwege/Staging - DAS WOLLEN WIR ANWENDEN) ---")
    j_cols = cols("jurisdictions")
    if j_cols is not None:
        for c in ["source_url", "source_license", "source_retrieved_at", "verification_status"]:
            print(f"  jurisdictions.{c}: {'JA (schon da!)' if c in j_cols else 'nein'}")
    print(f"  Tabelle authority_contact_channels existiert schon: "
          f"{'JA' if 'authority_contact_channels' in tables else 'nein'}")
    print(f"  Tabelle jurisdiction_staging_entries existiert schon: "
          f"{'JA' if 'jurisdiction_staging_entries' in tables else 'nein'}")

    print("\n--- alembic_version Tabelle ---")
    if "alembic_version" in tables:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        print(f"  vorhanden, Inhalt: {rows}")
    else:
        print("  existiert nicht (nie mit Alembic gestempelt)")

    print("\n--- jurisdictions Zeilenzahl (zur Orientierung) ---")
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM jurisdictions")).scalar()
    print(f"  {n} Zeilen")


if __name__ == "__main__":
    main()
