"""Inclusion engine — every figure ships with its cohort definition.

Inclusion answers "in what share of decks does this card appear?" — and
is meaningless without the denominator's definition. This engine
computes inclusion from the source the OWNER selected (see
:mod:`deckbuild_studio.settings`):

  * ``edhrec``    — the stored EDHREC stats snapshots (per commander and
                    bracket; selected brackets are aggregated as
                    sum(num_decks)/sum(potential_decks), i.e. deck-weighted,
                    and the per-bracket breakdown is always included).
                    Requires a commander context: EDHREC stats exist only
                    per commander.
  * ``decklists`` — the locally harvested real deck lists
                    (:mod:`deckbuild_studio.decklists`); denominator =
                    harvested AVAILABLE decks of the selected cohorts
                    (platforms + brackets from the settings; with a
                    commander context: that commander's decks, else all
                    harvested decks of the cohorts). Decks with identical
                    stored content under another deck id count ONCE
                    (lowest deck id wins) — a re-published copy is not a
                    second deck. Card rows with quantity <= 0 never count.
                    A deck is part of the universe only when it holds at
                    least one countable card — a quantity > 0 row that is
                    not the commander entry (commander entries are
                    excluded from the card figures, so a deck holding
                    only its commander can never contribute a hit and
                    must not inflate the denominator). Decks whose stored
                    content is unknown (no card rows at all) are excluded
                    by the same rule instead of collapsing onto one
                    shared empty fingerprint.
  * ``own_decks`` — the owner's own stored decks (latest revision each,
                    same basis as ``queries.own_deck_inclusion``).
  * ``combined``  — decklists + own_decks pooled (denominators add up).
                    EDHREC is never pooled in: its denominators are deck
                    counts of decks we do not hold individually.

Commander-category entries of harvested decks are excluded from the
card figures (a commander is in 100% of its own decks by construction);
they are reported separately in the definition block. When the
denominator is below ``inclusion.min_decks`` every figure is flagged
``sufficient: False`` and the definition states "ungenügende Daten" —
the numbers stay visible, never dressed up.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from . import settings as settings_mod
from .external import BRACKETS as EDHREC_BRACKETS
from .external import latest_snapshot
from .queries import own_deck_inclusion
from .store import Store

_LEVEL_BY_NAME = {name: level for name, level in EDHREC_BRACKETS.items()}
_NAME_BY_LEVEL = {level: name for name, level in EDHREC_BRACKETS.items()}


def _age_filter(cfg: dict) -> str | None:
    days = cfg["inclusion.max_age_days"]
    if not days:
        return None
    return (datetime.now(UTC) - timedelta(days=days)).isoformat(timespec="seconds")


def _finish(cfg: dict, *, source_label: str, denominator: int,
            counts: dict[str, dict], notes: list[str],
            commander_oracle_id: str | None,
            extra_definition: dict | None = None) -> dict:
    min_decks = cfg["inclusion.min_decks"]
    sufficient = denominator >= max(1, min_decks) if min_decks else denominator > 0
    results = []
    for oid, slot in counts.items():
        results.append({
            "oracle_id": oid, "name": slot["name"],
            "decks_with": slot["decks"],
            "denominator": denominator,
            "inclusion": (slot["decks"] / denominator) if denominator else None,
            "sufficient": sufficient,
            **({"per_bracket": slot["per_bracket"]} if "per_bracket" in slot else {}),
        })
    results.sort(key=lambda r: (-r["decks_with"], r["name"] or ""))
    definition = {
        "source": cfg["inclusion.source"], "source_label": source_label,
        "brackets": cfg["inclusion.brackets"],
        "platforms": cfg["inclusion.platforms"],
        "min_decks": min_decks,
        "max_age_days": cfg["inclusion.max_age_days"],
        "commander_oracle_id": commander_oracle_id,
        "denominator": denominator,
        "sufficient": sufficient,
        "sufficiency_note": None if sufficient else
            f"ungenügende Daten: Nenner {denominator} < Mindest-Nenner {min_decks}",
        "notes": notes,
    }
    if extra_definition:
        definition.update(extra_definition)
    return {"definition": definition, "results": results}


def _from_edhrec(store: Store, cfg: dict, commander_oracle_id: str | None) -> dict:
    notes: list[str] = []
    if commander_oracle_id is None:
        return _finish(
            cfg, source_label="EDHREC stats snapshots", denominator=0, counts={},
            notes=["EDHREC-Statistiken existieren nur je Commander — "
                   "ohne Commander-Kontext ist die Kohorte leer."],
            commander_oracle_id=None)
    cutoff = _age_filter(cfg)
    by_name: dict[str, str] = {}
    for r in store.conn.execute("SELECT oracle_id, name, front_name FROM scryfall_card"):
        by_name.setdefault(r["name"], r["oracle_id"])
        if r["front_name"]:
            by_name.setdefault(r["front_name"], r["oracle_id"])
    counts: dict[str, dict] = {}
    denominator = 0
    per_bracket_totals: dict[str, int] = {}
    for level in cfg["inclusion.brackets"]:
        bname = _NAME_BY_LEVEL.get(level)
        if bname is None:
            notes.append(f"Bracket {level}: keine EDHREC-Kohorte gespeichert "
                         "(EDHREC-Sync deckt nur 2/3/4 ab).")
            continue
        snap = latest_snapshot(store, "edhrec", "edhrec_stats",
                               commander_oracle_id=commander_oracle_id, bracket=bname)
        if snap is None or snap["status"] not in ("AVAILABLE", "PARTIAL"):
            notes.append(f"Bracket {level} ({bname}): kein EDHREC-Statistik-Snapshot.")
            continue
        if cutoff and snap["fetched_at"] < cutoff:
            notes.append(f"Bracket {level} ({bname}): Snapshot älter als "
                         f"{cfg['inclusion.max_age_days']} Tage — ausgeschlossen.")
            continue
        bracket_denominator = 0
        snap_counts: dict[str, dict] = {}
        for row in store.conn.execute(
                "SELECT name, num_decks, potential_decks FROM edhrec_card_stat "
                "WHERE snapshot_id=?", (snap["snapshot_id"],)):
            oid = by_name.get(row["name"])
            if oid is None or row["num_decks"] is None:
                continue
            slot = snap_counts.setdefault(oid, {"decks": 0, "potential": 0})
            slot["decks"] += row["num_decks"]
            slot["potential"] += row["potential_decks"] or 0
            bracket_denominator = max(bracket_denominator, row["potential_decks"] or 0)
            entry = counts.setdefault(oid, {"name": row["name"], "decks": 0,
                                            "per_bracket": {}})
            entry["decks"] += row["num_decks"]
            entry["per_bracket"][str(level)] = {
                "decks_with": row["num_decks"],
                "potential_decks": row["potential_decks"]}
        denominator += bracket_denominator
        per_bracket_totals[str(level)] = bracket_denominator
    notes.append("EDHREC-Aggregation über gewählte Brackets: "
                 "sum(num_decks)/sum(potential_decks) je Karte (deckgewichtet); "
                 "Einzelwerte je Bracket in per_bracket.")
    return _finish(cfg, source_label="EDHREC stats snapshots",
                   denominator=denominator, counts=counts, notes=notes,
                   commander_oracle_id=commander_oracle_id,
                   extra_definition={"per_bracket_denominators": per_bracket_totals})


def _content_fingerprint(rows: list[tuple]) -> str:
    """Content fingerprint of one deck: its stored card rows (identity,
    quantity, commander flag), order-independent. Two deck ids with the
    same fingerprint hold the same list — a copy, not a second deck."""
    digest = hashlib.sha256()
    for entry_key, quantity, is_commander in sorted(rows):
        digest.update(f"{entry_key}|{quantity}|{is_commander}\n".encode())
    return digest.hexdigest()


@contextmanager
def _universe_table(conn, deck_uids: list[str]) -> Iterator[str]:
    """Load deck uids into a TEMP table so universe queries never bind one
    variable per deck.

    SQLite caps bound variables (999 on older builds); a universe can be
    larger. ``CREATE ... AS SELECT ... FROM json_each(?)`` is one
    statement with one bound variable and, unlike an INSERT, opens no
    implicit transaction: a read-only query must not leave the
    connection locked. Adopted from upstream #1207 (``universe.py``:
    ``_universe_table``)."""
    name = "temp.universe_deck"
    conn.execute(f"DROP TABLE IF EXISTS {name}")
    conn.execute(
        f"CREATE TEMP TABLE {name} AS "
        "SELECT value AS deck_uid FROM json_each(?)",
        (json.dumps(deck_uids),),
    )
    try:
        yield name
    finally:
        conn.execute(f"DROP TABLE IF EXISTS {name}")


def _canonical_decks(store: Store, deck_uids: list[str]
                     ) -> tuple[list[str], int]:
    """One deck uid per distinct content fingerprint inside the selected
    universe (lowest deck uid wins). The same list re-published under
    another deck id — 163 excess ids in the real harvest, largest group
    55 copies — must not inflate a denominator or a hit count.

    Returns (canonical uids, excluded count): a deck is part of the
    universe only when it holds at least one countable card — a
    quantity > 0 row that is not the commander entry. Decks without
    one (commander-only lists, zero-quantity rows only, or no stored
    rows at all) are excluded instead of counting toward the
    denominator; an unknown (empty) content fingerprint therefore
    never collapses several decks onto one. Adopted from upstream
    #1207 (``universe.py``: unknown fingerprints stay distinct,
    empty decks leave the denominator), adapted to our figures, in
    which commander entries never contribute a hit."""
    if not deck_uids:
        return [], 0
    with _universe_table(store.conn, deck_uids) as table:
        eligible = {
            row["deck_uid"]
            for row in store.conn.execute(
                f"SELECT u.deck_uid FROM {table} u WHERE EXISTS ("
                "SELECT 1 FROM decklist_card c WHERE c.deck_uid = u.deck_uid "
                "AND c.quantity > 0 AND c.is_commander = 0)")
        }
        by_deck: dict[str, list[tuple]] = {}
        for row in store.conn.execute(
                f"SELECT c.deck_uid, c.entry_key, c.quantity, c.is_commander "
                f"FROM decklist_card c JOIN {table} u "
                f"ON u.deck_uid = c.deck_uid ORDER BY c.deck_uid"):
            by_deck.setdefault(row["deck_uid"], []).append(
                (row["entry_key"], row["quantity"], row["is_commander"]))
    first: dict[str, str] = {}
    for uid in sorted(eligible):
        first.setdefault(_content_fingerprint(by_deck.get(uid, [])), uid)
    return sorted(first.values()), len(deck_uids) - len(eligible)


def _decklist_counts(store: Store, cfg: dict,
                     commander_oracle_id: str | None
                     ) -> tuple[int, dict, list[str], dict]:
    notes: list[str] = []
    cutoff = _age_filter(cfg)
    # Bracket-less decks (browser harvests, bracket_level NULL) carry
    # no bracket to filter by: they join only via their selected
    # platform, as that platform's bracket-less cohort. Decks WITH a
    # bracket are filtered exactly as before, so every bracket
    # universe/denominator of a bracketed platform is unchanged.
    q = ("SELECT deck_uid FROM decklist_deck WHERE status='AVAILABLE' "
         "AND platform IN (%s) AND (bracket_level IN (%s) "
         "OR bracket_level IS NULL)" % (
             ",".join("?" for _ in cfg["inclusion.platforms"]),
             ",".join("?" for _ in cfg["inclusion.brackets"])))
    args: list = [*cfg["inclusion.platforms"], *cfg["inclusion.brackets"]]
    if commander_oracle_id is not None:
        q += " AND commander_oracle_id=?"
        args.append(commander_oracle_id)
    if cutoff:
        q += " AND fetched_at>=?"
        args.append(cutoff)
    period_from = cfg["inclusion.date_from"]
    period_to = cfg["inclusion.date_to"]
    excluded_no_timestamp = 0
    if period_from or period_to:
        # Period basis is the deck's SOURCE timestamp (Archidekt
        # updatedAt), never fetched_at. Decks without one are
        # excluded while a period is set — and counted, so the
        # definition states the loss instead of hiding it.
        excluded_no_timestamp = store.conn.execute(
            f"SELECT COUNT(*) FROM ({q}) WHERE source_updated_at IS NULL",
            args).fetchone()[0]
        q += " AND source_updated_at IS NOT NULL"
        if period_from:
            q += " AND substr(source_updated_at,1,10)>=?"
            args.append(period_from)
        if period_to:
            q += " AND substr(source_updated_at,1,10)<=?"
            args.append(period_to)
    deck_uids = [r["deck_uid"] for r in store.conn.execute(q, args)]
    canonical, excluded = _canonical_decks(store, deck_uids)
    removed = len(deck_uids) - excluded - len(canonical)
    if excluded:
        notes.append(f"{excluded} von {len(deck_uids)} Deck-IDs haben keine "
                     "zählbare Karte (nur Commander-Zeile, nur Mengen von 0 "
                     "oder keine gespeicherten Kartenzeilen) und zählen "
                     "nicht zum Nenner.")
    if removed:
        notes.append(f"{removed} von {len(deck_uids)} Deck-IDs sind "
                     "inhaltsgleiche Duplikate (gleicher Karteninhalt "
                     "unter anderer Deck-ID) und zählen einmal "
                     "(niedrigste Deck-ID gewinnt).")
    composition: dict = {"denominator_by_platform": {},
                         "denominator_by_bracket": {},
                         "period": {
                             "date_from": period_from,
                             "date_to": period_to,
                             "basis": ("source_updated_at (Archidekt "
                                       "updatedAt)"
                                       if (period_from or period_to)
                                       else None),
                             "excluded_no_timestamp":
                                 excluded_no_timestamp}}
    if excluded_no_timestamp:
        notes.append(f"{excluded_no_timestamp} Decks ohne Quell-"
                     "Zeitstempel wurden durch den gesetzten Zeitraum "
                     "ausgeschlossen (Zeitraum-Basis ist der Quell-"
                     "Zeitstempel, nicht das Abrufdatum).")
    if canonical:
        with _universe_table(store.conn, canonical) as table:
            for row in store.conn.execute(
                    f"SELECT d.platform, d.bracket_level FROM decklist_deck d "
                    f"JOIN {table} u ON u.deck_uid = d.deck_uid"):
                by_platform = composition["denominator_by_platform"]
                by_bracket = composition["denominator_by_bracket"]
                by_platform[str(row["platform"])] = \
                    by_platform.get(str(row["platform"]), 0) + 1
                # bracket-less decks (browser harvests) are reported
                # under the explicit "none" key — never folded into a
                # real bracket cohort
                bkey = ("none" if row["bracket_level"] is None
                        else str(row["bracket_level"]))
                by_bracket[bkey] = by_bracket.get(bkey, 0) + 1
        composition["denominator_by_platform"] = dict(
            sorted(composition["denominator_by_platform"].items()))
        composition["denominator_by_bracket"] = dict(
            sorted(composition["denominator_by_bracket"].items()))
    counts: dict[str, dict] = {}
    if canonical:
        with _universe_table(store.conn, canonical) as table:
            for row in store.conn.execute(
                    f"SELECT dc.oracle_id, dc.card_name, "
                    f"COUNT(DISTINCT dc.deck_uid) decks "
                    f"FROM decklist_card dc JOIN {table} u "
                    f"ON u.deck_uid = dc.deck_uid "
                    f"WHERE dc.is_commander=0 AND dc.oracle_id IS NOT NULL "
                    f"AND dc.quantity > 0 "
                    f"GROUP BY dc.oracle_id, dc.card_name"):
                counts[row["oracle_id"]] = {"name": row["card_name"],
                                            "decks": int(row["decks"])}
    notes.append("Commander-Einträge der Decks sind aus den Kartenwerten "
                 "ausgenommen (der Commander steht konstruktionsbedingt in "
                 "100% seiner Decks).")
    return len(canonical), counts, notes, composition


def _own_counts(store: Store, collection_id: str | None,
                commander_oracle_id: str | None = None) -> tuple[int, dict, list[str]]:
    if collection_id is None:
        rows = store.collections()
        if len(rows) != 1:
            return 0, {}, ["own_decks braucht eine collection_id "
                           f"(vorhanden: {[r['collection_id'] for r in rows]})"]
        collection_id = rows[0]["collection_id"]
    note = (f"eigene Decks der Collection {collection_id} (nur jeweils neueste "
            "Revision; Brackets/Plattformen gelten hier nicht)")
    if commander_oracle_id is None:
        data = own_deck_inclusion(store, collection_id)
        counts = {c["oracle_id"]: {"name": c["name"], "decks": c["decks"]}
                  for c in data["cards"]}
        return data["decks_total"], counts, [note]
    # Commander context: only own decks LED by this commander count —
    # same basis as own_deck_inclusion (latest revision per deck,
    # commander entries excluded), scoped by the deck's commander list
    # (deck.commander_oracle_ids is stored comma-separated, cf. decks.py).
    deck_ids = [r["deck_id"] for r in store.conn.execute(
        "SELECT deck_id, commander_oracle_ids FROM deck WHERE collection_id=?",
        (collection_id,))
        if commander_oracle_id in (r["commander_oracle_ids"] or "").split(",")]
    if not deck_ids:
        return 0, {}, [note + f"; keine eigenen Decks mit Commander "
                              f"{commander_oracle_id}"]
    rev_rows = store.conn.execute(
        "SELECT dr.revision_id, dr.deck_id, dr.created_at, dr.rowid AS rid "
        "FROM deck_revision dr WHERE dr.deck_id IN (%s) "
        "ORDER BY dr.deck_id, dr.created_at, dr.rowid"
        % ",".join("?" for _ in deck_ids), deck_ids).fetchall()
    latest: dict[str, str] = {}
    for row in rev_rows:
        latest[row["deck_id"]] = row["revision_id"]
    revision_ids = list(latest.values())
    counts: dict[str, dict] = {}
    if revision_ids:
        marks = ",".join("?" for _ in revision_ids)
        for row in store.conn.execute(
                f"SELECT dc.oracle_id, s.name AS name, "
                f"COUNT(DISTINCT dc.revision_id) AS decks "
                f"FROM deck_card dc LEFT JOIN scryfall_card s "
                f"ON s.oracle_id = dc.oracle_id "
                f"WHERE dc.revision_id IN ({marks}) AND dc.is_commander = 0 "
                f"GROUP BY dc.oracle_id", revision_ids):
            counts[row["oracle_id"]] = {"name": row["name"],
                                        "decks": int(row["decks"])}
    return len(revision_ids), counts, [note + " (nur Decks dieses Commanders)"]


def compute_inclusion(store: Store, *, commander_oracle_id: str | None = None,
                      collection_id: str | None = None,
                      overrides: dict | None = None) -> dict:
    """Inclusion figures + their cohort definition, per current settings."""
    cfg = settings_mod.resolve(store, overrides)
    source = cfg["inclusion.source"]
    notes: list[str] = []
    if source == "edhrec":
        return _from_edhrec(store, cfg, commander_oracle_id)
    if source == "decklists":
        denominator, counts, notes, composition = _decklist_counts(
            store, cfg, commander_oracle_id)
        return _finish(cfg, source_label="geerntete echte Decklisten (Archidekt)",
                       denominator=denominator, counts=counts, notes=notes,
                       commander_oracle_id=commander_oracle_id,
                       extra_definition=composition)
    if source == "own_decks":
        denominator, counts, notes = _own_counts(store, collection_id,
                                                 commander_oracle_id)
        return _finish(cfg, source_label="eigene gespeicherte Decks",
                       denominator=denominator, counts=counts, notes=notes,
                       commander_oracle_id=commander_oracle_id)
    # combined: harvested deck lists + own decks pooled; EDHREC stays apart.
    d_den, d_counts, d_notes, d_composition = _decklist_counts(
        store, cfg, commander_oracle_id)
    o_den, o_counts, o_notes = _own_counts(store, collection_id,
                                           commander_oracle_id)
    counts = d_counts
    for oid, slot in o_counts.items():
        entry = counts.setdefault(oid, {"name": slot["name"], "decks": 0})
        entry["decks"] += slot["decks"]
    notes = d_notes + o_notes + [
        "combined = geerntete Decklisten + eigene Decks gepoolt (Nenner "
        "addiert); EDHREC wird nicht eingemischt (andere Nenner-Semantik).",
        "denominator_by_platform/denominator_by_bracket beziehen sich auf "
        "den geernteten Teil des Nenners."]
    return _finish(cfg, source_label="Decklisten + eigene Decks (gepoolt)",
                   denominator=d_den + o_den, counts=counts, notes=notes,
                   commander_oracle_id=commander_oracle_id,
                   extra_definition=d_composition)


def _selected_deck_uids(store: Store, cfg: dict,
                          commander_oracle_id: str | None) -> list[str]:
    """Deck uids of the settings selection (same filters as
    _decklist_counts, including the period rule), NOT yet deduped."""
    cutoff = _age_filter(cfg)
    # bracket-less decks join via their platform only (see
    # _decklist_counts for the cohort-honesty rationale)
    q = ("SELECT deck_uid FROM decklist_deck WHERE status='AVAILABLE' "
         "AND platform IN (%s) AND (bracket_level IN (%s) "
         "OR bracket_level IS NULL)" % (
             ",".join("?" for _ in cfg["inclusion.platforms"]),
             ",".join("?" for _ in cfg["inclusion.brackets"])))
    args: list = [*cfg["inclusion.platforms"], *cfg["inclusion.brackets"]]
    if commander_oracle_id is not None:
        q += " AND commander_oracle_id=?"
        args.append(commander_oracle_id)
    if cutoff:
        q += " AND fetched_at>=?"
        args.append(cutoff)
    if cfg["inclusion.date_from"] or cfg["inclusion.date_to"]:
        q += " AND source_updated_at IS NOT NULL"
        if cfg["inclusion.date_from"]:
            q += " AND substr(source_updated_at,1,10)>=?"
            args.append(cfg["inclusion.date_from"])
        if cfg["inclusion.date_to"]:
            q += " AND substr(source_updated_at,1,10)<=?"
            args.append(cfg["inclusion.date_to"])
    return [r["deck_uid"] for r in store.conn.execute(q, args)]


def cooccurrence(store: Store, oracle_id: str, *,
                 commander_oracle_id: str | None = None,
                 limit: int = 25,
                 overrides: dict | None = None) -> dict:
    """Co-occurrence of one card in the canonical harvested decks of
    the current settings selection (ranking plan A2): for every
    partner card, the decks containing
    both, and the LIFT P(partner|card) / P(partner) — how much more
    often the partner appears alongside this card than overall.
    Commander entries never count; unmapped rows (oracle_id NULL)
    stay unassigned. Combo partners (a shared Commander Spellbook
    combo in the card's latest snapshot) are flagged (A4)."""
    import json as _json

    cfg = settings_mod.resolve(store, overrides)
    # _canonical_decks returns (canonical, excluded) since the upstream
    # #1207 fix: decks without a countable card never enter the
    # universe, so the co-occurrence denominator is the same canonical
    # denominator _decklist_counts reports.
    canonical, excluded_no_countable = _canonical_decks(
        store, _selected_deck_uids(store, cfg, commander_oracle_id))
    denominator = len(canonical)
    definition = {
        "source": "decklists",
        "platforms": cfg["inclusion.platforms"],
        "brackets": cfg["inclusion.brackets"],
        "date_from": cfg["inclusion.date_from"],
        "date_to": cfg["inclusion.date_to"],
        "commander_oracle_id": commander_oracle_id,
        "denominator": denominator,
        "excluded_no_countable_card": excluded_no_countable,
        "counting": "canonical decks (content dedupe); commander "
                    "entries excluded; quantity > 0",
    }
    out: dict = {"oracle_id": oracle_id, "definition": definition,
                 "decks_with_card": 0, "partners": []}
    if not canonical:
        out["note"] = "keine kanonischen Decks in der Auswahl"
        return out
    deck_cards: dict[str, set] = {}
    with _universe_table(store.conn, canonical) as table:
        for row in store.conn.execute(
                f"SELECT c.deck_uid, c.oracle_id FROM decklist_card c "
                f"JOIN {table} u ON u.deck_uid = c.deck_uid "
                f"WHERE c.is_commander=0 AND c.oracle_id IS NOT NULL "
                f"AND c.quantity>0"):
            deck_cards.setdefault(row["deck_uid"], set()).add(
                row["oracle_id"])
    with_card = [u for u, cards in deck_cards.items() if oracle_id in cards]
    out["decks_with_card"] = len(with_card)
    if not with_card:
        out["note"] = "Karte kommt in keinem kanonischen Deck der Auswahl vor"
        return out
    global_counts: dict[str, int] = {}
    for cards in deck_cards.values():
        for oid in cards:
            global_counts[oid] = global_counts.get(oid, 0) + 1
    together: dict[str, int] = {}
    for uid in with_card:
        for oid in deck_cards[uid]:
            if oid != oracle_id:
                together[oid] = together.get(oid, 0) + 1
    # Combo partners of this card (latest Spellbook snapshot).
    combo_partners: set = set()
    snap = latest_snapshot(store, "commanderspellbook", "spellbook_card",
                           oracle_id=oracle_id)
    if snap is not None:
        for row in store.conn.execute(
                "SELECT card_oracle_ids_json FROM spellbook_combo "
                "WHERE snapshot_id=?", (snap["snapshot_id"],)):
            try:
                ids = _json.loads(row["card_oracle_ids_json"] or "[]")
            except ValueError:
                continue
            if oracle_id in ids:
                combo_partners.update(i for i in ids if i != oracle_id)
    # Name lookup in chunks: the partner set of a popular card can
    # exceed SQLite's bound-variable cap, the same reason the universe
    # queries above go through a TEMP table.
    names: dict[str, str] = {}
    partner_ids = list(together)
    for start in range(0, len(partner_ids), 500):
        chunk = partner_ids[start:start + 500]
        for r in store.conn.execute(
                "SELECT oracle_id, name FROM scryfall_card "
                "WHERE oracle_id IN (%s)" % ",".join("?" for _ in chunk),
                chunk):
            names[r["oracle_id"]] = r["name"]
    partners = []
    for oid, both in together.items():
        p_partner = global_counts[oid] / denominator
        lift = (both / len(with_card)) / p_partner if p_partner else None
        partners.append({
            "oracle_id": oid, "name": names.get(oid),
            "decks_together": both,
            "decks_with_partner": global_counts[oid],
            "share_of_card_decks": both / len(with_card),
            "lift": lift,
            "combo_partner": oid in combo_partners,
        })
    partners.sort(key=lambda p: (-(p["lift"] or 0), -p["decks_together"],
                                 p["name"] or ""))
    out["partners"] = partners[:limit]
    out["partners_total"] = len(partners)
    return out
