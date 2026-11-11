"""Reference-data layer (commander-playtest-lab reuse) — synthetic mini
fixtures in the real file formats. Semantics under test:
  * Game Changer = label only, never a legality change.
  * Banned reference vs. Scryfall legality: discrepancies are reported,
    legality in the Scryfall store is never overwritten.
  * Role profiles are model estimates and are labelled as such.
"""
from __future__ import annotations

import json

from conftest import OID, write_foundation_xlsx

from deckbuild_studio.importers import detect_and_import
from deckbuild_studio.reference import (card_reference, import_commander_flags,
                                        import_role_profiles, reference_summary)

UNKNOWN_OID = "ffffffff-ffff-4fff-8fff-ffffffffffff"


def _flags_file(tmp_path):
    data = {
        "schema": "commander-card-flags-1.0.0",
        "scope": "Label only: Game Changers + Commander banned (test fixture).",
        "source": {"kind": "scryfall_oracle_cards_bulk",
                   "bulk_file": "oracle-cards-test.jsonl.gz",
                   "bulk_sha256": "deadbeef",
                   "data_as_of": "2026-10-31T09:01:54Z",
                   "card_count": 3, "commander_legality_counts": {"banned": 1}},
        "game_changers": [
            {"name": "Sol Ring (Test)", "oracle_id": OID["sol_ring"]},
            {"name": "Ghost Card", "oracle_id": UNKNOWN_OID},
        ],
        "commander_banned": [
            {"name": "Banned Legend", "oracle_id": OID["banned"]},
            {"name": "Alara, Test Sovereign", "oracle_id": OID["commander_a"]},
            {"name": "Ghost Banned", "oracle_id": UNKNOWN_OID},
        ],
    }
    path = tmp_path / "commander_flags.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _roles_file(tmp_path):
    data = {
        "schema_version": "0.4.0",
        "estimate_type": "structural_model_estimates",
        "data_as_of": "2026-08-09",
        "source_hash": "cafe1234",
        "profile_count": 2,
        "profiles": [
            {"oracle_name": "Sol Ring (Test)", "mana_value": 1.0,
             "roles": ["ramp", "engine"],
             "role_strengths": {"ramp": 1.0, "engine": 0.5},
             "mechanic_tags": ["mana_rock"], "color_requirements": {},
             "color_identity": [], "is_land": False},
            {"oracle_name": "Nonexistent Card XYZ", "mana_value": 2.0,
             "roles": ["payoff"], "role_strengths": {"payoff": 0.7},
             "mechanic_tags": [], "color_requirements": {},
             "color_identity": [], "is_land": False},
        ],
    }
    path = tmp_path / "structural_role_profiles.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _with_collection(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", [
        ("Sol Ring (Test)", 1, "Foundation"),
        ("Alara, Test Sovereign", 1, "Foundation"),
    ])
    detect_and_import(loaded_store, path)
    return loaded_store


def test_flags_import_counts_and_discrepancies(loaded_store, tmp_path):
    report = import_commander_flags(loaded_store, _flags_file(tmp_path))
    assert report["game_changers_imported"] == 2
    assert report["commander_banned_imported"] == 3
    assert report["not_in_scryfall_store"] == {
        "game_changers": 1, "commander_banned": 1}
    disc = report["discrepancies"]
    # Alara is 'legal' in Scryfall but on the reference banned list.
    assert disc["reference_banned_but_scryfall_not_banned"] == 1
    assert disc["reference_banned_not_in_scryfall_store"] == 1
    # Scryfall's own banned card (Banned Legend) IS in the reference.
    assert disc["scryfall_banned_not_in_reference"] == 0


def test_flags_never_change_scryfall_legality(loaded_store, tmp_path):
    import_commander_flags(loaded_store, _flags_file(tmp_path))
    # Reference says banned; Scryfall still says legal — no silent overwrite.
    assert loaded_store.scryfall(OID["commander_a"])["commander_legality"] == "legal"
    ref = card_reference(loaded_store, OID["commander_a"])
    assert [f["flag"] for f in ref["flags"]] == ["commander_banned_reference"]
    gc = card_reference(loaded_store, OID["sol_ring"])
    assert [f["flag"] for f in gc["flags"]] == ["game_changer"]
    assert "keine Legalitätsaussage" in gc["flags"][0]["label"]


def test_roles_import_resolution_and_estimate_label(loaded_store, tmp_path):
    report = import_role_profiles(loaded_store, _roles_file(tmp_path))
    assert report["profiles_imported"] == 2
    assert report["resolved"] == 1
    assert report["unresolved"] == 1  # Nonexistent Card XYZ — counted, not invented
    assert report["estimate_type"] == "structural_model_estimates"
    ref = card_reference(loaded_store, OID["sol_ring"])
    role = ref["role_profile"]
    assert role["roles"] == ["ramp", "engine"]
    assert role["data_kind"] == "structural_model_estimate"
    assert role["data_as_of"] == "2026-08-09"
    assert "Schätzung" in role["display_label"]
    assert "keine Beobachtungsdaten" in role["display_label"]


def test_collection_overlap(loaded_store, tmp_path):
    store = _with_collection(loaded_store, tmp_path)
    frep = import_commander_flags(store, _flags_file(tmp_path))
    rrep = import_role_profiles(store, _roles_file(tmp_path))
    cid = "foundation-schwarze-box"
    assert frep["overlap_by_collection"][cid]["game_changers_in_collection"] == 1
    assert frep["overlap_by_collection"][cid]["banned_reference_in_collection"] == 1
    assert rrep["overlap_by_collection"][cid] == 1


def test_import_is_idempotent(loaded_store, tmp_path):
    import_commander_flags(loaded_store, _flags_file(tmp_path))
    import_role_profiles(loaded_store, _roles_file(tmp_path))
    first = reference_summary(loaded_store)
    import_commander_flags(loaded_store, _flags_file(tmp_path))
    import_role_profiles(loaded_store, _roles_file(tmp_path))
    second = reference_summary(loaded_store)
    strip = lambda d: {k: v for k, v in d.items() if k != "imports"}  # noqa: E731
    assert strip(first) == strip(second)
    assert first["commander_flags"]["game_changers"] == 2
    assert first["role_profiles"]["profiles"] == 2
    # provenance of both imports is recorded
    kinds = {i["source_kind"] for i in first["imports"]}
    assert kinds == {"commander_flags", "structural_role_profiles"}
    for imp in first["imports"]:
        assert imp["source_project"] == "commander-playtest-lab"


def test_summary_before_import(loaded_store):
    assert reference_summary(loaded_store) == {"imported": False}
    assert card_reference(loaded_store, OID["sol_ring"]) is None
