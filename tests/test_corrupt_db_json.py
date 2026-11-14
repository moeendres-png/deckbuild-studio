"""Issue #33 regression (FIX-5): corrupt JSON columns in stored
``reference_role_profile`` rows must degrade to the field's empty
structure, never an unhandled 500 on the read paths (/api/cards).

Rows are seeded through the app's own write path
(``import_role_profiles`` — it always writes valid JSON) and then
corrupted in place; that is the only way a corrupt payload can exist
in the store. Same seed pattern as test_corrupt_payload.py (#21).

(The tier_assignment half of the original regression suite was
removed with the tier list itself, issue #59, 2026-11-14.)
"""
import json

import pytest
from fastapi.testclient import TestClient

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import web as web_mod
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.reference import (card_reference,
                                        import_role_profiles, reference_map)

CORRUPT = "{not valid json"
FC = "foundation-schwarze-box"
RING = OID["sol_ring"]


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


@pytest.fixture()
def client(coll, monkeypatch):
    monkeypatch.setattr(web_mod, "database_path", lambda: coll.path)
    return TestClient(web_mod.create_app())


def _roles_file(tmp_path):
    data = {
        "schema_version": "0.4.0",
        "estimate_type": "structural_model_estimates",
        "data_as_of": "2026-08-09",
        "source_hash": "cafe1234",
        "profile_count": 1,
        "profiles": [
            {"oracle_name": "Sol Ring (Test)", "mana_value": 1.0,
             "roles": ["ramp", "engine"],
             "role_strengths": {"ramp": 1.0, "engine": 0.5},
             "mechanic_tags": ["mana_rock"], "color_requirements": {},
             "color_identity": [], "is_land": False},
        ],
    }
    path = tmp_path / "structural_role_profiles.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _corrupt_role(store, *columns, oid=RING):
    sets = ", ".join(f"{c}=?" for c in columns)
    store.conn.execute(
        f"UPDATE reference_role_profile SET {sets} WHERE oracle_id=?",
        (*[CORRUPT] * len(columns), oid))
    store.conn.commit()


# ---------------------------------------------------------------------------
# reference_role_profile: card_reference / reference_map
# ---------------------------------------------------------------------------

def test_card_reference_corrupt_role_fields_degrade(loaded_store, tmp_path):
    import_role_profiles(loaded_store, _roles_file(tmp_path))
    _corrupt_role(loaded_store, "roles_json", "role_strengths_json",
                  "mechanic_tags_json")
    ref = card_reference(loaded_store, RING)
    role = ref["role_profile"]
    assert role["roles"] == []
    assert role["role_strengths"] == {}
    assert role["mechanic_tags"] == []
    # Provenance/label fields of the row are delivered unchanged.
    assert role["data_kind"] == "structural_model_estimate"
    assert role["estimate_type"] == "structural_model_estimates"
    assert role["data_as_of"] == "2026-08-09"


def test_card_reference_single_corrupt_field_degrades_only_it(
        loaded_store, tmp_path):
    import_role_profiles(loaded_store, _roles_file(tmp_path))
    _corrupt_role(loaded_store, "role_strengths_json")
    role = card_reference(loaded_store, RING)["role_profile"]
    assert role["role_strengths"] == {}
    # Valid sibling fields pass through with their real values.
    assert role["roles"] == ["ramp", "engine"]
    assert role["mechanic_tags"] == ["mana_rock"]


def test_reference_map_and_cards_api_survive_corrupt_row(
        client, coll, tmp_path):
    import_role_profiles(coll, _roles_file(tmp_path))
    _corrupt_role(coll, "roles_json")
    refs = reference_map(coll, [RING])
    assert refs[RING]["role_profile"]["roles"] == []
    assert refs[RING]["role_profile"]["role_strengths"] == {
        "ramp": 1.0, "engine": 0.5}
    resp = client.get("/api/cards", params={"collection_id": FC})
    assert resp.status_code == 200
    ring = next(c for c in resp.json() if c["oracle_id"] == RING)
    assert ring["reference"]["role_profile"]["roles"] == []
