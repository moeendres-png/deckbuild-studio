"""Tests für das Delta-Import-Protokoll (tools/delta_guard.py).

Synthetische Fixture-DB mit drei Tabellen: eine mit Primärschlüssel,
eine ohne Primärschlüssel (rowid-Sicherung) und eine mit großer
Text-Spalte (Streaming-Digest). Geprüft wird der volle Zyklus
before -> (Mutation als simulierter Import) -> verify inklusive der
Fehlerpfade (Exit 2 ohne Traceback).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import delta_guard as g

TOOL_PATH = Path(__file__).parent / "delta_guard.py"
BIG_BODY = "Anfang " + ("x" * 150_000) + " Ende"


def make_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                note TEXT
            );
            CREATE TABLE logs (
                message TEXT,
                level INTEGER
            );
            CREATE TABLE big_text (
                id INTEGER PRIMARY KEY,
                body TEXT
            );
            """
        )
        conn.executemany(
            "INSERT INTO items (id, name, note) VALUES (?, ?, ?)",
            [
                (1, "Alpha", "erster Eintrag"),
                (2, "Beta", None),  # NULL muss sich von '' unterscheiden
                (3, "Gamma", ""),
            ],
        )
        conn.executemany(
            "INSERT INTO logs (message, level) VALUES (?, ?)",
            [("start", 1), ("bereit", 2)],
        )
        conn.execute(
            "INSERT INTO big_text (id, body) VALUES (1, ?)", (BIG_BODY,)
        )
        conn.commit()
    finally:
        conn.close()
    return path


def mutate(db: Path, sql: str, params: tuple = ()) -> None:
    """Simuliert den 'Import': eine ganz normale Schreib-Transaktion."""
    conn = sqlite3.connect(db)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def run_before(db: Path, prefix: Path, tables=None, dumps=None) -> int:
    argv = ["before", "--db", str(db), "--out", str(prefix)]
    if tables:
        argv += ["--tables", ",".join(tables)]
    for spec in dumps or []:
        argv += ["--dump", spec]
    return g.main(argv)


def run_verify(db: Path, prefix: Path, expect=None, allow_replace=None,
               report: Path | None = None):
    argv = ["verify", "--db", str(db), "--before", str(prefix)]
    if expect:
        argv += ["--expect", ",".join(f"{t}={d:+d}" for t, d in expect.items())]
    if allow_replace:
        argv += ["--allow-replace", ",".join(allow_replace)]
    report_path = report or (prefix.parent / "report.json")
    argv += ["--report", str(report_path)]
    code = g.main(argv)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return code, payload


