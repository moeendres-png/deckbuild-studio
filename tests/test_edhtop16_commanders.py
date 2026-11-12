"""EDHTop16 per-card x commander layer — persisted-query API sync.

Recorded SYNTHETIC fixtures only: no network, no real scrapes, no
private collection data. The fixture's structure mirrors the real
API responses as verified live on 2026-11-12 (staples item keys
id/name/type/manaCost/playRateLastYear; stats keys count /
conversionRate / metaShare). Conversion exists ONLY as a
commander-level aggregate — the tests pin that no per-card
conversion is ever stored.
"""
from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import edhtop16 as t16
from deckbuild_studio import httpfetch
from deckbuild_studio.httpfetch import (Fetcher, FetchError, Response,
                                        RobotsDisallowed)
from deckbuild_studio.importers import import_foundation_workbook
from test_external import FakeFetcher

FX = Path(__file__).parent / "fixtures"
ALARA = "Alara, Test Sovereign"
ALPHA = "Partner Alpha"
RING_OID = OID["sol_ring"]
PLAINS_OID = OID["plains"]
STAPLES_ID = t16.PASTORIA_ID_STAPLES
STATS_ID = t16.PASTORIA_ID_STATS


def fx(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


@pytest.fixture()
def api():
    return json.loads(fx("edhtop16_commander_api.json"))


@pytest.fixture()
def one_commander_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            ("Sol Ring (Test)", 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


@pytest.fixture()
def two_commander_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), (ALPHA, 1, "Foundation"),
            ("Plains", 60, "Foundation"),
            ("Sol Ring (Test)", 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


class FakeApiFetcher(FakeFetcher):
    """FakeFetcher + post_json routed by (pastoria-id, commander).

    Routes map to (status, body) tuples, callables taking the payload,
    or Exception instances to raise."""

    def __init__(self, api_routes):
        super().__init__({})
        self.api_routes = api_routes
        self.posts: list[dict] = []

    def post_json(self, url, payload):
        self.posts.append(payload)
        key = (payload["extensions"]["pastoria-id"],
               payload["variables"].get("commander"))
        handler = self.api_routes.get(key)
        if handler is None:
            return Response(status=404, body=b"not found", url=url)
        if isinstance(handler, Exception):
            raise handler
        if callable(handler):
            return handler(payload)
        status, body = handler
        if isinstance(body, str):
            body = body.encode()
        return Response(status=status, body=body, url=url)


def _routes(api, commander=ALARA, overrides=None):
    staples = json.loads(json.dumps(api["staples_response"]))
    staples["data"]["commander"]["name"] = commander
    routes = {
        (STAPLES_ID, commander): (200, json.dumps(staples)),
        (STATS_ID, commander): (200, json.dumps(api["stats_response"])),
    }
    routes.update(overrides or {})
    return routes


def _commander_rows(store):
    return store.conn.execute(
        "SELECT * FROM edhtop16_commander_card_stat ORDER BY card_name"
    ).fetchall()


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def test_parse_commander_staples_fixture(api):
    parsed = t16.parse_commander_staples(json.dumps(api["staples_response"]))
    assert parsed["commander_name"] == ALARA
    assert parsed["skipped_records"] == 1  # the 1.7-rate record
    by_name = {c["name"]: c for c in parsed["cards"]}
    assert len(by_name) == 3
    assert by_name["Sol Ring (Test)"]["play_rate"] == pytest.approx(0.5)
    assert by_name["Sol Ring (Test)"]["mana_cost"] == "{1}"
    assert by_name["Plains"]["type"].startswith("Basic Land")


def test_parse_commander_staples_not_found_and_garbage():
    with pytest.raises(t16.CommanderNotFound):
        t16.parse_commander_staples('{"data": {"commander": null}}')
    with pytest.raises(t16.ParseError):
        t16.parse_commander_staples("not json")
    with pytest.raises(t16.ParseError):
        t16.parse_commander_staples('{"data": {"commander": {"name": "X"}}}')


def test_parse_commander_stats_fixture_and_absent(api):
    stats = t16.parse_commander_stats(json.dumps(api["stats_response"]))
    assert stats == {"entries_n": 40,
                     "conversion_rate": pytest.approx(0.275),
                     "meta_share": pytest.approx(0.0125)}
    empty = {"entries_n": None, "conversion_rate": None, "meta_share": None}
    assert t16.parse_commander_stats('{"data": {"commander": null}}') == empty
    assert t16.parse_commander_stats('{"data": {"commander": {}}}') == empty
    with pytest.raises(t16.ParseError):
        t16.parse_commander_stats("not json")


# ---------------------------------------------------------------------------
# Sync — happy path, provenance, caching
# ---------------------------------------------------------------------------

def test_sync_commanders_available(one_commander_store, api):
    fetcher = FakeApiFetcher(_routes(api))
    result = t16.sync_edhtop16_commanders(one_commander_store, fetcher)
    assert result["eligible_commanders"] == 1
    assert result["available"] == 1 and result["pairs_stored"] == 3
    assert len(fetcher.posts) == 2  # staples + stats, nothing else

    rows = _commander_rows(one_commander_store)
    assert len(rows) == 3
    ring = next(r for r in rows if r["card_name"] == "Sol Ring (Test)")
    assert ring["card_oracle_id"] == RING_OID
    assert ring["play_rate"] == pytest.approx(0.5)
    assert ring["entries_n"] == 40  # commander-level denominator per row
    assert ring["window"] == "ONE_YEAR"
    unknown = next(r for r in rows if r["card_name"] == "Unknown Card (Test)")
    assert unknown["card_oracle_id"] is None  # unresolved stays NULL

    # conversion lives ONLY in the commander-level aggregate table
    stat = one_commander_store.conn.execute(
        "SELECT * FROM edhtop16_commander_stat").fetchone()
    assert stat["commander_name"] == ALARA
    assert stat["entries_n"] == 40
    assert stat["conversion_rate"] == pytest.approx(0.275)
    assert stat["meta_share"] == pytest.approx(0.0125)
    card_cols = {r[1] for r in one_commander_store.conn.execute(
        "PRAGMA table_info(edhtop16_commander_card_stat)")}
    assert "conversion_rate" not in card_cols  # never a per-card value

    # provenance: snapshot carries parser, window, endpoint, query ids
    snap = one_commander_store.conn.execute(
        "SELECT * FROM external_snapshot WHERE kind=?",
        (t16.KIND_COMMANDER,)).fetchone()
    assert snap["status"] == "AVAILABLE"
    assert snap["source_url"] == t16.commander_page_url(ALARA)
    assert snap["sample_size"] == 40
    payload = json.loads(snap["payload_json"])
    assert payload["parser"] == t16.CMD_PARSER_ID
    assert payload["persisted_queries"]["staples"] == STAPLES_ID

    cov = result["coverage"]
    assert cov["commanders_by_status"] == {"AVAILABLE": 1}
    assert cov["pairs_total"] == 3
    assert cov["collection_cards_with_commander_values"] == 2  # ring+plains
    assert cov["total_identities"] == 3
    assert cov["pairs_per_commander_min"] == 3
    assert cov["pairs_per_commander_max"] == 3

    card = t16.card_edhtop16_commanders(one_commander_store, RING_OID)
    assert card["status"] == "AVAILABLE"
    assert len(card["commanders"]) == 1
    assert card["commanders"][0]["commander"] == ALARA
    assert card["commanders"][0]["play_rate"] == pytest.approx(0.5)
    assert card["commanders"][0]["entries_n"] == 40
    unlisted = t16.card_edhtop16_commanders(one_commander_store, PLAINS_OID)
    assert unlisted["commanders"][0]["play_rate"] == pytest.approx(0.25)


def test_sync_commanders_cached_and_force(one_commander_store, api):
    fetcher = FakeApiFetcher(_routes(api))
    t16.sync_edhtop16_commanders(one_commander_store, fetcher)
    again = t16.sync_edhtop16_commanders(one_commander_store, fetcher)
    assert again["cached_skipped"] == 1 and again["attempted"] == 0
    assert len(fetcher.posts) == 2  # no refetch without force
    forced = t16.sync_edhtop16_commanders(
        one_commander_store, fetcher, force=True)
    assert forced["available"] == 1
    assert len(fetcher.posts) == 4


def test_card_commanders_not_fetched(one_commander_store):
    got = t16.card_edhtop16_commanders(one_commander_store, RING_OID)
    assert got == {"status": "NOT_FETCHED", "commanders": []}
    cov = t16.edhtop16_commander_coverage(
        one_commander_store, "foundation-schwarze-box")
    assert cov["commanders_by_status"] == {"NOT_FETCHED": 1}
    assert cov["pairs_total"] == 0


# ---------------------------------------------------------------------------
# Sync — degraded and terminal outcomes
# ---------------------------------------------------------------------------

def test_sync_commanders_stats_failure_is_partial(one_commander_store, api):
    routes = _routes(api, overrides={(STATS_ID, ALARA): (500, "boom")})
    result = t16.sync_edhtop16_commanders(
        one_commander_store, FakeApiFetcher(routes))
    assert result["partial"] == 1 and result["available"] == 0
    # Without a usable entry count the API's zero-entry global
    # fallback cannot be ruled out, so card rows are WITHHELD (the
    # raw bundle stays in the snapshot; a later run fills them in).
    assert result["pairs_stored"] == 0
    assert _commander_rows(one_commander_store) == []
    stat = one_commander_store.conn.execute(
        "SELECT * FROM edhtop16_commander_stat").fetchone()
    assert stat["entries_n"] is None and stat["conversion_rate"] is None
    outcome = result["results"][0]
    assert "stats query answered HTTP 500" in outcome["detail"]
    assert "card rows withheld" in outcome["detail"]


def test_sync_commanders_zero_entries_discards_fallback(one_commander_store,
                                                        api):
    # Live-verified API behaviour (2026-11-12): a commander with 0
    # entries in the window gets the GLOBAL staples list back under
    # its own name (off-colour-identity cards at global rates). The
    # fixture's staples stand in for that fallback payload here.
    stats = json.loads(json.dumps(api["stats_response"]))
    stats["data"]["commander"]["stats"] = {
        "conversionRate": 0, "count": 0, "metaShare": 0}
    routes = _routes(api, overrides={
        (STATS_ID, ALARA): (200, json.dumps(stats))})
    result = t16.sync_edhtop16_commanders(
        one_commander_store, FakeApiFetcher(routes))
    # The capture itself succeeded — the truthful answer is "no data"
    assert result["available"] == 1 and result["partial"] == 0
    assert result["pairs_stored"] == 0  # fallback rows NOT attributed
    assert _commander_rows(one_commander_store) == []
    stat = one_commander_store.conn.execute(
        "SELECT * FROM edhtop16_commander_stat").fetchone()
    assert stat["entries_n"] == 0  # the published aggregate is stored
    assert stat["conversion_rate"] == 0
    outcome = result["results"][0]
    assert outcome["entries_n"] == 0
    assert "0 entries in the ONE_YEAR window" in outcome["detail"]
    assert "discarded" in outcome["detail"]
    snap = one_commander_store.conn.execute(
        "SELECT * FROM external_snapshot WHERE kind=?",
        (t16.KIND_COMMANDER,)).fetchone()
    assert snap["status"] == "AVAILABLE" and snap["sample_size"] == 0
    payload = json.loads(snap["payload_json"])
    assert payload["cards"] == 0 and payload["staples_returned"] == 3
    cov = result["coverage"]
    assert cov["pairs_total"] == 0
    assert cov["collection_cards_with_commander_values"] == 0


def test_sync_commanders_not_found_continues(two_commander_store, api):
    null_body = '{"data": {"commander": null}}'
    routes = _routes(api, commander=ALPHA,
                     overrides={(STAPLES_ID, ALARA): (200, null_body)})
    result = t16.sync_edhtop16_commanders(
        two_commander_store, FakeApiFetcher(routes))
    assert result["not_found"] == 1 and result["available"] == 1
    assert result["stopped_on_block"] is False
    cov = result["coverage"]
    assert cov["commanders_by_status"] == {"NOT_FOUND": 1, "AVAILABLE": 1}


def test_sync_commanders_blocked_stops_run(two_commander_store, api):
    routes = _routes(api, commander=ALPHA,
                     overrides={(STAPLES_ID, ALARA): (403, "no")})
    fetcher = FakeApiFetcher(routes)
    result = t16.sync_edhtop16_commanders(two_commander_store, fetcher)
    assert result["blocked"] == 1 and result["stopped_on_block"] is True
    assert result["attempted"] == 1
    # the second commander was never even requested — no escalation
    assert all(p["variables"]["commander"] == ALARA for p in fetcher.posts)
    snap = two_commander_store.conn.execute(
        "SELECT status FROM external_snapshot WHERE kind=?",
        (t16.KIND_COMMANDER,)).fetchone()
    assert snap["status"] == "BLOCKED"


def test_sync_commanders_robots_blocked(two_commander_store):
    routes = {(STAPLES_ID, ALARA): RobotsDisallowed("robots disallows /api/graphql")}
    result = t16.sync_edhtop16_commanders(
        two_commander_store, FakeApiFetcher(routes))
    assert result["blocked"] == 1 and result["stopped_on_block"] is True


def test_sync_commanders_network_error_continues(two_commander_store, api):
    routes = _routes(api, commander=ALPHA,
                     overrides={(STAPLES_ID, ALARA): FetchError(
                         None, "network error: IncompleteRead(11567 bytes read)")})
    result = t16.sync_edhtop16_commanders(
        two_commander_store, FakeApiFetcher(routes))
    assert result["network_errors"] == 1 and result["available"] == 1
    # the underlying transport error survives into the report — a bare
    # "transient network failure" proved undiagnosable in the live runs
    outcome = next(r for r in result["results"]
                   if r["commander"] == ALARA)
    assert outcome["status"] == "NETWORK"
    assert "IncompleteRead" in outcome["detail"]
    # transient failure wrote NOTHING for that commander (stays NOT_FETCHED)
    n = two_commander_store.conn.execute(
        "SELECT COUNT(*) n FROM external_snapshot WHERE kind=? "
        "AND commander_oracle_id=?",
        (t16.KIND_COMMANDER, OID["commander_a"])).fetchone()["n"]
    assert n == 0


def test_sync_commanders_name_mismatch_not_attributed(one_commander_store, api):
    other = json.loads(json.dumps(api["staples_response"]))
    other["data"]["commander"]["name"] = "Somebody Else, the Wrong"
    routes = _routes(api, overrides={(STAPLES_ID, ALARA): (200, json.dumps(other))})
    result = t16.sync_edhtop16_commanders(
        one_commander_store, FakeApiFetcher(routes))
    assert result["partial"] == 1 and result["pairs_stored"] == 0
    assert _commander_rows(one_commander_store) == []
    assert "not the requested" in result["results"][0]["detail"]


def test_sync_commanders_limit(two_commander_store, api):
    routes = _routes(api)
    routes.update(_routes(api, commander=ALPHA))
    result = t16.sync_edhtop16_commanders(
        two_commander_store, FakeApiFetcher(routes), limit=1)
    assert result["attempted"] == 1 and result["available"] == 1
    assert result["eligible_commanders"] == 2


# ---------------------------------------------------------------------------
# Fetcher.post_json — the sanctioned POST channel's politeness rules
# ---------------------------------------------------------------------------

class _HttpResp:
    def __init__(self, status=200, body=b"{}"):
        self.status = status
        self._body = body
        self.headers = {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _post_fetcher(monkeypatch, behaviours):
    """A real Fetcher whose urlopen replays `behaviours` in order
    (each a _HttpResp to return or an exception to raise)."""
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        behaviour = behaviours.pop(0)
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour

    monkeypatch.setattr(httpfetch.urllib.request, "urlopen", fake_urlopen)
    fetcher = Fetcher(min_interval=0, sleeper=lambda s: None)
    fetcher._robots["edhtop16.com"] = []  # robots pre-resolved: allowed
    return fetcher, calls


def test_post_json_success_sends_payload(monkeypatch):
    fetcher, calls = _post_fetcher(monkeypatch, [_HttpResp(200, b'{"ok": 1}')])
    resp = fetcher.post_json(t16.GRAPHQL_URL, {"variables": {"commander": "X"},
                                               "extensions": {"pastoria-id": "abc"}})
    assert resp.status == 200 and resp.text == '{"ok": 1}'
    req = calls[0]
    assert req.get_method() == "POST"
    sent = json.loads(req.data.decode())
    assert sent["extensions"]["pastoria-id"] == "abc"
    assert req.headers["Content-type"] == "application/json"


def test_post_json_retries_5xx_not_429(monkeypatch):
    err500 = urllib.error.HTTPError(t16.GRAPHQL_URL, 500, "boom", {},
                                    io.BytesIO(b"err"))
    fetcher, calls = _post_fetcher(monkeypatch, [err500, _HttpResp(200)])
    resp = fetcher.post_json(t16.GRAPHQL_URL, {"variables": {}})
    assert resp.status == 200 and len(calls) == 2  # one 5xx retry

    err429 = urllib.error.HTTPError(t16.GRAPHQL_URL, 429, "slow down", {},
                                    io.BytesIO(b"err"))
    fetcher, calls = _post_fetcher(monkeypatch, [err429])
    resp = fetcher.post_json(t16.GRAPHQL_URL, {"variables": {}})
    assert resp.status == 429 and len(calls) == 1  # 429 returned, no retry


def test_post_json_gzip_roundtrip(monkeypatch):
    # The staples answers are ~13 KB plain; the server drops those
    # connections mid-response (live diagnosis 2026-11-12), while the
    # ~3 KB gzip form gets through — post_json negotiates gzip and
    # decompresses transparently.
    import gzip as gzip_mod
    resp = _HttpResp(200, gzip_mod.compress(b'{"ok": 1}'))
    resp.headers = {"Content-Encoding": "gzip"}
    fetcher, calls = _post_fetcher(monkeypatch, [resp])
    out = fetcher.post_json(t16.GRAPHQL_URL, {"variables": {}})
    assert out.status == 200 and out.text == '{"ok": 1}'
    assert calls[0].headers["Accept-encoding"] == "gzip"


def test_post_json_network_error_retried_then_raises(monkeypatch):
    # The EDHTop16 server drops connections mid-response (observed
    # live: RemoteDisconnected / IncompleteRead) — transient network
    # failures are retried with backoff like in Fetcher.get, bounded
    # by max_retries, then surface as FetchError.
    fetcher, calls = _post_fetcher(
        monkeypatch, [urllib.error.URLError("down")] * 4)
    with pytest.raises(FetchError):
        fetcher.post_json(t16.GRAPHQL_URL, {"variables": {}})
    assert len(calls) == 4  # 1 initial + 3 retries

    fetcher, calls = _post_fetcher(
        monkeypatch, [urllib.error.URLError("down"), _HttpResp(200)])
    resp = fetcher.post_json(t16.GRAPHQL_URL, {"variables": {}})
    assert resp.status == 200 and len(calls) == 2  # recovered
