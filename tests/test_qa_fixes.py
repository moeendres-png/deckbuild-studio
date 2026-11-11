"""QA-fix regression tests for the PR #3 review findings (comment
6806751003): P0.1 Scryfall formats, P0.2 deck draft/legal status,
P0.3 web deck flows, P1.4 card_id, P1.5 multi-lot, P1.6 partner rules,
P1.7 strict quantities, P1.8 start order, P1.9 commander context.
Synthetic fixtures only — no private collection data."""
from __future__ import annotations

import gzip
import io
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from conftest import OID, synthetic_cards, write_foundation_xlsx
from deckbuild_studio import scryfall as scryfall_mod
from deckbuild_studio import web as web_mod
from deckbuild_studio.commander import pairing_mechanisms, partner_with_target
from deckbuild_studio.decks import _pair_legal, create_deck, export_revision, validate_deck
from deckbuild_studio.importers import (
    FOUNDATION_COLLECTION as FC,
)
from deckbuild_studio.importers import (
    ImportFailure,
    apply_card_id_registry,
    generated_card_id,
    import_foundation_workbook,
    import_normalized_workbook,
    load_card_id_registry,
)
from deckbuild_studio.scryfall import import_scryfall, sync_scryfall
from deckbuild_studio.store import Store

N_CARDS = len(OID)


# ---------------------------------------------------------------------------
# P0.1 — Scryfall formats detected from content, streamed
# ---------------------------------------------------------------------------

def _array_bytes(cards=None) -> bytes:
    return json.dumps(cards or synthetic_cards()).encode()


def _jsonl_bytes(cards=None) -> bytes:
    return "".join(json.dumps(c) + "\n" for c in (cards or synthetic_cards())).encode()


@pytest.mark.parametrize("name,blob", [
    ("default-cards.json", _array_bytes()),                    # plain JSON array
    ("default-cards.json.gz", gzip.compress(_array_bytes())),  # gzipped array
    ("default-cards.jsonl", _jsonl_bytes()),                   # plain JSONL
    ("default-cards.jsonl.gz", gzip.compress(_jsonl_bytes())),  # gzipped JSONL
    # the original QA bug: the NAME claims jsonl.gz, the CONTENT is a raw array
    ("default-cards.jsonl.gz", _array_bytes()),
    # and the reverse lie: plain name, gzipped JSONL content
    ("download.json", gzip.compress(_jsonl_bytes())),
])
def test_scryfall_all_formats_by_content(store, tmp_path, name, blob):
    path = tmp_path / name
    path.write_bytes(blob)
    result = import_scryfall(store, path)
    assert result["oracle_identities"] == N_CARDS
    assert result["printings_read"] == N_CARDS


def test_scryfall_streaming_multichunk(store, tmp_path):
    # >64 KiB payloads force several decoder chunks for both shapes.
    cards = []
    for i in range(300):
        c = dict(synthetic_cards()[11])  # Plains template
        c["oracle_id"] = f"10000000-0000-4000-8000-{i:012d}"
        c["id"] = f"printing-bulk-{i}"
        c["name"] = f"Bulk Land {i}"
        cards.append(c)
    arr = tmp_path / "big.json"
    arr.write_bytes(_array_bytes(cards))
    assert import_scryfall(store, tmp_path / "big.json")["oracle_identities"] == 300
    store2 = Store(tmp_path / "s2.sqlite3")
    jl = tmp_path / "big.jsonl.gz"
    jl.write_bytes(gzip.compress(_jsonl_bytes(cards)))
    assert import_scryfall(store2, jl)["oracle_identities"] == 300


def test_scryfall_garbage_rejected(store, tmp_path):
    path = tmp_path / "junk.json"
    path.write_text("this is not json at all")
    with pytest.raises(ValueError):
        import_scryfall(store, path)


class _Resp:
    def __init__(self, data: bytes):
        self._b = io.BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._b.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _mock_bulk(monkeypatch, index_entry: dict, payload: bytes):
    index = json.dumps({"data": [{"type": "oracle_cards"},
                                  {"type": "default_cards", **index_entry}]}).encode()

    def fake_urlopen(req, timeout=None):
        if "bulk-data" in req.full_url:
            return _Resp(index)
        return _Resp(payload)

    monkeypatch.setattr(scryfall_mod.urllib.request, "urlopen", fake_urlopen)


