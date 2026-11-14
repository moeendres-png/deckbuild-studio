"""Browser-harvest JSONL import (browserimport.py): provenance,
cohort honesty (bracket-less decks never enter a bracket cohort),
content dedupe against the Archidekt stock, honest partial data.

Fixture: tests/fixtures/browser_decklists.jsonl — 8 lines:
an EDHREC record (commander section + a sideboard entry), a
Moxfield partner record, a PARTIAL record, a malformed line, a
BLOCKED record, a record with an unresolvable card name, a record
content-identical to a pre-stored Archidekt deck, and a record
content-identical to the first record of the same file.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import OID
from deckbuild_studio import settings as settings_mod
from deckbuild_studio.browserimport import (
    BrowserImportError, aggregate_entries, import_browser_decklists,
    normalize_fetched_at, platform_deck_id, platform_for)
from deckbuild_studio.inclusion import compute_inclusion, cooccurrence

FIXTURE = Path(__file__).parent / "fixtures" / "browser_decklists.jsonl"

SAMI = "c4175a34-70bb-47e5-8406-efdc4d2cd079"          # Sami, Wildcat Captain
TEMPLE = "6f0d94d9-64bb-4175-83bc-301e8f79f54f"        # Temple of Triumph
CMD_TOWER = "0895c9b7-ae7d-4bb3-af17-3b75deb50a25"     # Command Tower
RUGGED = "8e7641e1-e814-4d5a-9cb3-71ad2f4ceee8"         # Rugged Prairie
CITADEL = "8dc067bf-f78f-4ac4-b6e7-b305c42cf0bc"       # Darksteel Citadel


def _register_cards(store):
    for oid, name in [(SAMI, "Sami, Wildcat Captain"),
                      (TEMPLE, "Temple of Triumph"),
                      (CMD_TOWER, "Command Tower"),
                      (RUGGED, "Rugged Prairie"),
                      (CITADEL, "Darksteel Citadel"),
                      (OID["partner_a"], "Partner Alpha"),
                      (OID["partner_b"], "Partner Beta")]:
        store.conn.execute(
            "INSERT OR REPLACE INTO scryfall_card(oracle_id,name,"
            "color_identity) VALUES(?,?,?)", (oid, name, ""))
    store.conn.commit()


def _store_archidekt_deck(store):
    """One pre-existing Archidekt deck (bracket 3) whose content the
    fixture's dup789 browser record repeats card for card."""
    uid = "archidekt:555001"
    rows = [(SAMI, "Sami, Wildcat Captain", 1, 1),
            (TEMPLE, "Temple of Triumph", 1, 0),
            (CMD_TOWER, "Command Tower", 1, 0)]
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,"
        "source_url,status,parser_version,sha256,raw_path,fetched_at,"
        "deck_size,card_entries,mapped_cards,unmapped_cards,"
        "unmapped_names_json,detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,"
        "?,?,?,?,?,?)",
        (uid, "archidekt", "555001", SAMI, "Sami, Wildcat Captain", 3,
         "archidekt_edhBracket", "https://archidekt.com/decks/555001",
         "AVAILABLE", "archidekt-deck/1.0.0", None, None,
         "2026-11-12T00:00:00+00:00", 3, 3, 3, 0, "[]", ""))
    for oid, name, qty, is_cmd in rows:
        store.conn.execute(
            "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,"
            "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)",
            (uid, oid, oid, name, qty, is_cmd))
    store.conn.commit()


@pytest.fixture()
def imported(store):
    _register_cards(store)
    _store_archidekt_deck(store)
    report = import_browser_decklists(store, FIXTURE)
    return store, report


def _deck(store, uid):
    return store.conn.execute(
        "SELECT * FROM decklist_deck WHERE deck_uid=?", (uid,)).fetchone()


# ---------------------------------------------------------------- helpers

