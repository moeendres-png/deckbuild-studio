#!/usr/bin/env python3
"""Documented browser-workflow check for the Deckbuild Studio UI (QA P0.3).

Boots the REAL server (subprocess, `mtg-deckbuilder serve`) against a
throwaway data folder seeded with a tiny synthetic collection, then
drives the exact workflow a browser user performs, over plain HTTP:

  1. GET  /                       -> page loads, deck-flow controls present
  2. GET  /api/commanders         -> pick the eligible commander
  3. GET  /api/pool               -> legal pool for that commander
  4. POST /api/decks/validate     -> verdict for a full 100-card deck
  5. POST /api/decks              -> save (status 'legal')
  6. POST /api/decks (parent)     -> save a variant revision
  7. GET  /api/decks/{id}/revisions, /api/decks/revision/{id} (load)
  8. GET  /api/decks/compare      -> diff of the two revisions
  9. GET  /api/decks/{rev}/export -> text export + X-Deck-Status header
 10. DELETE /api/decks/{id}       -> deck removed

Usage:  .venv/bin/python scripts/browser_workflow_check.py
Exit code 0 = every step behaved as documented. No private data is used.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

PORT = 18765
BASE = f"http://127.0.0.1:{PORT}"

CARDS = [
    {"id": "p1", "oracle_id": "30000000-0000-4000-8000-000000000001",
     "name": "Alara, Workflow Sovereign", "type_line": "Legendary Creature — Human Noble",
     "oracle_text": "Vigilance", "color_identity": ["G", "W"], "colors": ["G", "W"],
     "mana_cost": "{2}{G}{W}", "cmc": 4.0, "layout": "normal",
     "legalities": {"commander": "legal"}, "image_uris": {"normal": "https://example.invalid/a.jpg"}},
    {"id": "p2", "oracle_id": "30000000-0000-4000-8000-000000000002",
     "name": "Plains", "type_line": "Basic Land — Plains", "oracle_text": "",
     "color_identity": [], "colors": [], "mana_cost": "", "cmc": 0.0, "layout": "normal",
     "legalities": {"commander": "legal"}, "image_uris": {"normal": "https://example.invalid/p.jpg"}},
    {"id": "p3", "oracle_id": "30000000-0000-4000-8000-000000000003",
     "name": "Forest", "type_line": "Basic Land — Forest", "oracle_text": "",
     "color_identity": [], "colors": [], "mana_cost": "", "cmc": 0.0, "layout": "normal",
     "legalities": {"commander": "legal"}, "image_uris": {"normal": "https://example.invalid/f.jpg"}},
]
CMD, PLAINS, FOREST = (c["oracle_id"] for c in CARDS)


def http(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (localhost check)
        raw = resp.read().decode()
        return resp.status, resp.headers, raw


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {label}  {detail}")
    if not cond:
        raise SystemExit(f"workflow check FAILED at: {label}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="dbs-workflow-"))
    data = tmp / "data"
    data.mkdir()
    sf = tmp / "cards.jsonl"
    sf.write_text("".join(json.dumps(c) + "\n" for c in CARDS))
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Kartensammlung"
    ws.append(["Kartenname", "Anzahl", "Standort", "Farbidentität",
               "Manakosten", "Kartentyp", "Kartentext"])
    for name, qty in (("Alara, Workflow Sovereign", 1), ("Plains", 60), ("Forest", 120)):
        ws.append([name, qty, "Foundation", "", "", "", ""])
    xlsx = tmp / "collection.xlsx"
    wb.save(xlsx)

    env = {**os.environ, "MTG_DECKBUILDER_DATA": str(data)}
    cli = [sys.executable, "-m", "deckbuild_studio.cli"]
    subprocess.run([*cli, "import-scryfall", str(sf)], env=env, check=True,
                   capture_output=True)
    subprocess.run([*cli, "import-inventory", str(xlsx)], env=env, check=True,
                   capture_output=True)
    print(f"seeded throwaway data folder: {data}")

    server = subprocess.Popen([*cli, "serve", "--port", str(PORT)], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                status, _, _ = http("GET", "/api/status")
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("server did not come up")

        status, _, html = http("GET", "/")
        check("GET / page loads", status == 200)
        for el in ("savedeck", "variantdeck", "deckselect", "revisionselect",
                   "deletedeck", "comparebtn"):
            check(f"page contains #{el}", f'id="{el}"' in html)

        _, _, raw = http("GET", "/api/commanders?collection_id=foundation-schwarze-box")
        eligible = json.loads(raw)["eligible"]
        check("commander eligible", [c["oracle_id"] for c in eligible] == [CMD])

        entries = {PLAINS: 50, FOREST: 49}
        _, _, raw = http("POST", "/api/decks/validate",
                         {"collection_id": "foundation-schwarze-box", "name": "W",
                          "commander_oracle_ids": [CMD], "entries": entries})
        check("validate legal deck", json.loads(raw)["valid"] is True)

        _, _, raw = http("POST", "/api/decks",
                         {"collection_id": "foundation-schwarze-box", "name": "Workflow Deck",
                          "commander_oracle_ids": [CMD], "entries": entries})
        saved = json.loads(raw)
        check("save deck -> legal", saved["status"] == "legal", saved["revision_id"])

        entries2 = {PLAINS: 49, FOREST: 50}
        _, _, raw = http("POST", "/api/decks",
                         {"collection_id": "foundation-schwarze-box", "name": "Workflow Deck",
                          "commander_oracle_ids": [CMD], "entries": entries2,
                          "parent_revision_id": saved["revision_id"]})
        variant = json.loads(raw)
        check("save variant revision", variant["deck_id"] == saved["deck_id"])

        _, _, raw = http("GET", f"/api/decks/{saved['deck_id']}/revisions")
        check("revision list has 2", len(json.loads(raw)) == 2)
        _, _, raw = http("GET", f"/api/decks/revision/{variant['revision_id']}")
        check("load revision", json.loads(raw)["entries"] == entries2)

        _, _, raw = http("GET", f"/api/decks/compare?a={saved['revision_id']}"
                               f"&b={variant['revision_id']}")
        diff = json.loads(raw)
        check("compare shows change",
              diff["changed"].get(PLAINS) == [50, 49] and diff["names"][FOREST] == "Forest")

        _, headers, text = http("GET", f"/api/decks/{variant['revision_id']}/export")
        total = sum(int(line.split(" ", 1)[0]) for line in text.strip().splitlines())
        check("export legal + header",
              headers.get("X-Deck-Status") == "legal" and "ENTWURF" not in text
              and total == 100, f"{len(text.strip().splitlines())} grouped lines, {total} cards")

        _, _, raw = http("DELETE", f"/api/decks/{saved['deck_id']}")
        check("delete deck", json.loads(raw)["ok"] is True)
        _, _, raw = http("GET", "/api/decks?collection_id=foundation-schwarze-box")
        check("deck list empty after delete", json.loads(raw) == [])
    finally:
        server.terminate()
        server.wait(timeout=10)
    print("browser workflow check: ALL STEPS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
