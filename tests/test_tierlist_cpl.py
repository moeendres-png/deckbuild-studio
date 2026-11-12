"""Tierlist 1.1.0 — CPL adaptation tests (docs/TIERLIST_CPL_ADAPTATION.md
Revision 2). Under test:

* the pure counted tier function (CPL cuts + reason codes);
* the Verbreitung (gezählt) universe scope: dedupe, commander
  exclusion, quantity guard, period rule (source timestamp, honest
  exclusion count), minimum-size gate from settings, snapshot ids,
  LIST absence = counted 0, too small = U ("unbekannt");
* the separation of the two fields: harvested deck lists never move
  the Evidenz-Tier (frequency separation), marks move NEITHER field;
* A5: Top-Commanders fallback evidence inside cohort_inclusion
  (commander-page stats win; unknown commander = no evidence);
* A4: spellbook payload carries combo partner / result-type counts;
* co-occurrence with lift + combo-partner flag;
* schema migration of the derived tier cache.

Synthetic fixtures only.
"""
from __future__ import annotations

import json

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import external as ext
from deckbuild_studio import settings as settings_mod
from deckbuild_studio import tierlist as tl
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.inclusion import cooccurrence

FC = "foundation-schwarze-box"
ALARA = OID["commander_a"]
RING = OID["sol_ring"]
PLAINS = OID["plains"]
FOREST = OID["forest"]
NAMES = {ALARA: "Alara, Test Sovereign", RING: "Sol Ring (Test)",
         PLAINS: "Plains", FOREST: "Forest"}


@pytest.fixture()
def coll(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [
        ("Alara, Test Sovereign", 1, "Foundation"),
        ("Sol Ring (Test)", 1, "Schwarze Box"),
        ("Plains", 60, "Foundation"),
        ("Forest", 40, "Schwarze Box"),
    ])
    import_foundation_workbook(loaded_store, path)
    return loaded_store


def _deck(store, uid, bracket, rows, commander=ALARA, source_updated_at=None):
    """Store one harvested deck directly: rows are
    (oracle_id, quantity, is_commander)."""
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,"
        "source_url,status,parser_version,sha256,raw_path,fetched_at,"
        "source_updated_at,deck_size,card_entries,mapped_cards,"
        "unmapped_cards,unmapped_names_json,detail) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, "archidekt", uid.split(":", 1)[1], commander,
         NAMES[commander], bracket, "archidekt_edhBracket",
         f"https://archidekt.com/decks/{uid.split(':', 1)[1]}",
         "AVAILABLE", "archidekt-deck/1.0.0", None, None,
         "2026-11-12T00:00:00Z", source_updated_at,
         sum(q for _, q, _ in rows), len(rows), len(rows), 0, "[]", ""))
    for oid, qty, is_cmd in rows:
        store.conn.execute(
            "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,"
            "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)",
            (uid, oid, oid, NAMES[oid], qty, is_cmd))
    store.conn.commit()


def _decks(store, n, *, bracket=3, commander=ALARA, extra=(),
           source_updated_at=None):
    """n DISTINCT decks of one commander (the Plains count varies, so
    no two decks share a content fingerprint); ``extra`` cards are in
    every deck."""
    for i in range(n):
        rows = [(commander, 1, 1), (PLAINS, 20 + i, 0)]
        rows += [(oid, 1, 0) for oid in extra]
        _deck(store, f"archidekt:{bracket}{i:04d}", bracket, rows,
              commander=commander, source_updated_at=source_updated_at)


def _snap(store, source, kind, **kw):
    return ext.save_snapshot(
        store, source_name=source, kind=kind,
        url=kw.pop("url", f"https://example.invalid/{kind}"),
        status=kw.pop("status", "AVAILABLE"), **kw)


def _edhrec_global(store, oid, *, inclusion, num=100, potential=1000):
    snap = _snap(store, "edhrec", "edhrec_card", oracle_id=oid,
                 url=f"https://json.edhrec.com/pages/cards/x-{oid}.json")
    store.conn.execute(
        "INSERT INTO edhrec_card_global(snapshot_id,oracle_id,scryfall_id,"
        "num_decks,potential_decks,inclusion,salt) VALUES(?,?,?,?,?,?,?)",
        (snap, oid, None, num, potential, inclusion, None))
    store.conn.commit()
    return snap


