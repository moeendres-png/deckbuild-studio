"""Name -> URL-slug derivation (CANDIDATES only).

A derived slug is never trusted on its own: EDHREC snapshots are verified
against the commander name/cardId embedded in the fetched page, and
Playgroup commander ids are resolved through Playgroup's own autocomplete
endpoint. The slug rules mirror what both sites use publicly:
lowercase, accents folded, apostrophes dropped, any other run of
non-alphanumerics becomes a single hyphen. For double-faced cards the
front-face name is the canonical page name on both sites.
"""
from __future__ import annotations

import re
import unicodedata


def slugify(name: str) -> str:
    front = name.split(" // ")[0].strip()
    folded = unicodedata.normalize("NFKD", front)
    ascii_only = "".join(c for c in folded if not unicodedata.combining(c))
    ascii_only = ascii_only.replace("'", "").replace("’", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())
    return re.sub(r"-+", "-", slug).strip("-")


def front_name(name: str) -> str:
    return name.split(" // ")[0].strip()
