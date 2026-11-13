# Integration Wave 2 — Gesamtbaum (2026-11-12)

Branch `muse/integration-wave-2` in `deckbuild-studio-integration`.
Basis: decks-Klon @ `3ff70e9` (= Inhalt von GitHub-main `fe7f20e6`:
Basis + Kategorien + Tierlist 1.0.0 + Decklisten/Settings).
22 Commits über der Basis: 21 übernommene + 1 Integrations-Commit
(`772b571`). Keine GitHub-Schreibzugriffe, keine Schreibläufe auf die
echte DB — alle Verifikation lief auf einer Kopie
(`verify.sqlite3`, Backup `verify.sqlite3.bak-integration-wave2`).

## Übernahme je Quelle

### 1. Upstream-Fix `bbb37a5` (Inclusion, CPL #1207)
Cherry-pick `e0ae27b`, konfliktfrei (direkter Nachfolger der Basis).
Inhalt: Decks ohne zählbare Karte verlassen den Nenner;
`_canonical_decks` liefert `(canonical, excluded)`; Universum-Queries
über eine TEMP-Tabelle (`json_each`, eine gebundene Variable) statt
eines `?` je Deck.

### 2. External-Data-2 (`9c533c5`, 4 Commits)
Cherry-pick der Reihe `3ff70e9..muse/external-data-2`, konfliktfrei
(Basis identisch). Neue Module `rulings.py` / `edhtop16.py` /
`mtgjson.py`, store.py +4 Tabellen (`card_ruling`,
`edhtop16_card_stat`, `mtgjson_print`, `mtgjson_price`), CLI-Befehle
`sync-rulings` / `sync-edhtop16` / `sync-mtgjson`, Karten-Schublade mit
Regelhinweisen + EDHTop16-Badge, httpfetch mit RFC-9309-robots-Fix
(Gruppen-Ende zählt auch `Allow:`-Zeilen). Bericht der Lane:
`docs/EXTERNAL_DATA_2_REPORT.md`.

### 3. Daten-Vervollständigung (`1f555df`, 10 Commits ab `a2090b7`)
Cherry-pick der Reihe `5d13554..1f555df` (kein Merge gegen `a2090b7` —
der Stand enthält bewusst keinen Decklisten-Stack). Inhalte:
Playgroup-Parser 2.2.0, Commander-Page-Parser 1.1.0, Spellbook-Parser
1.2.0 (Split-Karten per Vollname), Split-Slug-Regel für
EDHREC-Kartenseiten, Heuristik `oracle-heuristic/2.1.0`,
Tagger-Vokabular 1.1.0 (`card_selection`→`loot`, `stax`⊃`hatebear`),
Tagger-Bulk-Route (`oracle_tags` als Primärquelle, Search-API als
Fallback `--via-search`). store.py / app.html / tierlist.py wurden von
dieser Lane nicht berührt.
**Einziger Konflikt:** `cli.py`-Hilfetext zu `sync-tagger` (HEAD hatte
dort zusätzlich die ext2-Befehle). Union: neuer Bulk-Hilfetext der
Daten-Lane + alle ext2-Befehlsbeschreibungen bleiben stehen.

### 4. Tierlist 1.1.0 (`40d97df`, eigene Commits)
Übernommen: `d61d46e` (Spec, Anlage der Datei), `58fb384` (Spec Rev. 2),
`bdb8ef3` (Implementierung), `0096e7c` (Tests/Doku), `558fe05`
(Legacy-DB-Fix), `40d97df` (Spec-Nachtrag). Der darunterliegende
Port-Commit `8cedf8f` wurde NICHT übernommen (der Decklisten-Stack ist
in der Basis neuer enthalten: Merge `a2033c0` + Upstream-Fix).
Textuell liefen alle Cherry-picks sauber durch — die inhaltlichen
Kollisionen mit dem Upstream-Fix lagen eine Ebene tiefer (s. u.).

## Semantische Union (Integrations-Commit `772b571`)

Der Upstream-Fix und Tierlist 1.1.0 wurden parallel gegen denselben
a6f2776-Stand entwickelt; drei Stellen mussten inhaltlich vereinigt
werden, obwohl git keinen Konflikt meldete:

1. **`inclusion.cooccurrence`** rief `_canonical_decks(...)` mit der
   alten Listen-Rückgabe auf → Laufzeitfehler mit der neuen
   Tupel-Rückgabe. Fix: Tupel entpacken; die Definition weist jetzt
   `excluded_no_countable_card` aus. Zusätzlich lief die Deck-Abfrage
   über ein `?` je Deck (bis 9.015 Variablen) und das Namens-Lookup
   über ein `?` je Partner (Sol Ring: 20.969 Partner) — beides auf das
   Upstream-Verfahren umgestellt (TEMP-Tabelle bzw. 500er-Chunks).
