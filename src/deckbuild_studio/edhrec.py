"""EDHREC adapter — parses the data EDHREC publicly ships inside its pages.

Verified 2026-11-11 against https://edhrec.com/commanders/tatyova-benthic-druid/core
(and /core/decks): the pages are Next.js (RSC) documents. The recommendation
data is embedded in the RSC payload as escaped JSON:

  * ``"gallery"``: {categories: [{label, slug}], paginationTotal,
    recs: [{category, name, cardId (slug), scryfallId, inclusion (fraction),
    numDecks, potentialDecks, synergy, lift, trendZscore}]}
  * ``"featured"``: {rec: {name, cardId, numDecks, rank}} — used to VERIFY
    that the fetched page really is the requested commander.
  * ``"optionsFilters"``: {brackets: [{bracket, count}], tags, budgets} —
    bracket counts are the cohort sizes; cohorts are never mixed.
  * decks pages embed ``"decks"``: [{urlhash, savedate, price, salt, tags,
    type counts}] — deck METADATA only; no full deck compositions are in
    the payload, and none are claimed.

Definitions as shipped by EDHREC in the payload: ``inclusion`` is the
fraction numDecks/potentialDecks for this bracket cohort; ``synergy`` and
``lift`` are stored verbatim as EDHREC computes them (EDHREC defines
synergy as the inclusion difference vs. other decks of the same colour
identity); we never recompute or reinterpret them. ``paginationTotal`` was
``$undefined`` in the verified payload, so gallery coverage total is
reported as unknown rather than guessed.
"""
from __future__ import annotations

import json
import math

PARSER_ID = "edhrec-rsc/2.2.0"  # 2.1.0: fail-closed card-stat validation,
# adopted 2026-11-11 from commander-playtest-lab #1196 (capture-proof
# checks). 2.2.0: inclusion must agree with numDecks/potentialDecks
# (QA round 2, PR #5) — a self-contradictory fraction is dropped like
# every other invalid stat, never stored as an unflagged fact. Additive:
# valid snapshots stored by earlier versions stay valid; the shared
# snapshot parser version (external.py) is unchanged.

# EDHREC ships ``inclusion`` rounded; honest payloads agree with the raw
# counts to well within a percentage point. Two points of tolerance
# absorb rounding/window noise while still catching real contradictions
# (e.g. a stated 90% against raw counts of 5/10 = 50%).
INCLUSION_TOLERANCE = 0.02


def _invalid_stat(rec: dict) -> bool:
    """A gallery rec is unusable when its counts contradict themselves:
    negative or non-numeric counts, numerator above denominator, a
    non-finite/non-numeric synergy/lift, or an ``inclusion`` fraction
    that disagrees with its own numDecks/potentialDecks beyond rounding
    tolerance (inclusion is DEFINED as that fraction — a contradiction
    means at least one of the numbers is not what it claims to be).
    Such rows are dropped and counted (``dropped_invalid``), never
    stored as facts."""
    for key in ("numDecks", "potentialDecks"):
        value = rec.get(key)
        if value is not None and (isinstance(value, bool)
                                  or not isinstance(value, (int, float))
                                  or value < 0):
            return True
    num, potential = rec.get("numDecks"), rec.get("potentialDecks")
    if isinstance(num, (int, float)) and isinstance(potential, (int, float)) \
            and num > potential:
        return True
    for key in ("synergy", "lift"):
        value = rec.get(key)
        if value is not None and (isinstance(value, bool)
                                  or not isinstance(value, (int, float))
                                  or not math.isfinite(value)):
            return True
    inclusion = rec.get("inclusion")
    if inclusion is not None:
        if isinstance(inclusion, bool) or not isinstance(inclusion, (int, float)) \
                or not math.isfinite(inclusion) or not 0 <= inclusion <= 1:
            return True
        if isinstance(num, (int, float)) and isinstance(potential, (int, float)) \
                and potential > 0:
            if abs(inclusion - num / potential) > INCLUSION_TOLERANCE:
                return True
    return False


class ParseError(Exception):
    pass


class VerificationError(Exception):
    """The fetched page is not the commander we asked for."""


def _unescape_rsc(html_text: str) -> str:
    return (html_text.replace("\\\\", "\x00")
            .replace('\\"', '"')
            .replace("\x00", "\\"))


def _extract(text: str, marker: str):
    idx = text.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    while start < len(text) and text[start] in " \t\r\n":
        start += 1  # raw_decode does not skip leading whitespace at idx
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
        return obj
    except (json.JSONDecodeError, ValueError):
        return None


