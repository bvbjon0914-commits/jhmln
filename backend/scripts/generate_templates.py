"""
Generiert die Word-Vorlagen für alle Auskunftsarten.

Layout orientiert sich an den Vonovia-Referenzvorlagen
(Serienbrief_Bauamt_Vorlage.docx / Serienbrief_Grundbuchamt_Vorlage.docx):
Absenderzeile, Trennlinie, Empfängerblock, rechtsbündiges Datum,
fett gesetzter Betreff mit Objektadresse und interner Referenz, Fließtext
mit auskunftsart-spezifischer Rechtsgrundlage, "Betroffenes Objekt/
Grundstück"-Block, Absatz zum berechtigten Interesse, Checkbox-Optionen,
Gebührenhinweis, DSGVO-Hinweis (kursiv/grau), Grußformel, Signatur-
Platzhalter, Anlagenzeile und optionaler Impressum-Fußblock.

Wird einmalig ausgeführt, um die Vorlagen unter /templates zu erzeugen.
Die {{ platzhalter }} bleiben erhalten und werden von docxtpl beim
tatsächlichen Erzeugen der Anschreiben (DocumentGenerationService) befüllt.
"""

import os
import sys

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.request_options import CHECKBOX_OPTIONS  # noqa: E402

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

GRAY = RGBColor(0x59, 0x59, 0x59)


