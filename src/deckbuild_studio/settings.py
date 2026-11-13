"""Owner settings — persistent, versioned key/value configuration.

Settings live in the ``app_setting`` table of the local store (never in
Git, never sent anywhere). The catalogue below is the single source of
truth for keys, types, defaults and validation; unknown keys and invalid
values are rejected, never silently stored.

The inclusion keys decide WHICH decks/cohorts flow into inclusion
figures (see :mod:`deckbuild_studio.inclusion`). Defaults reproduce the
behaviour the app had before settings existed: inclusion = the stored
EDHREC statistics snapshots, brackets 2/3/4 (Core/Upgraded/Optimized).
"""
from __future__ import annotations

import json
from datetime import date

from .store import Store, utcnow

SETTINGS_VERSION = 1

# key -> (kind, default, description)
# kinds: "source" (enum), "brackets" (list of ints 1..5),
#        "platforms" (list of str), "min_decks" (int >= 0),
#        "max_age_days" (int > 0 or None)
CATALOG: dict[str, dict] = {
    "inclusion.source": {
        "kind": "enum",
        "values": ["edhrec", "decklists", "own_decks", "combined"],
        "default": "edhrec",
        "description": "Welche Datenbasis die Inclusion-Werte speist: "
                       "edhrec = gespeicherte EDHREC-Statistik-Snapshots; "
                       "decklists = lokal geerntete echte Decklisten; "
                       "own_decks = nur die eigenen gespeicherten Decks; "
                       "combined = decklists + own_decks gepoolt "
                       "(EDHREC bleibt getrennt, andere Nenner-Semantik).",
    },
    "inclusion.brackets": {
        "kind": "brackets",
        "default": [2, 3, 4],
        "description": "Bracket-Kohorten (1=Exhibition, 2=Core, 3=Upgraded, "
                       "4=Optimized, 5=cEDH), die in die Inclusion einfließen. "
                       "Kohorten werden nie vermischt, ohne dass der Nenner "
                       "die Auswahl ausweist.",
    },
    "inclusion.platforms": {
        "kind": "platforms",
        "default": ["archidekt"],
        "description": "Plattformen der geernteten Decklisten, die zählen "
                       "(archidekt = API-Ernte; browser:edhrec / "
                       "browser:moxfield = volle Listen aus der "
                       "Browser-Sammlung, importiert per "
                       "import-browser-decklists — sie tragen KEIN "
                       "Bracket und bilden bei Auswahl die bracket-lose "
                       "Kohorte ihrer Plattform; moxfield direkt ist "
                       "BLOCKED — API per robots.txt gesperrt — und "
                       "liefert ohne Browser-Sammlung keine Daten).",
    },
    "inclusion.min_decks": {
        "kind": "min_decks",
        "default": 10,
        "description": "Mindest-Nenner: Liegen weniger Decks in der Kohorte, "
                       "werden Inclusion-Werte als 'ungenügende Daten' "
                       "markiert (Wert + Nenner bleiben sichtbar).",
    },
    "inclusion.max_age_days": {
        "kind": "max_age_days",
        "default": None,
        "description": "Optionales Höchstalter (Tage) der Snapshots/Decklisten "
                       "für die Inclusion; leer = kein Altersfilter.",
    },
    "inclusion.date_from": {
        "kind": "date",
        "default": None,
        "description": "Zeitraum-Beginn (ISO-Datum) für Decklisten-Universen: "
                       "Es zählen nur Decks, deren Quell-Zeitstempel "
                       "(Archidekt updatedAt) an/after diesem Datum liegt. "
                       "Decks ohne Quell-Zeitstempel werden bei gesetztem "
                       "Zeitraum ausgeschlossen und in der Definition "
                       "gezählt ausgewiesen; leer = kein Zeitraum.",
    },
    "inclusion.date_to": {
        "kind": "date",
        "default": None,
        "description": "Zeitraum-Ende (ISO-Datum, inklusive) für "
                       "Decklisten-Universen; Basis wie inclusion.date_from.",
    },
    "tierlist.min_universe": {
        "kind": "positive_int",
        "default": 30,
        "description": "Mindestgröße eines Deck-Universums für das Feld "
                       "'Verbreitung (gezählt)': Kleinere Universen liefern "
                       "die Stufe 'unbekannt' (U/UNIVERSE_TOO_SMALL) statt "
                       "einer gezählten Stufe. Default 30 (CPL-Default).",
    },
    "tierlist.model_version": {
        "kind": "enum",
        "values": ["tierlist/1.1.0", "tierlist/1.2.0"],
        "default": "tierlist/1.1.0",
        "description": "Aktive Modellversion der Evidenz-Tier "
                       "(Stärke-Schätzung): 1.1.0 = Kern-Signale "
                       "(EDHREC-Inclusion, Playgroup-Lift, Spellbook); "
                       "1.2.0 = Kern + begrenzte Turnier-Zusatzsignale "
                       "(docs/TIERLIST_1_2_DESIGN.md). Die Anzeige (API/UI) "
                       "zeigt die hier gewählte Version; berechnet wird "
                       "sie mit compute-tiers (CLI-Option --model "
                       "überschreibt die Auswahl für einen Lauf). Ein "
                       "Wechsel ändert keine gespeicherten Zeilen — er "
                       "wirkt auf Anzeige und nächsten Compute-Lauf.",
    },
    "tierlist.signal_edhtop16_global": {
        "kind": "bool",
        "default": True,
        "description": "Nur Modell 1.2.0: Zusatzsignal EDHTop16-Play-Rate "
                       "(global, Gewicht 0,10, Neutralwert-Floor 0,50). "
                       "AUS = die Komponente existiert im Compute-Lauf "
                       "nicht (kein Ersatzwert). Unter 1.1.0 wirkungslos.",
    },
    "tierlist.signal_edhtop16_commander": {
        "kind": "bool",
        "default": True,
        "description": "Nur Modell 1.2.0: Zusatzsignal EDHTop16-Play-Rate "
                       "je Commander-Kontext (Gewicht 0,10, Gate "
                       "entries_n >= 25, Neutralwert-Floor 0,50). "
                       "AUS = Komponente abwesend. Unter 1.1.0 wirkungslos.",
    },
    "tierlist.signal_topdeck_conversion": {
        "kind": "bool",
        "default": True,
        "description": "Nur Modell 1.2.0: Zusatzsignal TopDeck-Conversion "
                       "(global, Gewicht 0,10, Shrinkage K=50 Richtung "
                       "Kohorten-Baseline, Neutralwert-Floor 0,50). "
                       "AUS = Komponente abwesend. Unter 1.1.0 wirkungslos.",
    },
}

