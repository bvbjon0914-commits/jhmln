"""
Einmaliges Migrationsskript: kopiert alle Daten aus der lokalen SQLite-DB
in eine PostgreSQL-Zieldatenbank (z.B. Neon), in FK-sicherer Reihenfolge.

Aufruf:
    python scripts/migrate_to_postgres.py "postgresql+psycopg://user:pass@host/db"

Die Ziel-URL wird NICHT gespeichert, nur als Kommandozeilenargument übergeben.
"""

import sys

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.database.base import Base
from app.models import (
    RequestType, AdministrativeUnit, Authority, Building,
    Jurisdiction, Request, RequestItem, AppSettings,
)

# Reihenfolge wichtig: erst Tabellen ohne Fremdschlüssel-Abhängigkeiten
MODELS_IN_ORDER = [
    RequestType, AdministrativeUnit, Authority, Building,
    Jurisdiction, Request, RequestItem, AppSettings,
]

BATCH_SIZE = 1000


def main():
    if len(sys.argv) != 2:
        print("Nutzung: python scripts/migrate_to_postgres.py <postgres-url>")
        sys.exit(1)

    target_url = sys.argv[1]
    if target_url.startswith("postgresql://"):
        target_url = target_url.replace("postgresql://", "postgresql+psycopg://", 1)

    src_db = SessionLocal()
    target_engine = create_engine(target_url)
    TargetSession = sessionmaker(bind=target_engine)
    dst_db = TargetSession()

    print("→ Erstelle Tabellen in der Zieldatenbank (falls noch nicht vorhanden) …")
    Base.metadata.create_all(bind=target_engine)

    for model in MODELS_IN_ORDER:
        rows = src_db.query(model).all()
        columns = [c.name for c in model.__table__.columns]
        data = [{col: getattr(row, col) for col in columns} for row in rows]

        if not data:
            print(f"  {model.__tablename__}: 0 Zeilen (übersprungen)")
            continue

        existing = dst_db.query(model).count()
        if existing > 0:
            print(f"  {model.__tablename__}: Ziel hat bereits {existing} Zeilen, überspringe.")
            continue

        for i in range(0, len(data), BATCH_SIZE):
            batch = data[i : i + BATCH_SIZE]
            dst_db.execute(insert(model.__table__), batch)
        dst_db.commit()
        print(f"  {model.__tablename__}: {len(data)} Zeilen übertragen.")

    src_db.close()
    dst_db.close()
    print("✓ Migration abgeschlossen.")


if __name__ == "__main__":
    main()
