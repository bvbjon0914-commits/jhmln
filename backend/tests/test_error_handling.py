"""
Regressionstests für den globalen Fehler-/Request-Id-Mechanismus
(Priorität 2 des Auditberichts, Befund "Fehlerbehandlung").

Wichtigste Eigenschaft, die hier abgesichert wird: das bisherige
Antwortformat ({"detail": "..."}), auf das
frontend/src/components/common/Toast.tsx bei Fehlern zugreift, bleibt
UNVERÄNDERT - "request_id" wird nur ergänzt, nichts umbenannt.
"""
import pytest
from starlette.requests import Request

from app.main import http_exception_handler, unhandled_exception_handler
from fastapi import HTTPException


def _fake_request(request_id="req-123"):
    scope = {"type": "http", "method": "GET", "path": "/api/test", "headers": []}
    request = Request(scope)
    request.state.request_id = request_id
    return request


class TestRequestIdMiddleware:
    def test_every_response_carries_request_id_header(self, app_client):
        response = app_client.get("/api/auth/status")
        assert "x-request-id" in {k.lower() for k in response.headers.keys()}

    def test_request_id_is_unique_per_request(self, app_client):
        r1 = app_client.get("/api/auth/status")
        r2 = app_client.get("/api/auth/status")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


class TestHTTPExceptionHandler:
    @pytest.mark.asyncio
    async def test_detail_field_preserved_unchanged(self):
        """Kernanforderung: das Frontend liest response.data.detail - dieses
        Feld muss exakt wie vorher (nur 'detail', kein umbenanntes Feld)
        mit demselben Inhalt vorhanden sein."""
        exc = HTTPException(status_code=404, detail="Gebäude nicht gefunden")
        response = await http_exception_handler(_fake_request(), exc)

        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert body["detail"] == "Gebäude nicht gefunden"
        assert body["request_id"] == "req-123"

    @pytest.mark.asyncio
    async def test_custom_headers_preserved(self):
        """Z.B. der Retry-After-Header des Login-Ratenlimits darf nicht
        verloren gehen, wenn der Handler die Antwort umformt."""
        exc = HTTPException(status_code=429, detail="Zu viele Versuche", headers={"Retry-After": "900"})
        response = await http_exception_handler(_fake_request(), exc)

        assert response.headers.get("retry-after") == "900"

    def test_real_endpoint_error_still_has_detail_field(self, app_client):
        """End-to-End über einen echten, bereits vorhandenen Fehlerpfad
        (falsches Passwort -> 401)."""
        response = app_client.post("/api/auth/login", json={"password": "definitiv-falsch"})
        assert response.status_code == 401
        body = response.json()
        assert "detail" in body
        assert "request_id" in body


class TestUnhandledExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_generic_message_not_internal_details(self):
        """Die interne Exception-Message darf NICHT an den Client
        durchgereicht werden (könnte Pfade/Query-Fragmente/Bibliotheksdetails
        enthalten) - nur eine generische Meldung plus request_id."""
        exc = ValueError("interner Zustand: /etc/secret/pfad, connection string xyz")
        response = await unhandled_exception_handler(_fake_request(), exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert "etc/secret" not in body["detail"]
        assert "connection string" not in body["detail"]
        assert body["request_id"] == "req-123"
        assert "detail" in body  # Frontend-Kompatibilität (Toast.tsx)
