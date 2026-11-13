"""Commander Spellbook adapter — combo data via the public website.

Access audit, verified 2026-11-11:

  * ``backend.commanderspellbook.com`` (the REST API) serves a
    robots.txt of ``User-agent: * / Disallow: /`` — automated API
    access is BLOCKED for this tool and is not used; there is no
    bypass, no key, no mirror.
  * ``commanderspellbook.com`` (the public website) serves
    ``User-agent: * / Allow: /`` plus sitemaps. Its pages are
    server-rendered Next.js documents whose ``__NEXT_DATA__`` payload
    embeds the data — the same public-payload pattern as the EDHREC
    adapter. Only those pages are fetched, politely (honest user
    agent, >= 1 s per host, manual sync only, GET only).

Two page types carry per-card combo data:

  * Card pages (``/card/{spellbook_id}/``) are the authoritative
    source: they publish the card, its EXACT commander-legal combo
    total (``combosCount``), the top combos by popularity and its top
    combo partners (``partners``: card + shared-combo count). Only a
    page of combos is embedded server-side; the rest loads client-side
    from the (blocked) backend, so the combo LIST from a card page is
    partial by construction — the total never is.
  * Search pages (``/search/?q="Card Name"``) paginate at 50 combos
    with no published total. Their explanation string states the
    semantics: "Combos that use a card with "Card Name" in the name
    and are legal in Commander" — a SUBSTRING match, so every shipped
    combo is re-verified client-side (the card's full name — or, for
    '//' cards, its front name — must appear verbatim in the combo's
    ``uses``; Spellbook ships '//' cards under their full name there).
    For some cards the site
    answers a search with a 307 redirect to ONE combo detail page
    instead of a result list (verified for e.g. Act of Treason); that
    page is used only to learn the card's spellbook id, never as a
    result set.

Combo facts kept per combo: the spellbook combo id, the cards it uses
(names + Scryfall oracle ids, as shipped), the result features it
``produces`` (e.g. "Infinite colorless mana"), the combo's total
Cardmarket (EUR) / Card Kingdom (USD) prices as printed, its
popularity (deck count as shipped) and the mana value needed.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote_plus

from .edhrec import ParseError, VerificationError
from .store import Store

SOURCE_NAME = "commanderspellbook"
KIND = "spellbook_card"

PARSER_ID = "spellbook-ssr/1.2.0"  # 1.2.0: combo uses match the FULL
# oracle name as well as the front name — Spellbook ships '//' cards
# under their full name in combo uses (live-verified 2026-11-12 with
# 'Fable of the Mirror-Breaker // Reflection of Kiki-Jiki': 38 combos
# on the search page, 1.1.0 accepted 0 and found no spellbook id, so
# every '//' card was falsely NOT_FOUND). 1.1.0: card pages + redirect
# handling.
PAGE_SIZE = 50

_NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
_EXPLANATION = re.compile(r"with “(.+?)” in the name")

__all__ = ["PARSER_ID", "PAGE_SIZE", "ParseError", "VerificationError",
           "search_url", "card_url", "payload_page", "parse_search_page",
           "parse_combo_page", "parse_card_page", "spellbook_coverage"]


def search_url(card_name: str, page: int = 1) -> str:
    front = card_name.split(" // ")[0]
    url = f"https://commanderspellbook.com/search/?q={quote_plus(chr(34) + front + chr(34))}"
    if page > 1:
        url += f"&page={page}"
    return url


def card_url(spellbook_card_id: int) -> str:
    return f"https://commanderspellbook.com/card/{spellbook_card_id}/"


def _next_data(html_text: str) -> dict:
    match = _NEXT_DATA.search(html_text)
    if match is None:
        raise ParseError("no __NEXT_DATA__ payload in spellbook page")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ParseError(f"spellbook __NEXT_DATA__ invalid: {exc}") from exc


def payload_page(html_text: str) -> str | None:
    """The Next.js route of a spellbook page ('/search', '/combo/[id]',
    '/card/[id]') — used to tell a search result list apart from the
    combo-detail redirect some searches answer with. Falls back to the
    pageProps shape when the route field is absent."""
    try:
        data = _next_data(html_text)
    except ParseError:
        return None
    if data.get("page"):
        return data["page"]
    page_props = ((data.get("props") or {}).get("pageProps") or {})
    if "explanation" in page_props:
        return "/search"
    if "combo" in page_props:
        return "/combo/[id]"
    if "card" in page_props:
        return "/card/[id]"
    return None


def _price(raw) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _combo_view(raw: dict, card_name: str) -> dict | None:
    """Normalise one shipped combo; None when it does not actually use
    the requested card or is not legal in Commander. A '//' card is
    used when its FULL name appears in the combo's uses (the form
    Spellbook ships); the front name alone also counts."""
    legalities = raw.get("legalities") or {}
    if legalities and legalities.get("commander") is not True:
        return None
    uses = raw.get("uses") or []
    cards = [(u.get("card") or {}) for u in uses]
    names = [c.get("name") for c in cards]
    front = card_name.split(" // ")[0]
    if card_name not in names and front not in names:
        return None
    produces = []
    for item in raw.get("produces") or []:
        feature = (item.get("feature") or {}).get("name")
        if feature:
            produces.append(feature)
    prices = raw.get("prices") or {}
    return {
        "combo_id": raw.get("id"),
        "card_names": names,
        "card_oracle_ids": [c.get("oracleId") for c in cards],
        "card_spellbook_ids": [c.get("id") for c in cards],
        "produces": produces,
        "price_eur": _price(prices.get("cardmarket")),
        "price_usd": _price(prices.get("cardkingdom")),
        "popularity": raw.get("popularity"),
        "mana_value_needed": raw.get("manaValueNeeded"),
        "identity": raw.get("identity"),
        "variant_count": raw.get("variantCount"),
    }


def _spellbook_id_for(view: dict, card_name: str) -> int | None:
    front = card_name.split(" // ")[0]
    for name, sid in zip(view["card_names"], view["card_spellbook_ids"]):
        if name in (card_name, front) and isinstance(sid, int):
            return sid
    return None


def parse_search_page(html_text: str, *, card_name: str) -> dict:
    """Parse one server-rendered Spellbook search page. Verifies via the
    page's own explanation string that the page answers the requested
    card; every combo is additionally filtered to exact ``uses``."""
    data = _next_data(html_text)
    page_props = ((data.get("props") or {}).get("pageProps") or {})
    explanation = page_props.get("explanation") or ""
    named = _EXPLANATION.search(explanation)
    front = card_name.split(" // ")[0]
    if named is None:
        raise ParseError(f"unexpected spellbook explanation: {explanation!r}")
    if named.group(1) != front:
        raise VerificationError(
            f"spellbook page is about {named.group(1)!r}, not {front!r}")
    raw_combos = page_props.get("combos") or []
    combos = []
    spellbook_id: int | None = None
    for raw in raw_combos:
        view = _combo_view(raw, card_name)
        if view is not None:
            combos.append(view)
            if spellbook_id is None:
                spellbook_id = _spellbook_id_for(view, card_name)
    return {
        "page": page_props.get("page"),
        "explanation": explanation,
        "raw_count": len(raw_combos),
        "combos": combos,
        "spellbook_card_id": spellbook_id,
        "parser": PARSER_ID,
    }


def parse_combo_page(html_text: str, *, card_name: str) -> dict:
    """Parse a combo DETAIL page (the redirect target some searches
    answer with). Returns the single combo (when it uses the card) and
    the card's spellbook id — discovery evidence, not a result set."""
    data = _next_data(html_text)
    page_props = ((data.get("props") or {}).get("pageProps") or {})
    raw = page_props.get("combo")
    if not isinstance(raw, dict):
        raise ParseError("no combo object in spellbook combo page")
    view = _combo_view(raw, card_name)
    return {
        "combo": view,
        "spellbook_card_id": _spellbook_id_for(view, card_name) if view else None,
        "parser": PARSER_ID,
    }


