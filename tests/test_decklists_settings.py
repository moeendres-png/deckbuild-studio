"""Decklist harvest (Archidekt), owner settings, inclusion engine.

Fixtures are trimmed REAL Archidekt payloads (public deck/search JSON,
recorded 2026-11-12); all fetching is stubbed — no network in tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import settings as settings_mod
from deckbuild_studio.decklists import (decklist_coverage, parse_deck_detail,
                                        parse_list_page, sync_decklists)
from deckbuild_studio.httpfetch import Response
from deckbuild_studio.inclusion import compute_inclusion
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook

FIXTURES = Path(__file__).parent / "fixtures"
DECK_JSON = (FIXTURES / "archidekt_deck.json").read_text(encoding="utf-8")
LIST_JSON = (FIXTURES / "archidekt_list.json").read_text(encoding="utf-8")

SAMI = "c4175a34-70bb-47e5-8406-efdc4d2cd079"          # fixture deck commander
TEMPLE = "6f0d94d9-64bb-4175-83bc-301e8f79f54f"        # Temple of Triumph
CMD_TOWER = "0895c9b7-ae7d-4bb3-af17-3b75deb50a25"     # Command Tower


def _register_cards(store):
    """Make the fixture deck's oracle uids known to the local store."""
    for oid, name in [(SAMI, "Sami, Wildcat Captain"),
                      (TEMPLE, "Temple of Triumph"),
                      (CMD_TOWER, "Command Tower"),
                      ("8e7641e1-e814-4d5a-9cb3-71ad2f4ceee8", "Rugged Prairie"),
                      ("8dc067bf-f78f-4ac4-b6e7-b305c42cf0bc", "Darksteel Citadel")]:
        store.conn.execute(
            "INSERT OR REPLACE INTO scryfall_card(oracle_id,name,color_identity)"
            " VALUES(?,?,?)", (oid, name, ""))
    store.conn.commit()


class StubFetcher:
    """Routes Archidekt URLs to canned payloads; counts detail fetches."""

    def __init__(self, cohorts: dict[int, list[int]]):
        self.cohorts = cohorts  # bracket -> deck ids
        self.detail_calls = 0
        self.list_calls = 0

    def get(self, url, **kw):
        if "/api/decks/v3/" in url:
            self.list_calls += 1
            bracket = int(url.split("edhBracket=")[1].split("&")[0])
            page = int(url.rsplit("page=", 1)[1])
            ids = self.cohorts.get(bracket, [])
            rows = [{"id": i, "edhBracket": bracket, "size": 100}
                    for i in ids] if page == 1 else []
            body = json.dumps({"count": len(ids), "next": None,
                               "results": rows}).encode()
            return Response(status=200, body=body, url=url)
        if "/api/decks/" in url:
            self.detail_calls += 1
            return Response(status=200, body=DECK_JSON.encode(), url=url)
        raise AssertionError(f"unexpected URL {url}")


@pytest.fixture()
def harvested(store):
    _register_cards(store)
    fetcher = StubFetcher({3: [9001, 9002, 9003], 2: [8001, 8002]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(2, 3),
                            max_per_cohort=300)
    return store, fetcher, report


def _store_synthetic_deck(store, uid, bracket, rows, commander=SAMI):
    """Store one harvested deck directly: rows are
    (oracle_id, name, quantity, is_commander). Bypasses the fetcher so
    tests can build decks with distinct or identical content."""
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,"
        "source_url,status,parser_version,sha256,raw_path,fetched_at,"
        "deck_size,card_entries,mapped_cards,unmapped_cards,"
        "unmapped_names_json,detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, "archidekt", uid.split(":", 1)[1], commander,
         "Sami, Wildcat Captain", bracket, "archidekt_edhBracket",
         f"https://archidekt.com/decks/{uid.split(':', 1)[1]}",
         "AVAILABLE", "archidekt-deck/1.0.0", None, None,
         "2026-11-12T00:00:00Z", sum(q for _, _, q, _ in rows),
         len(rows), len(rows), 0, "[]", ""))
    for oid, name, qty, is_cmd in rows:
        store.conn.execute(
            "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,card_name,"
            "quantity,is_commander) VALUES(?,?,?,?,?,?)",
            (uid, oid, oid, name, qty, is_cmd))
    store.conn.commit()


# ---------------------------------------------------------------- parsing

def test_parse_list_page_fixture():
    page = parse_list_page(LIST_JSON)
    assert page["count"] == 267
    assert len(page["results"]) == 3
    assert all(r["edh_bracket"] == 3 for r in page["results"])


