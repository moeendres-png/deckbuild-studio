"""Tier computation — docs/TIERLIST_DESIGN.md, algorithm `tierlist/1.1.0`.

Two strictly separate fields (docs/TIERLIST_CPL_ADAPTATION.md §1,
owner decision 2026-11-12):

* **Evidenz-Tier (Stärke-Schätzung)** — scopes ``global`` + ``context``:
  the 1.0.0 multi-signal model, UNCHANGED weights and gates. A tier is
  a pure function of local, provenance-carrying snapshots: same
  inputs ⇒ same tier, bit for bit. Missing data is UNAVAILABLE, never
  0; unavailable signals drop out of the weighted score and their
  weight lowers the evidence score, which gates/caps the tier.
  Cohorts are never mixed. **Counted decklist frequency is NOT an
  input** — strength does not come from frequency alone.
  Signals: EDHREC global inclusion (global, w 0.55); EDHREC cohort
  inclusion (context, w 0.35) + synergy (w 0.25); Playgroup win-rate
  lift (w 0.25; observational, n >= 25, shrinkage n/(n+50));
  Spellbook combo density (w 0.20 global / 0.15 context).
  A5: where a context's cohort stats carry no row for a card, the
  card page's "Top Commanders" entry supplies the SAME construct
  (share of that commander's decks running the card) as a labelled
  fallback inside ``edhrec_cohort_inclusion``
  (``measurement="card_page_top_commanders"``, bracket-agnostic).
* **Verbreitung (gezählt)** — scope ``universe``: CPL's pure counted
  tiers over the harvested deck lists of the settings selection
  (profiles ``all`` + one per commander + one per
  commander x bracket cohort): CPL share cuts, no weights, no model
  — data_class DERIVED_DESCRIPTIVE, keyed by a citable universe
  snapshot id (hash over the universe definition + canonical deck
  ids + per-deck content fingerprints). Absence in the universe is a
  counted 0; a universe below the minimum size yields U
  ("unbekannt"), never a forced figure. A cohort profile holds ONE
  bracket of ONE commander (cohorts are never mixed); it exists only
  when the selection holds at least one deck of that cohort.

The combined scopes are a weighted model and say so: their payloads
carry data_class HEURISTIC_MODEL and, for U rows, a u_reason code.

Salt, price, Game-Changer/Banned flags and role claims are markers /
context in the evidence payload — they NEVER enter any score.

Owner marks are not read here at all: this module never touches the
``mark`` table, so flipping a mark cannot change any number or tier
in either field (regression-tested for both).

1.0.0 -> 1.1.0: universe scope (Verbreitung), data_class/u_reason in
every payload, A5 Top-Commander fallback evidence, Spellbook payload
carries combo partner/result-type counts (A4), tier_assignment gains
universe_id. The strength model itself is byte-identical to 1.0.0.

1.1.0 -> 1.2.0 (docs/TIERLIST_1_2_DESIGN.md): a SECOND, separately
selectable strength model. The core signals, weights, bands and
gates are unchanged; 1.2.0 adds capped tournament components with
asymmetric evidence — EDHTop16 play rate (global, w 0.10), TopDeck
conversion (global, w 0.10, shrinkage towards the cohort baseline)
and EDHTop16 per-commander play rate (context, w 0.10, entries_n
>= 25 gate). A tournament component is either present with a
subscore >= 0.50 (neutral floor) or UNAVAILABLE; absence is never a
0 and never lowers a tier. The S gate stays reserved for core
signals; tournament weight alone (<= 0.20) cannot cross the U gate.
Model selection + the three signal toggles are owner settings
(``tierlist.model_version``, ``tierlist.signal_*``); rows of both
versions coexist (algo_version is part of the primary key) and the
read API serves the selected version. Computing under 1.1.0 remains
byte-identical to before. The Verbreitung is computed identically
under both models.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import settings as settings_mod
from .decklists import BRACKET_NAMES
from .decklists import PARSER_VERSION as DECKLIST_PARSER_VERSION
from .external import BRACKETS, latest_snapshot
from .inclusion import _age_filter, _content_fingerprint, _universe_table
from .store import Store, utcnow

ALGO_VERSION = "tierlist/1.1.0"
MODEL_1_1_0 = "tierlist/1.1.0"
MODEL_1_2_0 = "tierlist/1.2.0"
MODELS = (MODEL_1_1_0, MODEL_1_2_0)

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
# tierlist/1.2.0 (docs/TIERLIST_1_2_DESIGN.md): the core weights above
# stay untouched; tournament layers are ADDITIONAL capped components.
# Asymmetric evidence: a tournament component is either present with a
# subscore >= TOURNAMENT_FLOOR (neutral 0.50) or UNAVAILABLE — absence
# is never a 0, and no tournament subscore ever falls below neutral.
GLOBAL_WEIGHTS_1_2 = {
    **GLOBAL_WEIGHTS,
    "edhtop16_play_rate": 0.10,
    "topdeck_conversion": 0.10,
}
CONTEXT_WEIGHTS_1_2 = {
    **CONTEXT_WEIGHTS,
    "edhtop16_commander_play_rate": 0.10,
}
TOURNAMENT_FLOOR = 0.50
TOPDECK_SHRINKAGE_K = 50      # same constant as Playgroup shrinkage
EDHTOP16_COMMANDER_MIN_ENTRIES = 25  # Playgroup's reliability threshold


@dataclass(frozen=True)
class ModelConfig:
    """Which model a compute run executes: the version plus the
    owner toggles of the optional 1.2.0 tournament signals (settings
    ``tierlist.signal_*``). Under 1.1.0 the toggles are inert."""

    version: str = MODEL_1_1_0
    edhtop16_global: bool = True
    edhtop16_commander: bool = True
    topdeck_conversion: bool = True

    @property
    def is_1_2(self) -> bool:
        return self.version == MODEL_1_2_0


def _model_from_cfg(cfg: dict, model: str | None) -> ModelConfig:
    version = model or cfg["tierlist.model_version"]
    if version not in MODELS:
        raise ValueError(f"unknown tierlist model {version!r} "
                         f"(known: {list(MODELS)})")
    return ModelConfig(
        version=version,
        edhtop16_global=bool(cfg["tierlist.signal_edhtop16_global"]),
        edhtop16_commander=bool(cfg["tierlist.signal_edhtop16_commander"]),
        topdeck_conversion=bool(cfg["tierlist.signal_topdeck_conversion"]))
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
    universe_id TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL,
    score REAL,
    evidence REAL NOT NULL,
    signals_json TEXT NOT NULL DEFAULT '{}',
    algo_version TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    input_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (oracle_id, scope, commander_oracle_id, bracket,
                 universe_id, algo_version)
);
CREATE INDEX IF NOT EXISTS tier_assignment_scope
    ON tier_assignment(scope, commander_oracle_id, bracket, tier);
CREATE INDEX IF NOT EXISTS tier_assignment_universe
    ON tier_assignment(scope, universe_id, tier);
"""


