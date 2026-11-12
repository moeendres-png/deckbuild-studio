"""Scryfall Tagger layer — functional tags via the OFFICIAL Search API.

The Scryfall Tagger itself has no official export/API (only an
undocumented GraphQL endpoint), which this project rejected as not
provenance-worthy. The supported route is the documented Search API
(https://scryfall.com/docs/api/cards/search) with the ``function:``
operator, whose result sets ARE the Tagger functional tags:

    GET https://api.scryfall.com/cards/search?q=function:<tag>&unique=cards

Verified live on 2026-11-12 (probe, see docs/CATEGORIES.md):
``function:ramp`` -> 2,353 cards, ``function:removal`` -> 6,490,
``function:board-wipe`` -> 952; an unknown tag answers 404 (same as a
known-but-empty tag — the two are indistinguishable, so per-tag
status NOT_FOUND honestly covers both). robots.txt of
api.scryfall.com disallows only /admin* and error pages — /cards/search
is allowed; the client below still checks robots.txt on every run.

Politeness / provenance rules (project-wide, cf. httpfetch):
honest User-Agent + Accept header (the API answers 400 without an
Accept header), >= 100 ms between requests (Scryfall's guidance is
50–100 ms), exponential backoff on 429/5xx honouring Retry-After.
Each tag sync stores a snapshot (raw pages gzipped, SHA-256, parser
version) in ``external_snapshot`` like every other external source,
and per-tag membership claims in ``card_tagger_claim``. Only oracle
ids present in the local Scryfall store become claims — the API's
global result sets also cover cards this store predates; those are
counted in the snapshot detail, never silently dropped or invented.
No collection data is sent anywhere: the queries contain nothing but
public tag names.
"""
from __future__ import annotations

import gzip
import hashlib
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import categories, roles as roles_mod
from .httpfetch import USER_AGENT, _robots_match, _robots_rules
from .store import Store, utcnow

TAGGER_VERSION = "scryfall-tagger-search/1.0.0"
SOURCE_NAME = "scryfall_tagger"
KIND = "tagger_function"
API_BASE = "https://api.scryfall.com"
SEARCH_URL = API_BASE + "/cards/search"

# tag -> our category. One primary tag per category (roles.ROLES maps
# category -> tag label; this is its inverse for the synced subset).
# Known aliases / near-duplicates that are deliberately NOT synced
# separately (documented in docs/CATEGORIES.md): mass-removal and
# sweeper return the same set as board-wipe; blink the same as
# flicker; spot-removal is a subset view of removal.
VOCABULARY: dict[str, str] = {
    label: category for category, label in roles_mod.ROLES.items()
}

# Tags whose live probe (2026-11-12) answered 404: the tag does not
# exist (or is empty) in the Search API. They stay in the vocabulary
# so every sync re-checks them and reports NOT_FOUND honestly instead
# of the category silently losing its external layer.
KNOWN_MISSING_TAGS = ("stax", "token", "card-selection")


class TaggerBlocked(Exception):
    """robots.txt or a hard HTTP block forbids this sync."""


