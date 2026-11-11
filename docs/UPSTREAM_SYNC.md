# Upstream-Abgleich mit commander-playtest-lab

Deckbuild Studio ist eine BUILD-only-Ausgründung des Studio-Moduls aus
`commander-playtest-lab`. Dort wird parallel weiterentwickelt (Claude).
Dieses Dokument protokolliert je Abgleich: was sich upstream geändert
hat, was wir übernommen haben und was bewusst nicht — mit Begründung.
Übernahmen erfolgen nur, wenn sie zu unseren Verträgen passen:
Provenienz je Datensatz, Statusmodell NOT_FETCHED/PARTIAL/BLOCKED/
AVAILABLE, keine erfundenen Werte (fehlend ≠ 0), Kohorten-Trennung,
keine privaten Daten an externe Dienste, kein PLAY/Engine-Code.

## Stand / Wasserzeichen (dieser Abgleich)

- Geprüft am: 2026-11-11 23:10 CET
- Unsere Migrationsbasis: upstream main `12af1c1b2`
- Upstream main-Head geprüft: **`39ffb336ea`** (per GitHub-Connector
  verifiziert; das lokale Clone-Objekt lag zum Prüfzeitpunkt noch
  nicht vor, der Abgleich erfolgte über Connector-Reads und
  Blob-SHA-Vergleiche der Verzeichnislistings)
- Geprüfte offene PRs (Head-SHAs per Connector):
  #1195 `6fe2722276`, #1196 `443fc57106`, #1194 `fa50b3d762`,
  #1177 `6d4c5f0b9a`, #1201 `7755f9673f` (nur zur Kenntnis),
  #1188 `089d8c2f58`, #1203 `0fccabcaa6` (neu, nur Kenntnis)

## Abgleich 2026-11-11 23:10 CET — main unverändert (`39ffb336ea`), keine Übernahme

| Upstream-Änderung | Datum | Kurzbeschreibung | Entscheidung | Begründung / unsere Umsetzung |
|---|---|---|---|---|
| #1203 (offen, neu, Head `0fccabcaa6`) „M5 multi-game batch simulation series with Wilson intervals and telemetry (Refs #1170)" | 2026-11-11 | Mehrspiel-Simulationsserien: Batch-Runner in Kindprozessen, deterministische Seeds, Wilson-Intervalle, Per-Card-Telemetrie, Tabellen `simulation_run`/`simulation_card`, API `/api/simulations/*`, CLI `simulate`, Tests `test_studio_simulations.py` | **Nicht übernommen (nur Kenntnis)** | Reines SIMULATE-Gebiet; Deckbuild Studio ist BUILD-only und enthält bewusst keine Simulations-/Engine-Anbindung. |
| #1196 (offen, Head `6325c1083d` → `443fc57106`) | 2026-11-11 | Nur Main-Merge + Fix-Commit `ec28ec72b7c1`: Test-Assertion „unlisted card observation count" 7 → 6 in `test_studio_edhrec_snapshot_import.py` (Zählung der Observation-Zeilen ihres Snapshot-Imports) | **Nicht übernommen** | Betrifft ausschließlich ihre Event-/Snapshot-Import-Maschinerie, die wir bereits nicht übernommen haben (URL-Allowlist in `edhrec_capture_proof.py` ist fest auf Chulane verdrahtet — am neuen Head gelesen). Unsere übernommene fail-closed Zähler-Validierung in `edhrec.py` (Zähler ≥ 0, num ≤ den, endliches lift/synergy, `dropped_invalid`) ist von der Zählkorrektur unberührt. |
| #1194 (offen, Head `5f8fe9a77c` → `fa50b3d762`) | 2026-11-11 | Nur Main-Merge + `edc96d8da7df`: SHA-256-Angabe der `source_multiset.csv` an den wahren Wert angeglichen | **Nicht übernommen** | Weiterhin nur Provenienz-Archiv ihres eingefrorenen V5-Korpus (Chulane); kein gleichartiger Offline-Korpus bei uns. SHA-je-Snapshot ist bei uns bereits abgedeckt. |
| #1177 (offen, Draft, Head `8ffec8bd5a` → `6d4c5f0b9a`) | 2026-11-11 | Nur `6d4c5f0b9a`: „comply with WS223 environment identity and ruff standards" (CI-/Lint-Konformität des Audit-Skripts) | **Nicht übernommen** | Weiterhin Einweg-Audit ihrer 63 Karten ohne Datenübernahme; keine inhaltliche Änderung. Tagger-Gegenabgleich bleibt spätere Option. |

