"""
MailgunService

Versendet E-Mails über die Mailgun HTTP API. Nie stillschweigend
halb funktionieren: fehlt die Konfiguration oder schlägt der Versand fehl,
wird eine klare MailgunError geworfen statt eine Mail zu verlieren oder
fälschlich als versendet zu gelten.
"""

import logging
from dataclasses import dataclass

import requests

from app.config import MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_DRY_RUN, MAILGUN_FROM_ADDRESS

logger = logging.getLogger(__name__)


class MailgunError(Exception):
    """Wird geworfen, wenn eine E-Mail nicht versendet werden konnte."""
    pass


@dataclass
class SendResult:
    dry_run: bool
    mailgun_message_id: str | None


def send_email(
    to: str,
    subject: str,
    text: str,
    attachments: list[tuple[str, bytes]],
) -> SendResult:
    """
    Versendet eine E-Mail mit Anhängen über Mailgun.

    Im Dry-Run-Modus (MAILGUN_DRY_RUN=true) wird nur geloggt, was gesendet
    worden wäre - damit ist der komplette Bündel-Versand-Ablauf lokal ohne
    laufendes Mailgun-Konto testbar, ohne Risiko einer echten Mail.
    """
    if MAILGUN_DRY_RUN:
        logger.info(
            "[MAILGUN DRY RUN] an=%s betreff=%r anhänge=%s",
            to,
            subject,
            [filename for filename, _ in attachments],
        )
        return SendResult(dry_run=True, mailgun_message_id=None)

    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        raise MailgunError(
            "Mailgun ist nicht konfiguriert (MAILGUN_API_KEY/MAILGUN_DOMAIN fehlen)."
        )

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": MAILGUN_FROM_ADDRESS,
                "to": to,
                "subject": subject,
                "text": text,
            },
            files=[("attachment", (filename, content)) for filename, content in attachments],
            timeout=30,
        )
    except requests.RequestException as exc:
        raise MailgunError(f"Mailgun-API nicht erreichbar: {exc}") from exc

    if response.status_code != 200:
        raise MailgunError(
            f"Mailgun-API-Fehler ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    return SendResult(dry_run=False, mailgun_message_id=data.get("id"))
