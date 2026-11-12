# Karten-Kategorien: Funktionen, Typen, Subtypen

Stand: 2026-11-12 · Lane `muse/categories-1` · alle Zahlen: Lauf auf einer
**Kopie** des echten Datenordners (Sammlung `foundation-schwarze-box`,
1.324 Oracle-Identitäten); die echte DB wurde nicht beschrieben.

Moritz' Anforderung: Karten müssen erstklassig nach (1) Funktionen/
Kategorien (Ramp, Removal, …), (2) Kartentypen (Creature, Instant, …)
und (3) Subtypen (Vampire, Human, …) erfasst sein — vollständig für die
ganze Sammlung — und danach muss sortierbar/filterbar sein.

## Schichten (streng getrennt, Herkunft je Claim)

| Ebene | Herkunft (`origin`) | Quelle | Art |
|---|---|---|---|
| Typ-Fakten | — (Fakten, keine Claims) | lokaler Scryfall-Bulk, Parser `type-parser/1.0.0` | deterministisch abgeleitet |
| Funktionen, Basis | `ORACLE_TEXT_HEURISTIC` | Oracle-Text aller Faces, Regelwerk `oracle-heuristic/2.0.0` | Heuristik — Suchhilfe, keine Beobachtung |
| Funktionen, Schätzung | `STRUCTURAL_PROFILE` | importierte Strukturprofile (commander-playtest-lab) | Modellschätzung, keine Beobachtung |
| Funktionen, extern | `SCRYFALL_TAGGER_SEARCH` | offizielle Scryfall-Search-API, `function:<tag>`, Sync `scryfall-tagger-search/1.0.0` | Community-Tags (Tagger), als Snapshots mit Hash/Zeitpunkt abgelegt |

Jede Schicht führt eine **Geprüft-Buchführung** (`card_category_check`):
Pro Karte und Schicht ist verzeichnet, dass sie geprüft wurde — auch mit
dem Ergebnis „keine Kategorie" (`claims = 0`). Eine Karte ohne Claims ist
damit von einer nie geprüften Karte unterscheidbar. Für die Profil-Schicht
existiert keine Vollprüfung (sie ist ein Import über 195 Profile); dort
bleibt `checked` ehrlich 0, nur `with_claims` zählt.

Jeder Ableitungs-/Sync-Lauf schreibt einen `category_run`-Eintrag
(Schicht, Version, Quelle, Status, Abdeckung). Statusmodell wie überall
im Projekt: `NOT_FETCHED / PARTIAL / BLOCKED / AVAILABLE / NOT_FOUND`.

## Ebene Typen (Ziel 100 %)

`mtg-deckbuilder derive-card-types` liest denselben lokalen Bulk-Katalog,
aus dem der Scryfall-Store importiert wurde (erste Druckversion je
`oracle_id` gewinnt — dieselbe Konvention wie `import_scryfall`), und
schreibt:

- `card_face(oracle_id, face_index, face_name, type_line, oracle_text, mana_cost, source_id, parser_version)` — eine Zeile je Kartenfläche. DFCs (transform/modal_dfc), Split-, Adventure-, Flip-, Leveler- und Prepare-Karten bekommen alle Faces getrennt; nur so sind z. B. die Subtypen der Rückseite auffindbar.
- `card_type_component(oracle_id, face_index, kind, value, position)` — `kind ∈ {supertype, type, subtype}`, `position` = Druckreihenfolge. Der Parser (`typeline.py`) ist verlustfrei: Ein Token links vom Gedankenstrich, das weder bekannter Supertyp noch bekannter Kartentyp ist, wird als Typ gespeichert statt verworfen.
- `card_keyword(oracle_id, keyword, source_id)` — die Keywords exakt wie Scryfall sie führt (Fähigkeiten/Aktionen, z. B. Flying, Partner, Cascade). Keywords existieren nur, wo Scryfall sie listet — das ist ein Fakt, keine Lücke.

Ohne Bulk-Datei (Fallback) werden die Faces aus den gespeicherten
`scryfall_card`-Spalten rekonstruiert; dann fehlen Back-Face-Texte und
alle Keywords, und der Lauf wird ehrlich als `PARTIAL` verbucht.

## Ebene Funktionen — Taxonomie

Definitionen (Kurzform; das versionierte Regex-Regelwerk in `roles.py`
ist die ausführbare Fassung). „Tagger-Tag" = Label der externen Schicht.

