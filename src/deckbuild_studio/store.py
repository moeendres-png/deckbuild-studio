"""SQLite store — separate layers, provenance on every record.

Layers (Issue #1 §6/§7):
  * Scryfall store:    ``scryfall_card`` (canonical, keyed by oracle_id)
  * Collection store:  ``collection`` / ``location`` / ``card_identity`` /
                       ``physical_lot`` (keyed by physical_lot_id,
                       upsert key (collection_id, oracle_id, location_id))
  * Deck store:        ``deck`` / ``deck_revision`` / ``deck_card``
  * External jobs:     ``sync_job`` (EDHREC / Playgroup, Phase-2 scaffold,
                       status NOT_FETCHED until a real fetch happens)
  * Provenance:        ``source`` (url/name, fetched_at, parser version,
                       sha256, data status) referenced by imported rows.

Adapted from commander-playtest-lab ``studio/store.py`` (schema v7 there);
owner-data coupling replaced by :mod:`deckbuild_studio.config`.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from . import PARSER_VERSION, SCHEMA_VERSION
from .config import database_path

SYNC_STATUSES = ("NOT_FETCHED", "PARTIAL", "BLOCKED", "AVAILABLE", "NOT_FOUND", "STALE")


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_url TEXT,
    file_name TEXT,
    sha256 TEXT,
    parser_version TEXT NOT NULL,
    data_status TEXT NOT NULL DEFAULT 'AVAILABLE',
    note TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scryfall_card (
    oracle_id TEXT PRIMARY KEY,
    scryfall_id TEXT,
    name TEXT NOT NULL,
    front_name TEXT,
    front_type_line TEXT,
    type_line TEXT,
    oracle_text TEXT,
    front_oracle_text TEXT,
    color_identity TEXT NOT NULL DEFAULT '',
    colors TEXT NOT NULL DEFAULT '',
    mana_cost TEXT,
    mana_value REAL,
    layout TEXT,
    image_uri TEXT,
    commander_legality TEXT,
    source_id TEXT REFERENCES source(source_id)
);
CREATE INDEX IF NOT EXISTS scryfall_name ON scryfall_card(name);
CREATE TABLE IF NOT EXISTS collection (
    collection_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_id TEXT REFERENCES source(source_id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS location (
    location_id TEXT NOT NULL,
    collection_id TEXT NOT NULL REFERENCES collection(collection_id),
    location_name TEXT NOT NULL,
    location_type TEXT,
    ownership_semantics TEXT,
    PRIMARY KEY (collection_id, location_id)
);
CREATE TABLE IF NOT EXISTS card_identity (
    card_id TEXT PRIMARY KEY,
    oracle_id TEXT NOT NULL,
    oracle_name TEXT,
    german_name TEXT,
    color_identity TEXT,
    mana_cost TEXT,
    mana_value REAL,
    type_line TEXT,
    oracle_text TEXT,
    is_basic_land INTEGER NOT NULL DEFAULT 0,
    commander_legal INTEGER,
    legality_verified_at TEXT,
    identity_evidence TEXT,
    source_id TEXT REFERENCES source(source_id)
);
CREATE INDEX IF NOT EXISTS identity_oracle ON card_identity(oracle_id);
CREATE TABLE IF NOT EXISTS physical_lot (
    physical_lot_id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL REFERENCES collection(collection_id),
    card_id TEXT,
    oracle_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    quantity INTEGER,
    quantity_exact INTEGER,
    quantity_lower_bound INTEGER,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_assumption TEXT,
    condition TEXT,
    printing_ref TEXT,
    pool_status TEXT,
    note TEXT,
    source_id TEXT REFERENCES source(source_id),
    UNIQUE (collection_id, oracle_id, location_id)
);
CREATE TABLE IF NOT EXISTS inventory_event (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id TEXT NOT NULL,
    sheet TEXT, card_id TEXT, event_type TEXT, detail TEXT,
    source_id TEXT REFERENCES source(source_id)
);
CREATE TABLE IF NOT EXISTS mark (
    oracle_id TEXT NOT NULL,
    collection_id TEXT NOT NULL,
    favorite INTEGER NOT NULL DEFAULT 0,
    excluded INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (oracle_id, collection_id)
);
CREATE TABLE IF NOT EXISTS deck (
    deck_id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    name TEXT NOT NULL,
    commander_oracle_ids TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deck_revision (
    revision_id TEXT PRIMARY KEY,
    deck_id TEXT NOT NULL REFERENCES deck(deck_id),
    parent_revision_id TEXT REFERENCES deck_revision(revision_id),
    deck_hash TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deck_card (
    revision_id TEXT NOT NULL REFERENCES deck_revision(revision_id),
    oracle_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    is_commander INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (revision_id, oracle_id, is_commander)
);
CREATE TABLE IF NOT EXISTS sync_job (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    commander_oracle_id TEXT,
    oracle_id TEXT,
    bracket TEXT,
    bracket_level INTEGER,
    target_url TEXT,
    status TEXT NOT NULL DEFAULT 'NOT_FETCHED',
    detail TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(_SCHEMA)
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- provenance ----------------------------------------------------
    def add_source(self, *, source_id: str, source_name: str, source_url: str | None = None,
                   file_name: str | None = None, sha256: str | None = None,
                   data_status: str = "AVAILABLE", note: str = "") -> str:
        self.conn.execute(
            "INSERT OR REPLACE INTO source(source_id,source_name,source_url,file_name,sha256,"
            "parser_version,data_status,note,imported_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (source_id, source_name, source_url, file_name, sha256, PARSER_VERSION,
             data_status, note, utcnow()),
        )
        return source_id

    # -- read helpers --------------------------------------------------
    def scryfall_by_name(self, name: str) -> list[sqlite3.Row]:
        """Exact paper-name matches: full card name OR full DFC name."""
        return self.conn.execute(
            "SELECT * FROM scryfall_card WHERE name = ?", (name,)
        ).fetchall()

    def scryfall(self, oracle_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM scryfall_card WHERE oracle_id = ?", (oracle_id,)
        ).fetchone()

    def inventory_rows(self, collection_id: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT l.*, COALESCE(s.name, i.oracle_name) AS name,
                   s.front_type_line, s.type_line AS scryfall_type_line,
                   s.color_identity AS scryfall_ci, s.commander_legality,
                   s.oracle_text AS scryfall_text, s.front_oracle_text,
                   s.image_uri, s.layout,
                   COALESCE(m.favorite,0) AS favorite,
                   COALESCE(m.excluded,0) AS excluded, COALESCE(m.note,'') AS mark_note
            FROM physical_lot l
            LEFT JOIN scryfall_card s ON s.oracle_id = l.oracle_id
            LEFT JOIN card_identity i ON i.card_id = l.card_id
            LEFT JOIN mark m ON m.oracle_id = l.oracle_id AND m.collection_id = l.collection_id
            WHERE l.collection_id = ?
            ORDER BY name
            """,
            (collection_id,),
        ).fetchall()

    def available_by_oracle(self, collection_id: str) -> dict[str, int]:
        """Available copies per oracle_id. Availability is derived ONLY from
        physical lots (quantity - reserved); never from row counts or location.
        Missing quantity (NULL) counts as unknown, not as copies."""
        out: dict[str, int] = {}
        for row in self.conn.execute(
            "SELECT oracle_id, quantity, reserved_quantity FROM physical_lot WHERE collection_id = ?",
            (collection_id,),
        ):
            if row["quantity"] is None:
                continue
            out[row["oracle_id"]] = out.get(row["oracle_id"], 0) + max(
                0, row["quantity"] - (row["reserved_quantity"] or 0)
            )
        return out

    def collections(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM collection ORDER BY collection_id").fetchall()

    def status(self) -> dict[str, object]:
        c = self.conn
        one = lambda q, *a: c.execute(q, a).fetchone()[0]  # noqa: E731
        jobs = {
            r["status"]: r["n"]
            for r in c.execute("SELECT status, COUNT(*) n FROM sync_job GROUP BY status")
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "parser_version": PARSER_VERSION,
            "scryfall_cards": one("SELECT COUNT(*) FROM scryfall_card"),
            "collections": [
                {
                    "collection_id": r["collection_id"],
                    "identities": one(
                        "SELECT COUNT(DISTINCT oracle_id) FROM physical_lot WHERE collection_id=?",
                        r["collection_id"]),
                    "lots": one("SELECT COUNT(*) FROM physical_lot WHERE collection_id=?",
                                r["collection_id"]),
                    "copies_reported": one(
                        "SELECT COALESCE(SUM(quantity),0) FROM physical_lot WHERE collection_id=?",
                        r["collection_id"]),
                    "locations": one("SELECT COUNT(*) FROM location WHERE collection_id=?",
                                     r["collection_id"]),
                }
                for r in self.collections()
            ],
            "sources": [dict(r) for r in c.execute(
                "SELECT source_id, source_name, file_name, data_status, imported_at FROM source"
                " ORDER BY imported_at")],
            "sync_jobs_by_status": jobs,
            "external_data": {
                "edhrec": "NOT_FETCHED",
                "playgroup": "NOT_FETCHED",
                "note": "Phase 1: job/status scaffold only; no external data fetched, none invented.",
            },
        }


def dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
