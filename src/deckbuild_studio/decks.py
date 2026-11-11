"""Deck store: per-commander deck context, revisions, variants, comparison, export.

Migrated concepts from commander-playtest-lab ``studio/decks.py`` +
``studio/builder.py`` (deck readiness), decoupled from the monorepo
``deck_variant``/``models`` modules: revisions are content-addressed
(SHA-256 over the sorted card list, as in the source), decks belong to
exactly one collection profile and one commander (or legal commander pair).

Validation (data-based pre-check, not a rules engine):
  * exactly 100 cards including commander(s)
  * singleton by oracle_id, with real exceptions only: Basic Lands and
    cards whose oracle text explicitly allows any number / up to N copies
  * every card's color identity subset of the commander's color identity
  * commander legality via legalities.commander (banlist)
  * copies never exceed physically available copies in the collection

Every stored revision carries the validation outcome at save time as an
explicit status (QA P0.2): ``legal`` only when validation passed,
otherwise ``draft``. A draft still saves (work in progress is never
lost), but it is never presented or exported as a legal deck: text
exports of drafts are headed "ENTWURF — nicht legal", and a legal-only
export is refused for drafts.
"""
from __future__ import annotations

import hashlib
import re
import uuid

from .commander import assess, pairing_mechanisms, partner_with_target
from .store import Store, utcnow

_ANY_NUMBER = re.compile(r"a deck can have any number of cards named", re.I)
_UP_TO = re.compile(r"a deck can have up to (\w+) copies of cards named|"
                    r"a deck can have up to (\w+) cards named", re.I)
_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15}


def singleton_limit(card) -> int:
    """Max copies allowed by singleton rule for this Scryfall row."""
    type_line = card["type_line"] or ""
    if "Basic" in type_line and "Land" in type_line:
        return 10**9
    text = card["oracle_text"] or ""
    if _ANY_NUMBER.search(text):
        return 10**9
    m = _UP_TO.search(text)
    if m:
        word = (m.group(1) or m.group(2) or "").lower()
        return _WORD_NUM.get(word, 1)
    return 1


def deck_hash(entries: list[tuple[str, int, bool]]) -> str:
    payload = "\n".join(f"{oid}|{qty}|{int(cmd)}" for oid, qty, cmd in sorted(entries))
    return hashlib.sha256(payload.encode()).hexdigest()


def _names_of(card) -> set[str]:
    """All names a card can be referenced by: full name + front-face name."""
    return {n for n in (card["name"], card["front_name"]) if n}


def _pair_legal(store: Store, ids: list[str]) -> tuple[bool, str]:
    if len(ids) == 1:
        return True, "single commander"
    if len(ids) != 2:
        return False, "at most two commanders"
    cards = [store.scryfall(i) for i in ids]
    if any(c is None for c in cards):
        return False, "commander not in Scryfall store"
    mech = [set(pairing_mechanisms(c["front_oracle_text"], c["front_type_line"])) for c in cards]  # type: ignore[index]
    # 'Partner with X' is restrictive (QA P1.6): if either card carries it,
    # BOTH must carry it and each must name the other exactly.
    if "partner_with" in mech[0] or "partner_with" in mech[1]:
        targets = [partner_with_target(c["front_oracle_text"]) for c in cards]  # type: ignore[index]
        if ("partner_with" in mech[0] and "partner_with" in mech[1]
                and targets[0] in _names_of(cards[1])  # type: ignore[arg-type]
                and targets[1] in _names_of(cards[0])):  # type: ignore[arg-type]
            return True, "Partner with"
        return False, ("Partner with: each card must name the other exactly "
                       f"(found: {targets[0]!r} / {targets[1]!r})")
    if "partner" in mech[0] and "partner" in mech[1]:
        return True, "Partner"
    if "friends_forever" in mech[0] and "friends_forever" in mech[1]:
        return True, "Friends forever"
    if ("choose_a_background" in mech[0] and "background" in mech[1]) or (
            "choose_a_background" in mech[1] and "background" in mech[0]):
        return True, "Choose a Background"
    if ("doctors_companion" in mech[0]) != ("doctors_companion" in mech[1]):
        other = cards[1] if "doctors_companion" in mech[0] else cards[0]
        if "Time Lord Doctor" in (other["front_type_line"] or ""):
            return True, "Doctor's companion"
    return False, "no compatible pairing mechanism (Partner / Friends forever / Background / Doctor's companion)"


