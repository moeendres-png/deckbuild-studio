"""Card roles for Deckbuild Studio — generalized from the upstream studio.

Upstream (commander-playtest-lab ``src/commander_lab/studio/roles.py``)
classifies cards with Scryfall-Tagger labels fetched per color identity
into ``card_role`` claims with origins (tagger / crosswalk / oracle-text
review). That pipeline is corpus- and fetch-specific; this project keeps
the *taxonomy* and the *origin discipline* and derives its claims from
data it already holds locally:

* ``ORACLE_TEXT_HEURISTIC`` — conservative regex heuristics over the
  locally stored Scryfall oracle text / type line. A heuristic claim is
  a search aid, never a measured fact; it is labelled as such wherever
  it is shown.
* ``STRUCTURAL_PROFILE`` — the structural role profiles imported via
  ``import-reference-data`` (``reference_role_profile``). Those are
  model estimates (``structural_model_estimates``), not observations;
  their roles are stored verbatim (they may exceed this taxonomy) and
  always carry the estimate origin.

Claims live in ``card_role(oracle_id, role, origin)`` and are rebuilt
deterministically by :func:`rebuild_roles` — no network access, no
collection data leaves the machine.
"""
from __future__ import annotations

import re

from .store import Store

# role -> upstream Scryfall-Tagger label (taxonomy adopted verbatim).
ROLES: dict[str, str] = {
    "ramp": "ramp",
    "mana_rock": "mana-rock",
    "mana_dork": "mana-dork",
    "land_ramp": "land-ramp",
    "card_draw": "draw",
    "card_advantage": "card-advantage",
    "cantrip": "cantrip",
    "tutor": "tutor",
    "removal": "removal",
    "board_wipe": "board-wipe",
    "counterspell": "counterspell",
    "bounce": "bounce",
    "flicker": "flicker",
    "recursion": "recursion",
    "protection": "protection",
    "graveyard_hate": "graveyard-hate",
    "lifegain": "lifegain",
}

ROLE_LABELS_DE: dict[str, str] = {
    "ramp": "Ramp", "mana_rock": "Mana Rock", "mana_dork": "Mana Dork",
    "land_ramp": "Land-Ramp", "card_draw": "Kartenzug",
    "card_advantage": "Kartenvorteil", "cantrip": "Cantrip",
    "tutor": "Tutor", "removal": "Removal", "board_wipe": "Board Wipe",
    "counterspell": "Counterspell", "bounce": "Bounce",
    "flicker": "Flicker", "recursion": "Reanimation/Rückholung",
    "protection": "Schutz", "graveyard_hate": "Friedhof-Hate",
    "lifegain": "Lebensgewinn",
}

