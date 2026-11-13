# Feature-Parität zum Studio-Deckbuilder in commander-playtest-lab

Stand: 2026-11-11. Upstream-Inventar aus `src/commander_lab/studio/`
( lokaler Clone, `origin/main` = `12af1c1b2`; der per Connector
verifizierte Head `39ffb336ea` mit #1202 ist in `docs/UPSTREAM_SYNC.md`
bereits abgeglichen — #1202 ändert an den hier inventarisierten
BUILD-Modulen nichts Grundsätzliches) plus den in `UPSTREAM_SYNC.md`
geprüften PR-Heads (#1194/#1195/#1196/#1177). Status: **vorhanden**
(gleichwertig), **übernommen** (in diesem Lauf implementiert),
**teilweise**, **nicht übernommen** (mit Begründung), **PLAY** (per
Projektvertrag ausgeschlossen).

| Feature | Upstream-Modul | Status bei uns | Entscheidung / Begründung |
|---|---|---|---|
| SQLite-Store, Provenienz je Datensatz | store.py | vorhanden | Eigenes Schema (source/sha256/Parser-Version), gleichwertige Disziplin. |
| Scryfall-Bulk-Import (Oracle-Ebene, Layouts übersprungen) | catalog.py `import_scryfall_oracle` | vorhanden | `scryfall.py`, plus `sync-scryfall`. |
| Sammlung ↔ Scryfall verknüpfen | catalog.py `link_collection` | vorhanden | Importer A/B/C mit Namensauflösung, Fehlerreport statt Raten. |
| Multipart-/Korpus-Import (externe Deck-Korpora) | catalog.py `import_cohort`, importers.py | nicht übernommen | Kein externes Deck-Korpus in Issue #1; unser Multipart ist das normalisierte Workbook (Importer A). |
| Fakt-Differenzen bei neuem Bulk (fact_differences) | catalog.py | nicht übernommen | Nice-to-have; Scryfall-Sync ersetzt Oracle-Fakten idempotent. Als spätere Option vermerkt. |
| Legal Pool je Commander | queries.py `legal_pool` | vorhanden | `decks.legal_pool` (Farbidentität, Legalität, physische Verfügbarkeit). |
| Korpus-Inklusion (hits/Nenner je Karte) | queries.py `corpus_inclusion` | **übernommen, generalisiert** | Kein Fremdkorpus vorhanden → Inklusion über die **eigenen Decks** (nur jeweils neueste Revision), `queries.own_deck_inclusion`, CLI `inclusion`, `/api/stats/inclusion`. Nenner = Deckzahl, keine Prozent-Erfindung bei 0 Decks. |
| Rollen-Taxonomie (17 Rollen) + Origin-Disziplin | roles.py | **übernommen, generalisiert** | `roles.py`: Taxonomie + Tagger-Labels 1:1; Claims lokal abgeleitet (s. u.) statt Tagger-Live-Fetch. |
| Rollen-Fetch über Scryfall-Tagger-API je Farbidentität | roles.py `fetch_role_file`/`import_roles` | nicht übernommen (Pipeline) | Live-Fetch fremder Tag-Dateien widerspricht dem lokalen, manuell syncbaren Datenmodell; die *Anspruchsstruktur* (Rolle × Herkunft) ist übernommen. |
| Rollen aus importierten Strukturprofilen | (Upstream: Tagger-Audit #1177, ohne Import) | **übernommen** | Unsere 195 importierten Profile (43 Sammlungskarten) werden als Claims mit Origin `STRUCTURAL_PROFILE` eingemischt — als Modellschätzung gekennzeichnet, wörtliche Rollen (auch außerhalb der 17er-Taxonomie). |
| Heuristische Rollen aus Oracle-Text | roles.py (Origin `ORACLE_TEXT_REVIEW` = manuelle Prüfung) | **übernommen, ehrlich abgewertet** | Origin `ORACLE_TEXT_HEURISTIC`: konservative Regex-Heuristik über lokalem Oracle-Text, überall als Heuristik beschriftet — keine manuelle Prüfung, keine Beobachtung. |
| Deck-Rollenzählung | builder.py `deck_roles` | **übernommen** | `roles.deck_role_counts`, in `/api/decks/validate` + UI. |
| Deck-Form (Typen, Kurve, Pips) | builder.py `deck_shape` | **übernommen** | `queries.deck_shape`, in Validierung + UI. |
| Zieh-Wahrscheinlichkeiten (hypergeometrisch) | builder.py `draw_probabilities` | **übernommen** | `queries.draw_probabilities` (Startblatt + bis Zug 3). |
| Lokaler Kartenbilder-Cache | images.py | **übernommen** | `images.py`: Fetch nur von `cards.scryfall.io`, atomares Schreiben, Cache neben der DB im privaten Datenordner; `/img/{oracle_id}`, CLI `fetch-images`. Nur Front (unser Store hält eine `image_uri` je Karte); `cached_image_by_name`/`public_card` sind Engine-Spielbetrieb → nicht übernommen. |
| Datenbericht (nur Zähler, „unbekannt ≠ 0", Rollen-Fingerabdruck) | data_report.py | **übernommen, generalisiert** | `report.py` (`deckbuild-data-report-1`), CLI `data-report`, `/api/data-report`; Fingerabdruck über unseren `card_role`-Claims; NOT_MEASURED-Liste an unsere Quellen angepasst. |
| Deck-Validierung, Revisionen, Hash, Export, Vergleich | decks.py, builder.py `diff_lists` | vorhanden | Phase 1; Vergleich = `compare_revisions`. |
| Deck-Liste (Decks + neueste Revision) | builder.py `list_decks`, web `/api/decks` | **übernommen** | `GET /api/decks` ergänzt. |
| Freie Entwürfe je Deck/Branch (Drafts) | builder.py `read/write/drop_draft`, web Draft-Routen | teilweise | Varianten laufen bei uns über Revisionen mit `parent_revision_id` (inhaltsadressiert). Freie Branch-Entwürfe ohne Revision wären ein zweites Zustandsmodell — nicht übernommen, Revisionsmodell deckt den Issue-#1-Umfang. |
| Markierungen setzen (Favorit/Ausschluss/Notiz) | builder.py `set_mark`, web `PUT /cards/{id}/mark` | vorhanden (Backend), **UI übernommen** | `POST /api/marks` existierte; jetzt Buttons (★/Ausschließen/Notiz) in der Sammlungsansicht. |
| Marks-Import/-Export | PR #1195 `marks.py` | vorhanden | Bereits im Upstream-Abgleich #1 übernommen (`marks.py`). |
| Pool-Filter nach Rolle/Favorit/Verfügbarkeit | web `/api/pool`, app.js | **übernommen (Rolle)** | `/api/pool?role=…` + Rollenfilter-Auswahl und Rollen-Badges im UI; Favorit/Verfügbarkeit sind bereits Pool-Felder bzw. Pool-Kriterium. |
| Karten-Detailansicht (Kohorten/Evidenz) | builder.py `card_detail`, web `/api/cards/{id}` | teilweise | `/api/cards` (Besitz/Box/Marks/Referenz/Rollen) + `/api/external/card` (Playgroup) decken die BUILD-Fragen; Kohorten-Detail ist korpusgebunden. |
| Pool-Karten mit Evidenz je Kohorte | builder.py `pool_cards`, sources.py (Coverage/Gap-Matrix, Spellbook-Combos) | nicht übernommen | Kohorten/Gap-Matrix/Combo-Datenbank sind CPL-Korpus-Maschinerie ohne Gegenstück in Issue #1; unsere Evidenzschichten sind EDHREC/Playgroup/Referenz mit eigener Provenienz. |
| Co-Occurrence (Kartenpaare im Korpus) | builder.py `card_cooccurrence` | nicht übernommen | Braucht ein Deck-Korpus; eigene Decks sind dafür zu wenige (Inklusion stattdessen). |
| Kohorten-Formen/-Größen | builder.py `cohort_shapes/cohort_sizes` | nicht übernommen | Korpus-Kohorten, kein Äquivalent. |
| Simulationen je Karte / neutrale Boards | builder.py `card_simulations`, `card_neutral_boards` | PLAY | SIMULATE — per Vertrag ausgeschlossen. |
| Prefilter für Simulationslisten | builder.py `prefilter_lists` | PLAY | Dient der Simulations-Pipeline. |
| Spiele/Partie/Launch (XMage) | games.py, play.py, launch.py, web `/api/games`, `/api/table` | PLAY | Ausgeschlossen (BUILD-only). |
| EDHREC-Snapshot-Import aus Dateien | sources.py, importers.py (Capture-Batches) | teilweise | Unser Adapter fetcht selbst mit SHA-256/Abrufzeit/Parser-Version je Snapshot (siehe UPSTREAM_SYNC zu #1196); ein zusätzlicher Datei-Import würde Fetch-Provenienz umgehen — nicht übernommen. |
| Quellen-Inventar als JSON | sources.py `source_inventory_payload` | vorhanden (äquivalent) | `/api/external/status` + `cache-status` mit Quelle/Datum/Status je Snapshot. |
| KI-Stil/Spielplan je Deck (#1173, auf main nach Basis) | builder/web (studio) | nicht übernommen | Spielplan/Stil sind PLAY-Vorbereitung (Piloten), kein BUILD-Feature. |

## Übernommen in diesem Lauf (Branch `muse/feature-parity-1`)

- `roles.py` — Rollen-Taxonomie, Heuristik-Claims + Profil-Claims mit
  Herkunft, `rebuild-roles` (CLI), Rollen in `/api/cards` + `/api/pool`
  (inkl. `role`-Filter), `/api/roles`, Deck-Rollenzählung.
- `images.py` — lokaler Bilder-Cache, `/img/{oracle_id}`,
  CLI `fetch-images`.
- `queries.py` — Own-Deck-Inklusion, Deck-Form, Zieh-Wahrscheinlichkeiten.
- `report.py` — counts-only Datenbericht, CLI `data-report`,
  `/api/data-report`.
- UI: Markierungs-Buttons, Rollen-Badges/-Filter, lokale Bilder mit
  Remote-Fallback, Form/Rollen/Zieh-Chancen in der Deckprüfung.
- `GET /api/decks` (Deck-Liste).

Echtlauf (Kopie des echten Datenordners): `rebuild-roles` klassifiziert
35.769 Scryfall-Karten → 14.843 Claims (14.512 Heuristik + 331 Profil);
von den 1.078 Sammlungskarten tragen 390 mindestens eine Rolle
(u. a. removal 108, card_draw 97, lifegain 89, ramp 49, mana_rock 13,
land_ramp 20, tutor 6, board_wipe 4 — Heuristik, keine Beobachtung).
