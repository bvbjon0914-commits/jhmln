"""
API Routes: Documents

Generiert Word-Dokumente für alle bestätigten RequestItems eines Requests
und stellt sie zum Download bereit (einzeln oder als ZIP).
"""

import io
import os
import re
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import GENERATED_DIR, TEMPLATES_DIR
from app.database import get_db_session
from app.models.authority import Authority
from app.models.building import Building
from app.models.request import Request, RequestItem
from app.models.request_type import RequestType
from app.services import DocumentGenerationService, DocumentGenerationError

router = APIRouter()


class DocumentGenerationPayload(BaseModel):
    request_id: str
    retry_failed_only: bool = False


@router.post("/documents/generate", tags=["Documents"])
def generate_documents(payload: DocumentGenerationPayload, db: Session = Depends(get_db_session)):
    """
    Generiert für jedes bestätigte RequestItem ein eigenes DOCX-Dokument.

    Ein Dokument wird nur generiert, wenn der RequestItem-Status
    MATCHED ist (also entweder automatisch eindeutig zugeordnet oder
    manuell bestätigt wurde).

    Mit retry_failed_only=True werden bereits erfolgreich generierte
    Dokumente übersprungen (document_status == GENERATED) – nur zuvor
    fehlgeschlagene bzw. noch nicht versuchte Items werden neu erzeugt.
    """
    request_record = db.query(Request).filter(Request.request_id == payload.request_id).first()
    if not request_record:
        raise HTTPException(status_code=404, detail=f"Request {payload.request_id} nicht gefunden")

    building = db.query(Building).filter(Building.building_id == request_record.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Zugehöriges Gebäude nicht gefunden")

    generator = DocumentGenerationService(templates_dir=TEMPLATES_DIR, output_dir=GENERATED_DIR)

    generated = []
    failed = []

    for item in request_record.items:
        if payload.retry_failed_only and item.document_status == "GENERATED":
            continue

        if item.matching_status != "MATCHED":
            failed.append({
                "request_item_id": item.request_item_id,
                "request_type_id": item.request_type_id,
                "reason": f"Status ist {item.matching_status}, kein Dokument generiert",
            })
            continue

        authority = db.query(Authority).filter(Authority.authority_id == item.authority_id).first()
        request_type = db.query(RequestType).filter(RequestType.request_type_id == item.request_type_id).first()

        if not authority or not request_type:
            failed.append({
                "request_item_id": item.request_item_id,
                "request_type_id": item.request_type_id,
                "reason": "Behörde oder Auskunftsart nicht gefunden",
            })
            continue

        try:
            doc = generator.generate_document(building, authority, request_type)
            item.document_path = doc.filepath
            item.document_status = "GENERATED"
            generated.append({
                "request_item_id": item.request_item_id,
                "request_type_id": item.request_type_id,
                "authority_id": item.authority_id,
                "filename": doc.filename,
                "filepath": doc.filepath,
            })
        except DocumentGenerationError as exc:
            item.document_status = "FAILED"
            failed.append({
                "request_item_id": item.request_item_id,
                "request_type_id": item.request_type_id,
                "reason": str(exc),
            })

    request_record.status = "COMPLETED" if not failed else "PARTIALLY_COMPLETED"
    db.commit()

    return {
        "request_id": request_record.request_id,
        "documents": generated,
        "failed": failed,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/documents/{request_item_id}/download", tags=["Documents"])
def download_document(request_item_id: str, db: Session = Depends(get_db_session)):
    """Lädt ein einzelnes generiertes Dokument herunter."""
    item = db.query(RequestItem).filter(RequestItem.request_item_id == request_item_id).first()
    if not item or not item.document_path:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")

    if not os.path.exists(item.document_path):
        raise HTTPException(status_code=404, detail="Dokumentdatei existiert nicht mehr auf dem Server")

    filename = os.path.basename(item.document_path)
    return FileResponse(
        path=item.document_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/documents/request/{request_id}/download-all", tags=["Documents"])
def download_all_documents(request_id: str, db: Session = Depends(get_db_session)):
    """Lädt alle generierten Dokumente eines Requests als ZIP herunter."""
    request_record = db.query(Request).filter(Request.request_id == request_id).first()
    if not request_record:
        raise HTTPException(status_code=404, detail=f"Request {request_id} nicht gefunden")

    items_with_docs = [i for i in request_record.items if i.document_path and os.path.exists(i.document_path)]
    if not items_with_docs:
        raise HTTPException(status_code=404, detail="Keine generierten Dokumente für diesen Request gefunden")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in items_with_docs:
            zip_file.write(item.document_path, arcname=os.path.basename(item.document_path))

    buffer.seek(0)
    zip_filename = f"{request_record.building_id}_{request_id}.zip"

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
    )


def _sanitize_folder_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9äöüÄÖÜß_\- ]", "_", value).strip() or "Gebaeude"


@router.get("/documents/download-all-combined", tags=["Documents"])
def download_all_combined(
    request_ids: str = Query(..., description="Kommagetrennte Liste von Request-IDs"),
    db: Session = Depends(get_db_session),
):
    """
    Lädt die generierten Dokumente mehrerer Requests (z.B. mehrere Gebäude
    in einem Durchlauf) als eine einzige ZIP-Datei herunter, mit einem
    Unterordner pro Gebäude.
    """
    ids = [r.strip() for r in request_ids.split(",") if r.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Keine request_ids angegeben")

    request_records = db.query(Request).filter(Request.request_id.in_(ids)).all()
    if not request_records:
        raise HTTPException(status_code=404, detail="Keine der angegebenen Requests gefunden")

    buffer = io.BytesIO()
    added_any = False
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for request_record in request_records:
            items_with_docs = [
                i for i in request_record.items if i.document_path and os.path.exists(i.document_path)
            ]
            if not items_with_docs:
                continue

            building = db.query(Building).filter(Building.building_id == request_record.building_id).first()
            folder = (
                _sanitize_folder_name(f"{building.street} {building.house_number}, {building.city}")
                if building
                else request_record.building_id
            )

            for item in items_with_docs:
                arcname = f"{folder}/{os.path.basename(item.document_path)}"
                zip_file.write(item.document_path, arcname=arcname)
                added_any = True

    if not added_any:
        raise HTTPException(status_code=404, detail="Keine generierten Dokumente für diese Requests gefunden")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=alle_schreiben.zip"},
    )
