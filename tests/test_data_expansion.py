"""Data-expansion tests — recorded SYNTHETIC fixtures only.

No network, no real scrapes, no private collection data. The fixtures
mirror the real structures verified on 2026-11-11 (EDHREC card JSON,
Commander Spellbook server-rendered search payload, Playgroup
commander page sections, Scryfall bulk printings) with invented
cards/numbers.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import edhrec_card as ec_mod
from deckbuild_studio import external as ext
from deckbuild_studio import playgroup as pg_mod
from deckbuild_studio import printdata as pd_mod
from deckbuild_studio import spellbook as sb_mod
from deckbuild_studio.httpfetch import FetchError
from deckbuild_studio.importers import import_foundation_workbook
from test_external import FakeFetcher

FX = Path(__file__).parent / "fixtures"
ALARA = "Alara, Test Sovereign"
RING = "Sol Ring (Test)"
RING_OID = OID["sol_ring"]
PLAINS_OID = OID["plains"]


def fx(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


@pytest.fixture()
def collection_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            (RING, 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


# --------------------------------------------------------------------------
# EDHREC card JSON parser
# --------------------------------------------------------------------------

def test_edhrec_card_parser_fields():
    parsed = ec_mod.parse_card_json(
        fx("edhrec_card_test_ring.json"), expected_name=RING,
        expected_slug="sol-ring-test")
    assert parsed["num_decks"] == 800
    assert parsed["potential_decks"] == 1000
    assert parsed["inclusion"] == pytest.approx(0.8)
    assert parsed["salt"] == pytest.approx(1.25)
    assert parsed["scryfall_id"] == "printing-sol_ring"
    assert [c["name"] for c in parsed["top_commanders"]] == [
        ALARA, "Beta, Test Captain"]
    assert parsed["top_commanders"][0]["num_decks"] == 90
    assert [e["cards"] for e in parsed["combo_examples"]] == [
        ["Test Horror", RING], ["Test Tyrant", RING]]
    assert parsed["combos_page"] == "/combos/sol-ring-test"
    assert parsed["similar"] == ["Mana Test Vault", "Test Monolith"]


def test_edhrec_card_parser_verification():
    with pytest.raises(ec_mod.VerificationError):
        ec_mod.parse_card_json(fx("edhrec_card_test_ring.json"),
                               expected_name=RING, expected_slug="other-card")
    with pytest.raises(ec_mod.VerificationError):
        ec_mod.parse_card_json(fx("edhrec_card_test_ring.json"),
                               expected_name="Other Card",
                               expected_slug="sol-ring-test")


def test_edhrec_card_parser_missing_salt_stays_none():
    data = json.loads(fx("edhrec_card_test_ring.json"))
    card = data["container"]["json_dict"]["card"]
    del card["salt"]
    del card["num_decks"]
    parsed = ec_mod.parse_card_json(json.dumps(data), expected_name=RING,
                                    expected_slug="sol-ring-test")
    assert parsed["salt"] is None
    assert parsed["inclusion"] is None  # missing numerator: never faked


# --------------------------------------------------------------------------
# Commander Spellbook parser
# --------------------------------------------------------------------------

def test_spellbook_parser_filters_to_exact_commander_legal_uses():
    parsed = sb_mod.parse_search_page(
        fx("spellbook_search_test_ring.html"), card_name=RING)
    assert parsed["raw_count"] == 3
    # combo 2 uses "Sol Ring (Test) Extra" (substring trap) and combo 3
    # is not commander-legal: only combo 1 counts.
    assert [c["combo_id"] for c in parsed["combos"]] == ["1-2"]
    combo = parsed["combos"][0]
    assert combo["card_oracle_ids"][0] == RING_OID
    assert combo["produces"] == ["Infinite colorless mana"]
    assert combo["price_eur"] == pytest.approx(5.89)
    assert combo["price_usd"] == pytest.approx(12.78)
    assert combo["popularity"] == 123


def test_spellbook_parser_verification():
    with pytest.raises(sb_mod.VerificationError):
        sb_mod.parse_search_page(fx("spellbook_search_test_ring.html"),
                                 card_name="Plains")
    with pytest.raises(sb_mod.ParseError):
        sb_mod.parse_search_page("<html>no payload</html>", card_name=RING)


def test_spellbook_parser_double_faced_card_full_name_uses():
    # Live-verified 2026-11-12 (Fable of the Mirror-Breaker): Spellbook
    # ships '//' cards under their FULL name in combo uses, while the
    # search explanation names the FRONT. Parser 1.1.0 required the
    # front name in uses and accepted 0 of 38 real combos.
    full = "Fable (Test) // Mirror (Test)"
    payload = {"props": {"pageProps": {
        "explanation": ("Combos that use a card with “Fable (Test)” "
                        "in the name and are legal in Commander."),
        "page": 1, "featured": None,
        "combos": [
            {"id": "9-9", "status": "OK", "legalities": {"commander": True},
             "uses": [{"card": {"name": full, "id": 4242,
                                "oracleId": "oid-fable"}},
                      {"card": {"name": "Test Horror", "oracleId": None}}],
             "produces": [], "prices": {}},
            # Substring trap: a different, longer name stays rejected.
            {"id": "8-8", "status": "OK", "legalities": {"commander": True},
             "uses": [{"card": {"name": full + " Extra",
                                "oracleId": "oid-other"}},
                      {"card": {"name": "Test Horror", "oracleId": None}}],
             "produces": [], "prices": {}}]}}}
    page = ('<html><body><script id="__NEXT_DATA__" '
            f'type="application/json">{json.dumps(payload)}</script>'
            "</body></html>")
    parsed = sb_mod.parse_search_page(page, card_name=full)
    assert [c["combo_id"] for c in parsed["combos"]] == ["9-9"]
    assert parsed["spellbook_card_id"] == 4242


def _spellbook_page(combos: list[dict], page: int = 1) -> str:
    payload = {"props": {"pageProps": {
        "explanation": ("Combos that use a card with “Sol Ring (Test)” "
                        "in the name and are legal in Commander."),
        "page": page, "featured": None, "combos": combos}}}
    return ('<html><body><script id="__NEXT_DATA__" '
            f'type="application/json">{json.dumps(payload)}</script>'
            "</body></html>")


def _filler_combo(n: int) -> dict:
    return {"id": f"filler-{n}", "status": "OK", "legalities": {"commander": True},
            "uses": [{"card": {"name": f"Filler Card {n}", "oracleId": None}},
                     {"card": {"name": "Other Filler", "oracleId": None}}],
            "produces": [], "prices": {}}


def _ring_combo(cid: str) -> dict:
    return {"id": cid, "status": "OK", "legalities": {"commander": True},
            "popularity": 7, "manaValueNeeded": 3, "identity": "U",
            "variantCount": 1,
            "uses": [{"card": {"name": RING, "oracleId": RING_OID}},
                     {"card": {"name": "Test Horror", "oracleId": None}}],
            "produces": [{"feature": {"name": "Infinite colorless mana"}}],
            "prices": {"cardmarket": "5.89", "cardkingdom": "12.78"}}


# --------------------------------------------------------------------------
# Scryfall print facts (local derivation)
# --------------------------------------------------------------------------

def _printing(oid, *, set_code="tst", cn="1", rarity="common", year="2020-01-01",
              eur="1.00", usd="1.10", games=("paper",), layout="normal"):
    return {"oracle_id": oid, "layout": layout, "games": list(games),
            "set": set_code, "collector_number": cn, "rarity": rarity,
            "released_at": year,
            "prices": {"eur": eur, "usd": usd}}


def test_print_facts_aggregation():
    cards = [
        _printing("oid-a", set_code="aaa", cn="1", rarity="rare",
                  year="2015-05-01", eur="3.50", usd="4.00"),
        _printing("oid-a", set_code="bbb", cn="2", rarity="uncommon",
                  year="2021-05-01", eur="0.40", usd=None),
        _printing("oid-a", set_code="ccc", cn="3", rarity="common",
                  year="2023-05-01", eur=None, usd="0.20", games=("mtgo",)),
        _printing("oid-a", layout="token", eur="9.99", usd="9.99"),
        _printing("oid-b", set_code="aaa", cn="9", rarity="mythic",
                  year="2019-01-01", eur=None, usd=None),
    ]
    agg = pd_mod.aggregate_printings(cards)
    a = agg["oid-a"]
    assert a["prints"] == 2  # digital-only and token printings excluded
    assert a["sets"] == {"aaa", "bbb"}
    assert a["min_eur"] == pytest.approx(0.40)
    assert a["min_eur_printing"] == "bbb:2"
    assert a["min_usd"] == pytest.approx(4.00)  # the mtgo printing never counts
    assert (a["first"], a["last"]) == (2015, 2021)
    b = agg["oid-b"]
    assert b["min_eur"] is None and b["min_usd"] is None  # never faked as 0


def test_derive_print_facts_store_roundtrip(store, tmp_path):
    bulk = tmp_path / "default-cards.jsonl.gz"
    with gzip.open(bulk, "wt", encoding="utf-8") as fh:
        for card in (_printing(RING_OID, eur="2.50", usd="3.00"),
                     _printing(PLAINS_OID, eur="0.10", usd="0.05")):
            fh.write(json.dumps(card) + "\n")
    out = pd_mod.derive_print_facts(store, bulk)
    assert out["identities"] == 2 and out["with_eur_price"] == 2
    row = store.conn.execute(
        "SELECT * FROM card_print_fact WHERE oracle_id=?", (RING_OID,)).fetchone()
    assert row["prints_count"] == 1
    assert row["min_eur"] == pytest.approx(2.50)
    assert row["min_rarity"] == "common"
    assert row["first_release_year"] == 2020
    src = store.conn.execute(
        "SELECT * FROM source WHERE source_id=?", (row["source_id"],)).fetchone()
    assert src is not None and src["sha256"]
    again = pd_mod.derive_print_facts(store, bulk)  # idempotent rebuild
    assert again["identities"] == 2


# --------------------------------------------------------------------------
# Playgroup commander page parser
# --------------------------------------------------------------------------

def test_parse_commander_page_sections():
    parsed = pg_mod.parse_commander_page(
        fx("playgroup_commander_page.html"), expected_name=ALARA)
    assert parsed["win_conditions"] == [
        {"label": "Combat", "pct": 60.0}, {"label": "Combo", "pct": 40.0}]
    assert parsed["seat_win_rates"] == [
        {"seat": 1, "win_pct": 50.0, "n": 100},
        {"seat": 2, "win_pct": 25.0, "n": 80}]
    assert parsed["mulligan_win_rates"] == [
        {"mulligans": 0, "win_pct": 40.0, "n": 50},
        {"mulligans": 1, "win_pct": 20.0, "n": 10}]
    best = parsed["matchups"]["best"]
    assert best[0] == {"opponent": "Test Foe Alpha", "games": 30,
                       "win_pct": 70.0, "small_sample": False}
    assert best[1]["small_sample"] is True  # 12 games < Playgroup's 25
    assert parsed["matchups"]["worst"][0]["opponent"] == "Test Foe Gamma"
    assert parsed["win_staples"] == [
        {"rank": 1, "name": "Test Bloom", "games": 72, "lift_pp": 9.5},
        {"rank": 2, "name": RING, "games": 30, "lift_pp": 3.0}]
    assert any("archetype" in a for a in parsed["absent_from_page"])


def test_parse_commander_page_wrong_commander():
    with pytest.raises(pg_mod.ParseError):
        pg_mod.parse_commander_page(fx("playgroup_commander_page.html"),
                                    expected_name="Nonexistent, Test")


def test_parse_commander_page_truncated_title_uses_heading():
    # Live evidence 2026-11-12: the site truncates long commander names
    # inside <title> ("Statistics for Commander 'Molten Man, Inferno |
    # Playgroup.gg"); the H1 carries the full name as its own segment.
    page = ("<html><head><title>Statistics for Commander 'Molten Man, "
            "Inferno | Playgroup.gg</title></head><body>"
            "<h1>Molten Man, Inferno Incarnate</h1></body></html>")
    parsed = pg_mod.parse_commander_page(
        page, expected_name="Molten Man, Inferno Incarnate")
    assert parsed["name"] == "Molten Man, Inferno Incarnate"


def test_parse_commander_page_truncated_title_wrong_heading_fails():
    page = ("<html><head><title>Statistics for Commander 'Molten Man, "
            "Inferno | Playgroup.gg</title></head><body>"
            "<h1>Some Other, Commander</h1></body></html>")
    with pytest.raises(pg_mod.ParseError):
        pg_mod.parse_commander_page(
            page, expected_name="Molten Man, Inferno Incarnate")


def test_parse_commander_page_truncated_title_heading_after_nav():
    # Real page layout (measured on all 63 stored pages): a fixed nav
    # block puts the H1 at segment index 15 — outside the 1.0.0
    # parser's window of 8, which is why the stored Molten Man page
    # stayed PARTIAL despite carrying the full name.
    nav = "".join(f"<div>nav {i}</div>" for i in range(14))
    page = ("<html><head><title>Statistics for Commander 'Molten Man, "
            "Inferno | Playgroup.gg</title></head><body>" + nav +
            "<h1>Molten Man, Inferno Incarnate</h1></body></html>")
    parsed = pg_mod.parse_commander_page(
        page, expected_name="Molten Man, Inferno Incarnate")
    assert parsed["name"] == "Molten Man, Inferno Incarnate"


def test_parse_commander_page_win_staples_with_badge_segments():
    # Real pages interleave a decorative badge ('Signature build')
    # between a staple's name and its stats, and again before the
    # lift (Bre of Clan Stoutarm / Doran, live pages 2026-11-12).
    # The 1.0.0 fixed-offset scan stopped at the first badge row.
    divs = ["Statistics for Commander 'Staple Test, Commander' | "
            "Playgroup.gg", "Staple Test, Commander",
            "Staples that win games for Staple Test, Commander",
            "Cards that raise this deck's measured win rate the most.",
            "#", "Card", "Lift", "Win-rate lift", "Confidence", "Games",
            "1", "Badge Card", "Signature build", "31 games",
            "· Signature build", "+7.5 pp", "31",
            "2", "Plain Card", "77 games", "+0.8 pp", "77",
            "Measured win-rate lift against decks on the same commander."]
    page = ("<html><body>" + "".join(f"<div>{d}</div>" for d in divs)
            + "</body></html>")
    parsed = pg_mod.parse_commander_page(
        page, expected_name="Staple Test, Commander")
    assert parsed["win_staples"] == [
        {"rank": 1, "name": "Badge Card", "games": 31, "lift_pp": 7.5},
        {"rank": 2, "name": "Plain Card", "games": 77, "lift_pp": 0.8}]


# --------------------------------------------------------------------------
# Syncs (fake fetcher)
# --------------------------------------------------------------------------

def test_sync_edhrec_cards_end_to_end_and_cache(collection_store):
    routes = {
        "https://json.edhrec.com/pages/cards/sol-ring-test.json":
            (200, fx("edhrec_card_test_ring.json")),
        "https://json.edhrec.com/pages/cards/plains.json": (404, "nope"),
        "https://json.edhrec.com/pages/cards/alara-test-sovereign.json":
            (404, "nope"),
    }
    fetcher = FakeFetcher(routes)
    cov = ext.sync_edhrec_cards(collection_store, fetcher, "foundation-schwarze-box")
    assert cov["total_identities"] == 3
    assert cov["available"] == 1 and cov["not_found"] == 2
    row = collection_store.conn.execute(
        "SELECT * FROM edhrec_card_global WHERE oracle_id=?", (RING_OID,)).fetchone()
    assert row["inclusion"] == pytest.approx(0.8)
    assert row["salt"] == pytest.approx(1.25)
    snap = ext.latest_snapshot(collection_store, "edhrec", "edhrec_card",
                               oracle_id=RING_OID)
    assert snap["status"] == "AVAILABLE"
    assert json.loads(snap["payload_json"])["top_commanders"][0]["name"] == ALARA
    calls = len(fetcher.calls)
    cov2 = ext.sync_edhrec_cards(collection_store, fetcher, "foundation-schwarze-box")
    assert cov2["cached_skipped"] == 3 and len(fetcher.calls) == calls


SPLIT_NAME = "Rise (Test) // Fall (Test)"
SPLIT_OID = "00000000-0000-4000-8000-000000000099"
SPLIT_SLUG = "rise-test-fall-test"


@pytest.fixture()
def split_store(store, tmp_path):
    from deckbuild_studio.scryfall import import_scryfall
    card = {
        "id": "printing-split", "oracle_id": SPLIT_OID, "name": SPLIT_NAME,
        "type_line": "Instant // Sorcery", "oracle_text": "",
        "color_identity": ["U", "B"], "colors": ["U", "B"], "mana_cost": "",
        "cmc": 4.0, "layout": "split", "legalities": {"commander": "legal"},
        "image_uris": {"normal": "https://example.invalid/img.jpg"},
        "card_faces": [
            {"name": "Rise (Test)", "type_line": "Instant",
             "oracle_text": "Draw a card.", "mana_cost": "{1}{U}"},
            {"name": "Fall (Test)", "type_line": "Sorcery",
             "oracle_text": "Target player discards a card.",
             "mana_cost": "{1}{B}"}],
    }
    path = tmp_path / "cards.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(card) + "\n")
    import_scryfall(store, path)
    xlsx = write_foundation_xlsx(tmp_path / "f.xlsx",
                                 [(SPLIT_NAME, 1, "Foundation")])
    import_foundation_workbook(store, xlsx)
    return store


def _split_edhrec_json() -> str:
    return json.dumps({"container": {"json_dict": {
        "card": {"name": SPLIT_NAME, "sanitized": SPLIT_SLUG,
                 "slug": SPLIT_SLUG, "num_decks": 25, "potential_decks": 100,
                 "salt": 0.5, "id": "printing-split", "cmc": 4.0},
        "cardlists": []}}, "panels": {}, "similar": []})


def test_sync_edhrec_cards_split_card_uses_full_name_slug(split_store):
    # EDHREC addresses split cards by full name (live-verified
    # 2026-11-12); the front-slug document is an empty stub. Only the
    # full-name route exists here, so a front-slug fetch would 404.
    routes = {f"https://json.edhrec.com/pages/cards/{SPLIT_SLUG}.json":
              (200, _split_edhrec_json())}
    fetcher = FakeFetcher(routes)
    cov = ext.sync_edhrec_cards(split_store, fetcher, "foundation-schwarze-box")
    assert cov["available"] == 1 and cov["not_found"] == 0
    snap = ext.latest_snapshot(split_store, "edhrec", "edhrec_card",
                               oracle_id=SPLIT_OID)
    assert snap["status"] == "AVAILABLE" and snap["slug"] == SPLIT_SLUG


def test_sync_card_atlas_split_card_uses_full_name_slug(split_store):
    page = (f"<html><body><h1>{SPLIT_NAME}</h1>"
            "<div><div>Times Brought</div><div>55</div></div>"
            "</body></html>")
    routes = {f"https://playgroup.gg/cards/{SPLIT_SLUG}": (200, page)}
    fetcher = FakeFetcher(routes)
    cov = ext.sync_card_atlas(split_store, fetcher, "foundation-schwarze-box")
    assert cov["attempted"] == 1 and cov["not_found"] == 0
    snap = ext.latest_snapshot(split_store, "playgroup", "playgroup_card",
                               oracle_id=SPLIT_OID)
    assert snap["slug"] == SPLIT_SLUG


def test_sync_edhrec_cards_slug_drift_refetches(collection_store):
    routes = {
        "https://json.edhrec.com/pages/cards/sol-ring-test.json":
            (200, fx("edhrec_card_test_ring.json")),
        "https://json.edhrec.com/pages/cards/plains.json": (404, "nope"),
        "https://json.edhrec.com/pages/cards/alara-test-sovereign.json":
            (404, "nope"),
    }
    fetcher = FakeFetcher(routes)
    ext.sync_edhrec_cards(collection_store, fetcher, "foundation-schwarze-box")
    calls = len(fetcher.calls)
    # Simulate a snapshot written under an outdated slug rule: it
    # answers a different URL and must NOT count as a cache hit.
    collection_store.conn.execute(
        "UPDATE external_snapshot SET slug='sol-ring' WHERE oracle_id=?",
        (RING_OID,))
    collection_store.conn.commit()
    cov2 = ext.sync_edhrec_cards(collection_store, fetcher,
                                 "foundation-schwarze-box")
    assert cov2["cached_skipped"] == 2 and cov2["attempted"] == 1
    assert len(fetcher.calls) == calls + 1
    snap = ext.latest_snapshot(collection_store, "edhrec", "edhrec_card",
                               oracle_id=RING_OID)
    assert snap["slug"] == "sol-ring-test"


def test_sync_card_atlas_slug_drift_refetches(collection_store):
    page = ("<html><body><h1>Sol Ring (Test)</h1>"
            "<div><div>Times Brought</div><div>55</div></div>"
            "<div>First-cast turn</div><div>n=40</div></body></html>")
    generic = ("<html><body><h1>{}</h1>"
               "<div><div>Times Brought</div><div>3</div></div>"
               "</body></html>")
    routes = {
        "https://playgroup.gg/cards/sol-ring-test": (200, page),
        "https://playgroup.gg/cards/plains":
            (200, generic.format("Plains")),
        "https://playgroup.gg/cards/alara-test-sovereign":
            (200, generic.format(ALARA)),
    }
    fetcher = FakeFetcher(routes)
    ext.sync_card_atlas(collection_store, fetcher, "foundation-schwarze-box")
    calls = len(fetcher.calls)
    collection_store.conn.execute(
        "UPDATE external_snapshot SET slug='sol-ring' WHERE oracle_id=?",
        (RING_OID,))
    collection_store.conn.commit()
    cov2 = ext.sync_card_atlas(collection_store, fetcher,
                               "foundation-schwarze-box")
    assert cov2["cached_skipped"] == 2 and cov2["attempted"] == 1
    assert len(fetcher.calls) == calls + 1


def test_sync_spellbook_cards_pagination_and_not_found(collection_store):
    ring_url = sb_mod.search_url(RING, 1)
    ring_url2 = sb_mod.search_url(RING, 2)
    routes = {
        # page 1 is full (50 raw) but only one combo actually uses the card
        ring_url: (200, _spellbook_page(
            [_ring_combo("1-2")] + [_filler_combo(n) for n in range(49)])),
        ring_url2: (200, _spellbook_page([_ring_combo("3-4")], page=2)),
        sb_mod.search_url("Plains", 1): (200, _spellbook_page([])),
        sb_mod.search_url(ALARA, 1): (200, _spellbook_page([])),
    }
    fetcher = FakeFetcher(routes)
    cov = ext.sync_spellbook_cards(collection_store, fetcher,
                                   "foundation-schwarze-box")
    assert cov["available"] == 1 and cov["not_found"] == 2
    assert cov["combos_captured"] == 2
    rows = collection_store.conn.execute(
        "SELECT combo_id, produces_json, price_eur FROM spellbook_combo "
        "ORDER BY combo_id").fetchall()
    assert [r["combo_id"] for r in rows] == ["1-2", "3-4"]
    assert json.loads(rows[0]["produces_json"]) == ["Infinite colorless mana"]
    assert rows[0]["price_eur"] == pytest.approx(5.89)
    snap = ext.latest_snapshot(collection_store, "commanderspellbook",
                               "spellbook_card", oracle_id=RING_OID)
    assert snap["status"] == "AVAILABLE"
    assert snap["coverage_status"] == "CAPTURED_COMPLETE"


def test_sync_spellbook_cards_page_cap_is_partial(collection_store):
    full = _spellbook_page([_ring_combo("1-2")]
                           + [_filler_combo(n) for n in range(49)])
    routes = {sb_mod.search_url(RING, p): (200, full) for p in (1, 2)}
    routes[sb_mod.search_url("Plains", 1)] = (200, _spellbook_page([]))
    routes[sb_mod.search_url(ALARA, 1)] = (200, _spellbook_page([]))
    cov = ext.sync_spellbook_cards(collection_store, FakeFetcher(routes),
                                   "foundation-schwarze-box", max_pages=2)
    assert cov["partial"] == 1
    snap = ext.latest_snapshot(collection_store, "commanderspellbook",
                               "spellbook_card", oracle_id=RING_OID)
    assert snap["status"] == "PARTIAL"
    assert snap["coverage_status"] == "TOTAL_UNKNOWN"


def _ring_combo_with_id(cid: str) -> dict:
    combo = _ring_combo(cid)
    combo["uses"][0]["card"]["id"] = 77
    combo["uses"][1]["card"]["id"] = 78
    return combo


def _spellbook_card_page(total: int, combos: list[dict]) -> str:
    payload = {"page": "/card/[id]", "props": {"pageProps": {
        "card": {"id": 77, "name": RING, "oracleId": RING_OID},
        "combosCount": total, "combos": combos, "formatTerm": "legal:commander",
        "partners": [{"card": {"id": 78, "name": "Test Horror",
                               "oracleId": None}, "count": 2}]}}}
    return ('<html><body><script id="__NEXT_DATA__" '
            f'type="application/json">{json.dumps(payload)}</script>'
            "</body></html>")


def _spellbook_combo_page(combo: dict) -> str:
    payload = {"page": "/combo/[id]", "props": {"pageProps": {"combo": combo}}}
    return ('<html><body><script id="__NEXT_DATA__" '
            f'type="application/json">{json.dumps(payload)}</script>'
            "</body></html>")


def test_spellbook_card_page_parser():
    parsed = sb_mod.parse_card_page(
        _spellbook_card_page(132, [_ring_combo_with_id("1-2")]), card_name=RING)
    assert parsed["combos_total"] == 132
    assert parsed["spellbook_card_id"] == 77
    assert parsed["oracle_id"] == RING_OID
    assert parsed["partners"] == [{"name": "Test Horror", "oracle_id": None,
                                   "spellbook_id": 78, "shared_combos": 2}]
    with pytest.raises(sb_mod.VerificationError):
        sb_mod.parse_card_page(_spellbook_card_page(1, []), card_name="Plains")


def test_sync_spellbook_via_search_discovery_uses_card_page(collection_store):
    routes = {
        sb_mod.search_url(RING, 1): (200, _spellbook_page([_ring_combo_with_id("1-2")])),
        sb_mod.card_url(77): (200, _spellbook_card_page(3, [_ring_combo_with_id("1-2"),
                                                            _ring_combo_with_id("3-4")])),
        sb_mod.search_url("Plains", 1): (200, _spellbook_page([])),
        sb_mod.search_url(ALARA, 1): (200, _spellbook_page([])),
    }
    cov = ext.sync_spellbook_cards(collection_store, FakeFetcher(routes),
                                   "foundation-schwarze-box")
    assert cov["available"] == 1 and cov["not_found"] == 2
    assert cov["combos_captured"] == 2 and cov["combos_total_known"] == 3
    snap = ext.latest_snapshot(collection_store, "commanderspellbook",
                               "spellbook_card", oracle_id=RING_OID)
    assert snap["status"] == "AVAILABLE"
    assert snap["coverage_status"] == "TOTAL_KNOWN"
    assert snap["displayed_total"] == 3 and snap["captured_count"] == 2
    payload = json.loads(snap["payload_json"])
    assert payload["spellbook_card_id"] == 77
    assert payload["partners"][0]["name"] == "Test Horror"


def test_sync_spellbook_search_redirect_discovers_card_page(collection_store):
    routes = {
        # the site answers this search with a combo detail page instead
        sb_mod.search_url(RING, 1): (200, _spellbook_combo_page(_ring_combo_with_id("9-9"))),
        sb_mod.card_url(77): (200, _spellbook_card_page(1, [_ring_combo_with_id("9-9")])),
        sb_mod.search_url("Plains", 1): (200, _spellbook_page([])),
        sb_mod.search_url(ALARA, 1): (200, _spellbook_page([])),
    }
    cov = ext.sync_spellbook_cards(collection_store, FakeFetcher(routes),
                                   "foundation-schwarze-box")
    assert cov["available"] == 1
    snap = ext.latest_snapshot(collection_store, "commanderspellbook",
                               "spellbook_card", oracle_id=RING_OID)
    assert snap["status"] == "AVAILABLE" and snap["displayed_total"] == 1
    rows = collection_store.conn.execute(
        "SELECT combo_id FROM spellbook_combo").fetchall()
    assert [r["combo_id"] for r in rows] == ["9-9"]


def test_sync_playgroup_commander_page(collection_store):
    routes = {
        ext.PG_AUTOCOMPLETE + "Alara%2C+Test+Sovereign":
            (200, fx("playgroup_autocomplete.html")),
        "https://playgroup.gg/commanders/9999-alara-test-sovereign":
            (200, fx("playgroup_commander_page.html")),
    }
    fetcher = FakeFetcher(routes)
    out = ext.sync_playgroup_commander_page(
        collection_store, fetcher, name=ALARA,
        commander_oracle_id=OID["commander_a"])
    assert out["status"] == "AVAILABLE"
    assert out["win_staples"] == 2
    staples = collection_store.conn.execute(
        "SELECT card_name, card_oracle_id, lift_pp FROM "
        "playgroup_commander_staple ORDER BY card_name").fetchall()
    by_name = {r["card_name"]: r for r in staples}
    assert by_name[RING]["card_oracle_id"] == RING_OID  # resolved locally
    assert by_name["Test Bloom"]["card_oracle_id"] is None  # unknown: NULL
    assert by_name["Test Bloom"]["lift_pp"] == pytest.approx(9.5)
    again = ext.sync_playgroup_commander_page(
        collection_store, fetcher, name=ALARA,
        commander_oracle_id=OID["commander_a"])
    assert again.get("cached") is True


def test_commander_page_cache_is_per_commander(collection_store):
    """Regression: a name-only page sync must never return ANOTHER
    commander's cached page (live-found: a name-only sync returned a
    different commander's snapshot because the cache key ignored the
    commander)."""
    ext.save_snapshot(collection_store, source_name="playgroup",
                      kind="playgroup_commander_page",
                      url="https://playgroup.gg/commanders/1-other",
                      status="AVAILABLE", slug="other-test-commander",
                      detail="seeded other commander")
    routes = {
        ext.PG_AUTOCOMPLETE + "Alara%2C+Test+Sovereign":
            (200, fx("playgroup_autocomplete.html")),
        "https://playgroup.gg/commanders/9999-alara-test-sovereign":
            (200, fx("playgroup_commander_page.html")),
    }
    fetcher = FakeFetcher(routes)
    out = ext.sync_playgroup_commander_page(collection_store, fetcher, name=ALARA)
    assert fetcher.calls, "must fetch instead of serving the wrong cache entry"
    assert out["status"] == "AVAILABLE"
    assert out["source_url"].endswith("9999-alara-test-sovereign")


# --------------------------------------------------------------------------
# Network-error resilience of the resumable collection syncs: a card
# whose fetch fails (after the fetcher's own retries) must NOT abort
# the whole run and must NOT get a snapshot — it stays NOT_FETCHED.
# --------------------------------------------------------------------------

def _boom(url):
    raise FetchError(None, f"network error for {url}: connection closed")


def test_sync_edhrec_cards_network_error_skips_card(collection_store):
    routes = {
        "https://json.edhrec.com/pages/cards/plains.json": _boom,
        "https://json.edhrec.com/pages/cards/sol-ring-test.json":
            (200, fx("edhrec_card_test_ring.json")),
        "https://json.edhrec.com/pages/cards/alara-test-sovereign.json":
            (404, "nope"),
    }
    cov = ext.sync_edhrec_cards(collection_store, FakeFetcher(routes),
                                "foundation-schwarze-box")
    assert cov["network_errors"] == 1
    assert cov["available"] == 1 and cov["not_found"] == 1
    assert cov["stopped_on_block"] is False
    assert ext.latest_snapshot(collection_store, "edhrec", "edhrec_card",
                               oracle_id=PLAINS_OID) is None


def test_sync_spellbook_cards_network_error_skips_card(collection_store):
    routes = {
        sb_mod.search_url("Plains", 1): _boom,
        sb_mod.search_url(RING, 1):
            (200, _spellbook_page([_ring_combo("1-2")])),
        sb_mod.search_url(ALARA, 1): (200, _spellbook_page([])),
    }
    cov = ext.sync_spellbook_cards(collection_store, FakeFetcher(routes),
                                   "foundation-schwarze-box")
    assert cov["network_errors"] == 1
    assert cov["available"] == 1 and cov["not_found"] == 1
    assert cov["stopped_on_block"] is False
    assert ext.latest_snapshot(collection_store, "commanderspellbook",
                               "spellbook_card",
                               oracle_id=PLAINS_OID) is None
