"""Playgroup.gg adapter — public JSON + server-rendered Card Atlas pages.

Verified 2026-11-11:
  * Commander pages link an official public JSON, e.g.
    ``/api/public/v1/commanders/2143.json`` for Chulane. It carries id,
    name, playgroup_url, cached_elo, global_rank, a ``stats`` object
    (games/won/lost/win_rate/decks_count/averages), ``graphs``
    (elo history, weekly games) and ``top_decks``. Fields the JSON does
    not offer (archetypes, matchups, seat/mulligan breakdowns, win
    conditions) are NOT invented — they are absent, and the snapshot
    detail says so.
  * The numeric commander id is resolved ONLY through Playgroup's own
    autocomplete endpoint used by its search box
    (``/api/v1/commanders?link=true&q=<name>``), matching the returned
    label EXACTLY against the card name. No id is ever guessed.
  * Card Atlas pages (``/cards/{slug}``) are server-rendered HTML with
    labelled live-telemetry stats. Playgroup itself states on the page:
    "Read this as correlation, not as the card's contribution" — all
    win-rate gaps stored here are OBSERVED CORRELATIONS from Playgroup
    Live games, never causal card effects. Thresholds stated on the page:
    play counts appear at >= 100 tracked games; full charts need >= 25
    observed games not dominated by a single pilot.
  * The commander HTML page (the ``playgroup_url`` the JSON links)
    publishes MORE than the JSON, verified 2026-11-11 on the Chulane
    page: a win-condition breakdown ("How does this commander win?"),
    win rate by seat position and by mulligan count (each with its
    sample size), best/worst matchups (opposing commanders with >= 10
    tracked games; Playgroup itself flags pairs under 25 games as
    "suggestive, not statistical"), and "Staples that win games" — a
    per-card win-rate lift table within this commander. Those sections
    are parsed by :func:`parse_commander_page`. Still absent: per-
    commander archetype data (the site has an archetype SEARCH, no
    per-commander archetype stats). The page's player-rating section
    is subjective and deliberately not captured.
"""
from __future__ import annotations

import html as html_mod
import json
import re

PARSER_ID = "playgroup/2.2.0"  # 2.2.0: cast-turn footer in the live
# segment format (float median, no middot after it) — the 2.1.0 pattern
# matched 0 of 1,227 stored real pages (verified offline 2026-11-12);
# commander-page title check accepts the exact H1 segment because the
# site truncates long commander names inside <title> (verified live
# 2026-11-12, "Molten Man, Inferno Incarnate").
# 2.1.0: quality warnings + JSON-LD dataset provenance, adopted
# 2026-11-11 from commander-playtest-lab #1202 (playgroup_parser.py).
# Additive only: snapshots stored by 2.0.0 stay valid; the shared
# snapshot parser version (external.py) is unchanged.
SMALL_SAMPLE_THRESHOLD = 25  # per Playgroup's own FAQ on the card page
COMMANDER_PAGE_PARSER_ID = "playgroup-commander-page/1.1.0"  # 1.1.0:
# heading window widened to the measured H1 position (segment 15 on
# all 63 stored pages; the 1.0.0 window of 8 never reached it when the
# <title> was truncated) and win-staple rows tolerate decorative badge
# segments between name and stats ('Signature build', Bre of Clan
# Stoutarm — 1.0.0 silently extracted 0 of 2 staples there).


class ParseError(Exception):
    pass


def parse_autocomplete(fragment: str, expected_name: str) -> dict | None:
    """Exact-label match in Playgroup's autocomplete response fragment."""
    candidates = re.findall(
        r"data-autocomplete-label='([^']*)'\s+data-autocomplete-value='([^']*)'", fragment)
    if not candidates:  # tolerate double-quoted variant
        candidates = re.findall(
            r'data-autocomplete-label="([^"]*)"\s+data-autocomplete-value="([^"]*)"', fragment)
    front = expected_name.split(" // ")[0]
    for label, value in candidates:
        label = html_mod.unescape(label)
        if label in (expected_name, front):
            m = re.match(r"/commanders/(\d+)-(.+)$", value.strip())
            if m:
                return {"playgroup_id": int(m.group(1)), "slug": m.group(2),
                        "label": label,
                        "url": f"https://playgroup.gg/commanders/{m.group(1)}-{m.group(2)}"}
    return None


