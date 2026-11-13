"""SQLite store — separate layers, provenance on every record.

Layers (Issue #1 §6/§7):
  * Scryfall store:    ``scryfall_card`` (canonical, keyed by oracle_id)
  * Collection store:  ``collection`` / ``location`` / ``card_identity`` /
                       ``physical_lot`` (keyed by physical_lot_id,
                       upsert key (collection_id, oracle_id, location_id,
                       lot_key, physical_lot_id) — several distinct lots of
                       one card at one location stay separate rows, even
                       when inserted without an explicit lot_key,
                       QA P1.5 + round 2 / PR #5)
  * Deck store:        ``deck`` / ``deck_revision`` / ``deck_card``;
                       every revision carries an explicit ``status``
                       ('legal' | 'draft') from validation at save time
                       (QA P0.2)
  * External jobs:     ``sync_job`` (EDHREC / Playgroup, Phase-2 scaffold,
                       status NOT_FETCHED until a real fetch happens)
  * Provenance:        ``source`` (url/name, fetched_at, parser version,
                       sha256, data status) referenced by imported rows.

Schema migrations are structural and idempotent (see ``_migrate``):
existing databases are upgraded in place, never recreated.

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

# Seconds a connection waits for the SQLite write lock before raising
# "database is locked" (the sqlite3 connect timeout IS the busy
# timeout). Computes such as compute_tiers hold ONE write transaction
# from their first write to the final commit, so the write lock is
# taken for the whole run (tens of seconds scoped, longer for full
# runs) — and every Store() construction writes briefly itself (schema
# check + schema_version upsert), so even pure API reads contend for
# that lock: with the sqlite3 default of 5 s they failed with HTTP 500
# while a compute was running (Issue #31). For this local single-user
# app, waiting is the graceful degradation; 300 s outlasts realistic
# compute runs. WAL is deliberately NOT enabled: journal_mode persists
# in the DB file, and WAL would not remove the wait anyway (requests
# still pass through the writing Store() init, and WAL keeps a single
# writer); a WAL database file copied without its -wal sidecar could
# also silently lose recent commits, which matters for the snapshot
# workflow.
BUSY_TIMEOUT_SECONDS = 300


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
    lot_key TEXT NOT NULL DEFAULT '',
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
    UNIQUE (collection_id, oracle_id, location_id, lot_key, physical_lot_id)
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
    status TEXT NOT NULL DEFAULT 'draft',
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
CREATE TABLE IF NOT EXISTS external_snapshot (
    snapshot_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    kind TEXT NOT NULL,
    commander_oracle_id TEXT,
    oracle_id TEXT,
    bracket TEXT,
    bracket_level INTEGER,
    slug TEXT,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    sha256 TEXT,
    etag TEXT,
    last_modified TEXT,
    fetched_at TEXT NOT NULL,
    sample_size INTEGER,
    captured_count INTEGER,
    displayed_total INTEGER,
    coverage_status TEXT,
    detail TEXT NOT NULL DEFAULT '',
    raw_path TEXT,
    payload_json TEXT
);
CREATE INDEX IF NOT EXISTS ext_snap_key ON external_snapshot(
    source_name, kind, commander_oracle_id, oracle_id, bracket, fetched_at);
CREATE TABLE IF NOT EXISTS edhrec_card_stat (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    category TEXT NOT NULL,
    card_slug TEXT,
    name TEXT NOT NULL,
    scryfall_id TEXT,
    inclusion REAL,
    num_decks INTEGER,
    potential_decks INTEGER,
    synergy REAL,
    lift REAL,
    trend_zscore REAL,
    PRIMARY KEY (snapshot_id, category, name)
);
CREATE TABLE IF NOT EXISTS edhrec_deck_entry (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    urlhash TEXT NOT NULL,
    savedate TEXT,
    price REAL,
    salt REAL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    type_counts_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (snapshot_id, urlhash)
);
CREATE TABLE IF NOT EXISTS app_setting (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decklist_listing (
    platform TEXT NOT NULL,
    commander_oracle_id TEXT,
    commander_name TEXT NOT NULL,
    bracket_level INTEGER NOT NULL,
    name_form TEXT NOT NULL DEFAULT 'full',
    listed_count INTEGER,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (platform, commander_name, bracket_level)
);
CREATE TABLE IF NOT EXISTS decklist_deck (
    deck_uid TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    platform_deck_id TEXT NOT NULL,
    commander_oracle_id TEXT,
    commander_name TEXT,
    bracket_level INTEGER,
    bracket_source TEXT,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    sha256 TEXT,
    raw_path TEXT,
    fetched_at TEXT NOT NULL,
    source_updated_at TEXT,
    deck_size INTEGER,
    card_entries INTEGER,
    mapped_cards INTEGER,
    unmapped_cards INTEGER,
    unmapped_names_json TEXT NOT NULL DEFAULT '[]',
    detail TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS decklist_cohort ON decklist_deck(
    platform, commander_oracle_id, bracket_level, status);
CREATE TABLE IF NOT EXISTS decklist_card (
    deck_uid TEXT NOT NULL REFERENCES decklist_deck(deck_uid),
    entry_key TEXT NOT NULL,
    oracle_id TEXT,
    card_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    is_commander INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (deck_uid, entry_key)
);
CREATE INDEX IF NOT EXISTS decklist_card_oracle ON decklist_card(oracle_id);
CREATE TABLE IF NOT EXISTS edhrec_card_global (
    snapshot_id TEXT PRIMARY KEY REFERENCES external_snapshot(snapshot_id),
    oracle_id TEXT NOT NULL,
    scryfall_id TEXT,
    num_decks INTEGER,
    potential_decks INTEGER,
    inclusion REAL,
    salt REAL
);
CREATE INDEX IF NOT EXISTS edhrec_card_global_oracle ON edhrec_card_global(oracle_id);
CREATE TABLE IF NOT EXISTS spellbook_combo (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    combo_id TEXT NOT NULL,
    card_oracle_ids_json TEXT NOT NULL DEFAULT '[]',
    card_names_json TEXT NOT NULL DEFAULT '[]',
    produces_json TEXT NOT NULL DEFAULT '[]',
    price_eur REAL,
    price_usd REAL,
    popularity INTEGER,
    mana_value_needed REAL,
    PRIMARY KEY (snapshot_id, combo_id)
);
CREATE TABLE IF NOT EXISTS playgroup_commander_staple (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    card_name TEXT NOT NULL,
    card_oracle_id TEXT,
    games INTEGER,
    lift_pp REAL,
    PRIMARY KEY (snapshot_id, card_name)
);
CREATE TABLE IF NOT EXISTS card_ruling (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    ruling_key TEXT NOT NULL,
    oracle_id TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT,
    comment TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, ruling_key)
);
CREATE INDEX IF NOT EXISTS card_ruling_oracle ON card_ruling(oracle_id);
CREATE TABLE IF NOT EXISTS edhtop16_card_stat (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    card_name TEXT NOT NULL,
    card_oracle_id TEXT,
    card_type TEXT,
    mana_cost TEXT,
    play_rate_last_year REAL,
    PRIMARY KEY (snapshot_id, card_name)
);
CREATE INDEX IF NOT EXISTS edhtop16_stat_oracle ON edhtop16_card_stat(card_oracle_id);
CREATE TABLE IF NOT EXISTS topdeck_tournament (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    tid TEXT NOT NULL,
    tournament_name TEXT,
    start_date INTEGER,
    swiss_num INTEGER,
    top_cut INTEGER,
    players INTEGER,
    decks_with_lists INTEGER,
    documents INTEGER,
    PRIMARY KEY (snapshot_id, tid)
);
CREATE TABLE IF NOT EXISTS topdeck_result (
    deck_uid TEXT PRIMARY KEY REFERENCES decklist_deck(deck_uid),
    snapshot_id TEXT NOT NULL,
    tid TEXT NOT NULL,
    player_name TEXT,
    player_id TEXT,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    wins_bracket INTEGER,
    losses_bracket INTEGER,
    top_cut_reached INTEGER,
    deck_source TEXT NOT NULL DEFAULT 'deckobj'
);
CREATE INDEX IF NOT EXISTS topdeck_result_tid ON topdeck_result(tid);
CREATE TABLE IF NOT EXISTS topdeck_card_stat (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    card_name TEXT NOT NULL,
    card_oracle_id TEXT,
    decks_with INTEGER NOT NULL,
    decks_in_cut INTEGER NOT NULL DEFAULT 0,
    top_cut_decks INTEGER NOT NULL DEFAULT 0,
    conversion_rate REAL,
    wins INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    games INTEGER NOT NULL DEFAULT 0,
    win_rate REAL,
    PRIMARY KEY (snapshot_id, card_name)
);
CREATE INDEX IF NOT EXISTS topdeck_stat_oracle ON topdeck_card_stat(card_oracle_id);
CREATE TABLE IF NOT EXISTS edhtop16_commander_card_stat (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    commander_oracle_id TEXT,
    commander_name TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_oracle_id TEXT,
    play_rate REAL,
    entries_n INTEGER,
    window TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, commander_name, card_name)
);
CREATE INDEX IF NOT EXISTS edhtop16_cmd_stat_card ON edhtop16_commander_card_stat(card_oracle_id);
CREATE INDEX IF NOT EXISTS edhtop16_cmd_stat_cmd ON edhtop16_commander_card_stat(commander_oracle_id);
CREATE TABLE IF NOT EXISTS edhtop16_commander_stat (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    commander_oracle_id TEXT,
    commander_name TEXT NOT NULL,
    entries_n INTEGER,
    conversion_rate REAL,
    meta_share REAL,
    window TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, commander_name)
);
CREATE TABLE IF NOT EXISTS mtgjson_print (
    snapshot_id TEXT NOT NULL REFERENCES external_snapshot(snapshot_id),
    mtgjson_uuid TEXT NOT NULL,
    oracle_id TEXT,
    scryfall_id TEXT,
    set_code TEXT,
    collector_number TEXT,
    card_name TEXT,
    language TEXT,
    multiverse_id INTEGER,
    PRIMARY KEY (snapshot_id, mtgjson_uuid)
);
CREATE INDEX IF NOT EXISTS mtgjson_print_oracle ON mtgjson_print(oracle_id);
CREATE TABLE IF NOT EXISTS card_print_fact (
    oracle_id TEXT PRIMARY KEY,
    prints_count INTEGER NOT NULL,
    sets_count INTEGER NOT NULL,
    rarities_json TEXT NOT NULL DEFAULT '[]',
    min_rarity TEXT,
    first_release_year INTEGER,
    last_release_year INTEGER,
    min_eur REAL,
    min_eur_printing TEXT,
    min_usd REAL,
    min_usd_printing TEXT,
    source_id TEXT REFERENCES source(source_id),
    parser_version TEXT NOT NULL,
    derived_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tier_assignment (
    oracle_id TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global',
    commander_oracle_id TEXT NOT NULL DEFAULT '',
    bracket TEXT NOT NULL DEFAULT '',
    universe_id TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL,
    score REAL,
    evidence REAL NOT NULL,
    signals_json TEXT NOT NULL DEFAULT '{}',
    algo_version TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    input_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (oracle_id, scope, commander_oracle_id, bracket,
                 universe_id, algo_version)
);
CREATE INDEX IF NOT EXISTS tier_assignment_scope
    ON tier_assignment(scope, commander_oracle_id, bracket, tier);
"""


