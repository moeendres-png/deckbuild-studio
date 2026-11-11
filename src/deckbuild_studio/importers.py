"""Collection importers — three explicit formats, no universal auto-detection
beyond the documented sheet signatures, no OCR.

A) Normalized workbook (primary acceptance format, Issue §0/§2):
   sheets 01_CARD_IDENTITY / 02_PHYSICAL_LOTS / 03_LOCATIONS /
   05_INVENTORY_CURRENT (+ 04/06/07/09/10 read for provenance/audit counts).
   card_id (local) and oracle_id (canonical) are preserved verbatim;
   quantity semantics: exact vs lower-bound vs missing (missing != 0).

B) Primary owner workbook ``Kartensammlung_Foundation_Schwarze_Box.xlsx``:
   single sheet ``Kartensammlung`` with 7 columns
   (Kartenname, Anzahl, Standort, Farbidentitat, Manakosten, Kartentyp,
   Kartentext). Names are resolved EXACTLY against the local Scryfall store
   (full paper name, incl. the full DFC name). Ambiguous/unresolved names
   abort the import with a report — never a guess. Upsert key is
   (collection_id, oracle_id, location_id); rows missing from a later file
   are NOT deleted (deletion only via explicit --mode replace-snapshot,
   which writes audit events). The source carries no reservations /
   conditions / printings: reserved=0 is stored with
   ``reserved_assumption='preliminary_zero_declared'`` — an openly declared
   assumption, not a verified fact. Profile: ``foundation-schwarze-box``,
   isolated from every other profile; locations ``Foundation`` and
   ``Schwarze Box`` are kept as distinct literal location names.

C) Generic CSV/XLSX via an explicit column-mapping config (JSON):
   {"collection_id": ..., "sheet": ... (xlsx only),
    "columns": {"name": "<col>", "quantity": "<col>", "location": "<col>",
                "reserved": "<col or null>", "condition": "<col or null>"}}
   Name resolution identical to (B).

All importers are idempotent and transactional: any error rolls the whole
import back. Every row carries source provenance (source_id -> source row).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from openpyxl import load_workbook

from .store import Store, sha256_file, utcnow

FOUNDATION_COLLECTION = "foundation-schwarze-box"
RESERVED_ASSUMPTION = "preliminary_zero_declared"


class ImportFailure(Exception):
    def __init__(self, report: dict):
        super().__init__(str(report.get("errors", report)))
        self.report = report


def _text(v: object) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _int(v: object, *, field: str, ctx: str) -> int | None:
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return int(float(str(v).replace(",", "."))) if isinstance(v, str) else int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ImportFailure({"errors": [f"{ctx}: {field}={v!r} is not an integer"]}) from exc


def _flag(v: object) -> int | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    s = str(v).strip().lower()
    if s in {"true", "yes", "ja", "1", "x"}:
        return 1
    if s in {"false", "no", "nein", "0", ""}:
        return 0
    return None


def _sheet_rows(path: Path, sheet: str) -> list[dict[str, object]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        return []
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    out = []
    for raw in rows[1:]:
        if raw is None or all(c is None for c in raw):
            continue
        out.append({headers[i]: raw[i] for i in range(min(len(headers), len(raw)))})
    return out


def _workbook_sheets(path: Path) -> list[str]:
    wb = load_workbook(path, read_only=True)
    return list(wb.sheetnames)


def _lot_id(collection_id: str, oracle_id: str, location_id: str) -> str:
    digest = hashlib.sha256(f"{collection_id}|{oracle_id}|{location_id}".encode()).hexdigest()[:20]
    return f"lot-{digest}"


def _ensure_collection(store: Store, collection_id: str, title: str, source_id: str) -> None:
    store.conn.execute(
        "INSERT OR IGNORE INTO collection(collection_id,title,source_id,created_at) VALUES(?,?,?,?)",
        (collection_id, title, source_id, utcnow()))


def _ensure_location(store: Store, collection_id: str, location_id: str,
                     name: str, ltype: str | None = None, ownership: str | None = None) -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO location(location_id,collection_id,location_name,location_type,"
        "ownership_semantics) VALUES(?,?,?,?,?)",
        (location_id, collection_id, name, ltype, ownership))


def _upsert_lot(store: Store, *, collection_id: str, card_id: str | None, oracle_id: str,
                location_id: str, quantity: int | None, quantity_exact: int | None,
                quantity_lower_bound: int | None, reserved: int = 0,
                reserved_assumption: str | None = None, condition: str | None = None,
                printing_ref: str | None = None, pool_status: str | None = None,
                note: str | None = None, source_id: str,
                physical_lot_id: str | None = None) -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO physical_lot(physical_lot_id,collection_id,card_id,oracle_id,"
        "location_id,quantity,quantity_exact,quantity_lower_bound,reserved_quantity,"
        "reserved_assumption,condition,printing_ref,pool_status,note,source_id)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (physical_lot_id or _lot_id(collection_id, oracle_id, location_id),
         collection_id, card_id, oracle_id, location_id, quantity, quantity_exact,
         quantity_lower_bound, reserved, reserved_assumption, condition, printing_ref,
         pool_status, note, source_id))


# ---------------------------------------------------------------------------
# A) Normalized workbook
# ---------------------------------------------------------------------------

def import_normalized_workbook(store: Store, path: str | Path,
                               collection_id: str = "normalized-1414") -> dict[str, object]:
    path = Path(path)
    sheets = _workbook_sheets(path)
    required = {"01_CARD_IDENTITY", "02_PHYSICAL_LOTS", "03_LOCATIONS", "05_INVENTORY_CURRENT"}
    missing = required - set(sheets)
    if missing:
        raise ImportFailure({"errors": [f"normalized workbook missing sheets: {sorted(missing)}"]})
    source_id = f"normalized:{sha256_file(path)[:16]}"
    report: dict[str, object] = {"format": "normalized", "collection_id": collection_id,
                                 "sheets": {}}
    try:
        store.add_source(source_id=source_id, source_name="Normalized collection workbook",
                         file_name=path.name, sha256=sha256_file(path))
        _ensure_collection(store, collection_id, "Normalized collection (reference profile)",
                           source_id)
        identities = _sheet_rows(path, "01_CARD_IDENTITY")
        id_by_card: dict[str, dict] = {}
        for r in identities:
            card_id = _text(r.get("card_id"))
            oracle_id = _text(r.get("oracle_id"))
            if not card_id or not oracle_id:
                raise ImportFailure({"errors": [f"01_CARD_IDENTITY row without card_id/oracle_id: {r}"]})
            id_by_card[card_id] = r
            store.conn.execute(
                "INSERT OR REPLACE INTO card_identity(card_id,oracle_id,oracle_name,german_name,"
                "color_identity,mana_cost,mana_value,type_line,oracle_text,is_basic_land,"
                "commander_legal,legality_verified_at,identity_evidence,source_id)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (card_id, oracle_id, _text(r.get("oracle_name")), _text(r.get("german_name")),
                 _text(r.get("color_identity")), _text(r.get("mana_cost")),
                 r.get("mana_value") if isinstance(r.get("mana_value"), (int, float)) else None,
                 _text(r.get("type_line")), _text(r.get("oracle_text")),
                 _flag(r.get("is_basic_land")) or 0, _flag(r.get("commander_legal")),
                 _text(r.get("legality_verified_at")), _text(r.get("identity_evidence_type")),
                 source_id))
        report["sheets"]["01_CARD_IDENTITY"] = len(identities)  # type: ignore[index]

        locations = _sheet_rows(path, "03_LOCATIONS")
        loc_ids: set[str] = set()
        for r in locations:
            lid = _text(r.get("location_id"))
            if lid:
                loc_ids.add(lid)
                _ensure_location(store, collection_id, lid,
                                 _text(r.get("location_name")) or lid,
                                 _text(r.get("location_type")),
                                 _text(r.get("ownership_semantics")))
        report["sheets"]["03_LOCATIONS"] = len(locations)  # type: ignore[index]

        lots = _sheet_rows(path, "02_PHYSICAL_LOTS")
        for r in lots:
            lot_id = _text(r.get("physical_lot_id"))
            card_id = _text(r.get("card_id"))
            if not lot_id or not card_id or card_id not in id_by_card:
                raise ImportFailure({"errors": [f"02_PHYSICAL_LOTS row with unknown card_id: {r}"]})
            lid = _text(r.get("location_id")) or "unknown"
            if lid not in loc_ids:
                _ensure_location(store, collection_id, lid, lid)
                loc_ids.add(lid)
            observed = _int(r.get("quantity_observed"), field="quantity_observed", ctx=lot_id)
            lower = _int(r.get("quantity_lower_bound"), field="quantity_lower_bound", ctx=lot_id)
            exact = _flag(r.get("quantity_exact"))
            # Effective quantity: exact observed value if flagged exact, else
            # the lower bound is the defensible available figure; a missing
            # quantity stays NULL (unknown), never 0.
            quantity = observed if observed is not None else lower
            _upsert_lot(
                store, collection_id=collection_id, card_id=card_id,
                oracle_id=str(id_by_card[card_id].get("oracle_id")),
                location_id=lid, quantity=quantity, quantity_exact=exact,
                quantity_lower_bound=lower,
                reserved=_int(r.get("reserved_quantity"), field="reserved_quantity",
                              ctx=lot_id) or 0,
                condition=_text(r.get("condition")),
                printing_ref=_text(r.get("printing_ref")),
                pool_status=_text(r.get("pool_status")), note=_text(r.get("note")),
                source_id=source_id, physical_lot_id=lot_id)
        report["sheets"]["02_PHYSICAL_LOTS"] = len(lots)  # type: ignore[index]

        current = _sheet_rows(path, "05_INVENTORY_CURRENT")
        report["sheets"]["05_INVENTORY_CURRENT"] = len(current)  # type: ignore[index]
        # Cross-check reported current totals against imported lots.
        lot_totals: dict[str, int] = {}
        for r in store.conn.execute(
                "SELECT oracle_id, COALESCE(SUM(quantity),0) q FROM physical_lot"
                " WHERE collection_id=? GROUP BY oracle_id", (collection_id,)):
            lot_totals[r["oracle_id"]] = r["q"]
        mismatches = []
        for r in current:
            card_id = _text(r.get("card_id"))
            reported = _int(r.get("observed_quantity"), field="observed_quantity",
                            ctx=str(card_id))
            if card_id in id_by_card and reported is not None:
                oid = str(id_by_card[card_id].get("oracle_id"))
                if lot_totals.get(oid, 0) != reported:
                    mismatches.append({"card_id": card_id, "reported": reported,
                                       "lots_total": lot_totals.get(oid, 0)})
        report["inventory_current_mismatches"] = mismatches

        for extra in ("04_INVENTORY_EVENTS", "06_SOURCES", "07_DATA_QUALITY",
                      "09_PRINTING_DETAILS", "10_NORMALIZATION_AUDIT"):
            if extra in sheets:
                rows = _sheet_rows(path, extra)
                report["sheets"][extra] = len(rows)  # type: ignore[index]
                if extra == "04_INVENTORY_EVENTS":
                    store.conn.executemany(
                        "INSERT INTO inventory_event(collection_id,sheet,card_id,event_type,"
                        "detail,source_id) VALUES(?,?,?,?,?,?)",
                        [(collection_id, extra, _text(r.get("card_id")),
                          _text(r.get("event_type")), json.dumps(
                              {k: (str(v) if v is not None else None) for k, v in r.items()},
                              ensure_ascii=False), source_id) for r in rows])
        store.conn.commit()
    except ImportFailure:
        store.conn.rollback()
        raise
    except Exception as exc:
        store.conn.rollback()
        raise ImportFailure({"errors": [f"normalized import failed, rolled back: {exc}"]}) from exc
    report["identities"] = len(id_by_card)
    report["lots"] = len(lots)
    return report


# ---------------------------------------------------------------------------
# B) Foundation / Schwarze Box (7 columns) + shared name-resolution core
# ---------------------------------------------------------------------------

def _resolve_names(store: Store, names: list[str]) -> tuple[dict[str, str], list[dict]]:
    """Exact paper-name resolution. Returns (name -> oracle_id, errors)."""
    resolved: dict[str, str] = {}
    errors: list[dict] = []
    for name in sorted(set(names)):
        rows = store.scryfall_by_name(name)
        oracle_ids = {r["oracle_id"] for r in rows}
        if len(oracle_ids) == 1:
            resolved[name] = next(iter(oracle_ids))
        elif not oracle_ids:
            errors.append({"name": name, "problem": "unresolved"})
        else:
            errors.append({"name": name, "problem": "ambiguous",
                           "oracle_ids": sorted(oracle_ids)})
    return resolved, errors


def _import_simple_rows(store: Store, *, collection_id: str, title: str,
                        rows: list[dict[str, object]], source_id: str,
                        source_name: str, file_name: str, file_sha: str,
                        mode: str = "upsert") -> dict[str, object]:
    """rows: dicts with name, quantity, location, reserved(optional), condition(optional)."""
    if mode not in {"upsert", "replace-snapshot"}:
        raise ImportFailure({"errors": [f"unknown import mode {mode!r}"]})
    resolved, errors = _resolve_names(store, [str(r["name"]) for r in rows])
    if errors:
        raise ImportFailure({"format": "simple", "collection_id": collection_id,
                             "errors": errors,
                             "note": "import aborted, nothing written (transaction rolled back)"})
    seen_keys: set[tuple[str, str]] = set()
    total_copies = 0
    locations: dict[str, int] = {}
    try:
        store.add_source(source_id=source_id, source_name=source_name, file_name=file_name,
                         sha256=file_sha,
                         note=f"reserved=0 assumption: {RESERVED_ASSUMPTION}"
                         if any(r.get("reserved") is None for r in rows) else "")
        _ensure_collection(store, collection_id, title, source_id)
        aggregated: dict[tuple[str, str], dict] = {}
        for r in rows:
            oid = resolved[str(r["name"])]
            loc_name = str(r["location"])
            key = (oid, loc_name)
            agg = aggregated.setdefault(key, {"quantity": 0, "reserved": None,
                                              "condition": r.get("condition")})
            qty = r.get("quantity")
            if qty is None:
                raise ImportFailure({"errors": [f"{r['name']}: quantity missing (missing != 0)"]})
            agg["quantity"] += int(qty)  # type: ignore[operator]
            if r.get("reserved") is not None:
                agg["reserved"] = (agg["reserved"] or 0) + int(r["reserved"])  # type: ignore[operator]
            total_copies += int(qty)  # type: ignore[arg-type]
            locations[loc_name] = locations.get(loc_name, 0) + int(qty)  # type: ignore[arg-type]
            seen_keys.add(key)
        for (oid, loc_name), agg in aggregated.items():
            location_id = loc_name  # literal location name is the id: never merged/renamed
            _ensure_location(store, collection_id, location_id, loc_name)
            reserved_known = agg["reserved"] is not None
            _upsert_lot(
                store, collection_id=collection_id, card_id=None, oracle_id=oid,
                location_id=location_id, quantity=agg["quantity"], quantity_exact=1,
                quantity_lower_bound=agg["quantity"],
                reserved=agg["reserved"] or 0,
                reserved_assumption=None if reserved_known else RESERVED_ASSUMPTION,
                condition=agg.get("condition"), source_id=source_id)
        if mode == "replace-snapshot":
            # Explicit, audited deletion of lots absent from this snapshot.
            existing = store.conn.execute(
                "SELECT oracle_id, location_id FROM physical_lot WHERE collection_id=?",
                (collection_id,)).fetchall()
            removed = 0
            for r in existing:
                if (r["oracle_id"], r["location_id"]) not in seen_keys:
                    store.conn.execute(
                        "DELETE FROM physical_lot WHERE collection_id=? AND oracle_id=?"
                        " AND location_id=?",
                        (collection_id, r["oracle_id"], r["location_id"]))
                    store.conn.execute(
                        "INSERT INTO inventory_event(collection_id,sheet,card_id,event_type,"
                        "detail,source_id) VALUES(?,?,?,?,?,?)",
                        (collection_id, "replace-snapshot", None, "lot_removed",
                         f"oracle_id={r['oracle_id']} location_id={r['location_id']}", source_id))
                    removed += 1
            removed_count = removed
        else:
            removed_count = 0
        store.conn.commit()
    except ImportFailure:
        store.conn.rollback()
        raise
    except Exception as exc:
        store.conn.rollback()
        raise ImportFailure({"errors": [f"import failed, rolled back: {exc}"]}) from exc
    return {"format": "simple", "collection_id": collection_id, "mode": mode,
            "rows": len(rows), "identities": len({oid for oid, _ in seen_keys}),
            "copies": total_copies, "locations": locations,
            "lots_upserted": len(aggregated), "lots_removed": removed_count,
            "reserved_assumption": RESERVED_ASSUMPTION}


def import_foundation_workbook(store: Store, path: str | Path,
                               mode: str = "upsert") -> dict[str, object]:
    path = Path(path)
    sheets = _workbook_sheets(path)
    if "Kartensammlung" not in sheets:
        raise ImportFailure({"errors": [f"sheet 'Kartensammlung' missing, found {sheets}"]})
    raw = _sheet_rows(path, "Kartensammlung")
    rows: list[dict[str, object]] = []
    for r in raw:
        name = _text(r.get("Kartenname"))
        if not name:
            continue
        rows.append({
            "name": name,
            "quantity": _int(r.get("Anzahl"), field="Anzahl", ctx=name),
            "location": _text(r.get("Standort")) or "unknown",
            "reserved": None,   # not present in this source — declared assumption
            "condition": None,  # not present in this source
        })
    sha = sha256_file(path)
    return _import_simple_rows(
        store, collection_id=FOUNDATION_COLLECTION,
        title="Foundation / Schwarze Box (primary)",
        rows=rows, source_id=f"foundation:{sha[:16]}",
        source_name="Kartensammlung_Foundation_Schwarze_Box.xlsx",
        file_name=path.name, file_sha=sha, mode=mode)


# ---------------------------------------------------------------------------
# C) Generic format via explicit mapping config
# ---------------------------------------------------------------------------

def import_mapped_file(store: Store, path: str | Path, mapping: dict) -> dict[str, object]:
    path = Path(path)
    collection_id = str(mapping["collection_id"])
    cols = mapping["columns"]
    raw_rows: list[dict[str, object]] = []
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as fh:
            raw_rows = [dict(r) for r in csv.DictReader(fh)]
    elif path.suffix.lower() in {".xlsx", ".xlsm"}:
        sheet = mapping.get("sheet") or _workbook_sheets(path)[0]
        raw_rows = _sheet_rows(path, sheet)
    else:
        raise ImportFailure({"errors": [f"unsupported file type {path.suffix}"]})

    def pick(r: dict, key: str):
        col = cols.get(key)
        return r.get(col) if col else None

    rows = []
    for r in raw_rows:
        name = _text(pick(r, "name"))
        if not name:
            continue
        rows.append({"name": name,
                     "quantity": _int(pick(r, "quantity"), field="quantity", ctx=name),
                     "location": _text(pick(r, "location")) or "unknown",
                     "reserved": _int(pick(r, "reserved"), field="reserved", ctx=name)
                     if cols.get("reserved") else None,
                     "condition": _text(pick(r, "condition"))})
    sha = sha256_file(path)
    return _import_simple_rows(
        store, collection_id=collection_id, title=f"Mapped import {collection_id}",
        rows=rows, source_id=f"mapped:{collection_id}:{sha[:16]}",
        source_name=f"mapped import ({path.name})", file_name=path.name, file_sha=sha,
        mode=str(mapping.get("mode", "upsert")))


def detect_and_import(store: Store, path: str | Path, *,
                      mapping: dict | None = None,
                      mode: str = "upsert") -> dict[str, object]:
    """Dispatch on the documented sheet signatures only."""
    path = Path(path)
    if mapping is not None:
        return import_mapped_file(store, path, mapping)
    if path.suffix.lower() == ".csv":
        raise ImportFailure({"errors": ["CSV import requires an explicit --mapping config"]})
    sheets = set(_workbook_sheets(path))
    if "01_CARD_IDENTITY" in sheets:
        return import_normalized_workbook(store, path)
    if "Kartensammlung" in sheets:
        return import_foundation_workbook(store, path, mode=mode)
    raise ImportFailure({"errors": [f"unknown workbook signature, sheets={sorted(sheets)}; "
                                    "use --mapping for generic files"]})


def normalization_report(store: Store) -> dict[str, object]:
    """Reconciliation report: identities, lots, copies, locations, commander count."""
    from .commander import commander_candidates

    report: dict[str, object] = {"collections": []}
    for coll in store.collections():
        cid = coll["collection_id"]
        rows = store.inventory_rows(cid)
        copies = sum(r["quantity"] or 0 for r in rows)
        per_location: dict[str, int] = {}
        for r in rows:
            per_location[r["location_id"]] = per_location.get(r["location_id"], 0) + (r["quantity"] or 0)
        candidates = commander_candidates(store, cid)
        report["collections"].append({  # type: ignore[attr-defined]
            "collection_id": cid,
            "source_rows": len(rows),
            "distinct_oracle_identities": len({r["oracle_id"] for r in rows}),
            "copies_reported": copies,
            "locations": per_location,
            "unresolved_identities": sum(1 for r in rows if r["name"] is None),
            "commanders_eligible": len(candidates["eligible"]),
            "commanders_needs_review": len(candidates["needs_review"]),
            "reserved_assumption": RESERVED_ASSUMPTION,
        })
    return report
