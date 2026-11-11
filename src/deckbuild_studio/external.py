"""Phase-2 scaffold for EDHREC / Playgroup sync — job/status bookkeeping ONLY.

No external fetching happens in Phase 1 and no data is invented: every job
starts as NOT_FETCHED. Phase 2 plugs real adapters into these job types:
  * EDHREC: 6 snapshots per commander — {core,upgraded,optimized} x
    {stats page, /decks page}; brackets Core=2, Upgraded=3, Optimized=4,
    cohorts never mixed.
  * Playgroup: commander profile (numeric id must be resolved from a real
    source, e.g. the public JSON linked on the commander page) and the
    Card Atlas (one job per collection identity, coverage report expected).
"""
from __future__ import annotations

import hashlib

from .store import Store, utcnow

BRACKETS = {"core": 2, "upgraded": 3, "optimized": 4}


def _job_id(*parts: str) -> str:
    return "job-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]


def register_commander_jobs(store: Store, commander_oracle_id: str, slug: str | None = None) -> int:
    """Create the 6 EDHREC jobs + 1 Playgroup commander job as NOT_FETCHED."""
    n = 0
    for bracket, level in BRACKETS.items():
        for view in ("stats", "decks"):
            url = f"https://edhrec.com/commanders/{slug}/{bracket}" + ("/decks" if view == "decks" else "")
            jid = _job_id("edhrec", commander_oracle_id, bracket, view)
            store.conn.execute(
                "INSERT OR IGNORE INTO sync_job(job_id,job_type,commander_oracle_id,bracket,"
                "bracket_level,target_url,status,detail,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (jid, f"edhrec_{view}", commander_oracle_id, bracket, level,
                 url if slug else None, "NOT_FETCHED",
                 "slug unresolved" if not slug else "phase 2: not fetched yet", utcnow()))
            n += 1
    jid = _job_id("playgroup_commander", commander_oracle_id)
    store.conn.execute(
        "INSERT OR IGNORE INTO sync_job(job_id,job_type,commander_oracle_id,status,detail,updated_at)"
        " VALUES(?,?,?,?,?,?)",
        (jid, "playgroup_commander", commander_oracle_id, "NOT_FETCHED",
         "numeric Playgroup id unresolved; must be resolved from a real source (phase 2)",
         utcnow()))
    store.conn.commit()
    return n + 1


def register_card_atlas_jobs(store: Store, collection_id: str) -> int:
    rows = store.conn.execute(
        "SELECT DISTINCT oracle_id FROM physical_lot WHERE collection_id=?",
        (collection_id,)).fetchall()
    for r in rows:
        jid = _job_id("playgroup_card", r["oracle_id"])
        store.conn.execute(
            "INSERT OR IGNORE INTO sync_job(job_id,job_type,oracle_id,status,detail,updated_at)"
            " VALUES(?,?,?,?,?,?)",
            (jid, "playgroup_card_atlas", r["oracle_id"], "NOT_FETCHED",
             "phase 2: not fetched yet", utcnow()))
    store.conn.commit()
    return len(rows)
