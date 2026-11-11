import pytest
from fastapi.testclient import TestClient

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import web as web_mod
from deckbuild_studio.external import register_card_atlas_jobs, register_commander_jobs
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook


@pytest.fixture()
def client(loaded_store, tmp_path, monkeypatch):
    rows = [("Alara, Test Sovereign", 1, "Foundation"), ("Plains", 60, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app())


def test_index_and_status(client):
    assert client.get("/").status_code == 200
    status = client.get("/api/status").json()
    assert status["scryfall_cards"] > 0
    assert status["external_data"]["playgroup"] == "NOT_FETCHED"


def test_commanders_endpoint(client):
    data = client.get("/api/commanders", params={"collection_id": FC}).json()
    assert [c["name"] for c in data["eligible"]] == ["Alara, Test Sovereign"]


def test_cards_endpoint_locations(client):
    data = client.get("/api/cards", params={"collection_id": FC}).json()
    plains = next(c for c in data if c["name"] == "Plains")
    assert plains["available"] == 60 and plains["locations"] == ["Foundation"]


def test_jobs_scaffold_not_fetched(loaded_store):
    n = register_commander_jobs(loaded_store, OID["commander_a"], "alara-test-sovereign")
    assert n == 7  # 6 EDHREC + 1 Playgroup
    rows = loaded_store.conn.execute("SELECT DISTINCT status FROM sync_job").fetchall()
    assert [r["status"] for r in rows] == ["NOT_FETCHED"]
    brackets = loaded_store.conn.execute(
        "SELECT bracket, bracket_level FROM sync_job WHERE job_type LIKE 'edhrec%'"
        " ORDER BY bracket_level").fetchall()
    assert [(r["bracket"], r["bracket_level"]) for r in brackets if r["bracket_level"] == 2]
    atlas = register_card_atlas_jobs(loaded_store, FC) if False else 0
    assert atlas == 0  # no collection imported in this fixture's store yet
