"""Tierlist 1.2.0 tests — docs/TIERLIST_1_2_DESIGN.md as contract.

The design rules under test: the core model is untouched (1.1.0 rows
stay byte-identical and coexist); tournament signals are capped,
floored at the neutral 0.50 and asymmetric (absence is UNAVAILABLE,
never a 0, and never lowers a card's core result); the EDHTop16
commander signal is gated at entries_n >= 25; a signal switch removes
the component entirely; tournament weight alone cannot cross the U
gate; the S gate stays reserved for core signals; marks have no
effect under 1.2.0 either; the Verbreitung (gezählt) is identical
under both models.
"""
from __future__ import annotations

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import external as ext
from deckbuild_studio import settings as settings_mod
from deckbuild_studio import tierlist as tl
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.payloads import loads_payload

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


def _snap(store, source, kind, **kw):
    return ext.save_snapshot(
        store, source_name=source, kind=kind,
        url=kw.pop("url", f"https://example.invalid/{kind}"),
        status=kw.pop("status", "AVAILABLE"), **kw)


def _edhrec_global(store, oid, *, inclusion, num=100, potential=1000):
    snap = _snap(store, "edhrec", "edhrec_card", oracle_id=oid)
    store.conn.execute(
        "INSERT INTO edhrec_card_global(snapshot_id,oracle_id,scryfall_id,"
        "num_decks,potential_decks,inclusion,salt) VALUES(?,?,?,?,?,?,?)",
        (snap, oid, None, num, potential, inclusion, None))
    store.conn.commit()
    return snap


def _spellbook(store, oid, *, total):
    return _snap(store, "commanderspellbook", "spellbook_card",
                 oracle_id=oid, captured_count=total or 0,
                 displayed_total=total, coverage_status="TOTAL_KNOWN",
                 payload={"combos_total": total,
                          "combo_count": total or 0, "partners": []})


def _e16_global(store, oid, rate):
    snap = _snap(store, "edhtop16", "edhtop16_staples",
                 url="https://edhtop16.com/staples")
    store.conn.execute(
        "INSERT INTO edhtop16_card_stat(snapshot_id,card_name,"
        "card_oracle_id,card_type,mana_cost,play_rate_last_year) "
        "VALUES(?,?,?,?,?,?)",
        (snap, NAMES[oid], oid, "Artifact", "{1}", rate))
    store.conn.commit()
    return snap


def _e16_commander(store, coid, *, status="AVAILABLE", rows=(),
                   commander_entries=None):
    snap = _snap(store, "edhtop16", "edhtop16_commander_staples",
                 commander_oracle_id=coid, status=status,
                 url="https://edhtop16.com/commander/x")
    for oid, rate, entries in rows:
        store.conn.execute(
            "INSERT INTO edhtop16_commander_card_stat(snapshot_id,"
            "commander_oracle_id,commander_name,card_name,card_oracle_id,"
            "play_rate,entries_n,window) VALUES(?,?,?,?,?,?,?,?)",
            (snap, coid, NAMES[coid], NAMES[oid], oid, rate, entries,
             "ONE_YEAR"))
    if commander_entries is not None:
        # The commander-level aggregate row the real importer always
        # writes alongside the card rows (edhtop16_commander_stat).
        store.conn.execute(
            "INSERT INTO edhtop16_commander_stat(snapshot_id,"
            "commander_oracle_id,commander_name,entries_n,"
            "conversion_rate,meta_share,window) VALUES(?,?,?,?,?,?,?)",
            (snap, coid, NAMES[coid], commander_entries, None, None,
             "ONE_YEAR"))
    store.conn.commit()
    return snap


