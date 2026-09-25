"""
Regressionstests für den Mailgun-Posteingangs-Webhook, insbesondere den
Idempotenz-Fix (Priorität 2 des Auditberichts, Befund "Idempotenz").
"""
import hashlib
import hmac
import os

import pytest

from app.models.inbound_email import InboundEmail

SIGNING_KEY = os.environ["MAILGUN_WEBHOOK_SIGNING_KEY"]


def _sign(timestamp: str, token: str) -> str:
    return hmac.new(
        key=SIGNING_KEY.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def webhook_form(message_id="msg-1", timestamp="1700000000", token="tok-1", **extra):
    data = {
        "timestamp": timestamp,
        "token": token,
        "signature": _sign(timestamp, token),
        "sender": "amt@example.de",
        "subject": "Ihre Anfrage",
        "body-plain": "Anbei die Antwort.",
        "Message-Id": message_id,
    }
    data.update(extra)
    return data


class TestSignatureVerification:
    def test_missing_signature_rejected(self, app_client):
        response = app_client.post("/api/mailbox/inbound", data={"timestamp": "1", "token": "x"})
        assert response.status_code == 403

    def test_wrong_signature_rejected(self, app_client):
        response = app_client.post(
            "/api/mailbox/inbound",
            data={"timestamp": "1700000000", "token": "tok-1", "signature": "falsch"},
        )
        assert response.status_code == 403

    def test_valid_signature_accepted(self, app_client, db_session):
        response = app_client.post("/api/mailbox/inbound", data=webhook_form())
        assert response.status_code == 200


class TestIdempotency:
    def test_first_delivery_creates_one_row(self, app_client, db_session):
        response = app_client.post("/api/mailbox/inbound", data=webhook_form(message_id="dup-1"))
        assert response.status_code == 200
        assert db_session.query(InboundEmail).filter_by(message_id="dup-1").count() == 1

    def test_duplicate_delivery_does_not_create_second_row(self, app_client, db_session):
        """Simuliert einen Mailgun-Retry derselben E-Mail: gleiche Message-Id,
        aber neuer timestamp/token/signature - genau das im Auditbericht
        beschriebene Szenario, das timestamp/token allein nicht abfangen."""
        first = app_client.post(
            "/api/mailbox/inbound",
            data=webhook_form(message_id="dup-2", timestamp="1700000000", token="tok-a"),
        )
        second = app_client.post(
            "/api/mailbox/inbound",
            data=webhook_form(message_id="dup-2", timestamp="1700000999", token="tok-b"),
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["duplicate_delivery"] is True
        assert second.json()["id"] == first.json()["id"]
        assert db_session.query(InboundEmail).filter_by(message_id="dup-2").count() == 1

    def test_duplicate_delivery_does_not_overwrite_matched_response(self, app_client, db_session):
        """Der im Audit konkret genannte Schadensfall: eine zweite Zustellung
        darf eine bereits gespeicherte Antwort nicht überschreiben."""
        response = app_client.post("/api/mailbox/inbound", data=webhook_form(message_id="dup-3"))
        first_id = response.json()["id"]

        again = app_client.post(
            "/api/mailbox/inbound",
            data=webhook_form(message_id="dup-3", timestamp="1700001000", token="tok-c"),
        )
        assert again.json()["id"] == first_id
        assert again.json()["duplicate_delivery"] is True

    def test_missing_message_id_still_processes_without_crashing(self, app_client, db_session):
        """Kein Beleg gefunden für den exakten Mailgun-Feldnamen (siehe
        Code-Kommentar) - fehlt er, muss die E-Mail trotzdem verarbeitet
        werden, nur eben ohne Idempotenzschutz, statt den Webhook mit einem
        Fehler abzulehnen."""
        form = webhook_form()
        form.pop("Message-Id")
        response = app_client.post("/api/mailbox/inbound", data=form)
        assert response.status_code == 200

    def test_different_message_ids_both_processed(self, app_client, db_session):
        app_client.post("/api/mailbox/inbound", data=webhook_form(message_id="unique-a"))
        app_client.post("/api/mailbox/inbound", data=webhook_form(message_id="unique-b"))
        assert db_session.query(InboundEmail).count() == 2
