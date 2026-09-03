"""
API Routes: Data Sources (Datenquellen-Registry)

Verwaltet den Katalog offizieller/offener deutscher Geodaten-Endpunkte
(z.B. ALKIS-Flurstücke, Hochwasser-/Wasserschutzzonen, Denkmal-Precheck)
sowie die zugehörige Routing-Tabelle (pro Bundesland+Kategorie: empfohlene
primäre Quelle + Fallback). Reine Referenzdaten – wird aktuell nicht in
die Matching-/Geocoding-Logik verdrahtet.
"""

import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.database import get_db_session
from app.models.data_source import DataSource, DataSourceRouting

router = APIRouter()


@router.get("/data-sources", tags=["DataSources"])
def list_data_sources(
    response: Response,
    category: Optional[str] = Query(None),
    state_code: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    query = db.query(DataSource)
    if category:
        query = query.filter(DataSource.category == category)
    if state_code:
        query = query.filter(DataSource.state_code == state_code)

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    rows = query.order_by(DataSource.category, DataSource.state).offset(offset).limit(limit).all()
    return [r.to_dict() for r in rows]


@router.get("/data-sources/categories", tags=["DataSources"])
def list_categories(db: Session = Depends(get_db_session)):
    rows = db.query(DataSource.category).distinct().order_by(DataSource.category).all()
    return [r[0] for r in rows if r[0]]


@router.get("/data-sources/routing", tags=["DataSources"])
def list_routing(
    response: Response,
    category: Optional[str] = Query(None),
    state_code: Optional[str] = Query(None),
    limit: int = Query(300, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    query = db.query(DataSourceRouting)
    if category:
        query = query.filter(DataSourceRouting.category == category)
    if state_code:
        query = query.filter(DataSourceRouting.state_code == state_code)

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    rows = query.order_by(DataSourceRouting.state_code, DataSourceRouting.category).offset(offset).limit(limit).all()
    return [r.to_dict() for r in rows]


def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@router.post("/data-sources/import", tags=["DataSources"])
async def import_data_source_registry(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_main),
):
    """
    Nur Haupt-Account: importiert die Datenquellen-Registry (JSON mit
    "sources"- und "routing"-Listen). Upsert per source_id bzw.
    (state_code, category) – erneutes Ausführen mit einer aktualisierten
    Datei ist also gefahrlos möglich.
    """
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Ungültiges JSON: {exc}")

    sources = data.get("sources", [])
    routing = data.get("routing", [])
    if not sources and not routing:
        raise HTTPException(status_code=400, detail="Datei enthält weder 'sources' noch 'routing'.")

    existing_sources = {s.source_id: s for s in db.query(DataSource).all()}
    sources_created = sources_updated = 0
    for entry in sources:
        source_id = entry.get("source_id")
        if not source_id:
            continue
        fields = {
            "country": entry.get("country"),
            "state": entry.get("state"),
            "state_code": entry.get("state_code"),
            "category": entry.get("category"),
            "sub_category": entry.get("sub_category"),
            "provider_name": entry.get("provider_name"),
            "provider_authority": entry.get("provider_authority"),
            "access_type": entry.get("access_type"),
            "endpoint": entry.get("endpoint"),
            "endpoint_mode": entry.get("endpoint_mode"),
            "feature_collection_or_type": entry.get("feature_collection_or_type"),
            "preferred_output": entry.get("preferred_output"),
            "license": entry.get("license"),
            "attribution": entry.get("attribution"),
            "is_open_data": entry.get("is_open_data"),
            "requires_auth": entry.get("requires_auth"),
            "requires_fee": entry.get("requires_fee"),
            "data_status": entry.get("data_status"),
            "legal_status": entry.get("legal_status"),
            "priority": entry.get("priority"),
            "fallback_source_id": entry.get("fallback_source_id"),
            "official_confirmation_required": entry.get("official_confirmation_required"),
            "last_verified": _parse_date(entry.get("last_verified")),
            "verification_note": entry.get("verification_note"),
            "source_url": entry.get("source_url"),
        }
        existing = existing_sources.get(source_id)
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            sources_updated += 1
        else:
            db.add(DataSource(source_id=source_id, **fields))
            sources_created += 1

    existing_routing = {
        (r.state_code, r.category): r for r in db.query(DataSourceRouting).all()
    }
    routing_created = routing_updated = 0
    for entry in routing:
        state_code = entry.get("state_code")
        category = entry.get("category")
        if not state_code or not category:
            continue
        fields = {
            "state": entry.get("state"),
            "routing_status": entry.get("routing_status"),
            "primary_source_id": entry.get("primary_source_id"),
            "fallback_source_id": entry.get("fallback_source_id"),
            "official_confirmation_required": entry.get("official_confirmation_required"),
            "implementation_note": entry.get("implementation_note"),
        }
        key = (state_code, category)
        existing = existing_routing.get(key)
        if existing:
            for field_key, value in fields.items():
                setattr(existing, field_key, value)
            routing_updated += 1
        else:
            db.add(DataSourceRouting(state_code=state_code, category=category, **fields))
            routing_created += 1

    db.commit()

    return {
        "sources_created": sources_created,
        "sources_updated": sources_updated,
        "routing_created": routing_created,
        "routing_updated": routing_updated,
    }
