"""Import, Prüfung und Nachrecherche von belegten Kontaktvorschlägen."""
from datetime import date, datetime, timezone
import hashlib
import io
import json
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.auth import get_current_user, require_main
from app.database import get_db_session
from app.models.authority import Authority
from app.models.authority_contact_channel import AuthorityContactChannel
from app.models.contact_review import ContactReview
from app.models.jurisdiction import Jurisdiction
from app.models.request_type import RequestType
from app.models.user import User
from app.services.contact_resolver import is_source_url, normalize_email
from app.services.dq_cache import clear_data_quality_cache

router = APIRouter(dependencies=[Depends(require_main)])
MAX_FILE = 8 * 1024 * 1024


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locator: str = Field(min_length=1, max_length=300)
    evidence_quote: str = Field(min_length=1, max_length=2000)


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    authority_id: str = Field(default="", max_length=50)
    authority_name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    request_type_id: str = Field(min_length=1, max_length=50)
    ags: list[str] = Field(min_length=1, max_length=1000)
    channel_type: Literal["EMAIL", "PORTAL"] = "EMAIL"
    value: str = Field(min_length=1, max_length=4096)
    source_url: str = Field(min_length=1, max_length=4096)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    evidence: list[Evidence] = Field(min_length=1, max_length=12)
    reasons: list[str] = Field(default_factory=list, max_length=20)


class ImportDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["civeloq-contact-review-1"]
    verification_status: Literal["UNVERIFIED"]
    generated_at: Optional[datetime] = None
    proposals: list[Proposal] = Field(max_length=2000)


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["CONFIRM", "REJECT", "RESEARCH"]
    version: int = Field(ge=1)
    source_checked: bool = False
    preferred: bool = False
    comment: str = Field(default="", max_length=1000)


def valid_rules(db, authority_id, request_type_id):
    today = date.today()
    return db.query(Jurisdiction).filter(
        Jurisdiction.authority_id == authority_id,
        Jurisdiction.request_type_id == request_type_id,
        Jurisdiction.active.is_(True),
        or_(Jurisdiction.valid_from.is_(None), Jurisdiction.valid_from <= today),
        or_(Jurisdiction.valid_to.is_(None), Jurisdiction.valid_to >= today),
    )


def resolve_target(db, p):
    query = db.query(Authority).filter_by(active=True)
    if p.authority_id:
        matches = query.filter_by(authority_id=p.authority_id).all()
    else:
        matches = query.filter_by(authority_name=p.authority_name, city=p.city).limit(2).all()
    if len(matches) != 1:
        raise ValueError("Behördenidentität fehlt oder ist mehrdeutig")
    a = matches[0]
    if (a.authority_name, a.city) != (p.authority_name, p.city):
        raise ValueError("Behördenname/Ort stimmen nicht mehr mit dem Bestand überein")
    if not db.query(RequestType).filter_by(request_type_id=p.request_type_id, active=True).first():
        raise ValueError("Auskunftsart ist unbekannt oder inaktiv")
    known = {r.ags for r in valid_rules(db, a.authority_id, p.request_type_id).all()}
    if not set(p.ags) <= known:
        raise ValueError("Für diese Behörde/Auskunftsart/AGS fehlt eine bestehende gültige Regel")
    return a


def import_proposals(db, document):
    summary = {"imported": 0, "duplicates": 0, "needs_review": 0, "details": []}
    for index, p in enumerate(document.proposals, 1):
        try:
            a = resolve_target(db, p)
            if not is_source_url(p.source_url):
                raise ValueError("HTTP(S)-Quellen-URL ist erforderlich")
            if p.observed_at.tzinfo is None:
                raise ValueError("Abrufzeit benötigt eine Zeitzone")
            observed = p.observed_at.astimezone(timezone.utc).replace(tzinfo=None)
            if observed > datetime.utcnow():
                raise ValueError("Abrufzeit liegt in der Zukunft")
            if p.channel_type == "EMAIL":
                value = normalize_email(p.value)
                if not value:
                    raise ValueError("Ungültige E-Mail-Adresse")
            else:
                value = p.value.strip()
                if not is_source_url(value):
                    raise ValueError("Portal benötigt eine HTTP(S)-Adresse")
            if any(len(reason) > 500 for reason in p.reasons):
                raise ValueError("Prüfgrund ist zu lang")
            identity = [
                a.authority_id,
                p.request_type_id,
                p.channel_type,
                value,
                p.source_url.strip(),
                p.source_sha256,
            ]
            key = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
            existing = db.get(ContactReview, key)
            if existing is not None:
                summary["duplicates"] += 1
                continue
            row = ContactReview(
                proposal_id=key,
                authority_id=a.authority_id,
                request_type_id=p.request_type_id,
                channel_type=p.channel_type,
                value=value,
                source_url=p.source_url.strip(),
                source_sha256=p.source_sha256,
                observed_at=observed,
                evidence=json.dumps([e.model_dump() for e in p.evidence], ensure_ascii=False),
                reasons=json.dumps(p.reasons, ensure_ascii=False),
                ags=json.dumps(sorted(set(p.ags))),
                status="PENDING",
                version=1,
                history="[]",
            )
            try:
                with db.begin_nested():
                    db.add(row)
                    db.flush()
            except IntegrityError as error:
                if db.get(ContactReview, key) is None:
                    raise HTTPException(
                        409, "Bestand wurde gleichzeitig verändert. Bitte erneut laden."
                    ) from error
                summary["duplicates"] += 1
                continue
            summary["imported"] += 1
        except ValueError as error:
            summary["needs_review"] += 1
            summary["details"].append({"row": index, "reason": str(error)})
    db.commit()
    return summary


