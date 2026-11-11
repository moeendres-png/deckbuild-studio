"""Local card-image cache.

Adopted from the upstream studio (``commander_lab/studio/images.py``):
images are fetched once from the public card-image host named by the
locally stored Scryfall image URI and then served from disk. The
request names only the public card image — nothing about quantities,
decks or the collection is sent. Cached files live next to the
database inside the private data folder, never in the Git tree.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from .store import Store

IMAGE_HOST = "cards.scryfall.io"
_USER_AGENT = "DeckbuildStudio/0.2 (local deck builder)"
_MAX_BYTES = 5_000_000


def image_folder(store: Store) -> Path:
    folder = store.path.parent / "images"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _download(address: str) -> bytes | None:
    parts = urlsplit(address)
    if parts.scheme != "https" or parts.hostname != IMAGE_HOST:
        return None
    request = urllib.request.Request(address, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read(_MAX_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    if not data or len(data) > _MAX_BYTES:
        return None
    return data


def image_address(store: Store, oracle_id: str) -> str | None:
    row = store.scryfall(oracle_id)
    if row is None:
        return None
    return row["image_uri"]


def cached_image(store: Store, oracle_id: str, *, fetch: bool = True) -> Path | None:
    """Path of the cached front image; fetches it once when missing."""
    target = image_folder(store) / f"{oracle_id}-front.jpg"
    if target.exists() and target.stat().st_size > 0:
        return target
    if not fetch:
        return None
    address = image_address(store, oracle_id)
    if not address:
        return None
    data = _download(address)
    if data is None:
        return None
    partial = target.with_suffix(".part")
    partial.write_bytes(data)
    partial.replace(target)
    return target


def fetch_images(store: Store, oracle_ids: list[str], *,
                 pause: float = 0.05) -> dict[str, int]:
    """Fill the cache for these cards. Returns what happened (counts)."""
    result = {"cached": 0, "fetched": 0, "missing": 0}
    for oracle_id in oracle_ids:
        if image_address(store, oracle_id) is None:
            result["missing"] += 1
        elif cached_image(store, oracle_id, fetch=False) is not None:
            result["cached"] += 1
        elif cached_image(store, oracle_id) is not None:
            result["fetched"] += 1
            time.sleep(pause)
        else:
            result["missing"] += 1
    return result


def cache_status(store: Store, oracle_ids: list[str] | None = None) -> dict:
    folder = store.path.parent / "images"
    files = list(folder.glob("*-front.jpg")) if folder.exists() else []
    status: dict[str, object] = {"cached_files": len(files)}
    if oracle_ids is not None:
        have = {p.name[: -len("-front.jpg")] for p in files}
        status["requested"] = len(oracle_ids)
        status["requested_cached"] = sum(1 for oid in oracle_ids if oid in have)
    return status