def ensure_schema(store: Store) -> None:
    info = store.conn.execute("PRAGMA table_info(tier_assignment)").fetchall()
    cols = {r["name"] for r in info}
    pk = {r["name"] for r in info if r["pk"]}
    if cols and ("universe_id" not in cols or "algo_version" not in pk):
        # tier_assignment is a pure cache (design §6): rows are a
        # derived function of the snapshots and are rebuilt wholesale
        # by the next compute-tiers run, so a shape change drops and
        # recreates the table instead of migrating derived rows.
        # 1.2.0: algo_version joins the primary key so the rows of
        # several model versions can coexist (the read API serves the
        # version the owner selected in the settings).
        store.conn.execute("DROP TABLE tier_assignment")
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


# --- tierlist/1.2.0 tournament mappings (docs/TIERLIST_1_2_DESIGN.md §3)
# Every mapping is floored at TOURNAMENT_FLOOR: presence in a selective
# tournament corpus is a positive signal, never a negative one.

def edhtop16_play_rate_subscore(play_rate: float) -> float:
    """EDHTop16 global staples-list play rate (share of last year's
    cEDH entries). Bands follow the measured distribution over the
    collection (median 0.019, p90 0.355); mere listing scores the
    floor because the published list is selective (1,333 of 35,769
    store cards)."""
    return _band(play_rate, [(0.30, 0.95), (0.20, 0.90), (0.10, 0.80),
                             (0.05, 0.70), (0.02, 0.60)], TOURNAMENT_FLOOR)


def edhtop16_commander_play_rate_subscore(play_rate: float) -> float:
    """EDHTop16 per-commander play rate (share of THAT commander's
    entries), band shape of the cohort-inclusion mapping, floored."""
    return _band(play_rate, [(0.60, 0.95), (0.40, 0.85), (0.25, 0.70),
                             (0.12, 0.60)], TOURNAMENT_FLOOR)


def topdeck_adjusted_conversion(conversion: float, n: int,
                                baseline: float) -> float:
    """TopDeck conversion shrunk towards the cohort baseline with
    K = TOPDECK_SHRINKAGE_K (the Playgroup shrinkage constant): at
    n = K the measured value is half earned, below that the cohort
    mean dominates."""
    return (conversion * n + baseline * TOPDECK_SHRINKAGE_K) / \
        (n + TOPDECK_SHRINKAGE_K)


def topdeck_conversion_subscore(ratio: float) -> float:
    """Mapping on adjusted/baseline. Measured shrunk ratios over the
    collection: median 0.90, p90 1.07, max 1.28 — the top bands are
    rare by construction. Below baseline the floor applies (presence
    in >= 10 cut-known tournament decks is the signal, not a demerit)."""
    return _band(ratio, [(1.30, 0.95), (1.20, 0.85), (1.10, 0.75),
                         (1.05, 0.65), (1.00, 0.58)], TOURNAMENT_FLOOR)


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
# Counted tiers (CPL mechanics — docs/TIERLIST_CPL_ADAPTATION.md §4.3)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class TierParams:
    """Parameters of the PURE counted tier function (CPL ``tiers.py``,
    values adopted as code defaults per spec D7: thresholds are code +
    version here, not stored owner parameters)."""

    min_universe: int = 30
    # Descending (tier, minimum inclusion share) cuts; first hit wins.
    cuts: tuple = (("S", 0.50), ("A", 0.35), ("B", 0.20), ("C", 0.10))
    fallback_tier: str = "D"

    def to_dict(self) -> dict:
        return {"min_universe": self.min_universe,
                "cuts": [[tier, cut] for tier, cut in self.cuts],
                "fallback_tier": self.fallback_tier}


DEFAULT_TIER_PARAMS = TierParams()


def counted_tier(share: float | None, denominator: int,
                 params: TierParams = DEFAULT_TIER_PARAMS
                 ) -> tuple[str, str]:
    """The counted tier of one inclusion share + CPL reason code:
    UNIVERSE_TOO_SMALL / DENOMINATOR_MISSING / SHARE_CUT /
    BELOW_LOWEST_CUT. A card absent from a LIST universe has share 0
    (a counted value), never a missing one."""
    if denominator < params.min_universe:
        return "U", "UNIVERSE_TOO_SMALL"
    if share is None:
        return "U", "DENOMINATOR_MISSING"
    for tier, cut in params.cuts:
        if share >= cut:
            return tier, "SHARE_CUT"
    return params.fallback_tier, "BELOW_LOWEST_CUT"


# --------------------------------------------------------------------------
# Combination rule (design §4)
# --------------------------------------------------------------------------

def combine(signals: list[dict]) -> dict:
    """Weighted score + evidence over the AVAILABLE signals, then the
    tier bands and gates/caps. ``signals`` entries carry ``signal``,
    ``weight`` and ``subscore`` (None when unavailable)."""
    available = [s for s in signals if s.get("subscore") is not None]
    weight_sum = sum(s["weight"] for s in available)
    # 1.2.0 adds optional weights on top of the core sum of 1.00, so
    # the raw sum can reach 1.20; evidence stays a [0, 1] measure.
    # Under 1.1.0 the sum never exceeds 1.00 — the clamp is a no-op
    # there and 1.1.0 results stay byte-identical.
    evidence = round(min(1.0, weight_sum), 10)
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
        # A4: combo integration detail of THIS card's combos (distinct
        # partners + distinct result types), from the stored combo
        # rows of the same snapshot — evidence detail, not new inputs.
        partners: set = set()
        produces: set = set()
        for crow in store.conn.execute(
                "SELECT card_oracle_ids_json, produces_json "
                "FROM spellbook_combo WHERE snapshot_id=?",
                (row["snapshot_id"],)):
            try:
                ids = json.loads(crow["card_oracle_ids_json"] or "[]")
            except json.JSONDecodeError:
                continue
            if oracle_id not in ids:
                continue
            partners.update(i for i in ids if i != oracle_id)
            try:
                prod = json.loads(crow["produces_json"] or "[]")
            except json.JSONDecodeError:
                prod = []
            if isinstance(prod, list):
                for item in prod:
                    produces.add(item if isinstance(item, str)
                                 else json.dumps(item, sort_keys=True))
        facts = (_snap_base(row), total, row["captured_count"] or 0,
                 row["status"], row["coverage_status"],
                 len(partners), len(produces))
    if cache is not None:
        cache[oracle_id] = facts
    return facts


def _spellbook_signal(store: Store, oracle_id: str, weight: float,
                      scope: str, cache: dict | None = None) -> dict:
    facts = _spellbook_facts(store, oracle_id, cache)
    if facts is None:
        return _unavailable("spellbook_combo_density", weight,
                            "not fetched (sync-spellbook)")
    snap, total, captured, status, coverage_status, n_partners, \
        n_produces = facts
    extra = {}
    if scope == "context":
        extra["context_free"] = True
    detail = {"combo_partners": n_partners, "produces_types": n_produces}
    if isinstance(total, int):
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": total, "combos_captured": captured,
             "total_is_exact": True, **detail},
            combo_subscore(total), snap, **extra)
    if captured > 0:
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": None, "combos_captured": captured,
             "total_is_exact": False, **detail,
             "note": "captured count is a lower bound (search route "
                     "publishes no grand total)"},
            combo_subscore(captured), snap, **extra)
    if status == "NOT_FOUND" and coverage_status == "TOTAL_KNOWN":
        return _available(
            "spellbook_combo_density", weight,
            {"combos_total": 0, "combos_captured": 0,
             "total_is_exact": True, **detail},
            combo_subscore(0), snap, **extra)
    return _unavailable("spellbook_combo_density", weight,
                        "combo total unknown (no card page, no captured "
                        "combos)", snap)


