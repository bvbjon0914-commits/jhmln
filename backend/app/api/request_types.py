"""
API Routes: RequestTypes
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.request_type import RequestType
from app.schemas import RequestTypeResponse

router = APIRouter()


@router.get("/request-types", response_model=List[RequestTypeResponse], tags=["RequestTypes"])
def list_request_types(active_only: bool = True, db: Session = Depends(get_db_session)):
    """Listet alle verfügbaren Auskunftsarten."""
    query = db.query(RequestType)
    if active_only:
        query = query.filter(RequestType.active.is_(True))
    return query.order_by(RequestType.name).all()
