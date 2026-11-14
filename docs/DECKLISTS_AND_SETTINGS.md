# Decklisten-Ernte (Archidekt) + Owner-Einstellungen + Inclusion-Engine

Stand: 2026-11-12. Sammlungs-Universum dieser Arbeit: ausschließlich
`MTG_Kartensammlung.xlsx` (v2) — 1.324 Identitäten / 1.815 Exemplare /
63 eligible Commander; Standorte Schwarze Box 1.153, Foundation 285,
Alen Lorwyn Box 377. (Die korrigierte 1.655er-Datei gehört zu
commander-playtest-lab und wurde hier nicht verwendet.)

## Teil A — Woher echte Decklisten kommen (und woher nicht)

### EDHREC: nur Metadaten, keine Listen (Beleg)

`edhrec_deck_entry` enthält 39.891 Zeilen (Brackets: core 14.071,
upgraded 11.744, optimized 4.252, dazu 9.824 aus einer Basis-Ansicht
ohne Bracket). Die Metadaten-Erfassung ist vollständig: bei allen 192
Bracket-Snapshots (64 Commander × 3) gilt `captured == displayed_total`.
Jeder Eintrag trägt ausschließlich: `urlhash` (22 Zeichen, base64url),
savedate, price, salt, tags, Typenzahlen. **Kein Plattformname, keine
Deck-URL.** Der einzige Listen-Link wäre EDHRECs eigenes
`/deckpreview/{urlhash}` — `edhrec.com/robots.txt` verbietet
`/deckpreview/` ausdrücklich. `json.edhrec.com` antwortet 403
(AccessDenied). Folge: EDHREC-Einträge sind nicht zu ihren Quell-Decks
auflösbar; sie bleiben Zähl-/Metadatenbasis (siehe Inclusion-Quelle
`edhrec`).

### Moxfield: BLOCKED (Beleg, nicht umgangen)

`api2.moxfield.com/robots.txt` = `Disallow: /` für alle. Zusätzlich
lösen EDHREC-urlhashes auf moxfield.com nicht auf (404 in 2 Proben).
Moxfield liefert keine Daten und wird als Plattform nur als „bekannt,
aber BLOCKED/datenlos" im Einstellungs-Katalog geführt.

### Archidekt: öffentliche API funktioniert (Beleg per Probe)

- Suche: `GET https://archidekt.com/api/decks/v3/?commanderName={name}
  &deckFormat=3&edhBracket={n}&page={p}` — 60 Zeilen/Seite, `count` =
  gelistete öffentliche Decks der Kohorte, Zeilen tragen `edhBracket`
  (Filter wirkt; Probe Referenz-Commander Bracket 3: count=267).
- Detail: `GET https://archidekt.com/api/decks/{id}/` (Trailing Slash
  nötig) — volle Kartenliste. `card.oracleCard.uid` ist die
  Scryfall-oracle_id (Mapping per ID, nicht per Namensraten).
  Kategorien mit `includedInDeck` definieren das Deck (Maybeboard
  ausgeschlossen); Kategorie `Commander` markiert den/die Commander.

**Kohorten-Ehrlichkeit:** Das Bracket eines geernteten Decks ist
Archidekts `edhBracket` (dieselbe offizielle Skala 1–5 mit denselben
Level-Namen wie EDHRECs Kohorten), gespeichert als
`bracket_source='archidekt_edhBracket'`. Es wird nie behauptet, dies
sei EDHRECs internes Deck-Set; EDHRECs eigenes Set bleibt über
`edhrec_deck_entry` und die Stats-Snapshots separat sichtbar.

## Ernte-Ergebnis (Echtlauf 2026-11-12, Kappe 300 je Kohorte)

