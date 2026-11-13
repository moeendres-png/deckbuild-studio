# Datenquellen-Erkundung — Befundbericht (2026-11-12)

Erkundung neuer Datenquellen gegen die drei bekannten Lücken des Deckbuild-Studios:

- **(a)** 11 leere und weitere dünne Commander×Bracket-Decklisten-Kohorten (Archidekt-Bestand: 9.211 Decks, B2 3.854 / B3 3.742 / B4 1.615, alle 63 Commander). Die 11 leeren Kohorten: B2 Myojin of Night's Reach · B3 Teyo, Diamondblade Mage; Vulture, Scheming Scavenger; Yargle, Goliath of Otaria · B4 Hapatra, the Desert Fang; Myojin of Night's Reach; Saheeli, Consul of Oversight; Teyo, Lightshield Expert; Venom, Evil Unleashed; Vulture, Scheming Scavenger; Winter, Tormented Loner.
- **(b)** Conversion je Karte wird von EDHTop16 nicht publiziert (nur Play-Rates; Sammlungstreffer 49/1.324 Karten).
- **(c)** Volle Decklisten von EDHREC/Moxfield sind per API nicht verfügbar.

Bestand (nicht erneut geprüft): Scryfall, EDHREC (Seiten/Statistiken), Playgroup, Spellbook, MTGJSON (Drucke/Fremdnamen), Archidekt B2–B4, EDHTop16 (Play-Rates).

Methodik: Jede Quelle wurde am 2026-11-12 live geprüft — Zugangsweg, robots.txt und ToS selbst gelesen, Stichprobe mit echten Zahlen gegen unsere 63 Commander / 1.324 Karten. Bei 429/403 auf einer Route wurde gestoppt, nicht umgangen. Keine GitHub-Schreibzugriffe, echte DB nur lesend (`mode=ro`), keine Accounts angelegt, keine kostenpflichtigen Dienste.

---

## 1. Moxfield — ABLEHNEN (Automation/API)

**Zugang:** Keine offizielle öffentliche API und keine Entwickler-Dokumentation. Die Decksuche läuft über ein internes, undokumentiertes Frontend-API (`api2.moxfield.com`, v2/v3). API-Zugang gibt es nur nach manueller Freigabe durch den Moxfield-Support.

**Rechtslage (selbst gelesen / belegt):**

- `api2.moxfield.com/robots.txt` (HTTP 200, direkt abgerufen): `User-agent: *` → `Disallow: /` — vollständiges Automationsverbot für die API-Domain.
- Moxfield-Entwickler, zitiert in GitHub-Issue mpc-autofill/mpc-autofill#265: *„Due to some bad actors, access to Moxfield's API has been made much more limited. For legitimate tools, we will grant access to the API…“* — Freigabe nur auf Anfrage an support@moxfield.com.
- GitHub `moxfield/moxfield-public` #143 belegt ein Whitelist-Programm (Partner-User-Agents) mit zusätzlichen Cloudflare-Validierungsproblemen selbst für freigegebene Clients.
- `moxfield.com/robots.txt` (Hauptdomain) verbietet nur `/user/admin.html`, `/search/*`, `/account/*`, `/collection/*`, `/binders/*` — Deckseiten selbst sind dort nicht ausgeschlossen.
- Ehrlichkeitsvermerk: Der Moxfield-ToS-Volltext konnte in dieser Umgebung nicht gelesen werden (SPA ohne Server-Rendering; Browser-Egress aus der VM blockiert, s. Abschnitt 6). Das Urteil stützt sich auf robots.txt der API-Domain und Moxfields eigene öffentliche Aussagen — beides eindeutig.

**Stichprobe:** Genau eine Probe-Anfrage an die Suchroute (vor dem robots-Befund) antwortete HTTP 200 mit Deck-JSON (u. a. Like-/View-Zähler); der Commander-Filter griff mit dem geratenen Parameter nicht sichtbar (totalResults 10.000). Danach wurde die Route nicht weiter genutzt. Eine Bracket-Kennzeichnung je Deck konnte per API nicht verifiziert werden.

**Urteil: ABLEHNEN** für jede automatisierte Nutzung. Einziger legitimer Weg wäre eine Support-Freigabe (Partner-API) — Owner-Entscheidung, kein technischer Schritt.

## 2. TopDeck.gg — ÜBERNEHMEN (bedingt: Owner legt kostenlosen API-Key an)

