"""EDHREC card-page adapter — global card facts from EDHREC's public JSON.

Verified 2026-11-11 against https://json.edhrec.com/pages/cards/sol-ring.json
(the JSON twin of https://edhrec.com/cards/sol-ring). Structure as shipped:

  * ``container.json_dict.card``: ``name``, ``sanitized`` (the slug),
    ``id`` (a Scryfall *printing* id, kept verbatim as evidence),
    ``num_decks`` / ``potential_decks`` across ALL commander decks in
    EDHREC's index, and ``salt`` — EDHREC's salt score. Salt is a survey-
    based friction/annoyance indicator, NOT a strength measure; it is
    stored verbatim and must never be blended into a strength signal.
  * ``container.json_dict.cardlists``: labelled lists; ``Top Commanders``
    carries the commanders running this card most (per-commander
    num/potential decks). Category lists (``Top Cards``, ``Creatures``
    ...) are other cards of a category, not facts about this card, and
    are not captured.
  * ``panels.combocounts``: example combos naming this card (EDHREC's
    combo panel; partner sets + EDHREC combo-page hrefs), terminated by
    a ``See More...`` entry linking the combos index for the card. It
    publishes NO numeric combo total — presence/examples only, never a
    count we invent.
  * ``similar``: names of similar cards (EDHREC's own grouping).

Global inclusion here is the plain fraction num_decks/potential_decks
over EDHREC's whole index — a different denominator from the per-
commander bracket cohorts in :mod:`deckbuild_studio.edhrec`; the two
are never mixed.
"""
from __future__ import annotations

import json

from .edhrec import ParseError, VerificationError

PARSER_ID = "edhrec-card-json/1.0.0"

__all__ = ["PARSER_ID", "ParseError", "VerificationError", "parse_card_json"]


def _int_or_none(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def _float_or_none(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def parse_card_json(text: str, *, expected_name: str, expected_slug: str) -> dict:
    """Parse one EDHREC card JSON document and verify it is the card we
    asked for (name + slug must both match; a mismatch means the slug
    resolved to a different card and nothing may be stored)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"EDHREC card JSON invalid: {exc}") from exc
    json_dict = ((data.get("container") or {}).get("json_dict") or {})
    card = json_dict.get("card") or {}
    name = card.get("name")
    front = expected_name.split(" // ")[0]
    if name not in (expected_name, front):
        raise VerificationError(
            f"card JSON name mismatch: {name!r} != {expected_name!r}")
    slug = card.get("sanitized") or card.get("slug")
    if slug != expected_slug:
        raise VerificationError(
            f"card JSON slug mismatch: {slug!r} != {expected_slug!r}")
    num = _int_or_none(card.get("num_decks"))
    potential = _int_or_none(card.get("potential_decks"))
    inclusion = None
    if num is not None and potential:
        inclusion = num / potential
    top_commanders: list[dict] = []
    for cardlist in json_dict.get("cardlists") or []:
        if cardlist.get("header") != "Top Commanders":
            continue
        for view in cardlist.get("cardviews") or []:
            top_commanders.append({
                "name": view.get("name"),
                "slug": view.get("slug") or view.get("sanitized"),
                "num_decks": _int_or_none(view.get("num_decks")),
                "potential_decks": _int_or_none(view.get("potential_decks")),
            })
    combo_examples: list[dict] = []
    combos_page: str | None = None
    panels = data.get("panels") or {}
    for entry in panels.get("combocounts") or []:
        value = (entry.get("value") or "").strip()
        href = entry.get("href") or ""
        if value.startswith("See More"):
            combos_page = href or None
            continue
        if value:
            combo_examples.append({
                "cards": [part.strip() for part in value.split(" + ") if part.strip()],
                "href": href,
            })
    return {
        "name": name,
        "slug": slug,
        "scryfall_id": card.get("id"),
        "num_decks": num,
        "potential_decks": potential,
        "inclusion": inclusion,
        "salt": _float_or_none(card.get("salt")),
        "top_commanders": top_commanders,
        "combo_examples": combo_examples,
        "combos_page": combos_page,
        "similar": [str(n) for n in (data.get("similar") or [])],
        "parser": PARSER_ID,
    }
