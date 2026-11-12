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
    documentation or base URL; the frontend's own data access is an
    undocumented internal GraphQL (Relay persisted queries embedded
    in the page). Like the Scryfall Tagger GraphQL before it, that is
    not a provenance-grade import path and is deliberately NOT used.

Semantics: ``play_rate_last_year`` is stored verbatim as published
(a fraction). The site does not publish the exact denominator of the
rate on the staples page, so none is recorded — the figure is a
tournament-popularity observation over cEDH entries of the last
year, NOT a win rate and not comparable to EDHREC inclusion or
Playgroup telemetry (different corpora, never mixed).
"""
from __future__ import annotations

import json
import re

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
              "this page and stay absent; the site's undocumented "
              "internal GraphQL is not used")
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
