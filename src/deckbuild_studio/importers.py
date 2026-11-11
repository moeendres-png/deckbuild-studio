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
import math
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
    """Strict quantity parsing (QA P1.7). Negative, fractional (1.9),
    non-numeric and non-finite quantities are import ERRORS with a clear
    per-row message — never silently truncated by int(). Empty stays
    None (missing != 0). Integral floats from spreadsheet cells (2.0)
    and German decimal strings naming a whole number ('2,0') are fine."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None

    def fail(reason: str) -> ImportFailure:
        return ImportFailure({"errors": [f"{ctx}: {field}={v!r} {reason}"]})

    if isinstance(v, bool):
        raise fail("is not an integer quantity")
    if isinstance(v, int):
        value = v
    elif isinstance(v, float):
        if not math.isfinite(v):
            raise fail("is not finite")
        if v != math.floor(v):
            raise fail("is fractional; quantities must be whole numbers")
        value = int(v)
    elif isinstance(v, str):
        s = v.strip()
        try:
            value = int(s)
        except ValueError:
            try:
                f = float(s.replace(",", "."))
            except ValueError:
                raise fail("is not an integer") from None
            if not math.isfinite(f):
                raise fail("is not finite")
            if f != math.floor(f):
                raise fail("is fractional; quantities must be whole numbers")
            value = int(f)
    else:
        raise fail("is not an integer")
    if value < 0:
        raise fail("is negative; quantities must be >= 0")
    return value


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


def _lot_id(collection_id: str, oracle_id: str, location_id: str, lot_key: str = "") -> str:
    base = f"{collection_id}|{oracle_id}|{location_id}"
    if lot_key:
        base += f"|{lot_key}"
    digest = hashlib.sha256(base.encode()).hexdigest()[:20]
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
                physical_lot_id: str | None = None, lot_key: str = "") -> None:
    store.conn.execute(
        "INSERT OR REPLACE INTO physical_lot(physical_lot_id,collection_id,card_id,oracle_id,"
        "location_id,lot_key,quantity,quantity_exact,quantity_lower_bound,reserved_quantity,"
        "reserved_assumption,condition,printing_ref,pool_status,note,source_id)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (physical_lot_id or _lot_id(collection_id, oracle_id, location_id, lot_key),
         collection_id, card_id, oracle_id, location_id, lot_key, quantity, quantity_exact,
         quantity_lower_bound, reserved, reserved_assumption, condition, printing_ref,
         pool_status, note, source_id))


# ---------------------------------------------------------------------------
# card_id resolution (QA P1.4): every imported lot references a stable
# card_identity. Order: (1) existing card_identity for the oracle_id,
# (2) an explicitly supplied card_id registry, (3) a deterministically
# GENERATED id, openly marked as generated. Known ids are never silently
# regenerated; a later registry can replace generated ids via
# apply_card_id_registry().
# ---------------------------------------------------------------------------

def generated_card_id(oracle_id: str) -> str:
    """Deterministic fallback card_id for an oracle identity without a
    known local id: 'card_' + sha256(oracle_id)[:24]. Documented as
    GENERATED (identity_evidence), replaceable by a registry import."""
    return "card_" + hashlib.sha256(oracle_id.encode()).hexdigest()[:24]


def load_card_id_registry(path: str | Path) -> dict[str, str]:
    """Read an oracle_id -> card_id registry from JSON or CSV.

    JSON: {"<oracle_id>": "<card_id>", ...} or a list of
    {"oracle_id": ..., "card_id": ...} objects (a wrapping "mappings"
    object is also accepted). CSV: columns oracle_id,card_id."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as fh:
            out = {}
            for row in csv.DictReader(fh):
                oid, cid = _text(row.get("oracle_id")), _text(row.get("card_id"))
                if oid and cid:
                    out[oid] = cid
            return out
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("mappings"), dict):
        data = data["mappings"]
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items() if k and v}
    if isinstance(data, list):
        out = {}
        for item in data:
            if isinstance(item, dict) and item.get("oracle_id") and item.get("card_id"):
                out[str(item["oracle_id"])] = str(item["card_id"])
        return out
    raise ImportFailure({"errors": [f"unsupported card_id registry format in {path.name}"]})


def _coerce_registry(registry: object) -> dict[str, str]:
    if registry is None:
        return {}
    if isinstance(registry, dict):
        return {str(k): str(v) for k, v in registry.items()}
    return load_card_id_registry(registry)  # type: ignore[arg-type]


