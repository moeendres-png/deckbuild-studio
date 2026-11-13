# TopDeck.gg-Schicht — Turnier-Decklisten, Spielergebnisse, selbst berechnete Conversion

Stand: 2026-11-13. Modul: `src/deckbuild_studio/topdeck.py` (Parser-ID
`topdeck-tournaments/1.1.0`; 1.1.0 anonymisiert Spielernamen beim
Import, s. §5), CLI: `sync-topdeck`, Tabellen:
`decklist_deck`/`decklist_card` (Kohorte `topdeck`), `topdeck_result`,
`topdeck_tournament`, `topdeck_card_stat`, Snapshots unter
`source_name='topdeck'`, `kind='topdeck_tournaments'`.

## 1. Quelle und Zugang

TopDeck.gg betreibt die Turnierplattform, deren Korpus auch EDHTop16
aggregiert. Als einzige geprüfte Quelle liefert sie **vollständige
Decklisten plus Spielergebnisse je Turnier** — daraus ist die
Conversion je Karte erstmals selbst berechenbar (die Größe, die
EDHTop16 nicht publiziert; vgl. `docs/DATA_SOURCES_EXPLORATION.md`
Abschnitt 2).

- Endpunkt: `POST https://topdeck.gg/api/v2/tournaments` (offizielle
  API v2, Query-Modus: `game="Magic: The Gathering"`,
  `format="EDH"` — exakt diese Schreibweisen; angefragte Spalten:
  `name, id, decklist, wins, draws, losses, winsBracket,
  lossesBracket`; mit `decklist` liefert die Antwort zusätzlich das
  strukturierte `deckObj` und je Standing das Feld `leader` =
  Commander-Name, Partner alphabetisch als `"A / B"`, DFC als
  Vorderseite).
- **Credential ausschließlich über den Connector `custom.topdeck`:**
  Die dynamische Credential-Surrogat-Mechanik
  (`dynamic_credentials.add_surrogate_to_request`,
  `allowed_hosts=["topdeck.gg"]`) setzt den hinterlegten API-Key in
  den `Authorization`-Header (roh, ohne „Bearer", wie die API-Doku es
  vorschreibt). Der echte Key existiert für den Code nicht: Er steht
  in keiner Umgebungsvariable, keiner Datei, keinem Log und keiner
  Datenbank. Ohne Connector-Zugang zeichnet der Sync **BLOCKED** auf
  und ruft nichts ab.
- Cloudflare bannt die Standard-Signatur von Python-urllib
  (HTTP 403, error code 1010) — der Client sendet einen normalen
  Client-User-Agent (wie der Connector-Helper). Redirects auf
  authentifizierten Requests sind deaktiviert.
- Key-Beschaffung (Owner-Schritt, erledigt 2026-11-12): TopDeck-Account
  → Developer-Portal → API-Key → Ablage im Secure Vault als Connector
  `custom.topdeck`. Key-Rotation ebenfalls dort.

## 2. Terms-Pflichten (Developer Terms, selbst gelesen)

- **§6.1 Attribution — Pflicht:** „Data provided by TopDeck.gg" mit
  Link auf https://topdeck.gg, sichtbar überall, wo die Daten
  angezeigt werden. Umsetzung: Die Karten-Antwort (`/api/external/card`)
  führt `attribution`/`attribution_url` im `topdeck`-Block mit, und
  die Karten-Schublade rendert die Attribution als eigenes Badge direkt
  unter dem „Turnier (TopDeck)"-Wert. Das Snippet folgt dem Beispiel
  aus der API-Doku.
- **§7:** Nur der dokumentierte API-Weg — kein Scraping, keine
  undokumentierten Routen.
- **§3:** Limits einhalten, „cache responsibly". Umsetzung s. §3.
- **§10:** API derzeit kostenlos.

## 3. Limits und Ernte-Verfahren

- **5 Requests/Minute** auf dem Query-Endpunkt je Key → der Client
  taktet auf **eine Anfrage je 13 s**.
- **1.000.000 Dokumente/Tag** je Account. Der Sync zählt konservativ
  mit: 1 je Turnier + 1 je Standing + 1 je publizierter Deckliste.
  Standard-Budget je Lauf: **950.000** (`--doc-budget`); wird es
  überschritten, stoppt der Lauf **vor** dem nächsten Teilfenster und
  zeichnet **PARTIAL** mit Fortschritt auf (fertige Fenster bleiben
  gespeichert; Conversion wird auf einem Teil-Korpus **nicht** neu
  berechnet — die Werte verbleiben beim letzten vollständigen
  Snapshot). Resume = denselben Zeitraum erneut laufen lassen oder per
  `--start/--end` gezielt ab dem fehlenden Fenster fortsetzen.