def parse_commander_json(text: str, *, expected_name: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"commander JSON invalid: {exc}") from exc
    name = data.get("name")
    front = expected_name.split(" // ")[0]
    if name not in (expected_name, front):
        raise ParseError(f"commander JSON name mismatch: {name!r} != {expected_name!r}")
    stats = data.get("stats") or {}
    return {
        "playgroup_id": data.get("id"), "name": name,
        "playgroup_url": data.get("playgroup_url"),
        "elo": data.get("cached_elo"), "global_rank": data.get("global_rank"),
        "stats": stats,
        "sample_size": stats.get("games_count"),
        "top_decks": data.get("top_decks") or [],
        "graphs_summary": {
            "elo_points": len((data.get("graphs") or {}).get("elo_rating") or []),
            "weekly_buckets": len((data.get("graphs") or {}).get("weekly_games_played") or {}),
        },
        "absent_from_public_json": ["archetypes", "matchups", "win_conditions",
                                    "seat_breakdown", "mulligan_breakdown", "players_count"],
    }


def _dataset_ld(html_text: str) -> dict:
    """JSON-LD ``Dataset`` block of the card page (identifier, dates,
    temporal coverage, license) — provenance as published by Playgroup
    itself. Adopted from commander-playtest-lab #1202."""
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            html_text, flags=re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Dataset":
            out: dict[str, str] = {}
            for key, src in (("identifier", "identifier"),
                             ("date_modified", "dateModified"),
                             ("temporal_coverage", "temporalCoverage"),
                             ("license", "license")):
                if data.get(src):
                    out[key] = str(data[src])
            return out
    return {}


def _segments(html_text: str) -> list[str]:
    body = re.sub(r"<script.*?</script>", " ", html_text, flags=re.S | re.I)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S | re.I)
    parts = re.split(r"<[^>]+>", body)
    return [html_mod.unescape(p).strip() for p in parts if p and p.strip()]


def _num(raw: str):
    raw = raw.replace(",", "").strip()
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return None


def _after(segs: list[str], label: str):
    for i, seg in enumerate(segs):
        if seg == label and i + 1 < len(segs):
            return segs[i + 1]
    return None


