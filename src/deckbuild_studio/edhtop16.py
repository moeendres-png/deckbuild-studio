"""EDHTop16 layer — cEDH tournament play rates from the public site.

Access audit (2026-11-12, evidence in docs/EXTERNAL_DATA.md):

  * ``https://edhtop16.com/robots.txt`` is ``User-agent: *`` with an
    EMPTY ``Disallow:`` — automated reads of public pages are not
    robots-excluded.
  * The public staples page (``/staples``, server-rendered) embeds its
    full data payload in the page — the same public-payload pattern
    this project uses for EDHREC (RSC) and Commander Spellbook (SSR).
    Per card it publishes exactly: name, type line, mana cost and
    ``playRateLastYear`` ("The most popular cards in competitive EDH,
    based on tournament data from the last year"). 1,332 distinct
    cards were embedded at audit time.
  * Per-card top-cut conversion and per-card entry counts are NOT
    published on that page (field-level check of every embedded
    record) — they stay absent (NULL), never derived or invented.
  * The site advertises "a robust API" on /about but publishes no API
    documentation or base URL; the frontend's own data access is a
    GraphQL with Relay persisted queries. The morning audit of
    2026-11-12 declined that channel as undocumented. A same-day
    re-verification of the Terms of Service corrected that assessment
    for the per-commander layer below: ToS § "API Usage" states "We
    provide an API for developers and data enthusiasts" (access
    as-is, may be rate limited, no implied endorsement), and the
    Acceptable Use rules prohibit only excessive automated requests.
    Persisted queries are the API's sole access mechanism (plaintext
    GraphQL is disabled server-side), so the per-commander layer uses
    exactly that channel — public commander names only, rate-limited,
    cached as snapshots like every other layer. The GLOBAL layer
    above continues to use the public staples page payload.

Semantics: ``play_rate_last_year`` is stored verbatim as published
(a fraction). The site does not publish the exact denominator of the
rate on the staples page, so none is recorded — the figure is a
tournament-popularity observation over cEDH entries of the last
year, NOT a win rate and not comparable to EDHREC inclusion or
Playgroup telemetry (different corpora, never mixed).

Second layer — per card x commander (``sync_edhtop16_commanders``,
kind ``edhtop16_commander_staples``): for every eligible commander
of the collection, the API's staples query publishes the commander's
top staples with ``playRateLastYear`` each, and the stats query
publishes the commander-level aggregates ``count`` (tournament
entries in the ONE_YEAR window — the denominator the play rates are
computed over), ``conversionRate`` and ``metaShare``. Card rows land
in ``edhtop16_commander_card_stat`` (play rate + the commander-level
``entries_n`` per row, the data form of the 2026-11-12 probe CSV);
the aggregates land in ``edhtop16_commander_stat``. Conversion is a
COMMANDER-level aggregate only: per-card conversion is published
nowhere (the staples payload carries no such field — field-verified
live) and stays absent, never derived from the aggregates.
Attribution guard (live-verified 2026-11-12): for a commander with
zero entries in the window the staples query answers with the API's
GLOBAL staples list under the requested commander's name — those
rows are discarded, never attributed; card rows are likewise
withheld whenever the stats query provides no usable entry count,
because the fallback cannot be ruled out without it.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote

from .external import latest_snapshot, save_snapshot
from .httpfetch import Fetcher, FetchError, RobotsDisallowed
from .store import Store

PARSER_ID = "edhtop16-staples/1.0.0"
SOURCE_NAME = "edhtop16"
KIND = "edhtop16_staples"
STAPLES_URL = "https://edhtop16.com/staples"
_PAGE_MARKER = "most popular cards in competitive edh"
_RECORD_START = re.compile(r'\{"id":"')


def _object_span(text: str, start: int) -> str | None:
    """The complete JSON object starting at ``start`` (string- and
    escape-aware brace matching; record values contain braces of
    their own, e.g. mana costs like ``{G}``)."""
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


class EdhTop16Error(Exception):
    """Terminal sync failure to surface (transient network error after
    the fetcher's retries — no snapshot written, stays NOT_FETCHED)."""


class ParseError(Exception):
    """The staples page does not carry the expected payload."""


def _unescape(html: str) -> str:
    """Undo the JS-string escaping of the embedded RSC/Relay payload."""
    return (html.replace('\\"', '"')
                .replace("\\u002F", "/").replace("\\u0026", "&")
                .replace("\\u003D", "=").replace("\\n", " "))


def parse_staples_page(html: str) -> dict:
    """Extract the card records embedded in the staples page.

    Raises ParseError when the page marker is absent (wrong page /
    redesign) or no record parses. Records with an out-of-range rate
    are skipped and counted. Duplicate names keep the first record."""
    if _PAGE_MARKER not in html.lower():
        raise ParseError("staples page marker text not found — "
                         "unexpected page (redesign or wrong route)")
    text = _unescape(html)
    cards: dict[str, dict] = {}
    skipped = 0
    for match in _RECORD_START.finditer(text):
        span = _object_span(text, match.start())
        if span is None or '"playRateLastYear"' not in span:
            continue
        try:
            obj = json.loads(span)
        except json.JSONDecodeError:
            skipped += 1
            continue
        name = obj.get("name")
        rate = obj.get("playRateLastYear")
        if not name or isinstance(rate, bool) or not isinstance(rate, (int, float)):
            skipped += 1
            continue
        if not 0.0 <= float(rate) <= 1.0:
            skipped += 1
            continue
        if name in cards:
            continue
        cards[name] = {"name": name, "type": obj.get("type"),
                       "mana_cost": obj.get("manaCost"),
                       "play_rate_last_year": float(rate)}
    if not cards:
        raise ParseError("no parseable card records in the staples payload")
    return {"cards": list(cards.values()), "skipped_records": skipped,
            "parser": PARSER_ID}


def _name_to_oracle(store: Store) -> dict[str, str]:
    """Exact paper name (full or front face) -> oracle_id, local only."""
    out: dict[str, str] = {}
    for r in store.conn.execute(
            "SELECT oracle_id, name, front_name FROM scryfall_card"):
        out.setdefault(r["name"], r["oracle_id"])
        if r["front_name"]:
            out.setdefault(r["front_name"], r["oracle_id"])
    return out


def sync_edhtop16(store: Store, fetcher: Fetcher, *,
                  collection_id: str = "foundation-schwarze-box",
                  force: bool = False) -> dict:
    """Fetch the public staples page ONCE and store its play rates.

    Honest statuses: AVAILABLE (page parsed), PARTIAL (parse error —
    raw kept for diagnosis), BLOCKED (robots / HTTP 403 / 429 / other
    HTTP error), NOT_FOUND (404). A transient network failure raises
    EdhTop16Error and writes nothing. Without ``force``, a current
    AVAILABLE snapshot is reused (single-page sync, re-runs are cheap
    but stay explicit)."""
    existing = latest_snapshot(store, SOURCE_NAME, KIND)
    if existing is not None and not force and existing["status"] == "AVAILABLE":
        return {"snapshot_id": existing["snapshot_id"], "status": "AVAILABLE",
                "cached": True, "detail": "current staples snapshot exists; "
                                           "pass --force to refetch"}

    def record(status: str, detail: str, raw: bytes | None = None) -> dict:
        snap = save_snapshot(store, source_name=SOURCE_NAME, kind=KIND,
                             url=STAPLES_URL, status=status, raw=raw,
                             detail=detail, payload={"parser": PARSER_ID})
        return {"snapshot_id": snap, "status": status,
                "source_url": STAPLES_URL, "detail": detail}

    try:
        resp = fetcher.get(STAPLES_URL)
    except RobotsDisallowed as exc:
        return record("BLOCKED", str(exc))
    except FetchError as exc:
        raise EdhTop16Error(f"staples fetch failed: {exc}") from exc
    if resp.status in (403, 429):
        return record("BLOCKED", f"HTTP {resp.status} — no escalation",
                      resp.body)
    if resp.status == 404:
        return record("NOT_FOUND", "HTTP 404 — staples page not found",
                      resp.body)
    if resp.status != 200:
        return record("BLOCKED", f"HTTP {resp.status}", resp.body)
    try:
        parsed = parse_staples_page(resp.text)
    except ParseError as exc:
        return record("PARTIAL", f"parse error: {exc}", resp.body)
    by_name = _name_to_oracle(store)
    resolved = 0
    detail = ("play rates as published by EDHTop16 (window: last year); "
              "per-card conversion and entry counts are NOT published on "
              "this page and stay absent; per-commander values live in "
              "the separate API layer (kind edhtop16_commander_staples)")
    if parsed["skipped_records"]:
        detail += f"; {parsed['skipped_records']} embedded records skipped " \
                  "(invalid shape/rate)"
    snap = save_snapshot(
        store, source_name=SOURCE_NAME, kind=KIND, url=STAPLES_URL,
        status="AVAILABLE", raw=resp.body, etag=resp.etag,
        last_modified=resp.last_modified,
        captured_count=len(parsed["cards"]),
        coverage_status="TOTAL_KNOWN", detail=detail,
        payload={"parser": PARSER_ID, "cards": len(parsed["cards"]),
                 "skipped_records": parsed["skipped_records"],
                 "window": "last_year"})
    store.conn.execute("DELETE FROM edhtop16_card_stat WHERE snapshot_id=?",
                       (snap,))
    for card in parsed["cards"]:
        oracle_id = by_name.get(card["name"])
        if oracle_id is not None:
            resolved += 1
        store.conn.execute(
            "INSERT OR REPLACE INTO edhtop16_card_stat(snapshot_id,card_name,"
            "card_oracle_id,card_type,mana_cost,play_rate_last_year) "
            "VALUES(?,?,?,?,?,?)",
            (snap, card["name"], oracle_id, card["type"], card["mana_cost"],
             card["play_rate_last_year"]))
    store.conn.commit()
    return {"snapshot_id": snap, "status": "AVAILABLE",
            "source_url": STAPLES_URL, "detail": detail,
            "cards_published": len(parsed["cards"]),
            "resolved_to_local_store": resolved,
            "unresolved_names": len(parsed["cards"]) - resolved,
            "collection": edhtop16_coverage(store, collection_id)}


def edhtop16_coverage(store: Store, collection_id: str) -> dict:
    total = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"collection_id": collection_id, "total_identities": total,
                "status": "NOT_FETCHED", "with_play_rate": 0,
                "cards_published": 0}
    row = store.conn.execute(
        "SELECT COUNT(DISTINCT s.card_oracle_id) covered FROM "
        "edhtop16_card_stat s JOIN physical_lot l "
        "ON l.oracle_id = s.card_oracle_id "
        "WHERE s.snapshot_id=? AND l.collection_id=?",
        (snap["snapshot_id"], collection_id)).fetchone()
    published = store.conn.execute(
        "SELECT COUNT(*) n FROM edhtop16_card_stat WHERE snapshot_id=?",
        (snap["snapshot_id"],)).fetchone()["n"]
    return {"collection_id": collection_id, "total_identities": total,
            "status": snap["status"], "with_play_rate": row["covered"],
            "cards_published": published,
            "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"]}


