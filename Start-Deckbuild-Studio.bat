@echo off
rem Double-click starter for Deckbuild Studio (Windows).
rem Starts the local server in the background and opens the UI.
cd /d %~dp0
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 launcher.py %*
) else (
    python launcher.py %*
)
if %errorlevel% neq 0 (
    echo.
    echo Start fehlgeschlagen - siehe Meldung oben.
    pause
)
