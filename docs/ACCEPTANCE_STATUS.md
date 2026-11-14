# Abnahmestatus zu Issue #1 — Stand 2026-11-13

Ehrliche Teilabnahme. **Issue #1 bleibt offen**, bis alle Punkte belegt sind.
Alle Zahlen stammen aus echten lokalen Läufen gegen den privaten Datenordner
(`MTG_DECKBUILDER_DATA`); keine privaten Sammlungsdaten in diesem Dokument
oder im Repository, nur aggregierte Zählwerte.

Korrekturstand 2026-11-13 (QA-1, Issue #19): Merge-/CI-Aussagen und die
Zählwerte zu EDHREC-Kartenseiten, Playgroup-Atlas und Spellbook an den
verifizierten Ist-Stand angeglichen.

Weitere Korrektur 2026-11-13 (Importer-A-Status): Der Importer-A-Echttest
ist seit 2026-11-12 bestanden; die zuvor als offen geführten Passagen
dazu sind unten an diesen Stand angeglichen.

## Daten-Erweiterung 1 + Tierlist (Branch `muse/data-expansion-1`, 2026-11-12)

Neue externe Datenquellen (manuell getriggert, lokal gecacht, mit
Provenienz in `external_snapshot`) und das Tierlist-System
(`tierlist/1.0.0`, Design in [TIERLIST_DESIGN](TIERLIST_DESIGN.md)
§10 mit allen Ergebniszahlen). Sammlungs-Universum ist ausschließlich
die v2-Sammlung (`MTG_Kartensammlung.xlsx`: 1.324 Identitäten /
1.815 Exemplare / 63 eligible Commander; Schwarze Box 1.153,
Foundation 285, Alen Lorwyn Box 377). Stand der Echtläufe:

- EDHREC-Kartenseiten 1.324/1.324 (1.323 AVAILABLE, 1 PARTIAL,
  0 NOT_FOUND); Spellbook-Kartenseiten 1.324/1.324 (257 AVAILABLE,
  1.067 NOT_FOUND, 3.926 Combo-Zeilen); Playgroup-Commander-Seiten
  63/63 (62 AVAILABLE, 1 PARTIAL mit dokumentiertem Grund);
  Scryfall-Druckfakten lokal abgeleitet (34.884 Identitäten).
- `compute-tiers` auf dem Echtdatenordner: 43.058 Zeilen
  (global S 5 / A 28 / B 114 / C 122 / D 1.052 / U 3; Kontext
  173 von 192 Commander×Bracket-Kontexten mit 41.734 bewerteten
  Karten). Alt-/Neu-Code auf identischer DB-Kopie byte-identisch
  (43.058/43.058 Zeilen); Live-Lauf reproduziert die Kopie exakt.
- Tests gesamt: **137 passed**, Ruff sauber. Wiederaufnehmbare
  Syncs überstehen transiente Netzwerkfehler pro Karte (Fix +
  Regressionstests, Commit `81bba20`); Tier-Compute per Batching
  von ~63 Min. auf ~14 Min. (Wandzeit unter Last) beschleunigt,
  Ergebnis unverändert (Commit `9593bf7`).
- Offen aus diesem Strang: Parser-Grund für die eine PARTIAL-
  Commander-Seite („Molten Man, Inferno Incarnate" — Seitentitel
  nennt den Commander nicht) ist ehrlich gespeichert, aber nicht
  behoben; Issue #1 bleibt bis zum formellen Abschluss (Phase 6)
  offen — der Importer-A-Echttest ist seit 2026-11-12 bestanden
  (siehe unten).

## Integration (Branch `muse/integration-1`, 2026-11-11)

Die beiden Entwicklungszweige sind zu einem Gesamtstand zusammengeführt:
QA-Fixes (`muse/qa-fixes-1`, Schema v2, 91 Tests) als Basis, Feature-Parität
(`muse/feature-parity-1`: Rollen-System, lokaler Bilder-Cache, Queries,
Datenbericht, Marks-UI, Deck-Liste) per Merge integriert. Konfliktlösung
inhaltlich (kein „ours/theirs“): `app.html` vereinigt beide Flow-Sets
(QA-Deck-Flows + Commander-Kontext, Paritäts-Rollenfilter/-Badges und
Marks-Buttons); die doppelte `/api/decks`-Route wurde auf die Schema-v2-
Variante (`decks.list_decks`, inkl. `latest_status`) vereinheitlicht,
deren Antwort zusätzlich die Paritäts-Felder `revisions`/`latest_hash`
führt. Schema v2 der QA-Fixes bleibt maßgeblich.

- Tests gesamt: **103 passed** (91 QA-Stand + 12 Paritäts-Tests, keine
  Überschneidungsverluste), Ruff mit Projekt-Konfiguration sauber,
  Import-Smoke und CLI-`--help` ok.
- Echtlauf-Smoke auf einer **Kopie** des Datenordners (Original per
  MD5-Prüfsumme unverändert): `rebuild-roles` klassifiziert 35.769
  Karten → 14.843 Claims (195 Profil-Karten); `data-report` zählt
  1.078/1.078 Identitäten, 1.089 Lots, 1.438 Exemplare; `inclusion`
  läuft (0 eigene Decks im Echtbestand → leere Liste); Deck-Validierung
  lehnt ein 41-Karten-Teildeck korrekt ab (nur Größenfehler), exakt 25
  eligible Commander; Zieh-Wahrscheinlichkeit P(≥2 Länder | 100/36) =
  0,7926 wie im Test fixiert.
- CI-Workflow im Integrations-Branch durch die kanonische Fassung
  ersetzt (Package-Erkennung, Ruff 0.17.4, Import-Smoke, pytest).

## Sammlung v2 — Echtimport und Sync-Erweiterung (2026-11-12)

Aktualisierte Sammlungsdatei des Owners (`MTG_Kartensammlung.xlsx`) als
strikte Obermenge des v1-Bestands (0 verschwunden, 0 Mengenänderungen)
mit drittem Standort **Alen Lorwyn Box**. Echtimport in den echten
Datenordner (vorab Backup `deckbuild.sqlite3.bak-collection-v2`),
bewusst **ohne die eine Zeile `Jace`** (Token Planeswalker — im
spielbaren Scryfall-Store per Design nicht enthalten; Originaldatei
unverändert, gefilterte Importkopie verwendet, Auslassung in
`docs/EXTERNAL_DATA.md` dokumentiert). DB-verifizierte Zielwerte:
**1.336 Lots / 1.324 Identitäten / 1.815 Exemplare** (Schwarze Box
1.153, Foundation 285, Alen Lorwyn Box 377 — Alt-Standorte
unverändert), **0 Lots mit `card_id IS NULL`**, eligible Commander
**25 → 63**, 0 needs_review. Sync-Erweiterung nur für die neuen
Einträge (Altbestand nicht erneut abgerufen): EDHREC **378/378
Ansichten für alle 63 Commander AVAILABLE**, Playgroup-Profile
**63/63 AVAILABLE** (11 davon ehrlich mit n=0 Spielen), Card Atlas
**1.324/1.324 versucht → 528 AVAILABLE, 701 PARTIAL, 95 NOT_FOUND,
0 BLOCKED** (Details: `docs/EXTERNAL_DATA.md`).

## QA-Fixes zu PR #3 (Branch `muse/qa-fixes-1`, 2026-11-11)

Alle Findings aus dem unabhängigen QA-Kommentar 6806751003 (3× P0,
7× P1) sind behoben — Details und Belege je Finding in
[QA_FIXES](QA_FIXES.md). Kurzstand:

- [x] **P0.1 Scryfall-Formate** — inhaltsbasierte Erkennung (Gzip-Magic
  + erstes Zeichen), Streaming für Roh-Array/.json/.json.gz/.jsonl/
  .jsonl.gz; beide Bulk-URI-Felder behandelt.
- [x] **P0.2 Entwurfs-Status** — Revisionen tragen `legal`/`draft`;
  Entwurf-Exporte sind als „ENTWURF — nicht legal“ gekennzeichnet,
  Legal-Export für Entwürfe verweigert (API-Feld + Header inklusive).
- [x] **P0.3 Frontend-Flows** — Speichern/Laden/Entfernen/Revisionen/
  Variante/Vergleich/Export im UI verdrahtet; Live-Browser-Workflow-
  Check (`scripts/browser_workflow_check.py`) komplett PASS.
- [x] **P1.4 card_id** — Primärimport lässt keine NULL-card_id mehr;
  Echtlauf verifiziert: 1.089/1.089 Lots mit card_id (deterministisch
  generiert, als generiert gekennzeichnet; Registry-Ersatz vorbereitet),
  1.078 Identitäten, Zahlen unverändert, Re-Import idempotent.
  Backup: `deckbuild.sqlite3.bak-qa` im Datenordner.
- [x] **P1.5 Mehrfach-Lots** — `lot_key`-Schema (Migration v1→v2);
  normalisierte Lots bleiben eigenständige Datensätze.
- [x] **P1.6 Partner-Regeln** — „Partner with X“ ist kein freies
  Partner; exakter Namensabgleich beidseitig; Background/Doctor
  positiv + negativ getestet.
- [x] **P1.7 Mengen-Validierung** — negativ/gebrochen/nicht-numerisch/
  nicht-endlich wird je Zeile abgelehnt (kein stilles Truncation).
- [x] **P1.8 Startreihenfolge** — README korrigiert (Scryfall zuerst);
  eindeutige Fehlermeldung bei leerem Scryfall-Store.
- [x] **P1.9 Commander-Kontext** — `/api/cards` wendet
  `commander_oracle_id` an (Legalität/Farbidentität/Pool je Karte);
  Favoriten/Notizen im UI bearbeitbar.
- [x] **P1.10 CI** — Workflow-Datei `.github/workflows/tests.yml`
  (pytest + Ruff 0.17.4 + Import-Smoke, mit Package-Erkennung); alle
  Schritte lokal nachgewiesen (103 Tests grün, Ruff sauber). Der
  zunächst durch die fehlende „Workflows“-Permission der GitHub-App
  blockierte Push und die zwischenzeitlich falsch abgelegte Datei
  (`.github/workflows/tests.yml/tests.yml`) sind behoben: Die
  Workflow-Dateien liegen auf main korrekt in `.github/workflows/`
  (vom Owner per Web-UI ersetzt, byte-identisch zur kanonischen
  Fassung); CI läuft auf jedem PR (Lint + pytest).
- Tests gesamt: **91 passed** (59 Bestand + 32 QA-Regressionstests);
  nach der Integration mit der Feature-Parität: **103 passed**.

## Erfüllt und belegt

- [x] **BUILD eigenständig lauffähig** — Paket `deckbuild_studio`, CLI
  `mtg-deckbuilder`, FastAPI-UI auf Port 8765, Server-Smoke-Test grün.
  Kein XMage/Forge, keine Simulation/PLAY, keine Monorepo-Imports.
  (Phase 1, PR #3, Head `aaee99e1`, gestapelt auf PR #2 — beide gemergt.)
- [x] **Primärbestand verlustfrei importiert** (Importer B, 7-spaltige XLSX
  direkt): 1.089 Zeilen / 1.078 Oracle-Identitäten / 1.438 Exemplare,
  Foundation 285 / Schwarze Box 1.153 getrennt, 0 ungelöst, Re-Import
  idempotent. `reserved=0` als `preliminary_zero_declared` gekennzeichnet.
  **v2-Update 2026-11-12:** Echtimport der aktualisierten Datei →
  1.336 Lots / 1.324 Identitäten / 1.815 Exemplare, dritter Standort
  Alen Lorwyn Box (377), ohne die Token-Zeile `Jace` (s. o.).
- [x] **Zweites Format getestet** — Importer C (generisches CSV/XLSX über
  explizites Spaltenmapping) und Importer A (normalisiertes Workbook)
  mit synthetischen Fixtures; Rollback-, Idempotenz- und Upsert-Tests.
  45 Tests insgesamt grün (Phase 1 + Phase 2).
- [x] **Alle legalen Commander des Primärbestands auswählbar** — exakt 25
  eligible, 0 needs_review (**v2 2026-11-12: 63 eligible, 0 needs_review**). Regel: commander-legal UND legendäre Kreatur
  auf der Vorderseite ODER ausdrückliche Erlaubnis. Negativfälle belegt:
  `Faithful Squire // Kaiso, Memory of Loyalty` (legendär nur Rückseite)
  und legendäre Planeswalker ohne Erlaubnis sind nicht eligible.
- [x] **Legale Decks aus eigenen Karten baubar** — Deckprüfung: 100 Karten
  inkl. Commander, Singleton nach oracle_id mit echten Ausnahmen,
  Farbidentität, physische Verfügbarkeit je Standort; Revisionen,
  Varianten, Vergleich, Export vorhanden. Datenbasierte Vorprüfung,
  keine Rules-Engine.
- [x] **EDHREC Core/Upgraded/Optimized integriert** — je Commander 6
  getrennte Snapshots (Stats + /decks, Brackets 2/3/4 nie vermischt).
  **Voll-Sync 2026-11-11: 150/150 Ansichten für alle 25 eligible
  Commander AVAILABLE**, plus ein Referenz-Commander (nicht im Bestand)
  mit Basis-Snapshots. **Erweiterung 2026-11-12: 378/378 Ansichten für
  alle 63 eligible Commander AVAILABLE.** Quellenbeschränkung dokumentiert: /decks liefert
  nur Metadaten (Datum/Preis/Tags/Typverteilung), keine vollständigen
  Decklisten; die Stats-Galerie liefert keine Gesamtzahl (Coverage
  `TOTAL_UNKNOWN`).
- [x] **Playgroup-Commander-Profile aufgelöst und geladen** — IDs über
  Playgroups eigene Autocomplete aus echter Quelle; **Voll-Sync
  2026-11-11: 25/25 Profile AVAILABLE** (Referenz-Commander, n=2.110;
  Tatyova 63, n=1.893; Ayli 2089, n=262; zwei Commander ehrlich mit
  n=0 Spielen). **Erweiterung 2026-11-12: 63/63 Profile AVAILABLE
  (11 mit n=0).** Quellenbeschränkung dokumentiert: Das öffentliche JSON
  enthält keine Archetyp-/Matchup-/Win-Condition-/Seat-/Mulligan-Felder.
- [x] **Daten lokal, versioniert, reproduzierbar gecacht** — Snapshots mit
  URL, Abrufzeit, Parser-Version (2.0.0), SHA-256, Status, Stichprobe;
  Parserwechsel invalidiert automatisch; manuelle CLI-Syncs
  (`sync-scryfall`, `import-inventory`, `sync-commander-data`,
  `sync-card-atlas`, `cache-status`, `cache-invalidate`); robots.txt
  geprüft, Rate-Limit ≥ 1 s, keine privaten Daten an externe Dienste.
- [x] **Keine privaten Daten in GitHub** — nur Code, Doku und synthetische
  Tests in PR #2/#3; `.gitignore`-Schutzregeln in beiden PRs enthalten.

## Offen / teilweise

- [x] **Card Atlas für alle 1.078 Karten** — Vollständiger Sync
  abgeschlossen (2026-11-11): **1.078/1.078 versucht → 425 AVAILABLE,
  582 PARTIAL (nur Basiszähler, davon viele `small_sample` n<25),
  71 NOT_FOUND (von der Quelle nicht geführt, stichprobenartig als
  echte 404 verifiziert), 0 BLOCKED.** Kein Kartenwert erfunden;
  PARTIAL/NOT_FOUND sind dokumentierte Datenlücken der Quelle.
  **Erweiterung 2026-11-12 (Sammlung v2): 1.324/1.324 versucht →
  528 AVAILABLE, 701 PARTIAL, 95 NOT_FOUND, 0 BLOCKED.**
- [x] **Deckbau End-to-End gegen den echten Bestand bewiesen**
  (2026-11-11, auf einer Datenkopie): Tatyova-Pool 417 Karten,
  100-Karten-Deck validiert legal, Export exakt 100 Zeilen,
  Variantenvergleich korrekt; Negativfälle (Banned-Karte Crusade,
  Farbverstoß, Singleton-/Verfügbarkeitsverstoß) werden mit präzisen
  Meldungen abgelehnt.
- [x] **Referenzdaten aus commander-playtest-lab übernommen** —
  Game-Changer-/Banned-Flags (53/83, 0 Diskrepanzen zu Scryfall) und
  strukturelle Rollenprofile (43 Karten der Sammlung, als
  Modellschätzung gekennzeichnet), siehe docs/REFERENCE_DATA.md.
- [x] **Upstream-Abgleich eingerichtet** — stündlicher Abgleich gegen
  commander-playtest-lab; erster Lauf 2026-11-11 mit drei Übernahmen
  (Playgroup-Qualitätswarnungen + JSON-LD-Provenienz aus #1202,
  EDHREC-Zähler-Validierung aus #1196, Markierungs-Import/-Export
  aus #1195), siehe docs/UPSTREAM_SYNC.md. 59 Tests grün.
- [x] **Feature-Parität zum alten Studio (BUILD)** — übernommen:
  Rollen-System (17er-Taxonomie, Claims mit Herkunft Heuristik/
  Strukturprofil; Echtlauf: 390 der 1.078 Sammlungskarten mit Rolle),
  lokaler Bilder-Cache (`/img/{oracle_id}`, nur cards.scryfall.io,
  UI mit Remote-Fallback), Own-Deck-Inklusion, Deck-Form +
  hypergeometrische Zieh-Chancen, counts-only Datenbericht,
  Marks-UI, Deck-Liste — siehe docs/FEATURE_PARITY.md. Bewusst nicht
  übernommen: PLAY/SIMULATE und Fremdkorpus-Maschinerie.
- [x] **Importer A gegen die echte 1.414er-XLSX** — Echttest am
  2026-11-12 bestanden; die echte normalisierte Datei
  (`MTG_Kartensammlung_NORMALISIERT.xlsx`) liegt in dieser Umgebung
  vor. Der 1.414er-Bestand bleibt separates Referenzprofil und
  wird nicht mit dem Primärbestand addiert.
- [x] **CI-Datei auf main korrigiert** — die zwischenzeitlich falsch
  unter `.github/workflows/tests.yml/tests.yml` abgelegte Workflow-
  Datei ist behoben; die Workflow-Dateien liegen auf main korrekt in
  `.github/workflows/` (Owner, Web-UI, byte-identisch zur kanonischen
  Fassung), CI läuft auf jedem PR (Lint + pytest).
- [x] **Merge-Stapel gemergt** — der Stapel #2 → #3 → #4 (Phase 2) →
  Integrations-PR (`muse/integration-1`: QA-Fixes + Parität) und alle
  Folge-Arbeit sind auf main: Gemergt sind die PRs #2–#6, #11–#15,
  #17 und #18; main-Head `e9616a09` (2026-11-13).

## Endstand 2026-11-13 (abends) — Bereinigung, Nachernte, Freigabe-Vorbereitung

- [x] **Referenz-Commander-Reste aus der Live-DB entfernt** — die
  Basis-Snapshots des nicht im Bestand geführten Commanders (Sync
  2026-11-11) sind gelöscht: 241 Karten-Stats, 9.824 Deck-Einträge,
  2 Snapshots, 7 Sync-Jobs und 8 Provenienz-Zeilen; EDHREC-Ansichten
  jetzt exakt **378** (63 Commander × 3 Brackets × 2), `source`-Zeilen
  danach 5.928, Integrität ok, Sicherung vor der Löschung im
  Datenordner.
- [x] **Alle Chulane-Referenzen aus dem Repo entfernt**
  (Owner-Entscheid 2026-11-13) — PR #28 gemergt; `grep -ri chulane`
  über den Repo-Baum = 0 Treffer, ebenso die alte Playgroup-ID;
  volle Suite auf dem PR-Baum 395 Tests grün. Das Alt-Exportformat
  wird nicht mehr gelesen.
- [x] **Nachernte der 11 leeren Kohorten eingearbeitet** — 3 Decks
  per Browser-Ernte (je 100 Karten, 0 ungemappt): Myojin of Night's
  Reach (Bracket 2), Vulture, Scheming Scavenger (Bracket 3), Venom,
  Evil Unleashed (Bracket 4), Plattform `browser:edhrec`, Parser
  `edhrec-rsc-browser-harvest/1.0.0`. Ernte-Korpus jetzt **9.215
  Decks AVAILABLE**, gefüllte Kohorten **181/189** (+3 `source`-Zeilen,
  jetzt 5.931); die übrigen 8 Kohorten sind bei EDHREC selbst decklos
  (quellenbelegt leer). Ernte-Werkzeug gegen das aktuelle
  EDHREC-Format repariert (PR #30, RSC-Flight-Parser).
- [x] **TopDeck-Endzählung** — Sammlungsabdeckung per SQL-Recount:
  **464 Karten mit Win-Rate, 331 mit Conversion** (DB maßgeblich;
  siehe docs/TOPDECK.md).
- [x] **Tier-Bestand unverändert belegt** — `tier_assignment` je
  Modellversion 634.202 Zeilen; global 1.1.0 S5/A28/B109/C134/
  D1.048/U1, global 1.2.0 S4/A29/B104/C163/D1.024/U1.
- [ ] **DB-Diät + Status-Vervollständigung + Release** — laufen
  (Payload-Kompression/Migration, fehlende Status-Sektionen für
  Spellbook/Decklisten, danach erste vollständige Version).

## Tierlist-Entfernung (Owner-Entscheid 2026-11-14, Issue #59)

Die Tierliste (Modelle `tierlist/1.0.0`–`1.2.0`, Evidenz-Tier,
„Verbreitung (gezählt)", Universen) wurde per Owner-Entscheid
vollständig aus dem Tool entfernt: Seite/UI, Endpunkte
(`/api/tiers*`, `/api/verbreitung`), CLI (`compute-tiers`),
Settings-Schlüssel `tierlist.*`, Schema-Erzeugung der Tabelle
`tier_assignment` für neue DBs und die drei Design-Dokumente
(`TIERLIST_DESIGN.md`, `TIERLIST_CPL_ADAPTATION.md`,
`TIERLIST_1_2_DESIGN.md`). Die Abschnitte oben bleiben als datierte
Historie stehen. Die Tier-DATEN bleiben erhalten: Archiv der
`tier_assignment`-Zeilen (1.268.404) als Einzeldatei in Google
Drive (Issue #58); der Drop der Bestandstabelle + finales VACUUM
auf der Live-DB erfolgt separat nach Archiv-Verifikation.
Unberührt: Deckbau, Sammlung, Inclusion-Werte und der kanonische
Decklisten-Nenner — dessen Zählung (Inhalts-Dedupe, Kohorten) lebt
jetzt in `decklists.canonical_selection_summary` mit identischen
Ergebnissen (Vorher/Nachher-Vergleich auf echter DB-Kopie im PR zu
Issue #59 belegt).