def _spellbook(store, oid, *, total):
    return _snap(store, "commanderspellbook", "spellbook_card",
                 oracle_id=oid, captured_count=total,
                 displayed_total=total, coverage_status="TOTAL_KNOWN",
                 url=f"https://commanderspellbook.com/search/?q=x-{oid}",
                 payload={"combos_total": total, "combo_count": total,
                          "partners": []})


def _card_page_top_commanders(store, oid, entries):
    """An EDHREC card-page snapshot whose parsed payload carries the
    given Top Commanders entries (the shape parse_card_json stores)."""
    return _snap(store, "edhrec", "edhrec_card", oracle_id=oid,
                 url=f"https://json.edhrec.com/pages/cards/y-{oid}.json",
                 payload={"name": NAMES[oid], "top_commanders": entries})


def _cohort_stats(store, commander, bracket_name, rows):
    snap = _snap(store, "edhrec", "edhrec_stats",
                 commander_oracle_id=commander, bracket=bracket_name,
                 slug="alara-test-sovereign",
                 url=f"https://edhrec.com/commanders/x/{bracket_name}")
    for name, inclusion, synergy in rows:
        store.conn.execute(
            "INSERT INTO edhrec_card_stat(snapshot_id,category,card_slug,"
            "name,scryfall_id,inclusion,num_decks,potential_decks,synergy,"
            "lift,trend_zscore) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (snap, "top", None, name, None, inclusion,
             int(inclusion * 100), 100, synergy, None, None))
    store.conn.commit()
    return snap


def _strength_rows(store):
    return [tuple(r) for r in store.conn.execute(
        "SELECT oracle_id, scope, commander_oracle_id, bracket, tier, "
        "score, evidence, algo_version, input_snapshot_ids_json "
        "FROM tier_assignment WHERE scope IN ('global','context') "
        "ORDER BY oracle_id, scope, commander_oracle_id, bracket")]


def _all_universe(store):
    universes = {u["profile"]: u for u in tl.list_universes(store)}
    return universes["all"]["universe_id"]


# ---------------------------------------------------------------------------
# Pure counted tier function (CPL tiers.py semantics)
# ---------------------------------------------------------------------------

def test_counted_tier_cuts_and_reasons():
    assert tl.counted_tier(0.50, 100) == ("S", "SHARE_CUT")
    assert tl.counted_tier(0.499, 100) == ("A", "SHARE_CUT")
    assert tl.counted_tier(0.35, 100) == ("A", "SHARE_CUT")
    assert tl.counted_tier(0.20, 100) == ("B", "SHARE_CUT")
    assert tl.counted_tier(0.10, 100) == ("C", "SHARE_CUT")
    assert tl.counted_tier(0.099, 100) == ("D", "BELOW_LOWEST_CUT")
    assert tl.counted_tier(0.0, 100) == ("D", "BELOW_LOWEST_CUT")
    assert tl.counted_tier(None, 100) == ("U", "DENOMINATOR_MISSING")
    assert tl.counted_tier(0.90, 29) == ("U", "UNIVERSE_TOO_SMALL")
    assert tl.counted_tier(0.90, 30) == ("S", "SHARE_CUT")
    # CPL: an explicitly empty cut list is an owner setting, not a
    # missing value — every counted card lands in the fallback tier.
    empty = tl.TierParams(cuts=())
    assert tl.counted_tier(0.99, 100, empty) == ("D", "BELOW_LOWEST_CUT")
    assert tl.DEFAULT_TIER_PARAMS.to_dict() == {
        "min_universe": 30,
        "cuts": [["S", 0.5], ["A", 0.35], ["B", 0.2], ["C", 0.1]],
        "fallback_tier": "D"}


# ---------------------------------------------------------------------------
# Verbreitung (gezählt): counting rules of the universe scope
# ---------------------------------------------------------------------------

