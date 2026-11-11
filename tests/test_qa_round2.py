"""Native regression tests for QA round 2 — the four contract gaps found
by the independent acceptance suite (PR #5, qa/independent-acceptance):

1. a deck commander must be physically owned in the deck's collection,
2. distinct physical lots of one card at one location coexist even
   without an explicit lot_key (schema v3) — incl. the v2 -> v3 migration,
3. create_deck never attaches a revision across collections and never
   silently ignores an unknown parent revision,
4. an EDHREC inclusion fraction that contradicts its own raw counts is
   dropped (fail-closed), never stored as an unflagged fact.

Synthetic fixtures only, mirroring tests/conftest.py conventions.
"""
from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio.decks import create_deck, validate_deck
from deckbuild_studio.edhrec import parse_stats_page
from deckbuild_studio.importers import (
    FOUNDATION_COLLECTION as FC,
    _upsert_lot,
    import_foundation_workbook,
    import_mapped_file,
)
from deckbuild_studio.store import Store

CMD = OID["commander_a"]  # "Alara, Test Sovereign"
PLAINS = OID["plains"]


def _foundation(store, tmp_path, rows, name="f.xlsx"):
    path = write_foundation_xlsx(tmp_path / name, rows)
    import_foundation_workbook(store, path)
    return store


# --- 1) commander ownership -------------------------------------------------

def test_commander_owned_validates_legal(loaded_store, tmp_path):
    _foundation(loaded_store, tmp_path,
                [("Alara, Test Sovereign", 1, "Foundation"),
                 ("Plains", 120, "Foundation")])
    verdict = validate_deck(loaded_store, FC, [CMD], {PLAINS: 99})
    assert verdict["valid"], verdict["errors"]


def test_commander_not_owned_rejected(loaded_store, tmp_path):
    _foundation(loaded_store, tmp_path, [("Plains", 120, "Foundation")])
    verdict = validate_deck(loaded_store, FC, [CMD], {PLAINS: 99})
    assert not verdict["valid"]
    assert any("not owned" in e and "available" in e for e in verdict["errors"])


def test_commander_fully_reserved_rejected(loaded_store, tmp_path):
    """Owned but every copy reserved -> zero available -> not a legal
    commander for this collection."""
    path = tmp_path / "res.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Name", "Menge", "Box", "Reserviert"])
        writer.writerows([("Alara, Test Sovereign", 1, "A", 1),
                          ("Plains", 120, "A", 0)])
    import_mapped_file(loaded_store, path, {
        "collection_id": "r2-reserved",
        "columns": {"name": "Name", "quantity": "Menge", "location": "Box",
                    "reserved": "Reserviert", "condition": None}})
    verdict = validate_deck(loaded_store, "r2-reserved", [CMD], {PLAINS: 99})
    assert not verdict["valid"]
    assert any("not owned" in e for e in verdict["errors"])


# --- 2) distinct lots without lot_key + v2 -> v3 migration ------------------

def test_two_lots_without_lot_key_coexist(loaded_store):
    """Direct upserts with distinct physical_lot_ids and the default
    lot_key='' must keep BOTH rows (schema v2 replaced the first)."""
    loaded_store.add_source(source_id="test", source_name="test")
    loaded_store.conn.execute(
        "INSERT OR IGNORE INTO collection(collection_id,title,created_at)"
        " VALUES('r2-lots','t','2026-11-11T00:00:00Z')")
    for lot_id, qty in (("lot-r2-a", 3), ("lot-r2-b", 2)):
        _upsert_lot(loaded_store, collection_id="r2-lots", card_id=None,
                    oracle_id=PLAINS, location_id="Box A", quantity=qty,
                    quantity_exact=1, quantity_lower_bound=qty,
                    source_id="test", physical_lot_id=lot_id)
    loaded_store.conn.commit()
    rows = loaded_store.conn.execute(
        "SELECT physical_lot_id, quantity FROM physical_lot"
        " WHERE collection_id='r2-lots' ORDER BY physical_lot_id").fetchall()
    assert [(r["physical_lot_id"], r["quantity"]) for r in rows] == [
        ("lot-r2-a", 3), ("lot-r2-b", 2)]


_V2_PHYSICAL_LOT = """
CREATE TABLE physical_lot (
    physical_lot_id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
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
    source_id TEXT,
    UNIQUE (collection_id, oracle_id, location_id, lot_key)
)
"""


def test_schema_migration_v2_to_v3_preserves_lots(tmp_path):
    path = tmp_path / "v2.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(_V2_PHYSICAL_LOT)
    conn.execute(
        "INSERT INTO physical_lot(physical_lot_id,collection_id,oracle_id,"
        "location_id,lot_key,quantity) VALUES('legacy-1','mig','oid-x','Box A','',4)")
    conn.commit()
    conn.close()

    store = Store(path)
    try:
        assert store.status()["schema_version"] == 3
        rows = store.conn.execute(
            "SELECT physical_lot_id, quantity FROM physical_lot").fetchall()
        assert [(r["physical_lot_id"], r["quantity"]) for r in rows] == [("legacy-1", 4)]
        uniques = []
        for idx in store.conn.execute("PRAGMA index_list(physical_lot)"):
            if idx[2]:
                uniques.append([r[2] for r in store.conn.execute(
                    f"PRAGMA index_info({idx[1]})")])
        assert ["collection_id", "oracle_id", "location_id", "lot_key",
                "physical_lot_id"] in uniques
        # the migrated table now accepts the second distinct lot
        store.conn.execute(
            "INSERT INTO collection(collection_id,title,created_at)"
            " VALUES('mig','t','2026-11-11T00:00:00Z')")
        store.conn.execute(
            "INSERT INTO physical_lot(physical_lot_id,collection_id,oracle_id,"
            "location_id,quantity) VALUES('legacy-2','mig','oid-x','Box A',1)")
        store.conn.commit()
        assert store.conn.execute(
            "SELECT COUNT(*) FROM physical_lot WHERE collection_id='mig'"
        ).fetchone()[0] == 2
    finally:
        store.close()


