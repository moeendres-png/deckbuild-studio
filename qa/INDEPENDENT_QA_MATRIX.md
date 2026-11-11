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
- **EXECUTED (independent):** cross-checked 26 source-derived legendary-creature
  candidates against provided Scryfall Default Cards archive (2026-11-09):
  25 eligible (including Ramos, Dragon Engine), 1 exclusion (Faithful
  Squire // Kaiso, Memory of Loyalty: only legendary on reverse).
- **STATIC REVIEW:** inspected PR #2/#3/#4 implementation; the tests in
  `qa/test_acceptance_edges.py` target observable contract violations.
- **NOT INDEPENDENTLY RUN:** Muse's reported 59 local tests and 1,078-card
  Card Atlas sync; GitHub Actions runs=0 at audit time; no authorized DB
  or private snapshot access in this QA session.
- **PUBLIC SOURCE CHECK:** EDHREC Tatyova core/decks vs unfiltered decks;
  Playgroup Sol Ring Card Atlas. Provider page availability does not prove
  stored snapshot values; those still require readback.

## Acceptance matrix
| ID | Contract | Evidence | Status | Owner |
|---|---|---|---|---|
| QA-01 | 1,089 rows / 1,078 unique names / 1,438 copies / 2 sites | Source read, parser count | PASS (raw data) | QA |
| QA-02 | Commander standalone set | 26 source candidates vs Scryfall 2026-11-09 | PASS (snapshot) | QA |
| QA-03 | Preserve existing card_id | `_import_simple_rows(card_id=None)` | BLOCKED / static defect | Muse |
| QA-04 | Preserve independent normalized physical lots | Unique(collector, Oracle, location) | BLOCKED / static defect | Muse |
| QA-05 | Reject invalid stock quantities | `_int` truncates; no negative guard | BLOCKED / static defect | Muse |
| QA-06 | Physically own all commanders | `validate_deck` skips availability of commander_ids | BLOCKED / static defect | Muse |
| QA-07 | Named Partner-with pairings | Generic Partner regex also matches Partner with | BLOCKED / static defect | Muse |
| QA-08 | Enforce same collection for deck revisions | `create_deck` reuses arbitrary parent deck_id | BLOCKED / static defect | Muse |
| QA-09 | EDHREC inclusion fraction reconciliation | counts checked but fraction is not | BLOCKED / static defect | Muse |
| QA-10 | All 6 bracket snapshots * 25 commanders | 3 pilot commanders claimed locally | NOT VERIFIED / PARTIAL | Muse |
| QA-11 | Card Atlas 1,078 statuses persisted | 425/582/71/0 reported locally | NOT VERIFIED | Muse |
| QA-12 | Web save/load/remove/compare/export | No such controls in app.html | FAIL (static) | Muse |
| QA-13 | Scryfall official download format | `sync_scryfall` names raw JSON download .jsonl.gz | BLOCKED / static defect | Muse |
| QA-14 | CI (pytest, import, browser smoke) | GitHub Actions runs=0 | NOT VERIFIED | Muse |
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
