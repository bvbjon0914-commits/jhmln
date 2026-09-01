"""
API Routes: Requests (Historie)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.building import Building
from app.models.request import Request

router = APIRouter()


@router.get("/requests", tags=["Requests"])
def list_requests(
    response: Response,
    building_id: Optional[str] = Query(None),
    orphaned_only: bool = Query(False, description="Nur Anfragen zu nicht mehr existierenden Gebäuden"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    """Listet die Anfrage-Historie, optional gefiltert nach Gebäude oder verwaisten Einträgen."""
    query = db.query(Request)
    if building_id:
        query = query.filter(Request.building_id == building_id)

    if orphaned_only:
        existing_building_ids = db.query(Building.building_id)
        query = query.filter(Request.building_id.notin_(existing_building_ids))

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    records = query.order_by(Request.created_at.desc()).offset(offset).limit(limit).all()

    building_ids = {r.building_id for r in records}
    buildings_by_id = {
        b.building_id: b
        for b in db.query(Building).filter(Building.building_id.in_(building_ids)).all()
    } if building_ids else {}

    results = []
    for r in records:
        data = r.to_dict()
        building = buildings_by_id.get(r.building_id)
        data["building"] = (
            {"street": building.street, "house_number": building.house_number, "city": building.city}
            if building
            else None
        )
        results.append(data)
    return results


@router.get("/requests/{request_id}", tags=["Requests"])
def get_request(request_id: str, db: Session = Depends(get_db_session)):
    """Holt die Details eines Requests inklusive aller RequestItems."""
    request_record = db.query(Request).filter(Request.request_id == request_id).first()
    if not request_record:
        raise HTTPException(status_code=404, detail=f"Request {request_id} nicht gefunden")
    return request_record.to_dict()


@router.delete("/requests/{request_id}", status_code=204, tags=["Requests"])
def delete_request(request_id: str, db: Session = Depends(get_db_session)):
    """Löscht eine Anfrage inklusive aller RequestItems."""
    request_record = db.query(Request).filter(Request.request_id == request_id).first()
    if not request_record:
        raise HTTPException(status_code=404, detail=f"Request {request_id} nicht gefunden")

    db.delete(request_record)
    db.commit()
    return None


@router.post("/requests/purge-orphaned", tags=["Requests"])
def purge_orphaned_requests(db: Session = Depends(get_db_session)):
    """Löscht alle Anfragen, deren Gebäude nicht mehr existiert."""
    existing_building_ids = db.query(Building.building_id)
    orphaned = db.query(Request).filter(Request.building_id.notin_(existing_building_ids)).all()

    for request_record in orphaned:
        db.delete(request_record)
    db.commit()

    return {"deleted": len(orphaned)}