def test_universe_dedupes_and_excludes_commander(coll):
    store = coll
    _decks(store, 30, extra=(RING,))
    # Five exact copies of deck 0 under fresh ids must not inflate
    # the denominator or the hits (content dedupe, lowest id wins).
    rows = [(ALARA, 1, 1), (PLAINS, 20, 0), (RING, 1, 0)]
    for j in range(5):
        _deck(store, f"archidekt:9{j:04d}", 3, rows)
    summary = tl.compute_tiers(store)
    assert summary["universe"]["denominators"]["all"] == 30
    all_id = _all_universe(store)
    ring = tl.get_tier(store, RING, universe_id=all_id)
    assert ring["tier"] == "S" and ring["score"] == 1.0
    assert ring["signals"]["field"] == "Verbreitung (gezählt)"
    value = ring["signals"]["signals"][0]["value"]
    assert value == {"hits": 30, "denominator": 30, "share": 1.0}
    # The commander itself: commander entries never count, so its
    # Verbreitung is a counted 0 -> D (LIST absence rule), never U.
    own = tl.get_tier(store, ALARA, universe_id=all_id)
    assert own["tier"] == "D" and own["score"] == 0.0
    assert own["signals"]["signals"][0]["value"]["hits"] == 0


def test_universe_quantity_zero_never_counts(coll):
    store = coll
    _decks(store, 30, extra=(RING,))
    _deck(store, "archidekt:7777", 3,
          [(ALARA, 1, 1), (PLAINS, 33, 0), (FOREST, 0, 0)])
    tl.compute_tiers(store)
    forest = tl.get_tier(store, FOREST, universe_id=_all_universe(store))
    assert forest["signals"]["signals"][0]["value"]["hits"] == 0
    assert forest["signals"]["signals"][0]["value"]["denominator"] == 31


def test_universe_scope_rows_snapshot_and_absence(coll):
    store = coll
    for i in range(40):
        rows = [(ALARA, 1, 1), (PLAINS, 20 + i, 0)]
        if i < 20:
            rows.append((RING, 1, 0))
        _deck(store, f"archidekt:3{i:04d}", 3, rows)
    summary = tl.compute_tiers(store)
    universes = {u["profile"]: u for u in tl.list_universes(store)}
    assert set(universes) == {"all", f"commander:{ALARA}",
                              f"commander:{ALARA}:bracket:3"}
    all_id = universes["all"]["universe_id"]
    assert universes["all"]["universe_size"] == 40
    assert summary["universe"]["denominators"]["all"] == 40

    ring = tl.get_tier(store, RING, universe_id=all_id)
    assert ring["tier"] == "S" and ring["score"] == 0.5
    assert ring["evidence"] == 1.0
    assert ring["signals"]["data_class"] == "DERIVED_DESCRIPTIVE"
    assert ring["signals"]["tier_reason"] == "SHARE_CUT"
    assert ring["signals"]["u_reason"] is None
    forest = tl.get_tier(store, FOREST, universe_id=all_id)
    assert forest["tier"] == "D" and forest["score"] == 0.0
    assert forest["signals"]["tier_reason"] == "BELOW_LOWEST_CUT"

    # Snapshot ids are stable over an unchanged corpus ...
    tl.compute_tiers(store)
    again = {u["profile"]: u["universe_id"]
             for u in tl.list_universes(store)}
    assert again["all"] == all_id
    # ... and rotate when a deck's content changes.
    store.conn.execute(
        "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,card_name,"
        "quantity,is_commander) VALUES(?,?,?,?,?,?)",
        ("archidekt:30000", FOREST, FOREST, "Forest", 1, 0))
    store.conn.commit()
    tl.compute_tiers(store)
    rotated = {u["profile"]: u["universe_id"]
               for u in tl.list_universes(store)}
    assert rotated["all"] != all_id
    forest2 = tl.get_tier(store, FOREST, universe_id=rotated["all"])
    assert forest2["signals"]["signals"][0]["value"]["hits"] == 1


def test_universe_scope_too_small_is_u_with_reason(coll):
    store = coll
    _decks(store, 10, extra=(RING,))
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING, universe_id=_all_universe(store))
    assert row["tier"] == "U" and row["evidence"] == 0.0
    assert row["score"] == 1.0  # the share is carried, the tier is gated
    assert row["signals"]["u_reason"] == "UNIVERSE_TOO_SMALL"


