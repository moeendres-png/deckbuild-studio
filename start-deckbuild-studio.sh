#!/bin/sh
# Starter for Deckbuild Studio (Linux/macOS).
# Starts the local server in the background and opens the UI.
cd "$(dirname "$0")" || exit 1
exec python3 launcher.py "$@"