**Zugang:** Offizielle, dokumentierte **API v2** (Doku: https://topdeck.gg/api/docs, selbst gelesen). `POST /v2/tournaments` im Query-Modus (Pflicht: `game`, `format`; Commander-Format heißt dort „EDH"). Antwortspalten u. a. `decklist`, `wins`/`draws`/`losses`, `winRate`-Felder; wird `decklist` angefragt, liefert die API zusätzlich **`deckObj`** (strukturierte Deckdaten). Das Feld `leader` trägt bei Commander-Formaten den Commander-Namen. Rate-Limits je Tier 5/50/100 Requests/Minute je API-Key, 1.000.000 Dokumente/Tag. EDHTop16 aggregiert genau diesen Turnier-Korpus.

**Rechtslage (Developer Terms, https://topdeck.gg/developer-terms, selbst gelesen):**

- §2.1: API-Key ist im Developer-Portal erstellbar (Account nötig — Owner-Schritt, wurde hier nicht angelegt).
- §6.1 **Attribution Pflicht**: *„Data provided by TopDeck.gg"* mit Link, sichtbar überall dort, wo die Daten angezeigt werden.
- §7 Verbot: *„Scrape the Services, get data other than through the documented API…“* — nur der dokumentierte API-Weg ist erlaubt.
- §10: *„The API, webhooks and Log in with TopDeck are currently free."*
- §3: Limits einhalten, *„cache responsibly"*.
- robots.txt der Domain: `User-agent: * Allow: /`.

**Stichprobe:**

- Ohne Key live getestet: HTTP 401 `{"error":"API key is required"}` — Endpunkt und Key-Mechanik damit verifiziert; eine inhaltliche Stichprobe ist ohne Key nicht möglich.
- Feld-Evidenz aus der offiziellen Doku (s. o.): vollständige Decklisten **plus** Spielergebnisse (W/D/L) je Turnier — daraus ist die **Conversion je Karte selbst berechenbar** (Anteil der Decks mit Karte X, die Top-Cuts/Siege erreichen), genau die Größe, die EDHTop16 nicht publiziert → **schließt Lücke (b)**.
- Commander-Überlappung ist dagegen klein: Der Korpus ist cEDH-Turnierdaten. Auf der EDHTop16-Startseite (live abgerufen) fand sich nur **1 unserer 63 Commander** in der Top-Auswahl (Brigid, Clachan's Heart // Brigid, Doun's Mind); die bestehende EDHTop16-Schicht trifft nur 49/1.324 Sammlungskarten. Für Lücke (a) (casual-lastige dünne Kohorten) taugt die Quelle nicht.

**Urteil: ÜBERNEHMEN** als neue Schicht „TopDeck-Turnierlisten" — unter drei Bedingungen: (1) M legt den kostenlosen API-Key im Developer-Portal an (Accounts sind für die Erkundung verboten), (2) Attribution „Data provided by TopDeck.gg" wird in der UI eingebaut, (3) Kohorte strikt getrennt führen (cEDH-Turniere ≠ Archidekt-Brackets). Nutzen: erste selbst berechenbare Conversion je Karte; erwartbare Abdeckung klein (Größenordnung der bisherigen 49 EDHTop16-Karten plus Turnierlisten-Details), aber qualitativ einzigartig. **Kein Probe-Import möglich**, solange kein Key existiert.

## 3. Deckstats.net + TappedOut — ABLEHNEN (Rechtslage)

**Deckstats.net:**

- robots.txt (direkt abgerufen): `Disallow: /api/`, `/search`, `/decks$`, `/*?` (alle Query-Strings) — API- und Suchrouten sind für Automation ausgeschlossen.
- ToS, Abschnitt „Your Use of Our Content" (Text per Suchindex der Domain gelesen; der Direktabruf der Terms-Seite lieferte keinen extrahierbaren Inhalt — Methodenlücke hier vermerkt): Verbot, Inhalte *„by robot, spider, scraper, web crawler, or other automated means"* als Quelle/Ersatz zu nutzen, plus Verbot, Robot-Exclusion-Header zu verletzen oder Maßnahmen gegen automatisierten Zugriff zu umgehen.

**TappedOut:**

- ToS §2(e)(ii) (http://tappedout.net/terms-of-use/, per Suchindex gelesen): ausdrückliches Verbot, Website-Inhalte mit *„any robot, bot, spider, crawler, spyware… extraction tool, or any other automatic device"* zu sammeln oder zu kopieren.
- robots.txt verbietet `*` zwar nicht (nur benannte Bots; bingbot Crawl-delay 5) — die ToS ist der Blocker. Eine öffentliche API-Dokumentation wurde nicht gefunden.

**Urteil: beide ABLEHNEN.** Rechtslage eindeutig; eine Umfang-Stichprobe erübrigt sich.

## 4. Archidekt-Erweiterung Brackets 1 + 5 — ABLEHNEN als Lückenschluss (gemessen)

**Zugang:** Dieselbe öffentliche API v3 wie der Bestand (`GET /api/decks/v3/?commanderName=…&deckFormat=3&edhBracket={1|5}`); robots.txt der Domain schließt nur `/login?`, `/partialCompare`, `/playtester-v2/`, `/sandbox?` aus.

**Stichprobe (vollständige Zählung, alle 63 Commander × B1/B5, 2026-11-12, alle 126 Antworten HTTP 200, keine Sperre):**

| Kohorte | Decks gesamt (63 Commander) | Ø je Commander | Commander mit 0 |
|---|---|---|---|
| B1 | 317 | 5,0 | 19 |
| B5 | 259 | 4,1 | 40 |
| (Vergleich B2, Bestand) | 3.854 | 61,2 | — |

- Die 11 Leer-Kohorten-Commander haben auch auf B1/B5 praktisch nichts: Myojin of Night's Reach B1=1/B5=0, Vulture, Scheming Scavenger 1/0, Yargle, Goliath of Otaria 1/0, alle übrigen acht 0/0. **Lücke (a) wird nicht geschlossen.**
- B5 ist stark konzentriert (Brigid 82, Maralen, Fae Ascendant 82, danach ≤ 15); B1-Spitze: Ramos, Dragon Engine 49, Fynn, the Fangbearer 33, Tatyova, Benthic Druid 23.

**Metadaten-Tiefe (1 Such- + 1 Detail-Abruf):** Suchzeilen tragen `viewCount`, Kommentar-Zähler, `tags`, `hasPrimer`, `createdAt`/`updatedAt`; das Deck-Detail zusätzlich `deckTags` und `points`. Die Signale sind dünn besetzt (Stichprobe B5-Deck: viewCount 6, Tags leer) — als Qualitäts-Signal höchstens ein schwacher Tie-Breaker, kein Kohorten-Füller. Unser Parser speichert bereits `source_updated_at`.

**Urteil: ABLEHNEN für die Lücken.** Technisch wäre die Erweiterung trivial (gleicher Harvester, nur Bracket-Parameter, Kohorten strikt getrennt), aber sie verdünnt die Statistik mit zwei sehr dünnen Kohorten, ohne eine einzige der 11 Lücken zu füllen. Bei späterem Bedarf jederzeit nachholbar.

## 5. MTGJSON-Restscheiben (ohne Preise) — ABLEHNEN (Zugewinn 0, gemessen)

**Bestand:** Die Schicht nutzt `AllPrintings.json.xz` (MTGJSON live: Version `5.3.0+20261111`) und liest `identifiers` (scryfallOracleId/scryfallId) **und** `foreignData` bereits inline aus derselben Datei.

**Messung (echte DB, read-only):**

- `mtgjson_print`: **59.452 Zeilen, 0 ohne oracle_id**, 1.324/1.324 Identitäten abgedeckt, 495 distinct Set-Codes.
- Fremdnamen: **47.746 Zeilen in 14 Sprachen** (u. a. English 11.706, Japanese 6.860, Spanish 6.644, German 6.213).
- Gegenprobe Scryfall: Summe `prints_count` über unsere 1.324 Karten = **11.484** < 11.706 englische MTGJSON-Zeilen → kein Mapping-Rückstand, den eine andere Scheibe heilen könnte.
- `AllIdentifiers` enthält dieselben Identifier anders verpackt, **keine Namensfelder** → Zugewinn Mapping 0, Fremdnamen 0.
- Set-Dateien brächten nur Set-Metadaten (Name/Datum/Typ) für die 495 Sets = reine Anzeige-Metadaten, kein Lückenschluss.

**Urteil: ABLEHNEN.** Δ ist nicht vermutet, sondern gemessen null.

## 6. EDHREC-Deckpreview per Browser-Tool — NUR-BROWSER-TOOL; VM-Test infrastruktur-blockiert

**Rechtsrahmen:** EDHREC-robots.txt schließt `/deckpreview/` für Crawler aus (Wildcard-Gruppe; vgl. `docs/EXTERNAL_DATA.md`). Es gibt keine API-Route; das Browser-Tool (`~/workspace/projects/browser-harvest-tool`, Parser `browser-harvest/1.0.0`) ist per Design ein **Owner-Lauf in der eigenen Browser-Session** auf dem Rechner von M, keine serverseitige Ernte.

**Test aus dieser VM (2026-11-12):** Zwei echte Deckpreview-URLs aus `edhrec_deck_entry` (neueste `savedate`-Einträge) wurden headless mit dem Tool gefahren. Ergebnis: Playwright meldet für **jede** URL `net::ERR_TUNNEL_CONNECTION_FAILED` — in einer Kontroll-Probe auch für `https://example.com/` und die EDHREC-Startseite, mit und ohne explizit konfigurierten Egress-Proxy. Befund: **Der Egress-Proxy dieser VM lehnt CONNECT-Tunnel des Chromium-Prozesses generell ab** (curl/HTTP-Clients der Laufzeit funktionieren, der Browser nicht). Das ist eine Infrastruktur-Blockade der VM, **keine** EDHREC-Blockade; über EDHREC-Verhalten lässt sich von hier keine Aussage treffen.

**Was positiv belegt ist:** Das Tool selbst ist lokal End-to-End verifiziert (Fixture-Lauf: 46 Einträge / 65 Karten korrekt extrahiert, Status AVAILABLE; Parser-Tests 5/5 grün). Auf dem Rechner von M existiert kein Egress-Proxy — der Heimlauf bleibt der entscheidende, noch ausstehende Verifikationsschritt.

**Urteil: NUR-BROWSER-TOOL** (wie konzipiert). Keine Implementierungsänderung nötig; optional könnte das Tool eine Proxy-Option bekommen, falls es je in einer Proxy-Umgebung laufen soll.

## 7. Scryfall-Catalogs — ABLEHNEN als Datenquelle (Zugewinn ≈ 0, gemessen)

**Zugang:** Offizielle Katalog-Endpunkte `api.scryfall.com/catalog/…` (live gezählt): creature-types 377, keyword-abilities 224, keyword-actions 80, ability-words 74, planeswalker-types 99, artifact-types 21, enchantment-types 13, land-types 18, supertypes 7, card-names 35.542.

**Abgleich mit der Sammlung (echte DB, read-only):**

- Unsere **158 Subtypen: 0 außerhalb** der offiziellen Typ-Kataloge.
- Unsere **99 Keywords: nur 4 außerhalb** aller Keyword-Kataloge — `Dinosaur Formula`, `Lizard Formula`, `Nosh`, `Share` (Sticker-/Sondermechanik-Texte, je marginal).

**Urteil: ABLEHNEN als Schicht.** Die Kataloge validieren nur, was unsere Ableitung schon korrekt enthält. Höchstens als QA-Whitelist-Referenz denkbar, kein Datengewinn.

---

## Zusammenfassung

| # | Quelle | Urteil | Schließt Lücke |
|---|---|---|---|
| 1 | Moxfield | **ABLEHNEN** (API-robots `Disallow: /`; Zugang nur per Support-Freigabe) | — |
| 2 | TopDeck.gg API v2 | **ÜBERNEHMEN** (bedingt: kostenloser Owner-API-Key + Attribution) | **(b)** Conversion je Karte selbst berechenbar |
| 3 | Deckstats / TappedOut | **ABLEHNEN** (robots/ToS verbieten Scraping ausdrücklich) | — |
| 4 | Archidekt B1/B5 | **ABLEHNEN** als Lückenschluss (317 + 259 Decks; Leer-Commander bleiben leer) | (a) nein, gemessen |
| 5 | MTGJSON-Restscheiben | **ABLEHNEN** (Δ = 0, gemessen) | — |
| 6 | EDHREC-Deckpreview | **NUR-BROWSER-TOOL** (Owner-Heimlauf; VM-Test proxy-blockiert, nicht EDHREC-blockiert) | (c) nur manuell |
| 7 | Scryfall-Catalogs | **ABLEHNEN** (0 bzw. 4 marginale Abweichungen) | — |

**Top-Empfehlung:** TopDeck.gg als einzige neue Schicht aufnehmen, sobald M einen kostenlosen API-Key angelegt hat — sie liefert als einzige Quelle vollständige Decklisten **mit Spielergebnissen** und macht damit Conversion je Karte erstmals berechenbar. Lücke (a) lässt sich mit keiner geprüften erlaubten Quelle schließen: Die 11 Commander sind plattformübergreifend praktisch ohne Decklisten (Archidekt B1–B5 gemessen; Moxfield rechtlich zu). Lücke (c) bleibt dem Owner-Browser-Tool vorbehalten.
