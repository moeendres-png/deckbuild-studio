# Tierlist Design

Status: design, decisions taken (Deckbuild Studio data mandate:
objective, provenance-carrying data only — no opinion scores).
Data basis: docs/EXTERNAL_DATA.md incl. "Data expansion 1"
(EDHREC card facts, Commander Spellbook, Playgroup commander pages,
Scryfall print facts). Nothing in this design needs a data source we
do not already store locally.

## 1. Goal and principles

* One tier per card — **global** scope — plus an optional **context**
  tier per (commander, bracket cohort). Both are computed, never
  edited.
* A tier is a pure function of local, provenance-carrying snapshots:
  same input snapshots ⇒ same tier, bit for bit. The function is
  versioned (`tierlist/1.0.0`); a threshold or weight change is a new
  algorithm version, and stored tiers record the version that made
  them.
* Every tier ships its evidence: which signals, which values, which
  sample sizes, which snapshot (source, fetched_at, parser version)
  each value came from. A tier without inspectable evidence is a bug.
* Missing data is **unavailable**, never 0. Unavailable signals drop
  out of the weighted score and their weight is redistributed; the
  lost weight lowers the *evidence* score and can cap the tier
  (§4). Measured zeros are data and stay zeros (e.g. an EDHREC card
  page with 0 decks, a Spellbook card page with combo total 0).
* Cohorts are never mixed: EDHREC bracket views (Core=2, Upgraded=3,
  Optimized=4) feed only the context tier of their own cohort; the
  global tier uses only cohort-free signals.
* Correlation is not causation — the evidence view says so where it
  matters (Playgroup win-rate differences are observational).

## 2. Scopes

| Scope | Key | Question it answers |
|---|---|---|
| Global | `oracle_id` | How established is this card in Commander overall? |
| Context | `oracle_id × commander_oracle_id × bracket` | How established is this card for THIS commander in THIS bracket cohort? |

A context tier exists only where the commander's EDHREC views and/or
Playgroup page for that cohort were actually fetched; otherwise the
UI shows the global tier and marks the context as NOT_FETCHED.

## 3. Signals

Each signal yields a subscore in [0, 1] via the stated mapping, or is
UNAVAILABLE. Subscores are computed from stored snapshot values only.

### 3.1 EDHREC global inclusion (global scope) — weight 0.55

`num_decks / potential_decks` from `edhrec_card_global`
(parser `edhrec-card-json/1.0.0`). Inclusion is heavily skewed, so
the mapping is banded, not linear:

| inclusion | ≥ 0.30 | ≥ 0.15 | ≥ 0.05 | ≥ 0.02 | ≥ 0.008 | ≥ 0.003 | > 0 | = 0 |
|---|---|---|---|---|---|---|---|---|
| subscore | 1.00 | 0.85 | 0.65 | 0.50 | 0.35 | 0.20 | 0.10 | 0.00 |

Justification: this is the single broadest measured adoption signal
(millions of decks). It measures adoption, not power — which is why
it never stands alone for the top tier (§4 evidence gates).

### 3.2 EDHREC cohort inclusion + synergy (context scope) — weights 0.35 / 0.25

