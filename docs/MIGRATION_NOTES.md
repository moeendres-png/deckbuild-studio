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

## Phase 2 (branch `muse/phase2-external-data`, on top of Phase 1)

Implemented: real EDHREC + Playgroup adapters, snapshot store, CLI sync,
UI views. Full source/ToS/coverage documentation: `docs/EXTERNAL_DATA.md`.

- `httpfetch.py`: polite fetcher — robots.txt enforced per host, ≥1 s
  rate limit, backoff on 429/5xx, honest UA, conditional GET. Privacy:
  only public commander/card slugs are requested; no collection data is
  ever sent.
- `edhrec.py`: parses the RSC-embedded JSON verified live on 2026-11-11
  (gallery recs / featured / optionsFilters / decks array). Slug is
  verified against the page's featured commander record. Brackets
  Core=2 / Upgraded=3 / Optimized=4 stay separate cohorts; decks are
  metadata-only (the payload contains no full decklists).
- `playgroup.py`: commander id resolved ONLY via Playgroup's own
  autocomplete (exact label match), then the officially linked public
  JSON `/api/public/v1/commanders/{id}.json`. Card Atlas parses the
  server-rendered `/cards/{slug}` pages; win-rate values are stored as
  observed correlations, never causal effects.
- `external.py`: snapshot storage (`external_snapshot`, SHA-256, parser
  version `2.0.0`, ETag, sample n, captured vs. displayed, coverage),
  resumable syncs, stop-on-block for the atlas, `cache-invalidate`;
  parser-version change invalidates automatically.
- UI: EDHREC tab (bracket switch, stats vs. decks, owned vs.
  recommendation with availability/location), Playgroup tab (commander
  profile + card values with n + coverage), Datenstatus tab (snapshot
  table with source/date/status). API: `/api/external/commander`,
  `/api/external/card`, `/api/external/status`.

### Trial runs 2026-11-11 (real fetches, private data folder only)

EDHREC — all 6 views AVAILABLE for all three test commanders; deck
metadata captured == cohort size in every bracket (COMPLETE_METADATA);
stats gallery captured recs with TOTAL_UNKNOWN (EDHREC ships no gallery
total):

| Commander | Bracket | Stats recs | Cohort (decks) | Decks captured |
|---|---|---|---|---|
| Chulane, Teller of Tales (reference, not in primary collection) | core | 210 | 558 | 558 |
| | upgraded | 233 | 755 | 755 |
| | optimized | 247 | 695 | 695 |
| Tatyova, Benthic Druid (GU, in collection) | core | 289 | 778 | 778 |
| | upgraded | 301 | 784 | 784 |
| | optimized | 303 | 500 | 500 |
| Ayli, Eternal Pilgrim (WB, in collection) | core | 273 | 233 | 233 |
| | upgraded | 312 | 176 | 176 |
| | optimized | 333 | 57 | 57 |

Chulane base views also fetched: stats 241 recs, decks 9,824 metadata
entries (all brackets combined; cohort total not published → TOTAL_UNKNOWN).

Playgroup commander profiles — ids resolved via autocomplete, JSON
AVAILABLE: Chulane id 2143 (matches the previously verified id),
games n=2,110; Tatyova id 63, n=1,893; Ayli id 2089, n=262. The public
JSON offers no archetypes/matchups/win-conditions/seat/mulligan fields;
recorded as absent, not invented.

Card Atlas: see `docs/EXTERNAL_DATA.md` trial-run note and the Phase-2
report (resumable sync, `--limit`; attempted/available/partial/
not_found/blocked/small-sample counted from the local job table).
No block was encountered in the commander runs.

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
