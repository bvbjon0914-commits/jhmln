"""Prüfdateien geben Kontakte erst nach einer ausdrücklichen Entscheidung frei."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
import pytest
from openpyxl import load_workbook
from app.api.auth import require_main
from app.models.authority_contact_channel import AuthorityContactChannel, ChannelType
from app.models.contact_review import ContactReview
from app.models.settings import AppSettings
from app.services.contact_resolver import ContactResolver
from tests.conftest import make_authority, make_jurisdiction, make_request_type


@pytest.fixture
def client(app_client, db_session):
    from app.main import app
    AppSettings.get_or_create(db_session).login_required = False
    db_session.commit()
    app.dependency_overrides[require_main] = lambda: None
    return app_client


@pytest.fixture
def stock(db_session):
    for rt in ['BAUAKTEN', 'BAULASTEN']:
        make_request_type(db_session, rt)
    a = make_authority(db_session, email='info@bochum.de')
    rules = [make_jurisdiction(db_session, rt, a.authority_id, ags='05911000') for rt in ['BAUAKTEN', 'BAULASTEN']]
    return a, rules


def proposal(stock, **kwargs):
    a, _ = stock
    return dict(authority_id=a.authority_id, authority_name=a.authority_name, city=a.city,
        request_type_id='BAUAKTEN', ags=['05911000'], channel_type='EMAIL', value='bauakten@bochum.de',
        source_url='https://www.bochum.de/akten', source_sha256='a'*64,
        observed_at=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),
        evidence=[{'locator':'Kontaktblock','evidence_quote':'Bauaktenauskunft: bauakten@bochum.de'}],
        reasons=['DIENSTLEISTUNG_BELEGT']) | kwargs


def upload(client, proposals, **kwargs):
    doc=dict(schema_version='civeloq-contact-review-1',verification_status='UNVERIFIED',proposals=proposals) | kwargs
    return client.post('/api/contact-reviews/import',files={'file':('civeloq_pruefung.json',json.dumps(doc).encode(),'application/json')})


def decision(client, p, action='CONFIRM', **kwargs):
    return client.post(f'/api/contact-reviews/{p.proposal_id}/decision',json=dict(
        decision=action,version=p.version,source_checked=True,preferred=False,comment='Quelle geprüft') | kwargs)


def test_import_is_separate_idempotent_and_does_not_touch_stock(client,stock,db_session):
    a,rules=stock; before=[r.to_dict() for r in rules]
    data=proposal(stock)
    assert upload(client,[data]).json()['imported']==1
    assert upload(client,[data,data]).json()['duplicates']==2
    assert db_session.query(ContactReview).count()==1
    assert db_session.query(AuthorityContactChannel).count()==0
    db_session.refresh(a)
    assert a.email=='info@bochum.de' and [r.to_dict() for r in rules]==before
    row=db_session.query(ContactReview).one()
    assert row.status=='PENDING' and row.channel_id is None


def test_confirm_requires_source_checkbox_and_scopes_contact(client,stock,db_session):
    a,_=stock;upload(client,[proposal(stock)])
    p=db_session.query(ContactReview).one()
    assert decision(client,p,source_checked=False).status_code==422
    assert db_session.query(AuthorityContactChannel).count()==0
    assert decision(client,p).status_code==200
    db_session.expire_all()
    resolver=ContactResolver(db_session,[a.authority_id])
    assert resolver.resolve(a,'BAUAKTEN').can_send
    assert not resolver.resolve(a,'BAULASTEN').can_send
    assert a.email=='info@bochum.de'
    p=db_session.get(ContactReview,p.proposal_id)
    assert p.status=='CONFIRMED' and p.version==2 and p.channel_id
    assert json.loads(p.history)[0]['actor']=='Haupt-Account'


@pytest.mark.parametrize('action,status',[('REJECT','REJECTED'),('RESEARCH','RESEARCH')])
def test_other_decisions_leave_contacts_unchanged(client,stock,db_session,action,status):
    upload(client,[proposal(stock)])
    p=db_session.query(ContactReview).one()
    assert decision(client,p,action).status_code==200
    db_session.refresh(p)
    assert p.status==status and db_session.query(AuthorityContactChannel).count()==0
    assert upload(client,[proposal(stock)]).json()['duplicates']==1
    db_session.refresh(p);assert p.status==status


def test_concurrent_or_terminal_decision_cannot_overwrite_history(client,stock,db_session):
    upload(client,[proposal(stock)])
    p=db_session.query(ContactReview).one();key=p.proposal_id
    assert decision(client,p,'RESEARCH').status_code==200
    stale=client.post(f'/api/contact-reviews/{key}/decision',json={'decision':'REJECT','version':1})
    assert stale.status_code==409
    db_session.refresh(p)
    assert decision(client,p,'REJECT').status_code==200
    db_session.refresh(p)
    assert decision(client,p,'CONFIRM').status_code==409
    assert len(json.loads(p.history))==2


def test_changed_jurisdiction_rolls_back_decision_claim(client,stock,db_session):
    _,rules=stock;upload(client,[proposal(stock)])
    p=db_session.query(ContactReview).one()
    rules[0].active=False;db_session.commit()
    assert decision(client,p).status_code==409
    db_session.refresh(p)
    assert p.status=='PENDING' and p.version==1
    assert db_session.query(AuthorityContactChannel).count()==0


@pytest.mark.parametrize('change',[
    {'authority_id':'missing'}, {'city':'Anderer Ort'}, {'ags':['05913000']},
    {'request_type_id':'UNBEKANNT'}, {'source_url':'javascript:alert(1)'},
    {'value':'keine-mail'}, {'observed_at':'2026-11-14T12:00:00'},
    {'observed_at':'2099-11-14T12:00:00Z'},
])
def test_misbound_or_invalid_candidates_are_not_imported(client,stock,db_session,change):
    response=upload(client,[proposal(stock,**change)])
    assert response.status_code==200 and response.json()['needs_review']==1
    assert db_session.query(ContactReview).count()==0


@pytest.mark.parametrize('change',[{'verified':True},{'evidence':[]},{'source_sha256':'wrong'}])
def test_forged_verification_and_missing_evidence_reject_file(client,stock,db_session,change):
    assert upload(client,[proposal(stock,**change)]).status_code==422
    assert db_session.query(ContactReview).count()==0


def test_large_file_is_rejected(client):
    r=client.post('/api/contact-reviews/import',files={'file':('big.json',b' '* (8*1024*1024+1),'application/json')})
    assert r.status_code==413


def test_name_only_lookup_refuses_duplicate_authorities(client,stock,db_session):
    a,_=stock
    make_authority(db_session,name=a.authority_name,city=a.city)
    assert upload(client,[proposal(stock,authority_id='')]).json()['needs_review']==1
    assert upload(client,[proposal(stock)]).json()['imported']==1


def test_portal_confirmation_does_not_enable_email(client,stock,db_session):
    a,_=stock
    upload(client,[proposal(stock,channel_type='PORTAL',value='https://service.bochum.de/antrag')])
    p=db_session.query(ContactReview).one();assert decision(client,p).status_code==200
    c=db_session.query(AuthorityContactChannel).one()
    assert c.channel_type==ChannelType.PORTAL and c.last_verified_at
    assert not ContactResolver(db_session,[a.authority_id]).resolve(a,'BAUAKTEN').can_send


def test_preference_changes_only_this_service_and_preserves_reviewed_contact_on_reject(client,stock,db_session):
    a,_=stock
    old=AuthorityContactChannel(authority_id=a.authority_id,request_type_id='BAUAKTEN',channel_type='EMAIL',value='archiv@bochum.de',active=True,preferred=True,last_verified_at=datetime.utcnow(),source_url='https://www.bochum.de/alt')
    other=AuthorityContactChannel(authority_id=a.authority_id,request_type_id='BAULASTEN',channel_type='EMAIL',value='baulasten@bochum.de',active=True,preferred=True)
    db_session.add_all([old,other]);db_session.commit()
    upload(client,[proposal(stock)]);p=db_session.query(ContactReview).one()
    assert decision(client,p,preferred=True).status_code==200
    db_session.refresh(old);db_session.refresh(other)
    assert not old.preferred and other.preferred and old.last_verified_at and old.active


def test_list_filters_counts_versioned_route_and_research_export(client,stock,db_session):
    upload(client,[proposal(stock),proposal(stock,request_type_id='BAULASTEN',value='baulasten@bochum.de')])
    response=client.get('/api/v1/contact-reviews',params={'request_type_id':'BAUAKTEN','search':'Bochum','limit':1}).json()
    assert response['total']==1 and response['counts']['PENDING']==2
    item=response['items'][0]
    assert item['stock']['email']=='info@bochum.de' and item['evidence'][0]['locator']=='Kontaktblock'
    p=db_session.get(ContactReview,item['proposal_id']);decision(client,p,'RESEARCH')
    export=client.get('/api/contact-reviews/export-needs')
    assert export.status_code==200
    wb=load_workbook(BytesIO(export.content),read_only=True)
    rows=list(wb['Fachkontakte prüfen'].values)
    assert len(rows)==2 and rows[1][-1]==stock[0].authority_id and rows[1][0]=='BAUAKTEN'
    assert wb.active['B2'].data_type=='s' and rows[1][1]=='05911000'
    wb.close()


def test_routes_require_main_even_with_general_login_disabled(client,stock):
    from app.main import app
    app.dependency_overrides.pop(require_main)
    assert client.get('/api/contact-reviews').status_code==403
    assert client.get('/api/contact-reviews/export-needs').status_code==403
    assert upload(client,[proposal(stock)]).status_code==403
    assert client.post('/api/contact-reviews/missing/decision',json={'decision':'REJECT','version':1}).status_code==403


def test_review_evidence_prevents_authority_deletion_after_rules_are_removed(client,stock,db_session):
    from app.models.jurisdiction import Jurisdiction
    upload(client,[proposal(stock)])
    a,_=stock
    db_session.query(Jurisdiction).filter_by(authority_id=a.authority_id).delete(synchronize_session=False)
    db_session.commit()
    assert client.delete(f'/api/authorities/{a.authority_id}').status_code==409
    assert db_session.query(ContactReview).count()==1


def test_review_evidence_is_kept_out_of_automatic_duplicate_merges(client,stock,db_session):
    from app.models.jurisdiction import Jurisdiction
    from app.api.data_quality import _find_duplicate_authority_groups
    a,_=stock
    upload(client,[proposal(stock)])
    db_session.query(Jurisdiction).filter_by(authority_id=a.authority_id).delete(synchronize_session=False)
    make_authority(db_session,name=a.authority_name,city=None)
    db_session.commit()
    resolvable,needs_review=_find_duplicate_authority_groups(db_session)
    assert not resolvable and needs_review


def test_duplicate_import_race_keeps_terminal_decision(client,stock,db_session,monkeypatch):
    upload(client,[proposal(stock)])
    p=db_session.query(ContactReview).one()
    assert decision(client,p,'REJECT').status_code==200
    original_get=db_session.get
    missed=[False]
    def stale_get(model,key,*args,**kwargs):
        if model is ContactReview and not missed[0]:
            missed[0]=True
            return None
        return original_get(model,key,*args,**kwargs)
    monkeypatch.setattr(db_session,'get',stale_get)
    response=upload(client,[proposal(stock)])
    assert response.status_code==200 and response.json()['duplicates']==1
    db_session.refresh(p)
    assert p.status=='REJECTED' and p.version==2
    assert db_session.query(ContactReview).count()==1
