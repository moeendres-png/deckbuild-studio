"""Scryfall catalogue import (public data only).

Reads the official bulk ``default-cards`` export in any of its real
shapes: raw JSON array, ``.json``, ``.json.gz``, ``.jsonl`` and
``.jsonl.gz``. The format is detected from the CONTENT (gzip magic bytes
+ first non-whitespace character), never from the file name (QA P0.1):
Scryfall's ``download_uri`` serves an uncompressed JSON array even where
an older local copy may be named ``*.jsonl.gz``. Both payloads are
streamed — JSONL line by line, JSON arrays via an incremental decoder —
so the ~500 MB catalogue is never loaded into memory at once.

One row per ``oracle_id`` is kept in the Scryfall store; printing-level
ids (``scryfall_id``) are only stored for the representative printing
and are never conflated with the oracle identity.

``sync_scryfall`` downloads ONLY this public catalogue (via the official
https://api.scryfall.io/bulk-data index) into the private data folder.
The bulk index offers the same export under ``jsonl_download_uri``
(JSONL, gzipped) and ``download_uri`` (plain JSON array); both fields
are handled. No private collection or deck data is ever sent anywhere.
"""
from __future__ import annotations

import gzip
import json
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from .store import Store, sha256_file

BULK_INDEX_URL = "https://api.scryfall.com/bulk-data"
NONPLAYABLE_LAYOUTS = {"token", "double_faced_token", "art_series", "emblem"}
USER_AGENT = "deckbuild-studio/0.1 (local personal deckbuilder)"
_GZIP_MAGIC = b"\x1f\x8b"
_CHUNK = 1 << 16


def _open_text(path: Path) -> TextIO:
    """Open ``path`` as a text stream, decompressing iff the CONTENT is
    gzip (magic bytes), regardless of the file name."""
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == _GZIP_MAGIC:
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, encoding="utf-8")


def _iter_json_array(first: str, fh: TextIO) -> Iterator[dict]:
    """Stream the objects of a JSON array. ``first`` is the already-read
    text starting at the opening '['; the rest is pulled from ``fh`` in
    chunks and decoded incrementally (never a full in-memory parse)."""
    decoder = json.JSONDecoder()
    buf = first.lstrip()
    if not buf.startswith("["):
        raise ValueError("JSON array expected")
    buf = buf[1:]  # consume '['
    exhausted = False

    def fill() -> None:
        nonlocal buf, exhausted
        chunk = fh.read(_CHUNK)
        if chunk:
            buf += chunk
        else:
            exhausted = True

    while True:
        buf = buf.lstrip()
        if buf.startswith(","):
            buf = buf[1:].lstrip()
        if buf.startswith("]"):
            return
        if not buf:
            if exhausted:
                raise ValueError("truncated JSON array: closing ']' missing")
            fill()
            continue
        while True:
            try:
                obj, idx = decoder.raw_decode(buf)
                break
            except json.JSONDecodeError:
                if exhausted:
                    raise
                fill()
        yield obj
        buf = buf[idx:]


def _iter_json_lines(first: str, fh: TextIO) -> Iterator[dict]:
    """Stream JSONL: one JSON object per line. ``first`` is the
    already-read first chunk (may end mid-line)."""
    pending = first
    while True:
        chunk = fh.read(_CHUNK)
        if not chunk:
            for line in pending.split("\n"):
                line = line.strip()
                if line:
                    yield json.loads(line)
            return
        pending += chunk
        *lines, pending = pending.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                yield json.loads(line)


def _objects(path: Path) -> Iterator[dict]:
    """Yield card objects from a bulk file of any real Scryfall shape,
    detected from content: gzip magic bytes decide decompression, the
    first non-whitespace character decides array vs. JSONL."""
    with _open_text(path) as fh:
        first = ""
        while True:
            stripped = first.lstrip()
            if stripped:
                break
            chunk = fh.read(_CHUNK)
            if not chunk:
                return  # empty file -> no objects
            first += chunk
        if stripped.startswith("["):
            yield from _iter_json_array(stripped, fh)
        elif stripped.startswith("{"):
            yield from _iter_json_lines(first, fh)
        else:
            raise ValueError(
                f"{path.name}: unrecognised bulk content (starts with "
                f"{stripped[:1]!r}); expected a JSON array or JSONL objects")


