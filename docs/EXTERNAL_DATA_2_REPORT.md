# External Data 2 — Abschlussbericht (2026-11-12)

Branch `muse/external-data-2` in `deckbuild-studio-ext2`
(Basis: Integrationsstand = GitHub-main `fe7f20e6`-Inhalt).
Auftrag: externe Datenquellen D1/D3/D4 sammeln, normalisieren/
kuratieren und sauber einpflegen — im Projekt-Stil (manuelle,
gecachte CLI-Syncs; Provenienz je Datensatz: Quelle/URL, Zeitpunkt,
SHA-256, Parser-Version; ehrliche Statuswerte; UNAVAILABLE ist nie 0).

Alle Live-Läufe liefen auf einer **Kopie** der echten DB
(`~/workspace/projects/ext2-verify-data/deckbuild.sqlite3`,
transaktionssichere sqlite3-`.backup`-Kopie, `PRAGMA
integrity_check` = ok; Backup der Kopie vor den Schreibläufen:
`deckbuild.sqlite3.bak-pre-ext2`). Auf die echte DB wurde NICHT
geschrieben (parallele Lane). Nenner aller Abdeckungen: die
**1.324 Identitäten** der Sammlung `foundation-schwarze-box`.

Vorher-Stand aller drei Schichten: nicht vorhanden (NOT_FETCHED,
0/1.324) — es sind neue Schichten.

---

## D1 — Scryfall Rulings (Bulk)

**Status: AVAILABLE** (nach Behebung eines echten Fetcher-Bugs, s. u.)

- Zugang: offizieller Bulk-Index `https://api.scryfall.com/bulk-data`
  wird zuerst gelesen; verwendet wird die jeweils aktuelle
  `jsonl_download_uri` des Eintrags `rulings` (nicht hartkodiert).
  Datei zum Laufzeitpunkt: `rulings-20261112100039.jsonl.gz`,
  komprimiert 5.295 KiB (Index-Metadatum), `updated_at`
  2026-11-12T10:00:39Z.
- Eingepflegt: **79.706 Rulings gesamt** (davon `wotc` 79.637,
  `scryfall` 69) über 20.080 distinkte oracle_ids, normalisiert in
  `card_ruling` unter einem Snapshot (`scryfall` /
  `scryfall_rulings`, Parser `scryfall-rulings/1.0.0`, SHA-256 der
  Datei im Snapshot).
- **Sammlungs-Abdeckung nachher: 725/1.324 (54,8 %) mit ≥ 1 Ruling;
  2.366 Rulings auf Sammlungskarten.** Die übrigen 599 Karten haben
  schlicht keine publizierten Rulings (leere Liste = Datum, kein
  Fehler, keine Rückfüllung).
- Idempotenz live verifiziert: Zweiter Lauf `cached: true`
  (Abgleich über das `bulk_updated_at` des Index; Download
  übersprungen). `--force` lädt erneut.
- Fehlerpfade (getestet): Index-HTTP-500 → BLOCKED-Snapshot;
  Index ohne `rulings`-Eintrag → BLOCKED; Datei-404 → NOT_FOUND;
  kaputte JSONL-Zeilen → PARTIAL mit Zählung im Detail;
  korruptes gzip → PARTIAL/unreadable; Robots-Verbot → BLOCKED;
  transienter Netzwerkfehler → `RulingsError`, KEIN Snapshot
  (bleibt NOT_FETCHED).
- Anzeige: `/api/external/card` liefert `rulings`
  (Status + Items); Karten-Schublade zeigt den Abschnitt
  „Regelhinweise" (Quelle WotC/Scryfall, Datum, Text) nur, wenn
  Rulings existieren.
- **Fetcher-Bug (echter Fund, gefixt + Regressionstests):** Der
  erste Live-Lauf endete ehrlich BLOCKED: `data.scryfall.io`
  liefert eine Cloudflare-verwaltete robots.txt, deren Wildcard-
  Gruppe `Allow: /` (kein Disallow) trägt und direkt vor benannten
  Training-Crawler-Gruppen mit `Disallow: /` steht.
  `_robots_rules` beendete Gruppen nur an Disallow-Zeilen, also
  „blutete" der `*`-Agent in die Folgegruppe und deren
  `Disallow: /` wurde als Wildcard-Sperre des ganzen Hosts
  fehlgedeutet. Fix nach RFC 9309: `allow`-Zeilen zählen als
  Regelzeilen für die Gruppen-Terminierung (gesammelt werden
  weiterhin nur Disallow-Präfixe). Danach: Lauf AVAILABLE.
  Der Wildcard-Gruppe ist per `Content-Signal: use=reference`
  Referenz-Nutzung erlaubt — dieses Tool cached lokal zu
  Referenz-Zwecken; kein Training, kein Search-Index.
