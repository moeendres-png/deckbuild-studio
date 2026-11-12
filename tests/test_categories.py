"""Card categories: type-line parser, type-fact derivation, heuristic
rules v2, checked bookkeeping, Tagger sync (fake client — no network),
and the /api filter/sort surface.

Synthetic fixtures only — no private collection data, no live calls.
"""
from __future__ import annotations

import gzip
import json

import pytest
from fastapi.testclient import TestClient

from conftest import OID, synthetic_cards, write_foundation_xlsx
from deckbuild_studio import categories as cat_mod
from deckbuild_studio import roles as roles_mod
from deckbuild_studio import tagger as tagger_mod
from deckbuild_studio import web as web_mod
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.scryfall import import_scryfall
from deckbuild_studio.typeline import parse_type_line, split_faces

VAMPIRE_OID = "00000000-0000-4000-8000-000000000101"
WRATH_OID = "00000000-0000-4000-8000-000000000102"
SWORDS_OID = "00000000-0000-4000-8000-000000000103"


def _extra_cards() -> list[dict]:
    base = {"color_identity": [], "colors": [], "cmc": 1.0, "layout": "normal",
            "legalities": {"commander": "legal"},
            "image_uris": {"normal": "https://example.invalid/img.jpg"}}
    return [
        {**base, "id": "printing-vampire", "oracle_id": VAMPIRE_OID,
         "name": "Test Vampire Lord", "type_line": "Creature — Vampire Noble",
         "oracle_text": "Flying, lifelink", "mana_cost": "{3}{B}",
         "color_identity": ["B"], "keywords": ["Flying", "Lifelink"]},
        {**base, "id": "printing-wrath", "oracle_id": WRATH_OID,
         "name": "Test Wrath", "type_line": "Sorcery",
         "oracle_text": "Destroy all creatures.", "mana_cost": "{2}{W}{W}",
         "color_identity": ["W"], "keywords": []},
        {**base, "id": "printing-swords", "oracle_id": SWORDS_OID,
         "name": "Test Swords", "type_line": "Instant",
         "oracle_text": "Exile target creature. You gain life equal to its toughness.",
         "mana_cost": "{W}", "color_identity": ["W"], "keywords": []},
    ]


def _bulk_file(tmp_path, cards=None):
    cards = cards if cards is not None else synthetic_cards() + _extra_cards()
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "default-cards.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for card in cards:
            fh.write(json.dumps(card) + "\n")
    return path


@pytest.fixture()
def cat_store(store, tmp_path):
    """Store with Scryfall import + derived type facts + role rebuild."""
    bulk = _bulk_file(tmp_path)
    import_scryfall(store, bulk)
    result = cat_mod.derive_card_types(store, bulk_path=bulk)
    assert result["status"] == "AVAILABLE"
    roles_mod.rebuild_roles(store)
    return store


# --- type-line parser -----------------------------------------------------

def test_parse_type_line_core():
    p = parse_type_line("Legendary Creature — Angel")
    assert p == {"supertypes": ["Legendary"], "types": ["Creature"],
                 "subtypes": ["Angel"]}
    p = parse_type_line("Basic Land — Plains")
    assert p["supertypes"] == ["Basic"] and p["types"] == ["Land"]
    assert p["subtypes"] == ["Plains"]
    p = parse_type_line("Artifact")
    assert p["types"] == ["Artifact"] and p["subtypes"] == []
    p = parse_type_line("Creature — Human Werewolf")
    assert p["subtypes"] == ["Human", "Werewolf"]
    p = parse_type_line("Legendary Planeswalker — Jace")
    assert p["types"] == ["Planeswalker"] and p["subtypes"] == ["Jace"]
    p = parse_type_line("Snow Creature — Zombie")
    assert p["supertypes"] == ["Snow"]


