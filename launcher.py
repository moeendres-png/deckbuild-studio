#!/usr/bin/env python3
"""Double-click launcher for Deckbuild Studio.

Starts the local web UI server in the background (if it is not already
running) and opens the UI in the default browser. Standard library only,
so any Python 3.12+ interpreter can run this file directly.

Usage:
    python launcher.py [--port 8765] [--no-browser] [--check]

--check only reports whether the server is reachable and exits; it never
starts anything.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
START_TIMEOUT_SECONDS = 30.0
PROBE_INTERVAL_SECONDS = 0.25

ROOT = Path(__file__).resolve().parent


def probe(port: int, timeout: float = 0.5) -> bool:
    """True when something accepts a TCP connection on HOST:port."""
    try:
        with socket.create_connection((HOST, port), timeout=timeout):
            return True
    except OSError:
        return False


def _venv_python() -> Path | None:
    """Interpreter of a project-local virtualenv, if one exists."""
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",  # Windows layout
        ROOT / ".venv" / "bin" / "python",  # POSIX layout
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def server_command(port: int) -> list[str]:
    """Command that starts the Deckbuild Studio server on ``port``.

    Preference order: the project virtualenv's interpreter, then the
    installed ``mtg-deckbuilder`` console script, then the current
    interpreter (works when the package is installed into it).
    """
    venv_python = _venv_python()
    if venv_python is not None:
        return [str(venv_python), "-m", "deckbuild_studio.cli",
                "serve", "--port", str(port)]
    console_script = shutil.which("mtg-deckbuilder")
    if console_script is not None:
        return [console_script, "serve", "--port", str(port)]
    return [sys.executable, "-m", "deckbuild_studio.cli",
            "serve", "--port", str(port)]


def _log_path() -> Path:
    data_dir = os.environ.get("MTG_DECKBUILDER_DATA")
    base = Path(data_dir) if data_dir else (
        Path.home() / ".local" / "share" / "mtg-collection-deckbuilder")
    return base / "launcher-server.log"


def start_server(port: int) -> subprocess.Popen[bytes]:
    """Start the server detached, with output going to the log file."""
    command = server_command(port)
    log_file = None
    try:
        log_path = _log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path.open("ab")
        print(f"Server-Log: {log_path}")
    except OSError:
        log_file = None  # fall back to DEVNULL below
    kwargs: dict[str, object] = {
        "cwd": str(ROOT),
        "stdout": log_file if log_file is not None else subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        # Detached, without a console window, so the launcher can exit
        # while the server keeps running after a double click.
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
            | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
            | subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        )
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)  # type: ignore[arg-type]


def wait_until_up(port: int, process: subprocess.Popen[bytes]) -> bool:
    """Wait for the server to accept connections; False on early exit."""
    deadline = time.monotonic() + START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if probe(port):
            return True
        if process.poll() is not None:
            return False
        time.sleep(PROBE_INTERVAL_SECONDS)
    return probe(port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true",
                        help="start the server without opening a browser")
    parser.add_argument("--check", action="store_true",
                        help="only report whether the server is reachable")
    args = parser.parse_args(argv)

    url = f"http://{HOST}:{args.port}/"
    if probe(args.port):
        print(f"Deckbuild Studio läuft bereits: {url}")
        if args.check:
            return 0
    elif args.check:
        print(f"Deckbuild Studio läuft nicht (Port {args.port}).")
        return 1
    else:
        print("Starte Deckbuild Studio …")
        process = start_server(args.port)
        if not wait_until_up(args.port, process):
            print(
                "FEHLER: Der Server ist nicht erreichbar gestartet. "
                f"Details im Log: {_log_path()}",
                file=sys.stderr,
            )
            return 1
        print(f"Deckbuild Studio läuft: {url}")

    if not args.no_browser:
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
