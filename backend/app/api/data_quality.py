"""
API Routes: Datenqualität

Liefert eine Übersicht über Lücken in den Stammdaten (z.B. Behörden ohne
E-Mail-Adresse oder Behörden, die in keiner Zuständigkeit referenziert
werden), damit diese proaktiv gepflegt werden können statt erst beim
Matching als NO_MATCH/"keine E-Mail" aufzufallen.
"""

import io
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction

router = APIRouter()

MAX_ITEMS = 200


def _serialize(a: Authority) -> dict:
    return {
        "authority_id": a.authority_id,
        "authority_name": a.authority_name,
        "city": a.city,
    }


def _authorities_without_email(db: Session) -> List[Authority]:
    return (
        db.query(Authority)
        .filter(Authority.active.is_(True))
        .filter(or_(Authority.email.is_(None), Authority.email == ""))
        .order_by(Authority.authority_name)
        .all()
    )


def _authorities_without_jurisdiction(db: Session) -> List[Authority]:
    referenced_ids = {row[0] for row in db.query(Jurisdiction.authority_id).distinct().all()}
    active_authorities = db.query(Authority).filter(Authority.active.is_(True)).all()
    without_jurisdiction = [a for a in active_authorities if a.authority_id not in referenced_ids]
    without_jurisdiction.sort(key=lambda a: a.authority_name or "")
    return without_jurisdiction


@router.get("/data-quality/summary", tags=["DataQuality"])
def data_quality_summary(db: Session = Depends(get_db_session)):
    total_authorities = db.query(Authority).filter(Authority.active.is_(True)).count()
    without_email = _authorities_without_email(db)
    without_jurisdiction = _authorities_without_jurisdiction(db)

    return {
        "total_authorities": total_authorities,
        "authorities_without_email": {
            "count": len(without_email),
            "items": [_serialize(a) for a in without_email[:MAX_ITEMS]],
        },
        "authorities_without_jurisdiction": {
            "count": len(without_jurisdiction),
            "items": [_serialize(a) for a in without_jurisdiction[:MAX_ITEMS]],
        },
    }


@router.get("/data-quality/export-xlsx", tags=["DataQuality"])
def export_data_quality_xlsx(db: Session = Depends(get_db_session)):
    """
    Exportiert alle Behörden mit unvollständigen Daten (ohne E-Mail bzw.
    ohne hinterlegte Zuständigkeit) als Excel-Datei mit zwei Arbeitsblättern
    – zur Weitergabe an Kolleg:innen, die die Lücken pflegen sollen.
    """

    columns = [
        "Behörde", "Abteilung", "Straße", "Hausnummer", "PLZ", "Ort",
        "Bundesland", "E-Mail", "Telefon", "Website",
    ]

    def to_rows(authorities: List[Authority]) -> List[dict]:
        return [
            {
                "Behörde": a.authority_name,
                "Abteilung": a.department_name,
                "Straße": a.street,
                "Hausnummer": a.house_number,
                "PLZ": a.postal_code,
                "Ort": a.city,
                "Bundesland": a.state,
                "E-Mail": a.email,
                "Telefon": a.phone,
                "Website": a.website,
            }
            for a in authorities
        ]

    without_email_df = pd.DataFrame(to_rows(_authorities_without_email(db)), columns=columns)
    without_jurisdiction_df = pd.DataFrame(to_rows(_authorities_without_jurisdiction(db)), columns=columns)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        without_email_df.to_excel(writer, sheet_name="Ohne E-Mail", index=False)
        without_jurisdiction_df.to_excel(writer, sheet_name="Ohne Zuständigkeit", index=False)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        headers={
            "Content-Disposition": "attachment; filename=datenqualitaet_luecken.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
    )
