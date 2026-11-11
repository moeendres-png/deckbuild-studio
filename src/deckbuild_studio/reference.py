"""Reference-data layer — card-specific reference data reused from the
sister project ``commander-playtest-lab`` (where it is committed under
``data/cards/``), imported by explicit file path. Nothing is copied into
this repository; provenance travels with every record.

Two sources (see docs/REFERENCE_DATA.md for what was deliberately NOT
taken over):

* ``commander_flags.json`` (schema ``commander-card-flags-1.0.0``):
  Game Changer labels and the Commander banned list, derived there from
  a Scryfall Oracle bulk file. Semantics: a Game Changer flag is a
  *bracket/labelling marker only* — it is NOT a legality verdict. The
  banned list is a *reference*; legality in Deckbuild Studio continues
  to come from the local Scryfall legalities. Discrepancies between the
  reference list and Scryfall are counted and reported, never silently
  overwritten in either direction.
* ``structural_role_profiles.json`` (schema 0.4.0): structural role
  profiles. These are MODEL ESTIMATES (``estimate_type`` =
  ``structural_model_estimates``, data as of 2026-08-09), carried
  unchanged and labelled as estimates in API/UI. They are never
  presented as EDHREC/Playgroup observations.

The schema here is strictly additive (new ``reference_*`` tables); no
existing table is altered.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .store import Store, sha256_file, utcnow

SOURCE_PROJECT = "commander-playtest-lab"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reference_import (
    source_kind TEXT PRIMARY KEY,
    source_project TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    schema_version TEXT,
    data_as_of TEXT,
    source_hash TEXT,
    file_sha256 TEXT,
    estimate_type TEXT,
    scope_note TEXT NOT NULL DEFAULT '',
    entry_count INTEGER NOT NULL DEFAULT 0,
    imported_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_card_flag (
    oracle_id TEXT NOT NULL,
    flag TEXT NOT NULL,
    name TEXT NOT NULL,
    in_scryfall_store INTEGER NOT NULL DEFAULT 0,
    source_kind TEXT NOT NULL,
    PRIMARY KEY (oracle_id, flag)
);
CREATE TABLE IF NOT EXISTS reference_role_profile (
    oracle_name TEXT PRIMARY KEY,
    oracle_id TEXT,
    resolution_status TEXT NOT NULL,
    roles_json TEXT NOT NULL DEFAULT '[]',
    role_strengths_json TEXT NOT NULL DEFAULT '{}',
    mechanic_tags_json TEXT NOT NULL DEFAULT '[]',
    estimate_type TEXT NOT NULL,
    data_as_of TEXT,
    payload_json TEXT NOT NULL,
    source_kind TEXT NOT NULL
);
"""

FLAGS_KIND = "commander_flags"
ROLES_KIND = "structural_role_profiles"

FLAG_LABELS = {
    "game_changer": "Game Changer (Bracket-Kennzeichnung, keine Legalitätsaussage)",
    "commander_banned_reference": (
        "Commander-Banned-Referenzliste (Legalität maßgeblich: Scryfall)"),
}

ROLE_ESTIMATE_LABEL = (
    "Strukturelle Schätzung (Modell), Stand {as_of} — keine Beobachtungsdaten"
)


def ensure_schema(store: Store) -> None:
    store.conn.executescript(_SCHEMA)
    store.conn.commit()


def _tables_exist(store: Store) -> bool:
    row = store.conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='reference_import'"
    ).fetchone()
    return bool(row and row[0])


def _collection_oracles(store: Store, collection_id: str) -> set[str]:
    return {r[0] for r in store.conn.execute(
        "SELECT DISTINCT oracle_id FROM physical_lot WHERE collection_id = ?",
        (collection_id,))}


def _record_import(store: Store, *, source_kind: str, path: Path,
                   schema_version: str | None, data_as_of: str | None,
                   source_hash: str | None, estimate_type: str | None,
                   scope_note: str, entry_count: int) -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO reference_import(source_kind,source_project,file_path,"
        "file_name,schema_version,data_as_of,source_hash,file_sha256,estimate_type,"
        "scope_note,entry_count,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (source_kind, SOURCE_PROJECT, str(path), path.name, schema_version,
         data_as_of, source_hash, sha256_file(path), estimate_type, scope_note,
         entry_count, utcnow()))