- Keine weiteren Änderungen: main-Head weiterhin `39ffb336ea`; offene
  PRs #1195/#1201/#1188 mit unveränderten Head-SHAs. Keine
  Code-Übernahme in diesem Lauf, keine Testläufe nötig (nur
  Doku-Eintrag).
- Hinweis: `get_pull_request_files` wird vom GitHub-MCP-Server aktuell
  nicht angeboten und `get_commit` liegt außerhalb der geprüften
  Lese-Tools — PR-Änderungen wurden über Branch-Commitlisten und
  gezielte `get_file_contents`-Reads (Verzeichnislistings, Testdateien,
  `edhrec_capture_proof.py` am neuen Head) verifiziert.

## Abgleich 2026-11-11 22:10 CET — main unverändert (`39ffb336ea`), kein neuer Commit

| Upstream-Änderung | Datum | Kurzbeschreibung | Entscheidung | Begründung / unsere Umsetzung |
|---|---|---|---|---|
| #1188 (offen, Draft, Head `089d8c2f58`) „docs(data): objective TAM/Chulane source index and privacy-safe agent handoff" | 2026-11-11 | Reiner Provenienz-Index als JSON (`data/provenance/commander_studio_drive_sources_20261111.json`, Schema `commander-studio-private-drive-source-index/v1`) + Handoff-Doku für drei Fremdkorpora: Chulane 994, TAM 91, TAM/Chandra 381 (Drive-URLs, behauptete SHA-256 je Quelldatei, Zeilenzahlen, Rollen, `source_manifest_automatic_import`-Flags). Keine Rohdaten, keine Codeänderung. | **Nicht übernommen** | Fremdkorpus (Chulane/TAM), kein Bezug zu unserer eigenen Sammlung — kein Chulane-Fokus per Vertrag. Die SHA-256-Angaben sind ausdrücklich nicht unabhängig nachgeprüft (`independent_sha256_recomputed_in_this_export: false`, „claims copied from frozen Drive manifests") — eine Übernahme würde unserem Provenienz-Vertrag (jede Angabe belegt, nichts behauptet) widersprechen. Mehrere Einträge tragen `source_manifest_automatic_import: true`, was unserem manuellen Sync-Vertrag widerspricht. Die Idee „Quellenindex mit SHA + Zeilenzahl" ist bei uns durch SHA-256 je Live-Snapshot + Parser-Version bereits abgedeckt. |

