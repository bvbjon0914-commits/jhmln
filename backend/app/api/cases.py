"""
API Routes: Cases (Aufträge)

Ein Auftrag bündelt mehrere Gebäude und die zu ihnen laufenden Anfragen,
damit der Fortschritt (was wurde beantragt, was fehlt noch, ist eine Antwort
da) über mehrere Gebäude/Behörden hinweg an einem Ort sichtbar ist.

Cases sind eine reine Sicht/Gruppierung: Löschen eines Case oder Entfernen
eines Gebäudes löscht NIE das zugrunde liegende Building/Request – diese
bleiben unabhängig in der normalen Anfrage-Historie bestehen.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.api.matching import _get_or_create_progress
from app.config import GENERATED_DIR, TEMPLATES_DIR
from app.database import get_db_session
from app.models.aktenzeichen import RequestItemReference
from app.models.authority import Authority
from app.models.building import Building
from app.models.case import Case, CaseBuilding, CaseRequest
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.request_type import RequestType
from app.services import DocumentGenerationService, DocumentGenerationError, MailgunError, send_email

router = APIRouter()


class CaseCreatePayload(BaseModel):
    name: str
    notes: Optional[str] = None


class CaseUpdatePayload(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AddBuildingPayload(BaseModel):
    building_id: str


class LinkRequestPayload(BaseModel):
    request_id: str


class SendBundlePayload(BaseModel):
    request_item_ids: list[str]


def _derive_item_status(item: RequestItem, progress: Optional[RequestItemProgress]) -> str:
    if progress and progress.reviewed_at:
        return "GEPRUEFT"
    if progress and progress.response_received_at:
        return "ANTWORT_ERHALTEN"
    if progress and progress.sent_at:
        return "GESENDET"
    if item.document_status == "GENERATED":
        return "BEREIT_ZUM_SENDEN"
    return "NICHT_BEANTRAGT"


def _case_progress_counts(db: Session, case_id: str) -> dict:
    item_ids = [
        row[0]
        for row in db.query(RequestItem.request_item_id)
        .join(Request, Request.request_id == RequestItem.request_id)
        .join(CaseRequest, CaseRequest.request_id == Request.request_id)
        .filter(CaseRequest.case_id == case_id)
        .all()
    ]
    total = len(item_ids)
    if total == 0:
        return {"items_total": 0, "items_done": 0}

    done = (
        db.query(RequestItemProgress)
        .filter(RequestItemProgress.request_item_id.in_(item_ids))
        .filter(RequestItemProgress.reviewed_at.isnot(None))
        .count()
    )
    return {"items_total": total, "items_done": done}


@router.post("/cases", tags=["Cases"])
def create_case(payload: CaseCreatePayload, db: Session = Depends(get_db_session)):
    case = Case(
        case_id=str(uuid.uuid4()),
        name=payload.name.strip(),
        notes=payload.notes,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case.to_dict()


@router.get("/cases", tags=["Cases"])
def list_cases(
    response: Response,
    search: Optional[str] = Query(None),
    limit: int = Query(25, le=200),
    offset: int = 0,
    db: Session = Depends(get_db_session),
):
    query = db.query(Case)
    if search:
        query = query.filter(Case.name.ilike(f"%{search}%"))

    response.headers["X-Total-Count"] = str(query.order_by(None).count())
    cases = query.order_by(Case.updated_at.desc()).offset(offset).limit(limit).all()

    results = []
    for case in cases:
        data = case.to_dict()
        data.update(_case_progress_counts(db, case.case_id))
        results.append(data)
    return results


@router.get("/cases/{case_id}", tags=["Cases"])
def get_case(case_id: str, db: Session = Depends(get_db_session)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    case_buildings = db.query(CaseBuilding).filter(CaseBuilding.case_id == case_id).all()
    building_ids = [cb.building_id for cb in case_buildings]
    buildings = (
        db.query(Building).filter(Building.building_id.in_(building_ids)).all() if building_ids else []
    )

    items_query = (
        db.query(RequestItem, Request.building_id)
        .join(Request, Request.request_id == RequestItem.request_id)
        .join(CaseRequest, CaseRequest.request_id == Request.request_id)
        .filter(CaseRequest.case_id == case_id)
    )
    rows = items_query.all()

    request_type_ids = {row[0].request_type_id for row in rows}
    authority_ids = {row[0].authority_id for row in rows if row[0].authority_id}
    item_ids = [row[0].request_item_id for row in rows]

    request_types_by_id = {
        rt.request_type_id: rt
        for rt in db.query(RequestType).filter(RequestType.request_type_id.in_(request_type_ids)).all()
    } if request_type_ids else {}
    authorities_by_id = {
        a.authority_id: a
        for a in db.query(Authority).filter(Authority.authority_id.in_(authority_ids)).all()
    } if authority_ids else {}
    progress_by_item_id = {
        p.request_item_id: p
        for p in db.query(RequestItemProgress).filter(RequestItemProgress.request_item_id.in_(item_ids)).all()
    } if item_ids else {}
    aktenzeichen_by_item_id = {
        r.request_item_id: r.aktenzeichen
        for r in db.query(RequestItemReference).filter(RequestItemReference.request_item_id.in_(item_ids)).all()
    } if item_ids else {}

    items = []
    for item, building_id in rows:
        request_type = request_types_by_id.get(item.request_type_id)
        authority = authorities_by_id.get(item.authority_id) if item.authority_id else None
        progress = progress_by_item_id.get(item.request_item_id)

        items.append({
            "request_item_id": item.request_item_id,
            "request_id": item.request_id,
            "building_id": building_id,
            "request_type_id": item.request_type_id,
            "request_type_name": request_type.name if request_type else item.request_type_id,
            "authority_id": item.authority_id,
            "authority_name": authority.authority_name if authority else None,
            "authority_email": authority.email if authority else None,
            "matching_status": item.matching_status,
            "document_status": item.document_status,
            "status": _derive_item_status(item, progress),
            "aktenzeichen": aktenzeichen_by_item_id.get(item.request_item_id),
            **(progress.to_dict() if progress else {
                "sent_at": None,
                "response_received_at": None,
                "response_document_filename": None,
                "reviewed_at": None,
            }),
        })

    data = case.to_dict()
    data["buildings"] = [b.to_dict() for b in buildings]
    data["items"] = items
    return data


@router.put("/cases/{case_id}", tags=["Cases"])
def update_case(case_id: str, payload: CaseUpdatePayload, db: Session = Depends(get_db_session)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    if payload.name is not None:
        case.name = payload.name.strip()
    if payload.notes is not None:
        case.notes = payload.notes
    if payload.status is not None:
        if payload.status not in ("OPEN", "CLOSED"):
            raise HTTPException(status_code=400, detail="status muss OPEN oder CLOSED sein")
        case.status = payload.status

    db.commit()
    db.refresh(case)
    return case.to_dict()


@router.delete("/cases/{case_id}", status_code=204, tags=["Cases"])
def delete_case(case_id: str, db: Session = Depends(get_db_session)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    # Nur die Zuordnungen entfernen – Buildings/Requests bleiben unangetastet.
    db.query(CaseBuilding).filter(CaseBuilding.case_id == case_id).delete()
    db.query(CaseRequest).filter(CaseRequest.case_id == case_id).delete()
    db.delete(case)
    db.commit()
    return None


@router.post("/cases/{case_id}/buildings", tags=["Cases"])
def add_building_to_case(case_id: str, payload: AddBuildingPayload, db: Session = Depends(get_db_session)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    building = db.query(Building).filter(Building.building_id == payload.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {payload.building_id} nicht gefunden")

    existing = (
        db.query(CaseBuilding)
        .filter(CaseBuilding.case_id == case_id, CaseBuilding.building_id == payload.building_id)
        .first()
    )
    if not existing:
        db.add(CaseBuilding(case_id=case_id, building_id=payload.building_id))
        db.commit()

    return {"ok": True}


@router.delete("/cases/{case_id}/buildings/{building_id}", status_code=204, tags=["Cases"])
def remove_building_from_case(case_id: str, building_id: str, db: Session = Depends(get_db_session)):
    db.query(CaseBuilding).filter(
        CaseBuilding.case_id == case_id, CaseBuilding.building_id == building_id
    ).delete()
    db.commit()
    return None


@router.post("/cases/{case_id}/link-request", tags=["Cases"])
def link_request_to_case(case_id: str, payload: LinkRequestPayload, db: Session = Depends(get_db_session)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    request_record = db.query(Request).filter(Request.request_id == payload.request_id).first()
    if not request_record:
        raise HTTPException(status_code=404, detail=f"Request {payload.request_id} nicht gefunden")

    existing = (
        db.query(CaseRequest)
        .filter(CaseRequest.case_id == case_id, CaseRequest.request_id == payload.request_id)
        .first()
    )
    if not existing:
        db.add(CaseRequest(case_id=case_id, request_id=payload.request_id))
        db.commit()

    return {"ok": True}


@router.post("/cases/{case_id}/send-bundle", tags=["Cases"])
def send_bundle(
    case_id: str,
    payload: SendBundlePayload,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_main),
):
    """
    Nur Haupt-Account: versendet alle übergebenen RequestItems als EINE
    E-Mail (ein Anhang pro Item) an ihre gemeinsame Behörde. Alle Items
    müssen zu diesem Case gehören, dieselbe Behörde haben, ein generiertes
    Dokument besitzen und noch nicht versendet sein - sonst wird der
    komplette Versand abgelehnt (all-or-nothing, nie einzelne Items
    stillschweigend überspringen, das wäre eine Form von Raten).

    Jedes Dokument wird beim Versenden frisch neu generiert (mit dem
    bereits vergebenen, stabilen Aktenzeichen aus Phase 2) statt sich auf
    den gespeicherten document_path zu verlassen - auf Render (Free-Tier)
    ist der Festplattenspeicher flüchtig und kann zwischen Generierung und
    manuellem "Jetzt senden" bereits gelöscht worden sein.
    """
    if not payload.request_item_ids:
        raise HTTPException(status_code=400, detail="Keine request_item_ids angegeben")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Auftrag {case_id} nicht gefunden")

    case_request_ids = {
        r[0] for r in db.query(CaseRequest.request_id).filter(CaseRequest.case_id == case_id).all()
    }
    items_by_id = {
        i.request_item_id: i
        for i in db.query(RequestItem).filter(RequestItem.request_item_id.in_(payload.request_item_ids)).all()
    }
    progress_by_item_id = {
        p.request_item_id: p
        for p in db.query(RequestItemProgress)
        .filter(RequestItemProgress.request_item_id.in_(payload.request_item_ids))
        .all()
    }

    problems = []
    for item_id in payload.request_item_ids:
        item = items_by_id.get(item_id)
        if not item:
            problems.append(f"{item_id}: nicht gefunden")
        elif item.request_id not in case_request_ids:
            problems.append(f"{item_id}: gehört nicht zu diesem Auftrag")
        elif item.document_status != "GENERATED":
            problems.append(f"{item_id}: Dokument nicht generiert")
        elif progress_by_item_id.get(item_id) and progress_by_item_id[item_id].sent_at:
            problems.append(f"{item_id}: bereits versendet")
    if problems:
        raise HTTPException(
            status_code=400,
            detail={"message": "Bündel kann nicht versendet werden", "problems": problems},
        )

    authority_ids = {items_by_id[i].authority_id for i in payload.request_item_ids}
    if len(authority_ids) != 1 or None in authority_ids:
        raise HTTPException(status_code=400, detail="Alle Items im Bündel müssen dieselbe Behörde haben")
    authority = db.query(Authority).filter(Authority.authority_id == authority_ids.pop()).first()
    if not authority or not authority.email:
        raise HTTPException(status_code=400, detail="Für diese Behörde ist keine E-Mail-Adresse hinterlegt")

    request_ids = {items_by_id[i].request_id for i in payload.request_item_ids}
    requests_by_id = {r.request_id: r for r in db.query(Request).filter(Request.request_id.in_(request_ids)).all()}
    building_ids = {r.building_id for r in requests_by_id.values()}
    buildings_by_id = {
        b.building_id: b for b in db.query(Building).filter(Building.building_id.in_(building_ids)).all()
    }
    request_type_ids = {items_by_id[i].request_type_id for i in payload.request_item_ids}
    request_types_by_id = {
        rt.request_type_id: rt
        for rt in db.query(RequestType).filter(RequestType.request_type_id.in_(request_type_ids)).all()
    }
    aktenzeichen_by_item_id = {
        r.request_item_id: r.aktenzeichen
        for r in db.query(RequestItemReference)
        .filter(RequestItemReference.request_item_id.in_(payload.request_item_ids))
        .all()
    }

    generator = DocumentGenerationService(templates_dir=TEMPLATES_DIR, output_dir=GENERATED_DIR)
    attachments: list[tuple[str, bytes]] = []
    aktenzeichen_list = []
    request_type_names = []

    for item_id in payload.request_item_ids:
        item = items_by_id[item_id]
        aktenzeichen = aktenzeichen_by_item_id.get(item_id)
        request_record = requests_by_id.get(item.request_id)
        building = buildings_by_id.get(request_record.building_id) if request_record else None
        request_type = request_types_by_id.get(item.request_type_id)
        if not aktenzeichen or not building or not request_type:
            raise HTTPException(
                status_code=400,
                detail=f"{item_id}: Aktenzeichen, Gebäude oder Auskunftsart fehlt - bitte zuerst das Schreiben generieren",
            )

        try:
            doc = generator.generate_document(building, authority, request_type, aktenzeichen)
        except DocumentGenerationError as exc:
            raise HTTPException(status_code=502, detail=f"{item_id}: Dokument konnte nicht erzeugt werden: {exc}")

        with open(doc.filepath, "rb") as f:
            content = f.read()
        attachments.append((doc.filename, content))
        aktenzeichen_list.append(aktenzeichen)
        request_type_names.append(request_type.name)
        item.document_path = doc.filepath

    subject = f"Auskunftsersuchen {', '.join(aktenzeichen_list)}"
    text = (
        "Sehr geehrte Damen und Herren,\n\n"
        f"anbei unsere Anfrage(n) betreffend {', '.join(request_type_names)}.\n\n"
        "Mit freundlichen Grüßen\nVonovia SE"
    )

    try:
        result = send_email(to=authority.email, subject=subject, text=text, attachments=attachments)
    except MailgunError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    now = datetime.utcnow()
    for item_id in payload.request_item_ids:
        _get_or_create_progress(db, item_id).sent_at = now
    db.commit()

    return {
        "sent": len(payload.request_item_ids),
        "dry_run": result.dry_run,
        "mailgun_message_id": result.mailgun_message_id,
    }
