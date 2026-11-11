"""Scryfall catalogue import (public data only).

Reads the official bulk ``default-cards`` export either as ``.jsonl(.gz)``
(one JSON object per line) or as a plain JSON array. One row per
``oracle_id`` is kept in the Scryfall store; printing-level ids
(``scryfall_id``) are only stored for the representative printing and are
never conflated with the oracle identity.

``sync_scryfall`` downloads ONLY this public catalogue (via the official
https://api.scryfall.io/bulk-data index) into the private data folder.
No private collection or deck data is ever sent anywhere.
"""
from __future__ import annotations

import gzip
import json
import urllib.request
from collections.abc import Iterator
from pathlib import Path

from .store import Store, sha256_file

BULK_INDEX_URL = "https://api.scryfall.com/bulk-data"
NONPLAYABLE_LAYOUTS = {"token", "double_faced_token", "art_series", "emblem"}
USER_AGENT = "deckbuild-studio/0.1 (local personal deckbuilder)"


def _objects(path: Path) -> Iterator[dict]:
    opener = gzip.open if path.suffix == ".gz" or path.name.endswith(".jsonl.gz") else open
    if path.name.endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        yield from data
        return
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[operator]
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


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


def sync_scryfall(store: Store, *, target_dir: Path) -> dict[str, object]:
    """Download the public default-cards bulk file, then import it."""
    req = urllib.request.Request(BULK_INDEX_URL, headers={"User-Agent": USER_AGENT,
                                                           "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed official URL)
        index = json.load(resp)
    entry = next(e for e in index["data"] if e["type"] == "default_cards")
    uri = entry.get("jsonl_download_uri") or entry["download_uri"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "default-cards.jsonl.gz"
    req = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(target, "wb") as fh:  # noqa: S310
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    result = import_scryfall(store, target)
    return {"downloaded_to": str(target), "bulk_updated_at": entry.get("updated_at"), **result}