def _banned_discrepancies(store: Store) -> dict[str, int]:
    """Reference banned list vs. Scryfall legalities — reported, never merged."""
    ref = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM reference_card_flag WHERE flag='commander_banned_reference'")}
    scry: dict[str, str | None] = {}
    for oid in ref:
        row = store.scryfall(oid)
        scry[oid] = row["commander_legality"] if row else None
    scryfall_banned = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM scryfall_card WHERE commander_legality='banned'")}
    return {
        "reference_banned_not_in_scryfall_store": sum(
            1 for v in scry.values() if v is None),
        "reference_banned_but_scryfall_not_banned": sum(
            1 for v in scry.values() if v is not None and v != "banned"),
        "scryfall_banned_not_in_reference": len(scryfall_banned - ref),
    }


def import_commander_flags(store: Store, path: str | Path) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = str(data.get("schema") or "")
    if not schema.startswith("commander-card-flags"):
        raise ValueError(f"unexpected flags schema: {schema!r}")
    source = data.get("source") or {}
    ensure_schema(store)
    try:
        store.conn.execute("DELETE FROM reference_card_flag")
        counts: dict[str, int] = {}
        not_in_store: dict[str, int] = {}
        for flag, key in (("game_changer", "game_changers"),
                          ("commander_banned_reference", "commander_banned")):
            entries = data.get(key) or []
            counts[key] = len(entries)
            not_in_store[key] = 0
            for entry in entries:
                oid = entry["oracle_id"]
                in_store = 1 if store.scryfall(oid) else 0
                if not in_store:
                    not_in_store[key] += 1
                store.conn.execute(
                    "INSERT OR REPLACE INTO reference_card_flag"
                    "(oracle_id,flag,name,in_scryfall_store,source_kind) VALUES(?,?,?,?,?)",
                    (oid, flag, entry.get("name", ""), in_store, FLAGS_KIND))
        _record_import(
            store, source_kind=FLAGS_KIND, path=path, schema_version=schema,
            data_as_of=source.get("data_as_of"),
            source_hash=source.get("bulk_sha256"), estimate_type=None,
            scope_note=str(data.get("scope") or "")[:500],
            entry_count=sum(counts.values()))
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    report: dict[str, object] = {
        "source_kind": FLAGS_KIND, "schema": schema,
        "game_changers_imported": counts.get("game_changers", 0),
        "commander_banned_imported": counts.get("commander_banned", 0),
        "not_in_scryfall_store": not_in_store,
        "discrepancies": _banned_discrepancies(store),
        "overlap_by_collection": {
            r["collection_id"]: {
                "game_changers_in_collection": len(
                    {x[0] for x in store.conn.execute(
                        "SELECT oracle_id FROM reference_card_flag WHERE flag='game_changer'")}
                    & _collection_oracles(store, r["collection_id"])),
                "banned_reference_in_collection": len(
                    {x[0] for x in store.conn.execute(
                        "SELECT oracle_id FROM reference_card_flag "
                        "WHERE flag='commander_banned_reference'")}
                    & _collection_oracles(store, r["collection_id"])),
            } for r in store.collections()
        },
    }
    return report


def import_role_profiles(store: Store, path: str | Path) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    estimate_type = str(data.get("estimate_type") or "")
    if estimate_type != "structural_model_estimates":
        raise ValueError(f"unexpected estimate_type: {estimate_type!r}")
    profiles = data.get("profiles") or []
    ensure_schema(store)
    resolved = ambiguous = unresolved = 0
    try:
        store.conn.execute("DELETE FROM reference_role_profile")
        for profile in profiles:
            name = profile["oracle_name"]
            rows = store.scryfall_by_name(name)
            oids = {r["oracle_id"] for r in rows}
            if len(oids) == 1:
                oid, status = next(iter(oids)), "resolved"
                resolved += 1
            elif len(oids) > 1:
                oid, status = None, "ambiguous"
                ambiguous += 1
            else:
                oid, status = None, "unresolved"
                unresolved += 1
            store.conn.execute(
                "INSERT OR REPLACE INTO reference_role_profile(oracle_name,oracle_id,"
                "resolution_status,roles_json,role_strengths_json,mechanic_tags_json,"
                "estimate_type,data_as_of,payload_json,source_kind)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (name, oid, status,
                 json.dumps(profile.get("roles") or [], ensure_ascii=False),
                 json.dumps(profile.get("role_strengths") or {}, ensure_ascii=False),
                 json.dumps(profile.get("mechanic_tags") or [], ensure_ascii=False),
                 estimate_type, data.get("data_as_of"),
                 json.dumps(profile, ensure_ascii=False), ROLES_KIND))
        _record_import(
            store, source_kind=ROLES_KIND, path=path,
            schema_version=str(data.get("schema_version") or ""),
            data_as_of=data.get("data_as_of"),
            source_hash=data.get("source_hash"), estimate_type=estimate_type,
            scope_note="Structural model estimates — not observations.",
            entry_count=len(profiles))
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    matched_oracles = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM reference_role_profile WHERE oracle_id IS NOT NULL")}
    return {
        "source_kind": ROLES_KIND,
        "schema_version": data.get("schema_version"),
        "estimate_type": estimate_type,
        "data_as_of": data.get("data_as_of"),
        "profiles_imported": len(profiles),
        "resolved": resolved, "ambiguous": ambiguous, "unresolved": unresolved,
        "overlap_by_collection": {
            r["collection_id"]: len(matched_oracles
                                    & _collection_oracles(store, r["collection_id"]))
            for r in store.collections()
        },
    }