def test_platform_and_id_helpers():
    assert platform_for("edhrec") == "browser:edhrec"
    assert platform_for("Moxfield") == "browser:moxfield"
    assert platform_for("") == "browser:generic"
    assert platform_deck_id("https://edhrec.com/deckpreview/abc123") == "abc123"
    assert platform_deck_id(
        "https://www.moxfield.com/decks/xyzpdq-personal") == "xyzpdq-personal"
    assert platform_deck_id("https://archidekt.com/decks/12345/x") == "12345"
    # no recognisable id segment -> stable hash fallback
    assert len(platform_deck_id("https://example.com/a.b/c.html")) == 24


def test_fetched_at_normalization():
    assert normalize_fetched_at("2026-11-12T13:45:00Z") == \
        "2026-11-12T13:45:00+00:00"
    assert normalize_fetched_at("2026-11-12T13:45:00+00:00") == \
        "2026-11-12T13:45:00+00:00"
    assert normalize_fetched_at("garbage") is None
    assert normalize_fetched_at(None) is None


def test_aggregate_entries_sections_and_quantities():
    entries, excluded = aggregate_entries({"cards": [
        {"name": "A", "quantity": 1, "section": "Commander"},
        {"name": "B", "quantity": 1, "section": "Lands"},
        {"name": "B", "quantity": 2, "section": "Lands"},
        {"name": "C", "quantity": 1, "section": "commanders"},
        {"name": "D", "quantity": 1, "section": "Maybeboard"},
        {"name": "E", "quantity": 0, "section": ""},
    ]})
    by_name = {e["name"]: e for e in entries}
    assert by_name["A"]["is_commander"] == 1
    assert by_name["C"]["is_commander"] == 1
    assert by_name["B"]["quantity"] == 3
    assert by_name["E"]["quantity"] == 1  # invalid quantity -> 1
    assert "D" not in by_name and excluded == 1


# ---------------------------------------------------------------- report

def test_import_report_counts(imported):
    _, report = imported
    assert report["records_total"] == 8
    assert report["malformed_lines"] == 1
    assert report["malformed_line_numbers"] == [4]
    assert report["records_by_status"] == {
        "AVAILABLE": 5, "BLOCKED": 1, "PARTIAL": 1}
    assert report["imported"] == 5
    assert report["imported_partial"] == 0
    assert report["replaced_existing"] == 0
    assert report["decks_by_platform"] == {
        "browser:edhrec": 4, "browser:moxfield": 1}
    assert report["entries_mapped"] == 17
    assert report["entries_unmapped"] == 1
    assert report["unmapped_names"] == ["Totally Fake Card 123"]
    assert report["decks_with_commander_id"] == 4
    assert report["decks_without_commander_id"] == 1
    assert report["sideboard_entries_excluded"] == 1
    assert report["duplicates_of_existing"] == 1
    assert report["duplicates_within_file"] == 1
    assert {d["deck_uid"] for d in report["duplicate_examples"]} == {
        "browser:edhrec:dup789", "browser:edhrec:abc124"}
    assert report["source_id"].startswith("browser-decklists:")


def test_non_available_records_are_never_filed(imported):
    store, _ = imported
    assert _deck(store, "browser:edhrec:partial99") is None
    assert _deck(store, "browser:moxfield:blocked77") is None
    total = store.conn.execute(
        "SELECT COUNT(*) FROM decklist_deck").fetchone()[0]
    assert total == 6  # 5 browser decks + the pre-stored Archidekt deck


# ---------------------------------------------------------------- rows

