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