def read_rows(prefix: Path) -> list[dict]:
    rows_file = Path(f"{prefix}.rows.jsonl")
    return [
        json.loads(line)
        for line in rows_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def failures_text(payload: dict) -> str:
    return "\n".join(payload["failures"])


# ---------------------------------------------------------------------------
# Happy Path
# ---------------------------------------------------------------------------


def test_before_counts_all_tables_and_metadata(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0

    counts = json.loads(Path(f"{prefix}.counts.json").read_text(encoding="utf-8"))
    assert counts["db_path"] == str(db.resolve())
    assert counts["db_size_bytes"] == db.stat().st_size
    assert counts["created_utc"]
    assert counts["affected_tables"] == ["items"]
    assert set(counts["tables"]) == {"items", "logs", "big_text"}
    assert counts["tables"]["items"]["rows"] == 3
    assert counts["tables"]["logs"]["rows"] == 2
    assert counts["tables"]["big_text"]["rows"] == 1
    # Digest nur für betroffene Tabellen.
    assert len(counts["tables"]["items"]["digest_sha256"]) == 64
    assert "digest_sha256" not in counts["tables"]["logs"]
    # Ohne --dump existiert die Zeilen-Datei (leer) — kein Altbestand.
    assert Path(f"{prefix}.rows.jsonl").read_text(encoding="utf-8") == ""


def test_before_verify_without_changes_passes(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items", "big_text"]) == 0
    code, payload = run_verify(db, prefix)
    assert code == 0
    assert payload["status"] == "PASS"
    assert payload["failures"] == []
    # Der Bericht vermerkt ausdrücklich den ausgelassenen Voll-Check.
    assert any("quick_check" in note for note in payload["notes"])


def test_tools_do_not_modify_the_database(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"],
                      dumps=["items:id = 1"]) == 0
    code, _ = run_verify(db, prefix)
    assert code == 0
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash


# ---------------------------------------------------------------------------
# Zähler-Deltas
# ---------------------------------------------------------------------------


def test_insert_in_affected_table_with_correct_expect_passes(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    mutate(db, "INSERT INTO items (id, name, note) VALUES (4, 'Delta', 'neu')")
    mutate(db, "INSERT INTO items (id, name, note) VALUES (5, 'Echo', NULL)")
    mutate(db, "INSERT INTO items (id, name, note) VALUES (6, 'Foxtrott', '')")
    code, payload = run_verify(db, prefix, expect={"items": 3})
    assert code == 0
    assert payload["status"] == "PASS"


def test_insert_in_affected_table_with_wrong_expect_fails(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    mutate(db, "INSERT INTO items (id, name, note) VALUES (4, 'Delta', 'neu')")
    code, payload = run_verify(db, prefix, expect={"items": 3})
    assert code == 1
    assert payload["status"] == "FAIL"
    assert "items" in failures_text(payload)


def test_delete_in_affected_table_with_negative_expect_passes(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    mutate(db, "DELETE FROM items WHERE id = 3")
    code, payload = run_verify(db, prefix, expect={"items": -1})
    assert code == 0
    assert payload["status"] == "PASS"


def test_change_in_unaffected_table_fails(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    mutate(db, "INSERT INTO logs (message, level) VALUES ('unerwartet', 9)")
    code, payload = run_verify(db, prefix, expect={"items": 0})
    assert code == 1
    assert payload["status"] == "FAIL"
    assert "logs" in failures_text(payload)


def test_new_table_after_before_fails(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix) == 0
    mutate(db, "CREATE TABLE ueberraschung (id INTEGER)")
    code, payload = run_verify(db, prefix)
    assert code == 1
    assert "ueberraschung" in failures_text(payload)


# ---------------------------------------------------------------------------
# Inhalts-Digest (Delta 0 erwartet)
# ---------------------------------------------------------------------------


def test_content_change_with_zero_delta_fails_via_digest(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    # Gleiche Zeilenzahl, anderer Inhalt: nur der Digest kann das sehen.
    mutate(db, "UPDATE items SET note = 'geaendert' WHERE id = 1")
    code, payload = run_verify(db, prefix, expect={"items": 0})
    assert code == 1
    assert "Digest" in failures_text(payload)


def test_change_deep_in_large_text_fails_via_digest(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["big_text"]) == 0
    mutate(db, "UPDATE big_text SET body = body || '!' WHERE id = 1")
    code, payload = run_verify(db, prefix, expect={"big_text": 0})
    assert code == 1
    assert "Digest" in failures_text(payload)


def test_null_and_empty_string_are_distinct(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    # NULL -> '' darf der Digest nicht übersehen (eindeutige Markierung).
    mutate(db, "UPDATE items SET note = '' WHERE id = 2")
    code, _ = run_verify(db, prefix, expect={"items": 0})
    assert code == 1


# ---------------------------------------------------------------------------
# Zeilen-Sicherung (--dump) und --allow-replace
# ---------------------------------------------------------------------------


def test_replaced_saved_row_fails_without_allow_replace(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"],
                      dumps=["items:id = 1"]) == 0
    mutate(db, "UPDATE items SET name = 'Ersetzt' WHERE id = 1")
    code, payload = run_verify(db, prefix, expect={"items": 0})
    assert code == 1
    assert "Gesicherte Zeile verändert" in failures_text(payload)
    assert payload["row_checks"]["changed"] == [
        {"table": "items", "pk": {"id": 1}}
    ]


def test_replaced_saved_row_passes_with_allow_replace(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"],
                      dumps=["items:id = 1"]) == 0
    mutate(db, "UPDATE items SET name = 'Ersetzt' WHERE id = 1")
    code, payload = run_verify(db, prefix, expect={"items": 0},
                               allow_replace=["items"])
    assert code == 0
    assert payload["status"] == "PASS"
    assert payload["row_checks"]["skipped_allow_replace"] == 1


def test_deleted_saved_row_fails(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"],
                      dumps=["items:id IN (1, 2)"]) == 0
    mutate(db, "DELETE FROM items WHERE id = 2")
    # Zähler-Delta stimmt (-1); einziger FAIL-Grund darf die Zeile sein.
    code, payload = run_verify(db, prefix, expect={"items": -1})
    assert code == 1
    assert payload["row_checks"]["missing"] == [
        {"table": "items", "pk": {"id": 2}}
    ]
    assert "Gesicherte Zeile fehlt" in failures_text(payload)


def test_dump_of_table_without_pk_uses_rowid(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, dumps=["logs:message = 'start'"]) == 0
    entries = read_rows(prefix)
    assert len(entries) == 1
    assert entries[0]["table"] == "logs"
    assert set(entries[0]["pk"]) == {"_rowid"}
    assert entries[0]["row"] == {"message": "start", "level": 1}

    # Zeile per rowid löschen: Zähler stimmt, Zeilenprüfung schlägt an.
    rowid = entries[0]["pk"]["_rowid"]
    mutate(db, "DELETE FROM logs WHERE rowid = ?", (rowid,))
    code, payload = run_verify(db, prefix, expect={"logs": -1})
    assert code == 1
    assert payload["row_checks"]["missing"][0]["pk"] == {"_rowid": rowid}


def test_saved_row_with_null_value_roundtrip(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    # Zeile 2 hat note = NULL; unverändert muss die Prüfung PASS liefern.
    assert run_before(db, prefix, dumps=["items:id = 2"]) == 0
    entries = read_rows(prefix)
    assert entries[0]["row"]["note"] is None
    code, payload = run_verify(db, prefix)
    assert code == 0
    assert payload["row_checks"]["checked"] == 1


# ---------------------------------------------------------------------------
# Fehlerpfade: Exit 2, kontrollierte Meldung, kein Traceback
# ---------------------------------------------------------------------------


def _run_cli(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *argv],
        capture_output=True, text=True, timeout=60,
    )


def test_missing_db_file_exit_2(tmp_path):
    missing = tmp_path / "gibt_es_nicht.sqlite3"
    result = _run_cli(["before", "--db", str(missing),
                       "--out", str(tmp_path / "vor")])
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "nicht gefunden" in result.stderr
    # mode=ro darf keine leere DB-Datei anlegen.
    assert not missing.exists()


def test_missing_db_file_in_verify_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix) == 0
    result = _run_cli(["verify", "--db", str(tmp_path / "weg.sqlite3"),
                       "--before", str(prefix)])
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_missing_before_prefix_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    result = _run_cli(["verify", "--db", str(db),
                       "--before", str(tmp_path / "kein_prefix")])
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "Before-Datei nicht gefunden" in result.stderr


def test_corrupt_before_file_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    Path(f"{prefix}.counts.json").write_text("{kaputt", encoding="utf-8")
    assert g.main(["verify", "--db", str(db), "--before", str(prefix)]) == 2


def test_unknown_table_in_tables_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    code = g.main(["before", "--db", str(db), "--out", str(tmp_path / "vor"),
                   "--tables", "items,unbekannt"])
    assert code == 2


def test_unknown_table_in_dump_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    code = g.main(["before", "--db", str(db), "--out", str(tmp_path / "vor"),
                   "--dump", "unbekannt:id = 1"])
    assert code == 2


def test_bad_dump_where_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    code = g.main(["before", "--db", str(db), "--out", str(tmp_path / "vor"),
                   "--dump", "items:spalte_gibt_es_nicht = 1"])
    assert code == 2


def test_unknown_table_in_expect_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix) == 0
    code = g.main(["verify", "--db", str(db), "--before", str(prefix),
                   "--expect", "unbekannt=+1"])
    assert code == 2


def test_invalid_expect_format_exit_2(tmp_path):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix) == 0
    code = g.main(["verify", "--db", str(db), "--before", str(prefix),
                   "--expect", "items~3"])
    assert code == 2


def test_verify_json_on_stdout_without_report_file(tmp_path, capsys):
    db = make_db(tmp_path / "test.sqlite3")
    prefix = tmp_path / "vor"
    assert run_before(db, prefix, tables=["items"]) == 0
    assert g.main(["verify", "--db", str(db), "--before", str(prefix)]) == 0
    out = capsys.readouterr().out
    marker = "--- delta-guard JSON ---"
    assert marker in out
    payload = json.loads(out.split(marker, 1)[1])
    assert payload["status"] == "PASS"