def parse_card_page(html_text: str, *, card_name: str) -> dict:
    """Parse a Spellbook card page: exact combo total, embedded top
    combos and top partners for one card (commander-legal view, as
    shipped: pageProps.formatTerm == 'legal:commander')."""
    data = _next_data(html_text)
    page_props = ((data.get("props") or {}).get("pageProps") or {})
    card = page_props.get("card") or {}
    front = card_name.split(" // ")[0]
    if card.get("name") not in (card_name, front):
        raise VerificationError(
            f"spellbook card page is about {card.get('name')!r}, "
            f"not {card_name!r}")
    combos = []
    for raw in page_props.get("combos") or []:
        view = _combo_view(raw, card_name)
        if view is not None:
            combos.append(view)
    partners = []
    for entry in page_props.get("partners") or []:
        partner_card = entry.get("card") or {}
        if partner_card.get("name"):
            partners.append({
                "name": partner_card["name"],
                "oracle_id": partner_card.get("oracleId"),
                "spellbook_id": partner_card.get("id"),
                "shared_combos": entry.get("count"),
            })
    total = page_props.get("combosCount")
    return {
        "spellbook_card_id": card.get("id"),
        "oracle_id": card.get("oracleId"),
        "combos_total": total if isinstance(total, int) else None,
        "combos": combos,
        "partners": partners,
        "parser": PARSER_ID,
    }


