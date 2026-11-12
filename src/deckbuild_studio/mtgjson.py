"""MTGJSON layer — card data only: printing mapping + foreign names.

MTGJSON (https://mtgjson.com/downloads/all-files/) publishes free bulk
files; the one file this layer consumes is ``AllPrintings`` (the .xz
twin, 100,578,120 B on 2026-11-12; the .gz is 185,593,989 B). The raw
file is NEVER persisted in the repo or the snapshot store: it is
downloaded (explicitly, ``--download``) into the private data folder
and STREAM-filtered; only the collection's slice is stored.

What this layer adds beyond the Scryfall store (field-verified
against the real file, build 5.3.0+20261111):

  * per-printing mapping: MTGJSON ``identifiers`` (``scryfallOracleId``
    / ``scryfallId``) join every printing (its own MTGJSON uuid, set,
    collector number, language, multiverse id) to the collection's
    oracle identities;
  * foreign-language printings (``AllPrintings`` -> ``foreignData``):
    printed name + language + multiverse id per language printing,
    keyed by that printing's own MTGJSON uuid.

Scope note: this layer originally also imported MTGJSON marketplace
prices (AllPricesToday) and a 90-day price history (AllPrices). Both
were REMOVED on 2026-11-12 by explicit owner decision ("nur die
Karten" — no price history, no store/buy features) before the layer
ever shipped to main or the real DB. Prices in this tool come from
Scryfall's print facts (``card_print_fact``) only. No purchase URLs
were ever stored or displayed by this layer.

Prints whose identifiers carry no scryfallOracleId are counted as
mapping gaps, never guessed. Snapshots record the file SHA-256
(computed while streaming), the MTGJSON build (meta date/version) and
the source file name — a re-run with an unchanged file hash skips the
parse (idempotent).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import lzma
import urllib.request
from pathlib import Path
from typing import BinaryIO, Iterator, TextIO

from .external import latest_snapshot, save_snapshot
from .httpfetch import USER_AGENT
from .store import Store

PARSER_ID = "mtgjson-slice/2.0.0"
SOURCE_NAME = "mtgjson"
BASE_URL = "https://mtgjson.com/api/v5"
FILES = {"printings": "AllPrintings.json.xz"}
_KINDS = {"printings": "mtgjson_printings"}
_CHUNK = 1 << 16
_GZIP_MAGIC = b"\x1f\x8b"
_XZ_MAGIC = b"\xfd7zXZ\x00"


class MtgjsonError(Exception):
    """A bulk file is missing or structurally unreadable."""


# --------------------------------------------------------------------------
# Streaming JSON machinery (the bulk file is a 100+ MB single document)
# --------------------------------------------------------------------------

class _HashingReader(io.RawIOBase):
    """Binary stream wrapper that SHA-256s everything read through it
    (the decompressors above it pull the raw bytes exactly once)."""

    def __init__(self, raw: BinaryIO):
        self._raw = raw
        self.hash = hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        data = self._raw.read(size)
        if data:
            self.hash.update(data)
        return data

    def readinto(self, b) -> int:
        data = self._raw.read(len(b))
        if data:
            self.hash.update(data)
            b[:len(data)] = data
        return len(data)

    def readable(self) -> bool:
        return True

    def close(self) -> None:
        try:
            self._raw.close()
        finally:
            super().close()


def open_bulk_text(path: Path) -> tuple[TextIO, _HashingReader]:
    """Open a bulk file as a text stream, decompressing by CONTENT
    magic (gzip / xz / plain). Returns the stream and the hashing
    reader; ``reader.hash.hexdigest()`` is final only after the
    stream is exhausted."""
    raw = open(path, "rb")
    magic = raw.read(6)
    raw.seek(0)
    reader = _HashingReader(raw)
    buffered = io.BufferedReader(reader)
    if magic[:2] == _GZIP_MAGIC:
        stream: TextIO = gzip.open(buffered, "rt", encoding="utf-8")
    elif magic[:6] == _XZ_MAGIC:
        stream = lzma.open(buffered, "rt", encoding="utf-8")
    else:
        stream = io.TextIOWrapper(buffered, encoding="utf-8")
    return stream, reader


class JsonCursor:
    """Minimal streaming reader over one JSON text stream: decode the
    values you want with ``json`` incremental decoding, structurally
    skip the rest (string/depth aware, unbounded size)."""

    def __init__(self, stream: TextIO):
        self._fh = stream
        self._buf = ""
        self._eof = False
        self._decoder = json.JSONDecoder()

    def _fill(self) -> bool:
        if self._eof:
            return False
        chunk = self._fh.read(_CHUNK)
        if chunk:
            self._buf += chunk
            return True
        self._eof = True
        return False

    def _need(self, n: int = 1) -> None:
        while len(self._buf) < n and self._fill():
            pass

    def _skip_ws(self) -> None:
        while True:
            self._buf = self._buf.lstrip(" \t\r\n")
            if self._buf or self._eof:
                return
            self._fill()

    def peek(self) -> str:
        self._skip_ws()
        self._need(1)
        return self._buf[:1]

    def expect(self, char: str) -> None:
        self._skip_ws()
        self._need(1)
        if not self._buf.startswith(char):
            raise MtgjsonError(f"expected {char!r} at stream position, "
                               f"found {self._buf[:20]!r}")
        self._buf = self._buf[1:]

    def read_string(self) -> str:
        self._skip_ws()
        while True:
            try:
                value, idx = self._decoder.raw_decode(self._buf)
                break
            except json.JSONDecodeError:
                if self._eof or not self._fill():
                    raise
        if not isinstance(value, str):
            raise MtgjsonError("expected a JSON string key")
        self._buf = self._buf[idx:]
        return value

    def decode_value(self):
        """Decode the next complete JSON value (bounded size: card
        objects, meta blocks)."""
        self._skip_ws()
        while True:
            try:
                value, idx = self._decoder.raw_decode(self._buf)
                break
            except json.JSONDecodeError:
                if self._eof or not self._fill():
                    raise
        self._buf = self._buf[idx:]
        return value

    def skip_value(self) -> None:
        """Structurally skip the next JSON value of ANY size."""
        self._skip_ws()
        self._need(1)
        first = self._buf[:1]
        if first in "{[":
            depth = 0
            in_str = False
            escaped = False
            i = 0
            while True:
                while i >= len(self._buf):
                    if not self._fill():
                        raise MtgjsonError("truncated JSON while skipping")
                c = self._buf[i]
                i += 1
                if in_str:
                    if escaped:
                        escaped = False
                    elif c == "\\":
                        escaped = True
                    elif c == '"':
                        in_str = False
                    continue
                if c == '"':
                    in_str = True
                elif c in "{[":
                    depth += 1
                elif c in "}]":
                    depth -= 1
                    if depth == 0:
                        self._buf = self._buf[i:]
                        return
        elif first == '"':
            self.read_string()
        else:  # number / true / false / null: read to a delimiter
            j = 0
            while True:
                while j >= len(self._buf):
                    if not self._fill():
                        break
                if j >= len(self._buf):
                    break
                if self._buf[j] in ",}] \t\r\n":
                    break
                j += 1
            self._buf = self._buf[j:]


def _object_entries(cursor: JsonCursor) -> Iterator[tuple[str, JsonCursor]]:
    """Yield (key, cursor) for each member of the object at the cursor;
    the caller decodes or skips each value before advancing."""
    cursor.expect("{")
    if cursor.peek() == "}":
        cursor.expect("}")
        return
    while True:
        key = cursor.read_string()
        cursor.expect(":")
        yield key, cursor
        if cursor.peek() == ",":
            cursor.expect(",")
            continue
        cursor.expect("}")
        return


def read_meta(path: Path) -> dict:
    """The ``meta`` block (date/version) of an MTGJSON file.

    MTGJSON writes ``meta`` as the first top-level key (verified on
    the real file); we stop at the first other key instead of
    structurally skipping the (huge) ``data`` block. If a future file
    reorders its keys, this returns {} — the meta values are payload
    provenance only, and empty is honest."""
    stream, _reader = open_bulk_text(path)
    with stream:
        cursor = JsonCursor(stream)
        for key, cur in _object_entries(cursor):
            if key == "meta":
                return cur.decode_value()
            return {}
        return {}


def iter_printings_cards(path: Path) -> Iterator[dict]:
    """Yield every card object of AllPrintings (data -> set -> cards),
    streamed; set-level siblings (tokens, booster data, …) are skipped
    structurally."""
    stream, _reader = open_bulk_text(path)
    with stream:
        cursor = JsonCursor(stream)
        for key, cur in _object_entries(cursor):
            if key != "data":
                cur.skip_value()
                continue
            for _set_code, set_cur in _object_entries(cur):
                for set_key, val_cur in _object_entries(set_cur):
                    if set_key != "cards":
                        val_cur.skip_value()
                        continue
                    val_cur.expect("[")
                    if val_cur.peek() == "]":
                        val_cur.expect("]")
                        continue
                    while True:
                        yield val_cur.decode_value()
                        if val_cur.peek() == ",":
                            val_cur.expect(",")
                            continue
                        val_cur.expect("]")
                        break


# --------------------------------------------------------------------------
# Download (explicit; sizes measured, never a background crawler)
# --------------------------------------------------------------------------

def download_mtgjson(target_dir: Path) -> dict:
    """Download the AllPrintings bulk file into ``target_dir``
    (streamed to disk). Returns the byte size of the file (a fresh
    HEAD value is in the module docstring; here: what actually
    landed)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}
    for key, name in FILES.items():
        url = f"{BASE_URL}/{name}"
        target = target_dir / name
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=600) as resp, \
                open(target, "wb") as fh:  # noqa: S310 (fixed official URL)
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
        out[key] = {"file": name, "bytes": target.stat().st_size,
                    "url": url}
    return out


