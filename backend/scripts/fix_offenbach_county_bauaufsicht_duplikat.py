# -*- coding: utf-8 -*-
"""Fix a COUNTY-level Bauaufsicht duplicate for BAUAKTEN/BAULASTEN at ags=06438
(Landkreis Offenbach, Hessen), found by the bundesweit matching self-test after
the MUNICIPALITY-level fix (fix_bauaufsicht_kreisweite_duplikate_bundesweit.py).

Root cause: the old bulk import ("...FINAL 20260831") scoped
'Stadt Offenbach - Untere Bauaufsichtsbehoerde' to ags=06438, which is actually
Landkreis Offenbach's own ags_kreis, not Stadt Offenbach am Main's (which is the
separate kreisfreie Stadt at ags=06413). This is the mirror image of the already-
fixed MUNICIPALITY-level bug: here the mis-scoped row sits at COUNTY level, and it
duplicates 'Landkreis Offenbach - Untere Bauaufsichtsbehoerde' (also ags=06438,
which is correct for the Landkreis).

A correct, VERIFIED replacement for Stadt Offenbach am Main already exists at
ags=06413 ('Offenbach am Main, Stadt - Bauaufsichtsbehoerde'), so expiring the
mis-scoped ags=06438 Stadt-row causes zero coverage loss.
"""
import sqlite3
import sys
from datetime import date, timedelta

TARGET_AGS = "06438"
CORRECT_STADT_AGS = "06413"
STADT_NAME_SUBSTR = "Stadt Offenbach"


def main(apply_changes: bool) -> None:
    conn = sqlite3.connect("authority_matching.db")
    conn.text_factory = str
    cur = conn.cursor()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    for rt in ["BAUAKTEN", "BAULASTEN"]:
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

        # Confirm the correct replacement exists before touching anything.
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
        print(f"  because correct replacement already exists: [{repl_status}] {repl_name} (ags={CORRECT_STADT_AGS}, jurisdiction_id={repl_id})")

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
                    f"Expired {today}: mis-scoped to ags={TARGET_AGS} (Landkreis Offenbach's ags_kreis) "
                    f"instead of Stadt Offenbach am Main's own ags={CORRECT_STADT_AGS}; correct VERIFIED "
                    f"row already exists there.",
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
