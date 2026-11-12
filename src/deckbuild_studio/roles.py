"""Card roles / function categories for Deckbuild Studio.

Generalized from the upstream studio, which classifies cards with
Scryfall-Tagger labels. This project keeps the *taxonomy* and the
*origin discipline* and derives its claims from three strictly
separate layers — origins are never merged silently:

* ``ORACLE_TEXT_HEURISTIC`` — versioned regex rules
  (:data:`HEURISTIC_VERSION`) over the oracle text of **all faces** of
  a card (face texts come from the type-fact layer in
  :mod:`deckbuild_studio.categories`; without it, the stored front
  face is used). A heuristic claim is a search aid, never a measured
  fact; it is labelled as such wherever it is shown.
* ``STRUCTURAL_PROFILE`` — the structural role profiles imported via
  ``import-reference-data`` (``reference_role_profile``). Those are
  model estimates (``structural_model_estimates``), not observations;
  their roles are stored verbatim (they may exceed this taxonomy) and
  always carry the estimate origin.
* ``SCRYFALL_TAGGER_SEARCH`` — membership in Scryfall's official
  ``function:<tag>`` search results, synced by
  :mod:`deckbuild_studio.tagger` and stored per tag in
  ``card_tagger_claim``; :func:`rebuild_roles` mirrors those claims
  into ``card_role`` under this origin.

Claims live in ``card_role(oracle_id, role, origin)`` and are rebuilt
deterministically by :func:`rebuild_roles` — no network access, no
collection data leaves the machine. Every rebuild also records, per
card, that the heuristic layer *examined* it
(``card_category_check``), including the outcome "no category" —
a card without claims is thus distinguishable from a card that was
never checked.
"""
from __future__ import annotations

import re
import sqlite3

from .store import Store

# role -> Scryfall-Tagger functional label (taxonomy adopted from
# upstream; the label is the tag the Tagger layer syncs, when it
# exists — see tagger.VOCABULARY for per-tag sync status).
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
    "sacrifice_outlet": "sacrifice-outlet",
    "stax": "stax",
    "anthem": "anthem",
    "mill": "mill",
    "discard": "discard",
    # Scryfall's functional tag for draw/discard filtering is 'loot'
    # (424 cards, live probe 2026-11-12); a tag literally named
    # 'card-selection' does not exist in the Search API (404, like
    # 'card-filtering', 'filtering', 'looting', 'dig', 'card-quality').
    "card_selection": "loot",
    "token_production": "token",
}

ROLE_LABELS_DE: dict[str, str] = {
    "ramp": "Ramp", "mana_rock": "Mana Rock", "mana_dork": "Mana Dork",
    "land_ramp": "Land-Ramp", "card_draw": "Kartenzug",
    "card_advantage": "Kartenvorteil", "cantrip": "Cantrip",
    "tutor": "Tutor", "removal": "Removal", "board_wipe": "Board Wipe",
    "counterspell": "Counterspell", "bounce": "Bounce",
    "flicker": "Flicker", "recursion": "Reanimation/Rückholung",
    "protection": "Schutz", "graveyard_hate": "Friedhof-Hate",
    "lifegain": "Lebensgewinn", "sacrifice_outlet": "Sacrifice Outlet",
    "stax": "Stax", "anthem": "Anthem/Buff", "mill": "Mill",
    "discard": "Abwurf (Gegner)", "card_selection": "Kartenauswahl",
    "token_production": "Token-Erzeugung",
}

