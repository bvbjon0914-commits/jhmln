"""
Regressionstests für den getrennten API-Key-Zugang für Systemintegrationen
(Priorität 3 des Auditberichts-Folgeberichts, Befund "M2M-Zugriff").
"""
import pytest

from app.services.auth import check_api_key


class TestCheckApiKeyUnit:
    def test_empty_configured_keys_always_false(self, monkeypatch):
        monkeypatch.setattr("app.services.auth.API_KEYS", set())
        assert check_api_key("irgendein-schluessel") is False

    def test_matching_key_true(self, monkeypatch):
        monkeypatch.setattr("app.services.auth.API_KEYS", {"geheim-123"})
        assert check_api_key("geheim-123") is True

    def test_non_matching_key_false(self, monkeypatch):
        monkeypatch.setattr("app.services.auth.API_KEYS", {"geheim-123"})
        assert check_api_key("falsch") is False

    def test_empty_key_false(self, monkeypatch):
        monkeypatch.setattr("app.services.auth.API_KEYS", {"geheim-123"})
        assert check_api_key("") is False


class TestApiKeyEndToEnd:
    def test_protected_route_rejects_without_credentials_when_login_required(self, app_client, db_session, monkeypatch):
        from app.models.settings import AppSettings
        settings = AppSettings.get_or_create(db_session)
        settings.login_required = True
        db_session.commit()

        response = app_client.get("/api/buildings")
        assert response.status_code == 401

    def test_protected_route_accepts_valid_api_key_without_cookie(self, app_client, db_session, monkeypatch):
        from app.models.settings import AppSettings
        settings = AppSettings.get_or_create(db_session)
        settings.login_required = True
        db_session.commit()

        monkeypatch.setattr("app.services.auth.API_KEYS", {"system-integration-key"})

        response = app_client.get("/api/buildings", headers={"X-API-Key": "system-integration-key"})
        assert response.status_code == 200

    def test_wrong_api_key_still_rejected(self, app_client, db_session, monkeypatch):
        from app.models.settings import AppSettings
        settings = AppSettings.get_or_create(db_session)
        settings.login_required = True
        db_session.commit()

        monkeypatch.setattr("app.services.auth.API_KEYS", {"system-integration-key"})

        response = app_client.get("/api/buildings", headers={"X-API-Key": "falscher-schluessel"})
        assert response.status_code == 401

    def test_api_key_works_independently_of_login_required_toggle(self, app_client, db_session, monkeypatch):
        """Ein Systemzugang mit gültigem Schlüssel darf nicht davon abhängen,
        ob der Browser-Login gerade global ein- oder ausgeschaltet ist."""
        from app.models.settings import AppSettings
        settings = AppSettings.get_or_create(db_session)
        settings.login_required = False
        db_session.commit()

        monkeypatch.setattr("app.services.auth.API_KEYS", {"system-integration-key"})

        response = app_client.get("/api/buildings", headers={"X-API-Key": "system-integration-key"})
        assert response.status_code == 200
