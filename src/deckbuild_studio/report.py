"""Counts-only data report: what the store holds, what is missing,
what is unknown — modelled on the upstream studio ``data_report.py``.

Every figure is a count with its denominator; a missing value is
counted as unknown, never as zero. The report contains no card names,
no note text and no deck contents, so it can be pasted into an issue.

The ``completeness`` section adds the per-layer status table of the
sister project's ``import_all.py`` (commander-playtest-lab), adapted
to this store-wide report: COMPLETE / PARTIAL / MISSING where a real
denominator exists, UNKNOWN where none does.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime

from . import roles as roles_mod
from .store import Store

REPORT_SCHEMA = "deckbuild-data-report-1"
SCRYFALL_STALE_AFTER_DAYS = 30

NOT_MEASURED = (
    "playgroup_coverage_beyond_imported_collection",
    "edhrec_coverage_beyond_synced_commanders",
    "collection_changes_since_last_export",
    "card_image_cache_completeness_without_fetch_run",
)


def _scalar(db: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    row = db.execute(sql, params).fetchone()
    return int(row[0]) if row is not None and row[0] is not None else 0


def _counter(db: sqlite3.Connection, sql: str, params: tuple = ()) -> dict[str, int]:
    return {str(r[0]): int(r[1]) for r in db.execute(sql, params)}


def _share(count: int, of: int) -> dict[str, int]:
    return {"count": count, "of": of}


def role_fingerprint(store: Store) -> str:
    """SHA-256 over all role claims — a before/after import comparison
    shows at a glance whether anything outside the import changed."""
    roles_mod.ensure_schema(store)
    lines = [f"{r['oracle_id']}|{r['role']}|{r['origin']}" for r in
             store.conn.execute(
                 "SELECT oracle_id, role, origin FROM card_role "
                 "ORDER BY oracle_id, role, origin")]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _tier_section(db: sqlite3.Connection) -> dict:
    """Tier coverage (counts only): rows per scope/tier + algorithm
    version. Absent table or no compute run yet -> measured zeros with
    an explicit ``computed`` flag, never invented tiers."""
    exists = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='tier_assignment'").fetchone()
    if exists is None:
        return {"computed": False, "global": {}, "context_rows": 0}
    # Several model versions may coexist (tierlist/1.2.0); the counts
    # describe the ACTIVE version (setting tierlist.model_version),
    # the versions list keeps the others visible.
    active = "tierlist/1.1.0"
    try:
        row = db.execute(
            "SELECT value_json FROM app_setting "
            "WHERE key='tierlist.model_version'").fetchone()
        if row is not None:
            import json as _json
            active = str(_json.loads(row[0]))
    except Exception:
        pass
    versions = [r[0] for r in db.execute(
        "SELECT DISTINCT algo_version FROM tier_assignment "
        "ORDER BY algo_version")]
    if active not in versions and versions:
        active = versions[-1]
    global_counts = _counter(
        db, "SELECT tier, COUNT(*) FROM tier_assignment "
            "WHERE scope='global' AND algo_version=? GROUP BY tier",
        (active,))
    context_rows = _scalar(
        db, "SELECT COUNT(*) FROM tier_assignment "
            "WHERE scope='context' AND algo_version=?", (active,))
    contexts = _scalar(
        db, "SELECT COUNT(DISTINCT commander_oracle_id || '|' || bracket) "
            "FROM tier_assignment WHERE scope='context' "
            "AND algo_version=?", (active,))
    meta = db.execute(
        "SELECT algo_version, MAX(computed_at) FROM tier_assignment "
        "GROUP BY algo_version ORDER BY 2 DESC LIMIT 1").fetchone()
    return {
        "computed": bool(global_counts or context_rows),
        "algo_version": meta[0] if meta else None,
        "active_model_version": active,
        "versions_present": versions,
        "last_computed_at": meta[1] if meta else None,
        "global": global_counts,
        "context_rows": context_rows,
        "contexts_with_rows": contexts,
    }


def _categories_section(store: Store) -> dict:
    """Category-layer coverage over the whole store (counts only):
    type facts, per-origin checked/with-claims, tagger tag status.
    Absent layers report zeros + recorded=false — never dressed up."""
    from . import categories as cat_mod
    cat_mod.ensure_schema(store)
    db = store.conn
    total = _scalar(db, "SELECT COUNT(*) FROM scryfall_card")
    layers: dict[str, dict] = {}
    for origin in roles_mod.ORIGINS:
        layers[origin] = {
            "checked": _share(_scalar(
                db, "SELECT COUNT(*) FROM card_category_check "
                    "WHERE origin = ?", (origin,)), total),
            "with_claims": _scalar(
                db, "SELECT COUNT(DISTINCT oracle_id) FROM card_role "
                    "WHERE origin = ?", (origin,)),
            "checked_no_category": _scalar(
                db, "SELECT COUNT(*) FROM card_category_check "
                    "WHERE origin = ? AND claims = 0", (origin,)),
        }
    tagger_tags = {
        str(r[0]): str(r[1]) for r in db.execute(
            "SELECT slug, status FROM external_snapshot "
            "WHERE source_name = 'scryfall_tagger' AND kind = 'tagger_function' "
            "ORDER BY fetched_at")}
    type_run = db.execute(
        "SELECT status FROM category_run WHERE layer = 'type_facts' "
        "ORDER BY created_at DESC LIMIT 1").fetchone()
    return {
        "type_facts": {
            "cards_with_faces": _share(_scalar(
                db, "SELECT COUNT(DISTINCT oracle_id) FROM card_face"), total),
            "cards_with_types": _share(_scalar(
                db, "SELECT COUNT(DISTINCT oracle_id) FROM card_type_component "
                    "WHERE kind = 'type'"), total),
            "cards_with_keywords": _scalar(
                db, "SELECT COUNT(DISTINCT oracle_id) FROM card_keyword"),
            "latest_run_status": type_run[0] if type_run else None,
        },
        "layers": layers,
        "tagger_tags_by_status": tagger_tags,
    }


COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
MISSING = "MISSING"
UNKNOWN = "UNKNOWN"

# Origins whose category layer examines every card in the store; their
# completeness denominator is the Scryfall card set. STRUCTURAL_PROFILE
# is deliberately not one of them: it is a curated file covering a
# fixed card set, so it is measured against its import manifest below
# (reference layers), never against the whole card set.
_CHECK_ORIGINS = ("ORACLE_TEXT_HEURISTIC", "SCRYFALL_TAGGER_SEARCH")

# External snapshot sources reported as their own completeness layer.
_SNAPSHOT_SOURCES = ("edhrec", "edhtop16", "playgroup",
                     "commanderspellbook")


def _table_exists(db: sqlite3.Connection, name: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone() is not None


def _pool_status(rows: int, covered: int, pool: int | None) -> str:
    """Status for a layer with a coverage denominator: nothing stored
    is MISSING; without a denominator the layer is present but its
    completeness cannot be told (UNKNOWN — never guessed COMPLETE);
    full coverage of the denominator is COMPLETE, anything between
    is PARTIAL."""
    if rows <= 0:
        return MISSING
    if pool is None or pool <= 0:
        return UNKNOWN
    return COMPLETE if covered >= pool else PARTIAL


def _snapshot_status(by_status: dict[str, int]) -> str:
    """Status for an external snapshot source: no snapshot at all is
    MISSING; a snapshot recorded as PARTIAL is a documented gap in
    that source's data, so the layer is PARTIAL; otherwise the layer
    is present, but the sync scope is owner-chosen (which commanders
    or cards to sync), so no coverage denominator exists and the
    status is UNKNOWN — see NOT_MEASURED for the coverage questions
    this report deliberately does not answer."""
    if sum(by_status.values()) <= 0:
        return MISSING
    if by_status.get("PARTIAL", 0) > 0:
        return PARTIAL
    return UNKNOWN


def _completeness_section(db: sqlite3.Connection, *,
                          pool: int, tiers: dict) -> list[dict]:
    """Import completeness per data layer (counts only): one entry
    per layer with its row count, how much of its denominator is
    covered, the denominator itself (``pool``; None where no target
    exists) and the status. Denominators are real targets, not
    aspirations:

    * inventory — every lot is expected to carry a quantity; a lot
      with neither quantity nor lower bound is an unresolved import
      remainder (the same gap the collections section counts).
    * card facts — every collection identity needs its Scryfall row.
    * category checks — the text/tagger layers examine every card.
    * reference layers — the import manifest (``reference_import``)
      records how many entries the source file held; the layer is
      complete when that many rows are stored.
    * tierlist — every collection identity needs a global tier row
      under the active model version (the card lists render one).
    * external snapshots / image cache — no denominator exists, so
      these can only be MISSING, PARTIAL (documented partial fetch)
      or UNKNOWN; they are never reported COMPLETE.
    """
    layers: list[dict] = []

    def add(key: str, layer: str, rows: int | None,
            covered: int | None, denom: int | None, basis: str,
            status: str | None = None) -> None:
        layers.append({
            "key": key, "layer": layer,
            "status": status if status is not None else _pool_status(
                rows or 0, covered or 0, denom),
            "rows": rows, "covered": covered, "pool": denom,
            "basis": basis,
        })

    lots = _scalar(db, "SELECT COUNT(*) FROM physical_lot")
    lots_known = _scalar(
        db, "SELECT COUNT(*) FROM physical_lot WHERE NOT "
            "(quantity IS NULL AND quantity_lower_bound IS NULL)")
    add("collection_inventory", "Collection inventory (lot quantities)",
        lots, lots_known, lots,
        "every lot carries a quantity or a lower bound")

    scryfall_total = _scalar(db, "SELECT COUNT(*) FROM scryfall_card")
    facts_covered = _scalar(
        db, "SELECT COUNT(DISTINCT p.oracle_id) FROM physical_lot p "
            "JOIN scryfall_card s ON s.oracle_id = p.oracle_id")
    add("card_facts_scryfall", "Card facts (Scryfall)",
        scryfall_total, facts_covered, pool,
        "collection identities with a Scryfall card row")

    for origin in _CHECK_ORIGINS:
        checked = check_rows = 0
        if _table_exists(db, "card_category_check"):
            # Coverage counts only checks of cards actually stored:
            # foreign or stale check rows (a migrated/restored DB)
            # must not inflate the layer to a false COMPLETE — the
            # same intersection the facts layer above applies (review
            # P2 on the completeness section).
            checked = _scalar(
                db, "SELECT COUNT(DISTINCT c.oracle_id) "
                    "FROM card_category_check c JOIN scryfall_card s "
                    "ON s.oracle_id = c.oracle_id "
                    "WHERE c.origin = ?", (origin,))
            check_rows = _scalar(
                db, "SELECT COUNT(*) FROM card_category_check "
                    "WHERE origin = ?", (origin,))
        add(f"category_check:{origin}", f"Category check ({origin})",
            check_rows, checked, scryfall_total,
            "cards examined by this category layer, of all stored cards")

    for kind, table, extra in (
            ("structural_role_profiles", "reference_role_profile", ""),
            ("commander_flags", "reference_card_flag",
             " WHERE source_kind = 'commander_flags'")):
        manifest = None
        if _table_exists(db, "reference_import"):
            row = db.execute(
                "SELECT entry_count FROM reference_import "
                "WHERE source_kind = ?", (kind,)).fetchone()
            manifest = int(row[0]) if row is not None else None
        rows = (_scalar(db, f"SELECT COUNT(*) FROM {table}{extra}")
                if _table_exists(db, table) else 0)
        add(f"reference:{kind}", f"Reference data ({kind})",
            rows, rows, manifest,
            "stored rows against the import manifest entry count")

    tier_rows = sum(tiers.get("global", {}).values())
    tier_covered = 0
    if _table_exists(db, "tier_assignment"):
        tier_covered = _scalar(
            db, "SELECT COUNT(DISTINCT p.oracle_id) FROM physical_lot p "
                "JOIN tier_assignment t ON t.oracle_id = p.oracle_id "
                "AND t.scope = 'global' AND t.algo_version = ?",
            (tiers.get("active_model_version") or "tierlist/1.1.0",))
    add("tierlist_global", "Tier list (global, active model version)",
        tier_rows, tier_covered, pool,
        "collection identities with a global tier row")

    snapshots: dict[str, dict[str, int]] = {}
    for r in db.execute(
            "SELECT source_name, status, COUNT(*) FROM external_snapshot "
            "GROUP BY source_name, status"):
        snapshots.setdefault(str(r[0]), {})[str(r[1])] = int(r[2])
    for source in _SNAPSHOT_SOURCES:
        by_status = snapshots.get(source, {})
        add(f"external:{source}", f"External snapshots ({source})",
            sum(by_status.values()), by_status.get("AVAILABLE", 0), None,
            "snapshot presence by recorded status; sync scope is "
            "owner-chosen, so no coverage target exists",
            status=_snapshot_status(by_status))
    topdeck_rows = (_scalar(db, "SELECT COUNT(*) FROM topdeck_tournament")
                    if _table_exists(db, "topdeck_tournament") else 0)
    topdeck_snaps = snapshots.get("topdeck", {})
    topdeck_presence = dict(topdeck_snaps)
    if topdeck_rows:
        topdeck_presence["corpus_rows"] = topdeck_rows
    add("external:topdeck", "External snapshots (topdeck)",
        topdeck_rows + sum(topdeck_snaps.values()),
        topdeck_snaps.get("AVAILABLE", 0), None,
        "TopDeck corpus tables plus the import marker snapshot; the "
        "upstream corpus is open-ended, so no coverage target exists",
        status=_snapshot_status(topdeck_presence))
    add("card_image_cache", "Card image cache", None, None, None,
        "not measured: completeness needs a fetch run / filesystem "
        "scan (see not_measured)", status=UNKNOWN)
    return layers


def data_report(store: Store) -> dict:
    db = store.conn
    now = datetime.now(UTC)
    collections: list[dict] = []
    for col in store.collections():
        cid = col["collection_id"]
        identities = _scalar(
            db, "SELECT COUNT(DISTINCT oracle_id) FROM physical_lot "
                "WHERE collection_id = ?", (cid,))
        lots = _scalar(
            db, "SELECT COUNT(*) FROM physical_lot WHERE collection_id = ?",
            (cid,))
        unknown_qty = _scalar(
            db, "SELECT COUNT(*) FROM physical_lot WHERE collection_id = ? "
                "AND quantity IS NULL AND quantity_lower_bound IS NULL",
            (cid,))
        collections.append({
            "collection_id": cid,
            "identities": _share(identities, identities),
            "lots": lots,
            "copies_reported": _scalar(
                db, "SELECT COALESCE(SUM(quantity),0) FROM physical_lot "
                    "WHERE collection_id = ?", (cid,)),
            "locations": _scalar(
                db, "SELECT COUNT(DISTINCT location_id) FROM physical_lot "
                    "WHERE collection_id = ?", (cid,)),
            "lots_with_unknown_quantity": _share(unknown_qty, lots),
            "reserved_copies": _scalar(
                db, "SELECT COALESCE(SUM(reserved_quantity),0) "
                    "FROM physical_lot WHERE collection_id = ?", (cid,)),
            "decks": _scalar(
                db, "SELECT COUNT(*) FROM deck WHERE collection_id = ?",
                (cid,)),
        })
    scryfall_cards = _scalar(db, "SELECT COUNT(*) FROM scryfall_card")
    sf_source = db.execute(
        "SELECT imported_at FROM source WHERE source_name LIKE 'Scryfall%' "
        "ORDER BY imported_at DESC LIMIT 1").fetchone()
    sf_age_days: int | None = None
    if sf_source is not None:
        try:
            imported = datetime.fromisoformat(str(sf_source[0]))
            sf_age_days = max(0, (now - imported).days)
        except ValueError:
            sf_age_days = None
    roles_mod.ensure_schema(store)
    marks_fav = _scalar(db, "SELECT COUNT(*) FROM mark WHERE favorite = 1")
    marks_excl = _scalar(db, "SELECT COUNT(*) FROM mark WHERE excluded = 1")
    marks_notes = _scalar(
        db, "SELECT COUNT(*) FROM mark WHERE note != ''")
    tiers_section = _tier_section(db)
    completeness = _completeness_section(
        db, pool=sum(c["identities"]["count"] for c in collections),
        tiers=tiers_section)
    report = {
        "schema": REPORT_SCHEMA,
        "generated_at": now.isoformat(timespec="seconds"),
        "collections": collections,
        "scryfall": {
            "oracle_identities": scryfall_cards,
            "commander_legal": _share(_scalar(
                db, "SELECT COUNT(*) FROM scryfall_card "
                    "WHERE commander_legality = 'legal'"), scryfall_cards),
            "with_image_uri": _share(_scalar(
                db, "SELECT COUNT(*) FROM scryfall_card "
                    "WHERE image_uri IS NOT NULL"), scryfall_cards),
            "snapshot_age_days": sf_age_days,
            "stale_after_days": SCRYFALL_STALE_AFTER_DAYS,
            "stale": (sf_age_days is not None
                      and sf_age_days > SCRYFALL_STALE_AFTER_DAYS),
        },
        "roles": {
            "fingerprint": role_fingerprint(store),
            "claims_by_origin": _counter(
                db, "SELECT origin, COUNT(*) FROM card_role GROUP BY origin"),
            "claims_by_role": _counter(
                db, "SELECT role, COUNT(*) FROM card_role GROUP BY role"),
            "cards_with_roles": _scalar(
                db, "SELECT COUNT(DISTINCT oracle_id) FROM card_role"),
            "collection_cards": sum(c["identities"]["count"]
                                    for c in collections),
        },
        "categories": _categories_section(store),
        "decks": {
            "decks": _scalar(db, "SELECT COUNT(*) FROM deck"),
            "revisions": _scalar(db, "SELECT COUNT(*) FROM deck_revision"),
        },
        "marks": {"favorites": marks_fav, "excluded": marks_excl,
                  "with_note": marks_notes},
        "tiers": tiers_section,
        "completeness": completeness,
        "external": {
            "snapshots_by_source_status": {
                f"{r[0]}/{r[1]}": int(r[2]) for r in db.execute(
                    "SELECT source_name, status, COUNT(*) "
                    "FROM external_snapshot GROUP BY source_name, status")},
            "jobs_by_status": _counter(
                db, "SELECT status, COUNT(*) FROM sync_job GROUP BY status"),
        },
        "not_measured": list(NOT_MEASURED),
    }
    return report
