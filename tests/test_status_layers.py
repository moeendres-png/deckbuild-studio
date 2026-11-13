"""Status endpoint completeness (Wave 3): /api/external/status must
list EVERY data layer — rulings, EDHTop16 (base + per-commander),
MTGJSON, TopDeck, tagger/roles categories — not only edhrec /
playgroup / card_atlas. A layer that never synced answers NOT_FETCHED
honestly; a seeded layer flips to its real status and counts.

Completion (Lane I): the same holds for the Spellbook combo layer
and the stored-decklist layer (universes / Verbreitung), and for
/api/status, whose external_data must carry the full layer set too
— both endpoints assemble it in Store._external_summary."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import web as web_mod
from deckbuild_studio.external import save_snapshot
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook

ALARA = "Alara, Test Sovereign"
LAYER_KEYS = ("rulings", "edhtop16", "edhtop16_commanders", "mtgjson",
              "topdeck", "categories", "spellbook", "decklists")


@pytest.fixture()
def collection_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            ("Sol Ring (Test)", 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


def _status(store, monkeypatch):
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    return client.get("/api/external/status",
                      params={"collection_id": FC}).json()


def test_status_lists_all_layers_not_fetched(collection_store, monkeypatch):
    st = _status(collection_store, monkeypatch)
    for key in LAYER_KEYS:
        assert key in st, f"layer {key} missing from /api/external/status"
    # pre-existing layers stay
    assert "edhrec" in st and "playgroup" in st and "card_atlas" in st
    # honest empty states
    assert st["rulings"]["status"] == "NOT_FETCHED"
    assert st["rulings"]["with_rulings"] == 0
    assert st["edhtop16"]["status"] == "NOT_FETCHED"
    assert st["edhtop16"]["with_play_rate"] == 0
    assert st["mtgjson"]["printings"]["status"] == "NOT_FETCHED"
    assert st["topdeck"]["status"] == "NOT_FETCHED"
    assert st["topdeck"]["cards_published"] == 0
    cmd = st["edhtop16_commanders"]
    assert cmd["eligible_commanders"] >= 1
    assert cmd["commanders_by_status"].get("NOT_FETCHED") == \
        cmd["eligible_commanders"]
    assert cmd["pairs_total"] == 0
    cat = st["categories"]
    assert cat["universe_identities"] == 3
    assert cat["layers"], "tagger/role layers must be present"
    sb = st["spellbook"]
    assert sb["status"] == "NOT_FETCHED"
    assert sb["attempted"] == 0
    assert sb["by_status"] == {}
    assert sb["cards_with_combos"] == 0
    assert sb["combos_total"] == 0
    assert sb["total_identities"] == 3
    dl = st["decklists"]
    assert dl["status"] == "NOT_FETCHED"
    assert dl["decks_total"] == 0
    assert dl["decks_by_platform"] == {}
    assert dl["cohort_decks"] == 0
    assert dl["cohort_listings"] == 0
    assert dl["universes"] == 0
    assert dl["canonical_denominator"] == 0


def test_status_rulings_layer_flips_with_seeded_snapshot(collection_store,
                                                         monkeypatch):
    snap_id = save_snapshot(collection_store, source_name="scryfall",
                            kind="scryfall_rulings",
                            url="https://example.test/rulings.jsonl",
                            status="AVAILABLE", raw=b"{}")
    collection_store.conn.execute(
        "INSERT INTO card_ruling(snapshot_id, ruling_key, oracle_id, "
        "source, published_at, comment) VALUES(?,?,?,?,?,?)",
        (snap_id, "k1", OID["plains"], "wtc", "2024-01-01", "Test ruling."))
    collection_store.conn.commit()
    st = _status(collection_store, monkeypatch)
    assert st["rulings"]["status"] == "AVAILABLE"
    assert st["rulings"]["with_rulings"] == 1
    assert st["rulings"]["rulings_total"] == 1
    assert st["rulings"]["total_identities"] == 3


# ------------------------------------------------------- Lane I: spellbook

def _spellbook_snap(store, oid, url, status, combos, fetched_at=None):
    snap_id = save_snapshot(store, source_name="commanderspellbook",
                            kind="spellbook_card", oracle_id=oid,
                            url=url, status=status, raw=b"{}")
    for i in range(combos):
        store.conn.execute(
            "INSERT INTO spellbook_combo(snapshot_id, combo_id, "
            "card_oracle_ids_json, card_names_json, produces_json) "
            "VALUES(?,?,?,?,?)",
            (snap_id, f"{url}-combo-{i}", "[]", "[]", "[]"))
    if fetched_at is not None:
        store.conn.execute(
            "UPDATE external_snapshot SET fetched_at=? "
            "WHERE snapshot_id=?", (fetched_at, snap_id))
    store.conn.commit()
    return snap_id


def test_status_spellbook_layer_counts_latest_snapshot_only(
        collection_store, monkeypatch):
    # An older Plains snapshot stored 5 combos; only the LATEST
    # snapshot's rows may count (2), older ones are history.
    _spellbook_snap(collection_store, OID["plains"],
                    "https://example.test/sb/plains-old", "AVAILABLE", 5,
                    fetched_at="2026-01-01T00:00:00+00:00")
    _spellbook_snap(collection_store, OID["plains"],
                    "https://example.test/sb/plains-new", "AVAILABLE", 2,
                    fetched_at="2026-06-01T00:00:00+00:00")
    _spellbook_snap(collection_store, OID["sol_ring"],
                    "https://example.test/sb/sol-ring", "NOT_FOUND", 0,
                    fetched_at="2026-05-01T00:00:00+00:00")
    # A snapshot for a card outside the collection never counts.
    _spellbook_snap(collection_store, OID["forest"],
                    "https://example.test/sb/forest", "AVAILABLE", 7)
    sb = _status(collection_store, monkeypatch)["spellbook"]
    assert sb["status"] == "AVAILABLE"
    assert sb["total_identities"] == 3
    assert sb["attempted"] == 2
    assert sb["by_status"] == {"AVAILABLE": 1, "NOT_FOUND": 1}
    assert sb["cards_with_combos"] == 1
    assert sb["combos_total"] == 2
    assert sb["fetched_at"] == "2026-06-01T00:00:00+00:00"


def test_status_spellbook_layer_partial_rollup(collection_store,
                                               monkeypatch):
    _spellbook_snap(collection_store, OID["plains"],
                    "https://example.test/sb/plains-partial",
                    "PARTIAL", 3)
    sb = _status(collection_store, monkeypatch)["spellbook"]
    assert sb["status"] == "PARTIAL"
    assert sb["by_status"] == {"PARTIAL": 1}
    assert sb["cards_with_combos"] == 1
    assert sb["combos_total"] == 3


# ------------------------------------------------------- Lane I: decklists

def _deck(store, uid, platform, bracket):
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid, platform, platform_deck_id, "
        "commander_oracle_id, commander_name, bracket_level, source_url, "
        "status, parser_version, fetched_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (uid, platform, uid.split(":")[1], OID["commander_a"], ALARA,
         bracket, f"https://example.test/{uid}", "AVAILABLE",
         "fixture/1.0.0", "2026-11-13T00:00:00+00:00"))


def _deck_card(store, uid, key, oid, name, qty, is_cmd):
    store.conn.execute(
        "INSERT INTO decklist_card(deck_uid, entry_key, oracle_id, "
        "card_name, quantity, is_commander) VALUES(?,?,?,?,?,?)",
        (uid, key, oid, name, qty, is_cmd))


def test_status_decklists_layer_counts(collection_store, monkeypatch):
    # Two content-identical archidekt decks collapse to ONE canonical
    # deck (the Verbreitung rule); the TopDeck deck is stored and
    # counted in decks_total but never folded into the cohort count.
    for uid in ("archidekt:1", "archidekt:2"):
        _deck(collection_store, uid, "archidekt", 3)
        _deck_card(collection_store, uid, "cmd", OID["commander_a"],
                   ALARA, 1, 1)
        _deck_card(collection_store, uid, "plains", OID["plains"],
                   "Plains", 5, 0)
        _deck_card(collection_store, uid, "solring", OID["sol_ring"],
                   "Sol Ring (Test)", 1, 0)
    _deck(collection_store, "topdeck:9", "topdeck", None)
    _deck_card(collection_store, "topdeck:9", "plains", OID["plains"],
               "Plains", 5, 0)
    collection_store.conn.execute(
        "INSERT INTO decklist_listing(platform, commander_oracle_id, "
        "commander_name, bracket_level, listed_count, updated_at) "
        "VALUES('archidekt', ?, ?, 3, 2, '2026-11-13T00:00:00+00:00')",
        (OID["commander_a"], ALARA))
    collection_store.conn.commit()
    dl = _status(collection_store, monkeypatch)["decklists"]
    assert dl["status"] == "AVAILABLE"
    assert dl["decks_total"] == 3
    assert dl["decks_by_platform"] == {"archidekt": 2, "topdeck": 1}
    assert dl["decks_by_status"] == {"AVAILABLE": 3}
    assert dl["cohort_decks"] == 2
    assert dl["cohort_listings"] == 1
    assert dl["canonical_denominator"] == 1
    assert dl["denominator_by_platform"] == {"archidekt": 1}
    assert dl["denominator_by_bracket"] == {"3": 1}
    assert dl["universes"] == 0


# ------------------------------------------- Lane I: /api/status + empty DB

def test_api_status_external_data_lists_all_layers(collection_store,
                                                   monkeypatch):
    monkeypatch.setattr(web_mod, "database_path",
                        lambda: collection_store.path)
    client = TestClient(web_mod.create_app())
    ext = client.get("/api/status").json()["external_data"]
    for key in ("edhrec", "playgroup", "card_atlas_coverage") + LAYER_KEYS:
        assert key in ext, f"layer {key} missing from /api/status"
    assert ext["spellbook"]["status"] == "NOT_FETCHED"
    assert ext["spellbook"]["combos_total"] == 0
    assert ext["decklists"]["status"] == "NOT_FETCHED"
    assert ext["decklists"]["decks_total"] == 0
    assert ext["rulings"]["status"] == "NOT_FETCHED"
    assert ext["topdeck"]["status"] == "NOT_FETCHED"


def test_status_endpoints_survive_empty_database(store, monkeypatch):
    # Bare store: schema only, no imports, no snapshots at all —
    # both endpoints answer 200 with honest NOT_FETCHED sections.
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    resp = client.get("/api/external/status", params={"collection_id": FC})
    assert resp.status_code == 200
    st = resp.json()
    for key in LAYER_KEYS:
        assert key in st, f"layer {key} missing on empty database"
    assert st["spellbook"]["status"] == "NOT_FETCHED"
    assert st["spellbook"]["total_identities"] == 0
    assert st["decklists"]["status"] == "NOT_FETCHED"
    assert st["decklists"]["decks_total"] == 0
    resp = client.get("/api/status")
    assert resp.status_code == 200
    ext = resp.json()["external_data"]
    assert ext["spellbook"]["status"] == "NOT_FETCHED"
    assert ext["decklists"]["canonical_denominator"] == 0
