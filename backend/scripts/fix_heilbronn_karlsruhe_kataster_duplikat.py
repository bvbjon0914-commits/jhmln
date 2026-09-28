# -*- coding: utf-8 -*-
"""Fix two KATASTER MUNICIPALITY-level duplicates: "Katasteramt Heilbronn" and
"Katasteramt Karlsruhe" (no "Stadt" suffix) are, despite their generic names,
actually the respective LANDKREIS cadastral offices - mis-scoped onto the
neighboring kreisfreie Stadt's ags (08121000 / 08212000) instead of their own
Landkreis ags (08125 / 08215). Same bug shape as Offenbach/Kassel, just
disguised by a name that doesn't literally repeat "Landkreis"/"Stadt".

Evidence (see docs/ABSCHLUSSBERICHT_DATENQUALITAET.md for the full writeup):
- "Katasteramt Heilbronn" (Lerchenstrasse 40, www.landkreis-heilbronn.de) has
  the IDENTICAL street address as the already-VERIFIED "Landratsamt Heilbronn
  - Vermessungsamt" (ags=08125, COUNTY).
- "Katasteramt Karlsruhe" (Beiertheimer Allee 2, www.landkreis-karlsruhe.de)
  is confirmed via the official LGL Baden-Wuerttemberg list of "Untere
  Vermessungsbehoerden - Landratsaemter" as the real address of Landratsamt
  Karlsruhe's Amt fuer Vermessung, Geoinformation und Flurneuordnung - the
  same real office as the already-VERIFIED COUNTY-level row (ags=08215),
  just a different building of the same Kreisverwaltung than the address
  currently stored there.

Both kreisfreie Staedte (Heilbronn, Karlsruhe) already have their own,
correctly-scoped "Katasteramt X, Stadt" row at the same ags - these are left
untouched. Expiring the mis-scoped Landkreis-under-city-name rows causes zero
coverage loss.
"""
import sqlite3
import sys
from datetime import date, timedelta

# (mis-scoped MUNICIPALITY ags, authority name to expire, correct COUNTY ags,
#  city label for messages)
TARGETS = [
    ("08121000", "Katasteramt Heilbronn", "08125", "Heilbronn"),
    ("08212000", "Katasteramt Karlsruhe", "08215", "Karlsruhe"),
]
REQUEST_TYPE_CODE = "KATASTER"


def main(apply_changes: bool) -> None:
    conn = sqlite3.connect("authority_matching.db")
    conn.text_factory = str
    cur = conn.cursor()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    for mis_ags, authority_name, correct_ags, city in TARGETS:
        print(f"\n{'=' * 20} {city} {'=' * 20}")
        cur.execute(
            """
            SELECT j.jurisdiction_id, j.verification_status
            FROM jurisdictions j
            JOIN authorities a ON a.authority_id = j.authority_id
            WHERE j.active = 1
              AND j.request_type_id = (SELECT request_type_id FROM request_types WHERE code = ?)
              AND j.ags = ?
              AND a.authority_name = ?
              AND (j.valid_to IS NULL OR j.valid_to >= date('now'))
            """,
            (REQUEST_TYPE_CODE, mis_ags, authority_name),
        )
        rows = cur.fetchall()
        if len(rows) != 1:
            print(f"  UNEXPECTED shape ({len(rows)} rows) - skipping, needs manual review")
            continue
        expire_id, expire_status = rows[0]

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
            (REQUEST_TYPE_CODE, correct_ags),
        )
        replacement = cur.fetchall()
        if not replacement:
            print(f"  NO replacement row found at ags={correct_ags} - skipping, needs manual review")
            continue
        repl_id, repl_name, repl_status = replacement[0]

        print(f"  EXPIRE [{expire_status}] {authority_name} (ags={mis_ags}, jurisdiction_id={expire_id})")
        print(
            f"  because correct replacement already exists: [{repl_status}] {repl_name} "
            f"(ags={correct_ags}, jurisdiction_id={repl_id})"
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
                    f"Expired {today}: mis-scoped to ags={mis_ags} (kreisfreie Stadt {city}'s ags) "
                    f"instead of Landkreis {city}'s own ags={correct_ags}; correct VERIFIED row "
                    f"already exists there (identical address / official LGL-BW list confirmed).",
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
