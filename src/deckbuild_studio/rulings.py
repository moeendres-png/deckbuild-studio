"""Scryfall rulings layer — official card rulings from the bulk export.

Source: Scryfall's official bulk-data index
(https://api.scryfall.com/bulk-data), file type ``rulings`` — one JSON
object per ruling (``oracle_id``, ``source`` = ``wotc`` | ``scryfall``,
``published_at``, ``comment``), shipped as gzipped JSONL (~5 MB) and
regenerated roughly every 12 h. The download URI is NEVER hardcoded:
the index is read first and its current ``jsonl_download_uri`` (legacy
fallback: ``download_uri``) is used, exactly like
:func:`deckbuild_studio.scryfall.sync_scryfall`.

Storage follows the project snapshot model: one ``external_snapshot``
row (source ``scryfall``, kind ``scryfall_rulings``) carries URL, fetch
time, SHA-256 of the downloaded file, parser id and the bulk file's own
``updated_at``; the rulings themselves land normalized in
``card_ruling`` under that snapshot. A re-run whose index
``updated_at`` matches the stored snapshot skips the download (the
sync is idempotent; ``--force`` overrides). Malformed lines are
COUNTED, never silently dropped: any skipped line turns the snapshot
PARTIAL with the counts in its detail text. A card without rulings is
a normal outcome (empty list) — rulings are never invented.

Rulings are rules clarifications (context for the card drawer), not a
strength signal; they feed no score anywhere.
"""
from __future__ import annotations

import gzip
import hashlib
import json

from .external import latest_snapshot, save_snapshot
from .httpfetch import Fetcher, FetchError, RobotsDisallowed
from .store import Store

PARSER_ID = "scryfall-rulings/1.0.0"
SOURCE_NAME = "scryfall"
KIND = "scryfall_rulings"
BULK_INDEX_URL = "https://api.scryfall.com/bulk-data"
BULK_TYPE = "rulings"
_GZIP_MAGIC = b"\x1f\x8b"


class RulingsError(Exception):
    """Terminal sync failure the caller should surface (e.g. transient
    network error after the fetcher's retries — no snapshot is written,
    the layer stays NOT_FETCHED and a later run retries)."""


class ParseError(Exception):
    """The bulk index or file could not be parsed at all."""


def find_rulings_entry(index: dict) -> dict | None:
    """The ``rulings`` entry of a bulk-data index document, or None."""
    for entry in index.get("data") or []:
        if isinstance(entry, dict) and entry.get("type") == BULK_TYPE:
            return entry
    return None


def parse_rulings_body(body: bytes) -> tuple[list[dict], dict]:
    """Parse one rulings bulk file body (gzipped or plain JSONL).

    Returns ``(rows, stats)``; rows are normalized dicts with
    ``oracle_id`` / ``source`` / ``published_at`` / ``comment``.
    Malformed lines and lines missing a required field are counted in
    ``stats`` — never silently dropped. A body that is neither valid
    gzip (when it carries the gzip magic) nor UTF-8 text yields zero
    rows and ``stats['unreadable'] = True``."""
    stats = {"lines": 0, "malformed": 0, "missing_fields": 0,
             "unreadable": False}
    if body[:2] == _GZIP_MAGIC:
        try:
            raw = gzip.decompress(body)
        except OSError:
            stats["unreadable"] = True
            return [], stats
    else:
        raw = body
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        stats["unreadable"] = True
        return [], stats
    rows: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        stats["lines"] += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            stats["malformed"] += 1
            continue
        if not isinstance(obj, dict):
            stats["malformed"] += 1
            continue
        oracle_id = obj.get("oracle_id")
        comment = obj.get("comment")
        if not oracle_id or not isinstance(comment, str) or not comment:
            stats["missing_fields"] += 1
            continue
        rows.append({
            "oracle_id": str(oracle_id),
            "source": str(obj.get("source") or "unknown"),
            "published_at": (str(obj["published_at"])
                             if obj.get("published_at") else None),
            "comment": comment,
        })
    return rows, stats


