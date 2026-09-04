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
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.database import get_db_session
from app.models.authority import Authority
from app.models.authority_location import AuthorityLocation
from app.models.building import Building
from app.models.case import CaseBuilding, CaseRequest
from app.models.jurisdiction import Jurisdiction
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.request_type import RequestType

router = APIRouter()

MAX_ITEMS = 200

# Felder, die beim Zusammenführen von Duplikaten von der zu löschenden
# Zeile auf die verbleibende übertragen werden, sofern dort noch leer.
_MERGE_FIELDS = (
    "department_name", "street", "house_number", "postal_code", "city",
    "state", "email", "phone", "website", "source",
)

_BUILDING_MERGE_FIELDS = ("property_name", "district", "state", "ags", "notes", "internal_reference")

# Geografische Felder, die den fachlichen Geltungsbereich einer Zuständig-
# keitsregel ausmachen. Zwei Regeln mit identischem authority_id+request_
# type_id UND identischem Geltungsbereich sind derselbe fachliche Fall.
_JURISDICTION_GEO_FIELDS = ("ags", "municipality", "district", "postal_code", "street", "house_number", "state")
# Innerhalb einer solchen Gruppe: nur wenn auch diese Felder identisch sind,
# ist es ein echtes Duplikat (z.B. versehentlich zweimal importiert) - weichen
# sie ab, ist unklar welche Zeile korrekt ist (nie raten).
_JURISDICTION_COMPARE_FIELDS = ("priority", "matching_level", "valid_from", "valid_to")


def _serialize(a: Authority) -> dict:
    return {
        "authority_id": a.authority_id,
        "authority_name": a.authority_name,
        "city": a.city,
    }


def _serialize_building(b: Building) -> dict:
    return {
        "building_id": b.building_id,
        "street": b.street,
        "house_number": b.house_number,
        "postal_code": b.postal_code,
        "city": b.city,
    }


def _serialize_jurisdictions(
    jurisdictions: List[Jurisdiction], db: Session, limit: int
) -> List[dict]:
    """Reichert eine (schon auf `limit` gekürzte) Liste um Anzeige-Kontext an."""
    subset = jurisdictions[:limit]
    authority_ids = {j.authority_id for j in subset}
    request_type_ids = {j.request_type_id for j in subset}
    authorities_by_id = {
        a.authority_id: a.authority_name
        for a in db.query(Authority).filter(Authority.authority_id.in_(authority_ids)).all()
    } if authority_ids else {}
    request_types_by_id = {
        rt.request_type_id: rt.name
        for rt in db.query(RequestType).filter(RequestType.request_type_id.in_(request_type_ids)).all()
    } if request_type_ids else {}
    return [
        {
            "jurisdiction_id": j.jurisdiction_id,
            "authority_name": authorities_by_id.get(j.authority_id, j.authority_id),
            "request_type_name": request_types_by_id.get(j.request_type_id, j.request_type_id),
            "ags": j.ags,
            "municipality": j.municipality,
        }
        for j in subset
    ]


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


def _buildings_with_review_required(db: Session) -> List[Building]:
    """
    Gebäude, deren zuletzt durchgeführtes Matching (neuester Request) für
    mindestens eine Auskunftsart "Prüfung nötig" (REVIEW_REQUIRED) ergab -
    also keine eindeutige Behörde gefunden wurde.
    """
    latest_per_building = (
        db.query(Request.building_id, func.max(Request.created_at).label("latest_at"))
        .group_by(Request.building_id)
        .subquery()
    )
    latest_requests = (
        db.query(Request.request_id, Request.building_id)
        .join(
            latest_per_building,
            (Request.building_id == latest_per_building.c.building_id)
            & (Request.created_at == latest_per_building.c.latest_at),
        )
        .all()
    )
    if not latest_requests:
        return []

    request_to_building = {r.request_id: r.building_id for r in latest_requests}
    review_request_ids = {
        row[0]
        for row in db.query(RequestItem.request_id)
        .filter(RequestItem.request_id.in_(request_to_building.keys()))
        .filter(RequestItem.matching_status == "REVIEW_REQUIRED")
        .distinct()
        .all()
    }
    building_ids = {request_to_building[rid] for rid in review_request_ids}
    if not building_ids:
        return []

    return (
        db.query(Building)
        .filter(Building.building_id.in_(building_ids))
        .order_by(Building.city, Building.street)
        .all()
    )


