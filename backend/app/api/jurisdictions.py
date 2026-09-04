"""
API Routes: Jurisdictions (Zuständigkeitsregeln)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.data_quality import _duplicate_jurisdiction_ids
from app.database import get_db_session
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.schemas import JurisdictionResponse, JurisdictionUpdate

router = APIRouter()


@router.get("/jurisdictions", response_model=List[JurisdictionResponse], tags=["Jurisdictions"])
def list_jurisdictions(
    response: Response,
    request_type_id: Optional[str] = Query(None),
    authority_id: Optional[str] = Query(None),
    ags: Optional[str] = Query(None, description="Exakter oder präfix-basierter AGS-Filter"),
    state: Optional[str] = Query(None, description="Exakter Bundesland-Filter"),
    municipality: Optional[str] = Query(None, description="Präfix-Filter auf die Gemeinde"),
    district: Optional[str] = Query(None, description="Präfix-Filter auf den Stadtteil/Bezirk"),
    duplicate_only: bool = Query(False, description="Nur als Duplikat erkannte Regeln"),
    orphaned_only: bool = Query(False, description="Nur Regeln, die auf eine deaktivierte Behörde zeigen"),
    active_only: bool = True,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    """Listet Zuständigkeitsregeln, gefiltert nach Auskunftsart/Behörde/AGS."""
    query = db.query(Jurisdiction)

    if active_only:
        query = query.filter(Jurisdiction.active.is_(True))
    if request_type_id:
        query = query.filter(Jurisdiction.request_type_id == request_type_id)
    if authority_id:
        query = query.filter(Jurisdiction.authority_id == authority_id)
    if ags:
        query = query.filter(Jurisdiction.ags.ilike(f"{ags}%"))
    if state:
        query = query.filter(Jurisdiction.state == state)
    if municipality:
        query = query.filter(Jurisdiction.municipality.ilike(f"{municipality}%"))
    if district:
        query = query.filter(Jurisdiction.district.ilike(f"{district}%"))
    if duplicate_only:
        dup_ids = _duplicate_jurisdiction_ids(db)
        query = query.filter(Jurisdiction.jurisdiction_id.in_(dup_ids)) if dup_ids else query.filter(False)
    if orphaned_only:
        inactive_authority_ids = db.query(Authority.authority_id).filter(Authority.active.is_(False))
        query = query.filter(Jurisdiction.authority_id.in_(inactive_authority_ids))

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    return (
        query.order_by(Jurisdiction.request_type_id, Jurisdiction.ags)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse, tags=["Jurisdictions"])
def get_jurisdiction(jurisdiction_id: str, db: Session = Depends(get_db_session)):
    """Holt die Details einer Zuständigkeitsregel."""
    jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == jurisdiction_id).first()
    if not jurisdiction:
        raise HTTPException(status_code=404, detail=f"Zuständigkeitsregel {jurisdiction_id} nicht gefunden")
    return jurisdiction


@router.put("/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse, tags=["Jurisdictions"])
def update_jurisdiction(
    jurisdiction_id: str, payload: JurisdictionUpdate, db: Session = Depends(get_db_session)
):
    """Aktualisiert eine Zuständigkeitsregel (z.B. Priorität, Aktiv-Status, AGS)."""
    jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == jurisdiction_id).first()
    if not jurisdiction:
        raise HTTPException(status_code=404, detail=f"Zuständigkeitsregel {jurisdiction_id} nicht gefunden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(jurisdiction, field, value)

    db.commit()
    db.refresh(jurisdiction)
    return jurisdiction


@router.delete("/jurisdictions/{jurisdiction_id}", status_code=204, tags=["Jurisdictions"])
def delete_jurisdiction(jurisdiction_id: str, db: Session = Depends(get_db_session)):
    """Löscht eine Zuständigkeitsregel."""
    jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == jurisdiction_id).first()
    if not jurisdiction:
        raise HTTPException(status_code=404, detail=f"Zuständigkeitsregel {jurisdiction_id} nicht gefunden")

    db.delete(jurisdiction)
    db.commit()
    return None