def test_parse_deck_detail_excludes_maybeboard_and_flags_commander():
    parsed = parse_deck_detail(DECK_JSON)
    names = {e["name"] for e in parsed["entries"]}
    assert "Unwinding Clock" not in names          # Maybeboard excluded
    assert "Sami, Wildcat Captain" in names
    sami = next(e for e in parsed["entries"] if e["name"] == "Sami, Wildcat Captain")
    assert sami["is_commander"] == 1
    assert sami["oracle_id"] == SAMI
    unmapped = next(e for e in parsed["entries"] if e["name"] == "Unmapped Test Card Zzz")
    assert unmapped["oracle_id"] is None


# ---------------------------------------------------------------- harvest

def test_harvest_stores_decks_with_provenance_and_mapping(harvested):
    store, fetcher, report = harvested
    assert report["totals"]["available"] == 5
    assert report["totals"]["listed"] == 5
    row = store.conn.execute(
        "SELECT * FROM decklist_deck WHERE deck_uid='archidekt:9001'").fetchone()
    assert row["status"] == "AVAILABLE"
    assert row["platform"] == "archidekt"
    assert row["bracket_level"] == 3
    assert row["bracket_source"] == "archidekt_edhBracket"
    assert row["commander_oracle_id"] == SAMI
    assert row["sha256"] and row["raw_path"]
    # mapping: 5 of 6 counted entries resolve to oracle ids; the name-only
    # entry is counted + named, never silently dropped
    assert row["mapped_cards"] == 5 and row["unmapped_cards"] == 1
    assert json.loads(row["unmapped_names_json"]) == ["Unmapped Test Card Zzz"]
    cov = decklist_coverage(store)
    assert cov["totals"]["available"] == 5
    assert cov["totals"]["mapped_cards"] == 25 and cov["totals"]["unmapped_cards"] == 5


def test_harvest_is_resumable_without_refetch(harvested):
    store, fetcher, _ = harvested
    before = fetcher.detail_calls
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(2, 3))
    assert fetcher.detail_calls == before          # zero new detail fetches
    assert report["totals"]["cached"] == 5
    assert report["totals"]["fetched"] == 0


class ErrFetcher:
    """Bracket 3: one 404 + one good deck. Bracket 2: twelve 403s."""

    def get(self, url, **kw):
        if "/api/decks/v3/" in url:
            bracket = int(url.split("edhBracket=")[1].split("&")[0])
            page = int(url.rsplit("page=", 1)[1])
            ids = {3: [7001, 7002], 2: list(range(6001, 6013))}.get(bracket, [])
            rows = [{"id": i, "edhBracket": bracket} for i in ids] if page == 1 else []
            return Response(status=200, url=url, body=json.dumps(
                {"count": len(ids), "results": rows}).encode())
        deck_id = int(url.rstrip("/").rsplit("/", 1)[1])
        if deck_id == 7001:
            return Response(status=404, body=b"nope", url=url)
        if deck_id == 7002:
            return Response(status=200, body=DECK_JSON.encode(), url=url)
        return Response(status=403, body=b"throttled", url=url)


def test_harvest_error_statuses_and_consecutive_block_stop(store):
    _register_cards(store)
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, ErrFetcher(), commanders=cmdrs, brackets=(3, 2))
    assert report["totals"]["not_found"] == 1
    assert report["totals"]["available"] == 1
    assert report["totals"]["blocked"] == 10          # stops after 10 in a row
    assert report["totals"]["stopped_on_block"] is True
    row = store.conn.execute(
        "SELECT status FROM decklist_deck WHERE deck_uid='archidekt:7001'").fetchone()
    assert row["status"] == "NOT_FOUND"                # failure kept w/ provenance


class ExplodingFetcher(StubFetcher):
    def get(self, url, **kw):
        if url.rstrip("/").endswith("/9002"):
            raise RuntimeError("boom")
        return super().get(url, **kw)