def card_edhtop16(store: Store, oracle_id: str) -> dict:
    """One card's EDHTop16 play rate from the latest snapshot.

    A synced card that is not on the staples list is NOT an error: it
    answers the snapshot status with ``listed: False`` and a NULL rate
    (not a published staple — different from 'rate 0')."""
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"status": "NOT_FETCHED", "listed": False,
                "play_rate_last_year": None}
    row = store.conn.execute(
        "SELECT card_name, play_rate_last_year FROM edhtop16_card_stat "
        "WHERE snapshot_id=? AND card_oracle_id=?",
        (snap["snapshot_id"], oracle_id)).fetchone()
    if row is None:
        return {"status": snap["status"], "listed": False,
                "play_rate_last_year": None,
                "snapshot_id": snap["snapshot_id"],
                "fetched_at": snap["fetched_at"], "window": "last_year"}
    return {"status": snap["status"], "listed": True,
            "card_name": row["card_name"],
            "play_rate_last_year": row["play_rate_last_year"],
            "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"], "window": "last_year",
            "label": "cEDH-Turniere (EDHTop16), letztes Jahr"}


# ---------------------------------------------------------------------------
# Second layer — per card x commander via the EDHTop16 API.
#
# Channel: POST https://edhtop16.com/api/graphql with Relay persisted
# queries (the API's sole access mechanism; ToS § "API Usage" provides
# the API for developers — see the module docstring). Only public
# commander names are sent; the Fetcher applies robots + throttle +
# 5xx-only backoff. The persisted-query ids below are the frontend's
# own query identifiers, verified live on 2026-11-12 (structure probe
# + the CPL probe script, commander-playtest-lab PR #1226).
# ---------------------------------------------------------------------------

