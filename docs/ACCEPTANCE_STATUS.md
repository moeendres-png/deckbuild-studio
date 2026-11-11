# Abnahmestatus zu Issue #1 — Stand 2026-11-11

Ehrliche Teilabnahme. **Issue #1 bleibt offen**, bis alle Punkte belegt sind.
Alle Zahlen stammen aus echten lokalen Läufen gegen den privaten Datenordner
(`MTG_DECKBUILDER_DATA`); keine privaten Sammlungsdaten in diesem Dokument
oder im Repository, nur aggregierte Zählwerte.

## Erfüllt und belegt

- [x] **BUILD eigenständig lauffähig** — Paket `deckbuild_studio`, CLI
  `mtg-deckbuilder`, FastAPI-UI auf Port 8765, Server-Smoke-Test grün.
  Kein XMage/Forge, keine Simulation/PLAY, keine Monorepo-Imports.
  (Phase 1, PR #3, Head `aaee99e1`, gestapelt auf PR #2 — beide ungemergt.)
- [x] **Primärbestand verlustfrei importiert** (Importer B, 7-spaltige XLSX
  direkt): 1.089 Zeilen / 1.078 Oracle-Identitäten / 1.438 Exemplare,
  Foundation 285 / Schwarze Box 1.153 getrennt, 0 ungelöst, Re-Import
  idempotent. `reserved=0` als `preliminary_zero_declared` gekennzeichnet.
- [x] **Zweites Format getestet** — Importer C (generisches CSV/XLSX über
  explizites Spaltenmapping) und Importer A (normalisiertes Workbook)
  mit synthetischen Fixtures; Rollback-, Idempotenz- und Upsert-Tests.
  45 Tests insgesamt grün (Phase 1 + Phase 2).
- [x] **Alle legalen Commander des Primärbestands auswählbar** — exakt 25
  eligible, 0 needs_review. Regel: commander-legal UND legendäre Kreatur
  auf der Vorderseite ODER ausdrückliche Erlaubnis. Negativfälle belegt:
  `Faithful Squire // Kaiso, Memory of Loyalty` (legendär nur Rückseite)
  und legendäre Planeswalker ohne Erlaubnis sind nicht eligible.
- [x] **Legale Decks aus eigenen Karten baubar** — Deckprüfung: 100 Karten
  inkl. Commander, Singleton nach oracle_id mit echten Ausnahmen,
  Farbidentität, physische Verfügbarkeit je Standort; Revisionen,
  Varianten, Vergleich, Export vorhanden. Datenbasierte Vorprüfung,
  keine Rules-Engine.
- [x] **EDHREC Core/Upgraded/Optimized integriert** — je Commander 6
  getrennte Snapshots (Stats + /decks, Brackets 2/3/4 nie vermischt),
  Probeläufe Chulane (Referenz), Tatyova, Ayli: alle 18 Ansichten
  AVAILABLE, plus Chulane-Basis (Stats + Decks) = 20 Snapshots.
  Quellenbeschränkung dokumentiert: /decks liefert nur Metadaten
  (Datum/Preis/Tags/Typverteilung), keine vollständigen Decklisten;
  die Stats-Galerie liefert keine Gesamtzahl (Coverage `TOTAL_UNKNOWN`).
- [x] **Playgroup-Commander-Profile aufgelöst und geladen** — IDs über
  Playgroups eigene Autocomplete aus echter Quelle: Chulane 2143
  (n=2.110), Tatyova 63 (n=1.893), Ayli 2089 (n=262), alle AVAILABLE.
  Quellenbeschränkung dokumentiert: Das öffentliche JSON enthält keine
  Archetyp-/Matchup-/Win-Condition-/Seat-/Mulligan-Felder.
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
- [ ] **Importer A gegen die echte 1.414er-XLSX** — bisher nur synthetisch
  verifiziert; die echte normalisierte Datei liegt in dieser Umgebung
  nicht vor. Der 1.414er-Bestand bleibt separates Referenzprofil und
  wird nicht mit dem Primärbestand addiert.
- [ ] **Phase 2 als PR** — lokal committet (Phase 2 `a4c8564`,
  Referenzdaten `8558ec5`, Upstream-Übernahmen `caed49e` auf
  `muse/phase2-external-data`); PR auf Basis von PR #3 folgt nach
  dessen Merge bzw. mit Owner-Go als weiterer Stapel.
- [ ] **Kartenbilder** — aktuell per Scryfall-URI verlinkt, noch kein
  lokaler Image-Cache.
- [ ] **Merge von PR #2 und PR #3** — Reihenfolge: erst #2, dann #3.
