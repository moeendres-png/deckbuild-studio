"""TRANSFER-1 (issue #43) — fail-closed universe-selection validation
at the tierlist compute entry (the CPL universe-spec rule: an unknown
name in a selection spec is a refusal, not an empty result).

Stored settings reach compute_tiers via resolve()/get_setting, which
tolerate unreadable rows by design; a parseable yet INVALID selection
written around set_setting (hand-edited DB, foreign tool, legacy row)
must be refused BEFORE any row is computed or deleted — before this
fix it silently computed an empty selection, which deleted every
universe row of the model version and reported the misleading note
"no harvested deck lists". A valid selection computes exactly as
before (validation only, no normalisation).

The raw writes below bypass set_setting on purpose: they are the gap
under test. Seeding mirrors tests/test_tierlist_cpl.py.
"""
from __future__ import annotations

import json

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import settings as settings_mod
from deckbuild_studio import tierlist as tl
from deckbuild_studio.importers import import_foundation_workbook

FC = "foundation-schwarze-box"
ALARA = OID["commander_a"]
PLAINS = OID["plains"]
NAMES = {ALARA: "Alara, Test Sovereign", PLAINS: "Plains"}


@pytest.fixture()
def coll(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [
        ("Alara, Test Sovereign", 1, "Foundation"),
        ("Plains", 60, "Foundation"),
    ])
    import_foundation_workbook(loaded_store, path)
    # 35 distinct archidekt decks, bracket 3 — a counted universe
    # above the default minimum size (30).
    for i in range(35):
        uid = f"archidekt:{i:04d}"
        rows = [(ALARA, 1, 1), (PLAINS, 20 + i, 0)]
        loaded_store.conn.execute(
            "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
            "commander_oracle_id,commander_name,bracket_level,"
            "bracket_source,source_url,status,parser_version,sha256,"
            "raw_path,fetched_at,source_updated_at,deck_size,"
            "card_entries,mapped_cards,unmapped_cards,"
            "unmapped_names_json,detail) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, "archidekt", f"{i:04d}", ALARA, NAMES[ALARA], 3,
             "archidekt_edhBracket", f"https://archidekt.com/decks/{i}",
             "AVAILABLE", "archidekt-deck/1.0.0", None, None,
             "2026-11-12T00:00:00Z", "2026-11-10T00:00:00Z",
             2, 2, 2, 0, "[]", ""))
        for oid, qty, is_cmd in rows:
            loaded_store.conn.execute(
                "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,"
                "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)",
                (uid, oid, oid, NAMES[oid], qty, is_cmd))
    loaded_store.conn.commit()
    return loaded_store


def _set_raw(store, key, value):
    """Write an app_setting row directly (around set_setting)."""
    store.conn.execute(
        "INSERT OR REPLACE INTO app_setting(key,value_json,updated_at) "
        "VALUES(?,?,?)", (key, json.dumps(value), "2026-11-13T00:00:00Z"))
    store.conn.commit()


def _universe_rows(store):
    return store.conn.execute(
        "SELECT oracle_id, commander_oracle_id, bracket, universe_id, "
        "tier, score, evidence, signals_json, algo_version, "
        "input_snapshot_ids_json FROM tier_assignment "
        "WHERE scope='universe' ORDER BY universe_id, oracle_id"
    ).fetchall()


def _total_rows(store):
    return store.conn.execute(
        "SELECT COUNT(*) c FROM tier_assignment").fetchone()["c"]


def test_unknown_platform_refused_before_any_delete(coll):
    tl.compute_tiers(coll)
    before = _universe_rows(coll)
    assert before  # the valid baseline produced universe rows
    total_before = _total_rows(coll)
    _set_raw(coll, "inclusion.platforms", ["archidekt2"])
    with pytest.raises(settings_mod.SettingError, match="unknown platform"):
        tl.compute_tiers(coll)
    # Nothing was deleted or recomputed: the refusal precedes all work,
    # on the full AND on the scoped compute path.
    assert _universe_rows(coll) == before
    assert _total_rows(coll) == total_before
    with pytest.raises(settings_mod.SettingError):
        tl.compute_tiers(coll, commander_oracle_id=ALARA)
    assert _universe_rows(coll) == before


@pytest.mark.parametrize("key,value", [
    ("inclusion.platforms", []),
    ("inclusion.brackets", []),
    ("inclusion.platforms", None),
    ("inclusion.brackets", [9]),
    ("inclusion.brackets", [0]),
    ("inclusion.brackets", ["3"]),
    ("inclusion.max_age_days", "30"),
    ("inclusion.max_age_days", -5),
    ("tierlist.min_universe", "abc"),
    ("tierlist.min_universe", 0),
    ("inclusion.date_from", "not-a-date"),
    ("inclusion.date_to", "2026-13-01"),
])
def test_invalid_selection_values_refused(coll, key, value):
    _set_raw(coll, key, value)
    with pytest.raises(settings_mod.SettingError):
        tl.compute_tiers(coll)


def test_reversed_period_refused(coll):
    _set_raw(coll, "inclusion.date_from", "2027-01-01")
    _set_raw(coll, "inclusion.date_to", "2026-01-01")
    with pytest.raises(settings_mod.SettingError, match="empty period"):
        tl.compute_tiers(coll)


def test_valid_stored_selection_computes_identically(coll):
    tl.compute_tiers(coll)
    before = _universe_rows(coll)
    assert before
    # An explicit stored selection equal to the catalogue defaults is
    # valid and must compute byte-identically (validation only).
    _set_raw(coll, "inclusion.platforms", ["archidekt"])
    _set_raw(coll, "inclusion.brackets", [2, 3, 4])
    _set_raw(coll, "tierlist.min_universe", 30)
    summary = tl.compute_tiers(coll)
    assert summary["universe"]["rows"] == len(before)
    assert _universe_rows(coll) == before


def test_valid_unsorted_brackets_accepted(coll):
    baseline = tl.compute_tiers(coll)
    _set_raw(coll, "inclusion.brackets", [4, 2, 3])
    summary = tl.compute_tiers(coll)  # must not raise, must not normalise
    assert summary["universe"]["denominators"] == \
        baseline["universe"]["denominators"]
    assert summary["universe"]["rows"] == baseline["universe"]["rows"]


def test_unparseable_selection_row_refused(coll):
    # FIX-7: a selection row that is not even JSON leaves the
    # selection unknown — the compute must refuse, not fall back
    # to a default selection and recompute with it.
    coll.conn.execute(
        "INSERT OR REPLACE INTO app_setting(key,value_json,updated_at) "
        "VALUES('tierlist.min_universe','{oops','2026-11-13T00:00:00Z')")
    coll.conn.commit()
    with pytest.raises(settings_mod.SettingError):
        tl.compute_tiers(coll)