CMD_PARSER_ID = "edhtop16-commander-staples/1.0.0"
KIND_COMMANDER = "edhtop16_commander_staples"
GRAPHQL_URL = "https://edhtop16.com/api/graphql"
PASTORIA_ID_STAPLES = "3979f7397ed9d69dbf496964ee5d235b"  # staples_CommanderStaplesQuery
PASTORIA_ID_STATS = "365ea6c7d469ca7dc4420af2a9ac0e94"    # page_CommanderStatsQuery
WINDOW = "ONE_YEAR"


class CommanderNotFound(Exception):
    """The API answered 200 but has no commander under that exact name
    (``data.commander`` is null) — a source fact, recorded NOT_FOUND."""


def commander_page_url(name: str) -> str:
    """The public commander page (staples tab) — the human-verifiable
    provenance URL of a commander snapshot."""
    return f"https://edhtop16.com/commander/{quote(name)}?tab=staples"


def _graphql(fetcher: Fetcher, query_id: str, variables: dict) -> tuple[int, str]:
    """One persisted-query POST; returns (HTTP status, body text)."""
    resp = fetcher.post_json(GRAPHQL_URL, {"variables": variables,
                                           "extensions": {"pastoria-id": query_id}})
    return resp.status, resp.text


def parse_commander_staples(body: str) -> dict:
    """Parse one staples persisted-query response.

    Raises CommanderNotFound when ``data.commander`` is null and
    ParseError on any other shape problem. Records with a missing
    name or an out-of-range rate are skipped and counted; duplicate
    names keep the first record."""
    try:
        res = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ParseError(f"staples response is not JSON: {exc}") from exc
    data = res.get("data") if isinstance(res, dict) else None
    if not isinstance(data, dict):
        raise ParseError("staples response has no data object")
    commander = data.get("commander")
    if commander is None:
        raise CommanderNotFound("API has no commander under this exact name")
    if not isinstance(commander, dict):
        raise ParseError("staples response commander is not an object")
    staples = commander.get("staples")
    if not isinstance(staples, list):
        raise ParseError("staples response has no staples list")
    cards: list[dict] = []
    seen: set[str] = set()
    skipped = 0
    for item in staples:
        if not isinstance(item, dict):
            skipped += 1
            continue
        name = item.get("name")
        rate = item.get("playRateLastYear")
        if (not name or isinstance(rate, bool)
                or not isinstance(rate, (int, float))
                or not 0.0 <= float(rate) <= 1.0):
            skipped += 1
            continue
        if name in seen:
            continue
        seen.add(name)
        cards.append({"name": name, "type": item.get("type"),
                      "mana_cost": item.get("manaCost"),
                      "play_rate": float(rate)})
    return {"commander_name": commander.get("name"), "cards": cards,
            "skipped_records": skipped, "parser": CMD_PARSER_ID}