def test_universe_min_size_follows_setting(coll):
    store = coll
    _decks(store, 12, extra=(RING,))
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING, universe_id=_all_universe(store))
    assert row["tier"] == "U"  # default minimum 30 (CPL default)
    settings_mod.set_setting(store, "tierlist.min_universe", 10)
    summary = tl.compute_tiers(store)
    assert summary["universe"]["params"]["min_universe"] == 10
    row = tl.get_tier(store, RING, universe_id=_all_universe(store))
    assert row["tier"] == "S" and row["score"] == 1.0


def test_universe_scope_follows_bracket_setting(coll):
    store = coll
    _decks(store, 35, bracket=2, extra=(RING,))
    tl.compute_tiers(store)
    assert {u["profile"] for u in tl.list_universes(store)} == {
        "all", f"commander:{ALARA}", f"commander:{ALARA}:bracket:2"}
    settings_mod.set_setting(store, "inclusion.brackets", [3])
    summary = tl.compute_tiers(store)
    # The settings selection is now empty: no universe exists and no
    # stale rows survive (honest "not computed", never silent zeros).
    assert summary["universe"]["profiles"] == 0
    assert tl.list_universes(store) == []
    assert tl.verbreitung_summary(store)["denominator"] == 0


def test_period_filter_uses_source_timestamp(coll):
    store = coll
    _decks(store, 35, extra=(RING,),
           source_updated_at="2026-06-15T10:00:00Z")
    _decks(store, 5, bracket=2)  # no source timestamp (NULL)
    summary = tl.compute_tiers(store)
    assert summary["universe"]["denominators"]["all"] == 40
    settings_mod.set_setting(store, "inclusion.date_from", "2026-01-01")
    summary = tl.compute_tiers(store)
    # The 5 timestamp-less decks are excluded AND counted in the
    # definition; fetched_at is never used as a deck date.
    assert summary["universe"]["denominators"]["all"] == 35
    uni = tl.list_universes(store)[0]
    assert uni["definition"]["excluded_no_timestamp"] == 5
    assert uni["definition"]["period_basis"].startswith("source_updated_at")
    # A period after every deck's source date -> empty selection.
    settings_mod.set_setting(store, "inclusion.date_from", "2027-01-01")
    summary = tl.compute_tiers(store)
    assert summary["universe"]["profiles"] == 0


def test_verbreitung_summary_reports_splits(coll):
    store = coll
    _decks(store, 30, bracket=3, extra=(RING,))
    _decks(store, 10, bracket=2)
    out = tl.verbreitung_summary(store)
    assert out["denominator"] == 40
    assert out["denominator_by_bracket"] == {"2": 10, "3": 30}
    assert out["denominator_by_platform"] == {"archidekt": 40}
    assert out["params"]["min_universe"] == 30
    assert out["snapshot_id"].startswith("universe:")


# ---------------------------------------------------------------------------
# Verbreitung per commander x bracket cohort (spec O2, implemented):
# one bracket of one commander, counted only from that cohort's decks.
# ---------------------------------------------------------------------------

def _cdecks(store, n, *, bracket, start, ring_in=0, commander=ALARA):
    """n decks of ONE cohort; the first ``ring_in`` also run RING.
    ``start`` offsets the Plains counts so decks of different cohorts
    never share a content fingerprint (no accidental cross-cohort
    dedupe in the pooled profiles)."""
    for i in range(n):
        rows = [(commander, 1, 1), (PLAINS, 20 + start + i, 0)]
        if i < ring_in:
            rows.append((RING, 1, 0))
        _deck(store, f"archidekt:{bracket}{start + i:04d}", bracket, rows,
              commander=commander)


def _cohort_id(store, commander, level):
    profile = f"commander:{commander}:bracket:{level}"
    for u in tl.list_universes(store):
        if u["profile"] == profile:
            return u["universe_id"]
    raise AssertionError(f"no cohort profile {profile}")


