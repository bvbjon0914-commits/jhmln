"""
API Routes: Matching

Kernfunktion: ermittelt zuständige Behörden für ein Gebäude + Auskunftsarten
und speichert das Ergebnis als Request/RequestItem für die Historie.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.building import Building
from app.models.request import Request, RequestItem
from app.models.request_type import RequestType
from app.services import JurisdictionMatchingService

router = APIRouter()


class MatchingRequestPayload(BaseModel):
    building_id: str
    request_type_ids: List[str]
    created_by: str = "anonymous"


class ManualAssignmentPayload(BaseModel):
    authority_id: str
    reason: str = "Manuell durch Benutzer geändert"


@router.post("/matching", tags=["Matching"])
def run_matching(payload: MatchingRequestPayload, db: Session = Depends(get_db_session)):
    """
    Führt das Matching für ein Gebäude und mehrere Auskunftsarten durch.

    Erzeugt einen Request-Datensatz (Historie) mit einem RequestItem
    pro Auskunftsart, inklusive Matching-Status und Begründung.
    """
    building = db.query(Building).filter(Building.building_id == payload.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {payload.building_id} nicht gefunden")

    if not payload.request_type_ids:
        raise HTTPException(status_code=400, detail="Mindestens eine Auskunftsart muss angegeben werden")

    # Auskunftsarten validieren
    valid_types = {
        rt.request_type_id
        for rt in db.query(RequestType).filter(RequestType.request_type_id.in_(payload.request_type_ids)).all()
    }
    invalid = set(payload.request_type_ids) - valid_types
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unbekannte Auskunftsarten: {invalid}")

    matcher = JurisdictionMatchingService(db)
    results = matcher.match_authorities(building, payload.request_type_ids)

    # Request + RequestItems anlegen (Audit-Trail)
    request_record = Request(
        request_id=f"REQ_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        building_id=building.building_id,
        created_by=payload.created_by,
        status="PENDING",
    )
    db.add(request_record)
    db.flush()  # damit request_id verfügbar ist, ohne bereits zu committen

    for result in results:
        item = RequestItem(
            request_item_id=f"ITEM_{uuid.uuid4().hex[:12]}",
            request_id=request_record.request_id,
            request_type_id=result.request_type_id,
            authority_id=result.authority_id,
            matching_level=result.matching_level,
            matching_status=result.matching_status,
            matching_confidence=result.matching_confidence,
            document_status="PENDING",
        )
        item.set_alternative_authorities(result.alternative_authorities)
        db.add(item)

    db.commit()
    db.refresh(request_record)

    return {
        "request_id": request_record.request_id,
        "building_id": building.building_id,
        "results": [
            {**result.to_dict(), "request_item_id": item.request_item_id}
            for result, item in zip(results, request_record.items)
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.put("/matching/items/{request_item_id}/assign", tags=["Matching"])
def manually_assign_authority(
    request_item_id: str,
    payload: ManualAssignmentPayload,
    db: Session = Depends(get_db_session),
):
    """
    Ermöglicht die manuelle Korrektur einer Zuordnung
    (z.B. bei REVIEW_REQUIRED / MULTIPLE_MATCHES oder NO_MATCH).
    """
    item = db.query(RequestItem).filter(RequestItem.request_item_id == request_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"RequestItem {request_item_id} nicht gefunden")

    item.authority_id = payload.authority_id
    item.matching_status = "MATCHED"
    item.matching_confidence = 1.0
    item.manually_changed = True
    item.manual_change_reason = payload.reason

    db.commit()
    db.refresh(item)

    return item.to_dict()