def parse_commander_stats(body: str) -> dict:
    """Commander-level aggregates from the stats persisted query.

    Field-optional by design: a field the response does not carry
    stays None — never derived. ``entries_n`` is the response's
    ``count`` (tournament entries in the window, the denominator of
    the play rates); ``conversion_rate`` and ``meta_share`` are the
    commander-level aggregates of the same names. Invalid JSON raises
    ParseError; a missing commander/stats object yields all-None."""
    try:
        res = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ParseError(f"stats response is not JSON: {exc}") from exc
    data = res.get("data") if isinstance(res, dict) else None
    commander = data.get("commander") if isinstance(data, dict) else None
    stats = commander.get("stats") if isinstance(commander, dict) else None
    empty = {"entries_n": None, "conversion_rate": None, "meta_share": None}
    if not isinstance(stats, dict):
        return empty

    def num(value: object) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    count = stats.get("count")
    return {
        "entries_n": count if isinstance(count, int)
        and not isinstance(count, bool) else None,
        "conversion_rate": num(stats.get("conversionRate")),
        "meta_share": num(stats.get("metaShare")),
    }


def _sync_one_commander(store: Store, fetcher: Fetcher, *,
                        oracle_id: str, name: str,
                        by_name: dict[str, str]) -> dict:
    """Fetch + store one commander's staples and aggregates.

    Status semantics (project conventions): BLOCKED on robots /
    403 / 429 / other non-200 from the staples query (the caller
    stops the run — no escalation); NOT_FOUND when the API does not
    know the exact commander name; PARTIAL when the staples parsed
    but the stats query failed or carried no usable count (card
    rows are withheld then — see the attribution guard below), or
    the staples payload itself was unparseable; a transient network
    failure returns the pseudo-status NETWORK and writes NOTHING
    (the commander stays NOT_FETCHED and a later run retries it)."""
    page_url = commander_page_url(name)
    payload_base = {"parser": CMD_PARSER_ID, "window": WINDOW,
                    "api_endpoint": GRAPHQL_URL,
                    "persisted_queries": {"staples": PASTORIA_ID_STAPLES,
                                          "stats": PASTORIA_ID_STATS}}

    def record(status: str, detail: str, bundle: dict) -> dict:
        raw = json.dumps(bundle, ensure_ascii=False).encode()
        snap = save_snapshot(store, source_name=SOURCE_NAME,
                             kind=KIND_COMMANDER, url=page_url,
                             status=status, commander_oracle_id=oracle_id,
                             raw=raw, detail=detail, payload=payload_base)
        return {"snapshot_id": snap, "status": status, "commander": name,
                "source_url": page_url, "detail": detail}

    # 1) Staples — the card rows.
    try:
        status, body = _graphql(fetcher, PASTORIA_ID_STAPLES,
                                {"commander": name,
                                 "staplesSortBy": "MOST_PLAYED"})
    except RobotsDisallowed as exc:
        return record("BLOCKED", str(exc), {})
    except FetchError as exc:
        # Keep the underlying error (IncompleteRead / RemoteDisconnected
        # / HTTP 5xx after retries) in the report — the 2026-11-12 runs
        # showed a bare "transient network failure" is undiagnosable.
        return {"status": "NETWORK", "commander": name,
                "detail": f"transient network failure ({exc}) — "
                          "no snapshot written"}
    bundle: dict = {"staples_response": body}
    if status in (403, 429):
        return record("BLOCKED", f"HTTP {status} from the API — no escalation",
                      bundle)
    if status == 404:
        return record("NOT_FOUND", "HTTP 404 from the API", bundle)
    if status != 200:
        return record("BLOCKED", f"HTTP {status} from the API", bundle)
    try:
        parsed = parse_commander_staples(body)
    except CommanderNotFound:
        return record("NOT_FOUND",
                      "API has no commander under this exact name", bundle)
    except ParseError as exc:
        return record("PARTIAL", f"staples parse error: {exc}", bundle)
    if parsed["commander_name"] and parsed["commander_name"] != name:
        # The API answered for a DIFFERENT commander than requested —
        # the rows must not be attributed to this commander.
        return record(
            "PARTIAL",
            f"API answered for {parsed['commander_name']!r}, not the "
            f"requested {name!r} — rows not attributed", bundle)

    # 2) Stats — commander-level aggregates. A failure here degrades
    # the snapshot to PARTIAL and the card rows are withheld (see
    # the attribution guard below): without a usable entry count
    # the zero-entry global fallback cannot be ruled out.
    stats = {"entries_n": None, "conversion_rate": None, "meta_share": None}
    stats_note = ""
    try:
        s_status, s_body = _graphql(fetcher, PASTORIA_ID_STATS,
                                    {"commander": name, "minEventSize": 0,
                                     "timePeriod": WINDOW})
        bundle["stats_response"] = s_body
        if s_status == 200:
            stats = parse_commander_stats(s_body)
            if stats["entries_n"] is None:
                stats_note = "stats response carried no usable entry count"
        else:
            stats_note = f"stats query answered HTTP {s_status}"
    except (RobotsDisallowed, FetchError) as exc:
        stats_note = f"stats query failed: {exc}"
    except ParseError as exc:
        stats_note = f"stats parse error: {exc}"

    entries_n = stats["entries_n"]

    # Attribution guard (live-verified 2026-11-12): for a commander
    # with ZERO entries in the window the API answers the staples
    # query with its GLOBAL staples list — off-color-identity cards
    # at global rates under the requested commander's name (e.g.
    # "Ruby, Daring Tracker", count 0, answered Vampiric Tutor
    # 0.909). Those rows are not this commander's data and are NEVER
    # stored. The same fallback cannot be ruled out when the stats
    # query failed to provide a usable entry count, so card rows are
    # withheld then, too — the raw bundle stays in the snapshot and
    # a later run with a working stats answer fills the rows in.
    store_rows = True
    fallback_note = ""
    if stats_note:
        store_rows = False
        fallback_note = (
            "card rows withheld: without a usable entry count the "
            "API's zero-entry global-fallback staples cannot be ruled "
            "out — rows are never attributed unverified")
    elif entries_n == 0:
        store_rows = False
        fallback_note = (
            "commander has 0 entries in the ONE_YEAR window; the API "
            "answers the staples query for zero-entry commanders with "
            "its global staples list (live-verified 2026-11-12) — "
            "that fallback payload was discarded, no card rows "
            "attributed")
    stored_cards = parsed["cards"] if store_rows else []
    detail = ("per-commander staples via the EDHTop16 API (ToS § API Usage "
              "provides an API for developers; persisted queries are its "
              "access mechanism); play_rate is playRateLastYear over the "
              "ONE_YEAR window and entries_n the commander-level entry "
              "total the rate is computed over; conversion is stored ONLY "
              "as a commander-level aggregate (edhtop16_commander_stat) — "
              "per-card conversion is not published and stays absent")
    if parsed["skipped_records"]:
        detail += (f"; {parsed['skipped_records']} staple records skipped "
                   "(invalid shape/rate)")
    if stats_note:
        detail += f"; {stats_note}"
    if fallback_note:
        detail += f"; {fallback_note}"
    final_status = "AVAILABLE" if not stats_note else "PARTIAL"
    raw = json.dumps(bundle, ensure_ascii=False).encode()
    snap = save_snapshot(
        store, source_name=SOURCE_NAME, kind=KIND_COMMANDER, url=page_url,
        status=final_status, commander_oracle_id=oracle_id, raw=raw,
        sample_size=entries_n, captured_count=len(stored_cards),
        coverage_status="TOTAL_UNKNOWN", detail=detail,
        payload={**payload_base, "commander": name,
                 "cards": len(stored_cards),
                 "staples_returned": len(parsed["cards"]),
                 "entries_n": entries_n,
                 "conversion_rate": stats["conversion_rate"],
                 "meta_share": stats["meta_share"]})
    store.conn.execute(
        "DELETE FROM edhtop16_commander_card_stat WHERE snapshot_id=?", (snap,))
    store.conn.execute(
        "DELETE FROM edhtop16_commander_stat WHERE snapshot_id=?", (snap,))
    store.conn.execute(
        "INSERT OR REPLACE INTO edhtop16_commander_stat(snapshot_id,"
        "commander_oracle_id,commander_name,entries_n,conversion_rate,"
        "meta_share,window) VALUES(?,?,?,?,?,?,?)",
        (snap, oracle_id, name, entries_n, stats["conversion_rate"],
         stats["meta_share"], WINDOW))
    resolved = 0
    for card in stored_cards:
        card_oracle_id = by_name.get(card["name"])
        if card_oracle_id is not None:
            resolved += 1
        store.conn.execute(
            "INSERT OR REPLACE INTO edhtop16_commander_card_stat(snapshot_id,"
            "commander_oracle_id,commander_name,card_name,card_oracle_id,"
            "play_rate,entries_n,window) VALUES(?,?,?,?,?,?,?,?)",
            (snap, oracle_id, name, card["name"], card_oracle_id,
             card["play_rate"], entries_n, WINDOW))
    store.conn.commit()
    return {"snapshot_id": snap, "status": final_status, "commander": name,
            "source_url": page_url, "detail": detail,
            "pairs": len(stored_cards),
            "resolved_to_local_store": resolved,
            "entries_n": entries_n,
            "conversion_rate": stats["conversion_rate"]}


