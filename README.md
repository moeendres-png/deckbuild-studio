# Deckbuild Studio

Standalone Commander-Deckbuilder aus dem BUILD-Modul von [commander-playtest-lab](https://github.com/moeendres-png/commander-playtest-lab), Quellrevision `10e663de0d274b3f22adf93c03b89d59bb01356c` (11.11.2026).

## Ziel

Lokale MTG-Kartensammlung einlesen, Karten per Scryfall-Oracle-ID normalisieren, Commander wählen und ausschließlich den eigenen verfügbaren Commander-legalen Kartenpool im Browser nutzen. Favoriten, Notizen, Filter, Kartenbilder, Listen, Entwürfe, Revisionen, Vergleiche und Exporte bleiben im BUILD-Bereich.

## Start

Python 3.12+:

```bash
python -m venv .venv
pip install -e ".[test]"
mtg-deckbuilder import-inventory "/privat/MTG_Kartensammlung.xlsx"
mtg-deckbuilder import-scryfall "/privat/default-cards.jsonl.gz"
mtg-deckbuilder normalization-report
mtg-deckbuilder serve
```

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