_TOURNAMENT_SEMANTICS = (
    "tournament cohort (cEDH) — additional signal of tierlist/1.2.0, "
    "floored at the neutral value 0.50; absence is UNAVAILABLE, "
    "never a penalty")


def _tournament_cache(store: Store, cache: dict | None) -> dict:
    """Per-run cache of the tournament layers' snapshots + the
    TopDeck cohort baseline (built once per compute run, like the
    Spellbook facts cache)."""
    if cache is None:
        cache = {}
    if "ready" in cache:
        return cache
    from . import edhtop16 as _e16
    cache["edhtop16_snap"] = latest_snapshot(store, _e16.SOURCE_NAME,
                                             _e16.KIND)
    cache["edhtop16_cmd_snaps"] = _e16._latest_commander_snapshots(store)
    # Commander-level entries per snapshot (the gate denominator),
    # for the gate-vs-absence reason distinction in the commander
    # signal: a card with no row of its own can only be told apart
    # from a below-gate commander via this aggregate.
    cache["edhtop16_cmd_entries"] = {
        r["snapshot_id"]: r["entries_n"] for r in store.conn.execute(
            "SELECT snapshot_id, entries_n FROM "
            "edhtop16_commander_stat")}
    cache["topdeck_snap"] = latest_snapshot(store, "topdeck",
                                            "topdeck_tournaments")
    cache["topdeck_baseline"] = None
    snap = cache["topdeck_snap"]
    if snap is not None:
        row = store.conn.execute(
            "SELECT AVG(CAST(top_cut_reached AS REAL)) mean_conv, "
            "COUNT(*) decks FROM topdeck_result WHERE snapshot_id=? "
            "AND top_cut_reached IS NOT NULL",
            (snap["snapshot_id"],)).fetchone()
        if row is not None and row["decks"] and row["mean_conv"]:
            cache["topdeck_baseline"] = {
                "baseline": float(row["mean_conv"]),
                "decks_with_known_cut": int(row["decks"])}
    cache["ready"] = True
    return cache


def _edhtop16_global_signal(store: Store, oracle_id: str, weight: float,
                            cache: dict) -> dict:
    """1.2.0 global: EDHTop16 staples-list play rate. A card that is
    not on the published list is UNAVAILABLE — the source publishes
    no rate for it, which is not a measured 0."""
    snap = cache["edhtop16_snap"]
    if snap is None:
        return _unavailable("edhtop16_play_rate", weight,
                            "not fetched (sync-edhtop16)")
    base = _snap_base(snap)
    row = store.conn.execute(
        "SELECT play_rate_last_year FROM edhtop16_card_stat "
        "WHERE snapshot_id=? AND card_oracle_id=?",
        (snap["snapshot_id"], oracle_id)).fetchone()
    if row is None or row["play_rate_last_year"] is None:
        return _unavailable(
            "edhtop16_play_rate", weight,
            "not on the published EDHTop16 staples list (absence "
            "carries no rate and is never scored as 0)", base)
    rate = float(row["play_rate_last_year"])
    return _available(
        "edhtop16_play_rate", weight,
        {"play_rate_last_year": rate, "window": "last_year",
         "note": "share of cEDH tournament entries running the card "
                 "(EDHTop16 staples list); the source does not "
                 "publish the exact denominator"},
        edhtop16_play_rate_subscore(rate), base,
        semantics=_TOURNAMENT_SEMANTICS)


def _topdeck_conversion_signal(store: Store, oracle_id: str,
                               weight: float, cache: dict) -> dict:
    """1.2.0 global: TopDeck conversion, computed locally from the
    stored tournament lists, shrunk towards the snapshot's cohort
    baseline (over decks). The source itself gates the rate at
    decks_in_cut >= 10; below that the counts are shown and the
    signal is UNAVAILABLE."""
    snap = cache["topdeck_snap"]
    if snap is None:
        return _unavailable("topdeck_conversion", weight,
                            "not fetched (sync-topdeck)")
    base = _snap_base(snap)
    baseline = cache["topdeck_baseline"]
    if baseline is None:
        return _unavailable(
            "topdeck_conversion", weight,
            "snapshot carries no decks with a known top-cut result, "
            "so no cohort baseline exists", base)
    row = store.conn.execute(
        "SELECT decks_with, decks_in_cut, top_cut_decks, "
        "conversion_rate FROM topdeck_card_stat WHERE snapshot_id=? "
        "AND card_oracle_id=?", (snap["snapshot_id"], oracle_id)).fetchone()
    if row is None:
        return _unavailable(
            "topdeck_conversion", weight,
            "card appears in no stored TopDeck tournament deck "
            "(absence is never scored as 0)", base)
    if row["conversion_rate"] is None:
        return _unavailable(
            "topdeck_conversion", weight,
            f"insufficient data: decks_in_cut={row['decks_in_cut']} "
            f"< 10 (decks_with={row['decks_with']})", base)
    n = int(row["decks_in_cut"])
    adjusted = topdeck_adjusted_conversion(
        float(row["conversion_rate"]), n, baseline["baseline"])
    ratio = adjusted / baseline["baseline"]
    return _available(
        "topdeck_conversion", weight,
        {"conversion_rate": float(row["conversion_rate"]),
         "adjusted_conversion": adjusted, "ratio_to_baseline": ratio,
         "cohort_baseline": baseline["baseline"],
         "baseline_decks": baseline["decks_with_known_cut"],
         "n": n, "decks_with": int(row["decks_with"]),
         "decks_in_cut": n, "top_cut_decks": int(row["top_cut_decks"]),
         "shrinkage_k": TOPDECK_SHRINKAGE_K,
         "attribution": "Data provided by TopDeck.gg"},
        topdeck_conversion_subscore(ratio), base,
        semantics=_TOURNAMENT_SEMANTICS)