def reference_summary(store: Store) -> dict:
    """Read-only summary (no schema writes — safe for status endpoints)."""
    if not _tables_exist(store):
        return {"imported": False}
    imports = [dict(r) for r in store.conn.execute(
        "SELECT source_kind, source_project, file_name, schema_version, data_as_of,"
        " source_hash, estimate_type, entry_count, imported_at"
        " FROM reference_import ORDER BY source_kind")]
    if not imports:
        return {"imported": False}
    flag_counts = {r["flag"]: r["n"] for r in store.conn.execute(
        "SELECT flag, COUNT(*) n FROM reference_card_flag GROUP BY flag")}
    roles_total = store.conn.execute(
        "SELECT COUNT(*) FROM reference_role_profile").fetchone()[0]
    roles_resolved = store.conn.execute(
        "SELECT COUNT(*) FROM reference_role_profile WHERE resolution_status='resolved'"
    ).fetchone()[0]
    matched_oracles = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM reference_role_profile WHERE oracle_id IS NOT NULL")}
    gc_oracles = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM reference_card_flag WHERE flag='game_changer'")}
    banned_oracles = {r[0] for r in store.conn.execute(
        "SELECT oracle_id FROM reference_card_flag WHERE flag='commander_banned_reference'")}
    return {
        "imported": True,
        "imports": imports,
        "commander_flags": {
            "game_changers": flag_counts.get("game_changer", 0),
            "commander_banned_reference": flag_counts.get("commander_banned_reference", 0),
            "note": "Game Changer = label only, no legality verdict; banned list is "
                    "a reference — legality comes from Scryfall.",
            "discrepancies_vs_scryfall": _banned_discrepancies(store),
        },
        "role_profiles": {
            "profiles": roles_total,
            "resolved": roles_resolved,
            "data_kind": "structural_model_estimates",
            "display_label": ROLE_ESTIMATE_LABEL.format(
                as_of=next((i["data_as_of"] for i in imports
                            if i["source_kind"] == ROLES_KIND), None) or "unbekannt"),
        },
        "overlap_by_collection": {
            r["collection_id"]: {
                "game_changers": len(gc_oracles & _collection_oracles(store, r["collection_id"])),
                "banned_reference": len(banned_oracles
                                        & _collection_oracles(store, r["collection_id"])),
                "role_profiles": len(matched_oracles
                                     & _collection_oracles(store, r["collection_id"])),
            } for r in store.collections()
        },
    }


def card_reference(store: Store, oracle_id: str) -> dict | None:
    """Flags + role estimate for one card; None when nothing is known."""
    if not _tables_exist(store):
        return None
    flags = [
        {"flag": r["flag"], "label": FLAG_LABELS.get(r["flag"], r["flag"])}
        for r in store.conn.execute(
            "SELECT flag FROM reference_card_flag WHERE oracle_id = ? ORDER BY flag",
            (oracle_id,))
    ]
    role_row = store.conn.execute(
        "SELECT * FROM reference_role_profile WHERE oracle_id = ?",
        (oracle_id,)).fetchone()
    role = None
    if role_row is not None:
        role = {
            "roles": json.loads(role_row["roles_json"]),
            "role_strengths": json.loads(role_row["role_strengths_json"]),
            "mechanic_tags": json.loads(role_row["mechanic_tags_json"]),
            "data_kind": "structural_model_estimate",
            "estimate_type": role_row["estimate_type"],
            "data_as_of": role_row["data_as_of"],
            "display_label": ROLE_ESTIMATE_LABEL.format(
                as_of=role_row["data_as_of"] or "unbekannt"),
        }
    if not flags and role is None:
        return None
    return {"flags": flags, "role_profile": role}


def reference_map(store: Store, oracle_ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for oid in oracle_ids:
        ref = card_reference(store, oid)
        if ref is not None:
            out[oid] = ref
    return out
