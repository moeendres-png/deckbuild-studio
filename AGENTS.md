# AGENTS.md — Deckbuild Studio: verbindliche Arbeitsregeln für Agenten

Diese Datei ist die einzige autoritative Regelquelle für alle Agenten, die in
diesem Repo arbeiten. Sie ersetzt die verstreuten Einzelregeln in Issue-Texten,
Doku-Dateien und Briefings; bei Widerspruch gilt diese Datei (Ausnahme: ein
jüngerer Owner-Entscheid im betroffenen Issue-Verlauf, §11).
Diese Datei ist eine **Mandats-Datei**: Änderungen nur per PR, der Merge erfolgt
ausschließlich durch den Owner — für sie gilt das Self-Merge-Gate (§6) nicht.

## 1. Mission und Scope

Deckbuild Studio ist ein **BUILD-only**, sammlungsbasierter
Commander-Deckbuilder: lokale Sammlung einlesen, Karten per Scryfall-Oracle-ID
normalisieren, ausschließlich aus dem eigenen, verfügbaren, Commander-legalen
Pool bauen (Favoriten, Notizen, Filter, Listen, Entwürfe, Revisionen,
Vergleiche, Exporte). Keine Simulation, keine Rules-Engine, kein PLAY-Code.

Verbindlicher Bestand ist die **Sammlung v2** (`MTG_Kartensammlung-2.xlsx`):
1.324 Identitäten / 1.336 Lots / 1.815 Exemplare, 63 eligible Commander;
Lagerorte: Schwarze Box, Foundation, Alen Lorwyn Box. Ältere Bestandsangaben
(z. B. „Foundation/Schwarze Box, 1.078 Karten, 25 Commander" in Issue #1) sind
überholt und keine Arbeitsgrundlage.

Hart verboten:

- Shopping-, Preis- oder Kauf-Features jeder Art.
- Eine Funktion zum Hinzufügen neuer Karten in den Bestand.
- Bezahlte Dienste oder kostenpflichtige APIs ohne vorheriges Owner-Go.
- Private XLSX-Dateien, Sammlungs-Rohdaten und Snapshot-Rohdaten im Repo.
- Das alte Studio-Exportformat wird nicht mehr gelesen (Owner-Entscheid
  2026-11-13, umgesetzt in PR #28); kein Commander ist im Produktcode
  hartcodiert bevorzugt.
- Die **Tierliste wird komplett entfernt** (Owner-Entscheid 2026-11-14):
  Seite, Modelle 1.1.0/1.2.0, Endpunkte und Settings entfallen; die
  Tier-Daten werden vorher als kompaktes Archiv nach Google Drive
  gesichert (Issue #58), die Code-Entfernung läuft über Issue #59,
  danach Tabellen-Drop und ein einmaliges VACUUM in der Live-DB.
  Tier-Features werden **nicht** wieder aufgebaut; die Tier-Daten
  existieren danach nur noch im Drive-Archiv.

## 2. Rollen und Arbeitsteilung

- **Owner (Moritz):** entscheidet Scope-Fragen, Mandats-Dateien, den
  Live-DB-Abschluss und finale Übergaben. Er ist die einzige Instanz, die
  Mandate ändert.
- **Zwei Co-Lead-Instanzen mit gleicher Autorität** arbeiten parallel:
  - Instanz A schreibt **allein die Live-Datenbank**.
  - Instanz B (externe VM, diese Linie) führt schwere QA-Läufe und
    Code-Fixes aus — **ausschließlich auf DB-Kopien**. Sie schreibt nie in
    die Live-DB und startet keine Läufe gegen sie. [PRAXIS: Die
    Arbeitsteilung steht bisher nur im Co-Lead-Mandat/Briefing, nicht im
    Repo.]
- Die **DB-Anonymisierungs-Nachrüstung ist vom Owner gestrichen**
  (2026-11-13) und wird nicht wieder aufgegriffen. Die Anonymisierung
  *beim Import* bleibt unverändert bestehen (§3).
- Technik-Entscheide innerhalb eines eigenen Pakets trifft die ausführende
  Instanz selbst. Gefundene Code-Probleme aus fremden Paketen werden im
  zuständigen Issue dokumentiert, **nicht** im fremden Paket mitgefixt;
  ein Fix wird ein eigenes Folge-Issue (Ausnahme nur mit Owner-Go).

## 3. Daten-Vertrag

- Es zählen nur **objektive Daten mit Provenienz**: Quelle, Zeitpunkt,
  ggf. Hash und Parser-Version werden je Datensatz/Datenstand festgehalten.
- Statusmodell für externe Daten: `NOT_FETCHED` / `PARTIAL` / `BLOCKED` /
  `AVAILABLE`. Fehlende Daten sind **nie 0** und werden nie erfunden;
  dünne Evidenz wird als solche ausgewiesen (Status/Zähler), nicht geglättet.
- **Kohorten werden nie gemischt** (z. B. Playgroup ≠ TopDeck ≠ EDHREC;
  verschiedene Snapshot-Stände nicht zu einer Zahl verrechnen).
- Nutzer-Marks (Favorit, Ausschluss, Notiz) beeinflussen **keine**
  berechnete Zahl.
- **Keine Klarnamen von Personen** in Daten, Issues oder Doku. Spieler-
  namen werden beim Import durch `anonymize_player_names` anonymisiert
  gespeichert (Initialen-Form, bijektiv, deterministisch). Karten- und
  Commander-Namen sind keine Personennamen. Das Ortslabel
  „Alen Lorwyn Box" bleibt als Lagerort bestehen.
- Große Payload-Spalten werden über den Codec in `payloads.py`
  komprimiert gespeichert (gzip + Base64, Marker-Präfix; PR #57):
  Roundtrip byte-identisch, Provenienz-Hashes laufen immer über den
  **Original**-Payload, unkomprimierte Alt-Zeilen bleiben ohne
  Migration lesbar. Neue große Payload-Spalten nutzen denselben Codec.
- DB-Wartung: ein `VACUUM` läuft genau **einmal** am Ende einer
  Wartungsoperation (nach Migration/Drop), nicht wiederholt.

## 4. Evidenz-Standard

Jede Feststellung trägt ihre Evidenzlage; im Zweifel wird sie benannt,
nicht versteckt:

- `UNKNOWN` ist **niemals** PASS und niemals 0.
- `NOT_RUN` ist **niemals** PASS. Ein Build-/Compile-Erfolg ist kein Test.
- Jede Zahl in Berichten, PRs und Übergaben nennt ihre Herkunft
  (Lauf, Commit-Stand, DB-Stand, Zählweise).
- Befunde werden mit Schwere **P1** (blockierend) / **P2** (relevant) /
  **P3** (kosmetisch/vermerkt) klassifiziert.
- Fehler und falsche Zwischenbefunde werden **offen an Ort und Stelle
  korrigiert** (Korrektur-Kommentar im selben Issue/PR), nicht still
  überschrieben.

## 5. Paket-Ablauf

- **Ein Paket = ein Issue = ein PR.** Vor Arbeitsbeginn wird das Paket
  per Kommentar auf dem Issue geclaimt (Instanz + Scope + Gates).
- Neue Arbeit bekommt **neue Dateien** (Berichte, Handoffs, Tabellen);
  alte Berichte werden nur gelesen, nie ergänzt oder überschrieben.
  [PRAXIS]
- Der PR folgt dem Repo-PR-Template (`.github/pull_request_template.md`)
  inkl. Gate-Checkliste und ehrlichem Teststand (was lief wirklich,
  mit Anzahl).
- Ergebnis-Kommentar auf dem Issue am Ende: was wurde getan, Belege
  (Testzahlen, Commit-/PR-Links), offene Restpunkte. Das Issue wird erst
  geschlossen, wenn das Ergebnis erledigt ist — ein PR, der nur ein
  Zwischenschritt ist, lässt das Issue offen.
- Berichte an den Owner: **deutsch, kompakt, Ergebnis zuerst**, mit
  Links auf Issues/PRs/Commits und echten Testzahlen. Delegierte Arbeit
  wird ohne Zwischenfragen zu Ende geführt; gemeldet wird bei
  Fertigstellung oder bei echter Unklarheit. [PRAXIS]

## 6. Self-Merge-Gate

`AGENT_SELF_MERGE = ENABLED` — nur für normale Code- und Doku-PRs und nur,
wenn **alle** Bedingungen auf demselben Stand erfüllt sind:

1. CI-Jobs `lint` **und** `pytest` (Workflow `tests`) stehen auf dem
   **exakten PR-Head** auf `success`. Das Repo hat keine Required Checks —
   der Stand wird per Check-Runs auf der Head-SHA verifiziert, nie
   angenommen; ein laufender (`in_progress`) Stand ist kein „grün".
2. Ein **unabhängiges Fresh-Eyes-Review** (Instanz ohne Arbeitskontext
   des Autors) endet mit PASS und ohne offenes P1/P2.
3. Für jeden Fix liegt ein **Changed-Line-Beleg** vor: ein benannter Test,
   der die geänderte Zeile ausführt und ohne die Änderung fehlschlägt.
   [PRAXIS]
4. Die gepushten Dateien sind per **Blob-SHA** lokal = remote abgeglichen.
   [PRAXIS]

Verbote ohne Ausnahme: kein Push direkt auf `main`, kein Force-Push,
kein History-Rewrite. Mandats-Dateien (diese Datei, Scope-Regeln) und
alles in §10 Genannte mergt nur der Owner.

## 7. Git- und Push-Mechanik [PRAXIS]

- Es gibt **keine lokalen Push-Credentials**. Der Schreibweg ist die
  GitHub-API (`push-files`): Text-only, Pfaddatei NUL-delimitiert **mit
  abschließendem NUL**, Pfade relativ zur Repo-Wurzel, Staging-Verzeichnis
  bildet die Repo-Struktur ab.
- Gepusht wird nur auf **Branches**, immer gegen den frisch gelesenen
  Head (vor dem Push `main` neu lesen; fremde Änderungen nie
  überschreiben). Binärdaten werden von `push-files` abgelehnt.
- Nach jedem Push: Remote-Stand gegen lokal per Blob-SHA diffen.

## 8. Test-Konventionen

- Runner: venv mit Python 3.12; Ruff-Pin = CI-Version (aktuell 0.17.4,
  `ruff check src tests`); Testlauf `python -m pytest -q`.
- Läufe immer mit `TMPDIR` auf der Workspace-Platte (das System-`/tmp`
  ist zu klein und erzeugt sonst falsch-positive Fehler). [PRAXIS]
- In Arbeitskopien (Rekonstruktionen ohne `.git`) wird `PYTHONPATH=src`
  gesetzt, damit der Kopie-Stand getestet wird, nicht eine installierte
  Fassung. [PRAXIS]
- Vor jedem Push laufen lokal die **gezielten Tests** der geänderten
  Dateien (plus thematische Nachbarschaft) und Ruff. Die **volle Suite
  ist CI-Gate** auf dem exakten PR-Head (§6) und ersetzt den lokalen
  Voll-Lauf als Arbiter. Schwere Läufe — volle Suite lokal,
  DB-Integritätsprüfungen, Server-Smokes auf DB-Kopien — führt
  Instanz B (§2) aus, lokal nur zur Diagnose roter CI, für Bäume ohne
  GitHub-Stand und für die Abschluss-QA auf finalen Ständen.
  [Owner-Vorgabe 2026-11-13]
- „CI grün" wird nur mit Trio aus PR-Nummer, Head-SHA und Check-Namen
  aus derselben Quelle behauptet. [PRAXIS]

## 9. Reuse-first und Upstream-Abgleich

Deckbuild Studio ist eine Ausgründung des Studio-Moduls aus
`commander-playtest-lab` (Upstream). Vor einem Eigenbau gilt:

- Bestand im eigenen Repo wiederverwenden, bevor Neues entsteht
  (vorhandene Helfer, Muster und Degradierungs-Konventionen der
  Codebasis haben Vorrang vor neuen Abstraktionen).
- Upstream-Übernahmen nur nach Abgleich gemäß `docs/UPSTREAM_SYNC.md`
  und nur, wenn sie zu den Verträgen dieser Datei passen (Provenienz,
  Statusmodell, Kohorten-Trennung, BUILD-only). Kein PLAY-/Engine-Code.
- Jede Übernahme und jede bewusste Nicht-Übernahme wird im
  UPSTREAM_SYNC-Protokoll mit Begründung festgehalten.

## 10. Eskalation und Owner-Grenzen

Eskaliert wird nur bei echten Blockern außerhalb des eigenen Zugriffs
und an Owner-Grenzen. Immer Owner-Sache:

- Scope-Änderungen und neue Features außerhalb von §1.
- Mandats-Dateien (diese AGENTS.md, Scope-Regeln).
- Alles, was die **Live-DB** abschließend verändert oder übergibt.
- Bezahlte Dienste, neue externe Accounts/Berechtigungen.

Alles andere entscheidet die ausführende Instanz im eigenen Paket und
legt es im Ergebnis-Kommentar offen (inkl. bewusst verworfener
Alternativen und bewusst nicht gezogener Folgepunkte).

## 11. Drift-Regel

- Issue-Texte können **stale** sein (bekannt: Issue #1 Bestands-Text,
  Issue #10 Koordinations-Protokoll). Bei Widerspruch zwischen einem
  Issue-Text und dieser Datei gilt diese Datei plus der jüngste
  Owner-Entscheid im Issue-Verlauf.
- Ein erkannter Widerspruch wird **offen benannt** (im Issue und im
  Bericht), nie still zugunsten einer Seite entschieden.
- Diese Datei selbst wird im Rhythmus des Upstream-Abgleichs gegen den
  Repo-Stand geprüft; veraltete Regeln werden **korrigiert, nicht
  ergänzt** — die Datei bleibt schlank und widerspruchsfrei.

## 12. Fertig-Definition

„Fertig" heißt semantisch fertig, nicht nur grün:

- Der geänderte Codepfad wurde von einem echten Lauf ausgeführt
  (kein reiner Compile-/Import-Erfolg als Testbehauptung).
- Gezielte Tests lokal gelaufen (§8); volle Suite als CI auf dem
  exakten Head verifiziert (§6), Review PASS (§6).
- Ergebnis-Kommentar mit Belegen gepostet; Issue-Zustand entspricht
  dem tatsächlichen Ergebnis (offen bei Zwischenschritt).
- Restpunkte sind benannt und entweder als Folge-Issue angelegt oder
  ausdrücklich als verworfen markiert.

<!-- Quellen- und Praxis-Markierungen stehen im Begleitbericht zum PR;
     [PRAXIS] im Text kennzeichnet Regeln aus der gelebten Arbeitsweise,
     die bisher nirgends im Repo standen. -->
