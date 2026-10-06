"""
Ankreuzbare Optionen je Auskunftsart (Single Source of Truth).

Wird vom Template-Generator (scripts/generate_templates.py), vom
Request-Types-Endpoint und vom DocumentGenerationService verwendet.
Der Schluessel entspricht dem Template-Code (request_type_id kleingeschrieben).
Die Reihenfolge der Optionen ist verbindlich: Index i entspricht dem
Platzhalter {{ checkbox_i }} im Word-Template und den gespeicherten
RequestItem.selected_options.
"""

from typing import Dict, List, Optional

CHECKBOX_OPTIONS: Dict[str, List[str]] = {
    "grundbuch": [
        "einfachen Grundbuchauszugs",
        "beglaubigten Grundbuchauszugs",
    ],
    "bauakten": [
        (
            "Übersendung von Kopien der vorhandenen Bauakte(n) (insbesondere Baugenehmigung, "
            "genehmigte Baupläne/Lagepläne, Abnahmeprotokolle)"
        ),
        "Mitteilung, ob und in welchem Umfang Bauakten zu diesem Objekt bei Ihnen vorliegen",
        "Terminvereinbarung zur Einsichtnahme vor Ort in Ihren Diensträumen",
    ],
    "baulasten": [
        "Übersendung eines aktuellen Auszugs aus dem Baulastenverzeichnis",
        "Mitteilung, ob und welche Baulasten zu diesem Grundstück eingetragen sind",
    ],
    "altlasten": [
        "Mitteilung, ob das Grundstück im Altlasten-/Bodenschutzkataster erfasst ist",
        "Übersendung vorhandener Unterlagen (Gutachten, Untersuchungsberichte)",
    ],
    "erschliessung": [
        "Mitteilung, ob Erschließungsbeiträge noch offen sind oder abgerechnet wurden",
        "Ausstellung einer Anliegerbescheinigung (Unbedenklichkeitsbescheinigung)",
    ],
    "denkmalschutz": [
        "Mitteilung, ob das Objekt in die Denkmalliste eingetragen ist",
        "Übersendung eines Auszugs aus der Denkmalliste bzw. relevanter Unterlagen",
    ],
    "bodendenkmalschutz": [
        "Mitteilung, ob Bodendenkmäler auf dem Grundstück bekannt/eingetragen sind",
        "Übersendung relevanter Unterlagen bzw. Auflagen für Baumaßnahmen",
    ],
    "wasserschutz": [
        "Mitteilung, ob das Grundstück in einem Wasserschutzgebiet liegt (inkl. Zone)",
        "Übersendung geltender Schutzgebietsverordnungen/Auflagen",
    ],
    "hochwasserschutz": [
        "Mitteilung, ob das Grundstück in einem Überschwemmungsgebiet liegt",
        "Übersendung von Hochwassergefahrenkarten bzw. relevanter Unterlagen",
    ],
    "kampfmittel": [
        "Auswertung der Luftbilder / Mitteilung des Ergebnisses",
        "Mitteilung, ob eine Sondierung/Räumung erforderlich ist",
    ],
    "kataster": [
        "Übersendung eines aktuellen Flurstücksnachweises",
        "Übersendung eines Auszugs aus der Liegenschaftskarte",
    ],
}


def get_checkbox_options(request_type_id_or_code: Optional[str]) -> List[str]:
    """Optionslabels einer Auskunftsart (leere Liste bei unbekannt/None)."""
    if not request_type_id_or_code:
        return []
    return list(CHECKBOX_OPTIONS.get(request_type_id_or_code.strip().lower(), []))


def sanitize_selection(request_type_id_or_code: Optional[str], indices) -> List[int]:
    """
    Bereinigt eine Auswahl: nur gueltige, eindeutige Indizes (0-basiert),
    aufsteigend sortiert. Alles andere (negativ, ausserhalb, Duplikate,
    Nicht-Integer, bool) wird verworfen - wirft nie.
    """
    count = len(get_checkbox_options(request_type_id_or_code))
    if not isinstance(indices, (list, tuple, set)):
        return []
    valid = {
        i for i in indices
        if isinstance(i, int) and not isinstance(i, bool) and 0 <= i < count
    }
    return sorted(valid)