def test_parse_type_line_lossless_and_empty():
    assert parse_type_line(None) == {"supertypes": [], "types": [], "subtypes": []}
    assert parse_type_line("") == {"supertypes": [], "types": [], "subtypes": []}
    # unknown left-of-dash tokens are kept as types, never dropped
    p = parse_type_line("Futuretype Creature — Elf")
    assert "Futuretype" in p["types"] and "Creature" in p["types"]
    assert split_faces("Instant // Instant") == ["Instant", "Instant"]
    assert split_faces("Artifact") == ["Artifact"]
    assert split_faces(None) == []


# --- derivation -------------------------------------------------------------

def test_derive_faces_keywords_and_filters(cat_store):
    info = cat_mod.card_type_info(cat_store, [OID["faithful"], VAMPIRE_OID])
    faithful = info[OID["faithful"]]
    assert [f["type_line"] for f in faithful["faces"]] == [
        "Creature — Human Soldier", "Legendary Creature — Spirit"]
    assert faithful["faces"][1]["supertypes"] == ["Legendary"]
    assert "Spirit" in faithful["subtypes"] and "Soldier" in faithful["subtypes"]
    vampire = info[VAMPIRE_OID]
    assert vampire["types"] == ["Creature"] and vampire["subtypes"] == ["Vampire", "Noble"]
    assert vampire["keywords"] == ["Flying", "Lifelink"]
    # any-face semantics: Spirit lives only on the back face
    assert cat_mod.filter_oracle_ids(cat_store, subtypes=["Spirit"]) == {OID["faithful"]}
    assert cat_mod.filter_oracle_ids(cat_store, types=["Artifact"]) == {OID["sol_ring"]}
    assert cat_mod.filter_oracle_ids(cat_store, keywords=["flying"]) == {VAMPIRE_OID}
    assert cat_mod.filter_oracle_ids(cat_store) is None
    facets = cat_mod.facet_counts(cat_store)
    assert facets["types"]["Creature"] >= 5 and facets["subtypes"]["Vampire"] == 1
    cov = cat_mod.type_coverage(cat_store)
    assert cov["with_faces"] == cov["universe"] and cov["with_types"] == cov["universe"]


def test_derive_fallback_without_bulk_is_partial(tmp_path):
    from deckbuild_studio.store import Store
    store = Store(tmp_path / "isolated" / "test.sqlite3")
    bulk = _bulk_file(tmp_path / "elsewhere")
    import_scryfall(store, bulk)
    result = cat_mod.derive_card_types(store)  # no bulk next to THIS database
    assert result["source"] == "db_fallback" and result["status"] == "PARTIAL"
    info = cat_mod.card_type_info(store, [OID["faithful"]])
    faces = info[OID["faithful"]]["faces"]
    assert len(faces) == 2 and faces[1]["subtypes"] == ["Spirit"]
    assert info[OID["faithful"]]["keywords"] == []  # honestly absent


# --- heuristic rules v2 ------------------------------------------------------

@pytest.mark.parametrize("text,types,expected", [
    ("Counter target noncreature spell.", "Instant", {"counterspell"}),
    ("Counter target instant or sorcery spell.", "Instant", {"counterspell"}),
    ("Sacrifice a creature: Draw a card.", "Enchantment",
     {"sacrifice_outlet", "card_draw"}),
    ("Spells your opponents cast cost {1} more to cast.", "Creature — Human",
     {"stax"}),
    ("Other creatures you control get +1/+1.", "Creature — Goblin", {"anthem"}),
    ("Target player mills two cards.", "Sorcery", {"mill"}),
    ("Target opponent discards two cards.", "Sorcery", {"discard"}),
    ("Scry 2.", "Instant", {"card_selection"}),
    ("Draw a card, then discard a card.", "Instant",
     {"card_draw", "card_selection"}),
    ("Create a Treasure token.", "Sorcery", {"token_production", "ramp"}),
    ("Create two 1/1 white Soldier creature tokens.", "Sorcery",
     {"token_production"}),
    ("Return all creatures to their owners' hands.", "Sorcery", {"board_wipe"}),
    ("Exile target creature. Return it to the battlefield under its owner's "
     "control at the beginning of the next end step.", "Instant", {"flicker"}),
    ("Destroy target nonland permanent.", "Instant", {"removal"}),
    ("Target creature fights target creature you don't control.", "Instant",
     {"removal"}),
])
def test_classify_v2_positive(text, types, expected):
    found = roles_mod.classify_text(text, types, 3.0)
    assert expected <= found, f"{text!r}: missing {expected - found}"


