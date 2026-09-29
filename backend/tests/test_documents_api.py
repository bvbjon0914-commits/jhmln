"""
Tests fuer POST /api/documents/generate - insbesondere dass NOT_APPLICABLE-
Items die Dokumentgenerierung nie blockieren und nicht als "failed" zaehlen.
"""
import pytest

from app.models.settings import AppSettings
from tests.conftest import (
    make_authority, make_building, make_request, make_request_item, make_request_type,
)


@pytest.fixture(autouse=True)
def _no_login_required(db_session):
    """documents.router liegt hinter require_login - diese Tests pruefen die
    NOT_APPLICABLE-Logik, nicht den Login, daher hier global deaktiviert
    (gleiches Muster wie tests/test_api_key_auth.py)."""
    settings = AppSettings.get_or_create(db_session)
    settings.login_required = False
    db_session.commit()


class TestNotApplicableDoesNotBlockGeneration:
    def test_not_applicable_item_lands_in_not_applicable_not_failed(self, app_client, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        building = make_building(db_session)
        request = make_request(db_session, building.building_id)
        make_request_item(db_session, request.request_id, "GRUNDBUCH", matching_status="NOT_APPLICABLE")

        response = app_client.post("/api/documents/generate", json={"request_id": request.request_id})

        assert response.status_code == 200
        body = response.json()
        assert body["failed"] == []
        assert len(body["not_applicable"]) == 1
        assert body["not_applicable"][0]["request_type_id"] == "GRUNDBUCH"

    def test_request_with_only_matched_and_not_applicable_items_completes(self, app_client, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        make_request_type(db_session, "BAULASTEN")
        authority = make_authority(db_session)
        building = make_building(db_session)
        request = make_request(db_session, building.building_id)
        make_request_item(
            db_session, request.request_id, "GRUNDBUCH",
            matching_status="MATCHED", authority_id=authority.authority_id,
        )
        make_request_item(db_session, request.request_id, "BAULASTEN", matching_status="NOT_APPLICABLE")

        response = app_client.post("/api/documents/generate", json={"request_id": request.request_id})

        assert response.status_code == 200
        body = response.json()
        assert len(body["documents"]) == 1
        assert len(body["not_applicable"]) == 1
        assert body["failed"] == []

        db_session.refresh(request)
        assert request.status == "COMPLETED"

    def test_genuine_no_match_item_still_counts_as_failed(self, app_client, db_session):
        """Regressionsschutz: ein echter, ungeklaerter NO_MATCH bleibt
        weiterhin sichtbar als 'failed' - nur NOT_APPLICABLE ist kein Fehler."""
        make_request_type(db_session, "GRUNDBUCH")
        building = make_building(db_session)
        request = make_request(db_session, building.building_id)
        make_request_item(db_session, request.request_id, "GRUNDBUCH", matching_status="NO_MATCH")

        response = app_client.post("/api/documents/generate", json={"request_id": request.request_id})

        assert response.status_code == 200
        body = response.json()
        assert body["not_applicable"] == []
        assert len(body["failed"]) == 1

        db_session.refresh(request)
        assert request.status == "PARTIALLY_COMPLETED"
