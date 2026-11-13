# Tierlist 1.2.0 — Design

Status: Design + Umsetzung auf Branch `muse/tierlist-1-2-0`
(Arbeitsstand 2026-11-12). Auftrag (M): „Schau dir an, welche
neuen Daten dir jetzt zur Verfügung stehen, arbeite die Tierlist
speziell aus, damit sie besser wird und die Stärke von Karten besser
darstellt und die neuen Daten sinnvoll nutzt — und dass das Programm
allgemein die Daten sinnvoll nutzt und mir Einstelloptionen dafür
gibt."

Grundlage: `docs/TIERLIST_DESIGN.md` (Modell 1.0.0/1.1.0). Dieses
Dokument ändert **nichts** an 1.1.0: `tierlist/1.2.0` ist eine
zusätzlich wählbare Modellversion. Bei Auswahl von 1.1.0 ist das
Verhalten byte-identisch zu vorher (Regressionstests, §7).

Alle Zahlen in §1 sind **gemessen** (SQL auf der Mess-Kopie, s.
Provenienz-Hinweis unten), nicht geschätzt.

Mess-Kopien (keine echte DB wurde angefasst):
- Basis: `run-data/deckbuild.sqlite3` des EDHTop16-Erweiterungs-Laufs
  (vollständiger Echt-DB-Abzug inkl. EDHTop16-Commander-Erweiterung,
  Stand 2026-11-12 16:34 UTC).
- Darin gemergt: die drei TopDeck-Tabellen + TopDeck-Snapshot aus dem
  TopDeck-Live-Lauf (`topdeck-live`, Stand 2026-11-12 14:17 UTC), weil
  der Basis-Abzug vor dem TopDeck-Lauf entstand.
- Sammlung in beiden: `foundation-schwarze-box`, 1.324 Identitäten /
  1.336 Lots / 1.815 Exemplare. (Die globale Tierliste führt zusätzlich
  eine Geister-Identität ohne Lot — 1.325 Zeilen; alle Abdeckungen
  hier zählen strikt über `physical_lot`.)

## 1. Daten-Inventar (gemessen, 2026-11-12)

