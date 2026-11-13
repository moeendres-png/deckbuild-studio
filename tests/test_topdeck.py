"""TopDeck.gg layer: official API v2 tournament lists + results, and
the locally computed per-card conversion / win rate.

All network access is faked. The fixture is a trimmed response in the
exact documented shape (standings carry ``decklist`` text with the
API's literal backslash-n newlines plus structured ``deckObj``;
``leader`` is the commander name, partners as "A / B"). One standing
has NO deckObj (text-only fallback), one has no list at all.

Hand-reckoned fixture expectations (tournaments: topCut 4 + topCut 0):

  Sol Ring (Test): decks P1,P2,P3,P4,P7,P8 = 6; cut-known 4 (P1..P4),
    cut hits 2 (P1, P2); W/D/L sums 11/5/10 = 26 games.
  Forest:          decks P2,P4,P5 = 3; cut-known 3, hits 2 (P2, P5);
    W/D/L 7/3/5 = 15 games.
  Plains:          decks P1,P8 = 2; cut-known 1 (P1), hits 1;
    W/D/L 4/1/3 = 8 games.
  Documents: 2 tournaments + 8 standings + 7 lists = 17.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import OID
from deckbuild_studio import topdeck as td_mod
from deckbuild_studio.topdeck import (ConnectorClient, TopDeckBlocked,
                                      anonymize_player_names,
                                      parse_decklist_text, parse_deckobj,
                                      parse_tournaments, sync_topdeck,
                                      top_cut_reached)

FIXTURES = Path(__file__).parent / "fixtures"
RAW = (FIXTURES / "topdeck_tournaments.json").read_bytes()
PAYLOAD = json.loads(RAW)

# one explicit window so the fake client sees exactly one request
START, END = 1757000000, 1759000000


class FakeClient:
    """Scripted post_tournaments: returns the fixture for every window
    (or raises the scripted error). Records the request bodies."""

    def __init__(self, payload=PAYLOAD, raw=RAW, error=None):
        self.payload = payload
        self.raw = raw
        self.error = error
        self.calls: list[dict] = []

    def post_tournaments(self, body):
        self.calls.append(body)
        if self.error is not None:
            raise self.error
        return self.payload, self.raw


def _sync(store, client, **kw):
    kw.setdefault("start", START)
    kw.setdefault("end", END)
    kw.setdefault("window_days", 30)
    return sync_topdeck(store, client, **kw)


# ---------------------------------------------------------------- parsing

def test_parse_deckobj_sections_metadata_and_commanders():
    standing = PAYLOAD[0]["standings"][2]  # partner deck
    entries = parse_deckobj(standing["deckObj"])
    by_name = {e["name"]: e for e in entries}
    assert set(by_name) == {"Partner Alpha", "Partner Beta",
                            "Sol Ring (Test)", "Island"}
    assert by_name["Partner Alpha"]["is_commander"] == 1
    assert by_name["Partner Beta"]["is_commander"] == 1
    assert by_name["Sol Ring (Test)"]["is_commander"] == 0
    assert all(e["quantity"] == 1 for e in entries)
    assert parse_deckobj(None) is None
    assert parse_deckobj("nope") is None


def test_parse_decklist_text_literal_newlines_and_sections():
    standing = PAYLOAD[0]["standings"][3]  # text-only deck
    assert "\\n" in standing["decklist"]  # the API's literal-\n quirk
    entries = parse_decklist_text(standing["decklist"])
    by_name = {e["name"]: e for e in entries}
    assert set(by_name) == {"Alara, Test Sovereign", "Sol Ring (Test)",
                            "Forest"}
    assert by_name["Alara, Test Sovereign"]["is_commander"] == 1
    assert by_name["Forest"]["quantity"] == 1
    assert parse_decklist_text(None) is None
    assert parse_decklist_text("") is None


def test_parse_tournaments_counts_leader_and_top_cut():
    parsed = parse_tournaments(PAYLOAD)
    assert parsed["skipped_tournaments"] == 0
    assert parsed["skipped_standings"] == 0
    t1, t2 = parsed["tournaments"]
    assert (t1["tid"], t1["top_cut"]) == ("fixture-cedh-clash", 4)
    assert (t2["tid"], t2["top_cut"]) == ("fixture-weekly-edh", 0)
    by_name = {s["name"]: s for s in t1["standings"]}
    assert by_name["Carol Example"]["leader"] == "Partner Alpha / Partner Beta"
    assert by_name["Dave Example"]["deck_source"] == "text"
    assert by_name["Frank Example"]["entries"] is None
    assert by_name["Frank Example"]["has_list_payload"] is False
    # top-cut truth comes from the bracket record, never from order
    assert top_cut_reached(by_name["Alice Example"], 4) is True   # WB 1
    assert top_cut_reached(by_name["Bob Example"], 4) is True     # LB 1
    assert top_cut_reached(by_name["Carol Example"], 4) is False  # 0/0
    assert top_cut_reached(by_name["Erin Example"], 4) is True    # WB 2
    grace = t2["standings"][0]
    assert top_cut_reached(grace, 0) is None  # tournament has no cut
    assert td_mod.count_documents(parsed) == 17


def test_parse_tournaments_rejects_non_array():
    with pytest.raises(td_mod.ParseError):
        parse_tournaments({"not": "a list"})


# ---------------------------------------------------------------- sync

def test_sync_stores_own_cohort_results_and_counts(loaded_store):
    client = FakeClient()
    result = _sync(loaded_store, client)
    assert result["status"] == "AVAILABLE"
    assert client.calls[0]["game"] == "Magic: The Gathering"
    assert client.calls[0]["format"] == "EDH"
    assert "decklist" in client.calls[0]["columns"]
    assert result["tournaments"] == 2 and result["standings"] == 8
    assert result["decks"] == 7 and result["decks_text_fallback"] == 1
    assert result["standings_without_list"] == 1
    assert result["documents"] == 17

    decks = loaded_store.conn.execute(
        "SELECT * FROM decklist_deck WHERE platform='topdeck'").fetchall()
    assert len(decks) == 7
    assert all(d["bracket_level"] is None for d in decks)
    assert all(d["bracket_source"] == "topdeck_tournament" for d in decks)
    assert all(d["status"] == "AVAILABLE" for d in decks)
    partner = next(d for d in decks
                   if d["commander_name"] == "Partner Alpha / Partner Beta")
    # a partner pair is not one card: no single commander id is claimed
    assert partner["commander_oracle_id"] is None
    cmds = loaded_store.conn.execute(
        "SELECT COUNT(*) n FROM decklist_card WHERE deck_uid=? "
        "AND is_commander=1", (partner["deck_uid"],)).fetchone()["n"]
    assert cmds == 2
    # player names are stored anonymised (initials rule): the
    # fixture's "Dave Example" / "Alice Example" land as initials
    dave = loaded_store.conn.execute(
        "SELECT * FROM topdeck_result WHERE player_name='D. E.'"
    ).fetchone()
    assert dave["deck_source"] == "text" and dave["top_cut_reached"] == 0
    assert dave["player_id"] == "player-4"  # pseudonymous id unchanged
    alice = loaded_store.conn.execute(
        "SELECT * FROM topdeck_result WHERE player_name='A. E.'"
    ).fetchone()
    assert alice["player_id"] == "player-1"
    assert alice["top_cut_reached"] == 1
    assert (alice["wins"], alice["draws"], alice["losses"]) == (3, 1, 1)

    snap = result["snapshot_id"]
    stats = {r["card_name"]: r for r in loaded_store.conn.execute(
        "SELECT * FROM topdeck_card_stat WHERE snapshot_id=?", (snap,))}
    ring = stats["Sol Ring (Test)"]
    assert (ring["decks_with"], ring["decks_in_cut"],
            ring["top_cut_decks"]) == (6, 4, 2)
    assert (ring["wins"], ring["draws"], ring["losses"],
            ring["games"]) == (11, 5, 10, 26)
    assert ring["card_oracle_id"] == OID["sol_ring"]
    forest = stats["Forest"]
    assert (forest["decks_with"], forest["decks_in_cut"],
            forest["top_cut_decks"]) == (3, 3, 2)
    assert (forest["wins"], forest["draws"], forest["losses"]) == (7, 3, 5)
    plains = stats["Plains"]
    assert (plains["decks_with"], plains["decks_in_cut"],
            plains["top_cut_decks"]) == (2, 1, 1)
    # below the minimum samples the rates stay NULL — counts only
    assert ring["conversion_rate"] is None and ring["win_rate"] is None
    assert forest["conversion_rate"] is None


def _big_payload() -> list:
    """One topCut-16 tournament, 12 players, all decks run the test
    Sol Ring; players 1-6 played a bracket match (cut reached),
    players 7-12 did not. Every record is W2 D1 L2 (5 games)."""
    standings = []
    for i in range(1, 13):
        mainboard = {"Sol Ring (Test)": {"count": 1, "id": "x"}}
        if i <= 3:
            mainboard["Forest"] = {"count": 1, "id": "y"}
        standings.append({
            "name": f"Player {i:02d}", "id": f"bp-{i}",
            "leader": "Alara, Test Sovereign",
            "decklist": "~~Commanders~~\\n1 Alara, Test Sovereign\\n",
            "deckObj": {"Commanders": {"Alara, Test Sovereign":
                                       {"count": 1, "id": "z"}},
                        "Mainboard": mainboard,
                        "metadata": {"game": "Magic: The Gathering",
                                     "format": "EDH"}},
            "wins": 2, "draws": 1, "losses": 2,
            "winsBracket": 1 if i <= 6 else 0,
            "lossesBracket": 0})
    return [{"TID": "fixture-big", "tournamentName": "Fixture Big",
             "swissNum": 6, "startDate": 1758000000, "topCut": 16,
             "game": "Magic: The Gathering", "format": "EDH",
             "standings": standings}]


def test_conversion_and_win_rate_math_above_threshold(loaded_store):
    payload = _big_payload()
    client = FakeClient(payload=payload,
                        raw=json.dumps(payload).encode())
    result = _sync(loaded_store, client)
    assert result["status"] == "AVAILABLE" and result["decks"] == 12
    stats = {r["card_name"]: r for r in loaded_store.conn.execute(
        "SELECT * FROM topdeck_card_stat WHERE snapshot_id=?",
        (result["snapshot_id"],))}
    ring = stats["Sol Ring (Test)"]
    assert (ring["decks_with"], ring["decks_in_cut"],
            ring["top_cut_decks"]) == (12, 12, 6)
    assert ring["conversion_rate"] == pytest.approx(0.5)
    assert (ring["wins"], ring["draws"], ring["losses"],
            ring["games"]) == (24, 12, 24, 60)
    assert ring["win_rate"] == pytest.approx(0.4)
    # 3 decks only: still below both thresholds
    assert stats["Forest"]["conversion_rate"] is None
    assert stats["Forest"]["win_rate"] is None
    card = td_mod.card_topdeck(loaded_store, OID["sol_ring"])
    assert card["listed"] is True
    assert card["conversion_rate"] == pytest.approx(0.5)
    assert card["win_rate"] == pytest.approx(0.4)
    assert card["attribution"] == "Data provided by TopDeck.gg"
    assert card["attribution_url"] == "https://topdeck.gg"


def test_card_topdeck_states(loaded_store):
    before = td_mod.card_topdeck(loaded_store, OID["sol_ring"])
    assert before["status"] == "NOT_FETCHED" and before["listed"] is False
    _sync(loaded_store, FakeClient())
    unlisted = td_mod.card_topdeck(loaded_store, OID["rats"])
    assert unlisted["listed"] is False
    assert unlisted["conversion_rate"] is None


def test_second_run_of_same_window_is_cached(loaded_store):
    client = FakeClient()
    first = _sync(loaded_store, client)
    second = _sync(loaded_store, client)
    assert first["status"] == "AVAILABLE"
    assert second.get("cached") is True
    assert len(client.calls) == 1  # no refetch (Terms: cache responsibly)


def test_budget_stop_is_partial_and_writes_no_stats(loaded_store):
    client = FakeClient()
    result = sync_topdeck(loaded_store, client, start=START, end=END,
                          window_days=7, doc_budget=20)
    # 17 documents per window: window 1 ok (17), window 2 ok (34 > 20
    # only stops BEFORE window 3) — honest progress, no conversion
    assert result["status"] == "PARTIAL"
    assert result["windows_completed"] == 2
    assert result["documents"] == 34
    n_stats = loaded_store.conn.execute(
        "SELECT COUNT(*) n FROM topdeck_card_stat").fetchone()["n"]
    assert n_stats == 0
    n_decks = loaded_store.conn.execute(
        "SELECT COUNT(*) n FROM decklist_deck WHERE platform='topdeck'"
    ).fetchone()["n"]
    assert n_decks == 7  # decks of completed windows stay stored


@pytest.mark.parametrize("status", [401, 429])
def test_sync_blocked_on_refusal(loaded_store, status):
    client = FakeClient(error=TopDeckBlocked(status, f"HTTP {status}"))
    result = _sync(loaded_store, client)
    assert result["status"] == "BLOCKED"
    assert loaded_store.conn.execute(
        "SELECT COUNT(*) n FROM decklist_deck WHERE platform='topdeck'"
    ).fetchone()["n"] == 0
    snap = td_mod.latest_snapshot(loaded_store, "topdeck",
                                  "topdeck_tournaments")
    assert snap["status"] == "BLOCKED"


def test_sync_blocked_without_connector_access(loaded_store):
    def no_credential(request):
        raise TopDeckBlocked(0, "no connector access: surrogate unavailable")

    class ExplodingOpener:
        def open(self, request, timeout=None):
            raise AssertionError("network must not be touched")

    client = ConnectorClient(credential_applier=no_credential,
                             opener=ExplodingOpener(), min_interval=0)
    result = _sync(loaded_store, client)
    assert result["status"] == "BLOCKED"
    assert "no connector access" in result["detail"]


# ------------------------------------------------------- anonymisation
# Owner rule (issue #1108): no real person names in stored data.
# Player names are reduced to their initials at import; the
# pseudonymous player_id is stored unchanged. All names below are
# synthetic.

def test_anonymize_multiword_and_case():
    m = anonymize_player_names(["Jane Mary Doe", "john doe"])
    assert m["Jane Mary Doe"] == "J. M. D."
    assert m["john doe"] == "J. D."


def test_anonymize_single_token_handle():
    m = anonymize_player_names(["somehandle"])
    assert m["somehandle"] == "S."


def test_anonymize_bracket_token_counts_as_part():
    m = anonymize_player_names(["[ABC] John Doe"])
    assert m["[ABC] John Doe"] == "A. J. D."


def test_anonymize_collision_numbering_is_deterministic():
    names = ["John Doe", "Jane Doe", "Jim Doe"]
    forward = anonymize_player_names(names)
    reverse = anonymize_player_names(list(reversed(names)))
    assert forward == reverse
    # sorted raw order: Jane Doe < Jim Doe < John Doe — the first
    # keeps the plain form, later ones get the running suffix
    assert forward["Jane Doe"] == "J. D."
    assert forward["Jim Doe"] == "J. D. #2"
    assert forward["John Doe"] == "J. D. #3"


def test_anonymize_keeps_distinct_values_distinct():
    names = ["John Doe", "Jane Doe", "Bob Smith", "Berta Smith",
             "handle1", "handle2", "Solo", None, ""]
    m = anonymize_player_names(names)
    raws = set(names)
    assert len({m[n] for n in raws}) == len(raws)


def test_anonymize_passthrough_empty_and_missing():
    m = anonymize_player_names([None, "", "   "])
    assert m[None] is None
    assert m[""] == ""
    assert m["   "] == "   "


def _named_payload() -> list:
    """Two players whose names collide under the initials rule plus
    one id-less handle standing; every deck runs the test Sol Ring."""
    def standing(name, pid, wins):
        row = {"name": name, "leader": "Alara, Test Sovereign",
               "deckObj": {"Commanders": {"Alara, Test Sovereign":
                                          {"count": 1, "id": "z"}},
                           "Mainboard": {"Sol Ring (Test)":
                                         {"count": 1, "id": "x"}},
                           "metadata": {"game": "Magic: The Gathering",
                                        "format": "EDH"}},
               "wins": wins, "draws": 0, "losses": 1,
               "winsBracket": 0, "lossesBracket": 0}
        if pid is not None:
            row["id"] = pid
        return row

    return [{"TID": "fixture-names", "tournamentName": "Fixture Names",
             "swissNum": 3, "startDate": 1758000000, "topCut": 0,
             "game": "Magic: The Gathering", "format": "EDH",
             "standings": [standing("Jane Doe", "pid-jane", 2),
                           standing("John Doe", "pid-john", 1),
                           standing("solohandle", None, 0)]}]


def test_sync_stores_only_anonymised_player_names(loaded_store):
    payload = _named_payload()
    client = FakeClient(payload=payload,
                        raw=json.dumps(payload).encode())
    result = _sync(loaded_store, client)
    assert result["status"] == "AVAILABLE" and result["decks"] == 3
    rows = loaded_store.conn.execute(
        "SELECT player_name, player_id FROM topdeck_result "
        "ORDER BY player_name").fetchall()
    # sorted raw order: "Jane Doe" < "John Doe" — Jane keeps the
    # plain initials form, John gets the collision suffix; the
    # pseudonymous ids are stored unchanged
    assert [(r["player_name"], r["player_id"]) for r in rows] == [
        ("J. D.", "pid-jane"), ("J. D. #2", "pid-john"), ("S.", None)]
    # no raw name survives in any stored column that carried it
    for raw_name in ("Jane Doe", "John Doe", "solohandle"):
        assert loaded_store.conn.execute(
            "SELECT COUNT(*) n FROM topdeck_result WHERE player_name=?",
            (raw_name,)).fetchone()["n"] == 0
        assert loaded_store.conn.execute(
            "SELECT COUNT(*) n FROM decklist_deck WHERE "
            "platform_deck_id LIKE ?", (f"%{raw_name}%",)
        ).fetchone()["n"] == 0
    # the id-less standing's platform deck id carries the anonymised
    # form, not the raw handle
    anon = loaded_store.conn.execute(
        "SELECT platform_deck_id FROM decklist_deck WHERE "
        "platform='topdeck' AND platform_deck_id LIKE '%:S.'"
    ).fetchone()
    assert anon is not None
    # statistics are computed from the anonymised rows unchanged:
    # all three decks run the test Sol Ring, W/D/L sums ride along
    stats = {r["card_name"]: r for r in loaded_store.conn.execute(
        "SELECT * FROM topdeck_card_stat WHERE snapshot_id=?",
        (result["snapshot_id"],))}
    ring = stats["Sol Ring (Test)"]
    assert ring["decks_with"] == 3
    assert (ring["wins"], ring["draws"], ring["losses"]) == (3, 0, 3)


# ---------------------------------------------------------------- client

class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


class _RecordingOpener:
    def __init__(self):
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return _FakeResponse(b"[]")


def test_client_pacing_user_agent_and_credential_hook():
    opener = _RecordingOpener()
    sleeps: list[float] = []
    now = [1000.0]

    def apply(request):
        request.add_header("Authorization", "hsurr:test-only")

    client = ConnectorClient(min_interval=13.0, sleeper=sleeps.append,
                             clock=lambda: now[0], opener=opener,
                             credential_applier=apply)
    parsed, _ = client.post_tournaments({"game": "Magic: The Gathering"})
    assert parsed == []
    now[0] = 1005.0  # 5 s later: 8 s of pacing remain
    client.post_tournaments({"game": "Magic: The Gathering"})
    assert sleeps == [pytest.approx(8.0)]
    req = opener.requests[0]
    assert req.full_url == "https://topdeck.gg/api/v2/tournaments"
    assert req.headers["User-agent"] == td_mod.USER_AGENT
    assert req.headers["Authorization"] == "hsurr:test-only"


class _TruncatedResponse:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        import http.client
        raise http.client.IncompleteRead(b"partial", 12345)


class _TruncatedOpener:
    def open(self, request, timeout=None):
        return _TruncatedResponse()


def test_client_truncated_body_is_transient_error():
    # regression (live 2026-11-12): a chunked response broke mid-body
    # and resp.read() raised http.client.IncompleteRead — that must
    # surface as TopDeckError, never as an unhandled crash.
    client = ConnectorClient(min_interval=0, opener=_TruncatedOpener(),
                             credential_applier=lambda req: None)
    with pytest.raises(td_mod.TopDeckError):
        client.post_tournaments({"game": "Magic: The Gathering"})


class FlakyClient:
    """Raises a transient TopDeckError for the first `failures` calls,
    then serves the fixture."""

    def __init__(self, failures=1):
        self.calls = 0
        self.failures = failures

    def post_tournaments(self, body):
        self.calls += 1
        if self.calls <= self.failures:
            raise td_mod.TopDeckError("simulated truncated response")
        return PAYLOAD, RAW


def test_sync_retries_transient_window_error_once(loaded_store):
    client = FlakyClient(failures=1)
    report = _sync(loaded_store, client, sleeper=lambda s: None)
    assert report["status"] == "AVAILABLE"
    assert client.calls == 2  # one failure + one successful retry


def test_sync_gives_up_after_second_transient_failure(loaded_store):
    client = FlakyClient(failures=99)
    with pytest.raises(td_mod.TopDeckError):
        _sync(loaded_store, client, sleeper=lambda s: None)
    assert client.calls == 2  # exactly one retry, no storm


# ---------------------------------------------------------------- universe

def _insert_archidekt_deck(store, uid: str, bracket: int, cards: list):
    store.conn.execute(
        "INSERT INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,"
        "source_url,status,parser_version,fetched_at,source_updated_at,"
        "deck_size,card_entries,mapped_cards,unmapped_cards) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, "archidekt", uid, OID["commander_a"], "Alara, Test Sovereign",
         bracket, "archidekt_edhBracket", "https://archidekt.com/decks/x",
         "AVAILABLE", "archidekt-deck/1.0.0", "2026-11-12T00:00:00Z",
         "2026-11-01T00:00:00Z", len(cards), len(cards), len(cards), 0))
    for oid, name in cards:
        store.conn.execute(
            "INSERT INTO decklist_card(deck_uid,entry_key,oracle_id,"
            "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)",
            (uid, oid, oid, name, 1, 0))
    store.conn.commit()


def _canonical_denominator(store) -> int:
    from deckbuild_studio import settings as settings_mod
    from deckbuild_studio.tierlist import (_canonical_universe,
                                           _load_decklist_selection)
    cfg = settings_mod.resolve(store)
    decks, _ = _load_decklist_selection(store, cfg)
    return _canonical_universe(decks)["denominator"]


def test_topdeck_decks_never_enter_bracket_universes(loaded_store):
    """Regression: the Archidekt bracket-universe denominator (9015 on
    the real DB) must be identical before and after a TopDeck sync —
    platform 'topdeck' is not selectable and bracket NULL never
    satisfies bracket_level IN (2,3,4)."""
    _insert_archidekt_deck(loaded_store, "archidekt:1", 2,
                            [(OID["sol_ring"], "Sol Ring (Test)")])
    _insert_archidekt_deck(loaded_store, "archidekt:2", 3,
                            [(OID["forest"], "Forest")])
    _insert_archidekt_deck(loaded_store, "archidekt:3", 3,
                            [(OID["island"], "Island")])
    before = _canonical_denominator(loaded_store)
    assert before == 3
    result = _sync(loaded_store, FakeClient())
    assert result["decks"] == 7
    after = _canonical_denominator(loaded_store)
    assert after == before == 3


# ---------------------------------------------------------------- web

@pytest.fixture()
def web_client(loaded_store, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from conftest import write_foundation_xlsx
    from deckbuild_studio import web as web_mod
    from deckbuild_studio.importers import import_foundation_workbook
    rows = [("Alara, Test Sovereign", 1, "Foundation"),
            ("Plains", 60, "Foundation")]
    path = write_foundation_xlsx(tmp_path / "f.xlsx", rows)
    import_foundation_workbook(loaded_store, path)
    monkeypatch.setattr(web_mod, "database_path", lambda: loaded_store.path)
    return TestClient(web_mod.create_app()), loaded_store


def test_web_external_card_carries_topdeck(web_client):
    client, store = web_client
    _sync(store, FakeClient())
    data = client.get("/api/external/card",
                      params={"oracle_id": OID["sol_ring"]}).json()
    td = data["topdeck"]
    assert td["listed"] is True and td["decks_with"] == 6
    assert td["attribution"] == "Data provided by TopDeck.gg"
    assert td["attribution_url"] == "https://topdeck.gg"
    # the drawer renders the attribution next to the TopDeck values
    html = client.get("/").text
    assert "Data provided by" in html and "https://topdeck.gg" in html
    assert "Turnier (TopDeck)" in html
