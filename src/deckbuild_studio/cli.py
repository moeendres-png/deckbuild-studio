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

    sf = sub.add_parser("import-scryfall")
    sf.add_argument("path")

    sub.add_parser("sync-scryfall")
    sub.add_parser("normalization-report")
    sub.add_parser("cache-status")

    cmd = sub.add_parser("commanders")
    cmd.add_argument("--collection", default="foundation-schwarze-box")

    scd = sub.add_parser("sync-commander-data")
    scd.add_argument("commander_oracle_id")
    scd.add_argument("--slug")

    sca = sub.add_parser("sync-card-atlas")
    sca.add_argument("--collection", default="foundation-schwarze-box")

    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    store = Store(database_path())
    try:
        if args.command in {"import-inventory", "import-collection"}:
            mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8")) if args.mapping else None
            try:
                _print(detect_and_import(store, args.path, mapping=mapping, mode=args.mode))
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
            from .external import register_commander_jobs
            _print({"jobs_registered": register_commander_jobs(
                store, args.commander_oracle_id, args.slug), "status": "NOT_FETCHED"})
        elif args.command == "sync-card-atlas":
            from .external import register_card_atlas_jobs
            _print({"jobs_registered": register_card_atlas_jobs(store, args.collection),
                    "status": "NOT_FETCHED"})
        elif args.command == "serve":
            import uvicorn
            from .web import create_app
            uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