| # | Schicht | Quelle / Tabellen | Zeilen gesamt | Sammlung (von 1.324) | Stand (fetched_at) | Provenienz-Felder |
|---|---|---|---|---|---|---|
| 1 | Scryfall-Basis | `scryfall_card`, `card_face` | 35.769 Karten | 1.324 (100 %) | 2026-11-12 | Snapshot-ID, Quelle, Parser-Version |
| 2 | Typen/Subtypen | `card_type_component` (type-parser/1.0.0) | 40 Typen, 674 Subtypen, 5 Supertypen (store-weit) | 1.324 mit Komponenten | 2026-11-12 | `category_run` (AVAILABLE, 35.769/35.769) |
| 3 | Keywords | `card_keyword` | 937 distinct (store-weit) | 622 mit ≥ 1 Keyword | 2026-11-12 | `source_id` je Zeile |
| 4 | EDHREC-Kartenseiten | `external_snapshot(kind=edhrec_card)` + `edhrec_card_global` | 1.325 Global-Zeilen | 1.323 AVAILABLE + 1 PARTIAL (Crusade); Salt für 1.324 | 2026-11-11/12 | Snapshot-ID, fetched_at, Parser-Version, Status |
| 5 | EDHREC Commander-Stats/Decks | `edhrec_card_stat`, `edhrec_deck_entry` | 42.474 Stat-Zeilen, 39.891 Deck-Einträge | 64 Commander × 3 Brackets, alle AVAILABLE | 2026-11-11/12 | Snapshot je Commander × Bracket |
| 6 | Playgroup-Profile | `external_snapshot(kind=playgroup_commander)` | 64 Snapshots | 63 eligible Commander abgedeckt | 2026-11-11/12 | Snapshot-ID, Status |
| 7 | Playgroup Card Atlas | `external_snapshot(kind=playgroup_card)` | letzter Stand je Karte: 528 A / 701 P / 95 NF | Win-Gap publiziert: 514; davon n ≥ 25: **409** | 2026-11-11/12 | Snapshot-ID, Status, Payload-Felder |
| 8 | Playgroup Commander-Seiten (Staples) | `playgroup_commander_staple` | 127 Zeilen (alle Snapshots) | Lift-Werte je Commander-Seite | 2026-11-11/12 | Snapshot je Commander |
| 9 | Spellbook | `spellbook_combo` | 3.926 Combo-Zeilen | 257 AVAILABLE mit ≥ 1 Combo; 1.067 NOT_FOUND (= 0 Combos, gemessen) | 2026-11-12 | Snapshot-ID, coverage_status |
| 10 | Tagger-Claims | `card_tagger_claim` | 38.057 Claims, 23 Tags | 797 mit ≥ 1 Claim | 2026-11-12 | Quelle (Search/Bulk), Snapshot |
| 11 | Rollen / Taxonomie | `card_role`, `card_category_check` | 68.524 Rollen-Zeilen | Union auf dieser Kopie: 901 (Heuristik 737, Tagger 797, Strukturprofile 44) — Stand der Mess-Kopie **vor** der Taxonomie-Erweiterung (Heuristik 2.1.0); die Erweiterung auf 30 Kategorien ist eine eigene, bereits integrierte Schicht und in dieser Zahl nicht enthalten; Kategorien-Check: 1.324 geprüft | 2026-11-12 | `origin` je Claim, Taxonomie-Version |
| 12 | Decklisten-Korpus (Archidekt) | `decklist_deck`, `decklist_card` | 9.211 Decks AVAILABLE, 785.840 Kartenzeilen | kanonischer Nenner 9.015 (Verbreitungs-Lauf, gleiche Datenbasis) | 2026-11-12 | Deck-UID, Plattform, Bracket, Inhalts-Fingerprint |
| 13 | Browser-Kohorten | `decklist_deck` (browser:*) | **0 importierte Listen** in dieser Kopie | — | — | Importer vorhanden (`browser-import/1.0.0`), Heimlauf gestrichen |
| 14 | Rulings | `card_ruling` | 79.663 Rulings | **725** mit ≥ 1 Ruling | 2026-11-12 | Scryfall-Snapshot, oracle_id |
| 15 | EDHTop16 Basis | `edhtop16_card_stat` | 1.333 publizierte Karten | **49** mit Play-Rate | 2026-11-12 12:40 UTC | Snapshot-ID, Fenster „last_year" |
| 16 | EDHTop16 Commander-Erweiterung | `edhtop16_commander_card_stat`, `edhtop16_commander_stat` | 1.900 Paare (23 AVAILABLE / 40 NOT_FOUND / 0 NOT_FETCHED) | **77** mit ≥ 1 Commander-Wert; nach n-Gate (§3.3): 300 Paare / 7 Karten im Kontext | 2026-11-12 16:34 UTC | Snapshot je Commander, entries_n, Fenster ONE_YEAR |
| 17 | TopDeck-Turniere | `topdeck_tournament`, `topdeck_result`, `topdeck_card_stat` | 12.890 Turniere, 91.750 Results, 76.437 Decks mit bekanntem Cut-Ergebnis, 21.823 Karten mit Statistik | **937** in ≥ 1 Turnier-Deck; **331** mit Conversion (n ≥ 10); **462** mit Win-Rate | 2026-11-12 14:17 UTC, Fenster 2025-11-12/2026-11-12 | Snapshot-ID, Attribution „Data provided by TopDeck.gg" |
| 18 | MTGJSON | `mtgjson_print` | 59.452 Drucke, davon 47.746 nicht-englische Namenszeilen (14 Sprachen) | 1.324 Identitäten (100 %) | 2026-11-12 12:41 UTC | Snapshot-ID, UUID je Druck |

Verteilungen, auf denen die Mappings in §3 beruhen (gemessen):

- **EDHTop16-Basis, Play-Rate der 49 Sammlungs-Karten:** min 0,0104 ·
  p25 0,0143 · Median 0,0191 · p75 0,0773 · p90 0,3547 · max 0,5889.
  Bänder: ≥ 0,30 → 5 Karten; ≥ 0,20 → 9; ≥ 0,10 → 12; ≥ 0,05 → 16;
  ≥ 0,02 → 24. Die publizierte Liste ist selektiv: 1.333 von 35.769
  Store-Karten (3,7 %).