def _ruling_key(row: dict) -> str:
    material = "|".join((row["oracle_id"], row["source"],
                         row["published_at"] or "", row["comment"]))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def sync_rulings(store: Store, fetcher: Fetcher, *,
                 collection_id: str = "foundation-schwarze-box",
                 force: bool = False) -> dict:
    """Download + store the Scryfall rulings bulk file (snapshot model).

    Result dict carries the honest status: AVAILABLE (file parsed
    cleanly), PARTIAL (lines skipped / file unreadable), BLOCKED
    (robots / HTTP 403 / 429 / other HTTP error / index without a
    rulings entry), NOT_FOUND (bulk file URL answers 404). A transient
    network failure raises :class:`RulingsError` and writes NOTHING —
    the layer stays NOT_FETCHED for the next run."""
    def record(status: str, detail: str, url: str,
               raw: bytes | None = None) -> dict:
        snap = save_snapshot(store, source_name=SOURCE_NAME, kind=KIND,
                             url=url, status=status, raw=raw, detail=detail,
                             payload={"parser": PARSER_ID})
        return {"snapshot_id": snap, "status": status, "source_url": url,
                "detail": detail}

    try:
        index_resp = fetcher.get(BULK_INDEX_URL)
    except RobotsDisallowed as exc:
        return record("BLOCKED", str(exc), BULK_INDEX_URL)
    except FetchError as exc:
        raise RulingsError(f"bulk index fetch failed: {exc}") from exc
    if index_resp.status in (403, 429):
        return record("BLOCKED", f"HTTP {index_resp.status} on bulk index",
                      BULK_INDEX_URL, index_resp.body)
    if index_resp.status != 200:
        return record("BLOCKED", f"HTTP {index_resp.status} on bulk index",
                      BULK_INDEX_URL, index_resp.body)
    try:
        index = json.loads(index_resp.text)
    except json.JSONDecodeError as exc:
        return record("BLOCKED", f"bulk index is not valid JSON: {exc}",
                      BULK_INDEX_URL, index_resp.body)
    entry = find_rulings_entry(index)
    if entry is None:
        return record("BLOCKED", "bulk index carries no 'rulings' entry",
                      BULK_INDEX_URL, index_resp.body)
    uri = entry.get("jsonl_download_uri") or entry.get("download_uri")
    if not uri:
        return record("BLOCKED", "rulings entry carries neither "
                                 "jsonl_download_uri nor download_uri",
                      BULK_INDEX_URL, index_resp.body)
    bulk_updated_at = entry.get("updated_at")

    existing = latest_snapshot(store, SOURCE_NAME, KIND)
    if existing is not None and not force and existing["status"] == "AVAILABLE":
        try:
            old_payload = json.loads(existing["payload_json"] or "{}")
        except json.JSONDecodeError:
            old_payload = {}
        if bulk_updated_at and old_payload.get("bulk_updated_at") == bulk_updated_at:
            return {"snapshot_id": existing["snapshot_id"], "status": "AVAILABLE",
                    "cached": True, "bulk_updated_at": bulk_updated_at,
                    "detail": "bulk file unchanged since the stored snapshot "
                              "(index updated_at match); download skipped"}

    try:
        resp = fetcher.get(uri)
    except RobotsDisallowed as exc:
        return record("BLOCKED", str(exc), uri)
    except FetchError as exc:
        raise RulingsError(f"rulings download failed: {exc}") from exc
    if resp.status in (403, 429):
        return record("BLOCKED", f"HTTP {resp.status} — no escalation", uri,
                      resp.body)
    if resp.status == 404:
        return record("NOT_FOUND", "HTTP 404 — bulk file URL from the index "
                                   "does not resolve", uri, resp.body)
    if resp.status != 200:
        return record("BLOCKED", f"HTTP {resp.status}", uri, resp.body)

    rows, stats = parse_rulings_body(resp.body)
    skipped = stats["malformed"] + stats["missing_fields"]
    if stats["unreadable"]:
        status = "PARTIAL"
        detail = ("downloaded file is unreadable (gzip/UTF-8 decode "
                  "failed); 0 rulings stored — file kept as snapshot raw "
                  "for diagnosis")
    elif skipped:
        status = "PARTIAL"
        detail = (f"{len(rows)} rulings stored; {skipped} lines skipped "
                  f"({stats['malformed']} malformed JSON, "
                  f"{stats['missing_fields']} missing oracle_id/comment)")
    else:
        status = "AVAILABLE"
        detail = f"{len(rows)} rulings stored, file parsed cleanly"
    by_source: dict[str, int] = {}
    for row in rows:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
    distinct_oracles = len({r["oracle_id"] for r in rows})
    snap = save_snapshot(
        store, source_name=SOURCE_NAME, kind=KIND, url=uri, status=status,
        raw=resp.body, etag=resp.etag, last_modified=resp.last_modified,
        sample_size=len(rows), captured_count=len(rows),
        coverage_status="TOTAL_KNOWN" if status == "AVAILABLE" else "PARTIAL",
        detail=detail,
        payload={"parser": PARSER_ID, "bulk_updated_at": bulk_updated_at,
                 "total_rulings": len(rows), "by_source": by_source,
                 "distinct_oracle_ids": distinct_oracles,
                 "lines": stats["lines"], "malformed": stats["malformed"],
                 "missing_fields": stats["missing_fields"],
                 "unreadable": stats["unreadable"]})
    store.conn.execute("DELETE FROM card_ruling WHERE snapshot_id=?", (snap,))
    store.conn.executemany(
        "INSERT OR IGNORE INTO card_ruling(snapshot_id,ruling_key,oracle_id,"
        "source,published_at,comment) VALUES(?,?,?,?,?,?)",
        [(snap, _ruling_key(r), r["oracle_id"], r["source"],
          r["published_at"], r["comment"]) for r in rows])
    store.conn.commit()
    return {"snapshot_id": snap, "status": status, "source_url": uri,
            "detail": detail, "bulk_updated_at": bulk_updated_at,
            "total_rulings": len(rows), "by_source": by_source,
            "distinct_oracle_ids": distinct_oracles,
            "collection": rulings_coverage(store, collection_id)}