@router.post("/contact-reviews/import", tags=["Contact reviews"])
def import_review_file(file: UploadFile, db: Session = Depends(get_db_session)):
    # The synchronous route runs in FastAPI's worker pool, keeping long imports
    # off the event loop. UploadFile.file is the bounded spooled upload.
    raw = file.file.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise HTTPException(413, "Maximal 8 MB je Prüfdatei")
    try:
        document = ImportDocument.model_validate_json(raw)
    except (ValidationError, ValueError) as error:
        raise HTTPException(
            422, "Ungültige Prüfdatei; erwartet wird civeloq_pruefung.json aus Bot 2.6"
        ) from error
    return import_proposals(db, document)


def serialize(p, a, request_name, channels):
    return {
        "proposal_id": p.proposal_id,
        "authority_id": p.authority_id,
        "authority_name": a.authority_name,
        "city": a.city,
        "request_type_id": p.request_type_id,
        "request_type_name": request_name,
        "channel_type": p.channel_type,
        "value": p.value,
        "source_url": p.source_url,
        "observed_at": p.observed_at.isoformat() + "Z",
        "source_sha256": p.source_sha256,
        "evidence": json.loads(p.evidence),
        "reasons": json.loads(p.reasons),
        "ags": json.loads(p.ags),
        "status": p.status,
        "version": p.version,
        "history": json.loads(p.history),
        "channel_id": p.channel_id,
        "stock": {
            "email": a.email,
            "phone": a.phone,
            "street": a.street,
            "house_number": a.house_number,
            "postal_code": a.postal_code,
            "city": a.city,
            "department_name": a.department_name,
        },
        "current_channels": [c.to_dict() for c in channels if c.request_type_id == p.request_type_id],
    }