- **EDHTop16-Commander-Paare nach `entries_n`:** 1.600 der 1.900 Paare
  stammen von Commandern mit entries_n ≤ 17 — dort sind die Play-Rates
  quantisiert (bei n = 1..7 nur Werte k/n; Median 0,5, p90 1,0) und
  als Stärke-Evidenz unbrauchbar. Nur 3 Commander haben entries_n ≥ 25
  (77 / 302 / 613) → 300 Paare, davon 10 Paare / 7 Sammlungs-Karten.
- **TopDeck-Conversion (331 Sammlungs-Karten, n = decks_in_cut ≥ 10):**
  roh min 0,0 · Median 0,209 · p75 0,264 · p90 0,308 · max 0,60.
  Kohorten-Baseline (über Decks mit bekanntem Cut-Ergebnis, n =
  76.437): **0,2685**. n-Verteilung: Median 46, max 52.312.
  Shrinkage-Test (K = 50, Ziel Baseline): geschrumpftes Verhältnis
  Median 0,898 · p90 1,074 · max 1,284; nur 2/331 Karten ≥ 1,25.
  → Echte Über-Conversion ist selten und klein; das Mapping in §3.4
  ist entsprechend konservativ.
- **Überlappung:** Alle 49 EDHTop16-Basis-Karten haben auch eine
  TopDeck-Conversion; Turnier-Signal gesamt: 349/1.324 Karten
  (26,4 %) — 331 TopDeck-Conversion + 77 EDHTop16-Commander (Union).

## 2. Leitplanken (unverändert aus 1.0.0/1.1.0, hier verbindlich)

1. Kern bleibt Kern: EDHREC-Inclusion, Playgroup-Lift,
   Spellbook-Combos mit ihren 1.0.0-Gewichten. Neue Signale sind
   begrenzte Zusatz-Komponenten (§3) mit Renormierung.
2. Asymmetrische Evidenz: Turnier-Signale wirken bei Vorliegen
   positiv; bei Fehlen entfallen sie (Renormierung), sie werden
   **nie** als 0 eingesetzt. Kein Turnier-Subscore liegt unter dem
   Neutralwert 0,50 (§3.2).
