"""
API Routes: Authorities
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.data_quality import _duplicate_authority_ids, _VERIFICATION_STALE_DAYS
from app.database import get_db_session
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction
from app.schemas import AuthorityCreate, AuthorityResponse, AuthorityUpdate

router = APIRouter()


@router.get("/authorities", response_model=List[AuthorityResponse], tags=["Authorities"])
def list_authorities(
    response: Response,
    search: Optional[str] = Query(None),
    ids: Optional[str] = Query(None, description="Kommagetrennte Liste von authority_id für Batch-Lookup"),
    active_only: bool = True,
    state: Optional[str] = Query(None, description="Exakter Bundesland-Filter"),
    has_email: Optional[bool] = Query(None, description="True: nur mit E-Mail, False: nur ohne E-Mail"),
    duplicate_only: bool = Query(False, description="Nur als Duplikat erkannte Behörden"),
    unverified_only: bool = Query(False, description="Nur nie oder vor >12 Monaten verifizierte Behörden"),
    without_jurisdiction_only: bool = Query(False, description="Nur Behörden ohne Zuständigkeitsregel"),
    without_address_only: bool = Query(False, description="Nur Behörden ohne Straße und Ort"),
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    """Listet Behörden, optional gefiltert."""
    query = db.query(Authority)

    if ids:
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        response.headers["X-Total-Count"] = str(len(id_list))
        return query.filter(Authority.authority_id.in_(id_list)).all()

    if active_only:
        query = query.filter(Authority.active.is_(True))

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            or_(
                Authority.authority_name.ilike(like_term),
                Authority.city.ilike(like_term),
                Authority.department_name.ilike(like_term),
                Authority.street.ilike(like_term),
                Authority.postal_code.ilike(like_term),
                Authority.email.ilike(like_term),
            )
        )
    if state:
        query = query.filter(Authority.state == state)
    if has_email is True:
        query = query.filter(Authority.email.isnot(None), Authority.email != "")
    elif has_email is False:
        query = query.filter(or_(Authority.email.is_(None), Authority.email == ""))
    if unverified_only:
        cutoff = datetime.utcnow() - timedelta(days=_VERIFICATION_STALE_DAYS)
        query = query.filter(or_(Authority.last_verified_at.is_(None), Authority.last_verified_at < cutoff))
    if without_jurisdiction_only:
        referenced_ids = db.query(Jurisdiction.authority_id).distinct()
        query = query.filter(Authority.authority_id.notin_(referenced_ids))
    if without_address_only:
        query = query.filter(or_(Authority.street.is_(None), Authority.street == ""))
        query = query.filter(or_(Authority.city.is_(None), Authority.city == ""))
    if duplicate_only:
        dup_ids = _duplicate_authority_ids(db)
        query = query.filter(Authority.authority_id.in_(dup_ids)) if dup_ids else query.filter(False)

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    return query.order_by(Authority.authority_name).offset(offset).limit(limit).all()


@router.get("/authorities/{authority_id}", response_model=AuthorityResponse, tags=["Authorities"])
def get_authority(authority_id: str, db: Session = Depends(get_db_session)):
    """Holt die Details einer Behörde."""
    authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
    if not authority:
        raise HTTPException(status_code=404, detail=f"Behörde {authority_id} nicht gefunden")
    return authority


@router.post("/authorities", response_model=AuthorityResponse, status_code=201, tags=["Authorities"])
def create_authority(payload: AuthorityCreate, db: Session = Depends(get_db_session)):
    """Legt eine neue Behörde an."""
    existing = db.query(Authority).filter(Authority.authority_id == payload.authority_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Behörde {payload.authority_id} existiert bereits")

    authority = Authority(**payload.model_dump())
    db.add(authority)
    db.commit()
    db.refresh(authority)
    return authority


@router.put("/authorities/{authority_id}", response_model=AuthorityResponse, tags=["Authorities"])
def update_authority(authority_id: str, payload: AuthorityUpdate, db: Session = Depends(get_db_session)):
    """Aktualisiert eine bestehende Behörde."""
    authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
    if not authority:
        raise HTTPException(status_code=404, detail=f"Behörde {authority_id} nicht gefunden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(authority, field, value)

    db.commit()
    db.refresh(authority)
    return authority


@router.put("/authorities/{authority_id}/verify", response_model=AuthorityResponse, tags=["Authorities"])
def verify_authority(authority_id: str, db: Session = Depends(get_db_session)):
    """
    Markiert eine Behörde als (heute) verifiziert - setzt last_verified_at,
    damit sie aus der Datenqualität-Kategorie "nicht verifiziert" verschwindet.
    """
    authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
    if not authority:
        raise HTTPException(status_code=404, detail=f"Behörde {authority_id} nicht gefunden")

    authority.last_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(authority)
    return authority


@router.delete("/authorities/{authority_id}", status_code=204, tags=["Authorities"])
def delete_authority(authority_id: str, db: Session = Depends(get_db_session)):
    """
    Löscht eine Behörde. Schlägt fehl, wenn noch Zuständigkeitsregeln auf sie
    verweisen (erst diese löschen oder die Behörde stattdessen deaktivieren).
    """
    authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
    if not authority:
        raise HTTPException(status_code=404, detail=f"Behörde {authority_id} nicht gefunden")

    jurisdiction_count = db.query(Jurisdiction).filter(Jurisdiction.authority_id == authority_id).count()
    if jurisdiction_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{jurisdiction_count} Zuständigkeitsregel(n) verweisen noch auf diese Behörde. "
                "Erst diese löschen oder die Behörde stattdessen deaktivieren."
            ),
        )

    db.delete(authority)
    db.commit()
    return None