- Kalibrierung (live, 2026-11-12): eine reife Woche (1.–8. Okt. 2026)
  = 352 Turniere, 5.893 Standings, 2.074 Listen ≈ **8.319 Dokumente**,
  Antwort ≈ 22 MB → 12 Monate ≈ **430.000 Dokumente**, gut unter dem
  Tagesbudget. Aktuellste Tage haben deutlich weniger publizierte
  Listen (Listen werden erst nach Turnierende öffentlich).
- Fenster: Standard sind die **letzten 12 Kalendermonate**,
  Teilfenster von **7 Tagen** (`--window-days`), älteste zuerst, eine
  Anfrage je Teilfenster.
- Wiederholung desselben Fensters nutzt den aktuellen AVAILABLE-
  Snapshot (`cached`), außer mit `--force`.
- Fehler-Ehrlichkeit: 401/403/429 → **BLOCKED**-Snapshot, kein
  Retry-Sturm; nicht-JSON-Antwort → **PARTIAL**; Netzwerkfehler
  (inkl. abgebrochener Chunked-Übertragung beim Lesen des Bodys,
  `http.client.IncompleteRead` — live am 2026-11-12 an einem
  ~22-MB-Fenster beobachtet) → das betroffene Fenster wird **einmal**
  wiederholt (30 s Abstand); schlägt auch das fehl, schlägt der Lauf
  fehl (kein Snapshot), bereits gespeicherte Fenster bleiben
  bestehen.
- Die vollständigen API-Antworten werden **nicht** aufbewahrt
  (12 Monate ≈ 1 GB JSON). Der Snapshot speichert ein **Manifest**
  mit SHA-256 und Dokumentenzahl je Teilfenster; die geparsten
  Decklisten selbst sind der aufbewahrte Bestand.

## 4. Kohorten-Trennung (warum der Nenner 9.015 unverändert bleibt)

Turnier-Decks liegen in denselben Decklisten-Tabellen wie die
Archidekt-Ernte, aber strikt getrennt:

- `platform='topdeck'`, `bracket_level=NULL`,
  `bracket_source='topdeck_tournament'` — Turniere haben kein
  EDH-Bracket, und es wird keins erfunden.
- Die Universum-Auswahl (Inclusion + Tierlist-Verbreitung) filtert
  `platform IN (inclusion.platforms)` **und** `bracket_level IN
  (2,3,4)`. `topdeck` steht nicht in der Plattform-Allowlist der
  Einstellungen (`KNOWN_PLATFORMS = archidekt, moxfield`) und kann
  dort auch nicht eingetragen werden; ein NULL-Bracket erfüllt die
  Bracket-Bedingung ohnehin nie. Ein Regressionstest rechnet den
  kanonischen Nenner vor/nach einem TopDeck-Sync und verlangt
  Gleichheit (auf der echten DB-Kopie beim Erstlauf ebenfalls
  verifiziert: 9.015 vor und nach dem Sync).
- Die Evidenz-Tier-Formel (`tierlist/1.1.0`) liest diese Schicht
  nicht; Conversion/Win-Rate sind eine eigene, provenienzführende
  Auswertung und werden **nicht** in die Tier-Formel gemischt.

## 5. Gespeicherte Daten und Parser-Verhalten

- `decklist_deck`/`decklist_card`: je Standing mit publizierter Liste
  ein Deck (`deck_uid = topdeck:{TID}:{player_id}`, Fallback Hash aus
  TID/Name/Leader). Karten-Mapping per Name gegen den lokalen
  Scryfall-Bestand (Volle/Front-Flächen-Name), nicht aufgelöste Namen
  werden gezählt und benannt (wie bei der Archidekt-Ernte).
  Abschnitte werden wie geliefert gespeichert (Commanders, Mainboard,
  gelegentlich Stickers/Attractions — Letztere sind keine Karten des
  100er-Decks im Regelsinn, stehen aber so in der eingereichten
  Liste); `metadata` im `deckObj` ist kein Kartenabschnitt.
