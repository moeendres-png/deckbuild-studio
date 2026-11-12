## Was & warum

<!-- Kurzbeschreibung der Änderung und des Grundes. Issue verlinken (Refs #…). -->

## Gate-Checkliste (Merge-Definition: docs/CI_GATES_PLAN.md)

- [ ] CI auf diesem PR-Head grün: Jobs `lint` und `pytest` (Workflow `tests`)
- [ ] Lokal `scripts/check.sh` auf dem finalen Head grün (Ruff + Import-Smoke + pytest)
- [ ] Neue/geänderte Logik ist durch Tests abgedeckt; Fehlerpfade sind geprüft
- [ ] Bei Vertrags-/Datenänderungen: unabhängige QA-Suite grün (PR-Lauf oder `workflow_dispatch` auf diesem Head)
- [ ] Keine privaten Daten im Diff (keine Sammlung/XLSX, kein Datenordner-Inhalt, keine Snapshot-Rohdaten)
- [ ] Doku fortgeschrieben, wo sich Verhalten oder Verträge ändern

## Teststand

<!-- Was wurde lokal/CI tatsächlich ausgeführt? Ergebnis + Testanzahl. UNKNOWN ist nicht PASS. -->