def _topdeck(store, *, decks=100, reached=25, cards=()):
    """One TopDeck snapshot whose deck-level baseline conversion is
    exactly reached/decks; cards are (oid, decks_with, decks_in_cut,
    top_cut_decks, conversion_rate|None)."""
    snap = _snap(store, "topdeck", "topdeck_tournaments",
                 url="https://topdeck.gg/api/v2/tournaments")
    for i in range(decks):
        # topdeck_result.deck_uid references decklist_deck (the sync
        # stores the tournament decks there, cohort 'topdeck').
        store.conn.execute(
            "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
            "commander_oracle_id,commander_name,bracket_level,"
            "bracket_source,source_url,status,parser_version,sha256,"
            "raw_path,fetched_at,source_updated_at,deck_size,"
            "card_entries,mapped_cards,unmapped_cards,"
            "unmapped_names_json,detail) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"td:{i}", "topdeck", str(i), ALARA, NAMES[ALARA], None,
             "topdeck_tournament", "https://topdeck.gg", "AVAILABLE",
             "topdeck-tournaments/1.0.0", None, None,
             "2026-11-12T00:00:00Z", None, 100, 100, 100, 0, "[]", ""))
        store.conn.execute(
            "INSERT INTO topdeck_result(deck_uid,snapshot_id,tid,"
            "player_name,player_id,wins,draws,losses,wins_bracket,"
            "losses_bracket,top_cut_reached,deck_source) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"td:{i}", snap, "t1", f"p{i}", None, 3, 0, 2, None, None,
             1 if i < reached else 0, "topdeck_tournament"))
    for oid, dw, dic, tcd, conv in cards:
        games = dw * 5
        store.conn.execute(
            "INSERT INTO topdeck_card_stat(snapshot_id,card_name,"
            "card_oracle_id,decks_with,decks_in_cut,top_cut_decks,"
            "conversion_rate,wins,draws,losses,games,win_rate) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (snap, NAMES[oid], oid, dw, dic, tcd, conv,
             int(games * 0.4), 0, int(games * 0.6), games, None))
    store.conn.commit()
    return snap


def _cohort_stats(store, coid, bracket, rows):
    snap = _snap(store, "edhrec", "edhrec_stats", commander_oracle_id=coid,
                 bracket=bracket, slug="alara-test-sovereign")
    for name, inclusion, synergy in rows:
        store.conn.execute(
            "INSERT INTO edhrec_card_stat(snapshot_id,category,card_slug,"
            "name,scryfall_id,inclusion,num_decks,potential_decks,synergy,"
            "lift,trend_zscore) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (snap, "top", None, name, None, inclusion,
             int(inclusion * 100), 100, synergy, None, None))
    store.conn.commit()
    return snap


def _deck(store, uid, bracket, rows, commander=ALARA):
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,"
        "source_url,status,parser_version,sha256,raw_path,fetched_at,"
        "source_updated_at,deck_size,card_entries,mapped_cards,"
        "unmapped_cards,unmapped_names_json,detail) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, "archidekt", uid.split(":", 1)[1], commander,
         NAMES[commander], bracket, "archidekt_edhBracket",
         "https://archidekt.com/decks/x", "AVAILABLE",
         "archidekt-deck/1.0.0", None, None, "2026-11-12T00:00:00Z", None,
         sum(q for _, q, _ in rows), len(rows), len(rows), 0, "[]", ""))
    for oid, qty, is_cmd in rows:
        store.conn.execute(
            "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,"
            "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)",
            (uid, oid, oid, NAMES[oid], qty, is_cmd))
    store.conn.commit()


def _rows(store, version):
    return [tuple(r) for r in store.conn.execute(
        "SELECT oracle_id, scope, commander_oracle_id, bracket, "
        "universe_id, tier, score, evidence, signals_json, "
        "input_snapshot_ids_json FROM tier_assignment "
        "WHERE algo_version=? ORDER BY oracle_id, scope, "
        "commander_oracle_id, bracket, universe_id", (version,))]


def _signals(row):
    return {s["signal"]: s for s in row["signals"]["signals"]}


M12 = tl.MODEL_1_2_0
M11 = tl.MODEL_1_1_0


# ---------------------------------------------------------------------------
# Pure mappings: bands, floor, shrinkage
# ---------------------------------------------------------------------------