def test_imported_deck_rows_carry_full_provenance(imported):
    store, _ = imported
    row = _deck(store, "browser:edhrec:abc123")
    assert row["platform"] == "browser:edhrec"
    assert row["platform_deck_id"] == "abc123"
    assert row["bracket_level"] is None      # no bracket — none invented
    assert row["bracket_source"] is None
    assert row["commander_oracle_id"] == SAMI
    assert row["commander_name"] == "Sami, Wildcat Captain"
    assert row["status"] == "AVAILABLE"
    assert row["parser_version"] == "browser-harvest/1.0.0"
    assert row["fetched_at"] == "2026-11-12T13:45:00+00:00"
    assert row["source_updated_at"] is None  # never fabricated
    assert row["deck_size"] == 5            # 1 + 1 + 1 + 2 (sideboard out)
    assert row["card_entries"] == 4
    assert row["mapped_cards"] == 4 and row["unmapped_cards"] == 0
    assert row["sha256"] and len(row["sha256"]) == 64
    assert row["raw_path"] and Path(row["raw_path"]).is_file()
    assert "browser-edhrec" in row["raw_path"]
    assert "sideboard" in row["detail"]
    cards = {r["card_name"]: r for r in store.conn.execute(
        "SELECT * FROM decklist_card WHERE deck_uid=?",
        ("browser:edhrec:abc123",))}
    assert cards["Sami, Wildcat Captain"]["is_commander"] == 1
    assert cards["Rugged Prairie"]["quantity"] == 2
    assert "Darksteel Citadel" not in cards


def test_partner_deck_keeps_both_names_and_no_single_id(imported):
    store, _ = imported
    row = _deck(store, "browser:moxfield:xyzpdq-personal")
    assert row["commander_name"] == "Partner Alpha + Partner Beta"
    assert row["commander_oracle_id"] is None
    assert "partner" in row["detail"]


def test_unresolvable_name_is_counted_and_named(imported):
    store, _ = imported
    row = _deck(store, "browser:edhrec:def456")
    assert row["mapped_cards"] == 2 and row["unmapped_cards"] == 1
    assert json.loads(row["unmapped_names_json"]) == ["Totally Fake Card 123"]
    fake = store.conn.execute(
        "SELECT * FROM decklist_card WHERE deck_uid=? AND oracle_id IS NULL",
        ("browser:edhrec:def456",)).fetchone()
    assert fake["entry_key"] == "name:Totally Fake Card 123"


def test_source_registered_with_provenance(imported):
    store, report = imported
    row = store.conn.execute(
        "SELECT * FROM source WHERE source_id=?",
        (report["source_id"],)).fetchone()
    assert row is not None
    assert row["parser_version"] == "browser-import/1.0.0"
    assert row["data_status"] == "AVAILABLE"
    assert row["sha256"] == report["file_sha256"]


# ---------------------------------------------------------------- cohorts

def test_browser_platforms_are_valid_settings(store):
    stored = settings_mod.set_setting(
        store, "inclusion.platforms", ["browser:edhrec", "archidekt"])
    assert stored == ["browser:edhrec", "archidekt"]
    assert "browser:moxfield" in settings_mod.KNOWN_PLATFORMS
    with pytest.raises(settings_mod.SettingError):
        settings_mod.set_setting(store, "inclusion.platforms", ["nope"])


def test_default_universe_is_unchanged_by_the_import(imported):
    """Regression: with the default platform selection (archidekt
    only), the denominator and bracket composition are exactly what
    they were before the browser decks existed."""
    store, _ = imported
    out = compute_inclusion(store, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["archidekt"]})
    definition = out["definition"]
    assert definition["denominator"] == 1
    assert definition["denominator_by_platform"] == {"archidekt": 1}
    assert definition["denominator_by_bracket"] == {"3": 1}


def test_browser_decks_form_a_bracketless_cohort(imported):
    store, _ = imported
    out = compute_inclusion(store, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["archidekt", "browser:edhrec"]})
    definition = out["definition"]
    # canonical contents: the Archidekt deck (its browser twin dedupes
    # onto it), browser deck abc123 (abc124 dedupes onto it), def456
    assert definition["denominator"] == 3
    assert definition["denominator_by_platform"] == {
        "archidekt": 1, "browser:edhrec": 2}
    # browser decks appear ONLY under the explicit "none" key — the
    # bracket cohorts keep exactly their bracketed decks
    assert definition["denominator_by_bracket"] == {"3": 1, "none": 2}

    out = compute_inclusion(store, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["browser:edhrec"]})
    definition = out["definition"]
    assert definition["denominator"] == 3
    assert definition["denominator_by_bracket"] == {"none": 3}


