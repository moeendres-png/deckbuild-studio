#!/usr/bin/env python3
"""Delta-Import-Protokoll für die Deckbuild-Studio-Datenbank.

Zweck: Künftige Importe in die große Live-DB (SQLite, mehrere GB)
absichern, OHNE vor jedem Import eine Vollkopie der DB anzulegen und
OHNE bei jedem Import einen vollständigen ``PRAGMA quick_check`` zu
fahren. Das Werkzeug friert stattdessen vor einem Import einen
leichtgewichtigen Vorher-Zustand ein (Zähler aller Tabellen, Inhalts-
Digests nur für die betroffenen Tabellen, optional einzelne Zeilen als
Wiederherstellungspunkt) und prüft nach dem Import exakt nach:

* Nicht betroffene Tabellen müssen zeilengenau unverändert sein.
* Betroffene Tabellen müssen exakt das erwartete Zähler-Delta haben.
* Bei erwartetem Delta 0 muss zusätzlich der Inhalts-Digest stimmen.
* Gesicherte Zeilen (``--dump``) müssen per Primärschlüssel noch
  existieren und unverändert sein — außer, die Tabelle ist per
  ``--allow-replace`` ausdrücklich zum Ersetzen freigegeben.

Ein vollständiger Integritätscheck (``quick_check``) läuft bewusst
NICHT in diesem Werkzeug; er bleibt ein separater, geplanter Vorgang.
Der Verify-Bericht weist ausdrücklich darauf hin.

Die DB wird ausschließlich lesend geöffnet (URI ``mode=ro``); dieses
Werkzeug schreibt niemals in eine Datenbank. Nur Standardbibliothek.

Beispiele:
    python tools/delta_guard.py before --db DB --out /tmp/vor_import \
        --tables card_signal,sources \
        --dump "sources:name = 'edhrec'"
    # ... Import läuft (anderes Programm) ...
    python tools/delta_guard.py verify --db DB --before /tmp/vor_import \
        --expect card_signal=+300,sources=+0 \
        --allow-replace sources --report /tmp/bericht.json

Exit-Codes: 0 = PASS bzw. ``before`` erfolgreich, 1 = Verify-FAIL,
2 = Benutzungsfehler (fehlende DB, fehlende Tabelle, kaputte
Before-Datei, ungültige Argumente) — ohne Traceback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

FORMAT_COUNTS = "delta-guard-counts/1"
FORMAT_REPORT = "delta-guard-report/1"
BLOB_MARKER = "$delta_guard_blob"
ROWID_PK = "_rowid"
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
_FETCH_CHUNK = 1000


class UsageError(Exception):
    """Kontrollierter Benutzungsfehler -> Meldung + Exit 2, kein Traceback."""


# ---------------------------------------------------------------------------
# Grundbausteine: Verbindung, Tabellen-Metadaten, kanonische Serialisierung
# ---------------------------------------------------------------------------


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Öffnet die DB strikt lesend (``mode=ro``); fehlt sie, ist das ein
    Benutzungsfehler, kein Absturz — und es wird garantiert keine neue,
    leere DB-Datei angelegt (das täte ein normaler Connect)."""
    if not db_path.is_file():
        raise UsageError(f"Datenbank nicht gefunden: {db_path}")
    uri = "file:" + quote(str(db_path.resolve())) + "?mode=ro"
    try:
        return sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise UsageError(f"Datenbank nicht lesbar: {db_path}: {exc}") from exc


def _list_tables(conn: sqlite3.Connection) -> list[str]:
    """Alle echten Tabellen (keine Views, keine internen ``sqlite_%``)."""
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    except sqlite3.Error as exc:
        raise UsageError(f"Tabellenliste nicht lesbar (kaputte DB?): {exc}") from exc
    return [str(row[0]) for row in rows]


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _table_columns(conn: sqlite3.Connection, table: str) -> list[tuple[str, int]]:
    """Spalten der Tabelle als (Name, pk_position); pk_position 0 = kein PK.
    Reihenfolge entspricht der Tabellendefinition."""
    try:
        rows = conn.execute(f"PRAGMA table_info({_quote_ident(table)})").fetchall()
    except sqlite3.Error as exc:
        raise UsageError(f"Schema von Tabelle {table!r} nicht lesbar: {exc}") from exc
    if not rows:
        raise UsageError(f"Tabelle existiert nicht: {table!r}")
    return [(str(row[1]), int(row[5])) for row in rows]


