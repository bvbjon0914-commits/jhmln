# -*- coding: utf-8 -*-
"""Fix 92 KAMPFMITTEL MUNICIPALITY-level duplicates in Sachsen, found by a
diagnostic pass over the 102 duplicate-ags groups surfaced by the nationwide
duplicate inventory (all located in Sachsen, ags prefix "14", spread across
10 Landkreise).

Root cause: a per-Gemeinde import created, for many Sachsen Gemeinden, a
SECOND jurisdiction row wrongly filed under a NEIGHBORING Gemeinde's ags,
carrying that OTHER Gemeinde's real authority label and address copied
verbatim from its own already-correct row (e.g. ags=14521040, Auerbach, has
its own genuine row "Auerbach - Ortspolizeibehoerde" at Hauptstrasse 83, PLUS
a stray second row also under Auerbach's ags but with authority_name/city/
street identical to Burkhardtsdorf's own correct row at ags=14521120). Same
bug shape as Offenbach/Kassel/Heilbronn/Karlsruhe (a real entity's row
mis-scoped under someone else's ags), just instantiated ~90 times within one
state's Kampfmittel data.

Every one of the 92 candidates below was verified (by a diagnostic agent,
then independently re-derived and spot-checked against the live DB) to have:
  - the "wrong" row's authority_name/city/street/house_number identical to an
    ALREADY-CORRECT, independently-existing row for a different Gemeinde
    elsewhere, and
  - the genuine self-row for the affected ags left completely untouched.
Expiring the mis-filed row therefore causes zero coverage loss anywhere.

Explicitly NOT included: 10 further duplicate-ags groups (Bergen, Theuma,
Werda, Hohendubrau, Muecka, Quitzdorf am See, Bahretal, Liebstadt, Jesewitz,
Zschepplin) whose "wrong" row cites an address that does NOT match ANY
existing correct row for the named city either - a deeper, still-unresolved
mislabeling issue (see docs/ABSCHLUSSBERICHT_DATENQUALITAET.md) that needs
its own investigation before any fix; left OFFEN/untouched by this script.

The candidate list is generated fresh from the DB by re-running the same
verified classification logic inline (not by trusting a static file), so
this script is self-contained and safely re-runnable/idempotent.
"""
import re
import sqlite3
import sys
from datetime import date, timedelta

REQUEST_TYPE_ID = "KAMPFMITTEL"
EXCLUDED_AGS = {"11000000", "02000000"}


def canonical_name(name):
    if not name:
        return ""
    n = name
    if " / " in n:
        n = n.split(" / ")[0]
    if "/" in n:
        n = n.split("/")[0]
    n = n.split(",")[0]
    return n.strip().lower()


def norm_addr(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("straße", "str").replace("strasse", "str")
    s = s.replace("str.", "str")
    s = re.sub(r"\s+", " ", s)
    return s.rstrip(".")


def addr_match(true_row, other_row):
    return (
        norm_addr(true_row[4]) == norm_addr(other_row[4])
        and norm_addr(true_row[5]) == norm_addr(other_row[5])
        and canonical_name(true_row[3]) == canonical_name(other_row[3])
    )


def find_candidates(cur):
    cur.execute(
        """
        SELECT ags FROM jurisdictions
        WHERE request_type_id = ? AND matching_level = 'MUNICIPALITY'
          AND (valid_to IS NULL OR valid_to >= date('now')) AND active = 1
          AND ags NOT IN ('11000000', '02000000')
        GROUP BY ags HAVING COUNT(*) > 1
        ORDER BY ags
        """,
        (REQUEST_TYPE_ID,),
    )
    groups = [r[0] for r in cur.fetchall()]

    def rows_for_ags(ags):
        cur.execute(
            """
            SELECT j.jurisdiction_id, j.authority_id, a.authority_name, a.city, a.street, a.house_number
            FROM jurisdictions j JOIN authorities a ON a.authority_id = j.authority_id
            WHERE j.request_type_id = ? AND j.ags = ? AND j.matching_level = 'MUNICIPALITY'
              AND (j.valid_to IS NULL OR j.valid_to >= date('now')) AND j.active = 1
            """,
            (REQUEST_TYPE_ID, ags),
        )
        return cur.fetchall()

    kreis_cache = {}

    def candidate_ags_for_kreis(kreis_prefix):
        if kreis_prefix not in kreis_cache:
            cur.execute(
                "SELECT ags, municipality_name FROM administrative_units WHERE ags_kreis=?",
                (kreis_prefix,),
            )
            kreis_cache[kreis_prefix] = cur.fetchall()
        return kreis_cache[kreis_prefix]

    safe = []
    unclear = []
    for ags in groups:
        rows = rows_for_ags(ags)
        kreis_units = candidate_ags_for_kreis(ags[:5])
        if len(rows) != 2:
            unclear.append((ags, "not_a_pair", rows))
            continue

        info = [{}, {}]
        for i, r in enumerate(rows):
            canon_city = canonical_name(r[3])
            cands = [c for c in kreis_units if canonical_name(c[1]) == canon_city]
            cands = list({c[0]: c for c in cands}.values())
            if len(cands) == 0 and canon_city:
                cands = [
                    c for c in kreis_units
                    if canonical_name(c[1]).startswith(canon_city + " ")
                    or canonical_name(c[1]).startswith(canon_city + "-")
                ]
                cands = list({c[0]: c for c in cands}.values())
            info[i]["row"] = r
            if len(cands) == 1:
                cand_ags = cands[0][0]
                if cand_ags == ags:
                    info[i]["is_self"] = True
                else:
                    true_rows = rows_for_ags(cand_ags)
                    if len(true_rows) == 1 and addr_match(true_rows[0], r):
                        info[i]["external_dup_of"] = (cand_ags, true_rows[0])

        ext_dup_idxs = [i for i in (0, 1) if "external_dup_of" in info[i]]
        if len(ext_dup_idxs) == 1:
            oi = ext_dup_idxs[0]
            wrong_row = info[oi]["row"]
            correct_ags, correct_row = info[oi]["external_dup_of"]
            safe.append((ags, wrong_row, correct_ags, correct_row))
        else:
            unclear.append((ags, "no_unique_external_dup", rows))

    return safe, unclear


def main(apply_changes: bool) -> None:
    conn = sqlite3.connect("authority_matching.db")
    conn.text_factory = str
    cur = conn.cursor()

    safe, unclear = find_candidates(cur)
    print(f"{len(safe)} SAFE_MISSCOPED_DUP, {len(unclear)} UNCLEAR (left untouched)")

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    for ags, wrong_row, correct_ags, correct_row in safe:
        wrong_id, _, wrong_name, wrong_city, wrong_street, wrong_house = wrong_row
        correct_id, _, correct_name, _, _, _ = correct_row
        print(
            f"  ags={ags}: EXPIRE jurisdiction_id={wrong_id} "
            f"('{wrong_name}' but address is really {wrong_city}'s: {wrong_street} {wrong_house}) "
            f"-- correct row {correct_id} at ags={correct_ags} ('{correct_name}')"
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
                    f"Expired {today}: mis-filed under ags={ags}, address/name actually belongs to "
                    f"the already-correct row at ags={correct_ags} (jurisdiction_id={correct_id}).",
                    wrong_id,
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
