"""Issue #31: API reads must not die with HTTP 500 ("database is
locked") while a compute holds a write transaction.

Production shape (QA-2 observation): long compute/import jobs
write in ONE transaction from their first write to the final commit,
so a second process holds the DB write lock for the whole run. Every
API request constructs a fresh Store(), whose init writes briefly
(schema check + schema_version upsert) — with sqlite3's default busy
timeout of 5 s that init write lost against any longer compute and
the read endpoint answered 500. The fix is the central busy timeout
on the Store connection (store.BUSY_TIMEOUT_SECONDS).
"""
from __future__ import annotations

import sqlite3
import threading
import time

from fastapi.testclient import TestClient

from deckbuild_studio import web as web_mod
from deckbuild_studio.store import Store

# Longer than sqlite3's old default busy timeout (5 s), far shorter
# than BUSY_TIMEOUT_SECONDS: a request that starts while the lock is
# held can only succeed by genuinely out-waiting the old default.
HOLD_SECONDS = 7.0


def test_store_connections_carry_busy_timeout(tmp_path):
    with Store(tmp_path / "t.sqlite3") as s:
        (ms,) = s.conn.execute("PRAGMA busy_timeout").fetchone()
    # == store.BUSY_TIMEOUT_SECONDS * 1000; the sqlite3 default is 5000.
    assert ms == 300_000


def test_api_read_survives_held_write_lock(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite3"
    with Store(db_path):
        pass  # schema, built the app's own way
    monkeypatch.setattr(web_mod, "database_path", lambda: db_path)

    # The "compute": a second connection holding an open write
    # transaction on the same file (BEGIN IMMEDIATE + a real write),
    # released by a timer after HOLD_SECONDS.
    writer = sqlite3.connect(db_path, check_same_thread=False)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES('test_lock', 'x')")

    def release() -> None:
        writer.commit()
        writer.close()

    timer = threading.Timer(HOLD_SECONDS, release)
    timer.start()
    try:
        client = TestClient(web_mod.create_app(), raise_server_exceptions=False)
        start = time.monotonic()
        resp = client.get("/api/status")
        elapsed = time.monotonic() - start
    finally:
        timer.cancel()
        try:
            writer.close()
        except Exception:
            pass
    assert resp.status_code == 200
    # The 200 must be earned by waiting past the old 5 s default —
    # not by the lock never having engaged.
    assert elapsed >= HOLD_SECONDS - 1.0