@pytest.mark.parametrize("text,types,forbidden", [
    # additional-cost sacrifice without a colon is not a free outlet
    ("As an additional cost to cast this spell, sacrifice a creature.",
     "Instant", {"sacrifice_outlet"}),
    ("Flying, vigilance", "Creature — Bird", {"stax", "anthem", "mill"}),
    ("Whenever you cast a Spirit spell, transform this creature.",
     "Creature — Human Soldier", {"tutor", "removal", "token_production"}),
])
def test_classify_v2_negative(text, types, forbidden):
    found = roles_mod.classify_text(text, types, 3.0)
    assert not (found & forbidden), f"{text!r}: unexpected {found & forbidden}"


def test_cantrip_needs_low_mana_value():
    text = "Draw a card, then discard a card."
    assert "cantrip" in roles_mod.classify_text(text, "Instant", 1.0)
    assert "cantrip" not in roles_mod.classify_text(text, "Instant", 3.0)


def test_classify_card_uses_all_faces():
    faces = [("First strike", "Creature — Human Werewolf"),
             ("Destroy target creature.", "Creature — Werewolf")]
    assert "removal" in roles_mod.classify_card(faces, 3.0)


def test_rebuild_records_checked_for_every_card(cat_store):
    rows = {r["oracle_id"]: r["claims"] for r in cat_store.conn.execute(
        "SELECT oracle_id, claims FROM card_category_check "
        "WHERE origin = ?", (roles_mod.ORIGIN_HEURISTIC,))}
    total = cat_store.conn.execute("SELECT COUNT(*) FROM scryfall_card").fetchone()[0]
    assert len(rows) == total
    # the rats carry no category but ARE recorded as examined with 0 claims
    assert rows[OID["rats"]] == 0
    assert rows[OID["sol_ring"]] >= 2  # mana_rock + ramp


# --- tagger sync (fake client) ------------------------------------------------

class FakeClient:
    def __init__(self, routes):
        self.routes = routes  # url -> (status, payload|None)
        self.calls = []

    def get_json(self, url):
        self.calls.append(url)
        status, payload = self.routes[url]
        return status, payload, json.dumps(payload or {}).encode()


def _page(ids, total=None, next_page=None):
    return {"object": "list", "total_cards": total if total is not None else len(ids),
            "has_more": next_page is not None, "next_page": next_page,
            "data": [{"oracle_id": i, "name": f"Card {i}"} for i in ids]}


def test_tagger_sync_paginates_and_intersects(cat_store):
    url1 = tagger_mod.search_url("ramp")
    url2 = url1 + "&page=2"
    client = FakeClient({
        url1: (200, _page([OID["sol_ring"], "outside-store-id"], total=3,
                          next_page=url2)),
        url2: (200, _page([OID["plains"]], total=3)),
    })
    result = tagger_mod.sync_tagger(cat_store, client=client, tags=["ramp"])
    tag = result["tags"]["ramp"]
    assert tag["status"] == "AVAILABLE" and tag["pages"] == 2
    assert tag["claims"] == 2  # outside-store id counted, not claimed
    assert result["checks_recorded"] is False  # subset run
    roles = roles_mod.card_roles(cat_store, OID["sol_ring"])
    assert roles["ramp"] == [roles_mod.ORIGIN_HEURISTIC, roles_mod.ORIGIN_TAGGER]
    snap = cat_store.conn.execute(
        "SELECT * FROM external_snapshot WHERE source_name='scryfall_tagger'").fetchone()
    assert snap["status"] == "AVAILABLE" and snap["displayed_total"] == 3
    assert snap["captured_count"] == 2 and snap["parser_version"] == tagger_mod.TAGGER_VERSION


