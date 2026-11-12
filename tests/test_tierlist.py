"""Tierlist tests — docs/TIERLIST_DESIGN.md as regression contract.

Synthetic fixtures only. The design rules under test: cohorts are
never mixed; missing signals are UNAVAILABLE, not 0; evidence gates
(U below 0.35, caps at B/A); the S gate; owner marks have NO effect
on any tier (byte-identical recompute after flipping every mark);
full reproducibility of a compute run; salt and price are markers
and never move a score.
"""
from __future__ import annotations

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import external as ext
from deckbuild_studio import tierlist as tl
from deckbuild_studio.importers import import_foundation_workbook

FC = "foundation-schwarze-box"
ALARA = OID["commander_a"]
RING = OID["sol_ring"]
PLAINS = OID["plains"]
FOREST = OID["forest"]


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


def _edhrec_global(store, oid, *, inclusion, num=100, potential=1000,
                   salt=None):
    snap = _snap(store, "edhrec", "edhrec_card", oracle_id=oid,
                 url=f"https://json.edhrec.com/pages/cards/x-{oid}.json")
    store.conn.execute(
        "INSERT INTO edhrec_card_global(snapshot_id,oracle_id,scryfall_id,"
        "num_decks,potential_decks,inclusion,salt) VALUES(?,?,?,?,?,?,?)",
        (snap, oid, None, num, potential, inclusion, salt))
    store.conn.commit()
    return snap


def _spellbook(store, oid, *, total=None, captured=0, coverage="TOTAL_KNOWN",
               status="AVAILABLE"):
    return _snap(store, "commanderspellbook", "spellbook_card",
                 oracle_id=oid, status=status, captured_count=captured,
                 displayed_total=total, coverage_status=coverage,
                 url=f"https://commanderspellbook.com/search/?q=x-{oid}",
                 payload={"combos_total": total, "combo_count": captured,
                          "partners": []})


def _atlas(store, oid, *, gap_pp, n_cast, n_never):
    return _snap(store, "playgroup", "playgroup_card", oracle_id=oid,
                 url=f"https://playgroup.gg/cards/x-{oid}",
                 payload={"name": "x", "fields": {"win_rates_observed": {
                     "observed_gap_pp": gap_pp, "n_cast": n_cast,
                     "n_never_drawn": n_never,
                     "win_rate_cast_pct": 30.0, "win_rate_never_drawn_pct": 25.0}}})


def _all_tier_rows(store):
    return [tuple(r) for r in store.conn.execute(
        "SELECT oracle_id, scope, commander_oracle_id, bracket, tier, "
        "score, evidence, signals_json, algo_version, "
        "input_snapshot_ids_json FROM tier_assignment "
        "ORDER BY oracle_id, scope, commander_oracle_id, bracket")]


# ---------------------------------------------------------------------------
# Band mappings + combination rule (pure)
# ---------------------------------------------------------------------------

def test_band_edges():
    assert tl.global_inclusion_subscore(0.30) == 1.00
    assert tl.global_inclusion_subscore(0.299) == 0.85
    assert tl.global_inclusion_subscore(0.0) == 0.00
    assert tl.global_inclusion_subscore(0.001) == 0.10
    assert tl.cohort_inclusion_subscore(0.60) == 1.00
    assert tl.cohort_inclusion_subscore(0.0) == 0.00
    assert tl.synergy_subscore(0.30) == 1.00
    assert tl.synergy_subscore(-0.20) == 0.15
    assert tl.combo_subscore(0) == 0.00
    assert tl.combo_subscore(2) == 0.30
    assert tl.combo_subscore(26) == 1.00
    assert tl.adjusted_lift(10.0, 50) == 5.0
    assert tl.lift_subscore(8.0) == 1.00
    assert tl.lift_subscore(-3.0) == 0.15


def _sig(name, weight, subscore):
    return {"signal": name, "weight": weight, "subscore": subscore,
            "available": subscore is not None}


def test_u_gate_below_evidence_035():
    # Only the combo signal (weight 0.20): even a perfect subscore is U.
    out = tl.combine([_sig("spellbook_combo_density", 0.20, 1.00),
                      _sig("edhrec_global_inclusion", 0.55, None),
                      _sig("playgroup_win_lift", 0.25, None)])
    assert out["tier"] == "U" and out["evidence"] == 0.20


def test_cap_b_and_a():
    # evidence 0.45 (playgroup + spellbook) caps at B despite score 1.0
    out = tl.combine([_sig("playgroup_win_lift", 0.25, 1.00),
                      _sig("spellbook_combo_density", 0.20, 1.00),
                      _sig("edhrec_global_inclusion", 0.55, None)])
    assert out["tier"] == "B"
    # evidence 0.55 (EDHREC inclusion only) caps at A despite score 1.0
    out = tl.combine([_sig("edhrec_global_inclusion", 0.55, 1.00),
                      _sig("playgroup_win_lift", 0.25, None),
                      _sig("spellbook_combo_density", 0.20, None)])
    assert out["tier"] == "A"