ORIGIN_HEURISTIC = "ORACLE_TEXT_HEURISTIC"
ORIGIN_PROFILE = "STRUCTURAL_PROFILE"
ORIGIN_TAGGER = "SCRYFALL_TAGGER_SEARCH"
ORIGINS = (ORIGIN_HEURISTIC, ORIGIN_PROFILE, ORIGIN_TAGGER)
HEURISTIC_VERSION = "oracle-heuristic/2.1.0"  # 2.1.0 (2026-11-12):
# protection also fires on a card's own keyword line (hexproof /
# shroud / indestructible / protection from — 2.0.0 required a
# 'gains/has' verb, so e.g. Zetalpa's own indestructible was missed),
# on 'have'-grants, on 'prevent all combat damage that would be
# dealt to' (the word 'combat' broke the 2.0.0 anchor; Fog Bank) and
# on 'prevent the next N damage that would be dealt' (Angel of
# Salvation); lifegain also fires on the lifelink keyword line;
# _ADD_MANA also accepts the worded templating 'add one/two/...
# mana of/in ...' and 'add an amount of ... mana' (Arcane Signet
# family — 2.0.0 required a literal mana symbol). Every addition was
# quantified store-wide and hand-checked on the collection before
# adoption (see docs/CATEGORIES.md); no other rule changed.
HEURISTIC_LABEL = "Heuristik aus Oracle-Text (lokal abgeleitet, keine Beobachtung)"
PROFILE_LABEL = "Strukturelle Schätzung (Modell) — keine Beobachtungsdaten"
TAGGER_LABEL = "Scryfall Tagger (offizielle Search-API, function:-Tags)"

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
# Rules of HEURISTIC_VERSION over one face's oracle text (lowercased).
# Each rule mirrors the everyday meaning of the taxonomy label;
# false negatives are acceptable, false positives are what we avoid.
# Rule ids are the role keys; the patterns are the versioned rulebook
# documented in docs/CATEGORIES.md.
_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("counterspell", re.compile(
        r"counter target [^.]{0,30}?\bspell\b"
        r"|counter target (activated|triggered)")),
    ("board_wipe", re.compile(
        r"(destroy|exile) all (creatures|permanents|nonland permanents|artifacts|enchantments|lands)"
        r"|(destroy|exile) each (creature|permanent|artifact|enchantment)"
        r"|sacrifice all (creatures|permanents|artifacts|enchantments)"
        r"|all creatures get -|(all|each) [^.]{0,60}get -\d+/-\d+"
        r"|each (player|opponent) sacrifices"
        r"|return all [^.]{0,80}to (their|its) owners'? hands?"
        r"|deals \d+ damage to each (creature|player|opponent|planeswalker)")),
    ("land_ramp", re.compile(
        r"search your library for (a|up to [^.]*?)basic land|search your library "
        r"for a [^.]*land card[^.]*put (it|that card|them) onto the battlefield")),
    ("graveyard_hate", re.compile(
        r"exile (target card from a graveyard|all cards from (a|all) graveyard"
        r"|target (player's|opponent's) graveyard|all graveyards)")),
    ("flicker", re.compile(
        r"exile [\s\S]{0,160}?return (it|that card|them|those cards|the exiled card) "
        r"to the battlefield")),
    ("recursion", re.compile(
        r"return target [^.]*card from your graveyard to (the battlefield|your hand)"
        r"|return [^.]*from your graveyard to the battlefield"
        r"|return [^.]{0,80}from (your|a) graveyard to (the battlefield|your hand)"
        r"|put [^.]{0,60}card from (your|a) graveyard (onto the battlefield|into your hand)")),
    ("bounce", re.compile(r"return target [^.]*to its owner's hand")),
    ("removal", re.compile(
        r"(destroy|exile) target (nonland )?(creature|artifact|enchantment|permanent|planeswalker|land)"
        r"|target creature gets -\d+/-\d+ until end of turn"
        r"|deals \d+ damage to (any target|target creature|target planeswalker)"
        r"|target (player|opponent) sacrifices"
        r"|fights? (another )?target")),
    ("card_advantage", re.compile(
        r"draw (two|three|four|five|six|seven|\d+|x) cards|draws? cards equal to"
        r"|draw a card for each")),
    ("card_draw", re.compile(
        r"draws? (a|one|two|three|x|\d+) cards?|\binvestigate\b")),
    ("lifegain", re.compile(
        r"(you )?gain[s]? (\d+|x) life|gain life equal to"
        r"|gains? [^.]*lifelink"
        r"|(?:^|[\n,])\s*lifelink\b")),
    ("protection", re.compile(
        r"(gains?|has|have) (hexproof|shroud|indestructible|protection from)"
        r"|(?:^|[\n,])\s*(hexproof|shroud|indestructible|protection from)\b"
        r"|prevent all (combat )?damage that would be dealt to"
        r"|prevent the next \d+ damage that would be dealt"
        r"|phases? out\b")),
    ("sacrifice_outlet", re.compile(
        r"sacrifice (a |an |another |this |one |two |three |x |any number of )[^:.]{0,70}:")),
    ("stax", re.compile(
        r"spells[^.]{0,60}cost \{?\d+\}? more"
        r"|doesn'?t untap during"
        r"|(players|opponents|each player) can'?t"
        r"|can cast no more than one|can'?t cast more than one"
        r"|counter it unless its controller pays")),
    ("anthem", re.compile(r"you control get \+\d+/\+\d+")),
    ("mill", re.compile(r"\bmills?\b")),
    ("discard", re.compile(r"(target|each) (player|opponent) discards")),
    ("card_selection", re.compile(
        r"draw [^.]{0,60}then discard|discard [^.]{0,40}then draw"
        r"|scry \d|surveil \d"
        r"|look at the top (one|two|three|four|five|six|seven|x|\d+) cards?")),
    ("token_production", re.compile(
        r"create (a|an|one|two|three|four|five|six|seven|eight|nine|ten|x|\d+|that many) "
        r"[^.]{0,80}tokens?\b|\binvestigate\b|\bpopulate\b")),
]

