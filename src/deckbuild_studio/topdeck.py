"""TopDeck.gg layer — cEDH tournament deck lists with player results,
and per-card top-cut conversion computed locally from those lists.

Access audit (2026-11-12, evidence in docs/DATA_SOURCES_EXPLORATION.md
section 2 and docs/TOPDECK.md):

  * Official, documented API v2 only: ``POST
    https://topdeck.gg/api/v2/tournaments`` (Developer Terms section 7
    forbids any other access route — no scraping). The credential
    comes from the Muse connector ``custom.topdeck``: a dynamic
    credential surrogate is placed into the ``Authorization`` header
    (raw key, no "Bearer" prefix, as the API docs prescribe). The raw
    API key never appears in this code, an environment variable, a log
    or the database. Without connector access the sync records BLOCKED
    and fetches nothing.
  * topdeck.gg sits behind Cloudflare, which bans the default
    Python-urllib client signature (HTTP 403, error code 1010) — the
    client sends a normal client User-Agent, like the connector's own
    helper does.
  * Limits (API docs + Terms section 3, "cache responsibly"): the
    query endpoint allows 5 requests/minute per key and each account
    can read 1,000,000 documents per UTC day. The client paces itself
    to one request per 13 s and the sync counts the documents it
    consumed (tournaments + standings + deck lists) and stops
    honestly (PARTIAL, with progress) before the configured budget
    would be exceeded. HTTP 401/403/429 are recorded BLOCKED — no
    retry storm, no escalation.
  * Attribution (Terms section 6.1) is mandatory: every surface that
    shows TopDeck data carries "Data provided by TopDeck.gg" with a
    link to https://topdeck.gg. The card payload therefore carries the
    attribution fields and the web UI renders them next to the values.

Storage (decision, justified in docs/TOPDECK.md): tournament decks go
into the shared ``decklist_deck`` / ``decklist_card`` tables with
``platform='topdeck'`` and ``bracket_level`` NULL (source
``topdeck_tournament``). They can never enter an Archidekt bracket
universe: the settings platform allow-list does not contain
'topdeck', and every universe query filters ``bracket_level IN
(2,3,4)``, which a NULL bracket never satisfies. Player results live
in ``topdeck_result``, tournaments in ``topdeck_tournament``, and the
computed per-card figures in ``topdeck_card_stat`` — all scoped to
the sync's snapshot, like every other layer.

Conversion semantics (computed here, NOT published by any source —
EDHTop16 publishes play rates only, per-card conversion stays absent
there): for every card, over the decks of one sync window,

  * ``decks_with`` — decks whose list contains the card (presence;
    quantity is irrelevant, commander entries count like any card),
  * top-cut conversion — of the decks in tournaments WITH a top cut
    (``topCut`` > 0) whose bracket record is known, the share that
    reached the cut. A player reached the cut exactly when they
    played at least one elimination-bracket match:
    ``winsBracket + lossesBracket > 0`` (both fields are documented
    standings columns; the standings array order is NOT a final
    ranking and is never used as one). Tournaments without a top cut
    and decks with an unknown bracket record stay out of this
    denominator — never silently counted either way.
  * win rate — sum of the published standing totals (``wins`` /
    (``wins`` + ``draws`` + ``losses``)) over all decks containing
    the card. The published totals include bracket matches; that is
    the source's own record and is labelled as such.

Rates are only published above minimum samples (conversion: at least
10 decks with a known bracket record; win rate: at least 10 decks
and 30 games). Below that the counts are stored and the rate stays
NULL — the same "unknown instead of a made-up number" rule the
tierlist uses. The figures never enter the evidence-tier formula
(tierlist 1.1.0); this is a separate, provenance-carrying layer.

The full API responses are NOT retained (a 12-month window is on the
order of a gigabyte of JSON); the snapshot stores a manifest with the
per-window SHA-256 and document counts instead, and the parsed deck
lists themselves are the retained record.
"""
from __future__ import annotations

import calendar as _calendar
import hashlib
import http.client
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .external import latest_snapshot, save_snapshot
from .store import Store, utcnow

PARSER_ID = "topdeck-tournaments/1.0.0"
SOURCE_NAME = "topdeck"
KIND = "topdeck_tournaments"
API_URL = "https://topdeck.gg/api/v2/tournaments"
EVENT_URL = "https://topdeck.gg/event/{tid}"
ATTRIBUTION = "Data provided by TopDeck.gg"
ATTRIBUTION_URL = "https://topdeck.gg"
GAME = "Magic: The Gathering"
FORMAT = "EDH"
COLUMNS = ["name", "id", "decklist", "wins", "draws", "losses",
           "winsBracket", "lossesBracket"]
