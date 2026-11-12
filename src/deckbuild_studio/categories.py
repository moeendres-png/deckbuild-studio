"""Card categories — the type layer and the category bookkeeping.

Three strictly separate layers live here / in :mod:`roles` /
:mod:`tagger`; they are never merged silently, every claim keeps its
origin:

1. **Type facts** (this module): supertypes / types / subtypes per
   face plus Scryfall keywords, parsed deterministically from the
   locally held Scryfall bulk catalogue (the same file the Scryfall
   store was imported from) with :mod:`typeline` (versioned parser).
   When no bulk file is present, facts fall back to the stored
   ``scryfall_card`` columns (front face exact; further faces only
   their type lines — their oracle texts and all keywords are then
   honestly missing and the run is recorded as PARTIAL).
2. **Function categories** (:mod:`roles`): heuristic claims
   (``ORACLE_TEXT_HEURISTIC``), structural estimates
   (``STRUCTURAL_PROFILE``) and Scryfall-Tagger claims
   (``SCRYFALL_TAGGER_SEARCH``, synced by :mod:`tagger`).
3. **Checked bookkeeping** (this module): ``card_category_check``
   records, per card and origin, that a layer actually *examined* the
   card — including the outcome "no category". A card without claims
   is therefore distinguishable from a card never checked.

Every derivation/sync writes a ``category_run`` row (layer, version,
source, status, coverage) — provenance as everywhere in this project.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .scryfall import NONPLAYABLE_LAYOUTS, _objects
from .store import Store, sha256_file, utcnow
from .typeline import TYPE_PARSER_VERSION, parse_type_line, split_faces

CATEGORIES_VERSION = "categories/1.0.0"
LAYER_TYPE_FACTS = "type_facts"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS card_face (
    oracle_id TEXT NOT NULL,
    face_index INTEGER NOT NULL,
    face_name TEXT,
    type_line TEXT,
    oracle_text TEXT,
    mana_cost TEXT,
    source_id TEXT,
    parser_version TEXT NOT NULL,
    PRIMARY KEY (oracle_id, face_index)
);
CREATE TABLE IF NOT EXISTS card_type_component (
    oracle_id TEXT NOT NULL,
    face_index INTEGER NOT NULL,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (oracle_id, face_index, kind, value)
);
CREATE INDEX IF NOT EXISTS card_type_component_value
    ON card_type_component(kind, value);
CREATE TABLE IF NOT EXISTS card_keyword (
    oracle_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    source_id TEXT,
    PRIMARY KEY (oracle_id, keyword)
);
CREATE INDEX IF NOT EXISTS card_keyword_value ON card_keyword(keyword);
CREATE TABLE IF NOT EXISTS card_category_check (
    oracle_id TEXT NOT NULL,
    origin TEXT NOT NULL,
    version TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    claims INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (oracle_id, origin)
);
CREATE TABLE IF NOT EXISTS card_tagger_claim (
    oracle_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    category TEXT NOT NULL,
    snapshot_id TEXT,
    PRIMARY KEY (oracle_id, tag)
);
CREATE INDEX IF NOT EXISTS card_tagger_claim_category
    ON card_tagger_claim(category);
CREATE TABLE IF NOT EXISTS category_run (
    run_id TEXT PRIMARY KEY,
    layer TEXT NOT NULL,
    version TEXT NOT NULL,
    source_id TEXT,
    status TEXT NOT NULL,
    cards_total INTEGER NOT NULL DEFAULT 0,
    cards_covered INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def ensure_schema(store: Store) -> None:
    store.conn.executescript(_SCHEMA)
    # position (print order of a component within its face) was added
    # after the first derivation runs; upgrade in place, idempotently.
    cols = {r[1] for r in store.conn.execute(
        "PRAGMA table_info(card_type_component)")}
    if cols and "position" not in cols:
        store.conn.execute(
            "ALTER TABLE card_type_component "
            "ADD COLUMN position INTEGER NOT NULL DEFAULT 0")


def write_run(store: Store, *, layer: str, version: str,
              source_id: str | None, status: str, cards_total: int,
              cards_covered: int, detail: str = "") -> str:
    """Record one derivation/sync run (provenance for a whole layer)."""
    ensure_schema(store)
    stamp = utcnow()
    run_id = "run-" + hashlib.sha256(
        f"{layer}|{version}|{stamp}|{detail}".encode()).hexdigest()[:24]
    store.conn.execute(
        "INSERT OR REPLACE INTO category_run(run_id,layer,version,source_id,"
        "status,cards_total,cards_covered,detail,created_at) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (run_id, layer, version, source_id, status, cards_total,
         cards_covered, detail, stamp))
    return run_id


def record_checks(store: Store, *, origin: str, version: str,
                  claims_by_card: dict[str, int]) -> None:
    """Upsert 'this layer examined this card' rows (claims may be 0)."""
    ensure_schema(store)
    stamp = utcnow()
    store.conn.executemany(
        "INSERT OR REPLACE INTO card_category_check(oracle_id,origin,version,"
        "checked_at,claims) VALUES(?,?,?,?,?)",
        [(oid, origin, version, stamp, int(n))
         for oid, n in claims_by_card.items()])


# ---------------------------------------------------------------------------
# Type-fact derivation
# ---------------------------------------------------------------------------

def find_bulk_file(store: Store) -> Path | None:
    """The local Scryfall bulk file next to this store's database —
    the file ``sync-scryfall`` downloaded / ``import-scryfall`` read."""
    root = Path(store.path).parent
    for folder in (root / "scryfall", root):
        for name in ("default-cards.jsonl.gz", "default-cards.json.gz",
                     "default-cards.jsonl", "default-cards.json",
                     "default-cards.download"):
            candidate = folder / name
            if candidate.exists():
                return candidate
    return None


def _faces_from_bulk(store: Store, bulk_path: Path,
                     store_ids: set[str]) -> tuple[dict, dict, dict]:
    """oracle_id -> (faces, keywords, counts) from the bulk file.

    First printing per oracle_id wins — the same convention as
    :func:`deckbuild_studio.scryfall.import_scryfall`, so the facts
    describe the same representative printing the store shows."""
    faces_by_id: dict[str, list[dict]] = {}
    keywords_by_id: dict[str, list[str]] = {}
    skipped_not_in_store = 0
    for card in _objects(bulk_path):
        oracle_id = card.get("oracle_id")
        if not oracle_id or card.get("layout") in NONPLAYABLE_LAYOUTS:
            continue
        if oracle_id in faces_by_id:
            continue
        if oracle_id not in store_ids:
            skipped_not_in_store += 1
            continue
        faces = card.get("card_faces") or [card]
        faces_by_id[oracle_id] = [
            {"name": f.get("name"), "type_line": f.get("type_line"),
             "oracle_text": f.get("oracle_text"),
             "mana_cost": f.get("mana_cost")}
            for f in faces]
        keywords_by_id[oracle_id] = [str(k) for k in (card.get("keywords") or [])]
    return faces_by_id, keywords_by_id, {"skipped_not_in_store": skipped_not_in_store}


def _faces_from_store(store: Store) -> dict[str, list[dict]]:
    """Fallback faces from the stored columns only: face type lines
    come from the combined ``type_line``; oracle text is stored only
    for the front face, keywords not at all (honest PARTIAL source)."""
    out: dict[str, list[dict]] = {}
    for row in store.conn.execute(
            "SELECT oracle_id, name, type_line, front_type_line, "
            "oracle_text, front_oracle_text, mana_cost FROM scryfall_card"):
        type_lines = split_faces(row["type_line"]) or (
            [row["front_type_line"]] if row["front_type_line"] else [])
        names = split_faces(row["name"])
        faces = []
        for i, type_line in enumerate(type_lines):
            faces.append({
                "name": names[i] if i < len(names) else None,
                "type_line": type_line,
                "oracle_text": (row["front_oracle_text"] or row["oracle_text"])
                               if i == 0 else None,
                "mana_cost": row["mana_cost"] if i == 0 else None,
            })
        out[row["oracle_id"]] = faces
    return out


def derive_card_types(store: Store, bulk_path: str | Path | None = None) -> dict:
    """(Re)build card_face / card_type_component / card_keyword.

    Deterministic and offline. Returns counts only; the run itself is
    recorded in ``category_run`` (status AVAILABLE only when a bulk
    file covered every card of the Scryfall store)."""
    ensure_schema(store)
    store_ids = {str(r[0]) for r in store.conn.execute(
        "SELECT oracle_id FROM scryfall_card")}
    path = Path(bulk_path) if bulk_path else find_bulk_file(store)
    source_id: str | None = None
    keywords_by_id: dict[str, list[str]] = {}
    extra: dict = {}
    if path is not None and path.exists():
        digest = sha256_file(path)
        source_id = f"scryfall:{digest[:16]}"
        store.add_source(
            source_id=source_id, source_name="Scryfall bulk (default-cards)",
            source_url="https://scryfall.com/docs/api/bulk-data",
            file_name=path.name, sha256=digest)
        faces_by_id, keywords_by_id, extra = _faces_from_bulk(
            store, path, store_ids)
        origin = "bulk"
    else:
        faces_by_id = _faces_from_store(store)
        origin = "db_fallback"
    face_rows: list[tuple] = []
    component_rows: list[tuple] = []
    keyword_rows: list[tuple] = []
    cards_with_keywords = 0
    for oracle_id, faces in faces_by_id.items():
        for idx, face in enumerate(faces):
            face_rows.append((oracle_id, idx, face["name"], face["type_line"],
                              face["oracle_text"], face["mana_cost"],
                              source_id, TYPE_PARSER_VERSION))
            parsed = parse_type_line(face["type_line"])
            for kind in ("supertypes", "types", "subtypes"):
                for position, value in enumerate(parsed[kind]):
                    component_rows.append(
                        (oracle_id, idx, kind[:-1], value, position))
        keywords = keywords_by_id.get(oracle_id) or []
        if keywords:
            cards_with_keywords += 1
        for keyword in keywords:
            keyword_rows.append((oracle_id, keyword, source_id))
    with store.conn:
        store.conn.execute("DELETE FROM card_face")
        store.conn.execute("DELETE FROM card_type_component")
        store.conn.execute("DELETE FROM card_keyword")
        store.conn.executemany(
            "INSERT OR REPLACE INTO card_face(oracle_id,face_index,face_name,"
            "type_line,oracle_text,mana_cost,source_id,parser_version) "
            "VALUES(?,?,?,?,?,?,?,?)", face_rows)
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_type_component(oracle_id,face_index,"
            "kind,value,position) VALUES(?,?,?,?,?)", component_rows)
        store.conn.executemany(
            "INSERT OR IGNORE INTO card_keyword(oracle_id,keyword,source_id) "
            "VALUES(?,?,?)", keyword_rows)
    covered = len(faces_by_id)
    total = len(store_ids)
    if origin == "bulk" and covered == total:
        status = "AVAILABLE"
    elif covered:
        status = "PARTIAL"
    else:
        status = "NOT_FOUND"
    detail = (f"source={origin}"
              + (f"; bulk={path.name}" if path is not None and origin == "bulk" else "")
              + f"; skipped_not_in_store={extra.get('skipped_not_in_store', 0)}")
    run_id = write_run(store, layer=LAYER_TYPE_FACTS,
                       version=TYPE_PARSER_VERSION, source_id=source_id,
                       status=status, cards_total=total,
                       cards_covered=covered, detail=detail)
    store.conn.commit()
    return {"run_id": run_id, "source": origin, "status": status,
            "cards_total": total, "cards_covered": covered,
            "faces": len(face_rows), "components": len(component_rows),
            "cards_with_keywords": cards_with_keywords,
            "keywords": len(keyword_rows),
            "skipped_not_in_store": extra.get("skipped_not_in_store", 0)}


# ---------------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------------

def _universe(store: Store, collection_id: str | None) -> list[str]:
    if collection_id:
        return [str(r[0]) for r in store.conn.execute(
            "SELECT DISTINCT oracle_id FROM physical_lot "
            "WHERE collection_id = ?", (collection_id,))]
    return [str(r[0]) for r in store.conn.execute(
        "SELECT oracle_id FROM scryfall_card")]


def card_type_info(store: Store, oracle_ids: list[str]) -> dict[str, dict]:
    """Per-card type facts: faces (with parsed components), card-level
    unions of supertypes/types/subtypes, and keywords."""
    ensure_schema(store)
    out: dict[str, dict] = {}
    if not oracle_ids:
        return out
    marks = ",".join("?" for _ in oracle_ids)
    args = list(oracle_ids)
    for oid in oracle_ids:
        out[oid] = {"faces": [], "supertypes": [], "types": [],
                    "subtypes": [], "keywords": []}
    components: dict[tuple[str, int], dict[str, list[str]]] = {}
    for row in store.conn.execute(
            f"SELECT oracle_id, face_index, kind, value FROM card_type_component "
            f"WHERE oracle_id IN ({marks}) ORDER BY face_index, kind, position", args):
        components.setdefault((row["oracle_id"], row["face_index"]), {
            "supertype": [], "type": [], "subtype": []})[row["kind"]].append(row["value"])
    for row in store.conn.execute(
            f"SELECT oracle_id, face_index, face_name, type_line FROM card_face "
            f"WHERE oracle_id IN ({marks}) ORDER BY face_index", args):
        comp = components.get((row["oracle_id"], row["face_index"]),
                              {"supertype": [], "type": [], "subtype": []})
        out[row["oracle_id"]]["faces"].append({
            "name": row["face_name"], "type_line": row["type_line"],
            "supertypes": comp["supertype"], "types": comp["type"],
            "subtypes": comp["subtype"]})
        for kind, key in (("supertype", "supertypes"), ("type", "types"),
                          ("subtype", "subtypes")):
            for value in comp[kind]:
                if value not in out[row["oracle_id"]][key]:
                    out[row["oracle_id"]][key].append(value)
    for row in store.conn.execute(
            f"SELECT oracle_id, keyword FROM card_keyword "
            f"WHERE oracle_id IN ({marks}) ORDER BY keyword", args):
        out[row["oracle_id"]]["keywords"].append(row["keyword"])
    return out


def filter_oracle_ids(store: Store, *, types: list[str] | None = None,
                      subtypes: list[str] | None = None,
                      supertypes: list[str] | None = None,
                      keywords: list[str] | None = None,
                      collection_id: str | None = None) -> set[str] | None:
    """Oracle ids matching ALL given dimensions (any-face semantics;
    within one dimension, any of the listed values matches).

    Returns ``None`` when no dimension is given (unfiltered)."""
    dims = [(kind, values) for kind, values in (
        ("type", types), ("subtype", subtypes), ("supertype", supertypes))
        if values]
    if not dims and not keywords:
        return None
    ensure_schema(store)
    universe = set(_universe(store, collection_id))

    def matching(kind: str, values: list[str]) -> set[str]:
        marks = ",".join("?" for _ in values)
        return {str(r[0]) for r in store.conn.execute(
            f"SELECT DISTINCT oracle_id FROM card_type_component "
            f"WHERE kind = ? AND value COLLATE NOCASE IN ({marks})",
            [kind, *values])}

    result: set[str] | None = None
    for kind, values in dims:
        result = matching(kind, values) if result is None else result & matching(kind, values)
    if keywords:
        marks = ",".join("?" for _ in keywords)
        kw = {str(r[0]) for r in store.conn.execute(
            f"SELECT DISTINCT oracle_id FROM card_keyword "
            f"WHERE keyword COLLATE NOCASE IN ({marks})", list(keywords))}
        result = kw if result is None else result & kw
    return (result or set()) & universe


def facet_counts(store: Store, collection_id: str | None = None) -> dict:
    """Distinct-card counts per type / subtype / supertype / keyword
    over the universe (collection identities or the whole store)."""
    ensure_schema(store)
    universe = _universe(store, collection_id)
    out: dict[str, dict[str, int]] = {"types": {}, "subtypes": {},
                                      "supertypes": {}, "keywords": {}}
    if not universe:
        return out
    marks = ",".join("?" for _ in universe)
    kind_key = {"type": "types", "subtype": "subtypes", "supertype": "supertypes"}
    for row in store.conn.execute(
            f"SELECT kind, value, COUNT(DISTINCT oracle_id) AS n "
            f"FROM card_type_component WHERE oracle_id IN ({marks}) "
            f"GROUP BY kind, value ORDER BY n DESC, value", universe):
        out[kind_key[row["kind"]]][row["value"]] = int(row["n"])
    for row in store.conn.execute(
            f"SELECT keyword, COUNT(DISTINCT oracle_id) AS n FROM card_keyword "
            f"WHERE oracle_id IN ({marks}) GROUP BY keyword ORDER BY n DESC, keyword",
            universe):
        out["keywords"][row["keyword"]] = int(row["n"])
    return out


def type_coverage(store: Store, collection_id: str | None = None) -> dict:
    """Hard coverage numbers of the type layer over the universe."""
    ensure_schema(store)
    universe = _universe(store, collection_id)
    total = len(universe)
    covered = with_types = with_keywords = 0
    if universe:
        marks = ",".join("?" for _ in universe)
        covered = store.conn.execute(
            f"SELECT COUNT(DISTINCT oracle_id) FROM card_face "
            f"WHERE oracle_id IN ({marks})", universe).fetchone()[0]
        with_types = store.conn.execute(
            f"SELECT COUNT(DISTINCT oracle_id) FROM card_type_component "
            f"WHERE kind = 'type' AND oracle_id IN ({marks})", universe).fetchone()[0]
        with_keywords = store.conn.execute(
            f"SELECT COUNT(DISTINCT oracle_id) FROM card_keyword "
            f"WHERE oracle_id IN ({marks})", universe).fetchone()[0]
    run = store.conn.execute(
        "SELECT * FROM category_run WHERE layer = ? ORDER BY created_at DESC "
        "LIMIT 1", (LAYER_TYPE_FACTS,)).fetchone()
    return {"universe": total, "with_faces": int(covered),
            "with_types": int(with_types), "with_keywords": int(with_keywords),
            "latest_run": dict(run) if run else None}


# ---------------------------------------------------------------------------
# Category coverage report (all layers, counts only)
# ---------------------------------------------------------------------------

def category_report(store: Store, collection_id: str | None = None) -> dict:
    """Per-layer coverage + per-category counts over the universe.

    Counts only — no card names, no collection internals beyond the
    identity count of the universe itself."""
    from . import roles as roles_mod  # lazy: roles imports nothing of us at top level
    ensure_schema(store)
    roles_mod.ensure_schema(store)
    universe = _universe(store, collection_id)
    total = len(universe)
    marks = ",".join("?" for _ in universe) if universe else ""

    def count(sql: str) -> int:
        if not universe:
            return 0
        return int(store.conn.execute(sql, universe).fetchone()[0])

    layers: dict[str, dict] = {}
    for origin in roles_mod.ORIGINS:
        checked = count(
            f"SELECT COUNT(*) FROM card_category_check "
            f"WHERE origin = '{origin}' AND oracle_id IN ({marks})")
        with_claims = count(
            f"SELECT COUNT(DISTINCT oracle_id) FROM card_role "
            f"WHERE origin = '{origin}' AND oracle_id IN ({marks})")
        layers[origin] = {
            "checked": checked, "with_claims": with_claims,
            "checked_no_category": count(
                f"SELECT COUNT(*) FROM card_category_check "
                f"WHERE origin = '{origin}' AND claims = 0 "
                f"AND oracle_id IN ({marks})"),
            "checks_recorded": checked > 0,
        }
    by_category: dict[str, dict] = {}
    if universe:
        rows = store.conn.execute(
            f"SELECT role, origin, COUNT(DISTINCT oracle_id) AS n FROM card_role "
            f"WHERE oracle_id IN ({marks}) GROUP BY role, origin", universe).fetchall()
        for row in rows:
            by_category.setdefault(row["role"], {})[row["origin"]] = int(row["n"])
    tagger_tags: dict[str, dict] = {}
    for row in store.conn.execute(
            "SELECT slug, status, fetched_at, displayed_total, captured_count "
            "FROM external_snapshot WHERE source_name = 'scryfall_tagger' "
            "AND kind = 'tagger_function' ORDER BY fetched_at"):
        tagger_tags[row["slug"]] = {
            "status": row["status"], "fetched_at": row["fetched_at"],
            "displayed_total": row["displayed_total"],
            "captured_count": row["captured_count"]}
    return {
        "collection_id": collection_id,
        "universe_identities": total,
        "type_layer": type_coverage(store, collection_id),
        "layers": layers,
        "by_category": by_category,
        "taxonomy": roles_mod.ROLES,
        "labels_de": roles_mod.ROLE_LABELS_DE,
        "tagger_tags": tagger_tags,
    }
