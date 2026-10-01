"""
Tests fuer die Nutzerverwaltung (/api/users) - Admin-only CRUD.
"""
from tests.conftest import make_user

VALID_CREATE_PAYLOAD = {
    "email": "neu@example.com",
    "password": "geheim123",
    "full_name": "Neu Nutzer",
    "phone": "0234 111111",
    "function": "Sachbearbeitung",
    "street": "Teststraße",
    "house_number": "2",
    "postal_code": "44787",
    "city": "Bochum",
}


def _login_as_main(app_client, db_session, email="main@example.com", password="geheim123"):
    make_user(db_session, email=email, password=password, is_main=True)
    app_client.post("/api/auth/login", json={"email": email, "password": password})


class TestUsersAuthGating:
    def test_list_without_login_rejected(self, app_client):
        # require_login (Router-Ebene) greift zuerst, bevor die
        # Route ihr eigenes Depends(require_main) je auswertet - deshalb 401
        # (nicht eingeloggt), nicht 403 (eingeloggt, aber kein Haupt-Account).
        response = app_client.get("/api/users")
        assert response.status_code == 401

    def test_list_as_non_main_user_rejected(self, app_client, db_session):
        make_user(db_session, email="standard@example.com", password="geheim123", is_main=False)
        app_client.post("/api/auth/login", json={"email": "standard@example.com", "password": "geheim123"})
        response = app_client.get("/api/users")
        assert response.status_code == 403

    def test_create_as_main_user_succeeds(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        response = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD)
        assert response.status_code == 201


