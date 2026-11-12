"""Name -> URL-slug derivation (CANDIDATES only).

A derived slug is never trusted on its own: EDHREC snapshots are verified
against the commander name/cardId embedded in the fetched page, and
Playgroup commander ids are resolved through Playgroup's own autocomplete
endpoint. The slug rules mirror what both sites use publicly:
lowercase, accents folded, apostrophes dropped, any other run of
non-alphanumerics becomes a single hyphen. For double-faced cards the
front-face name is the canonical page name on both sites — with one
verified exception: split-layout cards are addressed by their FULL
name on both sites (live check 2026-11-12: EDHREC ``rise.json`` is an
empty stub while ``rise-fall.json`` carries the card; Playgroup
answers ``/cards/rise-fall``). ``slugify_full`` covers that case; the
layout-aware choice lives in :mod:`deckbuild_studio.external`.
"""
from __future__ import annotations

import re
import unicodedata


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(c for c in folded if not unicodedata.combining(c))
    ascii_only = ascii_only.replace("'", "").replace("’", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())
    return re.sub(r"-+", "-", slug).strip("-")


def slugify(name: str) -> str:
    return _fold(name.split(" // ")[0].strip())


def slugify_full(name: str) -> str:
    """Slug of the FULL oracle name (both faces): 'Rise // Fall' ->
    'rise-fall'. Used for split-layout cards (see module docstring)."""
    return _fold(name.strip())


def front_name(name: str) -> str:
    return name.split(" // ")[0].strip()