def test_tournament_mappings_and_floor():
    assert tl.edhtop16_play_rate_subscore(0.30) == 0.95
    assert tl.edhtop16_play_rate_subscore(0.299) == 0.90
    assert tl.edhtop16_play_rate_subscore(0.02) == 0.60
    assert tl.edhtop16_play_rate_subscore(0.0001) == tl.TOURNAMENT_FLOOR
    assert tl.edhtop16_commander_play_rate_subscore(0.60) == 0.95
    assert tl.edhtop16_commander_play_rate_subscore(0.001) == 0.50
    assert tl.topdeck_conversion_subscore(1.30) == 0.95
    assert tl.topdeck_conversion_subscore(1.00) == 0.58
    assert tl.topdeck_conversion_subscore(0.40) == tl.TOURNAMENT_FLOOR
    # Shrinkage: (0.5*40 + 0.25*50) / 90 = 0.3611; at n=K half earned.
    assert tl.topdeck_adjusted_conversion(0.5, 40, 0.25) == \
        pytest.approx(0.3611, abs=1e-4)
    assert tl.topdeck_adjusted_conversion(0.9, 50, 0.25) == \
        pytest.approx((0.9 + 0.25) / 2)


def test_evidence_clamped_at_one():
    out = tl.combine([
        {"signal": "edhrec_global_inclusion", "weight": 0.55,
         "subscore": 1.0, "available": True},
        {"signal": "playgroup_win_lift", "weight": 0.25,
         "subscore": 1.0, "available": True},
        {"signal": "spellbook_combo_density", "weight": 0.20,
         "subscore": 1.0, "available": True},
        {"signal": "edhtop16_play_rate", "weight": 0.10,
         "subscore": 0.95, "available": True},
        {"signal": "topdeck_conversion", "weight": 0.10,
         "subscore": 0.95, "available": True}])
    assert out["evidence"] == 1.0 and out["tier"] == "S"


def test_s_gate_stays_core_only():
    # Score in the S band (0.86) built from combo 1.00 (not a gate
    # signal) + tournament 0.95: still A. Adding a core gate signal
    # at >= 0.85 makes it S.
    base = [
        {"signal": "edhrec_global_inclusion", "weight": 0.55,
         "subscore": 0.84, "available": True},
        {"signal": "playgroup_win_lift", "weight": 0.25,
         "subscore": 0.80, "available": True},
        {"signal": "spellbook_combo_density", "weight": 0.20,
         "subscore": 1.00, "available": True},
        {"signal": "topdeck_conversion", "weight": 0.10,
         "subscore": 0.95, "available": True}]
    out = tl.combine(base)
    assert out["score"] >= 0.85 and out["tier"] == "A"
    base[0] = {**base[0], "subscore": 0.85}
    assert tl.combine(base)["tier"] == "S"


# ---------------------------------------------------------------------------
# Global scope: presence, absence, asymmetry
# ---------------------------------------------------------------------------

def test_1_2_global_signals_present_and_absent(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06)
    _spellbook(store, RING, total=8)
    _e16_global(store, RING, 0.35)
    _topdeck(store, cards=[(RING, 900, 40, 20, 0.5),
                           (PLAINS, 30, 5, 1, None)])
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING)
    sig = _signals(ring)
    assert sig["edhtop16_play_rate"]["available"] is True
    assert sig["edhtop16_play_rate"]["subscore"] == 0.95
    assert sig["edhtop16_play_rate"]["value"]["play_rate_last_year"] == 0.35
    td = sig["topdeck_conversion"]
    assert td["available"] is True
    assert td["value"]["cohort_baseline"] == pytest.approx(0.25)
    assert td["value"]["n"] == 40
    assert td["value"]["adjusted_conversion"] == pytest.approx(0.3611,
                                                              abs=1e-4)
    assert td["subscore"] == 0.95  # ratio 1.444
    # Plains: in tournament decks but below the source's sample gate.
    plains = tl.get_tier(store, PLAINS)
    psig = _signals(plains)
    assert psig["topdeck_conversion"]["available"] is False
    assert "insufficient data" in psig["topdeck_conversion"]["reason"]
    assert psig["edhtop16_play_rate"]["available"] is False
    assert "never scored as 0" in psig["edhtop16_play_rate"]["reason"]


