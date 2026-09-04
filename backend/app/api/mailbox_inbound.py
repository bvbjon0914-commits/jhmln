"""
API Routes: Postfach-Empfang (Mailgun Inbound-Webhook + manuelle Zuordnung)

Der Webhook selbst (POST /mailbox/inbound) kann sich nicht per Cookie-Session
authentisieren - Mailgun ruft ihn direkt auf. Absicherung stattdessen über
Mailguns HMAC-Signatur. Alle übrigen Routen hier sind Verwaltungsrouten für
den Haupt-Account (jeweils einzeln mit require_main gesichert, das deckt
implizit auch "eingeloggt" ab) und deshalb bewusst NICHT über
dependencies=protected in main.py registriert - siehe dortige Kommentare.

Automatische Zuordnung nur, wenn ALLE drei Bedingungen erfüllt sind: genau
ein Aktenzeichen im Betreff/Text gefunden, dieses löst auf ein echtes
RequestItem auf, UND die Mail hat genau einen PDF-Anhang. Mehrere PDF-
Anhänge werden NIE automatisch zugeordnet, selbst bei eindeutigem
Aktenzeichen - welches PDF "die" Antwort ist, wäre sonst geraten. Solche
Fälle (und alle anderen nicht eindeutigen) landen in der Warteschlange zur
manuellen Zuordnung.
"""

import hashlib
import hmac
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.api.matching import _get_or_create_progress
from app.config import MAILGUN_WEBHOOK_SIGNING_KEY
from app.database import get_db_session
from app.models.aktenzeichen import RequestItemReference
from app.models.authority import Authority
from app.models.building import Building
from app.models.inbound_email import InboundEmail, InboundEmailAttachment
from app.models.request import Request as RequestRecord, RequestItem
from app.models.request_type import RequestType

router = APIRouter()

AKTENZEICHEN_RE = re.compile(r"VNV-\d{4}-\d{4}-[A-Z0-9_]+-\d+")


class AssignPayload(BaseModel):
    request_item_id: str
    attachment_id: Optional[int] = None