3. Kohorten-Trennung absolut: Turnier-Daten fließen nie in
   EDHREC-Inclusion oder Verbreitung ein. Die Verbreitung
   („Verbreitung (gezählt)") bleibt byte-identisches eigenes Feld.
4. Dünne Evidenz → U: Die Gates des Kerns gelten fort; Turnier-
   Gewichte allein (max. 0,20) erreichen die U-Schwelle 0,35 nicht —
   eine Karte ohne jedes Kern-Signal bleibt U, egal wie gut ihre
   Turnier-Werte sind. Der S-Gate bleibt Kern-Signalen vorbehalten.
5. Marks-Invarianz gilt auch für 1.2.0 (Test, §7).

## 3. Neue Signale in `tierlist/1.2.0`

### 3.1 Gewichte

Global (Kern 1,00 + optional max. 0,20):

| Signal | Gewicht | Scope |
|---|---|---|
| `edhrec_global_inclusion` (Kern) | 0,55 | global |
| `playgroup_win_lift` (Kern) | 0,25 | global + context |
| `spellbook_combo_density` (Kern) | 0,20 global / 0,15 context | beide |
| `edhtop16_play_rate` (neu, optional) | 0,10 | global |
| `topdeck_conversion` (neu, optional) | 0,10 | global |
| `edhrec_cohort_inclusion` (Kern) | 0,35 | context |
| `edhrec_cohort_synergy` (Kern) | 0,25 | context |
| `edhtop16_commander_play_rate` (neu, optional) | 0,10 | context |

Begründung der 0,10-Deckelung: Ein einzelnes Turnier-Signal kann den
Score um höchstens 0,10/1,20 ≈ 8,3 % des Abstands zum Neutralwert
verschieben; beide zusammen ≤ 16,7 %. Turnier-Daten sind
cEDH-spezifisch und decken nur 26,4 % der Sammlung ab — sie dürfen
korrigieren, nicht dominieren.

### 3.2 Neutralwert-Floor (Asymmetrie, präzise Fassung)

Kein Turnier-Subscore unterschreitet **0,50** (der Wert, den das
Kern-System einer durchschnittlichen Karte gibt: Playgroup-Lift ≥ 1 pp
→ 0,50; Inclusion-Bandmitte ≈ 0,50). Damit gilt:

- **Abwesenheit ist neutral**: Komponente entfällt, Renormierung über
  den Rest — eine Karte ohne Turnier-Daten erhält exakt ihr
  Kern-Ergebnis (per Test bewiesen, §7).
- **Anwesenheit ist nie negativ**: Die Komponente selbst trägt nie
  einen Wert < 0,50 bei. Eine Verwässerung sehr hoher Kern-Scores
  durch den Neutralwert ist arithmetisch möglich; sie ist durch die
  Gewichte gedeckelt und wird in der Impact-Analyse (§8) gemessen
  statt behauptet — gemessener Maximalwert auf Echtdaten: **−0,071
  Score-Punkte** (eine Karte, S→A; §8).
- **Gemessene Null bleibt Null — gilt hier nicht**: Eine nicht
  gelistete Karte hat keine gemessene 0, sondern keinen publizierten
  Wert (EDHTop16 publiziert nur seine Staples-Liste; TopDeck rechnet
  Conversion erst ab n ≥ 10). Nicht-gelistet = UNAVAILABLE.

### 3.3 `edhtop16_play_rate` (global, Gewicht 0,10)

Quelle: jüngster AVAILABLE-Snapshot `edhtop16_staples`,
`play_rate_last_year` (Anteil der cEDH-Turnier-Entries des letzten
Jahres, die die Karte spielen; Quelle legt den exakten Nenner nicht
offen — im Payload so vermerkt).

Mapping (Bänder an der gemessenen Verteilung, §1):

| play_rate | ≥ 0,30 | ≥ 0,20 | ≥ 0,10 | ≥ 0,05 | ≥ 0,02 | gelistet (> 0) | nicht gelistet |
|---|---|---|---|---|---|---|---|
| Subscore | 0,95 | 0,90 | 0,80 | 0,70 | 0,60 | 0,50 | UNAVAILABLE |

Der Floor 0,50 für „gelistet" ist durch die Selektivität der Liste
begründet (3,7 % aller Karten): Listung allein ist ein positives
Adoptions-Signal aus einem unabhängigen, ergebnisnahen Korpus.

### 3.4 `topdeck_conversion` (global, Gewicht 0,10)

Quelle: jüngster AVAILABLE-Snapshot `topdeck_tournaments`,
`topdeck_card_stat` (lokal aus den gespeicherten Turnierlisten
berechnet; Attribution Pflicht). Voraussetzungen: `conversion_rate`
nicht NULL — die Quelle setzt dafür `decks_in_cut ≥ 10` voraus
(CONVERSION_MIN_DECKS der Schicht); darunter UNAVAILABLE
(„Stichprobe zu klein"), mit den Zählern im Payload.

Verfahren (Shrinkage Richtung Kohorten-Mittel, wie Playgroup §3.3
des Basis-Designs):

```
baseline   = Σ top_cut_reached / Σ bekannte Cut-Ergebnisse   (über Decks desselben Snapshots; gemessen 0,2685 bei 76.437 Decks)
adjusted   = (conversion × n + baseline × K) / (n + K),  K = 50, n = decks_in_cut
ratio      = adjusted / baseline
```

Mapping auf `ratio` (Bänder an der gemessenen geschrumpften
Verteilung, §1):

| ratio | ≥ 1,30 | ≥ 1,20 | ≥ 1,10 | ≥ 1,05 | ≥ 1,00 | < 1,00 |
|---|---|---|---|---|---|---|
| Subscore | 0,95 | 0,85 | 0,75 | 0,65 | 0,58 | 0,50 (Floor) |

n wird im Payload und in der Schublade immer mit angezeigt
(`decks_with`, `decks_in_cut`, `top_cut_decks`, Roh-Conversion,
Baseline, adjustierte Conversion). K = 50 entspricht der
Playgroup-Shrinkage-Konstante — dieselbe Begründung: Bei n = 50 ist
der Messwert zur Hälfte „verdient", darunter dominiert das
Kohorten-Mittel.

### 3.5 `edhtop16_commander_play_rate` (context, Gewicht 0,10)

Quelle: jüngster Snapshot `edhtop16_commander_staples` DESSELBEN
Commanders (Kohorten-Trennung: kein commander-übergreifendes
Pooling), Paar (`play_rate`, `entries_n`).

- **Gate: `entries_n ≥ 25`** (Playgroups eigene Schwelle, hier auf die
  Entry-Zahl des Commanders angewandt). Darunter UNAVAILABLE mit
  Grund `insufficient data: entries_n=<n> < 25` — gemessen (§1) sind
  die Raten kleiner Kohorten quantisiertes Rauschen.
- Commander-Snapshot NOT_FOUND → UNAVAILABLE mit Grund
  `commander has no EDHTop16 tournament data (NOT_FOUND)` — ein
  gemessener Quellenfakt (40/63), kein Fehler.
- Mapping (Form der Cohort-Inclusion-Bänder, an die selektive
  Top-100-Liste des Commanders angepasst):

| play_rate | ≥ 0,60 | ≥ 0,40 | ≥ 0,25 | ≥ 0,12 | gelistet (> 0) | nicht gelistet |
|---|---|---|---|---|---|---|
| Subscore | 0,95 | 0,85 | 0,70 | 0,60 | 0,50 | UNAVAILABLE |

Heute passieren 300 Paare (3 Commander) das Gate, 7 Sammlungs-Karten
erhalten das Signal im Kontext — selten, aber echt. Sobald weitere
Commander die Schwelle erreichen, wächst das Signal ohne
Modelländerung.

### 3.6 Kombination und Gates in 1.2.0

```
score    = Σ (weight_i × subscore_i) / Σ (weight_i)   über verfügbare Signale (Kern + aktivierte Turnier-Signale)
evidence = min(1, Σ weight_i)                          über verfügbare Signale
```

Tier-Bänder und Gates **identisch** zu 1.0.0 (S ≥ 0,85 · A ≥ 0,70 ·
B ≥ 0,55 · C ≥ 0,40; U bei evidence < 0,35; Deckel B bei < 0,55;
Deckel A bei < 0,80). Zwei Präzisierungen:

- **S-Gate**: nur Kern-Signale (`edhrec_global_inclusion`,
  `edhrec_cohort_inclusion`, `playgroup_win_lift`) mit Subscore
  ≥ 0,85 qualifizieren — Turnier-Subscores nie. Eine Karte wird
  nicht allein durch Turnier-Daten S.
- **Evidence-Beitrag der Turnier-Signale**: Sie zählen zur Evidence
  (sie sind gemessene Daten), aber ihr Gesamtgewicht (≤ 0,20) liegt
  unter der U-Schwelle — ohne Kern-Signal bleibt es bei U (§2.4).
  Konkret neue Deckel-Lage: Kern-Evidence 0,45 (Playgroup +
  Spellbook) + beide Turnier-Signale = 0,65 → Deckel A statt B.
  Das ist gewollt: drei unabhängige gemessene Quellen sind mehr
  Evidenz als zwei; der Deckel A bleibt, S bleibt Kern-Gate.

## 4. Was bewusst KEIN Stärke-Signal wird

| Schicht | Warum nicht im Tier | Wo sie stattdessen wirkt |
|---|---|---|
| Rulings (725 Karten) | Regeltexte beschreiben Interaktionen, keine Stärke; Anzahl korreliert mit Textkomplexität, nicht mit Qualität. | Karten-Schublade: Anzahl + Liste (vorhanden) |
| MTGJSON-Drucke/Fremdnamen | Druck-Historie und Lokalisierung sind Sammler-/Sprachdaten, keine Spielstärke. | Schublade: Drucke + Fremdnamen (neu, §6) |
| Taxonomie/Rollen (901–1.065 Karten) | Rollen beschreiben, WAS eine Karte tut, nicht wie stark (Basis-Design §3.5, unverändert). | Filter/Kategorien in der Kartenliste (vorhanden), Kontext im Evidenz-Panel |
| Salt | Reibungs-/Stimmungsmaß; eine Karte ist nicht schwächer, weil Gegner sie nicht mögen (Basis-Design §3.5). | Badge (vorhanden) |
| Preis/Budget | Marktmaß (Knappheit/Nachfrage), kein Qualitätsmaß. | Budget-Badge (vorhanden) |
| Marks | Owner-Präferenz ist Filter, nie Input (Basis-Design §5). | Filter; Invarianz per Test |
| TopDeck-Win-Rate (462 Karten) | Doppelzählung desselben Korpus: Win-Rate und Conversion aus denselben Decks sind stark korreliert; zwei Komponenten aus einem Korpus würden dessen Gewicht faktisch verdoppeln. Conversion ist die trennschärfere Größe (Cut-Erreichen je Deck). | Anzeige in der Schublade (vorhanden) |
| EDHTop16-Commander-Aggregate (`conversion_rate`/`meta_share` je Commander) | Commander-Ebene, keine Karten-Evidenz; je Karte publiziert die Quelle keine Conversion (bleibt NULL). | Commander-Ansichten (vorhanden) |
| Playgroup-Atlas PARTIAL-Felder unter n < 25 | Quellen-eigene Zuverlässigkeitsschwelle (Basis-Design §3.3). | — (unverändert UNAVAILABLE) |
| Verbreitung (gezählt) | Häufigkeit ≠ Stärke (Owner-Entscheid 2026-11-12). | Eigenes Feld, unverändert |

## 5. Einstelloptionen (app_setting, versioniert)

Neue Schlüssel im bestehenden Katalog (`settings.py`), Defaults
begründet:

| Schlüssel | Typ | Default | Begründung |
|---|---|---|---|
| `tierlist.model_version` | enum [`tierlist/1.1.0`, `tierlist/1.2.0`] | `tierlist/1.1.0` | Bestandsverhalten bleibt Voreinstellung; 1.2.0 wird bewusst aktiviert (Owner-Kontrolle über den Modellwechsel). Lese-Pfade (API/UI) zeigen die aktive Version; `compute-tiers` rechnet die gewählte (CLI `--model` überschreibt pro Lauf). |
| `tierlist.signal_edhtop16_global` | bool | `true` | Signal ist selektiv (49 Karten) und floored — Nutzen ohne Risiko im Default. |
| `tierlist.signal_edhtop16_commander` | bool | `true` | Wie oben; wirkt durch das n-Gate heute nur auf 7 Karten im Kontext. |
| `tierlist.signal_topdeck_conversion` | bool | `true` | Größte neue Abdeckung (331 Karten); Shrinkage + Deckelung begrenzen den Einfluss. |

Regeln: Schalter wirken nur unter Modell 1.2.0 (unter 1.1.0 sind sie
 wirkungslos und werden in der UI als solche markiert). Schalter AUS
⇒ die Komponente existiert im Compute-Lauf nicht (nicht „Wert 0") —
per Test bewiesen. Die Settings-UI zeigt die vier Schlüssel mit
Beschreibung; die Tierlisten-Seite zeigt die aktive Modellversion
und die aktiven Signale. Ein Modell-/Schalter-Wechsel ändert keine
gespeicherten Zeilen — er wirkt beim nächsten `compute-tiers`-Lauf
(die UI weist darauf hin, wie bei allen Syncs: nichts ändert sich
still).

Beide Modellversionen dürfen gleichzeitig gespeichert sein:
`tier_assignment` erhält `algo_version` in den Primärschlüssel
(Cache-Tabelle, wird bei Formänderung wie bisher verworfen und vom
nächsten Compute neu aufgebaut). Lese-Pfade filtern kombinierte
Scopes auf die aktive Version; die Verbreitung liest bevorzugt die
aktive Version und sonst die jüngste (ihr Inhalt ist
versionsunabhängig identisch).

## 6. Transparenz und allgemeine Datennutzung

- **Evidenz-Schublade** (vorhanden, erweitert): Die Signal-Tabelle
  zeigt bereits je Signal Wert, n, Subscore, Gewicht, Quelle,
  fetched_at. Die Turnier-Signale erscheinen dort automatisch mit
  ihren Payloads (§3.3–3.5: Rohwert, n, Baseline/adjustiert bei
  TopDeck, entries_n-Gate-Grund bei EDHTop16-Commander). Zusätzlich
  zeigt die Schublade die aktive Modellversion der Zeile.
- **Karten-Schublade** (`/api/external/card`, erweitert):
  - `edhtop16_commanders`: EDHTop16-Werte je Commander (vorhandene
    Lesefunktion `card_edhtop16_commanders` war bisher nicht
    verdrahtet) — gerendert als Liste mit Play-Rate, entries_n,
    Fenster.
  - `mtgjson`: Drucke (Set/Nummer/Sprache) + Fremdnamen der Karte
    (neue Lesefunktion `card_mtgjson_prints`).
  - Rulings (Anzahl + Liste), EDHTop16-Basis, TopDeck mit
    Attribution: vorhanden, unverändert.
- **Kartenliste**: vorhandene Filter (Tier, Salt, Budget, Rollen,
  Kategorien) bleiben; neu ist nur die Modellversions-Anzeige im
  Tier-Badge-Titel (Tooltip: Version + Score + Evidenz). Kein Umbau.

## 7. Verifikation (Pflicht-Tests)

1. **1.1.0-Regression**: Compute unter 1.1.0 auf der Fixture-DB ⇒
   Zeilen byte-identisch zum bisherigen Verhalten (bestehende
   Tierlist-Tests laufen unverändert; ALGO_VERSION des 1.1.0-Pfades
   bleibt `tierlist/1.1.0` in den Zeilen).
2. **Marks-Invarianz 1.2.0**: Marks flippen ⇒ alle 1.2.0-Zeilen
   byte-identisch (global + context + universe).
3. **Schalter AUS**: jeweilige Komponente fehlt im Payload exakt;
   Score/Evidenz = Rechnung ohne diese Komponente.
4. **Fehlendes Turnier-Signal ⇒ keine Abwertung**: Karte ohne
   Turnier-Zeilen erhält unter 1.2.0 exakt Score/Evidenz/Tier ihrer
   Kern-Signale (Vergleich gegen Compute mit geleerten
   Turnier-Tabellen muss für diese Karten identische
   Tier-/Score-/Evidenz-Werte geben — so prüft es
   `test_absence_is_neutral`; der Reason-Text im Payload darf sich
   ändern, sobald ein Turnier-Snapshot existiert).
5. **Floor**: kein Turnier-Subscore < 0,50 (Eigenschaftstest über
   alle Band-Ränder).
6. **U-Schutz**: Karte nur mit Turnier-Signalen (Kern-Snapshots
   entfernt) ⇒ U trotz Subscore 0,95.
7. **S-Gate**: Karte mit Kern-Score im S-Band, aber keinem
   Kern-Signal ≥ 0,85, dafür Turnier 0,95 ⇒ A, nicht S.
8. **n-Gate**: EDHTop16-Commander-Paar mit entries_n = 24 ⇒
   UNAVAILABLE; mit 25 ⇒ verfügbar.
9. **Verbreitung unverändert**: universe-Zeilen (Tier/Score je
   universe_id) unter 1.1.0- und 1.2.0-Compute identisch.
10. **Kohorten-Trennung**: Turnier-Tabellen leeren/füllen ändert
    keine Inclusion-/Verbreitungs-Zahl (bestehende Tests +
    Stichprobe im Impact-Lauf).

## 8. Impact (gemessen auf der Mess-Kopie, 2026-11-12)

Beide Modelle wurden mit dem neuen Code auf derselben Mess-Kopie
(§1) vollständig gerechnet (1.1.0: 17:37 UTC, 1.2.0: 17:45 UTC;
je 1.325 globale, 44.595 Kontext- und 589.056 Universum-Zeilen).
Die 1.1.0-Verteilung reproduziert den bekannten Echt-DB-Stand exakt
— das validiert Kopie und 1.1.0-Pfad auf Echtdaten.

**Global:**

| Modell | S | A | B | C | D | U |
|---|---|---|---|---|---|---|
| 1.1.0 | 5 | 28 | 109 | 134 | 1.048 | 1 |
| 1.2.0 | 4 | 29 | 104 | 163 | 1.024 | 1 |

- **38 von 1.325 Karten ändern die Stufe: 28 auf, 10 ab.** Scores:
  187 auf, 139 ab (meist ohne Stufenwechsel).
- Verfügbare Turnier-Signale im Lauf: EDHTop16 global 49 Karten,
  TopDeck-Conversion 332 Zeilen (331 Sammlung + Geister-Identität).
- **Größte Aufsteiger** (alle mit dokumentierten Signalwerten):
  Stalactite Dagger D→C (TopDeck-Ratio 1,26 bei n = 980),
  Chomping Changeling C→B (Ratio 1,28, n = 218), Sanar C→B
  (Ratio 1,23, n = 51), Silver Myr C→B (Ratio 1,23, n = 613, plus
  EDHTop16 gelistet), Autumn's Veil D→C (EDHTop16-Rate 0,057 →
  0,70; Evidence 0,55 → 0,75 hebt den Deckel).
- **Absteiger sind ausnahmslos der dokumentierte Floor-Effekt**
  (§3.2): Karten an einer Stufengrenze, deren Turnier-Komponenten
  am Neutralwert 0,50 liegen (gemessene Conversion auf/unter der
  Baseline), verlieren durch die Renormierung wenige Hundertstel.
  Größter Fall: **Bojuka Bog S→A** (Score 0,891 → 0,823; EDHTop16
  0,60, TopDeck-Ratio 0,664 bei n = 586 — eine groß gemessene,
  unterdurchschnittliche Conversion; die Karte bleibt A mit
  Evidence 1,0). Übrige 9 Absteiger: B→C an der 0,55-Grenze
  (Scores 0,553–0,555 → 0,542–0,550). Maximaler Score-Verlust:
  **−0,071** (Garruk's Uprising, A→A). Kein Absteiger fällt unter
  C; kein Absteiger hat ein Turnier-Signal oberhalb des
  Neutralwerts verloren — die Komponenten selbst sind nie negativ.
  Ob der Bojuka-Bog-Fall (S-Gate über Kern erfüllt, Score durch
  zwei neutrale Turnier-Komponenten verwässert) eine Modell-
  Nachschärfung rechtfertigt, ist eine Design-Entscheidung für das
  Review der Hauptinstanz; das Modell wurde nach Sichtung der
  Ergebnisse NICHT ergebnisgetrieben nachjustiert.

**Kontext:** 147 von 44.595 Zeilen ändern die Stufe (**144 auf,
3 ab**); 460 Zeilen tragen ein verfügbares
EDHTop16-Commander-Signal. Konsistenzprüfung: **0 Änderungen auf
Zeilen ohne verfügbares Commander-Signal** — jede Kontext-Änderung
ist der neuen Komponente zurechenbar. Beispiele: Mana Vault
C→B (Tatyova-Kontext, Rate 0,805 bei entries_n 77), Lotus Petal
D→C (Rate 0,917 bei entries_n 613), Finale of Devastation D→C
in zwei Kohorten (Raten 0,54/0,96).

**Verbreitung:** alle 589.056 Universum-Zeilen unter beiden
Modellen **identisch** (Tier + Score je Karte × Universum, auf
Echtdaten nachgeprüft — zusätzlich zum Fixture-Test §7.9).

**Fazit des Impact-Laufs:** Der Effekt ist klein und gerichtet —
genau die vorgesehene Korrekturgröße: 2,9 % der Karten wechseln
die Stufe, fast ausschließlich D/C-Karten mit echter Turnier-
Überperformance nach oben und Grenzfälle durch den offengelegten
Neutralwert-Effekt nach unten. Die breite Masse (1.287 Karten)
bleibt unverändert, weil sie entweder keine Turnier-Daten hat
(neutral) oder ihre Kern-Evidenz dominiert.
