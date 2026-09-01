@echo off
REM Startet das Authority-Matching Frontend.
REM Beim ersten Ausfuehren: installiert npm-Pakete.
REM Danach: startet einfach nur den Dev-Server.

cd /d %~dp0

if not exist node_modules (
    echo [1/1] Installiere npm-Pakete (kann etwas dauern) ...
    npm install
)

echo.
echo Frontend startet auf http://localhost:5173
echo WICHTIG: Das Backend muss parallel in einem zweiten Fenster laufen (start-backend.bat)
echo.
npm run dev

pause
