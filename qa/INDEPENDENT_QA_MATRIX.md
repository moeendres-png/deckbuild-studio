# Deckbuild Studio — Independent QA matrix (2026-11-11)

Owner: independent QA. Muse owns all `src/deckbuild_studio/**`, native `tests/**`,
application workflows, and production fixes. This branch contains only isolated
synthetic checks and documentation. **Do not add user inventories, deck lists,
private caches or collection-level details here.**

## Evidence levels
- **EXECUTED (independent):** read the Google Drive source XLSX as CSV text and
  parsed its quoted/newline-containing rows: 1,089 rows, 1,078 unique names,
  1,438 copies; Foundation=285, Schwarze Box=1,153; no invalid quantities and
  no duplicate name+location combinations.
- **EXECUTED (independent):** cross-checked the entire 1,078-name source against
  provided Scryfall Default Cards (2026-11-09): 1,078/1,078 unique Oracle IDs,
  0 unresolved/ambiguous; 26 source-derived commander candidates yield 25
  standalone legal (including Ramos, Dragon Engine) and the sole exclusion
  Faithful Squire // Kaiso, Memory of Loyalty (legendary only on reverse).
  Historical owner workbook has 1,414 distinct card_id, each of the 1,078
  current names present, establishing stable original mapping by source name.
- **STATIC REVIEW:** inspected PR #2/#3/#4 implementation; the tests in
  `qa/test_acceptance_edges.py` target observable contract violations.
- **EXECUTED (real app, private local DB):** imported official Scryfall bulk:
  120,046 printings / 35,769 Oracle identities; imported real XLSX:
  1,089 lots / 1,078 Oracle IDs / 1,438 copies; second import idempotent;
  25 commander candidates, Tatyova filtered pool 417, valid 100-card deck,
  100-line export and legal variant comparison. All **1,089 physical lots have
  card_id=NULL** despite 1,078 historical card_id.
- **EXECUTED (mutation replay on private DB):** add 1 legal Chulane, 1 new box,
  increase 1 quantity => 1,079 identities / 1,440 copies / 26 commanders /
  3 locations; repeat unchanged; partial upsert retains unseen rows; explicit
  replace-snapshot removed 1,070 absent lots with 1,070 audit events.
- **EXECUTED (FastAPI TestClient on real private DB):** GET /, /api/status,
  /api/report, /api/cards (1,078), /api/commanders (25), /api/pool (417)
  succeeded; POST valid deck and GET export succeeded. But GET /api/decks/{revision}
  returned 404, GET /api/decks 405; POST invalid deck returned 200 with
  validation.valid=false **and persisted a revision**.
- **EXECUTED (GitHub Actions independent synthetic acceptance):**
  [run #43100442718](https://github.com/moeendres-png/deckbuild-studio/actions/runs/43100442718):
  **9 failed / 1 passed**. Failures: unowned commander accepted, null card_id,
  negative/fractional stock accepted, Infinity escaping as OverflowError,
  Partner-with wrong partner accepted, normalized lot collision, cross-profile
  revision attached, EDHREC inconsistent fraction silently stored. Only NaN
  quantity rejection passed. The Phase-1 native 28 and Phase-2 native 59
  reported tests remain **Muse claims**, not independently reproduced by this
  separate 10-case suite.
- **NOT INDEPENDENTLY VERIFIED:** live private EDHREC/Playgroup snapshots and
  the 1,078-card Card Atlas sync as stored in Muse's data folder; GitHub QA CI
  uses entirely synthetic data.
- **PUBLIC SOURCE CHECK:** EDHREC Tatyova core/decks vs unfiltered decks;
  Playgroup Sol Ring Card Atlas. Provider page availability does not prove
  stored snapshot values; those still require readback.

## Acceptance matrix
| ID | Contract | Evidence | Status | Owner |
|---|---|---|---|---|
| QA-01 | 1,089 rows / 1,078 Oracle IDs / 1,438 copies / 2 sites | Full source ↔ Scryfall + real DB importer | PASS | QA |
| QA-02 | Commander standalone set | 26 source candidates vs Scryfall 2026-11-09 | PASS (snapshot) | QA |
| QA-03 | Preserve existing card_id | Actual 1,089 SQL lots all NULL; CI failure | FAIL (real DB + CI) | Muse |
| QA-04 | Preserve independent normalized physical lots | SQLite IntegrityError in QA CI | FAIL (CI) | Muse |
| QA-05 | Reject invalid stock quantities | CI: -2 accepted; 1.7 truncated; Infinity OverflowError | FAIL (CI) | Muse |
| QA-06 | Physically own all commanders | CI validates 100-card deck with unowned commander | FAIL (CI) | Muse |
| QA-07 | Named Partner-with pairings | CI wrongly accepts unrelated Partner-with cards | FAIL (CI) | Muse |
| QA-08 | Enforce same collection for deck revisions | CI reused original deck_id across collections | FAIL (CI) | Muse |
| QA-09 | EDHREC inclusion fraction reconciliation | CI stores 90% for 5/10 without warning | FAIL (CI) | Muse |
| QA-10 | All 6 bracket snapshots * 25 commanders | 3 pilot commanders claimed locally | NOT VERIFIED / PARTIAL | Muse |
| QA-11 | Card Atlas 1,078 statuses persisted | 425/582/71/0 reported locally | NOT VERIFIED | Muse |
| QA-12 | Web save/load/remove/compare/export | GET deck 404, list 405, no UI flows; invalid persisted | FAIL (real API + static UI) | Muse |
| QA-13 | Scryfall official download format | `sync_scryfall` names raw JSON download .jsonl.gz | BLOCKED / static defect | Muse |
| QA-14 | CI (pytest, import, browser smoke) | Independent GitHub Actions #43100442718 | FAIL (9 failures; native suite not run) | Muse |
| QA-15 | Private data stays off GitHub | Reviewed visible PR filenames; no raw owner files seen | PASS (file list only) | QA |
| QA-16 | Parser fallback and offline snapshots | No independent DB tests | NOT VERIFIED | Muse |

## Required release gate
No merge/approval of #3/#4 until QA-03 through QA-09, QA-12, QA-13 are
fixed or accompanied by explicitly scoped acceptance decisions, reproducible
tests pass, and a real CI run plus browser E2E is visible. Merge stack:
#2 → #3 → #4; this QA branch is based on #4 and must be rebased after changes.

## Test command
`python -m pytest -q qa/test_acceptance_edges.py`

These tests are intentionally **not** marked `xfail`; an assertion failure
is a real unresolved acceptance check, not permission to call the module done.