def test_absence_is_neutral(coll):
    store = coll
    _edhrec_global(store, PLAINS, inclusion=0.06)
    _spellbook(store, PLAINS, total=8)
    tl.compute_tiers(store, model=M12)
    # (tier, score, evidence) of the global row — the payload's
    # provenance text legitimately changes once a snapshot exists;
    # the RESULT for a card without tournament data must not.
    def pick():
        return [(r[5], r[6], r[7]) for r in _rows(store, M12)
                if r[0] == PLAINS and r[1] == "global"]
    before = pick()
    # Tournament layers appear, but only with data for OTHER cards.
    _e16_global(store, RING, 0.59)
    _topdeck(store, cards=[(RING, 900, 40, 30, 0.75)])
    tl.compute_tiers(store, model=M12)
    assert pick() == before


def test_tournament_only_card_stays_u(coll):
    store = coll
    # Forest carries ONLY tournament data (strong values).
    _e16_global(store, FOREST, 0.59)
    _topdeck(store, cards=[(FOREST, 900, 500, 400, 0.80)])
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    row = tl.get_tier(store, FOREST)
    # evidence 0.20 < 0.35: tournament weight alone never crosses U.
    assert row["tier"] == "U" and row["evidence"] == pytest.approx(0.20)
    assert row["signals"]["u_reason"] == "INSUFFICIENT_EVIDENCE"


def test_below_baseline_conversion_floors_not_punishes(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06)
    _spellbook(store, RING, total=8)
    _topdeck(store, cards=[(RING, 900, 40, 4, 0.10)])
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    sig = _signals(tl.get_tier(store, RING))["topdeck_conversion"]
    assert sig["available"] is True
    assert sig["subscore"] == tl.TOURNAMENT_FLOOR
    assert sig["value"]["ratio_to_baseline"] < 1.0


# ---------------------------------------------------------------------------
# Context scope: the entries_n gate + NOT_FOUND honesty
# ---------------------------------------------------------------------------

def test_commander_signal_gate_and_not_found(coll):
    store = coll
    _cohort_stats(store, ALARA, "core",
                  [("Sol Ring (Test)", 0.70, 0.40), ("Plains", 0.50, 0.0)])
    _e16_commander(store, ALARA, rows=[(RING, 0.90, 24),
                                       (PLAINS, 0.90, 25)])
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core")
    rsig = _signals(ring)["edhtop16_commander_play_rate"]
    assert rsig["available"] is False
    assert "entries_n=24 < 25" in rsig["reason"]
    plains = tl.get_tier(store, PLAINS, commander_oracle_id=ALARA,
                         bracket="core")
    psig = _signals(plains)["edhtop16_commander_play_rate"]
    assert psig["available"] is True and psig["subscore"] == 0.95
    assert psig["value"]["entries_n"] == 25


def test_commander_signal_not_found_reason(coll):
    store = coll
    _cohort_stats(store, ALARA, "core", [("Sol Ring (Test)", 0.70, 0.40)])
    _e16_commander(store, ALARA, status="NOT_FOUND")
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core")
    sig = _signals(ring)["edhtop16_commander_play_rate"]
    assert sig["available"] is False
    assert "NOT_FOUND" in sig["reason"]


def test_commander_gate_reason_distinguishes_absent_card(coll):
    # PR17-F3 / #37: for a card with no row of its own, the reason
    # must name the commander-level gate when the COMMANDER is below
    # it — "not in his staples list" would mask the real cause. The
    # listed-but-gated card keeps the plain gate reason, and only
    # the text may differ: tier/score/evidence stay identical.
    store = coll
    _cohort_stats(store, ALARA, "core",
                  [("Sol Ring (Test)", 0.70, 0.40), ("Plains", 0.50, 0.0)])
    _e16_commander(store, ALARA, rows=[(RING, 0.90, 10)],
                   commander_entries=10)
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)

    def ctx(oid):
        return tl.get_tier(store, oid, commander_oracle_id=ALARA,
                           bracket="core")

    # Listed card, commander below the gate: unchanged gate reason.
    rsig = _signals(ctx(RING))["edhtop16_commander_play_rate"]
    assert rsig["available"] is False
    assert rsig["reason"] == "insufficient data: entries_n=10 < 25"
    # Absent card, same commander: the commander-level gate is the
    # reported cause, not a listing absence.
    plains = ctx(PLAINS)
    psig = _signals(plains)["edhtop16_commander_play_rate"]
    assert psig["available"] is False
    assert "entries_n=10 < 25" in psig["reason"]
    assert "commander-level gate" in psig["reason"]
    assert "not in this commander's published" not in psig["reason"]
    result_before = (plains["tier"], plains["score"], plains["evidence"])
    # Without the commander-level aggregate the gate cannot be
    # asserted: the absence wording returns — and the RESULT
    # (tier/score/evidence) is byte-identical, only the text moved.
    store.conn.execute("DELETE FROM edhtop16_commander_stat")
    store.conn.commit()
    tl.compute_tiers(store, model=M12)
    plains2 = ctx(PLAINS)
    psig2 = _signals(plains2)["edhtop16_commander_play_rate"]
    assert psig2["available"] is False
    assert psig2["reason"] == (
        "not in this commander's published EDHTop16 staples list "
        "(absence is never scored as 0)")
    assert (plains2["tier"], plains2["score"],
            plains2["evidence"]) == result_before