# --------------------------------------------------------------------------
# Sync
# --------------------------------------------------------------------------

def _collection_oracles(store: Store, collection_id: str) -> set[str]:
    return {r["oracle_id"] for r in store.conn.execute(
        "SELECT DISTINCT oracle_id FROM physical_lot WHERE collection_id=?",
        (collection_id,))}


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_unchanged(store: Store, kind: str, sha: str) -> dict | None:
    snap = latest_snapshot(store, SOURCE_NAME, kind)
    if snap is None or snap["status"] != "AVAILABLE":
        return None
    try:
        payload = json.loads(snap["payload_json"] or "{}")
    except json.JSONDecodeError:
        return None
    if payload.get("file_sha256") == sha:
        return {"snapshot_id": snap["snapshot_id"], "status": "AVAILABLE",
                "cached": True, "kind": kind,
                "detail": "file hash unchanged since the stored snapshot; "
                          "parse skipped"}
    return None


def _save_file_snapshot(store: Store, *, kind: str, path: Path, sha: str,
                        meta: dict, status: str, detail: str,
                        captured: int, extra_payload: dict) -> str:
    return save_snapshot(
        store, source_name=SOURCE_NAME, kind=kind,
        url=f"{BASE_URL}/{path.name}", status=status,
        coverage_status="TOTAL_KNOWN" if status == "AVAILABLE" else "PARTIAL",
        detail=detail, captured_count=captured,
        payload={"parser": PARSER_ID, "file": path.name,
                 "file_sha256": sha,
                 "mtgjson_version": meta.get("version"),
                 "mtgjson_date": meta.get("date"), **extra_payload})