def test_one_exploding_deck_never_kills_the_run(store):
    _register_cards(store)
    fetcher = ExplodingFetcher({3: [9001, 9002, 9003]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    assert report["totals"]["available"] == 2
    assert report["totals"]["partial"] == 1
    row = store.conn.execute(
        "SELECT status, detail FROM decklist_deck WHERE deck_uid='archidekt:9002'"
    ).fetchone()
    assert row["status"] == "PARTIAL" and "RuntimeError" in row["detail"]


def test_raw_save_failure_downgrades_to_partial_and_retries(store, monkeypatch):
    import deckbuild_studio.decklists as dl
    _register_cards(store)
    monkeypatch.setattr(dl, "_save_raw",
                        lambda s, raw: (_ for _ in ()).throw(
                            PermissionError("storage layer says no")))
    fetcher = StubFetcher({3: [9001]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    assert report["totals"]["available"] == 0 and report["totals"]["partial"] == 1
    row = store.conn.execute(
        "SELECT status, raw_path, mapped_cards FROM decklist_deck"
        " WHERE deck_uid='archidekt:9001'").fetchone()
    assert row["status"] == "PARTIAL" and row["raw_path"] is None
    assert row["mapped_cards"] == 5                    # cards still stored
    monkeypatch.undo()
    report2 = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    assert report2["totals"]["available"] == 1          # retried, now AVAILABLE


def test_cohort_storage_error_retries_then_succeeds(store, monkeypatch):
    import sqlite3
    import types

    import deckbuild_studio.decklists as dl
    _register_cards(store)
    monkeypatch.setattr(dl, "time", types.SimpleNamespace(sleep=lambda s: None))
    real_listing = dl._cohort_listing
    calls = {"n": 0}

    def flaky(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.OperationalError("disk I/O error")
        return real_listing(*a, **kw)

    monkeypatch.setattr(dl, "_cohort_listing", flaky)
    fetcher = StubFetcher({3: [9001]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    assert report["totals"]["available"] == 1
    assert report["totals"]["storage_errors"] == 0
    assert calls["n"] == 2                                # one retry happened


def test_cohort_persistent_storage_error_marks_cohort_and_continues(store, monkeypatch):
    import sqlite3
    import types

    import deckbuild_studio.decklists as dl
    _register_cards(store)
    monkeypatch.setattr(dl, "time", types.SimpleNamespace(sleep=lambda s: None))
    monkeypatch.setattr(dl, "_cohort_listing",
                        lambda *a, **kw: (_ for _ in ()).throw(
                            sqlite3.OperationalError("disk I/O error")))
    fetcher = StubFetcher({3: [9001], 2: [8001]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3, 2))
    assert report["totals"]["storage_errors"] == 2        # both cohorts marked
    assert [c["listing_status"] for c in report["cohorts"]] == [
        "STORAGE_ERROR", "STORAGE_ERROR"]                 # run did NOT die


def test_database_locked_propagates_to_cohort_retry(store, monkeypatch):
    import sqlite3
    import types

    import deckbuild_studio.decklists as dl
    _register_cards(store)
    monkeypatch.setattr(dl, "time", types.SimpleNamespace(sleep=lambda s: None))
    real_store = dl._store_deck
    calls = {"n": 0}

    def locked_once(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.OperationalError("database is locked")
        return real_store(*a, **kw)

    monkeypatch.setattr(dl, "_store_deck", locked_once)
    fetcher = StubFetcher({3: [9001, 9002]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    # the locked deck was retried at cohort level, not filed as PARTIAL
    assert report["totals"]["available"] == 2
    assert report["totals"]["partial"] == 0
    assert store.conn.execute(
        "SELECT COUNT(*) FROM decklist_deck WHERE status='PARTIAL'"
    ).fetchone()[0] == 0


def test_cohort_fetch_error_retries_then_succeeds(store, monkeypatch):
    import types

    import deckbuild_studio.decklists as dl
    from deckbuild_studio.httpfetch import FetchError
    _register_cards(store)
    monkeypatch.setattr(dl, "time", types.SimpleNamespace(sleep=lambda s: None))
    real_listing = dl._cohort_listing
    calls = {"n": 0}

    def flaky(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise FetchError(None, "IncompleteRead(9984 bytes read)")
        return real_listing(*a, **kw)

    monkeypatch.setattr(dl, "_cohort_listing", flaky)
    fetcher = StubFetcher({3: [9001]})
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(3,))
    assert report["totals"]["available"] == 1
    assert calls["n"] == 2


def test_fetcher_retries_incomplete_read(monkeypatch):
    import http.client
    import urllib.request

    from deckbuild_studio.httpfetch import Fetcher

    class Resp:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            raise http.client.IncompleteRead(b"part", 10)

    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return Resp()
        ok = Resp()
        ok.read = lambda: b"{}"
        return ok

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    fetcher = Fetcher(min_interval=0, sleeper=lambda s: None)
    monkeypatch.setattr(fetcher, "assert_allowed", lambda url: None)
    resp = fetcher.get("https://archidekt.com/api/decks/1/")
    assert resp.status == 200 and calls["n"] == 2


def test_resume_refetches_deck_stored_by_old_parser(harvested):
    store, fetcher, _ = harvested
    store.conn.execute("UPDATE decklist_deck SET parser_version='archidekt-deck/0.0.0'"
                       " WHERE deck_uid='archidekt:9001'")
    store.conn.commit()
    before = fetcher.detail_calls
    cmdrs = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]
    report = sync_decklists(store, fetcher, commanders=cmdrs, brackets=(2, 3))
    assert fetcher.detail_calls == before + 1          # only the stale one
    assert report["totals"]["cached"] == 4


def test_inclusion_empty_cohort_reports_insufficient(store):
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    out = compute_inclusion(store, commander_oracle_id=SAMI)
    assert out["definition"]["denominator"] == 0
    assert out["definition"]["sufficient"] is False
    assert out["results"] == []


def test_inclusion_max_age_excludes_stale_decks(harvested):
    store, _, _ = harvested
    store.conn.execute("UPDATE decklist_deck SET fetched_at='2000-01-01T00:00:00Z'"
                       " WHERE bracket_level=2")
    store.conn.commit()
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    out = compute_inclusion(store, commander_oracle_id=SAMI,
                            overrides={"inclusion.brackets": [2, 3],
                                       "inclusion.max_age_days": 30})
    # the 3 fresh bracket-3 decks share one fixture content: they count
    # as one deck (per-universe content dedupe)
    assert out["definition"]["denominator"] == 1


# ---------------------------------------------------------------- settings

def test_settings_defaults_reproduce_previous_behaviour(store):
    cfg = settings_mod.resolve(store)
    assert cfg["inclusion.source"] == "edhrec"
    assert cfg["inclusion.brackets"] == [2, 3, 4]
    assert cfg["inclusion.platforms"] == ["archidekt"]
    assert cfg["inclusion.min_decks"] == 10
    assert cfg["inclusion.max_age_days"] is None


def test_settings_roundtrip_and_validation(store):
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    assert settings_mod.get_setting(store, "inclusion.source") == "decklists"
    settings_mod.set_setting(store, "inclusion.brackets", [3, 2, 2])
    assert settings_mod.get_setting(store, "inclusion.brackets") == [2, 3]
    with pytest.raises(settings_mod.SettingError):
        settings_mod.set_setting(store, "inclusion.source", "gut feeling")
    with pytest.raises(settings_mod.SettingError):
        settings_mod.set_setting(store, "inclusion.brackets", [9])
    with pytest.raises(settings_mod.SettingError):
        settings_mod.set_setting(store, "unknown.key", 1)
    with pytest.raises(settings_mod.SettingError):
        settings_mod.set_setting(store, "inclusion.min_decks", -1)


# ---------------------------------------------------------------- inclusion

def test_inclusion_from_decklists_denominator_follows_cohort(harvested):
    store, _, _ = harvested
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    # NOTE: the stub serves the same fixture deck for every id, so all
    # harvested decks collapse to one canonical deck per universe (see
    # test_inclusion_dedupes_identical_deck_content); the cohort
    # behaviour with distinct decks is covered by
    # test_inclusion_denominator_follows_cohort_with_distinct_decks.
    only3 = compute_inclusion(store, commander_oracle_id=SAMI,
                              overrides={"inclusion.brackets": [3]})
    assert only3["definition"]["denominator"] == 1
    temple = next(r for r in only3["results"] if r["oracle_id"] == TEMPLE)
    assert temple["decks_with"] == 1 and temple["inclusion"] == 1.0
    both = compute_inclusion(store, commander_oracle_id=SAMI,
                             overrides={"inclusion.brackets": [2, 3]})
    assert both["definition"]["denominator"] == 1   # same content, one deck
    only2 = compute_inclusion(store, commander_oracle_id=SAMI,
                              overrides={"inclusion.brackets": [2]})
    assert only2["definition"]["denominator"] == 1


def test_inclusion_excludes_commander_and_flags_insufficient(harvested):
    store, _, _ = harvested
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    out = compute_inclusion(store, commander_oracle_id=SAMI)  # min_decks default 10
    assert out["definition"]["denominator"] == 1  # 5 fixture ids, one content
    assert out["definition"]["sufficient"] is False
    assert "ungenügende Daten" in out["definition"]["sufficiency_note"]
    assert all(r["oracle_id"] != SAMI for r in out["results"])  # commander excluded
    assert all(r["sufficient"] is False for r in out["results"])


def test_inclusion_dedupes_identical_deck_content(store):
    """Same list under two deck ids — incl. across brackets — counts once
    (lowest deck id wins); the denominator composition shows the split."""
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    cmd = [(SAMI, "Sami, Wildcat Captain", 1, 1)]
    temple = [(TEMPLE, "Temple of Triumph", 1, 0)]
    _store_synthetic_deck(store, "archidekt:1001", 3, cmd + temple)
    _store_synthetic_deck(store, "archidekt:1002", 2, cmd + temple)
    _store_synthetic_deck(store, "archidekt:1003", 3,
                          cmd + [(CMD_TOWER, "Command Tower", 1, 0)])
    out = compute_inclusion(store, commander_oracle_id=SAMI,
                            overrides={"inclusion.brackets": [2, 3]})
    assert out["definition"]["denominator"] == 2
    assert out["definition"]["denominator_by_platform"] == {"archidekt": 2}
    # canonical decks are 1001 and 1003, both bracket 3 — the bracket-2
    # copy adds no denominator slot
    assert out["definition"]["denominator_by_bracket"] == {"3": 2}
    temple_row = next(r for r in out["results"] if r["oracle_id"] == TEMPLE)
    assert temple_row["decks_with"] == 1 and temple_row["inclusion"] == 0.5
    assert any("inhaltsgleiche Duplikate" in n
               for n in out["definition"]["notes"])


def test_inclusion_same_main_different_commander_counts_twice(store):
    """The commander row is part of the fingerprint: same 99, different
    commander is a different deck."""
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    temple = [(TEMPLE, "Temple of Triumph", 1, 0)]
    _store_synthetic_deck(store, "archidekt:1001", 3,
                          [(SAMI, "Sami, Wildcat Captain", 1, 1)] + temple)
    _store_synthetic_deck(store, "archidekt:1002", 3,
                          [(OID["commander_a"], "Alara, Test Sovereign", 1, 1)]
                          + temple, commander=OID["commander_a"])
    out = compute_inclusion(store, overrides={"inclusion.brackets": [3]})
    assert out["definition"]["denominator"] == 2
    temple_row = next(r for r in out["results"] if r["oracle_id"] == TEMPLE)
    assert temple_row["decks_with"] == 2


def test_inclusion_denominator_follows_cohort_with_distinct_decks(store):
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    cmd = [(SAMI, "Sami, Wildcat Captain", 1, 1)]
    _store_synthetic_deck(store, "archidekt:1001", 3,
                          cmd + [(TEMPLE, "Temple of Triumph", 1, 0)])
    _store_synthetic_deck(store, "archidekt:1002", 3,
                          cmd + [(CMD_TOWER, "Command Tower", 1, 0)])
    _store_synthetic_deck(store, "archidekt:1003", 2,
                          cmd + [("8e7641e1-e814-4d5a-9cb3-71ad2f4ceee8",
                                  "Rugged Prairie", 1, 0)])
    only3 = compute_inclusion(store, commander_oracle_id=SAMI,
                              overrides={"inclusion.brackets": [3]})
    assert only3["definition"]["denominator"] == 2
    assert only3["definition"]["denominator_by_bracket"] == {"3": 2}
    both = compute_inclusion(store, commander_oracle_id=SAMI,
                             overrides={"inclusion.brackets": [2, 3]})
    assert both["definition"]["denominator"] == 3
    assert both["definition"]["denominator_by_bracket"] == {"2": 1, "3": 2}


def test_inclusion_ignores_zero_quantity_rows(store):
    """A stored card row with quantity 0 is not a card in the deck
    (the parser coerces to >= 1, so this guards the query itself)."""
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    _store_synthetic_deck(store, "archidekt:1001", 3,
                          [(SAMI, "Sami, Wildcat Captain", 1, 1),
                           (TEMPLE, "Temple of Triumph", 1, 0),
                           (CMD_TOWER, "Command Tower", 0, 0)])
    out = compute_inclusion(store, commander_oracle_id=SAMI,
                            overrides={"inclusion.brackets": [3]})
    assert out["definition"]["denominator"] == 1
    assert [r["oracle_id"] for r in out["results"]] == [TEMPLE]


def test_inclusion_excludes_decks_without_countable_card(store):
    """A deck is part of the universe only when it holds at least one
    countable card (quantity > 0, not the commander entry): a
    commander-only list, a list of zero-quantity rows only, and a deck
    without stored card rows all leave the denominator instead of
    counting as a deck that can never contribute a hit (upstream
    #1207: empty decks leave the denominator; unknown fingerprints
    stay distinct — here subsumed, because a deck without rows is
    excluded rather than collapsing onto an empty fingerprint)."""
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    cmd = [(SAMI, "Sami, Wildcat Captain", 1, 1)]
    _store_synthetic_deck(store, "archidekt:1001", 3,
                          cmd + [(TEMPLE, "Temple of Triumph", 1, 0)])
    _store_synthetic_deck(store, "archidekt:1002", 3, cmd)  # commander only
    _store_synthetic_deck(store, "archidekt:1003", 3,
                          cmd + [(TEMPLE, "Temple of Triumph", 0, 0),
                                 (CMD_TOWER, "Command Tower", 0, 0)])
    _store_synthetic_deck(store, "archidekt:1004", 3, [])  # no card rows
    out = compute_inclusion(store, commander_oracle_id=SAMI,
                            overrides={"inclusion.brackets": [3]})
    assert out["definition"]["denominator"] == 1
    assert any("3 von 4 Deck-IDs haben keine zählbare Karte" in n
               for n in out["definition"]["notes"])
    assert [r["oracle_id"] for r in out["results"]] == [TEMPLE]


def test_inclusion_large_universe_binds_no_variable_per_deck(store):
    """1100 distinct decks exceed SQLite's 999-variable cap on older
    builds: universe queries must load the ids through a TEMP table
    (one bound variable) instead of one ``?`` per deck (upstream
    #1207: large universes)."""
    settings_mod.set_setting(store, "inclusion.source", "decklists")
    settings_mod.set_setting(store, "inclusion.min_decks", 0)
    cmd = [(SAMI, "Sami, Wildcat Captain", 1, 1)]
    for i in range(1100):
        oid = f"00000000-0000-0000-0000-{i:012d}"
        _store_synthetic_deck(store, f"archidekt:{2000 + i}", 3,
                              cmd + [(oid, f"Testkarte {i}", 1, 0)])
    out = compute_inclusion(store, commander_oracle_id=SAMI,
                            overrides={"inclusion.brackets": [3]})
    assert out["definition"]["denominator"] == 1100
    assert len(out["results"]) == 1100
    assert all(r["decks_with"] == 1 for r in out["results"])


def test_inclusion_edhrec_default_matches_stored_stats(loaded_store):
    from deckbuild_studio.external import save_snapshot
    snap = save_snapshot(loaded_store, source_name="edhrec", kind="edhrec_stats",
                         url="https://edhrec.com/commanders/x/core", status="AVAILABLE",
                         commander_oracle_id=OID["commander_a"], bracket="core",
                         slug="alara-test-sovereign", sample_size=10)
    loaded_store.conn.execute(
        "INSERT INTO edhrec_card_stat(snapshot_id,category,card_slug,name,"
        "scryfall_id,inclusion,num_decks,potential_decks,synergy,lift,trend_zscore)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (snap, "artifacts", "sol-ring-test", "Sol Ring (Test)", None,
         0.7, 7, 10, None, None, None))
    loaded_store.conn.commit()
    out = compute_inclusion(loaded_store, commander_oracle_id=OID["commander_a"])
    assert out["definition"]["source"] == "edhrec"
    assert out["definition"]["denominator"] == 10
    sol = next(r for r in out["results"] if r["name"] == "Sol Ring (Test)")
    assert sol["decks_with"] == 7 and sol["inclusion"] == pytest.approx(0.7)
    assert sol["per_bracket"]["2"]["potential_decks"] == 10


def test_inclusion_own_decks_and_combined(loaded_store, tmp_path, harvested):
    rows = [("Alara, Test Sovereign", 1, "Foundation"), ("Plains", 60, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    from deckbuild_studio.decks import create_deck
    create_deck(loaded_store, FC, "Eigenes Deck", [OID["commander_a"]],
                {OID["sol_ring"]: 1, OID["plains"]: 36})
    own = compute_inclusion(loaded_store, collection_id=FC,
                            overrides={"inclusion.source": "own_decks"})
    assert own["definition"]["denominator"] == 1
    # commander context filters own decks by their commander:
    own_sami = compute_inclusion(loaded_store, collection_id=FC,
                                 commander_oracle_id=SAMI,
                                 overrides={"inclusion.source": "own_decks"})
    assert own_sami["definition"]["denominator"] == 0
    # combined without commander context pools everything in this shared
    # store: 1 harvested SAMI deck (5 fixture ids, one content) + 1 own Alara deck
    comb = compute_inclusion(loaded_store, collection_id=FC,
                             overrides={"inclusion.source": "combined"})
    assert comb["definition"]["denominator"] == 2
    assert any("EDHREC wird nicht eingemischt" in n
               for n in comb["definition"]["notes"])
    # combined in the SAMI context: 1 harvested + 0 own (Alara deck is not
    # a SAMI deck) — denominators never mix contexts silently
    comb_sami = compute_inclusion(loaded_store, collection_id=FC,
                                  commander_oracle_id=SAMI,
                                  overrides={"inclusion.source": "combined"})
    assert comb_sami["definition"]["denominator"] == 1


# ---------------------------------------------------------------- web API

@pytest.fixture()
def client(loaded_store, tmp_path, monkeypatch):
    from deckbuild_studio import web as web_mod
    rows = [("Alara, Test Sovereign", 1, "Foundation"), ("Plains", 60, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_settings_and_inclusion_endpoints(client):
    got = client.get("/api/settings").json()
    assert got["settings"]["inclusion.source"]["value"] == "edhrec"
    put = client.put("/api/settings", json={"inclusion.source": "decklists",
                                            "inclusion.min_decks": 3})
    assert put.status_code == 200
    assert put.json()["settings"]["inclusion.source"]["value"] == "decklists"
    bad = client.put("/api/settings", json={"inclusion.brackets": [7]})
    assert bad.status_code == 400
    inc = client.get("/api/inclusion",
                     params={"commander_oracle_id": OID["commander_a"]}).json()
    assert inc["definition"]["source"] == "decklists"
    assert inc["definition"]["denominator"] == 0
    assert inc["definition"]["sufficient"] is False  # 0 < 3: ungenügende Daten


def test_settings_put_is_atomic(client):
    bad = client.put("/api/settings", json={"inclusion.source": "own_decks",
                                            "inclusion.brackets": [9]})
    assert bad.status_code == 400
    got = client.get("/api/settings").json()
    # the valid key of the same request must NOT have been applied
    assert got["settings"]["inclusion.source"]["value"] == "edhrec"


# ---------------------------------------------------------------------------
# Targeted re-harvest: only cohorts below the canonical minimum are
# re-listed (empty ones included); full cohorts are not even listed.
# ---------------------------------------------------------------------------

OTHER = OID["planeswalker"]


def _seed_cohort(store, n, *, bracket, copies_of_first=0):
    """n canonically DISTINCT synthetic SAMI decks of one bracket
    (Temple quantity varies the content fingerprint), plus exact
    content copies of the first deck."""
    for i in range(n):
        _store_synthetic_deck(
            store, f"synth:{bracket}:{i}", bracket,
            [(SAMI, "Sami, Wildcat Captain", 1, 1),
             (TEMPLE, "Temple of Triumph", i + 1, 0)])
    for j in range(copies_of_first):
        _store_synthetic_deck(
            store, f"synth:{bracket}:copy{j}", bracket,
            [(SAMI, "Sami, Wildcat Captain", 1, 1),
             (TEMPLE, "Temple of Triumph", 1, 0)])


class CohortStubFetcher:
    """Archidekt stub routed by (commanderName, bracket); records
    every list call. List rows carry updatedAt, the detail payload is
    the harvested fixture deck."""

    def __init__(self, cohorts):
        self.cohorts = cohorts  # {(name, bracket): [deck ids]}
        self.list_calls = []
        self.detail_calls = 0

    def get(self, url, **kw):
        from urllib.parse import parse_qs, urlparse
        if "/api/decks/v3/" in url:
            q = parse_qs(urlparse(url).query)
            name = q["commanderName"][0]
            bracket = int(q["edhBracket"][0])
            page = int(q["page"][0])
            self.list_calls.append((name, bracket))
            ids = self.cohorts.get((name, bracket), [])
            rows = ([{"id": i, "edhBracket": bracket, "size": 100,
                      "updatedAt": "2026-11-20T10:00:00Z"} for i in ids]
                    if page == 1 else [])
            body = json.dumps({"count": len(ids), "next": None,
                               "results": rows}).encode()
            return Response(status=200, body=body, url=url)
        if "/api/decks/" in url:
            self.detail_calls += 1
            return Response(status=200, body=DECK_JSON.encode(), url=url)
        raise AssertionError(url)


SAMI_CMDR = [{"oracle_id": SAMI, "name": "Sami, Wildcat Captain"}]


def test_plan_targeted_harvest_uses_canonical_counts(store):
    from deckbuild_studio import decklists as dl
    _seed_cohort(store, 30, bracket=3, copies_of_first=5)  # canonical 30
    _seed_cohort(store, 10, bracket=2)                     # canonical 10
    assert dl.canonical_cohort_counts(store) == {
        (SAMI, 3): 30, (SAMI, 2): 10}
    plan = dl.plan_targeted_harvest(
        store, SAMI_CMDR + [{"oracle_id": OTHER, "name": "Test, X"}],
        (2, 3, 4), min_canonical=30)
    by_key = {(t["oracle_id"], t["bracket"]): t for t in plan}
    assert (SAMI, 3) not in by_key  # 30 distinct + 5 copies = canonical 30
    assert by_key[(SAMI, 2)]["canonical_before"] == 10
    assert by_key[(SAMI, 2)]["was_empty"] is False
    assert by_key[(SAMI, 4)]["canonical_before"] == 0
    assert by_key[(SAMI, 4)]["was_empty"] is True
    assert by_key[(OTHER, 2)]["canonical_before"] == 0
    assert len(plan) == 5  # SAMI B2+B4, OTHER B2+B3+B4
    # A lower threshold drops the 10-deck cohort from the plan too.
    plan10 = dl.plan_targeted_harvest(store, SAMI_CMDR, (2, 3, 4),
                                      min_canonical=10)
    assert [(t["oracle_id"], t["bracket"]) for t in plan10] == [(SAMI, 4)]


def test_targeted_harvest_fetches_only_thin_cohorts(store):
    from deckbuild_studio import decklists as dl
    _register_cards(store)
    _seed_cohort(store, 30, bracket=3)  # full cohort: never listed
    # One B2 deck already stored AVAILABLE (listed id 8001); its NULL
    # source_updated_at must survive the targeted run untouched.
    _store_synthetic_deck(
        store, "archidekt:8001", 2,
        [(SAMI, "Sami, Wildcat Captain", 1, 1),
         (TEMPLE, "Temple of Triumph", 3, 0)])
    fetcher = CohortStubFetcher({
        ("Sami, Wildcat Captain", 2): [8001, 8002, 8003],
        ("Sami, Wildcat Captain", 3): [9001],
    })
    report = dl.sync_decklists_targeted(
        store, fetcher, commanders=SAMI_CMDR, brackets=(2, 3, 4),
        min_canonical=30)
    assert report["targeted"] is True
    listed = {b for _, b in fetcher.list_calls}
    assert listed == {2, 4}          # B3 (canonical 30) never listed
    assert fetcher.detail_calls == 2  # 8002 + 8003; 8001 stayed cached
    targets = {(t["oracle_id"], t["bracket"]): t
               for t in report["targets"]}
    assert set(targets) == {(SAMI, 2), (SAMI, 4)}
    assert targets[(SAMI, 2)]["canonical_before"] == 1
    # 8002 and 8003 are the same fixture deck -> ONE canonical deck.
    assert targets[(SAMI, 2)]["canonical_after"] == 2
    assert targets[(SAMI, 4)]["canonical_before"] == 0
    assert targets[(SAMI, 4)]["canonical_after"] == 0
    assert targets[(SAMI, 4)]["was_empty"] is True
    coh4 = next(c for c in report["sync_run"]["cohorts"]
                if c["bracket"] == 4)
    assert coh4["listed_count"] == 0
    assert coh4["listing_status"] == "AVAILABLE"  # platform: 0 hits
    rows = {r[0]: r[1] for r in store.conn.execute(
        "SELECT deck_uid, source_updated_at FROM decklist_deck")}
    assert rows["archidekt:8002"] == "2026-11-20T10:00:00Z"
    assert rows["archidekt:8001"] is None  # never backfilled
    status = store.conn.execute(
        "SELECT status FROM decklist_deck WHERE deck_uid='archidekt:8002'"
    ).fetchone()[0]
    assert status == "AVAILABLE"


def test_targeted_explicit_targets_override_plan(store):
    from deckbuild_studio import decklists as dl
    _register_cards(store)
    _seed_cohort(store, 30, bracket=3)  # full — planned mode skips it
    fetcher = CohortStubFetcher({("Sami, Wildcat Captain", 3): [9100]})
    report = dl.sync_decklists_targeted(
        store, fetcher, commanders=SAMI_CMDR, brackets=(2, 3, 4),
        targets=[{"oracle_id": SAMI, "name": "Sami, Wildcat Captain",
                  "bracket": 3}])
    assert {b for _, b in fetcher.list_calls} == {3}
    t = report["targets"][0]
    assert t["canonical_before"] == 30 and t["canonical_after"] == 31
    # An explicit empty list is an honest no-op (no fetch at all).
    fetcher2 = CohortStubFetcher({})
    report2 = dl.sync_decklists_targeted(
        store, fetcher2, commanders=SAMI_CMDR, targets=[])
    assert report2["sync_run"] is None and fetcher2.list_calls == []
