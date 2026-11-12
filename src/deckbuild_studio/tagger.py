"""Scryfall Tagger layer — functional tags via official Scryfall routes.

Two official routes carry the Tagger's functional tags:

* **Bulk download (primary since 2026-11-12).** The official
  bulk-data API (https://api.scryfall.com/bulk-data) publishes
  ``oracle_tags``: the complete Tagger oracle-tag graph — every tag
  with label, aliases, hierarchy (parent/child ids) and its card
  taggings. This corrects the project's earlier finding that the
  Tagger was only reachable through an undocumented GraphQL endpoint
  (that endpoint is still never used). A functional tag's set is its
  SUBTREE union (the tag plus all descendants); verified 2026-11-12
  for the whole vocabulary: every Search-API result set is a subset
  of the corresponding bulk subtree (the bulk is the fresher
  source). See :func:`sync_tagger_bulk`.
* **Search API (fallback / cross-check).** The documented Search API
  (https://scryfall.com/docs/api/cards/search) with the ``function:``
  operator returns the same sets per tag:

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

TAGGER_VERSION = "scryfall-tagger-search/1.2.0"  # 1.2.0 (2026-11-12):
# vocabulary extended by taxonomy 1.1.0 (counted census of the whole
# oracle_tags bulk, docs/TAXONOMY_EXTENSION.md): the six new
# categories' tags join the vocabulary, and evasion gains the
# additional grant tag 'gives-evasion' (see VOCABULARY).
# 1.1.0 (2026-11-12): vocabulary corrected against the live API —
# card_selection syncs the tag that actually exists for it ('loot';
# 'card-selection' 404s), and stax gains the additional subset tag
# 'hatebear' (see VOCABULARY).
# All other tags unchanged; old snapshots stay as history.
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

# Additional subset tag (the single deliberate exception to one tag
# per category): there is NO generic 'stax' tag in the Search API
# (404; 'tax' is a broad pay-or-else mechanic set, 'lockdown' mixes
# prison pieces with pacifism auras — both probed 2026-11-12 and
# rejected as category mappings). 'hatebear' (66 cards) is the
# precisely-scoped creature subset of the stax function — small
# creatures with a hate effect (Thalia, Drannith Magistrate,
# Collector Ouphe ...). Its claims are stored under their real tag
# name, so provenance never pretends full stax coverage: the tag
# covers the creature slice of the category only.
VOCABULARY["hatebear"] = "stax"

# Second deliberate additional tag (taxonomy 1.1.0): 'gives evasion'
# (1,217 cards globally) is the grant side of the evasion function —
# cards that GIVE a creature evasion (auras, equipment, anthems of
# flight) perform the same deckbuilding function as cards that have
# evasion, but sit outside the 'evasion' tag's own set (counted
# 2026-11-12: 38 collection cards, 27 of them beyond the base tag,
# 11 in both). Its claims are stored under their real tag name, so
# provenance keeps the two halves of the category distinguishable.
VOCABULARY["gives-evasion"] = "evasion"

# Tags whose live probe (2026-11-12) answered 404: the tag does not
# exist (or is empty) in the Search API. They stay in the vocabulary
# so every sync re-checks them and reports NOT_FOUND honestly instead
# of the category silently losing its external layer. ('card-selection'
# left the vocabulary in 1.1.0: the category now syncs 'loot'.)
KNOWN_MISSING_TAGS = ("stax", "token")


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
                   captured: int, detail: str, payload: dict | None,
                   version: str = TAGGER_VERSION,
                   source_label: str = ("Scryfall Tagger (official Search "
                                        "API, function: tags)")) -> str:
    """Snapshot row for one tag, same shape/provenance discipline as
    external.save_snapshot, but stamped with the route's version."""
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
         version, sha, None, None, utcnow(), None, captured, total,
         status, detail, raw_path,
         json.dumps(payload, ensure_ascii=False) if payload is not None else None))
    store.add_source(
        source_id=f"src-{snap_id}",
        source_name=source_label,
        source_url=url, sha256=sha, data_status=status,
        note=f"tagger tag {tag} -> category {category}; parser {version}",
        parser_version=version)
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
    return _mirror_and_record(store, results, store_ids,
                              version=TAGGER_VERSION, layer="tagger_search",
                              full_run=tags is None)


