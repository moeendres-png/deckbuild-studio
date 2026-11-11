"""Dynamic commander eligibility — data-based pre-check, NOT a rules engine.

A card is a standalone commander candidate iff ALL hold:
  * Scryfall ``legalities.commander == 'legal'`` (this IS the banlist check:
    banned cards carry ``not_legal``), and
  * it is available in the collection (physical copies exist), and
  * one of:
      - the FRONT face type line is a Legendary Creature (DFC/MDFC: only the
        playable front face counts — a legendary back face alone does NOT
        qualify, e.g. Faithful Squire // Kaiso, Memory of Loyalty), or
      - the front-face oracle text explicitly says "can be your commander".

Pairing mechanisms (Partner, Partner with, Friends Forever,
Choose a Background / Background, Doctor's Companion) are recorded as data
(``pairing`` field) for pair validation; they never make a non-legendary or
non-creature card a standalone commander. Cards whose facts are missing
(no Scryfall row / unknown legality) are reported as ``needs_review``,
never silently released.
"""
from __future__ import annotations

import re
import sqlite3

PAIRING_PATTERNS = {
    # Plain Partner is always printed as "Partner (<reminder>)" at the
    # start of a line. "Partner with X" must NOT match here (QA P1.6):
    # it is a restricted pairing with exactly one named card.
    "partner": re.compile(r"^Partner\s*\(", re.M),
    "partner_with": re.compile(r"Partner with ([^\n(]+)"),
    "friends_forever": re.compile(r"Friends forever"),
    "choose_a_background": re.compile(r"Choose a Background"),
    "doctors_companion": re.compile(r"Doctor's companion"),
}


def pairing_mechanisms(front_text: str | None, front_type: str | None) -> list[str]:
    text = front_text or ""
    found = [name for name, pat in PAIRING_PATTERNS.items() if pat.search(text)]
    if front_type and "Background" in front_type:
        found.append("background")
    return found


def partner_with_target(front_text: str | None) -> str | None:
    """The card name X named by 'Partner with X', or None.

    The reminder text in parentheses is stripped; X is the partner's
    full card name as printed (e.g. 'Pir, Imaginative Rascal')."""
    m = PAIRING_PATTERNS["partner_with"].search(front_text or "")
    if not m:
        return None
    return m.group(1).strip() or None


def assess(row: sqlite3.Row) -> dict[str, object]:
    """Assess one inventory/scryfall-joined row (see Store.inventory_rows)."""
    name = row["name"]
    base: dict[str, object] = {
        "oracle_id": row["oracle_id"], "name": name,
        "color_identity": row["scryfall_ci"] or "",
        "image_uri": row["image_uri"],
    }
    if row["commander_legality"] is None:
        return {**base, "eligible": False, "status": "needs_review",
                "reason": "no Scryfall facts / unknown commander legality"}
    if row["commander_legality"] != "legal":
        return {**base, "eligible": False, "status": "not_legal",
                "reason": f"legalities.commander={row['commander_legality']}"}
    front_type = row["front_type_line"] or ""
    front_text = row["front_oracle_text"] or ""
    pairing = pairing_mechanisms(front_text, front_type)
    front_legendary_creature = "Legendary" in front_type and "Creature" in front_type
    explicit = "can be your commander" in front_text.lower()
    if front_legendary_creature:
        return {**base, "eligible": True, "status": "eligible",
                "reason": "legendary creature on front face", "pairing": pairing}
    if explicit:
        return {**base, "eligible": True, "status": "eligible",
                "reason": "oracle text: can be your commander", "pairing": pairing}
    return {**base, "eligible": False, "status": "not_commander",
            "reason": "front face is not a legendary creature and grants no "
                      "commander permission (legendary back face does not count)",
            "pairing": pairing}


def commander_candidates(store, collection_id: str) -> dict[str, list[dict]]:
    """Split the collection's distinct identities into eligible / needs_review / rest."""
    available = store.available_by_oracle(collection_id)
    eligible: list[dict] = []
    needs_review: list[dict] = []
    seen: set[str] = set()
    for row in store.inventory_rows(collection_id):
        oid = row["oracle_id"]
        if oid in seen or available.get(oid, 0) <= 0:
            continue
        seen.add(oid)
        result = assess(row)
        result["available"] = available.get(oid, 0)
        if result["eligible"]:
            eligible.append(result)  # type: ignore[arg-type]
        elif result["status"] == "needs_review":
            needs_review.append(result)  # type: ignore[arg-type]
    eligible.sort(key=lambda r: str(r["name"]))
    return {"eligible": eligible, "needs_review": needs_review}