def test_s_gate_needs_a_strong_performance_signal():
    # Weighted score >= 0.85 but no signal >= 0.85 -> downgraded to A.
    out = tl.combine([_sig("edhrec_global_inclusion", 0.55, 0.84),
                      _sig("playgroup_win_lift", 0.25, 0.84),
                      _sig("spellbook_combo_density", 0.20, 1.00)])
    assert out["score"] >= 0.85 and out["tier"] == "A"
    # Same shape with one adoption signal at 1.00 -> S stands.
    out = tl.combine([_sig("edhrec_global_inclusion", 0.55, 1.00),
                      _sig("playgroup_win_lift", 0.25, 0.84),
                      _sig("spellbook_combo_density", 0.20, 0.84)])
    assert out["tier"] == "S"


# ---------------------------------------------------------------------------
# Global scope over stored snapshots
# ---------------------------------------------------------------------------

def test_global_tier_from_snapshots(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06, num=60, potential=1000,
                   salt=0.4)
    _atlas(store, RING, gap_pp=4.0, n_cast=300, n_never=500)
    _spellbook(store, RING, total=8, captured=8)
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING)
    assert row is not None and row["scope"] == "global"
    # Worked example of the design doc: 0.65/0.65/0.65, evidence 1.0 -> B
    # (the strength model is unchanged in tierlist/1.1.0; counted
    # decklist frequency is NOT one of its signals).
    assert row["tier"] == "B" and row["evidence"] == 1.0
    assert row["score"] == pytest.approx(0.65)
    signals = {s["signal"]: s for s in row["signals"]["signals"]}
    assert signals["edhrec_global_inclusion"]["value"]["num_decks"] == 60
    assert signals["playgroup_win_lift"]["semantics"].startswith(
        "observational")
    assert row["signals"]["markers"]["salt"] == 0.4
    assert row["signals"]["data_class"] == "HEURISTIC_MODEL"
    assert row["signals"]["field"] == "Evidenz-Tier (Stärke-Schätzung)"
    assert row["signals"]["missing_signals"] == []


def test_missing_signals_are_unavailable_not_zero(coll):
    store = coll
    # No snapshots at all for Forest: U, score NULL, evidence 0.
    tl.compute_tiers(store)
    row = tl.get_tier(store, FOREST)
    assert row["tier"] == "U" and row["score"] is None
    assert row["evidence"] == 0.0
    assert set(row["signals"]["missing_signals"]) == {
        "edhrec_global_inclusion", "playgroup_win_lift",
        "spellbook_combo_density"}
    assert row["signals"]["u_reason"] == "NO_OBSERVATION"


def test_measured_zero_is_data(coll):
    store = coll
    # Inclusion measured 0 and combo total measured 0 are evidence.
    _edhrec_global(store, PLAINS, inclusion=0.0, num=0, potential=1000)
    _spellbook(store, PLAINS, total=0, captured=0)
    tl.compute_tiers(store)
    row = tl.get_tier(store, PLAINS)
    assert row["tier"] == "D" and row["score"] == 0.0
    assert row["evidence"] == pytest.approx(0.75)


def test_playgroup_small_sample_unavailable(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06)
    _atlas(store, RING, gap_pp=12.0, n_cast=10, n_never=900)
    tl.compute_tiers(store)
    row = tl.get_tier(store, RING)
    signals = {s["signal"]: s for s in row["signals"]["signals"]}
    assert signals["playgroup_win_lift"]["available"] is False
    assert "insufficient data" in signals["playgroup_win_lift"]["reason"]


def test_spellbook_lower_bound_when_total_unknown(coll):
    store = coll
    _spellbook(store, RING, total=None, captured=4, coverage="TOTAL_UNKNOWN")
    signals = {s["signal"]: s for s in tl.global_signals(store, RING)}
    sb = signals["spellbook_combo_density"]
    assert sb["available"] is True and sb["subscore"] == 0.50
    assert sb["value"]["total_is_exact"] is False


def test_salt_and_price_never_move_the_score(coll):
    store = coll
    store.add_source(source_id="src-x", source_name="test bulk")
    for oid, salt, eur in ((RING, 2.9, 120.0), (PLAINS, 0.1, 0.20)):
        _edhrec_global(store, oid, inclusion=0.06, salt=salt)
        _spellbook(store, oid, total=8, captured=8)
        store.conn.execute(
            "INSERT INTO card_print_fact(oracle_id,prints_count,sets_count,"
            "rarities_json,min_rarity,first_release_year,last_release_year,"
            "min_eur,min_eur_printing,min_usd,min_usd_printing,source_id,"
            "parser_version,derived_at) VALUES(?,1,1,'[]',NULL,2020,2020,"
            "?,NULL,NULL,NULL,'src-x','test/1',datetime('now'))", (oid, eur))
    store.conn.commit()
    tl.compute_tiers(store)
    ring, plains = tl.get_tier(store, RING), tl.get_tier(store, PLAINS)
    assert ring["tier"] == plains["tier"] and ring["score"] == plains["score"]
    assert ring["signals"]["markers"]["salt_band"] == "high friction"
    assert plains["signals"]["markers"]["budget_band"] == "≤ €1"
    assert ring["signals"]["markers"]["budget_band"] == "> €15"


