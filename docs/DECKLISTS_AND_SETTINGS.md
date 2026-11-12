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
  (Filter wirkt; Probe Chulane Bracket 3: count=267).
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
kanonischen Decks je Universum (ein Deck je Inhalts-Fingerabdruck
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

## Teil B — Einstellungen (Store-Tabelle `app_setting`, versioniert)

| Schlüssel | Typ | Default | Wirkung |
|---|---|---|---|
| `inclusion.source` | `edhrec`\|`decklists`\|`own_decks`\|`combined` | `edhrec` | Datenbasis der Inclusion-Werte |
| `inclusion.brackets` | Teilmenge von 1..5 | `[2, 3, 4]` | Kohorten, die einfließen |
| `inclusion.platforms` | Liste | `["archidekt"]` | Plattformen der Decklisten (`moxfield` bekannt, BLOCKED/datenlos) |
| `inclusion.min_decks` | int ≥ 0 | `10` | Mindest-Nenner; darunter „ungenügende Daten" (Wert bleibt sichtbar) |
| `inclusion.max_age_days` | int > 0 oder null | `null` | maximales Alter (Abrufzeit) einfließender Decks/Snapshots |

Defaults bilden das bisherige Verhalten ab (EDHREC-Statistik).
Validierung ist strikt: unbekannte Schlüssel/Werte werden abgelehnt
(400/Fehler), nie still gespeichert. PUT /api/settings ist atomar
(erst alles validieren, dann anwenden). Overrides per Request/j
...[truncated]