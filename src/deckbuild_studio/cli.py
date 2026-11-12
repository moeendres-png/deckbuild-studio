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
  import-marks           merge the owner's marks (favorite/excluded/note)
                         from a marks JSON (deckbuild-marks-1, upstream
                         studio-marks-1, or the old HTML studio export)
  export-marks           write this collection's marks as deckbuild-marks-1
  apply-card-id-registry replace generated card_ids by the known ids of a
                         registry file (JSON/CSV oracle_id -> card_id)
  derive-card-types      derive per-face type facts (supertypes / types /
                         subtypes) + Scryfall keywords from the local bulk
                         catalogue (offline; --bulk for an explicit file)
  sync-tagger            sync Scryfall Tagger functional tags via the
                         official Search API (function:<tag>), snapshots +
                         claims per tag; claims land in card_role under
                         origin SCRYFALL_TAGGER_SEARCH
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

    crp = sub.add_parser("category-report")
    crp.add_argument("--collection", help="restrict coverage to a collection")

    fi = sub.add_parser("fetch-images")
    fi.add_argument("--collection", required=True)
    fi.add_argument("--limit", type=int)

    sub.add_parser("data-report")

    inc = sub.add_parser("inclusion")
    inc.add_argument("--collection", required=True)

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
        elif args.command == "sync-tagger":
            from .tagger import sync_tagger
            _print(sync_tagger(store, tags=args.tags, max_pages=args.max_pages,
                               force=args.force))
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
            from .queries import own_deck_inclusion
            _print(own_deck_inclusion(store, args.collection))
        elif args.command == "serve":
            import uvicorn
            from .web import create_app
            uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