def _edhtop16_commander_signal(store: Store, oracle_id: str,
                               commander_oracle_id: str, weight: float,
                               cache: dict) -> dict:
    """1.2.0 context: EDHTop16 play rate within THIS commander's
    tournament entries (cohorts are never pooled). Gated at
    entries_n >= EDHTOP16_COMMANDER_MIN_ENTRIES — below that the
    published rates are quantised noise (measured: median 0.5 at
    entries_n <= 17). A NOT_FOUND commander snapshot is a measured
    source fact and is reported as the reason. For a card with no
    usable row the reason distinguishes the two causes (PR17-F3):
    the card is absent from the commander's published list, or the
    commander himself is below the entries gate — then the signal
    is unavailable for all his cards and the absence wording would
    mask the real cause. Only the reason text differs; availability
    and scores are identical either way."""
    snaps = cache["edhtop16_cmd_snaps"]
    snap = snaps.get(commander_oracle_id)
    if snap is None:
        return _unavailable(
            "edhtop16_commander_play_rate", weight,
            "commander not fetched (sync-edhtop16-commanders)")
    base = _snap_base(snap)
    if snap["status"] == "NOT_FOUND":
        return _unavailable(
            "edhtop16_commander_play_rate", weight,
            "commander has no EDHTop16 tournament data (NOT_FOUND — "
            "a measured source fact, not an error)", base)
    if snap["status"] not in ("AVAILABLE", "PARTIAL"):
        return _unavailable(
            "edhtop16_commander_play_rate", weight,
            f"commander snapshot status {snap['status']}", base)
    row = store.conn.execute(
        "SELECT play_rate, entries_n, window FROM "
        "edhtop16_commander_card_stat WHERE snapshot_id=? "
        "AND card_oracle_id=?", (snap["snapshot_id"], oracle_id)).fetchone()
    if row is not None and row["play_rate"] is not None:
        entries = row["entries_n"]
        if entries is None or int(entries) < EDHTOP16_COMMANDER_MIN_ENTRIES:
            return _unavailable(
                "edhtop16_commander_play_rate", weight,
                f"insufficient data: entries_n={entries} "
                f"< {EDHTOP16_COMMANDER_MIN_ENTRIES}", base)
        rate = float(row["play_rate"])
        return _available(
            "edhtop16_commander_play_rate", weight,
            {"play_rate": rate, "entries_n": int(entries),
             "window": row["window"],
             "note": "share of this commander's cEDH tournament entries "
                     "running the card (EDHTop16 commander staples)"},
            edhtop16_commander_play_rate_subscore(rate), base,
            semantics=_TOURNAMENT_SEMANTICS)
    # No usable row for this card. When the commander-level entries
    # count (edhtop16_commander_stat, cached per run) is known and
    # below the gate, the gate is the cause — it covers every card,
    # listed or not (a zero-entries commander has no card rows at
    # all: the importer withholds them). When the count is unknown
    # (the stats query failed — a PARTIAL snapshot, whose card rows
    # are likewise withheld) the gate cannot be asserted and the
    # absence wording stays.
    cmd_entries = (cache.get("edhtop16_cmd_entries") or {}).get(
        snap["snapshot_id"])
    if cmd_entries is not None and \
            int(cmd_entries) < EDHTOP16_COMMANDER_MIN_ENTRIES:
        return _unavailable(
            "edhtop16_commander_play_rate", weight,
            f"insufficient data: entries_n={int(cmd_entries)} "
            f"< {EDHTOP16_COMMANDER_MIN_ENTRIES} — commander-level "
            "gate: the commander himself is below the entries gate, "
            "so this signal is unavailable for all his cards (not a "
            "listing absence)", base)
    return _unavailable(
        "edhtop16_commander_play_rate", weight,
        "not in this commander's published EDHTop16 staples "
        "list (absence is never scored as 0)", base)


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


# --------------------------------------------------------------------------
# Decklist universes (LIST type) — counted inclusion over harvested decks
# --------------------------------------------------------------------------
# Selection, dedupe and counting mirror inclusion.py exactly (the
# figures a tier cites are the figures the inclusion engine reports):
# AVAILABLE decks inside the settings selection (platforms, brackets,
# age), identical content under several deck ids counts ONCE (lowest
# deck id wins), commander entries never count towards card figures,
# rows with quantity <= 0 never count. CPL's stored ``duplicate_of``
# is our computed content fingerprint — same rule, derived instead of
# stored (spec §3 D1/D9, §6 K3: we count by oracle_id, not by name).
# A deck without a countable card (a quantity > 0 row that is not the
# commander entry) is not part of the universe at all — commander-only
# lists, zero-quantity rows only or no stored rows could never
# contribute a hit and must not inflate the denominator (upstream
# #1207 rule, inclusion._canonical_decks; integration-wave-2 union).

def _dl_definition(cfg: dict, commander_oracle_id: str | None = None,
                   bracket_level: int | None = None) -> dict:
    definition = {
        "source": "decklists",
        "brackets": list(cfg["inclusion.brackets"]),
        "platforms": list(cfg["inclusion.platforms"]),
        "max_age_days": cfg["inclusion.max_age_days"],
        "date_from": cfg["inclusion.date_from"],
        "date_to": cfg["inclusion.date_to"],
        "period_basis": ("source_updated_at (Archidekt updatedAt)"
                         if (cfg["inclusion.date_from"]
                             or cfg["inclusion.date_to"]) else None),
    }
    if commander_oracle_id is not None:
        definition["commander_oracle_id"] = commander_oracle_id
    if bracket_level is not None:
        definition["brackets"] = [bracket_level]
    return definition


def _universe_snapshot_id(definition: dict,
                          uid_fingerprints: list[tuple[str, str]]) -> str:
    """CPL snapshot mechanics (spec D3): hash over the definition, the
    selected canonical deck ids and each deck's content fingerprint —
    two equal ids mean the same definition over the same deck
    contents, so every counted figure can cite its exact universe."""
    digest = hashlib.sha256()
    digest.update(json.dumps(definition, sort_keys=True).encode())
    for uid, fp in uid_fingerprints:
        digest.update(f"\n{uid}:{fp}".encode())
    return f"universe:{digest.hexdigest()[:16]}:{len(uid_fingerprints)}"


def _load_decklist_selection(store: Store, cfg: dict) -> tuple[list[dict], int]:
    """All AVAILABLE harvested decks of the settings selection, with
    their card rows (the same selection inclusion._decklist_counts
    makes, period rule included). Returns (decks,
    excluded_no_timestamp): while a period is set, decks without a
    SOURCE timestamp are excluded and counted — fetched_at is never
    passed off as a deck date."""
    platforms = list(cfg["inclusion.platforms"])
    brackets = list(cfg["inclusion.brackets"])
    if not platforms or not brackets:
        return [], 0
    cutoff = _age_filter(cfg)
    # Bracket-less decks (browser harvests, bracket_level NULL) join
    # only via their selected platform, as its bracket-less cohort —
    # the same rule inclusion._decklist_counts applies; they never
    # enter a bracket cohort (and _canonical_universe keeps them out
    # of denominator_by_bracket).
    q = ("SELECT deck_uid, platform, bracket_level, commander_oracle_id, "
         "source_updated_at FROM decklist_deck WHERE status='AVAILABLE' "
         "AND platform IN (%s) AND (bracket_level IN (%s) "
         "OR bracket_level IS NULL)" % (
             ",".join("?" for _ in platforms),
             ",".join("?" for _ in brackets)))
    args: list = [*platforms, *brackets]
    if cutoff:
        q += " AND fetched_at>=?"
        args.append(cutoff)
    date_from, date_to = cfg["inclusion.date_from"], cfg["inclusion.date_to"]
    decks: dict[str, dict] = {}
    excluded_no_timestamp = 0
    for row in store.conn.execute(q, args):
        if date_from or date_to:
            ts = row["source_updated_at"]
            if not ts:
                excluded_no_timestamp += 1
                continue
            day = str(ts)[:10]
            if (date_from and day < date_from) or (date_to and day > date_to):
                continue
        decks[row["deck_uid"]] = {
            "uid": row["deck_uid"], "platform": row["platform"],
            "bracket_level": row["bracket_level"],
            "commander_oracle_id": row["commander_oracle_id"], "rows": []}
    if not decks:
        return [], excluded_no_timestamp
    # TEMP-table join instead of one bound variable per deck (the
    # upstream #1207 mechanism inclusion uses; a full selection is
    # ~9k decks, above older SQLite variable caps).
    with _universe_table(store.conn, list(decks)) as table:
        for row in store.conn.execute(
                f"SELECT c.deck_uid, c.entry_key, c.quantity, "
                f"c.is_commander, c.oracle_id FROM decklist_card c "
                f"JOIN {table} u ON u.deck_uid = c.deck_uid"):
            decks[row["deck_uid"]]["rows"].append(
                (row["entry_key"], row["quantity"], row["is_commander"],
                 row["oracle_id"]))
    return list(decks.values()), excluded_no_timestamp


