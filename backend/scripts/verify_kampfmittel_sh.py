"""
Kampfmittelauskunft - Schleswig-Holstein: verifiziert die bereits
bestehende, geografisch korrekte STATE-Regel (Landeskriminalamt
Schleswig-Holstein - Kampfmittelräumdienst, Lärchenweg 17, 24242 Felde).

Fachliche Definition (aus templates/kampfmittel.docx): Auskunft über eine
mögliche Kampfmittelbelastung nach den Vorschriften zur
Kampfmittelräumung DES LANDES - Landesrecht/-organisation.

Unabhängig recherchiert und bestätigt (2026-09-26): Nach der
Landesbauordnung Schleswig-Holstein sind Bauherren vor Bauvorhaben/
Tiefbauarbeiten VERPFLICHTET, beim LKA SH eine (kostenpflichtige) Auskunft
zur Kampfmittelbelastung einzuholen - das LKA SH ist damit die tatsächliche,
gesetzlich vorgesehene Auskunftsstelle für genau diese Anfrageart. Die
bereits in der Datenbank hinterlegte Adresse (Lärchenweg 17, 24242 Felde)
stimmt exakt mit der amtlichen Kontaktseite überein.

Quelle: https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/POLIZEI/DasSindWir/LKA/Kampfmittelraeumdienst/kampfmittelraeumdienst.html

Rheinland-Pfalz bewusst NICHT bearbeitet: die zuständige Landesbehörde
(ADD - Aufsichts- und Dienstleistungsdirektion, Kampfmittelräumdienst)
erklärt auf ihrer eigenen Amtsseite ausdrücklich, dass die Beurteilung/
Bescheinigung der Kampfmittelfreiheit von Grundstücken NICHT zu ihren
Aufgaben gehört und auf private Luftbildauswertungs-Unternehmen verweist
(https://add.rlp.de/themen/kommunales-und-sicherheit/kampfmittelraeumdienst).
Eine Jurisdiction-Regel für RLP würde deshalb eine Zuständigkeit behaupten,
die die Behörde selbst verneint - das widerspricht dem Auftrag, keine
Zuständigkeiten zu erfinden. Siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md
für die ausführliche Einordnung.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, siehe source_url)"
SOURCE_URL = (
    "https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/"
    "POLIZEI/DasSindWir/LKA/Kampfmittelraeumdienst/kampfmittelraeumdienst.html"
)


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.jurisdiction import Jurisdiction
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        rule = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == "KAMPFMITTEL",
                Jurisdiction.state == "Schleswig-Holstein",
                Jurisdiction.matching_level == "STATE",
                Jurisdiction.active.is_(True),
            )
            .first()
        )
        if rule is None:
            print("FEHLER: keine aktive KAMPFMITTEL/Schleswig-Holstein/STATE-Regel gefunden - Abbruch.")
            sys.exit(1)

        print(f"Gefundene Regel: {rule.jurisdiction_id}, aktueller Status: {rule.verification_status}")
        if rule.verification_status in ("VERIFIED", "CORRECTED"):
            print("Bereits verifiziert - nichts zu tun (idempotent).")
            return

        staging = JurisdictionStagingService(db)
        verified = staging.verify_existing_rule(
            rule.jurisdiction_id, reviewer=REVIEWER, source_url=SOURCE_URL,
            source="LKA Schleswig-Holstein - Kampfmittelräumdienst (amtliche Kontaktseite)",
            source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
            notes=(
                "Unabhängig recherchiert: Landesbauordnung SH verpflichtet Bauherren zur "
                "kostenpflichtigen Auskunft beim LKA vor Bauvorhaben/Tiefbauarbeiten - LKA SH ist "
                "damit die tatsächliche gesetzliche Auskunftsstelle. Adresse stimmt mit Amtsseite überein."
            ),
        )
        db.commit()
        print(f"Verifiziert: {verified.jurisdiction_id}, verification_status={verified.verification_status}, "
              f"verified_by={verified.verified_by}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