- Keine weiteren Änderungen: main-Head weiterhin `39ffb336ea`; offene
  PRs #1195/#1196/#1194/#1177/#1201 mit unveränderten Head-SHAs
  (nur Aktivität ohne neue Commits: #1195 `updated_at` 20:07 UTC,
  #1201 19:50 UTC). Keine Code-Übernahme in diesem Lauf, keine
  Testläufe nötig (nur Doku-Eintrag).
- Maschinenlesbares Wasserzeichen für den regelmäßigen Abgleich:
  `~/workspace/goals/deckbuild-studio/hidden_files/upstream-sync-state.json`
  (liegt außerhalb des Repos, wird bei jedem Abgleich fortgeschrieben)

## Abgleich 2026-11-11 — main 12af1c1b2 → 39ffb336ea + offene PRs

| Upstream-Änderung | Datum | Kurzbeschreibung | Entscheidung | Begründung / unsere Umsetzung |
|---|---|---|---|---|
| #1202 (main `39ffb336ea`) „capture, normalize, and integrate Playgroup Card Atlas" | 2026-11-11 | Neues Modul `playgroup_parser.py` (strukturierte Atlas-Extraktion inkl. JSON-LD-Dataset, Top-Commander, Final Zones), eigene Tabelle `playgroup_card_atlas` (Schema v8), Offline-Dateiimport `import-playgroup-atlas` (HTML/JSON/JSONL/TSV), Builder-/UI-Einbindung | **Teilweise übernommen** | Parser-Ideen übernommen (siehe unten). Nicht übernommen: eigenes Spalten-Schema + Offline-Importweg — unser Snapshot-Modell (Roh-Payload .gz + SHA-256 + Parser-Version + geparste Felder) deckt dieselben Felder ab; ein Dateiimport würde die Fetch-Provenienz umgehen. |
| ↳ Qualitätswarnungen des Parsers (On-Curve-Nachrechnung, Brought-Zähler-Abgleich; exakte Quellwerte bleiben, Diskrepanzen werden gemeldet) | 2026-11-11 | Parser vergleicht berichtete Prozentwerte mit Zähler/Nenner und „Times Brought" mit dem Funnel-Header | **Übernommen** | `playgroup.py`: `quality_warnings` im Parse-Ergebnis (Schwelle >2 pp wie upstream), Werte werden nie still korrigiert. 2 Tests. |
| ↳ JSON-LD-Dataset-Provenienz + Lizenz/Attribution (CC BY 4.0, „Playgroup.gg") + Disclosure „keine kausale Kartenstärke" | 2026-11-11 | Parser liest identifier/dateModified/temporalCoverage/license aus dem JSON-LD-Block der Kartenseite | **Übernommen** | `playgroup.py`: `dataset`, `license` (Seitenangabe, sonst „CC BY 4.0"), `attribution` je Kartendatensatz. Korrelations-Disclosure führten wir bereits (`semantics`/`interpretation`). |
| ↳ Slug-Regel Apostroph → Bindestrich (`Drach'Nyen` → `drach-nyen`); unser `slugify` entfernt das Apostroph (`drachnyen`) | 2026-11-11 | Abweichende Slug-Normalisierung | **Nicht übernommen** | Unser Slug wurde live an 649+ Karten verifiziert; jede geparste Seite wird gegen den erwarteten Kartennamen geprüft — ein falscher Slug wird NOT_FOUND, nie falsche Daten. Regelwechsel mitten im laufenden Atlas-Sync würde die Konsistenz brechen. Bei einem künftigen Voll-Re-Sync erneut prüfen. |
| ↳ Status-Schwelle n≥30 → OK, darunter PARTIAL | 2026-11-11 | Upstream klassifiziert Stichproben mit fixer Schwelle 30 | **Nicht übernommen** | Wir nutzen Playgroups eigene, auf der Seite ausgewiesene Schwellen (volle Charts ab n≥25, `small_sample`-Markierung) — näher an der Quellensemantik. |
| ↳ `format_mode`-Dimension (Standard `multiplayer`) in der Atlas-Tabelle | 2026-11-11 | Datenmodell unterscheidet Spielmodi | **Nicht übernommen** | Wir rufen nur die Standard-Multiplayer-Ansicht ab; eine Dimension ohne zweiten Modus wäre spekulative Struktur. Bei einem echten zweiten Modus nachrüsten. |
| #1196 (offen, Head `6325c1083d`) „Fix EDHREC provenance: echte HTTP-Zeitgrenzen und immutable Event-Importe" | 2026-11-11 | Neues `edhrec_capture_proof.py`: fail-closed Validierung externer Capture-Manifeste (Event-Fingerabdruck aus URL+Startzeit+SHA, SHA-/Größen-/Zeitabgleich, HTTP-200-Nachweis, Zählerplausibilität `num_decks ≤ potential_decks`, endliche lift/synergy), Import als unveränderliche Events; CI-Capture-Workflow | **Teilweise übernommen** | Die Zähler-/Wertevalidierung ist in unseren Live-Parser übernommen: `edhrec.py` verwirft Recs mit negativen/nicht-numerischen Zählern, Zähler > Nenner oder nicht-endlichem synergy/lift und zählt sie als `dropped_invalid` (fail-closed statt still speichern). 2 Tests. Nicht übernommen: Manifest-/Event-Maschinerie und CI-Workflow — upstream fest auf Chulane-URLs (`json.edhrec.com/.../chulane-teller-of-tales`) und extern erfasste Batches verdrahtet; wir fetchen selbst live und speichern je Snapshot SHA-256 + Abrufzeit + Parser-Version. |
| #1195 (offen, Draft, Head `6fe2722276`) „Evidenz je Karte (Tierliste ohne Wertung) und Import eigener Markierungen" | 2026-11-11 | `evidence.py`: Evidenz-Schichten je Karte (Fakt/Deck/Game/Combo/Simulation strikt getrennt, fehlend ≠ 0, Tier grundsätzlich UNRATED ohne validiertes Modell; eigene Markierungen sind nie ein Stärke-Signal). `marks.py`: Import eigener Markierungen (favorite/excluded/note) aus `studio-marks-1` und aus dem Export des alten HTML-Studios (fav/notes; wish/variants/tierOverride werden gezählt-ignoriert, tierOverride bewusst nicht importiert), Merge-Semantik, All-or-nothing, Zählreport | **Teilweise übernommen** | Marks-Import übernommen und angepasst: neues `marks.py` + CLI `import-marks`/`export-marks`. Anpassung an unser Identitätsmodell: Auflösung oracle_id → lokale card_id → exakter Kartenname (nur eindeutig); Merge nur erwähnte Schlüssel; All-or-nothing; Report nur Zähler. Ehrliche Einschränkung: Der Alt-Export schlüsselt über die fremden card_ids des alten Studios — ohne deren ID-Registry (private 1.414er-Datei) zählen solche Einträge als unaufgelöst statt geraten zu werden. Eigenes Exportformat `deckbuild-marks-1` (Round-trip getestet). 4 Tests. Nicht übernommen: `evidence.py` als Code — seine Politik (fehlend ≠ 0, kein Tier aus Häufigkeit/Inclusion, Markierungen nie Stärke-Signal) ist bereits unser Vertrag; die Implementierung hängt an upstream-Korpus/Combos/ALL_DECKS (Chulane-zentriert, PLAY-nahe Schichten), die es bei uns bewusst nicht gibt. Hinweis: Die in #1195 enthaltene `playgroup_parser.py` ist byte-identisch zu #1202 (gleiche Linie, bereits oben abgeglichen). |
| #1194 (offen, Head `5f8fe9a77c`) „EDHREC V5: 963/963 Quellenprüfsummen, Offline-Deckstatistik" | 2026-11-11 | Provenienz-Archiv eines festen EDHREC-Korpus (Manifest + Multiset-CSV mit 963 Quellen, SHA-Prüfsummen, Verify-Skript, Offline-Deckstatus-Gate) | **Nicht übernommen** | Korpus-spezifisches Datenset (deren Chulane-/V5-Korpus, ZIP-Archiv). Die Idee „Prüfsumme je Quelle" ist bei uns durch SHA-256 je Live-Snapshot bereits abgedeckt; es gibt keinen gleichartigen Offline-Korpus zu verifizieren. |
| #1177 (offen, Draft, Head `8ffec8bd5a`) „Audit: 63 Karten gegen offiziellen Scryfall Tagger prüfen (ohne ACTIVE-Import)" | 2026-11-11 | Einmaliges Audit-Skript + Workflow: Rollen von 63 Foto-Karten gegen Scryfall-Tagger-Tags prüfen, bewusst ohne Import in den aktiven Bestand | **Nicht übernommen** | Einweg-Audit für deren konkrete 63 Karten, per Design ohne Datenübernahme. Als Idee vermerkt: Ein Tagger-Gegenabgleich wäre eine mögliche spätere Validierung unserer 43 strukturellen Rollenprofile (Schätzungen) — erst sinnvoll, wenn ein konkreter Qualitätszweifel oder ein größerer Rollenbestand vorliegt. |
| #1201 (offen, Head `7755f9673f`) „Engine-Preflight mit Java-Prüfung, Pin und JAR-Prüfsumme (Refs #1172)" | 2026-11-11 | Studio-Start/Engine-Bereitstellung (XMage, Java) | **Nicht übernommen (nur Kenntnis)** | PLAY/Engine-Bereich; Deckbuild Studio ist BUILD-only und enthält bewusst keine Engine-Anbindung. |

## Umsetzungsstand dieses Abgleichs

- Übernommen in: `src/deckbuild_studio/playgroup.py` (Qualitätswarnungen,
  JSON-LD/Lizenz/Attribution), `src/deckbuild_studio/edhrec.py`
  (fail-closed Stat-Validierung, `dropped_invalid`),
  `src/deckbuild_studio/marks.py` (neu) + CLI `import-marks`/`export-marks`.
- Parser-IDs dokumentarisch angehoben (`playgroup/2.1.0`,
  `edhrec-rsc/2.1.0`); die gemeinsame Snapshot-Parser-Version bleibt
  unverändert, weil alle Änderungen additiv bzw. verwurfseitig sind —
  bestehende Snapshots (inkl. des laufenden Atlas-Syncs) bleiben gültig
  und kein unnötiger Re-Fetch wird ausgelöst.
- Tests: 59 passed (51 Bestand + 8 neu: 2 EDHREC-Validierung,
  2 Playgroup-Warnungen/Dataset, 4 Marks).
- Bewusst offen: Slug-Regel-Differenz (Apostroph) bei künftigem
  Voll-Re-Sync erneut prüfen; Tagger-Gegenabgleich der Rollenprofile
  als mögliche spätere Validierung.