def _sync_printings(store: Store, path: Path, oracles: set[str]) -> dict:
    sha = _file_sha256(path)
    kind = _KINDS["printings"]
    cached = _snapshot_unchanged(store, kind, sha)
    if cached:
        return cached
    meta = read_meta(path)
    rows: list[tuple] = []
    stats = {"cards_seen": 0, "cards_kept": 0, "foreign_rows": 0,
             "without_oracle_id": 0, "kept_oracles": set()}
    for card in iter_printings_cards(path):
        stats["cards_seen"] += 1
        identifiers = card.get("identifiers") or {}
        oracle_id = identifiers.get("scryfallOracleId")
        if not oracle_id:
            stats["without_oracle_id"] += 1
            continue
        if oracle_id not in oracles:
            continue
        stats["cards_kept"] += 1
        stats["kept_oracles"].add(oracle_id)
        uuid = card.get("uuid")
        if not uuid:
            continue
        rows.append((uuid, oracle_id, identifiers.get("scryfallId"),
                     card.get("setCode"), card.get("number"),
                     card.get("name"), card.get("language"),
                     card.get("multiverseId")))
        for foreign in card.get("foreignData") or []:
            fuuid = foreign.get("uuid")
            if not fuuid:
                continue
            stats["foreign_rows"] += 1
            rows.append((fuuid, oracle_id,
                         (foreign.get("identifiers") or {}).get("scryfallId"),
                         card.get("setCode"), card.get("number"),
                         foreign.get("name"), foreign.get("language"),
                         foreign.get("multiverseId")))
    detail = (f"{stats['cards_kept']} printings of "
              f"{len(stats['kept_oracles'])} collection identities kept "
              f"(+ {stats['foreign_rows']} foreign-language rows) of "
              f"{stats['cards_seen']} cards streamed; "
              f"{stats['without_oracle_id']} cards carry no "
              "scryfallOracleId (mapping gap, counted, not guessed)")
    snap = _save_file_snapshot(
        store, kind=kind, path=path, sha=sha, meta=meta, status="AVAILABLE",
        detail=detail, captured=len(rows),
        extra_payload={"cards_seen": stats["cards_seen"],
                       "cards_kept": stats["cards_kept"],
                       "foreign_rows": stats["foreign_rows"],
                       "without_oracle_id": stats["without_oracle_id"],
                       "kept_oracles": len(stats["kept_oracles"])})
    store.conn.execute("DELETE FROM mtgjson_print WHERE snapshot_id=?", (snap,))
    store.conn.executemany(
        "INSERT OR IGNORE INTO mtgjson_print(snapshot_id,mtgjson_uuid,"
        "oracle_id,scryfall_id,set_code,collector_number,card_name,language,"
        "multiverse_id) VALUES(?,?,?,?,?,?,?,?,?)",
        [(snap, *r) for r in rows])
    store.conn.commit()
    return {"snapshot_id": snap, "status": "AVAILABLE", "kind": kind,
            "detail": detail,
            "cards_seen": stats["cards_seen"],
            "cards_kept": stats["cards_kept"],
            "foreign_rows": stats["foreign_rows"],
            "without_oracle_id": stats["without_oracle_id"],
            "kept_oracles": len(stats["kept_oracles"])}