_ADD_MANA = re.compile(
    r"\{t\}[^.]*add \{|add \{[wubrgcxs0-9]|[.]\s*add \{"
    r"|add (one|two|three|four|five) mana (of|in)\b"
    r"|add an amount of [^.]{0,50}mana\b")
_SEARCH_LAND_PUT_HAND = re.compile(
    r"search your library for a [^.]*land card[^.]*to your hand")
_TREASURE = re.compile(r"create [^.]{0,40}treasure tokens?\b")


def _tutor_in_text(text: str) -> bool:
    """A library search for a card that is not (only) a land search.

    Segment-wise (sentences): land searches are land_ramp, not tutors;
    a card that searches both a land and something else in separate
    sentences still earns the tutor claim from the other sentence."""
    for segment in text.split("."):
        if "search your library for" not in segment or "card" not in segment:
            continue
        if "land card" in segment or "basic land" in segment:
            continue
        return True
    return False


def classify_text(oracle_text: str | None, type_line: str | None,
                  mana_value: float | None) -> set[str]:
    """Heuristic roles of ONE face from its oracle text / type line."""
    text = (oracle_text or "").lower()
    types = (type_line or "")
    roles: set[str] = set()
    for role, pattern in _RULES:
        if pattern.search(text):
            roles.add(role)
    if _tutor_in_text(text):
        roles.add("tutor")
    if "land" not in types.lower() and _ADD_MANA.search(text):
        if "Artifact" in types:
            roles.add("mana_rock")
        elif "Creature" in types:
            roles.add("mana_dork")
        roles.add("ramp")
    if _TREASURE.search(text):
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


def classify_card(faces: list[tuple[str | None, str | None]],
                  mana_value: float | None) -> set[str]:
    """Heuristic roles of a whole card: union over all its faces."""
    roles: set[str] = set()
    for text, type_line in faces:
        roles |= classify_text(text, type_line, mana_value)
    return roles


def _table_exists(store: Store, name: str) -> bool:
    return store.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)).fetchone() is not None


