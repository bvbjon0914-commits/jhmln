"""
Regressionstests für die additive API-Versionierung (Priorität 3 des
Auditberichts-Folgeberichts, Befund "API-Stabilität").

Kernanforderung: /api MUSS unverändert weiterlaufen (das bestehende
Frontend ruft ausschließlich /api auf) - /api/v1 kommt nur ZUSÄTZLICH
hinzu.
"""


class TestApiVersioning:
    def test_legacy_api_prefix_still_works(self, app_client):
        response = app_client.get("/api/auth/status")
        assert response.status_code == 200

    def test_versioned_v1_prefix_works_equivalently(self, app_client):
        legacy = app_client.get("/api/auth/status")
        versioned = app_client.get("/api/v1/auth/status")

        assert versioned.status_code == legacy.status_code == 200
        assert versioned.json() == legacy.json()

    def test_v1_buildings_list_matches_legacy(self, app_client, db_session):
        from app.models.settings import AppSettings
        from tests.conftest import make_building
        AppSettings.get_or_create(db_session).login_required = False
        db_session.commit()
        make_building(db_session)

        legacy = app_client.get("/api/buildings")
        versioned = app_client.get("/api/v1/buildings")

        assert legacy.status_code == versioned.status_code == 200
        assert legacy.json() == versioned.json()

    def test_v1_requires_same_auth_as_legacy(self, app_client, db_session):
        from app.models.settings import AppSettings
        settings = AppSettings.get_or_create(db_session)
        settings.login_required = True
        db_session.commit()

        response = app_client.get("/api/v1/buildings")
        assert response.status_code == 401