PROVIDER = "custom.topdeck"
ALLOWED_HOSTS = ["topdeck.gg"]
USER_AGENT = "deckbuild-studio/1.0 (+https://topdeck.gg/api/docs)"
# 5 requests/minute per key on this endpoint -> one per 13 s is safely
# inside the limit; the daily document budget is guarded separately.
MIN_INTERVAL = 13.0
DEFAULT_DOC_BUDGET = 950_000
CONVERSION_MIN_DECKS = 10
WIN_RATE_MIN_DECKS = 10
WIN_RATE_MIN_GAMES = 30
_DYNAMIC_CREDENTIALS_PATHS = ["/opt/muse/skills/custom-connector-setup/bin"]


class TopDeckError(Exception):
    """Terminal sync failure to surface (transient network error — no
    snapshot written for the run; decks of completed windows stay
    stored and are reported by the next run's coverage)."""


class TopDeckBlocked(Exception):
    """The API refused the request (401/403/429) or no connector
    access exists. Recorded as a BLOCKED snapshot; never retried
    inside the run."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


class ParseError(Exception):
    """A 200 response that is not the documented tournaments array."""


# --------------------------------------------------------------------------
# API client (connector credential surrogate; the raw key never exists here)
# --------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):  # noqa: ANN002, ANN202
        raise RuntimeError("redirect refused, verify the endpoint")


def _apply_connector_credential(request: urllib.request.Request) -> None:
    """Place the custom.topdeck credential surrogate on the request.

    Raises TopDeckBlocked when the connector machinery is unavailable
    (no Muse connector access in this process) — the sync maps
    that to an honest BLOCKED snapshot instead of fetching anything."""
    for path in _DYNAMIC_CREDENTIALS_PATHS:
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        from dynamic_credentials import add_surrogate_to_request
    except ImportError as exc:
        raise TopDeckBlocked(
            0, f"no connector access: dynamic_credentials not importable "
               f"({exc}); the TopDeck credential is only available "
               f"through the custom.topdeck connector") from exc
    try:
        add_surrogate_to_request(request, PROVIDER, allowed_hosts=ALLOWED_HOSTS)
    except Exception as exc:  # DynamicCredentialError and friends
        raise TopDeckBlocked(
            0, f"no connector access: credential surrogate unavailable "
               f"({type(exc).__name__}: {exc})") from exc


class ConnectorClient:
    """Minimal POST client for the one documented query endpoint.

    Test hooks: ``opener`` (anything with .open(request, timeout=...)),
    ``sleeper`` / ``clock`` for pacing, and ``credential_applier``
    replace the connector hook in tests."""

    def __init__(self, *, min_interval: float = MIN_INTERVAL,
                 timeout: float = 180.0, sleeper=time.sleep,
                 clock=time.monotonic, opener=None,
                 credential_applier=None):
        self.min_interval = min_interval
        self.timeout = timeout
        self._sleeper = sleeper
        self._clock = clock
        self._opener = opener or urllib.request.build_opener(_NoRedirect())
        self._apply_credential = credential_applier or _apply_connector_credential
        self._last_request = 0.0
        self.requests = 0

    def _throttle(self) -> None:
        wait = self.min_interval - (self._clock() - self._last_request)
        if wait > 0:
            self._sleeper(wait)
        self._last_request = self._clock()

    def post_tournaments(self, body: dict) -> tuple[object, bytes]:
        """One paced POST. Returns (parsed JSON, raw body bytes).

        401/403/429 -> TopDeckBlocked; other HTTP errors and network
        failures -> TopDeckError; a non-JSON 200 -> ParseError."""
        self._throttle()
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            API_URL, data=data, method="POST",
            headers={"Content-Type": "application/json",
                     "User-Agent": USER_AGENT})
        self._apply_credential(request)
        self.requests += 1
        try:
            with self._opener.open(request, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:500]
            except Exception:  # noqa: BLE001 — detail is best-effort
                pass
            if exc.code in (401, 403, 429):
                raise TopDeckBlocked(
                    exc.code, f"HTTP {exc.code} from TopDeck API: "
                              f"{detail or exc.reason}") from exc
            raise TopDeckError(
                f"HTTP {exc.code} from TopDeck API: "
                f"{detail or exc.reason}") from exc
        except (urllib.error.URLError, TimeoutError, OSError,
                http.client.HTTPException) as exc:
            # HTTPException covers IncompleteRead & friends raised by
            # resp.read() when a chunked transfer breaks mid-body
            # (seen live 2026-11-12: a ~22 MB window response truncated
            # after 10.7 MB). Transient — the sync retries the window
            # once, then fails honestly as TopDeckError.
            raise TopDeckError(f"network error for {API_URL}: {exc}") from exc
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ParseError(f"response is not JSON: {exc}") from exc
        return parsed, raw


# --------------------------------------------------------------------------
# Payload parsing (pure functions — fixture-tested)
# --------------------------------------------------------------------------

def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def parse_deckobj(deck_obj: object) -> list[dict] | None:
    """deckObj -> aggregated entries [{name, quantity, is_commander}].

    Shape (documented + live-verified 2026-11-12): an object keyed by
    section ("Commanders", "Mainboard", occasionally "Stickers" /
    "Attractions"), each section mapping card name -> {"id": printing
    id, "count": n}; a "metadata" section (game/format/import info) is
    not a card section and is skipped. The printing id is NOT used —
    identity resolution is by name against the local store, like every
    other layer. Returns None when the payload is not an object."""
    if not isinstance(deck_obj, dict):
        return None
    entries: dict[str, dict] = {}
    for section, cards in deck_obj.items():
        if section == "metadata" or not isinstance(cards, dict):
            continue
        is_cmd = 1 if str(section).strip().lower() == "commanders" else 0
        for name, info in cards.items():
            qty = 1
            if isinstance(info, dict):
                qty = _as_int(info.get("count")) or 1
            elif isinstance(info, int) and info > 0:
                qty = info
            slot = entries.setdefault(
                str(name), {"name": str(name), "quantity": 0, "is_commander": 0})
            slot["quantity"] += qty
            slot["is_commander"] = max(slot["is_commander"], is_cmd)
    return sorted(entries.values(), key=lambda e: e["name"])


def parse_decklist_text(text: object) -> list[dict] | None:
    """The plain-text decklist -> the same entry shape as parse_deckobj.

    Live-verified quirk (2026-11-12): the API delivers the newlines as
    LITERAL backslash-n sequences, not real newlines — they are
    normalised first. Sections are ``~~Name~~`` header lines (the
    documented example: ``~~Commanders~~``), card lines are
    ``<count> <name>`` (a bare name counts once). Lines that carry no
    card (blank, stray markers) are skipped."""
    if not isinstance(text, str) or not text.strip():
        return None
    normalised = (text.replace("\\r\\n", "\n").replace("\\n", "\n")
                  .replace("\r", "\n"))
    entries: dict[str, dict] = {}
    section = ""
    for raw_line in normalised.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("~~") and line.endswith("~~") and len(line) > 4:
            section = line.strip("~").strip()
            continue
        qty, name = 1, line
        head, _, rest = line.partition(" ")
        if rest and head.isdigit():
            qty, name = int(head), rest.strip()
        if not name:
            continue
        is_cmd = 1 if section.lower() == "commanders" else 0
        slot = entries.setdefault(
            name, {"name": name, "quantity": 0, "is_commander": 0})
        slot["quantity"] += qty
        slot["is_commander"] = max(slot["is_commander"], is_cmd)
    if not entries:
        return None
    return sorted(entries.values(), key=lambda e: e["name"])


def _parse_standing(row: object) -> dict | None:
    """One standings row -> a deck record, or None when the row is not
    a usable standing (not an object / no name and no id). A standing
    WITHOUT a published list is a valid result row (deck=None)."""
    if not isinstance(row, dict):
        return None
    name = row.get("name")
    player_id = row.get("id")
    if name is None and player_id is None:
        return None
    if isinstance(row.get("players"), list) and not row.get("deckObj") \
            and not row.get("decklist"):
        return {"team_row": True, "name": name, "player_id": player_id}
    leader = row.get("leader") if isinstance(row.get("leader"), str) else None
    entries = parse_deckobj(row.get("deckObj"))
    deck_source = "deckobj"
    if not entries:
        entries = parse_decklist_text(row.get("decklist"))
        deck_source = "text"
    wins_bracket = _as_int(row.get("winsBracket"))
    losses_bracket = _as_int(row.get("lossesBracket"))
    return {
        "team_row": False,
        "name": str(name) if name is not None else None,
        "player_id": str(player_id) if player_id is not None else None,
        "leader": leader,
        "wins": _as_int(row.get("wins")),
        "draws": _as_int(row.get("draws")),
        "losses": _as_int(row.get("losses")),
        "wins_bracket": wins_bracket,
        "losses_bracket": losses_bracket,
        "bracket_known": wins_bracket is not None or losses_bracket is not None,
        "entries": entries,
        "deck_source": deck_source if entries else None,
        "has_list_payload": bool(row.get("deckObj") or row.get("decklist")),
    }


def parse_tournaments(payload: object) -> dict:
    """The documented response (a JSON array of tournaments) ->
    normalised tournaments + honest skip counters.

    Raises ParseError when the payload is not an array at all."""
    if not isinstance(payload, list):
        raise ParseError("response is not a JSON array of tournaments")
    tournaments: list[dict] = []
    skipped_tournaments = 0
    skipped_standings = 0
    for item in payload:
        if not isinstance(item, dict) or not item.get("TID"):
            skipped_tournaments += 1
            continue
        standings: list[dict] = []
        for row in item.get("standings") or []:
            parsed = _parse_standing(row)
            if parsed is None:
                skipped_standings += 1
                continue
            standings.append(parsed)
        tournaments.append({
            "tid": str(item["TID"]),
            "name": item.get("tournamentName"),
            "start_date": _as_int(item.get("startDate")),
            "swiss_num": _as_int(item.get("swissNum")),
            "top_cut": _as_int(item.get("topCut")) or 0,
            "standings": standings,
        })
    return {"tournaments": tournaments,
            "skipped_tournaments": skipped_tournaments,
            "skipped_standings": skipped_standings}


def count_documents(parsed: dict) -> int:
    """Conservative document accounting for the daily budget: one per
    tournament + one per standing + one per published deck list."""
    docs = 0
    for t in parsed["tournaments"]:
        docs += 1 + len(t["standings"])
        docs += sum(1 for s in t["standings"] if s.get("has_list_payload"))
    return docs


def top_cut_reached(standing: dict, top_cut: int) -> bool | None:
    """True/False when the bracket record decides it, None when the
    tournament has no top cut or the record is unknown. NEVER derived
    from the standings order (the array is not a final ranking)."""
    if not top_cut:
        return None
    if not standing["bracket_known"]:
        return None
    played = (standing["wins_bracket"] or 0) + (standing["losses_bracket"] or 0)
    return played > 0


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

def _name_to_oracle(store: Store) -> dict[str, str]:
    """Exact paper name (full or front face) -> oracle_id, local only."""
    out: dict[str, str] = {}
    for r in store.conn.execute(
            "SELECT oracle_id, name, front_name FROM scryfall_card"):
        out.setdefault(r["name"], r["oracle_id"])
        if r["front_name"]:
            out.setdefault(r["front_name"], r["oracle_id"])
    return out


def _resolve(store: Store, by_name: dict[str, str], name: str) -> str | None:
    oracle_id = by_name.get(name)
    if oracle_id is not None and store.scryfall(oracle_id) is not None:
        return oracle_id
    hit = store.scryfall_by_name(name)
    return hit[0]["oracle_id"] if len(hit) == 1 else None


def _deck_uid(tid: str, standing: dict) -> str:
    if standing["player_id"]:
        return f"topdeck:{tid}:{standing['player_id']}"
    digest = hashlib.sha256(
        f"{tid}|{standing['name']}|{standing['leader']}".encode()).hexdigest()[:16]
    return f"topdeck:{tid}:{digest}"


def _store_deck(store: Store, *, snapshot_id: str, tournament: dict,
                standing: dict, by_name: dict[str, str]) -> str:
    """Store one tournament deck + its result row; returns the deck_uid.

    The deck row carries the TopDeck cohort markers: platform
    'topdeck', bracket NULL (tournaments have no EDH bracket),
    bracket_source 'topdeck_tournament'. Only called for standings
    WITH a parsed list — a listless standing has no deck to store."""
    tid = tournament["tid"]
    uid = _deck_uid(tid, standing)
    entries = standing["entries"] or []
    leader = standing["leader"]
    leader_parts = [p.strip() for p in leader.split(" / ")] if leader else []
    commander_oracle_id = None
    detail_bits = [f"topdeck tournament {tid}",
                   f"deck source: {standing['deck_source']}"]
    if len(leader_parts) == 1:
        commander_oracle_id = _resolve(store, by_name, leader_parts[0])
    elif len(leader_parts) > 1:
        detail_bits.append(f"partner commander: {leader}")
    content = json.dumps(
        {"leader": leader, "entries": entries,
         "wins": standing["wins"], "draws": standing["draws"],
         "losses": standing["losses"]}, sort_keys=True, ensure_ascii=False)
    sha = hashlib.sha256(content.encode()).hexdigest()
    mapped = unmapped = 0
    unmapped_names: list[str] = []
    card_rows: list[tuple] = []
    for entry in entries:
        oracle_id = _resolve(store, by_name, entry["name"])
        if oracle_id is None:
            unmapped += 1
            unmapped_names.append(entry["name"])
        else:
            mapped += 1
        card_rows.append((uid, oracle_id or f"name:{entry['name']}", oracle_id,
                          entry["name"], entry["quantity"],
                          entry["is_commander"]))
    start_iso = None
    if tournament["start_date"]:
        start_iso = datetime.fromtimestamp(
            tournament["start_date"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.conn.execute(
        "INSERT OR REPLACE INTO decklist_deck(deck_uid,platform,platform_deck_id,"
        "commander_oracle_id,commander_name,bracket_level,bracket_source,source_url,"
        "status,parser_version,sha256,raw_path,fetched_at,source_updated_at,"
        "deck_size,card_entries,mapped_cards,unmapped_cards,unmapped_names_json,"
        "detail) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, "topdeck", f"{tid}:{standing['player_id'] or standing['name']}",
         commander_oracle_id, leader, None, "topdeck_tournament",
         EVENT_URL.format(tid=tid), "AVAILABLE", PARSER_ID, sha, None,
         utcnow(), start_iso,
         sum(e["quantity"] for e in entries), len(entries), mapped, unmapped,
         json.dumps(sorted(unmapped_names), ensure_ascii=False),
         "; ".join(detail_bits)))
    store.conn.execute("DELETE FROM decklist_card WHERE deck_uid=?", (uid,))
    store.conn.executemany(
        "INSERT OR REPLACE INTO decklist_card(deck_uid,entry_key,oracle_id,"
        "card_name,quantity,is_commander) VALUES(?,?,?,?,?,?)", card_rows)
    reached = top_cut_reached(standing, tournament["top_cut"])
    store.conn.execute(
        "INSERT OR REPLACE INTO topdeck_result(deck_uid,snapshot_id,tid,"
        "player_name,player_id,wins,draws,losses,wins_bracket,losses_bracket,"
        "top_cut_reached,deck_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, snapshot_id, tid, standing["name"], standing["player_id"],
         standing["wins"], standing["draws"], standing["losses"],
         standing["wins_bracket"], standing["losses_bracket"],
         None if reached is None else int(reached), standing["deck_source"]))
    return uid


def _flush_tournaments(store: Store, snapshot_id: str,
                       pending: list[tuple]) -> None:
    """Write the run's tournament summary rows under the FINAL
    snapshot id. They are buffered during the run because
    topdeck_tournament.snapshot_id is a foreign key into
    external_snapshot — the snapshot row only exists once the run
    records it (its id derives from the completed manifest)."""
    store.conn.executemany(
        "INSERT OR REPLACE INTO topdeck_tournament(snapshot_id,tid,"
        "tournament_name,start_date,swiss_num,top_cut,players,"
        "decks_with_lists,documents) VALUES(?,?,?,?,?,?,?,?,?)",
        [(snapshot_id, *row) for row in pending])
    store.conn.commit()


# --------------------------------------------------------------------------
# Sync
# --------------------------------------------------------------------------

def _months_back(end_ts: int, months: int) -> int:
    dt = datetime.fromtimestamp(end_ts, timezone.utc)
    year, month = dt.year, dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(dt.day, _calendar.monthrange(year, month)[1])
    return int(dt.replace(year=year, month=month, day=day).timestamp())


def _windows(start: int, end: int, window_days: int) -> list[tuple[int, int]]:
    step = max(1, window_days) * 86400
    out: list[tuple[int, int]] = []
    t = start
    while t < end:
        out.append((t, min(t + step, end)))
        t += step
    return out


def _window_label(start: int, end: int) -> str:
    fmt = "%Y-%m-%d"
    return (f"{datetime.fromtimestamp(start, timezone.utc).strftime(fmt)}/"
            f"{datetime.fromtimestamp(end, timezone.utc).strftime(fmt)}")


def sync_topdeck(store: Store, client=None, *,
                 collection_id: str = "foundation-schwarze-box",
                 force: bool = False, months: int = 12,
                 start: int | None = None, end: int | None = None,
                 window_days: int = 7,
                 doc_budget: int = DEFAULT_DOC_BUDGET,
                 sleeper=time.sleep) -> dict:
    """Harvest EDH tournament deck lists + results for one window.

    The window (default: the last ``months`` calendar months) is
    fetched in ``window_days`` sub-windows, oldest first, one paced
    request each. Every fetched deck is stored immediately, so a
    stopped run keeps its progress; the run's snapshot is written at
    the end (AVAILABLE), on a budget stop (PARTIAL, conversion NOT
    recomputed — the figures stay with the last complete snapshot) or
    on a refusal (BLOCKED). A repeat run of the same window reuses a
    current AVAILABLE snapshot unless ``force`` (Terms section 3:
    cache responsibly)."""
    if end is None:
        end = int(time.time())
    if start is None:
        start = _months_back(end, months)
    slug = f"{start}-{end}"
    label = _window_label(start, end)

    if client is None:
        try:
            client = ConnectorClient()
        except Exception as exc:  # noqa: BLE001 — client construction
            client = _UnavailableClient(exc)  # surfaces as BLOCKED below

    existing = latest_snapshot(store, SOURCE_NAME, KIND, slug=slug)
    if existing is not None and not force and existing["status"] == "AVAILABLE":
        return {"snapshot_id": existing["snapshot_id"], "status": "AVAILABLE",
                "cached": True, "window": label,
                "detail": "current topdeck snapshot for this window exists; "
                          "pass --force to refetch",
                "collection": topdeck_coverage(store, collection_id)}

    by_name = _name_to_oracle(store)
    windows = _windows(start, end, window_days)
    manifest_windows: list[dict] = []
    totals = {"tournaments": 0, "standings": 0, "decks": 0,
              "decks_text_fallback": 0, "standings_without_list": 0,
              "skipped_standings": 0, "skipped_team_standings": 0,
              "skipped_tournaments": 0, "duplicate_decks": 0,
              "documents": 0}
    aggregates: dict[str, dict] = {}
    seen_decks: set[str] = set()
    pending_tournaments: list[tuple] = []
    # The final snapshot id depends on the completed manifest, which
    # only exists at the end of the run — but result rows must carry
    # a snapshot id while storing. They are written under a
    # provisional id derived from the window and re-pointed to the
    # final snapshot id when the run records it (see record()).
    provisional_id = "snap-" + hashlib.sha256(
        f"{SOURCE_NAME}|{KIND}|{slug}".encode()).hexdigest()[:24]

    def manifest(status_note: str) -> bytes:
        return json.dumps(
            {"source": SOURCE_NAME, "kind": KIND, "parser": PARSER_ID,
             "window": {"start": start, "end": end, "label": label},
             "windows": manifest_windows, "totals": totals,
             "note": status_note}, sort_keys=True).encode()

    def record(status: str, detail: str, *, with_stats: bool = False) -> dict:
        snap = save_snapshot(
            store, source_name=SOURCE_NAME, kind=KIND, url=API_URL,
            status=status, slug=slug, raw=manifest(detail),
            captured_count=totals["decks"],
            displayed_total=totals["tournaments"],
            coverage_status="TOTAL_KNOWN" if status == "AVAILABLE" else None,
            detail=detail,
            payload={"parser": PARSER_ID, "window": label,
                     "documents": totals["documents"],
                     "windows_completed": len(manifest_windows),
                     "windows_total": len(windows), **totals})
        if snap != provisional_id:
            # save_snapshot derives its id from the manifest hash; move
            # the run's result rows onto the final id so provenance
            # joins up (tournament rows are only flushed now, under
            # the final id — see _flush_tournaments).
            store.conn.execute(
                "UPDATE topdeck_result SET snapshot_id=? "
                "WHERE snapshot_id=?", (snap, provisional_id))
            store.conn.commit()
        _flush_tournaments(store, snap, pending_tournaments)
        if with_stats:
            _write_card_stats(store, snap, aggregates, by_name)
        return {"snapshot_id": snap, "status": status, "source_url": API_URL,
                "window": label, "detail": detail, **totals,
                "windows_completed": len(manifest_windows),
                "windows_total": len(windows),
                "collection": topdeck_coverage(store, collection_id)}

    for w_start, w_end in windows:
        if totals["documents"] > doc_budget:
            detail = (f"document budget stop: {totals['documents']} documents "
                      f"consumed (budget {doc_budget}); windows "
                      f"{len(manifest_windows)}/{len(windows)} completed — "
                      f"resume by re-running this window or narrowing it; "
                      f"conversion NOT recomputed on a partial corpus")
            return record("PARTIAL", detail)
        body = {"game": GAME, "format": FORMAT, "start": w_start,
                "end": w_end, "columns": COLUMNS}
        try:
            try:
                payload, raw = client.post_tournaments(body)
            except TopDeckError:
                # one retry per window for transient failures (e.g. a
                # truncated chunked response); a refusal (BLOCKED) or a
                # parse error is never retried, and a second transient
                # failure ends the run as TopDeckError (CLI: FAILED) —
                # the windows stored so far stay stored.
                sleeper(30)
                payload, raw = client.post_tournaments(body)
        except TopDeckBlocked as exc:
            detail = (f"{exc.detail}; windows {len(manifest_windows)}/"
                      f"{len(windows)} completed before the refusal — "
                      f"no retry, no escalation")
            return record("BLOCKED", detail)
        except ParseError as exc:
            detail = (f"parse error in window {_window_label(w_start, w_end)}: "
                      f"{exc}; windows {len(manifest_windows)}/"
                      f"{len(windows)} completed")
            return record("PARTIAL", detail)
        parsed = parse_tournaments(payload)
        docs = count_documents(parsed)
        totals["documents"] += docs
        totals["skipped_tournaments"] += parsed["skipped_tournaments"]
        totals["skipped_standings"] += parsed["skipped_standings"]
        window_decks = 0
        for tournament in parsed["tournaments"]:
            totals["tournaments"] += 1
            decks_here = 0
            for standing in tournament["standings"]:
                totals["standings"] += 1
                if standing["team_row"]:
                    totals["skipped_team_standings"] += 1
                    continue
                if not standing["entries"]:
                    totals["standings_without_list"] += 1
                    continue
                uid = _deck_uid(tournament["tid"], standing)
                if uid in seen_decks:
                    totals["duplicate_decks"] += 1
                    continue
                seen_decks.add(uid)
                _store_deck(store, snapshot_id=provisional_id,
                            tournament=tournament, standing=standing,
                            by_name=by_name)
                decks_here += 1
                window_decks += 1
                totals["decks"] += 1
                if standing["deck_source"] == "text":
                    totals["decks_text_fallback"] += 1
                _accumulate(aggregates, tournament, standing)
            pending_tournaments.append(
                (tournament["tid"], tournament["name"],
                 tournament["start_date"], tournament["swiss_num"],
                 tournament["top_cut"], len(tournament["standings"]),
                 decks_here,
                 1 + len(tournament["standings"]) + sum(
                     1 for s in tournament["standings"]
                     if s.get("has_list_payload"))))
        store.conn.commit()
        manifest_windows.append(
            {"start": w_start, "end": w_end,
             "label": _window_label(w_start, w_end),
             "sha256": hashlib.sha256(raw).hexdigest(),
             "tournaments": len(parsed["tournaments"]),
             "decks": window_decks, "documents": docs})

    detail = (f"TopDeck EDH tournaments {label}: {totals['tournaments']} "
              f"tournaments, {totals['decks']} deck lists stored "
              f"({totals['decks_text_fallback']} via text fallback), "
              f"{totals['standings_without_list']} standings without a "
              f"published list, {totals['documents']} documents consumed; "
              f"conversion + win rate computed locally (see docs/TOPDECK.md); "
              f"full API responses are not retained — per-window SHA-256 "
              f"in the snapshot manifest")
    if totals["skipped_standings"] or totals["skipped_tournaments"]:
        detail += (f"; skipped {totals['skipped_tournaments']} malformed "
                   f"tournaments and {totals['skipped_standings']} "
                   f"malformed standings")
    return record("AVAILABLE", detail, with_stats=True)


class _UnavailableClient:
    """Stand-in used when the connector client cannot even be built;
    its first call raises the captured error as TopDeckBlocked."""

    def __init__(self, exc: Exception):
        self._exc = exc

    def post_tournaments(self, body: dict):  # noqa: ANN202
        if isinstance(self._exc, TopDeckBlocked):
            raise self._exc
        raise TopDeckBlocked(
            0, f"no connector access: {type(self._exc).__name__}: "
               f"{self._exc}")


def _accumulate(aggregates: dict[str, dict], tournament: dict,
                standing: dict) -> None:
    """Fold one deck into the per-card conversion aggregates (presence
    per deck; the deck's published W/D/L totals ride along)."""
    reached = top_cut_reached(standing, tournament["top_cut"])
    names = {e["name"] for e in standing["entries"] or []}
    for name in names:
        slot = aggregates.setdefault(
            name, {"decks_with": 0, "cut_known": 0, "cut_hits": 0,
                   "wins": 0, "draws": 0, "losses": 0})
        slot["decks_with"] += 1
        if reached is not None:
            slot["cut_known"] += 1
            slot["cut_hits"] += int(reached)
        slot["wins"] += standing["wins"] or 0
        slot["draws"] += standing["draws"] or 0
        slot["losses"] += standing["losses"] or 0


def _write_card_stats(store: Store, snapshot_id: str,
                      aggregates: dict[str, dict],
                      by_name: dict[str, str]) -> int:
    store.conn.execute("DELETE FROM topdeck_card_stat WHERE snapshot_id=?",
                       (snapshot_id,))
    written = 0
    for name, slot in aggregates.items():
        games = slot["wins"] + slot["draws"] + slot["losses"]
        conversion = None
        if slot["cut_known"] >= CONVERSION_MIN_DECKS:
            conversion = slot["cut_hits"] / slot["cut_known"]
        win_rate = None
        if slot["decks_with"] >= WIN_RATE_MIN_DECKS and games >= WIN_RATE_MIN_GAMES:
            win_rate = slot["wins"] / games
        store.conn.execute(
            "INSERT OR REPLACE INTO topdeck_card_stat(snapshot_id,card_name,"
            "card_oracle_id,decks_with,decks_in_cut,top_cut_decks,"
            "conversion_rate,wins,draws,losses,games,win_rate) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (snapshot_id, name, _resolve(store, by_name, name),
             slot["decks_with"], slot["cut_known"], slot["cut_hits"],
             conversion, slot["wins"], slot["draws"], slot["losses"],
             games, win_rate))
        written += 1
    store.conn.commit()
    return written