def sync_edhtop16_commanders(store: Store, fetcher: Fetcher, *,
                             collection_id: str = "foundation-schwarze-box",
                             force: bool = False,
                             limit: int | None = None) -> dict:
    """Per-card x commander play rates for every eligible commander
    of the collection, via the EDHTop16 API.

    Resumable like the Card Atlas: a commander with a current
    AVAILABLE snapshot is skipped unless ``force``. The run STOPS at
    the first BLOCKED commander (robots / 403 / 429 — no escalation);
    NOT_FOUND and PARTIAL commanders do not stop it, and a transient
    network failure writes nothing for that commander."""
    from .commander import commander_candidates

    eligible = commander_candidates(store, collection_id)["eligible"]
    commanders = [(c["oracle_id"], c["name"]) for c in eligible]
    summary: dict = {"collection_id": collection_id,
                     "eligible_commanders": len(commanders),
                     "attempted": 0, "cached_skipped": 0, "available": 0,
                     "partial": 0, "not_found": 0, "blocked": 0,
                     "network_errors": 0, "stopped_on_block": False,
                     "pairs_stored": 0, "results": []}
    by_name = _name_to_oracle(store)
    for oracle_id, name in commanders:
        existing = latest_snapshot(store, SOURCE_NAME, KIND_COMMANDER,
                                   commander_oracle_id=oracle_id)
        if (existing is not None and not force
                and existing["status"] == "AVAILABLE"):
            summary["cached_skipped"] += 1
            continue
        if limit is not None and summary["attempted"] >= limit:
            break
        summary["attempted"] += 1
        outcome = _sync_one_commander(store, fetcher, oracle_id=oracle_id,
                                      name=name, by_name=by_name)
        summary["results"].append(outcome)
        status = outcome["status"]
        if status in ("AVAILABLE", "PARTIAL"):
            summary[status.lower()] += 1
            summary["pairs_stored"] += outcome.get("pairs", 0)
        elif status == "NOT_FOUND":
            summary["not_found"] += 1
        elif status == "NETWORK":
            summary["network_errors"] += 1
        elif status == "BLOCKED":
            summary["blocked"] += 1
            summary["stopped_on_block"] = True
            break
    summary["coverage"] = edhtop16_commander_coverage(store, collection_id)
    return summary


