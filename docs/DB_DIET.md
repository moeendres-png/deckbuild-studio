# DB Diet — payload compression + delta-import protocol

> **Update 2026-11-14 (issue #59):** The tier list whose
> `signals_json` column this diet compressed was removed from the
> tool by owner decision. The compression described here still ran
> to completion on the live database first (all 1,268,404 rows), so
> the archived tier data (issue #58, preserved in Google Drive) is
> stored in exactly this compact `gzip+b64:` form; `payloads.py`
> remains the reference codec of that archive format and
> `tools/migrate_payload_compression.py` its migration tool. The
> table drop + final VACUUM on the live database are a separate
> step after the archive verification. Everything below is the
> record of the diet as designed and executed.

Measured on the production database (9,390,870,528 bytes) on 2026-11-13
and implemented the same day. This document records where the bytes
actually were (measured, not assumed), the compression design, the
migration tool, the rehearsal evidence, and the delta-import protocol
that replaces the full-copy backup + full integrity check per import.

## 1. Where the 9.39 GB were (dbstat, per table/index)

| Object | Size | Share | Note |
|---|---:|---:|---|
| `tier_assignment` | 5.108 GB | 54.4 % | 1,268,404 rows |
| `decklist_card` | 1.690 GB | 18.0 % | 9,789,867 rows |
| `sqlite_autoindex_decklist_card_1` (PK) | 1.417 GB | 15.1 % | duplicates the TEXT key |
| `decklist_card_oracle` (index) | 0.499 GB | 5.3 % | |
| `tier_assignment` indexes (3) | 0.353 GB | 3.8 % | |
| `decklist_deck` | 0.058 GB | 0.6 % | 101,073 rows |
| `external_snapshot` | 0.018 GB | 0.2 % | 5,923 rows |
| everything else | ~0.25 GB | ~2.7 % | |

Column sums (content bytes, `SUM(LENGTH(...))`):

| Column | Content | avg | max |
|---|---:|---:|---:|
| `tier_assignment.signals_json` | **2,482,321,301 B** | 1,957 B | 3,436 B |
| `tier_assignment.input_snapshot_ids_json` | 46,115,121 B | 36 B | 165 B |
| `external_snapshot.payload_json` | 12,244,593 B | 2,581 B | 270,486 B |

Findings that drove the design:

* The original suspicion (`external_snapshot.payload_json`) is
  **negligible**: 12 MB of content in an 18 MB table. Scope decision
  (co-lead review #51): it is deliberately **NOT** compressed — risk
  without benefit at that size; it stays plain, human-readable JSON
  and no snapshot read/write path changes at all (the `sha256` →
  `snapshot_id` provenance semantics are untouched).
* **`tier_assignment.signals_json` is the dominant payload block.** Its
  2.48 GB of content inflates the table to 5.11 GB because a ~2 KB text
  value spills to overflow pages whose last page is mostly slack
  (~2 KB waste per row × 1.27 M rows). Compressing the value below the
  inline threshold removes the content *and* the slack.
* `decklist_card` + its two indexes (~3.6 GB) are normalized row data,
  not payloads. Row-level compression cannot address them; that block
  is the diet's floor unless the schema changes (e.g. a card-name
  dictionary for `entry_key`) — deliberately out of scope here.

## 2. Codec (`src/deckbuild_studio/payloads.py`)

Application-level compression for the ONE in-scope column,
`tier_assignment.signals_json`:

* **Write** (`encode_payload`): values ≥ 512 bytes are gzip-compressed
  (level 6, `mtime=0`), base64-encoded and stored with the marker
  prefix `gzip+b64:` — always base64 TEXT, never raw gzip bytes in a
  TEXT column. Smaller values — and values whose packed form would not
  be smaller — are stored verbatim.
* **Read** (`decode_payload` / `loads_payload`): values without the
  marker pass through unchanged, so every database written before the
  codec stays fully readable (backward compatibility). Marked values
  decode back to the exact original text. A `bytes` value (BLOB in a
  TEXT column) is treated exactly like `json.loads` treated it.
* **Content invariant:** decompression restores the stored JSON
  byte-for-byte, so every consumer sees identical data; only the
  storage representation changes.
* **Failure contract:** an undecodable marked value raises
  `PayloadDecodeError`, a subclass of `json.JSONDecodeError`, so the
  readers' existing corrupt-value fallbacks apply unchanged.

Wired paths — the complete inventory of `signals_json` access, all in
`tierlist`: write in `_store_row` and `_store_universe_row`; read in
`_row_dict` (via `get_tier`/`list_tiers`), `list_universes` and
`tiers_map`. Every read goes through `loads_payload`, i.e.
decompression happens BEFORE each reader's silent fallback parsing —
guard tests (`tests/test_payloads.py`) seed compressed rows and assert
each reader returns the real signals/markers/universe block, so a
missed decompression fails loudly instead of silently degrading to
empty signals. There are no other `signals_json` readers in the
codebase (verified by grep; the web/report layers only consume the
parsed dicts these functions return).

**Rollback note:** after a database is migrated, do not roll back the
*code* without also restoring the pre-migration database backup — old
code reads a `gzip+b64:` value as corrupt JSON and would degrade those
rows' signals to empty (no data loss, but wrong signal display until
the database is restored or re-computed).

## 3. Migration (`tools/migrate_payload_compression.py`)

Converts stored plain values in place, per column, in batches:

* Keyset pagination over the primary key (no long-lived cursor over a
  mutating table); each batch commits separately.
* **Every converted row is verified before commit**: the decoded value
  must equal the original byte-for-byte (hence also SHA-256-equal).
  The summary counts `converted` and `verified` — they must be equal.
* **Resumable:** converted rows carry the marker and drop out of the
  candidate filter, so an interrupted run restarts where the data shows
  it stopped. Re-running a finished migration converts 0 rows.
* Content-agnostic: corrupt stored JSON is converted as opaque text and
  restored byte-identically (its corrupt-handling behaviour is kept).
* `--dry-run` measures without writing; `--vacuum` reclaims the freed
  pages at the end (without it the content shrinks but the file does
  not); `--report FILE` writes the JSON summary.

## 4. Rehearsal on a full copy (2026-11-13)

Source: the pre-harvest-import backup (byte-identical copy, MD5
checked). Before/after evidence:

* all-table counts + content digests of `decklist_card`/`decklist_deck`
  captured with `tools/delta_guard.py before`; `verify` after the
  migration must PASS (counts unchanged everywhere; digests of the
  untouched tables identical).
* server smoke (8 endpoints: `/api/status`, `/api/external/status`,
  `/api/tiers`, `/api/verbreitung`, `/api/commanders`,
  `/api/tiers/universes`, `/api/tiers/card/{id}`, `/api/cards`) captured
  before and after — payloads must be identical.
* migration result (measured on the copy): **1,268,404 of 1,268,404
  `signals_json` rows converted, 0 kept plain**; every row verified
  during conversion (decode-equality + SHA-256). Stored content:
  2,482,321,301 → 1,143,655,708 bytes. File size after VACUUM:
  **9,390,870,528 → 5,675,118,592 bytes (−39.6 %)**, freelist 0.
  `delta_guard verify`: **PASS** (all 43 tables count-identical,
  `decklist_card`/`decklist_deck` digests identical). Server smoke
  after: **8/8 endpoint payloads byte-identical** to the
  pre-migration captures.
* the remaining ~5.68 GB are real data, not payloads: `decklist_card`
  + its indexes (~3.6 GB) and the compressed tier table (~1.5 GB).
  Going below that needs a schema change, not compression, and is
  out of scope here.

## 5. Delta-import protocol (`tools/delta_guard.py`)

For every future import into the production database — instead of a
full file copy (~9 GB, ~1 h of checks) before and a full `quick_check`
after:

1. **Before the import** (seconds to minutes, read-only):
   `python tools/delta_guard.py before --db DB --out PREFIX
   --tables <affected tables> [--dump "TABLE:WHERE"]...`
   writes `PREFIX.counts.json` (row counts of ALL tables + a streaming
   SHA-256 content digest per affected table) and `PREFIX.rows.jsonl`
   (the rows an import will REPLACE, addressed by `--dump` scopes — the
   restore point for overwritten rows).
2. **Run the import** (single writer, one transaction discipline as
   before).
3. **After the import**:
   `python tools/delta_guard.py verify --db DB --before PREFIX
   --expect decklist_deck=+3,decklist_card=+300` —
   PASS requires: every unaffected table count-identical; every
   affected table changed by exactly the expected delta (digest-equal
   when the expected delta is 0); every dumped row still present and
   unchanged (unless its table is released via `--allow-replace`).
   The delta rows themselves are fully checked by the import's own
   validation (e.g. 100 cards per deck, 0 unmapped).
4. **No per-import `quick_check`.** The full integrity check runs
   separately on a schedule (and after migrations), not per import.

Worked example (the 3-deck harvest import, retroactively): affected
tables `decklist_deck,decklist_card,external_snapshot,source,sync_job`;
expected deltas `decklist_deck=+3, decklist_card=+300,
external_snapshot=+3, source=+3` (one snapshot + source row per deck);
no `--dump` scopes needed (pure inserts, nothing replaced).

## 6. Live runbook (Phase 2, only on explicit owner go)

1. Fresh FULL backup of the live DB (this one time — it is the
   pre-diet restore point):
   `deckbuild.sqlite3.bak-pre-diet-20261113` in the data folder.
2. `TMPDIR=~/tmp python tools/migrate_payload_compression.py
   --db <live> --batch-size 2000 --vacuum --report <report file>`
   (default column: `tier_assignment.signals_json` — the only
   in-scope column). **The `TMPDIR` redirect is mandatory on this
   machine:** VACUUM stages its working copy in the temp directory;
   the default `/tmp` is a 512 MB tmpfs and VACUUM dies with
   "database or disk is full" (observed in the rehearsal — the
   conversion itself had already committed; VACUUM is transactional
   and was simply re-run with `TMPDIR` set).
3. Verify: collection 1,324 identities / 1,336 lots / 1,815 copies;
   `tier_assignment` 634,202 rows per algo version (1.1.0 and 1.2.0);
   `decklist_deck` and `decklist_card` counts unchanged; `source`
   unchanged; EDHREC commander snapshots 378; `PRAGMA quick_check` =
   ok; server smoke on the real data folder (all endpoints 200,
   `/api/external/status` counters equal to the pre-migration run).
