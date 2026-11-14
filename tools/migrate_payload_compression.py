#!/usr/bin/env python3
"""Migrate stored JSON payloads to the compressed storage representation.

Converts plain-text values in the payload columns (default:
``tier_assignment.signals_json`` — the one measured dominant block,
2.48 GB of content; ``external_snapshot.payload_json`` totals 12 MB and
is deliberately out of scope, see ``docs/DB_DIET.md``) to the
``gzip+b64:`` representation defined by
:mod:`deckbuild_studio.payloads`, in place, batch by batch.
Every converted row is verified before its batch commits: the decoded
value must be byte-identical to the original (SHA-256 compared), so the
stored provenance hashes — which cover the ORIGINAL payload text — stay
valid for every single row, not just a sample.

Properties:

* **Resumable.** Converted rows carry the marker prefix and are skipped
  by the row filter, so an interrupted run (crash, Ctrl-C, disk full)
  can simply be re-started; it continues where the data shows it stopped.
  Each batch commits separately, so at most one batch of work is lost.
* **Content-agnostic.** Values are treated as opaque text: a stored
  payload that is corrupt JSON stays corrupt in exactly the same bytes
  after conversion (decode restores it byte-for-byte and the existing
  corrupt-payload handling keeps applying).
* **Small values stay plain.** The codec keeps payloads below its size
  threshold (and incompressible ones) verbatim; the migration counts
  them as ``kept_plain`` and never rewrites them.
* **Optional VACUUM** at the end (``--vacuum``) reclaims the freed pages;
  without it the file size does not change even though the content did.

Usage (from the repo root, package installed or ``PYTHONPATH=src``)::

    python tools/migrate_payload_compression.py --db COPY.sqlite3 --vacuum
    python tools/migrate_payload_compression.py --db COPY.sqlite3 --dry-run
    python tools/migrate_payload_compression.py --db DB \
        --column tier_assignment.signals_json

Phase discipline (docs/DB_DIET.md): run this ONLY against a copy until
the live migration is explicitly approved; the live database gets a
fresh full backup first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    from deckbuild_studio.payloads import PREFIX, decode_payload, encode_payload
except ImportError:  # running from a source checkout without install
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from deckbuild_studio.payloads import PREFIX, decode_payload, encode_payload

DEFAULT_COLUMNS = ("tier_assignment.signals_json",)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pk_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})") if r[5]]
    return cols


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone() is not None


def migrate_column(conn: sqlite3.Connection, table: str, column: str, *,
                   batch_size: int, dry_run: bool,
                   log=print) -> dict:
    """Convert one column; returns the per-column result counters.

    Keyset pagination (fresh bounded query per batch, ``WHERE (pk) >
    (last key)``) instead of one long-lived cursor: the table mutates
    under the migration (converted rows shrink), and SQLite does not
    guarantee stable iteration over a table being updated through the
    same connection. Converted rows also drop out of the candidate
    filter via the marker prefix, which is what makes a re-run after an
    interruption resume instead of restart.
    """
    pk_cols = _pk_columns(conn, table)
    key_cols = pk_cols if pk_cols else ["rowid"]
    key_sql = ", ".join(f'"{c}"' for c in key_cols)
    prefix_len = len(PREFIX)
    result = {"table": table, "column": column, "scanned": 0,
              "converted": 0, "verified": 0, "kept_plain": 0,
              "bytes_before": 0, "bytes_after": 0}
    last_key: tuple | None = None
    while True:
        sql = (f'SELECT {key_sql}, "{column}" FROM "{table}" '
               f'WHERE "{column}" IS NOT NULL '
               f"AND substr(\"{column}\", 1, {prefix_len}) <> ?")
        params: list = [PREFIX]
        if last_key is not None:
            placeholders = ", ".join("?" for _ in key_cols)
            sql += f" AND ({key_sql}) > ({placeholders})"
            params.extend(last_key)
        sql += f" ORDER BY {key_sql} LIMIT ?"
        params.append(batch_size)
        batch = conn.execute(sql, params).fetchall()
        if not batch:
            break
        pending: list[tuple] = []
        for row in batch:
            key, value = tuple(row[:-1]), row[-1]
            last_key = key
            if not isinstance(value, str):
                continue  # BLOB or numeric in a TEXT column: not a payload
            result["scanned"] += 1
            result["bytes_before"] += len(value.encode("utf-8"))
            encoded = encode_payload(value)
            if encoded == value:
                result["kept_plain"] += 1
                result["bytes_after"] += len(value.encode("utf-8"))
                continue
            # Full roundtrip proof for THIS row before it is staged:
            # the decoded text must be byte-identical to the original
            # (string equality, hence also SHA-256 equality).
            decoded = decode_payload(encoded)
            if decoded != value or _sha256(decoded) != _sha256(value):
                raise RuntimeError(
                    f"roundtrip verification failed for "
                    f"{table}.{column} key={key}")
            result["converted"] += 1
            result["verified"] += 1
            result["bytes_after"] += len(encoded.encode("utf-8"))
            pending.append((encoded, *key))
        if pending and not dry_run:
            where = " AND ".join(f'"{c}" = ?' for c in key_cols)
            conn.executemany(
                f'UPDATE "{table}" SET "{column}" = ? WHERE {where}', pending)
            conn.commit()
        log(f"  {table}.{column}: {result['converted']} converted, "
            f"{result['kept_plain']} kept plain ...")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compress stored JSON payloads in place (resumable).")
    parser.add_argument("--db", required=True, help="SQLite database file")
    parser.add_argument("--column", action="append", dest="columns",
                        metavar="TABLE.COLUMN",
                        help="payload column to convert (repeatable); "
                             "default: tier_assignment.signals_json")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true",
                        help="measure only: no writes, no VACUUM")
    parser.add_argument("--vacuum", action="store_true",
                        help="run VACUUM after converting (reclaims pages)")
    parser.add_argument("--report", metavar="FILE",
                        help="write a JSON summary to FILE")
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"error: database not found: {db_path}", file=sys.stderr)
        return 2
    columns = args.columns or list(DEFAULT_COLUMNS)
    for spec in columns:
        if "." not in spec:
            print(f"error: --column expects TABLE.COLUMN, got {spec!r}",
                  file=sys.stderr)
            return 2

    size_before = db_path.stat().st_size
    conn = sqlite3.connect(db_path, timeout=300)
    try:
        summary: dict = {"db": str(db_path), "dry_run": args.dry_run,
                         "file_bytes_before": size_before, "columns": []}
        t0 = time.time()
        for spec in columns:
            table, column = spec.rsplit(".", 1)
            if not _table_exists(conn, table):
                print(f"error: table not found: {table}", file=sys.stderr)
                return 2
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                print(f"error: column not found: {spec}", file=sys.stderr)
                return 2
            print(f"{spec}: converting (batch {args.batch_size})"
                  f"{' [dry-run]' if args.dry_run else ''} ...")
            summary["columns"].append(
                migrate_column(conn, table, column,
                               batch_size=args.batch_size,
                               dry_run=args.dry_run))
        summary["seconds"] = round(time.time() - t0, 1)
        if args.vacuum and not args.dry_run:
            print("VACUUM ...")
            conn.commit()
            conn.execute("VACUUM")
        summary["file_bytes_after"] = db_path.stat().st_size
    finally:
        conn.close()
    print(json.dumps(summary, indent=1))
    if args.report:
        Path(args.report).write_text(json.dumps(summary, indent=1),
                                      encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
