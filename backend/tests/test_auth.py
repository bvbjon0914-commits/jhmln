"""
Regressionstests für die im Auditbericht (Priorität 2) genannten
Sicherheitsfixes: Cookie-Konfiguration, CORS-Einschränkung, Login-
Ratenbegrenzung. Sowie Tests für den echten Nutzer-Account-Login (email+
password), der NEBEN dem alten Zwei-Passwoerter-Weg existiert.
"""
import pytest

from app.services import rate_limiter
from tests.conftest import make_user


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Der Ratenbegrenzer hält Prozess-globalen Zustand - zwischen Tests leeren,
    damit sich Testfälle nicht gegenseitig beeinflussen."""
    rate_limiter.reset_all()
    yield
    rate_limiter.reset_all()


class TestCookieSecureFlag:
    def test_login_sets_secure_cookie_by_default(self, app_client, db_session):
        import os
        response = app_client.post("/api/auth/login", json={"password": os.environ["SHARED_PASSWORD"]})

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "samesite=lax" in set_cookie.lower()


class TestCORSRestriction:
    def test_allowed_dev_origin_gets_cors_header(self, app_client):
        response = app_client.get(
            "/api/auth/status",
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_arbitrary_origin_does_not_get_cors_header(self, app_client):
        response = app_client.get(
            "/api/auth/status",
            headers={"Origin": "https://evil.example.com"},
        )
        assert "access-control-allow-origin" not in {k.lower() for k in response.headers.keys()}


class TestLoginRateLimiting:
    def test_wrong_password_does_not_block_immediately(self, app_client):
        response = app_client.post("/api/auth/login", json={"password": "falsch"})
        assert response.status_code == 401

    def test_repeated_failures_eventually_blocked(self, app_client):
        from app.config import LOGIN_RATE_LIMIT_MAX_ATTEMPTS

        last_status = None
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS + 2):
            last_status = app_client.post("/api/auth/login", json={"password": "falsch"}).status_code

        assert last_status == 429

    def test_successful_login_resets_counter(self, app_client, db_session):
        import os
        from app.config import LOGIN_RATE_LIMIT_MAX_ATTEMPTS

        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS - 1):
            app_client.post("/api/auth/login", json={"password": "falsch"})

        ok = app_client.post("/api/auth/login", json={"password": os.environ["SHARED_PASSWORD"]})
        assert ok.status_code == 200

        # Nach dem erfolgreichen Login ist der Zähler zurückgesetzt - ein
        # einzelner weiterer Fehlversuch darf nicht sofort blockiert werden.
        again = app_client.post("/api/auth/login", json={"password": "falsch"})
        assert again.status_code == 401

    def test_rate_limit_is_per_client_not_global(self, app_client):
        """TestClient nutzt für alle Anfragen dieselbe simulierte Client-IP -
        dieser Test dokumentiert lediglich, dass der Schlüssel überhaupt aus
        der Client-Adresse abgeleitet wird, nicht aus einem globalen Zähler."""
        from app.api.auth import _client_key
        from starlette.requests import Request

        scope = {"type": "http", "client": ("203.0.113.5", 12345), "headers": []}
        request = Request(scope)
        assert _client_key(request) == "203.0.113.5"


class TestUserAccountLogin:
    """Echter Nutzer-Account-Login (email+password) - existiert NEBEN dem
    alten Zwei-Passwoerter-Weg, der oben unveraendert weiter getestet wird."""

    def test_login_with_valid_credentials_succeeds(self, app_client, db_session):
        make_user(db_session, email="anna@example.com", password="geheim123", is_main=False)
        response = app_client.post("/api/auth/login", json={"email": "anna@example.com", "password": "geheim123"})
        assert response.status_code == 200
        body = response.json()
        assert body["is_main"] is False
        assert body["user"]["email"] == "anna@example.com"
        assert "password_hash" not in body["user"]

    def test_login_is_main_reflects_user_flag(self, app_client, db_session):
        make_user(db_session, email="chef@example.com", password="geheim123", is_main=True)
        response = app_client.post("/api/auth/login", json={"email": "chef@example.com", "password": "geheim123"})
        assert response.status_code == 200
        assert response.json()["is_main"] is True

    def test_login_wrong_password_rejected(self, app_client, db_session):
        make_user(db_session, email="anna@example.com", password="geheim123")
        response = app_client.post("/api/auth/login", json={"email": "anna@example.com", "password": "falsch"})
        assert response.status_code == 401

    def test_login_unknown_email_rejected_with_same_message_as_wrong_password(self, app_client, db_session):
        make_user(db_session, email="anna@example.com", password="geheim123")
        wrong_pw = app_client.post("/api/auth/login", json={"email": "anna@example.com", "password": "falsch"})
        unknown_email = app_client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
        assert unknown_email.status_code == 401
        assert unknown_email.json()["detail"] == wrong_pw.json()["detail"]

    def test_login_deactivated_user_rejected(self, app_client, db_session):
        make_user(db_session, email="ex@example.com", password="geheim123", active=False)
        response = app_client.post("/api/auth/login", json={"email": "ex@example.com", "password": "geheim123"})
        assert response.status_code == 401

    def test_auth_status_returns_user_profile_without_password_hash(self, app_client, db_session):
        make_user(db_session, email="anna@example.com", password="geheim123", full_name="Anna Muster")
        app_client.post("/api/auth/login", json={"email": "anna@example.com", "password": "geheim123"})
        status = app_client.get("/api/auth/status").json()
        assert status["user"]["full_name"] == "Anna Muster"
        assert "password_hash" not in status["user"]

    def test_legacy_password_only_login_still_works(self, app_client, db_session):
        """Regressionsschutz: der alte Zwei-Passwoerter-Weg (kein email-Feld
        im Payload) darf durch die Einfuehrung echter Accounts NICHT brechen."""
        import os

        response = app_client.post("/api/auth/login", json={"password": os.environ["SHARED_PASSWORD"]})
        assert response.status_code == 200
        assert response.json()["is_main"] is False
        assert response.json()["user"] is None
