# -*- coding: utf-8 -*-
"""
DELETE /api/matching/items/{request_item_id} - entfernt ein einzelnes, nicht
eindeutig zugeordnetes Ergebnis aus seiner Anfrage (Zuordnungs-Assistent:
"nicht eindeutige Treffer per Klick entfernen", ohne das Gebäude zu entfernen
und neu zu ermitteln).
"""
import pytest

from app.models.settings import AppSettings
from tests.conftest import make_building, make_request, make_request_item, make_request_type


@pytest.fixture(autouse=True)
def _no_login_required(db_session):
    """matching.router liegt hinter require_login - diese Tests prüfen das
    Entfernen von RequestItems, nicht den Login (gleiches Muster wie
    tests/test_documents_api.py)."""
    settings = AppSettings.get_or_create(db_session)
    settings.login_required = False
    db_session.commit()


class TestRemoveMatchingItem:
    def _make_item(self, db_session, matching_status="CONFLICTING"):
        make_request_type(db_session, code="KAMPFMITTEL")
        building = make_building(db_session)
        request = make_request(db_session, building.building_id)
        item = make_request_item(
            db_session, request.request_id, "KAMPFMITTEL", matching_status=matching_status
        )
        return item

    def test_remove_non_matched_item_succeeds(self, app_client, db_session):
        item = self._make_item(db_session, matching_status="CONFLICTING")
        item_id = item.request_item_id
        response = app_client.delete(f"/api/matching/items/{item_id}")
        assert response.status_code == 204

        db_session.expire_all()
        assert db_session.query(type(item)).filter_by(request_item_id=item_id).first() is None

    def test_remove_already_removed_item_404(self, app_client, db_session):
        item = self._make_item(db_session, matching_status="CONFLICTING")
        item_id = item.request_item_id
        app_client.delete(f"/api/matching/items/{item_id}")
        response = app_client.delete(f"/api/matching/items/{item_id}")
        assert response.status_code == 404

    def test_remove_matched_item_rejected(self, app_client, db_session):
        item = self._make_item(db_session, matching_status="MATCHED")
        response = app_client.delete(f"/api/matching/items/{item.request_item_id}")
        assert response.status_code == 409

    def test_remove_unknown_item_404(self, app_client):
        response = app_client.delete("/api/matching/items/ITEM_does-not-exist")
        assert response.status_code == 404

    def test_removed_item_not_included_in_generation(self, app_client, db_session):
        """Nach dem Entfernen zählt das Item nicht mehr mit - weder als
        erfolgreich generiert noch als fehlgeschlagen."""
        make_request_type(db_session, code="KAMPFMITTEL")
        building = make_building(db_session)
        request = make_request(db_session, building.building_id)
        keep = make_request_item(
            db_session, request.request_id, "KAMPFMITTEL", matching_status="CONFLICTING"
        )
        app_client.delete(f"/api/matching/items/{keep.request_item_id}")

        remaining = db_session.query(type(keep)).filter_by(request_id=request.request_id).all()
        assert remaining == []
