"""
Regressionstests für die im Auditbericht (Priorität 2) genannten
Sicherheitsfixes: Cookie-Konfiguration, CORS-Einschränkung, Login-
Ratenbegrenzung.
"""
import pytest

from app.services import rate_limiter


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
