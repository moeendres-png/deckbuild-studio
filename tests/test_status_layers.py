"""Status endpoint completeness (Wave 3): /api/external/status must
list EVERY data layer — rulings, EDHTop16 (base + per-commander),
MTGJSON, TopDeck, tagger/roles categories — not only edhrec /
playgroup / card_atlas. A layer that never synced answers NOT_FETCHED
honestly; a seeded layer flips to its real status and counts."""
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
              "topdeck", "categories")


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
