# Die Sammlungsdatei: So muss sie aussehen

Damit das Programm deine Kartensammlung einlesen kann, legst du sie als
Excel-Datei an. Diese Beschreibung zeigt, wie die Datei aufgebaut sein
muss, und was beim Einlesen passiert.

## Das Wichtigste in Kürze

- Eine Excel-Datei (`.xlsx`). Der Dateiname ist egal.
- Darin ein Tabellenblatt, das genau **`Kartensammlung`** heißt.
- Zeile 1 ist die Kopfzeile mit den Spaltenüberschriften.
- Darunter eine Zeile pro Karte und Standort: Wo eine Karte in
  mehreren Boxen liegt, bekommt sie eine Zeile pro Standort.

Bevor du deine Datei zum ersten Mal einliest, muss das Programm einmal
die Kartendaten geladen haben (siehe Installationsanleitung). Sonst
bricht der Import mit einem Hinweis ab, und es wird nichts übernommen.

## Die Spalten

Du brauchst nur drei Spalten:

| Spalte | Pflicht? | Bedeutung | Beispiel |
|---|---|---|---|
| `Kartenname` | Ja | Der genaue englische Name der Karte, so wie er auf der Karte steht. | `Lightning Bolt` |
| `Anzahl` | Ja | Wie viele Exemplare an diesem Standort liegen. Ganze Zahl. | `4` |
| `Standort` | Nein | Wo die Karten liegen, z. B. eine Box oder ein Ordner. Frei wählbar. | `Box A` |

Weitere Spalten sind erlaubt, zum Beispiel für deine eigenen Notizen —
sie werden beim Einlesen einfach ignoriert. Auch weitere Tabellenblätter
in der Datei sind kein Problem; gelesen wird nur das Blatt
`Kartensammlung`.

## Minimal-Beispiel

Blatt `Kartensammlung`:

| Kartenname | Anzahl | Standort |
|---|---|---|
| Lightning Bolt | 4 | Box A |
| Counterspell | 2 | Box A |
| Sol Ring | 1 | Ordner |
| Forest | 10 | Box B |

## Die Regeln im Detail

**Kopfzeile.** Die Überschriften müssen in Zeile 1 stehen und genau
`Kartenname`, `Anzahl` und `Standort` lauten, auch in der
Groß-/Kleinschreibung. Erkennt das Programm eine Überschrift nicht,
kann es die Spalte nicht lesen.

**Kartenname.** Es zählt der exakte englische Name, inklusive
Groß-/Kleinschreibung. Deutsche Kartennamen funktionieren nicht.
Karten mit zwei Namen — zum Beispiel doppelseitige Karten — schreibst
du mit beiden Namen in eine Zelle, getrennt durch ` // `, etwa
`Delver of Secrets // Insectile Aberration`.

**Anzahl.** Eine ganze Zahl pro Zeile. Kommazahlen (wie `1,5`),
Worte (wie `zwei`) und negative Zahlen sind Fehler. Eine leere
Anzahl ist ebenfalls ein Fehler — eine Zeile ohne Anzahl wird nicht
still als 0 gelesen. Die Zahl `0` ist erlaubt: Sie setzt die Menge
dieser Karte an diesem Standort auf 0.

**Standort.** Die Angabe ist freiwillig. Lässt du sie leer, landet die
Karte unter dem Standort `unknown`. Der Standort wird wörtlich
übernommen: `Box A` und `box a` wären zwei verschiedene Standorte.
Schreibe ihn deshalb immer gleich.

**Gleiche Karte mehrfach.** Kommt dieselbe Karte am selben Standort
in mehreren Zeilen vor, werden die Anzahlen zusammengezählt. Dieselbe
Karte an verschiedenen Standorten wird getrennt geführt.

**Leere Zeilen.** Komplett leere Zeilen werden übersprungen, ebenso
Zeilen ohne Kartennamen. Du musst die Datei also nicht perfekt
aufräumen.

**Erneut einlesen.** Du kannst eine geänderte Datei jederzeit wieder
einlesen. Die Mengen werden dann auf den Stand der Datei aktualisiert —
nicht verdoppelt. Karten, die in der neuen Datei fehlen, bleiben
gespeichert; gelöscht wird durch das Einlesen nichts.

## Wenn etwas schiefgeht

Bei einem Fehler wird **gar nichts** übernommen — auch nicht die
korrekten Zeilen. Die Fehlermeldung nennt die betroffenen Karten,
sodass du die Datei korrigieren und es einfach erneut versuchen
kannst. Häufige Ursachen:

- Ein Kartenname ist falsch geschrieben oder nicht der englische Name
  (die Meldung sagt dann, die Karte wurde nicht gefunden).
- Eine Anzahl ist leer, eine Kommazahl oder ein Wort.
- Das Tabellenblatt heißt nicht `Kartensammlung`.

**Kontrolle nach dem Import:** Das Programm meldet, wie viele Zeilen
und Karten es übernommen hat. Steht dort 0, obwohl deine Datei gefüllt
ist, prüfe zuerst die Kopfzeile: Schon eine abweichende Überschrift
(wie `Name` statt `Kartenname`) führt dazu, dass keine einzige Zeile
erkannt wird — ohne Fehlermeldung.
