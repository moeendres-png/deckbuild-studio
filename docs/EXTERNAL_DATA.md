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

Per-commander/per-view EDHREC + Playgroup results of the first trial
runs: see MIGRATION_NOTES.md "Phase 2". Card Atlas (collection
`foundation-schwarze-box`, 1,078 identities) was completed in resumable
runs on 2026-11-11, no block encountered:

| Attempted | AVAILABLE | PARTIAL (basic counts only) | NOT_FOUND | BLOCKED |
|---|---|---|---|---|
| 1,078 / 1,078 (100 %) | 425 | 582 | 71 | 0 |

Many PARTIAL snapshots are flagged `small_sample` (first-cast n < 25,
Playgroup's full-chart threshold). NOT_FOUND was spot-verified as real
HTTP 404 (e.g. `ajanis-pridemate`, `autumns-veil` — Playgroup has no
page for those slugs).

## Full commander sync (2026-11-11, real fetches, local data folder only)

All 25 eligible commanders of the primary collection were synced with
`sync-commander-data` (sequential, ≥ 1 s rate limit respected; the
Ayli/Tatyova snapshots from the trial runs were reused, not refetched).
Result: **EDHREC 150/150 views AVAILABLE** (25 commanders × 3 brackets ×
stats+decks; cohorts kept separate) and **Playgroup profiles 25/25
AVAILABLE**, each with its numeric id resolved via Playgroup's own
autocomplete (exact label match). EDHREC decks views remain
metadata-only and stats coverage `TOTAL_UNKNOWN`, as documented above.
Two profiles exist but have **0 tracked games** (Agrus Kos, Myojin of
Night's Reach) — stored as AVAILABLE with sample size 0, not as data.

| Commander | EDHREC views | Playgroup id | Playgroup games (n) |
|---|---|---|---|
| Agrus Kos, Wojek Veteran | 6/6 AVAILABLE | 2097 | 0 |
| Anowon, the Ruin Sage | 6/6 AVAILABLE | 110 | 106 |
| Arcanis the Omnipotent | 6/6 AVAILABLE | 1274 | 208 |
| Ayli, Eternal Pilgrim | 6/6 AVAILABLE | 2089 | 262 |
| Fynn, the Fangbearer | 6/6 AVAILABLE | 1742 | 3,116 |
| Garna, Bloodfist of Keld | 6/6 AVAILABLE | 581 | 274 |
| Halana and Alena, Partners | 6/6 AVAILABLE | 1637 | 1,233 |
| Jedit Ojanen of Efrava | 6/6 AVAILABLE | 1738 | 32 |
| Kaervek the Merciless | 6/6 AVAILABLE | 1792 | 526 |
| Kamahl, Pit Fighter | 6/6 AVAILABLE | 190 | 13 |
| Lathliss, Dragon Queen | 6/6 AVAILABLE | 201 | 2,179 |
| Linden, the Steadfast Queen | 6/6 AVAILABLE | 1987 | 97 |
| Lyra Dawnbringer | 6/6 AVAILABLE | 810 | 479 |
| Mica, Reader of Ruins | 6/6 AVAILABLE | 3844 | 95 |
| Myojin of Night's Reach | 6/6 AVAILABLE | 826 | 0 |
| Ovika, Enigma Goliath | 6/6 AVAILABLE | 2367 | 2,846 |
| Prime Speaker Zegana | 6/6 AVAILABLE | 439 | 303 |
| Ramos, Dragon Engine | 6/6 AVAILABLE | 573 | 2,836 |
| Ruby, Daring Tracker | 6/6 AVAILABLE | 2626 | 1,050 |
| Sanar, Unfinished Genius // Wild Idea | 6/6 AVAILABLE | 3830 | 152 |
| Surrak, the Hunt Caller | 6/6 AVAILABLE | 2275 | 21 |
| Syr Alin, the Lion's Claw | 6/6 AVAILABLE | 845 | 1 |
| Tam, Observant Sequencer // Deep Sight | 6/6 AVAILABLE | 3828 | 35 |
| Tatyova, Benthic Druid | 6/6 AVAILABLE | 63 | 1,893 |
| Zetalpa, Primal Dawn | 6/6 AVAILABLE | 1162 | 45 |

Reference commander (not in the collection, counted separately):
Chulane, Teller of Tales — EDHREC 6/6 AVAILABLE, Playgroup id 2143,
n = 2,110.

## Data expansion 1 (2026-11-11, branch `muse/data-expansion-1`)

Four additions, all audited with real probe fetches before any code was
written (same fetcher rules as above; probes ran on a COPY of the data
folder — see "Probe runs" below).

### EDHREC card pages (`sync-edhrec-cards`) — implemented

`https://json.edhrec.com/pages/cards/{slug}.json` (same public JSON host
as the commander views; robots allows the adapter's user agent).
Parser `edhrec-card-json/1.0.0`. Per card, stored in
`edhrec_card_global` under an `edhrec_card` snapshot: global
`num_decks` / `potential_decks` (inclusion = num/potential, computed,
potential ≤ 0 stays NULL), the card's **salt score** (shipped as-is;
a friction/mood indicator, NOT a strength signal — see
docs/TIERLIST_DESIGN.md), its top commanders (name, slug, decks,
potential), up to three example combos (EDHREC ships examples plus a
"See More" link — NO combo total is published on card pages, so none
is stored) and the "similar cards" list. Identity is verified twice:
the shipped card name must equal the requested name and its slug must
match the URL slug. 404 → NOT_FOUND (a normal outcome for recent or
obscure cards).

### Commander Spellbook (`sync-spellbook`) — implemented via the website; REST API blocked

* `backend.commanderspellbook.com/robots.txt` is
  `User-agent: * / Disallow: /` — the REST API is BLOCKED for automated
  access. It is not used, not mirrored, not bypassed.
* `commanderspellbook.com/robots.txt` allows crawling and publishes
  sitemaps. Pages are server-rendered Next.js documents; the embedded
  `__NEXT_DATA__` payload is the data source (same public-payload
  pattern as EDHREC). Parser `spellbook-ssr/1.1.0`.
* Authoritative per-card source is the **card page**
  (`/card/{spellbook_id}/`): it publishes the EXACT commander-legal
  combo total (`combosCount`), the top combos by popularity (one page
  embedded server-side only — the combo LIST is partial by
  construction, the total never is) and the top combo partners
  (card + shared-combo count). The **search page**
  (`/search/?q="Card Name"`, 50/page, no published total) discovers the
  spellbook card id; its explanation string documents SUBSTRING
  semantics, so every captured combo is re-verified (the card's front
  name must appear verbatim in the combo's `uses`, commander legality
  required). Some searches are answered with a 307 redirect to ONE
  combo detail page (verified: Act of Treason, Adaptive Automaton,
  Aether Spellbomb); that page is used for id discovery only, never as
  a result set. Captured combos are the union of card page + search
  pages while a known total is unreached (bounded by `--max-pages`,
  default 5). Stored per combo in `spellbook_combo`: uses (names +
  oracle ids as shipped), produced features, total Cardmarket EUR /
  Card Kingdom USD prices as printed, popularity, mana value needed.

### Scryfall print facts (`derive-print-facts`) — local derivation, no fetch

Derived from the already-local `default-cards` bulk file (never
re-fetched per card): per oracle identity, over paper printings only
(token/art/memorabilia layouts excluded): printings/sets counts,
rarity set + minimum, first/last release year, cheapest EUR and USD
prices WITH the printing that carries them (`set:collector_number`),
and the bulk's `game_changer` flag. Stored in `card_print_fact`,
re-derived idempotently; provenance is the bulk file's SHA-256 prefix.
Prices are Scryfall's published guide prices — a budget marker, never
a strength signal.

### Playgroup commander pages (`sync-commander-page`) — implemented

The public commander JSON provably has NO archetype, matchup,
win-condition, seat or mulligan fields (the parser records them as
`absent_from_public_json`). The public commander HTML page publishes
them; parser `playgroup-commander-page/1.0.0` captures: win conditions
(share per type, %), seat win rates (with seat n), mulligan win rates
(with n), best/worst matchups (≥ 10 games; rows below Playgroup's own
25-game reliability threshold are flagged `small_sample` — Playgroup
itself calls them "suggestive, not statistical") and "Staples that win
games" (rank, games, win-rate lift in percentage points; stored in
`playgroup_commander_staple`, resolved to oracle ids against the LOCAL
Scryfall store by exact front name, unresolved stays NULL). NOT
captured: archetypes (the site offers only a site-wide archetype
search; no per-commander archetype statistics are published) and the
page's player-ratings section (subjective ratings — not objective
telemetry, deliberately excluded). Cache note: page snapshots are
keyed by commander slug; a pre-fix cache collision (a name-only sync
returning another commander's page) was found in the probes, fixed and
covered by a regression test.

### Scryfall Tagger — audited, NOT adopted (documented only)

Tagger's robots.txt allows the site, but there is no official export,
bulk file or API field for its functional tags — the tag data exists
only behind the site's undocumented internal GraphQL endpoint.
Scraping an undocumented internal API is not a provenance-grade import
path, so Tagger is not integrated. Role claims therefore stay with
their existing local sources (`ORACLE_TEXT_HEURISTIC`,
`STRUCTURAL_PROFILE`), each claim keeping its origin. Revisit only if
Scryfall publishes an official tag export.

### Probe runs (2026-11-11, data-folder COPY, real fetches)

| Sync | Scope | Result |
|---|---|---|
| `derive-print-facts` | local bulk | 34,884 identities; collection coverage 1,324/1,324 facts, 1,323 with EUR price, 1,323 with USD price, 212 with ≥ 10 printings |
| `sync-edhrec-cards --limit 10` | 10 cards | 10 AVAILABLE, 0 partial/blocked/not-found (e.g. Adaptive Automaton: inclusion 0.009, salt 0.142, 94,329 / 10,542,169 decks) |
| `sync-spellbook` (3 resumable runs à 10) | 30 cards | 4 AVAILABLE, 3 PARTIAL (search-redirect parse errors — fixed, see below), 23 NOT_FOUND, 17 combos, 0 BLOCKED |
| `sync-spellbook --force --limit 12` (after card-page fix) | 12 cards | 5 AVAILABLE, 7 NOT_FOUND, 0 PARTIAL; 33 of 44 known combos captured; the three redirect cards now AVAILABLE with exact totals (Act of Treason 1/1, Adaptive Automaton 1/1, Aether Spellbomb 20/31) |
| `sync-commander-page` Chulane (id 2143) / Tatyova (id 63) | 2 commanders | both AVAILABLE, all 5 sections, 10 win staples each, 5 best + 5 worst matchups each |

New CLI: `sync-edhrec-cards [--collection] [--limit] [--force]`,
`sync-spellbook [--collection] [--limit] [--force] [--max-pages]`,
`sync-commander-page <oracle_id> | --name NAME [--force]`,
`derive-print-facts [--path]`.

## Collection v2 + sync extension (2026-11-12, real fetches, local data folder only)

The owner supplied an updated inventory file (`MTG_Kartensammlung.xlsx`,
same 7-column simple format): a strict superset of the v1 primary stock
(0 rows vanished, 0 quantities changed) adding a third location,
**Alen Lorwyn Box** (248 rows / 378 copies). Real import ran on
2026-11-12 (backup `deckbuild.sqlite3.bak-collection-v2` taken first)
**without one row**: `Jace` — a token (`Token Planeswalker — Jace`,
1× Alen Lorwyn Box) that the playable Scryfall store deliberately does
not contain; the importer aborts unresolved files by design, so the
import used a filtered copy (original file untouched) and the token is
documented here as excluded. Import result, verified against the DB:
**1,336 lots / 1,324 identities / 1,815 copies** (Schwarze Box 1,153,
Foundation 285, Alen Lorwyn Box 377), 0 lots with `card_id IS NULL`,
old locations unchanged. Eligible commanders rose **25 → 63**
(0 needs_review).

Commander sync extension for the 38 new eligible commanders (the 25 v1
commanders were NOT refetched): **EDHREC 228/228 views AVAILABLE** —
totals are now **378/378 views AVAILABLE for all 63 eligible
commanders** (plus reference Chulane 6/6 and one legacy bracket-less
base snapshot). **Playgroup profiles 38/38 AVAILABLE** (total 63/63),
ids resolved exactly via autocomplete. Nine of the new profiles exist
with **0 tracked games** (stored AVAILABLE with n=0, not as missing):
Hapatra, the Desert Frost; Loot, the Nexus; Saheeli, Consul of
Oversight; Stegron the Dinosaur Man; Swarm, Being of Bees; Teyo,
Diamondblade Mage; Teyo, Lightshield Expert; Winter, Team Player;
Yargle, Goliath of Otaria.

| Commander | EDHREC views | Playgroup id | Playgroup games (n) |
|---|---|---|---|
| Bre of Clan Stoutarm | 6/6 AVAILABLE | 3701 | 655 |
| Brigid, Clachan's Heart // Brigid, Doun's Mind | 6/6 AVAILABLE | 3702 | 1,169 |
| Carnage, Crimson Chaos | 6/6 AVAILABLE | 3475 | 32 |
| Doc Ock, Sinister Scientist | 6/6 AVAILABLE | 3401 | 8 |
| Doran, Besieged by Time | 6/6 AVAILABLE | 3703 | 1,806 |
| Durnan of the Yawning Portal | 6/6 AVAILABLE | 326 | 683 |
| Gideon the Oathless | 6/6 AVAILABLE | 4856 | 2 |
| Gilanra, Caller of Wirewood | 6/6 AVAILABLE | 687 | 671 |
| Hapatra, the Desert Fang | 6/6 AVAILABLE | 4887 | 3 |
| Hapatra, the Desert Frost | 6/6 AVAILABLE | 4888 | 0 |
| Kirol, Attentive First-Year | 6/6 AVAILABLE | 3707 | 105 |
| Lizard, Connors's Curse | 6/6 AVAILABLE | 3557 | 31 |
| Lluwen, Imperfect Naturalist | 6/6 AVAILABLE | 3708 | 224 |
| Loot, the Nexus | 6/6 AVAILABLE | 4896 | 0 |
| Maralen, Fae Ascendant | 6/6 AVAILABLE | 3709 | 3,106 |
| Mary Jane Watson | 6/6 AVAILABLE | 3559 | 8 |
| Molten Man, Inferno Incarnate | 6/6 AVAILABLE | 3561 | 39 |
| Prowler, Clawed Thief | 6/6 AVAILABLE | 3509 | 53 |
| Rhino, Barreling Brute | 6/6 AVAILABLE | 3510 | 24 |
| Rhys, the Evermore | 6/6 AVAILABLE | 3711 | 5 |
| Saheeli, Consul of Oversight | 6/6 AVAILABLE | 4933 | 0 |
| Saheeli, Jewel of Avishkar | 6/6 AVAILABLE | 4928 | 208 |
| Spider-Man Noir | 6/6 AVAILABLE | 3432 | 20 |
| Spider-Man, Web-Slinger | 6/6 AVAILABLE | 3434 | 2 |
| Stegron the Dinosaur Man | 6/6 AVAILABLE | 3437 | 0 |
| Sun-Spider, Nimble Webber | 6/6 AVAILABLE | 3573 | 14 |
| Swarm, Being of Bees | 6/6 AVAILABLE | 3575 | 0 |
| Teyo, Diamondblade Mage | 6/6 AVAILABLE | 4892 | 0 |
| Teyo, Lightshield Expert | 6/6 AVAILABLE | 4891 | 0 |
| Tinybones, Pocket Nuisance | 6/6 AVAILABLE | 4399 | 43 |
| Titanbones, Towering Heart | 6/6 AVAILABLE | 4397 | 14 |
| Tromell, Seymour's Butler | 6/6 AVAILABLE | 3350 | 59 |
| Venom, Evil Unleashed | 6/6 AVAILABLE | 3461 | 36 |
| Vulture, Scheming Scavenger | 6/6 AVAILABLE | 3531 | 3 |
| Winter, Team Player | 6/6 AVAILABLE | 4833 | 0 |
| Winter, Tormented Loner | 6/6 AVAILABLE | 4836 | 1 |
| Yargle, Glutton of Urborg | 6/6 AVAILABLE | 2155 | 91 |
| Yargle, Goliath of Otaria | 6/6 AVAILABLE | 4846 | 0 |

Card Atlas extension (incremental run; the 1,078 v1 cards were
cache-skipped): **246 new identities attempted → 98 AVAILABLE,
121 PARTIAL (72 of them `small_sample`), 27 NOT_FOUND, 0 BLOCKED,**
0 remaining NOT_FETCHED. Overall atlas coverage is now
**1,324/1,324 attempted → 523 AVAILABLE, 703 PARTIAL, 98 NOT_FOUND,
0 BLOCKED**. The 27 NOT_FOUND among the new cards (no Playgroup card
page): Aquitect's Defenses; Auntie's Sentence; Bogslither's Embrace;
Brigid's Command; Brigid, Clachan's Heart // Brigid, Doun's Mind;
Chandra's Emberling; Craftwork Crusher; Dawn's Light Archer; Emergency
Phytomedic // Seed Suture; Evershrike's Gift; Hallway Heckler //
Vicious Verse; Kraven's Cats; Lizard, Connors's Curse; Morcant's
Loyalist; Mysterio's Phantasm; Protege's Awakening; Prudent Fateseer
// Peer Review; Puca's Eye; Scarblade's Malice; Scorpion's Sting;
Tam's Resistance; Tethermage's Advantage; Theorix Metamage // Omit
Variables; Tromell, Seymour's Butler; Void Extrapolator // Omit
Variables; Whiplash Wordsmith // Vicious Verse; Woodwork Prodigy //
Soul Tether.

## Deck lists + inclusion settings (2026-11-12)

Real deck LISTS (not just EDHREC metadata) are harvested from
Archidekt's public API by bracket cohort, and an owner-settings system
decides which source/cohorts feed the inclusion figures
(`inclusion.source/brackets/platforms/min_decks/max_age_days`,
defaults = the previous EDHREC-stats behaviour). EDHREC's own deck
entries stay metadata-only (their only list link, `/deckpreview/`,
is robots-disallowed) and Moxfield is BLOCKED (API robots-disallowed,
no data). Full evidence, coverage table (9,211 decks AVAILABLE of
9,244 capped target; mapping 99.99%), cohort semantics and the
settings catalogue: `docs/DECKLISTS_AND_SETTINGS.md`.