| Kategorie | Label DE | Definition | Tagger-Tag |
|---|---|---|---|
| ramp | Ramp | Erzeugt Mana oder beschleunigt die Manaentwicklung über das normale Land-pro-Turn hinaus | ramp |
| mana_rock | Mana Rock | Artefakt, das Mana erzeugt | mana-rock |
| mana_dork | Mana Dork | Kreatur, die Mana erzeugt | mana-dork |
| land_ramp | Land-Ramp | Sucht Länder aus der Bibliothek ins Spiel (oder auf die Hand) | land-ramp |
| card_draw | Kartenzug | Zieht Karten (inkl. Investigate) | draw |
| card_advantage | Kartenvorteil | Zieht mehrere Karten / kartenanzahlabhängig | card-advantage |
| cantrip | Cantrip | Billiger (MV ≤ 2) Instant/Sorcery, der eine Karte zieht | cantrip |
| tutor | Tutor | Sucht eine (Nicht-Land-)Karte aus der Bibliothek | tutor |
| removal | Removal | Entfernt gezielt ein Permanent/Spell-relevantes Ziel (Destroy/Exile/−X/−X/Schaden/Fight/Edikt) | removal |
| board_wipe | Board Wipe | Entfernt massenhaft Permanents (Destroy/Exile all, −X/−X für alle, Mass-Bounce, „each player sacrifices") | board-wipe |
| counterspell | Counterspell | Neutralisiert einen Spruch/eine Fähigkeit auf dem Stack | counterspell |
| bounce | Bounce | Schickt ein Ziel auf die Hand seines Besitzers zurück | bounce |
| flicker | Flicker | Exiliert ein Permanent und bringt es (sofort/verzögert) zurück | flicker |
| recursion | Reanimation/Rückholung | Bringt Karten aus einem Friedhof zurück (Hand/Spiel) | recursion |
| protection | Schutz | Hexproof/Shroud/Indestructible/Protection, Schadensverhinderung, Phase-out | protection |
| graveyard_hate | Friedhof-Hate | Exiliert Karten aus Friedhöfen / ganze Friedhöfe | graveyard-hate |
| lifegain | Lebensgewinn | Lebenspunkte gewinnen, Lifelink verleihen | lifegain |
| sacrifice_outlet | Sacrifice Outlet | Freie/kostengünstige Opfer-Fähigkeit (Opfer als Kosten vor dem Doppelpunkt) | sacrifice-outlet |
| stax | Stax | Verteuert/verbietet gegnerische Aktionen, verhindert Untap | stax (404, s. u.) |
| anthem | Anthem/Buff | „Kreaturen, die du kontrollierst, erhalten +X/+X" | anthem |
| mill | Mill | Bibliothekskarten in den Friedhof legen (Mill-Aktion) | mill |
| discard | Abwurf (Gegner) | Gegner/Mitspieler werfen Karten ab | discard |
| card_selection | Kartenauswahl | Scry/Surveil/Loot (ziehen+abwerfen), Top-of-Library-Auswahl | card-selection (404) |
| token_production | Token-Erzeugung | Erzeugt Spielsteine (inkl. Investigate/Populate) | token (404) |

Profil-Rollen außerhalb dieser Taxonomie (z. B. `engine`, `finisher`)
bleiben verbatim unter ihrer Herkunft sichtbar — sie werden nicht in
die Taxonomie hineingedeutet.

### Heuristik-Regelwerk v2 (`roles.py`)

- Klassifikation über **alle Faces** (v1 nutzte nur die Vorderseite).
- Tutor segmentweise (Satzzellen): Land-Suchen sind Land-Ramp, kein
  Tutor; eine Karte, die in getrennten Sätzen Land und Nicht-Land
  sucht, erhält beides.
- Opfer-Outlet nur bei Opfer-**Kosten** (Doppelpunkt), nicht bei
  „als zusätzliche Kosten opfern" ohne Doppelpunkt.
- Counterspell auch für „counter target noncreature/instant or sorcery
  spell" (v1 verpasste diese Formen).
- Flicker satzübergreifend (Exile-Satz + Return-Satz), aber nur mit
  Rückkehr desselben Objekts („it/that card/them").
- Treasure-Erzeugung zählt als Ramp; Investigate als Kartenzug und
  Token-Erzeugung.

### Tagger-Schicht (offizieller Weg — trägt)

Der Scryfall Tagger selbst hat **keinen** offiziellen Export (nur eine
undokumentierte GraphQL-Schnittstelle — weiterhin nicht genutzt). Der
unterstützte Weg ist die dokumentierte Search-API mit dem
`function:`-Operator; deren Ergebnismengen **sind** die funktionalen
Tagger-Tags. Live-Probe am 2026-11-12 (erste Seite je Tag,
`unique=cards`): ramp 2.353, mana-rock 390, mana-dork 451, land-ramp
638, draw 4.337, card-advantage 6.336, cantrip 659, tutor 1.177,
removal 6.490, board-wipe 952, counterspell 553, bounce 944, flicker
204, recursion 2.283, protection 1.230, graveyard-hate 433, lifegain
2.640, sacrifice-outlet 1.502, anthem 545, mill 1.326, discard 592.

- **404-Tags** (existieren nicht oder sind leer — per API nicht
  unterscheidbar, Status `NOT_FOUND`): `stax`, `token`,
  `card-selection`. Diese Kategorien haben ehrlich **keine** externe
  Schicht; Heuristik/Profil bleiben ihre einzigen Quellen.
- **Aliase, bewusst nicht separat gesynct:** `mass-removal` und
  `sweeper` liefern dieselbe Menge wie `board-wipe` (je 952), `blink`
  dieselbe wie `flicker` (204), `spot-removal` (5.438) ist eine
  Teilmenge von `removal`. Ein Primär-Tag je Kategorie, keine
  stillschweigende Vermischung.
- robots.txt von api.scryfall.com erlaubt `/cards/search` (disallow
  nur `/admin*` + Fehlerseiten); der Client prüft sie trotzdem bei
  jedem Lauf. ≥ 100 ms Abstand (Scryfall-Empfehlung 50–100 ms),
  Backoff bei 429/5xx inkl. Retry-After, ehrlicher User-Agent +
  `Accept`-Header (ohne Accept antwortet die API 400).
- Je Tag ein Snapshot in `external_snapshot` (Rohseiten gzip, SHA-256,
  Parser-Version, `displayed_total` = API-Gesamtzahl,
  `captured_count` = Treffer im lokalen Store). Globale Ergebnisse
  enthalten Karten, die der lokale Bulk-Stand noch nicht kennt; diese
  werden gezählt (`outside_store` im Snapshot-Detail), nicht zu Claims.
- Claims je Tag werden nur bei vollständigem Lauf (`AVAILABLE`)
  ersetzt; ein `PARTIAL`-Lauf (Seitenfehler, `--max-pages`) lässt
  bestehende Claims unangetastet. Snapshots werden **vor** den Claims
  geschrieben (Absturz ⇒ Snapshot ohne Claims, nie Claims ohne
  Provenienz). Ohne `--force` übernimmt ein Lauf aktuelle Snapshots
  (AVAILABLE/NOT_FOUND) statt sie neu zu laden — der Sync ist so
  jederzeit fortsetzbar. Erst ein vollständiger, sauberer
  Vokabular-Lauf schreibt die Geprüft-Zeilen der Tagger-Schicht.

## Sortieren / Filtern

- `GET /api/cards` — neue Parameter: `type`, `subtype`, `keyword`
  (any-face: ein Treffer auf **irgendeiner** Fläche genügt),
  `category` + `category_origin` (Schicht wählbar), `sort=name|type|mana_value`.
  Jede Karte trägt `type_info` (Faces mit Supertypen/Typen/Subtypen,
  Karten-Unionen, Keywords).
- `GET /api/pool` — dieselben Filter (Rolle heißt weiter `role`,
  zusätzlich `category_origin`), Pool-Karten tragen `type_info`.
- `GET /api/categories` — Taxonomie + Labels, Abdeckung je Schicht
  (geprüft / mit Claims / geprüft-ohne-Kategorie), Zähler je Kategorie
  und Herkunft, Tagger-Status je Tag, Facetten (Typen/Subtypen/Keywords
  mit Karten-Zählern) für die UI-Auswahl.
- `POST /api/decks/validate` — zusätzlich `role_groups`: Deckliste
  gruppiert nach Primär-Kategorie (erste Kategorie in
  Taxonomie-Reihenfolge; `none` für kategorie-lose Karten).
- UI (Sammlung): Filterleiste Typ/Subtyp/Keyword/Funktion/Herkunft +
  Sortier-Auswahl; Karten zeigen Typ-/Subtyp-/Keyword-Badges.
  Deckbuilder: Pool zusätzlich nach Subtyp/Typ filterbar; die
  Entwurfsliste wird nach Primär-Kategorie gruppiert angezeigt.
- CLI: `derive-card-types [--bulk …]`, `rebuild-roles`,
  `sync-tagger [--tag …] [--max-pages N] [--force]`,
  `category-report [--collection …]`; der Datenbericht
  (`data-report`) enthält eine `categories`-Sektion (counts-only).

## Abdeckung (Datenkopie, Sammlung mit 1.324 Identitäten)

- **Typen: 1.324/1.324 (100 %)** mit Faces und Typ-Komponenten;
  622/1.324 Karten führen mindestens ein Keyword.
  Store-weit: 35.769/35.769, Lauf-Status AVAILABLE.
- **Heuristik: 1.324/1.324 geprüft**, davon 699 mit ≥ 1 Claim (52,8 %),
  625 geprüft-ohne-Kategorie. (Alter Stand zum Vergleich: v1-Heuristik
  nur Vorderseite, 390/1.078 = 36 % mit Rollen, ohne Geprüft-Nachweis.)
- **Strukturprofile: 44/1.324 mit Claims** (Import-Umfang, keine
  Vollprüfung — unverändert übernommen).
- **Tagger: 1.324/1.324 geprüft**, davon 797 mit ≥ 1 Claim (60,2 %),
  527 geprüft-ohne-Kategorie. 21 von 24 Tags `AVAILABLE`
  (36.030 Claims auf 20.736 Store-Karten), `stax`/`token`/
  `card-selection` ehrlich `NOT_FOUND`. Lauf-Status AVAILABLE.
  Größte Sammlungs-Kategorien extern: removal 275, card_advantage 199,
  card_draw 143, lifegain 132. Quercheck Heuristik↔Tagger:
  counterspell deckungsgleich 20/20 Karten in der Sammlung;
  removal Heuristik 129 ⊂ konservativ gegenüber Tagger 275.
- **Vereinigung aller Schichten: 887/1.324 Karten (67,0 %) tragen
  mindestens eine Funktions-Kategorie**; 437 Karten sind von Heuristik
  und Tagger geprüft und tragen in keiner Schicht eine Kategorie
  (überwiegend Länder und Vanilla-Kreaturen — als solche ausgewiesen,
  nicht still fehlend). Facetten der Sammlung: 8 Typen, 158 Subtypen,
  99 Keywords.

Stichproben (alle auf der Kopie geprüft, Ergebnis OK):
Sol Ring → Typ Artifact, Rollen mana_rock+ramp (Heuristik + Tagger,
ramp zusätzlich Profil) · Swords to Plowshares → Instant, gezieltes
Removal (alle drei Schichten) · Wrath of God → Sorcery, Board Wipe
(Heuristik + Tagger) · Counterspell → Counterspell (Heuristik +
Tagger) · eine Vampire-Kreatur der Sammlung → Subtyp Vampire, Keyword
Flying · DFC „Grizzled Outcasts // Krallenhorde Wantons" → Face 0
Human+Werewolf, Face 1 nur Werewolf (Face-Trennung exakt, Human nicht
auf der Rückseite).

## Offene Grenzen

- Keywords sind nur so vollständig wie Scryfalls Feld je Karte; ein
  Keyword auf genau einer Druckversion kann an der kanonischen
  Erst-Druckversion fehlen (gleiche Konvention wie der Store-Import).
- Die Heuristik bleibt eine Heuristik: Sie darf falsch-negative
  Treffer haben; falsch-positive werden durch konservative Muster
  (z. B. Doppelpunkt-Regel beim Outlet) begrenzt, sind aber nicht
  ausgeschlossen. Claims sind Suchhilfen, keine Beobachtungen.
- Tagger-Tags sind Community-kuratiert und ändern sich über die Zeit;
  jeder Sync ist ein datierter Snapshot, kein Live-Fakt.
- `stax`/`token`/`card-selection` haben keinen offiziellen Tag —
  wer dort externe Evidenz braucht, muss auf eine künftige
  Tagger-API warten; eine GraphQL-Hintertür wird nicht genutzt.
