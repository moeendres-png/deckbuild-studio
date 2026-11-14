"""FIX-2 (issue #27): a corrupt ``app_setting`` row must be VISIBLE.

Since PR #25 the read paths fall back to the catalogue default when a
stored ``value_json`` does not parse — correct for robustness, but the
fallback was invisible: in ``all_settings`` a corrupt key looked exactly
like a never-set key. ``all_settings`` now flags the entry with
``"corrupt": True`` (the value/overridden semantics are unchanged), and
``SETTINGS_VERSION`` is bumped for the payload extension.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from deckbuild_studio import settings as settings_mod
from deckbuild_studio import web as web_mod

KEY = "inclusion.source"


def _insert_corrupt(store, key: str = KEY) -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO app_setting(key, value_json, updated_at) "
        "VALUES(?, '{not valid json', '2026-11-13T00:00:00+00:00')", (key,))
    store.conn.commit()


def test_all_settings_flags_corrupt_row(store):
    _insert_corrupt(store)
    entry = settings_mod.all_settings(store)["settings"][KEY]
    assert entry["corrupt"] is True
    # fallback semantics of #25 unchanged: default value, not overridden
    assert entry["value"] == settings_mod.CATALOG[KEY]["default"]
    assert entry["overridden"] is False


def test_all_settings_valid_override_is_not_corrupt(store):
    settings_mod.set_setting(store, KEY, "decklists")
    entry = settings_mod.all_settings(store)["settings"][KEY]
    assert entry["corrupt"] is False
    assert entry["overridden"] is True
    assert entry["value"] == "decklists"


def test_all_settings_unset_keys_are_not_corrupt(store):
    payload = settings_mod.all_settings(store)
    assert payload["settings_version"] == 2
    assert all(entry["corrupt"] is False
               for entry in payload["settings"].values())


def test_all_settings_only_the_corrupt_key_is_flagged(store):
    _insert_corrupt(store)
    settings_mod.set_setting(store, "inclusion.min_decks", 5)
    settings = settings_mod.all_settings(store)["settings"]
    flagged = [k for k, e in settings.items() if e["corrupt"]]
    assert flagged == [KEY]


def test_get_setting_still_falls_back_without_crashing(store):
    _insert_corrupt(store)
    assert settings_mod.get_setting(store, KEY) == \
        settings_mod.CATALOG[KEY]["default"]


@pytest.fixture()
def client(loaded_store, monkeypatch):
    _insert_corrupt(loaded_store)
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_api_settings_shows_corrupt_flag(client):
    payload = client.get("/api/settings").json()
    assert payload["settings_version"] == 2
    assert payload["settings"][KEY]["corrupt"] is True
    assert payload["settings"][KEY]["value"] == "edhrec"
    others = [e for k, e in payload["settings"].items() if k != KEY]
    assert all(e["corrupt"] is False for e in others)


def test_unknown_and_scalar_rows_match_base_semantics(store):
    # A stored row for a key outside the catalogue never surfaces and
    # never crashes; a parseable scalar of the catalogue type is a
    # valid stored value.
    store.conn.execute(
        "INSERT INTO app_setting(key, value_json, updated_at) "
        "VALUES('unknown.key', '{broken', '2026-11-13T00:00:00+00:00')")
    store.conn.execute(
        "INSERT INTO app_setting(key, value_json, updated_at) "
        "VALUES('inclusion.min_decks', '5', '2026-11-13T00:00:00+00:00')")
    store.conn.commit()
    payload = settings_mod.all_settings(store)
    assert "unknown.key" not in payload["settings"]
    entry = payload["settings"]["inclusion.min_decks"]
    assert entry["corrupt"] is False and entry["overridden"] is True
    assert entry["value"] == 5


# --- FIX-4 (issue #32): parseable but wrong-typed values are corrupt ---
#
# The expected type is the type of the catalogue default. A wrong-typed
# row gets exactly the corrupt treatment of FIX-2 (default value, not
# overridden, "corrupt": True, get_setting falls back) — no second
# semantics. Exception pinned by the number-family rule: an int stored
# for a float default is a valid override.


def _insert_raw(store, key: str, raw_json: str) -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO app_setting(key, value_json, updated_at) "
        "VALUES(?, ?, '2026-11-13T00:00:00+00:00')", (key, raw_json))
    store.conn.commit()


def _entry(store, key: str) -> dict:
    return settings_mod.all_settings(store)["settings"][key]


def _assert_corrupt_treatment(store, key: str) -> None:
    entry = _entry(store, key)
    assert entry["corrupt"] is True
    assert entry["overridden"] is False
    assert entry["value"] == settings_mod.CATALOG[key]["default"]
    assert settings_mod.get_setting(store, key) == \
        settings_mod.CATALOG[key]["default"]


def test_str_for_int_default_is_corrupt(store):
    _insert_raw(store, "inclusion.min_decks", '"5"')
    _assert_corrupt_treatment(store, "inclusion.min_decks")


def test_int_for_bool_default_is_corrupt(store, monkeypatch):
    # isinstance(True, int) is True in Python — the reverse direction
    # must not slip through either: an int is not a bool setting value.
    # The shipped catalogue has no bool default anymore (the tierlist
    # signal switches left with the tier list, issue #59); pin the rule
    # against a catalogue entry of that shape, like the float tests.
    monkeypatch.setitem(settings_mod.CATALOG, "test.bool", {
        "kind": "min_decks", "default": True, "description": "test-only"})
    _insert_raw(store, "test.bool", "1")
    _assert_corrupt_treatment(store, "test.bool")


def test_bool_for_int_default_is_corrupt(store):
    _insert_raw(store, "inclusion.min_decks", "true")
    _assert_corrupt_treatment(store, "inclusion.min_decks")


def test_str_for_float_default_is_corrupt(store, monkeypatch):
    # the shipped catalogue has no float default; pin the rule against
    # a catalogue entry of that shape (int for float stays valid, a
    # string does not)
    monkeypatch.setitem(settings_mod.CATALOG, "test.float", {
        "kind": "min_decks", "default": 1.5, "description": "test-only"})
    _insert_raw(store, "test.float", '"1.5"')
    _assert_corrupt_treatment(store, "test.float")


def test_int_for_float_default_stays_valid(store, monkeypatch):
    monkeypatch.setitem(settings_mod.CATALOG, "test.float", {
        "kind": "min_decks", "default": 1.5, "description": "test-only"})
    _insert_raw(store, "test.float", "2")
    entry = _entry(store, "test.float")
    assert entry["corrupt"] is False and entry["overridden"] is True
    assert entry["value"] == 2
    assert settings_mod.get_setting(store, "test.float") == 2
    # ... while a bool is not part of the number family either
    _insert_raw(store, "test.float", "true")
    _assert_corrupt_treatment(store, "test.float")


def test_float_for_int_default_is_corrupt(store):
    _insert_raw(store, "inclusion.min_decks", "5.5")
    _assert_corrupt_treatment(store, "inclusion.min_decks")


def test_wrong_container_and_scalar_types_are_corrupt(store):
    cases = [
        ("inclusion.source", "5"),     # int for str (enum) default
        ("inclusion.brackets", '{"2": true}'),  # dict for list default
        ("inclusion.platforms", '"archidekt"'),  # str for list default
        ("inclusion.max_age_days", '"30"'),  # str for the None-default int
        ("inclusion.date_from", "20260101"),  # int for the None-default date
    ]
    for key, raw in cases:
        _insert_raw(store, key, raw)
    for key, _raw in cases:
        _assert_corrupt_treatment(store, key)


def test_correct_types_are_unchanged(store):
    cases = [
        ("inclusion.source", '"decklists"', "decklists"),
        ("inclusion.brackets", "[2, 3, 4]", [2, 3, 4]),
        ("inclusion.platforms", '["archidekt"]', ["archidekt"]),
        ("inclusion.min_decks", "5", 5),
        ("inclusion.max_age_days", "30", 30),
        ("inclusion.max_age_days", "null", None),
        ("inclusion.date_from", '"2026-01-01"', "2026-01-01"),
        ("inclusion.date_to", "null", None),
    ]
    for key, raw, expected in cases:
        # insert + assert per case: two cases share a key (max_age_days
        # as int and as null), INSERT OR REPLACE would hide the first
        _insert_raw(store, key, raw)
        entry = _entry(store, key)
        assert entry["corrupt"] is False, key
        assert entry["overridden"] is True, key
        assert entry["value"] == expected, key
        assert settings_mod.get_setting(store, key) == expected, key


@pytest.fixture()
def client_wrong_type(loaded_store, monkeypatch):
    _insert_raw(loaded_store, "inclusion.min_decks", '"5"')
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_api_settings_shows_wrong_type_as_corrupt(client_wrong_type):
    entry = client_wrong_type.get("/api/settings").json()["settings"][
        "inclusion.min_decks"]
    assert entry["corrupt"] is True
    assert entry["overridden"] is False
    assert entry["value"] == 10


def test_catalog_shape_every_default_passes_the_type_check(tmp_path):
    # Guard for the FIX-4 trap (review P3-1): a future catalogue entry
    # whose default _type_matches cannot classify would flag EVERY
    # stored value corrupt. Every default must accept itself, and any
    # None default must use a kind the checker knows.
    import json as _json

    from deckbuild_studio.settings import CATALOG, _stored_usable, \
        _type_matches
    for key, spec in CATALOG.items():
        default = spec["default"]
        assert _type_matches(key, default), key
        if default is None:
            assert spec["kind"] in ("max_age_days", "date"), key
        ok, value = _stored_usable(key, _json.dumps(default))
        assert ok and value == default, key
