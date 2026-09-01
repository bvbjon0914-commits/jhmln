"""
Gemeinsame SQLAlchemy Declarative Base.

ALLE Modelle müssen diese Base verwenden, sonst können sich
Foreign Keys zwischen Tabellen nicht auflösen.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