def _face_inputs(store: Store, row: sqlite3.Row) -> list[tuple[str | None, str | None]]:
    """(oracle_text, type_line) per face: from the type-fact layer
    when it has been derived, else the stored front face only."""
    if _table_exists(store, "card_face"):
        faces = store.conn.execute(
            "SELECT oracle_text, type_line FROM card_face "
            "WHERE oracle_id = ? ORDER BY face_index",
            (row["oracle_id"],)).fetchall()
        if faces:
            return [(f["oracle_text"], f["type_line"]) for f in faces]
    return [(row["front_oracle_text"] or row["oracle_text"],
             row["front_type_line"] or row["type_line"])]


def rebuild_roles(store: Store) -> dict:
    """Rebuild all role claims from local data (deterministic, offline).

    Heuristic claims come from all faces (type-fact layer when
    present); profile claims are copied from
    ``reference_role_profile`` when that import exists; Tagger claims
    are mirrored from ``card_tagger_claim`` when a Tagger sync ran.
    Only this module's three origins are rewritten — nothing else in
    ``card_role`` is touched. Returns counts only."""
    ensure_schema(store)
    rows = store.conn.execute(
        "SELECT oracle_id, front_oracle_text, oracle_text, front_type_line, "
        "type_line, mana_value FROM scryfall_card").fetchall()
    claims: list[tuple[str, str, str]] = []
    heuristic_counts: dict[str, int] = {}
    for row in rows:
        card_roles_found = classify_card(_face_inputs(store, row), row["mana_value"])
        heuristic_counts[row["oracle_id"]] = len(card_roles_found)
        for role in card_roles_found:
            claims.append((row["oracle_id"], role, ORIGIN_HEURISTIC))
    profile_cards = 0
    if _table_exists(store, "reference_role_profile"):
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
    tagger_claims = 0
    if _table_exists(store, "card_tagger_claim"):
        for trow in store.conn.execute(
                "SELECT oracle_id, category FROM card_tagger_claim"):
            claims.append((trow["oracle_id"], trow["category"], ORIGIN_TAGGER))
            tagger_claims += 1
    with store.conn:
        store.conn.execute(
            "DELETE FROM card_role WHERE origin IN (?, ?, ?)",
            (ORIGIN_HEURISTIC, ORIGIN_PROFILE, ORIGIN_TAGGER))
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_role(oracle_id, role, origin) "
            "VALUES (?, ?, ?)", claims)
    # 'examined' bookkeeping for the heuristic layer: every card of the
    # Scryfall store, including those with zero claims.
    from . import categories
    categories.record_checks(store, origin=ORIGIN_HEURISTIC,
                             version=HEURISTIC_VERSION,
                             claims_by_card=heuristic_counts)
    store.conn.commit()
    by_origin: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for row in store.conn.execute(
            "SELECT origin, COUNT(*) AS n FROM card_role GROUP BY origin"):
        by_origin[row["origin"]] = int(row["n"])
    for row in store.conn.execute(
            "SELECT role, COUNT(*) AS n FROM card_role GROUP BY role"):
        by_role[row["role"]] = int(row["n"])
    return {"cards_classified": len(rows), "claims": len(claims),
            "heuristic_version": HEURISTIC_VERSION,
            "profile_cards": profile_cards, "tagger_claims": tagger_claims,
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

    A card may carry several roles; claims of all origins are counted
    together here — origins stay visible per card via
    :func:`card_roles`."""
    counts: dict[str, int] = {}
    rmap = roles_map(store, list(entries))
    for oracle_id, roles in rmap.items():
        qty = entries.get(oracle_id, 0)
        for role in roles:
            counts[role] = counts.get(role, 0) + qty
    return counts


def primary_category(store: Store, oracle_id: str) -> str | None:
    """The card's first category in taxonomy order (any origin), for
    grouping deck lists by function; None when uncategorised."""
    found = card_roles(store, oracle_id)
    for role in ROLES:
        if role in found:
            return role
    # profile claims may exceed the taxonomy; use them verbatim last
    for role in sorted(found):
        return role
    return None


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
