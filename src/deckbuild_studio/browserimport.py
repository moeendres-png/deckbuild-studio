"""Import of browser-harvested deck lists (decklists_browser.jsonl).

The browser harvest tool (``browser_deck_harvest.py``, see its README)
drives the owner's own Chromium session over deck pages whose
operators offer no usable API — EDHREC's ``/deckpreview/`` is
robots-disallowed for crawlers and Moxfield's API is
robots-disallowed outright — and writes the FULL deck lists it
rendered to a JSONL file: one record per deck with ``source``,
``source_url``, ``fetched_at_utc``, ``parser_version``, ``deck_name``,
``cards`` (name / quantity / section), ``status`` and ``note``.

This module files those records into the same tables the Archidekt
harvest uses (``decklist_deck`` / ``decklist_card``) with the same
provenance discipline: per-deck source URL, harvest time, parser
version, SHA-256 of the raw record, the raw record gzipped next to
the database, and mapped/unmapped card counts with the unmapped
names kept — never silently dropped.

Cohort honesty: a browser record carries NO bracket — none is known
and none is invented. Decks land with ``bracket_level`` NULL and
``bracket_source`` NULL under their own platforms (``browser:edhrec``
/ ``browser:moxfield``), so a bracket filter can never place them in
a bracket cohort; they join a universe only when their platform is
selected, as that platform's bracket-less cohort (see
:mod:`deckbuild_studio.inclusion`). Content dedupe stays the
counting layer's job (``inclusion._canonical_decks``), exactly as
with Archidekt decks stored under several ids; the import report
counts how many imported lists are content-identical to decks that
were already stored.

Only AVAILABLE records are imported — PARTIAL / BLOCKED records are
counted and reported, never filed. Sideboard / maybeboard sections
are not part of a commander deck list (the Archidekt parser drops
non-deck categories the same way) and are excluded — counted, with
the count in the deck's detail and in the report. Commander entries
come from the record's commander section(s); a deck whose record
carries two commanders (partner) keeps both names and a NULL
commander_oracle_id rather than a misattributed single id.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from .inclusion import _content_fingerprint
from .store import Store, sha256_file, utcnow

PARSER_VERSION = "browser-import/1.0.0"
COMMANDER_SECTIONS = {"commander", "commanders"}
EXCLUDED_SECTIONS = {"sideboard", "maybeboard"}


class BrowserImportError(Exception):
    pass


# --------------------------------------------------------------------------
# Record shaping (pure functions — fixture-tested)
# --------------------------------------------------------------------------

def platform_for(source: object) -> str:
    """The decklist platform a browser record belongs to: the harvest
    source under its own ``browser:`` namespace (browser:edhrec,
    browser:moxfield, ...), never the platform's API name."""
    name = str(source or "").strip().lower()
    return f"browser:{name}" if name else "browser:generic"


def platform_deck_id(url: str) -> str:
    """The deck's id on its platform, taken from the page URL (the
    segment after /deckpreview/ resp. /decks/); falls back to a hash
    of the full URL when the URL carries no recognisable id."""
    segments = [s for s in urlparse(url).path.split("/") if s]
    lowered = [s.lower() for s in segments]
    for marker in ("deckpreview", "decks"):
        if marker in lowered:
            idx = lowered.index(marker)
            if idx + 1 < len(segments):
                return segments[idx + 1]
    if segments and "." not in segments[-1] and len(segments[-1]) <= 64:
        return segments[-1]
    return hashlib.sha256(url.encode()).hexdigest()[:24]


