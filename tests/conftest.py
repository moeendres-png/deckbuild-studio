"""Synthetic fixtures only — no private collection data in tests."""
from __future__ import annotations

import gzip
import json

import pytest
from openpyxl import Workbook

from deckbuild_studio.store import Store

# oracle ids (synthetic, stable)
OID = {
    "commander_a": "00000000-0000-4000-8000-000000000001",
    "faithful": "00000000-0000-4000-8000-000000000002",
    "planeswalker": "00000000-0000-4000-8000-000000000003",
    "pw_commander": "00000000-0000-4000-8000-000000000004",
    "partner_a": "00000000-0000-4000-8000-000000000005",
    "partner_b": "00000000-0000-4000-8000-000000000006",
    "background": "00000000-0000-4000-8000-000000000007",
    "choose_bg": "00000000-0000-4000-8000-000000000008",
    "banned": "00000000-0000-4000-8000-000000000009",
    "plains": "00000000-0000-4000-8000-000000000010",
    "forest": "00000000-0000-4000-8000-000000000011",
    "sol_ring": "00000000-0000-4000-8000-000000000012",
    "offcolor": "00000000-0000-4000-8000-000000000013",
    "rats": "00000000-0000-4000-8000-000000000014",
    "island": "00000000-0000-4000-8000-000000000015",
}


def _card(oid_key, name, type_line, *, ci="", oracle_text="", legality="legal",
          layout="normal", faces=None, mana_cost="{1}"):
    card = {
        "id": f"printing-{oid_key}", "oracle_id": OID[oid_key], "name": name,
        "type_line": type_line, "oracle_text": oracle_text,
        "color_identity": list(ci), "colors": list(ci), "mana_cost": mana_cost,
        "cmc": 1.0, "layout": layout, "legalities": {"commander": legality},
        "image_uris": {"normal": "https://example.invalid/img.jpg"},
    }
    if faces:
        card["card_faces"] = faces
    return card


def synthetic_cards() -> list[dict]:
    return [
        _card("commander_a", "Alara, Test Sovereign", "Legendary Creature — Human Noble",
              ci="GW", oracle_text="Vigilance"),
        _card("faithful", "Faithful Squire // Kaiso, Memory of Loyalty",
              "Creature — Human Soldier // Legendary Creature — Spirit",
              ci="W", layout="transform",
              faces=[
                  {"name": "Faithful Squire", "type_line": "Creature — Human Soldier",
                   "oracle_text": "Whenever you cast a Spirit spell, transform."},
                  {"name": "Kaiso, Memory of Loyalty",
                   "type_line": "Legendary Creature — Spirit",
                   "oracle_text": "Flying"}]),
        _card("planeswalker", "Test Planeswalker", "Legendary Planeswalker — Test",
              ci="U", oracle_text="+1: Draw a card."),
        _card("pw_commander", "Will, Test Commander", "Legendary Planeswalker — Will",
              ci="R", oracle_text="Will, Test Commander can be your commander."),
        _card("partner_a", "Partner Alpha", "Legendary Creature — Elf",
              ci="G", oracle_text="Partner (You can have two commanders if both have partner.)"),
        _card("partner_b", "Partner Beta", "Legendary Creature — Dwarf",
              ci="R", oracle_text="Partner (You can have two commanders if both have partner.)"),
        _card("background", "Noble Heritage (Test)", "Legendary Enchantment — Background",
              ci="W", oracle_text="Commander creatures you own have lifelink."),
        _card("choose_bg", "Candlekeep Sage (Test)", "Legendary Creature — Human Wizard",
              ci="U", oracle_text="Choose a Background (You can have a Background as a second commander.)"),
        _card("banned", "Banned Legend", "Legendary Creature — Demon",
              ci="B", legality="banned"),
        _card("plains", "Plains", "Basic Land — Plains", mana_cost=""),
        _card("forest", "Forest", "Basic Land — Forest", mana_cost=""),
        _card("island", "Island", "Basic Land — Island", ci="U", mana_cost=""),
        _card("sol_ring", "Sol Ring (Test)", "Artifact", mana_cost="{1}",
              oracle_text="{T}: Add {C}{C}."),
        _card("offcolor", "Blue Spell (Test)", "Instant", ci="U",
              oracle_text="Counter target spell."),
        _card("rats", "Relentless Test Rats", "Creature — Rat", ci="B",
              oracle_text="A deck can have any number of cards named Relentless Test Rats."),
    ]


NAMES = {c["name"]: c for c in synthetic_cards()}


@pytest.fixture()
def store(tmp_path):
    return Store(tmp_path / "test.sqlite3")


@pytest.fixture()
def scryfall_file(tmp_path):
    path = tmp_path / "default-cards.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for card in synthetic_cards():
            fh.write(json.dumps(card) + "\n")
    return path


@pytest.fixture()
def loaded_store(store, scryfall_file):
    from deckbuild_studio.scryfall import import_scryfall
    import_scryfall(store, scryfall_file)
    return store


def write_foundation_xlsx(path, rows):
    """rows: (name, qty, location)"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Kartensammlung"
    ws.append(["Kartenname", "Anzahl", "Standort", "Farbidentität",
               "Manakosten", "Kartentyp", "Kartentext"])
    for name, qty, loc in rows:
        card = NAMES.get(name, {})
        ws.append([name, qty, loc, "".join(card.get("color_identity", [])),
                   card.get("mana_cost", ""), card.get("type_line", ""), ""])
    wb.save(path)
    return path