# --------------------------------------------------------------------------
# Read side (coverage + per-card), mirroring the EDHTop16 layer's shape
# --------------------------------------------------------------------------

def topdeck_coverage(store: Store, collection_id: str) -> dict:
    total = store.conn.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"collection_id": collection_id, "total_identities": total,
                "status": "NOT_FETCHED", "with_conversion": 0,
                "with_win_rate": 0, "cards_published": 0}
    payload = json.loads(snap["payload_json"]) if snap["payload_json"] else {}

    def covered(column: str) -> int:
        return store.conn.execute(
            f"SELECT COUNT(DISTINCT s.card_oracle_id) covered FROM "
            f"topdeck_card_stat s JOIN physical_lot l "
            f"ON l.oracle_id = s.card_oracle_id "
            f"WHERE s.snapshot_id=? AND l.collection_id=? "
            f"AND s.{column} IS NOT NULL",
            (snap["snapshot_id"], collection_id)).fetchone()["covered"]

    published = store.conn.execute(
        "SELECT COUNT(*) n FROM topdeck_card_stat WHERE snapshot_id=?",
        (snap["snapshot_id"],)).fetchone()["n"]
    tournaments = store.conn.execute(
        "SELECT COUNT(*) n FROM topdeck_tournament WHERE snapshot_id=?",
        (snap["snapshot_id"],)).fetchone()["n"]
    return {"collection_id": collection_id, "total_identities": total,
            "status": snap["status"],
            "with_conversion": covered("conversion_rate"),
            "with_win_rate": covered("win_rate"),
            "cards_published": published, "tournaments": tournaments,
            "decks": payload.get("decks"), "documents": payload.get("documents"),
            "window": payload.get("window"),
            "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"]}