# ---------------------------------------------------------------------------
# Context scope: cohorts never mixed
# ---------------------------------------------------------------------------

def _cohort_stats(store, coid, bracket, rows):
    snap = _snap(store, "edhrec", "edhrec_stats", commander_oracle_id=coid,
                 bracket=bracket, slug="alara-test-sovereign",
                 url=f"https://edhrec.com/commanders/x/{bracket}")
    for name, inclusion, synergy in rows:
        store.conn.execute(
            "INSERT INTO edhrec_card_stat(snapshot_id,category,card_slug,"
            "name,scryfall_id,inclusion,num_decks,potential_decks,synergy,"
            "lift,trend_zscore) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (snap, "top", None, name, None, inclusion,
             int(inclusion * 100), 100, synergy, None, None))
    store.conn.commit()
    return snap


def test_context_tier_and_cohort_isolation(coll):
    store = coll
    _cohort_stats(store, ALARA, "core",
                  [("Sol Ring (Test)", 0.70, 0.40)])
    _cohort_stats(store, ALARA, "optimized",
                  [("Sol Ring (Test)", 0.01, -0.30)])
    global_before = tl.compute_tiers(store)
    core = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core")
    opt = tl.get_tier(store, RING, commander_oracle_id=ALARA,
                      bracket="optimized")
    # core: inclusion 1.00 + synergy 1.00, evidence 0.60 -> S band, cap A
    assert core["tier"] == "A" and core["evidence"] == pytest.approx(0.60)
    # optimized: 0.15 + 0.15 -> score 0.15, evidence 0.60 -> D
    assert opt["tier"] == "D"
    # The global tier ignores cohort stats entirely: still U (no
    # cohort-free signals were fetched).
    glob = tl.get_tier(store, RING)
    assert glob["tier"] == "U"
    assert global_before["global"]["tiers"] == {"U": 4}


def test_context_absent_without_fetched_data(coll):
    store = coll
    tl.compute_tiers(store)
    assert tl.get_tier(store, RING, commander_oracle_id=ALARA,
                       bracket="core") is None
    summary = tl.compute_tiers(store)
    assert summary["context"]["contexts_with_rated_cards"] == 0


# ---------------------------------------------------------------------------
# Marks isolation + reproducibility (design §5, §6)
# ---------------------------------------------------------------------------

def test_marks_never_change_tiers(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.40, salt=1.2)
    _spellbook(store, RING, total=30, captured=30)
    _atlas(store, RING, gap_pp=9.0, n_cast=800, n_never=900)
    tl.compute_tiers(store)
    before = _all_tier_rows(store)
    # Flip every kind of mark on every card.
    for oid in (RING, PLAINS, FOREST, ALARA):
        store.conn.execute(
            "INSERT OR REPLACE INTO mark(oracle_id,collection_id,favorite,"
            "excluded,note) VALUES(?,?,?,?,?)", (oid, FC, 1, 1, "flip"))
    store.conn.commit()
    tl.compute_tiers(store)
    assert _all_tier_rows(store) == before


def test_recompute_is_reproducible(coll):
    store = coll
    _edhrec_global(store, RING, inclusion=0.06)
    _spellbook(store, RING, total=8, captured=8)
    _cohort_stats(store, ALARA, "core", [("Sol Ring (Test)", 0.70, 0.40)])
    tl.compute_tiers(store)
    first = _all_tier_rows(store)
    tl.compute_tiers(store)
    assert _all_tier_rows(store) == first


# ---------------------------------------------------------------------------
# API surface
# ---------------------------------------------------------------------------

def test_tier_api(coll, monkeypatch):
    from fastapi.testclient import TestClient

    import deckbuild_studio.web as web_mod
    store = coll
    _edhrec_global(store, RING, inclusion=0.40)
    tl.compute_tiers(store)
    monkeypatch.setattr(web_mod, "database_path", lambda: store.path)
    client = TestClient(web_mod.create_app())
    card = client.get(f"/api/tiers/card/{RING}").json()
    assert card["global"]["tier"] in ("S", "A", "B", "C", "D", "U")
    assert card["global"]["signals"]["algo_version"] == tl.ALGO_VERSION
    lst = client.get("/api/tiers", params={"scope": "global"}).json()
    assert any(r["oracle_id"] == RING for r in lst)
    cards = client.get("/api/cards", params={"collection_id": FC}).json()
    ring = next(c for c in cards if c["oracle_id"] == RING)
    assert ring["tier"] is not None and ring["tier"]["tier"]
