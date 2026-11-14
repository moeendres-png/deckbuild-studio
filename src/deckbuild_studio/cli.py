"""CLI ``mtg-deckbuilder`` — follows the target repo README contract.

Commands:
  import-inventory "<xlsx>" [--mapping mapping.json] [--mode upsert|replace-snapshot]
      Normalized workbook, Foundation/Schwarze-Box workbook, or a generic
      CSV/XLSX via explicit mapping. (alias: import-collection)
  import-scryfall "<default-cards.jsonl.gz>"
  sync-scryfall          download the public Scryfall bulk catalogue only
  normalization-report   reconciliation + commander counts per collection
  commanders             list eligible commanders of a collection
  cache-status           store / cache / sync-job status (EDHREC+Playgroup: NOT_FETCHED)
  sync-commander-data    register Phase-2 jobs for a commander (NOT_FETCHED)
  sync-card-atlas        register Phase-2 Card-Atlas jobs for a collection (NOT_FETCHED)
  import-reference-data  import card reference data reused from
                         commander-playtest-lab (--commander-flags / --role-profiles)
  sync-decklists         harvest REAL public deck lists per commander x
                         bracket cohort (Archidekt API; EDHREC deck entries
                         are metadata only and their deckpreview route is
                         robots-disallowed — see docs/DECKLISTS_AND_SETTINGS.md);
                         --targeted re-lists only the cohorts below
                         --min-canonical canonical decks (empty cohorts
                         included), --cohorts-file takes an explicit
                         [{"commander": oracle_id|name, "bracket": n}] list
  import-browser-decklists "<decklists_browser.jsonl>"
                         import FULL deck lists harvested by the browser
                         tool from EDHREC/Moxfield pages (only AVAILABLE
                         records; the records carry no bracket — the
                         decks land bracket-less under browser:edhrec /
                         browser:moxfield, see docs/DECKLISTS_AND_SETTINGS.md)
  settings list|get|set  owner settings (inclusion source/cohorts/…)
  inclusion              inclusion figures WITH their cohort definition
                         (per settings; --commander for a commander context,
                         --collection alone = legacy own-deck inclusion)
  import-marks           merge the owner's marks (favorite/excluded/note)
                         from a marks JSON (deckbuild-marks-1 or upstream
                         studio-marks-1)
  export-marks           write this collection's marks as deckbuild-marks-1
  apply-card-id-registry replace generated card_ids by the known ids of a
                         registry file (JSON/CSV oracle_id -> card_id)
  derive-card-types      derive per-face type facts (supertypes / types /
                         subtypes) + Scryfall keywords from the local bulk
                         catalogue (offline; --bulk for an explicit file)
  sync-tagger            sync Scryfall Tagger functional tags from the
                         official oracle_tags bulk download (subtree
                         sets per tag; --via-search for the Search-API
                         route), snapshots + claims per tag; claims land
                         in card_role under origin SCRYFALL_TAGGER_SEARCH
  sync-rulings           sync the official Scryfall rulings bulk file
                         (index first, current jsonl_download_uri),
                         normalized into card_ruling under a snapshot
  sync-edhtop16          sync EDHTop16 card play rates (last year) from
                         the public staples page (embedded SSR payload);
                         conversion/entries are not published there and
                         stay absent (see docs/EXTERNAL_DATA.md)
  sync-topdeck           sync TopDeck.gg EDH tournament deck lists +
                         player results via the official API v2
                         (credential only through the custom.topdeck
                         connector); per-card top-cut conversion and
                         win rate are computed locally from the lists
                         (see docs/TOPDECK.md)
  sync-edhtop16-commanders
                         sync per-card x commander EDHTop16 play rates
                         (+ commander entry totals) for all eligible
                         commanders via the EDHTop16 API (persisted
                         queries; ToS § API Usage provides the API for
                         developers); conversion stays a commander-level
                         aggregate only — per-card conversion is not
                         published and stays absent
  sync-mtgjson           sync the MTGJSON card-data slice for the
                         collection (printing mapping + foreign-language
                         print names) from the local AllPrintings bulk
                         file in <data>/mtgjson (download it first with
                         --download); no prices, no purchase data
  category-report        coverage of all category layers (types /
                         heuristic / profile / tagger), counts only
  serve                  web UI on http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import data_dir, database_path
from .importers import ImportFailure, detect_and_import, normalization_report
from .scryfall import import_scryfall, sync_scryfall
from .store import Store


def _print(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mtg-deckbuilder")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("import-inventory", aliases=["import-collection"])
    inv.add_argument("path")
    inv.add_argument("--mapping", help="explicit column-mapping JSON (generic format)")
    inv.add_argument("--mode", default="upsert", choices=["upsert", "replace-snapshot"],
                     help="upsert never deletes missing rows; replace-snapshot is explicit + audited")
    inv.add_argument("--card-id-registry",
                     help="optional card_id registry file (JSON/CSV oracle_id -> card_id); "
                          "known card_ids are used instead of generated ones")

    sf = sub.add_parser("import-scryfall")
    sf.add_argument("path")

    sub.add_parser("sync-scryfall")
    sub.add_parser("normalization-report")
    sub.add_parser("cache-status")

    cmd = sub.add_parser("commanders")
    cmd.add_argument("--collection", default="foundation-schwarze-box")

    scd = sub.add_parser("sync-commander-data")
    scd.add_argument("commander_oracle_id", nargs="?",
                     help="oracle_id from the local Scryfall store; omit with --name")
    scd.add_argument("--name", help="commander name (e.g. for commanders not in the collection)")
    scd.add_argument("--slug", help="EDHREC slug candidate (always verified against the page)")
    scd.add_argument("--source", default="all", choices=["all", "edhrec", "playgroup"])
    scd.add_argument("--base", action="store_true", help="also fetch the EDHREC base views")
    scd.add_argument("--force", action="store_true", help="refetch even if a current snapshot exists")

    sca = sub.add_parser("sync-card-atlas")
    sca.add_argument("--collection", default="foundation-schwarze-box")
    sca.add_argument("--limit", type=int, help="max NEW fetches this run (sync is resumable)")
    sca.add_argument("--force", action="store_true")

    sec = sub.add_parser("sync-edhrec-cards")
    sec.add_argument("--collection", default="foundation-schwarze-box")
    sec.add_argument("--limit", type=int, help="max NEW fetches this run (sync is resumable)")
    sec.add_argument("--force", action="store_true")

    ssb = sub.add_parser("sync-spellbook")
    ssb.add_argument("--collection", default="foundation-schwarze-box")
    ssb.add_argument("--limit", type=int, help="max NEW cards this run (sync is resumable)")
    ssb.add_argument("--force", action="store_true")
    ssb.add_argument("--max-pages", type=int, default=5,
                     help="max search pages per card (50 combos per page)")

    scp = sub.add_parser("sync-commander-page")
    scp.add_argument("commander_oracle_id", nargs="?",
                     help="oracle_id from the local Scryfall store; omit with --name")
    scp.add_argument("--name", help="commander name")
    scp.add_argument("--force", action="store_true")

    dpf = sub.add_parser("derive-print-facts")
    dpf.add_argument("--path", help="bulk file (default: <data>/scryfall/default-cards.jsonl.gz)")

    imk = sub.add_parser("import-marks")
    imk.add_argument("path")
    imk.add_argument("--collection", help="collection_id (default: the only collection)")

    emk = sub.add_parser("export-marks")
    emk.add_argument("path")
    emk.add_argument("--collection", help="collection_id (default: the only collection)")

    acr = sub.add_parser("apply-card-id-registry")
    acr.add_argument("path", help="registry file (JSON/CSV oracle_id -> card_id)")

    ref = sub.add_parser("import-reference-data")
    ref.add_argument("--commander-flags", help="commander_flags.json from commander-playtest-lab")
    ref.add_argument("--role-profiles", help="structural_role_profiles.json from commander-playtest-lab")

    inv_cache = sub.add_parser("cache-invalidate")
    inv_cache.add_argument("--source", choices=["edhrec", "playgroup"])
    inv_cache.add_argument("--kind")

    rr = sub.add_parser("rebuild-roles")
    rr.add_argument("--collection", help="restrict the role summary to a collection")

    dct = sub.add_parser("derive-card-types")
    dct.add_argument("--bulk", help="explicit Scryfall bulk file "
                                    "(default: the file next to the database)")

    stg = sub.add_parser("sync-tagger")
    stg.add_argument("--tag", action="append", dest="tags",
                     help="sync only this tag (repeatable); default: full vocabulary")
    stg.add_argument("--max-pages", type=int,
                     help="cap pages per tag (run is then recorded PARTIAL)")
    stg.add_argument("--force", action="store_true",
                     help="refetch tags even when a current snapshot exists")
    stg.add_argument("--via-search", action="store_true",
                     help="use the Search-API route instead of the default "
                          "oracle_tags bulk download")
    stg.add_argument("--bulk-file",
                     help="sync from this local oracle_tags .jsonl.gz "
                          "instead of downloading the current bulk file")

    sru = sub.add_parser("sync-rulings")
    sru.add_argument("--collection", default="foundation-schwarze-box")
    sru.add_argument("--force", action="store_true",
                     help="redownload even if the bulk file is unchanged")

    set16 = sub.add_parser("sync-edhtop16")
    set16.add_argument("--collection", default="foundation-schwarze-box")
    set16.add_argument("--force", action="store_true")

    std = sub.add_parser("sync-topdeck")
    std.add_argument("--collection", default="foundation-schwarze-box")
    std.add_argument("--force", action="store_true",
                     help="refetch even when a current snapshot for this "
                          "exact window exists")
    std.add_argument("--months", type=int, default=12,
                     help="window length in calendar months back from "
                          "--end (default 12; ignored when --start is set)")
    std.add_argument("--start", type=int,
                     help="window start as unix seconds (overrides --months)")
    std.add_argument("--end", type=int,
                     help="window end as unix seconds (default: now)")
    std.add_argument("--window-days", type=int, default=7,
                     help="sub-window size in days (one paced API request "
                          "each; default 7)")
    std.add_argument("--doc-budget", type=int, default=950000,
                     help="stop (PARTIAL) before this many API documents "
                          "are consumed in one run (default 950000; the "
                          "account limit is 1,000,000 per UTC day)")

    set16c = sub.add_parser("sync-edhtop16-commanders")
    set16c.add_argument("--collection", default="foundation-schwarze-box")
    set16c.add_argument("--force", action="store_true")
    set16c.add_argument("--limit", type=int,
                        help="stop after this many commanders (resumable)")

    smj = sub.add_parser("sync-mtgjson")
    smj.add_argument("--collection", default="foundation-schwarze-box")
    smj.add_argument("--download", action="store_true",
                     help="download the MTGJSON AllPrintings bulk file "
                          "into <data>/mtgjson first (size is reported)")
    smj.add_argument("--dir", help="directory with the MTGJSON bulk "
                                   "file (default: <data>/mtgjson)")

    crp = sub.add_parser("category-report")
    crp.add_argument("--collection", help="restrict coverage to a collection")

    fi = sub.add_parser("fetch-images")
    fi.add_argument("--collection", required=True)
    fi.add_argument("--limit", type=int)

    sub.add_parser("data-report")

    inc = sub.add_parser("inclusion")
    inc.add_argument("--collection")
    inc.add_argument("--commander",
                     help="commander oracle_id: inclusion engine per current "
                          "settings (source/cohorts from `settings`)")

    sdl = sub.add_parser("sync-decklists")
    sdl.add_argument("--collection", default="foundation-schwarze-box")
    sdl.add_argument("--commander", help="single commander oracle_id (default: "
                                         "all eligible commanders of the collection)")
    sdl.add_argument("--brackets", default="2,3,4",
                     help="comma-separated bracket levels (default 2,3,4)")
    sdl.add_argument("--max-per-cohort", type=int, default=300,
                     help="cap of deck lists fetched per commander x bracket cohort")
    sdl.add_argument("--targeted", action="store_true",
                     help="re-list ONLY the cohorts whose canonical stored "
                          "deck count is below --min-canonical (empty "
                          "cohorts included); full cohorts are not listed")
    sdl.add_argument("--min-canonical", type=int, default=30,
                     help="canonical-deck threshold of the --targeted plan "
                          "(default 30)")
    sdl.add_argument("--cohorts-file",
                     help="explicit cohort list as JSON file: "
                          "[{\"commander\": oracle_id or exact name, "
                          "\"bracket\": level}] — these cohorts (and only "
                          "these) are re-listed")

    ibd = sub.add_parser("import-browser-decklists")
    ibd.add_argument("path", help="browser-harvest JSONL file "
                                  "(decklists_browser.jsonl)")

    st = sub.add_parser("settings")
    st_sub = st.add_subparsers(dest="settings_command", required=True)
    st_sub.add_parser("list")
    st_get = st_sub.add_parser("get")
    st_get.add_argument("key")
    st_set = st_sub.add_parser("set")
    st_set.add_argument("key")
    st_set.add_argument("value", help="JSON value (e.g. '\"decklists\"', '[2,3]', '10', 'null')")

    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    store = Store(database_path())
    try:
        if args.command in {"import-inventory", "import-collection"}:
            mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8")) if args.mapping else None
            try:
                _print(detect_and_import(store, args.path, mapping=mapping, mode=args.mode,
                                         card_id_registry=args.card_id_registry))
            except ImportFailure as exc:
                _print({"import": "FAILED", **exc.report})
                return 2
        elif args.command == "apply-card-id-registry":
            from .importers import apply_card_id_registry, load_card_id_registry
            try:
                _print(apply_card_id_registry(store, load_card_id_registry(args.path)))
            except ImportFailure as exc:
                _print({"import": "FAILED", **exc.report})
                return 2
        elif args.command == "import-scryfall":
            _print(import_scryfall(store, args.path))
        elif args.command == "sync-scryfall":
            _print(sync_scryfall(store, target_dir=data_dir() / "scryfall"))
        elif args.command == "normalization-report":
            _print(normalization_report(store))
        elif args.command == "cache-status":
            _print(store.status())
        elif args.command == "commanders":
            from .commander import commander_candidates
            result = commander_candidates(store, args.collection)
            _print({"eligible": [{"name": c["name"], "oracle_id": c["oracle_id"],
                                  "color_identity": c["color_identity"],
                                  "available": c["available"], "reason": c["reason"]}
                                 for c in result["eligible"]],
                    "needs_review": result["needs_review"]})
        elif args.command == "sync-commander-data":
            from .external import sync_edhrec, sync_playgroup_commander
            from .httpfetch import Fetcher
            name = args.name
            oid = args.commander_oracle_id
            if oid and not name:
                row = store.scryfall(oid)
                if row is None:
                    _print({"error": f"oracle_id {oid} not in local Scryfall store; "
                                     "pass --name explicitly"})
                    return 2
                name = row["name"]
            if not name:
                _print({"error": "commander_oracle_id or --name required"})
                return 2
            fetcher = Fetcher()
            out: dict[str, object] = {"commander": name, "oracle_id": oid}
            if args.source in ("all", "edhrec"):
                out["edhrec"] = sync_edhrec(store, fetcher, name=name,
                                            commander_oracle_id=oid, slug=args.slug,
                                            include_base=args.base, force=args.force)
            if args.source in ("all", "playgroup"):
                out["playgroup"] = sync_playgroup_commander(
                    store, fetcher, name=name, commander_oracle_id=oid, force=args.force)
            _print(out)
        elif args.command == "sync-card-atlas":
            from .external import card_atlas_coverage, sync_card_atlas
            from .httpfetch import Fetcher
            result = sync_card_atlas(store, Fetcher(), args.collection,
                                     limit=args.limit, force=args.force)
            _print({"sync_run": result, "coverage_total": card_atlas_coverage(store, args.collection)})
        elif args.command == "sync-edhrec-cards":
            from .external import sync_edhrec_cards
            from .httpfetch import Fetcher
            _print(sync_edhrec_cards(store, Fetcher(), args.collection,
                                     limit=args.limit, force=args.force))
        elif args.command == "sync-spellbook":
            from .external import sync_spellbook_cards
            from .httpfetch import Fetcher
            _print(sync_spellbook_cards(store, Fetcher(), args.collection,
                                        limit=args.limit, force=args.force,
                                        max_pages=args.max_pages))
        elif args.command == "sync-commander-page":
            from .external import sync_playgroup_commander_page
            from .httpfetch import Fetcher
            name = args.name
            oid = args.commander_oracle_id
            if oid and not name:
                row = store.scryfall(oid)
                if row is None:
                    _print({"error": f"oracle_id {oid} not in local Scryfall store; "
                                     "pass --name explicitly"})
                    return 2
                name = row["name"]
            if not name:
                _print({"error": "commander_oracle_id or --name required"})
                return 2
            _print(sync_playgroup_commander_page(
                store, Fetcher(), name=name, commander_oracle_id=oid,
                force=args.force))
        elif args.command == "derive-print-facts":
            from .printdata import derive_print_facts
            path = args.path or (data_dir() / "scryfall" / "default-cards.jsonl.gz")
            _print(derive_print_facts(store, path))
        elif args.command == "import-marks":
            from .marks import import_owner_marks
            try:
                _print(import_owner_marks(store, args.path,
                                          collection_id=args.collection))
            except (ValueError, json.JSONDecodeError) as exc:
                _print({"import": "FAILED", "error": str(exc)})
                return 2
        elif args.command == "export-marks":
            from .marks import export_owner_marks
            try:
                _print(export_owner_marks(store, args.path,
                                          collection_id=args.collection))
            except ValueError as exc:
                _print({"export": "FAILED", "error": str(exc)})
                return 2
        elif args.command == "import-reference-data":
            from .reference import (import_commander_flags, import_role_profiles,
                                    reference_summary)
            if not args.commander_flags and not args.role_profiles:
                _print({"error": "pass --commander-flags and/or --role-profiles"})
                return 2
            out: dict[str, object] = {}
            if args.commander_flags:
                out["commander_flags"] = import_commander_flags(store, args.commander_flags)
            if args.role_profiles:
                out["role_profiles"] = import_role_profiles(store, args.role_profiles)
            out["reference_data"] = reference_summary(store)
            _print(out)
        elif args.command == "cache-invalidate":
            from .external import invalidate_cache
            _print(invalidate_cache(store, source_name=args.source, kind=args.kind))
        elif args.command == "rebuild-roles":
            from . import roles as roles_mod
            result = roles_mod.rebuild_roles(store)
            if args.collection:
                ids = [str(r["oracle_id"]) for r in store.conn.execute(
                    "SELECT DISTINCT oracle_id FROM physical_lot "
                    "WHERE collection_id = ?", (args.collection,))]
                result["collection"] = roles_mod.role_counts(store, ids)
            _print(result)
        elif args.command == "derive-card-types":
            from .categories import derive_card_types
            _print(derive_card_types(store, bulk_path=args.bulk))
        elif args.command == "sync-rulings":
            from .httpfetch import Fetcher
            from .rulings import RulingsError, rulings_coverage, sync_rulings
            try:
                result = sync_rulings(store, Fetcher(),
                                      collection_id=args.collection,
                                      force=args.force)
            except RulingsError as exc:
                _print({"sync": "FAILED", "error": str(exc)})
                return 2
            _print({"sync_run": result,
                    "coverage": rulings_coverage(store, args.collection)})
        elif args.command == "sync-edhtop16":
            from .edhtop16 import EdhTop16Error, edhtop16_coverage, sync_edhtop16
            from .httpfetch import Fetcher
            try:
                result = sync_edhtop16(store, Fetcher(),
                                       collection_id=args.collection,
                                       force=args.force)
            except EdhTop16Error as exc:
                _print({"sync": "FAILED", "error": str(exc)})
                return 2
            _print({"sync_run": result,
                    "coverage": edhtop16_coverage(store, args.collection)})
        elif args.command == "sync-topdeck":
            from .topdeck import TopDeckError, sync_topdeck, topdeck_coverage
            try:
                result = sync_topdeck(store, collection_id=args.collection,
                                      force=args.force, months=args.months,
                                      start=args.start, end=args.end,
                                      window_days=args.window_days,
                                      doc_budget=args.doc_budget)
            except TopDeckError as exc:
                _print({"sync": "FAILED", "error": str(exc)})
                return 2
            _print({"sync_run": result,
                    "coverage": topdeck_coverage(store, args.collection)})
        elif args.command == "sync-edhtop16-commanders":
            from .edhtop16 import (EdhTop16Error, edhtop16_commander_coverage,
                                   sync_edhtop16_commanders)
            from .httpfetch import Fetcher
            try:
                result = sync_edhtop16_commanders(
                    store, Fetcher(), collection_id=args.collection,
                    force=args.force, limit=args.limit)
            except EdhTop16Error as exc:
                _print({"sync": "FAILED", "error": str(exc)})
                return 2
            _print({"sync_run": result,
                    "coverage": edhtop16_commander_coverage(
                        store, args.collection)})
        elif args.command == "sync-mtgjson":
            from .mtgjson import sync_mtgjson
            raw_dir = Path(args.dir) if args.dir else data_dir() / "mtgjson"
            _print(sync_mtgjson(store, raw_dir, collection_id=args.collection,
                                download=args.download))
        elif args.command == "sync-tagger":
            if args.via_search:
                from .tagger import sync_tagger
                _print(sync_tagger(store, tags=args.tags,
                                   max_pages=args.max_pages,
                                   force=args.force))
            else:
                from .tagger import (bulk_file_meta, download_oracle_tags,
                                     sync_tagger_bulk)
                if args.bulk_file:
                    path = Path(args.bulk_file)
                    meta = bulk_file_meta(path)
                else:
                    path, meta = download_oracle_tags(data_dir() / "scryfall")
                _print(sync_tagger_bulk(store, bulk_path=path,
                                        bulk_meta=meta, tags=args.tags))
        elif args.command == "category-report":
            from .categories import category_report
            _print(category_report(store, args.collection))
        elif args.command == "fetch-images":
            from . import images as images_mod
            ids = [str(r["oracle_id"]) for r in store.conn.execute(
                "SELECT DISTINCT oracle_id FROM physical_lot "
                "WHERE collection_id = ? ORDER BY oracle_id",
                (args.collection,))]
            if args.limit:
                ids = ids[: args.limit]
            _print(images_mod.fetch_images(store, ids))
        elif args.command == "data-report":
            from .report import data_report
            _print(data_report(store))
        elif args.command == "inclusion":
            if args.commander:
                from .inclusion import compute_inclusion
                _print(compute_inclusion(store, commander_oracle_id=args.commander,
                                         collection_id=args.collection))
            elif args.collection:
                from .queries import own_deck_inclusion
                _print(own_deck_inclusion(store, args.collection))
            else:
                _print({"error": "inclusion needs --commander (engine, per "
                                 "settings) or --collection (own decks)"})
                return 2
        elif args.command == "sync-decklists":
            from .commander import commander_candidates
            from .decklists import (decklist_coverage, sync_decklists,
                                    sync_decklists_targeted)
            from .httpfetch import Fetcher
            if args.commander:
                row = store.scryfall(args.commander)
                if row is None:
                    _print({"error": f"oracle_id {args.commander} not in local "
                                     "Scryfall store"})
                    return 2
                commanders = [{"oracle_id": args.commander, "name": row["name"]}]
            else:
                result = commander_candidates(store, args.collection)
                commanders = [{"oracle_id": c["oracle_id"], "name": c["name"]}
                              for c in result["eligible"]]
            try:
                try:
                    brackets = tuple(int(x) for x in args.brackets.split(",")
                                     if x.strip())
                except ValueError:
                    _print({"error": f"--brackets expects comma-separated ints, "
                                     f"got {args.brackets!r}"})
                    return
            except ValueError:
                _print({"error": f"invalid --brackets {args.brackets!r}"})
                return 2
            if args.targeted or args.cohorts_file:
                targets = None
                if args.cohorts_file:
                    try:
                        raw_targets = json.loads(
                            Path(args.cohorts_file).read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as exc:
                        _print({"error": f"--cohorts-file unreadable: {exc}"})
                        return 2
                    by_id = {c["oracle_id"]: c for c in commanders}
                    by_name = {c["name"]: c for c in commanders}
                    targets = []
                    for entry in raw_targets:
                        ref = entry.get("commander")
                        cmdr = by_id.get(ref) or by_name.get(ref)
                        if cmdr is None and ref:
                            row = store.scryfall(ref)
                            if row is None:
                                hits = store.scryfall_by_name(ref)
                                row = hits[0] if len(hits) == 1 else None
                            if row is not None:
                                cmdr = {"oracle_id": row["oracle_id"],
                                        "name": row["name"]}
                        if cmdr is None or not isinstance(
                                entry.get("bracket"), int):
                            _print({"error": f"cohort entry not resolvable: "
                                             f"{entry!r}"})
                            return 2
                        targets.append({"oracle_id": cmdr["oracle_id"],
                                        "name": cmdr["name"],
                                        "bracket": entry["bracket"]})
                targeted = sync_decklists_targeted(
                    store, Fetcher(), commanders=commanders,
                    brackets=brackets, max_per_cohort=args.max_per_cohort,
                    min_canonical=args.min_canonical, targets=targets)
                _print({"targeted_run": targeted,
                        "coverage": decklist_coverage(store)})
            else:
                report = sync_decklists(store, Fetcher(), commanders=commanders,
                                        brackets=brackets,
                                        max_per_cohort=args.max_per_cohort)
                _print({"sync_run": report, "coverage": decklist_coverage(store)})
        elif args.command == "import-browser-decklists":
            from .browserimport import BrowserImportError, import_browser_decklists
            try:
                _print(import_browser_decklists(store, args.path))
            except BrowserImportError as exc:
                _print({"import": "FAILED", "error": str(exc)})
                return 2
        elif args.command == "settings":
            from . import settings as settings_mod
            if args.settings_command == "list":
                _print(settings_mod.all_settings(store))
            elif args.settings_command == "get":
                try:
                    _print({args.key: settings_mod.get_setting(store, args.key)})
                except settings_mod.SettingError as exc:
                    _print({"error": str(exc)})
                    return 2
            elif args.settings_command == "set":
                try:
                    value = json.loads(args.value)
                except json.JSONDecodeError as exc:
                    _print({"error": f"value is not valid JSON: {exc}"})
                    return 2
                try:
                    stored = settings_mod.set_setting(store, args.key, value)
                except settings_mod.SettingError as exc:
                    _print({"error": str(exc)})
                    return 2
                _print({args.key: stored})
        elif args.command == "serve":
            import uvicorn
            from .web import create_app
            uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
