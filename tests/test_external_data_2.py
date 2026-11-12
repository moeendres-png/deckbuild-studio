"""External-data-2 tests — D1 Scryfall rulings, D3 EDHTop16, D4 MTGJSON.

Recorded SYNTHETIC fixtures only: no network, no real scrapes, no
private collection data. Fixture structures mirror the real sources
as verified live on 2026-11-12 (Scryfall bulk index + rulings JSONL,
EDHTop16 staples SSR payload, MTGJSON AllPrintings shape).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import edhtop16 as t16_mod
from deckbuild_studio import mtgjson as mj_mod
from deckbuild_studio import rulings as rul_mod
from deckbuild_studio.httpfetch import FetchError, RobotsDisallowed
from deckbuild_studio.importers import import_foundation_workbook
from test_external import FakeFetcher

FX = Path(__file__).parent / "fixtures"
ALARA = "Alara, Test Sovereign"
RING = "Sol Ring (Test)"
RING_OID = OID["sol_ring"]
PLAINS_OID = OID["plains"]
INDEX_URL = rul_mod.BULK_INDEX_URL
RULINGS_URL = "https://data.scryfall.io/rulings/rulings-test.jsonl.gz"


def fx(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


@pytest.fixture()
def collection_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            (RING, 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


# --------------------------------------------------------------------------
# D1 — Scryfall rulings
# --------------------------------------------------------------------------

def _rulings_routes(extra_lines: str = "", file_status: int = 200,
                    index_body: str | None = None) -> dict:
    body = fx("scryfall_rulings.jsonl") + extra_lines
    return {
        INDEX_URL: (200, index_body if index_body is not None
                    else fx("scryfall_bulk_index.json")),
        RULINGS_URL: (file_status, gzip.compress(body.encode())),
    }


def test_rulings_parse_body_variants():
    raw = fx("scryfall_rulings.jsonl").encode()
    rows, stats = rul_mod.parse_rulings_body(gzip.compress(raw))
    assert len(rows) == 4 and stats["malformed"] == 0
    rows2, _ = rul_mod.parse_rulings_body(raw)  # plain JSONL also works
    assert len(rows2) == 4
    bad, stats3 = rul_mod.parse_rulings_body(
        b'{"oracle_id": "x", "comment": "ok"}\nnot json\n{"oracle_id": "y"}\n')
    assert len(bad) == 1 and stats3["malformed"] == 1
    assert stats3["missing_fields"] == 1
    none_rows, stats4 = rul_mod.parse_rulings_body(b"\x1f\x8b corrupt")
    assert none_rows == [] and stats4["unreadable"] is True


def test_rulings_sync_available_and_provenance(collection_store):
    routes = _rulings_routes()
    served_body = routes[RULINGS_URL][1]
    result = rul_mod.sync_rulings(collection_store, FakeFetcher(routes))
    assert result["status"] == "AVAILABLE"
    assert result["total_rulings"] == 4
    assert result["by_source"] == {"wotc": 3, "scryfall": 1}
    assert result["distinct_oracle_ids"] == 3
    assert result["bulk_updated_at"] == "2026-11-12T01:02:03.000+00:00"
    # provenance: the snapshot's sha256 is over the exact wire bytes
    snap = collection_store.conn.execute(
        "SELECT * FROM external_snapshot WHERE kind='scryfall_rulings'"
    ).fetchone()
    assert snap["sha256"] == hashlib.sha256(served_body).hexdigest()
    assert snap["source_url"] == RULINGS_URL
    payload = json.loads(snap["payload_json"])
    assert payload["parser"] == rul_mod.PARSER_ID
    assert payload["total_rulings"] == 4
    cov = result["collection"]
    assert cov["total_identities"] == 3 and cov["with_rulings"] == 2
    assert cov["rulings_total"] == 3  # ring x2 + plains x1 (unknown oid out)


def test_rulings_sync_cached_and_force(collection_store):
    fetcher = FakeFetcher(_rulings_routes())
    rul_mod.sync_rulings(collection_store, fetcher)
    again = rul_mod.sync_rulings(collection_store, fetcher)
    assert again["cached"] is True
    assert fetcher.calls.count(RULINGS_URL) == 1  # download skipped
    forced = rul_mod.sync_rulings(collection_store, fetcher, force=True)
    assert forced["status"] == "AVAILABLE" and "cached" not in forced
    assert fetcher.calls.count(RULINGS_URL) == 2


def test_rulings_sync_partial_on_malformed_lines(collection_store):
    fetcher = FakeFetcher(_rulings_routes(extra_lines="definitely not json\n"))
    result = rul_mod.sync_rulings(collection_store, fetcher)
    assert result["status"] == "PARTIAL"
    assert result["total_rulings"] == 4
    assert "1 lines skipped (1 malformed JSON" in result["detail"]


def test_rulings_sync_blocked_variants(collection_store):
    # index HTTP 500 -> BLOCKED snapshot with the index URL
    routes = _rulings_routes()
    routes[INDEX_URL] = (500, "boom")
    result = rul_mod.sync_rulings(collection_store, FakeFetcher(routes))
    assert result["status"] == "BLOCKED" and result["source_url"] == INDEX_URL
    # index without a rulings entry -> BLOCKED
    empty_index = json.dumps({"object": "list", "data": [
        {"type": "default_cards", "jsonl_download_uri": "https://x/y"}]})
    result = rul_mod.sync_rulings(
        collection_store, FakeFetcher(_rulings_routes(index_body=empty_index)))
    assert result["status"] == "BLOCKED"
    assert "no 'rulings' entry" in result["detail"]
    # bulk file 404 -> NOT_FOUND
    result = rul_mod.sync_rulings(
        collection_store, FakeFetcher(_rulings_routes(file_status=404)))
    assert result["status"] == "NOT_FOUND"


def test_rulings_sync_robots_and_network(collection_store):
    class RobotsFetcher(FakeFetcher):
        def get(self, url, *, etag=None, last_modified=None):
            raise RobotsDisallowed("robots.txt disallows /bulk-data")

    result = rul_mod.sync_rulings(collection_store, RobotsFetcher({}))
    assert result["status"] == "BLOCKED"

    class NetFetcher(FakeFetcher):
        def get(self, url, *, etag=None, last_modified=None):
            raise FetchError(None, "network down")

    with pytest.raises(rul_mod.RulingsError):
        rul_mod.sync_rulings(collection_store, NetFetcher({}))
    # transient network failure writes NOTHING (stays NOT_FETCHED)
    n = collection_store.conn.execute(
        "SELECT COUNT(*) n FROM external_snapshot WHERE kind='scryfall_rulings'"
    ).fetchone()["n"]
    assert n == 1  # only the robots BLOCKED snapshot above


def test_card_rulings_helper_states(collection_store):
    assert rul_mod.card_rulings(collection_store, RING_OID)["status"] == "NOT_FETCHED"
    rul_mod.sync_rulings(collection_store, FakeFetcher(_rulings_routes()))
    got = rul_mod.card_rulings(collection_store, RING_OID)
    assert got["status"] == "AVAILABLE" and len(got["items"]) == 2
    assert got["items"][0]["published_at"] == "2021-05-01"  # DESC order
    assert {i["source"] for i in got["items"]} == {"wotc", "scryfall"}
    empty = rul_mod.card_rulings(collection_store, OID["commander_a"])
    assert empty["status"] == "AVAILABLE" and empty["items"] == []


# --------------------------------------------------------------------------
# D3 — EDHTop16
# --------------------------------------------------------------------------

def test_edhtop16_parse_fixture():
    parsed = t16_mod.parse_staples_page(fx("edhtop16_staples.html"))
    by_name = {c["name"]: c for c in parsed["cards"]}
    assert len(by_name) == 3  # the 1.7-rate record is skipped
    assert parsed["skipped_records"] == 1
    assert by_name[RING]["play_rate_last_year"] == pytest.approx(0.9123)
    assert by_name[RING]["mana_cost"] == "{1}"  # braces survive parsing
    assert by_name[ALARA]["type"].startswith("Legendary Creature")


def test_edhtop16_parse_requires_marker():
    with pytest.raises(t16_mod.ParseError):
        t16_mod.parse_staples_page("<html><body>some other page</body></html>")


def test_edhtop16_sync_and_coverage(collection_store):
    fetcher = FakeFetcher({t16_mod.STAPLES_URL: (200, fx("edhtop16_staples.html"))})
    result = t16_mod.sync_edhtop16(collection_store, fetcher)
    assert result["status"] == "AVAILABLE"
    assert result["cards_published"] == 3
    assert result["resolved_to_local_store"] == 2
    assert result["unresolved_names"] == 1
    cov = result["collection"]
    assert cov["total_identities"] == 3 and cov["with_play_rate"] == 2
    assert "conversion" in result["detail"]  # absence documented in detail
    cached = t16_mod.sync_edhtop16(collection_store, fetcher)
    assert cached["cached"] is True
    card = t16_mod.card_edhtop16(collection_store, RING_OID)
    assert card["listed"] is True
    assert card["play_rate_last_year"] == pytest.approx(0.9123)
    assert card["window"] == "last_year"
    unlisted = t16_mod.card_edhtop16(collection_store, PLAINS_OID)
    assert unlisted["listed"] is False
    assert unlisted["play_rate_last_year"] is None  # unlisted != rate 0


def test_edhtop16_sync_blocked_variants(collection_store):
    html = fx("edhtop16_staples.html")
    result = t16_mod.sync_edhtop16(
        collection_store, FakeFetcher({t16_mod.STAPLES_URL: (403, "no")}))
    assert result["status"] == "BLOCKED"
    result = t16_mod.sync_edhtop16(
        collection_store, FakeFetcher({t16_mod.STAPLES_URL: (404, "no")}))
    assert result["status"] == "NOT_FOUND"
    result = t16_mod.sync_edhtop16(
        collection_store,
        FakeFetcher({t16_mod.STAPLES_URL: (200, "<html>redesign</html>")}))
    assert result["status"] == "PARTIAL"
    assert html  # fixture referenced above stays the happy-path source


# --------------------------------------------------------------------------
# D4 — MTGJSON
# --------------------------------------------------------------------------

def _raw_dir(tmp_path: Path) -> Path:
    raw = tmp_path / "mtgjson"
    raw.mkdir()
    shutil.copy(FX / "mtgjson_printings.json", raw / mj_mod.FILES["printings"])
    return raw


def test_mtgjson_streaming_readers():
    cards = list(mj_mod.iter_printings_cards(FX / "mtgjson_printings.json"))
    assert len(cards) == 5  # tokens array is skipped, not yielded
    meta = mj_mod.read_meta(FX / "mtgjson_printings.json")
    assert meta == {"date": "2026-11-11", "version": "5.3.0+test"}


def test_mtgjson_sync_slices(collection_store, tmp_path):
    raw = _raw_dir(tmp_path)
    result = mj_mod.sync_mtgjson(collection_store, raw)
    assert result["status"] == "AVAILABLE"
    pr = result["printings"]
    assert pr["cards_seen"] == 5 and pr["cards_kept"] == 3
    assert pr["foreign_rows"] == 2 and pr["without_oracle_id"] == 1
    assert pr["kept_oracles"] == 2  # ring + plains (Foreign Only Card is out)
    # Card data only: no price slices exist in the result (owner
    # decision 2026-11-12 — prices/history removed, see module docs).
    assert "prices_today" not in result and "prices_history" not in result
    cov = result["coverage"]
    assert cov["printings"]["collection_oracles_covered"] == 2
    assert cov["printings"]["print_rows"] == 5  # 3 kept cards + 2 foreign rows
    assert cov["printings"]["foreign_rows"] == 2
    assert "prices_today" not in cov and "prices_history" not in cov


def test_mtgjson_no_price_layer(collection_store, tmp_path):
    """Removal regression (owner decision 2026-11-12): the schema has
    no MTGJSON price table, the module exposes no price API, and a
    sync creates no price snapshots — card data only."""
    tables = {r["name"] for r in collection_store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "mtgjson_print" in tables
    assert "mtgjson_price" not in tables
    assert not hasattr(mj_mod, "card_market_prices")
    assert not hasattr(mj_mod, "flatten_prices")
    assert not hasattr(mj_mod, "iter_price_entries")
    assert set(mj_mod.FILES) == {"printings"}
    mj_mod.sync_mtgjson(collection_store, _raw_dir(tmp_path))
    kinds = {r["kind"] for r in collection_store.conn.execute(
        "SELECT DISTINCT kind FROM external_snapshot "
        "WHERE source_name='mtgjson'")}
    assert kinds == {"mtgjson_printings"}


def test_mtgjson_sync_idempotent(collection_store, tmp_path):
    raw = _raw_dir(tmp_path)
    mj_mod.sync_mtgjson(collection_store, raw)
    again = mj_mod.sync_mtgjson(collection_store, raw)
    assert again["printings"]["cached"] is True
    n = collection_store.conn.execute(
        "SELECT COUNT(*) n FROM mtgjson_print").fetchone()["n"]
    assert n == 5  # no duplication on re-run


def test_mtgjson_missing_printings_is_not_fetched(collection_store, tmp_path):
    raw = tmp_path / "empty"
    raw.mkdir()
    result = mj_mod.sync_mtgjson(collection_store, raw)
    assert result["status"] == "NOT_FETCHED"
    n = collection_store.conn.execute(
        "SELECT COUNT(*) n FROM external_snapshot WHERE source_name='mtgjson'"
    ).fetchone()["n"]
    assert n == 0


# --------------------------------------------------------------------------
# Fetcher robots regression — Cloudflare managed robots.txt shape
# (found live on data.scryfall.io during the D1 verification run)
# --------------------------------------------------------------------------

CLOUDFLARE_SHAPED_ROBOTS = """User-agent: *
Content-Signal: search=yes,ai-train=no,use=reference
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: *
Disallow: /temp
Disallow: /errors
"""


def test_robots_rules_cloudflare_shape():
    from deckbuild_studio.httpfetch import _robots_rules
    rules = _robots_rules(CLOUDFLARE_SHAPED_ROBOTS)
    # the named training-crawler 'Disallow: /' must NOT become a
    # wildcard rule just because the wildcard group above it carries
    # an Allow line instead of Disallow lines
    assert rules == ["/temp", "/errors"]


def test_robots_rules_plain_groups_unchanged():
    from deckbuild_studio.httpfetch import _robots_rules
    text = "User-agent: *\nDisallow: /admin\n\nUser-agent: FooBot\nDisallow: /\n"
    assert _robots_rules(text) == ["/admin"]


# --------------------------------------------------------------------------
# Web API — rulings + edhtop16 on the card endpoint
# --------------------------------------------------------------------------

def test_external_card_endpoint_includes_new_layers(
        collection_store, monkeypatch):
    from fastapi.testclient import TestClient

    from deckbuild_studio import web as web_mod
    rul_mod.sync_rulings(collection_store, FakeFetcher(_rulings_routes()))
    t16_mod.sync_edhtop16(
        collection_store,
        FakeFetcher({t16_mod.STAPLES_URL: (200, fx("edhtop16_staples.html"))}))
    monkeypatch.setattr(web_mod, "database_path",
                        lambda: collection_store.path)
    client = TestClient(web_mod.create_app())
    resp = client.get(f"/api/external/card?oracle_id={RING_OID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rulings"]["status"] == "AVAILABLE"
    assert len(data["rulings"]["items"]) == 2
    assert data["edhtop16"]["listed"] is True
    assert data["edhtop16"]["play_rate_last_year"] == pytest.approx(0.9123)
    resp = client.get(f"/api/external/card?oracle_id={PLAINS_OID}")
    data = resp.json()
    assert len(data["rulings"]["items"]) == 1
    assert data["edhtop16"]["listed"] is False


def test_external_card_endpoint_without_syncs(loaded_store, monkeypatch):
    from fastapi.testclient import TestClient

    from deckbuild_studio import web as web_mod
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    client = TestClient(web_mod.create_app())
    resp = client.get(f"/api/external/card?oracle_id={RING_OID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "NOT_FETCHED"  # playgroup layer untouched
    assert data["rulings"] == {"status": "NOT_FETCHED", "items": []}
    assert data["edhtop16"]["status"] == "NOT_FETCHED"