def _mirror_and_record(store: Store, results: dict[str, dict],
                       store_ids: set[str], *, version: str, layer: str,
                       full_run: bool) -> dict:
    """Shared tail of both Tagger routes: re-mirror card_tagger_claim
    into card_role under the tagger origin, and — only for a complete
    vocabulary run with no BLOCKED/PARTIAL tag — record 'examined'
    rows for every store card."""
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
    clean = all(r["status"] in ("AVAILABLE", "NOT_FOUND")
                for r in results.values())
    if full_run and clean:
        categories.record_checks(
            store, origin=roles_mod.ORIGIN_TAGGER, version=version,
            claims_by_card={oid: claim_counts.get(oid, 0) for oid in store_ids})
        store.conn.commit()
    run_status = "AVAILABLE" if (full_run and clean) else "PARTIAL"
    run_id = categories.write_run(
        store, layer=layer, version=version, source_id=None,
        status=run_status, cards_total=len(store_ids),
        cards_covered=len(store_ids) if (full_run and clean) else len(claim_counts),
        detail="; ".join(f"{t}:{r['status']}" for t, r in results.items()))
    store.conn.commit()
    return {"run_id": run_id, "run_status": run_status,
            "tags": results, "cards_with_claims": len(claim_counts),
            "claims_total": sum(claim_counts.values()),
            "checks_recorded": bool(full_run and clean)}


# ---------------------------------------------------------------------------
# Bulk route: the official oracle_tags download (primary since 2026-11-12)
# ---------------------------------------------------------------------------

TAGGER_BULK_VERSION = "scryfall-tagger-bulk/1.1.0"  # 1.1.0
# (2026-11-12): vocabulary of taxonomy 1.1.0 (six new categories,
# 'gives-evasion' additional tag — see TAGGER_VERSION note).
BULK_SOURCE_LABEL = "Scryfall Tagger (official bulk download, oracle_tags)"
BULK_INDEX_URL = API_BASE + "/bulk-data"

# Search-API function names that are neither the bulk tag's label nor
# one of its aliases (verified against the 2026-11-12 bulk file): the
# API's own synonym for the Tagger label on the right.
BULK_ROOT_OVERRIDES = {"board-wipe": "sweeper"}


def _bulk_key(text: str) -> str:
    """Slug-normal form used by the Search API's function names:
    lowercase, spaces become hyphens ('mana rock' -> 'mana-rock')."""
    return text.lower().replace(" ", "-")


class OracleTagsBulk:
    """A parsed oracle_tags bulk file: the full Tagger tag graph."""

    def __init__(self, records: list[dict]):
        self._by_id = {r["id"]: r for r in records}
        self._resolver: dict[str, dict] = {}
        for rec in records:
            self._resolver.setdefault(_bulk_key(rec["label"]), rec)
            for alias in rec.get("aliases") or []:
                self._resolver.setdefault(_bulk_key(alias), rec)
        self.tag_count = len(records)

    def resolve(self, tag: str) -> dict | None:
        """The tag record a function name denotes: its label or alias
        (slug-normalised), with BULK_ROOT_OVERRIDES applied first."""
        return self._resolver.get(_bulk_key(BULK_ROOT_OVERRIDES.get(tag, tag)))

    def subtree(self, root: dict) -> tuple[set[str], int]:
        """(oracle ids, tag count) of the root tag plus all its
        descendant tags — the set the Search API's function: operator
        returns for the root's name."""
        seen: set[str] = set()
        stack = [root]
        ids: set[str] = set()
        while stack:
            node = stack.pop()
            if node["id"] in seen:
                continue
            seen.add(node["id"])
            for tagging in node.get("taggings") or []:
                oid = tagging.get("oracle_id")
                if oid:
                    ids.add(str(oid))
            for child_id in node.get("child_ids") or []:
                child = self._by_id.get(child_id)
                if child is not None:
                    stack.append(child)
        return ids, len(seen)


def load_oracle_tags(path) -> OracleTagsBulk:
    records = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return OracleTagsBulk(records)


def bulk_file_meta(path, *, download_uri: str | None = None,
                   updated_at: str | None = None) -> dict:
    raw = Path(path).read_bytes()
    return {"download_uri": download_uri, "updated_at": updated_at,
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "local_file": str(path)}


