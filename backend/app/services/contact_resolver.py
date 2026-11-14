"""Resolve email recipients per authority *and* request type.

The flat Authority.email is retained as a research/fallback contact. Only a
reviewed, sourced channel for the requested service can be used for email.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional
from urllib.parse import urlsplit

from email_validator import EmailNotValidError, validate_email
from sqlalchemy.orm import Session

from app.models.authority import Authority
from app.models.authority_contact_channel import AuthorityContactChannel, ChannelType


def normalize_email(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized
    except EmailNotValidError:
        return None


def is_source_url(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and not parsed.username
        )
    except ValueError:
        return False


def channel_is_verified(channel: AuthorityContactChannel) -> bool:
    verified = channel.last_verified_at
    if verified is None or not is_source_url(channel.source_url):
        return False
    if verified.tzinfo is not None:
        verified = verified.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.utcnow()
    return now - timedelta(days=365) <= verified <= now


@dataclass(frozen=True)
class ResolvedContact:
    email: Optional[str] = None
    status: str = "MISSING"
    can_send: bool = False
    source_url: Optional[str] = None
    channel_id: Optional[int] = None
    fallback_email: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ContactResolver:
    """Batch-load channels once; resolve without modifying ORM objects."""

    def __init__(self, db: Session, authority_ids: Iterable[str]):
        self.channels = defaultdict(list)
        ids = set(authority_ids)
        if ids:
            for channel in (
                db.query(AuthorityContactChannel)
                .filter(
                    AuthorityContactChannel.authority_id.in_(ids),
                    AuthorityContactChannel.active.is_(True),
                )
                .all()
            ):
                self.channels[channel.authority_id].append(channel)

    def resolve(
        self, authority: Optional[Authority], request_type_id: str
    ) -> ResolvedContact:
        if authority is None or not authority.active:
            return ResolvedContact(
                status="MISSING" if authority is None else "INACTIVE"
            )
        fallback = normalize_email(authority.email)
        candidates = [
            c
            for c in self.channels[authority.authority_id]
            if c.request_type_id == request_type_id
            and c.channel_type == ChannelType.EMAIL
            and normalize_email(c.value)
        ]
        if not candidates:
            return ResolvedContact(
                status="GENERAL_ONLY" if fallback else "MISSING",
                fallback_email=fallback,
            )

        # An unreviewed preferred candidate must never displace a reviewed one.
        reviewed = [c for c in candidates if channel_is_verified(c)]
        candidates = reviewed or candidates
        preferred = [c for c in candidates if c.preferred]
        candidates = preferred or candidates
        addresses = {normalize_email(c.value).casefold() for c in candidates}
        if len(addresses) != 1:
            return ResolvedContact(status="CONFLICT", fallback_email=fallback)
        channel = min(candidates, key=lambda c: c.id)
        verified = channel_is_verified(channel)
        return ResolvedContact(
            email=normalize_email(channel.value),
            status="VERIFIED" if verified else "UNVERIFIED",
            can_send=verified,
            source_url=channel.source_url,
            channel_id=channel.id,
            fallback_email=fallback,
        )
