# QA-Fixes zu PR #3 — Kommentar 6806751003 (unabhängige statische QA)

Branch `muse/qa-fixes-1` ab Phase-2-Stand `23a92e7`. Alle 10 Findings
(3× P0, 7× P1) sind behoben und mit Tests belegt: **91 Tests grün**
(59 Bestand + 32 neue in `tests/test_qa_fixes.py`), Ruff sauber.
Pro Finding: Befund → Fix → Testbeleg → Commit.

## P0.1 — Scryfall-Formate robust (Commit `1a5732a`)

- **Befund:** `sync_scryfall` speicherte den `download_uri`-Download
  (unkomprimiertes JSON-Array) als `default-cards.jsonl.gz`; `_objects`
  parste nach Zielnamen (gzip + JSONL) und wäre am realen Format
  gescheitert.
- **Fix:** Formaterkennung am **Inhalt**: Gzip über Magic Bytes
  (`1f 8b`), Array vs. JSONL über das erste Nicht-Whitespace-Zeichen.
  JSONL wird zeilenweise gestreamt, JSON-Arrays über einen inkrementellen
  Decoder (64-KiB-Chunks) — kein Voll-Laden. `sync_scryfall` behandelt
  beide Bulk-Index-Felder (`jsonl_download_uri` bevorzugt,
  `download_uri` als Fallback) und speichert die Datei unter einem Namen,
  der ihrem echten Format entspricht.
- **Beleg:** Parametrisierte Tests aller 5 Formatvarianten inkl.
  Namens-/Inhalts-Widerspruch in beide Richtungen (Datei heißt
  `.jsonl.gz`, enthält Roh-Array; Datei heißt `.json`, enthält
  Gzip-JSONL), Multi-Chunk-Streaming (300 Karten), Garbage-Ablehnung,
  gemockter Bulk-Index-Sync für beide URI-Felder.

## P0.2 — Ungültige Decks sind Entwürfe, nie legal (Commits `aa4a709`, `0bd8796`)

- **Befund:** `create_deck` committete auch bei `valid=False`, ohne den
  Status festzuhalten.
- **Fix:** Schema v2: `deck_revision.status` (`legal` | `draft`) aus der
  Validierung zum Speicherzeitpunkt. Migration bestehender Revisionen:
  Default `draft` (nie rückwirkend als legal behauptet). Entwürfe werden
  gespeichert (kein Arbeitsverlust), aber: Text-Exporte tragen die
  Kopfzeile `# ENTWURF — nicht legal`, die API liefert den Status als
  Feld (`status` in Responses, `X-Deck-Status`-Header beim Export), und
  `export_revision(..., require_legal=True)` bzw.
  `GET …/export?legal_only=true` verweigert Entwürfe (HTTP 409).
  Commander-Menge/Verfügbarkeit bleiben Teil der Validierung.
- **Beleg:** Tests: ungültiges Deck → `draft`, Export gekennzeichnet,
  Legal-Export wirft/409; gültiges 100-Karten-Deck → `legal`, Export
  ohne ENTWURF-Kopf; Migrations-Test v1→v2.

## P0.3 — Frontend-Flows verdrahtet (Commits `75ecee8`, `23ef843`)

- **Befund:** `app.html` hatte nur Pool laden / Hinzufügen / Validate;
  Speichern, Laden, Entfernen, Revisionen, Varianten, Vergleich und
  Export fehlten in der Oberfläche.
- **Fix:** Neue API-Endpunkte (`GET /api/decks`,
  `GET /api/decks/{deck_id}/revisions`,
  `GET /api/decks/revision/{revision_id}`, `DELETE /api/decks/{deck_id}`)
  und vollständige UI-Flows im Deckbuilder-Tab: Deck speichern, als
  Variante speichern (neue Revision mit Parent), Deck-/Revisionslisten,
  Revision in den Builder laden, Deck entfernen, zwei Revisionen
  vergleichen (Diff mit Kartennamen + Status), Export-Links mit
  sichtbarem Legal-/Entwurf-Status.
- **Beleg:** TestClient-E2E über den kompletten Flow (Speichern →
  Variante → Listen → Laden → Vergleich → Export/409 → Löschen → 404),
  Index-HTML enthält alle Flow-Controls; zusätzlich dokumentierter
  Live-Check `scripts/browser_workflow_check.py` gegen einen echten
  HTTP-Server (Throwaway-Datenordner): **alle 17 Prüfschritte PASS**
  (Seite, Controls, Commander, Pool, Validate, Save legal, Variante,
  Revisionen, Laden, Vergleich, Export 100 Karten, Löschen).