def _ensure_card_identity(store: Store, oracle_id: str, source_id: str,
                          registry: dict[str, str] | None = None) -> str:
    """Resolve or create the card_identity for an oracle_id (QA P1.4
    order: existing identity -> registry -> generated). Facts are copied
    from the local Scryfall store when available."""
    row = store.conn.execute(
        "SELECT card_id FROM card_identity WHERE oracle_id=? ORDER BY card_id",
        (oracle_id,)).fetchone()
    if row:
        return str(row["card_id"])
    from_registry = bool(registry and registry.get(oracle_id))
    card_id = registry[oracle_id] if from_registry else generated_card_id(oracle_id)
    sf = store.scryfall(oracle_id)
    legal = None
    if sf is not None and sf["commander_legality"] is not None:
        legal = 1 if sf["commander_legality"] == "legal" else 0
    store.conn.execute(
        "INSERT OR IGNORE INTO card_identity(card_id,oracle_id,oracle_name,german_name,"
        "color_identity,mana_cost,mana_value,type_line,oracle_text,is_basic_land,"
        "commander_legal,legality_verified_at,identity_evidence,source_id)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (card_id, oracle_id,
         sf["name"] if sf else None, None,
         sf["color_identity"] if sf else None,
         sf["mana_cost"] if sf else None,
         sf["mana_value"] if sf else None,
         sf["type_line"] if sf else None,
         sf["oracle_text"] if sf else None,
         1 if sf and "Basic" in (sf["type_line"] or "") and "Land" in (sf["type_line"] or "") else 0,
         legal, utcnow(),
         "card_id_registry" if from_registry else "generated:sha256(oracle_id)",
         source_id))
    row = store.conn.execute(
        "SELECT card_id FROM card_identity WHERE oracle_id=? ORDER BY card_id",
        (oracle_id,)).fetchone()
    return str(row["card_id"])


