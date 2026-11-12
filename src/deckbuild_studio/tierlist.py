"""Tier computation — docs/TIERLIST_DESIGN.md, algorithm `tierlist/1.0.0`.

A tier is a pure function of local, provenance-carrying snapshots:
same inputs ⇒ same tier, bit for bit. Missing data is UNAVAILABLE,
never 0; unavailable signals drop out of the weighted score and their
weight lowers the evidence score, which gates/caps the tier. Cohorts
are never mixed: EDHREC bracket stats feed only the context tier of
their own bracket; the global tier uses only cohort-free signals.

Signals (design §3):
  * EDHREC global inclusion (global, w 0.55) — banded mapping.
  * EDHREC cohort inclusion (context, w 0.35) + synergy (w 0.25).
  * Playgroup win-rate lift (both scopes, w 0.25) — observational,
    n >= 25 (the source's own threshold), shrinkage n/(n+50).
  * Spellbook combo density (both scopes, w 0.20 global / 0.15
    context) — exact card-page total, else the captured count as a
    labelled lower bound; total unknown ⇒ UNAVAILABLE.
Salt, price, Game-Changer/Banned flags and role claims are markers /
context in the evidence payload — they NEVER enter the score.

Owner marks (§5) are not read here at all: this module never touches
the ``mark`` table, so flipping a mark cannot change a tier.
"""
from __future__ import annotations

import json

from .external import BRACKETS, latest_snapshot
from .store import Store, utcnow

ALGO_VERSION = "tierlist/1.0.0"

GLOBAL_WEIGHTS = {
    "edhrec_global_inclusion": 0.55,
    "playgroup_win_lift": 0.25,
    "spellbook_combo_density": 0.20,
}
CONTEXT_WEIGHTS = {
    "edhrec_cohort_inclusion": 0.35,
    "edhrec_cohort_synergy": 0.25,
    "playgroup_win_lift": 0.25,
    "spellbook_combo_density": 0.15,
}
# Signals that count as performance/adoption evidence for the S gate.
S_GATE_SIGNALS = {"edhrec_global_inclusion", "edhrec_cohort_inclusion",
                  "playgroup_win_lift"}
PLAYGROUP_MIN_N = 25       # Playgroup's own reliability threshold
PLAYGROUP_SHRINKAGE_K = 50
TIER_ORDER = ["U", "D", "C", "B", "A", "S"]  # ascending strength; U = unrated

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tier_assignment (
    oracle_id TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global',
    commander_oracle_id TEXT NOT NULL DEFAULT '',
    bracket TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL,
    score REAL,
    evidence REAL NOT NULL,
    signals_json TEXT NOT NULL DEFAULT '{}',
    algo_version TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    input_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (oracle_id, scope, commander_oracle_id, bracket)
);
CREATE INDEX IF NOT EXISTS tier_assignment_scope
    ON tier_assignment(scope, commander_oracle_id, bracket, tier);
