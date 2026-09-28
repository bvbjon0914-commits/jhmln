import os
import ssl
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, engine_from_config
from sqlalchemy import pool

from alembic import context

# Damit "from app...." unabhängig vom Arbeitsverzeichnis funktioniert, in dem
# `alembic` aufgerufen wird (z.B. auch aus dem Projekt-Root heraus).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dieselbe DATABASE_URL-Auflösung wie die Anwendung selbst (app/database/
# engine.py): Alembic soll IMMER gegen die Datenbank arbeiten, die die App
# beim Start auch tatsächlich verwendet - nie eine in alembic.ini fest
# hinterlegte, u.U. veraltete URL. Kein Fallback auf Produktionswerte: ohne
# gesetzte DATABASE_URL greift derselbe SQLite-Default wie in der App.
from app.database.engine import DATABASE_URL  # noqa: E402
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Alle Modelle importieren, damit sie auf Base.metadata registriert sind,
# bevor Autogenerate die Metadaten mit der Datenbank vergleicht.
from app.database.base import Base  # noqa: E402
from app.models import (  # noqa: E402,F401
    Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
    AdministrativeUnit, AppSettings, AuthorityLocation,
    Case, CaseBuilding, CaseRequest, RequestItemProgress,
    DataSource, DataSourceRouting,
    AktenzeichenSequence, RequestSequence, RequestItemReference,
    InboundEmail, InboundEmailAttachment,
    AuthorityContactChannel, JurisdictionStagingEntry,
    User,
)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.get_main_option("sqlalchemy.url")
    if url.startswith("postgresql+pg8000://"):
        # pg8000 (reiner Python-Treiber, keine kompilierten DLLs - Workaround
        # fuer Windows-Rechner ohne funktionierendes psycopg2-binary-Wheel)
        # kennt "sslmode"/"ssl_context=true" als URL-Query-Parameter NICHT;
        # diese SQLAlchemy-Version (2.0.52) wandelt das auch nicht automatisch
        # um (opts.update(url.query) reicht den rohen String durch). Deshalb
        # hier ein echtes ssl.SSLContext-Objekt per connect_args uebergeben,
        # statt sich auf engine_from_config()/die URL allein zu verlassen.
        # Betrifft NUR den pg8000-Sonderfall - Produktion (Linux/Render) nutzt
        # weiterhin ganz normal postgresql:// mit psycopg2.
        connectable = create_engine(
            url, poolclass=pool.NullPool,
            connect_args={"ssl_context": ssl.create_default_context()},
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite kann die meisten ALTER-TABLE-Varianten (Spalte umbenennen/
            # löschen, Constraint ändern) nicht direkt - Alembics Batch-Modus
            # baut die Tabelle dafür transparent neu statt in-place zu ändern.
            # Für Postgres (Produktion) ist das ein No-Op, dort läuft ALTER
            # TABLE direkt.
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