2. **`tierlist._canonical_universe`** kannte die Upstream-Regel nicht:
   Es faltete nur inhaltsgleiche Decks zusammen, Commander-only-Listen
   und leere Decks blieben im Nenner (9.048 statt 9.015) — im
   Widerspruch zum eigenen Anspruch „spiegelt inclusion.py exakt" und
   zum Inclusion-Nenner. Fix: Decks ohne zählbare Karte (Menge > 0,
   nicht der Commander-Eintrag) verlassen das Universum; die Zahl der
   so ausgeschlossenen Decks steht je Universum in der Definition
   (`excluded_no_countable`, fließt in die Snapshot-ID ein, analog zu
   `excluded_no_timestamp`).
3. **`tierlist._load_decklist_selection`** band ebenfalls ein `?` je
   Deck (~9.211) → auf `_universe_table` umgestellt (gleiche Semantik,
   kein Variablen-Limit).

Union-Regeln geprüft: store.py = alle Tabellen aller Stände (30
`CREATE TABLE`, inkl. `decklist_deck.source_updated_at` + Migration,
`tier_assignment.universe_id` in DDL+PK); der Legacy-Fix ist
eingehalten — der Index `tier_assignment_universe` steht NICHT in der
store-DDL, sondern wird erst in `tierlist.ensure_schema` nach dem
Cache-Rebuild angelegt. httpfetch.py enthält beide Fixes
(IncompleteRead-Retry aus dem Decklisten-Strang + RFC-9309-robots aus
ext2). app.html/web.py/cli.py enthalten alle Blöcke/Endpunkte/Befehle
aller Stände (Settings/Inclusion, Kategorien-Filter, Universum-Kopf +
Verbreitungs-Badge, Ko-Okkurrenz-Schublade, Regelhinweise,
EDHTop16-Badge; `/api/verbreitung`, `/api/tiers/universes`,
`/api/cards/{id}/cooccurrence`, `sync-rulings|sync-edhtop16|
sync-mtgjson`, `sync-tagger` mit Bulk-Default).

## Gates (alle auf dem integrierten Baum)

| Gate | Ergebnis |
|---|---|
| Native Suite (`pytest`) | **282 passed**, 1 Warning (1.042,69 s unter langsamer IO) |
| QA-Suite (`pytest qa/`) | **10 passed** |
| Ruff | **All checks passed** |
| Legacy-Test (1.0.0-Schema-DB öffnet + migriert) | **passed** (in der Suite + explizit einzeln) |
| Erwartung Testzahl | > 231 → 282 erreicht |

## DB-Kopie-Verifikation (Kopie der echten DB, Stand 2026-11-12)

### Die drei neuen Syncs (auf der Kopie)
| Sync | Status | Abdeckung Sammlung |
|---|---|---|
| `sync-rulings` | AVAILABLE | **725/1.324** Karten mit ≥ 1 Ruling (2.366 Rulings; gesamt 79.706 gespeichert, 79.637 WotC / 69 Scryfall, 20.080 oracle_ids) |
| `sync-edhtop16` | AVAILABLE | **49/1.324** mit Play-Rate (1.332 publizierte Karten, 1.332/1.332 namensaufgelöst; Conversion/Entries publiziert die Quelle nicht → bleiben abwesend) |
| `sync-mtgjson --history` | AVAILABLE | **1.324/1.324** Identitäten, 12.342 Drucke (+ 47.110 Fremdsprachen-Zeilen, Mapping-Lücke 0); Preise heute 68.656 Punkte / 11.386 Drucke; Historie 5.981.304 Punkte / 11.397 Drucke (2026-08-13..11-11) |

Rohdateien für MTGJSON wurden aus dem ext2-Arbeitsordner
(`mtgjson-raw/`, gitignored) wiederverwendet.

### Tierlist-Compute `tierlist/1.1.0` (auf der Kopie)
- **Verbreitung, Profil `all`: Nenner = 9.015** ✅ (Snapshot-ID
  `universe:39ea68c5160d76d4:9015`; Aufteilung nach Brackets:
  **B2 3.729 / B3 3.687 / B4 1.599**; Plattform Archidekt 9.015;
  `excluded_no_countable` = 75 Deck-IDs, kanonische Dedupe −33
  gegenüber 9.048). 64 Profile, 203.696 Verbreitungs-Zeilen;
  gezählte Stufen gesamt: S 602 / A 798 / B 1.811 / C 3.389 /
  D 148.806 / U 48.290.
