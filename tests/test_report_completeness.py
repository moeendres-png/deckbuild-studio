"""Completeness table of the data report (TRANSFER-2, issue #44):
one status per data layer — COMPLETE / PARTIAL / MISSING where a
real denominator exists, UNKNOWN where none does. Each test pins one
status class per layer family; the section must stay counts-only.
"""
import json

from conftest import OID, synthetic_cards

from deckbuild_studio import categories as cat_mod
from deckbuild_studio import reference as ref_mod
from deckbuild_studio.report import data_report


def _by_key(report):
    return {e["key"]: e for e in report["completeness"]}


def _collection(store, rows):
    """rows: (oracle_id, quantity, quantity_lower_bound)."""
    store.conn.execute(
        "INSERT INTO collection(collection_id, title, created_at) "
        "VALUES ('c1', 'Test', '2026-01-01')")
    for i, (oid, qty, lower) in enumerate(rows):
        store.conn.execute(
            "INSERT INTO physical_lot(physical_lot_id, collection_id, "
            "oracle_id, location_id, quantity, quantity_lower_bound) "
            "VALUES (?, 'c1', ?, 'loc', ?, ?)", (f"lot{i}", oid, qty, lower))
    store.conn.commit()


def _snapshot(store, sid, source, status):
    store.conn.execute(
        "INSERT INTO external_snapshot(snapshot_id, source_name, kind, "
        "source_url, status, parser_version, fetched_at) "
        "VALUES (?, ?, 'page', 'https://example.invalid', ?, '1', "
        "'2026-01-01')", (sid, source, status))
    store.conn.commit()


def _tier_row(store, oid, version="tierlist/1.1.0"):
    store.conn.execute(
        "INSERT INTO tier_assignment(oracle_id, scope, tier, evidence, "
        "algo_version, computed_at) VALUES (?, 'global', 'B', 1.0, ?, "
        "'2026-01-01')", (oid, version))
    store.conn.commit()


def test_completeness_empty_store_is_missing_or_unknown(store):
    layers = _by_key(data_report(store))
    for key in ("collection_inventory", "card_facts_scryfall",
                "category_check:ORACLE_TEXT_HEURISTIC",
                "category_check:SCRYFALL_TAGGER_SEARCH",
                "reference:structural_role_profiles",
                "reference:commander_flags", "tierlist_global",
                "external:edhrec", "external:edhtop16",
                "external:playgroup", "external:commanderspellbook",
                "external:topdeck"):
        assert layers[key]["status"] == "MISSING", key
    assert layers["card_image_cache"]["status"] == "UNKNOWN"
    assert layers["card_image_cache"]["rows"] is None


def test_completeness_partial_states(loaded_store):
    _collection(loaded_store, [(OID["sol_ring"], 2, None),
                               (OID["forest"], None, None)])
    layers = _by_key(data_report(loaded_store))
    inv = layers["collection_inventory"]
    assert (inv["status"], inv["rows"], inv["covered"], inv["pool"]) == \
        ("PARTIAL", 2, 1, 2)
    facts = layers["card_facts_scryfall"]
    assert (facts["status"], facts["covered"], facts["pool"]) == \
        ("COMPLETE", 2, 2)
    assert layers["category_check:ORACLE_TEXT_HEURISTIC"]["status"] == \
        "MISSING"

    _tier_row(loaded_store, OID["sol_ring"])
    layers = _by_key(data_report(loaded_store))
    tier = layers["tierlist_global"]
    assert (tier["status"], tier["covered"], tier["pool"]) == \
        ("PARTIAL", 1, 2)

    ref_mod.ensure_schema(loaded_store)
    loaded_store.conn.execute(
        "INSERT INTO reference_import(source_kind, source_project, "
        "file_path, file_name, scope_note, entry_count, imported_at) "
        "VALUES ('structural_role_profiles', 'p', 'f', 'f.json', '', 3, "
        "'2026-01-01')")
    for name in ("Card A", "Card B"):
        loaded_store.conn.execute(
            "INSERT INTO reference_role_profile(oracle_name, "
            "resolution_status, estimate_type, payload_json, source_kind) "
            "VALUES (?, 'resolved', 'est', '{}', "
            "'structural_role_profiles')", (name,))
    loaded_store.conn.commit()
    layers = _by_key(data_report(loaded_store))
    ref = layers["reference:structural_role_profiles"]
    assert (ref["status"], ref["rows"], ref["pool"]) == ("PARTIAL", 2, 3)

    _snapshot(loaded_store, "s1", "edhrec", "PARTIAL")
    _snapshot(loaded_store, "s2", "edhtop16", "AVAILABLE")
    layers = _by_key(data_report(loaded_store))
    assert layers["external:edhrec"]["status"] == "PARTIAL"
    assert layers["external:edhtop16"]["status"] == "UNKNOWN"
    assert layers["external:playgroup"]["status"] == "MISSING"
    assert layers["card_image_cache"]["status"] == "UNKNOWN"


