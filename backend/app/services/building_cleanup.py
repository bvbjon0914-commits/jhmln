"""
Löscht ein Gebäude samt ALLEM, was in der Datenbank per Fremdschlüssel daran hängt.

Hintergrund: SQLite (lokal) erzwingt Fremdschlüssel standardmäßig nicht, Postgres
(Produktion/Neon) schon - ein nur halb kaskadierendes Löschen scheitert dort mit
einem IntegrityError (500 / "Network Error" im Browser), obwohl es lokal "geht".
Alle Löschwege für Gebäude sollen deshalb diese eine Funktion benutzen.

Reihenfolge (Kinder vor Eltern):
  RequestItemProgress, RequestItemReference (Aktenzeichen) -> an RequestItems
  InboundEmail.matched_request_item_id -> auf NULL (die eingegangene E-Mail selbst
      bleibt erhalten, nur die Verknüpfung zum gelöschten Vorgang entfällt)
  RequestSequence, CaseRequest -> an Requests
  RequestItem, Request
  CaseBuilding -> am Gebäude
  Building
"""

from typing import List

from sqlalchemy.orm import Session

from app.models.aktenzeichen import RequestItemReference, RequestSequence
from app.models.building import Building
from app.models.case import CaseBuilding, CaseRequest
from app.models.inbound_email import InboundEmail
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress


def delete_requests_with_dependents(db: Session, request_ids: List[str]) -> int:
    """Löscht Anfragen inkl. Items, Fortschritt, Aktenzeichen und Auftragsverknüpfungen.

    Committet NICHT. Gibt die Anzahl der gelöschten Requests zurück.
    """
    if not request_ids:
        return 0

    item_ids = [r[0] for r in db.query(RequestItem.request_item_id).filter(RequestItem.request_id.in_(request_ids)).all()]
    if item_ids:
        db.query(RequestItemProgress).filter(RequestItemProgress.request_item_id.in_(item_ids)).delete(
            synchronize_session=False
        )
        db.query(RequestItemReference).filter(RequestItemReference.request_item_id.in_(item_ids)).delete(
            synchronize_session=False
        )
        db.query(InboundEmail).filter(InboundEmail.matched_request_item_id.in_(item_ids)).update(
            {InboundEmail.matched_request_item_id: None}, synchronize_session=False
        )
    db.query(RequestSequence).filter(RequestSequence.request_id.in_(request_ids)).delete(synchronize_session=False)
    db.query(CaseRequest).filter(CaseRequest.request_id.in_(request_ids)).delete(synchronize_session=False)
    db.query(RequestItem).filter(RequestItem.request_id.in_(request_ids)).delete(synchronize_session=False)
    deleted = db.query(Request).filter(Request.request_id.in_(request_ids)).delete(synchronize_session=False)
    db.flush()
    return deleted


def delete_building_with_dependents(db: Session, building_id: str) -> bool:
    """Löscht das Gebäude inkl. Anfragen/Items/Fortschritt/Aktenzeichen/Auftragsverknüpfungen.

    Gibt False zurück, wenn es das Gebäude nicht gibt. Committet NICHT - das macht
    der Aufrufer (so kann er mehrere Gebäude in einer Transaktion löschen).
    """
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if building is None:
        return False

    request_ids = [r[0] for r in db.query(Request.request_id).filter(Request.building_id == building_id).all()]
    delete_requests_with_dependents(db, request_ids)

    db.query(CaseBuilding).filter(CaseBuilding.building_id == building_id).delete(synchronize_session=False)
    db.delete(building)
    db.flush()
    return True
