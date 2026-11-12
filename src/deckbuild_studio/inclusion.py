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


def _canonical_decks(store: Store, deck_uids: list[str]) -> list[str]:
    """One deck uid per distinct content fingerprint inside the selected
    universe (lowest deck uid wins). The same list re-published under
    another deck id — 163 excess ids in the real harvest, largest group
    55 copies — must not inflate a denominator or a hit count."""
    if not deck_uids:
        return []
    marks = ",".join("?" for _ in deck_uids)
    by_deck: dict[str, list[tuple]] = {}
    for row in store.conn.execute(
            f"SELECT deck_uid, entry_key, quantity, is_commander "
            f"FROM decklist_card WHERE deck_uid IN ({marks}) "
            f"ORDER BY deck_uid", deck_uids):
        by_deck.setdefault(row["deck_uid"], []).append(
            (row["entry_key"], row["quantity"], row["is_commander"]))
    first: dict[str, str] = {}
    for uid in sorted(deck_uids):
        first.setdefault(_content_fingerprint(by_deck.get(uid, [])), uid)
    return sorted(first.values())


def _decklist_counts(store: Store, cfg: dict,
                     commander_oracle_id: str | None
                     ) -> tuple[int, dict, list[str], dict]:
    notes: list[str] = []
    cutoff = _age_filter(cfg)
    q = ("SELECT deck_uid FROM decklist_deck WHERE status='AVAILABLE' "
         "AND platform IN (%s) AND bracket_level IN (%s)" % (
             ",".join("?" for _ in cfg["inclusion.platforms"]),
             ",".join("?" for _ in cfg["inclusion.brackets"])))
    args: list = [*cfg["inclusion.platforms"], *cfg["inclusion.brackets"]]
    if commander_oracle_id is not None:
        q += " AND commander_oracle_id=?"
        args.append(commander_oracle_id)
    if cutoff:
        q += " AND fetched_at>=?"
        args.append(cutoff)
    deck_uids = [r["deck_uid"] for r in store.conn.execute(q, args)]
    canonical = _canonical_decks(store, deck_uids)
    removed = len(deck_uids) - len(canonical)
    if removed:
        notes.append(f"{removed} von {len(deck_uids)} Deck-IDs sind "
                     "inhaltsgleiche Duplikate (gleicher Karteninhalt "
                     "unter anderer Deck-ID) und zählen einmal "
                     "(niedrigste Deck-ID gewinnt).")
    composition: dict = {"denominator_by_platform": {},
                         "denominator_by_bracket": {}}
    if canonical:
        marks = ",".join("?" for _ in canonical)
        for row in store.conn.execute(
                f"SELECT platform, bracket_level FROM decklist_deck "
                f"WHERE deck_uid IN ({marks})", canonical):
            by_platform = composition["denominator_by_platform"]
            by_bracket = composition["denominator_by_bracket"]
            by_platform[str(row["platform"])] = \
                by_platform.get(str(row["platform"]), 0) + 1
            by_bracket[str(row["bracket_level"])] = \
                by_bracket.get(str(row["bracket_level"]), 0) + 1
        composition["denominator_by_platform"] = dict(
            sorted(composition["denominator_by_platform"].items()))
        composition["denominator_by_bracket"] = dict(
            sorted(composition["denominator_by_bracket"].items()))
    counts: dict[str, dict] = {}
    if canonical:
        marks = ",".join("?" for _ in canonical)
        for row in store.conn.execute(
                f"SELECT dc.oracle_id, dc.card_name, COUNT(DISTINCT dc.deck_uid) decks "
                f"FROM decklist_card dc WHERE dc.deck_uid IN ({marks}) "
                f"AND dc.is_commander=0 AND dc.oracle_id IS NOT NULL "
                f"AND dc.quantity > 0 "
                f"GROUP BY dc.oracle_id, dc.card_name", canonical):
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
