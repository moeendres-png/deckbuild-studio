# Programm-Launcher (Doppelklick-Starter)

Deckbuild Studio bleibt eine lokale Web-App (Server + Browser-UI,
Port 8765). Der Launcher nimmt nur den manuellen Serverstart ab:

- **Windows:** `Start-Deckbuild-Studio.bat` doppelklicken.
- **Linux/macOS:** `start-deckbuild-studio.sh` ausführen
  (oder `python3 launcher.py`).

## Verhalten von `launcher.py`

1. Prüft, ob die UI unter `http://127.0.0.1:8765/` schon erreichbar ist.
   Wenn ja, wird kein zweiter Server gestartet.
2. Sonst startet er den Server abgelöst im Hintergrund
   (`mtg-deckbuilder serve`, Ausgabe nach `launcher-server.log` im
   Datenordner) und wartet, bis der Port antwortet (max. 30 s).
3. Öffnet danach die UI im Standard-Browser.

Der Launcher selbst braucht nur die Python-Standardbibliothek
(Python 3.12+). Für den Server nutzt er, in dieser Reihenfolge: das
Projekt-Virtualenv (`.venv`), das installierte `mtg-deckbuilder`-Skript
oder den aktuellen Interpreter.

## Optionen

| Option | Wirkung |
|---|---|
| `--port N` | anderer Port (Standard 8765) |
| `--no-browser` | Server starten, ohne den Browser zu öffnen |
| `--check` | nur melden, ob der Server läuft (Exit-Code 0/1); startet nichts |

Schlägt der Start fehl, steht die Server-Ausgabe in
`launcher-server.log` im Datenordner (`MTG_DECKBUILDER_DATA`, Standard
`~/.local/share/mtg-collection-deckbuilder`).