def _canonical_universe(decks: list[dict]) -> dict:
    """Canonical decks + per-card hit counts of ONE universe (the
    decks of one selection). Content-identical decks collapse to the
    lowest deck uid; hits count distinct canonical decks."""
    first: dict[str, dict] = {}
    excluded_no_countable = 0
    for deck in sorted(decks, key=lambda d: d["uid"]):
        if not any(qty > 0 and not is_cmd
                   for _, qty, is_cmd, _ in deck["rows"]):
            excluded_no_countable += 1
            continue
        fp = _content_fingerprint(
            [(key, qty, is_cmd) for key, qty, is_cmd, _ in deck["rows"]])
        deck["_fp"] = fp
        first.setdefault(fp, deck)
    canonical = sorted(first.values(), key=lambda d: d["uid"])
    counts: dict[str, int] = {}
    for deck in canonical:
        for oid in {oid for _, qty, is_cmd, oid in deck["rows"]
                    if not is_cmd and oid is not None and qty > 0}:
            counts[oid] = counts.get(oid, 0) + 1
    by_platform: dict[str, int] = {}
    by_bracket: dict[str, int] = {}
    for deck in canonical:
        by_platform[deck["platform"]] = \
            by_platform.get(deck["platform"], 0) + 1
        if deck["bracket_level"] is not None:
            key = str(deck["bracket_level"])
            by_bracket[key] = by_bracket.get(key, 0) + 1
    return {
        "denominator": len(canonical), "counts": counts,
        "excluded_no_countable": excluded_no_countable,
        "uid_fingerprints": sorted((d["uid"], d["_fp"]) for d in canonical),
        "composition": {
            "denominator_by_platform": dict(sorted(by_platform.items())),
            "denominator_by_bracket": dict(sorted(by_bracket.items())),
        },
    }


def _decklist_data(store: Store, cfg: dict) -> dict | None:
    """Every Verbreitung universe of the current settings selection,
    built once per compute run: pooled (``all``) + one per commander
    + one per commander x bracket cohort. None when the selection is
    empty. The excluded-no-timestamp count of the period rule is
    carried into every profile definition."""
    decks, excluded_no_timestamp = _load_decklist_selection(store, cfg)
    if not decks:
        return None

    def build(subset: list[dict], definition: dict) -> dict:
        definition["excluded_no_timestamp"] = excluded_no_timestamp
        uni = _canonical_universe(subset)
        definition["excluded_no_countable"] = uni["excluded_no_countable"]
        uni["definition"] = definition
        uni["snapshot_id"] = _universe_snapshot_id(
            definition, uni["uid_fingerprints"])
        return uni

    data: dict = {"all": build(decks, _dl_definition(cfg)),
                  "by_commander": {}, "by_cohort": {}}
    by_commander: dict[str, list[dict]] = {}
    by_cohort: dict[tuple[str, int], list[dict]] = {}
    for deck in decks:
        coid = deck["commander_oracle_id"]
        if not coid:
            continue
        by_commander.setdefault(coid, []).append(deck)
        if deck["bracket_level"] is not None:
            by_cohort.setdefault((coid, deck["bracket_level"]),
                                 []).append(deck)
    for coid, subset in by_commander.items():
        uni = build(subset, _dl_definition(cfg, commander_oracle_id=coid))
        uni["commander_oracle_id"] = coid
        data["by_commander"][coid] = uni
    for (coid, level), subset in sorted(by_cohort.items()):
        uni = build(subset, _dl_definition(
            cfg, commander_oracle_id=coid, bracket_level=level))
        uni["commander_oracle_id"] = coid
        uni["bracket_level"] = level
        data["by_cohort"][(coid, level)] = uni
    return data


def _universe_block(uni: dict, profile: str) -> dict:
    return {"profile": profile, "universe_type": "LIST",
            "snapshot_id": uni["snapshot_id"],
            "universe_size": uni["denominator"],
            "commander_oracle_id": uni.get("commander_oracle_id"),
            "bracket_level": uni.get("bracket_level"),
            "definition": uni["definition"], **uni["composition"]}


def global_signals(store: Store, oracle_id: str,
                   spellbook_cache: dict | None = None,
                   model: ModelConfig | None = None,
                   tournament_cache: dict | None = None) -> list[dict]:
    model = model or ModelConfig()
    w = GLOBAL_WEIGHTS_1_2 if model.is_1_2 else GLOBAL_WEIGHTS
    signals = [
        _edhrec_global_signal(store, oracle_id, w["edhrec_global_inclusion"]),
        _playgroup_lift_signal(store, oracle_id, w["playgroup_win_lift"]),
        _spellbook_signal(store, oracle_id, w["spellbook_combo_density"],
                          "global", spellbook_cache),
    ]
    if model.is_1_2:
        cache = _tournament_cache(store, tournament_cache)
        if model.edhtop16_global:
            signals.append(_edhtop16_global_signal(
                store, oracle_id, w["edhtop16_play_rate"], cache))
        if model.topdeck_conversion:
            signals.append(_topdeck_conversion_signal(
                store, oracle_id, w["topdeck_conversion"], cache))
    return signals


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


def _top_commander_evidence(store: Store,
                              name_map: dict[str, str]) -> dict:
    """A5 (spec §4.3): {(card_oid, commander_oid): entry} from the
    "Top Commanders" cardviews stored in the parsed payload of every
    card's latest AVAILABLE EDHREC card page. An entry measures the
    share of that commander's decks running the card — the same
    construct as cohort inclusion, read from the card page instead of
    the commander page. Commanders resolve by card name or EDHREC
    slug; unresolvable entries are dropped, never guessed."""
    slug_map: dict[str, str] = {}
    for r in store.conn.execute(
            "SELECT commander_oracle_id, slug FROM external_snapshot "
            "WHERE kind='edhrec_stats' AND slug IS NOT NULL "
            "AND commander_oracle_id IS NOT NULL"):
        slug_map.setdefault(r["slug"], r["commander_oracle_id"])
    latest: dict[str, object] = {}
    for row in store.conn.execute(
            "SELECT * FROM external_snapshot WHERE kind='edhrec_card' "
            "AND status='AVAILABLE' AND oracle_id IS NOT NULL "
            "ORDER BY fetched_at DESC"):
        latest.setdefault(row["oracle_id"], row)
    out: dict = {}
    for oid, row in latest.items():
        if not row["payload_json"]:
            continue
        try:
            payload = json.loads(row["payload_json"]) or {}
        except json.JSONDecodeError:
            continue
        for entry in payload.get("top_commanders") or []:
            coid = name_map.get(entry.get("name") or "") \
                or slug_map.get(entry.get("slug") or "")
            num, pot = entry.get("num_decks"), entry.get("potential_decks")
            if coid is None or not isinstance(num, int) \
                    or not isinstance(pot, int) or not pot:
                continue
            out[(oid, coid)] = {
                "inclusion": num / pot, "num_decks": num,
                "potential_decks": pot, "snap": _snap_base(row)}
    return out