def test_cohort_spread_uses_only_the_cohorts_decks(coll):
    store = coll
    _cdecks(store, 40, bracket=3, start=0, ring_in=20)    # share 20/40
    _cdecks(store, 40, bracket=2, start=100, ring_in=0)  # share 0/40
    summary = tl.compute_tiers(store)
    universes = {u["profile"]: u for u in tl.list_universes(store)}
    assert set(universes) == {
        "all", f"commander:{ALARA}",
        f"commander:{ALARA}:bracket:2", f"commander:{ALARA}:bracket:3"}
    assert summary["universe"]["cohort_profiles"] == 2
    assert summary["universe"]["denominators"][
        f"commander:{ALARA}:bracket:3"] == 40
    coh3 = universes[f"commander:{ALARA}:bracket:3"]
    assert coh3["bracket_level"] == 3 and coh3["universe_size"] == 40
    assert coh3["commander_oracle_id"] == ALARA
    assert coh3["definition"]["brackets"] == [3]
    assert coh3["definition"]["commander_oracle_id"] == ALARA

    ring3 = tl.get_tier(store, RING, universe_id=coh3["universe_id"])
    assert ring3["tier"] == "S" and ring3["score"] == 0.5
    assert ring3["bracket"] == "upgraded"
    assert ring3["commander_oracle_id"] == ALARA
    assert ring3["signals"]["signals"][0]["value"] == {
        "hits": 20, "denominator": 40, "share": 0.5}
    assert ring3["signals"]["data_class"] == "DERIVED_DESCRIPTIVE"
    # The pooled commander profile mixes both brackets: 20/80 -> B.
    # The cohort figure must NOT be the pooled one (never mixed).
    pooled = tl.get_tier(
        store, RING,
        universe_id=universes[f"commander:{ALARA}"]["universe_id"])
    assert pooled["tier"] == "B" and pooled["score"] == 0.25
    # Bracket 2 cohort: RING absent -> counted 0 -> D (LIST rule).
    ring2 = tl.get_tier(
        store, RING,
        universe_id=universes[f"commander:{ALARA}:bracket:2"]
        ["universe_id"])
    assert ring2["tier"] == "D" and ring2["score"] == 0.0
    # A collection card absent from the cohort is a counted 0 there too.
    forest3 = tl.get_tier(store, FOREST, universe_id=coh3["universe_id"])
    assert forest3["tier"] == "D"
    assert forest3["signals"]["signals"][0]["value"]["hits"] == 0


def test_cohort_spread_below_minimum_is_u(coll):
    store = coll
    _cdecks(store, 10, bracket=4, start=200, ring_in=10)
    summary = tl.compute_tiers(store)
    assert summary["universe"]["denominators"][
        f"commander:{ALARA}:bracket:4"] == 10
    row = tl.get_tier(store, RING,
                      universe_id=_cohort_id(store, ALARA, 4))
    assert row["tier"] == "U" and row["evidence"] == 0.0
    assert row["score"] == 1.0  # share carried, tier gated — as pooled
    assert row["signals"]["u_reason"] == "UNIVERSE_TOO_SMALL"
    assert row["bracket"] == "optimized"


def test_cohort_spread_no_decks_no_profile(coll):
    store = coll
    _cdecks(store, 35, bracket=3, start=0, ring_in=5)
    tl.compute_tiers(store)
    profiles = {u["profile"] for u in tl.list_universes(store)}
    assert f"commander:{ALARA}:bracket:2" not in profiles
    assert f"commander:{ALARA}:bracket:4" not in profiles


def test_cohort_spread_marks_invariant(coll):
    store = coll
    _cdecks(store, 40, bracket=3, start=0, ring_in=20)
    tl.compute_tiers(store)
    coh_id = _cohort_id(store, ALARA, 3)
    before = tl.get_tier(store, RING, universe_id=coh_id)
    assert before["tier"] == "S"
    for oid in (RING, PLAINS, FOREST, ALARA):
        store.conn.execute(
            "INSERT OR REPLACE INTO mark(oracle_id,collection_id,favorite,"
            "excluded,note) VALUES(?,?,?,?,?)", (oid, FC, 1, 1, "flip"))
    store.conn.commit()
    tl.compute_tiers(store)
    after = tl.get_tier(store, RING, universe_id=coh_id)
    assert after["tier"] == before["tier"]
    assert after["score"] == before["score"]
    assert after["signals"]["signals"][0]["value"] == \
        before["signals"]["signals"][0]["value"]