def card_topdeck(store: Store, oracle_id: str) -> dict:
    """One card's self-computed TopDeck tournament figures from the
    latest snapshot. A card below the minimum sample is listed with
    its counts and NULL rates (an honest 'sample too small', never a
    made-up number); a card in no stored deck is ``listed: False``."""
    snap = latest_snapshot(store, SOURCE_NAME, KIND)
    if snap is None:
        return {"status": "NOT_FETCHED", "listed": False,
                "conversion_rate": None, "win_rate": None,
                "attribution": ATTRIBUTION, "attribution_url": ATTRIBUTION_URL}
    payload = json.loads(snap["payload_json"]) if snap["payload_json"] else {}
    row = store.conn.execute(
        "SELECT card_name, decks_with, decks_in_cut, top_cut_decks, "
        "conversion_rate, wins, draws, losses, games, win_rate FROM "
        "topdeck_card_stat WHERE snapshot_id=? AND card_oracle_id=?",
        (snap["snapshot_id"], oracle_id)).fetchone()
    if row is None:
        return {"status": snap["status"], "listed": False,
                "conversion_rate": None, "win_rate": None,
                "snapshot_id": snap["snapshot_id"],
                "fetched_at": snap["fetched_at"],
                "window": payload.get("window"),
                "attribution": ATTRIBUTION,
                "attribution_url": ATTRIBUTION_URL}
    return {"status": snap["status"], "listed": True,
            "card_name": row["card_name"],
            "decks_with": row["decks_with"],
            "decks_in_cut": row["decks_in_cut"],
            "top_cut_decks": row["top_cut_decks"],
            "conversion_rate": row["conversion_rate"],
            "wins": row["wins"], "draws": row["draws"],
            "losses": row["losses"], "games": row["games"],
            "win_rate": row["win_rate"],
            "snapshot_id": snap["snapshot_id"],
            "fetched_at": snap["fetched_at"],
            "window": payload.get("window"),
            "label": "Turniere (TopDeck.gg), Conversion + Win-Rate "
                     "lokal aus den Turnierlisten berechnet",
            "attribution": ATTRIBUTION,
            "attribution_url": ATTRIBUTION_URL}
