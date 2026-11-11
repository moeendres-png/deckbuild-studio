"""Read models computed from stored rows, each figure with its denominator.

Generalized from the upstream studio (``queries.py`` /
``builder.py``): upstream computes corpus inclusion over imported
*source* decks; this project has no external deck corpus — the honest
local equivalent is inclusion over the owner's **own decks** of a
collection. Only each deck's **latest revision** counts, so iterating
on a deck does not inflate the figures.
"""
from __future__ import annotations

import re
from math import comb

from .store import Store

_TYPE_ORDER = ("Creature", "Planeswalker", "Battle", "Instant", "Sorcery",
               "Artifact", "Enchantment", "Land")
_SYMBOL = re.compile(r"\{([^}]+)\}")


def main_type(type_line: str | None) -> str:
    text = type_line or ""
    front = text.split("//")[0]
    for kind in _TYPE_ORDER:
        if kind in front:
            return kind
    return "Other"


def _latest_revision_ids(store: Store, collection_id: str) -> list[str]:
    """The latest revision id of every deck of the collection."""
    rows = store.conn.execute(
        "SELECT dr.revision_id, dr.deck_id, dr.created_at, dr.rowid AS rid "
        "FROM deck_revision dr JOIN deck d USING (deck_id) "
        "WHERE d.collection_id = ? ORDER BY dr.deck_id, dr.created_at, dr.rowid",
        (collection_id,)).fetchall()
    latest: dict[str, str] = {}
    for row in rows:  # ascending: the last row per deck wins
        latest[row["deck_id"]] = row["revision_id"]
    return list(latest.values())


def own_deck_inclusion(store: Store, collection_id: str) -> dict:
    """In how many of the owner's own decks each card appears.

    Denominator = number of decks of the collection (latest revision
    each). A share is ``None``-free by construction here — with zero
    decks the card list is empty and the denominator is reported as 0,
    never dressed up as a percentage.
    """
    revision_ids = _latest_revision_ids(store, collection_id)
    total = len(revision_ids)
    cards: list[dict] = []
    if revision_ids:
        marks = ",".join("?" for _ in revision_ids)
        for row in store.conn.execute(
                f"SELECT dc.oracle_id, s.name AS name, "
                f"COUNT(DISTINCT dc.revision_id) AS decks, "
                f"SUM(dc.quantity) AS copies "
                f"FROM deck_card dc JOIN deck_revision dr "
                f"ON dr.revision_id = dc.revision_id "
                f"LEFT JOIN scryfall_card s ON s.oracle_id = dc.oracle_id "
                f"WHERE dc.revision_id IN ({marks}) AND dc.is_commander = 0 "
                f"GROUP BY dc.oracle_id ORDER BY decks DESC, copies DESC, name",
                revision_ids):
            cards.append({
                "oracle_id": row["oracle_id"], "name": row["name"],
                "decks": int(row["decks"]), "of_decks": total,
                "share": (int(row["decks"]) / total) if total else None,
                "copies": int(row["copies"] or 0),
            })
    return {"collection_id": collection_id, "decks_total": total,
            "basis": "latest revision of each own deck",
            "cards": cards}


def deck_shape(store: Store, entries: dict[str, int]) -> dict:
    """Type distribution, mana curve and colour pips of a deck list.

    Mirrors upstream ``builder.deck_shape``: figures describe the list
    itself (main deck incl. commander entries as passed in)."""
    types: dict[str, int] = {}
    curve: dict[str, int] = {}
    pips: dict[str, int] = {}
    lands = 0
    total = 0
    for oracle_id, qty in entries.items():
        row = store.scryfall(oracle_id)
        if row is None:
            continue
        total += qty
        kind = main_type(row["front_type_line"] or row["type_line"])
        types[kind] = types.get(kind, 0) + qty
        if kind == "Land":
            lands += qty
        else:
            mv = row["mana_value"]
            bucket = "7+" if mv is None or mv >= 7 else str(int(mv))
            curve[bucket] = curve.get(bucket, 0) + qty
        for symbol in _SYMBOL.findall(row["mana_cost"] or ""):
            if symbol in "WUBRG":
                pips[symbol] = pips.get(symbol, 0) + qty
    return {"total_cards": total, "types": types, "mana_curve": curve,
            "color_pips": pips, "lands": lands}


def _hypergeom_at_least(total_n: int, success_k: int, draws: int,
                          min_hits: int) -> float | None:
    if total_n < draws or draws <= 0 or success_k < 0 or success_k > total_n:
        return None
    misses = total_n - success_k
    probability = 0.0
    for hits in range(min_hits, min(success_k, draws) + 1):
        if draws - hits > misses:
            continue
        probability += comb(success_k, hits) * comb(misses, draws - hits)
    return probability / comb(total_n, draws)


def draw_probabilities(deck_size: int, lands: int, *,
                       hand: int = 7) -> dict:
    """Hypergeometric land probabilities for the opening hand (and by
    turn 3 on the play, i.e. hand + 3 draws) — pure combinatorics over
    the stated deck size, as upstream ``builder.draw_probabilities``."""
    if deck_size <= 0 or lands < 0 or lands > deck_size:
        return {"deck_size": deck_size, "lands": lands,
                "opening_hand": None, "by_turn_3": None}
    opening = {f"at_least_{k}": _hypergeom_at_least(deck_size, lands, hand, k)
               for k in (1, 2, 3, 4)}
    by_turn_3 = {f"at_least_{k}": _hypergeom_at_least(
        deck_size, lands, hand + 3, k) for k in (1, 2, 3, 4)}
    return {"deck_size": deck_size, "lands": lands,
            "opening_hand": opening, "by_turn_3": by_turn_3}