def _verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    if not MAILGUN_WEBHOOK_SIGNING_KEY or not timestamp or not token or not signature:
        return False
    expected = hmac.new(
        key=MAILGUN_WEBHOOK_SIGNING_KEY.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _is_pdf(filename: Optional[str], content_type: Optional[str]) -> bool:
    if content_type and content_type.lower() == "application/pdf":
        return True
    return bool(filename) and filename.lower().endswith(".pdf")


@router.post("/mailbox/inbound", tags=["Mailbox"])
async def receive_inbound_email(request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()

    timestamp = str(form.get("timestamp", ""))
    token = str(form.get("token", ""))
    signature = str(form.get("signature", ""))
    if not _verify_mailgun_signature(timestamp, token, signature):
        raise HTTPException(status_code=403, detail="Ungültige Mailgun-Signatur")

    from_address = str(form.get("sender") or form.get("from") or "")
    subject = str(form.get("subject") or "")
    body_text = str(form.get("body-plain") or "")

    attachments = []
    for key, value in form.multi_items():
        if key.startswith("attachment") and hasattr(value, "read"):
            content = await value.read()
            attachments.append(
                {
                    "filename": value.filename or key,
                    "content_type": value.content_type,
                    "content": content,
                }
            )

    pdf_attachments = [a for a in attachments if _is_pdf(a["filename"], a["content_type"])]
    aktenzeichen_matches = set(AKTENZEICHEN_RE.findall(subject)) or set(AKTENZEICHEN_RE.findall(body_text))

    matched_item_id = None
    auto_matched = False

    if len(aktenzeichen_matches) == 1 and len(pdf_attachments) == 1:
        candidate = next(iter(aktenzeichen_matches))
        ref = db.query(RequestItemReference).filter(RequestItemReference.aktenzeichen == candidate).first()
        if ref:
            progress = _get_or_create_progress(db, ref.request_item_id)
            progress.response_document = pdf_attachments[0]["content"]
            progress.response_document_filename = pdf_attachments[0]["filename"] or "antwort.pdf"
            progress.response_received_at = datetime.utcnow()
            matched_item_id = ref.request_item_id
            auto_matched = True

    inbound = InboundEmail(
        from_address=from_address,
        subject=subject,
        body_text=body_text,
        matched_request_item_id=matched_item_id,
        auto_matched=auto_matched,
    )
    db.add(inbound)
    db.flush()

    for a in attachments:
        db.add(
            InboundEmailAttachment(
                inbound_email_id=inbound.id,
                filename=a["filename"],
                content_type=a["content_type"],
                content=a["content"],
            )
        )

    db.commit()
    return {"id": inbound.id, "matched": auto_matched, "matched_request_item_id": matched_item_id}


@router.get("/mailbox/inbound/pending", tags=["Mailbox"])
def list_pending_inbound_emails(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """Nur Haupt-Account: Warteschlange nicht automatisch zugeordneter Antworten."""
    emails = (
        db.query(InboundEmail)
        .filter(InboundEmail.matched_request_item_id.is_(None))
        .order_by(InboundEmail.received_at.desc())
        .all()
    )
    return [e.to_dict() for e in emails]


@router.get("/mailbox/inbound/attachments/{attachment_id}/download", tags=["Mailbox"])
def download_inbound_attachment(
    attachment_id: int, db: Session = Depends(get_db_session), _: None = Depends(require_main)
):
    """Nur Haupt-Account: Anhang einer eingehenden E-Mail zur Sichtung vor der Zuordnung."""
    attachment = db.query(InboundEmailAttachment).filter(InboundEmailAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Anhang nicht gefunden")
    return Response(
        content=attachment.content,
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{attachment.filename or "anhang.pdf"}"'},
    )


@router.get("/mailbox/lookup-aktenzeichen", tags=["Mailbox"])
def lookup_aktenzeichen(q: str, db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: sucht RequestItems anhand eines Aktenzeichen-Teiltexts,
    für die manuelle Zuordnung einer Warteschlangen-E-Mail. Gibt genug Kontext
    zurück (Gebäude, Behörde, Auskunftsart), damit der Mensch die richtige
    Zeile visuell bestätigen kann, statt blind eine ID einzutippen.
    """
    q = q.strip()
    if len(q) < 3:
        return []

    refs = (
        db.query(RequestItemReference)
        .filter(RequestItemReference.aktenzeichen.ilike(f"%{q}%"))
        .limit(25)
        .all()
    )
    if not refs:
        return []

    item_ids = [r.request_item_id for r in refs]
    items_by_id = {
        i.request_item_id: i
        for i in db.query(RequestItem).filter(RequestItem.request_item_id.in_(item_ids)).all()
    }
    request_ids = {i.request_id for i in items_by_id.values()}
    requests_by_id = {
        r.request_id: r for r in db.query(RequestRecord).filter(RequestRecord.request_id.in_(request_ids)).all()
    }
    building_ids = {r.building_id for r in requests_by_id.values()}
    buildings_by_id = {
        b.building_id: b for b in db.query(Building).filter(Building.building_id.in_(building_ids)).all()
    }
    authority_ids = {i.authority_id for i in items_by_id.values() if i.authority_id}
    authorities_by_id = {
        a.authority_id: a for a in db.query(Authority).filter(Authority.authority_id.in_(authority_ids)).all()
    } if authority_ids else {}
    request_type_ids = {i.request_type_id for i in items_by_id.values()}
    request_types_by_id = {
        rt.request_type_id: rt
        for rt in db.query(RequestType).filter(RequestType.request_type_id.in_(request_type_ids)).all()
    }

    results = []
    for ref in refs:
        item = items_by_id.get(ref.request_item_id)
        if not item:
            continue
        req = requests_by_id.get(item.request_id)
        building = buildings_by_id.get(req.building_id) if req else None
        authority = authorities_by_id.get(item.authority_id) if item.authority_id else None
        request_type = request_types_by_id.get(item.request_type_id)
        results.append(
            {
                "request_item_id": item.request_item_id,
                "aktenzeichen": ref.aktenzeichen,
                "building_label": f"{building.street} {building.house_number}, {building.city}" if building else None,
                "authority_name": authority.authority_name if authority else None,
                "request_type_name": request_type.name if request_type else item.request_type_id,
            }
        )
    return results


@router.post("/mailbox/inbound/{inbound_id}/assign", tags=["Mailbox"])
def assign_inbound_email(
    inbound_id: int,
    payload: AssignPayload,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_main),
):
    """
    Nur Haupt-Account: ordnet eine in der Warteschlange stehende E-Mail
    manuell einem RequestItem zu - gleiche "Anhang in RequestItemProgress
    kopieren"-Logik wie der Auto-Match-Pfad. Bei mehreren PDF-Anhängen muss
    attachment_id angegeben werden (der Mensch entscheidet, welcher der
    richtige ist - das System rät nie).
    """
    inbound = db.query(InboundEmail).filter(InboundEmail.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Eingehende E-Mail nicht gefunden")
    if inbound.matched_request_item_id:
        raise HTTPException(status_code=400, detail="Diese E-Mail ist bereits zugeordnet")

    item = db.query(RequestItem).filter(RequestItem.request_item_id == payload.request_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"RequestItem {payload.request_item_id} nicht gefunden")

    attachments = (
        db.query(InboundEmailAttachment).filter(InboundEmailAttachment.inbound_email_id == inbound_id).all()
    )
    pdf_attachments = [a for a in attachments if _is_pdf(a.filename, a.content_type)]

    if len(pdf_attachments) == 0:
        raise HTTPException(status_code=400, detail="Diese E-Mail hat keinen PDF-Anhang")
    if len(pdf_attachments) == 1:
        chosen = pdf_attachments[0]
    else:
        if payload.attachment_id is None:
            raise HTTPException(
                status_code=400,
                detail="Mehrere PDF-Anhänge - bitte attachment_id des richtigen Anhangs angeben",
            )
        chosen = next((a for a in pdf_attachments if a.id == payload.attachment_id), None)
        if not chosen:
            raise HTTPException(status_code=400, detail="Anhang nicht gefunden")

    progress = _get_or_create_progress(db, payload.request_item_id)
    progress.response_document = chosen.content
    progress.response_document_filename = chosen.filename or "antwort.pdf"
    progress.response_received_at = datetime.utcnow()

    inbound.matched_request_item_id = payload.request_item_id
    inbound.auto_matched = False
    db.commit()

    return {"ok": True}