| Größe | Wert |
|---|---|
| Commander (eligible, v2) | 63 |
| Kohorten (63 × Brackets 2/3/4) | 189 |
| Listings gespeichert | 178 (11 Kohorten sind leer, s. u.) |
| Summe `listed_count` (Archidekt-Zählung) | 10.603 |
| Ziel-Decks (Σ min(listed, 300)) | 9.244 |
| **Decks AVAILABLE gespeichert** | **9.211** |
| davon Bracket 2 / 3 / 4 | 3.854 / 3.742 / 1.615 |
| Fehlgeschlagen (NOT_FOUND/BLOCKED/PARTIAL-Endstand) | 0 |
| Karten-Einträge gesamt | 785.850 |
| davon auf oracle_id gemappt | 785.744 (99,99 %) |
| ungemappt (gezählt + benannt, nie still verworfen) | 106 |
| Roh-JSON-Dateien (gzip, im privaten Datenordner) | 9.789 Dateien, 419 MB |

**Differenz 9.244 − 9.211 = 33:** exakt die Summe der Fehlbeträge in
27 Kohorten (je 1–4 Decks, größter: Ramos Bracket 3 mit 298/300).
Ursache: 33 Decks sind unter zwei Kohorten gelistet (z. B.
Partner-Commander) und werden — Schlüssel ist die Plattform-Deck-ID —
einmal gespeichert (unter der zuletzt synchronisierten Kohorte).
Der Nenner einer Inclusion-Rechnung ist damit je Kohorte um
höchstens 4 kleiner als die Listungs-Kappe; die Definition am Wert
weist den tatsächlichen Nenner aus.