def _latest_commander_snapshots(store: Store) -> dict[str, object]:
    """commander_oracle_id -> latest commander-staples snapshot row."""
    latest: dict[str, object] = {}
    for row in store.conn.execute(
            "SELECT * FROM external_snapshot WHERE source_name=? AND kind=? "
            "ORDER BY fetched_at DESC", (SOURCE_NAME, KIND_COMMANDER)):
        key = row["commander_oracle_id"]
        if key is not None and key not in latest:
            latest[key] = row
    return latest


def edhtop16_commander_coverage(store: Store,
                                collection_id: str) -> dict:
    """Coverage of the per-commander layer over one collection:
    commanders with a snapshot, card x commander pairs, and how many
    collection identities carry at least one per-commander value."""
    from .commander import commander_candidates

    eligible = commander_candidates(store, collection_id)["eligible"]
    total_identities = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    latest = _latest_commander_snapshots(store)
    snap_ids: list[str] = []
    by_status: dict[str, int] = {}
    for commander in eligible:
        snap = latest.get(commander["oracle_id"])
        if snap is None:
            by_status["NOT_FETCHED"] = by_status.get("NOT_FETCHED", 0) + 1
            continue
        by_status[snap["status"]] = by_status.get(snap["status"], 0) + 1
        if snap["status"] in ("AVAILABLE", "PARTIAL"):
            snap_ids.append(snap["snapshot_id"])
    pairs = 0
    cards_covered = 0
    per_commander: list[int] = []
    if snap_ids:
        marks = ",".join("?" * len(snap_ids))
        pairs = store.conn.execute(
            f"SELECT COUNT(*) n FROM edhtop16_commander_card_stat "
            f"WHERE snapshot_id IN ({marks})", snap_ids).fetchone()["n"]
        cards_covered = store.conn.execute(
            f"SELECT COUNT(DISTINCT s.card_oracle_id) n FROM "
            f"edhtop16_commander_card_stat s JOIN physical_lot l "
            f"ON l.oracle_id = s.card_oracle_id "
            f"WHERE s.snapshot_id IN ({marks}) AND l.collection_id=?",
            (*snap_ids, collection_id)).fetchone()["n"]
        per_commander = [r["n"] for r in store.conn.execute(
            f"SELECT COUNT(*) n FROM edhtop16_commander_card_stat "
            f"WHERE snapshot_id IN ({marks}) GROUP BY commander_name",
            snap_ids)]
    return {"collection_id": collection_id,
            "eligible_commanders": len(eligible),
            "commanders_by_status": by_status,
            "total_identities": total_identities,
            "collection_cards_with_commander_values": cards_covered,
            "pairs_total": pairs,
            "pairs_per_commander_min": min(per_commander) if per_commander else 0,
            "pairs_per_commander_max": max(per_commander) if per_commander else 0,
            "window": WINDOW}


