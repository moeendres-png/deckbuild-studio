import pytest
from openpyxl import Workbook

from conftest import OID, write_foundation_xlsx
from deckbuild_studio.importers import (
    FOUNDATION_COLLECTION,
    ImportFailure,
    import_foundation_workbook,
    import_mapped_file,
    import_normalized_workbook,
    normalization_report,
)
from deckbuild_studio.scryfall import import_scryfall


def test_scryfall_import_counts(loaded_store, scryfall_file):
    n = loaded_store.conn.execute("SELECT COUNT(*) FROM scryfall_card").fetchone()[0]
    assert n == len(OID)


def test_scryfall_json_array(tmp_path, store):
    import json
    from conftest import synthetic_cards
    p = tmp_path / "cards.json"
    p.write_text(json.dumps(synthetic_cards()))
    result = import_scryfall(store, p)
    assert result["oracle_identities"] == len(OID)


def _foundation_rows():
    return [("Alara, Test Sovereign", 1, "Foundation"),
            ("Faithful Squire // Kaiso, Memory of Loyalty", 1, "Schwarze Box"),
            ("Plains", 60, "Foundation"),
            ("Forest", 60, "Schwarze Box"),
            ("Sol Ring (Test)", 2, "Schwarze Box")]


def test_foundation_import_and_reconciliation(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", _foundation_rows())
    report = import_foundation_workbook(loaded_store, path)
    assert report["rows"] == 5
    assert report["identities"] == 5
    assert report["copies"] == 124
    assert report["locations"] == {"Foundation": 61, "Schwarze Box": 63}
    rep = normalization_report(loaded_store)["collections"][0]
    assert rep["collection_id"] == FOUNDATION_COLLECTION
    assert rep["distinct_oracle_identities"] == 5
    assert rep["locations"] == {"Foundation": 61, "Schwarze Box": 63}
    # reserved=0 only as declared assumption
    row = loaded_store.conn.execute(
        "SELECT reserved_quantity, reserved_assumption FROM physical_lot LIMIT 1").fetchone()
    assert row["reserved_quantity"] == 0
    assert row["reserved_assumption"] == "preliminary_zero_declared"


def test_foundation_import_idempotent(loaded_store, tmp_path):
    path = write_foundation_xlsx(tmp_path / "f.xlsx", _foundation_rows())
    import_foundation_workbook(loaded_store, path)
    import_foundation_workbook(loaded_store, path)
    rep = normalization_report(loaded_store)["collections"][0]
    assert rep["copies_reported"] == 124
    assert rep["source_rows"] == 5


def test_foundation_unresolved_aborts_and_rolls_back(loaded_store, tmp_path):
    rows = _foundation_rows() + [("Nonexistent Card XYZ", 1, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    with pytest.raises(ImportFailure) as exc:
        import_foundation_workbook(loaded_store, path)
    assert any(e["problem"] == "unresolved" for e in exc.value.report["errors"])
    assert loaded_store.conn.execute("SELECT COUNT(*) FROM physical_lot").fetchone()[0] == 0


def test_upsert_keeps_missing_rows_replace_snapshot_deletes_audited(loaded_store, tmp_path):
    p1 = write_foundation_xlsx(tmp_path / "f1.xlsx", _foundation_rows())
    import_foundation_workbook(loaded_store, p1)
    smaller = [r for r in _foundation_rows() if r[0] != "Sol Ring (Test)"]
    p2 = write_foundation_xlsx(tmp_path / "f2.xlsx", smaller)
    report = import_foundation_workbook(loaded_store, p2)  # default upsert
    assert report["lots_removed"] == 0
    assert loaded_store.available_by_oracle(FOUNDATION_COLLECTION)[OID["sol_ring"]] == 2
    report = import_foundation_workbook(loaded_store, p2, mode="replace-snapshot")
    assert report["lots_removed"] == 1
    assert OID["sol_ring"] not in loaded_store.available_by_oracle(FOUNDATION_COLLECTION)
    events = loaded_store.conn.execute(
        "SELECT COUNT(*) FROM inventory_event WHERE event_type='lot_removed'").fetchone()[0]
    assert events == 1


def _normalized_workbook(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "01_CARD_IDENTITY"
    ws.append(["card_id", "oracle_id", "oracle_name", "german_name", "color_identity",
               "mana_cost", "mana_value", "type_line", "oracle_text", "is_basic_land",
               "commander_legal", "legality_verified_at", "identity_evidence_type"])
    ws.append(["card-001", OID["commander_a"], "Alara, Test Sovereign", None, "GW",
               "{2}{G}{W}", 4, "Legendary Creature — Human Noble", "Vigilance", False,
               True, "2026-11-09", "scryfall_name"])
    ws.append(["card-002", OID["sol_ring"], "Sol Ring (Test)", None, "",
               "{1}", 1, "Artifact", "{T}: Add {C}{C}.", False, True,
               "2026-11-09", "scryfall_name"])
    ws = wb.create_sheet("02_PHYSICAL_LOTS")
    ws.append(["physical_lot_id", "card_id", "quantity_observed", "quantity_lower_bound",
               "quantity_exact", "printing_ref", "condition", "location_id", "pool_status",
               "reserved_quantity", "reservation_target_id", "source_id", "verified_at", "note"])
    ws.append(["lot-1", "card-001", 1, 1, True, None, "NM", "loc-a", "available", 0,
               None, "src-1", "2026-11-09", None])
    ws.append(["lot-2", "card-002", 3, 3, True, None, "NM", "loc-a", "available", 1,
               "opp-1", "src-1", "2026-11-09", None])
    ws = wb.create_sheet("03_LOCATIONS")
    ws.append(["location_id", "location_name", "location_type", "ownership_semantics"])
    ws.append(["loc-a", "Box A", "box", "own"])
    ws = wb.create_sheet("05_INVENTORY_CURRENT")
    ws.append(["card_id", "observed_quantity", "physical_owned_quantity_lower_bound",
               "reserved_for_opponents_quantity", "available_for_own_decks_quantity_lower_bound",
               "quantity_exact", "quantity_semantics", "number_of_lots",
               "currently_available_for_own_decks", "last_verified_at"])
    ws.append(["card-001", 1, 1, 0, 1, True, "exact", 1, True, "2026-11-09"])
    ws.append(["card-002", 3, 3, 1, 2, True, "exact", 1, True, "2026-11-09"])
    wb.save(path)
    return path


def test_normalized_import_lossless_ids_and_reservation(loaded_store, tmp_path):
    path = _normalized_workbook(tmp_path / "n.xlsx")
    report = import_normalized_workbook(loaded_store, path, collection_id="normalized-test")
    assert report["identities"] == 2 and report["lots"] == 2
    assert report["inventory_current_mismatches"] == []
    ids = {r["card_id"] for r in loaded_store.conn.execute("SELECT card_id FROM card_identity")}
    assert ids == {"card-001", "card-002"}
    avail = loaded_store.available_by_oracle("normalized-test")
    assert avail[OID["sol_ring"]] == 2  # 3 copies - 1 reserved


def test_normalized_import_rollback_on_bad_lot(loaded_store, tmp_path):
    path = _normalized_workbook(tmp_path / "n.xlsx")
    wb = Workbook()
    # corrupt: reference unknown card in lots by rebuilding minimal broken file
    from openpyxl import load_workbook
    book = load_workbook(path)
    book["02_PHYSICAL_LOTS"].append(
        ["lot-x", "card-999", 1, 1, True, None, "NM", "loc-a", "available", 0,
         None, "src-1", "2026-11-09", None])
    book.save(path)
    with pytest.raises(ImportFailure):
        import_normalized_workbook(loaded_store, path, collection_id="normalized-test")
    assert loaded_store.conn.execute("SELECT COUNT(*) FROM card_identity").fetchone()[0] == 0


def test_mapped_csv_import(loaded_store, tmp_path):
    csv_path = tmp_path / "other.csv"
    csv_path.write_text(
        "Name;Menge;Box;Reserviert\nAlara, Test Sovereign;1;Kiste 1;0\nPlains;10;Kiste 1;2\n",
        encoding="utf-8")
    # csv module default delimiter is ',' — the mapping fixture uses ';' via excel? keep simple:
    csv_path.write_text(
        'Name,Menge,Box,Reserviert\n"Alara, Test Sovereign",1,Kiste 1,0\nPlains,10,Kiste 1,2\n',
        encoding="utf-8")
    mapping = {"collection_id": "mapped-profile",
               "columns": {"name": "Name", "quantity": "Menge", "location": "Box",
                           "reserved": "Reserviert", "condition": None}}
    report = import_mapped_file(loaded_store, csv_path, mapping)
    assert report["identities"] == 2 and report["copies"] == 11
    assert loaded_store.available_by_oracle("mapped-profile")[OID["plains"]] == 8
    # profile isolation
    assert loaded_store.available_by_oracle(FOUNDATION_COLLECTION) == {}


def test_mapped_xlsx_import(loaded_store, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Bestand"
    ws.append(["Titel", "Stk", "Ort"])
    ws.append(["Forest", 5, "Mappe"])
    wb.save(tmp_path / "other.xlsx")
    mapping = {"collection_id": "mapped-xlsx", "sheet": "Bestand",
               "columns": {"name": "Titel", "quantity": "Stk", "location": "Ort"}}
    report = import_mapped_file(loaded_store, tmp_path / "other.xlsx", mapping)
    assert report["copies"] == 5