_PHYSICAL_LOT_CURRENT = """
CREATE TABLE physical_lot (
    physical_lot_id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL REFERENCES collection(collection_id),
    card_id TEXT,
    oracle_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    lot_key TEXT NOT NULL DEFAULT '',
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
    UNIQUE (collection_id, oracle_id, location_id, lot_key, physical_lot_id)
)
"""

_LOT_COLUMNS = (
    "physical_lot_id,collection_id,card_id,oracle_id,location_id,lot_key,"
    "quantity,quantity_exact,quantity_lower_bound,reserved_quantity,"
    "reserved_assumption,condition,printing_ref,pool_status,note,source_id")


def _unique_index_columns(conn: sqlite3.Connection, table: str) -> list[list[str]]:
    """Column lists of every UNIQUE index on ``table`` (incl. autoindexes
    backing UNIQUE constraints)."""
    out: list[list[str]] = []
    for idx in conn.execute(f"PRAGMA index_list({table})"):
        if idx[2]:  # unique flag
            out.append([r[2] for r in conn.execute(f"PRAGMA index_info({idx[1]})")])
    return out


def _rebuild_physical_lot(conn: sqlite3.Connection, *, keep_lot_key: bool) -> None:
    """Rebuild physical_lot with the current DDL, preserving every row.
    ``keep_lot_key=False`` is the v1 shape (no lot_key column yet): legacy
    rows receive lot_key='' (the aggregated snapshot-lot key)."""
    lot_key_expr = "lot_key" if keep_lot_key else "''"
    select_cols = _LOT_COLUMNS.replace(",lot_key,", f",{lot_key_expr},")
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("ALTER TABLE physical_lot RENAME TO physical_lot_old")
        conn.execute(_PHYSICAL_LOT_CURRENT)
        conn.execute(
            f"INSERT INTO physical_lot({_LOT_COLUMNS}) SELECT {select_cols}"
            " FROM physical_lot_old")
        conn.execute("DROP TABLE physical_lot_old")
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _migrate(conn: sqlite3.Connection) -> None:
    """Structural, idempotent upgrades for databases created by older
    schema versions.

    v1 -> v2:
      * ``deck_revision.status`` (QA P0.2): pre-existing revisions cannot be
        re-validated retroactively with certainty, so they default to
        'draft' — never silently claimed 'legal'.
      * ``physical_lot.lot_key`` (QA P1.5): uniqueness widens from
        (collection_id, oracle_id, location_id) to include lot_key, so
        several distinct lots of one card at one location survive. The
        table is rebuilt; every legacy row keeps its physical_lot_id and
        gets lot_key='' (the aggregated snapshot-lot key).

    v2 -> v3 (QA round 2, PR #5):
      * ``physical_lot`` uniqueness widens once more to include
        physical_lot_id: two distinct normalized lots of one card at one
        location must coexist even when neither carries an explicit
        lot_key (the v2 constraint made the second such insert fail /
        replace the first). Importer upserts are unaffected — they always
        address their lot by its deterministic physical_lot_id, and
        normalized lots keep lot_key = physical_lot_id. Table rebuilt,
        all rows and lot_keys preserved.
    """
    rev_cols = _columns(conn, "deck_revision")
    if rev_cols and "status" not in rev_cols:
        conn.execute(
            "ALTER TABLE deck_revision ADD COLUMN status TEXT NOT NULL DEFAULT 'draft'")
    deck_cols = _columns(conn, "decklist_deck")
    if deck_cols and "source_updated_at" not in deck_cols:
        # tierlist/1.1.0: the deck's source timestamp (Archidekt
        # updatedAt from the listing) — the only honest basis for
        # period filters; legacy rows stay NULL (unknown), never
        # backfilled with fetched_at.
        conn.execute(
            "ALTER TABLE decklist_deck ADD COLUMN source_updated_at TEXT")
    lot_cols = _columns(conn, "physical_lot")
    if lot_cols and "lot_key" not in lot_cols:
        _rebuild_physical_lot(conn, keep_lot_key=False)
        lot_cols = _columns(conn, "physical_lot")
    if lot_cols:
        lot_uniques = _unique_index_columns(conn, "physical_lot")
        widened = ["collection_id", "oracle_id", "location_id", "lot_key",
                   "physical_lot_id"]
        if widened not in lot_uniques:
            _rebuild_physical_lot(conn, keep_lot_key=True)
    conn.commit()