- Neuer CLI-Befehl: `sync-rulings [--collection] [--force]`.

## D3 — EDHTop16

**Status: AVAILABLE für die publizierten Play-Rates;
Conversion/Entries per Karte NICHT importiert (von der Quelle auf
der öffentlichen Seite nicht publiziert — kein BLOCKED des Zugangs,
sondern ehrlich fehlende Felder).**

Zugangs-Prüfung mit Belegen (2026-11-12):

- `GET https://edhtop16.com/robots.txt` → HTTP 200, 24 Byte:
  `User-agent: *` mit LEEREM `Disallow:` — öffentliche Seiten sind
  robots-seitig nicht ausgeschlossen.
- `/about` wirbt mit „a robust API", aber es existieren keine
  auffindbaren API-Dokumente, keine Basis-URL, kein Key-Verfahren.
  Die Frontend-Daten laufen über eine undokumentierte interne
  GraphQL (Relay Persisted Queries, in den Seiten eingebettet).
  Nach Projekt-Präzedenz (Scryfall Tagger, docs/EXTERNAL_DATA.md)
  ist eine undokumentierte interne API kein provenienztragfähiger
  Importweg → **nicht genutzt, nichts umgangen**.
- Genutzt wird die öffentliche, servergerenderte Staples-Seite
  (`/staples`) mit ihrem eingebetteten Payload — dasselbe Muster wie
  EDHREC-RSC und Spellbook-SSR in diesem Projekt. Feldprüfung aller
  1.332 eingebetteten Datensätze: je Karte NUR Name, Typzeile,
  Manakosten, `playRateLastYear`. **Top-Cut-Conversion und
  Entry-Zahlen je Karte werden dort nicht publiziert** → sie bleiben
  abwesend (NULL), werden nicht abgeleitet oder erfunden. Auch der
  exakte Nenner der Rate wird auf der Seite nicht offengelegt
  (Beschriftung: „based on tournament data from the last year") →
  keiner gespeichert.
- Eingepflegt: **1.332 publizierte Karten**, Namensauflösung gegen
  den lokalen Scryfall-Store **1.332/1.332 (100 %)**, Tabelle
  `edhtop16_card_stat`, Snapshot `edhtop16` / `edhtop16_staples`,
  Parser `edhtop16-staples/1.0.0`. Rate wird verbatim als publiziert
  gespeichert (Bruchteil).
- **Sammlungs-Abdeckung nachher: 49/1.324 (3,7 %)** — nur 49
  Sammlungskarten sind cEDH-Staples des letzten Jahres; der Rest ist
  schlicht nicht gelistet (`listed: False`, Rate NULL — ausdrücklich
  KEINE 0). Stichproben: Wishclaw Talisman 0,589; Forest 0,516;
  Llanowar Elves 0,355; Arcane Signet 0,287.
- Anzeige: Badge in der Karten-Schublade mit klarer Kennzeichnung
  „cEDH-Turniere (EDHTop16, letztes Jahr): Play-Rate … %", nur für
  gelistete Karten; Tooltip weist aus, dass die Quelle den exakten
  Nenner nicht offenlegt.
- Neuer CLI-Befehl: `sync-edhtop16 [--collection] [--force]`.

## D4 — MTGJSON (nur additive Scheiben)

**Status: AVAILABLE (alle drei Scheiben).**

Dateigrößen VOR dem Voll-Download per HEAD gemessen (2026-11-12)
und mit den tatsächlich geladenen Bytes abgeglichen (identisch):

| Datei | Bytes (HEAD = geladen) | Verwendung |
|---|---|---|
| `AllPrintings.json.gz` | 185.593.989 | nicht geladen (xz-Zwilling genutzt) |
| `AllPrintings.json.xz` | 100.578.120 | Drucke + foreignData |
| `AllPrices.json.gz` | 148.153.354 | 90-Tage-Historie (nur Streaming-Filter) |
| `AllPricesToday.json.gz` | 5.617.621 | Tagespreise |

- Rohdateien liegen nur im Arbeits-/Datenordner (gitignored), nie
  im Repo, nie im Snapshot-Store. Persistiert wird ausschließlich
  die Sammlungs-Scheibe; die Historie wird in EINEM Streaming-Durch-
  lauf auf die Druck-uuids der Sammlung gefiltert.
- **Printings:** 115.916 Karten gestreamt; **0 ohne
  `scryfallOracleId`** → quellen-seitige Mapping-Quote 100 %.
  Behalten: **12.342 Drucke, die 1.324/1.324 Sammlungs-Identitäten
  (100 %) abdecken**, plus 47.110 fremdsprachige Zeilen
  (`foreignData`: Druckname, Sprache, Multiverse-ID, eigene
  MTGJSON-uuid je Sprachdruck) = 59.452 Zeilen in `mtgjson_print`.
- **Preise heute** (Build 5.3.0+20261111, Stichtag 2026-11-11):
  **68.656 Papier-Preispunkte** über 11.386 bepreiste Drucke;
  **1.324/1.324 Identitäten** über ≥ 1 Druck bepreist.
  Provider-Matrix (Feldnachweis am echten File): cardkingdom
  USD retail 15.055 + buylist 6.665; cardmarket EUR retail 15.588;
  manapool USD retail 15.495; tcgplayer USD retail 15.853;
  Finishes normal/foil/etched. **Cardsphere existiert in diesem
  Build nicht** (nicht erfunden); der mtgo-Block (cardhoarder) ist
  digital und wird übersprungen (0 Zeilen, per Abfrage verifiziert).
  Cardmarket/TCGPlayer überlappen herkunftsseitig mit Scryfalls
  Guide-Preisen; Card Kingdom, Manapool und alle Buylist-Preise
  sind neu (additiv, eigene Provenienz-Schicht `mtgjson_price`).
- **90-Tage-Historie** (Opt-in `--history`): **5.981.304
  Preispunkte** über 11.397 Drucke, 89 distinkte Datumswerte
  2026-08-13..2026-11-11 in der Scheibe (zwei Kalendertage im
  Fenster tragen für diese Scheibe keine Punkte). Datei enthält
  114.934 uuids (Today: 114.658).
- Idempotenz live verifiziert: kompletter Re-Lauf mit `--history`
  in ~9 s, alle drei Scheiben `cached: true` (SHA-256 der Dateien
  wird beim Streaming berechnet und im Snapshot-Payload geführt;
  unveränderte Datei → Parse übersprungen).
- Stichproben: Arcane Signet (40K #227): CK retail normal 4,99 USD,
  CK buylist 1,50 USD, Manapool 4,25 USD, Cardmarket 3,66 EUR,
  TCGPlayer 4,31 USD — plausible Marktwerte; deutsche Drucknamen
  vorhanden (z. B. „Verdammen", „Heilige Stärke").
- Neuer CLI-Befehl:
  `sync-mtgjson [--collection] [--download] [--history] [--dir]`.
  Lese-Helper `card_market_prices(store, oracle_id, history=…)`.

---

## Neue/geänderte Dateien

**Neu:** `src/deckbuild_studio/rulings.py`,
`src/deckbuild_studio/edhtop16.py`, `src/deckbuild_studio/mtgjson.py`,
`tests/test_external_data_2.py`,
`tests/fixtures/scryfall_rulings.jsonl`,
`tests/fixtures/scryfall_bulk_index.json`,
`tests/fixtures/edhtop16_staples.html`,
`tests/fixtures/mtgjson_printings.json`,
`tests/fixtures/mtgjson_prices_today.json`,
`tests/fixtures/mtgjson_prices_history.json`,
`docs/EXTERNAL_DATA_2_REPORT.md`.

**Geändert:** `src/deckbuild_studio/store.py` (neue Tabellen
`card_ruling`, `edhtop16_card_stat`, `mtgjson_print`,
`mtgjson_price` — per `CREATE TABLE IF NOT EXISTS`, keine Migration
nötig), `src/deckbuild_studio/external.py` (`_SOURCES` um scryfall/
edhtop16/mtgjson ergänzt), `src/deckbuild_studio/cli.py` (drei neue
Kommandos + Hilfe), `src/deckbuild_studio/web.py`
(`/api/external/card` um `rulings` + `edhtop16` erweitert),
`src/deckbuild_studio/static/app.html` (Schubladen-Abschnitte
„Regelhinweise" + EDHTop16-Badge, HTML-Escaping für Ruling-Texte),
`src/deckbuild_studio/httpfetch.py` (Robots-Gruppen-Fix, s. D1),
`docs/EXTERNAL_DATA.md` (Abschnitt „Data expansion 2"),
`.gitignore` (Fixtures-Ausnahme `*.jsonl`, `mtgjson-raw/`).

## Tests

- Neu: `tests/test_external_data_2.py` — 20 Tests (D1: 7, D3: 4,
  D4: 5, Web-API: 2, Robots-Regression: 2), alle offline gegen
  Fixtures, inkl. Fehlerpfade (BLOCKED/NOT_FOUND/PARTIAL/Netzwerk,
  kaputtes JSONL/gzip, fehlende Dateien, Idempotenz).
- Native Suite gesamt (finaler Baum): **231 passed** (734 s).
- QA-Suite `qa/`: **10 passed**.
- Ruff: **All checks passed!**
- Baseline vor den Änderungen: 211 native Tests grün → +20 neue.

## Commits (nur lokal, kein Push)

- `9dbd96a` feat(external-data-2): Scryfall rulings bulk sync (D1) +
  EDHTop16 staples play rates (D3) [inkl. D4-Modul + Tabellen]
- `01b6744` fix(tests): commit the scryfall rulings JSONL fixture
- `2dbddff` fix(httpfetch): robots group termination counts Allow
  lines (RFC 9309)
- Abschluss-Commit: docs (EXTERNAL_DATA.md-Abschnitt „Data
  expansion 2" + dieser Bericht) und Tooltip-Wording in app.html
  (Nenner-Ehrlichkeit) — Hash s. Git-Log auf diesem Branch.

## Ehrliche Restpunkte

1. **Echte DB nicht beschrieben** (Aufgaben-Vorgabe; eine andere
   Lane schrieb parallel). Die drei Kommandos laufen unverändert
   gegen den echten Datenordner; der erste Lauf dort steht noch
   aus. Alle Zahlen oben stammen von der verifizierten Kopie.
2. **EDHTop16 Conversion/Entries** sind über keinen
   provenienztragfähigen Weg verfügbar (nur undokumentierte interne
   GraphQL). Erneut prüfen, falls EDHTop16 eine dokumentierte API
   veröffentlicht.
3. **MTGJSON-Historie bläht Snapshots auf** (~6 Mio. Zeilen je
   Historien-Snapshot in der Kopie gemessen). Eine Retention-/
   Rotationsregel für Snapshot-Historien existiert projektweit
   nicht (gilt für alle Schichten gleichermaßen) — nicht Teil
   dieses Pakets.
4. **MTGJSON-Preise werden noch nicht in der UI gerendert**
   (gespeichert + per `card_market_prices()` lesbar; D4 verlangte
   keine Anzeige — D1/D3-Anzeigen sind umgesetzt).
5. **Umgebungs-Reparatur (kein Repo-Change):** Die `.venv` dieser
   Arbeitskopie zeigte per Editable-`.pth` auf den decks-Klon; für
   die Läufe auf den ext2-Baum korrigiert (sonst hätten Tests den
   falschen Baum importiert).

---

## Nachtrag 2026-11-12 — Preis-Historie und Marktplatz-Preise entfernt (Owner-Entscheid)

Per Owner-Entscheid vom 2026-11-12 („in dem Tool kein
Preis-Historie-Ding und auch kein Store oder
Neue-Karten-dazu-Kauf-Features — erstmal nur die Karten, also das
komplett entfernen") wurden die in D4 beschriebenen
**MTGJSON-Marktplatz-Preise (AllPricesToday) und die
90-Tage-Preis-Historie (AllPrices) vollständig entfernt** — im
Integrations-Branch `muse/integration-wave-2`, bevor diese Schicht
GitHub-main oder die echte DB je erreichte. Von MTGJSON bleibt
ausschließlich Karten-Daten bestehen: Druck-Mapping
(identifiers → oracle_id/scryfall_id) und fremdsprachige
Drucknamen (`foreignData`); `sync-mtgjson` besteht mit genau
diesem Umfang fort. Kauf-URLs (`purchaseUrls`) wurden von dieser
Schicht zu keinem Zeitpunkt gespeichert oder angezeigt
(Volltext-Prüfung). Die obenstehenden D4-Zahlen beschreiben den
historischen Lane-Stand vor der Entfernung; die lebende Doku ist
`docs/EXTERNAL_DATA.md`. Details und Verifikation:
Entfernungs-Nachtrag in `docs/INTEGRATION_WAVE_2.md`.
