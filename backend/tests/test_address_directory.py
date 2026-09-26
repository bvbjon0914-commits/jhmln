"""
Tests für app/services/address_directory.py (Destatis-Anschriftenverzeichnis).

Nutzt eine winzige, synthetische Test-Excel-Datei mit derselben Struktur
wie das echte Verzeichnis (tests/fixtures/mini_anschriften.xlsx) - NIE die
echte, große Destatis-Datei in Tests einbinden.
"""
import os

from app.services.address_directory import (
    SATZART_GEMEINDE,
    SATZART_VERBANDSGEMEINDE,
    build_ars_index,
    load_address_directory,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "mini_anschriften.xlsx")


def test_load_address_directory_parses_header_and_types():
    df = load_address_directory(FIXTURE_PATH)
    assert len(df) == 2
    assert df.iloc[0]["ARS"] == "71315001"
    assert df.iloc[0]["Satzart"] == 50
    assert df.iloc[1]["AGS"] == "07132001"


def test_build_ars_index_looks_up_verbandsgemeinde_by_ars():
    df = load_address_directory(FIXTURE_PATH)
    index = build_ars_index(df)

    entry = index["71315001"]
    assert entry.name == "Verbandsgemeindeverwaltung Adenau"
    assert entry.satzart == SATZART_VERBANDSGEMEINDE
    assert entry.plz == "53518"
    assert entry.ort == "Adenau"
    assert entry.email == "vgadenau@adenau.de"


def test_index_distinguishes_gemeinde_from_verbandsgemeinde_satzart():
    df = load_address_directory(FIXTURE_PATH)
    index = build_ars_index(df)

    gemeinde_entry = index["71315001004"]
    assert gemeinde_entry.satzart == SATZART_GEMEINDE
    assert gemeinde_entry.name == "Antweiler"
    # Die Gemeinde-Zeile hat in diesem Verzeichnis keine eigene Adresse/E-Mail hinterlegt.
    assert gemeinde_entry.email is None
