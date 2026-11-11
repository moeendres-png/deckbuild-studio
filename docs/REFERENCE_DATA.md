# Referenzdaten aus commander-playtest-lab

Deckbuild Studio übernimmt **kartenspezifische Referenzdaten** aus dem
Schwesterprojekt `commander-playtest-lab` (dort committed unter
`data/cards/`). Die Übernahme erfolgt per Dateipfad über den CLI-Befehl
`mtg-deckbuilder import-reference-data`; die JSON-Dateien selbst werden
**nicht** in dieses Repository kopiert. Jeder importierte Datensatz
trägt Provenienz: Quellprojekt, Dateiname, Schema-Version, `data_as_of`,
Source-Hash der Quelldatei, Datei-SHA-256 und Importzeit
(Tabelle `reference_import`).

## Übernommen

### 1. Commander-Flags — `commander_flags.json`
- Schema `commander-card-flags-1.0.0`, Quelle dort: Scryfall-Oracle-Bulk
  `oracle-cards-20261031090154.jsonl.gz` (Bulk-SHA-256 als Source-Hash
  übernommen), Stand 2026-10-31.
- Inhalt: 53 **Game Changer** + 83 **Commander-Banned**, Zuordnung per
  `oracle_id` (Tabelle `reference_card_flag`).
- **Semantik (strikt):** Ein Game-Changer-Flag ist eine Bracket-/
  Kennzeichnungsinformation, **kein Legalitätsurteil**. Die Banned-Liste
  ist eine **Referenz** — die Legalität in Deckbuild Studio kommt
  weiterhin ausschließlich aus den lokalen Scryfall-Legalities.
  Abweichungen zwischen Referenzliste und Scryfall-Status werden im
  Import-Report und in `cache-status` gezählt und sichtbar gemacht
  (`discrepancies_vs_scryfall`), **niemals still überschrieben** —
  in keine der beiden Richtungen.

### 2. Strukturelle Rollenprofile — `structural_role_profiles.json`
- Schema 0.4.0, `estimate_type = structural_model_estimates`,
  `data_as_of = 2026-08-09`, Source-Hash in der Datei.
- Inhalt: 195 Profile (Rollen, Rollenstärken, Mechanik-Tags u. a.),
  Zuordnung per `oracle_name` → `oracle_id` über den lokalen
  Scryfall-Store (Tabelle `reference_role_profile`). Nicht auflösbare
  oder mehrdeutige Namen werden gezählt und gemeldet, nicht erfunden.
- **Semantik (strikt):** Das sind **Modell-Schätzungen**, keine
  Beobachtungen. `estimate_type` wird unverändert mitgeführt; API und UI
  kennzeichnen jeden Wert als „Strukturelle Schätzung (Modell),
  Stand 2026-08-09 — keine Beobachtungsdaten". Eine Darstellung als
  EDHREC- oder Playgroup-Befund ist ausgeschlossen.

## Bewusst NICHT übernommen

| Datei | Grund |
|---|---|
| `data/cards/pilot_card_knowledge.json` (7.231 Karten) | Enthält faktisch Scryfall-Druckfakten — Duplikat des eigenen Scryfall-Stores, kein Mehrwert, nur Drift-Risiko. |
| `data/cards/xmage_card_facts.json` | Engine-spezifische XMage-Fakten; Deckbuild Studio ist BUILD-only und grenzt XMage bewusst aus. |
| `data/meta/card_frequencies/*` | Meta-Frequenzen fremder Commander mit anderer Provenienz/Zielsetzung; keine Referenzdaten für die eigene Sammlung. |

## Anzeige

- `/api/cards` und `/api/pool` liefern je Karte ein `reference`-Feld
  (Flags mit erklärendem Label; Rollenprofil mit Schätzungs-Label);
  die UI zeigt Badges („Game Changer", „Banned-Referenz",
  „Rollen (Schätzung): …").
- `mtg-deckbuilder cache-status` enthält `reference_data` mit
  Import-Provenienz, Zählwerten je Quelle, Diskrepanzen zu Scryfall
  und Überlappung je Collection.

## Echter Lauf (2026-11-11, lokaler Datenordner)

- Flags: **53 Game Changer / 83 Banned importiert**, alle 136 Einträge
  per `oracle_id` im lokalen Scryfall-Store vorhanden (0 nicht
  auflösbar). Diskrepanzen zu Scryfall: **0** (Referenz-Banned-Liste
  deckt sich exakt mit den Scryfall-Legalities des Stores).
  Überlappung mit der Collection `foundation-schwarze-box`:
  0 Game Changer, 1 Banned-Referenz (**Crusade** — physisch vorhanden,
  aber Commander-gebannt; Legalität folgt Scryfall, nicht der Liste).
- Rollenprofile: **195 importiert, 195 aufgelöst, 0 mehrdeutig,
  0 unaufgelöst**; davon **43 in der Collection** (per `oracle_id`).
- Re-Import ist idempotent (gleicher Endstand, Provenienz aktualisiert).
