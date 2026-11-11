# External Data — EDHREC & Playgroup.gg (Phase 2)

Local, manually triggered, reproducible snapshots of **public** data.
No background crawler, no automatic sync on UI clicks. Adapters:
`edhrec.py` (parser), `playgroup.py` (parser), `external.py` (sync/storage),
`httpfetch.py` (polite fetcher), `slugs.py` (slug candidates).

## Privacy — what the adapters never send

Requests are plain GETs of publicly known commander/card pages, exactly
like a browser visit. The adapters **never** send: collection quantities,
locations/boxes, reservations, own deck lists, oracle-id lists of the
collection, or any account data. There is no login, no cookie, no request
body. Private snapshots live only in the private data folder
(`MTG_DECKBUILDER_DATA`, default `~/.local/share/mtg-collection-deckbuilder`):
SQLite rows in `external_snapshot` (+ `edhrec_card_stat` /
`edhrec_deck_entry`) and the raw page bodies gzipped under
`snapshots/<source>/<sha256>.gz` next to the database. Nothing external is
committed to Git; tests use synthetic fixtures only.

## Fetcher rules (robots / ToS)

Checked 2026-11-11:

- **EDHREC** `robots.txt`: wildcard group disallows only
  `/articles/embed/`, `/articles/preview*`, `/deckpreview/`. Commander
  pages (`/commanders/...`) are allowed. Terms: <https://edhrec.com/terms>.
- **Playgroup** `robots.txt`: the wildcard group disallows
  `/live_sessions/*` (join/new), `/playtest*`, `/commanders/*/playtest`,
  `/sets/*/playtest/`, `/brew`. Commander pages, the public JSON, the
  search autocomplete and `/cards/...` are allowed.
- The fetcher loads `robots.txt` once per host and enforces it
  (`RobotsDisallowed` → snapshot status `BLOCKED`, never fetched anyway),
  waits **≥ 1 s** between requests to a host, backs off exponentially on
  429/5xx (honouring `Retry-After`, capped), sends an honest User-Agent
  (`DeckbuildStudio/0.2 …`), and uses conditional GET (ETag /
  Last-Modified → 304 = cache hit) when a validator is stored.
- A `403`/`429` during the Card-Atlas mass sync **stops the run**
  (`stopped_on_block`); there is no escalation, rotation or bypass.

## EDHREC adapter

- URL set per commander (brackets are separate cohorts, **never mixed**):
  `/commanders/{slug}/{core|upgraded|optimized}` and the same + `/decks`;
  optional base `/commanders/{slug}` and `/decks` (`--base`).
  Bracket levels: Core=2, Upgraded=3, Optimized=4.
- Slug: derived from the Scryfall name (`slugs.slugify`, front face for
  DFCs) and **verified** — the page's embedded featured record must match
  the commander name or slug, otherwise the snapshot is `NOT_FOUND`
  ("slug verification failed"), never silently accepted.
- Page structure (verified 2026-11-11, Next.js/RSC): data is embedded as
  escaped JSON — `gallery.recs[]` (category, name, card slug, scryfallId,
  `inclusion` fraction, `numDecks`, `potentialDecks`, `synergy`, `lift`,
  trend), `gallery.categories[]` (label/slug), `featured.rec`
  (name/cardId/numDecks/rank), `optionsFilters` (per-bracket deck counts
  = cohort sizes, tags, budgets). Decks pages embed `decks[]` with
  **metadata only** (urlhash, savedate, price, salt, tags, type counts) —
  no full deck compositions are published in the payload and none are
  claimed; a deck's source link is its EDHREC decks page + urlhash.
- Definitions: `inclusion` is stored as shipped (fraction) together with
  its numerator/denominator (`numDecks`/`potentialDecks`); a missing or
  zero denominator makes inclusion **unknown** (NULL), never 0.
  `synergy`/`lift` are stored verbatim as EDHREC computes them (EDHREC
  defines synergy as the inclusion difference against other decks of the
  same colour identity).
- Coverage: the gallery ships `paginationTotal: undefined` → stats
  coverage is `TOTAL_UNKNOWN` (captured rec count is recorded, no total
  invented). Decks coverage compares captured (deduped by urlhash) vs.
  the bracket cohort count: `COMPLETE_METADATA` / `PARTIAL`.

## Playgroup adapter

