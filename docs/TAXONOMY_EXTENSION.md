# Taxonomie-Erweiterung 1.1.0 — Zählung und Entscheidungsprotokoll

Stand: 2026-11-12 · Lane `muse/taxonomy-ext-1` · alle Zahlen: Läufe auf einer
**Kopie** der echten DB (Integrität geprüft); die echte DB wurde nicht beschrieben.

## Methode

Auftrag von M: Die Funktions-Taxonomie wird **datenbasiert** erweitert,
nicht auf Verdacht. Grundlage ist eine Vollzählung des offiziellen
Scryfall-Bulks `oracle_tags` (Datei `oracle-tags-20261112100040.jsonl.gz`,
Bulk-Stand 2026-11-12T10:00:40Z, SHA-256
`54fe9777d6a767c8d934966688568ae90cb3547678d9b62212788d468c054ea7`, 4.604 Tags)
gegen die Sammlung (1.324 Oracle-Identitäten mit physischen Lots).
Gezählt wurde je Tag die **Subtree-Vereinigung** (Tag + alle Nachfahren) —
exakt die Menge, die ein Tagger-Sync als Claims schreiben würde.
Die vollständige Zähltabelle aller 4.604 Tags steht in
`docs/TAXONOMY_TAG_COUNTS_2026-11-12.md`.

**Entscheidungsregel.** Ein Tag wird neue Kategorie, wenn
(a) Sammlungs-Abdeckung ≥ 13 Karten (≈ 1 %),
(b) funktional eigenständig gegenüber den bestehenden 24 Kategorien
    (Teilmengen-Verhältnisse per Schnittmengen-Zählung belegt) und
(c) deckbaulich eine Funktion (kein Art-/Flavor-/Kreaturtyp-Tag —
    die Typ-Ebene existiert separat).
204 Tags erreichen ≥ 13 Sammlungs-Karten; für jeden steht unten das
Urteil mit Begründung. Zusätzlich wurden die im Vorfeld namentlich
diskutierten Tags unterhalb der Schwelle einzeln geprüft (Anhang).

## Übernahmen (Taxonomie 24 → 30)

| Kategorie | Label DE | Tagger-Tag(s) | Sammlung (Tagger-Subtree) | Heuristik | Neu abgedeckte Karten* |
|---|---|---|---:|---|---:|
| evasion | Evasion | `evasion` + `gives-evasion` (Zusatz-Tag) | 232 (205 + 38, Schnitt 11) | ja (2.2.0) | 102 |
| combat_trick | Kampftrick | `combat trick` | 79 | ja, nur Instant-Faces (2.2.0) | 28 |
| mana_sink | Mana-Senke | `mana sink` | 63 | **nein — bewusst Tagger-only** | 24 |
| tapper | Tappen (Kontrolle) | `tapper` | 25 | ja (2.2.0) | 16 |
| theft | Kontrollübernahme | `theft` | 17 | ja (2.2.0) | 8 |
| copy_effects | Kopier-Effekte | `copy` | 15 | ja (2.2.0) | 5 |

* Karten der Sammlung, die vor der Erweiterung in **keiner** Schicht eine
Kategorie trugen und durch diese Kategorie erstmals eine erhalten (gegen die
Vereinigungsmenge aller Schichten gezählt; Überschneidungen der neuen
Kategorien untereinander sind im Gesamtdelta unten bereinigt).

Begründungen im Einzelnen:

- **evasion** (205 Karten, größte gemessene Lücke): Evasions-Kreaturen und
  -Grants sind eine eigenständige Deckbau-Funktion (durchschlagende
  Angreifer); beste Schnittmenge zu einer Alt-Kategorie nur 23/205
  (card_advantage). Der Zusatz-Tag `gives-evasion` (38, davon 27 außerhalb
  des Basis-Tags) bildet die Grant-Seite — gleiches Muster wie `hatebear`
  bei `stax`, Claims tragen den echten Tag-Namen.