# --- 3) create_deck parent-revision isolation -------------------------------

def _mapped_collection(store, tmp_path, collection_id):
    path = tmp_path / f"{collection_id}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Name", "Menge", "Box"])
        writer.writerows([("Alara, Test Sovereign", 1, "A"),
                          ("Plains", 120, "A")])
    import_mapped_file(store, path, {
        "collection_id": collection_id,
        "columns": {"name": "Name", "quantity": "Menge", "location": "Box",
                    "reserved": None, "condition": None}})


def test_parent_revision_same_collection_is_variant(loaded_store, tmp_path):
    _mapped_collection(loaded_store, tmp_path, "r2-alpha")
    first = create_deck(loaded_store, "r2-alpha", "Deck", [CMD], {PLAINS: 99})
    second = create_deck(loaded_store, "r2-alpha", "Deck", [CMD], {PLAINS: 99},
                         parent_revision_id=first["revision_id"])
    assert second["deck_id"] == first["deck_id"]


def test_parent_revision_cross_collection_rejected(loaded_store, tmp_path):
    _mapped_collection(loaded_store, tmp_path, "r2-alpha")
    _mapped_collection(loaded_store, tmp_path, "r2-beta")
    first = create_deck(loaded_store, "r2-alpha", "Deck", [CMD], {PLAINS: 99})
    with pytest.raises(ValueError, match="cross-collection"):
        create_deck(loaded_store, "r2-beta", "Deck", [CMD], {PLAINS: 99},
                    parent_revision_id=first["revision_id"])
    # nothing was attached to the alpha deck
    count = loaded_store.conn.execute(
        "SELECT COUNT(*) FROM deck_revision WHERE deck_id=?",
        (first["deck_id"],)).fetchone()[0]
    assert count == 1


def test_parent_revision_unknown_rejected(loaded_store, tmp_path):
    _mapped_collection(loaded_store, tmp_path, "r2-alpha")
    with pytest.raises(LookupError, match="not found"):
        create_deck(loaded_store, "r2-alpha", "Deck", [CMD], {PLAINS: 99},
                    parent_revision_id="does-not-exist")


def test_web_parent_revision_errors_are_http(loaded_store, tmp_path, monkeypatch):
    """The API maps the library contract onto HTTP: unknown parent ->
    404, cross-collection parent -> 409 (never an opaque 500)."""
    from fastapi.testclient import TestClient

    from deckbuild_studio import web as web_mod

    _mapped_collection(loaded_store, tmp_path, "r2-alpha")
    _mapped_collection(loaded_store, tmp_path, "r2-beta")
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    client = TestClient(web_mod.create_app(), raise_server_exceptions=False)
    first = client.post("/api/decks", json={
        "collection_id": "r2-alpha", "name": "Deck",
        "commander_oracle_ids": [CMD], "entries": {PLAINS: 99}}).json()
    cross = client.post("/api/decks", json={
        "collection_id": "r2-beta", "name": "Deck",
        "commander_oracle_ids": [CMD], "entries": {PLAINS: 99},
        "parent_revision_id": first["revision_id"]})
    assert cross.status_code == 409
    unknown = client.post("/api/decks", json={
        "collection_id": "r2-alpha", "name": "Deck",
        "commander_oracle_ids": [CMD], "entries": {PLAINS: 99},
        "parent_revision_id": "does-not-exist"})
    assert unknown.status_code == 404


# --- 4) EDHREC inclusion consistency ----------------------------------------

def _stats_html(recs):
    return ('"gallery":' + json.dumps({"recs": recs, "categories": []}) +
            ' "featured":' + json.dumps({"rec": {"name": "R2 Commander",
                                                  "cardId": "r2-commander"}}) +
            ' "optionsFilters":' + json.dumps(
                {"brackets": [{"bracket": "core", "count": 10}]}))


def _parse(recs):
    return parse_stats_page(_stats_html(recs), expected_name="R2 Commander",
                            expected_slug="r2-commander", bracket="core")


def _rec(**over):
    rec = {"name": "R2 Card", "category": "creatures", "cardId": "r2-card",
           "numDecks": 5, "potentialDecks": 10, "inclusion": 0.5,
           "synergy": 0.1, "lift": 0.2}
    rec.update(over)
    return rec


def test_edhrec_consistent_inclusion_kept():
    parsed = _parse([_rec()])
    assert parsed["dropped_invalid"] == 0
    assert [c["name"] for c in parsed["cards"]] == ["R2 Card"]
    assert parsed["cards"][0]["inclusion"] == 0.5


def test_edhrec_inclusion_within_rounding_tolerance_kept():
    parsed = _parse([_rec(inclusion=0.51)])  # 0.51 vs 5/10: rounding noise
    assert parsed["dropped_invalid"] == 0
    assert len(parsed["cards"]) == 1


def test_edhrec_inclusion_contradiction_dropped():
    parsed = _parse([_rec(inclusion=0.9)])  # claims 90%, counts say 50%
    assert parsed["cards"] == []
    assert parsed["dropped_invalid"] == 1


def test_edhrec_inclusion_out_of_range_without_counts_dropped():
    rec = _rec(inclusion=1.5)
    del rec["numDecks"], rec["potentialDecks"]
    parsed = _parse([rec])
    assert parsed["cards"] == []
    assert parsed["dropped_invalid"] == 1
