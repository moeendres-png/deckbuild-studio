@echo off
rem Doppelklick-Starter fuer den Browser-Decklisten-Sammler (Windows).
rem Das Fenster bleibt am Ende IMMER offen (pause), damit Meldungen
rem und Fehler sichtbar bleiben.
cd /d %~dp0
where py >nul 2>nul
if %errorlevel% neq 0 (
    echo Python wurde nicht gefunden. Bitte Python 3.12+ installieren.
    pause
    exit /b 1
)
py -3 -c "import playwright" 2>nul
if %errorlevel% neq 0 (
    echo Playwright fehlt - installiere es jetzt einmalig ...
    py -3 -m pip install playwright
    py -3 -m playwright install chromium
)
echo.
echo Starte Sammler: EDHREC-Decklisten aus der Studio-Datenbank, max. 50.
echo Tab 1 im Browser oeffnet sich: dort ggf. "Accept All" klicken,
echo danach hier ENTER druecken.
echo.
py -3 browser_deck_harvest.py --edhrec-from-db --limit 50
echo.
echo Fertig. Die Listen liegen in decklists_browser.jsonl
echo (diese Datei danach an Muse zurueckgeben).
pause