def test_tagger_sync_not_found_and_blocked(cat_store):
    url = tagger_mod.search_url("stax")
    client = FakeClient({url: (404, {"object": "error", "details": "no match"})})
    result = tagger_mod.sync_tagger(cat_store, client=client, tags=["stax"])
    assert result["tags"]["stax"]["status"] == "NOT_FOUND"
    url2 = tagger_mod.search_url("mill")
    client2 = FakeClient({url2: (403, None)})
    result2 = tagger_mod.sync_tagger(cat_store, client=client2, tags=["mill"])
    assert result2["tags"]["mill"]["status"] == "BLOCKED"
    assert cat_store.conn.execute(
        "SELECT COUNT(*) FROM card_tagger_claim").fetchone()[0] == 0


def test_tagger_partial_keeps_previous_claims(cat_store):
    url = tagger_mod.search_url("bounce")
    good = FakeClient({url: (200, _page([OID["sol_ring"]]))})
    tagger_mod.sync_tagger(cat_store, client=good, tags=["bounce"])
    assert cat_store.conn.execute(
        "SELECT COUNT(*) FROM card_tagger_claim WHERE tag='bounce'").fetchone()[0] == 1
    url_p2 = url + "&page=2"
    flaky = FakeClient({
        url: (200, _page([OID["plains"]], total=2, next_page=url_p2)),
        url_p2: (500, None),
    })
    result = tagger_mod.sync_tagger(cat_store, client=flaky, tags=["bounce"],
                                    force=True)
    assert result["tags"]["bounce"]["status"] == "PARTIAL"
    # previous claims survive a partial re-sync untouched
    rows = cat_store.conn.execute(
        "SELECT oracle_id FROM card_tagger_claim WHERE tag='bounce'").fetchall()
    assert [r["oracle_id"] for r in rows] == [OID["sol_ring"]]


def test_tagger_reuses_current_snapshot_without_force(cat_store):
    url = tagger_mod.search_url("ramp")
    client = FakeClient({url: (200, _page([OID["sol_ring"]]))})
    tagger_mod.sync_tagger(cat_store, client=client, tags=["ramp"])

    class ExplodingClient:
        def get_json(self, url):
            raise AssertionError("must not fetch when a snapshot is reused")

    result = tagger_mod.sync_tagger(cat_store, client=ExplodingClient(),
                                    tags=["ramp"])
    assert result["tags"]["ramp"]["status"] == "AVAILABLE"
    assert result["tags"]["ramp"]["pages"] == 0
    assert roles_mod.card_roles(cat_store, OID["sol_ring"])["ramp"] == [
        roles_mod.ORIGIN_HEURISTIC, roles_mod.ORIGIN_TAGGER]


def test_tagger_full_run_records_checks(cat_store, monkeypatch):
    monkeypatch.setattr(tagger_mod, "VOCABULARY", {"ramp": "ramp"})
    url = tagger_mod.search_url("ramp")
    client = FakeClient({url: (200, _page([OID["sol_ring"]]))})
    result = tagger_mod.sync_tagger(cat_store, client=client)
    assert result["run_status"] == "AVAILABLE" and result["checks_recorded"] is True
    checked = cat_store.conn.execute(
        "SELECT COUNT(*) FROM card_category_check WHERE origin = ?",
        (roles_mod.ORIGIN_TAGGER,)).fetchone()[0]
    total = cat_store.conn.execute("SELECT COUNT(*) FROM scryfall_card").fetchone()[0]
    assert checked == total
    # a later roles rebuild keeps the tagger claims (mirror source intact)
    roles_mod.rebuild_roles(cat_store)
    assert roles_mod.card_roles(cat_store, OID["sol_ring"])["ramp"] == [
        roles_mod.ORIGIN_HEURISTIC, roles_mod.ORIGIN_TAGGER]