def spellbook_coverage(store: Store, collection_id: str) -> dict:
    """Collection coverage of the Commander Spellbook layer.

    Spellbook snapshots are PER CARD (source 'commanderspellbook',
    kind 'spellbook_card'); a card's facts live in its LATEST
    snapshot — the same rule the tier list's combo signal applies
    (older snapshots are history and never counted). Combo counts
    therefore read the rows of ``spellbook_combo`` stored under each
    collection identity's latest snapshot: ``cards_with_combos``
    counts the identities whose latest snapshot stores >= 1 combo
    row, ``combos_total`` counts those rows (a combo shared by two
    fetched cards is stored once per card snapshot and counts once
    per storing card — the stored-row count of the layer).

    The roll-up ``status`` is NOT_FETCHED until at least one
    collection card was attempted; AVAILABLE when every attempted
    card reached a definitive answer (AVAILABLE or NOT_FOUND — a
    card Spellbook does not know is an answer, not a gap); PARTIAL
    while any attempted card's latest snapshot is PARTIAL/BLOCKED.
    The exact per-status counts travel in ``by_status``.
    """
    c = store.conn
    total = c.execute(
        "SELECT COUNT(DISTINCT oracle_id) n FROM physical_lot "
        "WHERE collection_id=?", (collection_id,)).fetchone()["n"]
    latest = c.execute(
        "SELECT s.snapshot_id, s.status, s.fetched_at "
        "FROM external_snapshot s "
        "WHERE s.source_name=? AND s.kind=? AND s.oracle_id IN "
        "(SELECT DISTINCT oracle_id FROM physical_lot "
        "WHERE collection_id=?) "
        "AND NOT EXISTS (SELECT 1 FROM external_snapshot t "
        "WHERE t.source_name=s.source_name AND t.kind=s.kind "
        "AND t.oracle_id IS s.oracle_id "
        "AND (t.fetched_at > s.fetched_at OR "
        "(t.fetched_at = s.fetched_at "
        "AND t.snapshot_id > s.snapshot_id)))",
        (SOURCE_NAME, KIND, collection_id)).fetchall()
    by_status: dict[str, int] = {}
    for row in latest:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    attempted = len(latest)
    cards_with_combos = 0
    combos_total = 0
    if latest:
        marks = ",".join("?" for _ in latest)
        row = c.execute(
            f"SELECT COUNT(DISTINCT snapshot_id) cards, COUNT(*) combos "
            f"FROM spellbook_combo WHERE snapshot_id IN ({marks})",
            [r["snapshot_id"] for r in latest]).fetchone()
        cards_with_combos = row["cards"]
        combos_total = row["combos"]
    if not attempted:
        status = "NOT_FETCHED"
    elif all(s in ("AVAILABLE", "NOT_FOUND") for s in by_status):
        status = "AVAILABLE"
    else:
        status = "PARTIAL"
    return {"collection_id": collection_id, "total_identities": total,
            "status": status, "attempted": attempted,
            "by_status": by_status,
            "cards_with_combos": cards_with_combos,
            "combos_total": combos_total,
            "fetched_at": max((r["fetched_at"] for r in latest),
                               default=None)}