def normalize_fetched_at(value: object) -> str | None:
    """A record's harvest timestamp in the store's utcnow() format
    (ISO, seconds, +00:00). None when missing/unparseable — the
    caller falls back to the import time and says so in the detail."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat(timespec="seconds")


def aggregate_entries(record: dict) -> tuple[list[dict], int]:
    """A record's card list aggregated the way parse_deck_detail
    aggregates an Archidekt deck: per card name (quantities summed),
    commander-section entries flagged. Returns (entries,
    excluded_count): entries are {name, quantity, is_commander};
    sideboard / maybeboard entries are excluded and counted."""
    by_name: dict[str, dict] = {}
    excluded = 0
    cards = record.get("cards")
    if not isinstance(cards, list):
        return [], 0
    for card in cards:
        if not isinstance(card, dict):
            continue
        name = str(card.get("name") or "").strip()
        if not name:
            continue
        section = str(card.get("section") or "").strip().lower()
        if section in EXCLUDED_SECTIONS:
            excluded += 1
            continue
        qty = card.get("quantity")
        qty = qty if isinstance(qty, int) and qty > 0 else 1
        slot = by_name.setdefault(name, {"name": name, "quantity": 0,
                                         "is_commander": 0})
        slot["quantity"] += qty
        if section in COMMANDER_SECTIONS:
            slot["is_commander"] = 1
    return sorted(by_name.values(), key=lambda e: e["name"]), excluded


# --------------------------------------------------------------------------
# Name resolution (mirrors decklists._store_deck + the EDHREC name map)
# --------------------------------------------------------------------------

class _Resolver:
    """Card name -> oracle_id against the local Scryfall store:
    exact full-name match first (scryfall_by_name), then a unique
    front-face match for DFC front names (the inclusion engine's
    EDHREC name map does the same). Anything else stays unmapped —
    counted and named by the caller, never guessed. Cached per run."""

    def __init__(self, store: Store):
        self.store = store
        self.cache: dict[str, str | None] = {}

    def __call__(self, name: str) -> str | None:
        if name in self.cache:
            return self.cache[name]
        result: str | None = None
        hits = self.store.scryfall_by_name(name)
        if len(hits) == 1:
            result = hits[0]["oracle_id"]
        else:
            rows = self.store.conn.execute(
                "SELECT DISTINCT oracle_id FROM scryfall_card "
                "WHERE front_name=?", (name,)).fetchall()
            if len(rows) == 1:
                result = rows[0]["oracle_id"]
        self.cache[name] = result
        return result


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

def _save_raw(store: Store, platform: str, raw: bytes) -> tuple[str, str]:
    """Gzipped raw record next to the database (the decklists
    _save_raw pattern, per-platform folder). Raises OSError."""
    sha = hashlib.sha256(raw).hexdigest()
    folder = Path(store.path).parent / "snapshots" / platform.replace(":", "-")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{sha}.gz"
    if target.exists():
        return sha, str(target)
    tmp = folder / f".{sha}.tmp"
    tmp.write_bytes(gzip.compress(raw))
    tmp.replace(target)
    return sha, str(target)


def _existing_fingerprints(store: Store) -> dict[str, str]:
    """Content fingerprint -> lowest deck uid over the AVAILABLE
    decks already stored, restricted to decks with a countable card
    (the same eligibility inclusion._canonical_decks applies: decks
    without one never dedupe onto a shared fingerprint)."""
    rows_by_deck: dict[str, list[tuple]] = {}
    eligible: set[str] = set()
    for row in store.conn.execute(
            "SELECT c.deck_uid, c.entry_key, c.quantity, c.is_commander "
            "FROM decklist_card c JOIN decklist_deck d "
            "ON d.deck_uid = c.deck_uid WHERE d.status='AVAILABLE' "
            "ORDER BY c.deck_uid"):
        rows_by_deck.setdefault(row["deck_uid"], []).append(
            (row["entry_key"], row["quantity"], row["is_commander"]))
        if row["quantity"] > 0 and not row["is_commander"]:
            eligible.add(row["deck_uid"])
    first: dict[str, str] = {}
    for uid in sorted(eligible):
        first.setdefault(_content_fingerprint(rows_by_deck[uid]), uid)
    return first


def import_browser_decklists(store: Store, path: str | Path) -> dict:
    """Import one browser-harvest JSONL file. Per-record problems
    (bad JSON, missing fields, unresolvable card names) are counted
    in the report, never fatal; a missing/unreadable FILE raises
    BrowserImportError (the CLI turns that into import FAILED)."""
    path = Path(path)
    if not path.is_file():
        raise BrowserImportError(f"file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BrowserImportError(f"cannot read {path}: {exc}") from exc
    file_sha = sha256_file(path)

    report: dict = {
        "format": "browser-decklists",
        "file": str(path), "file_sha256": file_sha,
        "parser_version": PARSER_VERSION,
        "records_total": 0, "malformed_lines": 0,
        "malformed_line_numbers": [],
        "records_by_status": {},
        "imported": 0, "imported_partial": 0, "replaced_existing": 0,
        "decks_by_platform": {},
        "entries_mapped": 0, "entries_unmapped": 0, "unmapped_names": [],
        "decks_with_commander_id": 0, "decks_without_commander_id": 0,
        "sideboard_entries_excluded": 0,
        "duplicates_of_existing": 0, "duplicates_within_file": 0,
        "duplicate_examples": [],
    }
    unmapped_names: set[str] = set()
    resolver = _Resolver(store)
    existing_fp = _existing_fingerprints(store)
    run_fp: dict[str, str] = {}
    seen_uids: set[str] = set()
    pre_existing_uids = {r["deck_uid"] for r in store.conn.execute(
        "SELECT deck_uid FROM decklist_deck")}

    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        report["records_total"] += 1
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        if not isinstance(record, dict):
            report["malformed_lines"] += 1
            if len(report["malformed_line_numbers"]) < 20:
                report["malformed_line_numbers"].append(lineno)
            continue
        status = str(record.get("status") or "MISSING")
        by_status = report["records_by_status"]
        by_status[status] = by_status.get(status, 0) + 1
        if status != "AVAILABLE":
            continue  # counted above, never filed (module docstring)

        platform = platform_for(record.get("source"))
        url = str(record.get("source_url") or "")
        deck_id = platform_deck_id(url)
        uid = f"{platform}:{deck_id}"
        clash = store.conn.execute(
            "SELECT source_url FROM decklist_deck WHERE deck_uid=?",
            (uid,)).fetchone()
        if clash is not None and clash["source_url"] != url:
            # two different pages, one extracted id: keep both by
            # suffixing this deck's id with a hash of its URL
            deck_id = f"{deck_id}-{hashlib.sha256(url.encode()).hexdigest()[:8]}"
            uid = f"{platform}:{deck_id}"
        if uid in pre_existing_uids:
            report["replaced_existing"] += 1

        entries, excluded = aggregate_entries(record)
        resolved = [(entry, resolver(entry["name"])) for entry in entries]
        report["sideboard_entries_excluded"] += excluded
        detail_bits: list[str] = []
        deck_name = str(record.get("deck_name") or "").strip()
        if deck_name:
            detail_bits.append(f"title: {deck_name}")
        note = str(record.get("note") or "").strip()
        if note:
            detail_bits.append(f"harvest note: {note}")
        if excluded:
            detail_bits.append(
                f"{excluded} sideboard/maybeboard entries excluded")
        if not entries:
            detail_bits.append("record carried no cards")

        commander_resolved = [(e, o) for e, o in resolved if e["is_commander"]]
        commander_name: str | None = None
        commander_oracle_id: str | None = None
        if len(commander_resolved) == 1:
            commander_name = commander_resolved[0][0]["name"]
            commander_oracle_id = commander_resolved[0][1]
        elif len(commander_resolved) > 1:
            commander_name = " + ".join(
                e["name"] for e, _ in commander_resolved)
            detail_bits.append(
                f"commanders: {commander_name} (partner — no single "
                "commander_oracle_id stored)")
        else:
            detail_bits.append("no commander section in record")

        fetched_at = normalize_fetched_at(record.get("fetched_at_utc"))
        if fetched_at is None:
            fetched_at = utcnow()
            detail_bits.append(
                "fetched_at missing/unparseable in record — import time used")

        total_cards = 0
        card_rows: list[tuple] = []
        deck_unmapped: list[str] = []
        for entry, oracle_id in resolved:
            total_cards += entry["quantity"]
            if oracle_id is None:
                deck_unmapped.append(entry["name"])
                unmapped_names.add(entry["name"])
            card_rows.append((uid, oracle_id or f"name:{entry['name']}",
                              oracle_id, entry["name"], entry["quantity"],
                              entry["is_commander"]))
        mapped = len(entries) - len(deck_unmapped)
        report["entries_mapped"] += mapped
        report["entries_unmapped"] += len(deck_unmapped)

        raw = line.encode("utf-8")
        sha: str | None = None
        raw_path: str | None = None
        deck_status = "AVAILABLE"
        try:
            sha, raw_path = _save_raw(store, platform, raw)
        except OSError as exc:
            # mirror decklists: the cards are still stored, the deck
            # is downgraded to PARTIAL so it stays out of every
            # universe until a re-import saves the raw record
            deck_status = "PARTIAL"
            detail_bits.append(f"raw save failed: {exc}")
        store.conn.execute(
            "INSERT OR REPLACE INTO decklist_deck(deck_uid,platform,"
            "platform_deck_id,commander_oracle_id,commander_name,"
            "bracket_level,bracket_source,source_url,status,"
            "parser_version,sha256,raw_path,fetched_at,source_updated_at,"
            "deck_size,card_entries,mapped_cards,unmapped_cards,"
            "unmapped_names_json,detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,"
            "?,?,?,?,?,?,?,?)",
            (uid, platform, deck_id, commander_oracle_id, commander_name,
             None, None, url, deck_status,
             str(record.get("parser_version") or PARSER_VERSION),
             sha, raw_path, fetched_at, None, total_cards, len(entries),
             mapped, len(deck_unmapped),
             json.dumps(sorted(set(deck_unmapped)), ensure_ascii=False),
             "; ".join(detail_bits)))
        store.conn.execute("DELETE FROM decklist_card WHERE deck_uid=?", (uid,))
        store.conn.executemany(
            "INSERT OR REPLACE INTO decklist_card(deck_uid,entry_key,"
            "oracle_id,card_name,quantity,is_commander) "
            "VALUES(?,?,?,?,?,?)", card_rows)
        store.conn.commit()

        if deck_status == "AVAILABLE":
            report["imported"] += 1
        else:
            report["imported_partial"] += 1
        by_platform = report["decks_by_platform"]
        by_platform[platform] = by_platform.get(platform, 0) + 1
        if commander_oracle_id:
            report["decks_with_commander_id"] += 1
        else:
            report["decks_without_commander_id"] += 1

        # content-duplicate bookkeeping (the counting layer dedupes
        # for real; this only REPORTS how many imported lists were
        # already known by content)
        countable = any(e["quantity"] > 0 and not e["is_commander"]
                        for e, _ in resolved)
        if deck_status == "AVAILABLE" and countable and uid not in seen_uids:
            fp = _content_fingerprint([
                (o or f"name:{e['name']}", e["quantity"], e["is_commander"])
                for e, o in resolved])
            if fp in existing_fp and existing_fp[fp] != uid:
                report["duplicates_of_existing"] += 1
                if len(report["duplicate_examples"]) < 10:
                    report["duplicate_examples"].append(
                        {"deck_uid": uid, "canonical_uid": existing_fp[fp]})
            elif fp in run_fp:
                report["duplicates_within_file"] += 1
                if len(report["duplicate_examples"]) < 10:
                    report["duplicate_examples"].append(
                        {"deck_uid": uid, "canonical_uid": run_fp[fp]})
            run_fp.setdefault(fp, uid)
        seen_uids.add(uid)

    report["unmapped_names"] = sorted(unmapped_names)
    report["decks_by_platform"] = dict(
        sorted(report["decks_by_platform"].items()))
    report["records_by_status"] = dict(
        sorted(report["records_by_status"].items()))
    data_status = "AVAILABLE" if report["imported"] else "PARTIAL"
    status_bits = ", ".join(f"{k}: {v}" for k, v in
                            report["records_by_status"].items())
    platform_bits = ", ".join(report["decks_by_platform"])
    source_id = store.add_source(
        source_id=f"browser-decklists:{file_sha[:16]}",
        source_name="Browser-harvest deck lists (JSONL)",
        file_name=path.name, sha256=file_sha, data_status=data_status,
        note=(f"{report['imported']} decks imported from "
              f"{report['records_total']} records ({status_bits}); "
              f"platforms: {platform_bits}; "
              "no brackets (bracket-less source)"),
        parser_version=PARSER_VERSION)
    store.conn.commit()
    report["source_id"] = source_id
    return report