**Inhaltsdedupe bei Inclusion (seit Upstream-Abgleich 2026-11-12,
Anlass: Review-Fix in upstream-PR #1207):** Gleiche Liste unter
zwei Deck-IDs zählt einmal. Der Inclusion-Nenner ist die Zahl der
kanonischen Decks je Selektion (ein Deck je Inhalts-Fingerabdruck
— gespeicherte Kartenzeilen inkl. Commander-Zeile; niedrigste
Deck-ID gewinnt); die Definition weist den Nenner zusätzlich je
Plattform und je Bracket aus (`denominator_by_platform`,
`denominator_by_bracket`) und meldet, wie viele Deck-IDs als
inhaltsgleiche Duplikate herausfielen. Messung auf der echten
Ernte (Stand 2026-11-12): 9.211 AVAILABLE-Decks enthalten 163
inhaltsgleiche Mehrfach-IDs (47 Fingerabdrücke, größte Gruppe 55
Kopien einer Liste; 21 Gruppen über Bracket-Grenzen hinweg) —
kanonischer Gesamt-Nenner 9.048. Beispiel Tatyova Bracket 3:
281 → 278. Kartenzeilen mit Menge ≤ 0 zählen nie (Parser
erzwingt bereits ≥ 1; die Zählabfrage prüft es zusätzlich).

**Leere Kohorten (11, in der DB ohne Listing-Zeile, weil
`listed_count = 0`):** Hapatra B4; Myojin B2, B4; Saheeli, Consul of
Oversight B4; Teyo, Diamondblade Mage B3; Teyo, Lightshield Expert B4;
Venom B4; Vulture B3, B4; Winter B4; Yargle B3.

**Ungemappte Karten (Top):** Copy (8), Beast (6), Angel (5),
Elf Warrior (4), Ape (4), Plant (3), Goblin (3), Clue (3) — überwiegend
Token-/Emblem-Einträge aus Archidekt-Listen ohne Scryfall-oracle_id;
sie stehen mit Namen in `decklist_card` (oracle_id NULL) und in
`decklist_deck.unmapped_names_json`.

**Lauf-Historie (ehrlich):** Die Ernte brauchte mehrere Läufe über
~5,5 h: VM-Neustart (1.758 Decks), Storage-EPERM-Crash (3.337),
SQLite-„disk I/O error" (3.436), Lock-Contention-Phase und
Prozess-Kills durch die Umgebung. Alle Zwischenstände waren per
Resume-Pfad verlustfrei fortsetzbar; der Schlusslauf meldete
4.783 fetched / 4.463 cached / 0 Fehler. Die dabei gefundenen
Fehlerklassen sind als Fixes + Tests im Code (siehe Git-Historie
`muse/decklists-settings-1`: Parser-Versions-Resume, atomares
Settings-PUT, Per-Deck-Isolation, Raw-Save-Degradierung,
Kohorten-Retry bei Storage-/Fetch-Fehlern, Lock ≠ Deck-Fehler,
IncompleteRead-Retry im Fetcher).

Provenienz je Deck (`decklist_deck`): Plattform, Plattform-Deck-ID,
Commander (oracle_id + Name), Bracket + `bracket_source`, Source-URL,
Status, Parser-Version `archidekt-deck/1.0.0`, SHA-256 + Pfad des
Roh-JSON, Abrufzeit, Deckgröße, Mapping-Zähler, ungemappte Namen.

## Gezielte Nachernte dünner/leerer Kohorten (Targeted-Modus)

`sync-decklists --targeted` listet NUR die Kohorten erneut, deren
**kanonische** Deckzahl (Inhalts-Dedupe wie in der
kanonischen Selektion, `decklists.canonical_cohort_counts`) unter
`--min-canonical` (Default 30) liegt — die leeren Kohorten sind der
Kopf dieser Liste, kein Sonderfall. `--cohorts-file` nimmt stattdessen
eine explizite Liste `[{"commander": oracle_id|Name, "bracket": n}]`.
Volle Kohorten werden nicht einmal gelistet (kein Request). Bereits
gespeicherte Decks einer Ziel-Kohorte bleiben per Resume-Regel
gecached; nur neue Decks werden geholt. Neue Decks tragen das
`updatedAt` ihres Listings als `source_updated_at`; die NULL-Zeitstempel
des Bestands werden NIE rückwirkend gefüllt (damit bleibt der
Zeitraum-Ausschluss des Bestands ehrlich, siehe Teil B).

**Kopie-Lauf 2026-11-12** (DB-Kopie, echte DB unberührt;
Ausgangslage 9.211 Decks, kanonisch je Kohorte summiert 9.027 —
12 Inhalts-Dubletten existieren kohortenübergreifend und zählen je
Kohorte einmal, im gepoolten Nenner global nur einmal: 9.015):

- Ziel-Kohorten (< 30 kanonisch): **126 von 189**, davon 11 leer.
- Alle 126 erneut gelistet: **889 Listenzeilen, 888 cached,
  1 neu geholt, 0 Fehler**; jede Kohorte `listing_status=AVAILABLE`.
- Einziges neues Deck: `archidekt:28313791` (Gideon the Oathless,
  Bracket 2; Kohorte 8 → 9 kanonisch; `source_updated_at` =
  `2026-11-12T04:38:10.612464Z` aus dem Listing; es ist das einzige
  Deck der Kopie mit gesetztem `source_updated_at` — kein Backfill).
- **Keine Kohorte erreicht durch die Nachernte die 30er-Schwelle**
  (0 Übergänge). Die dünnen Kohorten sind auf der Plattform selbst
  dünn: die frischen Listings decken sich fast exakt mit dem Bestand
  (größtes Listing: 29 Zeilen, Prowler B2 — davon 1 Inhalts-Dublette,
  kanonisch 28).
- **Alle 11 leeren Kohorten bleiben leer** — Quellenbefund: Archidekt
  meldet für diese (Commander, Bracket)-Abfragen aktuell `count=0`
  (frisches Listing `listed_count=0`, Status AVAILABLE; per
  Direktabfrage gegengeprüft für Myojin of Night's Reach B2 und
  Vulture, Scheming Scavenger B4: je `count=0`; Gideon B2 als
  Positiv-Kontrolle: `count=9`). Es sind exakt die 11 aus dem
  Ernte-Ergebnis oben: Hapatra B4; Myojin B2+B4; Saheeli, Consul of
  Oversight B4; Teyo, Diamondblade Mage B3; Teyo, Lightshield Expert
  B4; Venom B4; Vulture B3+B4; Winter, Tormented Loner B4; Yargle,
  Goliath of Otaria B3. Für diese Kohorten existiert folglich auch
  keine kanonischen Decks.

**Verbreitungs-Neurechnung auf derselben Kopie** (`compute-tiers`,
tierlist/1.1.0, nach der Nachernte): 242 Universum-Profile =
1 `all` (Nenner 9.016 = 9.015 + 1 neues Deck) + 63 Commander-Profile
+ **178 Kohorten-Profile**; Universe-Zeilen 589.106 (vorher 203.696).
Von den 178 Kohorten haben **63 einen Nenner ≥ 30** (echte Stufen
S–D) und **115 einen Nenner < 30** (alle Zeilen U/„unbekannt",
Anteil als Score mitgeführt). Alle 178 Kohorten-Nenner stimmen exakt
mit der unabhängigen Vorab-Zählung (`canonical_cohort_counts`,
+1 Gideon-Deck) überein — 0 Abweichungen. Die globale
Evidenz-Verteilung ist unverändert (S5/A28/B109/C134/D1.048/U1).
Handrechnung (unabhängiges Skript, nur Rohzeilen): Maralen B3
(Nenner 298): Forest 280 Treffer → S, Sol Ring 241 → S; Ramos B2
(Nenner 300): Forest 261 → S, Sol Ring 219 → S; Gideon B2 (Nenner 9):
Swamp 7 → U, Sol Ring 5 → U — alle 6 Werte exakt wie gespeichert.

## Teil A2 — Browser-Sammlung: volle EDHREC-/Moxfield-Listen (Importer)

EDHREC-Deckpreview und Moxfield sind für Crawler/API gesperrt (Teil
A) — die **einzige** verbleibende Route zu ihren VOLLEN Listen ist
die Browser-Sammlung des Owners: Das Sammel-Tool
(`browser_deck_harvest.py`, im Repo unter `tools/browser-harvest/`
inkl. Parser-Tests und `Start-Sammeln.bat`) fährt die eigene, angemeldete
Chromium-Sitzung des Owners über die Seiten und schreibt je Deck
einen JSONL-Record (`decklists_browser.jsonl`) mit Quelle,
Source-URL, Erntezeit, Parser-Version, Deckname, Kartenliste
(Name/Menge/Sektion), Status und Notiz.

Import: `mtg-deckbuilder import-browser-decklists <datei.jsonl>`
(Importer `browser-import/1.0.0`, Modul `browserimport.py`). Die
Records landen in denselben Tabellen wie die Archidekt-Ernte, mit
derselben Provenienz-Disziplin (Source-URL, Erntezeit als
`fetched_at`, Parser-Version des Records, SHA-256 + gz-Roh-Record
unter `snapshots/browser-<quelle>/`, Mapping-Zähler, ungemappte
Namen ausgewiesen; die Datei selbst wird als Quelle in der
`source`-Tabelle registriert). Es gelten die Regeln:

- **Nur `AVAILABLE`-Records werden importiert.** PARTIAL/BLOCKED
  werden gezählt und im Import-Report ausgewiesen, nie abgelegt.
- **Plattform ehrlich getrennt:** `browser:edhrec` /
  `browser:moxfield` (aus dem `source`-Feld des Records) — nie als
  API-Plattform getarnt. Beide stehen in der Plattform-Auswahl der
  Einstellungen (`inclusion.platforms`).
- **Kein Bracket — Kohorten-Ehrlichkeit:** Ein Browser-Record kennt
  kein Bracket; gespeichert wird `bracket_level` NULL /
  `bracket_source` NULL, nichts wird erfunden. Die
  kanonische Selektion (Inclusion + Decklisten-Status) lässt bracket-lose
  Decks **nur über ihre Plattform** zu — als bracket-lose Kohorte
  dieser Plattform; in der Nenner-Zerlegung erscheinen sie unter dem
  ausdrücklichen Schlüssel `none` (nur in
  `denominator_by_platform`). Decks MIT Bracket werden exakt wie
  bisher gefiltert — die Bracket-Nenner der Archidekt-Universen
  bleiben unverändert (Regressionstest: kanonischer Nenner der
  echten DB bleibt 9.015). Bei gesetztem Zeitraum zählen
  Browser-Decks nicht mit (sie haben keinen Quell-Zeitstempel;
  `source_updated_at` bleibt NULL und wird nie erfunden) und werden
  wie alle Decks ohne Zeitstempel gezählt ausgeschlossen.
- **Commander** kommt aus der Commander-Sektion des Records
  (`Commander`/`commanders`). Partner-Decks (zwei Commander)
  behalten beide Namen (`A + B`) und `commander_oracle_id` NULL —
  keine falsche Einzel-Zuordnung. Ohne Commander-Sektion bleiben
  beide Felder leer (Detail-Vermerk).
- **Sideboard/Maybeboard** sind keine Deckliste und werden
  ausgeschlossen (gezählt, im Deck-Detail und Report ausgewiesen) —
  wie die Archidekt-Ernte Nicht-Deck-Kategorien auslässt.
- **Namensauflösung** wie bei der Archidekt-Ernte (exakter
  Scryfall-Name, sonst eindeutiger Front-Name); unauflösbare Namen
  bleiben als `name:<Name>`-Zeilen mit Zähler + Namensliste ehrlich
  im Deck, statt still zu verschwinden.
- **Dedupe** läuft über die bestehende Inhalts-Kanonik der
  Zähl-Schicht (gleiche Kartenliste = einmal zählen, niedrigste
  Deck-ID gewinnt) — inhaltsgleiche Browser-Listen zählen also
  nicht doppelt neben ihren Archidekt-Zwillingen. Der Import-Report
  zählt sie aus (`duplicates_of_existing` /
  `duplicates_within_file`).
- **Grenzen:** Was die Seite nicht gerendert hat, steht nicht im
  Record — der Import erfindet nichts nach. Ein fehlgeschlagener
  Roh-Save degradiert das Deck auf PARTIAL (wie bei Archidekt) und
  hält es aus jeder kanonischen Selektion, bis ein Re-Import den Roh-Record
  sichert. Re-Import derselben Datei ersetzt die Decks in-place
  (idempotent).

## Teil B — Einstellungen (Store-Tabelle `app_setting`, versioniert)

| Schlüssel | Typ | Default | Wirkung |
|---|---|---|---|
| `inclusion.source` | `edhrec`\|`decklists`\|`own_decks`\|`combined` | `edhrec` | Datenbasis der Inclusion-Werte |
| `inclusion.brackets` | Teilmenge von 1..5 | `[2, 3, 4]` | Kohorten, die einfließen |
| `inclusion.platforms` | Liste | `["archidekt"]` | Plattformen der Decklisten (`moxfield` bekannt, BLOCKED/datenlos; `browser:edhrec`/`browser:moxfield` = Browser-Sammlung, bracket-los, s. Teil A2) |
| `inclusion.min_decks` | int ≥ 0 | `10` | Mindest-Nenner; darunter „ungenügende Daten" (Wert bleibt sichtbar) |
| `inclusion.max_age_days` | int > 0 oder null | `null` | maximales Alter (Abrufzeit) einfließender Decks/Snapshots |

Defaults bilden das bisherige Verhalten ab (EDHREC-Statistik).
Validierung ist strikt: unbekannte Schlüssel/Werte werden abgelehnt
(400/Fehler), nie still gespeichert. PUT /api/settings ist atomar
(erst alles validieren, dann anwenden). Overrides per Request/j
...[truncated]