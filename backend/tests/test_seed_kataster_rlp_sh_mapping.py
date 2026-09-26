"""
Absichert die statische Kreis-Zuordnung in scripts/seed_kataster_rlp_sh.py
(Liegenschaftskataster RLP+SH) gegen die amtliche AGS-Referenztabelle:
jeder zugeordnete ags_kreis muss real existieren, kein Kreis darf doppelt
oder gar nicht zugeordnet sein (36 RLP + 15 SH insgesamt).
"""
from scripts.seed_kataster_rlp_sh import RLP_OFFICES, SH_OFFICES


def test_rlp_mapping_covers_all_36_kreise_exactly_once():
    rlp_kreise = [
        "07111", "07131", "07132", "07133", "07134", "07135", "07137", "07138",
        "07140", "07141", "07143", "07211", "07231", "07232", "07233", "07235",
        "07311", "07312", "07313", "07314", "07315", "07316", "07317", "07318",
        "07319", "07320", "07331", "07332", "07333", "07334", "07335", "07336",
        "07337", "07338", "07339", "07340",
    ]
    assert len(rlp_kreise) == 36

    assigned = [k for kreise in RLP_OFFICES.values() for k in kreise]
    assert sorted(assigned) == sorted(rlp_kreise), "RLP-Zuordnung deckt nicht exakt alle 36 Kreise/Städte ab"
    assert len(assigned) == len(set(assigned)), "Ein Kreis ist mehreren VermKÄ zugeordnet"


def test_sh_mapping_covers_all_15_kreise_exactly_once():
    sh_kreise = [
        "01001", "01002", "01003", "01004", "01051", "01053", "01054", "01055",
        "01056", "01057", "01058", "01059", "01060", "01061", "01062",
    ]
    assert len(sh_kreise) == 15

    assigned = [k for kreise in SH_OFFICES.values() for k in kreise]
    assert sorted(assigned) == sorted(sh_kreise), "SH-Zuordnung deckt nicht exakt alle 15 Kreise/Städte ab"
    assert len(assigned) == len(set(assigned)), "Ein Kreis ist mehreren Katasterämtern zugeordnet"