"""


def ensure_schema(store: Store) -> None:
    store.conn.executescript(_SCHEMA)


# --------------------------------------------------------------------------
# Band mappings (design §3) — pure functions
# --------------------------------------------------------------------------

def _band(value: float, steps: list[tuple[float, float]], below: float) -> float:
    for threshold, subscore in steps:
        if value >= threshold:
            return subscore
    return below


def global_inclusion_subscore(inclusion: float) -> float:
    if inclusion == 0:
        return 0.00
    return _band(inclusion, [(0.30, 1.00), (0.15, 0.85), (0.05, 0.65),
                             (0.02, 0.50), (0.008, 0.35), (0.003, 0.20)], 0.10)


def cohort_inclusion_subscore(inclusion: float) -> float:
    if inclusion == 0:
        return 0.00
    return _band(inclusion, [(0.60, 1.00), (0.40, 0.85), (0.25, 0.65),
                             (0.12, 0.50), (0.05, 0.35)], 0.15)


def synergy_subscore(synergy: float) -> float:
    return _band(synergy, [(0.30, 1.00), (0.15, 0.80), (0.05, 0.60),
                           (-0.05, 0.45), (-0.15, 0.30)], 0.15)


def lift_subscore(adjusted_lift_pp: float) -> float:
    return _band(adjusted_lift_pp, [(8.0, 1.00), (5.0, 0.80), (3.0, 0.65),
                                    (1.0, 0.50), (0.0, 0.40), (-2.0, 0.30)], 0.15)


def combo_subscore(total: int) -> float:
    if total == 0:
        return 0.00
    return _band(total, [(26, 1.00), (11, 0.80), (6, 0.65), (3, 0.50)], 0.30)


def adjusted_lift(lift_pp: float, n: int) -> float:
    """Playgroup lift with sample-size shrinkage (design §3.3)."""
    return lift_pp * n / (n + PLAYGROUP_SHRINKAGE_K)


def salt_band(salt: float | None) -> str | None:
    if salt is None:
        return None
    if salt >= 1.5:
        return "high friction"
    if salt >= 1.0:
        return "noticeable"
    return "low"


def budget_band(min_eur: float | None) -> str | None:
    if min_eur is None:
        return None
    if min_eur <= 1:
        return "≤ €1"
    if min_eur <= 5:
        return "≤ €5"
    if min_eur <= 15:
        return "≤ €15"
    return "> €15"


# --------------------------------------------------------------------------
# Combination rule (design §4)
# --------------------------------------------------------------------------

def combine(signals: list[dict]) -> dict:
    """Weighted score + evidence over the AVAILABLE signals, then the
    tier bands and gates/caps. ``signals`` entries carry ``signal``,
    ``weight`` and ``subscore`` (None when unavailable)."""
    available = [s for s in signals if s.get("subscore") is not None]
    weight_sum = sum(s["weight"] for s in available)
    evidence = round(weight_sum, 10)
    score = None
    if available:
        score = sum(s["weight"] * s["subscore"] for s in available) / weight_sum
    tier = "U"
    if score is not None and evidence >= 0.35:
        if score >= 0.85:
            tier = "S"
        elif score >= 0.70:
            tier = "A"
        elif score >= 0.55:
            tier = "B"
        elif score >= 0.40:
            tier = "C"
        else:
            tier = "D"
        cap = None
        if evidence < 0.55:
            cap = "B"
        elif evidence < 0.80:
            cap = "A"
        if cap is not None and TIER_ORDER.index(tier) > TIER_ORDER.index(cap):
            tier = cap
        if tier == "S" and not any(
                s["signal"] in S_GATE_SIGNALS and s["subscore"] >= 0.85
                for s in available):
            tier = "A"
    return {"tier": tier, "score": score, "evidence": evidence}


# --------------------------------------------------------------------------
# Signal extraction — pure readers over stored snapshots
# --------------------------------------------------------------------------

def _snap_base(row) -> dict:
    return {"snapshot_id": row["snapshot_id"], "source_url": row["source_url"],
            "fetched_at": row["fetched_at"],
            "parser_version": row["parser_version"], "status": row["status"]}


def _unavailable(name: str, weight: float, reason: str,
                 snap: dict | None = None) -> dict:
    out = {"signal": name, "weight": weight, "available": False,
           "subscore": None, "reason": reason}
    if snap is not None:
        out.update(snap)
    return out


def _available(name: str, weight: float, value: dict, subscore: float,
               snap: dict, **extra) -> dict:
    out = {"signal": name, "weight": weight, "available": True,
           "value": value, "subscore": subscore}
    out.update(snap)
    out.update(extra)
    return out


def _edhrec_global_signal(store: Store, oracle_id: str, weight: float) -> dict:
    row = latest_snapshot(store, "edhrec", "edhrec_card", oracle_id=oracle_id)
    if row is None:
        return _unavailable("edhrec_global_inclusion", weight,
                            "not fetched (sync-edhrec-cards)")
    snap = _snap_base(row)
    grow = store.conn.execute(
        "SELECT * FROM edhrec_card_global WHERE snapshot_id=?",
        (row["snapshot_id"],)).fetchone()
    if grow is None or grow["inclusion"] is None:
        return _unavailable("edhrec_global_inclusion", weight,
                            "snapshot carries no inclusion value", snap)
    return _available(
        "edhrec_global_inclusion", weight,
        {"inclusion": grow["inclusion"], "num_decks": grow["num_decks"],
         "potential_decks": grow["potential_decks"]},
        global_inclusion_subscore(grow["inclusion"]), snap)


def _playgroup_lift_signal(store: Store, oracle_id: str, weight: float) -> dict:
    """Global scope: per-card Card-Atlas observed win-rate gap."""
    row = latest_snapshot(store, "playgroup", "playgroup_card",
                          oracle_id=oracle_id)
    if row is None:
        return _unavailable("playgroup_win_lift", weight,
                            "not fetched (sync-card-atlas)")
    snap = _snap_base(row)
    fields = {}
    if row["payload_json"]:
        try:
            fields = (json.loads(row["payload_json"]) or {}).get("fields") or {}
        except json.JSONDecodeError:
            fields = {}
    win = fields.get("win_rates_observed") or {}
    gap = win.get("observed_gap_pp")
    if gap is None:
        return _unavailable("playgroup_win_lift", weight,
                            "card page publishes no observed win-rate gap", snap)
    ns = [win[k] for k in ("n_cast", "n_never_drawn")
          if isinstance(win.get(k), (int, float))]
    n = int(min(ns)) if ns else None
    if n is None:
        return _unavailable("playgroup_win_lift", weight,
                            "win-rate gap published without a sample size", snap)
    if n < PLAYGROUP_MIN_N:
        return _unavailable("playgroup_win_lift", weight,
                            f"insufficient data: n={n} < {PLAYGROUP_MIN_N}", snap)
    adj = adjusted_lift(float(gap), n)
    return _available(
        "playgroup_win_lift", weight,
        {"lift_pp": float(gap), "adjusted_lift_pp": adj, "n": n,
         "win_rate_cast_pct": win.get("win_rate_cast_pct"),
         "win_rate_never_drawn_pct": win.get("win_rate_never_drawn_pct"),
         "ci95_pp": win.get("ci95_pp")},
        lift_subscore(adj), snap,
        semantics="observational — correlation, not causation")


def _spellbook_facts(store: Store, oracle_id: str,
                     cache: dict | None) -> tuple | None:
    """(snap_base, total, captured, status, coverage_status) for the
    card's latest Spellbook snapshot, or None when never fetched.
    The facts are scope/weight-independent, so a compute run may
    cache them per card (the same card appears in many contexts)."""
    if cache is not None and oracle_id in cache:
        return cache[oracle_id]
    row = latest_snapshot(store, "commanderspellbook", "spellbook_card",
                          oracle_id=oracle_id)
    facts = None
    if row is not None:
        payload = {}
        if row["payload_json"]:
            try:
                payload = json.loads(row["payload_json"]) or {}
            except json.JSONDecodeError:
                payload = {}
        total = payload.get("combos_total")
        if not isinstance(total, int):
            total = row["displayed_total"]
        facts = (_snap_base(row), total, row["captured_count"] or 0,
                 row["status"], row["coverage_status"])
    if cache is not None:
        cache[oracle_id] = facts
    return facts


def _spellbook_signal(store: Store, oracle_id: str, weight: float,
                      scope: str, cache: dict | None = None) -> dict:
    facts = _spellbook_facts(store, oracle_id, cache)
    if facts is None:
        return _unavailable("spellbook_combo_density", weight,
                            "not fetched (sync-spellbook)")
    snap, total, captured, status, coverage_status = facts
    extra = {}
    if scope == "context":
        extra["context_free"] = True
    if isinstance(total, int):
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": total, "combos_captured": captured,
             "total_is_exact": True},
            combo_subscore(total), snap, **extra)
    if captured > 0:
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": None, "combos_captured": captured,
             "total_is_exact": False,
             "note": "captured count is a lower bound (search route "
                     "publishes no grand total)"},
            combo_subscore(captured), snap, **extra)
    if status == "NOT_FOUND" and coverage_status == "TOTAL_KNOWN":
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": 0, "combos_captured": 0, "total_is_exact": True},
            combo_subscore(0), snap, **extra)
    return _unavailable("spellbook_combo_density", weight,
                        "combo total unknown (no card page, no captured "
                        "combos)", snap)


def _markers(store: Store, oracle_id: str,
             cache: dict | None = None,
             roles_cache: dict | None = None) -> dict:
    """Non-score context: salt, budget, hard flags, role claims.
    Markers are scope-independent; a compute run may cache them per
    card instead of recomputing them for every context. Role claims
    should come from ``roles_cache`` (one batched roles_map call per
    card batch): roles_map runs an ensure_schema executescript on
    every call (~100 ms), which made per-card calls the dominant
    cost of a full compute (97% in profiling)."""
    if cache is not None and oracle_id in cache:
        return cache[oracle_id]
    markers = _markers_uncached(store, oracle_id, roles_cache)
    if cache is not None:
        cache[oracle_id] = markers
    return markers


def _markers_uncached(store: Store, oracle_id: str,
                      roles_cache: dict | None = None) -> dict:
    salt = None
    row = latest_snapshot(store, "edhrec", "edhrec_card", oracle_id=oracle_id)
    if row is not None:
        grow = store.conn.execute(
            "SELECT salt FROM edhrec_card_global WHERE snapshot_id=?",
            (row["snapshot_id"],)).fetchone()
        if grow is not None:
            salt = grow["salt"]
    price = store.conn.execute(
        "SELECT min_eur, min_eur_printing, derived_at FROM card_print_fact "
        "WHERE oracle_id=?", (oracle_id,)).fetchone()
    flags: list[str] = []
    try:
        from .reference import card_reference
        ref = card_reference(store, oracle_id)
    except Exception:
        ref = None
    if ref:
        flags = [f["flag"] for f in ref.get("flags") or []]
    roles: dict = {}
    try:
        if roles_cache is not None and oracle_id in roles_cache:
            roles = roles_cache[oracle_id]
        else:
            from .roles import roles_map
            roles = roles_map(store, [oracle_id]).get(oracle_id, {})
    except Exception:
        roles = {}
    return {
        "salt": salt, "salt_band": salt_band(salt),
        "budget_eur": price["min_eur"] if price else None,
        "budget_band": budget_band(price["min_eur"]) if price else None,
        "budget_printing": price["min_eur_printing"] if price else None,
        "flags": flags,
        "roles": roles,
    }


def global_signals(store: Store, oracle_id: str,
                   spellbook_cache: dict | None = None) -> list[dict]:
    w = GLOBAL_WEIGHTS
    return [
        _edhrec_global_signal(store, oracle_id, w["edhrec_global_inclusion"]),
        _playgroup_lift_signal(store, oracle_id, w["playgroup_win_lift"]),
        _spellbook_signal(store, oracle_id, w["spellbook_combo_density"],
                          "global", spellbook_cache),
    ]


# --------------------------------------------------------------------------
# Context scope (commander x bracket cohort)
# --------------------------------------------------------------------------

def _name_to_oracle(store: Store) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in store.conn.execute(
            "SELECT oracle_id, name, front_name FROM scryfall_card"):
        out.setdefault(r["name"], r["oracle_id"])
        if r["front_name"]:
            out.setdefault(r["front_name"], r["oracle_id"])
    return out


def _cohort_stats(store: Store, commander_oracle_id: str,
                  bracket: str,
                  name_map: dict[str, str] | None = None
                  ) -> tuple[object | None, dict[str, dict]]:
    """Latest AVAILABLE EDHREC stats snapshot of ONE bracket + its card
    rows keyed by oracle_id (name-mapped; multi-category duplicates
    collapse to the row with the most decks — the values are the same
    card in the same cohort). ``name_map`` may be shared across a
    whole compute run (building it scans the full Scryfall store)."""
    row = latest_snapshot(store, "edhrec", "edhrec_stats",
                          commander_oracle_id=commander_oracle_id,
                          bracket=bracket)
    if row is None or row["status"] != "AVAILABLE":
        return (row if row is not None else None), {}
    by_name = name_map if name_map is not None else _name_to_oracle(store)
    cards: dict[str, dict] = {}
    for stat in store.conn.execute(
            "SELECT * FROM edhrec_card_stat WHERE snapshot_id=? "
            "ORDER BY name, num_decks DESC", (row["snapshot_id"],)):
        oid = by_name.get(stat["name"])
        if oid is None or oid in cards:
            continue
        cards[oid] = {"inclusion": stat["inclusion"],
                      "num_decks": stat["num_decks"],
                      "potential_decks": stat["potential_decks"],
                      "synergy": stat["synergy"]}
    return row, cards


def _staples(store: Store, commander_oracle_id: str) -> tuple[object | None, dict[str, dict]]:
    """Latest Playgroup commander-page snapshot + its win staples keyed
    by oracle_id (rows whose name did not resolve to exactly one
    Scryfall card carry card_oracle_id NULL and are skipped)."""
    row = latest_snapshot(store, "playgroup", "playgroup_commander_page",
                          commander_oracle_id=commander_oracle_id)
    if row is None or row["status"] != "AVAILABLE":
        return (row if row is not None else None), {}
    cards: dict[str, dict] = {}
    for staple in store.conn.execute(
            "SELECT * FROM playgroup_commander_staple WHERE snapshot_id=?",
            (row["snapshot_id"],)):
        if staple["card_oracle_id"]:
            cards[staple["card_oracle_id"]] = {
                "lift_pp": staple["lift_pp"], "games": staple["games"]}
    return row, cards


def context_signals(store: Store, oracle_id: str, commander_oracle_id: str,
                    bracket: str, cohort: dict[str, dict],
                    staples: dict[str, dict],
                    snaps: dict[str, object | None],
                    spellbook_cache: dict | None = None) -> list[dict]:
    w = CONTEXT_WEIGHTS
    signals: list[dict] = []
    stat = cohort.get(oracle_id)
    stats_snap = snaps.get("stats")
    stats_base = _snap_base(stats_snap) if stats_snap is not None else None
    if stat is not None and stat["inclusion"] is not None:
        signals.append(_available(
            "edhrec_cohort_inclusion", w["edhrec_cohort_inclusion"],
            {"inclusion": stat["inclusion"], "num_decks": stat["num_decks"],
             "potential_decks": stat["potential_decks"], "bracket": bracket},
            cohort_inclusion_subscore(stat["inclusion"]), stats_base))
    else:
        signals.append(_unavailable(
            "edhrec_cohort_inclusion", w["edhrec_cohort_inclusion"],
            "card not in this cohort's EDHREC stats (or no stats "
            "snapshot for the bracket)", stats_base))
    if stat is not None and stat["synergy"] is not None:
        signals.append(_available(
            "edhrec_cohort_synergy", w["edhrec_cohort_synergy"],
            {"synergy": stat["synergy"], "bracket": bracket},
            synergy_subscore(stat["synergy"]), stats_base))
    else:
        signals.append(_unavailable(
            "edhrec_cohort_synergy", w["edhrec_cohort_synergy"],
            "no synergy value for this card in this cohort", stats_base))
    staple = staples.get(oracle_id)
    pg_snap = snaps.get("page")
    pg_base = _snap_base(pg_snap) if pg_snap is not None else None
    if staple is not None and staple["lift_pp"] is not None \
            and staple["games"] is not None:
        if staple["games"] < PLAYGROUP_MIN_N:
            signals.append(_unavailable(
                "playgroup_win_lift", w["playgroup_win_lift"],
                f"insufficient data: n={staple['games']} < {PLAYGROUP_MIN_N}",
                pg_base))
        else:
            adj = adjusted_lift(staple["lift_pp"], staple["games"])
            signals.append(_available(
                "playgroup_win_lift", w["playgroup_win_lift"],
                {"lift_pp": staple["lift_pp"], "adjusted_lift_pp": adj,
                 "n": staple["games"],
                 "note": "commander-page staple lift (commander-wide, "
                         "not bracket-specific)"},
                lift_subscore(adj), pg_base,
                semantics="observational — correlation, not causation"))
    else:
        signals.append(_unavailable(
            "playgroup_win_lift", w["playgroup_win_lift"],
            "card is not a win staple on this commander's Playgroup "
            "page (or no page snapshot)", pg_base))
    signals.append(_spellbook_signal(
        store, oracle_id, w["spellbook_combo_density"], "context",
        spellbook_cache))
    return signals


# --------------------------------------------------------------------------
# Computation + storage
# --------------------------------------------------------------------------

def _payload(scope: str, signals: list[dict], markers: dict,
             commander_oracle_id: str = "", bracket: str = "") -> dict:
    payload: dict = {
        "scope": scope,
        "algo_version": ALGO_VERSION,
        "signals": signals,
        "missing_signals": [s["signal"] for s in signals
                            if s.get("subscore") is None],
        "markers": markers,
    }
    if scope == "context":
        payload["commander_oracle_id"] = commander_oracle_id
        payload["bracket"] = bracket
        payload["cohort_label"] = f"{bracket} cohort (EDHREC) + Playgroup commander page"
    return payload


def _store_row(store: Store, oracle_id: str, scope: str,
               commander_oracle_id: str, bracket: str,
               signals: list[dict], markers: dict, computed_at: str) -> dict:
    result = combine(signals)
    payload = _payload(scope, signals, markers, commander_oracle_id, bracket)
    snap_ids = sorted({s["snapshot_id"] for s in signals
                       if s.get("snapshot_id")})
    store.conn.execute(
        "INSERT OR REPLACE INTO tier_assignment(oracle_id,scope,"
        "commander_oracle_id,bracket,tier,score,evidence,signals_json,"
        "algo_version,computed_at,input_snapshot_ids_json) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (oracle_id, scope, commander_oracle_id, bracket, result["tier"],
         result["score"], result["evidence"],
         json.dumps(payload, ensure_ascii=False, sort_keys=True),
         ALGO_VERSION, computed_at, json.dumps(snap_ids)))
    return result


def _tier_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1
    return counts


def _u_reasons(rows_signals: list[list[dict]]) -> dict[str, int]:
    reasons: dict[str, int] = {}
    for signals in rows_signals:
        for s in signals:
            if s.get("subscore") is None:
                reasons[s["signal"]] = reasons.get(s["signal"], 0) + 1
    return reasons


def compute_tiers(store: Store, *, collection_id: str | None = None,
                  commander_oracle_id: str | None = None,
                  bracket: str | None = None) -> dict:
    """(Re)compute tier rows. Default: global scope for every card that
    is in a collection or carries a global signal, plus every fetched
    commander x bracket context. Deterministic over unchanged
    snapshots (only ``computed_at`` differs between runs)."""
    ensure_schema(store)
    if bracket is not None and bracket not in BRACKETS:
        level = {2: "core", 3: "upgraded", 4: "optimized"}
        try:
            bracket = level[int(bracket)]  # type: ignore[arg-type]
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"unknown bracket {bracket!r}") from None
    computed_at = utcnow()
    summary: dict = {"algo_version": ALGO_VERSION, "computed_at": computed_at}
    # Per-run caches: markers and Spellbook facts are scope-independent
    # and the name map scans the whole Scryfall store — computing them
    # once per card/run instead of once per context keeps a full
    # 63-commander x 3-bracket run tractable (results are identical).
    markers_cache: dict = {}
    spellbook_cache: dict = {}
    roles_cache: dict = {}
    name_map: dict[str, str] | None = None

    def _preload_roles(oids) -> None:
        try:
            from .roles import roles_map
            roles_cache.update(roles_map(store, sorted(oids)))
        except Exception:
            pass  # per-card fallback in _markers stays correct

    # ---- global scope -------------------------------------------------
    if commander_oracle_id is None:
        if collection_id:
            universe = {r["oracle_id"] for r in store.conn.execute(
                "SELECT DISTINCT oracle_id FROM physical_lot "
                "WHERE collection_id=?", (collection_id,))}
        else:
            universe = {r["oracle_id"] for r in store.conn.execute(
                "SELECT DISTINCT oracle_id FROM physical_lot")}
        universe |= {r["oracle_id"] for r in store.conn.execute(
            "SELECT oracle_id FROM edhrec_card_global")}
        universe |= {r["oracle_id"] for r in store.conn.execute(
            "SELECT DISTINCT oracle_id FROM external_snapshot "
            "WHERE kind IN ('spellbook_card','playgroup_card') "
            "AND oracle_id IS NOT NULL")}
        if collection_id:
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='global' "
                "AND oracle_id IN (SELECT DISTINCT oracle_id FROM "
                "physical_lot WHERE collection_id=?)", (collection_id,))
        else:
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='global'")
        rows: list[dict] = []
        u_signals: list[list[dict]] = []
        _preload_roles(universe)
        for oid in sorted(universe):
            signals = global_signals(store, oid, spellbook_cache)
            result = _store_row(store, oid, "global", "", "", signals,
                                _markers(store, oid, markers_cache,
                                         roles_cache),
                                computed_at)
            rows.append(result)
            if result["tier"] == "U":
                u_signals.append(signals)
        summary["global"] = {
            "cards": len(rows), "tiers": _tier_counts(rows),
            "u_missing_signal_counts": _u_reasons(u_signals),
        }

    # ---- context scope ------------------------------------------------
    commanders = {r["commander_oracle_id"] for r in store.conn.execute(
        "SELECT DISTINCT commander_oracle_id FROM external_snapshot "
        "WHERE kind IN ('edhrec_stats','playgroup_commander_page') "
        "AND commander_oracle_id IS NOT NULL")}
    if commander_oracle_id is not None:
        commanders &= {commander_oracle_id}
    brackets = [bracket] if bracket else list(BRACKETS)
    ctx_rows: list[dict] = []
    ctx_u: list[list[dict]] = []
    contexts_with_cards = 0
    contexts_total = 0
    for coid in sorted(commanders):
        page_row, staples = _staples(store, coid)
        for br in brackets:
            if name_map is None:
                name_map = _name_to_oracle(store)
            stats_row, cohort = _cohort_stats(store, coid, br, name_map)
            if stats_row is None and page_row is None:
                continue
            if stats_row is not None and stats_row["status"] != "AVAILABLE" \
                    and page_row is None:
                continue
            contexts_total += 1
            cards = set(cohort) | set(staples)
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='context' "
                "AND commander_oracle_id=? AND bracket=?", (coid, br))
            if cards:
                contexts_with_cards += 1
            snaps = {"stats": stats_row, "page": page_row}
            _preload_roles(cards)
            for oid in sorted(cards):
                signals = context_signals(store, oid, coid, br, cohort,
                                          staples, snaps, spellbook_cache)
                result = _store_row(store, oid, "context", coid, br,
                                    signals,
                                    _markers(store, oid, markers_cache,
                                             roles_cache),
                                    computed_at)
                ctx_rows.append(result)
                if result["tier"] == "U":
                    ctx_u.append(signals)
    summary["context"] = {
        "commanders": len(commanders), "brackets": brackets,
        "contexts_total": contexts_total,
        "contexts_with_rated_cards": contexts_with_cards,
        "cards": len(ctx_rows), "tiers": _tier_counts(ctx_rows),
        "u_missing_signal_counts": _u_reasons(ctx_u),
    }
    store.conn.commit()
    return summary


# --------------------------------------------------------------------------
# Read API (used by the web layer)
# --------------------------------------------------------------------------

def _row_dict(row) -> dict:
    d = dict(row)
    d["signals"] = json.loads(d.pop("signals_json") or "{}")
    d["input_snapshot_ids"] = json.loads(d.pop("input_snapshot_ids_json")
                                         or "[]")
    return d


def get_tier(store: Store, oracle_id: str, *,
             commander_oracle_id: str | None = None,
             bracket: str | None = None) -> dict | None:
    ensure_schema(store)
    if commander_oracle_id is None:
        row = store.conn.execute(
            "SELECT * FROM tier_assignment WHERE oracle_id=? "
            "AND scope='global'", (oracle_id,)).fetchone()
    else:
        row = store.conn.execute(
            "SELECT * FROM tier_assignment WHERE oracle_id=? "
            "AND scope='context' AND commander_oracle_id=? AND bracket=?",
            (oracle_id, commander_oracle_id, bracket or "")).fetchone()
    return _row_dict(row) if row is not None else None


def tiers_map(store: Store, oracle_ids: list[str]) -> dict[str, dict]:
    """Compact global-tier lookup for card lists (badge rendering):
    tier/score/evidence plus the non-score markers (salt band, budget
    band, hard flags) — markers never influence the tier itself."""
    ensure_schema(store)
    out: dict[str, dict] = {}
    if not oracle_ids:
        return out
    marks = ",".join("?" for _ in oracle_ids)
    for row in store.conn.execute(
            f"SELECT oracle_id, tier, score, evidence, algo_version, "
            f"computed_at, signals_json FROM tier_assignment "
            f"WHERE scope='global' AND oracle_id IN ({marks})",
            list(oracle_ids)):
        d = dict(row)
        try:
            markers = (json.loads(d.pop("signals_json") or "{}")
                       .get("markers") or {})
        except json.JSONDecodeError:
            markers = {}
        d["markers"] = {k: markers.get(k) for k in
                        ("salt", "salt_band", "budget_eur", "budget_band",
                         "flags")}
        out[row["oracle_id"]] = d
    return out


def list_tiers(store: Store, *, scope: str = "global",
               commander_oracle_id: str | None = None,
               bracket: str | None = None, tier: str | None = None,
               collection_id: str | None = None,
               limit: int | None = None) -> list[dict]:
    ensure_schema(store)
    q = ("SELECT t.*, COALESCE(s.name, '') AS name FROM tier_assignment t "
         "LEFT JOIN scryfall_card s ON s.oracle_id = t.oracle_id "
         "WHERE t.scope=?")
    args: list = [scope]
    if scope == "context":
        if commander_oracle_id is not None:
            q += " AND t.commander_oracle_id=?"
            args.append(commander_oracle_id)
        if bracket is not None:
            q += " AND t.bracket=?"
            args.append(bracket)
    if tier is not None:
        q += " AND t.tier=?"
        args.append(tier)
    if collection_id is not None:
        q += (" AND t.oracle_id IN (SELECT DISTINCT oracle_id FROM "
              "physical_lot WHERE collection_id=?)")
        args.append(collection_id)
    q += " ORDER BY t.tier, t.score DESC, name"
    if limit is not None:
        q += " LIMIT ?"
        args.append(limit)
    return [_row_dict(r) for r in store.conn.execute(q, args)]