def validate_deck(store: Store, collection_id: str,
                  commander_ids: list[str], entries: dict[str, int]) -> dict[str, object]:
    """entries: oracle_id -> quantity for the 99 (commanders excluded)."""
    errors: list[str] = []
    warnings: list[str] = []
    available = store.available_by_oracle(collection_id)

    # Commander checks
    cmd_rows = []
    for oid in commander_ids:
        row = store.scryfall(oid)
        if row is None:
            errors.append(f"commander {oid}: not in Scryfall store (needs_review)")
            continue
        cmd_rows.append(row)
        if row["commander_legality"] != "legal":
            errors.append(f"commander {row['name']}: legalities.commander={row['commander_legality']}")
        fake = {"name": row["name"], "oracle_id": oid, "scryfall_ci": row["color_identity"],
                "commander_legality": row["commander_legality"],
                "front_type_line": row["front_type_line"],
                "front_oracle_text": row["front_oracle_text"], "image_uri": row["image_uri"]}
        class _R(dict):
            pass
        verdict = assess(_R(fake))  # type: ignore[arg-type]
        if not verdict["eligible"]:
            errors.append(f"commander {row['name']}: {verdict['reason']}")
    ok_pair, pair_reason = _pair_legal(store, commander_ids)
    if not ok_pair:
        errors.append(f"commander pair: {pair_reason}")
    ci = set("".join(r["color_identity"] or "" for r in cmd_rows))

    total = len(commander_ids) + sum(entries.values())
    if total != 100:
        errors.append(f"deck size {total} != 100 (including commander)")

    for oid, qty in entries.items():
        card = store.scryfall(oid)
        if card is None:
            errors.append(f"{oid}: not in Scryfall store (needs_review)")
            continue
        if qty < 1:
            errors.append(f"{card['name']}: quantity {qty} < 1")
        if card["commander_legality"] != "legal":
            errors.append(f"{card['name']}: banned/not legal in Commander")
        if not set(card["color_identity"] or "") <= ci:
            errors.append(f"{card['name']}: color identity {card['color_identity']} outside commander identity")
        limit = singleton_limit(card)
        if qty > limit:
            errors.append(f"{card['name']}: singleton violation ({qty} > {limit})")
        if qty > available.get(oid, 0):
            errors.append(f"{card['name']}: {qty} copies exceed available {available.get(oid, 0)}")
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "size": total, "color_identity": "".join(sorted(ci)), "pairing": pair_reason}


def revision_status(store: Store, revision_id: str) -> str | None:
    """Stored status of a revision ('legal' | 'draft'), None if unknown."""
    row = store.conn.execute("SELECT status FROM deck_revision WHERE revision_id=?",
                             (revision_id,)).fetchone()
    return row["status"] if row else None