- `topdeck_result`: Spielername/-ID, Leader, `wins/draws/losses`
  (die von der Quelle publizierten Gesamtwerte inkl. Bracket-Spielen),
  `winsBracket/lossesBracket`, daraus abgeleitet `top_cut_reached`
  (1/0/NULL) und `deck_source` (`deckobj`|`text`). Der Spielername
  wird **nur anonymisiert gespeichert** (Owner-Regel #1108, keine
  echten Personennamen in Daten): `anonymize_player_names` in
  `topdeck.py` reduziert jeden Namen auf die Initialen-Form
  („J. D."; Ein-Token-Handles auf „X."; Team-/Clan-Klammer-Tokens
  zählen als Namensteil). Kollidieren zwei verschiedene Rohwerte auf
  dieselben Initialen, behält der in sortierter Reihenfolge erste
  die reine Form, die weiteren erhalten die Zusätze „ #2", „ #3"
  usw. — distinkte Werte bleiben distinkt, alle Zählungen und
  Gruppierungen exakt. Die pseudonyme `player_id` wird unverändert
  gespeichert. Der Abgleich gilt je Fetch-Fenster des Imports; die
  kanonische Abbildung über den Gesamtbestand rechnet der
  DB-Bereinigungsschritt mit derselben Funktion.
- `topdeck_tournament`: Turnier-Metadaten je Snapshot (Name,
  Startzeit, Swiss-Runden, `topCut`, Spieler, Listen, Dokumente).
- **Text-Fallback mit PARTIAL-Ehrlichkeit:** Steht kein `deckObj`
  zur Verfügung, wird die Textliste geparst (`deck_source='text'`,
  in der Lauf-Bilanz gesondert gezählt). Eigenheit der API (live
  verifiziert): Die Textliste enthält Zeilenumbrüche als **literale
  `\n`-Sequenzen**; der Parser normalisiert sie. Abschnitte sind
  `~~Name~~`-Kopfzeilen, Kartenzeilen `<Anzahl> <Name>`.
- Standings ohne publizierte Liste sind Ergebnis-Zeilen ohne Deck:
  Sie werden gezählt (`standings_without_list`), erzeugen aber kein
  Deck und gehen in keine Karten-Kennzahl ein. Team-Zeilen
  (Standing mit `players`-Array ohne eigene Liste) werden gesondert
  gezählt und übersprungen.
- Commander-Zuordnung: `leader` wird als `commander_name` geführt.
  Bei Partnern (`"A / B"`) bleibt `commander_oracle_id` **NULL** —
  ein Paar ist keine einzelne Karte; beide Partner stehen als
  `is_commander`-Zeilen in `decklist_card`. DFC-Leader liefert die
  API bereits als Vorderseite.

## 6. Conversion-Definition (selbst berechnet, nirgends publiziert)

Je Karte, über alle Decks **eines Sync-Fensters** (Präsenz im Deck;
Menge irrelevant; Commander-Einträge zählen wie jede Karte):

- **Top-Cut-Conversion** = Anteil der Decks mit dieser Karte, die den
  Top Cut erreicht haben — Nenner nur Decks in Turnieren **mit**
  Top Cut (`topCut > 0`) und **bekanntem** Bracket-Rekord.
  „Top Cut erreicht" heißt exakt: Der Spieler hat mindestens ein
  Ausscheidungs-Spiel bestritten, `winsBracket + lossesBracket > 0`.
  Die Reihenfolge des Standings-Arrays ist **keine** Endplatzierung
  und wird nie als solche benutzt (live geprüft: nicht nach
  Siegen/Rekord sortiert). Turniere ohne Top Cut und Decks mit
  unbekanntem Bracket-Rekord bleiben aus dem Nenner — nie still
  mitgezählt.
- **Win-Rate** = Σ `wins` / Σ (`wins`+`draws`+`losses`) über alle
  Decks mit dieser Karte, aus den publizierten Standing-Gesamtwerten
  (inkl. Bracket-Spielen — das ist der Rekord der Quelle und wird so
  beschriftet).
