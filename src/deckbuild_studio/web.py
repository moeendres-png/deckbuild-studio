"""FastAPI web UI — standalone BUILD frontend.

Adapted from commander-playtest-lab ``studio/web.py`` + ``static/app.*``;
all /games, /play and launch (XMage) routes were dropped, the Chulane-fixed
commander context was replaced by the dynamic commander selection, and
EDHREC/Playgroup are shown as honest status views (NOT_FETCHED, Phase 2).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from . import decks as decks_mod
from .commander import commander_candidates
from .config import database_path
from .external import (card_atlas_coverage, latest_snapshot,
                       register_card_atlas_jobs, register_commander_jobs)
from .importers import normalization_report
from .store import Store

STATIC = Path(__file__).parent / "static"


def _store() -> Store:
    return Store(database_path())


class DeckIn(BaseModel):
    collection_id: str
    name: str
    commander_oracle_ids: list[str]
    entries: dict[str, int]
    note: str = ""
    parent_revision_id: str | None = None


class MarkIn(BaseModel):
    collection_id: str
    oracle_id: str
    favorite: bool = False
    excluded: bool = False
    note: str = ""


def create_app() -> FastAPI:
    app = FastAPI(title="Deckbuild Studio", version="0.1.0")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "app.html")

    @app.get("/api/status")
    def status() -> dict:
        with _store() as s:
            return s.status()

    @app.get("/api/report")
    def report() -> dict:
        with _store() as s:
            return normalization_report(s)

    @app.get("/api/collections")
    def collections() -> list[dict]:
        with _store() as s:
            return [dict(r) for r in s.collections()]

    @app.get("/api/cards")
    def cards(collection_id: str, q: str = "", commander_oracle_id: str | None = None) -> list[dict]:
        with _store() as s:
            available = s.available_by_oracle(collection_id)
            rows_all = s.inventory_rows(collection_id)
            loc_map: dict[str, set] = {}
            for x in rows_all:
                loc_map.setdefault(x["oracle_id"], set()).add(x["location_id"])
            out, seen = [], set()
            for r in rows_all:
                oid = r["oracle_id"]
                if oid in seen:
                    continue
                seen.add(oid)
                if q and q.lower() not in (r["name"] or "").lower():
                    continue
                out.append({
                    "oracle_id": oid, "name": r["name"], "card_id": r["card_id"],
                    "color_identity": r["scryfall_ci"], "type_line": r["scryfall_type_line"],
                    "image_uri": r["image_uri"], "commander_legality": r["commander_legality"],
                    "available": available.get(oid, 0),
                    "locations": sorted(loc_map.get(oid, set())),
                    "favorite": bool(r["favorite"]), "excluded": bool(r["excluded"]),
                    "note": r["mark_note"],
                })
            from .reference import reference_map
            refs = reference_map(s, [c["oracle_id"] for c in out])
            for c in out:
                c["reference"] = refs.get(c["oracle_id"])
            return out

    @app.post("/api/marks")
    def marks(mark: MarkIn) -> dict:
        with _store() as s:
            s.conn.execute(
                "INSERT OR REPLACE INTO mark(oracle_id,collection_id,favorite,excluded,note)"
                " VALUES(?,?,?,?,?)",
                (mark.oracle_id, mark.collection_id, int(mark.favorite),
                 int(mark.excluded), mark.note))
            s.conn.commit()
        return {"ok": True}

    @app.get("/api/commanders")
    def commanders(collection_id: str) -> dict:
        with _store() as s:
            return commander_candidates(s, collection_id)

    @app.get("/api/pool")
    def pool(collection_id: str, commander: list[str] = Query(...)) -> list[dict]:
        with _store() as s:
            rows = decks_mod.legal_pool(s, collection_id, commander)
            from .reference import reference_map
            refs = reference_map(s, [r["oracle_id"] for r in rows])
            for r in rows:
                r["reference"] = refs.get(r["oracle_id"])
            return rows

    @app.post("/api/decks/validate")
    def validate(body: DeckIn) -> dict:
        with _store() as s:
            return decks_mod.validate_deck(s, body.collection_id,
                                           body.commander_oracle_ids, body.entries)

    @app.post("/api/decks")
    def create_deck(body: DeckIn) -> dict:
        with _store() as s:
            return decks_mod.create_deck(s, body.collection_id, body.name,
                                         body.commander_oracle_ids, body.entries,
                                         note=body.note,
                                         parent_revision_id=body.parent_revision_id)

    @app.get("/api/decks/{revision_id}/export", response_class=PlainTextResponse)
    def export(revision_id: str) -> str:
        with _store() as s:
            text = decks_mod.export_revision(s, revision_id)
            if not text.strip():
                raise HTTPException(404, "revision not found")
            return text

    @app.get("/api/decks/compare")
    def compare(a: str, b: str) -> dict:
        with _store() as s:
            return decks_mod.compare_revisions(s, a, b)

    @app.post("/api/sync/commander-jobs")
    def commander_jobs(commander_oracle_id: str, slug: str | None = None) -> dict:
        with _store() as s:
            return {"jobs_registered": register_commander_jobs(s, commander_oracle_id, slug),
                    "status": "NOT_FETCHED"}

    @app.post("/api/sync/card-atlas-jobs")
    def atlas_jobs(collection_id: str) -> dict:
        with _store() as s:
            return {"jobs_registered": register_card_atlas_jobs(s, collection_id),
                    "status": "NOT_FETCHED"}

    # -- Phase 2: external data views (local snapshots only; the UI never
    #    triggers live scraping) -----------------------------------------
    def _snap_dict(s: Store, source: str, kind: str, **kw) -> dict | None:
        row = latest_snapshot(s, source, kind, **kw)
        if row is None:  # fall back to any parser version -> visible as STALE
            row = latest_snapshot(s, source, kind, parser_version=None, **kw)
            if row is None:
                return None
            d = dict(row)
            d["status"] = "STALE"
            d["detail"] = (d.get("detail") or "") + " [parser version changed; re-sync to refresh]"
            return d
        return dict(row)

    @app.get("/api/external/commander")
    def external_commander(commander_oracle_id: str,
                           collection_id: str | None = None) -> dict:
        with _store() as s:
            available = s.available_by_oracle(collection_id) if collection_id else {}
            loc_map: dict[str, set] = {}
            if collection_id:
                for x in s.inventory_rows(collection_id):
                    loc_map.setdefault(x["oracle_id"], set()).add(x["location_id"])
            by_name = {}
            for r in s.conn.execute("SELECT oracle_id, name, front_name FROM scryfall_card"):
                by_name[r["name"]] = r["oracle_id"]
                if r["front_name"]:
                    by_name.setdefault(r["front_name"], r["oracle_id"])
            out: dict = {"commander_oracle_id": commander_oracle_id, "edhrec": {},
                         "playgroup": None}
            for bracket in ("core", "upgraded", "optimized"):
                entry: dict = {}
                stats = _snap_dict(s, "edhrec", "edhrec_stats",
                                   commander_oracle_id=commander_oracle_id, bracket=bracket)
                if stats:
                    cards = []
                    if stats["status"] != "STALE":
                        for c in s.conn.execute(
                                "SELECT * FROM edhrec_card_stat WHERE snapshot_id=? "
                                "ORDER BY category, num_decks DESC", (stats["snapshot_id"],)):
                            oid = by_name.get(c["name"])
                            if oid is not None and oid not in loc_map:
                                oid = None  # known to Scryfall, but NOT in this collection
                            cards.append({**dict(c), "owned_oracle_id": oid,
                                          "owned_available": available.get(oid, 0) if oid else 0,
                                          "owned_locations": sorted(loc_map.get(oid, set())) if oid else []})
                    stats.pop("payload_json", None)
                    entry["stats"] = {**stats, "cards": cards}
                decks_snap = _snap_dict(s, "edhrec", "edhrec_decks",
                                        commander_oracle_id=commander_oracle_id, bracket=bracket)
                if decks_snap:
                    entries = []
                    if decks_snap["status"] != "STALE":
                        entries = [dict(r) for r in s.conn.execute(
                            "SELECT * FROM edhrec_deck_entry WHERE snapshot_id=? "
                            "ORDER BY savedate DESC", (decks_snap["snapshot_id"],))]
                    decks_snap.pop("payload_json", None)
                    entry["decks"] = {**decks_snap, "entries": entries}
                out["edhrec"][bracket] = entry
            pg = _snap_dict(s, "playgroup", "playgroup_commander",
                            commander_oracle_id=commander_oracle_id)
            if pg:
                payload = pg.pop("payload_json", None)
                out["playgroup"] = {**pg, "data": json.loads(payload) if payload else None}
            return out

    @app.get("/api/external/card")
    def external_card(oracle_id: str, collection_id: str | None = None) -> dict:
        with _store() as s:
            snap = _snap_dict(s, "playgroup", "playgroup_card", oracle_id=oracle_id)
            if snap is None:
                return {"oracle_id": oracle_id, "status": "NOT_FETCHED"}
            payload = snap.pop("payload_json", None)
            out = {**snap, "data": json.loads(payload) if payload else None}
            if collection_id:
                available = s.available_by_oracle(collection_id)
                out["owned_available"] = available.get(oracle_id, 0)
                out["owned_locations"] = sorted(
                    {x["location_id"] for x in s.inventory_rows(collection_id)
                     if x["oracle_id"] == oracle_id})
            return out

    @app.get("/api/external/status")
    def external_status(collection_id: str = "foundation-schwarze-box") -> dict:
        with _store() as s:
            summary = s._external_summary()
            summary["card_atlas"] = card_atlas_coverage(s, collection_id)
            return summary

    return app


app = create_app()
