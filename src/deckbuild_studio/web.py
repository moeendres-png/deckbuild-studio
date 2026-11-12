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


_TYPE_SORT_ORDER = ("Creature", "Planeswalker", "Battle", "Instant",
                    "Sorcery", "Artifact", "Enchantment", "Land")


def _sort_cards(s: Store, out: list[dict], sort: str) -> None:
    """In-place sort of card dicts (name / front-face main type /
    mana value; name is always the tiebreaker)."""
    from .queries import main_type
    if sort == "type":
        order = {t: i for i, t in enumerate(_TYPE_SORT_ORDER)}
        out.sort(key=lambda c: (order.get(main_type(c.get("type_line")), 99),
                                (c.get("name") or "").lower()))
    elif sort == "mana_value":
        mv = {r["oracle_id"]: r["mana_value"] for r in s.conn.execute(
            "SELECT oracle_id, mana_value FROM scryfall_card")}
        out.sort(key=lambda c: (mv.get(c["oracle_id"]) is None,
                                mv.get(c["oracle_id"]) or 0.0,
                                (c.get("name") or "").lower()))
    else:
        out.sort(key=lambda c: (c.get("name") or "").lower())


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
    def cards(collection_id: str, q: str = "", commander_oracle_id: str | None = None,
              card_type: str | None = Query(None, alias="type"),
              subtype: str | None = None, supertype: str | None = None,
              keyword: str | None = None,
              category: str | None = None, category_origin: str | None = None,
              sort: str = "name") -> list[dict]:
        """Collection browser. Category-layer filters (all optional,
        combinable): ``type`` / ``subtype`` / ``supertype`` facts and
        ``keyword`` match ANY face of a card; ``category`` matches a
        function category (role), optionally restricted to one origin
        layer via ``category_origin``. ``sort``: name (default) |
        type | mana_value."""
        with _store() as s:
            available = s.available_by_oracle(collection_id)
            rows_all = s.inventory_rows(collection_id)
            loc_map: dict[str, set] = {}
            for x in rows_all:
                loc_map.setdefault(x["oracle_id"], set()).add(x["location_id"])
            # QA P1.9: commander_oracle_id is a real commander CONTEXT,
            # not a ignored parameter — each card is flagged with its
            # legality / color-identity fit / pool membership for that
            # commander (same rules as decks.legal_pool).
            cmd_ci: set[str] | None = None
            if commander_oracle_id is not None:
                cmd = s.scryfall(commander_oracle_id)
                if cmd is None:
                    raise HTTPException(
                        404, f"commander {commander_oracle_id} not in Scryfall store")
                cmd_ci = set(cmd["color_identity"] or "")
            out, seen = [], set()
            for r in rows_all:
                oid = r["oracle_id"]
                if oid in seen:
                    continue
                seen.add(oid)
                if q and q.lower() not in (r["name"] or "").lower():
                    continue
                entry = {
                    "oracle_id": oid, "name": r["name"], "card_id": r["card_id"],
                    "color_identity": r["scryfall_ci"], "type_line": r["scryfall_type_line"],
                    "image_uri": r["image_uri"], "commander_legality": r["commander_legality"],
                    "available": available.get(oid, 0),
                    "locations": sorted(loc_map.get(oid, set())),
                    "favorite": bool(r["favorite"]), "excluded": bool(r["excluded"]),
                    "note": r["mark_note"],
                }
                if cmd_ci is not None:
                    in_identity = set(r["scryfall_ci"] or "") <= cmd_ci
                    is_legal = r["commander_legality"] == "legal"
                    entry["commander_legal"] = is_legal
                    entry["in_commander_identity"] = in_identity
                    entry["in_commander_pool"] = bool(
                        is_legal and in_identity and oid != commander_oracle_id
                        and available.get(oid, 0) > 0)
                out.append(entry)
            from .reference import reference_map
            from .roles import roles_map
            from .tierlist import tiers_map
            refs = reference_map(s, [c["oracle_id"] for c in out])
            roles = roles_map(s, [c["oracle_id"] for c in out])
            tiers = tiers_map(s, [c["oracle_id"] for c in out])
            for c in out:
                c["reference"] = refs.get(c["oracle_id"])
                c["roles"] = roles.get(c["oracle_id"], {})
                c["tier"] = tiers.get(c["oracle_id"])
            # --- category-layer filters + sorting -------------------
            from . import categories as cat_mod
            allowed = cat_mod.filter_oracle_ids(
                s, types=[card_type] if card_type else None,
                subtypes=[subtype] if subtype else None,
                supertypes=[supertype] if supertype else None,
                keywords=[keyword] if keyword else None,
                collection_id=collection_id)
            if allowed is not None:
                out = [c for c in out if c["oracle_id"] in allowed]
            if category:
                out = [c for c in out if category in c["roles"] and (
                    category_origin is None
                    or category_origin in c["roles"][category])]
            infos = cat_mod.card_type_info(s, [c["oracle_id"] for c in out])
            for c in out:
                c["type_info"] = infos.get(c["oracle_id"], {
                    "faces": [], "supertypes": [], "types": [],
                    "subtypes": [], "keywords": []})
            _sort_cards(s, out, sort)
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
    def pool(collection_id: str, commander: list[str] = Query(...),
             role: str | None = None,
             card_type: str | None = Query(None, alias="type"),
             subtype: str | None = None, keyword: str | None = None,
             category_origin: str | None = None,
             sort: str = "name") -> list[dict]:
        with _store() as s:
            rows = decks_mod.legal_pool(s, collection_id, commander)
            from .reference import reference_map
            from .roles import roles_map
            from .tierlist import tiers_map
            refs = reference_map(s, [r["oracle_id"] for r in rows])
            roles = roles_map(s, [r["oracle_id"] for r in rows])
            tiers = tiers_map(s, [r["oracle_id"] for r in rows])
            for r in rows:
                r["reference"] = refs.get(r["oracle_id"])
                r["roles"] = roles.get(r["oracle_id"], {})
                r["tier"] = tiers.get(r["oracle_id"])
            if role:
                rows = [r for r in rows if role in r["roles"] and (
                    category_origin is None
                    or category_origin in r["roles"][role])]
            from . import categories as cat_mod
            allowed = cat_mod.filter_oracle_ids(
                s, types=[card_type] if card_type else None,
                subtypes=[subtype] if subtype else None,
                keywords=[keyword] if keyword else None,
                collection_id=collection_id)
            if allowed is not None:
                rows = [r for r in rows if r["oracle_id"] in allowed]
            infos = cat_mod.card_type_info(s, [r["oracle_id"] for r in rows])
            for r in rows:
                r["type_info"] = infos.get(r["oracle_id"], {
                    "faces": [], "supertypes": [], "types": [],
                    "subtypes": [], "keywords": []})
            _sort_cards(s, rows, sort)
            return rows

    @app.get("/api/categories")
    def categories_endpoint(collection_id: str | None = None) -> dict:
        """Category layer at a glance: taxonomy, per-layer coverage
        (incl. 'checked, no category'), per-category counts, tagger
        sync status, and the filter facets (types/subtypes/keywords
        present in the universe) for the UI selects."""
        from .categories import category_report, facet_counts
        with _store() as s:
            report = category_report(s, collection_id)
            report["facets"] = facet_counts(s, collection_id)
            return report

    @app.get("/api/roles")
    def roles(collection_id: str | None = None) -> dict:
        from .roles import ROLE_LABELS_DE, ROLES, role_counts
        with _store() as s:
            ids = None
            if collection_id:
                ids = [str(r["oracle_id"]) for r in s.conn.execute(
                    "SELECT DISTINCT oracle_id FROM physical_lot "
                    "WHERE collection_id = ?", (collection_id,))]
            counts = role_counts(s, ids)
            return {"taxonomy": ROLES, "labels_de": ROLE_LABELS_DE,
                    "heuristic_label": "Heuristik aus Oracle-Text "
                                       "(lokal abgeleitet, keine Beobachtung)",
                    **counts}

    @app.get("/api/data-report")
    def data_report() -> dict:
        from .report import data_report as build_report
        with _store() as s:
            return build_report(s)

    # -- Tierlist (docs/TIERLIST_DESIGN.md; computed locally from
    #    snapshots by `compute-tiers`, never edited, marks-free) -------
    @app.get("/api/tiers")
    def tiers(scope: str = "global", commander_oracle_id: str | None = None,
              bracket: str | None = None, tier: str | None = None,
              collection_id: str | None = None,
              universe_id: str | None = None) -> list[dict]:
        from .tierlist import list_tiers
        with _store() as s:
            return list_tiers(s, scope=scope,
                              commander_oracle_id=commander_oracle_id,
                              bracket=bracket, tier=tier,
                              collection_id=collection_id,
                              universe_id=universe_id)

    @app.get("/api/tiers/universes")
    def tier_universes() -> list[dict]:
        from .tierlist import list_universes
        with _store() as s:
            return list_universes(s)

    @app.get("/api/verbreitung")
    def verbreitung() -> dict:
        from .tierlist import verbreitung_summary
        with _store() as s:
            return verbreitung_summary(s)

    @app.get("/api/cards/{oracle_id}/cooccurrence")
    def card_cooccurrence(oracle_id: str,
                          commander_oracle_id: str | None = None,
                          limit: int = 25) -> dict:
        from .inclusion import cooccurrence
        with _store() as s:
            return cooccurrence(s, oracle_id,
                                commander_oracle_id=commander_oracle_id,
                                limit=limit)

    @app.get("/api/tiers/card/{oracle_id}")
    def tier_card(oracle_id: str, commander_oracle_id: str | None = None,
                  bracket: str | None = None,
                  universe_id: str | None = None) -> dict:
        from .tierlist import get_tier
        with _store() as s:
            out: dict = {"oracle_id": oracle_id,
                         "global": get_tier(s, oracle_id)}
            if commander_oracle_id is not None:
                out["context"] = get_tier(
                    s, oracle_id, commander_oracle_id=commander_oracle_id,
                    bracket=bracket)
                out["context_status"] = (
                    "AVAILABLE" if out["context"] is not None
                    else "NOT_FETCHED")
            if universe_id is not None:
                out["universe"] = get_tier(s, oracle_id,
                                           universe_id=universe_id)
                out["universe_status"] = (
                    "AVAILABLE" if out["universe"] is not None
                    else "NOT_FETCHED")
            return out

    @app.get("/api/stats/inclusion")
    def inclusion(collection_id: str) -> dict:
        from .queries import own_deck_inclusion
        with _store() as s:
            return own_deck_inclusion(s, collection_id)

    @app.get("/api/settings")
    def get_settings() -> dict:
        from . import settings as settings_mod
        with _store() as s:
            return settings_mod.all_settings(s)

    @app.put("/api/settings")
    def put_settings(body: dict) -> dict:
        from . import settings as settings_mod
        if not isinstance(body, dict) or not body:
            raise HTTPException(400, "expected a JSON object of setting keys")
        with _store() as s:
            try:
                # atomic: validate ALL values first — one invalid key must
                # not leave earlier keys of the same request applied
                for key, value in body.items():
                    settings_mod.validate_setting(key, value)
                for key, value in body.items():
                    settings_mod.set_setting(s, key, value)
            except settings_mod.SettingError as exc:
                raise HTTPException(400, str(exc)) from exc
            return settings_mod.all_settings(s)

    @app.get("/api/inclusion")
    def inclusion_engine(commander_oracle_id: str | None = None,
                         collection_id: str | None = None) -> dict:
        """Inclusion per current owner settings — every result set carries
        its cohort definition (source, brackets, denominator, sufficiency)."""
        from .inclusion import compute_inclusion
        with _store() as s:
            return compute_inclusion(s, commander_oracle_id=commander_oracle_id,
                                     collection_id=collection_id)

    @app.get("/img/{oracle_id}")
    def img(oracle_id: str, fetch: int = 1) -> FileResponse:
        from .images import cached_image
        with _store() as s:
            path = cached_image(s, oracle_id, fetch=bool(fetch))
        if path is None:
            raise HTTPException(404, "no cached image")
        return FileResponse(path, media_type="image/jpeg")

    @app.post("/api/decks/validate")
    def validate(body: DeckIn) -> dict:
        with _store() as s:
            result = decks_mod.validate_deck(s, body.collection_id,
                                             body.commander_oracle_ids,
                                             body.entries)
            from .queries import deck_shape, draw_probabilities
            from .roles import deck_role_counts
            entries = dict(body.entries)
            for oid in body.commander_oracle_ids:
                entries.setdefault(oid, 1)
            shape = deck_shape(s, entries)
            result["shape"] = shape
            result["roles"] = deck_role_counts(s, entries)
            # deck view grouped by primary function category
            from .roles import ROLES as _TAXONOMY
            from .roles import roles_map as _roles_map
            rmap = _roles_map(s, list(entries))
            groups: dict[str, list[dict]] = {}
            for oid, qty in entries.items():
                found = rmap.get(oid, {})
                primary = next((r for r in _TAXONOMY if r in found), None)
                if primary is None and found:
                    primary = sorted(found)[0]
                groups.setdefault(primary or "none", []).append(
                    {"oracle_id": oid, "quantity": qty})
            result["role_groups"] = groups
            size = shape["total_cards"] or (
                len(body.commander_oracle_ids) + sum(body.entries.values()))
            result["draw_probabilities"] = draw_probabilities(
                size, shape["lands"])
            return result

    @app.post("/api/decks")
    def create_deck(body: DeckIn) -> dict:
        with _store() as s:
            try:
                return decks_mod.create_deck(s, body.collection_id, body.name,
                                             body.commander_oracle_ids, body.entries,
                                             note=body.note,
                                             parent_revision_id=body.parent_revision_id)
            except LookupError as exc:
                # unknown parent revision (QA round 2, PR #5)
                raise HTTPException(404, str(exc)) from exc
            except ValueError as exc:
                # cross-collection parent revision (QA round 2, PR #5)
                raise HTTPException(409, str(exc)) from exc

    @app.get("/api/decks")
    def list_decks(collection_id: str) -> list[dict]:
        with _store() as s:
            return decks_mod.list_decks(s, collection_id)

    @app.get("/api/decks/revision/{revision_id}")
    def get_revision(revision_id: str) -> dict:
        with _store() as s:
            status = decks_mod.revision_status(s, revision_id)
            if status is None:
                raise HTTPException(404, "revision not found")
            rev = s.conn.execute("SELECT * FROM deck_revision WHERE revision_id=?",
                                 (revision_id,)).fetchone()
            deck = s.conn.execute("SELECT * FROM deck WHERE deck_id=?",
                                  (rev["deck_id"],)).fetchone()
            commanders, entries = decks_mod.revision_entries(s, revision_id)
            return {"revision_id": revision_id, "deck_id": rev["deck_id"],
                    "name": deck["name"], "collection_id": deck["collection_id"],
                    "parent_revision_id": rev["parent_revision_id"],
                    "deck_hash": rev["deck_hash"], "status": status,
                    "note": rev["note"], "created_at": rev["created_at"],
                    "commander_oracle_ids": commanders, "entries": entries}

    @app.get("/api/decks/{deck_id}/revisions")
    def list_revisions(deck_id: str) -> list[dict]:
        with _store() as s:
            if s.conn.execute("SELECT 1 FROM deck WHERE deck_id=?",
                              (deck_id,)).fetchone() is None:
                raise HTTPException(404, "deck not found")
            return decks_mod.list_revisions(s, deck_id)

    @app.delete("/api/decks/{deck_id}")
    def delete_deck(deck_id: str) -> dict:
        with _store() as s:
            if not decks_mod.delete_deck(s, deck_id):
                raise HTTPException(404, "deck not found")
            return {"ok": True, "deleted": deck_id}

    @app.get("/api/decks/{revision_id}/export")
    def export(revision_id: str, legal_only: bool = False) -> PlainTextResponse:
        with _store() as s:
            status = decks_mod.revision_status(s, revision_id)
            if status is None:
                raise HTTPException(404, "revision not found")
            try:
                text = decks_mod.export_revision(s, revision_id, require_legal=legal_only)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
            # QA P0.2: the deck status travels with the export as a field.
            return PlainTextResponse(text, headers={"X-Deck-Status": status})

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
            from .edhtop16 import card_edhtop16
            from .rulings import card_rulings
            from .topdeck import card_topdeck
            snap = _snap_dict(s, "playgroup", "playgroup_card", oracle_id=oracle_id)
            if snap is None:
                out = {"oracle_id": oracle_id, "status": "NOT_FETCHED"}
            else:
                payload = snap.pop("payload_json", None)
                out = {**snap, "data": json.loads(payload) if payload else None}
            # Data expansion 2: official Scryfall rulings + EDHTop16
            # tournament play rate of this card (each honest about its
            # own sync state; empty/absent is data, never an error).
            out["rulings"] = card_rulings(s, oracle_id)
            out["edhtop16"] = card_edhtop16(s, oracle_id)
            # TopDeck.gg tournament lists: conversion + win rate are
            # computed locally from the stored lists (EDHTop16 does not
            # publish them); attribution per Developer Terms section 6.1
            # travels with the payload and is rendered next to the data.
            out["topdeck"] = card_topdeck(s, oracle_id)
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
            # All remaining data layers, each from its own coverage
            # function (same sources the CLI sync/coverage paths use);
            # a layer that never synced answers NOT_FETCHED honestly.
            from .categories import category_report
            from .edhtop16 import (edhtop16_commander_coverage,
                                   edhtop16_coverage)
            from .mtgjson import mtgjson_coverage
            from .rulings import rulings_coverage
            from .topdeck import topdeck_coverage
            summary["rulings"] = rulings_coverage(s, collection_id)
            summary["edhtop16"] = edhtop16_coverage(s, collection_id)
            summary["edhtop16_commanders"] = edhtop16_commander_coverage(
                s, collection_id)
            summary["mtgjson"] = mtgjson_coverage(s, collection_id)
            summary["topdeck"] = topdeck_coverage(s, collection_id)
            summary["categories"] = category_report(s, collection_id)
            return summary

    return app


app = create_app()
