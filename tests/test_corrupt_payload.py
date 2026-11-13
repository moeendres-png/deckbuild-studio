"""Issue #21 regression: a corrupt/invalid ``payload_json`` in a stored
snapshot must degrade to an honest STALE state, never an unhandled 500.

Snapshots are seeded through ``external.save_snapshot`` (which always
writes valid JSON via ``json.dumps``) and then corrupted in place —
that is the only way a corrupt payload can exist in the store.
"""
import pytest
from fastapi.testclient import TestClient

from conftest import OID
from deckbuild_studio import topdeck as td_mod
from deckbuild_studio import web as web_mod
from deckbuild_studio.external import save_snapshot

CORRUPT = "{not valid json"


def _corrupt(store, snapshot_id: str) -> None:
    store.conn.execute(
        "UPDATE external_snapshot SET payload_json=? WHERE snapshot_id=?",
        (CORRUPT, snapshot_id))
    store.conn.commit()


@pytest.fixture()
def client(loaded_store, monkeypatch):
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_external_card_corrupt_payload_is_stale_not_500(client, loaded_store):
    snap_id = save_snapshot(
        loaded_store, source_name="playgroup", kind="playgroup_card",
        oracle_id=OID["sol_ring"], url="https://playgroup.gg/cards/sol-ring",
        status="AVAILABLE", payload={"games": 12})
    _corrupt(loaded_store, snap_id)
    resp = client.get("/api/external/card",
                      params={"oracle_id": OID["sol_ring"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "STALE"
    assert data["data"] is None
    assert "payload_json corrupt" in data["detail"]


def test_external_commander_corrupt_payload_is_stale_not_500(client, loaded_store):
    snap_id = save_snapshot(
        loaded_store, source_name="playgroup", kind="playgroup_commander",
        commander_oracle_id=OID["commander_a"],
        url="https://playgroup.gg/commanders/1-test",
        status="AVAILABLE", payload={"games": 34})
    _corrupt(loaded_store, snap_id)
    resp = client.get("/api/external/commander",
                      params={"commander_oracle_id": OID["commander_a"]})
    assert resp.status_code == 200
    pg = resp.json()["playgroup"]
    assert pg["status"] == "STALE"
    assert pg["data"] is None
    assert "payload_json corrupt" in pg["detail"]


def _seed_topdeck(store) -> str:
    return save_snapshot(
        store, source_name=td_mod.SOURCE_NAME, kind=td_mod.KIND,
        url="https://topdeck.gg", status="AVAILABLE",
        payload={"decks": 3, "documents": 4, "window": "last_year"})


def test_topdeck_coverage_corrupt_payload_is_stale(loaded_store):
    _corrupt(loaded_store, _seed_topdeck(loaded_store))
    out = td_mod.topdeck_coverage(loaded_store, "foundation-schwarze-box")
    assert out["status"] == "STALE"
    assert out["decks"] is None and out["documents"] is None
    assert out["window"] is None


def test_card_topdeck_corrupt_payload_is_stale(loaded_store):
    _corrupt(loaded_store, _seed_topdeck(loaded_store))
    out = td_mod.card_topdeck(loaded_store, OID["sol_ring"])
    assert out["status"] == "STALE"
    assert out["listed"] is False
    assert out["window"] is None


def test_card_topdeck_corrupt_payload_keeps_listed_row_values(loaded_store):
    snap_id = _seed_topdeck(loaded_store)
    loaded_store.conn.execute(
        "INSERT INTO topdeck_card_stat(snapshot_id,card_name,card_oracle_id,"
        "decks_with,decks_in_cut,top_cut_decks,conversion_rate,wins,draws,"
        "losses,games,win_rate) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (snap_id, "Sol Ring (Test)", OID["sol_ring"], 40, 10, 8, 0.25,
         30, 2, 20, 52, 0.61))
    loaded_store.conn.commit()
    _corrupt(loaded_store, snap_id)
    out = td_mod.card_topdeck(loaded_store, OID["sol_ring"])
    # The stat row is real table data and survives; only the payload-
    # derived window is honestly empty and the layer is marked STALE.
    assert out["status"] == "STALE"
    assert out["listed"] is True
    assert out["decks_with"] == 40 and out["win_rate"] == 0.61
    assert out["window"] is None


def test_topdeck_non_object_payload_is_stale(loaded_store):
    snap_id = _seed_topdeck(loaded_store)
    loaded_store.conn.execute(
        "UPDATE external_snapshot SET payload_json='[1, 2]' "
        "WHERE snapshot_id=?", (snap_id,))
    loaded_store.conn.commit()
    out = td_mod.topdeck_coverage(loaded_store, "foundation-schwarze-box")
    assert out["status"] == "STALE"