def context_signals(store: Store, oracle_id: str, commander_oracle_id: str,
                    bracket: str, cohort: dict[str, dict],
                    staples: dict[str, dict],
                    snaps: dict[str, object | None],
                    spellbook_cache: dict | None = None,
                    top_commander: dict | None = None,
                    model: ModelConfig | None = None,
                    tournament_cache: dict | None = None) -> list[dict]:
    model = model or ModelConfig()
    w = CONTEXT_WEIGHTS_1_2 if model.is_1_2 else CONTEXT_WEIGHTS
    signals: list[dict] = []
    stat = cohort.get(oracle_id)
    stats_snap = snaps.get("stats")
    stats_base = _snap_base(stats_snap) if stats_snap is not None else None
    if stat is not None and stat["inclusion"] is not None:
        signals.append(_available(
            "edhrec_cohort_inclusion", w["edhrec_cohort_inclusion"],
            {"inclusion": stat["inclusion"], "num_decks": stat["num_decks"],
             "potential_decks": stat["potential_decks"], "bracket": bracket,
             "measurement": "commander_page_stats",
             "bracket_specific": True},
            cohort_inclusion_subscore(stat["inclusion"]), stats_base))
    elif top_commander is not None:
        # A5 fallback: the commander page carries no row for this
        # card, but the card page's Top-Commanders entry measures the
        # same construct for this commander (bracket-agnostic, like
        # the Playgroup staple lift). Provenance is the card page.
        signals.append(_available(
            "edhrec_cohort_inclusion", w["edhrec_cohort_inclusion"],
            {"inclusion": top_commander["inclusion"],
             "num_decks": top_commander["num_decks"],
             "potential_decks": top_commander["potential_decks"],
             "bracket": bracket,
             "measurement": "card_page_top_commanders",
             "bracket_specific": False},
            cohort_inclusion_subscore(top_commander["inclusion"]),
            top_commander["snap"]))
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
    if model.is_1_2 and model.edhtop16_commander:
        signals.append(_edhtop16_commander_signal(
            store, oracle_id, commander_oracle_id,
            w["edhtop16_commander_play_rate"],
            _tournament_cache(store, tournament_cache)))
    return signals


# --------------------------------------------------------------------------
# Computation + storage
# --------------------------------------------------------------------------

def _u_reason_combined(tier: str, signals: list[dict]) -> str | None:
    """The one reason code of a combined-scope U row (spec §4.4; CPL's
    code list has no evidence gate, so these two codes extend it):
    NO_OBSERVATION when no signal was available at all,
    INSUFFICIENT_EVIDENCE when signals exist but their combined
    evidence stays below the U gate."""
    if tier != "U":
        return None
    if any(s.get("subscore") is not None for s in signals):
        return "INSUFFICIENT_EVIDENCE"
    return "NO_OBSERVATION"


def _payload(scope: str, signals: list[dict], markers: dict,
             commander_oracle_id: str = "", bracket: str = "",
             u_reason: str | None = None,
             model_version: str = MODEL_1_1_0) -> dict:
    payload: dict = {
        "scope": scope,
        "field": "Evidenz-Tier (Stärke-Schätzung)",
        "algo_version": model_version,
        # The combined scopes weight several signals into one score —
        # a model, and labelled as one (CPL design rule, spec D5).
        "data_class": "HEURISTIC_MODEL",
        "u_reason": u_reason,
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
               signals: list[dict], markers: dict, computed_at: str,
               model_version: str = MODEL_1_1_0) -> dict:
    result = combine(signals)
    payload = _payload(scope, signals, markers, commander_oracle_id, bracket,
                       u_reason=_u_reason_combined(result["tier"], signals),
                       model_version=model_version)
    snap_ids = sorted({s["snapshot_id"] for s in signals
                       if s.get("snapshot_id")})
    snap_ids += sorted({s["universe"]["snapshot_id"] for s in signals
                        if s.get("universe")})
    store.conn.execute(
        "INSERT OR REPLACE INTO tier_assignment(oracle_id,scope,"
        "commander_oracle_id,bracket,universe_id,tier,score,evidence,"
        "signals_json,algo_version,computed_at,input_snapshot_ids_json) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oracle_id, scope, commander_oracle_id, bracket, "", result["tier"],
         result["score"], result["evidence"],
         json.dumps(payload, ensure_ascii=False, sort_keys=True),
         model_version, computed_at, json.dumps(sorted(set(snap_ids)))))
    return result


