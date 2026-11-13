"""Owner-marks import/export — adopted from commander-playtest-lab
PR #1195 (marks.py), adapted to oracle_id identity. Synthetic data only."""
from __future__ import annotations

import json

import pytest

from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.marks import export_owner_marks, import_owner_marks

from conftest import OID, write_foundation_xlsx

ALARA = "Alara, Test Sovereign"
SOL_RING_NAME = "Sol Ring (Test)"  # name in the synthetic Scryfall cards


@pytest.fixture()
def collection_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            (SOL_RING_NAME, 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


def _write(tmp_path, payload, name="marks.json"):
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _mark(store, oracle_id):
    return store.conn.execute(
        "SELECT favorite, excluded, note FROM mark WHERE oracle_id = ?",
        (oracle_id,)).fetchone()


def test_import_by_oracle_id_and_name_and_merge(collection_store, tmp_path):
    store = collection_store
    path = _write(tmp_path, {"format": "deckbuild-marks-1", "marks": [
        {"oracle_id": OID["commander_a"], "favorite": True, "note": "main"},
        {"card_name": SOL_RING_NAME, "excluded": True},
        {"card_name": "No Such Card", "favorite": True},
    ]})
    report = import_owner_marks(store, path)
    assert report["entries"] == 3 and report["resolved"] == 2
    assert report["unresolved"] == 1 and report["changed"] == 2
    row = _mark(store, OID["commander_a"])
    assert (row["favorite"], row["excluded"], row["note"]) == (1, 0, "main")
    # merge: a second file that only sets the note must keep favorite
    path2 = _write(tmp_path, {"format": "studio-marks-1", "marks": [
        {"oracle_id": OID["commander_a"], "note": "updated"}]}, name="m2.json")
    report2 = import_owner_marks(store, path2)
    assert report2["changed"] == 1
    row = _mark(store, OID["commander_a"])
    assert (row["favorite"], row["note"]) == (1, "updated")
    # idempotent: importing the same file again changes nothing
    assert import_owner_marks(store, path2)["changed"] == 0


def test_import_invalid_file_writes_nothing(collection_store, tmp_path):
    store = collection_store
    path = _write(tmp_path, {"format": "deckbuild-marks-1", "marks": [
        {"oracle_id": OID["commander_a"], "favorite": True},
        {"oracle_id": OID["commander_a"], "favorite": "yes"},  # invalid flag
    ]})
    with pytest.raises(ValueError):
        import_owner_marks(store, path)
    assert _mark(store, OID["commander_a"]) is None  # all-or-nothing


def test_unknown_format_rejected_writes_nothing(collection_store, tmp_path):
    store = collection_store
    path = _write(tmp_path, {"app": "some-other-studio", "state": {
        "fav": {"foreign-id-1": True}, "notes": {"foreign-id-1": "hello"}}})
    with pytest.raises(ValueError):
        import_owner_marks(store, path)
    assert _mark(store, OID["commander_a"]) is None


def test_export_roundtrip(collection_store, tmp_path):
    store = collection_store
    import_owner_marks(store, _write(tmp_path, {"format": "deckbuild-marks-1", "marks": [
        {"oracle_id": OID["commander_a"], "favorite": True, "note": "keep"}]}))
    out = tmp_path / "export.json"
    report = export_owner_marks(store, out)
    assert report["marks"] == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["format"] == "deckbuild-marks-1"
    entry = payload["marks"][0]
    assert entry["oracle_id"] == OID["commander_a"]
    assert entry["card_name"] == ALARA and entry["favorite"] is True
    # round-trip into the same store is a no-op
    assert import_owner_marks(store, out)["changed"] == 0
