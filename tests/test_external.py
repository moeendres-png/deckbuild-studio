"""Phase-2 external-data tests — recorded SYNTHETIC fixtures only.

No network, no real scrapes, no private collection data. The fixtures
mirror the real page structures verified on 2026-11-11 (EDHREC RSC JSON,
Playgroup public commander JSON, autocomplete fragment, Card Atlas HTML)
with invented commanders/cards/numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import OID, write_foundation_xlsx
from deckbuild_studio import edhrec as edhrec_mod
from deckbuild_studio import external as ext
from deckbuild_studio import playgroup as pg_mod
from deckbuild_studio.httpfetch import Fetcher, Response, _robots_match, _robots_rules
from deckbuild_studio.importers import FOUNDATION_COLLECTION as FC
from deckbuild_studio.importers import import_foundation_workbook
from deckbuild_studio.slugs import slugify

FX = Path(__file__).parent / "fixtures"
ALARA = "Alara, Test Sovereign"
ALARA_SLUG = "alara-test-sovereign"
ALARA_OID = OID["commander_a"]


def fx(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


class FakeFetcher(Fetcher):
    """Route-table fetcher: no network, no robots fetch, calls recorded."""

    def __init__(self, routes):
        super().__init__(min_interval=0)
        self.routes = routes
        self.calls: list[str] = []

    def assert_allowed(self, url: str) -> None:  # robots tested separately
        return None

    def get(self, url: str, *, etag=None, last_modified=None) -> Response:
        self.calls.append(url)
        handler = self.routes.get(url)
        if handler is None:
            for prefix, h in self.routes.items():
                if url.startswith(prefix):
                    handler = h
                    break
        if handler is None:
            return Response(status=404, body=b"not found", url=url)
        if callable(handler):
            return handler(url)
        status, body = handler
        if isinstance(body, str):
            body = body.encode()
        return Response(status=status, body=body, url=url)


def edhrec_routes() -> dict:
    routes = {}
    for bracket in ext.BRACKETS:
        routes[f"https://edhrec.com/commanders/{ALARA_SLUG}/{bracket}"] = (200, fx("edhrec_stats.html"))
        routes[f"https://edhrec.com/commanders/{ALARA_SLUG}/{bracket}/decks"] = (200, fx("edhrec_decks.html"))
    return routes


@pytest.fixture()
def collection_store(loaded_store, tmp_path):
    rows = [(ALARA, 1, "Foundation"), ("Plains", 60, "Foundation"),
            ("Sol Ring (Test)", 1, "Schwarze Box")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    return loaded_store


# ---------------------------------------------------------------- slugs/robots

def test_slugify():
    assert slugify("Chulane, Teller of Tales") == "chulane-teller-of-tales"
    assert slugify("Alara, Test Sovereign") == ALARA_SLUG
    assert slugify("Faithful Squire // Kaiso, Memory of Loyalty") == "faithful-squire"
    assert slugify("Lim-Dûl's Vault") == "lim-duls-vault"
    assert slugify("Sol Ring") == "sol-ring"


def test_slugify_full_and_card_page_slug():
    from deckbuild_studio.external import _card_page_slug
    from deckbuild_studio.slugs import slugify_full
    assert slugify_full("Rise // Fall") == "rise-fall"
    assert slugify_full("Faithful Squire // Kaiso, Memory of Loyalty") == \
        "faithful-squire-kaiso-memory-of-loyalty"
    # Split-layout cards are addressed by full name on EDHREC and
    # Playgroup (verified live 2026-11-12); all other layouts by front.
    assert _card_page_slug("Rise // Fall", "split") == "rise-fall"
    assert _card_page_slug("Faithful Squire // Kaiso, Memory of Loyalty",
                           "transform") == "faithful-squire"
    assert _card_page_slug("Sol Ring", "normal") == "sol-ring"
    assert _card_page_slug("Rise // Fall", None) == "rise"


def test_robots_rules_respected():
    _robots_rules("User-agent: *\nDisallow: /deckpreview/\nDisallow: /articles/preview$\n")
    assert _robots_match("/deckpreview/", "/deckpreview/abc")
    assert not _robots_match("/deckpreview/", "/commanders/x/core")
    assert _robots_match("/articles/preview$", "/articles/preview")
    assert not _robots_match("/articles/preview$", "/articles/preview/x")


# ---------------------------------------------------------------- EDHREC parser

def test_parse_edhrec_stats_fixture():
    parsed = edhrec_mod.parse_stats_page(fx("edhrec_stats.html"),
                                         expected_name=ALARA, expected_slug=ALARA_SLUG,
                                         bracket="core")
    assert parsed["commander"]["name"] == ALARA
    assert parsed["cohort_decks"] == 10
    assert parsed["bracket_counts_all"] == {"core": 10, "upgraded": 20, "optimized": 30}
    assert parsed["categories"]["top-cards"] == "Top Cards"
    assert parsed["displayed_total"] is None and parsed["coverage_status"] == "TOTAL_UNKNOWN"
    cards = {c["name"]: c for c in parsed["cards"]}
    assert cards["Test Sol Ring"]["num_decks"] == 5
    assert cards["Test Sol Ring"]["potential_decks"] == 10
    assert cards["Test Sol Ring"]["inclusion"] == 0.5
    # zero denominator -> inclusion must become unknown, never 0/0 invented
    assert cards["Test Beast"]["potential_decks"] == 0
    assert cards["Test Beast"]["inclusion"] is None


def test_parse_edhrec_stats_verification_mismatch():
    with pytest.raises(edhrec_mod.VerificationError):
        edhrec_mod.parse_stats_page(fx("edhrec_stats.html"),
                                    expected_name="Someone Else",
                                    expected_slug="someone-else", bracket="core")


def test_parse_edhrec_decks_dedupe_and_coverage():
    parsed = edhrec_mod.parse_decks_page(fx("edhrec_decks.html"),
                                         expected_name=ALARA, expected_slug=ALARA_SLUG,
                                         bracket="core")
    assert parsed["captured_count"] == 2  # duplicate urlhash deduped
    assert parsed["displayed_total"] == 10
    assert parsed["coverage_status"] == "PARTIAL"  # 2 of 10 — never claim all
    entry = parsed["entries"][0]
    assert entry["savedate"] == "2026-01-02" and entry["type_counts"]["creatures"] == 40


# ---------------------------------------------------------------- Playgroup parser

def test_parse_playgroup_autocomplete_exact_only():
    hit = pg_mod.parse_autocomplete(fx("playgroup_autocomplete.html"), ALARA)
    assert hit == {"playgroup_id": 9999, "slug": ALARA_SLUG, "label": ALARA,
                   "url": f"https://playgroup.gg/commanders/9999-{ALARA_SLUG}"}
    assert pg_mod.parse_autocomplete(fx("playgroup_autocomplete.html"), "Nonexistent") is None


def test_parse_playgroup_commander_json():
    parsed = pg_mod.parse_commander_json(fx("playgroup_commander.json"), expected_name=ALARA)
    assert parsed["playgroup_id"] == 9999 and parsed["sample_size"] == 100
    assert parsed["stats"]["games_won"] == 30
    assert "matchups" in parsed["absent_from_public_json"]
    with pytest.raises(pg_mod.ParseError):
        pg_mod.parse_commander_json(fx("playgroup_commander.json"), expected_name="Other")


def test_parse_playgroup_card_full():
    f = pg_mod.parse_card_page(fx("playgroup_card_full.html"), expected_name="Test Ring")
    assert f["times_brought"] == 131091 and f["decks_running"] == 56468
    assert f["live_inclusion_pct"] == 88 and f["drawn_to_played_pct"] == 90
    assert f["first_cast_n"] == 33509
    assert f["first_cast_distribution_pct"]["T1"] == 35
    assert f["cast_turn_p25"] == 1 and f["cast_turn_p75"] == 6
    assert f["on_curve"] == {"pct": 35.0, "numerator": 11627, "denominator": 33509,
                             "turn": 1, "definition_as_labelled_on_page": "cast on the stated turn"}
    assert f["funnel"]["reached_battlefield"] == 33509
    win = f["win_rates_observed"]
    assert win["win_rate_cast_pct"] == 31 and win["n_cast"] == 30121
    assert win["ci95_pp"] == [8.5, 9.7]
    assert "correlation" in win["interpretation"]
    assert f["final_zone_distribution"]["distribution_pct"]["Battlefield"] == 68.7
    assert f["top_commanders_by_decks"][0] == {"commander": "Test Commander Alpha", "decks": 566}


def test_parse_playgroup_card_low_data():
    f = pg_mod.parse_card_page(fx("playgroup_card_low.html"),
                               expected_name="Obscure Test Card")
    assert f["times_brought"] == 12 and "first_cast_n" not in f
    with pytest.raises(pg_mod.ParseError):
        pg_mod.parse_card_page(fx("playgroup_card_low.html"), expected_name="Wrong Card")


def test_parse_playgroup_card_live_cast_turn_format():
    # Live segment shape since the site's current rendering (verified
    # against 1,227 stored real pages 2026-11-12): float median and no
    # middot after it. The 2.1.0 pattern matched none of them.
    page = ("<html><body><div>Test Ring</div><div>Times Brought 55</div>"
            "<div>Decks Running 21</div>"
            "<div>Median 7.5 P25 6 · P75 9 · max 12</div></body></html>")
    f = pg_mod.parse_card_page(page, expected_name="Test Ring")
    assert f["cast_turn_median"] == 7.5
    assert f["cast_turn_p25"] == 6 and f["cast_turn_p75"] == 9
    assert f["cast_turn_max"] == 12
    # Integer medians in the live shape stay integers.
    page_int = page.replace("Median 7.5", "Median 4")
    assert pg_mod.parse_card_page(
        page_int, expected_name="Test Ring")["cast_turn_median"] == 4


# ---------------------------------------------------------------- sync flows

def test_sync_edhrec_end_to_end_and_cache(collection_store):
    fetcher = FakeFetcher(edhrec_routes())
    results = ext.sync_edhrec(collection_store, fetcher, name=ALARA,
                              commander_oracle_id=ALARA_OID)
    assert len(results) == 6
    assert all(r["status"] == "AVAILABLE" for r in results if r["kind"] == "edhrec_stats")
    decks = [r for r in results if r["kind"] == "edhrec_decks"]
    assert all(r["status"] == "PARTIAL" for r in decks)  # fixture: 2 of 10 decks
    snap = ext.latest_snapshot(collection_store, "edhrec", "edhrec_stats",
                               commander_oracle_id=ALARA_OID, bracket="core")
    assert snap["sha256"] and snap["sample_size"] == 10 and snap["status"] == "AVAILABLE"
    rows = collection_store.conn.execute(
        "SELECT COUNT(*) n FROM edhrec_card_stat WHERE snapshot_id=?",
        (snap["snapshot_id"],)).fetchone()
    assert rows["n"] == 3
    jobs = collection_store.conn.execute(
        "SELECT status FROM sync_job WHERE job_type='edhrec_stats' AND bracket='core'"
    ).fetchone()
    assert jobs["status"] == "AVAILABLE"
    calls = len(fetcher.calls)
    again = ext.sync_edhrec(collection_store, fetcher, name=ALARA,
                            commander_oracle_id=ALARA_OID)
    assert len(fetcher.calls) == calls  # fully cached, no new requests
    assert all(r.get("cached") for r in again)


def test_sync_edhrec_404_and_blocked(collection_store):
    fetcher = FakeFetcher({})  # everything 404
    results = ext.sync_edhrec(collection_store, fetcher, name=ALARA,
                              commander_oracle_id=ALARA_OID)
    assert all(r["status"] == "NOT_FOUND" for r in results)
    fetcher2 = FakeFetcher({prefix: (403, "forbidden") for prefix in
                            ("https://edhrec.com/commanders/alara-test-sovereign",)})
    results2 = ext.sync_edhrec(collection_store, fetcher2, name=ALARA,
                               commander_oracle_id=ALARA_OID, force=True)
    assert all(r["status"] == "BLOCKED" for r in results2)


def test_sync_playgroup_commander_and_unresolved(collection_store):
    routes = {
        ext.PG_AUTOCOMPLETE + "Alara%2C+Test+Sovereign": (200, fx("playgroup_autocomplete.html")),
        "https://playgroup.gg/api/public/v1/commanders/9999.json": (200, fx("playgroup_commander.json")),
    }
    fetcher = FakeFetcher(routes)
    res = ext.sync_playgroup_commander(collection_store, fetcher, name=ALARA,
                                       commander_oracle_id=ALARA_OID)
    assert res["status"] == "AVAILABLE" and res["playgroup_id"] == 9999
    assert res["sample_size"] == 100
    miss = FakeFetcher({ext.PG_AUTOCOMPLETE: (200, "<ul></ul>")})
    res2 = ext.sync_playgroup_commander(collection_store, miss, name="Plains",
                                        commander_oracle_id=OID["plains"], force=True)
    assert res2["status"] == "NOT_FOUND" and res2["resolution"] == "UNRESOLVED"


def _card_page(name: str, telemetry: bool = True) -> Response:
    if telemetry:
        body = (f"<html><body><h1>{name}</h1>"
                "<div><div>Times Brought</div><div>500</div></div>"
                "<div>First-cast turn</div><div>n=120</div></body></html>")
    else:
        body = (f"<html><body><h1>{name}</h1>"
                "<div><div>Times Brought</div><div>3</div></div></body></html>")
    return Response(status=200, body=body.encode(), url="")


def test_sync_card_atlas_limit_resume_and_coverage(collection_store):
    names = {"alara-test-sovereign": ALARA, "plains": "Plains", "sol-ring-test": "Sol Ring (Test)"}
    routes = {"https://playgroup.gg/cards/": lambda url: _card_page(names[url.rsplit("/", 1)[1]])}
    fetcher = FakeFetcher(routes)
    cov = ext.sync_card_atlas(collection_store, fetcher, FC, limit=2)
    assert cov["total_identities"] == 3 and cov["attempted"] == 2
    assert cov["available"] == 2 and cov["remaining_not_fetched"] == 1
    cov2 = ext.sync_card_atlas(collection_store, fetcher, FC)  # resume
    assert cov2["cached_skipped"] == 2 and cov2["attempted"] == 1
    total = ext.card_atlas_coverage(collection_store, FC)
    assert total["attempted"] == 3 and total["jobs_by_status"].get("AVAILABLE") == 3


def test_sync_card_atlas_blocked_stops(collection_store):
    routes = {"https://playgroup.gg/cards/": (403, "rate limited")}
    fetcher = FakeFetcher(routes)
    cov = ext.sync_card_atlas(collection_store, fetcher, FC)
    assert cov["blocked"] == 1 and cov["stopped_on_block"] is True
    assert cov["attempted"] == 1  # stopped immediately, no escalation


def test_parser_version_invalidation_and_manual_invalidate(collection_store):
    fetcher = FakeFetcher(edhrec_routes())
    ext.sync_edhrec(collection_store, fetcher, name=ALARA, commander_oracle_id=ALARA_OID)
    snap = ext.latest_snapshot(collection_store, "edhrec", "edhrec_stats",
                               commander_oracle_id=ALARA_OID, bracket="core")
    assert snap is not None
    # simulate an old-parser snapshot: invisible to current-version lookups
    collection_store.conn.execute(
        "UPDATE external_snapshot SET parser_version='0.0.1' WHERE snapshot_id=?",
        (snap["snapshot_id"],))
    collection_store.conn.commit()
    assert ext.latest_snapshot(collection_store, "edhrec", "edhrec_stats",
                               commander_oracle_id=ALARA_OID, bracket="core") is None
    old = ext.latest_snapshot(collection_store, "edhrec", "edhrec_stats",
                              commander_oracle_id=ALARA_OID, bracket="core",
                              parser_version=None)
    assert old is not None and not ext.snapshot_is_current(old)
    out = ext.invalidate_cache(collection_store, source_name="edhrec")
    assert out["snapshots_deleted"] >= 1
    assert ext.latest_snapshot(collection_store, "edhrec", "edhrec_stats",
                               commander_oracle_id=ALARA_OID, bracket="core",
                               parser_version=None) is None
    job = collection_store.conn.execute(
        "SELECT status FROM sync_job WHERE job_type='edhrec_stats' LIMIT 1").fetchone()
    assert job["status"] == "NOT_FETCHED"


def test_web_external_endpoints(collection_store, monkeypatch):
    from fastapi.testclient import TestClient

    from deckbuild_studio import web as web_mod
    ext.sync_edhrec(collection_store, FakeFetcher(edhrec_routes()), name=ALARA,
                    commander_oracle_id=ALARA_OID)
    pg_routes = {
        ext.PG_AUTOCOMPLETE + "Alara%2C+Test+Sovereign": (200, fx("playgroup_autocomplete.html")),
        "https://playgroup.gg/api/public/v1/commanders/9999.json": (200, fx("playgroup_commander.json")),
    }
    ext.sync_playgroup_commander(collection_store, FakeFetcher(pg_routes), name=ALARA,
                                 commander_oracle_id=ALARA_OID)
    monkeypatch.setattr(web_mod, "database_path", lambda: collection_store.path)
    client = TestClient(web_mod.create_app())
    data = client.get("/api/external/commander",
                      params={"commander_oracle_id": ALARA_OID, "collection_id": FC}).json()
    core = data["edhrec"]["core"]["stats"]
    assert core["status"] == "AVAILABLE" and core["bracket"] == "core"
    assert data["edhrec"]["upgraded"]["stats"]["sample_size"] == 20  # own cohort, never mixed
    assert data["edhrec"]["core"]["decks"]["coverage_status"] == "PARTIAL"
    plains = next(c for c in core["cards"] if c["name"] == "Plains")
    assert plains["owned_available"] == 60 and plains["owned_locations"] == ["Foundation"]
    assert data["playgroup"]["data"]["playgroup_id"] == 9999
    st = client.get("/api/external/status", params={"collection_id": FC}).json()
    assert st["card_atlas"]["total_identities"] == 3
    card = client.get("/api/external/card", params={"oracle_id": OID["plains"]}).json()
    assert card["status"] == "NOT_FETCHED"


def test_status_summary_counts_snapshots(collection_store):
    fetcher = FakeFetcher(edhrec_routes())
    ext.sync_edhrec(collection_store, fetcher, name=ALARA, commander_oracle_id=ALARA_OID)
    summary = collection_store.status()["external_data"]
    assert summary["edhrec"]["by_status"].get("AVAILABLE") == 3
    assert summary["edhrec"]["by_status"].get("PARTIAL") == 3
    payload = json.dumps(summary)  # must be JSON-serialisable for cache-status CLI
    assert "payload_json" not in payload  # raw parsed payloads stay out of the summary


# ------------------------------------------------- upstream sync 2026-11-11
# Adopted from commander-playtest-lab #1196 (fail-closed stat validation)
# and #1202 (quality warnings + JSON-LD dataset provenance).

def test_parse_edhrec_stats_drops_invalid_rows():
    parsed = edhrec_mod.parse_stats_page(fx("edhrec_stats_invalid.html"),
                                         expected_name=ALARA, expected_slug=ALARA_SLUG,
                                         bracket="core")
    names = [c["name"] for c in parsed["cards"]]
    assert names == ["Test Sol Ring"]  # num>potential, string synergy, negative count dropped
    assert parsed["dropped_invalid"] == 3
    assert parsed["captured_count"] == 1


def test_parse_edhrec_stats_valid_fixture_drops_nothing():
    parsed = edhrec_mod.parse_stats_page(fx("edhrec_stats.html"),
                                         expected_name=ALARA, expected_slug=ALARA_SLUG,
                                         bracket="core")
    assert parsed["dropped_invalid"] == 0


_PG_DISCREPANCY_HTML = """
<html><head><script type="application/ld+json">
{"@type": "Dataset", "identifier": "playgroup-cards-test",
 "dateModified": "2026-11-01", "temporalCoverage": "2025/2026",
 "license": "https://creativecommons.org/licenses/by/4.0/"}