def test_sync_scryfall_jsonl_download_uri(store, tmp_path, monkeypatch):
    _mock_bulk(monkeypatch,
               {"updated_at": "2026-11-11T00:00:00Z",
                "jsonl_download_uri": "https://example.invalid/default-cards-x.jsonl.gz",
                "download_uri": "https://example.invalid/default-cards-x.json"},
               gzip.compress(_jsonl_bytes()))
    result = sync_scryfall(store, target_dir=tmp_path / "dl")
    assert result["downloaded_to"].endswith("default-cards.jsonl.gz")
    assert result["oracle_identities"] == N_CARDS


def test_sync_scryfall_download_uri_serves_raw_array(store, tmp_path, monkeypatch):
    # Legacy field only: download_uri serves an UNCOMPRESSED JSON array —
    # the exact P0.1 failure (was stored as .jsonl.gz and parsed as gzip).
    _mock_bulk(monkeypatch,
               {"updated_at": "2026-11-11T00:00:00Z",
                "download_uri": "https://example.invalid/default-cards-x.json"},
               _array_bytes())
    result = sync_scryfall(store, target_dir=tmp_path / "dl")
    assert result["downloaded_to"].endswith("default-cards.json")
    assert result["oracle_identities"] == N_CARDS


# ---------------------------------------------------------------------------
# P0.2 — invalid decks are drafts, never legal
# ---------------------------------------------------------------------------