def test_cohort_spread_web_surface(coll, monkeypatch):
    from fastapi.testclient import TestClient

    import deckbuild_studio.web as web_mod
    store = coll
    _cdecks(store, 40, bracket=3, start=0, ring_in=20)
    tl.compute_tiers(store)
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    universes = client.get("/api/tiers/universes").json()
    coh = next(u for u in universes
               if u["profile"] == f"commander:{ALARA}:bracket:3")
    assert coh["bracket_level"] == 3 and coh["universe_size"] == 40
    rows = client.get("/api/tiers", params={
        "scope": "universe", "universe_id": coh["universe_id"]}).json()
    ring = next(r for r in rows if r["oracle_id"] == RING)
    assert ring["tier"] == "S"
    card = client.get(f"/api/tiers/card/{RING}",
                      params={"universe_id": coh["universe_id"]}).json()
    assert card["universe"]["tier"] == "S"
    assert card["universe"]["bracket"] == "upgraded"


# ---------------------------------------------------------------------------
# Field separation: frequency never moves the Evidenz-Tier; marks move
# neither field (Moritz negative tests).
# ---------------------------------------------------------------------------

def test_decklists_never_change_strength_tiers(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.40)
    _spellbook(store, RING, total=30)
    _cohort_stats(store, ALARA, "core", [("Plains", 0.9, 0.1)])
    tl.compute_tiers(store)
    before = _strength_rows(store)
    assert before  # the strength model produced rows
    _decks(store, 40, extra=(RING,))
    tl.compute_tiers(store)
    assert _strength_rows(store) == before
    # ... while the Verbreitung field now exists and is counted.
    ring = tl.get_tier(store, RING, universe_id=_all_universe(store))
    assert ring["tier"] == "S"


def test_marks_never_change_either_field(coll):
    store = coll
    _decks(store, 35, extra=(RING,))
    _edhrec_global(store, RING, inclusion=0.40)
    _spellbook(store, RING, total=30)
    tl.compute_tiers(store)
    before_strength = _strength_rows(store)
    all_id = _all_universe(store)
    verb_before = tl.get_tier(store, RING, universe_id=all_id)
    assert verb_before["tier"] == "S"
    for oid in (RING, PLAINS, FOREST, ALARA):
        store.conn.execute(
            "INSERT OR REPLACE INTO mark(oracle_id,collection_id,favorite,"
            "excluded,note) VALUES(?,?,?,?,?)", (oid, FC, 1, 1, "flip"))
    store.conn.commit()
    tl.compute_tiers(store)
    assert _strength_rows(store) == before_strength
    verb_after = tl.get_tier(store, RING, universe_id=all_id)
    # Explicit Verbreitung payload comparison (hits/share/tier), the
    # negative test Moritz asked for on the new field.
    assert verb_after["tier"] == verb_before["tier"]
    assert verb_after["score"] == verb_before["score"]
    assert verb_after["signals"]["signals"][0]["value"] == \
        verb_before["signals"]["signals"][0]["value"]


# ---------------------------------------------------------------------------
# A5 — Top Commanders fallback evidence (EDHREC card pages)
# ---------------------------------------------------------------------------

def test_a5_fallback_supplies_cohort_inclusion(coll):
    store = coll
    _cohort_stats(store, ALARA, "core", [("Plains", 0.9, 0.1)])
    snap = _card_page_top_commanders(store, RING, [
        {"name": "Alara, Test Sovereign", "slug": "alara-test-sovereign",
         "num_decks": 80, "potential_decks": 100}])
    summary = tl.compute_tiers(store)
    row = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                      bracket="core")
    # RING is in no cohort stat — the context row exists purely from
    # the card page's Top Commanders evidence.
    assert row is not None
    sig = next(s for s in row["signals"]["signals"]
               if s["signal"] == "edhrec_cohort_inclusion")
    assert sig["available"] is True
    assert sig["value"]["measurement"] == "card_page_top_commanders"
    assert sig["value"]["bracket_specific"] is False
    assert sig["value"]["inclusion"] == pytest.approx(0.8)
    assert sig["snapshot_id"] == snap  # provenance = the card page
    # evidence = cohort weight 0.35 alone -> S band capped to B
    assert row["tier"] == "B"
    assert summary["context"]["a5_top_commander_rows"] >= 1


