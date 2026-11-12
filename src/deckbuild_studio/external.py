"""External data sync — EDHREC + Playgroup adapters, snapshots, coverage.

Phase 2 implementation on top of the Phase-1 job scaffold. Every fetched
record is a *snapshot*: source URL, fetch time, parser version, SHA-256 of
the raw body, status (AVAILABLE / PARTIAL / BLOCKED / NOT_FOUND / STALE /
NOT_FETCHED), sample size where the source publishes one, and a coverage
statement. Nothing is invented: a failed or empty fetch produces a status,
never data. Raw bodies are stored gzipped NEXT TO the private database
(never in Git). Parsed payloads live in ``external_snapshot.payload_json``;
EDHREC card stats / deck entries additionally in their own tables.

Privacy: adapters request only publicly known commander/card slugs, one
page at a time, like a normal website visit. No collection quantities,
locations, deck lists or oracle-id lists are ever sent anywhere.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import quote_plus

from . import edhrec as edhrec_mod
from . import edhrec_card as edhrec_card_mod
from . import playgroup as pg_mod
from . import spellbook as spellbook_mod
from .httpfetch import Fetcher, FetchError, RobotsDisallowed
from .slugs import front_name, slugify
from .store import Store, utcnow

BRACKETS = {"core": 2, "upgraded": 3, "optimized": 4}
EXTERNAL_PARSER_VERSION = "2.0.0"
_SOURCES = {"edhrec": "EDHREC", "playgroup": "Playgroup.gg",
            "commanderspellbook": "Commander Spellbook"}


def _job_id(*parts: str) -> str:
    return "job-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]


# --------------------------------------------------------------------------
# Phase-1 job scaffold (kept; sync below fills these jobs with real states)
# --------------------------------------------------------------------------

def register_commander_jobs(store: Store, commander_oracle_id: str, slug: str | None = None) -> int:
    """Create the 6 EDHREC jobs + 1 Playgroup commander job as NOT_FETCHED."""
    n = 0
    for bracket, level in BRACKETS.items():
        for view in ("stats", "decks"):
            url = f"https://edhrec.com/commanders/{slug}/{bracket}" + ("/decks" if view == "decks" else "")
            jid = _job_id("edhrec", commander_oracle_id, bracket, view)
            store.conn.execute(
                "INSERT OR IGNORE INTO sync_job(job_id,job_type,commander_oracle_id,bracket,"
                "bracket_level,target_url,status,detail,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (jid, f"edhrec_{view}", commander_oracle_id, bracket, level,
                 url if slug else None, "NOT_FETCHED",
                 "slug unresolved" if not slug else "phase 2: not fetched yet", utcnow()))
            n += 1
    jid = _job_id("playgroup_commander", commander_oracle_id)
    store.conn.execute(
        "INSERT OR IGNORE INTO sync_job(job_id,job_type,commander_oracle_id,status,detail,updated_at)"
        " VALUES(?,?,?,?,?,?)",
        (jid, "playgroup_commander", commander_oracle_id, "NOT_FETCHED",
         "numeric Playgroup id unresolved; must be resolved from a real source (phase 2)",
         utcnow()))
    store.conn.commit()
    return n + 1


def register_card_atlas_jobs(store: Store, collection_id: str) -> int:
    rows = store.conn.execute(
        "SELECT DISTINCT oracle_id FROM physical_lot WHERE collection_id=?",
        (collection_id,)).fetchall()
    for r in rows:
        jid = _job_id("playgroup_card", r["oracle_id"])
        store.conn.execute(
            "INSERT OR IGNORE INTO sync_job(job_id,job_type,oracle_id,status,detail,updated_at)"
            " VALUES(?,?,?,?,?,?)",
            (jid, "playgroup_card_atlas", r["oracle_id"], "NOT_FETCHED",
             "phase 2: not fetched yet", utcnow()))
    store.conn.commit()
    return len(rows)


# --------------------------------------------------------------------------
# Snapshot storage
# --------------------------------------------------------------------------

def _snapshot_id(source: str, kind: str, url: str, sha: str | None) -> str:
    return "snap-" + hashlib.sha256(f"{source}|{kind}|{url}|{sha or ''}".encode()).hexdigest()[:24]


def latest_snapshot(store: Store, source_name: str, kind: str, *,
                    commander_oracle_id: str | None = None,
                    oracle_id: str | None = None,
                    bracket: str | None = None,
                    slug: str | None = None,
                    parser_version: str | None = EXTERNAL_PARSER_VERSION):
    """Latest snapshot for a key. Snapshots written by another parser
    version are invisible here — that is the cache invalidation on parser
    change (old rows remain as history). ``slug`` additionally narrows
    the key (commander pages are identified by slug, not oracle id)."""
    q = ("SELECT * FROM external_snapshot WHERE source_name=? AND kind=? "
         "AND commander_oracle_id IS ? AND oracle_id IS ? AND bracket IS ?")
    args: list = [source_name, kind, commander_oracle_id, oracle_id, bracket]
    if slug is not None:
        q += " AND slug IS ?"
        args.append(slug)
    if parser_version is not None:
        q += " AND parser_version=?"
        args.append(parser_version)
    q += " ORDER BY fetched_at DESC LIMIT 1"
    return store.conn.execute(q, args).fetchone()


def snapshot_is_current(row) -> bool:
    return row is not None and row["parser_version"] == EXTERNAL_PARSER_VERSION


def save_snapshot(store: Store, *, source_name: str, kind: str, url: str, status: str,
                  commander_oracle_id: str | None = None, oracle_id: str | None = None,
                  bracket: str | None = None, slug: str | None = None,
                  raw: bytes | None = None, etag: str | None = None,
                  last_modified: str | None = None, sample_size: int | None = None,
                  captured_count: int | None = None, displayed_total: int | None = None,
                  coverage_status: str | None = None, detail: str = "",
                  payload: dict | None = None) -> str:
    sha = hashlib.sha256(raw).hexdigest() if raw is not None else None
    snap_id = _snapshot_id(source_name, kind, url, sha)
    raw_path: str | None = None
    if raw is not None:
        folder = Path(store.path).parent / "snapshots" / source_name
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{sha}.gz"
        if not target.exists():
            target.write_bytes(gzip.compress(raw))
        raw_path = str(target)
    level = BRACKETS.get(bracket) if bracket else None
    store.conn.execute(
        "INSERT OR REPLACE INTO external_snapshot(snapshot_id,source_name,kind,"
        "commander_oracle_id,oracle_id,bracket,bracket_level,slug,source_url,status,"
        "parser_version,sha256,etag,last_modified,fetched_at,sample_size,captured_count,"
        "displayed_total,coverage_status,detail,raw_path,payload_json)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (snap_id, source_name, kind, commander_oracle_id, oracle_id, bracket, level,
         slug, url, status, EXTERNAL_PARSER_VERSION, sha, etag, last_modified, utcnow(),
         sample_size, captured_count, displayed_total, coverage_status, detail,
         raw_path, json.dumps(payload, ensure_ascii=False) if payload is not None else None))
    store.add_source(
        source_id=f"src-{snap_id}", source_name=_SOURCES.get(source_name, source_name),
        source_url=url, sha256=sha, data_status=status,
        note=f"{kind} snapshot; parser {EXTERNAL_PARSER_VERSION}",
        parser_version=EXTERNAL_PARSER_VERSION)
    store.conn.commit()
    return snap_id


def _set_job(store: Store, *, job_type: str, status: str, detail: str,
             commander_oracle_id: str | None = None, oracle_id: str | None = None,
             bracket: str | None = None, url: str | None = None) -> None:
    q = "UPDATE sync_job SET status=?, detail=?, updated_at=?"
    args: list = [status, detail[:500], utcnow()]
    if url:
        q += ", target_url=?"
        args.append(url)
    q += " WHERE job_type=?"
    args.append(job_type)
    if commander_oracle_id is not None:
        q += " AND commander_oracle_id=?"
        args.append(commander_oracle_id)
    if oracle_id is not None:
        q += " AND oracle_id=?"
        args.append(oracle_id)
    if bracket is not None:
        q += " AND bracket=?"
        args.append(bracket)
    store.conn.execute(q, args)
    store.conn.commit()


def _result(row) -> dict:
    if row is None:
        return {}
    d = dict(row)
    d.pop("payload_json", None)
    return d


# --------------------------------------------------------------------------
# EDHREC sync
# --------------------------------------------------------------------------

def _edhrec_url(slug: str, bracket: str | None, view: str) -> str:
    base = f"https://edhrec.com/commanders/{slug}"
    if bracket:
        base += f"/{bracket}"
    if view == "decks":
        base += "/decks"
    return base


def sync_edhrec(store: Store, fetcher: Fetcher, *, name: str,
                commander_oracle_id: str | None = None, slug: str | None = None,
                include_base: bool = False, force: bool = False) -> list[dict]:
    slug = slug or slugify(name)
    if commander_oracle_id:
        register_commander_jobs(store, commander_oracle_id, slug)
    views: list[tuple[str | None, str]] = []
    if include_base:
        views += [(None, "stats"), (None, "decks")]
    for bracket in BRACKETS:
        views += [(bracket, "stats"), (bracket, "decks")]
    results: list[dict] = []
    for bracket, view in views:
        kind = f"edhrec_{view}"
        url = _edhrec_url(slug, bracket, view)

        def record(status: str, detail: str, raw: bytes | None = None) -> None:
            snap = save_snapshot(store, source_name="edhrec", kind=kind, url=url,
                                 status=status, commander_oracle_id=commander_oracle_id,
                                 bracket=bracket, slug=slug, raw=raw, detail=detail)
            results.append({"snapshot_id": snap, "status": status, "source_url": url,
                            "bracket": bracket, "kind": kind, "detail": detail})
            _set_job(store, job_type=kind, status=status, detail=detail,
                     commander_oracle_id=commander_oracle_id, bracket=bracket, url=url)

        existing = latest_snapshot(store, "edhrec", kind,
                                   commander_oracle_id=commander_oracle_id, bracket=bracket)
        if existing is not None and not force and existing["status"] in ("AVAILABLE", "PARTIAL"):
            results.append({**_result(existing), "cached": True})
            continue
        etag = existing["etag"] if existing is not None else None
        lm = existing["last_modified"] if existing is not None else None
        try:
            resp = fetcher.get(url, etag=etag, last_modified=lm)
        except RobotsDisallowed as exc:
            record("BLOCKED", str(exc))
            continue
        if resp.status == 304 and existing is not None:
            results.append({**_result(existing), "cached": True, "not_modified": True})
            continue
        if resp.status in (403, 429):
            record("BLOCKED", f"HTTP {resp.status} (rate limited / forbidden)", resp.body)
            continue
        if resp.status == 404:
            record("NOT_FOUND", "HTTP 404 — EDHREC has no such page for this slug")
            continue
        if resp.status != 200:
            record("BLOCKED", f"HTTP {resp.status}", resp.body)
            continue
        try:
            if view == "stats":
                parsed = edhrec_mod.parse_stats_page(
                    resp.text, expected_name=name, expected_slug=slug,
                    bracket=bracket or "base")
            else:
                parsed = edhrec_mod.parse_decks_page(
                    resp.text, expected_name=name, expected_slug=slug,
                    bracket=bracket or "base")
        except edhrec_mod.VerificationError as exc:
            record("NOT_FOUND", f"slug verification failed: {exc}", resp.body)
            continue
        except edhrec_mod.ParseError as exc:
            record("PARTIAL", f"parse error: {exc}", resp.body)
            continue
        if view == "stats":
            status = "AVAILABLE"
            detail = ("gallery recs captured; EDHREC ships no gallery total "
                      "(paginationTotal undefined) — coverage total unknown"
                      if parsed["coverage_status"] == "TOTAL_UNKNOWN" else "")
            snap = save_snapshot(
                store, source_name="edhrec", kind=kind, url=url, status=status,
                commander_oracle_id=commander_oracle_id, bracket=bracket, slug=slug,
                raw=resp.body, etag=resp.etag, last_modified=resp.last_modified,
                sample_size=parsed["cohort_decks"], captured_count=parsed["captured_count"],
                displayed_total=parsed["displayed_total"],
                coverage_status=parsed["coverage_status"], detail=detail,
                payload={k: parsed[k] for k in
                         ("commander", "bracket_counts_all", "tags", "budgets", "categories")})
            store.conn.execute("DELETE FROM edhrec_card_stat WHERE snapshot_id=?", (snap,))
            for card in parsed["cards"]:
                store.conn.execute(
                    "INSERT OR REPLACE INTO edhrec_card_stat(snapshot_id,category,card_slug,"
                    "name,scryfall_id,inclusion,num_decks,potential_decks,synergy,lift,"
                    "trend_zscore) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (snap, card["category"] or "unknown", card["card_slug"], card["name"],
                     card["scryfall_id"], card["inclusion"], card["num_decks"],
                     card["potential_decks"], card["synergy"], card["lift"],
                     card["trend_zscore"]))
            store.conn.commit()
        else:
            status = "PARTIAL" if parsed["coverage_status"] == "PARTIAL" else "AVAILABLE"
            snap = save_snapshot(
                store, source_name="edhrec", kind=kind, url=url, status=status,
                commander_oracle_id=commander_oracle_id, bracket=bracket, slug=slug,
                raw=resp.body, etag=resp.etag, last_modified=resp.last_modified,
                sample_size=parsed["cohort_decks"], captured_count=parsed["captured_count"],
                displayed_total=parsed["displayed_total"],
                coverage_status=parsed["coverage_status"], detail=parsed["note"],
                payload={"commander": parsed["commander"]})
            store.conn.execute("DELETE FROM edhrec_deck_entry WHERE snapshot_id=?", (snap,))
            for entry in parsed["entries"]:
                store.conn.execute(
                    "INSERT OR REPLACE INTO edhrec_deck_entry(snapshot_id,urlhash,savedate,"
                    "price,salt,tags_json,type_counts_json) VALUES(?,?,?,?,?,?,?)",
                    (snap, entry["urlhash"], entry["savedate"], entry["price"], entry["salt"],
                     json.dumps(entry["tags"]), json.dumps(entry["type_counts"])))
            store.conn.commit()
        _set_job(store, job_type=kind, status=status,
                 detail=f"captured={parsed['captured_count']} cohort={parsed['cohort_decks']}",
                 commander_oracle_id=commander_oracle_id, bracket=bracket, url=url)
        results.append({"snapshot_id": snap, "status": status, "source_url": url,
                        "bracket": bracket, "kind": kind,
                        "captured_count": parsed["captured_count"],
                        "sample_size": parsed["cohort_decks"],
                        "coverage_status": parsed["coverage_status"]})
    return results


# --------------------------------------------------------------------------
# Playgroup sync
# --------------------------------------------------------------------------

PG_AUTOCOMPLETE = "https://playgroup.gg/api/v1/commanders?link=true&q="


def resolve_playgroup_commander(fetcher: Fetcher, name: str) -> dict | None:
    """Resolve the numeric Playgroup id via Playgroup's own autocomplete.

    The label must match the card name EXACTLY (or its front face). Returns
    None when Playgroup has no exact match — the id is never guessed."""
    resp = fetcher.get(PG_AUTOCOMPLETE + quote_plus(front_name(name)))
    if resp.status != 200:
        return None
    return pg_mod.parse_autocomplete(resp.text, name)


def sync_playgroup_commander(store: Store, fetcher: Fetcher, *, name: str,
                             commander_oracle_id: str | None = None,
                             force: bool = False) -> dict:
    if commander_oracle_id:
        register_commander_jobs(store, commander_oracle_id, slugify(name))
    existing = latest_snapshot(store, "playgroup", "playgroup_commander",
                               commander_oracle_id=commander_oracle_id)
    if existing is not None and not force and existing["status"] == "AVAILABLE":
        return {**_result(existing), "cached": True}
    ac_url = PG_AUTOCOMPLETE + quote_plus(front_name(name))
    try:
        resolved = resolve_playgroup_commander(fetcher, name)
    except RobotsDisallowed as exc:
        snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                             url=ac_url, status="BLOCKED",
                             commander_oracle_id=commander_oracle_id,
                             slug=slugify(name), detail=str(exc))
        _set_job(store, job_type="playgroup_commander", status="BLOCKED", detail=str(exc),
                 commander_oracle_id=commander_oracle_id)
        return {"snapshot_id": snap, "status": "BLOCKED", "detail": str(exc)}
    if resolved is None:
        detail = ("UNRESOLVED: Playgroup autocomplete has no exact-label match "
                  "for this commander; numeric id not guessed")
        snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                             url=ac_url, status="NOT_FOUND",
                             commander_oracle_id=commander_oracle_id,
                             slug=slugify(name), detail=detail)
        _set_job(store, job_type="playgroup_commander", status="NOT_FOUND", detail=detail,
                 commander_oracle_id=commander_oracle_id)
        return {"snapshot_id": snap, "status": "NOT_FOUND", "detail": detail,
                "resolution": "UNRESOLVED"}
    json_url = f"https://playgroup.gg/api/public/v1/commanders/{resolved['playgroup_id']}.json"
    try:
        resp = fetcher.get(json_url)
    except RobotsDisallowed as exc:
        snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                             url=json_url, status="BLOCKED",
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"], detail=str(exc))
        return {"snapshot_id": snap, "status": "BLOCKED", "detail": str(exc)}
    if resp.status != 200:
        status = "NOT_FOUND" if resp.status == 404 else ("BLOCKED" if resp.status in (403, 429) else "PARTIAL")
        detail = f"HTTP {resp.status} from public commander JSON"
        snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                             url=json_url, status=status, raw=resp.body,
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"], detail=detail)
        _set_job(store, job_type="playgroup_commander", status=status, detail=detail,
                 commander_oracle_id=commander_oracle_id, url=resolved["url"])
        return {"snapshot_id": snap, "status": status, "detail": detail}
    try:
        parsed = pg_mod.parse_commander_json(resp.text, expected_name=name)
    except pg_mod.ParseError as exc:
        snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                             url=json_url, status="PARTIAL", raw=resp.body,
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"], detail=f"parse error: {exc}")
        _set_job(store, job_type="playgroup_commander", status="PARTIAL",
                 detail=f"parse error: {exc}", commander_oracle_id=commander_oracle_id,
                 url=resolved["url"])
        return {"snapshot_id": snap, "status": "PARTIAL", "detail": f"parse error: {exc}"}
    detail = ("public JSON offers no archetypes/matchups/win-conditions/"
              "seat/mulligan/players fields — absent, not invented")
    snap = save_snapshot(store, source_name="playgroup", kind="playgroup_commander",
                         url=json_url, status="AVAILABLE", raw=resp.body,
                         etag=resp.etag, last_modified=resp.last_modified,
                         commander_oracle_id=commander_oracle_id,
                         slug=resolved["slug"], sample_size=parsed["sample_size"],
                         detail=detail, payload=parsed)
    _set_job(store, job_type="playgroup_commander", status="AVAILABLE",
             detail=f"playgroup_id={resolved['playgroup_id']} games={parsed['sample_size']}",
             commander_oracle_id=commander_oracle_id, url=resolved["url"])
    return {"snapshot_id": snap, "status": "AVAILABLE", "source_url": json_url,
            "playgroup_id": resolved["playgroup_id"], "sample_size": parsed["sample_size"]}


def sync_card_atlas(store: Store, fetcher: Fetcher, collection_id: str, *,
                    limit: int | None = None, force: bool = False) -> dict:
    """Resumable Card-Atlas sync over one collection profile.

    Stops at the first BLOCKED response (403/429/robots) — no escalation,
    no bypass. Already-synced cards (current parser version) are skipped
    unless ``force``; that is what makes the sync resumable."""
    register_card_atlas_jobs(store, collection_id)
    seen: dict[str, str] = {}
    for row in store.inventory_rows(collection_id):
        if row["name"]:
            seen.setdefault(row["oracle_id"], row["name"])
    coverage = {"collection_id": collection_id, "total_identities": len(seen),
                "attempted": 0, "cached_skipped": 0, "available": 0, "partial": 0,
                "not_found": 0, "blocked": 0, "small_sample": 0,
                "network_errors": 0, "stopped_on_block": False}
    for oracle_id, name in sorted(seen.items(), key=lambda kv: kv[1]):
        existing = latest_snapshot(store, "playgroup", "playgroup_card", oracle_id=oracle_id)
        if existing is not None and not force and existing["status"] in ("AVAILABLE", "PARTIAL", "NOT_FOUND"):
            coverage["cached_skipped"] += 1
            continue
        if limit is not None and coverage["attempted"] >= limit:
            break
        slug = slugify(name)
        url = f"https://playgroup.gg/cards/{slug}"
        coverage["attempted"] += 1

        def blocked(detail: str, raw: bytes | None = None, stop: bool = True) -> None:
            save_snapshot(store, source_name="playgroup", kind="playgroup_card", url=url,
                          status="BLOCKED", oracle_id=oracle_id, slug=slug,
                          raw=raw, detail=detail)
            _set_job(store, job_type="playgroup_card_atlas", status="BLOCKED",
                     detail=detail, oracle_id=oracle_id, url=url)
            coverage["blocked"] += 1
            coverage["stopped_on_block"] = stop

        try:
            resp = fetcher.get(url)
        except RobotsDisallowed as exc:
            blocked(str(exc))
            break
        except FetchError:
            # Transient network failure (the fetcher already retried
            # with backoff): record NOTHING — the card stays NOT_FETCHED
            # and a later run retries it. Not a block; the run goes on.
            coverage["network_errors"] += 1
            continue
        if resp.status in (403, 429):
            blocked(f"HTTP {resp.status} — sync stopped, no escalation", resp.body)
            break
        if resp.status == 404:
            detail = "HTTP 404 — Playgroup has no card page for this slug"
            save_snapshot(store, source_name="playgroup", kind="playgroup_card", url=url,
                          status="NOT_FOUND", oracle_id=oracle_id, slug=slug, detail=detail)
            _set_job(store, job_type="playgroup_card_atlas", status="NOT_FOUND",
                     detail=detail, oracle_id=oracle_id, url=url)
            coverage["not_found"] += 1
            continue
        if resp.status != 200:
            blocked(f"HTTP {resp.status}", resp.body)
            break
        try:
            fields = pg_mod.parse_card_page(resp.text, expected_name=name)
        except pg_mod.ParseError as exc:
            detail = f"page does not match card / no parseable card page: {exc}"
            save_snapshot(store, source_name="playgroup", kind="playgroup_card", url=url,
                          status="NOT_FOUND", oracle_id=oracle_id, slug=slug,
                          raw=resp.body, detail=detail)
            _set_job(store, job_type="playgroup_card_atlas", status="NOT_FOUND",
                     detail=detail, oracle_id=oracle_id, url=url)
            coverage["not_found"] += 1
            continue
        sample = fields.get("first_cast_n") or fields.get("times_brought")
        has_telemetry = "first_cast_n" in fields or "win_rates_observed" in fields
        has_any = any(k in fields for k in ("times_brought", "decks_running",
                                            "live_inclusion_pct"))
        status = "AVAILABLE" if has_telemetry else "PARTIAL"
        if not has_any and not has_telemetry:
            fields = {**fields, "note": "page exists but publishes no stats "
                                        "(below Playgroup thresholds or untracked)"}
        detail = ""
        if isinstance(sample, (int, float)) and sample < pg_mod.SMALL_SAMPLE_THRESHOLD:
            detail = f"small_sample: n={sample} below Playgroup full-chart threshold 25"
            coverage["small_sample"] += 1
        if status == "PARTIAL":
            detail = ((detail + " ") if detail else "") + "basic counts only / no telemetry charts"
        save_snapshot(store, source_name="playgroup", kind="playgroup_card", url=url,
                      status=status, oracle_id=oracle_id, slug=slug, raw=resp.body,
                      etag=resp.etag, last_modified=resp.last_modified,
                      sample_size=int(sample) if isinstance(sample, (int, float)) else None,
                      detail=detail.strip(), payload={"name": name, "fields": fields})
        _set_job(store, job_type="playgroup_card_atlas", status=status,
                 detail=detail or f"n={sample}", oracle_id=oracle_id, url=url)
        coverage["available" if status == "AVAILABLE" else "partial"] += 1
    coverage["remaining_not_fetched"] = (
        coverage["total_identities"] - coverage["cached_skipped"] - coverage["attempted"])
    return coverage


def card_atlas_coverage(store: Store, collection_id: str) -> dict:
    rows = store.conn.execute(
        "SELECT status, COUNT(*) n FROM sync_job WHERE job_type='playgroup_card_atlas' "
        "GROUP BY status").fetchall()
    total = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot WHERE collection_id=?",
        (collection_id,)).fetchone()["n"]
    by_status = {r["status"]: r["n"] for r in rows}
    return {"collection_id": collection_id, "total_identities": total,
            "jobs_by_status": by_status,
            "attempted": sum(v for k, v in by_status.items() if k != "NOT_FETCHED"),
            "note": "attempted = latest job status per collection identity; "
                    "NOT_FETCHED identities were never requested"}


def invalidate_cache(store: Store, *, source_name: str | None = None,
                     kind: str | None = None) -> dict:
    """Explicit cache invalidation (parser-version changes invalidate
    automatically by making old rows invisible to latest_snapshot)."""
    q = "SELECT snapshot_id FROM external_snapshot WHERE 1=1"
    args: list = []
    if source_name:
        q += " AND source_name=?"
        args.append(source_name)
    if kind:
        q += " AND kind=?"
        args.append(kind)
    ids = [r["snapshot_id"] for r in store.conn.execute(q, args).fetchall()]
    for snap_id in ids:
        store.conn.execute("DELETE FROM edhrec_card_stat WHERE snapshot_id=?", (snap_id,))
        store.conn.execute("DELETE FROM edhrec_deck_entry WHERE snapshot_id=?", (snap_id,))
        store.conn.execute("DELETE FROM external_snapshot WHERE snapshot_id=?", (snap_id,))
    store.conn.execute(
        "UPDATE sync_job SET status='NOT_FETCHED', detail='cache invalidated', updated_at=? "
        "WHERE job_type LIKE 'edhrec%' OR job_type LIKE 'playgroup%' "
        "OR job_type LIKE 'spellbook%'", (utcnow(),))
    store.conn.commit()
    return {"snapshots_deleted": len(ids)}


# --------------------------------------------------------------------------
# Data expansion (2026-11-11): EDHREC card pages, Commander Spellbook,
# Playgroup commander pages. Same rules as the Phase-2 adapters: public
# slugs only, snapshots with full provenance, honest statuses, stop on
# block, nothing invented.
# --------------------------------------------------------------------------

def _register_oracle_jobs(store: Store, collection_id: str, job_type: str,
                          detail: str) -> int:
    rows = store.conn.execute(
        "SELECT DISTINCT oracle_id FROM physical_lot WHERE collection_id=?",
        (collection_id,)).fetchall()
    for r in rows:
        store.conn.execute(
            "INSERT OR IGNORE INTO sync_job(job_id,job_type,oracle_id,status,detail,updated_at)"
            " VALUES(?,?,?,?,?,?)",
            (_job_id(job_type, r["oracle_id"]), job_type, r["oracle_id"],
             "NOT_FETCHED", detail, utcnow()))
    store.conn.commit()
    return len(rows)


def _collection_card_names(store: Store, collection_id: str) -> dict[str, str]:
    seen: dict[str, str] = {}
    for row in store.inventory_rows(collection_id):
        if row["name"]:
            seen.setdefault(row["oracle_id"], row["name"])
    return seen


def sync_edhrec_cards(store: Store, fetcher: Fetcher, collection_id: str, *,
                      limit: int | None = None, force: bool = False) -> dict:
    """EDHREC per-card global facts (inclusion over the whole EDHREC
    index, salt, top commanders) for every identity of a collection.
    Resumable like the Card Atlas; stops at the first BLOCKED."""
    _register_oracle_jobs(store, collection_id, "edhrec_card",
                          "data expansion: not fetched yet")
    seen = _collection_card_names(store, collection_id)
    coverage = {"collection_id": collection_id, "total_identities": len(seen),
                "attempted": 0, "cached_skipped": 0, "available": 0, "partial": 0,
                "not_found": 0, "blocked": 0, "network_errors": 0,
                "stopped_on_block": False}
    for oracle_id, name in sorted(seen.items(), key=lambda kv: kv[1]):
        existing = latest_snapshot(store, "edhrec", "edhrec_card", oracle_id=oracle_id)
        if existing is not None and not force and existing["status"] in (
                "AVAILABLE", "PARTIAL", "NOT_FOUND"):
            coverage["cached_skipped"] += 1
            continue
        if limit is not None and coverage["attempted"] >= limit:
            break
        slug = slugify(name)
        url = f"https://json.edhrec.com/pages/cards/{slug}.json"
        coverage["attempted"] += 1

        def record(status: str, detail: str, raw: bytes | None = None) -> None:
            save_snapshot(store, source_name="edhrec", kind="edhrec_card", url=url,
                          status=status, oracle_id=oracle_id, slug=slug,
                          raw=raw, detail=detail)
            _set_job(store, job_type="edhrec_card", status=status, detail=detail,
                     oracle_id=oracle_id, url=url)
            coverage[status.lower()] = coverage.get(status.lower(), 0) + 1

        try:
            resp = fetcher.get(url)
        except RobotsDisallowed as exc:
            record("BLOCKED", str(exc))
            coverage["stopped_on_block"] = True
            break
        except FetchError:
            # Transient network failure after the fetcher's retries:
            # no snapshot, the card stays NOT_FETCHED for the next run.
            coverage["network_errors"] += 1
            continue
        if resp.status in (403, 429):
            record("BLOCKED", f"HTTP {resp.status} — sync stopped, no escalation",
                   resp.body)
            coverage["stopped_on_block"] = True
            break
        if resp.status == 404:
            record("NOT_FOUND", "HTTP 404 — EDHREC has no card page for this slug")
            continue
        if resp.status != 200:
            record("BLOCKED", f"HTTP {resp.status}", resp.body)
            coverage["stopped_on_block"] = True
            break
        try:
            parsed = edhrec_card_mod.parse_card_json(
                resp.text, expected_name=name, expected_slug=slug)
        except edhrec_card_mod.VerificationError as exc:
            record("NOT_FOUND", f"slug verification failed: {exc}", resp.body)
            continue
        except edhrec_card_mod.ParseError as exc:
            record("PARTIAL", f"parse error: {exc}", resp.body)
            continue
        status = "AVAILABLE" if parsed["inclusion"] is not None else "PARTIAL"
        detail = ("global EDHREC index facts (whole-index denominator, NOT a "
                  "per-commander bracket cohort); salt is a friction "
                  "indicator, not strength")
        if parsed["salt"] is None:
            detail += "; salt not published for this card (stays NULL)"
        snap = save_snapshot(
            store, source_name="edhrec", kind="edhrec_card", url=url, status=status,
            oracle_id=oracle_id, slug=slug, raw=resp.body, etag=resp.etag,
            last_modified=resp.last_modified,
            sample_size=parsed["potential_decks"],
            captured_count=parsed["num_decks"],
            displayed_total=parsed["potential_decks"],
            coverage_status="TOTAL_KNOWN", detail=detail,
            payload={k: parsed[k] for k in
                     ("name", "top_commanders", "combo_examples",
                      "combos_page", "similar", "parser")})
        store.conn.execute("DELETE FROM edhrec_card_global WHERE snapshot_id=?", (snap,))
        store.conn.execute(
            "INSERT INTO edhrec_card_global(snapshot_id,oracle_id,scryfall_id,"
            "num_decks,potential_decks,inclusion,salt) VALUES(?,?,?,?,?,?,?)",
            (snap, oracle_id, parsed["scryfall_id"], parsed["num_decks"],
             parsed["potential_decks"], parsed["inclusion"], parsed["salt"]))
        store.conn.commit()
        _set_job(store, job_type="edhrec_card", status=status,
                 detail=f"inclusion={parsed['inclusion']} salt={parsed['salt']}",
                 oracle_id=oracle_id, url=url)
        coverage["available" if status == "AVAILABLE" else "partial"] += 1
    coverage["remaining_not_fetched"] = (
        coverage["total_identities"] - coverage["cached_skipped"] - coverage["attempted"])
    return coverage


def sync_spellbook_cards(store: Store, fetcher: Fetcher, collection_id: str, *,
                         limit: int | None = None, force: bool = False,
                         max_pages: int = 5) -> dict:
    """Commander Spellbook combos per collection card, via the public
    website (the REST API host is robots-disallowed and never touched).

    Route per card: the search page discovers the card's spellbook id
    (some searches redirect to a single combo page — used for discovery
    only); the card page then publishes the EXACT combo total and the
    top partners. Captured combos are the union of both pages plus
    further search pages while the known total is not reached (bounded
    by max_pages). Stops at the first BLOCKED."""
    _register_oracle_jobs(store, collection_id, "spellbook_card",
                          "data expansion: not fetched yet")
    seen = _collection_card_names(store, collection_id)
    coverage = {"collection_id": collection_id, "total_identities": len(seen),
                "attempted": 0, "cached_skipped": 0, "available": 0, "partial": 0,
                "not_found": 0, "blocked": 0, "combos_captured": 0,
                "combos_total_known": 0, "network_errors": 0,
                "stopped_on_block": False}
    for oracle_id, name in sorted(seen.items(), key=lambda kv: kv[1]):
        slug = slugify(name)
        existing = latest_snapshot(store, "commanderspellbook", "spellbook_card",
                                   oracle_id=oracle_id)
        if existing is not None and not force and existing["status"] in (
                "AVAILABLE", "PARTIAL", "NOT_FOUND"):
            coverage["cached_skipped"] += 1
            continue
        if limit is not None and coverage["attempted"] >= limit:
            break
        coverage["attempted"] += 1
        first_url = spellbook_mod.search_url(name, 1)
        combos: dict[str, dict] = {}
        total: int | None = None
        partners: list[dict] = []
        card_sid: int | None = None
        if existing is not None and existing["payload_json"]:
            try:
                card_sid = json.loads(existing["payload_json"]).get(
                    "spellbook_card_id")
            except (json.JSONDecodeError, AttributeError):
                card_sid = None
        search_exhausted = False
        search_pages = 0
        failure: tuple[str, str, bytes | None] | None = None

        def fetch(url: str):
            """(response, failure) — failure is a (status, detail, raw)
            triple for terminal HTTP/robots outcomes. A transient
            network error (after the fetcher's own retries) yields the
            pseudo-status NETWORK: the card is abandoned WITHOUT a
            snapshot, so it stays NOT_FETCHED for the next run."""
            try:
                resp = fetcher.get(url)
            except RobotsDisallowed as exc:
                return None, ("BLOCKED", str(exc), None)
            except FetchError as exc:
                return None, ("NETWORK", str(exc), None)
            if resp.status in (403, 429):
                return None, ("BLOCKED", f"HTTP {resp.status} — sync stopped, "
                                          "no escalation", resp.body)
            if resp.status != 200:
                return None, ("BLOCKED", f"HTTP {resp.status}", resp.body)
            return resp, None

        def absorb(views) -> None:
            for view in views or []:
                if view["combo_id"]:
                    combos.setdefault(view["combo_id"], view)

        # 1) Discovery via the search route (skipped when the spellbook
        #    id is already known from an earlier snapshot).
        if card_sid is None:
            resp, failure = fetch(first_url)
            if failure is None:
                route = spellbook_mod.payload_page(resp.text)
                if route == "/combo/[id]":
                    try:
                        found = spellbook_mod.parse_combo_page(resp.text,
                                                               card_name=name)
                        if found["combo"] is not None:
                            absorb([found["combo"]])
                        card_sid = found["spellbook_card_id"]
                        search_exhausted = True  # search route unusable
                    except spellbook_mod.ParseError as exc:
                        failure = ("PARTIAL", f"parse error: {exc}", resp.body)
                elif route == "/search":
                    try:
                        parsed = spellbook_mod.parse_search_page(resp.text,
                                                                 card_name=name)
                    except spellbook_mod.VerificationError as exc:
                        failure = ("NOT_FOUND", f"page verification failed: "
                                                f"{exc}", resp.body)
                    except spellbook_mod.ParseError as exc:
                        failure = ("PARTIAL", f"parse error: {exc}", resp.body)
                    else:
                        absorb(parsed["combos"])
                        card_sid = parsed["spellbook_card_id"]
                        search_pages = 1
                        search_exhausted = parsed["raw_count"] < spellbook_mod.PAGE_SIZE
                else:
                    failure = ("PARTIAL", f"unexpected spellbook page route "
                                          f"{route!r}", resp.body)
        # 2) The card page: exact total + top partners + top combos.
        if failure is None and card_sid is not None:
            resp, card_failure = fetch(spellbook_mod.card_url(card_sid))
            if card_failure is not None and card_failure[0] in (
                    "BLOCKED", "NETWORK"):
                failure = card_failure
            elif card_failure is None:
                try:
                    parsed_card = spellbook_mod.parse_card_page(resp.text,
                                                                card_name=name)
                except (spellbook_mod.ParseError,
                        spellbook_mod.VerificationError) as exc:
                    failure = ("PARTIAL", f"card page parse error: {exc}",
                               resp.body)
                else:
                    total = parsed_card["combos_total"]
                    partners = parsed_card["partners"]
                    absorb(parsed_card["combos"])
        # 3) Enrich the combo list via further search pages while a
        #    known total is unreached (or the total is unknown and the
        #    search is not exhausted), bounded by max_pages.
        while (failure is None and not search_exhausted
               and search_pages >= 1 and search_pages < max_pages
               and (total is None or len(combos) < total)):
            resp, page_failure = fetch(spellbook_mod.search_url(
                name, search_pages + 1))
            if page_failure is not None:
                failure = page_failure
                break
            try:
                parsed = spellbook_mod.parse_search_page(resp.text,
                                                         card_name=name)
            except (spellbook_mod.ParseError,
                    spellbook_mod.VerificationError) as exc:
                failure = ("PARTIAL", f"parse error: {exc}", resp.body)
                break
            absorb(parsed["combos"])
            search_pages += 1
            search_exhausted = parsed["raw_count"] < spellbook_mod.PAGE_SIZE

        if failure is not None and failure[0] == "NETWORK":
            coverage["network_errors"] += 1
            continue
        if failure is not None:
            status, detail, raw = failure
            save_snapshot(store, source_name="commanderspellbook",
                          kind="spellbook_card", url=first_url, status=status,
                          oracle_id=oracle_id, slug=slug, raw=raw, detail=detail,
                          payload={"spellbook_card_id": card_sid}
                          if card_sid else None)
            _set_job(store, job_type="spellbook_card", status=status,
                     detail=detail, oracle_id=oracle_id, url=first_url)
            coverage[status.lower()] += 1
            if status == "BLOCKED":
                coverage["stopped_on_block"] = True
                break
            continue
        if not combos and not total:
            detail = ("spellbook lists no commander-legal combo using this "
                      "card (verified exact-name uses filter; card page "
                      "total is 0 or no result page exists)")
            save_snapshot(store, source_name="commanderspellbook",
                          kind="spellbook_card", url=first_url, status="NOT_FOUND",
                          oracle_id=oracle_id, slug=slug, detail=detail,
                          captured_count=0,
                          coverage_status="TOTAL_KNOWN" if total == 0
                          else "TOTAL_UNKNOWN",
                          displayed_total=total,
                          payload={"spellbook_card_id": card_sid}
                          if card_sid else None)
            _set_job(store, job_type="spellbook_card", status="NOT_FOUND",
                     detail=detail, oracle_id=oracle_id, url=first_url)
            coverage["not_found"] += 1
            continue
        complete = total is not None or search_exhausted
        status = "AVAILABLE" if complete else "PARTIAL"
        if total is not None:
            detail = (f"{len(combos)} of {total} commander-legal combos "
                      "captured (card page total is exact; list = top "
                      "combos by popularity + search pages)")
            coverage["combos_total_known"] += total
        else:
            detail = (f"{len(combos)} combos captured; the search route "
                      "publishes no grand total"
                      + (" (search exhausted)" if search_exhausted else
                         f"; page cap {max_pages} reached, total unknown"))
        snap = save_snapshot(
            store, source_name="commanderspellbook", kind="spellbook_card",
            url=first_url, status=status, oracle_id=oracle_id, slug=slug,
            captured_count=len(combos), displayed_total=total,
            coverage_status="TOTAL_KNOWN" if total is not None else (
                "CAPTURED_COMPLETE" if complete else "TOTAL_UNKNOWN"),
            detail=detail,
            payload={"name": name, "combo_count": len(combos),
                     "combos_total": total, "partners": partners,
                     "spellbook_card_id": card_sid,
                     "parser": spellbook_mod.PARSER_ID})
        store.conn.execute("DELETE FROM spellbook_combo WHERE snapshot_id=?", (snap,))
        for combo in combos.values():
            store.conn.execute(
                "INSERT OR REPLACE INTO spellbook_combo(snapshot_id,combo_id,"
                "card_oracle_ids_json,card_names_json,produces_json,price_eur,"
                "price_usd,popularity,mana_value_needed) VALUES(?,?,?,?,?,?,?,?,?)",
                (snap, combo["combo_id"],
                 json.dumps(combo["card_oracle_ids"], ensure_ascii=False),
                 json.dumps(combo["card_names"], ensure_ascii=False),
                 json.dumps(combo["produces"], ensure_ascii=False),
                 combo["price_eur"], combo["price_usd"], combo["popularity"],
                 combo["mana_value_needed"]))
        store.conn.commit()
        _set_job(store, job_type="spellbook_card", status=status, detail=detail,
                 oracle_id=oracle_id, url=first_url)
        coverage["available" if status == "AVAILABLE" else "partial"] += 1
        coverage["combos_captured"] += len(combos)
    coverage["remaining_not_fetched"] = (
        coverage["total_identities"] - coverage["cached_skipped"] - coverage["attempted"])
    return coverage


def sync_playgroup_commander_page(store: Store, fetcher: Fetcher, *, name: str,
                                  commander_oracle_id: str | None = None,
                                  force: bool = False) -> dict:
    """The Playgroup commander HTML page: win conditions, seat/mulligan
    win rates, matchups and win-lift staples — the sections the public
    JSON does not offer (see playgroup.parse_commander_page)."""
    existing = latest_snapshot(store, "playgroup", "playgroup_commander_page",
                               commander_oracle_id=commander_oracle_id,
                               slug=slugify(name))
    if existing is not None and not force and existing["status"] == "AVAILABLE":
        return {**_result(existing), "cached": True}
    try:
        resolved = resolve_playgroup_commander(fetcher, name)
    except RobotsDisallowed as exc:
        snap = save_snapshot(store, source_name="playgroup",
                             kind="playgroup_commander_page",
                             url=PG_AUTOCOMPLETE + quote_plus(front_name(name)),
                             status="BLOCKED",
                             commander_oracle_id=commander_oracle_id,
                             slug=slugify(name), detail=str(exc))
        return {"snapshot_id": snap, "status": "BLOCKED", "detail": str(exc)}
    if resolved is None:
        detail = ("UNRESOLVED: Playgroup autocomplete has no exact-label "
                  "match; page URL not guessed")
        snap = save_snapshot(store, source_name="playgroup",
                             kind="playgroup_commander_page",
                             url=PG_AUTOCOMPLETE + quote_plus(front_name(name)),
                             status="NOT_FOUND",
                             commander_oracle_id=commander_oracle_id,
                             slug=slugify(name), detail=detail)
        return {"snapshot_id": snap, "status": "NOT_FOUND", "detail": detail}
    page_url = resolved["url"]
    try:
        resp = fetcher.get(page_url)
    except RobotsDisallowed as exc:
        snap = save_snapshot(store, source_name="playgroup",
                             kind="playgroup_commander_page", url=page_url,
                             status="BLOCKED",
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"], detail=str(exc))
        return {"snapshot_id": snap, "status": "BLOCKED", "detail": str(exc)}
    if resp.status != 200:
        status = "NOT_FOUND" if resp.status == 404 else (
            "BLOCKED" if resp.status in (403, 429) else "PARTIAL")
        snap = save_snapshot(store, source_name="playgroup",
                             kind="playgroup_commander_page", url=page_url,
                             status=status, raw=resp.body,
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"],
                             detail=f"HTTP {resp.status} from commander page")
        return {"snapshot_id": snap, "status": status,
                "detail": f"HTTP {resp.status}"}
    try:
        parsed = pg_mod.parse_commander_page(resp.text, expected_name=name)
    except pg_mod.ParseError as exc:
        snap = save_snapshot(store, source_name="playgroup",
                             kind="playgroup_commander_page", url=page_url,
                             status="PARTIAL", raw=resp.body,
                             commander_oracle_id=commander_oracle_id,
                             slug=resolved["slug"],
                             detail=f"parse error: {exc}")
        return {"snapshot_id": snap, "status": "PARTIAL",
                "detail": f"parse error: {exc}"}
    sections = [k for k in ("win_conditions", "seat_win_rates",
                            "mulligan_win_rates", "win_staples")
                if parsed[k]]
    if parsed["matchups"]["best"] or parsed["matchups"]["worst"]:
        sections.append("matchups")
    detail = ("page sections captured: " + (", ".join(sections) or "none")
              + "; absent: " + "; ".join(parsed["absent_from_page"]))
    snap = save_snapshot(store, source_name="playgroup",
                         kind="playgroup_commander_page", url=page_url,
                         status="AVAILABLE", raw=resp.body, etag=resp.etag,
                         last_modified=resp.last_modified,
                         commander_oracle_id=commander_oracle_id,
                         slug=resolved["slug"], detail=detail, payload=parsed)
    store.conn.execute(
        "DELETE FROM playgroup_commander_staple WHERE snapshot_id=?", (snap,))
    for staple in parsed["win_staples"]:
        rows = store.conn.execute(
            "SELECT DISTINCT oracle_id FROM scryfall_card WHERE front_name=? "
            "OR name=?", (staple["name"], staple["name"])).fetchall()
        card_oracle = rows[0]["oracle_id"] if len(rows) == 1 else None
        store.conn.execute(
            "INSERT OR REPLACE INTO playgroup_commander_staple(snapshot_id,"
            "card_name,card_oracle_id,games,lift_pp) VALUES(?,?,?,?,?)",
            (snap, staple["name"], card_oracle,
             staple["games"], staple["lift_pp"]))
    store.conn.commit()
    return {"snapshot_id": snap, "status": "AVAILABLE", "source_url": page_url,
            "playgroup_id": resolved["playgroup_id"], "sections": sections,
            "win_staples": len(parsed["win_staples"]),
            "matchups": {k: len(v) for k, v in parsed["matchups"].items()
                         if isinstance(v, list)}}
