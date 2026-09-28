# -*- coding: utf-8 -*-
"""Read-only diagnostic: categorize all BAUAKTEN/BAULASTEN MUNICIPALITY duplicate-ags
pairs to see how many match the established 'Landkreis X pinned to Kreisstadt AGS,
correct COUNTY row already exists' bug pattern vs need individual review.
Uses AGS-based Kreis lookup (robust) instead of fragile authority-name matching."""
import sqlite3

conn = sqlite3.connect("authority_matching.db")
conn.text_factory = str
cur = conn.cursor()

for rt in ["BAUAKTEN", "BAULASTEN"]:
    print(f"\n{'='*20} {rt} {'='*20}")
    cur.execute("""
        SELECT ags FROM jurisdictions
        WHERE active=1 AND request_type_id=? AND matching_level='MUNICIPALITY'
        AND (valid_to IS NULL OR valid_to >= date('now')) AND ags IS NOT NULL
        GROUP BY ags HAVING COUNT(*) > 1
    """, (rt,))
    dup_ags = [r[0] for r in cur.fetchall()]
    print(f"{len(dup_ags)} duplicate AGS groups")

    clean_pattern = []
    needs_review = []
    for ags in dup_ags:
        cur.execute("""
            SELECT j.jurisdiction_id, a.authority_name, j.priority, j.verification_status
            FROM jurisdictions j JOIN authorities a ON a.authority_id = j.authority_id
            WHERE j.active=1 AND j.request_type_id=? AND j.ags=? AND j.matching_level='MUNICIPALITY'
            AND (j.valid_to IS NULL OR j.valid_to >= date('now'))
        """, (rt, ags))
        rows = cur.fetchall()
        names = [r[1] for r in rows]
        landkreis_rows = [r for r in rows if r[1].startswith("Landkreis ") or r[1].startswith("Kreis ")]
        other_rows = [r for r in rows if r not in landkreis_rows]

        # Look up the Kreis this ags belongs to
        cur.execute("SELECT DISTINCT ags_kreis FROM administrative_units WHERE ags=?", (ags,))
        kreis_row = cur.fetchone()
        ags_kreis = kreis_row[0] if kreis_row else None

        if len(rows) == 2 and len(landkreis_rows) == 1 and len(other_rows) == 1 and ags_kreis:
            cur.execute("""
                SELECT j.jurisdiction_id, a.authority_name FROM jurisdictions j
                JOIN authorities a ON a.authority_id = j.authority_id
                WHERE j.active=1 AND j.request_type_id=? AND j.matching_level='COUNTY'
                AND (j.valid_to IS NULL OR j.valid_to >= date('now'))
                AND j.ags = ?
            """, (rt, ags_kreis))
            county_matches = cur.fetchall()
            if county_matches:
                clean_pattern.append((ags, ags_kreis, landkreis_rows[0], other_rows[0], county_matches[0]))
            else:
                needs_review.append((ags, names, f"no COUNTY row for ags_kreis={ags_kreis}"))
        else:
            needs_review.append((ags, names, f"unexpected shape ({len(rows)} rows, {len(landkreis_rows)} Landkreis-named, ags_kreis={ags_kreis})"))

    print(f"Clean pattern (Landkreis+Stadt pair, correct COUNTY row exists): {len(clean_pattern)}")
    print(f"Needs individual review: {len(needs_review)}")
    for ags, names, reason in needs_review:
        print(f"  {ags}: {names} -- {reason}")

    print(f"\n--- Clean pattern details (first 10) ---")
    for ags, ags_kreis, lk_row, other_row, county_row in clean_pattern[:10]:
        print(f"  ags={ags} kreis={ags_kreis}: EXPIRE [{lk_row[1]}] KEEP [{other_row[1]}] (COUNTY exists: [{county_row[1]}])")
