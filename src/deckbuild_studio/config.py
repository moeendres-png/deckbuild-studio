"""Private data-folder resolution.

Replaces the source repo's ``commander_lab.owner_data`` coupling:
the data folder is chosen ONLY via ``MTG_DECKBUILDER_DATA``
(default ``~/.local/share/mtg-collection-deckbuilder``) and never lives
inside the Git tree.
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "MTG_DECKBUILDER_DATA"
DATABASE_NAME = "deckbuild.sqlite3"


def data_dir() -> Path:
    raw = os.environ.get(ENV_VAR)
    root = Path(raw).expanduser() if raw else Path.home() / ".local" / "share" / "mtg-collection-deckbuilder"
    root.mkdir(parents=True, exist_ok=True)
    return root


def database_path() -> Path:
    return data_dir() / DATABASE_NAME