def _pk_columns(columns: list[tuple[str, int]]) -> list[str]:
    """Primärschlüssel-Spalten in PK-Reihenfolge (leer, wenn kein PK)."""
    return [name for name, pk in sorted(columns, key=lambda c: c[1]) if pk > 0]


def _is_without_rowid(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return bool(row and row[0] and "without rowid" in str(row[0]).lower())


def _order_clause(conn: sqlite3.Connection, table: str, columns: list[tuple[str, int]]) -> str:
    """Deterministische Sortierung: ``rowid`` (Spezifikation), bei
    WITHOUT-ROWID-Tabellen ersatzweise die PK-Spalten."""
    if _is_without_rowid(conn, table):
        pk = _pk_columns(columns)
        if pk:
            return " ORDER BY " + ", ".join(_quote_ident(c) for c in pk)
        return " ORDER BY " + ", ".join(_quote_ident(c) for c, _ in columns)
    return " ORDER BY rowid"


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {_quote_ident(table)}").fetchone()
    except sqlite3.Error as exc:
        raise UsageError(f"Zählung von Tabelle {table!r} fehlgeschlagen: {exc}") from exc
    return int(row[0])


def _canonical_value(value: object) -> bytes:
    """Kanonische, typ-eindeutige Serialisierung eines SQLite-Werts.

    Jeder Wert trägt ein Typ-Präfix und (bei Text/Blob) eine Länge, damit
    z. B. NULL, leerer String und der Text ``'NULL'`` garantiert
    verschiedene Bytes ergeben und Feldgrenzen nie verschwimmen."""
    if value is None:
        return b"N;"
    if isinstance(value, bool):  # SQLite kennt kein bool, nur zur Sicherheit
        return b"I:" + (b"1" if value else b"0") + b";"
    if isinstance(value, int):
        return b"I:" + str(value).encode("ascii") + b";"
    if isinstance(value, float):
        return b"F:" + repr(value).encode("ascii") + b";"
    if isinstance(value, str):
        data = value.encode("utf-8")
        return b"S:" + str(len(data)).encode("ascii") + b":" + data + b";"
    if isinstance(value, (bytes, bytearray, memoryview)):
        data = bytes(value)
        return b"B:" + str(len(data)).encode("ascii") + b":" + data + b";"
    raise UsageError(f"Nicht serialisierbarer SQLite-Wert: {type(value)!r}")


def _table_digest(conn: sqlite3.Connection, table: str) -> str:
    """SHA-256 über gestreamten, deterministischen Zeilen-Dump.

    Es wird zeilenweise gelesen (``fetchmany``), nie die ganze Tabelle in
    den Speicher geladen — das ist die Voraussetzung dafür, dass das
    Werkzeug auch an einer mehrere GB großen DB brauchbar bleibt."""
    columns = _table_columns(conn, table)
    order = _order_clause(conn, table, columns)
    hasher = hashlib.sha256()
    try:
        cursor = conn.execute(f"SELECT * FROM {_quote_ident(table)}{order}")
        while True:
            chunk = cursor.fetchmany(_FETCH_CHUNK)
            if not chunk:
                break
            for row in chunk:
                hasher.update(b"|".join(_canonical_value(v) for v in row))
                hasher.update(b"\n")
    except sqlite3.Error as exc:
        raise UsageError(f"Digest von Tabelle {table!r} fehlgeschlagen: {exc}") from exc
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# JSONL-Zeilen-Sicherung (Wiederherstellungspunkt für ersetzte Bestandszeilen)
# ---------------------------------------------------------------------------


def _encode_value(value: object) -> object:
    """SQLite-Wert JSON-sicher machen; Blobs als markiertes Hex-Objekt,
    damit sie beim Dekodieren eindeutig von Text unterscheidbar sind."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {BLOB_MARKER: bytes(value).hex()}
    if value is None or isinstance(value, (int, float, str)):
        return value
    raise UsageError(f"Nicht JSON-sicherer SQLite-Wert: {type(value)!r}")


def _decode_value(value: object) -> object:
    if isinstance(value, dict) and set(value) == {BLOB_MARKER}:
        return bytes.fromhex(str(value[BLOB_MARKER]))
    return value


def _dump_rows(
    conn: sqlite3.Connection,
    table: str,
    where: str,
    known_tables: list[str],
) -> list[dict[str, object]]:
    """Alle Zeilen von ``table``, die ``where`` genügen, als Einträge mit
    PK + vollem Zeileninhalt. Ohne PK wird die rowid als ``_rowid``
    gesichert — sonst wäre die Zeile nach dem Import nicht wiederfindbar."""
    if table not in known_tables:
        raise UsageError(f"--dump: Tabelle existiert nicht: {table!r}")
    if not where.strip():
        raise UsageError(f"--dump: leere WHERE-Bedingung für Tabelle {table!r}")
    columns = _table_columns(conn, table)
    column_names = [name for name, _ in columns]
    pk_cols = _pk_columns(columns)
    order = _order_clause(conn, table, columns)
    select_rowid = "" if pk_cols else "rowid AS __delta_guard_rowid, "
    sql = f"SELECT {select_rowid}* FROM {_quote_ident(table)} WHERE {where}{order}"
    try:
        cursor = conn.execute(sql)
        fetched = cursor.fetchall()
    except sqlite3.Error as exc:
        raise UsageError(
            f"--dump für Tabelle {table!r} (WHERE {where!r}) fehlgeschlagen: {exc}"
        ) from exc
    entries: list[dict[str, object]] = []
    for raw in fetched:
        values = list(raw)
        rowid_value = None
        if not pk_cols:
            rowid_value = values.pop(0)
        row = {
            name: _encode_value(value) for name, value in zip(column_names, values)
        }
        if pk_cols:
            pk = {name: row[name] for name in pk_cols}
        else:
            pk = {ROWID_PK: _encode_value(rowid_value)}
        entries.append({"table": table, "pk": pk, "row": row})
    return entries


# ---------------------------------------------------------------------------
# Argument-Hilfen
# ---------------------------------------------------------------------------


def _split_csv(values: list[str] | None) -> list[str]:
    """Komma-Listen (auch mehrfach angebbare Optionen) flach und
    reihenfolge-erhaltend ohne Duplikate zurückgeben."""
    result: list[str] = []
    for value in values or []:
        for part in value.split(","):
            part = part.strip()
            if part and part not in result:
                result.append(part)
    return result


def _parse_dump_spec(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise UsageError(
            f"--dump erwartet die Form TABELLE:WHERE, erhalten: {spec!r}"
        )
    table, where = spec.split(":", 1)
    table = table.strip()
    if not table:
        raise UsageError(f"--dump ohne Tabellenname: {spec!r}")
    return table, where


def _parse_expect(values: list[str] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values or []:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            if "=" not in part:
                raise UsageError(
                    f"--expect erwartet die Form TABELLE=+N/-N/0, erhalten: {part!r}"
                )
            table, _, delta_text = part.partition("=")
            table = table.strip()
            delta_text = delta_text.strip()
            try:
                delta = int(delta_text)
            except ValueError:
                raise UsageError(
                    f"--expect: ungültiges Delta {delta_text!r} für Tabelle {table!r}"
                ) from None
            if table in result:
                raise UsageError(f"--expect: Tabelle mehrfach angegeben: {table!r}")
            result[table] = delta
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Subcommand: before
# ---------------------------------------------------------------------------


def cmd_before(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    affected = _split_csv(args.tables)
    dump_specs = [_parse_dump_spec(spec) for spec in args.dump or []]

    conn = _connect_readonly(db_path)
    try:
        tables = _list_tables(conn)
        for table in affected:
            if table not in tables:
                raise UsageError(f"--tables: Tabelle existiert nicht: {table!r}")

        table_info: dict[str, dict[str, object]] = {}
        for table in tables:
            entry: dict[str, object] = {"rows": _row_count(conn, table)}
            if table in affected:
                entry["digest_sha256"] = _table_digest(conn, table)
            table_info[table] = entry

        dumped: list[dict[str, object]] = []
        total_dumped = 0
        for table, where in dump_specs:
            entries = _dump_rows(conn, table, where, tables)
            dumped.extend(entries)
            total_dumped += len(entries)
    finally:
        conn.close()

    counts_path = Path(f"{args.out}.counts.json")
    rows_path = Path(f"{args.out}.rows.jsonl")
    counts_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "format": FORMAT_COUNTS,
        "db_path": str(db_path.resolve()),
        "created_utc": _utc_now(),
        "db_size_bytes": db_path.stat().st_size,
        "affected_tables": affected,
        "dump_specs": [
            {"table": table, "where": where} for table, where in dump_specs
        ],
        "dumped_rows": total_dumped,
        "tables": table_info,
    }
    try:
        counts_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # Die rows-Datei wird immer (ggf. leer) geschrieben, damit ein
        # späterer verify-Lauf nie eine veraltete Sicherung eines früheren
        # Laufs mit demselben Prefix prüft.
        with rows_path.open("w", encoding="utf-8") as handle:
            for entry in dumped:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise UsageError(f"Ausgabedateien nicht schreibbar ({args.out!r}): {exc}") from exc

    print(f"before: {len(table_info)} Tabellen gezählt, "
          f"{len(affected)} betroffene Tabelle(n) mit Digest, "
          f"{total_dumped} Zeile(n) gesichert.")
    print(f"before: geschrieben: {counts_path} und {rows_path}")
    return EXIT_PASS


# ---------------------------------------------------------------------------
# Subcommand: verify
# ---------------------------------------------------------------------------


def _load_before(prefix: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Before-Dateien laden; jede Unstimmigkeit ist ein Benutzungsfehler
    (Exit 2), kein FAIL — ein kaputter Vorher-Zustand sagt nichts über
    den Import aus."""
    counts_path = Path(f"{prefix}.counts.json")
    if not counts_path.is_file():
        raise UsageError(f"Before-Datei nicht gefunden: {counts_path}")
    try:
        data = json.loads(counts_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UsageError(f"Before-Datei nicht lesbar: {counts_path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("tables"), dict):
        raise UsageError(
            f"Before-Datei hat kein gültiges Format (Feld 'tables' fehlt): {counts_path}"
        )
    for name, entry in data["tables"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("rows"), int):
            raise UsageError(
                f"Before-Datei beschädigt: Eintrag für Tabelle {name!r} ohne Zeilenzahl"
            )
    if not isinstance(data.get("affected_tables", []), list):
        raise UsageError("Before-Datei beschädigt: 'affected_tables' ist keine Liste")

    rows_path = Path(f"{prefix}.rows.jsonl")
    dumped_rows: list[dict[str, object]] = []
    if rows_path.is_file():
        try:
            lines = rows_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise UsageError(f"Zeilen-Sicherung nicht lesbar: {rows_path}: {exc}") from exc
        for lineno, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except ValueError as exc:
                raise UsageError(
                    f"Zeilen-Sicherung beschädigt ({rows_path}, Zeile {lineno}): {exc}"
                ) from exc
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("table"), str)
                or not isinstance(entry.get("pk"), dict)
                or not isinstance(entry.get("row"), dict)
            ):
                raise UsageError(
                    f"Zeilen-Sicherung beschädigt ({rows_path}, Zeile {lineno}): "
                    "Eintrag ohne table/pk/row"
                )
            dumped_rows.append(entry)
    return data, dumped_rows


def _fetch_saved_row(
    conn: sqlite3.Connection,
    entry: dict[str, object],
    tables_now: list[str],
) -> dict[str, object] | None:
    """Gesicherte Zeile per PK erneut laden; None = nicht mehr vorhanden.
    Eine verschwundene Tabelle zählt als 'Zeile fehlt' (FAIL), nicht als
    Benutzungsfehler — der Import könnte sie entfernt haben."""
    table = str(entry["table"])
    if table not in tables_now:
        return None
    columns = _table_columns(conn, table)
    column_names = [name for name, _ in columns]
    pk = dict(entry["pk"])  # type: ignore[arg-type]
    conditions: list[str] = []
    params: list[object] = []
    if set(pk) == {ROWID_PK}:
        conditions.append("rowid IS ?")
        params.append(_decode_value(pk[ROWID_PK]))
    else:
        for name, value in pk.items():
            conditions.append(f"{_quote_ident(str(name))} IS ?")
            params.append(_decode_value(value))
    sql = (
        f"SELECT * FROM {_quote_ident(table)} WHERE "
        + " AND ".join(conditions)
    )
    try:
        raw = conn.execute(sql, params).fetchone()
    except sqlite3.Error:
        return None
    if raw is None:
        return None
    return {name: value for name, value in zip(column_names, raw)}


def cmd_verify(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    expect = _parse_expect(args.expect)
    allow_replace = _split_csv(args.allow_replace)
    before, dumped_rows = _load_before(args.before)

    before_tables: dict[str, dict[str, object]] = before["tables"]  # type: ignore[assignment]
    before_affected = [str(t) for t in before.get("affected_tables", [])]
    for table in expect:
        if table not in before_tables:
            raise UsageError(f"--expect: Tabelle im Before-Zustand unbekannt: {table!r}")
    for table in allow_replace:
        if table not in before_tables:
            raise UsageError(
                f"--allow-replace: Tabelle im Before-Zustand unbekannt: {table!r}"
            )
    for table in before_affected:
        if table not in before_tables:
            raise UsageError(
                f"Before-Datei beschädigt: betroffene Tabelle {table!r} fehlt in 'tables'"
            )

    failures: list[str] = []
    table_reports: list[dict[str, object]] = []
    affected_now = set(before_affected) | set(expect)

    conn = _connect_readonly(db_path)
    try:
        tables_now = _list_tables(conn)
        counts_now = {table: _row_count(conn, table) for table in tables_now}

        for table in sorted(set(tables_now) - set(before_tables)):
            failures.append(f"Neue Tabelle nach dem Import: {table!r}")
        for table in sorted(set(before_tables) - set(tables_now)):
            failures.append(f"Tabelle seit dem Import verschwunden: {table!r}")

        for table in sorted(set(before_tables) & set(tables_now)):
            before_count = int(before_tables[table]["rows"])
            after_count = counts_now[table]
            delta = after_count - before_count
            is_affected = table in affected_now
            expected_delta = expect.get(table, 0) if is_affected else 0
            report: dict[str, object] = {
                "table": table,
                "affected": is_affected,
                "rows_before": before_count,
                "rows_after": after_count,
                "delta": delta,
                "expected_delta": expected_delta if is_affected else 0,
                "count_ok": delta == expected_delta if is_affected else delta == 0,
                "digest_checked": False,
                "digest_ok": None,
            }
            if not report["count_ok"]:
                if is_affected:
                    failures.append(
                        f"Tabelle {table!r}: Delta {delta:+d}, "
                        f"erwartet {expected_delta:+d} "
                        f"({before_count} -> {after_count} Zeilen)"
                    )
                else:
                    failures.append(
                        f"Nicht betroffene Tabelle {table!r} verändert: "
                        f"{before_count} -> {after_count} Zeilen"
                    )
            # Digest nur, wo er Aussagekraft hat: betroffene Tabelle,
            # Delta 0 erwartet, Digest im Before-Zustand vorhanden und
            # keine Replace-Freigabe (Ersetzen verändert den Digest
            # definitionsgemäß).
            before_digest = before_tables[table].get("digest_sha256")
            if (
                is_affected
                and expected_delta == 0
                and isinstance(before_digest, str)
                and table not in allow_replace
                and report["count_ok"]
            ):
                report["digest_checked"] = True
                digest_now = _table_digest(conn, table)
                report["digest_ok"] = digest_now == before_digest
                if digest_now != before_digest:
                    failures.append(
                        f"Tabelle {table!r}: Inhalt verändert (Digest weicht ab), "
                        "obwohl Delta 0 erwartet wurde"
                    )
            table_reports.append(report)

        # Gesicherte Zeilen einzeln per PK nachprüfen.
        row_missing: list[dict[str, object]] = []
        row_changed: list[dict[str, object]] = []
        rows_checked = 0
        rows_skipped = 0
        for entry in dumped_rows:
            table = str(entry["table"])
            if table in allow_replace:
                rows_skipped += 1
                continue
            rows_checked += 1
            current = _fetch_saved_row(conn, entry, tables_now)
            label = {"table": table, "pk": entry["pk"]}
            if current is None:
                row_missing.append(label)
                failures.append(
                    f"Gesicherte Zeile fehlt nach dem Import: "
                    f"Tabelle {table!r}, PK {entry['pk']!r}"
                )
                continue
            saved_row = {
                name: _decode_value(value)
                for name, value in dict(entry["row"]).items()  # type: ignore[arg-type]
            }
            if current != saved_row:
                row_changed.append(label)
                failures.append(
                    f"Gesicherte Zeile verändert nach dem Import: "
                    f"Tabelle {table!r}, PK {entry['pk']!r}"
                )
    finally:
        conn.close()

    status = "PASS" if not failures else "FAIL"
    report_payload: dict[str, object] = {
        "format": FORMAT_REPORT,
        "status": status,
        "db_path": str(db_path.resolve()),
        "before_prefix": args.before,
        "checked_utc": _utc_now(),
        "tables": table_reports,
        "row_checks": {
            "checked": rows_checked,
            "skipped_allow_replace": rows_skipped,
            "missing": row_missing,
            "changed": row_changed,
        },
        "failures": failures,
        "notes": [
            "Es wurde bewusst KEIN vollständiger PRAGMA quick_check gefahren; "
            "der Integritätscheck läuft separat/geplant.",
        ],
    }

    print(f"verify: {status}")
    for entry in table_reports:
        marker = "OK " if entry["count_ok"] and entry["digest_ok"] is not False else "!! "
        kind = "betroffen " if entry["affected"] else "unberührt "
        digest_text = ""
        if entry["digest_checked"]:
            digest_text = f", Digest {'OK' if entry['digest_ok'] else 'abweichend'}"
        print(
            f"  {marker}{kind} {entry['table']}: "
            f"{entry['rows_before']} -> {entry['rows_after']} Zeilen "
            f"(Delta {entry['delta']:+d}, erwartet {entry['expected_delta']:+d})"
            f"{digest_text}"
        )
    if dumped_rows:
        print(f"  Gesicherte Zeilen geprüft: {rows_checked}, "
              f"per --allow-replace übersprungen: {rows_skipped}, "
              f"fehlend: {len(row_missing)}, verändert: {len(row_changed)}")
    for failure in failures:
        print(f"  FAIL: {failure}")
    print("  Hinweis: Kein vollständiger quick_check gefahren — "
          "Integritätscheck läuft separat/geplant.")

    report_json = json.dumps(report_payload, ensure_ascii=False, indent=2)
    if args.report:
        report_path = Path(args.report)
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_json + "\n", encoding="utf-8")
        except OSError as exc:
            raise UsageError(f"Bericht nicht schreibbar: {report_path}: {exc}") from exc
        print(f"verify: JSON-Bericht geschrieben: {report_path}")
    else:
        print("--- delta-guard JSON ---")
        print(report_json)
    return EXIT_PASS if status == "PASS" else EXIT_FAIL


# ---------------------------------------------------------------------------
# CLI-Gerüst
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="delta_guard.py",
        description=(
            "Delta-Import-Protokoll: Vorher-Zustand einer SQLite-DB "
            "einfrieren (Zähler + Digests + Zeilen-Sicherung) und nach "
            "einem Import exakt dagegen prüfen — ohne Vollkopie und "
            "ohne Voll-quick_check je Import."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_before = sub.add_parser("before", help="Vorher-Zustand schreiben")
    p_before.add_argument("--db", required=True, help="Pfad zur SQLite-DB (wird nur lesend geöffnet)")
    p_before.add_argument("--out", required=True, help="Ausgabe-Prefix (schreibt PREFIX.counts.json + PREFIX.rows.jsonl)")
    p_before.add_argument(
        "--tables", action="append", default=None,
        help="Betroffene Tabellen, komma-getrennt (für diese wird ein Inhalts-Digest gespeichert); wiederholbar",
    )
    p_before.add_argument(
        "--dump", action="append", default=None, metavar="TABELLE:WHERE",
        help="Zeilen sichern, die der WHERE-Bedingung genügen (Wiederherstellungspunkt); wiederholbar",
    )
    p_before.set_defaults(func=cmd_before)

    p_verify = sub.add_parser("verify", help="DB gegen einen Before-Zustand prüfen")
    p_verify.add_argument("--db", required=True, help="Pfad zur SQLite-DB (wird nur lesend geöffnet)")
    p_verify.add_argument("--before", required=True, help="Prefix eines früheren before-Laufs")
    p_verify.add_argument(
        "--expect", action="append", default=None, metavar="T=+N",
        help="Erwartete Zähler-Deltas betroffener Tabellen, z. B. T1=+3,T2=-1,T3=0; wiederholbar",
    )
    p_verify.add_argument(
        "--allow-replace", action="append", default=None, dest="allow_replace",
        help="Tabellen, deren gesicherte Zeilen ersetzt werden dürfen, komma-getrennt; wiederholbar",
    )
    p_verify.add_argument(
        "--report", default=None,
        help="Maschinenlesbaren JSON-Bericht in diese Datei schreiben (sonst auf stdout)",
    )
    p_verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except UsageError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (sqlite3.Error, OSError, ValueError) as exc:
        # Letzte Auffanglinie: kontrollierte Meldung statt Traceback.
        print(f"Fehler: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
