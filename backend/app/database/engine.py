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
        # Neon (serverless Postgres) schließt Verbindungen serverseitig nach
        # Inaktivität – ohne pre_ping versucht der Pool dann, eine bereits
        # tote Verbindung wiederzuverwenden ("SSL connection has been closed
        # unexpectedly"). pre_ping testet jede Verbindung vor Gebrauch mit
        # einem leichten SELECT und baut sie bei Bedarf transparent neu auf.
        # pool_recycle erneuert Verbindungen zusätzlich proaktiv, bevor Neons
        # eigenes Idle-Timeout greifen kann.
        pool_pre_ping=True,
        pool_recycle=280,
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

    Seit Einführung von Alembic (backend/alembic/) ist dies bewusst NUR noch
    ein Sicherheitsnetz für eine komplett leere Datenbank (z.B. beim allerersten
    lokalen Start) - create_all() erstellt fehlende Tabellen, ändert aber NIE
    eine bereits existierende Tabelle (keine neue Spalte, keine geänderte
    Constraint). Echte Schemaänderungen ab jetzt IMMER über eine Alembic-
    Migration (`alembic revision --autogenerate` + `alembic upgrade head`),
    nie durch bloßes Ändern eines Modells.

    WICHTIG - einmaliger manueller Schritt vor Produktivnutzung von Alembic:
    Die produktive Datenbank wurde bisher ausschließlich über dieses
    create_all() verwaltet und hat deshalb noch KEINE alembic_version-Tabelle.

    KORREKTES Verfahren (zwei Schritte, NICHT `alembic stamp head`!):

      1. `alembic stamp ab0d36228547` (exakt die Baseline-Revision, die den
         Schemastand von create_all() zum Zeitpunkt ihrer Erstellung
         abbildet) - markiert die DB als "hat die Baseline bereits", ohne
         DDL auszuführen.
      2. `alembic upgrade head` - führt jetzt ALLE seither hinzugekommenen
         echten Migrationen (neue Spalten/Tabellen) tatsächlich als DDL aus.

      `alembic stamp head` (ohne Revision, also der aktuell neueste Stand)
      wäre hier ein Fehler: "head" bewegt sich mit jeder neuen Migration
      weiter, während die Produktivdatenbank nur dem BASELINE-Schema
      entspricht. Ein Stamp direkt auf head würde Alembic fälschlich
      glauben lassen, alle seit der Baseline hinzugekommenen Spalten (z.B.
      InboundEmail.message_id, Building.source_system) existierten bereits
      - ihre DDL würde NIE ausgeführt, und die Anwendung schlägt beim
      ersten Zugriff auf eine dieser tatsächlich fehlenden Spalten fehl.
      Bei jeder neuen Migration muss Schritt 1 weiterhin exakt
      `ab0d36228547` referenzieren, nicht "head".

    Siehe tests/test_migrations.py::TestExistingDatabaseAdoption für das
    getestete Verfahren an einer Kopie. Erfordert Zugriff auf die Neon-
    Produktivdatenbank und wurde hier bewusst NICHT automatisiert oder
    ausgeführt.
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings, AuthorityLocation,
        Case, CaseBuilding, CaseRequest, RequestItemProgress,
        DataSource, DataSourceRouting,
        AktenzeichenSequence, RequestSequence, RequestItemReference,
        InboundEmail, InboundEmailAttachment,
        AuthorityContactChannel, JurisdictionStagingEntry,
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
    Case.metadata.create_all(bind=engine)
    CaseBuilding.metadata.create_all(bind=engine)
    CaseRequest.metadata.create_all(bind=engine)
    RequestItemProgress.metadata.create_all(bind=engine)
    DataSource.metadata.create_all(bind=engine)
    DataSourceRouting.metadata.create_all(bind=engine)
    AktenzeichenSequence.metadata.create_all(bind=engine)
    RequestSequence.metadata.create_all(bind=engine)
    RequestItemReference.metadata.create_all(bind=engine)
    InboundEmail.metadata.create_all(bind=engine)
    InboundEmailAttachment.metadata.create_all(bind=engine)
    AuthorityContactChannel.metadata.create_all(bind=engine)
    JurisdictionStagingEntry.metadata.create_all(bind=engine)

    print("✓ Datenbank initialisiert")


def drop_all_tables():
    """
    Löscht ALLE Tabellen. Nur für Development / Testing!
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings, AuthorityLocation,
        Case, CaseBuilding, CaseRequest, RequestItemProgress,
        DataSource, DataSourceRouting,
        AktenzeichenSequence, RequestSequence, RequestItemReference,
        InboundEmail, InboundEmailAttachment,
        AuthorityContactChannel, JurisdictionStagingEntry,
    )

    JurisdictionStagingEntry.metadata.drop_all(bind=engine)
    AuthorityContactChannel.metadata.drop_all(bind=engine)
    InboundEmailAttachment.metadata.drop_all(bind=engine)
    InboundEmail.metadata.drop_all(bind=engine)
    DataSourceRouting.metadata.drop_all(bind=engine)
    DataSource.metadata.drop_all(bind=engine)
    CaseRequest.metadata.drop_all(bind=engine)
    CaseBuilding.metadata.drop_all(bind=engine)
    Case.metadata.drop_all(bind=engine)
    RequestItemProgress.metadata.drop_all(bind=engine)
    RequestItemReference.metadata.drop_all(bind=engine)
    RequestSequence.metadata.drop_all(bind=engine)
    AktenzeichenSequence.metadata.drop_all(bind=engine)
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