KNOWN_PLATFORMS = ["archidekt", "moxfield", "browser:edhrec", "browser:moxfield"]


class SettingError(ValueError):
    pass


def _validate(key: str, value: object) -> object:
    spec = CATALOG.get(key)
    if spec is None:
        raise SettingError(f"unknown setting: {key!r} (known: {sorted(CATALOG)})")
    kind = spec["kind"]
    if kind == "enum":
        if value not in spec["values"]:
            raise SettingError(f"{key}: {value!r} not in {spec['values']}")
        return value
    if kind == "brackets":
        if not isinstance(value, (list, tuple)) or not value:
            raise SettingError(f"{key}: must be a non-empty list of bracket levels 1..5")
        out = []
        for v in value:
            if isinstance(v, bool) or not isinstance(v, int) or v < 1 or v > 5:
                raise SettingError(f"{key}: invalid bracket level {v!r} (allowed 1..5)")
            if v not in out:
                out.append(v)
        return sorted(out)
    if kind == "platforms":
        if not isinstance(value, (list, tuple)) or not value:
            raise SettingError(f"{key}: must be a non-empty list of platform names")
        out = []
        for v in value:
            if not isinstance(v, str) or v not in KNOWN_PLATFORMS:
                raise SettingError(f"{key}: unknown platform {v!r} (known: {KNOWN_PLATFORMS})")
            if v not in out:
                out.append(v)
        return out
    if kind == "min_decks":
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SettingError(f"{key}: must be an integer >= 0")
        return value
    if kind == "max_age_days":
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise SettingError(f"{key}: must be a positive integer or null")
        return value
    if kind == "date":
        if value is None:
            return None
        if not isinstance(value, str):
            raise SettingError(f"{key}: must be an ISO date string or null")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise SettingError(
                f"{key}: {value!r} is not an ISO date (YYYY-MM-DD)") from None
        if parsed.isoformat() != value:
            raise SettingError(
                f"{key}: {value!r} is not an ISO date (YYYY-MM-DD)")
        return value
    if kind == "positive_int":
        if isinstance(value, bool) or not isinstance(value, int) \
                or value < 1 or value > 100000:
            raise SettingError(f"{key}: must be an integer in 1..100000")
        return value
    if kind == "bool":
        if not isinstance(value, bool):
            raise SettingError(f"{key}: must be a boolean (true/false)")
        return value
    raise AssertionError(kind)  # pragma: no cover


