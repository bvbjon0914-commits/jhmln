"""
Laedt eine ETL-CSV (authority_name, ags, municipality, state, district, street,
house_number, priority, matching_level, department_name, street_addr,
postal_code, city, phone, email, website, source, notes) in die echte
Authority + Jurisdiction Tabellen der App - fuer eine feste request_type_id.

Nutzung: python3 load_domain.py <csv_pfad> <REQUEST_TYPE_ID>
"""
import sys
import os
import uuid
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from app.database import SessionLocal
from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    v = str(v).strip()
    return v or None


def main(csv_path, request_type_id):
    df = pd.read_csv(csv_path, dtype=str)
    db = SessionLocal()

    authorities_by_key = {(a.authority_name, a.city): a for a in db.query(Authority).all()}
    existing_jur_keys = {
        (j.request_type_id, j.authority_id, j.ags, j.district, j.street, j.house_number)
        for j in db.query(Jurisdiction)
    }

    created_auth = 0
    updated_auth = 0
    created_jur = 0
    skipped_dup = 0

    for _, row in df.iterrows():
        name = clean(row.get("authority_name"))
        if not name:
            continue
        row_request_type_id = clean(row.get("request_type_id")) or request_type_id
        city = clean(row.get("city"))
        key = (name, city)
        auth = authorities_by_key.get(key)
        if auth is None:
            auth = Authority(
                authority_id=str(uuid.uuid4()),
                authority_name=name,
                city=city,
                source=clean(row.get("source")) or "Import",
                active=True,
            )
            db.add(auth)
            authorities_by_key[key] = auth
            created_auth += 1
        else:
            updated_auth += 1

        for db_field, csv_col in (
            ("department_name", "department_name"),
            ("street", "street_addr"),
            ("postal_code", "postal_code"),
            ("state", "state"),
            ("email", "email"),
            ("phone", "phone"),
            ("website", "website"),
        ):
            val = clean(row.get(csv_col))
            if val:
                setattr(auth, db_field, val)

        ags = clean(row.get("ags"))
        district = clean(row.get("district"))
        street = clean(row.get("street"))
        house_number = clean(row.get("house_number"))
        jkey = (row_request_type_id, auth.authority_id, ags, district, street, house_number)
        if jkey in existing_jur_keys:
            skipped_dup += 1
            continue

        priority_raw = clean(row.get("priority"))
        jurisdiction = Jurisdiction(
            jurisdiction_id=str(uuid.uuid4()),
            request_type_id=row_request_type_id,
            authority_id=auth.authority_id,
            state=clean(row.get("state")) if not ags and not district else None,
            ags=ags,
            municipality=clean(row.get("municipality")),
            district=district,
            street=street,
            house_number=house_number,
            priority=int(priority_raw) if priority_raw else 100,
            matching_level=clean(row.get("matching_level")),
            source=clean(row.get("source")) or "Import",
            notes=clean(row.get("notes")),
            active=True,
        )
        db.add(jurisdiction)
        existing_jur_keys.add(jkey)
        created_jur += 1

    db.commit()
    print(f"OK: {request_type_id} <- {csv_path}")
    print(f"  Behoerden neu: {created_auth}, wiederverwendet: {updated_auth}")
    print(f"  Zustaendigkeiten neu: {created_jur}, uebersprungen (Duplikat): {skipped_dup}")
    db.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