- **Mindest-Stichproben:** Conversion nur ab **10** Decks mit
  bekanntem Bracket-Rekord; Win-Rate nur ab **10** Decks und **30**
  Spielen. Darunter stehen die Zähler in `topdeck_card_stat`, die
  Rate bleibt **NULL** („Stichprobe zu klein" in der UI) — dieselbe
  Unbekannt-statt-erfunden-Regel wie in der Tierlist.
- Anzeige: Karten-Schublade, Abschnitt „Turnier (TopDeck)" direkt
  neben der EDHTop16-Play-Rate (die ihrerseits eine **publizierte**
  Größe bleibt — die beiden werden beschriftet unterschieden und nie
  vermischt).

## 7. Grenzen

- **cEDH-Korpus:** Nur Turniere der TopDeck-Plattform (überwiegend
  kompetitives EDH). Erwartbare Sammlungs-Abdeckung ist klein
  (Größenordnung der 49 EDHTop16-Karten); die Schicht sagt nichts
  über Casual-/Bracket-Spiel.
- Nicht jedes Standing hat eine öffentliche Liste (im jüngsten
  Tagesfenster nur ~10 %; in reifen Fenstern ~35 %) — die Abdeckung
  ist quellenbedingt und wird je Lauf ausgewiesen.
- Deckgrößen in der Quelle sind meist exakt 100, vereinzelt mehr
  (Sticker-/Attraction-Abschnitte); die Listen werden wie eingereicht
  übernommen, nicht „korrigiert".
- Test-Events existieren in der Quelle (u. a. mit Zukunfts-Daten);
  das Ernte-Fenster liegt strikt in der Vergangenheit, ein Filtern
  nach Namen findet nicht statt (keine erfundene Auswahlregel).
- Spielergebnisse sind Veranstalter-Eingaben (API-Doku/Terms:
  „as is") — die Schicht rechnet mit ihnen, validiert sie aber nicht
  gegen eine zweite Quelle.

## 8. Betrieb

```bash
# Standard: letzte 12 Monate, Wochenfenster (Erstlauf 2026-11-12
# auf DB-Kopie gefahren; Echt-DB folgt in Phase 4)
mtg-deckbuilder sync-topdeck

# gezieltes Fenster / Fortsetzung (unix-Sekunden; Beispiel)
mtg-deckbuilder sync-topdeck --start 1759000000 --end 1761600000

# engeres Budget / feinere Fenster
mtg-deckbuilder sync-topdeck --doc-budget 400000 --window-days 3
```

Voraussetzung ist ausschließlich der verbundene Connector
`custom.topdeck` (s. §1). Der Sync ist der einzige Schreibweg dieser
Schicht; Lesen über `card_topdeck()` (API `/api/external/card`) und
`topdeck_coverage()`.

## 9. Erstlauf 2026-11-12 (DB-Kopie) — gemessene Bilanz

Vollständiger Lauf über das Standard-Fenster, Snapshot
`snap-ab874246183a4407baef9e1d`, Status **AVAILABLE**:

- Fenster `2025-11-12/2026-11-12`, 53/53 Wochenfenster,
  **329.554 Dokumente** (Tagesbudget 1 Mio. inkl. aller Vorproben
  und des unten genannten Fehlversuchs eingehalten).
- **12.890 Turniere**, 224.914 Standings, **91.750 gespeicherte
  Decklisten** (davon 1 per Text-Fallback), 133.131 Standings ohne
  veröffentlichte Liste, 33 Team-Zeilen übersprungen, 0 Duplikate.
- Karten-Statistik: 21.823 Karten publiziert; global 7.345 Karten
  mit Conversion, 10.824 mit Win-Rate. Sammlungsabdeckung
  (`foundation-schwarze-box`, 1.324 Identitäten): **331 Karten mit
  Conversion, 462 mit Win-Rate**.
- **Handverifikation per unabhängigem SQL-Recount** aus
  `decklist_card` ⨝ `topdeck_result`: „Sol Ring" stimmt in allen
  Feldern überein (89.799 Decks, 75.158 Cut-bekannt, 20.247 im Top
  Cut, W/D/L 74.824/88.333/216.060, Conversion 0,2694, Win-Rate
  0,1973). „Mana Crypt" steht zu Recht in keiner Statistik: **0
  Decks** im Korpus (seit 2024-09-23 im Commander-Format gebannt;
  Fenster beginnt 2025-11).
- **Nenner-Invarianz live bestätigt:** kanonischer
  Inclusion-Nenner nach dem Sync = **9.015** (nur `archidekt`;
  B2 3.729 / B3 3.687 / B4 1.599) — wie vor dem Sync.
  `PRAGMA quick_check` = ok.
- **Fehlversuch vorher:** Der erste Anlauf starb nach 32.938 Decks
  (~20 Fenster) an einer abgebrochenen Chunked-Übertragung
  (`http.client.IncompleteRead` nach 10,7 von ~22 MB), die als
  nicht abgefangene Exception den Lauf beendete — kein Snapshot,
  gespeicherte Fenster blieben intakt. Fix in Commit `f6f068e`
  (HTTPException → transienter Fehler, ein Wiederholungsversuch je
  Fenster, 3 Regressions-Tests); der hier bilanzierte Lauf ist der
  vollständige Neulauf danach.
