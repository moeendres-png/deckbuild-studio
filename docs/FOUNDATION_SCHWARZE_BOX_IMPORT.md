# Foundation / Schwarze Box — Importvertrag v1

**Primärer aktueller Sammlungs-Snapshot:** `Kartensammlung_Foundation_Schwarze_Box.xlsx` (lokal; **nicht committen**). Der frühere 1.414er-Bestand ist ein separates Referenzprofil, nicht ein automatisch zu addierender Teilbestand.

## Quelle und Mapping

Ein Tabellenblatt `Kartensammlung`, 7 Spalten: `Kartenname`, `Anzahl`, `Standort`, `Farbidentität`, `Manakosten`, `Kartentyp`, `Kartentext`.

Das maschinenlesbare Profil liegt unter `config/collection_profiles/foundation_schwarze_box.json`. Der XLSX-Importer soll sowohl diese Quelle direkt als auch ein normalisiertes Zwischenformat mit `01_CARD_IDENTITY`, `02_PHYSICAL_LOTS`, `03_LOCATIONS` und `05_INVENTORY_CURRENT` unterstützen.

Lokaler Quellenabgleich (Scryfall Bulk 2026-11-09): 1.089 Quellzeilen, **1.078 eindeutige Oracle-Karten**, 1.438 Exemplare, 2 Standorte, 0 Ambiguitäten und 0 fehlende Matches. **Alle 1.078 Oracle-IDs** kommen im früheren normalisierten Bestand vor: bestehende `card_id` wiederverwenden, aber physische Bestände **nicht blind doppelt zählen**. Foundation/Schwarze Box sind Quell-Standorte; keine stillschweigende Gleichsetzung mit früheren anderen Boxbezeichnungen.

## Commander und Sonderfälle

**25 Einzelcommander-Kandidaten** nach Scryfall-Stand 2026-11-09: `legalities.commander=legal` und legendäre Kreatur **auf der Commander-fähigen Vorderseite**, bzw. ausdrückliche Commander-Erlaubnis. `Faithful Squire // Kaiso, Memory of Loyalty` ist **nicht** als Einzelcommander geeignet (legendär nur rückseitig), obwohl die Kartenidentität im Format legal ist. Partner-/Background-Sonderfälle zusätzlich gesondert prüfen.

Die UI soll alle gültigen eigenen Commander dynamisch anbieten. Kein Hardcoding eines festen Commanders.

## Folgescans / neue Karten

- Wiederholter Import mit `collection_id=foundation-schwarze-box`.
- Globale Kartenidentität nach Oracle-ID; physischer Lot-Schlüssel nach (`collection_id`, `oracle_id`, `Standort`).
- Bei gleicher Karte am gleichen Standort Mengen **aktualisieren**, nicht addieren; neue Karten/Standorte ergänzen.
- Fehlende Zeilen **nicht automatisch als gelöscht interpretieren**. Snapshot-Ersetzung oder tatsächliches Entfernen nur explizit nach Audit.
- Quellenhash, Zeitstempel, geänderte Zeilen und alte/neue Mengen protokollieren.
- Mengen im Ausgang sind als gemeldete Zahlen bekannt, **Reservierungen, physische Druckversionen, Foil und Zustände jedoch nicht**. Ausgangsannahme `0 reserved` nur sichtbar als unbestätigt; keine fälschliche Provenienz behaupten.

## Öffentliche Datenjobs

Für die 25 Commander: 150 EDHREC-Bracket-Ziele (`core`, `upgraded`, `optimized` je Statistik/`decks`) und 25 Playgroup-Commander-ID-Auflösungen. Für die 1.078 Karten: Card-Atlas-Synchronisationsjobs. **1.253 Aufträge, zunächst NOT_FETCHED/NEEDS_ID_RESOLUTION**. Die tatsächlich aufgelösten IDs und Slugs müssen verifiziert werden. Nur zulässige, rate-limitierte, ausdrücklich anstoßbare Datenabrufe; nie private Bestandsmengen oder Lagerorte senden.

## Akzeptanz

1. Original-XLSX und normalisierte Arbeitsmappe ergeben denselben 1.078er-Oracle-Bestand und 1.438 gemeldete Exemplare an 2 Standorten.
2. Alle 25 Kandidaten können als Commander ausgewählt werden, sofern keine besondere Rechts-/Datenprüfung dagegensteht; False-Positive Faithful Squire explizit ausgeschlossen.
3. Zweiter Import mit neuen Karten/Mengen aktualisiert den gleichen Bestand ohne Verdoppelung.
4. Deckbau, Varianten, Export und Quellenstatus im Browser.
5. Git enthält ausschließlich Adapter/Profil/Tests mit synthetischen Daten, niemals die konkrete Sammlung.