class SearchClient:
    """Polite client for api.scryfall.com (mirrors httpfetch rules).

    ``get_json(url)`` returns ``(status, payload|None, raw_bytes)``;
    HTTP errors are returned, not raised, except robots disallowance
    which raises :class:`TaggerBlocked`. Tests inject fakes with the
    same signature — no network in tests."""

    def __init__(self, *, min_interval: float = 0.12, max_retries: int = 3,
                 timeout: float = 30.0, sleeper=time.sleep):
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.timeout = timeout
        self.sleeper = sleeper
        self._last = 0.0
        self._disallows: list[str] | None = None

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": USER_AGENT, "Accept": "application/json"}

    def _check_robots(self) -> None:
        if self._disallows is None:
            rules: list[str] = []
            try:
                req = urllib.request.Request(API_BASE + "/robots.txt",
                                             headers=self._headers())
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    rules = _robots_rules(resp.read().decode("utf-8", "replace"))
            except Exception:
                rules = []  # unreachable robots.txt: proceed, rate limit applies
            self._disallows = rules
        for pattern in self._disallows:
            if _robots_match(pattern, "/cards/search"):
                raise TaggerBlocked(
                    f"robots.txt disallows /cards/search (rule: {pattern})")

    def _throttle(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            self.sleeper(wait)
        self._last = time.monotonic()

    def get_json(self, url: str) -> tuple[int, dict | None, bytes]:
        self._check_robots()
        backoff = 1.0
        for attempt in range(self.max_retries + 1):
            self._throttle()
            req = urllib.request.Request(url, headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    return resp.status, json.loads(raw), raw
            except urllib.error.HTTPError as exc:
                raw = exc.read() if exc.fp else b""
                if exc.code in (403, 429) or exc.code >= 500:
                    if attempt < self.max_retries:
                        delay = backoff * (2 ** attempt)
                        retry_after = exc.headers.get("Retry-After") if exc.headers else None
                        if retry_after and retry_after.isdigit():
                            delay = min(float(retry_after), 60.0)
                        self.sleeper(delay)
                        continue
                try:
                    return exc.code, json.loads(raw), raw
                except ValueError:
                    return exc.code, None, raw
            except (urllib.error.URLError, TimeoutError, OSError,
                    http.client.HTTPException):
                # HTTPException covers IncompleteRead / RemoteDisconnected
                # style failures while streaming a page body.
                if attempt < self.max_retries:
                    self.sleeper(backoff * (2 ** attempt))
                    continue
                raise
        raise AssertionError("unreachable")


def search_url(tag: str) -> str:
    query = urllib.parse.quote(f"function:{tag}", safe="")
    return f"{SEARCH_URL}?q={query}&unique=cards"


def _save_snapshot(store: Store, *, tag: str, category: str, url: str,
                   status: str, raw_pages: list[bytes], total: int | None,
                   captured: int, detail: str, payload: dict | None) -> str:
    """Snapshot row for one tag, same shape/provenance discipline as
    external.save_snapshot, but stamped with TAGGER_VERSION."""
    raw = b"\n".join(raw_pages) if raw_pages else None
    sha = hashlib.sha256(raw).hexdigest() if raw is not None else None
    snap_id = "snap-" + hashlib.sha256(
        f"{SOURCE_NAME}|{KIND}|{url}|{sha or ''}".encode()).hexdigest()[:24]
    raw_path: str | None = None
    if raw is not None:
        folder = Path(store.path).parent / "snapshots" / SOURCE_NAME
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{sha}.gz"
        if not target.exists():
            target.write_bytes(gzip.compress(raw))
        raw_path = str(target)
    store.conn.execute(
        "INSERT OR REPLACE INTO external_snapshot(snapshot_id,source_name,kind,"
        "commander_oracle_id,oracle_id,bracket,bracket_level,slug,source_url,status,"
        "parser_version,sha256,etag,last_modified,fetched_at,sample_size,"
        "captured_count,displayed_total,coverage_status,detail,raw_path,payload_json)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (snap_id, SOURCE_NAME, KIND, None, None, None, None, tag, url, status,
         TAGGER_VERSION, sha, None, None, utcnow(), None, captured, total,
         status, detail, raw_path,
         json.dumps(payload, ensure_ascii=False) if payload is not None else None))
    store.add_source(
        source_id=f"src-{snap_id}",
        source_name="Scryfall Tagger (official Search API, function: tags)",
        source_url=url, sha256=sha, data_status=status,
        note=f"tagger tag {tag} -> category {category}; parser {TAGGER_VERSION}",
        parser_version=TAGGER_VERSION)
    store.conn.commit()
    return snap_id


def _latest_tag_snapshot(store: Store, tag: str):
    return store.conn.execute(
        "SELECT * FROM external_snapshot WHERE source_name = ? AND kind = ? "
        "AND slug = ? AND parser_version = ? ORDER BY fetched_at DESC LIMIT 1",
        (SOURCE_NAME, KIND, tag, TAGGER_VERSION)).fetchone()


def _replace_claims(store: Store, tag: str, category: str,
                    oracle_ids: list[str], snapshot_id: str | None) -> None:
    with store.conn:
        store.conn.execute("DELETE FROM card_tagger_claim WHERE tag = ?", (tag,))
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_tagger_claim(oracle_id,tag,category,"
            "snapshot_id) VALUES(?,?,?,?)",
            [(oid, tag, category, snapshot_id) for oid in oracle_ids])


def _sync_one_tag(store: Store, client, tag: str, category: str,
                  store_ids: set[str], max_pages: int | None,
                  force: bool = False) -> dict:
    url = search_url(tag)
    if not force:
        previous = _latest_tag_snapshot(store, tag)
        if previous is not None and previous["status"] in ("AVAILABLE", "NOT_FOUND"):
            payload = None
            if previous["payload_json"]:
                try:
                    payload = json.loads(previous["payload_json"])
                except ValueError:
                    payload = None
            if previous["status"] == "NOT_FOUND" or payload is not None:
                ids = {str(i) for i in (payload or {}).get("oracle_ids", [])}
                in_store = sorted(ids & store_ids)
                if previous["status"] == "AVAILABLE":
                    _replace_claims(store, tag, category, in_store,
                                    previous["snapshot_id"])
                return {"tag": tag, "category": category,
                        "status": previous["status"],
                        "total_cards": previous["displayed_total"], "pages": 0,
                        "claims": len(in_store) if previous["status"] == "AVAILABLE" else 0,
                        "snapshot_id": previous["snapshot_id"],
                        "detail": f"reused snapshot of {previous['fetched_at']}"}
    ids: set[str] = set()
    raw_pages: list[bytes] = []
    total: int | None = None
    pages = 0
    status = "AVAILABLE"
    detail = ""
    next_url: str | None = url
    try:
        while next_url:
            if max_pages is not None and pages >= max_pages:
                status = "PARTIAL"
                detail = f"max_pages={max_pages} reached with more pages open"
                break
            code, payload, raw = client.get_json(next_url)
            if code == 404 and pages == 0:
                status = "NOT_FOUND"
                detail = "search answered 404 (tag unknown or empty)"
                raw_pages.append(raw)
                break
            if code != 200 or payload is None:
                status = "BLOCKED" if (code in (403, 429) and pages == 0) else "PARTIAL"
                detail = f"HTTP {code} on page {pages + 1}"
                if raw:
                    raw_pages.append(raw)
                break
            raw_pages.append(raw)
            pages += 1
            if total is None:
                total = payload.get("total_cards")
            for card in payload.get("data") or []:
                oid = card.get("oracle_id")
                if oid:
                    ids.add(str(oid))
            next_url = payload.get("next_page") if payload.get("has_more") else None
    except TaggerBlocked as exc:
        status = "BLOCKED"
        detail = str(exc)
    in_store = ids & store_ids
    payload_doc = {"tag": tag, "category": category,
                   "oracle_ids": sorted(ids)} if status == "AVAILABLE" else None
    # Snapshot FIRST, claims second: a crash can then only leave a
    # snapshot without claims (provenance intact, re-sync repairs the
    # claims), never claims without their snapshot.
    snap_id = _save_snapshot(
        store, tag=tag, category=category, url=url, status=status,
        raw_pages=raw_pages, total=total, captured=len(in_store),
        detail=(detail + f"; result_ids={len(ids)}; in_store={len(in_store)}"
                f"; outside_store={len(ids) - len(in_store)}").strip("; "),
        payload=payload_doc)
    if status == "AVAILABLE":
        _replace_claims(store, tag, category, sorted(in_store), snap_id)
    return {"tag": tag, "category": category, "status": status,
            "total_cards": total, "pages": pages,
            "claims": len(in_store) if status == "AVAILABLE" else 0,
            "snapshot_id": snap_id, "detail": detail}


def sync_tagger(store: Store, *, client=None, tags: list[str] | None = None,
                max_pages: int | None = None, force: bool = False) -> dict:
    """Sync Tagger membership for the vocabulary (or a subset).

    Claims are replaced per tag only when that tag completes
    (AVAILABLE). Afterwards, ``card_role`` is re-mirrored from
    ``card_tagger_claim`` under origin SCRYFALL_TAGGER_SEARCH, and —
    only for a complete vocabulary run with no BLOCKED/PARTIAL tag —
    'examined' rows are recorded for every store card."""
    categories.ensure_schema(store)
    roles_mod.ensure_schema(store)
    client = client or SearchClient()
    store_ids = {str(r[0]) for r in store.conn.execute(
        "SELECT oracle_id FROM scryfall_card")}
    wanted = tags if tags is not None else list(VOCABULARY)
    results: dict[str, dict] = {}
    for tag in wanted:
        category = VOCABULARY.get(tag)
        if category is None:
            results[tag] = {"tag": tag, "status": "NOT_FOUND",
                            "detail": "tag not in vocabulary"}
            continue
        results[tag] = _sync_one_tag(store, client, tag, category,
                                     store_ids, max_pages, force=force)
    # mirror claims into card_role under the tagger origin
    claim_counts: dict[str, int] = {}
    with store.conn:
        store.conn.execute("DELETE FROM card_role WHERE origin = ?",
                           (roles_mod.ORIGIN_TAGGER,))
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_role(oracle_id, role, origin) "
            "VALUES (?, ?, ?)",
            [(r[0], r[1], roles_mod.ORIGIN_TAGGER) for r in store.conn.execute(
                "SELECT oracle_id, category FROM card_tagger_claim")])
    for row in store.conn.execute(
            "SELECT oracle_id, COUNT(*) AS n FROM card_tagger_claim "
            "GROUP BY oracle_id"):
        claim_counts[row["oracle_id"]] = int(row["n"])
    full_run = tags is None
    clean = all(r["status"] in ("AVAILABLE", "NOT_FOUND")
                for r in results.values())
    if full_run and clean:
        categories.record_checks(
            store, origin=roles_mod.ORIGIN_TAGGER, version=TAGGER_VERSION,
            claims_by_card={oid: claim_counts.get(oid, 0) for oid in store_ids})
        store.conn.commit()
    run_status = "AVAILABLE" if (full_run and clean) else "PARTIAL"
    run_id = categories.write_run(
        store, layer="tagger_search", version=TAGGER_VERSION, source_id=None,
        status=run_status, cards_total=len(store_ids),
        cards_covered=len(store_ids) if (full_run and clean) else len(claim_counts),
        detail="; ".join(f"{t}:{r['status']}" for t, r in results.items()))
    store.conn.commit()
    return {"run_id": run_id, "run_status": run_status,
            "tags": results, "cards_with_claims": len(claim_counts),
            "claims_total": sum(claim_counts.values()),
            "checks_recorded": bool(full_run and clean)}