def _building_has_real_progress(db: Session, building_id: str) -> bool:
    """
    True, wenn für dieses Gebäude schon einmal ein Schreiben tatsächlich als
    versendet markiert wurde oder eine Antwort hinterlegt ist - solche
    Gebäude werden von der automatischen Bereinigung übersprungen, auch wenn
    das aktuelle Matching "Prüfung nötig" zeigt (nie echte Arbeit löschen).
    """
    request_ids = [r[0] for r in db.query(Request.request_id).filter(Request.building_id == building_id).all()]
    if not request_ids:
        return False
    item_ids = [
        r[0]
        for r in db.query(RequestItem.request_item_id).filter(RequestItem.request_id.in_(request_ids)).all()
    ]
    if not item_ids:
        return False
    return (
        db.query(RequestItemProgress)
        .filter(RequestItemProgress.request_item_id.in_(item_ids))
        .filter(or_(RequestItemProgress.sent_at.isnot(None), RequestItemProgress.response_received_at.isnot(None)))
        .first()
        is not None
    )


def _authorities_unverified(db: Session) -> List[Authority]:
    """Aktive Behörden, die noch nie verifiziert wurden (last_verified_at leer)."""
    return (
        db.query(Authority)
        .filter(Authority.active.is_(True))
        .filter(Authority.last_verified_at.is_(None))
        .order_by(Authority.authority_name)
        .all()
    )


def _jurisdictions_orphaned(db: Session) -> List[Jurisdiction]:
    """
    Aktive Zuständigkeitsregeln, deren Behörde inzwischen deaktiviert wurde.
    Rein informativ (keine Auto-Aktion): unklar, ob die Regel deaktiviert
    oder die Behörde reaktiviert werden sollte - das muss ein Mensch
    entscheiden.
    """
    inactive_ids = {row[0] for row in db.query(Authority.authority_id).filter(Authority.active.is_(False)).all()}
    if not inactive_ids:
        return []
    return (
        db.query(Jurisdiction)
        .filter(Jurisdiction.active.is_(True))
        .filter(Jurisdiction.authority_id.in_(inactive_ids))
        .order_by(Jurisdiction.jurisdiction_id)
        .all()
    )


def _find_duplicate_jurisdiction_groups(db: Session):
    """
    Findet Gruppen aktiver Zuständigkeitsregeln mit identischem authority_id
    + request_type_id + identischem Geltungsbereich (_JURISDICTION_GEO_FIELDS).
    Weder Datenbank noch Import verhindern das aktuell strukturell - es gibt
    keine Unique-Constraint auf diese Kombination.

    Nur wenn zusätzlich _JURISDICTION_COMPARE_FIELDS (priority, matching_level,
    Gültigkeitszeitraum) ebenfalls übereinstimmen, ist es ein echtes Duplikat
    (z.B. versehentlich zweimal importiert) -> resolvable, älteste Zeile
    bleibt erhalten. Weichen diese Felder voneinander ab, ist unklar, welche
    Zeile korrekt ist -> needs_review, nie raten.
    """
    active = db.query(Jurisdiction).filter(Jurisdiction.active.is_(True)).all()

    def _norm(value):
        return value.strip() if isinstance(value, str) else value

    groups: dict = {}
    for j in active:
        key = (j.authority_id, j.request_type_id) + tuple(_norm(getattr(j, f)) for f in _JURISDICTION_GEO_FIELDS)
        groups.setdefault(key, []).append(j)

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        rows_sorted = sorted(rows, key=lambda j: j.created_at or datetime.min)
        keep = rows_sorted[0]
        remove = rows_sorted[1:]

        identical = all(
            all(getattr(dup, f) == getattr(keep, f) for f in _JURISDICTION_COMPARE_FIELDS) for dup in remove
        )
        if identical:
            resolvable.append({"keep": keep, "remove": remove})
        else:
            needs_review.append(keep)

    return resolvable, needs_review


