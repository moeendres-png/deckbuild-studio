"""PERF #36: reference_map must return exactly what per-card
card_reference lookups return, with a constant number of queries
instead of three per card (existence + flags + role profile).

Written by the co-lead after the implementing agent's report claimed
this file existed but never wrote it; the equality and query-count
assertions below are the actual evidence for the refactor.
"""

from deckbuild_studio import reference as ref


def _seed(store, oid, *, flags=(), role=False, role_twice=False):
    ref.ensure_schema(store)
    for flag in flags:
        store.conn.execute(
            "INSERT OR REPLACE INTO reference_card_flag"
            "(oracle_id, flag, name, in_scryfall_store, source_kind) "
            "VALUES(?,?,?,1,?)", (oid, flag, oid, ref.FLAGS_KIND))
    if role:
        for i in range(2 if role_twice else 1):
            store.conn.execute(
                "INSERT OR REPLACE INTO reference_role_profile"
                "(oracle_name, oracle_id, resolution_status, roles_json,"
                " role_strengths_json, mechanic_tags_json, estimate_type,"
                " data_as_of, payload_json, source_kind) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (f"{oid}-name-{i}", oid, "resolved",
                 '["ramp"]' if i == 0 else '["draw"]',
                 '{"ramp": 0.5}', '["mana"]', "model", "2026-01-01",
                 "{}", ref.ROLES_KIND))
    store.conn.commit()


def _expected(store, ids):
    out = {}
    for oid in ids:
        one = ref.card_reference(store, oid)
        if one is not None:
            out[oid] = one
    return out


def test_reference_map_equals_per_card_lookups(store):
    _seed(store, "c-flags", flags=("game_changer",))
    _seed(store, "c-role", role=True)
    _seed(store, "c-both", flags=("commander_banned_reference",),
          role=True)
    _seed(store, "c-twice", role=True, role_twice=True)
    _seed(store, "c-none")
    ids = ["c-both", "c-flags", "c-missing", "c-role", "c-none",
           "c-twice", "c-flags"]
    got = ref.reference_map(store, ids)
    assert got == _expected(store, ids)
    # Input order is the result order; the missing and the
    # neither-flags-nor-role card are absent, exactly as per-card.
    assert list(got) == ["c-both", "c-flags", "c-role", "c-twice"]
    # Duplicate role rows: the first row wins (fetchone semantics).
    assert got["c-twice"]["role_profile"]["roles"] == ["ramp"]


def test_reference_map_query_count_is_constant(store):
    for i in range(30):
        _seed(store, f"q-{i:02d}", flags=("game_changer",), role=True)
    statements = []
    store.conn.set_trace_callback(statements.append)
    try:
        got = ref.reference_map(store, [f"q-{i:02d}" for i in range(30)])
    finally:
        store.conn.set_trace_callback(None)
    assert len(got) == 30
    # 30 cards in ONE chunk: flags query + role query. The old
    # per-card implementation issued 3 statements per card (90+).
    assert len(statements) <= 4


def test_reference_map_chunk_boundary_501_cards(store):
    ids = [f"b-{i:03d}" for i in range(501)]
    for oid in ids:
        _seed(store, oid, flags=("game_changer",))
    got = ref.reference_map(store, ids)
    assert got == _expected(store, ids)
    assert list(got) == ids


def test_reference_map_empty_and_missing_tables(store):
    assert ref.reference_map(store, []) == {}
    assert ref.reference_map(store, ["nope"]) == {}
