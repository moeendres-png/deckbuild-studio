"""Independent, synthetic acceptance tests; no user inventory or private snapshots.
These checks are intentionally red until Muse fixes the corresponding contracts.
Run: python -m pytest -q qa/test_acceptance_edges.py
"""
import csv
import json

import pytest

from deckbuild_studio.decks import _pair_legal, create_deck, validate_deck
from deckbuild_studio.edhrec import parse_stats_page
from deckbuild_studio.importers import ImportFailure, import_mapped_file
from deckbuild_studio.scryfall import import_scryfall
from deckbuild_studio.store import Store

OIDS = {key: f"00000000-0000-4000-8000-{n:012d}" for n, key in enumerate(
    ["owned", "unowned", "plains", "a", "b"], 1)}


def _card(key, name, type_line, text="", color=""):
    return {"object": "card", "id": f"synthetic-{key}",
            "oracle_id": OIDS[key], "name": name, "type_line": type_line,
            "oracle_text": text, "color_identity": list(color), "colors": list(color),
            "legalities": {"commander": "legal"}, "layout": "normal",
            "cmc": 1, "mana_cost": "{1}", "games": ["paper"]}


@pytest.fixture
def db(tmp_path):
    s = Store(tmp_path / "independent-qa.sqlite3")
    cards = [
        _card("owned", "QA Owned Commander", "Legendary Creature — Wizard"),
        _card("unowned", "QA Unowned Commander", "Legendary Creature — Wizard"),
        _card("plains", "Plains", "Basic Land — Plains"),
        _card("a", "QA Alice", "Legendary Creature — Elf", "Partner with QA Bob"),
        _card("b", "QA Carol", "Legendary Creature — Dwarf", "Partner with QA Dan"),
    ]
    file = tmp_path / "scryfall.json"
    file.write_text(json.dumps(cards), encoding="utf-8")
    import_scryfall(s, file)
    yield s
    s.close()


def _import(s, tmp_path, collection, rows):
    file = tmp_path / f"{collection}.csv"
    with file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Name", "Menge", "Box"])
        writer.writerows(rows)
    return import_mapped_file(s, file, {
        "collection_id": collection,
        "columns": {"name": "Name", "quantity": "Menge", "location": "Box",
                    "reserved": None, "condition": None},
    })


def test_commander_must_be_physically_owned(db, tmp_path):
    """P0: a valid-looking 100-card deck cannot use an unowned commander."""
    _import(db, tmp_path, "qa-one", [("Plains", 99, "Box A")])
    result = validate_deck(db, "qa-one", [OIDS["unowned"]], {OIDS["plains"]: 99})
    assert not result["valid"], "Unowned commander must be rejected"
    assert any("availab" in x.lower() or "owned" in x.lower() for x in result["errors"])


def test_existing_card_id_survives_simple_import(db, tmp_path):
    """P1: an already normalized Oracle identity keeps its local card_id."""
    db.conn.execute("INSERT INTO card_identity(card_id,oracle_id) VALUES(?,?)",
                    ("card-existing-001", OIDS["plains"]))
    db.conn.commit()
    _import(db, tmp_path, "qa-two", [("Plains", 1, "Box A")])
    lot = db.conn.execute(
        "SELECT card_id FROM physical_lot WHERE collection_id='qa-two'").fetchone()
    assert lot["card_id"] == "card-existing-001"


@pytest.mark.parametrize("bad", ["-2", "1.7", "NaN", "Infinity"])
def test_invalid_quantities_rejected_atomically(db, tmp_path, bad):
    """P1: no negative, fractional, NaN or infinite stock numbers."""
    with pytest.raises(ImportFailure):
        _import(db, tmp_path, "qa-quantities", [("Plains", bad, "Box A")])
    count = db.conn.execute(
        "SELECT COUNT(*) FROM physical_lot WHERE collection_id='qa-quantities'").fetchone()[0]
    assert count == 0


def test_partner_with_cannot_pair_arbitrary_cards(db):
    """P1: Partner with X does not grant generic Partner."""
    ok, _ = _pair_legal(db, [OIDS["a"], OIDS["b"]])
    assert not ok, "QA Alice partners with QA Bob, not QA Carol"


def test_distinct_normalized_lots_same_location_are_allowed(db):
    """P1: independent physical lots must survive at the same location."""
    db.conn.execute("INSERT INTO collection(collection_id,title,created_at) VALUES(?,?,?)",
                    ("qa-lots", "QA Lots", "2026-11-11T00:00:00Z"))
    for lot in ["lot-A", "lot-B"]:
        db.conn.execute(
            "INSERT INTO physical_lot(physical_lot_id,collection_id,oracle_id,"
            "location_id,quantity) VALUES(?,?,?,?,?)",
            (lot, "qa-lots", OIDS["plains"], "Box A", 1))
    assert db.conn.execute(
        "SELECT COUNT(*) FROM physical_lot WHERE collection_id='qa-lots'").fetchone()[0] == 2


def test_revision_cannot_silently_change_collection(db, tmp_path):
    """P1: cross-collection parent revision must be rejected or isolated."""
    rows = [("QA Owned Commander", 1, "A"), ("Plains", 99, "A")]
    _import(db, tmp_path, "qa-alpha", rows)
    _import(db, tmp_path, "qa-beta", rows)
    first = create_deck(db, "qa-alpha", "Original", [OIDS["owned"]],
                        {OIDS["plains"]: 99})
    try:
        second = create_deck(db, "qa-beta", "Invalid re-parent", [OIDS["owned"]],
                             {OIDS["plains"]: 99},
                             parent_revision_id=first["revision_id"])
    except (ValueError, LookupError):
        return
    assert second["deck_id"] != first["deck_id"], (
        "A revision from qa-beta must not be attached to a qa-alpha deck")


def test_edhrec_fraction_disagreement_is_never_silent():
    """P1: inclusion must match numerator/denominator or carry quality warning."""
    rec = {"name": "QA Example Card", "category": "creatures",
           "cardId": "qa-example-card", "numDecks": 5,
           "potentialDecks": 10, "inclusion": 0.9, "synergy": 0.1, "lift": 0.2}
    html = ('"gallery":' + json.dumps({"recs": [rec], "categories": []}) +
            ' "featured":' + json.dumps({"rec": {"name": "QA Commander",
                                                  "cardId": "qa-commander"}}) +
            ' "optionsFilters":' + json.dumps({"brackets": [{"bracket": "core",
                                                             "count": 10}]}))
    parsed = parse_stats_page(html, expected_name="QA Commander",
                              expected_slug="qa-commander", bracket="core")
    assert not parsed["cards"] or parsed.get("quality_warnings") or parsed["dropped_invalid"], (
        "90% inclusion contradicts 5/10 = 50%; cannot be stored as unflagged fact")
