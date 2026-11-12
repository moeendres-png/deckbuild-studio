"""Feature parity with the upstream studio (BUILD): roles, image cache,
own-deck inclusion, deck shape/draw odds, counts-only data report.

Synthetic fixtures only — downloads are monkeypatched, no network.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from conftest import OID
from deckbuild_studio import images as images_mod
from deckbuild_studio import roles as roles_mod
from deckbuild_studio import web as web_mod
from deckbuild_studio.decks import create_deck
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.queries import (deck_shape, draw_probabilities,
                                       own_deck_inclusion)
from deckbuild_studio.reference import import_role_profiles
from deckbuild_studio.report import data_report, role_fingerprint

from conftest import write_foundation_xlsx


# --- roles ---------------------------------------------------------------

def test_classify_text_core_roles():
    sol = roles_mod.classify_text("{T}: Add {C}{C}.", "Artifact", 1.0)
    assert {"mana_rock", "ramp"} <= sol
    counter = roles_mod.classify_text("Counter target spell.", "Instant", 2.0)
    assert counter == {"counterspell", "cantrip"} or "counterspell" in counter
    # taxonomy 1.1.0 / heuristic 2.2.0: the bare keyword line is now
    # an evasion claim (before 1.1.0 this asserted == set())
    assert roles_mod.classify_text("Flying", "Creature — Bird", 3.0) == {"evasion"}
    wipe = roles_mod.classify_text("Destroy all creatures.", "Sorcery", 5.0)
    assert "board_wipe" in wipe
    tutor = roles_mod.classify_text(
        "Search your library for a card, put it into your hand.",
        "Sorcery", 2.0)
    assert "tutor" in tutor and "land_ramp" not in tutor
    land = roles_mod.classify_text(
        "Search your library for a basic land card, put it onto the "
        "battlefield tapped.", "Sorcery", 2.0)
    assert {"land_ramp", "ramp"} <= land


def test_rebuild_roles_and_profile_merge(loaded_store, tmp_path):
    roles_mod.rebuild_roles(loaded_store)
    sol = roles_mod.card_roles(loaded_store, OID["sol_ring"])
    assert sol.get("mana_rock") == [roles_mod.ORIGIN_HEURISTIC]
    # profile import adds verbatim estimate roles on top
    data = {"schema_version": "0.4.0",
            "estimate_type": "structural_model_estimates",
            "data_as_of": "2026-08-09", "source_hash": "cafe1234",
            "profiles": [{"oracle_name": "Sol Ring (Test)",
                          "roles": ["ramp", "engine"],
                          "role_strengths": {"ramp": 1.0},
                          "mechanic_tags": [], "color_requirements": {},
                          "color_identity": [], "is_land": False}]}
    path = tmp_path / "roles.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    import_role_profiles(loaded_store, path)
    roles_mod.rebuild_roles(loaded_store)
    sol = roles_mod.card_roles(loaded_store, OID["sol_ring"])
    assert sol["ramp"] == [roles_mod.ORIGIN_HEURISTIC, roles_mod.ORIGIN_PROFILE]
    assert sol["engine"] == [roles_mod.ORIGIN_PROFILE]
    counts = roles_mod.deck_role_counts(
        loaded_store, {OID["sol_ring"]: 1, OID["offcolor"]: 1})
    assert counts["mana_rock"] == 1 and counts["counterspell"] == 1


# --- images ---------------------------------------------------------------

def test_image_cache_host_guard_and_roundtrip(loaded_store, monkeypatch):
    assert images_mod._download("https://evil.example/x.jpg") is None
    assert images_mod._download("http://cards.scryfall.io/x.jpg") is None
    monkeypatch.setattr(images_mod, "_download",
                        lambda addr: b"\xff\xd8fake-jpeg")
    path = images_mod.cached_image(loaded_store, OID["sol_ring"])
    assert path is not None and path.read_bytes() == b"\xff\xd8fake-jpeg"
    # second call serves from disk without downloading again
    monkeypatch.setattr(images_mod, "_download",
                        lambda addr: pytest.fail("must not download twice"))
    assert images_mod.cached_image(loaded_store, OID["sol_ring"]) == path
    status = images_mod.cache_status(loaded_store, [OID["sol_ring"]])
    assert status["requested_cached"] == 1


def test_fetch_images_counts(loaded_store, monkeypatch):
    monkeypatch.setattr(images_mod, "_download", lambda addr: b"img")
    result = images_mod.fetch_images(
        loaded_store, [OID["sol_ring"], "no-such-oracle"], pause=0)
    assert result == {"cached": 0, "fetched": 1, "missing": 1}
    again = images_mod.fetch_images(loaded_store, [OID["sol_ring"]], pause=0)
    assert again["cached"] == 1


# --- inclusion / shape / draw odds ---------------------------------------

def _collection_with_decks(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [
        ("Alara, Test Sovereign", 1, "Foundation"),
        ("Sol Ring (Test)", 4, "Foundation"), ("Plains", 60, "Foundation"),
        ("Forest", 60, "Foundation")])
    import_foundation_workbook(loaded_store, path)
    entries = {OID["sol_ring"]: 1, OID["plains"]: 30, OID["forest"]: 20}
    create_deck(loaded_store, FC, "Deck Eins", [OID["commander_a"]], entries)
    # second deck: an older revision with the ring, superseded by one without
    d2 = create_deck(loaded_store, FC, "Deck Zwei", [OID["commander_a"]],
                     entries)
    create_deck(loaded_store, FC, "Deck Zwei", [OID["commander_a"]],
                {OID["plains"]: 40, OID["forest"]: 20},
                parent_revision_id=d2["revision_id"])
    return loaded_store


def test_own_deck_inclusion_latest_revision_only(loaded_store, tmp_path):
    _collection_with_decks(loaded_store, tmp_path)
    result = own_deck_inclusion(loaded_store, FC)
    assert result["decks_total"] == 2
    by_name = {c["name"]: c for c in result["cards"]}
    # ring is in deck 1 only — deck 2's latest revision dropped it
    assert by_name["Sol Ring (Test)"]["decks"] == 1
    assert by_name["Sol Ring (Test)"]["share"] == 0.5
    assert by_name["Plains"]["decks"] == 2


def test_deck_shape_and_draw_probabilities(loaded_store, tmp_path):
    _collection_with_decks(loaded_store, tmp_path)
    shape = deck_shape(loaded_store, {OID["plains"]: 30, OID["sol_ring"]: 1,
                                      OID["commander_a"]: 1})
    assert shape["lands"] == 30 and shape["total_cards"] == 32
    assert shape["types"]["Land"] == 30 and shape["types"]["Artifact"] == 1
    probs = draw_probabilities(100, 36)
    opening = probs["opening_hand"]
    assert opening["at_least_1"] > opening["at_least_4"] > 0
    assert 0.75 < opening["at_least_2"] < 0.82  # exact value: 0.7926
    assert draw_probabilities(0, 0)["opening_hand"] is None


# --- data report -----------------------------------------------------------

def test_data_report_counts_only(loaded_store, tmp_path):
    _collection_with_decks(loaded_store, tmp_path)
    roles_mod.rebuild_roles(loaded_store)
    report = data_report(loaded_store)
    assert report["schema"] == "deckbuild-data-report-1"
    col = report["collections"][0]
    assert col["collection_id"] == FC and col["decks"] == 2
    assert report["decks"] == {"decks": 2, "revisions": 3}
    assert report["roles"]["cards_with_roles"] > 0
    assert report["roles"]["fingerprint"] == role_fingerprint(loaded_store)
    assert report["scryfall"]["commander_legal"]["of"] > 0
    text = json.dumps(report)
    assert "Sol Ring" not in text and "Deck Eins" not in text  # counts only


# --- web -------------------------------------------------------------------

@pytest.fixture()
def client(loaded_store, tmp_path, monkeypatch):
    _collection_with_decks(loaded_store, tmp_path)
    roles_mod.rebuild_roles(loaded_store)
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_web_roles_and_pool_filter(client):
    data = client.get("/api/roles", params={"collection_id": FC}).json()
    assert data["by_role"]["mana_rock"] == 1
    assert data["labels_de"]["mana_rock"] == "Mana Rock"
    pool = client.get("/api/pool", params={
        "collection_id": FC, "commander": OID["commander_a"],
        "role": "mana_rock"}).json()
    assert [c["name"] for c in pool] == ["Sol Ring (Test)"]
    assert pool[0]["roles"]["mana_rock"] == [roles_mod.ORIGIN_HEURISTIC]


def test_web_data_report_and_inclusion(client):
    report = client.get("/api/data-report").json()
    assert report["schema"] == "deckbuild-data-report-1"
    inc = client.get("/api/stats/inclusion",
                     params={"collection_id": FC}).json()
    assert inc["decks_total"] == 2


def test_web_img_route(client, monkeypatch):
    monkeypatch.setattr(images_mod, "_download", lambda addr: b"\xff\xd8img")
    resp = client.get(f"/img/{OID['sol_ring']}")
    assert resp.status_code == 200 and resp.content == b"\xff\xd8img"
    assert client.get("/img/unknown-oracle").status_code == 404


def test_web_deck_list(client):
    decks = client.get("/api/decks", params={"collection_id": FC}).json()
    assert {d["name"] for d in decks} == {"Deck Eins", "Deck Zwei"}
    zwei = next(d for d in decks if d["name"] == "Deck Zwei")
    assert zwei["revisions"] == 2 and zwei["latest_revision_id"]


def test_web_validate_includes_shape_and_roles(client):
    resp = client.post("/api/decks/validate", json={
        "collection_id": FC, "name": "Entwurf",
        "commander_oracle_ids": [OID["commander_a"]],
        "entries": {OID["sol_ring"]: 1, OID["plains"]: 30}})
    body = resp.json()
    assert body["shape"]["lands"] == 30
    assert body["roles"]["mana_rock"] == 1
    assert body["draw_probabilities"]["opening_hand"]["at_least_2"] is not None