ORIGIN_HEURISTIC = "ORACLE_TEXT_HEURISTIC"
ORIGIN_PROFILE = "STRUCTURAL_PROFILE"
ORIGINS = (ORIGIN_HEURISTIC, ORIGIN_PROFILE)
HEURISTIC_LABEL = "Heuristik aus Oracle-Text (lokal abgeleitet, keine Beobachtung)"
PROFILE_LABEL = "Strukturelle Schätzung (Modell) — keine Beobachtungsdaten"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS card_role (
    oracle_id TEXT NOT NULL,
    role TEXT NOT NULL,
    origin TEXT NOT NULL,
    PRIMARY KEY (oracle_id, role, origin)
);
CREATE INDEX IF NOT EXISTS card_role_role ON card_role(role);
"""


def ensure_schema(store: Store) -> None:
    store.conn.executescript(_SCHEMA)


# --- heuristic classification -------------------------------------------
# Conservative patterns over the front-face oracle text (lowercased).
# Each rule mirrors the everyday meaning of the upstream tagger label;
# false negatives are acceptable, false positives are what we avoid.
_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("counterspell", re.compile(r"counter target (spell|activated|triggered)")),
    ("board_wipe", re.compile(
        r"(destroy|exile) all (creatures|permanents|nonland|artifacts|enchantments)"
        r"|all creatures get -|each player sacrifices")),
    ("land_ramp", re.compile(
        r"search your library for (a|up to [^.]*?)basic land|search your library "
        r"for a [^.]*land card[^.]*put (it|that card|them) onto the battlefield")),
    ("tutor", re.compile(r"search your library for a card")),
    ("graveyard_hate", re.compile(
        r"exile (target card from a graveyard|all cards from (a|all) graveyard)")),
    ("flicker", re.compile(
        r"exile [^.]*then return (it|that card|them) to the battlefield"
        r"|exile target [^.]*return it to the battlefield")),
    ("recursion", re.compile(
        r"return target [^.]*card from your graveyard to (the battlefield|your hand)"
        r"|return [^.]*from your graveyard to the battlefield")),
    ("bounce", re.compile(r"return target [^.]*to its owner's hand")),
    ("removal", re.compile(
        r"(destroy|exile) target (creature|artifact|enchantment|permanent|planeswalker|nonland)"
        r"|target creature gets -\d+/-\d+ until end of turn"
        r"|deals \d+ damage to (any target|target creature|target planeswalker)")),
    ("card_advantage", re.compile(
        r"draw (two|three|four|five|\d+) cards|draws? cards equal to"
        r"|draw a card for each")),
    ("card_draw", re.compile(r"draws? (a|one|two|three|x|\d+) cards?")),
    ("lifegain", re.compile(r"(you )?gain[s]? \d+ life|gains? [^.]*lifelink")),
    ("protection", re.compile(
        r"(gains?|has) (hexproof|indestructible|protection from)"
        r"|prevent all damage that would be dealt to")),
]

_ADD_MANA = re.compile(r"\{t\}[^.]*add \{|add \{[wubrgcxs0-9]|[.]\s*add \{")
_SEARCH_LAND_PUT_HAND = re.compile(
    r"search your library for a [^.]*land card[^.]*to your hand")


def classify_text(oracle_text: str | None, type_line: str | None,
                  mana_value: float | None) -> set[str]:
    """Heuristic roles of one card from its (front) oracle text/type line."""
    text = (oracle_text or "").lower()
    types = (type_line or "")
    roles: set[str] = set()
    for role, pattern in _RULES:
        if pattern.search(text):
            roles.add(role)
    if "land" not in types.lower() and _ADD_MANA.search(text):
        if "Artifact" in types:
            roles.add("mana_rock")
        elif "Creature" in types:
            roles.add("mana_dork")
        roles.add("ramp")
    if "land_ramp" in roles:
        roles.add("ramp")
    if _SEARCH_LAND_PUT_HAND.search(text):
        roles.add("land_ramp")
        roles.add("ramp")
    if "card_draw" in roles and mana_value is not None and mana_value <= 2 \
            and any(t in types for t in ("Instant", "Sorcery")):
        roles.add("cantrip")
    return roles


def rebuild_roles(store: Store) -> dict:
    """Rebuild all role claims from local data (deterministic, offline).

    Heuristic claims come from the Scryfall store; profile claims are
    copied from ``reference_role_profile`` when that import exists.
    Returns counts only.
    """
    ensure_schema(store)
    rows = store.conn.execute(
        "SELECT oracle_id, front_oracle_text, oracle_text, front_type_line, "
        "type_line, mana_value FROM scryfall_card").fetchall()
    claims: list[tuple[str, str, str]] = []
    for row in rows:
        text = row["front_oracle_text"] or row["oracle_text"]
        types = row["front_type_line"] or row["type_line"]
        for role in classify_text(text, types, row["mana_value"]):
            claims.append((row["oracle_id"], role, ORIGIN_HEURISTIC))
    profile_cards = 0
    have_profiles = store.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='reference_role_profile'").fetchone()
    if have_profiles:
        import json
        for prow in store.conn.execute(
                "SELECT oracle_id, roles_json FROM reference_role_profile "
                "WHERE oracle_id IS NOT NULL"):
            try:
                roles = json.loads(prow["roles_json"] or "[]")
            except (TypeError, ValueError):
                roles = []
            profile_cards += 1
            for role in roles:
                if isinstance(role, str) and role:
                    claims.append((prow["oracle_id"], role, ORIGIN_PROFILE))
    with store.conn:
        store.conn.execute("DELETE FROM card_role")
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_role(oracle_id, role, origin) "
            "VALUES (?, ?, ?)", claims)
    by_origin: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for row in store.conn.execute(
            "SELECT origin, COUNT(*) AS n FROM card_role GROUP BY origin"):
        by_origin[row["origin"]] = int(row["n"])
    for row in store.conn.execute(
            "SELECT role, COUNT(*) AS n FROM card_role GROUP BY role"):
        by_role[row["role"]] = int(row["n"])
    return {"cards_classified": len(rows), "claims": len(claims),
            "profile_cards": profile_cards,
            "by_origin": by_origin, "by_role": by_role}


def card_roles(store: Store, oracle_id: str) -> dict[str, list[str]]:
    """role -> [origins] for one card ({} before the first rebuild)."""
    ensure_schema(store)
    out: dict[str, list[str]] = {}
    for row in store.conn.execute(
            "SELECT role, origin FROM card_role WHERE oracle_id = ? "
            "ORDER BY role, origin", (oracle_id,)):
        out.setdefault(row["role"], []).append(row["origin"])
    return out


def roles_map(store: Store, oracle_ids: list[str]) -> dict[str, dict[str, list[str]]]:
    ensure_schema(store)
    out: dict[str, dict[str, list[str]]] = {}
    if not oracle_ids:
        return out
    marks = ",".join("?" for _ in oracle_ids)
    for row in store.conn.execute(
            f"SELECT oracle_id, role, origin FROM card_role "
            f"WHERE oracle_id IN ({marks}) ORDER BY role, origin",
            list(oracle_ids)):
        out.setdefault(row["oracle_id"], {}).setdefault(
            row["role"], []).append(row["origin"])
    return out


def deck_role_counts(store: Store, entries: dict[str, int]) -> dict[str, int]:
    """How many cards of a deck list (oracle_id -> qty) carry each role.

    Mirrors upstream ``builder.deck_roles``: a card may carry several
    roles; heuristic and profile claims are counted together here —
    origins stay visible per card via :func:`card_roles`.
    """
    counts: dict[str, int] = {}
    rmap = roles_map(store, list(entries))
    for oracle_id, roles in rmap.items():
        qty = entries.get(oracle_id, 0)
        for role in roles:
            counts[role] = counts.get(role, 0) + qty
    return counts


def role_counts(store: Store, oracle_ids: list[str] | None = None) -> dict:
    """Counts per role (optionally restricted to a set of oracle ids)."""
    ensure_schema(store)
    if oracle_ids is None:
        rows = store.conn.execute(
            "SELECT role, COUNT(DISTINCT oracle_id) AS n FROM card_role "
            "GROUP BY role").fetchall()
    else:
        if not oracle_ids:
            return {"by_role": {}, "cards_with_roles": 0}
        marks = ",".join("?" for _ in oracle_ids)
        rows = store.conn.execute(
            f"SELECT role, COUNT(DISTINCT oracle_id) AS n FROM card_role "
            f"WHERE oracle_id IN ({marks}) GROUP BY role",
            list(oracle_ids)).fetchall()
    if oracle_ids is None:
        cards = store.conn.execute(
            "SELECT COUNT(DISTINCT oracle_id) FROM card_role").fetchone()[0]
    else:
        marks = ",".join("?" for _ in oracle_ids)
        cards = store.conn.execute(
            f"SELECT COUNT(DISTINCT oracle_id) FROM card_role "
            f"WHERE oracle_id IN ({marks})", list(oracle_ids)).fetchone()[0]
    return {"by_role": {r["role"]: int(r["n"]) for r in rows},
            "cards_with_roles": int(cards)}
