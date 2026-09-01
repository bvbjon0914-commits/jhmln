@echo off
REM Startet das Authority-Matching Backend.
REM Beim ersten Ausfuehren: legt venv an, installiert Pakete, erzeugt Vorlagen + Testdaten.
REM Danach: startet einfach nur den Server.

cd /d %~dp0

if not exist venv (
    echo [1/4] Erstelle virtuelle Python-Umgebung ...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [2/4] Installiere Python-Pakete ...
pip install -q -r requirements.txt

if not exist templates\grundbuch.docx (
    echo [3/4] Erzeuge Word-Vorlagen ...
    python scripts\generate_templates.py
)

if not exist authority_matching.db (
    echo [4/4] Lege Testdaten an ...
    python scripts\seed_data.py
)

echo.
echo Backend startet auf http://localhost:8000  (Strg+C zum Beenden)
echo.
uvicorn app.main:app --reload

pause