- **Commander id resolution**: only via Playgroup's own search
  autocomplete (`/api/v1/commanders?link=true&q=<front name>` — the
  endpoint the site's search box uses), requiring an **exact label
  match**. No match → snapshot `NOT_FOUND` with detail `UNRESOLVED`;
  ids are never guessed and never derived from Scryfall ids.
- **Commander snapshot**: the officially linked public JSON
  `/api/public/v1/commanders/{id}.json` (verified for Chulane = 2143).
  Stored: games won/lost, win rate, decks count, games count (sample n),
  averages, `cached_elo`, `global_rank`, top decks, graph sizes.
  The JSON does **not** offer archetypes, matchups, win conditions,
  seat/mulligan breakdowns or player counts — those fields are recorded
  as absent (`absent_from_public_json`), not invented.
- **Card Atlas**: `/cards/{slug}` is server-rendered HTML; the parser
  extracts only labelled values actually present: Live Inclusion,
  Times Brought, Decks Running, Median Cast Turn, Drawn → Played,
  first-cast distribution + n, cast-turn median/P25/P75/max, on-curve
  (with the numerator/denominator/turn as labelled), cast-same-turn %,
  brought/drawn/battlefield/still-on-board funnel, observed win rates
  with n and the 95 % CI of the gap, final zone distribution, top
  commanders by decks. Two inconsistent "brought" figures on the page
  (stat block vs. funnel header) are stored as separate fields, as
  published.
- **Semantics (binding)**: Card-Atlas values are Playgroup **Live**
  per-card telemetry from tracked games — an **observed correlation,
  not a causal card effect** (Playgroup prints the same warning on the
  page). This is a different corpus from the Playgroup commander
  statistics; the two are never merged. Site thresholds: play counts
  appear at ≥ 100 tracked games; full charts need ≥ 25 observed games
  not dominated by one pilot — snapshots with n < 25 are flagged
  `small_sample`. Cards whose page publishes only basic counts are
  `PARTIAL`; cards with no page are `NOT_FOUND` — both are normal
  coverage outcomes, reported in the coverage report.

## Status model & cache

Statuses: `NOT_FETCHED` (job registered, never requested), `AVAILABLE`,
`PARTIAL`, `BLOCKED` (403/429/robots/network policy), `NOT_FOUND`,
`STALE` (snapshot exists but was written by an older parser version —
shown as STALE in the UI; `latest_snapshot` ignores other parser
versions, so a parser change invalidates the cache automatically),
plus per-snapshot `coverage_status`.

Every snapshot records: stable snapshot id, source name/URL, fetch time
(UTC), parser version (`2.0.0` external parser; EDHREC parser id
`edhrec-rsc/2.0.0`, Playgroup `playgroup/2.0.0`), SHA-256 of the raw
body, ETag/Last-Modified, sample size, captured vs. displayed counts,
detail text. Re-running a sync without `--force` reuses current
snapshots (resumable Card Atlas); `cache-invalidate [--source] [--kind]`
deletes snapshots and resets jobs to `NOT_FETCHED`.

## CLI

```bash
mtg-deckbuilder sync-commander-data <oracle_id> [--slug S] [--source edhrec|playgroup|all] [--base] [--force]
mtg-deckbuilder sync-commander-data --name "Chulane, Teller of Tales"   # reference/test commander, not in the primary collection
mtg-deckbuilder sync-card-atlas [--collection foundation-schwarze-box] [--limit N] [--force]
mtg-deckbuilder cache-status        # per-source/commander/bracket status, age (fetched_at), atlas coverage
mtg-deckbuilder cache-invalidate [--source edhrec|playgroup] [--kind edhrec_stats]
```

## Trial runs (2026-11-11, real fetches, local data folder only)

Per-commander/per-view EDHREC + Playgroup results: see MIGRATION_NOTES.md
"Phase 2". Card Atlas (collection `foundation-schwarze-box`, 1,078
identities), two resumable runs (`--limit 60`, then `--limit 140`),
no block encountered:

| Attempted | AVAILABLE | PARTIAL (basic counts only) | NOT_FOUND | BLOCKED | NOT_FETCHED (remaining) |
|---|---|---|---|---|---|
| 200 / 1,078 (18.6 %) | 72 | 115 | 13 | 0 | 878 |

96 of the 200 latest card snapshots are flagged `small_sample`
(first-cast n < 25, Playgroup's full-chart threshold). NOT_FOUND was
spot-verified as real HTTP 404 (e.g. `ajanis-pridemate`,
`autumns-veil` — Playgroup has no page for those slugs). The remaining
878 identities are honestly `NOT_FETCHED`; the sync resumes where it
stopped (`sync-card-atlas` without `--limit` continues, ~1.7 s/card at
the ≥1 s rate limit plus page load). Full completion is a runtime
question, not a code question — no completeness is claimed.