def _store_universe_row(store: Store, oracle_id: str, uni: dict,
                        *, profile: str, commander_oracle_id: str,
                        params: TierParams, computed_at: str,
                        bracket: str = "",
                        model_version: str = MODEL_1_1_0) -> dict:
    """One PURE counted tier row of the universe scope (CPL card_tier
    breakdown shape): the counted signal alone decides, no weights,
    no markers. score = counted share, evidence = 1.0 for a counted
    value and 0.0 for a U row."""
    den = uni["denominator"]
    hits = uni["counts"].get(oracle_id, 0)
    share = hits / den if den else None
    tier, reason = counted_tier(share, den, params)
    counted = tier != "U"
    signal = {"signal": "decklist_inclusion", "weight": 1.0,
              "available": counted,
              "subscore": share if counted else None,
              "value": {"hits": hits, "denominator": den, "share": share},
              "reason": None if counted else reason,
              "source_label": "harvested real deck lists (LIST universe)",
              "parser_version": DECKLIST_PARSER_VERSION,
              "data_class": "DERIVED_DESCRIPTIVE",
              "universe": _universe_block(uni, profile)}
    payload = {
        "scope": "universe",
        "field": "Verbreitung (gezählt)",
        "algo_version": model_version,
        "data_class": "DERIVED_DESCRIPTIVE",
        "u_reason": None if counted else reason,
        "tier_reason": reason,
        "params": params.to_dict(),
        "universe": _universe_block(uni, profile),
        "signals": [signal],
        "missing_signals": [] if counted else ["decklist_inclusion"],
        "markers": {},
    }
    store.conn.execute(
        "INSERT OR REPLACE INTO tier_assignment(oracle_id,scope,"
        "commander_oracle_id,bracket,universe_id,tier,score,evidence,"
        "signals_json,algo_version,computed_at,input_snapshot_ids_json) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oracle_id, "universe", commander_oracle_id, bracket,
         uni["snapshot_id"], tier, share, 1.0 if counted else 0.0,
         json.dumps(payload, ensure_ascii=False, sort_keys=True),
         model_version, computed_at, json.dumps([uni["snapshot_id"]])))
    return {"tier": tier, "score": share,
            "evidence": 1.0 if counted else 0.0}


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
                  bracket: str | None = None,
                  universes: bool = True,
                  model: str | None = None) -> dict:
    """(Re)compute tier rows. Default: the Evidenz-Tier (global scope
    for every card that is in a collection or carries a global signal,
    plus every fetched commander x bracket context) and — with
    ``universes`` — the Verbreitung (gezählt) of every deck universe
    (profile ``all`` + one per commander with harvested decks + one
    per commander x bracket cohort).
    Deterministic over unchanged snapshots (only ``computed_at``
    differs between runs).

    ``model`` selects the strength-model version (``tierlist/1.1.0``
    or ``tierlist/1.2.0``); the default is the ``tierlist.model_version``
    setting. A run replaces only the rows of ITS model version, so
    versions coexist and the read API can serve the selected one.
    The Verbreitung is a pure count, identical under every model; its
    rows carry the producing run's version label."""
    ensure_schema(store)
    if bracket is not None and bracket not in BRACKETS:
        level = {2: "core", 3: "upgraded", 4: "optimized"}
        try:
            bracket = level[int(bracket)]  # type: ignore[arg-type]
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"unknown bracket {bracket!r}") from None
    computed_at = utcnow()
    cfg = settings_mod.resolve(store)
    model_cfg = _model_from_cfg(cfg, model)
    summary: dict = {"algo_version": model_cfg.version,
                     "model": model_cfg.version,
                     "computed_at": computed_at}
    tournament_cache: dict = {}
    # The counted decklist universes of the current settings selection
    # (Verbreitung only — never an input of the Evidenz-Tier).
    dl = _decklist_data(store, cfg)
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
                "AND algo_version=? "
                "AND oracle_id IN (SELECT DISTINCT oracle_id FROM "
                "physical_lot WHERE collection_id=?)",
                (model_cfg.version, collection_id))
        else:
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='global' "
                "AND algo_version=?", (model_cfg.version,))
        rows: list[dict] = []
        u_signals: list[list[dict]] = []
        _preload_roles(universe)
        for oid in sorted(universe):
            signals = global_signals(store, oid, spellbook_cache,
                                     model=model_cfg,
                                     tournament_cache=tournament_cache)
            result = _store_row(store, oid, "global", "", "", signals,
                                _markers(store, oid, markers_cache,
                                         roles_cache),
                                computed_at,
                                model_version=model_cfg.version)
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
    # A5 evidence, built once per run: (card, commander) -> Top-
    # Commanders entry of the card's EDHREC card page (fallback for
    # cohort inclusion + context rows for cards with only that
    # evidence).
    if name_map is None:
        name_map = _name_to_oracle(store)
    top_map = _top_commander_evidence(store, name_map)
    top_by_commander: dict[str, set] = {}
    for (card_oid, cmd_oid) in top_map:
        top_by_commander.setdefault(cmd_oid, set()).add(card_oid)
    ctx_rows: list[dict] = []
    ctx_u: list[list[dict]] = []
    ctx_a5 = 0
    contexts_with_cards = 0
    contexts_total = 0
    for coid in sorted(commanders):
        page_row, staples = _staples(store, coid)
        for br in brackets:
            stats_row, cohort = _cohort_stats(store, coid, br, name_map)
            if stats_row is None and page_row is None:
                continue
            if stats_row is not None and stats_row["status"] != "AVAILABLE" \
                    and page_row is None:
                continue
            contexts_total += 1
            cards = set(cohort) | set(staples) \
                | top_by_commander.get(coid, set())
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='context' "
                "AND commander_oracle_id=? AND bracket=? "
                "AND algo_version=?", (coid, br, model_cfg.version))
            if cards:
                contexts_with_cards += 1
            snaps = {"stats": stats_row, "page": page_row}
            _preload_roles(cards)
            for oid in sorted(cards):
                signals = context_signals(
                    store, oid, coid, br, cohort, staples, snaps,
                    spellbook_cache,
                    top_commander=top_map.get((oid, coid)),
                    model=model_cfg,
                    tournament_cache=tournament_cache)
                if any(s["signal"] == "edhrec_cohort_inclusion"
                       and (s.get("value") or {}).get("measurement")
                       == "card_page_top_commanders" for s in signals):
                    ctx_a5 += 1
                result = _store_row(store, oid, "context", coid, br,
                                    signals,
                                    _markers(store, oid, markers_cache,
                                             roles_cache),
                                    computed_at,
                                    model_version=model_cfg.version)
                ctx_rows.append(result)
                if result["tier"] == "U":
                    ctx_u.append(signals)
    summary["context"] = {
        "commanders": len(commanders), "brackets": brackets,
        "contexts_total": contexts_total,
        "contexts_with_rated_cards": contexts_with_cards,
        "cards": len(ctx_rows), "tiers": _tier_counts(ctx_rows),
        "u_missing_signal_counts": _u_reasons(ctx_u),
        "a5_top_commander_rows": ctx_a5,
        "a5_commanders_with_evidence": len(top_by_commander),
        "a5_pairs": len(top_map),
    }

    # ---- universe scope (pure counted tiers, spec §4.3) --------------
    if universes:
        # Universe rows are rebuilt wholesale per run scope — also when
        # the selection turned empty, so no stale profile survives.
        if commander_oracle_id is None:
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='universe' "
                "AND algo_version=?", (model_cfg.version,))
        else:
            store.conn.execute(
                "DELETE FROM tier_assignment WHERE scope='universe' "
                "AND commander_oracle_id=? AND algo_version=?",
                (commander_oracle_id, model_cfg.version))
        if dl is None:
            summary["universe"] = {
                "profiles": 0, "rows": 0, "cohort_profiles": 0,
                "tiers": {},
                "denominators": {},
                "note": "no harvested deck lists (sync-decklists)"}
        else:
            if collection_id:
                base_cards = {r["oracle_id"] for r in store.conn.execute(
                    "SELECT DISTINCT oracle_id FROM physical_lot "
                    "WHERE collection_id=?", (collection_id,))}
            else:
                base_cards = {r["oracle_id"] for r in store.conn.execute(
                    "SELECT DISTINCT oracle_id FROM physical_lot")}
            if commander_oracle_id is None:
                profiles = [("all", "", dl["all"], "")] + [
                    (f"commander:{coid}", coid, dl["by_commander"][coid],
                     "")
                    for coid in sorted(dl["by_commander"])] + [
                    (f"commander:{coid}:bracket:{level}", coid,
                     dl["by_cohort"][(coid, level)],
                     BRACKET_NAMES.get(level, ""))
                    for (coid, level) in sorted(dl["by_cohort"])]
            else:
                profiles = []
                if commander_oracle_id in dl["by_commander"]:
                    profiles.append(
                        (f"commander:{commander_oracle_id}",
                         commander_oracle_id,
                         dl["by_commander"][commander_oracle_id], ""))
                profiles += [
                    (f"commander:{commander_oracle_id}:bracket:{level}",
                     commander_oracle_id,
                     dl["by_cohort"][(commander_oracle_id, level)],
                     BRACKET_NAMES.get(level, ""))
                    for (coid, level) in sorted(dl["by_cohort"])
                    if coid == commander_oracle_id]
            run_params = TierParams(
                min_universe=int(cfg["tierlist.min_universe"]))
            u_rows: list[dict] = []
            denominators: dict[str, int] = {}
            for profile, coid_key, uni, bracket_name in profiles:
                denominators[profile] = uni["denominator"]
                for oid in sorted(set(uni["counts"]) | base_cards):
                    u_rows.append(_store_universe_row(
                        store, oid, uni, profile=profile,
                        commander_oracle_id=coid_key,
                        params=run_params,
                        computed_at=computed_at,
                        bracket=bracket_name,
                        model_version=model_cfg.version))
            summary["universe"] = {
                "profiles": len(profiles), "rows": len(u_rows),
                "cohort_profiles": sum(
                    1 for p in profiles if ":bracket:" in p[0]),
                "tiers": _tier_counts(u_rows),
                "denominators": denominators,
                "params": run_params.to_dict(),
            }
    store.conn.commit()
    return summary