- **combat_trick** (79): Instant-schnelle Kampfinteraktion (Pump/Protection
  im Kampf) ist ein eigener Deckbau-Slot; `giant-growth` (19) ist per
  Schnittmenge Teilbaum von `combat trick` und damit mit abgedeckt.
- **mana_sink** (63): wiederholbar nutzbare Mana-Ausgänge sind der klassische
  Gegenpart zu Ramp-Überschuss. **Keine Heuristik-Regel**: Eine wiederholbar
  nutzbare aktivierte Fähigkeit mit Manakosten ist aus dem Oracle-Text nicht
  trennscharf ableitbar — ein Regex würde auf tausende beliebige aktivierte
  Fähigkeiten feuern. Die Kategorie bleibt ehrlich Tagger-only.
- **tapper** (25): Tap-Effekte auf fremde Permanents (Tempo/Kontrolle,
  z. B. Icy Manipulator) — Gegenstück zu `bounce` in derselben Granularität;
  größte Schnittmenge nur 4/25 (removal).
- **theft** (17): Kontrollübernahme als Funktion. Der Ober-Tag
  `control changing effects` (20) wurde **nicht** gemappt: Seine 3
  zusätzlichen Karten sind Weggabe-/Tausch-Effekte (Bazaar Trader,
  Harmless Offering, Wishclaw Talisman) — keine Diebstahl-Semantik.
- **copy_effects** (15): Effekt-Kopien (Spruch- und Permanent-Kopien) als
  eigene Effektklasse; klein, aber gemessen eigenständig (größte
  Schnittmenge 3/15).

Die sechs Kategorien stehen am **Ende** der Taxonomie-Reihenfolge:
Die Primär-Kategorie (Deck-Gruppierung) bereits kategorisierter Karten
ändert sich dadurch nie; nur bisher kategorie-lose Karten gewinnen eine
Gruppe.

## Heuristik-Regeln 2.2.0 — Quantifizierung vor Übernahme

Jede neue Regel wurde store-weit gezählt und ihre Sammlungs-Treffer
einzeln gegen den Kartentext geprüft (Projekt-Regel seit 2.0.0):

