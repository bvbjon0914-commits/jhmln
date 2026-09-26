"""
Lädt das amtliche Destatis-Anschriftenverzeichnis der Gemeinde- und
Stadtverwaltungen (sowie Verbandsgemeinden/Ämter/Landkreise) und macht es
über den Amtlichen Regionalschlüssel (ARS) nachschlagbar.

WICHTIG (Auftrag: "Die allgemeine Verwaltungs-E-Mail darf nicht automatisch
zum bestätigten Fachamtkontakt werden"): dieses Modul liefert AUSSCHLIESSLICH
Organisationsname, Adresse und allgemeine Kontakt-E-Mail - es liefert NIE
eine fachliche Zuständigkeitsaussage. Ob eine hier gefundene Organisation
für eine bestimmte Auskunftsart zuständig ist, muss IMMER separat belegt
werden (Fundstelle mit fachlichem Bezug, nicht nur diese Adresse).

Datei selbst wird NICHT ins Repository übernommen (großes, außerhalb dieses
Projekts lizenziertes Werk, wie auch die VG250-Rohdaten) - der Pfad wird
pro Aufruf übergeben.

Satzarten im Destatis-Verzeichnis (Spalte "Satzart"):
    10 = Bund, 20 = Land, 30 = Regierungsbezirk, 40 = Kreis/kreisfreie Stadt,
    50 = Verwaltungsgemeinschaft/Verbandsgemeinde/Amt/Samtgemeinde,
    60 = Gemeinde/Stadt
"""
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

SATZART_BUND = 10
SATZART_LAND = 20
SATZART_KREIS = 40
SATZART_VERBANDSGEMEINDE = 50
SATZART_GEMEINDE = 60

_COLUMNS = [
    "Land_code", "Land_name", "Satzart", "Textkennzeichen", "Textkennzeichen_label",
    "ARS", "AGS", "Gemeinde", "Verwaltungssitz", "Strasse", "PLZ", "Ort", "Email",
    "Flaeche", "Bev_insgesamt", "Bev_m", "Bev_w", "Bev_je_km2",
]


@dataclass
class AddressEntry:
    ars: str
    ags: Optional[str]
    name: str
    strasse: Optional[str]
    plz: Optional[str]
    ort: Optional[str]
    email: Optional[str]
    satzart: int


def load_address_directory(xlsx_path: str, sheet_name: str = "Anschriften_31_01_2026") -> pd.DataFrame:
    """Liest das Destatis-Anschriftenverzeichnis roh ein (Header ab Zeile 4)."""
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=3)
    df.columns = _COLUMNS
    # Zeile 4 (0-indiziert) der Originaldatei ist eine zweite, gemessene
    # Einheiten-Unterkopfzeile ("in km2", "insgesamt", ...) ohne Satzart/ARS -
    # wird hier als Kopfzeilen-Artefakt verworfen, nicht als Datenzeile gezählt.
    df = df[df["Satzart"].notna()].copy()
    df["ARS"] = df["ARS"].apply(lambda v: str(int(v)) if pd.notna(v) else None)
    df["AGS"] = df["AGS"].apply(lambda v: str(int(v)).zfill(8) if pd.notna(v) else None)
    return df


def build_ars_index(df: pd.DataFrame) -> Dict[str, AddressEntry]:
    """Baut ein ARS -> AddressEntry-Nachschlagewerk (ein Eintrag pro ARS)."""
    index: Dict[str, AddressEntry] = {}
    for _, row in df.iterrows():
        if not row["ARS"]:
            continue
        index[row["ARS"]] = AddressEntry(
            ars=row["ARS"], ags=row["AGS"], name=str(row["Gemeinde"]),
            strasse=row["Strasse"] if pd.notna(row["Strasse"]) else None,
            plz=str(int(row["PLZ"])) if pd.notna(row["PLZ"]) else None,
            ort=row["Ort"] if pd.notna(row["Ort"]) else None,
            email=row["Email"] if pd.notna(row["Email"]) else None,
            satzart=int(row["Satzart"]),
        )
    return index