def validate_setting(key: str, value: object) -> object:
    """Validate + normalise one value WITHOUT storing it (for atomic
    multi-key updates: validate everything first, then apply)."""
    return _validate(key, value)


def _parse_stored(raw: object) -> tuple[bool, object]:
    """Decode one stored ``value_json``. Returns (True, value) on success
    and (False, None) when the stored text is not valid JSON — read paths
    must never crash on a corrupt row (hand-edited DB, interrupted write);
    they fall back to the catalogue default instead, exactly like the
    other defensive payload parses in this codebase (mtgjson, tierlist,
    report). The row itself is left untouched: read tolerance only, the
    next ``set_setting`` rewrites it — never a silent data change."""
    try:
        return True, json.loads(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False, None


def get_setting(store: Store, key: str) -> object:
    """Effective value of one setting (stored override or catalogue default)."""
    if key not in CATALOG:
        raise SettingError(f"unknown setting: {key!r}")
    row = store.conn.execute(
        "SELECT value_json FROM app_setting WHERE key=?", (key,)).fetchone()
    if row is None:
        return CATALOG[key]["default"]
    ok, value = _parse_stored(row["value_json"])
    return value if ok else CATALOG[key]["default"]


def set_setting(store: Store, key: str, value: object) -> object:
    value = _validate(key, value)
    store.conn.execute(
        "INSERT OR REPLACE INTO app_setting(key,value_json,updated_at) VALUES(?,?,?)",
        (key, json.dumps(value), utcnow()))
    store.conn.commit()
    return value


def all_settings(store: Store) -> dict:
    """Every catalogue key with effective value, default and metadata."""
    stored = {}
    for r in store.conn.execute("SELECT key, value_json FROM app_setting"):
        ok, value = _parse_stored(r["value_json"])
        if ok:
            stored[r["key"]] = value
        # corrupt row: skipped — the catalogue default applies below and
        # the key reports as not overridden (same fallback as get_setting)
    out = {}
    for key, spec in CATALOG.items():
        out[key] = {
            "value": stored.get(key, spec["default"]),
            "default": spec["default"],
            "overridden": key in stored,
            "kind": spec["kind"],
            "description": spec["description"],
        }
        if "values" in spec:
            out[key]["values"] = spec["values"]
    return {"settings_version": SETTINGS_VERSION, "settings": out}


def resolve(store: Store, overrides: dict | None = None) -> dict:
    """Flat {key: value} of effective settings, with optional per-call
    overrides (validated the same way; overrides are never persisted)."""
    cfg = {key: get_setting(store, key) for key in CATALOG}
    for key, value in (overrides or {}).items():
        cfg[key] = _validate(key, value)
    return cfg