## P1.4 — card_id beim Primärimport (Commit `7a966aa`)

- **Befund:** `_import_simple_rows` schrieb Lots mit `card_id=NULL`;
  im echten Datenordner waren **alle 1.089 Lots ohne card_id**
  (Vorab-Messung auf einer Kopie bestätigt).
- **Fix:** Auflösungsreihenfolge je Oracle-Identität: (1) vorhandene
  `card_identity`, (2) optionale Registry-Datei (JSON/CSV
  oracle_id→card_id; CLI `--card-id-registry`), (3) deterministisch
  generiert `card_id = "card_" + sha256(oracle_id)[:24]`, in
  `identity_evidence` offen als `generated:sha256(oracle_id)`
  gekennzeichnet. `apply_card_id_registry()` (CLI
  `apply-card-id-registry`) ersetzt später gezielt generierte IDs durch
  bekannte und zieht Lots konsistent mit; eine vorhandene
  nicht-generierte ID, die der Registry widerspricht, wird als Konflikt
  gemeldet und **nicht** still überschrieben.
- **Beleg:** Unit-Tests (generierte IDs + Stabilität über Re-Import,
  Registry beim Import, Registry nachträglich inkl. Konfliktfall,
  CSV-Registry). **Echtlauf** (zuerst auf Datenkopie, danach mit Backup
  `deckbuild.sqlite3.bak-qa` im echten Datenordner): Re-Import des
  Primärbestands → **1.089/1.089 Lots mit card_id, 1.078
  card_identity-Zeilen, 0× NULL**; Zahlen unverändert (1.438 Exemplare,
  Foundation 285 / Schwarze Box 1.153); zweiter Import →
  card_id-Mapping identisch (idempotent); Commander weiter exakt
  25 eligible / 0 needs_review.

## P1.5 — Mehrere Lots pro Karte/Ort verlustfrei (Commits `aa4a709`, `7a966aa`)

- **Befund:** `UNIQUE(collection_id, oracle_id, location_id)` ließ
  normalisierte Lots gleicher Karte am selben Ort zusammenfallen.
- **Fix:** Schema v2: `physical_lot.lot_key`, Eindeutigkeit jetzt
  `(collection_id, oracle_id, location_id, lot_key)`; Tabellen-Rebuild
  als Migration (Legacy-Zeilen behalten ihre `physical_lot_id`,
  `lot_key=''`). Importer A nutzt die echte `physical_lot_id` als
  `lot_key` (eigenständige Datensätze); das einfache Format nutzt
  `lot_key=''` als aggregiertes Snapshot-Lot (Verhalten unverändert);
  `replace-snapshot` verwaltet nur noch `lot_key=''`-Lots.
- **Beleg:** Synthetisches normalisiertes Workbook mit 2 Lots gleicher
  Karte am selben Ort (NM 3×/1 reserviert, LP 2×/0) → beide Lots
  erhalten, Mengen/Reservierungen getrennt, Verfügbarkeit 4;
  Migrations-Test auf handgebauter v1-DB.

## P1.6 — Partner-Regeln korrekt (Commit `0bd8796`)

- **Befund:** `^Partner\b` matchte auch „Partner with X“ als freies
  Partner; `_pair_legal` prüfte den benannten Partner nicht.
- **Fix:** Freies Partner nur noch als `^Partner\s*\(` (so wird es
  gedruckt). Neuer Helfer `partner_with_target()`; trägt eine Karte
  „Partner with“, müssen **beide** Karten es tragen und einander exakt
  benennen (Abgleich gegen Voll- und Frontname).
- **Beleg:** Paar-Matrix als Tests: Partner-with gegenseitig legal;
  Partner-with + generisches Partner illegal; Partner-with mit
  falschem Ziel illegal; freies Partner legal; Choose a Background +
  Background-Subtyp legal / mit falschem Partner illegal; Doctor's
  Companion + Time Lord Doctor legal; Companion+Companion und
  Doctor+Doctor illegal. Bestandstests (Partner-Paar-Deck) weiter grün.

