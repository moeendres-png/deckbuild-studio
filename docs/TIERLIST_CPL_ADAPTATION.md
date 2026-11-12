# Tierlist — CPL-Anpassung: Delta-Spezifikation

Status: **Revision 2 (2026-11-12)** — ersetzt Revision 1 vollständig.
Enthält die Moritz-Entscheidungen vom 2026-11-12, 10:57 und 11:00 Uhr
(Namensentscheidung „Verbreitung (gezählt)", UI-/Funktionsumfang,
Ranking-Verschärfung, Blöcke A4/A5 des Daten- und Ranking-Plans
`deckbuild-datenplan-ranking.md`).

Ziel: Unsere Tierlist (`tierlist/1.0.0`, `docs/TIERLIST_DESIGN.md`) an
die Tier-Mechanik von commander-playtest-lab (CPL, PR #1207 zu
Issue #1205) anpassen — soweit mit unseren Verträgen verträglich.

Referenz-Stand CPL: Branch `muse/1205-deckbuilder-data-20261112`,
Head `dd75904b2` (Folge-Review PASS; zum Extraktionszeitpunkt war der
PR upstream noch nicht gemergt und seine `quality`-CI rot — Referenz
war das reviewte Design. Nachtrag 2026-11-12: PR #1207 ist inzwischen
mit finalem Head `3f24b542` gemergt; die hier extrahierte Mechanik
stammt aus dem reviewten Branch-Stand.)

Referenz-Stand eigene Bausteine: Decklisten-/Settings-Stack
(`inclusion.py`, `decklists.py`, `settings.py`) aus Branch
`muse/decklists-settings-1`, Head `a6f2776`: 9.211 geerntete
Decklisten, **9.048 kanonische Decks** nach Inhalts-Dedupe.

Arbeitsregeln: nur objektive Daten mit Provenienz (Quelle, Zeitpunkt,
Hash, Parser-Version, Status); Kohorten nie vermischen;
UNAVAILABLE ≠ 0; Marks ohne Einfluss auf jede berechnete Zahl;
Determinismus bis auf `computed_at`.

---

## 1. Zwei getrennte Felder (Moritz-Entscheidung, verbindlich)

| Feld | Frage | Datenbasis | Stufen |
|---|---|---|---|
| **Verbreitung (gezählt)** | Wie verbreitet ist die Karte in den Decklisten des eingestellten Universums? | ausschließlich gezählte eigene Decklisten | S–D, sonst „unbekannt" |
| **Evidenz-Tier (Stärke-Schätzung)** | Wie stark ist die Karte (allgemein / für diesen Commander)? | Mehrsignal-Modell aus Beobachtungsdaten (EDHREC, Playgroup, Spellbook) | S–U |

Regeln:

- **Stärke kommt nicht aus Häufigkeit allein.** Die gezählte
  Decklisten-Häufigkeit geht **nicht** in die Evidenz-Tier ein — sie
  steht ausschließlich im Feld „Verbreitung (gezählt)".
- Die Evidenz-Tier wird über Stärkesignale verbessert (Abschnitt 4.3),
  nicht über Frequenz.
- Beide Felder sind marks-invariant (Negativtest, Abschnitt 6).

CPL kennt nur ein Feld (gezählte Inclusion-Tiers). Unsere Trennung
übernimmt die CPL-Mechanik für das Verbreitungs-Feld 1:1-nah und
behält das eigene Mehrsignal-Modell für die Stärke — das ist die
zentrale Anpassungsentscheidung dieser Spezifikation (D1).

---

## 2. CPL-Mechanik (extrahiert aus dem Code, nicht aus Summaries)

### 2.1 `src/commander_lab/studio/tiers.py` (102 Zeilen)

- Reine Funktion über gezählte Inclusion:
  `TierParams(min_universe=30, cuts=((S,0.50),(A,0.35),(B,0.20),(C,0.10)),
  fallback_tier=D)`.
- `tier_for_share(share, denominator)`: Nenner < 30 →
  `(U, UNIVERSE_TOO_SMALL)`; share None → `(U, DENOMINATOR_MISSING)`;
  sonst erster Cut mit `share >= cut` → `(ladder_tier, SHARE_CUT)`,
  darunter `(D, BELOW_LOWEST_CUT)`.
- Breakdown je Wert: hits, denominator, share, universe_snapshot,
  params, `data_class=DERIVED_DESCRIPTIVE`.
- Parameter sind bei CPL **Owner-Einstellungen**; eine explizit leere
  Cut-Liste bleibt leer (Test sichert das ab).

### 2.2 `universe.py` (278 Zeilen) + `decklist_import.py`

- Universum-Profile als DB-Tabelle `universe_profile`; Spec-Schlüssel
  platforms, cohorts, date_from, date_to, min_main_cards; unbekannte
  Schlüssel sind ein Fehler.
- Auswahl: nur Decks mit `duplicate_of IS NULL` (Inhalts-Dedupe per
  sha256-Fingerprint über (Karte, Sektion, Anzahl); Duplikate zeigen
  auf die erste Kopie).
- Gezählte Sektionen: `main, commander, companion` — Sideboard und
  Maybeboard nie.
- Inclusion: hits = COUNT(DISTINCT deck_id) je Karte; Nenner = |U|;
  share = None bei |U| = 0 (nie durch 0 teilen, nie 0 behaupten).
- `snapshot_id = universe:<sha256[:16]>:<n>` über Spec + sortierte
  Deck-IDs + gespeicherte Deck-Inhalts-Fingerprints.

### 2.3 CPL-Design-Doku `docs/DECKBUILDER_TIERLIST_DESIGN.md`

(Entwurf, über den implementierten Kern hinaus — als Design-Referenz
gewertet, nicht als Ist-Stand.)

- Zwei Universum-Typen: **LIST** (Abwesenheit in der Liste = gezählte
  0) vs. **AGGREGATE** (Abwesenheit = UNKNOWN); nie vermischt.
- Gewichtete Aggregation ⇒ Datenklasse `HEURISTIC_MODEL`.
- U-Reason-Codes u. a.: NO_OBSERVATION, DENOMINATOR_MISSING,
  SAMPLE_BELOW_MIN, UNIVERSE_TOO_SMALL, SOURCE_STATUS_REVIEW.
- Parameter-Sätze als DB-Tabelle mit Hash; optionaler
  Perzentil-Grenzmodus; Marker/Flags nie Tier-Eingaben.
- Ko-Okkurrenz ist dort als Auswertung vorgesehen (Namens-Matching
  als Risiko benannt).

### 2.4 Was CPL nicht hat

- Kein Mehrsignal-/Stärke-Modell, kein Playgroup-Lift, keine
  EDHREC-Synergy, **keine Combo-Einbindung in der Tier** (Spellbook
  kommt in CPLs Tier-Mechanik nicht vor), keine Evidenz-Gates,
  keine Shrinkage.

---

## 3. Unser Stand (tierlist/1.0.0, auf main gemergt)

- Scopes `global` + `context` (Commander × Bracket), Tabelle
  `tier_assignment`, Payload je Zeile mit allen Signalen, Gewichten,
  Snapshot-IDs, Marker-Block (Salt/Budget/Rollen/Flags — nie Inputs).
- Global: EDHREC-Inclusion 0,55 / Playgroup-Lift 0,25 /
  Spellbook-Combo-Dichte 0,20.
- Kontext: Kohorten-Inclusion 0,35 / Synergy 0,25 / Playgroup-Lift
  0,25 / Spellbook 0,15 (genaue Werte: Code `CONTEXT_WEIGHTS`).
- Gates: Evidenz < 0,35 ⇒ U; Deckel B < 0,55; Deckel A < 0,80;
  S braucht ein Signal ≥ 0,85. Playgroup-Lift erst ab n ≥ 25,
  Shrinkage n/(n+50).
- Echte DB: 43.058 Zeilen; global S 5 / A 28 / B 114 / C 122 /
  D 1.052 / U 3.

---

## 4. Zielbild tierlist/1.1.0

### 4.1 Feld „Verbreitung (gezählt)" (neuer Scope `universe`)

Reine CPL-Mechanik auf unserem Korpus:

- **Profile** werden aus den Universum-Einstellungen abgeleitet
  (keine eigene Profil-Tabelle): `all` (alle gewählten Kohorten
  gepoolt) + je ein Profil je Commander mit geernteten Decks
  (Brackets gepoolt). Ein Profil = ein Universum mit eigener
  `universe_id` (Snapshot-Mechanik §2.2: Hash über Definition +
  kanonische Deck-UIDs + Inhalts-Fingerprints).
- **Zählregeln** exakt wie `inclusion.py`: nur AVAILABLE-Decks der
  gewählten Plattformen/Brackets/Zeitraum; Inhalts-Dedupe (niedrigste
  Deck-UID gewinnt); Commander-Einträge zählen nicht mit (Abweichung
  zu CPL §2.2, begründet in D13); nur Einträge mit quantity > 0 und
  gesetzter oracle_id; Nenner = kanonische Deckzahl, immer im Payload.
- **Stufen**: `counted_tier` mit CPL-Cuts (S ≥ 0,50; A ≥ 0,35;
  B ≥ 0,20; C ≥ 0,10; sonst D/`BELOW_LOWEST_CUT`). Nenner <
  Mindestgröße ⇒ U/`UNIVERSE_TOO_SMALL`; fehlender Nenner ⇒
  U/`DENOMINATOR_MISSING`. Abwesenheit im Universum = gezählte 0
  (LIST-Regel) ⇒ D, **nicht** U. UI zeigt U als „unbekannt".
- **Payload** je Zeile: hits, denominator, share, `tier_reason`,
  `u_reason`, `data_class=DERIVED_DESCRIPTIVE`, Universum-Block
  (Profil, Definition, Zusammensetzung nach Plattform/Bracket,
  Snapshot-ID), Parameter-Satz, Feldname „Verbreitung (gezählt)".
- **Kartenmenge** je Profil: im Universum beobachtete Karten ∪
  Sammlungskarten (damit jede eigene Karte einen Wert oder ein
  ehrliches „unbekannt" bekommt).

### 4.2 Universum-Einstellungen (UI-Kopf der Tierliste-Seite)

Basis: vorhandene `app_setting`-Schlüssel der Decklisten-Lane
(`inclusion.brackets`, `inclusion.platforms`, `inclusion.min_decks`,
`inclusion.max_age_days`). Erweiterungen dieser Lane:

- **Zeitraum**: neue Schlüssel `inclusion.date_from` /
  `inclusion.date_to` (ISO-Datum, optional). Basis ist der
  **Quell-Zeitstempel des Decks** (Archidekt-`updatedAt` aus dem
  Listing; wird ab dieser Lane als `source_updated_at` gespeichert).
  Decks ohne Quell-Zeitstempel werden bei gesetztem Zeitraum
  ausgeschlossen und in der Definition gezählt ausgewiesen
  (`excluded_no_timestamp`) — `fetched_at` wird **nicht** als
  Deck-Datum ausgegeben (Ranking-Plan: keine gefälschten Zeitstempel).
  Konsequenz für den Bestand: Die 9.211 geernteten Decks haben noch
  keinen Quell-Zeitstempel (NULL) — ein gesetzter Zeitraum liefert
  bis zur nächsten Ernte ein leeres Universum mit ehrlicher
  Definition statt falscher Treffer.
- **Mindestgröße**: neuer Schlüssel `tierlist.min_universe`
  (Default 30 = CPL-Default). Er steuert das U-Gate der Verbreitung.
  (Die Anzeige-Schwelle `inclusion.min_decks` für Inclusion-Listen
  bleibt davon getrennt.)
- **Anzeige**: Die Seite zeigt immer die aktuelle Universum-
  Definition mit kanonischer Deckzahl und Aufteilung nach Plattform
  und Bracket (aus dem kanonischen `all`-Universum).
- **Bewusst nicht in diesem Schritt** (Moritz): Sortieren/Filtern
  nach der Verbreitungs-Stufe, eigene Stufen-Grenzen speichern,
  Profile löschen. Die CPL-Cuts bleiben Code-Konstante der Version
  (unser §8-Vertrag: Schwellen = Code + Version, keine DB-Tabelle).

### 4.3 Evidenz-Tier (Stärke) — unverändertes Modell, gezielte Verstärkung

Das 1.0.0-Mehrsignal-Modell (Gewichte, Gates, Shrinkage) bleibt
**unverändert** — insbesondere geht **keine** gezählte Häufigkeit in
die Stärke ein. Verstärkt wird nur die Evidenz-Basis:

- **A1 Synergy (vorhanden)**: EDHREC-Synergy je Commander × Karte ist
  bereits eigenes Kontext-Signal (Gewicht 0,25). Spec-Stand: bleibt;
  Abdeckung wird in der Validierung nachgezählt und berichtet.
- **A3 Playgroup-Lift (vorhanden)**: Win-Lift mit n-Anzeige, Gate
  n ≥ 25, Shrinkage n/(n+50) — unverändert. Die feldgenaue
  PARTIAL-Auswertung des Card Atlas ist Vorarbeit der Daten-Lane
  (dort laufend), keine Änderung in dieser Lane.
- **A4 Combo-Einbindung (vorhanden, gegen CPL gespiegelt)**: CPL
  führt **kein** Combo-Signal (ihre Tier ist reine Inclusion).
  Unser Spellbook-Signal (Combo-Dichte, global 0,20 / Kontext 0,15)
  bleibt Stärke-Signal: Combo-Einbindung misst Vernetzung/
  Synergie-Potenzial, nicht Decklisten-Häufigkeit. Payload weist
  Anzahl Combos, erfasste Combos und — neu — die Zahl distinkter
  Combo-Partner und Ergebnis-Typen (aus `spellbook_combo`) aus.
- **A5 Top-Commander-Evidenz (neu)**: Die EDHREC-Kartenseiten
  speichern „Top Commanders" je Karte (der vorhandene Parser
  extrahiert Name, Slug, num_decks, potential_decks bereits ins
  Snapshot-Payload). Gemessene Abdeckung auf der echten DB (Kopie,
  2026-11-12): 1.322/1.322 AVAILABLE-Snapshots mit
  Top-Commander-Daten, 31.728 (Karte, Commander)-Paare, 47 der 64
  Kontext-Commander per Name vertreten. Mechanik: Fehlt die
  Kohorten-Statistik eines Kontexts für eine Karte, liefert der
  Top-Commander-Eintrag der Karte die Kohorten-Inclusion desselben
  Konstrukts (Anteil der Decks dieses Commanders mit der Karte, aus
  der Kartenseite gemessen) — als Fallback **innerhalb** des Signals
  `cohort_inclusion`, im Payload gekennzeichnet
  (`measurement="card_page_top_commanders"`, Provenienz =
  Kartenseiten-Snapshot). Die Commander-Seiten-Statistik bleibt
  Primärquelle und gewinnt immer. Die Evidenz ist bracket-agnostisch
  (wie das Playgroup-Signal) und wird als solche gekennzeichnet
  (`bracket_specific=false`). Karten mit nur dieser Evidenz erhalten
  Kontext-Zeilen (Kontext-Kartenmenge wird um die Top-Commander-
  Evidenz des Commanders erweitert).
- **A6**: Salt/Preis bleiben Marker; Kategorien/Rollen sind
  Fit-Information (Deck-Bedarf), **kein** Stärke-Signal — sie gehen
  nicht in den Score ein (bestehender Vertrag, hier bestätigt).

### 4.4 Ko-Okkurrenz (Karten-Schublade)

- Berechnung aus den kanonischen Decks der aktuellen
  Universum-Auswahl (optional je Commander eingegrenzt): je Karte
  die Partner mit gemeinsamen Decks, Nenner (Decks mit der Karte)
  und **Lift** = P(Partner|Karte) / P(Partner) — Lift statt
  Roh-Häufigkeit (Ranking-Plan A2).
- Anzeige in der Evidenz-Schublade auf Klick („Wird gespielt mit …"):
  Partner, gemeinsame Decks, Lift; Combo-Partner (gemeinsame
  Spellbook-Combo, aus `spellbook_combo.card_oracle_ids_json`)
  werden markiert (A4-Verstärkung).
- Einträge ohne oracle_id (97 ungemappte Token-/Emblem-Namen)
  bleiben unzugeordnet und tauchen nicht als Partner auf.

### 4.5 Read-API / UI

- `GET /api/tiers?scope=universe&universe_id=…`,
  `GET /api/tiers/universes` (Profile + Definitionen),
  `GET /api/verbreitung` (aktuelle Definition + kanonische Deckzahl
  + Aufteilung Plattform/Bracket + Profile),
  `GET /api/cards/{oracle_id}/cooccurrence` (Lift-Liste).
- Karten-Kachel: Badge „Verbreitung (gezählt)": Stufe + Treffer/
  Deckzahl/Anteil oder „unbekannt". Evidenz-Schublade: Block
  „Verbreitung (gezählt)" + Ko-Okkurrenz auf Klick.
- Kopf der Seite: Universum-Formular (Plattform, Brackets, Zeitraum,
  Mindestgröße) über die vorhandenen Settings-Endpunkte; danach ist
  `compute-tiers` erneut zu rechnen (Hinweis im Formular, kein
  Auto-Trigger in dieser Lane).

---

## 5. Entscheidungen (übernommen / angepasst / nicht übernommen)

| # | Punkt | Entscheidung | Begründung |
|---|---|---|---|
| D1 | CPL-Einsignal-Tier vs. unser Mehrsignal-Modell | **angepasst**: CPL-Mechanik wird das Feld „Verbreitung (gezählt)"; Stärke bleibt Mehrsignal | Moritz-Entscheid 10:57: Stärke nicht aus Häufigkeit; beide Felder getrennt führen |
| D2 | Gezählte Inclusion in die Evidenz-Tier | **nicht übernommen** (Rev. 1 hatte sie als Signal vorgesehen) | Moritz-Entscheid 10:57/11:00 + Ranking-Plan: Häufigkeit bleibt aufs Verbreitungs-Feld begrenzt; Trennung per Test gesichert (§6.2) |
| D3 | Snapshot-ID-Mechanik (Hash über Definition + Deck-IDs + Fingerprints) | **übernommen** | Determinismus + Provenienz; Fingerprints existieren in `inclusion.py` |
| D4 | U-Reason-Codes | **übernommen** (Verbreitung: CPL-Codes; Evidenz-Tier: NO_OBSERVATION / INSUFFICIENT_EVIDENCE ergänzt) | „unbekannt" muss begründbar sein, nie pauschal |
| D5 | `data_class` je Payload | **übernommen**: Verbreitung `DERIVED_DESCRIPTIVE`, Evidenz-Tier `HEURISTIC_MODEL` | CPL-Design §2.3; macht den Modell-Charakter der Stärke sichtbar |
| D6 | LIST/AGGREGATE-Trennung | **übernommen** als benannte Regel | Unser Verhalten erfüllt sie faktisch (gezählt: Abwesenheit = 0; Aggregate: Abwesenheit = UNAVAILABLE) |
| D7 | Parameter als DB-Tabelle (CPL: Owner-Einstellungen) | **nicht übernommen**: Cuts bleiben Code-Konstante + Version; nur Mindestgröße ist UI-Einstellung (`tierlist.min_universe`, Default 30) | Unser Vertrag (Design-Doku): Schwellen versioniert im Code; Mindestgröße ist Betriebs-, keine Modellgröße |
| D8 | Perzentil-Grenzen als Option | **nicht übernommen** | Kein Bedarf belegt; Cuts sind absolut und quellenunabhängig lesbar |
| D9 | Duplikat-Schalter je Universum | **nicht übernommen** | Dedupe ist bei uns Datenregel (Integrität), keine Zähl-Option |
| D10 | Evidenz-Gates | **behalten** (nur Evidenz-Tier) | Unsere Ausprägung von „ignorieren mit Offenlegung"; Verbreitung kennt stattdessen das Mindestgrößen-Gate |
| D11 | Ko-Okkurrenz | **übernommen + angepasst**: mit Lift statt Roh-Häufigkeit, Combo-Partner markiert | Ranking-Plan A2/A4; Namensrisiko bei uns durch oracle_id-Mapping weitgehend entschärft |
| D12 | Simulation/Engine-Bezug in Tiers | **nicht übernommen** | BUILD-only-Vertrag |
| D13 | Commander-Sektion zählt im Universum mit (CPL) | **angepasst**: Commander-Einträge zählen nicht mit | CPL-Universen sind commander-homogen (Commander-Anteil sonst konstant 1,0); unsere Profile mischen Commander — Commander-Zeilen würden jede Verbreitung verfälschen |

Konflikte: K1 (Einsignal vs. Mehrsignal) ist durch D1 entschieden.
K2 (min_universe 30 vs. min_decks 10) bleibt getrennt begründet
(§4.2). K3 (Zählung per oracle_id statt Name) bleibt: CPL zählt per
Name; wir zählen per oracle_id (Mapping-Quote 99,99 %, Rest ehrlich
unzugeordnet).

---

## 6. Invarianzen & Tests (Pflicht)

1. **Marks-Invarianz für beide Felder** (Negativtest): Favorit,
   Ausschluss und Notiz ändern weder Verbreitungs-Zahl/-Stufe noch
   Evidenz-Tier — inklusive explizitem Payload-Vergleich der
   Verbreitungs-Werte (hits/share/tier) vor/nach Marks-Flip.
2. **Frequenz-Trennung**: Evidenz-Tier-Zeilen (global + Kontext) sind
   mit und ohne geerntete Decklisten identisch.
3. **Determinismus**: zweimal rechnen ⇒ identische Zeilen inkl.
   `universe_id`s (bis auf `computed_at`); Snapshot-ID rotiert bei
   Inhaltsänderung eines Decks.
4. **Zählregeln**: Dedupe (Duplikat zählt einmal), Commander-
   Ausschluss, quantity-0-Guard, Zeitraum-Ausschluss ohne
   Quell-Zeitstempel + Zähler in der Definition, Mindestgrößen-Gate.
5. **A5**: Commander-Seiten-Statistik gewinnt gegen Top-Commander-
   Fallback; Fallback trägt `measurement`-Kennzeichnung und die
   Kartenseiten-Provenienz; unbekannter Commander-Name ⇒ keine
   Evidenz (kein Raten).
6. **Schema-Migration**: 1.0.0-förmige `tier_assignment`-Tabelle wird
   beim Öffnen neu aufgebaut (abgeleiteter Cache, kein Verlust an
   Quelldaten).
7. Gesamtsuite grün, Ruff sauber.

---

## 7. Validierung auf der DB-Kopie

- Vorher-Verteilung 1.0.0 sichern (43.058 Zeilen; global
  S 5/A 28/B 114/C 122/D 1.052/U 3), dann mit 1.1.0-Code auf der
  Kopie rechnen.
- Berichten: Verbreitung-Verteilung je Profil (`all`: Nenner 9.048
  erwartet), Evidenz-Tier-Delta (erwartet: global identisch;
  Kontext-Zeilen-Delta nur durch A5-Evidenz, mit Zahlen),
  A1-Synergy-Abdeckung (Kontexte mit Synergy-Evidenz),
  A5-Abdeckung (Commander mit Top-Commander-Evidenz; Paare;
  Kontext-Zeilen mit Fallback-Evidenz).

---

## 8. Offene Punkte

- **O1 (entfallen)**: Rev. 1 schlug neue Evidenz-Gewichte vor —
  durch D1/D2 gegenstandslos; das Stärke-Modell bleibt 1.0.0.
- **O2**: Bracket-getrennte Verbreitungs-Profile (Mechanik über die
  Definition vorbereitet; 1.1.0 materialisiert `all` + je Commander
  gepoolt). Entscheidung erst bei Bedarf.
- **O3**: Quell-Zeitstempel füllt sich erst mit der nächsten
  Decklisten-Ernte (Bestandszeilen NULL). Zeitraum bis dahin ehrlich
  leer (§4.2) — Re-Harvest ist Owner-/Daten-Lane-Thema, nicht
  diese Lane.
