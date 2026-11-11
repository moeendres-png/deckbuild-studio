# Migration Notes — Phase 1 (BUILD migration)

Source: `commander-playtest-lab`, BUILD module `src/commander_lab/studio/`
at `origin/main` 12af1c1b2 (README source revision 10e663de0).
Target: this repo, branch `muse/phase1-build-migration`.

## Taken over (adapted, decoupled)

| Source | Here | Change |
|---|---|---|
| `studio/store.py` (SQLite, provenance `source` table, schema v7) | `deckbuild_studio/store.py` | `commander_lab.owner_data` coupling replaced by `MTG_DECKBUILDER_DATA` (default `~/.local/share/mtg-collection-deckbuilder`); layers split into Scryfall / Collection / Deck / Sync-Job stores |
| `studio/importers.py` — `import_inventory_workbook` (tabs 01/02/03/05…) | `importers.import_normalized_workbook` | Same sheet contract, card_id/oracle_id/physical_lot_id preserved, reservations + exact-vs-lower-bound semantics kept, transactional rollback |
| `studio/catalog.py` — `import_scryfall_oracle`, `_faces`, image extraction | `scryfall.py` | Same face/image handling; additionally filters non-playable layouts (token/art/emblem) that otherwise break exact name resolution; reads `.jsonl(.gz)` and JSON arrays |
| `studio/decks.py` + `builder.py` (revisions, content hash, readiness) | `decks.py` | Monorepo `deck_readiness`/`deck_variant`/`models` imports removed; revisions content-addressed (SHA-256), variants via `parent_revision_id`, compare + text export kept |
| `studio/web.py` + `static/app.{html,css,js}` | `web.py` + `static/app.html` | FastAPI routes for collection / commanders / pool / decks / status kept as API; frontend rewritten as one standalone page with the same areas (Sammlung, Commander, Deckbuilder, Datenstatus) |
| `studio/__main__.py` (CLI shape) | `cli.py` | Commands per target README: `import-inventory`, `import-scryfall`, `sync-scryfall`, `normalization-report`, `serve`, plus `commanders`, `cache-status`, `sync-commander-data`, `sync-card-atlas` |
| `studio/roles.py`, `sources.py` (BUILD parts: marks, EDHREC table shapes) | `mark` table, `external.py` job scaffold | Roles/favorites/notes kept as marks; EDHREC/Playgroup reduced to an honest job/status scaffold (Phase 2) |

## Removed (not copied)

- `games.py`, `play.py`, `launch.py`, `static/partie.*` — PLAY / XMage /
  game view / simulation. No XMage, Forge, rules-engine or pilot code exists
  in this repo (the words occur only in removal notes like this one).
- `sources.py`'s fixed `builder.ALL_DECKS` Chulane focus — replaced by the
  dynamic commander selection in `commander.py`. No card name is hardcoded.
- Corpus/simulation importers of the monorepo (`import_corpus_*`,
  `import_simulation_report`, hub corpus) — not BUILD deckbuilding.

## New in Phase 1

- Importer B: the 7-column primary workbook
  (`Kartensammlung_Foundation_Schwarze_Box.xlsx`, sheet `Kartensammlung`)
  with exact Scryfall name resolution, profile `foundation-schwarze-box`,
  upsert key `(collection_id, oracle_id, location_id)`, audited
  `replace-snapshot` mode, declared `reserved=0` assumption.
- Importer C: generic CSV/XLSX via explicit JSON column mapping.
- `commander.py`: front-face commander eligibility incl. DFC rule
  (legendary back face alone does not qualify), pairing mechanisms as data,
  `needs_review` instead of silent release.
- `sync-scryfall` uses the current official API domain
  `https://api.scryfall.com/bulk-data` (the `.io` domain is the legacy
  alias) and the entry's `jsonl_download_uri`; only the public catalogue
  is downloaded, into the private data folder only.

## Known gaps / Phase-2 connection points

- EDHREC: per commander 6 snapshots — brackets Core=2 / Upgraded=3 /
  Optimized=4 × (stats, /decks) — jobs are registered as `NOT_FETCHED`
  (`external.register_commander_jobs`); no adapter, no data yet.
- Playgroup: numeric commander-id resolution (must come from a real
  source, e.g. the public JSON linked on the commander page) and the Card
  Atlas (one job per collection identity,
  `external.register_card_atlas_jobs`) are `NOT_FETCHED` scaffolds;
  a coverage report is part of Phase 2.
- The owner-side prepared 1,253 external sync jobs exist only privately
  with the owner; they are not in this repo (only the job types/statuses
  are mirrored here).
- Deck validation is a data-based pre-check (legality, color identity,
  singleton with real oracle-text exceptions, physical availability),
  not a rules engine.
- Card images are referenced by Scryfall image URI (hotlink at display
  time); no local image cache yet (source `images.py` behaviour reduced).
- The normalized 1,414-card workbook was not available locally during
  Phase 1 acceptance; Importer A is verified with synthetic fixtures in
  exactly the documented sheet/column shape, and the primary profile
  acceptance (1,089 / 1,078 / 1,438 / 25 commanders) was run against the
  real primary workbook.