def test_commander_gate_reason_zero_entries_commander(coll):
    # A zero-entries commander has NO card rows at all (the importer
    # withholds them — the API's global-fallback guard), so every
    # card used to read as "not listed". The gate is the cause.
    store = coll
    _cohort_stats(store, ALARA, "core", [("Sol Ring (Test)", 0.70, 0.40)])
    _e16_commander(store, ALARA, rows=(), commander_entries=0)
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core")
    sig = _signals(ring)["edhtop16_commander_play_rate"]
    assert sig["available"] is False
    assert "entries_n=0 < 25" in sig["reason"]
    assert "commander-level gate" in sig["reason"]


def test_commander_absence_reason_kept_above_gate(coll):
    # Commander ABOVE the gate: an absent card is a plain listing
    # absence (Fall A) and keeps the original wording; the listed
    # card is available as before.
    store = coll
    _cohort_stats(store, ALARA, "core",
                  [("Sol Ring (Test)", 0.70, 0.40), ("Plains", 0.50, 0.0)])
    _e16_commander(store, ALARA, rows=[(RING, 0.90, 77)],
                   commander_entries=77)
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core")
    rsig = _signals(ring)["edhtop16_commander_play_rate"]
    assert rsig["available"] is True and rsig["subscore"] == 0.95
    plains = tl.get_tier(store, PLAINS, commander_oracle_id=ALARA,
                         bracket="core")
    psig = _signals(plains)["edhtop16_commander_play_rate"]
    assert psig["available"] is False
    assert psig["reason"] == (
        "not in this commander's published EDHTop16 staples list "
        "(absence is never scored as 0)")


# ---------------------------------------------------------------------------
# Settings: toggles remove components; validation; model selection
# ---------------------------------------------------------------------------

def test_signal_switch_removes_component(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06)
    _topdeck(store, cards=[(RING, 900, 40, 20, 0.5)])
    settings_mod.set_setting(store, "tierlist.signal_topdeck_conversion",
                             False)
    tl.compute_tiers(store, model=M12)
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    ring = tl.get_tier(store, RING)
    names = [s["signal"] for s in ring["signals"]["signals"]]
    assert "topdeck_conversion" not in names
    # The EDHTop16 toggle defaults on but no data -> stays UNAVAILABLE
    # (component listed as missing, exactly like an unfetched core
    # signal); only the switch removes a component.
    assert "edhtop16_play_rate" in names


def test_settings_validation():
    from deckbuild_studio.settings import SettingError
    with pytest.raises(SettingError):
        settings_mod.validate_setting("tierlist.signal_topdeck_conversion",
                                      "yes")
    with pytest.raises(SettingError):
        settings_mod.validate_setting("tierlist.model_version",
                                      "tierlist/9.9.9")
    assert settings_mod.validate_setting(
        "tierlist.model_version", M12) == M12
    assert settings_mod.validate_setting(
        "tierlist.signal_edhtop16_global", False) is False


