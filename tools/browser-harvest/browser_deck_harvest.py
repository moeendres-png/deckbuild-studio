#!/usr/bin/env python3
"""Browser-Decklisten-Sammler (EDHREC-Deckpreview / Moxfield).

Öffnet Chromium mit einem persistenten Profil. Der ERSTE Tab bleibt auf
einer Deckseite stehen, damit der Nutzer dort einmalig die
Cookie-Zustimmung ("Accept All") anklicken kann. Der ZWEITE Tab lädt
danach Deck für Deck und speichert die VOLLEN Decklisten als JSONL.

Die Extraktion nutzt primär die JSON-Antworten, die die Seite selbst
lädt (Netzwerk-Mitschnitt), ersatzweise eingebettetes JSON im HTML und
zuletzt den sichtbaren Text. Kein Headless-Tarnmodus, keine
Captcha-Lösung, menschliches Tempo, Stopp bei Blockaden (403/429).

Beispiele:
    python browser_deck_harvest.py --urls urls.txt --out decks.jsonl
    python browser_deck_harvest.py --edhrec-from-db --limit 50
    python browser_deck_harvest.py --urls urls.txt --resume

Ausgabe je Deck eine JSON-Zeile:
    {"source": "edhrec", "source_url": ..., "fetched_at_utc": ...,
     "deck_name": ..., "cards": [{"name": ..., "quantity": 1,
     "section": "Creatures"}, ...], "status": "AVAILABLE", "note": ""}
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PARSER_VERSION = "browser-harvest/1.0.0"
DEFAULT_PROFILE = ".browser-profile"
DEFAULT_OUT = "decklists_browser.jsonl"


# ---------------------------------------------------------------------------
# Reine Parser (ohne Browser testbar)
# ---------------------------------------------------------------------------

def _iter_dicts(node, path=()):
    """Alle dicts in einer JSON-Struktur durchlaufen (mit Schlüsselpfad)."""
    if isinstance(node, dict):
        yield node, path
        for key, value in node.items():
            yield from _iter_dicts(value, path + (str(key),))
    elif isinstance(node, list):
        for item in node:
            yield from _iter_dicts(item, path)


def _card_name(node: dict) -> str | None:
    for key in ("name", "card_name", "label"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    card = node.get("card")
    if isinstance(card, dict):
        return _card_name(card)
    return None


def _quantity(node: dict) -> int:
    for key in ("quantity", "count", "qty", "copies"):
        value = node.get(key)
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(value, str) and value.isdigit() and int(value) > 0:
            return int(value)
    return 1


def parse_deck_payload(payload) -> list[dict]:
    """Karten aus einer Deck-JSON ziehen (EDHREC/Moxfield/generisch).

    Sucht dicts mit Kartenname; die Sektion kommt aus dem Schlüsselpfad
    (z. B. "Creatures", "mainboard", "commanders"), sofern vorhanden.
    Doppelte Namen je Sektion werden mit summierter Anzahl geführt.
    """
    found: dict[tuple[str, str], int] = {}
    order: list[tuple[str, str]] = []
    # Wrapper-Knoten (Moxfield-Form) tragen die Anzahl und delegieren den
    # Namen an ein verschachteltes "card"-dict — dieses darf nicht
    # zusätzlich als eigener Eintrag zählen (Doppelzählung).
    card_children = set()
    for node, _ in _iter_dicts(payload):
        child = node.get("card")
        if isinstance(child, dict):
            card_children.add(id(child))
    for node, path in _iter_dicts(payload):
        if id(node) in card_children:
            continue
        name = _card_name(node)
        if name is None:
            continue
        # Heuristik gegen Fehlgriffe: Knoten, die selbst wie eine
        # Karten-Referenz aussehen, tragen typischerweise wenige,
        # bekannte Schlüssel oder einen verschachtelten "card"-Knoten.
        if "card" not in node and not (
            {"quantity", "count", "qty"} & set(node)
            or any(part.lower() in (
                "cardviews", "cards", "mainboard", "commanders",
                "sideboard", "creatures", "instants", "sorceries",
                "artifacts", "enchantments", "planeswalkers", "lands",
                "boards", "board") for part in path)
        ):
            continue
        section = ""
        for part in reversed(path):
            if part.lower() in (
                "commanders", "commander", "mainboard", "sideboard",
                "creatures", "instants", "sorceries", "artifacts",
                "enchantments", "planeswalkers", "lands", "battle",
                "companion",
            ):
                section = part
                break
        key = (name, section)
        if key not in found:
            order.append(key)
            found[key] = 0
        found[key] += _quantity(node)
    return [
        {"name": name, "quantity": found[(name, section)], "section": section}
        for name, section in order
    ]


_TEXT_LINE = re.compile(r"^\s*(\d+)\s*[x×]?\s+(.+?)\s*$")


def parse_deck_text(text: str) -> list[dict]:
    """Ersatz-Extraktion aus sichtbarem Text: Zeilen '4 Lightning Bolt'."""
    cards: list[dict] = []
    for line in text.splitlines():
        match = _TEXT_LINE.match(line)
        if match:
            cards.append({
                "name": match.group(2),
                "quantity": int(match.group(1)),
                "section": "",
            })
    return cards


def detect_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "edhrec" in host:
        return "edhrec"
    if "moxfield" in host:
        return "moxfield"
    if "archidekt" in host:
        return "archidekt"
    return "generic"


# ---------------------------------------------------------------------------
# URL-Quellen
# ---------------------------------------------------------------------------

def read_urls_file(path: Path) -> list[str]:
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def edhrec_urls_from_db(db_path: Path, limit: int,
                        commander_slug: str | None) -> list[str]:
    """Deckpreview-URLs aus den gespeicherten EDHREC-Deck-Einträgen."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        if commander_slug:
            rows = con.execute(
                "SELECT DISTINCT e.urlhash FROM edhrec_deck_entry e "
                "JOIN external_snapshot s ON s.snapshot_id = e.snapshot_id "
                "WHERE s.slug LIKE ? ORDER BY e.urlhash LIMIT ?",
                (f"%{commander_slug}%", limit),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT DISTINCT urlhash FROM edhrec_deck_entry "
                "ORDER BY urlhash LIMIT ?", (limit,),
            ).fetchall()
    finally:
        con.close()
    return [f"https://edhrec.com/deckpreview/{row[0]}" for row in rows]


