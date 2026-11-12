"""Harvest of REAL public deck lists, organised by bracket cohort.

Why this module exists (evidence, 2026-11-12): EDHREC's commander
``/decks`` pages list every deck of a bracket cohort as METADATA
(urlhash, date, price, salt, type counts) — captured in
``edhrec_deck_entry`` — but the only link to a full list is EDHREC's own
``/deckpreview/{urlhash}``, and EDHREC's robots.txt disallows
``/deckpreview/`` outright. The payload carries no platform name and no
platform URL per deck, so an EDHREC entry cannot be resolved to its
source deck from public data. Moxfield is not a way out either:
``api2.moxfield.com/robots.txt`` disallows everything (``/``) and the
EDHREC urlhashes do not resolve on moxfield.com (HTTP 404 in probes).

What IS publicly reachable is Archidekt's own API:
  * deck search: ``GET https://archidekt.com/api/decks/v3/
    ?commanderName={name}&deckFormat=3&edhBracket={n}&page={p}``
    (60 rows/page, ``count`` = listed public decks of the cohort,
    each row carries ``edhBracket``),
  * deck detail: ``GET https://archidekt.com/api/decks/{id}/``
    (full card list; every card entry carries ``card.oracleCard.uid``
    = the Scryfall oracle_id, so mapping is by id, not by name guess).

Cohort honesty: a harvested deck's bracket is ARCHIDEKT's ``edhBracket``
(the platform's implementation of the official 1..5 bracket scale, same
level names as EDHREC's cohorts). It is stored as ``bracket_source =
'archidekt_edhBracket'`` and never claimed to be EDHREC's internal deck
set — EDHREC's set stays visible separately via ``edhrec_deck_entry``
counts and the EDHREC stats snapshots.

Storage: one ``decklist_deck`` row per deck with full provenance
(platform, platform deck id, commander, bracket, fetch time, parser
version, SHA-256, status); the raw JSON is kept gzipped next to the
private database, never in Git. Card rows in ``decklist_card`` are
aggregated per (oracle_id | unmapped name); unmapped cards are counted
and named, never silently dropped. Re-running the sync skips decks
already stored AVAILABLE with the current parser version (resumable).

Privacy: requests carry only public commander names and public deck
ids, exactly like the platform's own search UI. No collection data is
sent anywhere.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote_plus

from .httpfetch import FetchError, Fetcher, RobotsDisallowed
from .slugs import front_name
from .store import Store, utcnow

PARSER_VERSION = "archidekt-deck/1.0.0"
PLATFORM = "archidekt"
LIST_URL = "https://archidekt.com/api/decks/v3/"
DETAIL_URL = "https://archidekt.com/api/decks/{deck_id}/"
PAGE_SIZE = 60
BRACKET_NAMES = {1: "exhibition", 2: "core", 3: "upgraded", 4: "optimized", 5: "cedh"}
MAX_CONSECUTIVE_BLOCKED = 10


class DecklistError(Exception):
    pass


def _deck_uid(platform: str, deck_id: object) -> str:
    return f"{platform}:{deck_id}"


# --------------------------------------------------------------------------
# Archidekt payload parsing (pure functions — fixture-tested)
# --------------------------------------------------------------------------

def parse_list_page(text: str) -> dict:
    """One search-result page: total count + [{id, edhBracket, size}]."""
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise DecklistError(f"list page is not JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise DecklistError("list page carries no results array")
    rows = []
    for r in data["results"]:
        if isinstance(r, dict) and r.get("id") is not None:
            rows.append({"id": r["id"], "edh_bracket": r.get("edhBracket"),
                         "size": r.get("size"), "name": r.get("name"),
                         "updated_at": r.get("updatedAt")})
    count = data.get("count")
    return {"count": count if isinstance(count, int) else None, "results": rows}


def parse_deck_detail(text: str) -> dict:
    """One Archidekt deck JSON -> aggregated card entries.

    A card entry counts toward the deck when at least one of its
    categories is a deck category with ``includedInDeck`` (Maybeboard &
    co. are excluded by the deck's own category definitions; entries
    without categories count as main-deck). Entries are aggregated by
    oracle identity: ``card.oracleCard.uid`` is the Scryfall oracle_id;
    entries without a uid fall back to the oracle card's name and are
    resolved by the caller against the local Scryfall store.
    """
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise DecklistError(f"deck detail is not JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
        raise DecklistError("deck detail carries no cards array")
    included = {c["name"] for c in data.get("categories") or []
                if isinstance(c, dict) and c.get("includedInDeck")}
    entries: dict[str, dict] = {}
    total_cards = 0
    for entry in data["cards"]:
        if not isinstance(entry, dict):
            continue
        cats = [c for c in entry.get("categories") or [] if isinstance(c, str)]
        if cats and included and not any(c in included for c in cats):
            continue  # e.g. Maybeboard: not part of the deck list
        card = entry.get("card") or {}
        oracle = card.get("oracleCard") or {}
        uid = oracle.get("uid")
        name = oracle.get("name") or card.get("displayName") or ""
        qty = entry.get("quantity")
        qty = qty if isinstance(qty, int) and qty > 0 else 1
        is_cmd = 1 if "Commander" in cats else 0
        key = uid if uid else f"name:{name}"
        slot = entries.setdefault(key, {"oracle_id": uid, "name": name,
                                        "quantity": 0, "is_commander": 0})
        slot["quantity"] += qty
        slot["is_commander"] = max(slot["is_commander"], is_cmd)
        total_cards += qty
    return {
        "deck_id": data.get("id"), "name": data.get("name"),
        "edh_bracket": data.get("edhBracket"),
        "deck_format": data.get("deckFormat"),
        "theorycrafted": bool(data.get("theorycrafted")),
        "entries": sorted(entries.values(), key=lambda e: e["name"]),
        "total_cards": total_cards,
    }


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

def _save_raw(store: Store, raw: bytes) -> tuple[str, str]:
    """Write the gzipped raw payload via temp file + atomic rename.

    Raises OSError on storage failure; the caller decides the deck's
    fate (a failed raw save must never kill a long harvest run — seen
    in practice: a PermissionError from the storage layer after ~1,600
    successful writes aborted the process before this was hardened)."""
    sha = hashlib.sha256(raw).hexdigest()
    folder = Path(store.path).parent / "snapshots" / PLATFORM
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{sha}.gz"
    if target.exists():
        return sha, str(target)
    tmp = folder / f".{sha}.tmp"
    tmp.write_bytes(gzip.compress(raw))
    tmp.replace(target)
    return sha, str(target)


def deck_status(store: Store, deck_uid: str) -> str | None:
    row = store.conn.execute(
        "SELECT status FROM decklist_deck WHERE deck_uid=?", (deck_uid,)).fetchone()
    return row["status"] if row else None


def deck_is_current(store: Store, deck_uid: str) -> bool:
    """Resume predicate: only an AVAILABLE deck stored by the CURRENT
    parser version counts as harvested; anything else is re-fetched."""
    row = store.conn.execute(
        "SELECT status, parser_version FROM decklist_deck WHERE deck_uid=?",
        (deck_uid,)).fetchone()
    return bool(row) and row["status"] == "AVAILABLE" \
        and row["parser_version"] == PARSER_VERSION


def _store_deck(store: Store, *, deck_id: object, commander_oracle_id: str | None,
                commander_name: str, bracket_level: int, status: str,
                detail: str = "", parsed: dict | None = None,
                raw: bytes | None = None,
                source_updated_at: str | None = None) -> None:
    uid = _deck_uid(PLATFORM, deck_id)
    sha = raw_path = None
    if raw is not None:
        sha = hashlib.sha256(raw).hexdigest()
        try:
            sha, raw_path = _save_raw(store, raw)
        except OSError as exc:
            # cards are still stored; the deck is downgraded to PARTIAL
            # (not skipped on resume, so the raw save is retried later)
            raw_path = None
            detail = f"{detail}; raw save failed: {exc}".strip("; ")
            if status == "AVAILABLE":
                status = "PARTIAL"
    mapped = unmapped = 0
    unmapped_names: list[str] = []
    card_rows: list[tuple] = []
    if parsed is not None:
        for entry in parsed["entries"]:
            oracle_id = entry["oracle_id"]
            if oracle_id is not None and store.scryfall(oracle_id) is None:
                hit = store.scryfall_by_name(entry["name"])
                oracle_id = hit[0]["oracle_id"] if len(hit) == 1 else None
            if oracle_id is None:
                unmapped += 1
                unmapped_names.append(entry["name"])
            else:
                mapped += 1
            card_rows.append((uid, oracle_id or f"name:{entry['name']}", oracle_id,
                              entry["name"], entry["quantity"], entry["is_commander"]))
    store.conn.execute(
        "INSERT OR REPLACE INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,source_url,"
        "status,parser_version,sha256,raw_path,fetched_at,source_updated_at,"
        "deck_size,card_entries,mapped_cards,unmapped_cards,unmapped_names_json,"
        "detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, PLATFORM, str(deck_id), commander_oracle_id, commander_name,
         bracket_level, "archidekt_edhBracket",
         DETAIL_URL.format(deck_id=deck_id), status, PARSER_VERSION, sha, raw_path,
         utcnow(), source_updated_at,
         parsed["total_cards"] if parsed else None,
         len(parsed["entries"]) if parsed else 0, mapped, unmapped,
         json.dumps(sorted(unmapped_names), ensure_ascii=False), detail))
    store.conn.execute("DELETE FROM decklist_card WHERE deck_uid=?", (uid,))
    store.conn.executemany(
        "INSERT OR REPLACE INTO decklist_card(deck_uid,entry_key,oracle_id,"
        "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)", card_rows)
    store.conn.commit()
    return status


# --------------------------------------------------------------------------
# Sync
# --------------------------------------------------------------------------

def _list_url(name: str, bracket: int, page: int) -> str:
    return (f"{LIST_URL}?commanderName={quote_plus(name)}&deckFormat=3"
            f"&edhBracket={bracket}&page={page}")


def _cohort_listing(store: Store, fetcher: Fetcher, *, name: str,
                    commander_oracle_id: str | None, bracket: int,
                    max_decks: int) -> dict:
    """Collect up to ``max_decks`` deck ids of one cohort (listing phase).

    Returns {listed_count, name_form, ids, status, detail}. Tries the
    full card name first, then the front-face name for DFC commanders."""
    forms = [("full", name)]
    if "//" in name:
        forms.append(("front", front_name(name)))
    last: dict = {"listed_count": None, "name_form": "full", "ids": [],
                  "updated": {}, "status": "NOT_FOUND",
                  "detail": "no listing"}
    for form, form_name in forms:
        try:
            resp = fetcher.get(_list_url(form_name, bracket, 1))
        except RobotsDisallowed as exc:
            return {"listed_count": None, "name_form": form, "ids": [],
                    "status": "BLOCKED", "detail": str(exc)}
        if resp.status in (403, 429):
            return {"listed_count": None, "name_form": form, "ids": [],
                    "status": "BLOCKED", "detail": f"HTTP {resp.status} on search"}
        if resp.status != 200:
            last = {"listed_count": None, "name_form": form, "ids": [],
                    "status": "NOT_FOUND", "detail": f"HTTP {resp.status} on search"}
            continue
        try:
            page = parse_list_page(resp.text)
        except DecklistError as exc:
            last = {"listed_count": None, "name_form": form, "ids": [],
                    "status": "PARTIAL", "detail": str(exc)}
            continue
        count = page["count"]
        if not count:
            last = {"listed_count": 0, "name_form": form, "ids": [],
                    "updated": {}, "status": "AVAILABLE",
                    "detail": "cohort empty on Archidekt"}
            continue
        ids: list = []
        updated: dict = {}
        seen: set = set()
        rows = page["results"]
        page_no = 1
        truncation = ""
        while True:
            for r in rows:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    ids.append(r["id"])
                    updated[r["id"]] = r.get("updated_at")
            if len(ids) >= min(count, max_decks) or not rows:
                break
            page_no += 1
            try:
                resp = fetcher.get(_list_url(form_name, bracket, page_no))
            except RobotsDisallowed as exc:
                return {"listed_count": count, "name_form": form, "ids": ids,
                        "status": "BLOCKED", "detail": str(exc)}
            if resp.status != 200:
                truncation = (f"; listing truncated at page {page_no}: "
                              f"HTTP {resp.status} (ids so far kept)")
                break
            try:
                rows = parse_list_page(resp.text)["results"]
            except DecklistError as exc:
                truncation = (f"; listing truncated at page {page_no}: "
                              f"{exc} (ids so far kept)")
                break
        ids = ids[:max_decks]
        store.conn.execute(
            "INSERT OR REPLACE INTO decklist_listing(platform,commander_oracle_id,"
            "commander_name,bracket_level,name_form,listed_count,updated_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (PLATFORM, commander_oracle_id, name, bracket, form, count, utcnow()))
        store.conn.commit()
        return {"listed_count": count, "name_form": form, "ids": ids,
                "updated": {i: updated.get(i) for i in ids},
                "status": "AVAILABLE",
                "detail": f"listed={count}, ids collected={len(ids)}{truncation}"}
    return last


def _sync_cohort(store: Store, fetcher: Fetcher, *, cmdr: dict, bracket: int,
                 max_per_cohort: int, consecutive_blocked: int) -> tuple[dict, int, bool]:
    """One commander x bracket cohort. Returns (cohort, blocked_run,
    stopped). Counts are cohort-local; the caller folds them into the
    report totals only after the cohort completed, so a retried cohort
    never double-counts (its stored decks come back as 'cached')."""
    listing = _cohort_listing(
        store, fetcher, name=cmdr["name"],
        commander_oracle_id=cmdr.get("oracle_id"), bracket=bracket,
        max_decks=max_per_cohort)
    cohort = {"commander": cmdr["name"], "bracket": bracket,
              "bracket_name": BRACKET_NAMES.get(bracket),
              "listed_count": listing["listed_count"],
              "name_form": listing["name_form"],
              "listing_status": listing["status"],
              "fetched": 0, "cached": 0, "available": 0,
              "not_found": 0, "blocked": 0, "partial": 0}
    stopped = False
    for deck_id in listing["ids"]:
        if deck_is_current(store, _deck_uid(PLATFORM, deck_id)):
            cohort["cached"] += 1
            continue
        cohort["fetched"] += 1
        outcome = _sync_one_deck(
            store, fetcher, cmdr=cmdr, bracket=bracket, deck_id=deck_id,
            source_updated_at=(listing.get("updated") or {}).get(deck_id))
        cohort[outcome] += 1
        if outcome == "blocked":
            consecutive_blocked += 1
            if consecutive_blocked >= MAX_CONSECUTIVE_BLOCKED:
                stopped = True
                break
        else:
            consecutive_blocked = 0
    return cohort, consecutive_blocked, stopped


def sync_decklists(store: Store, fetcher: Fetcher, *, commanders: list[dict],
                   brackets: tuple[int, ...] = (2, 3, 4),
                   max_per_cohort: int = 300) -> dict:
    """Resumable harvest over commander x bracket cohorts.

    ``commanders``: [{oracle_id, name}]. Decks already stored AVAILABLE
    with the current parser version are skipped (counted as cached).
    Stops the whole run after MAX_CONSECUTIVE_BLOCKED consecutive blocked
    detail fetches (rate-limit protection) — state stays resumable.
    A transient storage failure (sqlite3.OperationalError, e.g. a flaky
    disk layer) retries the affected cohort with backoff and, if it
    persists, marks that one cohort STORAGE_ERROR and CONTINUES with
    the next — one bad patch must not kill a multi-hour run (observed
    twice in the real 2026-11-12 run: PermissionError and disk I/O)."""
    report: dict = {"commanders": len(commanders), "brackets": list(brackets),
                    "max_per_cohort": max_per_cohort, "cohorts": [],
                    "totals": {"listed": 0, "fetched": 0, "cached": 0,
                               "available": 0, "not_found": 0, "blocked": 0,
                               "partial": 0, "storage_errors": 0,
                               "stopped_on_block": False}}
    consecutive_blocked = 0
    for cmdr in commanders:
        for bracket in brackets:
            cohort = None
            for attempt in range(3):
                try:
                    cohort, consecutive_blocked, stopped = _sync_cohort(
                        store, fetcher, cmdr=cmdr, bracket=bracket,
                        max_per_cohort=max_per_cohort,
                        consecutive_blocked=consecutive_blocked)
                    break
                except (sqlite3.OperationalError, FetchError) as exc:
                    # transient storage contention OR a network failure the
                    # fetcher already retried: same treatment — back off,
                    # retry the cohort, finally mark + continue
                    try:
                        store.conn.rollback()
                    except sqlite3.Error:
                        pass
                    if attempt == 2:
                        cohort = {"commander": cmdr["name"], "bracket": bracket,
                                  "bracket_name": BRACKET_NAMES.get(bracket),
                                  "listed_count": None, "name_form": "full",
                                  "listing_status": (
                                      "STORAGE_ERROR"
                                      if isinstance(exc, sqlite3.OperationalError)
                                      else "FETCH_ERROR"),
                                  "detail": f"{type(exc).__name__}: {exc}",
                                  "fetched": 0, "cached": 0, "available": 0,
                                  "not_found": 0, "blocked": 0, "partial": 0}
                        report["totals"]["storage_errors"] += 1
                        stopped = False
                    else:
                        time.sleep(15 * (attempt + 1))
            if cohort["listed_count"]:
                report["totals"]["listed"] += cohort["listed_count"]
            for key in ("fetched", "cached", "available", "not_found",
                        "blocked", "partial"):
                report["totals"][key] += cohort[key]
            report["cohorts"].append(cohort)
            if stopped:
                report["totals"]["stopped_on_block"] = True
                return report
    return report


def _sync_one_deck(store: Store, fetcher: Fetcher, *, cmdr: dict, bracket: int,
                   deck_id: object,
                   source_updated_at: str | None = None) -> str:
    """Fetch + store ONE deck; returns 'available' | 'not_found' |
    'blocked' | 'partial'. NEVER raises: a single deck's failure —
    network, parse, storage — is recorded as PARTIAL with the reason
    and the run continues (a multi-hour harvest must not die on one
    deck; observed in practice with a storage PermissionError)."""
    base = dict(deck_id=deck_id, commander_oracle_id=cmdr.get("oracle_id"),
                commander_name=cmdr["name"], bracket_level=bracket,
                source_updated_at=source_updated_at)
    try:
        try:
            resp = fetcher.get(DETAIL_URL.format(deck_id=deck_id))
        except RobotsDisallowed as exc:
            _store_deck(store, status="BLOCKED", detail=str(exc), **base)
            return "blocked"
        if resp.status in (403, 429):
            _store_deck(store, status="BLOCKED", detail=f"HTTP {resp.status}",
                        raw=resp.body, **base)
            return "blocked"
        if resp.status == 404:
            _store_deck(store, status="NOT_FOUND",
                        detail="HTTP 404 (deleted/private?)", **base)
            return "not_found"
        if resp.status != 200:
            _store_deck(store, status="BLOCKED", detail=f"HTTP {resp.status}",
                        raw=resp.body, **base)
            return "blocked"
        try:
            parsed = parse_deck_detail(resp.text)
        except DecklistError as exc:
            _store_deck(store, status="PARTIAL", detail=str(exc),
                        raw=resp.body, **base)
            return "partial"
        detail_bits = []
        if parsed["edh_bracket"] is not None and parsed["edh_bracket"] != bracket:
            detail_bits.append(
                f"detail edhBracket={parsed['edh_bracket']} != cohort {bracket}")
        if parsed["theorycrafted"]:
            detail_bits.append("theorycrafted")
        effective = _store_deck(store, status="AVAILABLE",
                                detail="; ".join(detail_bits),
                                parsed=parsed, raw=resp.body, **base)
        return "available" if effective == "AVAILABLE" else "partial"
    except Exception as exc:  # noqa: BLE001 — one deck must not kill the run
        if isinstance(exc, sqlite3.OperationalError) and "locked" in str(exc):
            # Contention (another process holds the DB) is transient and
            # NOT this deck's fault: propagate to the cohort-level retry,
            # which backs off and resumes — the deck must not be filed
            # as PARTIAL for a lock it didn't cause (observed in the real
            # run: bursts of 'database is locked' while a second process
            # held long transactions).
            raise
        try:
            _store_deck(store, status="PARTIAL",
                        detail=f"unexpected: {type(exc).__name__}: {exc}", **base)
        except Exception:  # noqa: BLE001 — even the failure record may fail
            pass
        return "partial"


def decklist_coverage(store: Store) -> dict:
    """Per commander x bracket: listed (Archidekt count) vs stored decks
    by status, plus card-mapping quality over AVAILABLE decks."""
    listings = store.conn.execute(
        "SELECT * FROM decklist_listing ORDER BY commander_name, bracket_level").fetchall()
    decks = store.conn.execute(
        "SELECT commander_name, bracket_level, status, COUNT(*) n, "
        "SUM(mapped_cards) mapped, SUM(unmapped_cards) unmapped "
        "FROM decklist_deck GROUP BY commander_name, bracket_level, status").fetchall()
    by_key: dict[tuple, dict] = {}
    for d in decks:
        slot = by_key.setdefault((d["commander_name"], d["bracket_level"]),
                                 {"available": 0, "not_found": 0, "blocked": 0,
                                  "partial": 0, "mapped_cards": 0, "unmapped_cards": 0})
        slot[d["status"].lower()] = d["n"]
        slot["mapped_cards"] += d["mapped"] or 0
        slot["unmapped_cards"] += d["unmapped"] or 0
    cohorts = []
    for lst in listings:
        key = (lst["commander_name"], lst["bracket_level"])
        slot = by_key.get(key, {"available": 0, "not_found": 0, "blocked": 0,
                                "partial": 0, "mapped_cards": 0, "unmapped_cards": 0})
        mapped, unmapped = slot["mapped_cards"], slot["unmapped_cards"]
        cohorts.append({
            "commander": lst["commander_name"], "bracket": lst["bracket_level"],
            "bracket_name": BRACKET_NAMES.get(lst["bracket_level"]),
            "listed_count": lst["listed_count"], **slot,
            "mapping_share": (mapped / (mapped + unmapped)) if (mapped + unmapped) else None})
    totals = {"listed": sum(c["listed_count"] or 0 for c in cohorts),
              "available": sum(c["available"] for c in cohorts),
              "not_found": sum(c["not_found"] for c in cohorts),
              "blocked": sum(c["blocked"] for c in cohorts),
              "partial": sum(c["partial"] for c in cohorts),
              "mapped_cards": sum(c["mapped_cards"] for c in cohorts),
              "unmapped_cards": sum(c["unmapped_cards"] for c in cohorts)}
    return {"cohorts": cohorts, "totals": totals,
            "note": "listed = Archidekt public search count for the cohort "
                    "(commanderName + deckFormat=3 + edhBracket); obtained = "
                    "deck lists stored locally AVAILABLE"}
