"""Anonymisation determinism beyond the single-group case (PR18-F-2).

The documented contract (``topdeck.anonymize_player_names``): within
one initials group the raw values are ordered by their plain string
sort, the first keeps the plain initials form, later ones get
" #2", " #3", ... — so the mapping is a bijection on the given value
set and deterministic REGARDLESS of input order. All names below are
synthetic.

test_topdeck.py already covers one collision group in forward and
reverse order. This module extends coverage to: several collision
groups present at once, ALL permutations of multi-group inputs, and
case collisions — distinct raw values that differ only in letter
case collapse into one initials group (initials are uppercased) and
are ranked by the plain (codepoint) string sort, in which uppercase
letters sort before lowercase ones.
"""

from __future__ import annotations

import itertools
import random

from deckbuild_studio.topdeck import anonymize_player_names

# Two full collision groups plus a non-colliding name. Plain string
# sort inside "J. D.": Jane Doe < Jim Doe < John Doe; inside
# "B. S.": Berta Smith < Bob Smith.
MULTI_GROUP = ["John Doe", "Jane Doe", "Jim Doe", "Bob Smith", "Berta Smith", "Jane Mary Doe"]
MULTI_GROUP_EXPECTED = {
    "Jane Doe": "J. D.",
    "Jim Doe": "J. D. #2",
    "John Doe": "J. D. #3",
    "Berta Smith": "B. S.",
    "Bob Smith": "B. S. #2",
    "Jane Mary Doe": "J. M. D.",
}

# Case variants of one name all reduce to "J. D."; the plain string
# sort ranks "JOHN DOE" < "John Doe" < "john doe" (uppercase letters
# have lower codepoints than lowercase ones).
CASE_GROUP = ["john doe", "John Doe", "JOHN DOE"]
CASE_GROUP_EXPECTED = {
    "JOHN DOE": "J. D.",
    "John Doe": "J. D. #2",
    "john doe": "J. D. #3",
}

# Single-token values collide too: all three reduce to "S."; plain
# sort ranks "Solo" < "s1" < "somehandle".
HANDLE_GROUP = ["somehandle", "s1", "Solo"]
HANDLE_GROUP_EXPECTED = {
    "Solo": "S.",
    "s1": "S. #2",
    "somehandle": "S. #3",
}


def test_multiple_collision_groups_at_once():
    assert anonymize_player_names(MULTI_GROUP) == MULTI_GROUP_EXPECTED


def test_all_permutations_of_multi_group_input():
    # 720 permutations: numbering inside EVERY group must stay put.
    for perm in itertools.permutations(MULTI_GROUP):
        assert anonymize_player_names(list(perm)) == MULTI_GROUP_EXPECTED


def test_case_collision_numbering_follows_plain_sort():
    assert anonymize_player_names(CASE_GROUP) == CASE_GROUP_EXPECTED


def test_all_permutations_of_case_group():
    for perm in itertools.permutations(CASE_GROUP):
        assert anonymize_player_names(list(perm)) == CASE_GROUP_EXPECTED


def test_single_token_case_and_handle_collision():
    assert anonymize_player_names(HANDLE_GROUP) == HANDLE_GROUP_EXPECTED
    for perm in itertools.permutations(HANDLE_GROUP):
        assert anonymize_player_names(list(perm)) == HANDLE_GROUP_EXPECTED


def test_case_group_mixed_with_other_groups_and_passthrough():
    names = CASE_GROUP + ["Bob Smith", "Berta Smith", "Jane Mary Doe", None, "", "!!!"]
    expected = {
        **CASE_GROUP_EXPECTED,
        "Berta Smith": "B. S.",
        "Bob Smith": "B. S. #2",
        "Jane Mary Doe": "J. M. D.",
        None: None,
        "": "",
        "!!!": "!!!",  # no alphanumeric character: passes through
    }
    assert anonymize_player_names(names) == expected
    rng = random.Random(20261113)
    for _ in range(200):
        shuffled = names[:]
        rng.shuffle(shuffled)
        assert anonymize_player_names(shuffled) == expected


def test_bijection_over_combined_value_set():
    names = MULTI_GROUP + CASE_GROUP + HANDLE_GROUP + ["Jane Mary Doe", None, ""]
    # "Jane Mary Doe" appears in MULTI_GROUP already; dedupe the set.
    values = set(names)
    mapping = anonymize_player_names(sorted(values, key=str))
    assert len({mapping[v] for v in values}) == len(values)