- **Globale Evidenz-Tier:** S 5 / A 28 / B 109 / C 134 / D 1.048 / U 1
  (1.325 Zeilen, s. Restrisiko 1).
- **Kontexte:** 192 gesamt (64 Commander × 3 Brackets),
  **178 mit bewerteten Karten** ✅ (Erwartung ≥ 178); 44.595
  Kontext-Zeilen (S 16 / A 13.169 / B 5.533 / C 15.321 / D 10.541 /
  U 15); A5-Fallback: 2.856 Top-Commander-Zeilen.
- **Ko-Okkurrenz-Smoke** (Integrations-Fix, echte Daten): Sol Ring —
  Nenner 9.015, 6.602 Decks mit der Karte, 20.969 Partner, Lift-Werte
  werden geliefert.

## Restrisiken / ehrliche Anmerkungen

1. **Global-Scope zählt 1.325 statt 1.324 Zeilen:** Der Compute ohne
   `--collection` läuft über die Identitäts-Registry
   (`card_identity`). Darin steht noch `Morcant's Loyalist` — die
   Identität existiert seit der Goliath-Korrektur ohne physischen Lot
   (Sammlung selbst: exakt 1.324 Identitäten mit Lots). Datenzustand
   der echten DB, kein Integrationsfehler; ein Compute mit
   `--collection` zeigt die Sammlungs-Sicht.
2. **Globale Verteilung leicht verschoben** gegenüber dem letzten
   1.0.0-Stand (B 114→109, C 122→134, D 1.052→1.048, U 3→1): Die Kopie
   enthält die neueren Re-Syncs der Daten-Vervollständigungs-Lane
   (u. a. Spellbook-Parser 1.2.0 mit Split-Karten-Matching, Atlas
   523→524 AVAILABLE) — Daten-Drift durch bessere Quellenstände,
   kein Modellwechsel (Evidenz-Modell 1.0.0 unverändert).
3. **Verbreitungs-Snapshot-IDs ändern sich** gegenüber dem
   Solo-Lauf der Tierlist-Lane, weil `excluded_no_countable` jetzt in
   der Universum-Definition steht und die kanonische Deckmenge kleiner
   ist (9.015). Absicht: Verbreitung und Inclusion zitieren ab jetzt
   denselben Nenner.
4. **Zeitraum-Filter wirkungslos auf dem Bestand:** Alle geernteten
   Decks haben `source_updated_at = NULL` (die Ernte lief vor dem
   Feld); mit gesetztem Zeitraum würden sie ehrlich ausgeschlossen
   und gezählt. Volle Wirkung erst nach der nächsten Ernte.
5. Die Verifikationsdateien (`verify.sqlite3`, `verify-data/`,
   Backup) liegen ungetrackt im Arbeitsbaum und sind nicht Teil der
   Commits. Kein Lauf hat die echte DB geschrieben.

---

## Nachtrag 2026-11-12 — Entfernung MTGJSON-Preis-Historie, Marktplatz-Preise, Store-/Kauf-Features (Owner-Entscheid)

**Entscheid (M, 2026-11-12 12:34, verbindlich):** „In dem Tool
kein Preis-Historie-Ding und auch kein Store oder
Neue-Karten-dazu-Kauf-Features oder so — erstmal nur die Karten,
also das komplett entfernen." Ausgeführt im Integrations-Branch
`muse/integration-wave-2`, **bevor** die MTGJSON-Schicht GitHub-main
oder die echte DB je erreichte. Von MTGJSON bleibt ausschließlich
Karten-Daten: Druck-Mapping (identifiers → oracle_id/scryfall_id)
und fremdsprachige Drucknamen (`foreignData`); `sync-mtgjson`
besteht mit genau diesem Umfang fort (Parser-Version ehrlich auf
`mtgjson-slice/2.0.0` angehoben). Nicht angefasst (nicht Teil des
Entscheids): Scryfall-Druckfakten inkl. Tagespreis in
`card_print_fact` (Budget-Marker), Rulings (D1),
EDHTop16-Play-Rates (D3), alle übrigen Schichten.

### Entfernt (Commits `f76abe0`, `cd85261`; gesamt 87 Insertions / 280 Deletions über 6 Dateien)

- **Preis-Historie:** CLI-Flag `--history` und alle
  Historien-Codepfade in `mtgjson.py` (`_sync_prices`-Historienzweig,
  `iter_price_entries`, `flatten_prices`), Historien-Fixture
  `tests/fixtures/mtgjson_prices_history.json` (gelöscht),
  Historien-Test `test_mtgjson_sync_history_opt_in` (ersetzt, s. u.),
  alle Historien-Stellen in der lebenden Doku.
