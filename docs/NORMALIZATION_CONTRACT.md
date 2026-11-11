# Normalization Contract — Deckbuild Studio

Version: Parser/Schema 1.0.0. This contract defines how collection data is
normalized into the local store. Private collection files themselves are
never part of this repository.

## Identity keys — never conflated

| Key | Meaning |
|---|---|
| `oracle_id` | Canonical game-card identity (Scryfall). All legality, singleton and pool logic keys on it. |
| `card_id` | Stable local key from the normalized workbook (`01_CARD_IDENTITY`). Preserved verbatim on import; never re-assigned. |
| `scryfall_id` | Printing-level id. Stored only for the representative printing in the Scryfall store; never used as card identity. |
| `physical_lot_id` | One physical stock row. Normalized imports keep source lot ids; simple/mapped imports derive a deterministic id from the upsert key. |
| `location_id` | Location within one collection profile. For the primary profile the literal location name is the id (`Foundation`, `Schwarze Box`) — locations are never merged or renamed automatically. |

## Quantity semantics

- Missing quantity = **unknown** (`NULL`), never 0.
- Normalized lots keep `quantity_observed`, `quantity_lower_bound` and
  `quantity_exact` separately; the effective quantity is the observed value
  if present, else the lower bound.
- Availability = sum over lots of `quantity - reserved_quantity`. It is
  derived **only** from physical lots — never from row counts or location.
- The primary 7-column source (`Kartensammlung`) contains no reservations,
  conditions or printings. Imports therefore store `reserved_quantity = 0`
  with `reserved_assumption = 'preliminary_zero_declared'`: an openly
  declared preliminary assumption, not a verified fact.

## Name resolution (simple + mapped importers)

- Exact paper-name match against the local Scryfall store, including the
  full DFC name (`A // B`). No fuzzy matching, no guessing.
- Non-playable Scryfall objects (layouts `token`, `double_faced_token`,
  `art_series`, `emblem`) are excluded from the Scryfall store; otherwise
  tokens sharing a playable card's name would make resolution ambiguous.
- Ambiguous or unresolved names abort the whole import with an error
  report; the transaction is rolled back, nothing is written.

## Import modes and idempotency

- Default mode `upsert`, key `(collection_id, oracle_id, location_id)`:
  re-importing the same file changes nothing; rows missing from a newer
  file are **not** deleted.
- Deletion happens only in the explicit mode `replace-snapshot`, and every
  removed lot is written to `inventory_event` as an audit record.
- Every import is one transaction (rollback on any error) and records a
  `source` row: file name, SHA-256, parser version, import time, data status.

## Collection profiles

Profiles are isolated: lots, marks and decks belong to exactly one
`collection_id`. The primary profile is `foundation-schwarze-box`; the
older normalized 1,414-card workbook is a separate reference profile.
Profiles may be linked via `oracle_id` only; quantities are never added
across profiles.

## Commander eligibility (data-based pre-check, not a rules engine)

Eligible = `legalities.commander = 'legal'` (banlist included) AND
available in the collection AND (front-face type line is a Legendary
Creature OR front-face oracle text says "can be your commander").
A legendary back face alone does not qualify. Missing Scryfall facts put a
card into `needs_review`, never into the eligible set. Pairing mechanisms
(Partner, Partner with, Friends Forever, Choose a Background, Doctor's
Companion, Background) are recorded as data and checked for pairs during
deck validation.