def already_done(out_path: Path) -> set[str]:
    done: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("status") == "AVAILABLE":
                done.add(record.get("source_url", ""))
    return done


# ---------------------------------------------------------------------------
# Browser-Lauf
# ---------------------------------------------------------------------------

def run(urls: list[str], out_path: Path, profile_dir: Path,
        delay_min: float, delay_max: float, no_pause: bool,
        headless: bool) -> int:
    from playwright.sync_api import sync_playwright  # lazy: Parser ohne

    done = already_done(out_path)
    todo = [u for u in urls if u not in done]
    print(f"URLs gesamt: {len(urls)} · bereits vorhanden: "
          f"{len(urls) - len(todo)} · zu laden: {len(todo)}")
    if not todo:
        print("Nichts zu tun.")
        return 0

    written = 0
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            viewport={"width": 1400, "height": 900},
        )
        # Tab 1: Consent-Tab — bleibt offen stehen.
        tab1 = context.pages[0] if context.pages else context.new_page()
        tab1.goto(todo[0], wait_until="domcontentloaded")
        if not no_pause:
            print()
            print(">>> Tab 1 zeigt jetzt eine Deckseite.")
            print(">>> Bitte dort ggf. 'Accept All' anklicken und dann")
            print(">>> hier im Fenster ENTER drücken. Tab 1 bleibt offen.")
            input(">>> Bereit? [ENTER] ")
        # Tab 2: Arbeits-Tab.
        tab2 = context.new_page()

        payloads: list = []

        def on_response(response):
            try:
                ctype = response.headers.get("content-type", "")
                if "json" not in ctype:
                    return
                body = response.json()
            except Exception:
                return
            payloads.append(body)

        tab2.on("response", on_response)

        with out_path.open("a", encoding="utf-8") as out:
            for index, url in enumerate(todo, 1):
                payloads.clear()
                record = {
                    "source": detect_source(url),
                    "source_url": url,
                    "fetched_at_utc": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"),
                    "parser_version": PARSER_VERSION,
                    "deck_name": "",
                    "cards": [],
                    "status": "PARTIAL",
                    "note": "",
                }
                try:
                    response = tab2.goto(
                        url, wait_until="domcontentloaded", timeout=60000)
                    status_code = response.status if response else 0
                    if status_code in (403, 429):
                        print(f"[{index}/{len(todo)}] BLOCKIERT "
                              f"(HTTP {status_code}) — Lauf stoppt. "
                              f"Seite ggf. in Tab 1 prüfen.")
                        record["status"] = "BLOCKED"
                        record["note"] = f"http {status_code}"
                        out.write(json.dumps(record) + "\n")
                        out.flush()
                        break
                    tab2.wait_for_timeout(2500)
                    cards: list[dict] = []
                    for payload in payloads:
                        cards = parse_deck_payload(payload)
                        if len(cards) >= 40:
                            break
                    if len(cards) < 40:
                        # Eingebettetes JSON / sichtbarer Text als Ersatz.
                        content = tab2.content()
                        for blob in re.findall(
                                r'<script[^>]*type="application/json"[^>]*>'
                                r"(.*?)</script>", content, re.S):
                            try:
                                cards = parse_deck_payload(json.loads(blob))
                            except json.JSONDecodeError:
                                continue
                            if len(cards) >= 40:
                                break
                    if len(cards) < 40:
                        text_cards = parse_deck_text(tab2.inner_text("body"))
                        if len(text_cards) > len(cards):
                            cards = text_cards
                    record["cards"] = cards
                    total = sum(c["quantity"] for c in cards)
                    if len(cards) >= 40:
                        record["status"] = "AVAILABLE"
                    else:
                        record["note"] = (
                            f"nur {len(cards)} Karten extrahiert")
                    title = tab2.title()
                    record["deck_name"] = title
                    print(f"[{index}/{len(todo)}] {record['status']}: "
                          f"{len(cards)} Einträge / {total} Karten — {url}")
                    if record["status"] == "AVAILABLE":
                        written += 1
                except Exception as exc:  # noqa: BLE001 — Lauf robust halten
                    record["status"] = "PARTIAL"
                    record["note"] = f"{type(exc).__name__}: {exc}"[:200]
                    print(f"[{index}/{len(todo)}] FEHLER bei {url}: "
                          f"{record['note']}")
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                if index < len(todo):
                    time.sleep(random.uniform(delay_min, delay_max))
        print(f"Fertig. Neu verfügbare Decklisten: {written}. "
              f"Ausgabe: {out_path}")
        if not no_pause:
            input("ENTER zum Schließen des Browsers ")
        context.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--urls", type=Path, help="Textdatei, eine Deck-URL "
                                                "je Zeile")
    src.add_argument("--edhrec-from-db", action="store_true",
                     help="Deckpreview-URLs aus der Studio-Datenbank "
                          "edhrec_deck_entry aufbauen")
    parser.add_argument("--db", type=Path, default=Path.home() / ".local"
                        / "share" / "mtg-collection-deckbuilder"
                        / "deckbuild.sqlite3")
    parser.add_argument("--commander", default=None,
                        help="nur Decks dieses Commander-Slugs "
                             "(nur mit --edhrec-from-db)")
    parser.add_argument("--limit", type=int, default=200,
                        help="max. Decks je Lauf (Standard 200)")
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    parser.add_argument("--profile", type=Path, default=Path(DEFAULT_PROFILE),
                        help="persistentes Browser-Profil (Standard "
                             ".browser-profile)")
    parser.add_argument("--delay-min", type=float, default=2.5)
    parser.add_argument("--delay-max", type=float, default=5.0)
    parser.add_argument("--no-pause", action="store_true",
                        help="ohne Consent-/Schluss-Pausen laufen")
    parser.add_argument("--headless", action="store_true",
                        help="ohne sichtbares Fenster (für Tests; für "
                             "den echten Lauf NICHT empfohlen)")
    args = parser.parse_args(argv)

    if args.urls:
        urls = read_urls_file(args.urls)
    else:
        urls = edhrec_urls_from_db(args.db, args.limit, args.commander)
    urls = urls[: args.limit] if args.urls else urls
    return run(urls, args.out, args.profile, args.delay_min, args.delay_max,
               args.no_pause, args.headless)


if __name__ == "__main__":
    sys.exit(main())