- **Marktplatz-Preise (Heute-Werte):** Tabelle `mtgjson_price`
  inkl. Index `mtgjson_price_uuid` aus der Schema-DDL in
  `store.py` (−12 Zeilen); Schreibpfad `_sync_prices` und
  Lese-Helper `card_market_prices()` aus `mtgjson.py` (654 → 494
  Zeilen); Download-Umfang von `download_mtgjson` auf AllPrintings
  reduziert; Fixture `tests/fixtures/mtgjson_prices_today.json`
  (gelöscht); alle Preis-Erwartungen aus den Tests; Preis-Abschnitte
  in `docs/EXTERNAL_DATA.md` (komplett auf den reduzierten Umfang
  umgeschrieben).
- **API/UI:** Es existierte keine API-/UI-Anbindung der
  Marktplatz-Preise (der Lese-Helper war ungenutzt) — nichts zu
  demontieren; der CLI-Hilfetext nennt den reduzierten Umfang jetzt
  ausdrücklich („no prices, no purchase data").
- **Regressionsschutz:** Neuer Test `test_mtgjson_no_price_layer`
  pinnt die Entfernung (frisches Schema ohne `mtgjson_price`,
  kein Preis-API auf dem Modul, keine Preis-Snapshots nach einem
  Sync, `FILES == {"printings"}`).

### Kauf-URLs — ausdrückliche Bestätigung

Volltext-Suche (`purchase`, case-insensitiv) über `src/`, `tests/`,
`qa/` und `docs/`: **Die MTGJSON-Schicht hat zu keinem Zeitpunkt
Kauf-URLs (`purchaseUrls`) oder Kauf-Links gespeichert oder
angezeigt** — der Import las aus AllPrintings ausschließlich
`identifiers`, Set/Nummer/Name/Sprache/`multiverseId` und
`foreignData`. Es gab keine Store-/Kauf-Features zu entfernen;
verbliebene Treffer des Suchbegriffs sind die neuen ausdrücklichen
„keine Kauf-Daten"-Hinweise selbst. (Die Scryfall-Preisfelder in
`spellbook.py`/`card_print_fact` sind Guide-Preise, keine
Kauf-Links, und per Entscheid ausdrücklich Bestand.)

### Verifikation (nur Kopien; echte DB nie geschrieben)

- **DB-Kopie** (`verify-removal-data/deckbuild.sqlite3`, Kopie der
  Integrations-Verifikations-DB): Printings-Snapshot + `mtgjson_print`
  vorher geleert, Preis-Tabelle als Kontrolle stehengelassen
  (6.049.960 Zeilen). Reduzierter `sync-mtgjson` (nur AllPrintings
  im Rohverzeichnis): **AVAILABLE — 1.324/1.324 Identitäten**
  (12.342 Drucke, 47.110 Fremdnamen-Zeilen, 59.452 Druckzeilen,
  Mapping-Lücke 0), neuer Snapshot mit Parser
  `mtgjson-slice/2.0.0`. Danach: `mtgjson_price` weiterhin exakt
  **6.049.960 Zeilen (unangetastet)**, **keine neuen**
  `mtgjson_prices_*`-Snapshots, `PRAGMA integrity_check` = ok.
- **Frisches Schema:** Eine per CLI neu angelegte DB enthält nur
  `mtgjson_print`, kein `mtgjson_price`; der Sync meldet ohne
  Rohdatei ehrlich NOT_FETCHED.
- **Gates auf dem bereinigten Baum:** native Suite **282 passed**
  (Ausgangslage 282 — der entfernte Historien-Test wurde 1:1 durch
  den Entfernungs-Regressions-Test ersetzt), QA-Suite **10 passed**,
  **Ruff: All checks passed**.

### Ehrliche Restpunkte

- Bestehende DB-Dateien behalten die Tabelle `mtgjson_price` als
  tote Altlast (kein Migrations-Zwang) — betroffen sind nur
  Verifikations-Kopien; auf main und der echten DB existierte die
  Schicht nie.
- Die alten `mtgjson_prices_*`-Snapshots in den Verifikations-Kopien
  bleiben als Provenienz des Entfernungs-Zeitpunkts stehen.
- Verifikations-Artefakte (`verify-removal-data/`,
  `verify-removal-raw/`) liegen ungetrackt im Arbeitsbaum und sind
  nicht Teil der Commits.