def create_deck(store: Store, collection_id: str, name: str,
                commander_ids: list[str], entries: dict[str, int],
                note: str = "", parent_revision_id: str | None = None) -> dict[str, object]:
    """Create deck + first revision, or a new revision (variant) of an existing deck.

    The revision is stored with the validation verdict of THIS moment:
    status 'legal' iff validation passed, else 'draft' (QA P0.2)."""
    verdict = validate_deck(store, collection_id, commander_ids, entries)
    status = "legal" if verdict["valid"] else "draft"
    deck_id = None
    if parent_revision_id:
        row = store.conn.execute("SELECT deck_id FROM deck_revision WHERE revision_id=?",
                                 (parent_revision_id,)).fetchone()
        if row:
            deck_id = row["deck_id"]
    if deck_id is None:
        deck_id = uuid.uuid4().hex[:12]
        store.conn.execute(
            "INSERT INTO deck(deck_id,collection_id,name,commander_oracle_ids,created_at)"
            " VALUES(?,?,?,?,?)",
            (deck_id, collection_id, name, ",".join(commander_ids), utcnow()))
    revision_id = uuid.uuid4().hex[:12]
    rows = [(oid, q, False) for oid, q in entries.items()] + \
           [(oid, 1, True) for oid in commander_ids]
    store.conn.execute(
        "INSERT INTO deck_revision(revision_id,deck_id,parent_revision_id,deck_hash,"
        "status,note,created_at) VALUES(?,?,?,?,?,?,?)",
        (revision_id, deck_id, parent_revision_id, deck_hash(rows), status, note, utcnow()))
    store.conn.executemany(
        "INSERT INTO deck_card(revision_id,oracle_id,quantity,is_commander) VALUES(?,?,?,?)",
        [(revision_id, oid, q, int(cmd)) for oid, q, cmd in rows])
    store.conn.commit()
    return {"deck_id": deck_id, "revision_id": revision_id, "status": status,
            "deck_hash": deck_hash(rows), "validation": verdict}


def revision_entries(store: Store, revision_id: str) -> tuple[list[str], dict[str, int]]:
    commanders: list[str] = []
    entries: dict[str, int] = {}
    for r in store.conn.execute("SELECT * FROM deck_card WHERE revision_id=?", (revision_id,)):
        if r["is_commander"]:
            commanders.append(r["oracle_id"])
        else:
            entries[r["oracle_id"]] = r["quantity"]
    return commanders, entries


def compare_revisions(store: Store, rev_a: str, rev_b: str) -> dict[str, object]:
    _, a = revision_entries(store, rev_a)
    _, b = revision_entries(store, rev_b)
    names = {}
    for oid in a.keys() | b.keys():
        row = store.scryfall(oid)
        names[oid] = row["name"] if row else oid
    return {
        "added": {k: b[k] for k in b.keys() - a.keys()},
        "removed": {k: a[k] for k in a.keys() - b.keys()},
        "changed": {k: (a[k], b[k]) for k in a.keys() & b.keys() if a[k] != b[k]},
        "names": names,
        "status_a": revision_status(store, rev_a),
        "status_b": revision_status(store, rev_b),
    }


DRAFT_EXPORT_HEADER = "# ENTWURF — nicht legal (Validierung nicht bestanden)"


def export_revision(store: Store, revision_id: str, *, require_legal: bool = False) -> str:
    """Text export of one revision. Drafts are unmistakably headed as
    drafts (QA P0.2); with ``require_legal=True`` exporting a draft is
    refused outright. Returns '' for an unknown revision_id."""
    status = revision_status(store, revision_id)
    if status is None:
        return ""
    if require_legal and status != "legal":
        raise ValueError(
            f"revision {revision_id} is a draft (status={status}); "
            "a legal export is only possible for legal revisions")
    lines: list[str] = []
    if status != "legal":
        lines += [DRAFT_EXPORT_HEADER, f"# Status: {status}"]
    for r in store.conn.execute(
            """SELECT dc.quantity, dc.is_commander, s.name FROM deck_card dc
               LEFT JOIN scryfall_card s ON s.oracle_id = dc.oracle_id
               WHERE dc.revision_id=? ORDER BY dc.is_commander DESC, s.name""",
            (revision_id,)):
        tag = " (Commander)" if r["is_commander"] else ""
        lines.append(f"{r['quantity']} {r['name'] or r['oracle_id']}{tag}")
    return "\n".join(lines) + "\n"