def sync_mtgjson(store: Store, raw_dir: Path, *,
                 collection_id: str = "foundation-schwarze-box",
                 download: bool = False) -> dict:
    """Stream-filter the MTGJSON AllPrintings file down to the
    collection (printing mapping + foreign-language print names).

    A missing file is reported as NOT_FETCHED (no invented data).
    Card data only — this layer imports no prices and no purchase
    information (see the module docstring's scope note)."""
    raw_dir = Path(raw_dir)
    result: dict = {"collection_id": collection_id, "raw_dir": str(raw_dir)}
    if download:
        result["downloaded"] = download_mtgjson(raw_dir)
    path = raw_dir / FILES["printings"]
    if not path.exists():
        result["status"] = "NOT_FETCHED"
        result["detail"] = ("AllPrintings file missing — run with "
                             "--download or place the file in the raw "
                             "directory; nothing imported")
        result["missing"] = {"printings": str(path)}
        return result
    oracles = _collection_oracles(store, collection_id)
    result["collection_identities"] = len(oracles)
    result["printings"] = _sync_printings(store, path, oracles)
    result["coverage"] = mtgjson_coverage(store, collection_id)
    result["status"] = "AVAILABLE"
    return result


def card_mtgjson_prints(store: Store, oracle_id: str) -> dict:
    """One card's stored MTGJSON printings of the latest snapshot:
    every printing (set, collector number, language, printed name)
    plus the distinct foreign-language names. Printings are
    collector/language data — display only, never a tier input."""
    snap = latest_snapshot(store, SOURCE_NAME, _KINDS["printings"])
    if snap is None:
        return {"status": "NOT_FETCHED", "prints": [], "foreign_names": []}
    prints = [dict(r) for r in store.conn.execute(
        "SELECT set_code, collector_number, language, card_name, "
        "mtgjson_uuid FROM mtgjson_print WHERE snapshot_id=? "
        "AND oracle_id=? ORDER BY language, set_code, collector_number",
        (snap["snapshot_id"], oracle_id))]
    foreign: dict[str, str] = {}
    for p in prints:
        if p["language"] and p["language"] != "English":
            foreign.setdefault(p["language"], p["card_name"])
    return {"status": snap["status"], "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"], "prints": prints,
            "prints_total": len(prints),
            "foreign_names": [{"language": lang, "name": name}
                              for lang, name in sorted(foreign.items())]}


def mtgjson_coverage(store: Store, collection_id: str) -> dict:
    total = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    out: dict = {"collection_id": collection_id, "total_identities": total}
    snap = latest_snapshot(store, SOURCE_NAME, _KINDS["printings"])
    if snap is None:
        out["printings"] = {"status": "NOT_FETCHED"}
    else:
        row = store.conn.execute(
            "SELECT COUNT(DISTINCT oracle_id) oracles, COUNT(*) prints, "
            "SUM(CASE WHEN language IS NOT NULL AND language <> 'English' "
            "THEN 1 ELSE 0 END) foreign_rows FROM mtgjson_print "
            "WHERE snapshot_id=?", (snap["snapshot_id"],)).fetchone()
        out["printings"] = {"status": snap["status"],
                            "snapshot_id": snap["snapshot_id"],
                            "fetched_at": snap["fetched_at"],
                            "collection_oracles_covered": row["oracles"],
                            "print_rows": row["prints"],
                            "foreign_rows": row["foreign_rows"]}
    return out
