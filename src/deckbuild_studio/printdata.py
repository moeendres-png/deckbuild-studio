"""Scryfall print facts — LOCAL derivation from the cached bulk file.

No network access. Aggregates every paper printing of each oracle
identity in the already-downloaded default-cards bulk (the same file
:func:`deckbuild_studio.scryfall.import_scryfall` consumes) into
objective print facts:

  * how many printings and distinct sets exist,
  * which rarities the card was printed at (and the most common one),
  * first / last release year,
  * the cheapest non-foil paper price per currency (EUR / USD) and the
    printing (``set:collector_number``) that carries it.

Prices are point-in-time values OF THE BULK SNAPSHOT — the source row
registered for the bulk file carries its SHA-256 and import date, and
every fact row references it. A printing without a published price
contributes nothing; a card with no priced printing keeps NULL, never
0. Prices are budget/context facts only — never a strength signal.
"""
from __future__ import annotations

import json
from pathlib import Path

from .scryfall import NONPLAYABLE_LAYOUTS, _objects
from .store import Store, sha256_file, utcnow

PARSER_ID = "scryfall-print-facts/1.0.0"

RARITY_ORDER = {"common": 0, "uncommon": 1, "rare": 2, "mythic": 3,
                "special": 4, "bonus": 5}


def _price(raw) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def aggregate_printings(cards) -> dict[str, dict]:
    """Pure aggregation over bulk card objects (print level)."""
    agg: dict[str, dict] = {}
    for card in cards:
        oracle_id = card.get("oracle_id")
        if not oracle_id or card.get("layout") in NONPLAYABLE_LAYOUTS:
            continue
        games = card.get("games") or []
        if games and "paper" not in games:
            continue  # digital-only printing: no paper fact
        entry = agg.setdefault(oracle_id, {
            "prints": 0, "sets": set(), "rarities": set(),
            "first": None, "last": None,
            "min_eur": None, "min_eur_printing": None,
            "min_usd": None, "min_usd_printing": None,
        })
        entry["prints"] += 1
        if card.get("set"):
            entry["sets"].add(card["set"])
        if card.get("rarity"):
            entry["rarities"].add(card["rarity"])
        released = (card.get("released_at") or "")[:4]
        if released.isdigit():
            year = int(released)
            entry["first"] = year if entry["first"] is None else min(entry["first"], year)
            entry["last"] = year if entry["last"] is None else max(entry["last"], year)
        prices = card.get("prices") or {}
        printing = f"{card.get('set')}:{card.get('collector_number')}"
        for key, field in (("eur", "min_eur"), ("usd", "min_usd")):
            value = _price(prices.get(key))
            if value is None:
                continue
            if entry[field] is None or value < entry[field]:
                entry[field] = value
                entry[field + "_printing"] = printing
    return agg


def derive_print_facts(store: Store, bulk_path: str | Path) -> dict:
    """(Re)build ``card_print_fact`` from a local bulk file. Idempotent:
    the table is replaced wholesale, keyed to the bulk file's source."""
    bulk_path = Path(bulk_path)
    agg = aggregate_printings(_objects(bulk_path))
    digest = sha256_file(bulk_path)
    source_id = f"scryfall:{digest[:16]}"
    store.add_source(source_id=source_id,
                     source_name="Scryfall bulk (default-cards)",
                     source_url="https://scryfall.com/docs/api/bulk-data",
                     file_name=bulk_path.name, sha256=digest)
    now = utcnow()
    rows = []
    for oracle_id, e in sorted(agg.items()):
        rarities = sorted(e["rarities"], key=lambda r: RARITY_ORDER.get(r, 99))
        rows.append((
            oracle_id, e["prints"], len(e["sets"]),
            json.dumps(rarities), rarities[0] if rarities else None,
            e["first"], e["last"], e["min_eur"], e["min_eur_printing"],
            e["min_usd"], e["min_usd_printing"], source_id, PARSER_ID, now))
    with store.conn:
        store.conn.execute("DELETE FROM card_print_fact")
        store.conn.executemany(
            "INSERT INTO card_print_fact(oracle_id,prints_count,sets_count,"
            "rarities_json,min_rarity,first_release_year,last_release_year,"
            "min_eur,min_eur_printing,min_usd,min_usd_printing,source_id,"
            "parser_version,derived_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows)
    return {
        "identities": len(rows),
        "with_eur_price": sum(1 for r in rows if r[7] is not None),
        "with_usd_price": sum(1 for r in rows if r[9] is not None),
        "source_id": source_id,
        "parser": PARSER_ID,
    }