def test_completeness_complete_states(loaded_store):
    ids = [c["oracle_id"] for c in synthetic_cards()]
    cat_mod.ensure_schema(loaded_store)
    _collection(loaded_store, [(oid, 1, None) for oid in ids])
    for oid in ids:
        _tier_row(loaded_store, oid)
        for origin in ("ORACLE_TEXT_HEURISTIC", "SCRYFALL_TAGGER_SEARCH"):
            loaded_store.conn.execute(
                "INSERT INTO card_category_check(oracle_id, origin, "
                "version, checked_at, claims) VALUES (?, ?, '1', "
                "'2026-01-01', 0)", (oid, origin))
    loaded_store.conn.commit()
    # The category layers' denominator is the whole Scryfall card set;
    # the synthetic import holds exactly the collection's cards.
    ref_mod.ensure_schema(loaded_store)
    loaded_store.conn.execute(
        "INSERT INTO reference_import(source_kind, source_project, "
        "file_path, file_name, scope_note, entry_count, imported_at) "
        "VALUES ('structural_role_profiles', 'p', 'f', 'f.json', '', 2, "
        "'2026-01-01')")
    loaded_store.conn.execute(
        "INSERT INTO reference_import(source_kind, source_project, "
        "file_path, file_name, scope_note, entry_count, imported_at) "
        "VALUES ('commander_flags', 'p', 'f', 'f.json', '', 1, "
        "'2026-01-01')")
    for name in ("Card A", "Card B"):
        loaded_store.conn.execute(
            "INSERT INTO reference_role_profile(oracle_name, "
            "resolution_status, estimate_type, payload_json, source_kind) "
            "VALUES (?, 'resolved', 'est', '{}', "
            "'structural_role_profiles')", (name,))
    loaded_store.conn.execute(
        "INSERT INTO reference_card_flag(oracle_id, flag, name, "
        "source_kind) VALUES (?, 'game_changer', 'Card A', "
        "'commander_flags')", (ids[0],))
    loaded_store.conn.commit()
    _snapshot(loaded_store, "s1", "edhrec", "AVAILABLE")

    report = data_report(loaded_store)
    layers = _by_key(report)
    for key in ("collection_inventory", "card_facts_scryfall",
                "category_check:ORACLE_TEXT_HEURISTIC",
                "category_check:SCRYFALL_TAGGER_SEARCH",
                "reference:structural_role_profiles",
                "reference:commander_flags", "tierlist_global"):
        assert layers[key]["status"] == "COMPLETE", key
    assert layers["tierlist_global"]["covered"] == \
        layers["tierlist_global"]["pool"] == len(ids)
    # Present but denominator-free layers stay UNKNOWN even here.
    assert layers["external:edhrec"]["status"] == "UNKNOWN"
    assert layers["card_image_cache"]["status"] == "UNKNOWN"
    # Counts only: no card names anywhere in the report.
    assert "Sol Ring (Test)" not in json.dumps(report)