# --- API: filters / sorting / categories endpoint ------------------------------

@pytest.fixture()
def client(cat_store, tmp_path, monkeypatch):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [
        ("Alara, Test Sovereign", 1, "Foundation"),
        ("Sol Ring (Test)", 4, "Foundation"),
        ("Faithful Squire // Kaiso, Memory of Loyalty", 1, "Foundation"),
        ("Plains", 60, "Foundation"), ("Forest", 60, "Foundation")])
    import_foundation_workbook(cat_store, path)
    monkeypatch.setattr(web_mod, "database_path", lambda: cat_store.path)
    return TestClient(web_mod.create_app())


def test_api_cards_type_subtype_keyword_filters(client):
    cards = client.get("/api/cards", params={
        "collection_id": FC, "type": "Artifact"}).json()
    assert [c["name"] for c in cards] == ["Sol Ring (Test)"]
    assert cards[0]["type_info"]["types"] == ["Artifact"]
    # subtype on the BACK face of a DFC still matches (any-face)
    cards = client.get("/api/cards", params={
        "collection_id": FC, "subtype": "Spirit"}).json()
    assert [c["name"] for c in cards] == [
        "Faithful Squire // Kaiso, Memory of Loyalty"]
    cards = client.get("/api/cards", params={
        "collection_id": FC, "type": "Creature", "subtype": "Human"}).json()
    assert {c["name"] for c in cards} == {
        "Alara, Test Sovereign", "Faithful Squire // Kaiso, Memory of Loyalty"}


def test_api_cards_category_filter_and_sort(client):
    cards = client.get("/api/cards", params={
        "collection_id": FC, "category": "mana_rock"}).json()
    assert [c["name"] for c in cards] == ["Sol Ring (Test)"]
    cards = client.get("/api/cards", params={
        "collection_id": FC, "category": "mana_rock",
        "category_origin": roles_mod.ORIGIN_TAGGER}).json()
    assert cards == []  # no tagger sync in this fixture — honest empty
    names = [c["name"] for c in client.get("/api/cards", params={
        "collection_id": FC, "sort": "name"}).json()]
    assert names == sorted(names)
    by_type = client.get("/api/cards", params={
        "collection_id": FC, "sort": "type"}).json()
    kinds = [c["type_info"]["types"][0] if c["type_info"]["types"] else "?"
             for c in by_type]
    assert kinds.index("Creature") < kinds.index("Land")


def test_api_categories_endpoint(client):
    data = client.get("/api/categories", params={"collection_id": FC}).json()
    assert data["universe_identities"] == 5
    assert data["type_layer"]["with_faces"] == 5
    assert data["taxonomy"]["sacrifice_outlet"] == "sacrifice-outlet"
    assert data["layers"][roles_mod.ORIGIN_HEURISTIC]["checked"] == 5
    assert data["facets"]["types"]["Creature"] == 2
    assert data["by_category"]["mana_rock"][roles_mod.ORIGIN_HEURISTIC] == 1


def test_api_pool_subtype_filter_and_validate_groups(client):
    pool = client.get("/api/pool", params={
        "collection_id": FC, "commander": OID["commander_a"],
        "subtype": "Soldier"}).json()
    assert [c["name"] for c in pool] == [
        "Faithful Squire // Kaiso, Memory of Loyalty"]
    resp = client.post("/api/decks/validate", json={
        "collection_id": FC, "name": "Entwurf",
        "commander_oracle_ids": [OID["commander_a"]],
        "entries": {OID["sol_ring"]: 1, OID["plains"]: 30}})
    groups = resp.json()["role_groups"]
    assert groups["ramp"] == [{"oracle_id": OID["sol_ring"], "quantity": 1}]
    # commander (no category) and plains share the honest "none" group
    assert {(g["oracle_id"], g["quantity"]) for g in groups["none"]} == {
        (OID["plains"], 30), (OID["commander_a"], 1)}
