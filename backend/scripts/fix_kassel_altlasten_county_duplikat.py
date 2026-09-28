# -*- coding: utf-8 -*-
"""Fix a COUNTY-level ALTLASTEN (Bodenschutz) duplicate at ags=06633
(Landkreis Kassel, Hessen), found by a diagnostic pass over the ALTLASTEN
duplicate-ags groups surfaced by the matching self-test.

Root cause: same shape as the Offenbach Bauaufsicht case
(fix_offenbach_county_bauaufsicht_duplikat.py) - the old bulk import scoped
'Stadt Kassel - Untere Bodenschutzbehoerde' to ags=06633, which is actually
Landkreis Kassel's own ags_kreis, not Stadt Kassel's (a separate kreisfreie
Stadt at ags=06611000). A correct, VERIFIED MUNICIPALITY-level row for Stadt
Kassel already exists at ags=06611000, so expiring the mis-scoped COUNTY row
at 06633 causes zero coverage loss.

NOTE: 5 sibling ALTLASTEN duplicate-ags groups (Goettingen 03159, Hildesheim
03254, Celle 03351, Cuxhaven 03352, Luenburg 03355 - all Niedersachsen) were
checked and are NOT this bug: both rows carry an explicit note documenting
that these are "grosse selbstaendige Staedte" under NKomVG with genuine dual
Bodenschutz competency alongside their Landkreis. Those are deliberately left
untouched.
"""
import sqlite3
import sys
from datetime import date, timedelta

TARGET_AGS = "06633"
CORRECT_STADT_AGS = "06611000"
STADT_NAME_SUBSTR = "Stadt Kassel"
REQUEST_TYPE_CODE = "ALTLASTEN"


def main(apply_changes: bool) -> None:
    conn = sqlite3.connect("authority_matching.db")
    conn.text_factory = str
    cur = conn.cursor()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

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
        (REQUEST_TYPE_CODE, TARGET_AGS),
    )
    rows = cur.fetchall()
    if len(rows) != 2:
        print(f"UNEXPECTED shape ({len(rows)} rows) - aborting, needs manual review")
        conn.close()
        return

    stadt_rows = [r for r in rows if STADT_NAME_SUBSTR in r[1]]
    other_rows = [r for r in rows if r not in stadt_rows]
    if len(stadt_rows) != 1 or len(other_rows) != 1:
        print("UNEXPECTED names - aborting, needs manual review")
        for r in rows:
            print("  ", r)
        conn.close()
        return

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
        (REQUEST_TYPE_CODE, CORRECT_STADT_AGS),
    )
    replacement = cur.fetchall()
    if not replacement:
        print(f"NO replacement row found at ags={CORRECT_STADT_AGS} - aborting, needs manual review")
        conn.close()
        return

    expire_id, expire_name, expire_status = stadt_rows[0]
    keep_id, keep_name, keep_status = other_rows[0]
    repl_id, repl_name, repl_status = replacement[0]

    print(f"EXPIRE [{expire_status}] {expire_name} (ags={TARGET_AGS}, jurisdiction_id={expire_id})")
    print(f"KEEP   [{keep_status}] {keep_name} (ags={TARGET_AGS}, jurisdiction_id={keep_id})")
    print(
        f"because correct replacement already exists: [{repl_status}] {repl_name} "
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
        conn.commit()
        print("\nApplied.")
    else:
        print("\nDry-run only, no changes made. Pass --apply to persist.")
    conn.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