From the commander's bracket stats (existing `sync-commander-data`
snapshots of the SAME bracket only). Inclusion within the commander's
deck population, same band shape as §3.1 shifted up (context pools
are smaller): ≥ 0.60 → 1.00; ≥ 0.40 → 0.85; ≥ 0.25 → 0.65;
≥ 0.12 → 0.50; ≥ 0.05 → 0.35; > 0 → 0.15; = 0 → 0.00.
Synergy (EDHREC's shipped value, roughly [-1, 1]): ≥ 0.30 → 1.00;
≥ 0.15 → 0.80; ≥ 0.05 → 0.60; ≥ -0.05 → 0.45; ≥ -0.15 → 0.30;
else 0.15. Synergy is the commander-specific part inclusion cannot
see; it gets its own weight so a generally popular but off-plan card
does not inherit the commander's tier.

### 3.3 Playgroup win-rate difference (both scopes) — weight 0.25

Observational win-rate lift of decks/cards, from Playgroup commander
pages ("Staples that win games": lift in percentage points over n
games) and, in global scope, per-card atlas values where present.

* n < 25 → signal UNAVAILABLE ("insufficient data"). 25 is
  Playgroup's own reliability threshold ("suggestive, not
  statistical" below it) — we adopt the source's threshold instead of
  inventing one.
* Shrinkage for the rest: `adjusted_lift = lift_pp × n / (n + 50)`.
* Mapping on adjusted lift (pp): ≥ 8 → 1.00; ≥ 5 → 0.80; ≥ 3 → 0.65;
  ≥ 1 → 0.50; ≥ 0 → 0.40; ≥ -2 → 0.30; else 0.15.
* The evidence view labels this signal "observational — correlation,
  not causation" wherever it is shown. It is the only performance
  signal we have; its weight is capped at 0.25 for exactly that
  reason.

### 3.4 Spellbook combo density (both scopes) — weight 0.20 global / 0.15 context

`combos_total` from the card page (exact) when known; the captured
count when only the search route answered (then it is a lower bound
and the snapshot says so). Mapping: 0 → 0.00 (measured: not a combo
piece — that IS evidence); 1–2 → 0.30; 3–5 → 0.50; 6–10 → 0.65;
11–25 → 0.80; > 25 → 1.00. Total unknown → UNAVAILABLE.
Combo density measures combo relevance, not general strength — hence
the modest weight. In context scope the signal stays the global one
(combos are commander-independent until a deck exists) and is
labelled context-free in the evidence view.

### 3.5 Signals that are NOT scores

* **Salt (EDHREC)** — a friction/mood indicator, displayed as its own
  badge (≥ 1.5 "high friction", ≥ 1.0 "noticeable", below "low"). It
  NEVER enters the score: a card is not weaker because opponents
  dislike it.
* **Game Changer / Banned (reference data)** — hard markers (badges),
  zero points. Banned additionally removes the card from legal
  deckbuilding, as today.
* **Price (cheapest EUR printing, `card_print_fact`)** — budget
  marker only (€ ≤ 1 / ≤ 5 / ≤ 15 / > 15). NEVER a strength signal:
  price measures scarcity and demand, not quality, and including it
  would make the tier a market echo.
* **Role claims (heuristics / structural profiles, with origin)** —
  deliberately NOT a tier signal. Roles describe what a card does in
  a deck, not how strong it is; deck-relative coverage/uniqueness
  belongs to the deck view ("this deck lacks ramp"), not to an
  intrinsic card tier. Claims appear in the evidence panel as context
  with their origin (`ORACLE_TEXT_HEURISTIC` /
  `STRUCTURAL_PROFILE`), so their weaker provenance stays visible.

## 4. Combination rule

```
score    = Σ (weight_i × subscore_i) / Σ (weight_i)   over available signals
evidence = Σ (weight_i)                               over available signals  (∈ [0, 1])
```

Tier bands on `score`: S ≥ 0.85 · A ≥ 0.70 · B ≥ 0.55 · C ≥ 0.40 ·
D < 0.40 — then gates/caps apply:

* `evidence < 0.35` → **U** (unrated: not enough measured data; the
  evidence view lists exactly which signals are missing).
* `evidence < 0.55` → capped at **B**.
* `evidence < 0.80` → capped at **A**.
* **S** additionally requires at least one *performance or adoption*
  signal at subscore ≥ 0.85 (Playgroup §3.3 or inclusion §3.1/§3.2) —
  combo density alone can never make an S.

Worked example (global): a card with inclusion 0.06 (0.65), Playgroup
lift +4 pp at n = 300 (adjusted 3.43 → 0.65), combo total 8 (0.65)
scores 0.65 with evidence 1.00 → **B**, and the evidence view shows
all three inputs. The same card with only the EDHREC page fetched
scores 0.65 at evidence 0.55 → still B, but one more missing signal
would have capped it — the cap, not the average, is what thin data
costs.

## 5. Owner marks — hard rule

Owner marks (favorite / exclusion / note, `deckbuild-marks-1`) are
FILTERS, not inputs. The tier computation must not read the marks
table — enforced structurally (the tier module gets no marks handle)
and by a regression test: flipping every mark must leave every
computed tier byte-identical. A mark can hide a card or pin it to a
list; it can never raise or lower a tier.

## 6. Storage and computation

* New table `tier_assignment(oracle_id, scope, commander_oracle_id,
  bracket, tier, score, evidence, signals_json, algo_version,
  computed_at, input_snapshot_ids_json)` — one row per card/scope,
  replaced wholesale per compute run. `signals_json` is the complete
  evidence breakdown (per signal: value, n, subscore, weight,
  snapshot id, fetched_at).
* `mtg-deckbuilder compute-tiers [--collection] [--commander OID]
  [--bracket N]` — manual, like every sync; no background jobs.
  Prints a coverage summary (how many cards per tier, how many U and
  why). Deterministic: two runs over unchanged snapshots produce
  identical rows except `computed_at`.
* Staleness: a tier row is only as fresh as its oldest input
  snapshot; the UI shows that date. Re-running a source sync does not
  silently change tiers — tiers change when `compute-tiers` runs.

## 7. UI concept

* **Tier badge** on every card tile: letter + band colour, scope
  aware (global by default). U renders as a neutral "U — unrated",
  never as D.
* **Evidence drawer** per card: one row per signal (name, raw value
  with unit, sample size, subscore bar, source + fetch date, link to
  the source page), the markers row (Salt badge, Game Changer,
  Banned, budget €), the role claims with origin, and — for context
  tiers — the cohort label ("Optimized cohort, EDHREC + Playgroup,
  fetched 2026-11-11"). Missing signals are listed by name with the
  sync command that would fetch them.
* **Filters**: tier (multi-select, incl. U), salt friction, budget
  band, Game Changer, combo density ≥ n, role. Owner marks remain a
  separate filter group, visually distinct from tier filters.
* **Context switcher**: Global / per commander / per commander +
  bracket. Switching re-reads stored context tiers; commanders
  without fetched context data show global + NOT_FETCHED note.

## 8. Deliberate differences to the old system (commander-playtest-lab)

The old studio had tiers with a `tierOverride` in its export — a
manual value stored next to the computed one, i.e. two truths. Here:

* There is exactly ONE tier value per card/scope: the computed one.
  No override column exists in `tier_assignment`, and exports carry
  the computed tier + algo version + evidence, nothing else.
* An owner who disagrees gets a **personal display adjustment**
  (+1 / −1 step, stored in the marks domain, rendered as
  "A · personal: S"), which is presentation only: it is never written
  into tier storage, never exported as a tier, and never visible to
  the computation (§5's test covers it).
* Thresholds/weights are code + version, not per-card edits: changing
  one's mind about a CARD is impossible by design; changing one's
  mind about the MODEL is an algorithm version bump with a changelog.

## 9. Implementation plan (dependencies)

1. Signal extractors over Teil-1 tables (`edhrec_card_global`,
   `spellbook_combo` snapshots, `card_print_fact`,
   `playgroup_commander_staple`, existing EDHREC bracket stats) —
   pure readers, unit-tested against fixtures. *(No new fetching.)*
2. `tierlist.py`: mappings of §3, combination rule of §4,
   `ALGO_VERSION = "tierlist/1.0.0"`. Tests: band edges, caps,
   U-gate, S-gate, determinism, marks-isolation (§5).
3. `tier_assignment` table + `compute-tiers` CLI + coverage summary.
4. Full manual syncs on the real data folder (EDHREC cards +
   Spellbook for the primary collection) so the global tier has
   evidence for more than the probe batches; context tiers for the
   commanders whose views already exist.
5. UI: badge, evidence drawer, filters, context switcher (§7).
6. Acceptance: recompute twice → identical; spot-check 10 cards'
   evidence against the live source pages; marks-flip test green.

Out of scope for v1: deck-relative scoring (role coverage of a
concrete deck), any machine learning, Tagger data (no admissible
import path — see EXTERNAL_DATA.md), price history (single-point
guide prices only).
## 10. Implementation + real-data results (2026-11-12)

Implemented as designed above (`tierlist/1.0.0`), on branch
`muse/data-expansion-1`:

* `tierlist.py` — band mappings (§3), combination rule (§4), signal
  extractors over the local snapshots (EDHREC card pages + bracket
  stats, Playgroup card atlas + commander pages, Commander Spellbook
  card snapshots), `compute_tiers()` writing `tier_assignment`
  (tier, score, evidence, full signal payload with provenance,
  algo version, input snapshot IDs). Markers (salt band, budget
  band, Game-Changer/Banned flags, role claims with origin) ride in
  the payload and never enter the score; the module never reads the
  `mark` table.
* CLI `compute-tiers` (+ `tiers` section in `data-report`), API
  `GET /api/tiers` (scope/commander/bracket/tier/collection filters)
  and `GET /api/tiers/card/{oracle_id}` (global + optional context
  with `context_status`), `tier` badge data on `/api/cards` and
  `/api/pool`. UI: tier badge + friction/budget marker badges on
  card tiles, tier filter, global/context switcher with bracket
  selector, evidence drawer (values, n, source, fetched_at, missing
  signals, markers, roles).
* Tests: 17 tierlist tests in the suite (band edges, U gate, caps,
  S gate both directions, worked example from §4, UNAVAILABLE ≠ 0,
  measured zero, small-sample rule, lower-bound combos, salt/price
  neutrality, cohort isolation, marks invariance with byte-identical
  rows, reproducibility) — full suite 137 passed, Ruff clean.

Full syncs on the real data folder (collection v2 from
`MTG_Kartensammlung.xlsx`: 1,324 identities / 1,815 copies / 63
eligible commanders; locations Schwarze Box 1,153, Foundation 285,
Alen Lorwyn Box 377), 2026-11-11/12:

* Scryfall print facts derived locally: 34,884 store identities,
  33,788 with an EUR guide price.
* EDHREC card pages: 1,324/1,324 — 1,321 AVAILABLE, 1 PARTIAL,
  2 NOT_FOUND, 0 BLOCKED.
* Commander Spellbook card pages: 1,324/1,324 — 248 AVAILABLE,
  1,076 NOT_FOUND (no commander-legal combo uses the card),
  0 BLOCKED; 3,830 combo rows captured.
* Playgroup commander pages: 63/63 — 62 AVAILABLE, 1 PARTIAL
  ("Molten Man, Inferno Incarnate": page title does not name the
  commander — recorded with that reason); 56 win-staple rows.

`compute-tiers` on the real folder (computed_at
2026-11-12T03:28:46Z, 43,058 rows):

* Global (1,324 cards): S 5, A 28, B 114, C 122, D 1,052, U 3.
  The 3 U cards (Crusade; Rise // Fall; Spite // Malice) have no
  usable snapshot at any of the three sources — all signals
  UNAVAILABLE, listed per card in the evidence payload.
* Context: 64 commanders × 3 brackets = 192 contexts, 173 with
  rated cards, 41,734 card rows (S 15, A 13,173, B 5,484,
  C 15,123, D 7,929, U 10). The 19 contexts without rows have
  neither an AVAILABLE EDHREC stats snapshot nor a commander page.
  Context U rows are staple-only cards whose cohort inclusion,
  synergy and combo signals are all missing (evidence ≤ 0.25).

Verification beyond the unit tests: the full compute was run with
the pre-optimization and the optimized code on an identical copy of
the real database — all 43,058 rows byte-identical (the optimization
batches `roles_map`, whose per-call schema executescript was 97% of
per-card cost, and shares per-run caches; ~63 min → ~14 min wall
under load). The live run reproduced the copy's rows exactly.

## 11. Changelog — tierlist/1.1.0 (CPL adaptation, 2026-11-12)

Full decision record: `docs/TIERLIST_CPL_ADAPTATION.md` (Revision 2).

- **Two separate fields.** The strength model of this document
  (§§1–10) is the **Evidenz-Tier (Stärke-Schätzung)** and is
  **unchanged** in 1.1.0 — same signals, weights, gates, shrinkage.
  Counted decklist frequency is not, and must not become, a strength
  input (owner decision 2026-11-12: strength does not come from
  frequency alone).
- **New scope `universe` — „Verbreitung (gezählt)"**: CPL's pure
  counted tiers over our harvested deck lists (cuts S ≥ 0.50,
  A ≥ 0.35, B ≥ 0.20, C ≥ 0.10, else D; universe below the minimum
  size → U/`UNIVERSE_TOO_SMALL`, shown as „unbekannt"). Profiles are
  derived from the inclusion settings (`all` + one per commander,
  brackets pooled) and keyed by `universe_id`, a snapshot id hashed
  over the universe definition + canonical deck ids + deck content
  fingerprints. Counting mirrors `inclusion.py`: AVAILABLE decks of
  the selection, content dedupe, commander entries excluded,
  quantity > 0, oracle_id-keyed; a period filter uses the deck's
  source timestamp (`source_updated_at`, Archidekt `updatedAt`) and
  counts timestamp-less decks as excluded instead of falling back to
  `fetched_at`. Minimum size is the `tierlist.min_universe` setting
  (default 30, the CPL default); the CPL cuts stay code constants of
  this version. Payload `data_class` is `DERIVED_DESCRIPTIVE`.
- **Provenance**: every payload carries `data_class` (combined scopes
  `HEURISTIC_MODEL`), a `field` label, and — for U rows — `u_reason`
  (`NO_OBSERVATION` / `INSUFFICIENT_EVIDENCE` in the combined scopes).
- **A5 — Top-Commander evidence**: where a context's cohort stats
  carry no row for a card, the „Top Commanders" entry of the card's
  EDHREC card page supplies cohort inclusion of the same construct as
  a labelled fallback (`measurement="card_page_top_commanders"`,
  bracket-agnostic, card-page provenance). Commander-page stats
  always win. Cards with only this evidence get context rows.
- **A4 — Combo detail**: the Spellbook signal value additionally
  carries the distinct combo-partner count and result-type count of
  the card's combos (evidence detail; the subscore is unchanged).
  CPL has no combo signal at all — ours stays, as documented in the
  adaptation spec.
- **Co-occurrence** (not a tier input): `inclusion.cooccurrence`
  computes partner cards with decks-together and lift
  P(partner|card)/P(partner) over the canonical decks of the current
  selection; combo partners are flagged. Surfaced in the card drawer.
- The `tier_assignment` cache schema gained the `universe_id` column
  (primary key extended); a legacy-shape table is rebuilt on first
  open — the cache is derived, nothing is lost.
- Marks isolation is regression-tested for BOTH fields; a dedicated
  separation test proves harvested deck lists never change a single
  Evidenz-Tier row.
