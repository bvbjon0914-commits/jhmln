# -*- coding: utf-8 -*-
"""One-off matching self-test: one representative Gemeinde per Kreis x every request type. Not part of the seed pipeline."""
import sys
import os
import sqlite3

sys.path.insert(0, os.getcwd())
from app.database.engine import SessionLocal  # noqa: E402
from app.services.jurisdiction_matcher import JurisdictionMatchingService  # noqa: E402

db = SessionLocal()
svc = JurisdictionMatchingService(db)

conn = sqlite3.connect("authority_matching.db")
cur = conn.cursor()
cur.execute("""
    SELECT ags_kreis, MIN(ags) as sample_ags, state_name, MIN(county_name), MIN(municipality_name)
    FROM administrative_units
    GROUP BY ags_kreis
""")
kreise = cur.fetchall()
cur.execute("SELECT request_type_id FROM request_types")
types = [r[0] for r in cur.fetchall()]

print(f"{len(kreise)} Kreise x {len(types)} Auskunftsarten = {len(kreise) * len(types)} Kombinationen")


class FakeBuilding:
    pass


status_counts = {}
multiple_matches_samples = []
no_match_samples = []

count = 0
for ags_kreis, sample_ags, state, county, muni in kreise:
    for rt in types:
        b = FakeBuilding()
        b.building_id = "selftest"
        b.ags = sample_ags
        b.state = state
        b.postal_code = None
        b.city = muni
        b.district = None
        b.street = None
        b.house_number = None
        try:
            result = svc.match_authority(b, rt)
            status = result.matching_status
        except Exception as e:
            status = f"ERROR:{type(e).__name__}:{e}"
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "MULTIPLE_MATCHES" and len(multiple_matches_samples) < 50:
            multiple_matches_samples.append((rt, sample_ags, state, county, muni))
        if status == "NO_MATCH" and len(no_match_samples) < 50:
            no_match_samples.append((rt, sample_ags, state, county, muni))
        count += 1
    if count % 440 < len(types):
        print(f"... {count} done", flush=True)

print("\n=== STATUS COUNTS ===")
for k, v in sorted(status_counts.items(), key=lambda x: -x[1]):
    print(k, v)

print("\n=== MULTIPLE_MATCHES samples ===")
for s in multiple_matches_samples:
    print(s)

print("\n=== NO_MATCH samples ===")
for s in no_match_samples:
    print(s)

db.close()