def rulings_coverage(store: Store, collection_id: str) -> dict:
    """Collection coverage of the LATEST rulings snapshot: how many of
    the collection's identities carry >= 1 stored ruling."""
    total = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"collection_id": collection_id, "total_identities": total,
                "status": "NOT_FETCHED", "with_rulings": 0,
                "rulings_total": 0}
    row = store.conn.execute(
        "SELECT COUNT(DISTINCT r.oracle_id) covered, COUNT(*) rulings "
        "FROM card_ruling r JOIN physical_lot l ON l.oracle_id = r.oracle_id "
        "WHERE r.snapshot_id=? AND l.collection_id=?",
        (snap["snapshot_id"], collection_id)).fetchone()
    return {"collection_id": collection_id, "total_identities": total,
            "status": snap["status"], "with_rulings": row["covered"],
            "rulings_total": row["rulings"],
            "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"]}


def card_rulings(store: Store, oracle_id: str) -> dict:
    """Rulings of one card from the latest snapshot (card-drawer API).

    ``status`` is NOT_FETCHED until a sync ran; a synced card without
    rulings answers AVAILABLE/PARTIAL (the snapshot's status) with an
    empty item list — 'no rulings published' is data, not an error."""
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"status": "NOT_FETCHED", "items": []}
    items = [dict(r) for r in store.conn.execute(
        "SELECT source, published_at, comment FROM card_ruling "
        "WHERE snapshot_id=? AND oracle_id=? "
        "ORDER BY published_at DESC, comment",
        (snap["snapshot_id"], oracle_id))]
    return {"status": snap["status"], "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"], "items": items}
