"""Import/export of the owner's own card marks (favorite / excluded / note).

Adopted 2026-11-11 from commander-playtest-lab PR #1195 (``marks.py``),
adapted to this project's identity model. Marks are filters and
availability conditions for the owner's own use — never a strength
signal: no evidence, rating or recommendation in this project reads
them. A marks file is private data and never belongs in a repository.

Semantics (mirroring upstream, adapted):

* The import MERGES. A key an entry does not mention stays as it is.
* The whole file is validated before anything is written
  (all-or-nothing); the report holds counts only, never note text.
* Entries that cannot be resolved are counted and skipped, never
  guessed. Resolution order: ``oracle_id`` (Scryfall store) ->
  ``card_id`` (local ``card_identity`` of an imported collection) ->
  ``card_name`` (exact Scryfall name, only when unambiguous).
* Formats read: ``deckbuild-marks-1`` (this project's export) and
  ``studio-marks-1`` (upstream export): ``{"format": ..., "marks":
  [{"oracle_id"?, "card_id"?, "card_name"?, "favorite"?, "excluded"?,
  "note"?}]}``. (The old HTML studio export format was dropped
  2026-11-13 by owner decision; its files are no longer read.)
"""
from __future__ import annotations

import json
from pathlib import Path

from .store import Store

EXPORT_FORMAT = "deckbuild-marks-1"
_ACCEPTED_FORMATS = {EXPORT_FORMAT, "studio-marks-1"}


def _flag(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError(f"{field} must be true or false, not {value!r}")


def _entries(data: object) -> tuple[list[dict], dict[str, int]]:
    """Normalise a marks file to entries + ignored-field counts."""
    if not isinstance(data, dict):
        raise ValueError("a marks file is a JSON object")
    if data.get("format") in _ACCEPTED_FORMATS:
        marks = data.get("marks")
        if not isinstance(marks, list):
            raise ValueError("'marks' must be a list")
        entries: list[dict] = []
        for item in marks:
            if not isinstance(item, dict):
                raise ValueError("every mark is an object")
            entries.append(item)
        return entries, {}
    raise ValueError(
        f"not a marks file: expected format {EXPORT_FORMAT!r}/'studio-marks-1'")


def _resolve_collection(store: Store, collection_id: str | None) -> str:
    rows = store.collections()
    ids = [str(r["collection_id"]) for r in rows]
    if collection_id is not None:
        if collection_id not in ids:
            raise ValueError(f"unknown collection: {collection_id!r} (have {ids})")
        return collection_id
    if len(ids) == 1:
        return ids[0]
    raise ValueError(f"collection_id required (have {ids})")


def _resolve_oracle(store: Store, entry: dict) -> str | None:
    oracle_id = str(entry.get("oracle_id") or "").strip()
    if oracle_id:
        return oracle_id if store.scryfall(oracle_id) is not None else None
    card_id = str(entry.get("card_id") or "").strip()
    if card_id:
        row = store.conn.execute(
            "SELECT oracle_id FROM card_identity WHERE card_id = ?",
            (card_id,)).fetchone()
        if row is not None:
            return str(row["oracle_id"])
    name = str(entry.get("card_name") or "").strip()
    if name:
        rows = store.scryfall_by_name(name)
        if len(rows) == 1:
            return str(rows[0]["oracle_id"])
    return None


def import_owner_marks(store: Store, path: str | Path, *,
                       collection_id: str | None = None) -> dict:
    """Merge marks from ``path`` into one collection. All or nothing;
    the report holds counts only."""
    collection_id = _resolve_collection(store, collection_id)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries, ignored = _entries(data)
    plan: list[tuple[str, dict]] = []
    unresolved = 0
    for entry in entries:
        keys: dict[str, object] = {}
        if "favorite" in entry:
            keys["favorite"] = _flag(entry["favorite"], "favorite")
        if "excluded" in entry:
            keys["excluded"] = _flag(entry["excluded"], "excluded")
        if "note" in entry:
            if not isinstance(entry["note"], str):
                raise ValueError("note must be text")
            keys["note"] = entry["note"]
        if not keys:
            continue
        oracle_id = _resolve_oracle(store, entry)
        if oracle_id is None:
            unresolved += 1
            continue
        plan.append((oracle_id, keys))
    changed = 0
    with store.conn:
        for oracle_id, keys in plan:
            row = store.conn.execute(
                "SELECT favorite, excluded, note FROM mark "
                "WHERE oracle_id = ? AND collection_id = ?",
                (oracle_id, collection_id)).fetchone()
            before = (0, 0, "") if row is None else (
                row["favorite"], row["excluded"], row["note"])
            after = (int(bool(keys.get("favorite", before[0]))),
                     int(bool(keys.get("excluded", before[1]))),
                     str(keys.get("note", before[2])))
            if row is not None and after == before:
                continue
            store.conn.execute(
                "INSERT OR REPLACE INTO mark(oracle_id, collection_id, "
                "favorite, excluded, note) VALUES (?, ?, ?, ?, ?)",
                (oracle_id, collection_id, *after))
            changed += 1
    favorites = store.conn.execute(
        "SELECT COUNT(*) FROM mark WHERE collection_id = ? AND favorite = 1",
        (collection_id,)).fetchone()[0]
    return {"collection_id": collection_id, "entries": len(entries),
            "resolved": len(plan), "unresolved": unresolved,
            "changed": changed, "favorites_after": int(favorites),
            "ignored_fields": ignored}


def export_owner_marks(store: Store, path: str | Path, *,
                       collection_id: str | None = None) -> dict:
    """Write this project's marks format (private file, owner's data)."""
    collection_id = _resolve_collection(store, collection_id)
    rows = store.conn.execute(
        "SELECT m.oracle_id, m.favorite, m.excluded, m.note, s.name AS card_name "
        "FROM mark m LEFT JOIN scryfall_card s ON s.oracle_id = m.oracle_id "
        "WHERE m.collection_id = ? ORDER BY s.name, m.oracle_id",
        (collection_id,)).fetchall()
    payload = {
        "format": EXPORT_FORMAT,
        "collection_id": collection_id,
        "marks": [{"oracle_id": r["oracle_id"], "card_name": r["card_name"],
                   "favorite": bool(r["favorite"]),
                   "excluded": bool(r["excluded"]), "note": r["note"]}
                  for r in rows],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return {"collection_id": collection_id, "marks": len(rows),
            "path": str(path)}