| Regel | Store-Treffer | Sammlungs-Treffer | Handprüfung |
|---|---:|---:|---|
| evasion (Keyword-Zeile / can't-be-blocked / Team-Grant) | 4.963 | 185 | OK — u. a. Fear-Aura, Levitation, Profane Command (Fear-Modus) korrekt |
| combat_trick (Pump/Grant, nur Instant) | 171 | 11 | OK — Giant Growth, Stave Off, Tel-Jilad Defiance u. a., 0 Fehlgriffe |
| tapper (tap target/all …) | 477 | 19 | OK — Icy Manipulator, Vedalken Certarch, Naya Charm (Tap-Modus) u. a. |
| theft (gain control / you control enchanted …) | 206 | 6 | OK — Act of Treason, Goatnap, Nicol Bolas, Planeswalker u. a.; Aura-Formeln über die zweite Alternative |
| copy_effects (copy target spell… / token that's a copy) | 469 | 9 | OK — Reverberate, Rite of Replication, Rootborn Defenses u. a. |
| mana_sink | — | — | **keine Regel** (s. o.) |

Falsch-negative Treffer sind wie überall in der Heuristik akzeptiert
(z. B. erfasst die Theft-Regel 6 der 17 Tagger-Karten); falsch-positive
werden durch die engen Muster vermieden.

## Verifikation (DB-Kopie, Bulk-Sync + Rebuild mit neuem Code)

| Schicht / Maß | Vorher | Nachher |
|---|---:|---:|
| Tagger-Claims (Store gesamt) | 38.057 | 50.942 |
| Tagger: Sammlungs-Karten mit ≥ 1 Claim | 797 | 1.002 |
| Heuristik: Sammlungs-Karten mit ≥ 1 Claim | 737 | 871 |
| Strukturprofile | 44 | 44 |
| **Vereinigung aller Schichten** | **901/1.324 (68,0 %)** | **1.065/1.324 (80,4 %)** |
| Ohne jeden Claim | 423 | 259 |

Alle 24 Alt-Kategorien behalten exakt ihre Sammlungs-Zähler (removal 281,
card_advantage 198, lifegain 132, card_draw 150, ramp 101,
token_production 99, sacrifice_outlet 88, recursion 65, card_selection
64, tutor 59, protection 55, mill 52, cantrip 44, land_ramp 43,
bounce 38, board_wipe 36, anthem 34, discard 30, mana_dork 27,
mana_rock 26, counterspell 20, stax 13, graveyard_hate 12,
flicker 6); die neuen Kategorien stehen bei evasion 232, combat_trick
79, mana_sink 63, tapper 25, theft 17, copy_effects 15 (jeweils Vereinigung
aller Schichten, identisch zu den gezählten Tagger-Subtrees). Der volle
Tagger-Lauf meldet `AVAILABLE` (30 Tags AVAILABLE, `stax`/`token` weiter
ehrlich `NOT_FOUND`) und schreibt die Geprüft-Zeilen der Schicht.

Versionen: Taxonomie `categories/1.1.0`, Heuristik `oracle-heuristic/2.2.0`,
Tagger-Search `scryfall-tagger-search/1.2.0`, Tagger-Bulk
`scryfall-tagger-bulk/1.1.0`.

## Entscheidungsprotokoll — alle 204 Tags ≥ 13 Sammlungs-Karten

Spalten: Sammlung = Subtree-Karten in der Sammlung · Neu = Karten, die ohne
diesen Tag in keiner Schicht eine Kategorie hätten (gegen die alte
Vereinigungsmenge gezählt) · Größte Schnittmenge mit einer Alt-Kategorie
(nur Tagger-Mengen, Sammlungs-restringiert).

| Tag | Sammlung | Neu | Größte Schnittmenge | Urteil | Begründung |
|---|---:|---:|---|---|---|
| triggered-ability | 530 | 131 | card_advantage 106 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| cycle | 385 | 103 | card_advantage 76 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| activated-ability | 360 | 89 | removal 58 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| card-names | 300 | 87 | removal 73 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| spot-removal | 255 | 0 | removal 255 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| single-target-instant/sorcery | 242 | 37 | removal 125 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| removal-creature | 237 | 0 | removal 237 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| flavors-of-vanilla | 218 | 86 | card_advantage 28 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| evasion | 205 | 91 | card_advantage 23 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| alliteration | 160 | 51 | card_advantage 31 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| burn | 135 | 6 | removal 116 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| hate | 127 | 27 | removal 51 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| pure-draw | 117 | 0 | card_advantage 117 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-burn | 112 | 0 | removal 112 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| burn-creature | 104 | 0 | removal 104 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| repeatable-crime | 102 | 28 | removal 50 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| removal-planeswalker | 96 | 0 | removal 96 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| type-errata | 96 | 42 | removal 16 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| burn-player | 89 | 6 | removal 70 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| french-vanilla | 82 | 62 | lifegain 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| combat-trick | 79 | 28 | protection 17 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| staple-with-set's-mechanic | 79 | 15 | removal 27 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| virtual-vanilla | 79 | 15 | card_advantage 18 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| single-english-word-name | 68 | 10 | removal 28 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| unique-type-line | 66 | 22 | removal 10 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| burn-planeswalker | 65 | 0 | removal 65 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-destroy | 65 | 0 | removal 65 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| typal | 65 | 23 | anthem 9 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| typal-creature | 65 | 23 | anthem 9 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| death-trigger | 64 | 10 | card_advantage 25 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| mana-sink | 63 | 24 | removal 13 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| cheaper-than-mv | 62 | 14 | recursion 13 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| tutor-to | 59 | 0 | tutor 59 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| virtual-french-vanilla | 59 | 9 | lifegain 12 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| repeatable-removal | 58 | 0 | removal 58 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| thingfall | 58 | 27 | card_advantage 8 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| gains-pp-counters | 56 | 35 | card_advantage 4 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| repeatable-card-advantage | 56 | 0 | card_advantage 56 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| cycle-land | 55 | 18 | lifegain 14 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| type-errata-addition | 55 | 22 | removal 11 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| blue-effect | 54 | 0 | removal 27 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| peek | 54 | 3 | mill 24 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| cast-trigger | 53 | 14 | card_advantage 15 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| attack-trigger | 52 | 22 | card_advantage 8 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| burn-any | 52 | 0 | removal 52 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| burn-battle | 52 | 0 | removal 52 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-artifact | 52 | 0 | removal 52 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| drawback | 51 | 31 | removal 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| sacrifice-self | 51 | 1 | removal 17 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| multiple-targets | 50 | 11 | removal 26 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| removal-enchantment | 50 | 0 | removal 50 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| library-manipulation | 49 | 0 | mill 25 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| repeatable-lifegain | 48 | 0 | lifegain 48 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| mill-self | 47 | 0 | mill 47 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| tapland | 47 | 17 | lifegain 14 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| black-effect | 46 | 1 | discard 30 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| repeatable-draw | 46 | 0 | card_advantage 46 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| gives-mm-counters | 45 | 16 | removal 15 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| top-deck-manipulation | 45 | 0 | mill 25 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| noncreature-typal | 44 | 13 | card_advantage 8 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| power-boost-to-all | 44 | 8 | anthem 15 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| more-expensive-than-mv | 43 | 11 | removal 14 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| peek-library | 43 | 0 | mill 24 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| repeatable-pp-counters | 42 | 26 | lifegain 3 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| tutor-land | 42 | 0 | tutor 42 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| utility-land | 42 | 8 | lifegain 14 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| mana-producer | 40 | 0 | ramp 40 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| cast-trigger-you | 39 | 12 | card_advantage 9 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| draw-engine | 39 | 0 | card_advantage 39 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| namesake-spell | 39 | 13 | removal 8 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| death-trigger-self | 38 | 6 | card_advantage 15 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| gives-evasion | 38 | 17 | protection 7 | **AUFGENOMMEN** | Zusatz-Tag der Kategorie evasion (Grant-Seite, wie hatebear bei stax) |
| protects-self | 38 | 8 | protection 4 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| additional-cost | 37 | 7 | removal 14 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| attacking-matters-self | 37 | 15 | card_advantage 7 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| counters-matter | 37 | 14 | card_advantage 5 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| intervening-if-clause | 37 | 11 | card_advantage 7 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| lands-matter | 37 | 11 | lifegain 7 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| cycle-dual-land | 36 | 12 | lifegain 12 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| discard-outlet | 36 | 1 | card_advantage 24 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| dual-land | 36 | 12 | lifegain 12 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| exile-self | 36 | 4 | recursion 13 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| repeatable-token-generator | 36 | 0 | mill 4 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| power-matters | 35 | 12 | removal 11 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| repeatable-pure-draw | 35 | 0 | card_advantage 35 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| gives-pp-counters | 34 | 16 | card_advantage 6 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| opponent-loses-life | 34 | 12 | lifegain 12 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| pinger | 34 | 2 | removal 24 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| removal-toughness | 34 | 0 | removal 34 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| tutor-to-hand | 33 | 0 | tutor 33 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| type-addition-phyrexian | 33 | 14 | removal 6 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| draft-signpost | 32 | 5 | removal 8 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| gives-castable-from-nonhand | 32 | 2 | card_advantage 21 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| group-slug | 32 | 7 | lifegain 10 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| synergy-artifact | 32 | 14 | sacrifice_outlet 8 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| tutor-land-basic | 32 | 0 | tutor 32 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| alternative-cost | 31 | 6 | removal 9 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| creaturefall | 31 | 18 | card_advantage 4 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| hand-disruption | 31 | 1 | discard 30 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| saboteur | 31 | 8 | card_advantage 13 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| bottomless-mana-sink | 30 | 15 | removal 6 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| gives-castable-from-exile | 30 | 2 | card_advantage 19 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| multiple-bodies | 30 | 0 | mill 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| repeatable-creature-tokens | 30 | 0 | anthem 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| modal | 29 | 4 | removal 19 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| removal-equipment | 28 | 0 | removal 28 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| type-change | 28 | 11 | removal 6 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| protects-creature | 27 | 0 | protection 27 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| refund | 27 | 0 | ramp 25 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| removal-battle | 27 | 0 | removal 27 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| landfall | 26 | 8 | removal 6 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| mana-value-matters | 26 | 3 | removal 9 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| recursion-creature | 26 | 0 | recursion 26 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-aura | 26 | 0 | removal 26 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-spacecraft | 26 | 0 | removal 26 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| removal-vehicle | 26 | 0 | removal 26 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| toughness-boost-to-all | 26 | 3 | anthem 12 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| attacking-matters | 25 | 14 | card_advantage 4 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| reanimate | 25 | 0 | recursion 25 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| repeatable-sacrifice-outlet | 25 | 0 | sacrifice_outlet 25 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| sacrifice-outlet-creature | 25 | 0 | sacrifice_outlet 25 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| tapper | 25 | 16 | removal 4 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| tapper-creature | 25 | 16 | removal 4 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| activate-from-hand | 24 | 5 | tutor 10 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| delayed-trigger | 24 | 5 | recursion 9 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| hate-color | 24 | 5 | removal 8 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| removal-bounce | 24 | 0 | bounce 24 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| surveil | 24 | 0 | mill 24 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| tutor-to-battlefield | 24 | 0 | tutor 24 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| recursion-self | 23 | 0 | recursion 23 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| regrowth | 23 | 0 | card_advantage 23 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| activate-from-graveyard | 22 | 2 | recursion 16 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| gives-flying | 22 | 11 | card_advantage 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| out-of-color-token | 22 | 0 | mill 6 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| remove-counters | 22 | 7 | protection 3 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| remove-counters-you | 22 | 7 | protection 3 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| tap-outlet | 22 | 6 | removal 5 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| burst-draw | 21 | 0 | card_advantage 21 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| inverted-effects | 21 | 0 | lifegain 19 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| self-replacement-effect | 21 | 4 | removal 7 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| tutor-land-to-battlefield | 21 | 0 | tutor 21 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| castable-from-graveyard | 20 | 4 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| castable-from-nonhand | 20 | 4 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| control-changing-effects | 20 | 10 | recursion 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| discount-self | 20 | 8 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| multi-removal | 20 | 0 | removal 20 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| synergy-instant | 20 | 5 | ramp 5 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| synergy-sorcery | 20 | 5 | ramp 5 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| tap-fuel-creature | 20 | 6 | removal 3 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| bottom-deck-manipulation | 19 | 0 | card_advantage 7 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| burn-with-set's-mechanic | 19 | 1 | removal 18 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| drain-life | 19 | 0 | lifegain 19 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| giant-growth | 19 | 11 | lifegain 2 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| red-effect | 19 | 0 | card_advantage 17 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| removal-exile | 19 | 0 | removal 19 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| cards-in-graveyard-matter | 18 | 3 | mill 5 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| impulse | 18 | 0 | card_advantage 18 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| poison-mechanics | 18 | 12 | card_advantage 2 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| removal-nonland | 18 | 0 | removal 18 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| rescue | 18 | 0 | bounce 18 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| untapper | 18 | 11 | card_advantage 2 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| characteristic-defining-ability | 17 | 7 | removal 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| counter-fuel | 17 | 4 | ramp 3 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| martyr | 17 | 0 | removal 8 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| mini-refund | 17 | 0 | ramp 16 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| scales-with-power | 17 | 4 | removal 9 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| theft | 17 | 8 | recursion 3 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| adds-multiple-mana | 16 | 0 | ramp 15 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| cost-ignorer | 16 | 1 | card_advantage 10 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| enlarge | 16 | 7 | removal 2 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| gains-flying | 16 | 10 | graveyard_hate 1 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| removal-land | 16 | 0 | removal 16 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| symmetrical | 16 | 1 | card_advantage 5 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| untapper-creature | 16 | 11 | removal 2 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| copy | 15 | 5 | removal 3 | **AUFGENOMMEN** | aufgenommen (s. Übernahme-Tabelle) |
| disenchant/naturalize | 15 | 0 | removal 15 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| egg | 15 | 0 | card_advantage 10 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| mm-counter-cost | 15 | 3 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| poisonous | 15 | 10 | card_advantage 2 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| prevent-blocker | 15 | 8 | removal 6 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| scry | 15 | 0 | card_advantage 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| unique-mana-cost | 15 | 4 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| block-trigger | 14 | 5 | removal 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| cda-subtype | 14 | 5 | removal 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| changeling | 14 | 5 | removal 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| color-change | 14 | 4 | card_advantage 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| enters-in-company | 14 | 0 | removal 2 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| fun-ruling | 14 | 3 | removal 4 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| gives-haste | 14 | 7 | cantrip 1 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| hate-set-mechanic | 14 | 4 | removal 4 | Abgelehnt — heterogen | Sammel-Tag über mehrere Funktionen, keine einzelne Funktion |
| life-payment | 14 | 2 | card_advantage 10 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| regrowth-creature | 14 | 0 | card_advantage 14 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| synergy-white | 14 | 3 | anthem 3 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| bear-with-set's-mechanic | 13 | 8 | protection 2 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| cycle-mono-land | 13 | 3 | lifegain 2 | Abgelehnt — Land-Form | Land-Formklasse; Länder sind die Typ-Ebene, keine Funktions-Kategorie |
| damage-prevention | 13 | 3 | protection 6 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| firebreathing | 13 | 7 | removal 3 | Abgelehnt — Sicht/Umbenennung | Sicht, Teilmenge-nah oder Umbenennung einer bestehenden Kategorie |
| gainland | 13 | 0 | lifegain 13 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| gains-haste | 13 | 4 | recursion 9 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| gives-trample | 13 | 5 | cantrip 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |
| lifegain-matters | 13 | 4 | lifegain 6 | Abgelehnt — Thema/Mechanik | Themen-/Synergie-Achse oder Mechanik-Familie, keine Funktion; Auffindbarkeit über Typ-/Subtyp-/Keyword-Facetten |
| removal-sacrifice | 13 | 0 | removal 13 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| rescue-creature | 13 | 0 | bounce 13 | Abgelehnt — Teilmenge | per Schnittmenge ⊆ einer bestehenden Kategorie (gemessen) |
| type-addition-human | 13 | 5 | removal 3 | Abgelehnt — Form/Struktur | Form-, Struktur-, Kosten- oder Trivia-Eigenschaft, keine Deckbau-Funktion |

## Anhang — namentlich diskutierte Tags unterhalb der Schwelle

| Tag | Sammlung | Global | Urteil | Begründung |
|---|---:|---:|---|---|
| sneak (Alias: *cheat into play*) | 4 | 297 | Abgelehnt — unter Schwelle (a) | Die Cheat-into-play-Funktion existiert im Bulk nur unter diesem Label/Alias; 4 Sammlungs-Karten < 13. |
| cheat-death | 9 | 322 | Abgelehnt — unter Schwelle (a) | Automatische Reanimation; zusätzlich Teilmenge-nah zu recursion. |
| free-cast-another | 9 | 437 | Abgelehnt — unter Schwelle (a) | Gratis-Zauber-Grants; 9 < 13. |
| clone | 1 | 77 | Abgelehnt — unter Schwelle (a) | Nur 1 Sammlungs-Karte (Omni-Changeling); Permanent-Kopien laufen über `copy` (copy_effects) mit. |
| extra turn | 0 | 65 | Abgelehnt — unter Schwelle (a) | Der Tag existiert global (65 Karten), die Sammlung enthält **keine** Extra-Turn-Karte. |

Die übrigen ~4.400 Tags unter 13 Sammlungs-Karten scheitern sämtlich an
Regel (a); ihre Zähler stehen in der vollständigen Zähltabelle.
