import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio.commander import commander_candidates
from deckbuild_studio.decks import (
    compare_revisions,
    create_deck,
    export_revision,
    legal_pool,
    validate_deck,
)
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook


@pytest.fixture()
def collection(loaded_store, tmp_path):
    rows = [("Alara, Test Sovereign", 1, "Foundation"),
            ("Partner Alpha", 1, "Foundation"),
            ("Partner Beta", 1, "Foundation"),
            ("Faithful Squire // Kaiso, Memory of Loyalty", 1, "Schwarze Box"),
            ("Test Planeswalker", 1, "Foundation"),
            ("Will, Test Commander", 1, "Foundation"),
            ("Noble Heritage (Test)", 1, "Foundation"),
            ("Candlekeep Sage (Test)", 1, "Foundation"),
            ("Banned Legend", 1, "Foundation"),
            ("Plains", 60, "Foundation"),
            ("Forest", 120, "Schwarze Box"),
            ("Island", 60, "Schwarze Box"),
            ("Sol Ring (Test)", 2, "Schwarze Box"),
            ("Blue Spell (Test)", 1, "Foundation"),
            ("Relentless Test Rats", 40, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


def test_commander_candidates_exact_set(collection):
    result = commander_candidates(collection, FC)
    names = {c["name"] for c in result["eligible"]}
    assert names == {"Alara, Test Sovereign", "Will, Test Commander",
                     "Partner Alpha", "Partner Beta", "Candlekeep Sage (Test)"}
    assert result["needs_review"] == []


def test_faithful_squire_not_a_commander(collection):
    result = commander_candidates(collection, FC)
    assert all(c["oracle_id"] != OID["faithful"] for c in result["eligible"])


def test_planeswalker_without_permission_not_a_commander(collection):
    result = commander_candidates(collection, FC)
    assert all(c["oracle_id"] != OID["planeswalker"] for c in result["eligible"])
    assert all(c["oracle_id"] != OID["banned"] for c in result["eligible"])
    assert all(c["oracle_id"] != OID["background"] for c in result["eligible"])


def test_partner_pairing_recorded(collection):
    result = commander_candidates(collection, FC)
    alpha = next(c for c in result["eligible"] if c["name"] == "Partner Alpha")
    assert "partner" in alpha["pairing"]


def test_legal_deck_100_with_basics(collection):
    entries = {OID["plains"]: 50, OID["forest"]: 49}
    verdict = validate_deck(collection, FC, [OID["commander_a"]], entries)
    assert verdict["valid"], verdict["errors"]


def test_deck_size_enforced(collection):
    verdict = validate_deck(collection, FC, [OID["commander_a"]], {OID["plains"]: 10})
    assert not verdict["valid"]
    assert any("!= 100" in e for e in verdict["errors"])


def test_singleton_violation_and_exception(collection):
    entries = {OID["plains"]: 97, OID["sol_ring"]: 2}
    verdict = validate_deck(collection, FC, [OID["commander_a"]], entries)
    assert not verdict["valid"]
    assert any("singleton" in e for e in verdict["errors"])
    # any-number exception: rats may repeat (needs B in identity -> use banned-free check
    # via commander_a? rats are B, outside GW identity, so they must fail on color, not singleton)
    entries = {OID["rats"]: 40, OID["plains"]: 59}
    verdict = validate_deck(collection, FC, [OID["commander_a"]], entries)
    assert not any("singleton" in e for e in verdict["errors"])


def test_color_identity_violation(collection):
    entries = {OID["plains"]: 98, OID["offcolor"]: 1}
    verdict = validate_deck(collection, FC, [OID["commander_a"]], entries)
    assert not verdict["valid"]
    assert any("color identity" in e for e in verdict["errors"])


def test_availability_violation(collection):
    entries = {OID["plains"]: 61, OID["forest"]: 38}  # only 60 Plains available
    verdict = validate_deck(collection, FC, [OID["commander_a"]], entries)
    assert not verdict["valid"]
    assert any("exceed available" in e for e in verdict["errors"])


def test_banned_card_rejected_in_deck(collection):
    verdict = validate_deck(collection, FC, [OID["banned"]], {OID["plains"]: 99})
    assert not verdict["valid"]


def test_partner_pair_deck(collection):
    # Partner Alpha (G) + Partner Beta (R): pool identity G+R; fill with
    # Forests (G) — legal; size = 2 commanders + 98.
    verdict = validate_deck(collection, FC,
                            [OID["partner_a"], OID["partner_b"]],
                            {OID["forest"]: 98})
    assert verdict["valid"], verdict["errors"]
    assert verdict["pairing"] == "Partner"


def test_unpaired_double_commander_rejected(collection):
    verdict = validate_deck(collection, FC,
                            [OID["commander_a"], OID["partner_a"]],
                            {OID["forest"]: 98})
    assert not verdict["valid"]


def test_deck_revision_variant_compare_export(collection):
    entries = {OID["plains"]: 50, OID["forest"]: 49}
    first = create_deck(collection, FC, "Test Deck", [OID["commander_a"]], entries)
    assert first["validation"]["valid"]
    entries2 = {OID["plains"]: 49, OID["forest"]: 49, OID["sol_ring"]: 1}
    second = create_deck(collection, FC, "Test Deck", [OID["commander_a"]], entries2,
                         parent_revision_id=first["revision_id"])
    diff = compare_revisions(collection, first["revision_id"], second["revision_id"])
    assert OID["sol_ring"] in diff["added"]
    text = export_revision(collection, second["revision_id"])
    assert "Alara, Test Sovereign" in text and "(Commander)" in text


def test_legal_pool_follows_color_identity(collection):
    pool = legal_pool(collection, FC, [OID["commander_a"]])
    names = {p["name"] for p in pool}
    assert "Blue Spell (Test)" not in names
    assert "Plains" in names and "Sol Ring (Test)" in names
    assert "Banned Legend" not in names
