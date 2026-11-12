# Browser-Decklisten-Sammler

Sammelt **volle Decklisten** von Deckseiten (EDHREC-Deckpreview,
Moxfield) über einen echten, sichtbaren Chromium-Browser — für die
Fälle, in denen eine Website keine API anbietet und reine HTTP-Abrufe
blockiert. Der Browser läuft mit **deinem eigenen Profil und deiner
eigenen Zustimmung** (Cookie-Banner), in menschlichem Tempo, und
stoppt bei Blockaden (HTTP 403/429), statt sich durchzuzwingen.

## Ablauf (genau wie besprochen)

1. Das Skript öffnet Chromium mit einem persistenten Profil
   (`.browser-profile/` — deine Zustimmung bleibt gespeichert).
2. **Tab 1** lädt eine Deckseite und **bleibt offen**. Beim ersten Lauf
   klickst du dort einmalig **„Accept All"** und drückst dann im
   Terminal-Fenster ENTER.
3. **Tab 2** lädt danach Deck für Deck. Aus den JSON-Antworten, die die
   Seite selbst lädt, werden die vollen Kartenlisten extrahiert und
   sofort zeilenweise in die Ausgabe geschrieben (abruchsicher).

## Installation (einmalig, Windows)

```bat
py -3 -m pip install playwright
py -3 -m playwright install chromium
```

## Start

Deck-URLs aus der eigenen Studio-Datenbank (EDHREC-Deck-Einträge,
z. B. nur Chulane, max. 50):

```bat
py -3 browser_deck_harvest.py --edhrec-from-db --commander chulane --limit 50
```

Oder beliebige Deck-URLs aus einer Textdatei (eine URL je Zeile):

```bat
py -3 browser_deck_harvest.py --urls urls.txt --out decklists_browser.jsonl
```

- `--resume` ist eingebaut: Bereits erfolgreich geladene URLs (Status
  AVAILABLE in der Ausgabe) werden übersprungen.
- Standard-Tempo: 2,5–5 s Pause zwischen Decks (`--delay-min/--delay-max`).
- Standard-Limit: 200 Decks je Lauf (`--limit`).

## Ausgabe

`decklists_browser.jsonl` — je Deck eine Zeile: Quelle, URL,
Abrufzeitpunkt (UTC), Parser-Version, Deckname, Kartenliste
(Name, Anzahl, Sektion), Status (AVAILABLE/PARTIAL/BLOCKED) und
Notiz. Die Datei geht danach an Muse zurück; der Import ins
Deckbuild Studio läuft dort mit derselben Provenienz-Führung wie bei
allen anderen Quellen.

## Ehrliche Grenzen

- Die Extraktion liest, was die Seite im Browser lädt. Ändert eine
  Website ihre interne Datenform, meldet das Skript ehrlich PARTIAL
  statt still falsche Listen zu liefern (Schwelle: unter 40
  extrahierte Karten gilt ein Deck nicht als vollständig).
- Bei 403/429 stoppt der Lauf sofort — dann bitte in Tab 1 schauen,
  ob die Seite etwas von dir will (z. B. erneut Zustimmung).
