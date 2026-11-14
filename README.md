# Deckbuild Studio

Standalone Commander-Deckbuilder aus dem BUILD-Modul von [commander-playtest-lab](https://github.com/moeendres-png/commander-playtest-lab), Quellrevision `10e663de0d274b3f22adf93c03b89d59bb01356c` (11.11.2026).

## Ziel

Lokale MTG-Kartensammlung einlesen, Karten per Scryfall-Oracle-ID normalisieren, Commander wählen und ausschließlich den eigenen verfügbaren Commander-legalen Kartenpool im Browser nutzen. Favoriten, Notizen, Filter, Kartenbilder, Listen, Entwürfe, Revisionen, Vergleiche und Exporte bleiben im BUILD-Bereich.

## Start

Python 3.12+:

**Startreihenfolge wichtig:** Zuerst der Scryfall-Katalog (die
Namensauflösung der Sammlung braucht ihn), danach die Sammlung:

```bash
python -m venv .venv
pip install -e ".[test]"
mtg-deckbuilder sync-scryfall
# alternativ offline: mtg-deckbuilder import-scryfall "/privat/default-cards.jsonl.gz"
mtg-deckbuilder import-inventory "/privat/MTG_Kartensammlung.xlsx"
mtg-deckbuilder normalization-report
mtg-deckbuilder serve
```

Ein Sammlungsimport bei leerem Scryfall-Store bricht mit einer
eindeutigen Fehlermeldung ab („zuerst import-scryfall/sync-scryfall
ausführen"), statt alle Namen als unauflösbar zu melden. Der
Scryfall-Import erkennt das Dateiformat am Inhalt (JSON-Array, `.json`,
`.json.gz`, `.jsonl`, `.jsonl.gz`), nicht am Dateinamen.

Öffnen: http://127.0.0.1:8765

Der Python-Cache für den gewählten Commander liegt mit Datenbank und Kartenbildern in einem lokalen, privaten Ordner (`MTG_DECKBUILDER_DATA`; Standard `~/.local/share/mtg-collection-deckbuilder`). Der lokale `sync-scryfall`-Befehl lädt lediglich den **öffentlichen** Scryfall-Bulk-Katalog; private Sammlungen und Decklisten werden nicht übertragen.

Siehe [Normalisierung](docs/NORMALIZATION_CONTRACT.md) und [Issue #1](https://github.com/moeendres-png/deckbuild-studio/issues/1).

**Nicht enthalten:** XMage, Spielsimulationen, Partieansichten und Simulator-/Pilot-Code. Import, Farben, Legalität und Singleton sind datenbasierte Vorprüfungen, keine vollständige Rules-Engine.

Private XLSX-Dateien, Mengen und Lagerorte gehören **nicht** in dieses Git-Repository.

## Phase 1 (lokal verifiziert, 11.11.2026)

Eigenständiges Paket `src/deckbuild_studio/`, CLI wie oben beschrieben.
Zusätzlich: `mtg-deckbuilder commanders`, `cache-status`,
`sync-commander-data <oracle_id>` und `sync-card-atlas` (Phase-2-Jobs,
Status `NOT_FETCHED` — es werden keine externen Daten erfunden).
Importer: (A) normalisiertes Workbook (Tabs 01/02/03/05 …), (B) die
7-spaltige Primärdatei `Kartensammlung_Foundation_Schwarze_Box.xlsx`
(Profil `foundation-schwarze-box`), (C) generisches CSV/XLSX über
explizites Spaltenmapping (JSON, `--mapping`).
Details: [MIGRATION_NOTES](docs/MIGRATION_NOTES.md),
[Normalisierung](docs/NORMALIZATION_CONTRACT.md).
Tests: `pip install -e ".[test]" && pytest` (synthetische Fixtures,
keine privaten Daten).

## Karten-Kategorien (Funktionen / Typen / Subtypen)

Jede Karte ist erstklassig kategorisiert und danach filter-/sortierbar:
Typ-Fakten je Kartenfläche (Supertypen/Typen/Subtypen + Scryfall-Keywords,
deterministisch aus dem lokalen Bulk abgeleitet) und Funktions-Kategorien
in drei getrennten Schichten (Oracle-Text-Heuristik, Strukturprofile,
Scryfall Tagger über die offizielle Search-API) — jede Schicht mit
Geprüft-Nachweis pro Karte. CLI: `derive-card-types`, `rebuild-roles`,
`sync-tagger`, `category-report`; UI/API: Filter für Typ/Subtyp/Keyword/
Kategorie je Schicht + Sortierung. Details: [CATEGORIES](docs/CATEGORIES.md).

## Änderung 2026-11-14: Tierliste entfernt

Per Owner-Entscheid (Issue #59) enthält Deckbuild Studio keine
Tierliste mehr (keine Stufen-Anzeigen, keine Modell-/Signal-
Einstellungen, kein `compute-tiers`). Die Tier-Daten sind als
Archiv in Google Drive erhalten (Issue #58). Deckbau, Sammlung
und alle übrigen Datenschichten sind unverändert.