class TestUsersCRUD:
    def test_create_then_list(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        assert created["email"] == "neu@example.com"
        assert "password_hash" not in created

        listed = app_client.get("/api/users").json()
        emails = {u["email"] for u in listed}
        assert "neu@example.com" in emails

    def test_create_duplicate_email_rejected(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        app_client.post("/api/users", json=VALID_CREATE_PAYLOAD)
        duplicate = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD)
        assert duplicate.status_code == 409

    def test_update_changes_fields(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        response = app_client.put(f"/api/users/{created['user_id']}", json={"full_name": "Geänderter Name"})
        assert response.status_code == 200
        assert response.json()["full_name"] == "Geänderter Name"

    def test_password_reset_takes_effect_on_next_login(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()

        app_client.put(f"/api/users/{created['user_id']}", json={"password": "neues-passwort"})

        old_login = app_client.post(
            "/api/auth/login", json={"email": "neu@example.com", "password": "geheim123"}
        )
        assert old_login.status_code == 401

        new_login = app_client.post(
            "/api/auth/login", json={"email": "neu@example.com", "password": "neues-passwort"}
        )
        assert new_login.status_code == 200

    def test_delete_removes_user_and_blocks_login(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()

        response = app_client.delete(f"/api/users/{created['user_id']}")
        assert response.status_code == 204

        login = app_client.post(
            "/api/auth/login", json={"email": "neu@example.com", "password": "geheim123"}
        )
        assert login.status_code == 401

    def test_response_never_contains_password_hash(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        fetched = app_client.get(f"/api/users/{created['user_id']}").json()
        assert "password_hash" not in fetched

    def test_cannot_deactivate_last_active_main_user(self, app_client, db_session):
        """Sicherheitsnetz gegen versehentliches Aussperren."""
        make_user(db_session, email="only-main@example.com", password="geheim123", is_main=True)
        app_client.post("/api/auth/login", json={"email": "only-main@example.com", "password": "geheim123"})
        me = app_client.get("/api/users").json()[0]

        response = app_client.put(f"/api/users/{me['user_id']}", json={"active": False})
        assert response.status_code == 400

    def test_admin_created_user_has_active_status(self, app_client, db_session):
        """Admin-angelegte Accounts sind sofort vertrauenswuerdig, nie 'pending'
        (das gilt nur fuer die oeffentliche Selbstregistrierung)."""
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        assert created["status"] == "active"


class TestUserApproval:
    """Admin-Freigabe/Ablehnung von per Selbstregistrierung angelegten
    'pending'-Accounts (POST /users/{user_id}/approve bzw. /reject)."""

    def _register_pending(self, app_client, email="pending@example.com", password="geheim123"):
        payload = {
            "email": email,
            "password": password,
            "full_name": "Pending Nutzer",
            "phone": "0234 333333",
            "function": "Sachbearbeitung",
            "street": "Teststraße",
            "house_number": "4",
            "postal_code": "44787",
            "city": "Bochum",
        }
        response = app_client.post("/api/auth/register", json=payload)
        assert response.status_code == 201
        return email, password

    def test_approve_without_login_rejected(self, app_client, db_session):
        from app.models.user import User

        email, _ = self._register_pending(app_client)
        user = db_session.query(User).filter_by(email=email).first()
        response = app_client.post(f"/api/users/{user.user_id}/approve")
        assert response.status_code == 401

    def test_reject_without_login_rejected(self, app_client, db_session):
        from app.models.user import User

        email, _ = self._register_pending(app_client)
        user = db_session.query(User).filter_by(email=email).first()
        response = app_client.post(f"/api/users/{user.user_id}/reject")
        assert response.status_code == 401

    def test_approve_as_non_main_user_rejected(self, app_client, db_session):
        email, _ = self._register_pending(app_client)
        make_user(db_session, email="standard@example.com", password="geheim123", is_main=False)
        app_client.post("/api/auth/login", json={"email": "standard@example.com", "password": "geheim123"})

        from app.models.user import User
        user = db_session.query(User).filter_by(email=email).first()
        response = app_client.post(f"/api/users/{user.user_id}/approve")
        assert response.status_code == 403

    def test_approve_flow_allows_login_afterwards(self, app_client, db_session):
        email, password = self._register_pending(app_client)
        _login_as_main(app_client, db_session)

        from app.models.user import User
        pending_user = db_session.query(User).filter_by(email=email).first()

        response = app_client.post(f"/api/users/{pending_user.user_id}/approve")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "active"
        assert body["active"] is True
        assert body["reviewed_by"] is not None
        assert body["reviewed_at"] is not None

        # Admin-Session durch den anschliessenden Login-Versuch ersetzen -
        # der frisch freigegebene Account muss sich jetzt einloggen koennen.
        login = app_client.post("/api/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200

    def test_reject_flow_keeps_login_blocked(self, app_client, db_session):
        email, password = self._register_pending(app_client)
        _login_as_main(app_client, db_session)

        from app.models.user import User
        pending_user = db_session.query(User).filter_by(email=email).first()

        response = app_client.post(f"/api/users/{pending_user.user_id}/reject")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "rejected"
        assert body["active"] is False
        assert body["reviewed_by"] is not None
        assert body["reviewed_at"] is not None

        # Die Zeile bleibt fuer Audit/Historie erhalten (nicht geloescht).
        assert db_session.query(User).filter_by(email=email).first() is not None

        login = app_client.post("/api/auth/login", json={"email": email, "password": password})
        assert login.status_code == 401

    def test_approve_non_pending_user_conflict(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        # Admin-angelegte Accounts sind bereits "active", nicht "pending".
        response = app_client.post(f"/api/users/{created['user_id']}/approve")
        assert response.status_code == 409

    def test_reject_non_pending_user_conflict(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        created = app_client.post("/api/users", json=VALID_CREATE_PAYLOAD).json()
        response = app_client.post(f"/api/users/{created['user_id']}/reject")
        assert response.status_code == 409

    def test_approve_unknown_user_404(self, app_client, db_session):
        _login_as_main(app_client, db_session)
        response = app_client.post("/api/users/USR-does-not-exist/approve")
        assert response.status_code == 404

    def test_list_users_filtered_by_pending_status(self, app_client, db_session):
        self._register_pending(app_client, email="pending-one@example.com")
        _login_as_main(app_client, db_session)
        app_client.post("/api/users", json=VALID_CREATE_PAYLOAD)  # ein "active"-Account

        response = app_client.get("/api/users", params={"status": "pending"})
        assert response.status_code == 200
        emails = {u["email"] for u in response.json()}
        assert emails == {"pending-one@example.com"}


class TestMyAccount:
    """Selbstbearbeitung/-löschung des eigenen Accounts (GET/PUT/DELETE
    /users/me) - bewusst require_login statt require_main, jeder
    eingeloggte Nutzer darf seinen eigenen Account verwalten."""

    def _login_as_standard(self, app_client, db_session, email="standard@example.com", password="geheim123"):
        make_user(db_session, email=email, password=password, is_main=False)
        app_client.post("/api/auth/login", json={"email": email, "password": password})

    def test_get_without_login_rejected(self, app_client):
        response = app_client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_returns_own_account(self, app_client, db_session):
        self._login_as_standard(app_client, db_session)
        response = app_client.get("/api/users/me")
        assert response.status_code == 200
        assert response.json()["email"] == "standard@example.com"
        assert "password_hash" not in response.json()

    def test_update_changes_own_fields(self, app_client, db_session):
        self._login_as_standard(app_client, db_session)
        response = app_client.put("/api/users/me", json={"full_name": "Neuer Name", "phone": "0170 123"})
        assert response.status_code == 200
        assert response.json()["full_name"] == "Neuer Name"
        assert response.json()["phone"] == "0170 123"

    def test_update_cannot_grant_is_main(self, app_client, db_session):
        """UserSelfUpdate hat kein is_main-Feld - ein zusaetzliches Feld im
        Request wird von Pydantic ignoriert, nicht angewendet."""
        self._login_as_standard(app_client, db_session)
        app_client.put("/api/users/me", json={"is_main": True, "active": False})
        me = app_client.get("/api/users/me").json()
        assert me["is_main"] is False
        assert me["active"] is True

    def test_update_duplicate_email_rejected(self, app_client, db_session):
        make_user(db_session, email="vergeben@example.com", password="geheim123", is_main=False)
        self._login_as_standard(app_client, db_session)
        response = app_client.put("/api/users/me", json={"email": "vergeben@example.com"})
        assert response.status_code == 409

    def test_password_change_takes_effect_on_next_login(self, app_client, db_session):
        self._login_as_standard(app_client, db_session)
        response = app_client.put("/api/users/me", json={"password": "neues-passwort"})
        assert response.status_code == 200

        old_login = app_client.post(
            "/api/auth/login", json={"email": "standard@example.com", "password": "geheim123"}
        )
        assert old_login.status_code == 401

        new_login = app_client.post(
            "/api/auth/login", json={"email": "standard@example.com", "password": "neues-passwort"}
        )
        assert new_login.status_code == 200

    def test_delete_without_login_rejected(self, app_client):
        response = app_client.delete("/api/users/me")
        assert response.status_code == 401

    def test_delete_removes_own_account_and_blocks_future_login(self, app_client, db_session):
        self._login_as_standard(app_client, db_session)
        response = app_client.delete("/api/users/me")
        assert response.status_code == 204

        login = app_client.post(
            "/api/auth/login", json={"email": "standard@example.com", "password": "geheim123"}
        )
        assert login.status_code == 401

    def test_delete_clears_session_cookie(self, app_client, db_session):
        self._login_as_standard(app_client, db_session)
        app_client.delete("/api/users/me")
        # Nach dem Selbstlöschen muss die Session-Route wieder wie ausgeloggt
        # antworten, nicht mit einem Fehler über einen jetzt geisterhaften User.
        status = app_client.get("/api/auth/status").json()
        assert status["logged_in"] is False

    def test_cannot_delete_own_account_as_last_active_main_user(self, app_client, db_session):
        make_user(db_session, email="only-main@example.com", password="geheim123", is_main=True)
        app_client.post("/api/auth/login", json={"email": "only-main@example.com", "password": "geheim123"})
        response = app_client.delete("/api/users/me")
        assert response.status_code == 400

    def test_second_main_user_can_delete_own_account(self, app_client, db_session):
        make_user(db_session, email="main-one@example.com", password="geheim123", is_main=True)
        make_user(db_session, email="main-two@example.com", password="geheim123", is_main=True)
        app_client.post("/api/auth/login", json={"email": "main-two@example.com", "password": "geheim123"})
        response = app_client.delete("/api/users/me")
        assert response.status_code == 204

    def test_me_route_not_shadowed_by_user_id_route(self, app_client, db_session):
        """Regressionstest fuer die FastAPI-Routing-Falle: /users/me muss vor
        /users/{user_id} registriert sein, sonst würde "me" als user_id
        interpretiert und require_main statt require_login greifen."""
        self._login_as_standard(app_client, db_session)
        response = app_client.get("/api/users/me")
        assert response.status_code == 200
        # Ein Standard-Nutzer bekäme hier 403, wenn "me" stattdessen in
        # GET /users/{user_id} (require_main) gelandet wäre.