@pytest.fixture()
def collection(loaded_store, tmp_path):
    rows = [("Alara, Test Sovereign", 1, "Foundation"),
            ("Plains", 60, "Foundation"),
            ("Forest", 120, "Schwarze Box"),
            ("Sol Ring (Test)", 2, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


def test_invalid_deck_saved_as_draft_and_marked(collection):
    made = create_deck(collection, FC, "Kaputt", [OID["commander_a"]],
                       {OID["plains"]: 10})  # wrong size
    assert made["status"] == "draft"
    assert not made["validation"]["valid"]
    text = export_revision(collection, made["revision_id"])
    assert text.startswith("# ENTWURF — nicht legal")
    with pytest.raises(ValueError):
        export_revision(collection, made["revision_id"], require_legal=True)


def test_valid_deck_is_legal_and_exports_clean(collection):
    made = create_deck(collection, FC, "Gut", [OID["commander_a"]],
                       {OID["plains"]: 50, OID["forest"]: 49})
    assert made["status"] == "legal"
    text = export_revision(collection, made["revision_id"], require_legal=True)
    assert "ENTWURF" not in text
    assert "Alara, Test Sovereign" in text


# ---------------------------------------------------------------------------
# P0.3 / P1.9 — web flows + marks + commander context
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(collection, monkeypatch):
    monkeypatch.setattr(web_mod, "database_path", lambda: collection.path)
    return TestClient(web_mod.create_app())


def test_web_deck_flow_end_to_end(client):
    draft = client.post("/api/decks", json={
        "collection_id": FC, "name": "Web Deck",
        "commander_oracle_ids": [OID["commander_a"]],
        "entries": {OID["plains"]: 10}}).json()
    assert draft["status"] == "draft"
    decks = client.get("/api/decks", params={"collection_id": FC}).json()
    assert len(decks) == 1 and decks[0]["latest_status"] == "draft"
    deck_id, rev1 = draft["deck_id"], draft["revision_id"]

    variant = client.post("/api/decks", json={
        "collection_id": FC, "name": "Web Deck",
        "commander_oracle_ids": [OID["commander_a"]],
        "entries": {OID["plains"]: 50, OID["forest"]: 49},
        "parent_revision_id": rev1}).json()
    assert variant["status"] == "legal" and variant["deck_id"] == deck_id

    revs = client.get(f"/api/decks/{deck_id}/revisions").json()
    assert [r["status"] for r in revs] == ["draft", "legal"]

    loaded = client.get(f"/api/decks/revision/{variant['revision_id']}").json()
    assert loaded["entries"] == {OID["plains"]: 50, OID["forest"]: 49}
    assert loaded["commander_oracle_ids"] == [OID["commander_a"]]

    diff = client.get("/api/decks/compare",
                      params={"a": rev1, "b": variant["revision_id"]}).json()
    assert diff["status_a"] == "draft" and diff["status_b"] == "legal"
    assert diff["names"][OID["forest"]] == "Forest"

    resp = client.get(f"/api/decks/{rev1}/export")
    assert resp.headers["x-deck-status"] == "draft"
    assert resp.text.startswith("# ENTWURF — nicht legal")
    assert client.get(f"/api/decks/{rev1}/export",
                      params={"legal_only": True}).status_code == 409
    ok = client.get(f"/api/decks/{variant['revision_id']}/export",
                    params={"legal_only": True})
    assert ok.status_code == 200 and ok.headers["x-deck-status"] == "legal"

    assert client.delete(f"/api/decks/{deck_id}").json()["ok"] is True
    assert client.get("/api/decks", params={"collection_id": FC}).json() == []
    assert client.get(f"/api/decks/revision/{rev1}").status_code == 404


def test_index_contains_deck_flow_controls(client):
    html = client.get("/").text
    for element_id in ("savedeck", "variantdeck", "deckselect", "revisionselect",
                       "loadrevision", "deletedeck", "cmpa", "cmpb", "comparebtn",
                       "deckstatus"):
        assert f'id="{element_id}"' in html


def test_marks_editable_via_api(client):
    client.post("/api/marks", json={"collection_id": FC, "oracle_id": OID["plains"],
                                    "favorite": True, "excluded": False,
                                    "note": "Mana-Basis"})
    cards = client.get("/api/cards", params={"collection_id": FC}).json()
    plains = next(c for c in cards if c["oracle_id"] == OID["plains"])
    assert plains["favorite"] is True and plains["note"] == "Mana-Basis"
    client.post("/api/marks", json={"collection_id": FC, "oracle_id": OID["plains"],
                                    "favorite": False, "excluded": False, "note": ""})
    cards = client.get("/api/cards", params={"collection_id": FC}).json()
    plains = next(c for c in cards if c["oracle_id"] == OID["plains"])
    assert plains["favorite"] is False and plains["note"] == ""


def test_cards_commander_context_applied(client):
    cards = client.get("/api/cards", params={
        "collection_id": FC, "commander_oracle_id": OID["commander_a"]}).json()
    by_name = {c["name"]: c for c in cards}
    assert by_name["Plains"]["in_commander_pool"] is True
    assert by_name["Plains"]["in_commander_identity"] is True
    assert by_name["Alara, Test Sovereign"]["in_commander_pool"] is False  # itself
    plain = client.get("/api/cards", params={"collection_id": FC}).json()
    assert "in_commander_pool" not in plain[0]
    assert client.get("/api/cards", params={
        "collection_id": FC, "commander_oracle_id": "no-such-id"}).status_code == 404


# ---------------------------------------------------------------------------
# P1.4 — card_id: generated deterministically, registry wins, never NULL
# ---------------------------------------------------------------------------

def test_simple_import_assigns_generated_card_ids(collection):
    lots = collection.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot WHERE collection_id=?", (FC,)).fetchall()
    assert lots and all(r["card_id"] for r in lots)
    for r in lots:
        assert r["card_id"] == generated_card_id(r["oracle_id"])
    n_ids = collection.conn.execute("SELECT COUNT(*) FROM card_identity").fetchone()[0]
    assert n_ids == len({r["oracle_id"] for r in lots})
    evidence = collection.conn.execute(
        "SELECT DISTINCT identity_evidence FROM card_identity").fetchall()
    assert [r["identity_evidence"] for r in evidence] == ["generated:sha256(oracle_id)"]


def test_card_id_stable_across_reimport(loaded_store, tmp_path):
    rows = [("Plains", 10, "Foundation"), ("Sol Ring (Test)", 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    before = {r["oracle_id"]: r["card_id"] for r in loaded_store.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot")}
    import_foundation_workbook(loaded_store, path)
    after = {r["oracle_id"]: r["card_id"] for r in loaded_store.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot")}
    assert before == after


def test_registry_at_import_and_apply_later(loaded_store, tmp_path):
    rows = [("Plains", 10, "Foundation"), ("Forest", 5, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps({OID["plains"]: "card-plains-known"}))
    import_foundation_workbook(loaded_store, path, card_id_registry=reg_path)
    ids = {r["oracle_id"]: r["card_id"] for r in loaded_store.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot")}
    assert ids[OID["plains"]] == "card-plains-known"          # registry wins
    assert ids[OID["forest"]] == generated_card_id(OID["forest"])  # generated fallback
    # later registry replaces the generated id, lots follow consistently
    report = apply_card_id_registry(loaded_store, {OID["forest"]: "card-forest-known"})
    assert report["replaced"] == 1 and report["conflicts"] == []
    ids = {r["oracle_id"]: r["card_id"] for r in loaded_store.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot")}
    assert ids[OID["forest"]] == "card-forest-known"
    # a non-generated id is never silently overwritten
    report = apply_card_id_registry(loaded_store, {OID["plains"]: "card-other"})
    assert report["replaced"] == 0 and len(report["conflicts"]) == 1
    ids = {r["oracle_id"]: r["card_id"] for r in loaded_store.conn.execute(
        "SELECT oracle_id, card_id FROM physical_lot")}
    assert ids[OID["plains"]] == "card-plains-known"


def test_load_card_id_registry_csv(tmp_path):
    p = tmp_path / "reg.csv"
    p.write_text("oracle_id,card_id\noid-1,card-1\noid-2,card-2\n")
    assert load_card_id_registry(p) == {"oid-1": "card-1", "oid-2": "card-2"}


# ---------------------------------------------------------------------------
# P1.5 — several lots of one card at one location stay separate (+ migration)
# ---------------------------------------------------------------------------

def _two_lot_workbook(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "01_CARD_IDENTITY"
    ws.append(["card_id", "oracle_id", "oracle_name", "german_name", "color_identity",
               "mana_cost", "mana_value", "type_line", "oracle_text", "is_basic_land",
               "commander_legal", "legality_verified_at", "identity_evidence_type"])
    ws.append(["card-002", OID["sol_ring"], "Sol Ring (Test)", None, "",
               "{1}", 1, "Artifact", "{T}: Add {C}{C}.", False, True,
               "2026-11-09", "scryfall_name"])
    ws = wb.create_sheet("02_PHYSICAL_LOTS")
    ws.append(["physical_lot_id", "card_id", "quantity_observed", "quantity_lower_bound",
               "quantity_exact", "printing_ref", "condition", "location_id", "pool_status",
               "reserved_quantity", "reservation_target_id", "source_id", "verified_at", "note"])
    ws.append(["lot-a", "card-002", 3, 3, True, None, "NM", "loc-a", "available", 1,
               "opp-1", "src-1", "2026-11-09", None])
    ws.append(["lot-b", "card-002", 2, 2, True, None, "LP", "loc-a", "available", 0,
               None, "src-1", "2026-11-09", None])
    ws = wb.create_sheet("03_LOCATIONS")
    ws.append(["location_id", "location_name", "location_type", "ownership_semantics"])
    ws.append(["loc-a", "Box A", "box", "own"])
    ws = wb.create_sheet("05_INVENTORY_CURRENT")
    ws.append(["card_id", "observed_quantity", "physical_owned_quantity_lower_bound",
               "reserved_for_opponents_quantity", "available_for_own_decks_quantity_lower_bound",
               "quantity_exact", "quantity_semantics", "number_of_lots",
               "currently_available_for_own_decks", "last_verified_at"])
    ws.append(["card-002", 5, 5, 1, 4, True, "exact", 2, True, "2026-11-09"])
    wb.save(path)
    return path


def test_normalized_two_lots_same_card_same_location(loaded_store, tmp_path):
    path = _two_lot_workbook(tmp_path / "n2.xlsx")
    report = import_normalized_workbook(loaded_store, path, collection_id="multi-lot")
    assert report["lots"] == 2
    assert report["inventory_current_mismatches"] == []
    rows = loaded_store.conn.execute(
        "SELECT physical_lot_id, quantity, reserved_quantity, condition FROM physical_lot"
        " WHERE collection_id='multi-lot' ORDER BY physical_lot_id").fetchall()
    assert [(r["physical_lot_id"], r["quantity"], r["reserved_quantity"], r["condition"])
            for r in rows] == [("lot-a", 3, 1, "NM"), ("lot-b", 2, 0, "LP")]
    assert loaded_store.available_by_oracle("multi-lot")[OID["sol_ring"]] == 4


def test_schema_migration_from_v1(tmp_path):
    db = tmp_path / "v1.sqlite3"
    conn = sqlite3.connect(db)
    conn.executescript("""
    CREATE TABLE collection (collection_id TEXT PRIMARY KEY, title TEXT NOT NULL,
        source_id TEXT, created_at TEXT NOT NULL);
    CREATE TABLE physical_lot (
        physical_lot_id TEXT PRIMARY KEY,
        collection_id TEXT NOT NULL REFERENCES collection(collection_id),
        card_id TEXT, oracle_id TEXT NOT NULL, location_id TEXT NOT NULL,
        quantity INTEGER, quantity_exact INTEGER, quantity_lower_bound INTEGER,
        reserved_quantity INTEGER NOT NULL DEFAULT 0, reserved_assumption TEXT,
        condition TEXT, printing_ref TEXT, pool_status TEXT, note TEXT, source_id TEXT,
        UNIQUE (collection_id, oracle_id, location_id));
    CREATE TABLE deck (deck_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL,
        name TEXT NOT NULL, commander_oracle_ids TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE deck_revision (
        revision_id TEXT PRIMARY KEY, deck_id TEXT NOT NULL REFERENCES deck(deck_id),
        parent_revision_id TEXT, deck_hash TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
    INSERT INTO collection VALUES ('c1','T',NULL,'2026-01-01');
    INSERT INTO physical_lot VALUES ('lot-1','c1','card-x','oid-1','loc-a',3,1,3,0,NULL,NULL,NULL,NULL,NULL,NULL);
    INSERT INTO deck VALUES ('d1','c1','Alt','oid-1','2026-01-01');
    INSERT INTO deck_revision VALUES ('r1','d1',NULL,'hash','','2026-01-01');
    """)
    conn.commit()
    conn.close()
    store = Store(db)
    lot_cols = {r[1] for r in store.conn.execute("PRAGMA table_info(physical_lot)")}
    assert "lot_key" in lot_cols
    lot = store.conn.execute("SELECT * FROM physical_lot").fetchone()
    assert lot["physical_lot_id"] == "lot-1" and lot["quantity"] == 3 and lot["lot_key"] == ""
    rev = store.conn.execute("SELECT status FROM deck_revision WHERE revision_id='r1'").fetchone()
    assert rev["status"] == "draft"  # never retroactively claimed legal
    # widened uniqueness: a second, distinct lot of the same card+location works
    store.conn.execute(
        "INSERT INTO physical_lot(physical_lot_id,collection_id,card_id,oracle_id,"
        "location_id,lot_key,quantity) VALUES('lot-2','c1','card-x','oid-1','loc-a','lot-b',2)")
    store.conn.commit()
    assert store.conn.execute("SELECT COUNT(*) FROM physical_lot").fetchone()[0] == 2
    store.close()


# ---------------------------------------------------------------------------
# P1.6 — Partner with / Background / Doctor's companion
# ---------------------------------------------------------------------------

EXTRA_OID = {
    "pw_a": "20000000-0000-4000-8000-000000000001",
    "pw_b": "20000000-0000-4000-8000-000000000002",
    "pw_solo": "20000000-0000-4000-8000-000000000003",
    "companion": "20000000-0000-4000-8000-000000000004",
    "doctor": "20000000-0000-4000-8000-000000000005",
    "doctor_b": "20000000-0000-4000-8000-000000000006",
    "companion_b": "20000000-0000-4000-8000-000000000007",
}


def _extra_card(key, name, type_line, text, ci="U"):
    return {"id": f"printing-{key}", "oracle_id": EXTRA_OID[key], "name": name,
            "type_line": type_line, "oracle_text": text,
            "color_identity": list(ci), "colors": list(ci), "mana_cost": "{1}{U}",
            "cmc": 2.0, "layout": "normal", "legalities": {"commander": "legal"},
            "image_uris": {"normal": "https://example.invalid/img.jpg"}}


@pytest.fixture()
def pair_store(store, tmp_path):
    cards = synthetic_cards() + [
        _extra_card("pw_a", "Toothy, Test Friend", "Legendary Creature — Illusion",
                    "Partner with Pir, Test Rascal (When this creature enters, "
                    "target player may put Pir into their hand.)"),
        _extra_card("pw_b", "Pir, Test Rascal", "Legendary Creature — Human",
                    "Partner with Toothy, Test Friend (When this creature enters, "
                    "target player may put Toothy into their hand.)"),
        _extra_card("pw_solo", "Lonely, Test Legend", "Legendary Creature — Human",
                    "Partner with Absent, Test Card (reminder)"),
        _extra_card("companion", "Test Companion", "Legendary Creature — Human",
                    "Doctor's companion (You can have two commanders if one is a Doctor.)"),
        _extra_card("companion_b", "Second Companion", "Legendary Creature — Human",
                    "Doctor's companion (You can have two commanders if one is a Doctor.)"),
        _extra_card("doctor", "The Test Doctor", "Legendary Creature — Time Lord Doctor",
                    "Gallifrey stands!"),
        _extra_card("doctor_b", "The Other Doctor", "Legendary Creature — Time Lord Doctor",
                    "Allons-y!"),
    ]
    path = tmp_path / "cards.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in cards))
    import_scryfall(store, path)
    return store


def test_partner_with_is_not_free_partner():
    mech = pairing_mechanisms(
        "Partner with Pir, Test Rascal (When this creature enters, ...)",
        "Legendary Creature — Illusion")
    assert "partner_with" in mech and "partner" not in mech
    assert partner_with_target("Partner with Pir, Test Rascal (reminder)") == "Pir, Test Rascal"
    mech = pairing_mechanisms("Partner (You can have two commanders ...)",
                             "Legendary Creature — Elf")
    assert mech == ["partner"]


def test_pair_matrix(pair_store):
    ok = lambda a, b: _pair_legal(pair_store, [a, b])[0]  # noqa: E731
    # Partner with: mutual exact naming only
    assert ok(EXTRA_OID["pw_a"], EXTRA_OID["pw_b"])
    assert not ok(EXTRA_OID["pw_a"], OID["partner_a"])     # generic Partner is not enough
    assert not ok(EXTRA_OID["pw_solo"], EXTRA_OID["pw_b"])  # names someone else
    # free Partner still works both ways
    assert ok(OID["partner_a"], OID["partner_b"])
    # Choose a Background + Background subtype; wrong partner rejected
    assert ok(OID["choose_bg"], OID["background"])
    assert not ok(OID["choose_bg"], OID["partner_a"])
    # Doctor's companion: exactly one companion + a Time Lord Doctor
    assert ok(EXTRA_OID["companion"], EXTRA_OID["doctor"])
    assert not ok(EXTRA_OID["companion"], OID["partner_a"])
    assert not ok(EXTRA_OID["companion"], EXTRA_OID["companion_b"])
    assert not ok(EXTRA_OID["doctor"], EXTRA_OID["doctor_b"])


def test_partner_with_full_deck_validation(pair_store):
    # No collection needed for _pair_legal, but validate_deck checks
    # availability: use an empty collection -> pair verdict must still be
    # reported; assert on the pairing string + no pair error.
    verdict = validate_deck(pair_store, "empty-collection",
                            [EXTRA_OID["pw_a"], EXTRA_OID["pw_b"]],
                            {OID["island"]: 98})
    assert verdict["pairing"] == "Partner with"
    assert not any("pair" in e for e in verdict["errors"])


# ---------------------------------------------------------------------------
# P1.7 — strict quantities + update scenarios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_qty", [1.9, -1, "abc", "inf", "1,9"])
def test_invalid_quantities_rejected(loaded_store, tmp_path, bad_qty):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [("Plains", bad_qty, "Foundation")])
    with pytest.raises(ImportFailure) as exc:
        import_foundation_workbook(loaded_store, path)
    assert exc.value.report["errors"]
    assert loaded_store.conn.execute("SELECT COUNT(*) FROM physical_lot").fetchone()[0] == 0


def test_quantity_update_scenarios(loaded_store, tmp_path):
    v1 = write_foundation_xlsx(tmp_path / "v1.xlsx", [
        ("Plains", 60, "Foundation"), ("Sol Ring (Test)", 2, "Schwarze Box"),
        ("Forest", 10, "Schwarze Box")])
    import_foundation_workbook(loaded_store, v1)
    v2 = write_foundation_xlsx(tmp_path / "v2.xlsx", [
        ("Plains", 30, "Foundation"),            # decrease
        ("Sol Ring (Test)", 5, "Schwarze Box"),  # increase
        ("Forest", 10, "Mappe"),                 # new location
        ("Island", 7, "Foundation")])            # new card; Forest@Schwarze Box absent
    import_foundation_workbook(loaded_store, v2)
    avail = loaded_store.available_by_oracle(FC)
    assert avail[OID["plains"]] == 30
    assert avail[OID["sol_ring"]] == 5
    assert avail[OID["island"]] == 7
    # card missing from the new snapshot is kept (upsert never deletes)
    assert avail[OID["forest"]] == 20
    locs = {r["location_id"]: r["quantity"] for r in loaded_store.conn.execute(
        "SELECT location_id, quantity FROM physical_lot WHERE oracle_id=?",
        (OID["forest"],))}
    assert locs == {"Schwarze Box": 10, "Mappe": 10}


# ---------------------------------------------------------------------------
# P1.8 — empty Scryfall store: explicit start-order error
# ---------------------------------------------------------------------------

def test_import_with_empty_scryfall_store_message(store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [("Plains", 1, "Foundation")])
    with pytest.raises(ImportFailure) as exc:
        import_foundation_workbook(store, path)
    assert "import-scryfall" in exc.value.report["errors"][0]
    assert "sync-scryfall" in exc.value.report["errors"][0]
