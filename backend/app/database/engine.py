"""
SQLAlchemy Engine und Session Management
Unterstützt SQLite (MVP) und PostgreSQL (Production)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Umgebungsvariablen für Datenbankverbindung
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./authority_matching.db"
)

# SQLite für MVP
if DATABASE_URL.startswith("sqlite://"):
    # WICHTIG: kein StaticPool hier! StaticPool zwingt ALLE Sessions auf eine
    # einzige physische Verbindung – das ist nur für :memory:-Datenbanken
    # nötig (die sonst pro Verbindung neu/leer wären). Bei der Datei-DB führt
    # das dazu, dass gleichzeitige Requests (z.B. Matching für mehrere
    # Gebäude parallel) sich denselben Cursor teilen und mit kryptischen
    # SQLAlchemy-Fehlern kollidieren. Der Standard-Pool erzeugt bei Bedarf
    # separate Verbindungen; SQLite regelt die Nebenläufigkeit dann selbst
    # über Datei-Locking.
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
# PostgreSQL für Production
else:
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=10,
        max_overflow=20,
    )

# SessionLocal für Dependency Injection
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db_session() -> Session:
    """
    Erzeugt eine neue Datenbankverbindung.
    Wird als FastAPI Dependency verwendet.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialisiert die Datenbank.
    Erstellt alle Tabellen basierend auf den ORM-Modellen.
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings, AuthorityLocation,
    )

    # Metadaten aller Models
    Building.metadata.create_all(bind=engine)
    RequestType.metadata.create_all(bind=engine)
    Authority.metadata.create_all(bind=engine)
    Jurisdiction.metadata.create_all(bind=engine)
    Request.metadata.create_all(bind=engine)
    RequestItem.metadata.create_all(bind=engine)
    AdministrativeUnit.metadata.create_all(bind=engine)
    AppSettings.metadata.create_all(bind=engine)
    AuthorityLocation.metadata.create_all(bind=engine)

    print("✓ Datenbank initialisiert")


def drop_all_tables():
    """
    Löscht ALLE Tabellen. Nur für Development / Testing!
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings, AuthorityLocation,
    )

    Building.metadata.drop_all(bind=engine)
    RequestType.metadata.drop_all(bind=engine)
    Authority.metadata.drop_all(bind=engine)
    Jurisdiction.metadata.drop_all(bind=engine)
    Request.metadata.drop_all(bind=engine)
    RequestItem.metadata.drop_all(bind=engine)
    AdministrativeUnit.metadata.drop_all(bind=engine)
    AuthorityLocation.metadata.drop_all(bind=engine)
    AppSettings.metadata.drop_all(bind=engine)

    print("⚠ Alle Tabellen gelöscht!")
