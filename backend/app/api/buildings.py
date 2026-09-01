"""
API Routes: Buildings
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db_session
from app.models.building import Building
from app.models.request import Request
from app.schemas import BuildingCreate, BuildingResponse, BuildingUpdate

router = APIRouter()


@router.get("/buildings", response_model=List[BuildingResponse], tags=["Buildings"])
def list_buildings(
    response: Response,
    search: Optional[str] = Query(None, description="Suche über Straße, Ort, PLZ, interne Referenz"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    """Listet Gebäude, optional gefiltert über einen Suchbegriff."""
    query = db.query(Building)

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            or_(
                Building.street.ilike(like_term),
                Building.city.ilike(like_term),
                Building.postal_code.ilike(like_term),
                Building.internal_reference.ilike(like_term),
                Building.property_name.ilike(like_term),
                Building.building_id.ilike(like_term),
            )
        )

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    return query.order_by(Building.city, Building.street).offset(offset).limit(limit).all()


@router.get("/buildings/{building_id}", response_model=BuildingResponse, tags=["Buildings"])
def get_building(building_id: str, db: Session = Depends(get_db_session)):
    """Holt die Details eines Gebäudes."""
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {building_id} nicht gefunden")
    return building


@router.post("/buildings", response_model=BuildingResponse, status_code=201, tags=["Buildings"])
def create_building(payload: BuildingCreate, db: Session = Depends(get_db_session)):
    """Legt ein neues Gebäude an. Die building_id wird serverseitig erzeugt, falls nicht mitgegeben."""
    data = payload.model_dump()
    building_id = data.pop("building_id", None) or str(uuid.uuid4())

    existing = db.query(Building).filter(Building.building_id == building_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Gebäude {building_id} existiert bereits")

    building = Building(building_id=building_id, **data)
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.put("/buildings/{building_id}", response_model=BuildingResponse, tags=["Buildings"])
def update_building(building_id: str, payload: BuildingUpdate, db: Session = Depends(get_db_session)):
    """Aktualisiert ein bestehendes Gebäude."""
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {building_id} nicht gefunden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(building, field, value)

    db.commit()
    db.refresh(building)
    return building


@router.delete("/buildings/{building_id}", status_code=204, tags=["Buildings"])
def delete_building(building_id: str, db: Session = Depends(get_db_session)):
    """Löscht ein Gebäude inklusive aller zugehörigen Anfragen (Historie)."""
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {building_id} nicht gefunden")

    for request in db.query(Request).filter(Request.building_id == building_id).all():
        db.delete(request)  # kaskadiert über die Relationship auf RequestItems

    db.delete(building)
    db.commit()
    return None
