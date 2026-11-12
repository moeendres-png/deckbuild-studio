"""Type-line parser — deterministic, versioned, lossless.

Parses one face's Scryfall ``type_line`` (e.g. ``"Legendary Creature —
Angel"``, ``"Basic Land — Plains"``, ``"Enchantment — Aura"``) into
supertypes / types / subtypes so they can be stored and queried as
facts instead of substrings. The parser never drops a token: a token
left of the dash that is neither a known supertype nor a known card
type is recorded as a *type* (new card types appear over time; losing
one silently would break the completeness contract of the category
layer). Subtypes are every token right of the dash, verbatim.

``parse_type_line`` is pure and offline; ``TYPE_PARSER_VERSION`` is
recorded with every derived fact row (provenance).
"""
from __future__ import annotations

TYPE_PARSER_VERSION = "type-parser/1.0.0"

SUPERTYPES = frozenset({"Basic", "Legendary", "Snow", "World", "Ongoing"})

CARD_TYPES = frozenset({
    "Artifact", "Battle", "Conspiracy", "Creature", "Dungeon",
    "Enchantment", "Instant", "Kindred", "Land", "Phenomenon", "Plane",
    "Planeswalker", "Scheme", "Sorcery", "Tribal", "Vanguard",
})

# Scryfall writes the dash as " — " (em dash). Older / hand-written
# fixtures occasionally use en dash or hyphen; accept all three, but
# split only on a dash surrounded by spaces so subtype names that
# contain hyphens (none known, but cheap insurance) survive intact.
_DASHES = (" — ", " – ", " - ")


def split_type_line(type_line: str) -> tuple[str, str]:
    """(left, right) of a type line; right is '' when there is no dash."""
    for dash in _DASHES:
        if dash in type_line:
            left, _, right = type_line.partition(dash)
            return left.strip(), right.strip()
    return type_line.strip(), ""


def parse_type_line(type_line: str | None) -> dict[str, list[str]]:
    """Parse one face's type line into supertypes / types / subtypes.

    Order is preserved as printed. Empty / missing input parses to
    three empty lists (the caller records coverage separately — a card
    with no type line is a data gap, not a parse result)."""
    out: dict[str, list[str]] = {"supertypes": [], "types": [], "subtypes": []}
    if not type_line:
        return out
    left, right = split_type_line(type_line)
    for token in left.split():
        if token in SUPERTYPES:
            out["supertypes"].append(token)
        else:
            # known card type OR unknown token: both are types, so no
            # token is ever lost.
            out["types"].append(token)
    if right:
        out["subtypes"] = right.split()
    return out


def split_faces(combined: str | None) -> list[str]:
    """Split a combined multi-face string (``"A // B"``) into faces.

    Scryfall joins face values (names, type lines) with ``" // "`` at
    card level. A single-face value yields a one-element list."""
    if not combined:
        return []
    return [part.strip() for part in combined.split(" // ")]
