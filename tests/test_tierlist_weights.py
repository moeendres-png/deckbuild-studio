"""Pin the tierlist weight constants to the design contract (PR17-F-1).

The expected values below are the DESIGN values of
docs/TIERLIST_1_2_DESIGN.md §3.1 (weight table) and §3.2 (neutral
floor 0.50) — they are pinned here deliberately, NOT read back from
the code: if a weight in ``tierlist.py`` ever drifts from the design
(a typo, a well-meant retune), these tests fail instead of the model
silently changing. The core weights are the unchanged 1.0.0/1.1.0
weights (design §2 rule 1: "Kern bleibt Kern"); the 1.2.0 tournament
components are additional capped layers (§3.1: global core 1.00 plus
optional max. 0.20; each tournament signal 0.10).

Sum invariants from the same source: global core sums to 1.00,
context core sums to 1.00 (0.35 + 0.25 + 0.25 + 0.15), the 1.2.0
global set sums to 1.20 and the 1.2.0 context set to 1.10.
"""

from __future__ import annotations

import pytest

from deckbuild_studio import tierlist as tl

# docs/TIERLIST_1_2_DESIGN.md §3.1 — core weights, model tierlist/1.1.0
DESIGN_GLOBAL_WEIGHTS = {
    "edhrec_global_inclusion": 0.55,
    "playgroup_win_lift": 0.25,
    "spellbook_combo_density": 0.20,
}
DESIGN_CONTEXT_WEIGHTS = {
    "edhrec_cohort_inclusion": 0.35,
    "edhrec_cohort_synergy": 0.25,
    "playgroup_win_lift": 0.25,
    "spellbook_combo_density": 0.15,
}
# docs/TIERLIST_1_2_DESIGN.md §3.1 — additional 1.2.0 tournament layers
DESIGN_GLOBAL_TOURNAMENT = {
    "edhtop16_play_rate": 0.10,
    "topdeck_conversion": 0.10,
}
DESIGN_CONTEXT_TOURNAMENT = {
    "edhtop16_commander_play_rate": 0.10,
}


def test_global_weights_1_1_0_match_design():
    assert tl.GLOBAL_WEIGHTS == DESIGN_GLOBAL_WEIGHTS


def test_context_weights_1_1_0_match_design():
    assert tl.CONTEXT_WEIGHTS == DESIGN_CONTEXT_WEIGHTS


def test_global_weights_1_2_0_match_design():
    assert tl.GLOBAL_WEIGHTS_1_2 == {**DESIGN_GLOBAL_WEIGHTS, **DESIGN_GLOBAL_TOURNAMENT}


def test_context_weights_1_2_0_match_design():
    assert tl.CONTEXT_WEIGHTS_1_2 == {**DESIGN_CONTEXT_WEIGHTS, **DESIGN_CONTEXT_TOURNAMENT}


def test_tournament_layer_is_purely_additive():
    # Design §2 rule 1 + §3.1: 1.2.0 keeps every core weight untouched
    # and only ADDS the capped tournament components.
    for key, value in DESIGN_GLOBAL_WEIGHTS.items():
        assert tl.GLOBAL_WEIGHTS_1_2[key] == value
    for key, value in DESIGN_CONTEXT_WEIGHTS.items():
        assert tl.CONTEXT_WEIGHTS_1_2[key] == value
    assert set(tl.GLOBAL_WEIGHTS_1_2) - set(tl.GLOBAL_WEIGHTS) == set(DESIGN_GLOBAL_TOURNAMENT)
    assert set(tl.CONTEXT_WEIGHTS_1_2) - set(tl.CONTEXT_WEIGHTS) == set(DESIGN_CONTEXT_TOURNAMENT)


def test_weight_sums_match_design():
    # §3.1: "Global (Kern 1,00 + optional max. 0,20)"; the context core
    # sums to 1.00 as well, its 1.2.0 form to 1.10.
    assert sum(tl.GLOBAL_WEIGHTS.values()) == pytest.approx(1.00)
    assert sum(tl.CONTEXT_WEIGHTS.values()) == pytest.approx(1.00)
    assert sum(tl.GLOBAL_WEIGHTS_1_2.values()) == pytest.approx(1.20)
    assert sum(tl.CONTEXT_WEIGHTS_1_2.values()) == pytest.approx(1.10)


def test_tournament_weights_capped_at_design_max():
    # §3.1/§2 rule 4: tournament weight alone (max. 0.20 global,
    # 0.10 context) stays below the 0.35 U gate — the cap is a design
    # invariant, not an accident of the current numbers.
    global_tournament = sum(tl.GLOBAL_WEIGHTS_1_2[k] for k in DESIGN_GLOBAL_TOURNAMENT)
    context_tournament = sum(tl.CONTEXT_WEIGHTS_1_2[k] for k in DESIGN_CONTEXT_TOURNAMENT)
    assert global_tournament == pytest.approx(0.20)
    assert context_tournament == pytest.approx(0.10)


def test_tournament_floor_matches_design():
    # docs/TIERLIST_1_2_DESIGN.md §3.2: no tournament subscore falls
    # below the neutral value 0.50.
    assert tl.TOURNAMENT_FLOOR == 0.50