def test_versions_coexist_and_1_1_0_is_unchanged(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.40)
    _spellbook(store, RING, total=30)
    _e16_global(store, RING, 0.35)
    _topdeck(store, cards=[(RING, 900, 40, 20, 0.5)])
    tl.compute_tiers(store, model=M11)
    rows_11 = _rows(store, M11)
    tl.compute_tiers(store, model=M12)
    # 1.1.0 rows untouched by the 1.2.0 run; 1.1.0 payloads carry no
    # tournament component at all.
    assert _rows(store, M11) == rows_11
    ring_11 = next(r for r in rows_11 if r[0] == RING and r[1] == "global")
    # signals_json is read through the payload codec (storage may be
    # gzip+b64-compressed; the decoded content is what must be stable).
    payload = loads_payload(ring_11[8])
    assert [s["signal"] for s in payload["signals"]] == [
        "edhrec_global_inclusion", "playgroup_win_lift",
        "spellbook_combo_density"]
    # Read API serves the selected version.
    assert tl.get_tier(store, RING)["algo_version"] == M11
    settings_mod.set_setting(store, "tierlist.model_version", M12)
    assert tl.get_tier(store, RING)["algo_version"] == M12


def test_marks_invariance_1_2(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.40)
    _spellbook(store, RING, total=30)
    _e16_global(store, RING, 0.35)
    _topdeck(store, cards=[(RING, 900, 40, 20, 0.5)])
    tl.compute_tiers(store, model=M12)
    before = _rows(store, M12)
    for oid in (RING, PLAINS, FOREST, ALARA):
        store.conn.execute(
            "INSERT OR REPLACE INTO mark(oracle_id,collection_id,favorite,"
            "excluded,note) VALUES(?,?,?,?,?)", (oid, FC, 1, 1, "flip"))
    store.conn.commit()
    tl.compute_tiers(store, model=M12)
    assert _rows(store, M12) == before


def test_external_card_api_carries_new_blocks(coll, monkeypatch):
    from fastapi.testclient import TestClient

    import deckbuild_studio.web as web_mod
    store = coll
    _e16_commander(store, ALARA, rows=[(RING, 0.42, 77)])
    snap = _snap(store, "mtgjson", "mtgjson_printings")
    for lang, name, set_code in (("English", "Sol Ring (Test)", "C19"),
                                 ("German", "Sonnenring", "C19")):
        store.conn.execute(
            "INSERT INTO mtgjson_print(snapshot_id,mtgjson_uuid,oracle_id,"
            "scryfall_id,set_code,collector_number,card_name,language,"
            "multiverse_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (snap, f"uuid-{lang}", RING, None, set_code, "1", name, lang,
             None))
    store.conn.commit()
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    d = client.get("/api/external/card",
                   params={"oracle_id": RING}).json()
    cmds = d["edhtop16_commanders"]["commanders"]
    assert len(cmds) == 1 and cmds[0]["play_rate"] == 0.42
    assert cmds[0]["entries_n"] == 77
    assert d["mtgjson"]["prints_total"] == 2
    assert d["mtgjson"]["foreign_names"] == [
        {"language": "German", "name": "Sonnenring"}]
    # Settings round-trip through the API (bool kind + model enum).
    r = client.put("/api/settings",
                   json={"tierlist.model_version": M12,
                         "tierlist.signal_topdeck_conversion": False})
    assert r.status_code == 200
    got = r.json()["settings"]
    assert got["tierlist.model_version"]["value"] == M12
    assert got["tierlist.signal_topdeck_conversion"]["value"] is False
    bad = client.put("/api/settings",
                     json={"tierlist.signal_topdeck_conversion": "yes"})
    assert bad.status_code == 400


def test_verbreitung_identical_under_both_models(coll):
    store = coll
    for i in range(35):
        rows = [(ALARA, 1, 1), (PLAINS, 20 + i, 0), (RING, 1, 0)]
        _deck(store, f"archidekt:{i:04d}", 3, rows)
    tl.compute_tiers(store, model=M11)
    uni_11 = [r for r in _rows(store, M11) if r[1] == "universe"]
    tl.compute_tiers(store, model=M12)
    uni_12 = [r for r in _rows(store, M12) if r[1] == "universe"]
    # Same profiles, same tiers/scores — only the version label and
    # payload header may differ, never a counted value.
    def key(r):
        return (r[0], r[2], r[3], r[4])
    by_11 = {key(r): (r[5], r[6]) for r in uni_11}
    by_12 = {key(r): (r[5], r[6]) for r in uni_12}
    assert by_11 and by_11 == by_12
