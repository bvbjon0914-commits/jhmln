# -*- coding: utf-8 -*-
"""Fix a COUNTY-level Wasserbehoerde duplicate at ags=06633 (Landkreis Kassel,
Hessen) for HOCHWASSERSCHUTZ/WASSERSCHUTZ - the same mis-scoped-duplicate
pattern as Offenbach Bauaufsicht and Kassel ALTLASTEN
(fix_offenbach_county_bauaufsicht_duplikat.py,
fix_kassel_altlasten_county_duplikat.py).

'Magistrat der Stadt Kassel - Untere Wasserbehoerde' sits at COUNTY ags=06633
(Landkreis Kassel's own ags_kreis), duplicating 'Kreisausschuss des
Landkreises Kassel - Untere Wasserbehoerde' (also correctly ags=06633). Kassel
city is a separate kreisfreie Stadt (ags=06611000) with an already-VERIFIED
MUNICIPALITY-level row there ('Stadt Kassel - Untere Wasserbehoerde'), so
expiring the mis-scoped COUNTY row causes zero coverage loss.

NOT to be confused with fix_wasserbehoerde_stadt_rescope.py, which handles a
DIFFERENT, legitimate pattern (Niedersachsen "grosse selbstaendige Stadt" /
Saarland Kombibehoerden) where the city's water authority needs to be
RE-SCOPED to its own municipality ags rather than simply expired, because no
correct replacement exists there yet.
"""
import sqlite3
import sys
from datetime import date, timedelta

TARGET_AGS = "06633"
CORRECT_STADT_AGS = "06611000"
STADT_NAME_SUBSTR = "Magistrat der Stadt Kassel"
REQUEST_TYPE_CODES = ["HOCHWASSERSCHUTZ", "WASSERSCHUTZ"]


def main(apply_changes: bool) -> None:
    conn = sqlite3.connect("authority_matching.db")
    conn.text_factory = str
    cur = conn.cursor()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    for rt in REQUEST_TYPE_CODES:
        print(f"\n{'=' * 20} {rt} {'=' * 20}")
        cur.execute(
            """
            SELECT j.jurisdiction_id, a.authority_name, j.verification_status
            FROM jurisdictions j
            JOIN authorities a ON a.authority_id = j.authority_id
            WHERE j.active = 1
              AND j.request_type_id = (SELECT request_type_id FROM request_types WHERE code = ?)
              AND j.matching_level = 'COUNTY'
              AND j.ags = ?
              AND (j.valid_to IS NULL OR j.valid_to >= date('now'))
            """,
            (rt, TARGET_AGS),
        )
        rows = cur.fetchall()
        if len(rows) != 2:
            print(f"  UNEXPECTED shape ({len(rows)} rows) - skipping, needs manual review")
            continue

        stadt_rows = [r for r in rows if STADT_NAME_SUBSTR in r[1]]
        other_rows = [r for r in rows if r not in stadt_rows]
        if len(stadt_rows) != 1 or len(other_rows) != 1:
            print("  UNEXPECTED names - skipping, needs manual review")
            for r in rows:
                print("   ", r)
            continue

        cur.execute(
            """
            SELECT j.jurisdiction_id, a.authority_name, j.verification_status
            FROM jurisdictions j
            JOIN authorities a ON a.authority_id = j.authority_id
            WHERE j.active = 1
              AND j.request_type_id = (SELECT request_type_id FROM request_types WHERE code = ?)
              AND j.ags = ?
              AND (j.valid_to IS NULL OR j.valid_to >= date('now'))
            """,
            (rt, CORRECT_STADT_AGS),
        )
        replacement = cur.fetchall()
        if not replacement:
            print(f"  NO replacement row found at ags={CORRECT_STADT_AGS} - skipping, needs manual review")
            continue

        expire_id, expire_name, expire_status = stadt_rows[0]
        keep_id, keep_name, keep_status = other_rows[0]
        repl_id, repl_name, repl_status = replacement[0]

        print(f"  EXPIRE [{expire_status}] {expire_name} (ags={TARGET_AGS}, jurisdiction_id={expire_id})")
        print(f"  KEEP   [{keep_status}] {keep_name} (ags={TARGET_AGS}, jurisdiction_id={keep_id})")
        print(
            f"  because correct replacement already exists: [{repl_status}] {repl_name} "
            f"(ags={CORRECT_STADT_AGS}, jurisdiction_id={repl_id})"
        )

        if apply_changes:
            cur.execute(
                """
                UPDATE jurisdictions
                SET valid_to = ?,
                    notes = COALESCE(notes || ' | ', '') || ?
                WHERE jurisdiction_id = ?
                """,
                (
                    yesterday,
                    f"Expired {today}: mis-scoped to ags={TARGET_AGS} (Landkreis Kassel's ags_kreis) "
                    f"instead of Stadt Kassel's own ags={CORRECT_STADT_AGS}; correct VERIFIED row "
                    f"already exists there.",
                    expire_id,
                ),
            )

    if apply_changes:
        conn.commit()
        print("\nApplied.")
    else:
        print("\nDry-run only, no changes made. Pass --apply to persist.")
    conn.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