def parse_card_page(html_text: str, *, expected_name: str) -> dict:
    segs = _segments(html_text)
    joined = " ".join(segs)
    fields: dict[str, object] = {}
    if expected_name not in joined and expected_name.split(" // ")[0] not in joined:
        raise ParseError(f"card page does not mention {expected_name!r}")
    for label, key in (("Times Brought", "times_brought"),
                       ("Decks Running", "decks_running"),
                       ("Median Cast Turn", "median_cast_turn"),
                       ("Drawn → Played", "drawn_to_played_pct")):
        raw = _after(segs, label)
        if raw is not None:
            fields[key] = _num(raw.rstrip("%")) if raw else None
    for i, seg in enumerate(segs):
        if seg == "Live Inclusion" and i > 0 and segs[i - 1].endswith("%"):
            fields["live_inclusion_pct"] = _num(segs[i - 1].rstrip("%"))
    m = re.search(r"First-cast turn\s+n=([\d,]+)", joined)
    if m:
        fields["first_cast_n"] = _num(m.group(1))
        dist: dict[str, float] = {}
        for i, seg in enumerate(segs):
            if re.fullmatch(r"T\d+(?:-\d+|\+)?", seg) and i > 0 and segs[i - 1].endswith("%"):
                val = _num(segs[i - 1].rstrip("%"))
                if val is not None:
                    dist[seg] = val  # type: ignore[assignment]
        if dist:
            fields["first_cast_distribution_pct"] = dist
    # Cast-turn footer as rendered live (2026-11-12): "Median 7.5
    # P25 6 · P75 9 · max 12" — float median, middot only before P75
    # and max. The older segment shape "Median 3 · P25 1 · P75 6 ·
    # max 41" (test fixture) stays accepted via the optional middot.
    m = re.search(r"Median\s+([\d.]+)\s+·?\s*P25\s+(\d+)\s+·\s+P75\s+(\d+)"
                  r"\s+·\s+max\s+(\d+)", joined)
    if m:
        fields["cast_turn_median"] = _num(m.group(1))
        fields["cast_turn_p25"] = int(m.group(2))
        fields["cast_turn_p75"] = int(m.group(3))
        fields["cast_turn_max"] = int(m.group(4))
    m = re.search(r"On curve\s+([\d.]+)%\s+\((\d+)\s*/\s*(\d+)\s+cast on T(\d+)\)", joined)
    if m:
        fields["on_curve"] = {"pct": float(m.group(1)), "numerator": int(m.group(2)),
                              "denominator": int(m.group(3)), "turn": int(m.group(4)),
                              "definition_as_labelled_on_page": "cast on the stated turn"}
    m = re.search(r"Cast same turn as drawn\s+([\d.]+)%", joined)
    if m:
        fields["cast_same_turn_as_drawn_pct"] = float(m.group(1))
    funnel: dict[str, object] = {}
    for label, key in (("Brought to game", "brought"), ("Ever drawn", "ever_drawn"),
                       ("Reached battlefield", "reached_battlefield"),
                       ("Still on board at game end", "still_on_board_at_game_end")):
        raw = _after(segs, label)
        if raw is not None:
            funnel[key] = _num(raw)
    m = re.search(r"([\d,]+)\s+brought\s+·\s+([\d,]+)\s+players", joined)
    if m:
        funnel["brought_header"] = _num(m.group(1))
        funnel["players"] = _num(m.group(2))
    if funnel:
        fields["funnel"] = funnel
    win: dict[str, object] = {}
    m = re.search(r"Players who cast this card win\s+([\d.]+)%\s+of the time\s+\(n=([\d,]+)\)"
                  r".{0,12}vs\s+([\d.]+)%\s+when it never left the library\s+\(n=([\d,]+)\)",
                  joined)
    if m:
        win = {"win_rate_cast_pct": float(m.group(1)), "n_cast": _num(m.group(2)),
               "win_rate_never_drawn_pct": float(m.group(3)), "n_never_drawn": _num(m.group(4)),
               "interpretation": "observed correlation in Playgroup Live games, "
                                 "NOT a causal card effect (per Playgroup's own note)"}
    m = re.search(r"left it in hand, they won\s+([\d.]+)%\s+\(n=([\d,]+)\)", joined)
    if m and win:
        win["win_rate_drawn_in_hand_pct"] = float(m.group(1))
        win["n_drawn_in_hand"] = _num(m.group(2))
    m = re.search(r"Observed gap\s+([+-]?[\d.]+)pp;\s+95% confidence interval\s+"
                  r"([+-]?[\d.]+)pp to\s+([+-]?[\d.]+)pp", joined)
    if m and win:
        win["observed_gap_pp"] = float(m.group(1))
        win["ci95_pp"] = [float(m.group(2)), float(m.group(3))]
    if win:
        fields["win_rates_observed"] = win
    for i, seg in enumerate(segs):
        if seg == "Final zone distribution" and i + 1 < len(segs):
            m = re.match(r"([\d,]+) instances", segs[i + 1])
            if m:
                zones: dict[str, object] = {"instances": _num(m.group(1))}
                dist: dict[str, float] = {}
                for j in range(i + 2, min(i + 30, len(segs) - 1)):
                    if segs[j].endswith("%") and segs[j + 1] in (
                            "Library", "Battlefield", "Graveyard", "Exile", "Hand",
                            "Command Zone", "Stack"):
                        val = _num(segs[j].rstrip("%"))
                        if val is not None:
                            dist[segs[j + 1]] = val  # type: ignore[assignment]
                zones["distribution_pct"] = dist
                fields["final_zone_distribution"] = zones
            break
    for i, seg in enumerate(segs):
        if seg == "Commanders that played this card":
            tops = []
            j = i + 1
            while j < len(segs) and len(tops) < 10:
                m = re.fullmatch(r"([\d,]+) decks", segs[j])
                if m:
                    name = next((segs[k] for k in range(j - 1, i, -1)
                                 if not segs[k].isdigit()), None)
                    if name:
                        tops.append({"commander": name, "decks": _num(m.group(1))})
                j += 1
            if tops:
                fields["top_commanders_by_decks"] = tops
            break
    # Quality warnings: preserve the exact source numbers, but flag
    # internal inconsistencies instead of silently correcting them
    # (adopted from commander-playtest-lab #1202, playgroup_parser.py).
    warnings: list[str] = []
    oc = fields.get("on_curve")
    if isinstance(oc, dict) and oc.get("denominator"):
        calc = round(100.0 * oc["numerator"] / oc["denominator"], 1)
        if abs(calc - oc["pct"]) > 2.0:
            warnings.append(
                f"On-curve calculation discrepancy: reported {oc['pct']}% but "
                f"{oc['numerator']}/{oc['denominator']} = {calc}%")
    funnel_d = fields.get("funnel")
    brought_header = funnel_d.get("brought_header") if isinstance(funnel_d, dict) else None
    if (fields.get("times_brought") is not None and brought_header is not None
            and fields["times_brought"] != brought_header):
        warnings.append(
            f"Brought count discrepancy: Times Brought = {fields['times_brought']} "
            f"vs Funnel Brought = {brought_header}")
    if warnings:
        fields["quality_warnings"] = warnings
    dataset = _dataset_ld(html_text)
    if dataset:
        fields["dataset"] = dataset
    fields["license"] = dataset.get("license") or "CC BY 4.0"
    fields["attribution"] = "Playgroup.gg"
    fields["semantics"] = ("Playgroup Live per-card gameplay telemetry "
                           "(live tracked games), observed correlation — "
                           "not a causal card effect")
    return fields


