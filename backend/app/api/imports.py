"""
API Routes: Imports
"""

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_is_main
from app.database import get_db_session
from app.services import ImportService

router = APIRouter()


@router.post("/import/preview", tags=["Imports"])
async def preview_import(
    file: UploadFile = File(...),
    sheet: str = Form(None, description="Bei mehrblättrigen Excel-Dateien: das zu lesende Arbeitsblatt"),
    db: Session = Depends(get_db_session),
):
    """Liest die Datei ein und zeigt eine Vorschau + verfügbare Spalten."""
    content = await file.read()
    service = ImportService(db)

    try:
        sheets = service.list_sheets(content, file.filename)
        df = service.read_file(content, file.filename, sheet_name=sheet)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return service.preview(df, sheets=sheets, selected_sheet=sheet)


@router.post("/import/buildings", tags=["Imports"])
async def import_buildings(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="JSON: {db_field: csv_column}"),
    sheet: str = Form(None, description="Bei mehrblättrigen Excel-Dateien: das zu lesende Arbeitsblatt"),
    db: Session = Depends(get_db_session),
):
    """Importiert Gebäude aus einer CSV/Excel-Datei."""
    content = await file.read()
    service = ImportService(db)

    try:
        df = service.read_file(content, file.filename, sheet_name=sheet)
        mapping_dict = json.loads(mapping)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    summary = service.import_buildings(df, mapping_dict)
    return summary.to_dict()


@router.post("/import/authorities", tags=["Imports"])
async def import_authorities(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    fill_gaps: bool = Form(False, description="Nur Haupt-Account: fehlende Felder bei bestehenden Behörden ergänzen"),
    sheet: str = Form(None, description="Bei mehrblättrigen Excel-Dateien: das zu lesende Arbeitsblatt"),
    db: Session = Depends(get_db_session),
    is_main: bool = Depends(get_is_main),
):
    """Importiert Behörden aus einer CSV/Excel-Datei."""
    if fill_gaps and not is_main:
        raise HTTPException(
            status_code=403,
            detail="Nur der Haupt-Account darf fehlende Daten bei bestehenden Behörden ergänzen.",
        )

    content = await file.read()
    service = ImportService(db)

    try:
        df = service.read_file(content, file.filename, sheet_name=sheet)
        mapping_dict = json.loads(mapping)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    summary = service.import_authorities(df, mapping_dict, fill_gaps=fill_gaps)
    return summary.to_dict()


@router.post("/import/jurisdictions", tags=["Imports"])
async def import_jurisdictions(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="JSON: {db_field: csv_column}"),
    request_type_id: str = Form(..., description="Auskunftsart, für die dieser Import gilt"),
    sheet: str = Form(None, description="Bei mehrblättrigen Excel-Dateien: das zu lesende Arbeitsblatt"),
    db: Session = Depends(get_db_session),
):
    """Importiert Zuständigkeiten (Behörde + Kontaktdaten + AGS) aus einer CSV/Excel-Datei."""
    content = await file.read()
    service = ImportService(db)

    try:
        df = service.read_file(content, file.filename, sheet_name=sheet)
        mapping_dict = json.loads(mapping)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    summary = service.import_jurisdictions(df, mapping_dict, request_type_id)
    return summary.to_dict()