def download_oracle_tags(target_dir) -> tuple[Path, dict]:
    """Download the current oracle_tags bulk file via the official
    bulk-data index (two GETs: the index, then the file). Stores it
    as ``oracle-tags.jsonl.gz`` in target_dir; returns (path, meta)."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        BULK_INDEX_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        index = json.loads(resp.read())
    entry = next((e for e in index.get("data") or []
                  if e.get("type") == "oracle_tags"), None)
    if entry is None or not entry.get("jsonl_download_uri"):
        raise TaggerBlocked("bulk-data index lists no oracle_tags download")
    req = urllib.request.Request(entry["jsonl_download_uri"],
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read()
    path = target_dir / "oracle-tags.jsonl.gz"
    path.write_bytes(raw)
    return path, {"download_uri": entry["jsonl_download_uri"],
                  "updated_at": entry.get("updated_at"),
                  "sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw), "local_file": str(path)}


def sync_tagger_bulk(store: Store, *, bulk_path, bulk_meta: dict,
                     tags: list[str] | None = None) -> dict:
    """Sync Tagger membership from a local oracle_tags bulk file.

    Same claim/check discipline as the Search-API route: one snapshot
    per tag (stamped TAGGER_BULK_VERSION; the raw body is the bulk
    file itself, stored once — the snapshots folder deduplicates by
    SHA-256), claims replaced per tag only when the tag resolves,
    card_role re-mirrored, 'examined' rows only on a complete clean
    run. A vocabulary tag with no label/alias in the bulk is honestly
    NOT_FOUND — the generic 'stax' and 'token' tags exist in neither
    the bulk graph nor the Search API."""
    categories.ensure_schema(store)
    roles_mod.ensure_schema(store)
    bulk = load_oracle_tags(bulk_path)
    bulk_raw = Path(bulk_path).read_bytes()
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
        root = bulk.resolve(tag)
        if root is None:
            # The consulted source is the bulk file itself; the #tag=
            # anchor keeps each missing tag's snapshot URL (and thus
            # its snapshot id) distinct from the other missing tags.
            snap_id = _save_snapshot(
                store, tag=tag, category=category,
                url=(f"{bulk_meta.get('download_uri') or bulk_meta['local_file']}"
                     f"#tag={tag}"),
                status="NOT_FOUND", raw_pages=[bulk_raw], total=None,
                captured=0,
                detail=(f"no tag labelled or aliased {tag!r} in the "
                        f"oracle_tags bulk (updated "
                        f"{bulk_meta.get('updated_at')}, sha256 "
                        f"{bulk_meta['sha256'][:12]}…)"),
                payload=None, version=TAGGER_BULK_VERSION,
                source_label=BULK_SOURCE_LABEL)
            results[tag] = {"tag": tag, "category": category,
                            "status": "NOT_FOUND", "total_cards": None,
                            "pages": 0, "claims": 0, "snapshot_id": snap_id,
                            "detail": "tag absent from oracle_tags bulk"}
            continue
        ids, subtree_tags = bulk.subtree(root)
        in_store = sorted(ids & store_ids)
        payload_doc = {"tag": tag, "category": category,
                       "oracle_ids": sorted(ids),
                       "root_label": root["label"],
                       "subtree_tags": subtree_tags, "bulk": bulk_meta}
        snap_id = _save_snapshot(
            store, tag=tag, category=category, url=root["uri"],
            status="AVAILABLE", raw_pages=[bulk_raw], total=len(ids),
            captured=len(in_store),
            detail=(f"bulk subtree of {root['label']!r} "
                    f"({subtree_tags} tags); result_ids={len(ids)}; "
                    f"in_store={len(in_store)}; "
                    f"outside_store={len(ids) - len(in_store)}; "
                    f"bulk updated {bulk_meta.get('updated_at')}"),
            payload=payload_doc, version=TAGGER_BULK_VERSION,
            source_label=BULK_SOURCE_LABEL)
        _replace_claims(store, tag, category, in_store, snap_id)
        results[tag] = {"tag": tag, "category": category,
                        "status": "AVAILABLE", "total_cards": len(ids),
                        "pages": 0, "claims": len(in_store),
                        "snapshot_id": snap_id,
                        "detail": f"root {root['label']!r}, "
                                  f"{subtree_tags} subtree tags"}
    return _mirror_and_record(store, results, store_ids,
                              version=TAGGER_BULK_VERSION,
                              layer="tagger_bulk", full_run=tags is None)