def _verify(featured: dict | None, expected_name: str, expected_slug: str) -> dict:
    rec = (featured or {}).get("rec") or {}
    name = rec.get("name")
    card_id = rec.get("cardId")
    if not name:
        raise VerificationError("page carries no featured commander record")
    front = expected_name.split(" // ")[0]
    if name not in (expected_name, front) and card_id != expected_slug:
        raise VerificationError(
            f"slug verification failed: page is for {name!r} (cardId={card_id!r}), "
            f"expected {expected_name!r} / {expected_slug!r}")
    return rec


def _bracket_counts(options: dict | None) -> dict[str, int]:
    out: dict[str, int] = {}
    for entry in (options or {}).get("brackets") or []:
        if isinstance(entry, dict) and entry.get("bracket") and isinstance(entry.get("count"), int):
            out[entry["bracket"]] = entry["count"]
    return out


def parse_stats_page(html_text: str, *, expected_name: str, expected_slug: str,
                     bracket: str) -> dict:
    text = _unescape_rsc(html_text)
    gallery = _extract(text, '"gallery":')
    if not isinstance(gallery, dict) or not isinstance(gallery.get("recs"), list):
        raise ParseError("no gallery/recs payload found in EDHREC page")
    featured = _extract(text, '"featured":')
    commander = _verify(featured, expected_name, expected_slug)
    options = _extract(text, '"optionsFilters":') or {}
    counts = _bracket_counts(options)
    categories = {c.get("slug"): c.get("label")
                  for c in gallery.get("categories") or [] if isinstance(c, dict)}
    cards = []
    dropped_invalid = 0
    for rec in gallery["recs"]:
        if not isinstance(rec, dict) or not rec.get("name"):
            continue
        if _invalid_stat(rec):
            dropped_invalid += 1
            continue
        potential = rec.get("potentialDecks")
        num = rec.get("numDecks")
        inclusion = rec.get("inclusion")
        if not potential:  # never invent a denominator; 0/None -> unknown inclusion
            inclusion = None
        cards.append({
            "category": rec.get("category"), "name": rec.get("name"),
            "card_slug": rec.get("cardId"), "scryfall_id": rec.get("scryfallId"),
            "inclusion": inclusion, "num_decks": num, "potential_decks": potential,
            "synergy": rec.get("synergy"), "lift": rec.get("lift"),
            "trend_zscore": rec.get("trendZscore"),
        })
    pagination_total = gallery.get("paginationTotal")
    return {
        "commander": {"name": commander.get("name"), "card_slug": commander.get("cardId"),
                      "rank": commander.get("rank"), "num_decks_featured": commander.get("numDecks")},
        "bracket": bracket,
        "cohort_decks": counts.get(bracket),
        "bracket_counts_all": counts,
        "tags": options.get("tags") or [],
        "budgets": options.get("budgets") or [],
        "categories": categories,
        "cards": cards,
        "dropped_invalid": dropped_invalid,
        "captured_count": len(cards),
        "displayed_total": pagination_total if isinstance(pagination_total, int) else None,
        "coverage_status": "TOTAL_KNOWN" if isinstance(pagination_total, int) else "TOTAL_UNKNOWN",
    }


def parse_decks_page(html_text: str, *, expected_name: str, expected_slug: str,
                     bracket: str) -> dict:
    text = _unescape_rsc(html_text)
    decks = _extract(text, '"decks":')
    if not isinstance(decks, list):
        raise ParseError("no decks array found in EDHREC decks page")
    featured = _extract(text, '"featured":')
    commander = _verify(featured, expected_name, expected_slug)
    options = _extract(text, '"optionsFilters":') or {}
    counts = _bracket_counts(options)
    total = counts.get(bracket)
    entries = []
    seen: set[str] = set()
    type_keys = ("creatures", "instants", "sorceries", "artifacts", "enchantments",
                 "planeswalkers", "battles", "lands")
    for d in decks:
        if not isinstance(d, dict) or not d.get("urlhash") or d["urlhash"] in seen:
            continue
        seen.add(d["urlhash"])
        entries.append({
            "urlhash": d["urlhash"], "savedate": d.get("savedate"),
            "price": d.get("price"), "salt": d.get("salt"),
            "tags": d.get("tags") or [],
            "type_counts": {k: d.get(k) for k in type_keys if d.get(k) is not None},
        })
    captured = len(entries)
    coverage = ("COMPLETE_METADATA" if total is not None and captured >= total
                else "PARTIAL" if total is not None else "TOTAL_UNKNOWN")
    return {
        "commander": {"name": commander.get("name"), "card_slug": commander.get("cardId")},
        "bracket": bracket, "cohort_decks": total,
        "entries": entries, "captured_count": captured,
        "displayed_total": total, "coverage_status": coverage,
        "note": "deck metadata only (date, price, salt, tags, type counts); "
                "the public payload contains no full deck compositions",
    }
