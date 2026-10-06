# -*- coding: utf-8 -*-
"""
DELETE /api/buildings/{id} - muss auch dann funktionieren, wenn Fremdschlüssel
ERZWUNGEN werden (Postgres/Neon in Produktion). SQLite erzwingt sie standardmäßig
nicht, ein nur halb kaskadierendes Löschen fiel deshalb lokal nie auf, scheiterte
in Produktion aber mit IntegrityError (-> "Network Error" im Browser).
"""
import pytest
from sqlalchemy import event, text

from app.database.engine import engine
from app.models.aktenzeichen import RequestItemReference, RequestSequence
from app.models.building import Building
from app.models.case import Case, CaseBuilding, CaseRequest
from app.models.inbound_email import InboundEmail
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.settings import AppSettings
from tests.conftest import make_building, make_request, make_request_item, make_request_type


@pytest.fixture(autouse=True)
def _no_login_required(db_session):
    settings = AppSettings.get_or_create(db_session)
    settings.login_required = False
    db_session.commit()


@pytest.fixture()
def fk_enforced(db_session):
    """Schaltet für neue Verbindungen PRAGMA foreign_keys=ON ein (wie Postgres)."""

    def _on_connect(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    event.listen(engine, "connect", _on_connect)
    engine.dispose()
    try:
        yield
    finally:
        event.remove(engine, "connect", _on_connect)
        engine.dispose()


def _building_with_everything(db):
    make_request_type(db, code="GRUNDBUCH")
    building = make_building(db)
    request = make_request(db, building.building_id)
    item = make_request_item(db, request.request_id, "GRUNDBUCH", matching_status="MATCHED")

    db.add(RequestItemProgress(request_item_id=item.request_item_id))
    db.add(RequestItemReference(request_item_id=item.request_item_id, aktenzeichen="CIV-2026-0001-GB"))
    db.add(RequestSequence(request_id=request.request_id, sequence_number=1, year=2026))
    db.add(Case(case_id="CASE-1", name="Auftrag"))
    db.commit()
    db.add(CaseBuilding(case_id="CASE-1", building_id=building.building_id))
    db.add(CaseRequest(case_id="CASE-1", request_id=request.request_id))
    db.add(InboundEmail(from_address="amt@example.org", matched_request_item_id=item.request_item_id))
    db.commit()
    return building, request, item


class TestDeleteBuilding:
    def test_delete_with_all_dependents_under_enforced_foreign_keys(self, app_client, db_session, fk_enforced):
        building, request, item = _building_with_everything(db_session)
        building_id, request_id, item_id = building.building_id, request.request_id, item.request_item_id

        response = app_client.delete(f"/api/buildings/{building_id}")
        assert response.status_code == 204

        db_session.expire_all()
        assert db_session.query(Building).filter_by(building_id=building_id).first() is None
        assert db_session.query(Request).filter_by(request_id=request_id).first() is None
        assert db_session.query(RequestItem).filter_by(request_item_id=item_id).first() is None
        assert db_session.query(RequestItemProgress).count() == 0
        assert db_session.query(RequestItemReference).count() == 0
        assert db_session.query(RequestSequence).count() == 0
        assert db_session.query(CaseBuilding).count() == 0
        assert db_session.query(CaseRequest).count() == 0

    def test_inbound_email_is_kept_but_unlinked(self, app_client, db_session, fk_enforced):
        building, _request, _item = _building_with_everything(db_session)
        app_client.delete(f"/api/buildings/{building.building_id}")

        db_session.expire_all()
        mail = db_session.query(InboundEmail).one()
        assert mail.matched_request_item_id is None
        assert db_session.query(Case).filter_by(case_id="CASE-1").first() is not None

    def test_delete_unknown_building_404(self, app_client):
        response = app_client.delete("/api/buildings/does-not-exist")
        assert response.status_code == 404

    def test_other_buildings_are_untouched(self, app_client, db_session, fk_enforced):
        building, _request, _item = _building_with_everything(db_session)
        other = make_building(db_session, street="Andere Straße", house_number="5")
        other_id = other.building_id

        app_client.delete(f"/api/buildings/{building.building_id}")

        db_session.expire_all()
        assert db_session.query(Building).filter_by(building_id=other_id).first() is not None


class TestDeleteRequest:
    def test_delete_request_under_enforced_foreign_keys(self, app_client, db_session, fk_enforced):
        _building, request, item = _building_with_everything(db_session)
        request_id, item_id = request.request_id, item.request_item_id

        response = app_client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 204

        db_session.expire_all()
        assert db_session.query(Request).filter_by(request_id=request_id).first() is None
        assert db_session.query(RequestItem).filter_by(request_item_id=item_id).first() is None
        assert db_session.query(RequestSequence).count() == 0
        assert db_session.query(RequestItemReference).count() == 0
        assert db_session.query(CaseRequest).count() == 0

    def test_purge_orphaned_requests_under_enforced_foreign_keys(self, app_client, db_session, fk_enforced):
        building, request, _item = _building_with_everything(db_session)
        request_id = request.request_id
        # Gebäude "verwaist" machen: nur das Gebäude entfernen, Request bleibt (FK aus, kurz)
        db_session.execute(text("PRAGMA foreign_keys=OFF"))
        db_session.query(CaseBuilding).delete()
        db_session.delete(db_session.query(Building).filter_by(building_id=building.building_id).one())
        db_session.commit()
        db_session.execute(text("PRAGMA foreign_keys=ON"))

        response = app_client.post("/api/requests/purge-orphaned")
        assert response.status_code == 200
        assert response.json()["deleted"] == 1
        db_session.expire_all()
        assert db_session.query(Request).filter_by(request_id=request_id).first() is None