def apply_card_id_registry(store: Store, registry: object, *,
                           source_id: str = "card-id-registry:manual") -> dict[str, object]:
    """Apply an oracle_id -> card_id registry AFTER an import (QA P1.4).

    Generated ids are replaced by the registered known ids, and all
    physical lots follow consistently. An existing NON-generated id that
    disagrees with the registry is reported as a conflict and NOT
    overwritten silently; a card_id already owned by another oracle_id
    is likewise a conflict. Lots still carrying card_id=NULL receive the
    resolved id."""
    reg = _coerce_registry(registry)
    report: dict[str, object] = {"replaced": 0, "created": 0, "filled_lots": 0,
                                 "unchanged": 0, "conflicts": []}
    conflicts: list[dict] = report["conflicts"]  # type: ignore[assignment]
    try:
        for oracle_id, new_id in sorted(reg.items()):
            owner = store.conn.execute(
                "SELECT oracle_id FROM card_identity WHERE card_id=?", (new_id,)).fetchone()
            if owner is not None and owner["oracle_id"] != oracle_id:
                conflicts.append({"oracle_id": oracle_id, "card_id": new_id,
                                  "problem": "card_id already belongs to another oracle_id"})
                continue
            row = store.conn.execute(
                "SELECT card_id FROM card_identity WHERE oracle_id=? ORDER BY card_id",
                (oracle_id,)).fetchone()
            if row is None:
                _ensure_card_identity(store, oracle_id, source_id, reg)
                report["created"] = int(report["created"]) + 1
                current = new_id
            elif row["card_id"] == new_id:
                report["unchanged"] = int(report["unchanged"]) + 1
                current = new_id
            elif row["card_id"] == generated_card_id(oracle_id):
                old_id = str(row["card_id"])
                store.conn.execute("UPDATE card_identity SET card_id=? WHERE card_id=?",
                                   (new_id, old_id))
                cur = store.conn.execute("UPDATE physical_lot SET card_id=? WHERE card_id=?",
                                         (new_id, old_id))
                report["replaced"] = int(report["replaced"]) + 1
                report["filled_lots"] = int(report["filled_lots"]) + cur.rowcount
                current = new_id
            else:
                conflicts.append({"oracle_id": oracle_id, "card_id": new_id,
                                  "problem": f"existing non-generated card_id "
                                             f"{row['card_id']!r} kept"})
                current = str(row["card_id"])
            cur = store.conn.execute(
                "UPDATE physical_lot SET card_id=? WHERE oracle_id=? AND card_id IS NULL",
                (current, oracle_id))
            report["filled_lots"] = int(report["filled_lots"]) + cur.rowcount
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    return report


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
                # QA P1.5: the real physical_lot_id is the lot_key, so
                # several distinct lots of one card at one location stay
                # separate rows instead of collapsing into one.
                source_id=source_id, physical_lot_id=lot_id, lot_key=lot_id)
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
                        mode: str = "upsert",
                        card_id_registry: object = None) -> dict[str, object]:
    """rows: dicts with name, quantity, location, reserved(optional), condition(optional)."""
    if mode not in {"upsert", "replace-snapshot"}:
        raise ImportFailure({"errors": [f"unknown import mode {mode!r}"]})
    if store.conn.execute("SELECT COUNT(*) FROM scryfall_card").fetchone()[0] == 0:
        # QA P1.8: name resolution is impossible without the catalogue;
        # fail loudly with the correct start order instead of reporting
        # every single name as "unresolved".
        raise ImportFailure({"errors": [
            "Scryfall store is empty — no card name can be resolved. "
            "Zuerst import-scryfall/sync-scryfall ausführen "
            "('mtg-deckbuilder sync-scryfall' or "
            "'mtg-deckbuilder import-scryfall <default-cards file>'), "
            "then the inventory import."]})
    registry = _coerce_registry(card_id_registry)
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
            # QA P1.7 (defence in depth): quantities must already have
            # passed the strict _int() validation at the parsing layer.
            if isinstance(qty, bool) or not isinstance(qty, int):
                raise ImportFailure({"errors": [
                    f"{r['name']}: quantity={qty!r} is not a validated integer"]})
            if qty < 0:
                raise ImportFailure({"errors": [
                    f"{r['name']}: quantity={qty} is negative"]})
            res = r.get("reserved")
            if res is not None and (isinstance(res, bool) or not isinstance(res, int) or res < 0):
                raise ImportFailure({"errors": [
                    f"{r['name']}: reserved={res!r} is not a valid quantity"]})
            agg["quantity"] += qty
            if res is not None:
                agg["reserved"] = (agg["reserved"] or 0) + res
            total_copies += qty
            locations[loc_name] = locations.get(loc_name, 0) + qty
            seen_keys.add(key)
        card_ids: dict[str, str] = {}
        for (oid, loc_name), agg in aggregated.items():
            location_id = loc_name  # literal location name is the id: never merged/renamed
            _ensure_location(store, collection_id, location_id, loc_name)
            reserved_known = agg["reserved"] is not None
            # QA P1.4: never leave a lot with card_id=NULL — resolve the
            # stable card_identity (existing -> registry -> generated).
            if oid not in card_ids:
                card_ids[oid] = _ensure_card_identity(store, oid, source_id, registry)
            _upsert_lot(
                store, collection_id=collection_id, card_id=card_ids[oid], oracle_id=oid,
                location_id=location_id, quantity=agg["quantity"], quantity_exact=1,
                quantity_lower_bound=agg["quantity"],
                reserved=agg["reserved"] or 0,
                reserved_assumption=None if reserved_known else RESERVED_ASSUMPTION,
                condition=agg.get("condition"), source_id=source_id, lot_key="")
        if mode == "replace-snapshot":
            # Explicit, audited deletion of aggregated snapshot lots
            # (lot_key='') absent from this snapshot. Distinct lots owned
            # via lot_key (normalized imports) are never touched here.
            existing = store.conn.execute(
                "SELECT oracle_id, location_id FROM physical_lot WHERE collection_id=?"
                " AND lot_key=''",
                (collection_id,)).fetchall()
            removed = 0
            for r in existing:
                if (r["oracle_id"], r["location_id"]) not in seen_keys:
                    store.conn.execute(
                        "DELETE FROM physical_lot WHERE collection_id=? AND oracle_id=?"
                        " AND location_id=? AND lot_key=''",
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
            "card_ids_resolved": len(card_ids),
            "reserved_assumption": RESERVED_ASSUMPTION}


def import_foundation_workbook(store: Store, path: str | Path,
                               mode: str = "upsert",
                               card_id_registry: object = None) -> dict[str, object]:
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
        file_name=path.name, file_sha=sha, mode=mode,
        card_id_registry=card_id_registry)


# ---------------------------------------------------------------------------
# C) Generic format via explicit mapping config
# ---------------------------------------------------------------------------

def import_mapped_file(store: Store, path: str | Path, mapping: dict,
                       card_id_registry: object = None) -> dict[str, object]:
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
        mode=str(mapping.get("mode", "upsert")), card_id_registry=card_id_registry)


def detect_and_import(store: Store, path: str | Path, *,
                      mapping: dict | None = None,
                      mode: str = "upsert",
                      card_id_registry: object = None) -> dict[str, object]:
    """Dispatch on the documented sheet signatures only."""
    path = Path(path)
    if mapping is not None:
        return import_mapped_file(store, path, mapping, card_id_registry=card_id_registry)
    if path.suffix.lower() == ".csv":
        raise ImportFailure({"errors": ["CSV import requires an explicit --mapping config"]})
    sheets = set(_workbook_sheets(path))
    if "01_CARD_IDENTITY" in sheets:
        return import_normalized_workbook(store, path)
    if "Kartensammlung" in sheets:
        return import_foundation_workbook(store, path, mode=mode,
                                          card_id_registry=card_id_registry)
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