def test_bracket_filter_never_admits_browser_decks(imported):
    """Even the widest bracket selection [1..5] cannot pull a
    bracket-less deck into a bracket cohort: with platform archidekt
    the browser decks stay out entirely, whatever the brackets."""
    store, _ = imported
    out = compute_inclusion(store, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["archidekt"],
        "inclusion.brackets": [1, 2, 3, 4, 5]})
    assert out["definition"]["denominator"] == 1
    assert out["definition"]["denominator_by_bracket"] == {"3": 1}


def test_commander_scope_and_cooccurrence_on_browser_decks(imported):
    store, _ = imported
    out = compute_inclusion(store, commander_oracle_id=SAMI, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["browser:edhrec"]})
    assert out["definition"]["denominator"] == 3  # abc123, def456, dup789
    co = cooccurrence(store, TEMPLE, overrides={
        "inclusion.platforms": ["browser:edhrec"]})
    assert co["definition"]["denominator"] == 3
    assert co["decks_with_card"] == 3
    partners = {p["oracle_id"]: p for p in co["partners"]}
    assert partners[CMD_TOWER]["decks_together"] == 2


def test_decklist_selection_sees_browser_decks_only_via_platform(imported):
    from deckbuild_studio.decklists import _load_decklist_selection
    store, _ = imported
    cfg = settings_mod.resolve(store, {
        "inclusion.platforms": ["browser:edhrec"]})
    decks, excluded = _load_decklist_selection(store, cfg)
    assert excluded == 0
    assert {d["uid"] for d in decks} == {
        "browser:edhrec:abc123", "browser:edhrec:abc124",
        "browser:edhrec:def456", "browser:edhrec:dup789"}
    assert all(d["bracket_level"] is None for d in decks)
    cfg = settings_mod.resolve(store, {"inclusion.platforms": ["archidekt"]})
    decks, _ = _load_decklist_selection(store, cfg)
    assert {d["uid"] for d in decks} == {"archidekt:555001"}


# ---------------------------------------------------------------- errors

def test_missing_file_raises(store):
    with pytest.raises(BrowserImportError):
        import_browser_decklists(store, "/nonexistent/decklists_browser.jsonl")


def test_reimport_replaces_in_place(imported):
    store, _ = imported
    before = store.conn.execute(
        "SELECT COUNT(*) FROM decklist_deck").fetchone()[0]
    report = import_browser_decklists(store, FIXTURE)
    after = store.conn.execute(
        "SELECT COUNT(*) FROM decklist_deck").fetchone()[0]
    assert before == after == 6
    assert report["imported"] == 5
    assert report["replaced_existing"] == 5


def test_raw_save_failure_downgrades_to_partial(store, tmp_path, monkeypatch):
    import deckbuild_studio.browserimport as bi
    _register_cards(store)
    line = {"source": "edhrec",
            "source_url": "https://edhrec.com/deckpreview/rawfail1",
            "fetched_at_utc": "2026-11-12T14:00:00Z",
            "parser_version": "browser-harvest/1.0.0", "deck_name": "X",
            "cards": [{"name": "Sami, Wildcat Captain", "quantity": 1,
                       "section": "Commander"},
                      {"name": "Temple of Triumph", "quantity": 1,
                       "section": "Lands"}],
            "status": "AVAILABLE", "note": ""}
    path = tmp_path / "one.jsonl"
    path.write_text(json.dumps(line) + "\n", encoding="utf-8")

    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(bi, "_save_raw", boom)
    report = import_browser_decklists(store, path)
    assert report["imported"] == 0 and report["imported_partial"] == 1
    row = _deck(store, "browser:edhrec:rawfail1")
    assert row["status"] == "PARTIAL"
    assert "raw save failed" in row["detail"]
    # a PARTIAL deck joins no universe, not even its own platform's
    out = compute_inclusion(store, overrides={
        "inclusion.source": "decklists",
        "inclusion.platforms": ["browser:edhrec"]})
    assert out["definition"]["denominator"] == 0
