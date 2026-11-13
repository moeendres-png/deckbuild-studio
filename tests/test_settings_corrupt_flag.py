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

KEY = "tierlist.model_version"


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
    settings_mod.set_setting(store, KEY, "tierlist/1.2.0")
    entry = settings_mod.all_settings(store)["settings"][KEY]
    assert entry["corrupt"] is False
    assert entry["overridden"] is True
    assert entry["value"] == "tierlist/1.2.0"


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
    assert payload["settings"][KEY]["value"] == "tierlist/1.1.0"
    others = [e for k, e in payload["settings"].items() if k != KEY]
    assert all(e["corrupt"] is False for e in others)


def test_unknown_and_scalar_rows_match_base_semantics(store):
    # A stored row for a key outside the catalogue never surfaces and
    # never crashes; a parseable scalar is a valid stored value (the
    # shared _parse_stored definition of "corrupt" is: not parseable).
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