</script></head><body>
<h1>Discrepancy Card</h1>
<div>Times Brought</div><div>500</div>
<div>450 brought · 12 players</div>
<div>On curve 50% (10 / 100 cast on T2)</div>
</body></html>
"""

_PG_CLEAN_HTML = """
<html><head><script type="application/ld+json">
{"@type": "Dataset", "identifier": "playgroup-cards-clean"}
</script></head><body>
<h1>Clean Card</h1>
<div>Times Brought</div><div>450</div>
<div>450 brought · 12 players</div>
<div>On curve 10% (10 / 100 cast on T2)</div>
</body></html>
"""


def test_parse_playgroup_card_quality_warnings_and_dataset():
    f = pg_mod.parse_card_page(_PG_DISCREPANCY_HTML, expected_name="Discrepancy Card")
    warnings = f["quality_warnings"]
    assert any("On-curve calculation discrepancy" in w for w in warnings)
    assert any("Brought count discrepancy" in w for w in warnings)
    # exact source numbers are preserved, never silently corrected
    assert f["times_brought"] == 500 and f["funnel"]["brought_header"] == 450
    assert f["on_curve"]["pct"] == 50.0 and f["on_curve"]["numerator"] == 10
    assert f["dataset"]["identifier"] == "playgroup-cards-test"
    assert f["dataset"]["date_modified"] == "2026-11-01"
    assert f["license"] == "https://creativecommons.org/licenses/by/4.0/"
    assert f["attribution"] == "Playgroup.gg"


def test_parse_playgroup_card_clean_no_warnings():
    f = pg_mod.parse_card_page(_PG_CLEAN_HTML, expected_name="Clean Card")
    assert "quality_warnings" not in f
    assert f["dataset"]["identifier"] == "playgroup-cards-clean"
    assert f["license"] == "CC BY 4.0"  # default when the page states none
