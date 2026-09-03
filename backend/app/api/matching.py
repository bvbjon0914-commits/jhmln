"""
API Routes: Matching

Kernfunktion: ermittelt zuständige Behörden für ein Gebäude + Auskunftsarten
und speichert das Ergebnis als Request/RequestItem für die Historie.
"""

import csv
import io
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.authority import Authority
from app.models.building import Building
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.request_type import RequestType
from app.services import JurisdictionMatchingService

router = APIRouter()

STATUS_LABELS = {
    "MATCHED": "Eindeutig",
    "REVIEW_REQUIRED": "Prüfung nötig",
    "MULTIPLE_MATCHES": "Konflikt",
    "NO_MATCH": "Kein Treffer",
}


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


@router.get("/matching/export-csv", tags=["Matching"])
def export_results_csv(
    request_ids: str = Query(..., description="Kommagetrennte Liste von Request-IDs"),
    db: Session = Depends(get_db_session),
):
    """
    Exportiert die Zuordnungsergebnisse mehrerer Requests (z.B. mehrere
    Gebäude eines Durchlaufs) als CSV – unabhängig davon, ob bereits
    Schreiben generiert wurden. Für Reporting/Dokumentation.
    """
    ids = [r.strip() for r in request_ids.split(",") if r.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Keine request_ids angegeben")

    request_records = db.query(Request).filter(Request.request_id.in_(ids)).all()
    if not request_records:
        raise HTTPException(status_code=404, detail="Keine der angegebenen Requests gefunden")

    buffer = io.StringIO()
    buffer.write("﻿")  # UTF-8 BOM, damit Excel Umlaute korrekt anzeigt
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(
        ["Gebäude", "AGS", "Auskunftsart", "Status", "Zugeordnete Behörde", "Behörde E-Mail", "Manuell geändert"]
    )

    for request_record in request_records:
        building = db.query(Building).filter(Building.building_id == request_record.building_id).first()
        building_label = f"{building.street} {building.house_number}, {building.city}" if building else request_record.building_id
        ags = building.ags if building else ""

        for item in request_record.items:
            request_type = db.query(RequestType).filter(RequestType.request_type_id == item.request_type_id).first()
            authority = (
                db.query(Authority).filter(Authority.authority_id == item.authority_id).first()
                if item.authority_id
                else None
            )
            writer.writerow(
                [
                    building_label,
                    ags or "",
                    request_type.name if request_type else item.request_type_id,
                    STATUS_LABELS.get(item.matching_status, item.matching_status),
                    authority.authority_name if authority else "",
                    authority.email if authority and authority.email else "",
                    "Ja" if item.manually_changed else "",
                ]
            )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        headers={
            "Content-Disposition": "attachment; filename=zuordnungsergebnisse.csv",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


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


def _get_or_create_progress(db: Session, request_item_id: str) -> RequestItemProgress:
    item = db.query(RequestItem).filter(RequestItem.request_item_id == request_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"RequestItem {request_item_id} nicht gefunden")

    progress = (
        db.query(RequestItemProgress)
        .filter(RequestItemProgress.request_item_id == request_item_id)
        .first()
    )
    if not progress:
        progress = RequestItemProgress(request_item_id=request_item_id)
        db.add(progress)
    return progress


@router.put("/matching/items/{request_item_id}/mark-sent", tags=["Matching"])
def mark_item_sent(request_item_id: str, db: Session = Depends(get_db_session)):
    """Markiert ein Anschreiben manuell als versendet (Auftrags-Fortschritt)."""
    progress = _get_or_create_progress(db, request_item_id)
    progress.sent_at = datetime.utcnow()
    db.commit()
    return progress.to_dict()


@router.post("/matching/items/{request_item_id}/upload-response", tags=["Matching"])
async def upload_item_response(
    request_item_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    """
    Lädt die Antwort einer Behörde (PDF) hoch und hinterlegt sie am Auftrags-
    Fortschritt. Wird als Bytes in der Datenbank gespeichert (nicht auf
    Festplatte), damit sie einen Redeploy übersteht.
    """
    content = await file.read()
    progress = _get_or_create_progress(db, request_item_id)
    progress.response_document = content
    progress.response_document_filename = file.filename or "antwort.pdf"
    progress.response_received_at = datetime.utcnow()
    db.commit()
    return progress.to_dict()


@router.get("/matching/items/{request_item_id}/response-download", tags=["Matching"])
def download_item_response(request_item_id: str, db: Session = Depends(get_db_session)):
    progress = (
        db.query(RequestItemProgress)
        .filter(RequestItemProgress.request_item_id == request_item_id)
        .first()
    )
    if not progress or not progress.response_document:
        raise HTTPException(status_code=404, detail="Keine Antwort hinterlegt")

    filename = progress.response_document_filename or "antwort.pdf"
    return Response(
        content=progress.response_document,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/matching/items/{request_item_id}/mark-reviewed", tags=["Matching"])
def mark_item_reviewed(request_item_id: str, db: Session = Depends(get_db_session)):
    progress = _get_or_create_progress(db, request_item_id)
    progress.reviewed_at = datetime.utcnow()
    db.commit()
    return progress.to_dict()