def _find_duplicate_building_groups(db: Session):
    """
    Findet Gebäude mit identischer normalisierter Adresse (Straße, Haus-
    nummer, PLZ, Ort) unter verschiedenen building_ids. Weder Datenbank noch
    Import verhindern das aktuell strukturell - nur internal_reference ist
    eindeutig, und das ist nullable.

    Nur auflösbar, wenn GENAU EIN Gebäude der Gruppe bereits referenziert ist
    (Request oder Auftrag) - dieses bleibt erhalten, die referenzlosen werden
    gelöscht (fehlende Felder vorher übernommen, siehe _BUILDING_MERGE_FIELDS).
    Sind mehrere Gebäude der Gruppe JEWEILS referenziert, würde ein Automerge
    zwei unabhängige Anfrage-Historien stillschweigend zusammenwerfen - das
    landet in needs_review statt geraten zu werden. Bewusst konservativ bei
    postal_code: unterschiedliche (nicht nur fehlende) PLZ gruppieren nicht
    zusammen, auch wenn Straße/Hausnummer/Ort übereinstimmen.
    """
    buildings = db.query(Building).all()

    groups: dict = {}
    for b in buildings:
        key = (
            (b.street or "").strip().lower(),
            (b.house_number or "").strip().lower(),
            (b.postal_code or "").strip(),
            (b.city or "").strip().lower(),
        )
        groups.setdefault(key, []).append(b)

    referenced_ids = {row[0] for row in db.query(Request.building_id).distinct().all()}
    referenced_ids |= {row[0] for row in db.query(CaseBuilding.building_id).distinct().all()}

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        referenced = [b for b in rows if b.building_id in referenced_ids]

        if len(referenced) >= 2:
            needs_review.append(rows[0])
            continue

        if len(referenced) == 1:
            keep = referenced[0]
            remove = [b for b in rows if b.building_id != keep.building_id]
        else:
            rows_sorted = sorted(rows, key=lambda b: b.created_at or datetime.min)
            keep = rows_sorted[0]
            remove = rows_sorted[1:]

        resolvable.append({"keep": keep, "remove": remove})

    return resolvable, needs_review