# ---------------------------------------------------------------------------
# Commander HTML page (sections the public JSON does not offer)
# ---------------------------------------------------------------------------

_PCT_SEG = re.compile(r"^(\d+(?:\.\d+)?)%$")
_GAMES_SEG = re.compile(r"^(\d+) games$")
_N_SEG = re.compile(r"^n=(\d+)$")
_PP_SEG = re.compile(r"^([+-]?\d+(?:\.\d+)?) pp$")


def parse_commander_page(html_text: str, *, expected_name: str) -> dict:
    """Parse the extra sections of a Playgroup commander page.

    Verified against the real page structure on 2026-11-11 (Chulane):
    labelled segment triples/pairs as rendered by the site. Everything
    here is observed Playgroup Live telemetry — correlation, not a
    causal effect. Sections a page does not render stay empty lists;
    nothing is interpolated."""
    segs = _segments(html_text)
    front = expected_name.split(" // ")[0]
    # The site truncates long commander names inside <title> (live
    # evidence 2026-11-12: "Statistics for Commander 'Molten Man,
    # Inferno | Playgroup.gg" for "Molten Man, Inferno Incarnate"),
    # while the page H1 carries the full name as its own segment.
    # Accept either proof — never a substring of a longer name.
    title_seen = any(s.startswith("Statistics for Commander '")
                     for s in segs[:4])
    named_in_title = any(
        s.startswith("Statistics for Commander '")
        and (expected_name in s or front in s) for s in segs[:4])
    # The H1 sits at segment index 15 on every one of the 63 stored
    # pages (fixed nav block before it); window 40 covers template
    # drift, and a 63x62 cross-check over the stored pages shows no
    # foreign commander name ever appears inside that window.
    named_in_heading = any(s in (expected_name, front) for s in segs[:40])
    title_ok = title_seen and (named_in_title or named_in_heading)
    if not title_ok:
        raise ParseError(
            f"commander page title does not name {expected_name!r}")
    out: dict = {
        "name": front,
        "win_conditions": [],
        "win_conditions_basis": ("share of wins across tracked games "
                                 "with a recorded win condition"),
        "seat_win_rates": [],
        "mulligan_win_rates": [],
        "matchups": {"best": [], "worst": [],
                     "basis": ("opposing commanders with at least ten "
                               "tracked games; pairs under 25 games are "
                               "flagged small_sample (Playgroup: "
                               "'suggestive, not statistical')")},
        "win_staples": [],
        "absent_from_page": [
            "archetypes (site-wide archetype search only; no "
            "per-commander archetype statistics published)",
            "player_ratings (subjective section; deliberately not "
            "captured — not objective telemetry)",
        ],
        "parser": COMMANDER_PAGE_PARSER_ID,
    }
    # Win conditions: label / pct pairs right after the summary sentence.
    for i, seg in enumerate(segs):
        if "of wins come via" in seg:
            j = i + 1
            while j + 1 < len(segs) and len(out["win_conditions"]) < 12:
                label, pct = segs[j], segs[j + 1]
                m = _PCT_SEG.match(pct)
                if (m is None or _PCT_SEG.match(label)
                        or label.startswith("Staples that win games")):
                    break
                out["win_conditions"].append(
                    {"label": label, "pct": float(m.group(1))})
                j += 2
            break
    # Seat positions and mulligan counts: label -> pct -> n= triples.
    for i, seg in enumerate(segs):
        if i + 2 >= len(segs):
            break
        pct = _PCT_SEG.match(segs[i + 1])
        nval = _N_SEG.match(segs[i + 2])
        if pct is None or nval is None:
            continue
        seat = re.fullmatch(r"Seat (\d+)", seg)
        if seat:
            out["seat_win_rates"].append({
                "seat": int(seat.group(1)),
                "win_pct": float(pct.group(1)), "n": int(nval.group(1))})
            continue
        mull = re.fullmatch(r"(\d+) mulligans?", seg)
        if mull:
            out["mulligan_win_rates"].append({
                "mulligans": int(mull.group(1)),
                "win_pct": float(pct.group(1)), "n": int(nval.group(1))})
    # Best / worst matchups: name / "N games" / pct triples.
    for heading, key in (("Top 5 best matchups", "best"),
                         ("Top 5 worst matchups", "worst")):
        if heading not in segs:
            continue
        j = segs.index(heading) + 1
        entries = []
        while j + 2 < len(segs) and len(entries) < 5:
            games = _GAMES_SEG.match(segs[j + 1])
            pct = _PCT_SEG.match(segs[j + 2])
            if games is None or pct is None:
                break
            n = int(games.group(1))
            entries.append({
                "opponent": segs[j], "games": n,
                "win_pct": float(pct.group(1)),
                "small_sample": n < SMALL_SAMPLE_THRESHOLD})
            j += 3
        out["matchups"][key] = entries
    # Win staples: rank / name / "N games" / "+X pp" rows after the
    # table header (the trailing Games column repeats the count).
    # Decorative badge segments (e.g. 'Signature build' on Bre of Clan
    # Stoutarm, both after the name and before the lift) may sit
    # between the name and its stats, so the games and lift segments
    # are located by a bounded forward scan instead of fixed offsets.
    start = next((i for i, s in enumerate(segs)
                  if s.startswith("Staples that win games for")), None)
    if start is not None:
        header = next((i for i in range(start, min(start + 15, len(segs)))
                       if segs[i] == "Games"), None)
        if header is not None:
            j = header + 1
            rank = 1
            rows = []
            while j + 1 < len(segs) and len(rows) < 25:
                if segs[j] != str(rank):
                    break
                g = next((k for k in range(j + 2, min(j + 5, len(segs)))
                          if _GAMES_SEG.match(segs[k])), None)
                if g is None:
                    break
                lift_at = next((k for k in range(g + 1, min(g + 3, len(segs)))
                                if _PP_SEG.match(segs[k])), None)
                if lift_at is None:
                    break
                n = int(_GAMES_SEG.match(segs[g]).group(1))
                rows.append({"rank": rank, "name": segs[j + 1],
                             "games": n,
                             "lift_pp": float(
                                 _PP_SEG.match(segs[lift_at]).group(1))})
                j = lift_at + 1
                if j < len(segs) and segs[j] == str(n):
                    j += 1  # Games column repeats the same count
                rank += 1
            out["win_staples"] = rows
    return out