def card_edhtop16_commanders(store: Store, oracle_id: str) -> dict:
    """One card's per-commander EDHTop16 play rates, from each
    commander's latest commander-staples snapshot.

    A card absent from a commander's staples list simply has no row
    for that commander (not a rate of 0). Before the first sync the
    answer is NOT_FETCHED with an empty list."""
    latest = _latest_commander_snapshots(store)
    if not latest:
        return {"status": "NOT_FETCHED", "commanders": []}
    rows: list[dict] = []
    for snap in latest.values():
        row = store.conn.execute(
            "SELECT commander_name, commander_oracle_id, play_rate, "
            "entries_n, window FROM edhtop16_commander_card_stat "
            "WHERE snapshot_id=? AND card_oracle_id=?",
            (snap["snapshot_id"], oracle_id)).fetchone()
        if row is None:
            continue
        rows.append({"commander": row["commander_name"],
                     "commander_oracle_id": row["commander_oracle_id"],
                     "play_rate": row["play_rate"],
                     "entries_n": row["entries_n"],
                     "window": row["window"],
                     "status": snap["status"],
                     "fetched_at": snap["fetched_at"],
                     "snapshot_id": snap["snapshot_id"]})
    rows.sort(key=lambda r: -(r["play_rate"] or 0.0))
    return {"status": "AVAILABLE", "commanders": rows}