@router.get("/data-quality/summary", tags=["DataQuality"])
def data_quality_summary(db: Session = Depends(get_db_session)):
    total_authorities = db.query(Authority).filter(Authority.active.is_(True)).count()
    without_email = _authorities_without_email(db)
    without_jurisdiction = _authorities_without_jurisdiction(db)
    without_address = _authorities_without_address(db)
    duplicate_groups, needs_review_groups = _find_duplicate_authority_groups(db)
    duplicate_items = [dup for g in duplicate_groups for dup in g["remove"]]
    review_buildings = _buildings_with_review_required(db)
    review_buildings_skipped = sum(1 for b in review_buildings if _building_has_real_progress(db, b.building_id))

    unverified = _authorities_unverified(db)
    orphaned_jurisdictions = _jurisdictions_orphaned(db)
    dup_jurisdiction_groups, dup_jurisdiction_needs_review = _find_duplicate_jurisdiction_groups(db)
    dup_jurisdiction_items = [dup for g in dup_jurisdiction_groups for dup in g["remove"]]
    dup_building_groups, dup_building_needs_review = _find_duplicate_building_groups(db)
    dup_building_items = [dup for g in dup_building_groups for dup in g["remove"]]

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
        "buildings_review_required": {
            "count": len(review_buildings),
            "items": [_serialize_building(b) for b in review_buildings[:MAX_ITEMS]],
            "needs_review_count": review_buildings_skipped,
        },
        "authorities_unverified": {
            "count": len(unverified),
            "items": [_serialize(a) for a in unverified[:MAX_ITEMS]],
        },
        "jurisdictions_orphaned": {
            "count": len(orphaned_jurisdictions),
            "items": _serialize_jurisdictions(orphaned_jurisdictions, db, MAX_ITEMS),
        },
        "duplicate_jurisdictions": {
            "count": len(dup_jurisdiction_items),
            "items": _serialize_jurisdictions(dup_jurisdiction_items, db, MAX_ITEMS),
            "needs_review_count": len(dup_jurisdiction_needs_review),
        },
        "duplicate_buildings": {
            "count": len(dup_building_items),
            "items": [_serialize_building(b) for b in dup_building_items[:MAX_ITEMS]],
            "needs_review_count": len(dup_building_needs_review),
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


@router.post("/data-quality/merge-duplicate-jurisdictions", tags=["DataQuality"])
def merge_duplicate_jurisdictions(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Zuständigkeits-Duplikate
    auf (siehe _find_duplicate_jurisdiction_groups). Die älteste Zeile pro
    Gruppe bleibt erhalten, die restlichen (nachweislich identischen)
    Duplikate werden gelöscht.
    """
    resolvable, needs_review = _find_duplicate_jurisdiction_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        for dup in group["remove"]:
            db.delete(dup)
            removed += 1
        group["keep"].updated_at = now

    db.commit()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/merge-duplicate-buildings", tags=["DataQuality"])
def merge_duplicate_buildings(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Gebäude-Duplikate auf
    (siehe _find_duplicate_building_groups). Das referenzierte (oder bei
    keiner Referenz: älteste) Gebäude bleibt erhalten und wird um fehlende
    Felder aus den Duplikaten ergänzt; die referenzlosen Duplikate werden
    gelöscht.
    """
    resolvable, needs_review = _find_duplicate_building_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        keep = group["keep"]
        for dup in group["remove"]:
            for field_name in _BUILDING_MERGE_FIELDS:
                if not getattr(keep, field_name) and getattr(dup, field_name):
                    setattr(keep, field_name, getattr(dup, field_name))
            db.delete(dup)
            removed += 1
        keep.updated_at = now

    db.commit()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/delete-review-required-buildings", tags=["DataQuality"])
def delete_review_required_buildings(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löscht Gebäude, deren zuletzt ermittelte Zuständigkeit
    als "Prüfung nötig" markiert ist (siehe _buildings_with_review_required),
    zusammen mit ihrer Anfrage-Historie (Requests/RequestItems/Progress) und
    Auftrags-Verknüpfungen. Gebäude, für die schon einmal ein Schreiben real
    versendet wurde oder eine Antwort hinterlegt ist, werden übersprungen und
    bleiben zur manuellen Prüfung stehen (nie echte Arbeit löschen).
    """
    candidates = _buildings_with_review_required(db)

    deleted = 0
    skipped = 0
    for building in candidates:
        if _building_has_real_progress(db, building.building_id):
            skipped += 1
            continue

        request_ids = [
            r[0] for r in db.query(Request.request_id).filter(Request.building_id == building.building_id).all()
        ]
        if request_ids:
            item_ids = [
                r[0]
                for r in db.query(RequestItem.request_item_id)
                .filter(RequestItem.request_id.in_(request_ids))
                .all()
            ]
            if item_ids:
                db.query(RequestItemProgress).filter(
                    RequestItemProgress.request_item_id.in_(item_ids)
                ).delete(synchronize_session=False)
            db.query(CaseRequest).filter(CaseRequest.request_id.in_(request_ids)).delete(synchronize_session=False)
            db.query(RequestItem).filter(RequestItem.request_id.in_(request_ids)).delete(synchronize_session=False)
            db.query(Request).filter(Request.building_id == building.building_id).delete(synchronize_session=False)

        db.query(CaseBuilding).filter(CaseBuilding.building_id == building.building_id).delete(
            synchronize_session=False
        )
        db.delete(building)
        deleted += 1

    db.commit()
    return {"deleted": deleted, "skipped": skipped}


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
    Exportiert alle Datenqualität-Kategorien als Excel-Datei mit einem
    Arbeitsblatt pro Kategorie – zur Weitergabe an Kolleg:innen, die die
    Lücken pflegen sollen.
    """

    authority_columns = [
        "Behörde", "Abteilung", "Straße", "Hausnummer", "PLZ", "Ort",
        "Bundesland", "E-Mail", "Telefon", "Website",
    ]

    def authority_rows(authorities: List[Authority]) -> List[dict]:
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

    building_columns = ["Straße", "Hausnummer", "PLZ", "Ort"]

    def building_rows(buildings: List[Building]) -> List[dict]:
        return [
            {
                "Straße": b.street,
                "Hausnummer": b.house_number,
                "PLZ": b.postal_code,
                "Ort": b.city,
            }
            for b in buildings
        ]

    jurisdiction_columns = ["Behörde", "Auskunftsart", "AGS", "Gemeinde"]

    def jurisdiction_rows(jurisdictions: List[Jurisdiction]) -> List[dict]:
        serialized = _serialize_jurisdictions(jurisdictions, db, len(jurisdictions))
        return [
            {
                "Behörde": j["authority_name"],
                "Auskunftsart": j["request_type_name"],
                "AGS": j["ags"],
                "Gemeinde": j["municipality"],
            }
            for j in serialized
        ]

    duplicate_authority_groups, _ = _find_duplicate_authority_groups(db)
    duplicate_authority_items = [dup for g in duplicate_authority_groups for dup in g["remove"]]
    duplicate_jurisdiction_groups, _ = _find_duplicate_jurisdiction_groups(db)
    duplicate_jurisdiction_items = [dup for g in duplicate_jurisdiction_groups for dup in g["remove"]]
    duplicate_building_groups, _ = _find_duplicate_building_groups(db)
    duplicate_building_items = [dup for g in duplicate_building_groups for dup in g["remove"]]

    sheets: List[tuple] = [
        ("Ohne E-Mail", pd.DataFrame(authority_rows(_authorities_without_email(db)), columns=authority_columns)),
        (
            "Ohne Zuständigkeit",
            pd.DataFrame(authority_rows(_authorities_without_jurisdiction(db)), columns=authority_columns),
        ),
        ("Ohne Adresse", pd.DataFrame(authority_rows(_authorities_without_address(db)), columns=authority_columns)),
        (
            "Nicht verifiziert",
            pd.DataFrame(authority_rows(_authorities_unverified(db)), columns=authority_columns),
        ),
        (
            "Behörden-Duplikate",
            pd.DataFrame(authority_rows(duplicate_authority_items), columns=authority_columns),
        ),
        (
            "Zuständigkeits-Duplikate",
            pd.DataFrame(jurisdiction_rows(duplicate_jurisdiction_items), columns=jurisdiction_columns),
        ),
        (
            "Verwaiste Zuständigkeiten",
            pd.DataFrame(jurisdiction_rows(_jurisdictions_orphaned(db)), columns=jurisdiction_columns),
        ),
        (
            "Gebäude-Duplikate",
            pd.DataFrame(building_rows(duplicate_building_items), columns=building_columns),
        ),
        (
            "Gebäude Prüfung nötig",
            pd.DataFrame(building_rows(_buildings_with_review_required(db)), columns=building_columns),
        ),
    ]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        headers={
            "Content-Disposition": "attachment; filename=datenqualitaet_luecken.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
    )