@router.get("/contact-reviews", tags=["Contact reviews"])
def list_reviews(
    status: Literal["OPEN", "PENDING", "RESEARCH", "CONFIRMED", "REJECTED", "ALL"] = "OPEN",
    request_type_id: Optional[str] = None,
    search: str = Query("", max_length=200),
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
):
    query = (
        db.query(ContactReview, Authority, RequestType.name)
        .join(
            Authority,
            Authority.authority_id == ContactReview.authority_id,
        )
        .join(RequestType, RequestType.request_type_id == ContactReview.request_type_id)
    )
    if status == "OPEN":
        query = query.filter(ContactReview.status.in_(["PENDING", "RESEARCH"]))
    elif status != "ALL":
        query = query.filter(ContactReview.status == status)
    if request_type_id:
        query = query.filter(ContactReview.request_type_id == request_type_id)
    if search.strip():
        term = "%" + search.strip() + "%"
        query = query.filter(
            or_(
                Authority.authority_name.ilike(term),
                Authority.city.ilike(term),
                ContactReview.value.ilike(term),
            )
        )
    total = query.count()
    rows = (
        query.order_by(ContactReview.updated_at.desc(), ContactReview.proposal_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    authority_ids = {p.authority_id for p, _, _ in rows}
    channels = (
        db.query(AuthorityContactChannel)
        .filter(AuthorityContactChannel.authority_id.in_(authority_ids))
        .all()
        if authority_ids
        else []
    )
    grouped = {}
    for c in channels:
        grouped.setdefault(c.authority_id, []).append(c)
    counts = dict(db.query(ContactReview.status, func.count()).group_by(ContactReview.status).all())
    return {
        "items": [serialize(p, a, name, grouped.get(a.authority_id, [])) for p, a, name in rows],
        "total": total,
        "counts": counts,
    }


@router.get("/contact-reviews/export-needs", tags=["Contact reviews"])
def export_research_needs(db: Session = Depends(get_db_session)):
    rows = db.query(ContactReview, Authority).join(Authority).filter(ContactReview.status == "RESEARCH").all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Fachkontakte prüfen"
    ws.append(
        [
            "Auskunftsart",
            "AGS",
            "Gemeinde",
            "Behörde",
            "Abteilung",
            "Straße",
            "Hausnummer",
            "PLZ",
            "Ort",
            "E-Mail",
            "Telefon",
            "Website",
            "Quelle",
            "Kontaktstatus",
            "Behörden-ID",
        ]
    )
    seen = set()
    for p, a in rows:
        pair = (a.authority_id, p.request_type_id)
        if pair in seen:
            continue
        seen.add(pair)
        ags = sorted({j.ags for j in valid_rules(db, *pair).all() if j.ags})
        values = [
            p.request_type_id,
            ", ".join(ags),
            "",
            a.authority_name,
            a.department_name,
            a.street,
            a.house_number,
            a.postal_code,
            a.city,
            a.email,
            a.phone,
            a.website,
            p.source_url,
            "RESEARCH",
            a.authority_id,
        ]
        for col, value in enumerate(values, 1):
            cell = ws.cell(ws.max_row + 1 if col == 1 else ws.max_row, col, value or "")
            cell.data_type = "s"
            cell.number_format = "@"
    stream = io.BytesIO()
    wb.save(stream)
    wb.close()
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="fachkontakte_nachrecherche.xlsx"'},
    )


@router.post("/contact-reviews/{proposal_id}/decision", tags=["Contact reviews"])
def decide_review(
    proposal_id: str,
    payload: Decision,
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    p = db.get(ContactReview, proposal_id)
    if p is None:
        raise HTTPException(404, "Vorschlag nicht gefunden")
    if p.version != payload.version or p.status not in {"PENDING", "RESEARCH"}:
        raise HTTPException(409, "Vorschlag wurde bereits bearbeitet. Bitte neu laden.")
    if payload.decision == "CONFIRM" and not payload.source_checked:
        raise HTTPException(422, "Quelle öffnen und Zuordnung zur Auskunftsart ausdrücklich prüfen")
    status = {"CONFIRM": "CONFIRMED", "REJECT": "REJECTED", "RESEARCH": "RESEARCH"}[payload.decision]
    now = datetime.utcnow()
    actor = current_user.email if current_user else "Haupt-Account"
    history = json.loads(p.history) + [
        {
            "at": now.isoformat() + "Z",
            "actor": actor,
            "decision": payload.decision,
            "comment": payload.comment,
            "version": p.version + 1,
        }
    ]
    claimed = (
        db.query(ContactReview)
        .filter(
            ContactReview.proposal_id == proposal_id,
            ContactReview.version == payload.version,
            ContactReview.status.in_(["PENDING", "RESEARCH"]),
        )
        .update(
            {
                "status": status,
                "version": payload.version + 1,
                "updated_at": now,
                "history": json.dumps(history, ensure_ascii=False),
            },
            synchronize_session=False,
        )
    )
    if claimed != 1:
        db.rollback()
        raise HTTPException(409, "Vorschlag wurde gleichzeitig bearbeitet. Bitte neu laden.")
    if payload.decision == "CONFIRM":
        a = db.query(Authority).filter_by(authority_id=p.authority_id).with_for_update().first()
        rt = db.get(RequestType, p.request_type_id)
        known = {r.ags for r in valid_rules(db, p.authority_id, p.request_type_id).all()}
        if a is None or rt is None or not a.active or not rt.active or not set(json.loads(p.ags)) <= known:
            db.rollback()
            raise HTTPException(409, "Bestandszuordnung hat sich geändert; erneut recherchieren")
        channel = (
            db.query(AuthorityContactChannel)
            .filter_by(
                authority_id=p.authority_id,
                request_type_id=p.request_type_id,
                channel_type=p.channel_type,
                value=p.value,
            )
            .first()
        )
        if channel is None:
            channel = AuthorityContactChannel(
                authority_id=p.authority_id,
                request_type_id=p.request_type_id,
                channel_type=p.channel_type,
                value=p.value,
                preferred=False,
            )
            db.add(channel)
        if payload.preferred:
            db.query(AuthorityContactChannel).filter_by(
                authority_id=p.authority_id, request_type_id=p.request_type_id, channel_type=p.channel_type
            ).update({"preferred": False})
        channel.active = True
        channel.preferred = bool(payload.preferred or channel.preferred)
        channel.source_url = p.source_url
        channel.source = "In Kontaktprüfung bestätigt"
        channel.last_verified_at = now
        channel.verified_by = actor
        db.flush()
        db.query(ContactReview).filter_by(proposal_id=p.proposal_id).update({"channel_id": channel.id})
    db.commit()
    db.expire_all()
    clear_data_quality_cache()
    return {"proposal_id": proposal_id, "status": status, "version": payload.version + 1}