## P1.7 — Mengen strikt validieren (Commit `7a966aa`)

- **Befund:** `_int` machte aus `1.9` still `1` (float-Truncation).
- **Fix:** Strikte Prüfung in allen Importern: negativ, gebrochen,
  nicht-numerisch und nicht-endlich → `ImportFailure` mit klarer
  Meldung je Zeile (Feld + Wert + Grund); zusätzlich Defence-in-Depth
  in `_import_simple_rows`. Ganzzahlige Zellen (2.0, „2,0“) bleiben ok.
- **Beleg:** Parametrisierte Ablehnungstests (1.9 / −1 / „abc“ / „inf“ /
  „1,9“) inkl. Rollback (0 Lots); Update-Szenarien: neue Karte,
  Mengenerhöhung, Mengensenkung, neuer Standort, im neuen Snapshot
  fehlende Karte bleibt erhalten (Upsert löscht nie).

## P1.8 — Startreihenfolge (Commits `7a966aa`, `fe833af`)

- **Fix:** README zeigt jetzt Scryfall zuerst (`sync-scryfall` bzw.
  `import-scryfall`), dann `import-inventory`. Importer B/C brechen bei
  leerem Scryfall-Store mit eindeutiger Meldung ab: „Zuerst
  import-scryfall/sync-scryfall ausführen …“, statt jeden Namen einzeln
  als unauflösbar zu melden.
- **Beleg:** Test auf leerem Store prüft die Meldung.

## P1.9 — API/UI-Kontext (Commit `75ecee8`)

- **Befund:** `GET /api/cards` ignorierte `commander_oracle_id`;
  Favoriten/Notizen waren im UI nicht bearbeitbar.
- **Fix:** Mit `commander_oracle_id` liefert jede Karte
  `commander_legal`, `in_commander_identity` und `in_commander_pool`
  (gleiche Regeln wie `decks.legal_pool`; unbekannte Commander-ID →
  404). Die Sammlung zeigt den Pool-Status als Badge, wenn ein Commander
  gewählt ist. Favorit (★-Toggle) und Notiz (Feld + Speichern) sind je
  Karte im UI bearbeitbar (`POST /api/marks`, Merge-Semantik wie im
  Marks-Import). Deckvarianten-Verwaltung siehe P0.3.
- **Beleg:** TestClient-Tests für Kontext-Flags (Commander selbst nie im
  Pool, Off-Color draußen, 404-Fall, Felder fehlen ohne Parameter) und
  Mark setzen/entfernen inkl. Notiz.

## P1.10 — CI lokal nachgewiesen (Commit `fe833af`)

- **Fix:** `.github/workflows/tests.yml` (aus der vorbereiteten Datei
  übernommen und erweitert): pytest, Ruff-Check (`ruff` in den
  Test-Deps, Minimalkonfiguration in `pyproject.toml`),
  Import-Smoke (`import deckbuild_studio` + `mtg-deckbuilder --help`).
  4 Ruff-Funde im Bestand (2 ungenutzte Imports, 2 tote Zuweisungen in
  Tests) bereinigt.
- **Beleg (lokal, alle Schritte der Reihe nach ausgeführt):**
  `ruff check src tests` → *All checks passed!*;
  `python -c "import deckbuild_studio"` → ok;
  `mtg-deckbuilder --help` → ok;
  `pytest -q` → **91 passed**.
- **Offen (ehrlich):** Der GitHub-Push der Workflow-Datei ist durch die
  fehlende „Workflows“-Permission der GitHub-App blockiert (403,
  bekannt). Die Datei liegt im Branch bereit; sobald die Permission
  erteilt ist oder der Owner die Datei einspielt, läuft dieselbe
  Pipeline auf GitHub.

## Gesamtnachweis

- Tests: 59 (Bestand) + 32 (neu) = **91 passed**, Ruff sauber.
- Echtläufe nur auf Datenkopien; einziger Echtlauf im echten Ordner war
  die card_id-Verifikation (P1.4) mit vorherigem Backup
  `~/.local/share/mtg-collection-deckbuilder/deckbuild.sqlite3.bak-qa`
  (liegt weiterhin dort; Wiederherstellung jederzeit möglich).
- Keine GitHub-Schreibzugriffe; keine privaten Daten im Repository
  (nur aggregierte Zählwerte in dieser Doku).
