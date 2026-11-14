"""DB diet: signals_json compression (deckbuild_studio.payloads).

Scope (co-lead review #51, measured — docs/DB_DIET.md):
``tier_assignment.signals_json`` is the dominant payload block (2.48 GB
of content) and IS compressed. ``external_snapshot.payload_json``
totals 12 MB and is deliberately NOT compressed — it stays plain JSON;
several tests below pin that scope decision so it cannot regress
silently.

Invariants under test:
  * roundtrip is byte-identical for every payload shape (the stored
    content is the provenance — nothing may change but the
    representation);
  * legacy plain signals (every database written before the codec)
    stay readable unchanged;
  * small payloads are stored verbatim — no representation churn;
  * a corrupt COMPRESSED value degrades exactly like a corrupt plain
    one (PayloadDecodeError is a json.JSONDecodeError, so the existing
    fallback handling applies);
  * GUARD: every signals_json reader decompresses BEFORE its silent
    fallback parsing. A compressed row read through any official read
    path must yield its real content — never an empty ``{}`` / None
    markers / an empty universe block. (Plain ``json.loads`` on a
    stored compressed value raises, so a reader that bypassed the
    codec would trip these tests loudly instead of silently
    degrading.)
  * the migration converts in place, verifies every row, and is
    resumable/idempotent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import OID
from deckbuild_studio import tierlist as tierlist_mod
from deckbuild_studio import topdeck as td_mod
from deckbuild_studio import web as web_mod
from deckbuild_studio.external import latest_snapshot, save_snapshot
from deckbuild_studio.payloads import (
    PREFIX,
    PayloadDecodeError,
    decode_payload,
    encode_payload,
    is_compressed,
    loads_payload,
)

BIG = json.dumps({"cards": [{"name": f"Test Card {i}", "inclusion": 0.5}
                             for i in range(200)]}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# codec unit tests
# ---------------------------------------------------------------------------

def test_roundtrip_large_payload_is_byte_identical():
    stored = encode_payload(BIG)
    assert is_compressed(stored)
    assert len(stored) < len(BIG) // 2
    assert decode_payload(stored) == BIG
    assert hashlib.sha256(decode_payload(stored).encode()).hexdigest() == \
        hashlib.sha256(BIG.encode()).hexdigest()


def test_small_payload_stays_plain():
    text = '{"games": 12}'
    assert encode_payload(text) == text
    assert not is_compressed(encode_payload(text))


def test_unicode_roundtrip():
    text = json.dumps({"name": "Übermut — Ætherflux, naïve café",
                       "pad": "x" * 900}, ensure_ascii=False)
    assert decode_payload(encode_payload(text)) == text


def test_incompressible_payload_stays_plain():
    # Deterministic near-maximum-entropy ASCII (~6.5 bits/char over a
    # 94-symbol alphabet): gzip can only reach ~0.85x, the base64 framing
    # costs 1.33x — the packed form cannot win, the plain original stays.
    text = "".join(
        chr(33 + hashlib.sha256(i.to_bytes(4, "little")).digest()[0] % 94)
        for i in range(4000))
    assert encode_payload(text) == text
    assert decode_payload(encode_payload(text)) == text


def test_none_and_plain_passthrough():
    assert encode_payload(None) is None
    assert decode_payload(None) is None
    assert decode_payload('{"a": 1}') == '{"a": 1}'
    assert loads_payload('{"a": 1}') == {"a": 1}


def test_loads_payload_compressed():
    assert loads_payload(encode_payload(BIG)) == json.loads(BIG)


def test_blob_bytes_behave_like_json_loads():
    # A BLOB in a TEXT column (hand-edited DB) must degrade through the
    # same ValueError path plain json.loads offered before the codec.
    assert loads_payload(b'{"a": 1}') == {"a": 1}
    assert not is_compressed(b"gzip+b64:AAAA")
    with pytest.raises(ValueError):
        loads_payload(b"\xff\xfe{")


@pytest.mark.parametrize("corrupt", [
    PREFIX + "!!!not-base64!!!",
    PREFIX + "aGVsbG8gd29ybGQ=",          # valid base64, not gzip
    PREFIX,                                # empty body
])
def test_corrupt_compressed_raises_json_decode_error(corrupt):
    with pytest.raises(PayloadDecodeError):
        decode_payload(corrupt)
    # ... and PayloadDecodeError IS a JSONDecodeError, so every existing
    # corrupt-payload handler (STALE marking, {} fallback) catches it.
    with pytest.raises(json.JSONDecodeError):
        loads_payload(corrupt)


def test_truncated_compressed_raises():
    stored = encode_payload(BIG)
    with pytest.raises(json.JSONDecodeError):
        loads_payload(stored[: len(stored) // 2])


def test_corrupt_plain_json_still_raises_plain_decode_error():
    with pytest.raises(json.JSONDecodeError):
        loads_payload("{not valid json")


# ---------------------------------------------------------------------------
# Scope guard: external_snapshot.payload_json stays PLAIN (review #51)
# ---------------------------------------------------------------------------

def test_save_snapshot_stores_big_payload_plain(store):
    payload = {"spellbook_card_id": 4242, "blob": "combo text " * 400}
    snap_id = save_snapshot(
        store, source_name="commanderspellbook", kind="spellbook_card",
        oracle_id=OID["sol_ring"], url="https://example.invalid/card",
        status="AVAILABLE", payload=payload)
    row = store.conn.execute(
        "SELECT payload_json FROM external_snapshot WHERE snapshot_id=?",
        (snap_id,)).fetchone()
    # plain JSON, byte-identical to the pre-diet representation
    assert not is_compressed(row["payload_json"])
    assert json.loads(row["payload_json"]) == payload
    snap = latest_snapshot(store, "commanderspellbook", "spellbook_card",
                           oracle_id=OID["sol_ring"])
    parsed, corrupt = td_mod._snapshot_payload(snap)
    assert not corrupt and parsed == payload


def test_marker_lookalike_in_payload_json_is_just_corrupt(store):
    """payload_json is never decoded: a hand-written marker-looking
    value is plain corrupt JSON for the snapshot readers (STALE path),
    not a compressed payload."""
    snap_id = save_snapshot(
        store, source_name="playgroup", kind="playgroup_card",
        oracle_id=OID["sol_ring"], url="https://example.invalid/card",
        status="AVAILABLE", payload={"games": 1})
    store.conn.execute(
        "UPDATE external_snapshot SET payload_json=? WHERE snapshot_id=?",
        (PREFIX + "aGVsbG8=", snap_id))
    store.conn.commit()
    snap = latest_snapshot(store, "playgroup", "playgroup_card",
                           oracle_id=OID["sol_ring"])
    parsed, corrupt = td_mod._snapshot_payload(snap)
    assert corrupt and parsed == {}


def test_playgroup_payload_path_unchanged_and_functional(store):
    fields = {"win_rates_observed": {
        "observed_gap_pp": 6.0, "n_cast": 500, "n_never_drawn": 700,
        "win_rate_cast_pct": 55.0, "win_rate_never_drawn_pct": 49.0,
        "ci95_pp": [1.0, 11.0], "pad": "p" * 800}}
    save_snapshot(
        store, source_name="playgroup", kind="playgroup_card",
        oracle_id=OID["sol_ring"], url="https://example.invalid/card",
        status="AVAILABLE", payload={"fields": fields})
    row = store.conn.execute(
        "SELECT payload_json FROM external_snapshot").fetchone()
    assert not is_compressed(row["payload_json"])
    sig = tierlist_mod._playgroup_lift_signal(store, OID["sol_ring"], 0.25)
    assert sig["available"] is True
    assert sig["value"]["lift_pp"] == 6.0


# ---------------------------------------------------------------------------
# API level: big snapshot payload end-to-end through the plain path
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(loaded_store, monkeypatch):
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_api_big_payload_card_reads_back(client, loaded_store):
    payload = {"fields": {"games": 7}, "blob": "z" * 3000}
    save_snapshot(
        loaded_store, source_name="playgroup", kind="playgroup_card",
        oracle_id=OID["sol_ring"], url="https://playgroup.gg/cards/sol-ring",
        status="AVAILABLE", payload=payload)
    resp = client.get("/api/external/card",
                      params={"oracle_id": OID["sol_ring"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "AVAILABLE"
    assert data["data"] == payload


# ---------------------------------------------------------------------------
# tier_assignment.signals_json: write path + every reader (GUARD tests)
# ---------------------------------------------------------------------------

def _insert_tier_row(store, *, scope="global", universe_id="",
                     signals_json, tier="A"):
    store.conn.execute(
        "INSERT INTO tier_assignment(oracle_id,scope,commander_oracle_id,"
        "bracket,universe_id,tier,score,evidence,signals_json,algo_version,"
        "computed_at,input_snapshot_ids_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (OID["sol_ring"], scope, "", "", universe_id, tier, 0.9, 0.9,
         signals_json, tierlist_mod._active_model(store),
         "2026-01-01T00:00:00+00:00", "[]"))
    store.conn.commit()


def test_tier_store_compresses_signals_and_get_tier_reads_back(store):
    signals = [{"signal": "edhrec_global_inclusion", "weight": 0.55,
                "subscore": 0.9, "available": True, "snapshot_id": "snap-x",
                "value": {"inclusion": 0.5, "pad": "s" * 1500}}]
    tierlist_mod._store_row(
        store, OID["sol_ring"], "global", "", "", signals, {},
        "2026-01-01T00:00:00+00:00",
        model_version=tierlist_mod._active_model(store))
    store.conn.commit()
    raw = store.conn.execute(
        "SELECT signals_json FROM tier_assignment").fetchone()["signals_json"]
    assert is_compressed(raw)
    row = tierlist_mod.get_tier(store, OID["sol_ring"])
    assert row is not None
    assert row["signals"]["signals"][0]["signal"] == "edhrec_global_inclusion"
    assert row["signals"]["signals"][0]["value"]["pad"] == "s" * 1500


def test_tier_legacy_plain_signals_still_read(store):
    signals = {"signals": [{"signal": "x"}], "markers": {}}
    _insert_tier_row(store, signals_json=json.dumps(signals))
    row = tierlist_mod.get_tier(store, OID["sol_ring"])
    assert row["signals"] == signals


def test_tier_corrupt_compressed_signals_degrade_to_empty(store):
    good = encode_payload(json.dumps({"signals": [], "pad": "q" * 900}))
    _insert_tier_row(store, signals_json=good[: len(good) // 2])
    row = tierlist_mod.get_tier(store, OID["sol_ring"])
    assert row is not None and row["tier"] == "A"  # scalars survive
    assert row["signals"] == {}                    # payload degrades


def test_guard_stored_compressed_value_is_not_plain_json(store):
    """Meta-guard: a stored compressed signals value is NOT parseable by
    plain json.loads. Any reader that bypassed the codec would raise —
    and the reader tests below prove the official paths do not."""
    _insert_tier_row(store, signals_json=encode_payload(BIG))
    raw = store.conn.execute(
        "SELECT signals_json FROM tier_assignment").fetchone()["signals_json"]
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)


def test_guard_tiers_map_decompresses_markers(store):
    signals = {"markers": {"salt": 42.0, "salt_band": "high",
                           "budget_eur": 3.5, "budget_band": "low",
                           "flags": ["storm"]},
               "pad": "m" * 1200}
    _insert_tier_row(store, signals_json=encode_payload(
        json.dumps(signals, ensure_ascii=False, sort_keys=True)))
    out = tierlist_mod.tiers_map(store, [OID["sol_ring"]])
    markers = out[OID["sol_ring"]]["markers"]
    # a missed decompression would silently yield all-None markers here
    assert markers == {"salt": 42.0, "salt_band": "high",
                       "budget_eur": 3.5, "budget_band": "low",
                       "flags": ["storm"]}


def test_guard_list_universes_decompresses_block(store):
    signals = {"universe": {"profile": "archidekt:all",
                            "universe_type": "platform",
                            "universe_size": 123,
                            "definition": {"platform": "archidekt"}},
               "pad": "u" * 1200}
    _insert_tier_row(store, scope="universe", universe_id="uni-test",
                     signals_json=encode_payload(
                         json.dumps(signals, ensure_ascii=False,
                                    sort_keys=True)),
                     tier="C")
    out = tierlist_mod.list_universes(store)
    entry = next(u for u in out if u["universe_id"] == "uni-test")
    # a missed decompression would silently yield profile/size None here
    assert entry["profile"] == "archidekt:all"
    assert entry["universe_size"] == 123
    assert entry["definition"] == {"platform": "archidekt"}


# ---------------------------------------------------------------------------
# migration tool (generic; the diet run targets signals_json by default)
# ---------------------------------------------------------------------------

def _load_migration():
    path = Path(__file__).resolve().parent.parent / "tools" / \
        "migrate_payload_compression.py"
    spec = importlib.util.spec_from_file_location("migrate_payloads", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture_db(path: Path) -> dict[str, str | None]:
    """Minimal snapshot/tier tables with every payload shape; returns the
    original values keyed by snapshot_id."""
    originals: dict[str, str | None] = {
        "snap-big": BIG,
        "snap-small": '{"games": 3}',
        "snap-corrupt": "{not valid json " + "x" * 900,
        "snap-none": None,
        "snap-pre": encode_payload(BIG),
    }
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE external_snapshot (snapshot_id TEXT PRIMARY KEY,"
                " payload_json TEXT)")
    con.executemany("INSERT INTO external_snapshot VALUES(?,?)",
                    originals.items())
    con.execute("CREATE TABLE tier_assignment (oracle_id TEXT, scope TEXT,"
                " signals_json TEXT NOT NULL DEFAULT '{}',"
                " PRIMARY KEY (oracle_id, scope))")
    con.execute("INSERT INTO tier_assignment VALUES('o1','global',?)", (BIG,))
    con.commit()
    con.close()
    return originals


def test_migration_converts_verifies_and_is_idempotent(tmp_path):
    mod = _load_migration()
    db = tmp_path / "fixture.sqlite3"
    originals = _fixture_db(db)
    both = ["--column", "external_snapshot.payload_json",
            "--column", "tier_assignment.signals_json"]
    assert mod.main(["--db", str(db), *both]) == 0
    con = sqlite3.connect(db)
    stored = dict(con.execute(
        "SELECT snapshot_id, payload_json FROM external_snapshot"))
    # big + corrupt converted (corrupt stays byte-identical after decode),
    # small kept plain, NULL untouched, pre-compressed untouched
    assert is_compressed(stored["snap-big"])
    assert decode_payload(stored["snap-big"]) == originals["snap-big"]
    assert stored["snap-small"] == originals["snap-small"]
    assert decode_payload(stored["snap-corrupt"]) == originals["snap-corrupt"]
    assert stored["snap-none"] is None
    assert stored["snap-pre"] == originals["snap-pre"]
    tier = con.execute("SELECT signals_json FROM tier_assignment").fetchone()[0]
    assert is_compressed(tier) and decode_payload(tier) == BIG
    con.close()
    # resume/idempotency: a second run converts nothing further
    assert mod.main(["--db", str(db), *both]) == 0
    con = sqlite3.connect(db)
    assert dict(con.execute(
        "SELECT snapshot_id, payload_json FROM external_snapshot")) == stored
    con.close()


def test_migration_default_column_is_signals_only(tmp_path):
    mod = _load_migration()
    db = tmp_path / "fixture.sqlite3"
    originals = _fixture_db(db)
    assert mod.main(["--db", str(db)]) == 0
    con = sqlite3.connect(db)
    # default run: signals converted, snapshot payloads untouched (scope)
    assert dict(con.execute(
        "SELECT snapshot_id, payload_json FROM external_snapshot")) == originals
    tier = con.execute("SELECT signals_json FROM tier_assignment").fetchone()[0]
    assert is_compressed(tier)
    con.close()


def test_migration_dry_run_writes_nothing(tmp_path):
    mod = _load_migration()
    db = tmp_path / "fixture.sqlite3"
    originals = _fixture_db(db)
    before = db.read_bytes()
    assert mod.main(["--db", str(db), "--dry-run"]) == 0
    con = sqlite3.connect(db)
    assert dict(con.execute(
        "SELECT snapshot_id, payload_json FROM external_snapshot")) == originals
    con.close()
    assert db.read_bytes() == before


def test_migration_missing_db_and_table_are_usage_errors(tmp_path):
    mod = _load_migration()
    assert mod.main(["--db", str(tmp_path / "nope.sqlite3")]) == 2
    db = tmp_path / "fixture.sqlite3"
    _fixture_db(db)
    assert mod.main(["--db", str(db), "--column", "nope.payload_json"]) == 2
    assert mod.main(["--db", str(db), "--column", "external_snapshot.nope"]) == 2
