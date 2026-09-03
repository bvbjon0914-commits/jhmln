"""
SQLAlchemy ORM Models: DataSource, DataSourceRouting

Katalog offizieller/offener deutscher Geodaten-Endpunkte (WFS/WMS/OGC API/
Downloads je Bundesland und Kategorie, z.B. ALKIS-Flurstücke, Hochwasser-
/Wasserschutzzonen, Denkmal-Precheck) plus einer Routing-Tabelle, die pro
Bundesland+Kategorie eine empfohlene primäre und Fallback-Quelle nennt.

Bewusst als reine Referenzdaten angelegt: die Tabellen werden befüllt und
sind über die API abrufbar, aber (noch) nicht in die aktive Matching-/
Geocoding-Logik verdrahtet – das wäre eine eigene, größere Feature-
Entscheidung. Grundlage für eine spätere automatisierte Vorab-Prüfung
gegen amtliche Quellen, bevor eine Anfrage bei der Behörde gestellt wird.
"""

from sqlalchemy import Column, String, Boolean, Integer, Date, Text, Index
from app.database.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    source_id = Column(String(100), primary_key=True, nullable=False)

    country = Column(String(10), nullable=True)
    state = Column(String(100), nullable=True)
    state_code = Column(String(10), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    sub_category = Column(String(255), nullable=True)

    provider_name = Column(String(255), nullable=True)
    provider_authority = Column(String(255), nullable=True)

    access_type = Column(String(50), nullable=True)
    endpoint = Column(Text, nullable=True)
    endpoint_mode = Column(String(50), nullable=True)
    feature_collection_or_type = Column(Text, nullable=True)
    preferred_output = Column(String(100), nullable=True)

    license = Column(Text, nullable=True)
    attribution = Column(Text, nullable=True)

    is_open_data = Column(Boolean, nullable=True)
    requires_auth = Column(Boolean, nullable=True)
    requires_fee = Column(Boolean, nullable=True)

    data_status = Column(Text, nullable=True)
    legal_status = Column(String(100), nullable=True)
    priority = Column(Integer, nullable=True)
    fallback_source_id = Column(String(100), nullable=True)
    official_confirmation_required = Column(Boolean, nullable=True)

    last_verified = Column(Date, nullable=True)
    verification_note = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_data_sources_state_category", "state_code", "category"),
    )

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "country": self.country,
            "state": self.state,
            "state_code": self.state_code,
            "category": self.category,
            "sub_category": self.sub_category,
            "provider_name": self.provider_name,
            "provider_authority": self.provider_authority,
            "access_type": self.access_type,
            "endpoint": self.endpoint,
            "endpoint_mode": self.endpoint_mode,
            "feature_collection_or_type": self.feature_collection_or_type,
            "preferred_output": self.preferred_output,
            "license": self.license,
            "attribution": self.attribution,
            "is_open_data": self.is_open_data,
            "requires_auth": self.requires_auth,
            "requires_fee": self.requires_fee,
            "data_status": self.data_status,
            "legal_status": self.legal_status,
            "priority": self.priority,
            "fallback_source_id": self.fallback_source_id,
            "official_confirmation_required": self.official_confirmation_required,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "verification_note": self.verification_note,
            "source_url": self.source_url,
        }


class DataSourceRouting(Base):
    """Pro Bundesland+Kategorie: empfohlene primäre Quelle + Fallback."""

    __tablename__ = "data_source_routing"

    routing_id = Column(Integer, primary_key=True, autoincrement=True)

    state_code = Column(String(10), nullable=False, index=True)
    state = Column(String(100), nullable=True)
    category = Column(String(100), nullable=False, index=True)

    routing_status = Column(String(50), nullable=True)  # AUTO, AUTO_PRECHECK, PARTIAL, ...
    primary_source_id = Column(String(100), nullable=True)
    fallback_source_id = Column(String(100), nullable=True)
    official_confirmation_required = Column(Boolean, nullable=True)
    implementation_note = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_data_source_routing_state_category", "state_code", "category", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "routing_id": self.routing_id,
            "state_code": self.state_code,
            "state": self.state,
            "category": self.category,
            "routing_status": self.routing_status,
            "primary_source_id": self.primary_source_id,
            "fallback_source_id": self.fallback_source_id,
            "official_confirmation_required": self.official_confirmation_required,
            "implementation_note": self.implementation_note,
        }
