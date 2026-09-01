"""
SQLAlchemy ORM Model: AdministrativeUnit

Bildet die offizielle AGS-Hierarchie ab (Destatis-Gemeindeverzeichnis).
Wird für Landkreis- und Bundesland-Fallback im Matching benötigt
(Matching-Stufe 5 und 6).

AGS-Struktur (8-stellig):
    Land (2)  + Regierungsbezirk (1) + Kreis (2) + Gemeinde (3)
    z.B. 05    9                       1           1000
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from app.database.base import Base


class AdministrativeUnit(Base):
    """
    Referenztabelle: Offizielle Gemeinde-/Kreis-/Länderstruktur.
    
    Primary Key: ags (8-stellig, eindeutig pro Gemeinde)
    
    Diese Tabelle wird per Import aus dem Destatis-Gemeindeverzeichnis
    befüllt und NICHT manuell gepflegt.
    """
    
    __tablename__ = "administrative_units"

    # Primary Key: vollständiger AGS (8-stellig)
    ags = Column(String(8), primary_key=True, nullable=False)

    # ========== AGS-Bestandteile (aus dem Schlüssel abgeleitet) ==========

    ags_land = Column(String(2), nullable=False, index=True)          # Bundesland-Code
    ags_regierungsbezirk = Column(String(1), nullable=True)           # Regierungsbezirk (nicht in allen Bundesländern)
    ags_kreis = Column(String(5), nullable=False, index=True)         # Land+RB+Kreis (5-stellig) = Landkreis-Schlüssel
    ags_gemeinde = Column(String(3), nullable=False)                  # Gemeindeteil (3-stellig)

    # ========== Klartext-Namen ==========

    state_name = Column(String(100), nullable=False, index=True)      # z.B. "Nordrhein-Westfalen"
    county_name = Column(String(150), nullable=True, index=True)      # Landkreis / kreisfreie Stadt
    municipality_name = Column(String(150), nullable=False, index=True)  # Gemeindename

    # Gemeindetyp (z.B. "kreisfreie Stadt", "kreisangehörige Gemeinde")
    municipality_type = Column(String(100), nullable=True)

    # ========== Zusatzinfo aus dem Gemeindeverzeichnis ==========

    area_km2 = Column(Float, nullable=True)           # Fläche in km²
    population = Column(Integer, nullable=True)        # Einwohnerzahl

    # Optional, falls in der Quelldatei vorhanden (nicht immer der Fall!)
    postal_code = Column(String(10), nullable=True, index=True)

    # ========== Metadaten ==========

    source = Column(String(255), default="Destatis Gemeindeverzeichnis")
    data_stand = Column(String(20), nullable=True)     # z.B. "31.12.2025" – Stichtag der Quelldatei
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_admin_units_kreis', 'ags_kreis'),
        Index('idx_admin_units_land', 'ags_land'),
        Index('idx_admin_units_municipality_name', 'municipality_name'),
        Index('idx_admin_units_postal_code', 'postal_code'),
    )

    def __repr__(self):
        return (
            f"<AdministrativeUnit(ags={self.ags}, "
            f"municipality={self.municipality_name}, "
            f"county={self.county_name}, state={self.state_name})>"
        )

    @staticmethod
    def parse_ags(ags: str) -> dict:
        """
        Zerlegt einen 8-stelligen AGS in seine Bestandteile.
        
        Beispiel: "05911000"
            -> land="05", rb="9", kreis="05911", gemeinde="000"
        
        Hinweis: Nicht alle Bundesländer nutzen die RB-Stelle
        (z.B. Bayern, Baden-Württemberg schon; Nordrhein-Westfalen
        historisch auch, andere Länder haben hier "0").
        """
        if not ags or len(ags) != 8 or not ags.isdigit():
            raise ValueError(f"Ungültiger AGS: '{ags}' (muss 8-stellig numerisch sein)")

        return {
            "ags_land": ags[0:2],
            "ags_regierungsbezirk": ags[2:3],
            "ags_kreis": ags[0:5],
            "ags_gemeinde": ags[5:8],
        }

    def to_dict(self) -> dict:
        return {
            "ags": self.ags,
            "ags_land": self.ags_land,
            "ags_kreis": self.ags_kreis,
            "state_name": self.state_name,
            "county_name": self.county_name,
            "municipality_name": self.municipality_name,
            "municipality_type": self.municipality_type,
            "area_km2": self.area_km2,
            "population": self.population,
            "postal_code": self.postal_code,
            "data_stand": self.data_stand,
        }
