"""
API Routes: Datenqualität

Liefert eine Übersicht über Lücken in den Stammdaten (z.B. Behörden ohne
E-Mail-Adresse oder Behörden, die in keiner Zuständigkeit referenziert
werden), damit diese proaktiv gepflegt werden können statt erst beim
Matching als NO_MATCH/"keine E-Mail" aufzufallen.
"""

import io
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.database import get_db_session
from app.models.authority import Authority
from app.models.authority_location import AuthorityLocation
from app.models.jurisdiction import Jurisdiction
from app.models.request import RequestItem

router = APIRouter()

MAX_ITEMS = 200

# Felder, die beim Zusammenführen von Duplikaten von der zu löschenden
# Zeile auf die verbleibende übertragen werden, sofern dort noch leer.
_MERGE_FIELDS = (
    "department_name", "street", "house_number", "postal_code", "city",
    "state", "email", "phone", "website", "source",
)


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


def _authorities_without_address(db: Session) -> List[Authority]:
    """
    Behörden ganz ohne Straße UND Ort. Wichtig: genau diese führen beim
    Kartenpin-Geocoding sonst zu einer irreführenden Auflösung auf den
    geografischen Mittelpunkt Deutschlands (siehe get_authority_location).
    """
    return (
        db.query(Authority)
        .filter(Authority.active.is_(True))
        .filter(or_(Authority.street.is_(None), Authority.street == ""))
        .filter(or_(Authority.city.is_(None), Authority.city == ""))
        .order_by(Authority.authority_name)
        .all()
    )


def _is_unlocated(a: Authority) -> bool:
    return not (a.street and a.street.strip()) and not (a.city and a.city.strip())


def _find_duplicate_authority_groups(db: Session):
    """
    Findet Namens-Gruppen mit genau einer "unlokalisierten" Behörde (weder
    Straße noch Ort hinterlegt) und mindestens einer weiteren, aktiven
    Behörde gleichen Namens, die eine Adresse hat.

    Typischer Entstehungsweg: ein Import ohne Ortsangabe legt eine Behörde
    ohne Adresse an; ein späterer fill_gaps-Import mit dieser Behörde
    (jetzt mit Ort) findet die alte Zeile nicht (Abgleich lief über
    Name+Ort) und legt fälschlich eine zweite, doppelte Behörde an. Die
    unlokalisierte Zeile bleibt i.d.R. die "echte", weil Zuständigkeits-
    regeln bereits auf sie zeigen können - deshalb wird in sie gemergt,
    nicht umgekehrt.

    Gibt (resolvable, needs_review) zurück. Aufgelöst wird nur, wenn die zu
    löschende(n) Zeile(n) nachweislich von keiner Zuständigkeitsregel und
    keinem Anfrage-Item referenziert werden - alle anderen Fälle landen in
    needs_review statt geraten zu werden.
    """
    active = db.query(Authority).filter(Authority.active.is_(True)).all()
    referenced_ids = {row[0] for row in db.query(Jurisdiction.authority_id).distinct().all()}
    referenced_ids |= {
        row[0]
        for row in db.query(RequestItem.authority_id).filter(RequestItem.authority_id.isnot(None)).distinct().all()
    }

    groups: dict = {}
    for a in active:
        groups.setdefault((a.authority_name or "").strip().lower(), []).append(a)

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        stubs = [a for a in rows if _is_unlocated(a)]
        full = [a for a in rows if not _is_unlocated(a)]
        if len(stubs) != 1 or not full:
            continue

        keep = stubs[0]
        if any(dup.authority_id in referenced_ids for dup in full):
            needs_review.append(keep)
            continue

        resolvable.append({"keep": keep, "remove": full})

    return resolvable, needs_review


@router.get("/data-quality/summary", tags=["DataQuality"])
def data_quality_summary(db: Session = Depends(get_db_session)):
    total_authorities = db.query(Authority).filter(Authority.active.is_(True)).count()
    without_email = _authorities_without_email(db)
    without_jurisdiction = _authorities_without_jurisdiction(db)
    without_address = _authorities_without_address(db)
    duplicate_groups, needs_review_groups = _find_duplicate_authority_groups(db)
    duplicate_items = [dup for g in duplicate_groups for dup in g["remove"]]

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
        "authorities_without_address": {
            "count": len(without_address),
            "items": [_serialize(a) for a in without_address[:MAX_ITEMS]],
        },
        "duplicate_authorities": {
            "count": len(duplicate_items),
            "items": [_serialize(a) for a in duplicate_items[:MAX_ITEMS]],
            "needs_review_count": len(needs_review_groups),
        },
    }


@router.post("/data-quality/merge-duplicate-authorities", tags=["DataQuality"])
def merge_duplicate_authorities(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Behörden-Duplikate auf
    (siehe _find_duplicate_authority_groups). Die unlokalisierte Zeile
    bleibt bestehen und wird um die Felder der Duplikat-Zeile ergänzt
    (nur dort, wo sie selbst noch leer ist); die Duplikat-Zeile(n) werden
    danach gelöscht.
    """
    resolvable, needs_review = _find_duplicate_authority_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        keep = group["keep"]
        for dup in group["remove"]:
            for field_name in _MERGE_FIELDS:
                if not getattr(keep, field_name) and getattr(dup, field_name):
                    setattr(keep, field_name, getattr(dup, field_name))
            db.delete(dup)
            removed += 1
        keep.updated_at = now

    db.commit()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/clear-bad-geocoding", tags=["DataQuality"])
def clear_bad_geocoding(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: entfernt gecachte Kartenkoordinaten von Behörden ohne
    hinterlegte Adresse. Bis zu einem Fix in get_authority_location konnten
    solche Behörden fälschlich auf den geografischen Mittelpunkt Deutschlands
    (nahe Erfurt) geocodiert werden – dieser Aufruf räumt bereits gecachte
    Fehltreffer auf, damit die Karte sie danach korrekt als "keine Adresse"
    behandelt statt einen falschen Pin zu zeigen.
    """
    affected_ids = [a.authority_id for a in _authorities_without_address(db)]
    if not affected_ids:
        return {"deleted": 0}

    deleted = (
        db.query(AuthorityLocation)
        .filter(AuthorityLocation.authority_id.in_(affected_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted}


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
    without_address_df = pd.DataFrame(to_rows(_authorities_without_address(db)), columns=columns)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        without_email_df.to_excel(writer, sheet_name="Ohne E-Mail", index=False)
        without_jurisdiction_df.to_excel(writer, sheet_name="Ohne Zuständigkeit", index=False)
        without_address_df.to_excel(writer, sheet_name="Ohne Adresse", index=False)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        headers={
            "Content-Disposition": "attachment; filename=datenqualitaet_luecken.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
    )