def list_decks(store: Store, collection_id: str) -> list[dict]:
    """Deck overview for one collection: latest revision + status each."""
    out: list[dict] = []
    for d in store.conn.execute(
            "SELECT * FROM deck WHERE collection_id=? ORDER BY created_at, name",
            (collection_id,)):
        # Chronology = insertion order (rowid): created_at has only
        # second resolution and revision_id is random, so ordering by
        # them would scramble revisions created within the same second.
        revs = store.conn.execute(
            "SELECT revision_id, status, deck_hash, created_at FROM deck_revision"
            " WHERE deck_id=? ORDER BY rowid DESC",
            (d["deck_id"],)).fetchall()
        latest = revs[0] if revs else None
        out.append({
            "deck_id": d["deck_id"], "name": d["name"],
            "commander_oracle_ids": [x for x in d["commander_oracle_ids"].split(",") if x],
            "created_at": d["created_at"], "revision_count": len(revs),
            # Field name from the feature-parity deck list (same count).
            "revisions": len(revs),
            "latest_revision_id": latest["revision_id"] if latest else None,
            "latest_status": latest["status"] if latest else None,
            "latest_hash": latest["deck_hash"] if latest else None,
        })
    return out


def list_revisions(store: Store, deck_id: str) -> list[dict]:
    """All revisions of a deck, oldest first (insertion order via rowid —
    created_at's second resolution cannot order same-second revisions),
    each with size + status."""
    out = []
    for r in store.conn.execute(
            "SELECT * FROM deck_revision WHERE deck_id=? ORDER BY rowid",
            (deck_id,)):
        size = store.conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM deck_card WHERE revision_id=?",
            (r["revision_id"],)).fetchone()[0]
        out.append({"revision_id": r["revision_id"], "deck_id": deck_id,
                    "parent_revision_id": r["parent_revision_id"],
                    "deck_hash": r["deck_hash"], "status": r["status"],
                    "note": r["note"], "created_at": r["created_at"], "size": size})
    return out


def delete_deck(store: Store, deck_id: str) -> bool:
    """Delete a deck with all revisions and cards. False if unknown."""
    row = store.conn.execute("SELECT deck_id FROM deck WHERE deck_id=?",
                             (deck_id,)).fetchone()
    if row is None:
        return False
    revs = [r["revision_id"] for r in store.conn.execute(
        "SELECT revision_id FROM deck_revision WHERE deck_id=?", (deck_id,))]
    try:
        for rev in revs:
            store.conn.execute("DELETE FROM deck_card WHERE revision_id=?", (rev,))
        store.conn.execute("DELETE FROM deck_revision WHERE deck_id=?", (deck_id,))
        store.conn.execute("DELETE FROM deck WHERE deck_id=?", (deck_id,))
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    return True


def legal_pool(store: Store, collection_id: str, commander_ids: list[str]) -> list[dict]:
    """Available, commander-legal pool within the commanders' color identity."""
    ci = set()
    for oid in commander_ids:
        row = store.scryfall(oid)
        if row:
            ci |= set(row["color_identity"] or "")
    available = store.available_by_oracle(collection_id)
    pool: list[dict] = []
    seen: set[str] = set()
    for row in store.inventory_rows(collection_id):
        oid = row["oracle_id"]
        if oid in seen or oid in commander_ids:
            continue
        seen.add(oid)
        if row["commander_legality"] != "legal":
            continue
        if not set(row["scryfall_ci"] or "") <= ci:
            continue
        if available.get(oid, 0) <= 0:
            continue
        pool.append({"oracle_id": oid, "name": row["name"],
                     "color_identity": row["scryfall_ci"] or "",
                     "type_line": row["scryfall_type_line"],
                     "available": available[oid], "image_uri": row["image_uri"],
                     "favorite": bool(row["favorite"])})
    pool.sort(key=lambda r: str(r["name"]))
    return pool