def test_a5_commander_page_stats_win_over_fallback(coll):
    store = coll
    _cohort_stats(store, ALARA, "core", [("Sol Ring (Test)", 0.10, 0.0)])
    _card_page_top_commanders(store, RING, [
        {"name": "Alara, Test Sovereign", "slug": "alara-test-sovereign",
         "num_decks": 80, "potential_decks": 100}])
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                      bracket="core")
    sig = next(s for s in row["signals"]["signals"]
               if s["signal"] == "edhrec_cohort_inclusion")
    assert sig["value"]["measurement"] == "commander_page_stats"
    assert sig["value"]["inclusion"] == pytest.approx(0.10)


def test_a5_unknown_commander_is_no_evidence(coll):
    store = coll
    _cohort_stats(store, ALARA, "core", [("Plains", 0.9, 0.1)])
    _card_page_top_commanders(store, RING, [
        {"name": "Nobody, The Unresolvable", "slug": "nobody",
         "num_decks": 80, "potential_decks": 100}])
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                      bracket="core")
    assert row is None  # no row is created from unresolvable evidence


# ---------------------------------------------------------------------------
# A4 — spellbook payload detail (combo partners / result types)
# ---------------------------------------------------------------------------

def test_a4_spellbook_value_carries_partner_and_produces_counts(coll):
    store = coll
    snap = _spellbook(store, RING, total=8)
    combos = [([RING, FOREST, PLAINS], ["Token"]),
              ([RING, FOREST], ["Token", "Mana"])]
    for i, (ids, produces) in enumerate(combos):
        store.conn.execute(
            "INSERT INTO spellbook_combo(snapshot_id,combo_id,"
            "card_oracle_ids_json,card_names_json,produces_json) "
            "VALUES(?,?,?,?,?)",
            (snap, f"c{i}", json.dumps(ids),
             json.dumps([NAMES[i] for i in ids]), json.dumps(produces)))
    store.conn.commit()
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING)
    sig = next(s for s in row["signals"]["signals"]
               if s["signal"] == "spellbook_combo_density")
    assert sig["value"]["combos_total"] == 8
    assert sig["value"]["combo_partners"] == 2       # Forest + Plains
    assert sig["value"]["produces_types"] == 2       # Token + Mana


# ---------------------------------------------------------------------------
# Co-occurrence (A2): lift, dedupe basis, combo-partner flag
# ---------------------------------------------------------------------------

def test_cooccurrence_lift_and_combo_flag(coll):
    store = coll
    for i in range(40):
        rows = [(ALARA, 1, 1), (PLAINS, 20 + i, 0)]
        if i < 20:
            rows.append((RING, 1, 0))
        if i < 10:
            rows.append((FOREST, 1, 0))  # always together with RING
        _deck(store, f"archidekt:3{i:04d}", 3, rows)
    snap = _spellbook(store, RING, total=3)
    store.conn.execute(
        "INSERT INTO spellbook_combo(snapshot_id,combo_id,"
        "card_oracle_ids_json,card_names_json,produces_json) "
        "VALUES(?,?,?,?,?)",
        (snap, "c0", json.dumps([RING, FOREST]),
         json.dumps(["Sol Ring (Test)", "Forest"]),
         json.dumps(["Mana"])))
    store.conn.commit()
    out = cooccurrence(store, RING)
    assert out["definition"]["denominator"] == 40
    assert out["decks_with_card"] == 20
    partners = {p["oracle_id"]: p for p in out["partners"]}
    forest, plains = partners[FOREST], partners[PLAINS]
    # P(Forest|Ring) = 10/20 = 0.5; P(Forest) = 10/40 = 0.25 -> lift 2
    assert forest["decks_together"] == 10
    assert forest["lift"] == pytest.approx(2.0)
    assert forest["combo_partner"] is True
    # Plains is everywhere: lift exactly 1, no combo flag.
    assert plains["lift"] == pytest.approx(1.0)
    assert plains["combo_partner"] is False
    assert out["partners"][0]["oracle_id"] == FOREST  # lift order
    # Commander-scoped view of the same corpus.
    scoped = cooccurrence(store, RING, commander_oracle_id=ALARA)
    assert scoped["decks_with_card"] == 20


def test_cooccurrence_card_absent_is_honest(coll):
    store = coll
    _decks(store, 5)
    out = cooccurrence(store, FOREST)
    assert out["decks_with_card"] == 0 and out["partners"] == []
    assert "note" in out


# ---------------------------------------------------------------------------
# Web API surface of the new fields
# ---------------------------------------------------------------------------