# --------------------------------------------------------------------------
# Read API (used by the web layer)
# --------------------------------------------------------------------------

def _row_dict(row) -> dict:
    d = dict(row)
    # A corrupt JSON column (hand-edited DB, interrupted write) degrades
    # to the field's empty structure instead of raising JSONDecodeError
    # — an unhandled 500 on /api/tiers and /api/tiers/card/{id}. Same
    # read tolerance as list_universes/tiers_map below and
    # settings._parse_stored; the row's scalar fields are delivered
    # unchanged and the stored row itself is never rewritten here.
    try:
        d["signals"] = json.loads(d.pop("signals_json") or "{}")
    except ValueError:
        d["signals"] = {}
    try:
        d["input_snapshot_ids"] = json.loads(
            d.pop("input_snapshot_ids_json") or "[]")
    except ValueError:
        d["input_snapshot_ids"] = []
    return d


def _active_model(store: Store) -> str:
    """The model version the read API serves: the owner's
    ``tierlist.model_version`` setting (default tierlist/1.1.0)."""
    return str(settings_mod.get_setting(store, "tierlist.model_version"))


def _universe_version(store: Store, active: str,
                      universe_id: str | None = None) -> str | None:
    """Which version's universe rows to serve: the counted field is
    identical under every model, so prefer the active model's rows
    and fall back to the most recently computed ones."""
    q = ("SELECT algo_version, MAX(computed_at) latest FROM "
         "tier_assignment WHERE scope='universe'")
    args: list = []
    if universe_id is not None:
        q += " AND universe_id=?"
        args.append(universe_id)
    q += " GROUP BY algo_version"
    versions = {r["algo_version"]: r["latest"]
                for r in store.conn.execute(q, args)}
    if not versions:
        return None
    if active in versions:
        return active
    return max(versions, key=lambda v: versions[v])


def get_tier(store: Store, oracle_id: str, *,
             commander_oracle_id: str | None = None,
             bracket: str | None = None,
             universe_id: str | None = None) -> dict | None:
    ensure_schema(store)
    active = _active_model(store)
    if universe_id is not None:
        version = _universe_version(store, active, universe_id)
        if version is None:
            return None
        row = store.conn.execute(
            "SELECT * FROM tier_assignment WHERE oracle_id=? "
            "AND scope='universe' AND universe_id=? AND algo_version=?",
            (oracle_id, universe_id, version)).fetchone()
    elif commander_oracle_id is None:
        row = store.conn.execute(
            "SELECT * FROM tier_assignment WHERE oracle_id=? "
            "AND scope='global' AND algo_version=?",
            (oracle_id, active)).fetchone()
    else:
        row = store.conn.execute(
            "SELECT * FROM tier_assignment WHERE oracle_id=? "
            "AND scope='context' AND commander_oracle_id=? AND bracket=? "
            "AND algo_version=?",
            (oracle_id, commander_oracle_id, bracket or "", active)).fetchone()
    return _row_dict(row) if row is not None else None


def list_universes(store: Store) -> list[dict]:
    """The stored universe profiles of the universe scope: snapshot
    id, profile, size and definition of every computed universe.
    When several model versions hold rows of the same universe, the
    active model's row wins (the counted content is identical)."""
    ensure_schema(store)
    active = _active_model(store)
    chosen: dict[str, tuple] = {}
    for row in store.conn.execute(
            "SELECT universe_id, commander_oracle_id, signals_json, "
            "algo_version, computed_at FROM tier_assignment "
            "WHERE scope='universe'"):
        key = row["universe_id"]
        rank = (row["algo_version"] == active, row["computed_at"])
        if key not in chosen or rank > chosen[key][0]:
            chosen[key] = (rank, row)
    out: dict[str, dict] = {}
    for key, (_, row) in chosen.items():
        try:
            block = (json.loads(row["signals_json"] or "{}")
                     .get("universe") or {})
        except json.JSONDecodeError:
            block = {}
        out[key] = {
            "universe_id": row["universe_id"],
            "profile": block.get("profile"),
            "universe_type": block.get("universe_type"),
            "universe_size": block.get("universe_size"),
            "definition": block.get("definition"),
            "commander_oracle_id": row["commander_oracle_id"],
            "bracket_level": block.get("bracket_level"),
        }
    return [out[key] for key in sorted(out)]


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
            f"WHERE scope='global' AND algo_version=? "
            f"AND oracle_id IN ({marks})",
            [_active_model(store), *oracle_ids]):
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


def verbreitung_summary(store: Store) -> dict:
    """The Verbreitung (gezählt) header data for the tier page: the
    current universe definition of the settings selection, its
    canonical deck count with the platform/bracket split, the
    effective minimum size, and the stored universe profiles. Built
    live from the selection (not from stored tier rows), so the
    header is truthful even before the next compute-tiers run."""
    ensure_schema(store)
    cfg = settings_mod.resolve(store)
    params = TierParams(min_universe=int(cfg["tierlist.min_universe"]))
    dl = _decklist_data(store, cfg)
    out: dict = {
        "field": "Verbreitung (gezählt)",
        "definition": _dl_definition(cfg),
        "denominator": 0,
        "denominator_by_platform": {},
        "denominator_by_bracket": {},
        "excluded_no_timestamp": 0,
        "snapshot_id": None,
        "params": params.to_dict(),
        "profiles": list_universes(store),
    }
    if dl is not None:
        all_uni = dl["all"]
        out["definition"] = all_uni["definition"]
        out["denominator"] = all_uni["denominator"]
        out["denominator_by_platform"] = \
            all_uni["composition"]["denominator_by_platform"]
        out["denominator_by_bracket"] = \
            all_uni["composition"]["denominator_by_bracket"]
        out["excluded_no_timestamp"] = \
            all_uni["definition"].get("excluded_no_timestamp", 0)
        out["snapshot_id"] = all_uni["snapshot_id"]
    return out


def list_tiers(store: Store, *, scope: str = "global",
               commander_oracle_id: str | None = None,
               bracket: str | None = None, tier: str | None = None,
               collection_id: str | None = None,
               universe_id: str | None = None,
               limit: int | None = None) -> list[dict]:
    ensure_schema(store)
    active = _active_model(store)
    if scope == "universe":
        version = _universe_version(store, active, universe_id)
        if version is None:
            return []
    else:
        version = active
    q = ("SELECT t.*, COALESCE(s.name, '') AS name FROM tier_assignment t "
         "LEFT JOIN scryfall_card s ON s.oracle_id = t.oracle_id "
         "WHERE t.scope=? AND t.algo_version=?")
    args: list = [scope, version]
    if universe_id is not None:
        q += " AND t.universe_id=?"
        args.append(universe_id)
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