def _faces(card: dict) -> list[dict]:
    return card.get("card_faces") or [card]


def _image(holder: dict) -> str | None:
    uris = holder.get("image_uris") or {}
    return uris.get("normal") or uris.get("large") or uris.get("small")


def import_scryfall(store: Store, path: str | Path) -> dict[str, int]:
    path = Path(path)
    source_id = f"scryfall:{sha256_file(path)[:16]}"
    seen: dict[str, tuple] = {}
    total = 0
    for card in _objects(path):
        total += 1
        oracle_id = card.get("oracle_id")
        if not oracle_id:
            continue
        if card.get("layout") in NONPLAYABLE_LAYOUTS:
            # Tokens / art series / emblems are non-playable objects (Issue
            # sheet 08_NONPLAYABLE_OBJECTS). Keeping them would make exact
            # paper-name resolution ambiguous (e.g. the token named
            # "Llanowar Elves" vs. the playable card of the same name).
            continue
        faces = _faces(card)
        front = faces[0]
        legalities = card.get("legalities") or {}
        row = (
            oracle_id,
            card.get("id"),
            card.get("name"),
            front.get("name"),
            front.get("type_line"),
            card.get("type_line"),
            card.get("oracle_text") or front.get("oracle_text"),
            front.get("oracle_text"),
            "".join(card.get("color_identity") or []),
            "".join(card.get("colors") or []),
            card.get("mana_cost") or front.get("mana_cost"),
            card.get("cmc"),
            card.get("layout"),
            _image(card) or _image(front),
            legalities.get("commander"),
            source_id,
        )
        # Keep the first printing per oracle_id (oracle-level facts are
        # identical across printings; printing choice is display-only).
        seen.setdefault(oracle_id, row)
    try:
        store.add_source(source_id=source_id, source_name="Scryfall bulk (default-cards)",
                         source_url="https://scryfall.com/docs/api/bulk-data",
                         file_name=path.name, sha256=sha256_file(path))
        store.conn.executemany(
            "INSERT OR REPLACE INTO scryfall_card(oracle_id,scryfall_id,name,front_name,"
            "front_type_line,type_line,oracle_text,front_oracle_text,color_identity,colors,"
            "mana_cost,mana_value,layout,image_uri,commander_legality,source_id)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            list(seen.values()),
        )
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    return {"printings_read": total, "oracle_identities": len(seen)}


def _target_name(uri: str) -> str:
    """Local file name carrying the suffix of the REAL download format,
    so later readers can see what was fetched (parsing itself is
    content-based and does not rely on this name)."""
    for suffix, name in ((".jsonl.gz", "default-cards.jsonl.gz"),
                         (".json.gz", "default-cards.json.gz"),
                         (".jsonl", "default-cards.jsonl"),
                         (".json", "default-cards.json")):
        if uri.split("?")[0].endswith(suffix):
            return name
    return "default-cards.download"


def sync_scryfall(store: Store, *, target_dir: Path) -> dict[str, object]:
    """Download the public default-cards bulk file, then import it.

    The bulk index entry carries the export twice: ``jsonl_download_uri``
    (JSONL, gzipped — preferred, streams line-by-line) and the legacy
    ``download_uri`` (a plain, uncompressed JSON array). Both are
    handled; the file is stored under a name matching its real format.
    """
    req = urllib.request.Request(BULK_INDEX_URL, headers={"User-Agent": USER_AGENT,
                                                           "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed official URL)
        index = json.load(resp)
    entry = next(e for e in index["data"] if e["type"] == "default_cards")
    uri = entry.get("jsonl_download_uri") or entry.get("download_uri")
    if not uri:
        raise ValueError("bulk-data index entry for default_cards carries "
                         "neither jsonl_download_uri nor download_uri")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / _target_name(uri)
    req = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(target, "wb") as fh:  # noqa: S310
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    result = import_scryfall(store, target)
    return {"downloaded_to": str(target), "download_uri_used": uri,
            "bulk_updated_at": entry.get("updated_at"), **result}