# ---------------------------------------------------------------------------
# Auskunftsart-spezifische Inhalte
#
# subject_line1 / subject_line2: fett gesetzter zweizeiliger Betreff
# legal_basis:   Rechtsgrundlage im Fließtext (Bundesland wird eingesetzt)
# object_label:  "Objekt" oder "Grundstück"
# interest_hint: Klammerbeispiel für das berechtigte Interesse
# (Die ankreuzbaren Anfrageoptionen stehen zentral in
#  app/services/request_options.py und werden als {{ checkbox_i }}-Platzhalter
#  gerendert - ☒/☐ je nach Auswahl beim Generieren.)
# extra_note:    optionaler zusätzlicher Hinweisabsatz (kursiv, wie im
#                Grundbuch-Muster die Anmerkung zu Gemarkung/Flur)
# ---------------------------------------------------------------------------
REQUEST_TYPE_TEXTS = {
    "grundbuch": {
        "subject_line1": "Antrag auf Grundbucheinsicht / Erteilung eines Grundbuchauszugs – Objekt",
        "legal_basis": (
            "hiermit beantrage(n) ich/wir gemäß § 12 der Grundbuchordnung (GBO) "
            "Einsicht in das Grundbuch bzw. die Erteilung eines Grundbuchauszugs für das "
            "nachfolgend bezeichnete Grundstück."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Erbfolge, Bevollmächtigung durch den Eigentümer, "
            "Verkehrswertermittlung im Auftrag"
        ),
        "intro": "Wir bitten um Übersendung eines:",
        "extra_note": (
            "(Gemarkung, Flur und Flurstück sind uns derzeit nicht bekannt – wir bitten "
            "um Identifikation anhand der oben genannten Adresse.)"
        ),
    },
    "bauakten": {
        "subject_line1": "Antrag auf Akteneinsicht / Bauaktenauskunft – Objekt",
        "legal_basis": (
            "hiermit beantrage(n) ich/wir Akteneinsicht bzw. Auskunft aus der Bauakte für "
            "das nachfolgend bezeichnete Objekt. Die Anfrage stützt sich auf die "
            "einschlägigen Vorschriften der Bauordnung des Landes {state} sowie – so "
            "weit einschlägig – auf § 29 des Verwaltungsverfahrensgesetzes (VwVfG) bzw. "
            "das entsprechende Landesverwaltungsverfahrensgesetz."
        ),
        "object_label": "Objekt",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "gutachterliche Tätigkeit"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "baulasten": {
        "subject_line1": "Antrag auf Auskunft aus dem Baulastenverzeichnis – Objekt",
        "legal_basis": (
            "hiermit beantrage(n) ich/wir eine Auskunft aus dem Baulastenverzeichnis nach "
            "der Landesbauordnung des Landes {state} für das nachfolgend bezeichnete "
            "Grundstück."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung einer Bebauung/Veräußerung"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "altlasten": {
        "subject_line1": "Antrag auf Altlastenauskunft – Objekt",
        "legal_basis": (
            "hiermit beantrage(n) ich/wir eine Auskunft aus dem Altlasten-/Bodenschutzkataster "
            "gemäß § 21 des Bundes-Bodenschutzgesetzes (BBodSchG) i. V. m. dem "
            "Bodenschutzrecht des Landes {state} für das nachfolgend bezeichnete Grundstück."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung einer Transaktion/Bebauung"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "erschliessung": {
        "subject_line1": "Anfrage zu Erschließungsbeiträgen / Anliegerbescheinigung – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft über den Stand der Erschließungsbeiträge "
            "gemäß §§ 127 ff. des Baugesetzbuches (BauGB) sowie um Ausstellung einer "
            "Anliegerbescheinigung für das nachfolgend bezeichnete Grundstück."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung einer Transaktion"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "denkmalschutz": {
        "subject_line1": "Anfrage zum Denkmalschutzstatus – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft, ob für das nachfolgend bezeichnete Objekt "
            "eine Eintragung in die Denkmalliste nach dem Denkmalschutzgesetz des Landes "
            "{state} besteht."
        ),
        "object_label": "Objekt",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung von Umbau-/Modernisierungsmaßnahmen"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "bodendenkmalschutz": {
        "subject_line1": "Anfrage zum Bodendenkmalschutz – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft, ob für das nachfolgend bezeichnete "
            "Grundstück Bodendenkmäler nach dem Denkmalschutzgesetz des Landes {state} "
            "bekannt oder eingetragen sind."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung von Baumaßnahmen"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "wasserschutz": {
        "subject_line1": "Anfrage zum Wasserschutzgebiet – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft, ob sich das nachfolgend bezeichnete "
            "Grundstück innerhalb eines festgesetzten Wasserschutzgebietes gemäß § 51 des "
            "Wasserhaushaltsgesetzes (WHG) i. V. m. dem Wassergesetz des Landes {state} "
            "befindet."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung einer Transaktion/Bebauung"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "hochwasserschutz": {
        "subject_line1": "Anfrage zum Hochwasserrisiko – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft, ob das nachfolgend bezeichnete Grundstück "
            "in einem festgesetzten Überschwemmungsgebiet gemäß § 76 des "
            "Wasserhaushaltsgesetzes (WHG) i. V. m. dem Wassergesetz des Landes {state} liegt."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Risikobewertung im Rahmen der Bestandsverwaltung"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "kampfmittel": {
        "subject_line1": "Anfrage zur Kampfmittelfreiheit – Objekt",
        "legal_basis": (
            "hiermit bitte(n) ich/wir um Auskunft über eine mögliche Kampfmittelbelastung des "
            "nachfolgend bezeichneten Grundstücks gemäß den einschlägigen Vorschriften zur "
            "Kampfmittelräumung des Landes {state} sowie ggf. um Mitteilung des weiteren "
            "Vorgehens."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vorbereitung von Baumaßnahmen"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
    "kataster": {
        "subject_line1": "Antrag auf Auskunft aus dem Liegenschaftskataster – Objekt",
        "legal_basis": (
            "hiermit beantrage(n) ich/wir eine aktuelle Auskunft aus dem Liegenschaftskataster "
            "(Flurstücksnachweis / Auszug aus der Liegenschaftskarte) nach dem Vermessungs- "
            "und Katastergesetz des Landes {state} für das nachfolgend bezeichnete "
            "Grundstück."
        ),
        "object_label": "Grundstück",
        "interest_hint": (
            "Eigentümerstellung, Rechtsnachfolge, Bevollmächtigung durch den Eigentümer, "
            "Vermessungs-/Vermarktungszwecke"
        ),
        "intro": "Wir bitten höflich um:",
        "extra_note": None,
    },
}


def _set_bottom_border(paragraph, color="999999", size=6):
    """Fügt einem Absatz eine untere Rahmenlinie hinzu (Trennlinie)."""
    p_pr = paragraph._p.get_or_add_pPr()
    p_borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    p_borders.append(bottom)
    p_pr.append(p_borders)


def _gray_small(paragraph, text, size=8, italic=False):
    run = paragraph.add_run(text)
    run.font.size = Pt(size)
    run.font.color.rgb = GRAY
    run.italic = italic
    return run


def build_template(code: str, texts: dict) -> str:
    """Erstellt ein einzelnes DOCX-Template und gibt den Dateipfad zurück."""
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.line_spacing = 1.05

    section = doc.sections[0]
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    # --- Absenderblock (Civeloq) -----------------------------------
    # Personendaten (Name, Adresse, Telefon, E-Mail) kommen automatisch aus
    # dem eingeloggten Nutzer-Account (siehe app/services/document_generator.py
    # build_context) - nur der Firmenname "Civeloq" bleibt statisch.
    p = doc.add_paragraph()
    run = p.add_run("Civeloq")
    run.bold = True

    p = doc.add_paragraph()
    p.add_run("{{ sender_name }}")

    p = doc.add_paragraph()
    _gray_small(
        p,
        "{{ sender_street }} {{ sender_house_number }} · {{ sender_postal_code }} {{ sender_city }} · "
        "Tel. {{ sender_phone }} · {{ sender_email }}",
    )

    p = doc.add_paragraph()
    _gray_small(
        p,
        "Civeloq · {{ sender_street }} {{ sender_house_number }} · {{ sender_postal_code }} {{ sender_city }}",
        size=7.5,
    )
    _set_bottom_border(p)

    doc.add_paragraph()

    # --- Empfängerblock ------------------------------------------------
    doc.add_paragraph("{{ authority_name }}")
    doc.add_paragraph("{{ authority_department }}")
    doc.add_paragraph("{{ authority_street }} {{ authority_house_number }}")
    doc.add_paragraph("{{ authority_postal_code }} {{ authority_city }}")

    doc.add_paragraph()

    # --- Datum, rechtsbündig -------------------------------------------
    date_p = doc.add_paragraph("Bochum, den {{ current_date }}")
    date_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # --- Aktenzeichen, rechtsbündig --------------------------------------
    az_p = doc.add_paragraph("Unser Zeichen: {{ aktenzeichen }}")
    az_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_paragraph()

    # --- Betreff (zweizeilig, fett) --------------------------------------
    subj1 = doc.add_paragraph()
    r = subj1.add_run(texts["subject_line1"] + " ")
    r.bold = True
    r2 = subj1.add_run("{{ building_street }} {{ building_house_number }}")
    r2.bold = True

    subj2 = doc.add_paragraph()
    r = subj2.add_run(
        "({{ building_postal_code }} {{ building_city }}  –  interne Referenz "
        "{{ internal_reference }})"
    )
    r.bold = True

    doc.add_paragraph()

    # --- Anrede + Anfragetext --------------------------------------------
    doc.add_paragraph("Sehr geehrte Damen und Herren,")
    doc.add_paragraph()

    body_text = texts["legal_basis"].format(state="{{ building_state }}")
    doc.add_paragraph(body_text)
    doc.add_paragraph()

    # --- Objektangaben -----------------------------------------------------
    label_p = doc.add_paragraph()
    label_p.add_run(f"Betroffenes {texts['object_label']}:").bold = True
    doc.add_paragraph("Gemeinde: {{ building_city }}")
    doc.add_paragraph(
        "Adresse: {{ building_street }} {{ building_house_number }}, "
        "{{ building_postal_code }} {{ building_city }}"
    )
    doc.add_paragraph("Bundesland: {{ building_state }}")
    doc.add_paragraph("Interne Referenz-Nr.: {{ internal_reference }}")

    if texts.get("extra_note"):
        note_p = doc.add_paragraph()
        _gray_small(note_p, texts["extra_note"], size=9.5, italic=True)

    doc.add_paragraph()

    # --- Berechtigtes Interesse ---------------------------------------------
    interest_label = "erforderliche berechtigte Interesse"
    doc.add_paragraph(
        f"Das für die Anfrage {interest_label} ergibt sich aus [BITTE ERGÄNZEN: z. B. "
        f"{texts['interest_hint']}]. Einen entsprechenden Nachweis (z. B. Grundbuchauszug, "
        "Vollmacht, Auftragsschreiben) fügen wir diesem Schreiben als Anlage bei."
    )
    doc.add_paragraph()

    # --- Checkboxen ---------------------------------------------------------
    doc.add_paragraph(texts["intro"])
    for i, option in enumerate(CHECKBOX_OPTIONS[code]):
        # Ein einziger Run, damit docxtpl den Platzhalter ersetzen kann.
        doc.add_paragraph(f"{{{{ checkbox_{i} }}}} {option}")
    doc.add_paragraph()

    # --- Gebührenhinweis -----------------------------------------------
    doc.add_paragraph(
        "Für die Bearbeitung dieser Anfrage anfallende Verwaltungsgebühren gemäß der "
        "für Sie geltenden Gebührenordnung werden von uns übernommen. Sollten die Kosten "
        "voraussichtlich [BETRAG] EUR übersteigen, bitten wir um vorherige Mitteilung."
    )
    doc.add_paragraph()

    # --- DSGVO-Hinweis (kursiv, grau) ----------------------------------
    dsgvo_p = doc.add_paragraph()
    _gray_small(
        dsgvo_p,
        "Datenschutzhinweis: Die von uns im Rahmen dieser Anfrage übermittelten sowie die "
        "im Zuge der Bearbeitung ggf. erhaltenen personenbezogenen Daten werden von uns "
        "ausschließlich zur Bearbeitung dieses Anliegens auf Grundlage von Art. 6 Abs. 1 "
        "lit. f DSGVO (berechtigtes Interesse) bzw. Art. 6 Abs. 1 lit. c DSGVO (rechtliche "
        "Verpflichtung) verarbeitet und nicht an unbefugte Dritte weitergegeben.",
        size=10,
        italic=True,
    )
    doc.add_paragraph()

    doc.add_paragraph(
        "Für Rückfragen stehen wir Ihnen gerne unter den oben genannten Kontaktdaten zur "
        "Verfügung. Vielen Dank für Ihre Unterstützung."
    )
    doc.add_paragraph()

    doc.add_paragraph("Mit freundlichen Grüßen")
    doc.add_paragraph()
    doc.add_paragraph("{{ sender_name }}")
    doc.add_paragraph("{{ sender_function }}")
    doc.add_paragraph()

    anlagen_p = doc.add_paragraph()
    r = anlagen_p.add_run("Anlagen: [ggf. Vollmacht / Eigentumsnachweis / Auftragsschreiben]")
    r.italic = True

    # --- Impressum-Fußblock -------------------------------------------
    doc.add_paragraph()
    impressum_p = doc.add_paragraph()
    _set_bottom_border(impressum_p, color="CCCCCC", size=4)
    impressum_p.add_run(
        "Civeloq · Sitz: [Ort] · Registergericht: [Amtsgericht] · "
        "Registernummer: [HRB ...] · Vorstand: [Name(n)] · USt-IdNr.: [DE ...]"
    ).font.size = Pt(8)
    hint_p = doc.add_paragraph()
    _gray_small(
        hint_p,
        "(Hinweis: Dieser Impressum-Block ist nur erforderlich, wenn der Absender ein im "
        "Handelsregister eingetragenes Unternehmen ist, § 37a HGB / § 35a AktG. Bitte die "
        "eckigen Klammern vor Versand ausfüllen.)",
        size=7.5,
        italic=True,
    )

    output_path = os.path.join(TEMPLATES_DIR, f"{code}.docx")
    doc.save(output_path)
    return output_path


def main():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    for code, texts in REQUEST_TYPE_TEXTS.items():
        path = build_template(code, texts)
        print(f"✓ Erstellt: {path}")


if __name__ == "__main__":
    main()