class Store:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=BUSY_TIMEOUT_SECONDS)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(_SCHEMA)
        _migrate(self.conn)
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
                   data_status: str = "AVAILABLE", note: str = "",
                   parser_version: str | None = None) -> str:
        self.conn.execute(
            "INSERT OR REPLACE INTO source(source_id,source_name,source_url,file_name,sha256,"
            "parser_version,data_status,note,imported_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (source_id, source_name, source_url, file_name, sha256,
             parser_version or PARSER_VERSION, data_status, note, utcnow()),
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
            "external_data": self._external_summary(),
            "reference_data": self._reference_summary(),
        }

    def _reference_summary(self) -> dict[str, object]:
        """Reference-data layer (commander-playtest-lab reuse); read-only,
        returns {'imported': False} until `import-reference-data` ran."""
        from .reference import reference_summary
        return reference_summary(self)  # type: ignore[return-value]

    def _external_summary(
            self, collection_id: str = "foundation-schwarze-box"
    ) -> dict[str, object]:
        """Phase-2 snapshot summary: per source, latest snapshot per key.

        Also carries every remaining data layer, each from its own
        coverage function (the same sources the CLI sync/coverage
        paths use), so /api/status and /api/external/status report
        the full layer set from this one assembly point. A layer
        that never synced answers NOT_FETCHED honestly."""
        c = self.conn
        out: dict[str, object] = {}
        for source_name in ("edhrec", "playgroup"):
            rows = c.execute(
                "SELECT * FROM external_snapshot WHERE source_name=? ORDER BY fetched_at",
                (source_name,)).fetchall()
            latest: dict[tuple, dict] = {}
            for r in rows:
                key = (r["kind"], r["commander_oracle_id"], r["oracle_id"], r["bracket"])
                latest[key] = dict(r)
            snaps = []
            for snap in latest.values():
                snap.pop("payload_json", None)
                snaps.append(snap)
            by_status: dict[str, int] = {}
            for snap in snaps:
                by_status[snap["status"]] = by_status.get(snap["status"], 0) + 1
            out[source_name] = {"snapshots": snaps, "by_status": by_status,
                                "total_snapshots_stored": len(rows)}
        atlas = [s for s in out["playgroup"]["snapshots"]  # type: ignore[index,union-attr]
                 if s["kind"] == "playgroup_card"]
        attempted = len(atlas)
        out["card_atlas_coverage"] = {  # type: ignore[assignment]
            "attempted_latest": attempted,
            "available": sum(1 for s in atlas if s["status"] == "AVAILABLE"),
            "partial": sum(1 for s in atlas if s["status"] == "PARTIAL"),
            "not_found": sum(1 for s in atlas if s["status"] == "NOT_FOUND"),
            "blocked": sum(1 for s in atlas if s["status"] == "BLOCKED"),
            "small_sample": sum(1 for s in atlas
                                if s["status"] in ("AVAILABLE", "PARTIAL")
                                and (s["sample_size"] or 0) < 25),
            "note": "Counts are the LATEST snapshot per card; attempted may be "
                    "less than the collection size when a sync ran with --limit.",
        }
        from .categories import category_report
        from .decklists import decklist_status
        from .edhtop16 import (edhtop16_commander_coverage,
                               edhtop16_coverage)
        from .mtgjson import mtgjson_coverage
        from .rulings import rulings_coverage
        from .spellbook import spellbook_coverage
        from .topdeck import topdeck_coverage
        out["rulings"] = rulings_coverage(self, collection_id)
        out["edhtop16"] = edhtop16_coverage(self, collection_id)
        out["edhtop16_commanders"] = edhtop16_commander_coverage(
            self, collection_id)
        out["mtgjson"] = mtgjson_coverage(self, collection_id)
        out["topdeck"] = topdeck_coverage(self, collection_id)
        out["categories"] = category_report(self, collection_id)
        out["spellbook"] = spellbook_coverage(self, collection_id)
        out["decklists"] = decklist_status(self)
        return out


def dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
