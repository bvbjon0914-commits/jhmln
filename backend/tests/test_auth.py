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


REGISTER_PAYLOAD = {
    "email": "neu-registriert@example.com",
    "password": "geheim123",
    "full_name": "Neu Registriert",
    "phone": "0234 222222",
    "function": "Sachbearbeitung",
    "street": "Teststraße",
    "house_number": "3",
    "postal_code": "44787",
    "city": "Bochum",
}


class TestSelfRegistration:
    """Oeffentliche Selbstregistrierung (POST /auth/register) - legt einen
    'pending'/inaktiven Account an, der erst nach Admin-Freigabe nutzbar ist."""

    def test_register_creates_pending_inactive_user(self, app_client, db_session):
        response = app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert response.status_code == 201
        assert response.json()["status"] == "pending"

        from app.models.user import User

        user = db_session.query(User).filter(User.email == REGISTER_PAYLOAD["email"]).first()
        assert user is not None
        assert user.status == "pending"
        assert user.active is False
        assert user.is_main is False

    def test_registered_user_cannot_log_in(self, app_client, db_session):
        app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)

        response = app_client.post(
            "/api/auth/login",
            json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
        )
        # Gleiche generische Fehlermeldung wie bei jedem anderen falschen
        # Login - ein pending Account darf sich nicht einloggen, ohne dass
        # das nach aussen als Sonderfall erkennbar ist.
        assert response.status_code == 401
        assert response.json()["detail"] == "E-Mail oder Passwort falsch."

    def test_duplicate_email_registration_rejected(self, app_client, db_session):
        app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        duplicate = app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert duplicate.status_code == 409

    def test_duplicate_against_existing_active_user_rejected(self, app_client, db_session):
        """Die E-Mail-Pruefung bei der Registrierung ist status-unabhaengig -
        auch gegen einen bereits aktiven Account (nicht nur pending/rejected)."""
        make_user(db_session, email=REGISTER_PAYLOAD["email"], password="irrelevant")
        duplicate = app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert duplicate.status_code == 409

    def test_register_response_never_contains_password(self, app_client, db_session):
        response = app_client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        body = response.json()
        assert "password" not in body
        assert "password_hash" not in body

    def test_register_cannot_set_is_main_or_active_or_status(self, app_client, db_session):
        """is_main/active/status duerfen niemals vom Client kommen - auch
        wenn mitgeschickt, werden sie vom Server ignoriert/ueberschrieben."""
        payload = {**REGISTER_PAYLOAD, "is_main": True, "active": True, "status": "active"}
        response = app_client.post("/api/auth/register", json=payload)
        assert response.status_code == 201

        from app.models.user import User

        user = db_session.query(User).filter(User.email == REGISTER_PAYLOAD["email"]).first()
        assert user.is_main is False
        assert user.active is False
        assert user.status == "pending"