def test_new_endpoints(coll, monkeypatch):
    from fastapi.testclient import TestClient

    import deckbuild_studio.web as web_mod
    store = coll
    _decks(store, 35, extra=(RING,))
    tl.compute_tiers(store)
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    verb = client.get("/api/verbreitung").json()
    assert verb["denominator"] == 35
    assert verb["denominator_by_bracket"] == {"3": 35}
    card = client.get(f"/api/tiers/card/{RING}",
                      params={"universe_id": verb["snapshot_id"]}).json()
    assert card["universe"]["tier"] == "S"
    assert card["universe"]["signals"]["field"] == "Verbreitung (gezählt)"
    cooc = client.get(f"/api/cards/{RING}/cooccurrence").json()
    assert cooc["decks_with_card"] == 35


# ---------------------------------------------------------------------------
# Schema migration of the derived cache
# ---------------------------------------------------------------------------

def test_legacy_database_file_opens_and_migrates(tmp_path):
    """Regression (found on the real-DB copy): a database FILE whose
    tier_assignment still has the 1.0.0 shape must open cleanly with
    the new code — the store DDL must not reference universe_id before
    tierlist.ensure_schema had a chance to rebuild the cache."""
    import sqlite3

    from deckbuild_studio.store import Store

    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE tier_assignment ("
        "oracle_id TEXT NOT NULL, scope TEXT NOT NULL DEFAULT 'global',"
        "commander_oracle_id TEXT NOT NULL DEFAULT '',"
        "bracket TEXT NOT NULL DEFAULT '', tier TEXT NOT NULL,"
        "score REAL, evidence REAL NOT NULL,"
        "signals_json TEXT NOT NULL DEFAULT '{}',"
        "algo_version TEXT NOT NULL, computed_at TEXT NOT NULL,"
        "input_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',"
        "PRIMARY KEY (oracle_id, scope, commander_oracle_id, bracket));"
        "INSERT INTO tier_assignment VALUES('x','global','','','A',0.9,"
        "1.0,'{}','tierlist/1.0.0','2026-11-12T00:00:00Z','[]');")
    conn.commit()
    conn.close()
    store = Store(path)  # must not raise
    try:
        tl.ensure_schema(store)
        cols = {r["name"] for r in store.conn.execute(
            "PRAGMA table_info(tier_assignment)")}
        assert "universe_id" in cols
        idx = {r["name"] for r in store.conn.execute(
            "PRAGMA index_list(tier_assignment)")}
        assert "tier_assignment_universe" in idx
        assert store.conn.execute(
            "SELECT COUNT(*) FROM tier_assignment").fetchone()[0] == 0
        deck_cols = {r["name"] for r in store.conn.execute(
            "PRAGMA table_info(decklist_deck)")}
        assert "source_updated_at" in deck_cols
    finally:
        store.close()


def test_schema_migration_rebuilds_legacy_cache(store):
    store.conn.execute("DROP TABLE IF EXISTS tier_assignment")
    store.conn.executescript(
        "CREATE TABLE tier_assignment ("
        "oracle_id TEXT NOT NULL, scope TEXT NOT NULL DEFAULT 'global',"
        "commander_oracle_id TEXT NOT NULL DEFAULT '',"
        "bracket TEXT NOT NULL DEFAULT '', tier TEXT NOT NULL,"
        "score REAL, evidence REAL NOT NULL,"
        "signals_json TEXT NOT NULL DEFAULT '{}',"
        "algo_version TEXT NOT NULL, computed_at TEXT NOT NULL,"
        "input_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',"
        "PRIMARY KEY (oracle_id, scope, commander_oracle_id, bracket));")
    store.conn.execute(
        "INSERT INTO tier_assignment VALUES('x','global','','','A',0.9,"
        "1.0,'{}','tierlist/1.0.0','2026-11-12T00:00:00Z','[]')")
    store.conn.commit()
    tl.ensure_schema(store)
    cols = {r["name"] for r in store.conn.execute(
        "PRAGMA table_info(tier_assignment)")}
    assert "universe_id" in cols
    # The derived cache was dropped, not migrated row by row.
    assert store.conn.execute(
        "SELECT COUNT(*) FROM tier_assignment").fetchone()[0] == 0
