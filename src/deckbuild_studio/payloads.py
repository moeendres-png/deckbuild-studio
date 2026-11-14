"""Application-level compression codec for large stored JSON texts.

History: the codec was built for the database diet
(``docs/DB_DIET.md``), where one JSON column of the since-removed
tier store held 2.48 GB of highly redundant plain text in 1.27M
rows (avg ~2 KB; the text compresses to well under the SQLite
inline threshold, which removes both the content bytes and the
overflow-page slack). The tier store was removed on 2026-11-14
(issue #59); this module stays as the shared codec of
``tools/migrate_payload_compression.py`` and as the reference
implementation of the archive format in which the removed tier
data is preserved (issue #58) — the format must remain readable
for exactly as long as that archive exists.

Scope note: ``external_snapshot.payload_json`` is deliberately NOT
compressed — it totals 12 MB across the whole database, so
compressing it would be risk without benefit, and it stays plain,
human-readable JSON.

The codec:

* :func:`encode_payload` — on write. Payloads at or above
  ``_MIN_COMPRESS_BYTES`` are gzip-compressed, base64-encoded and stored
  with the unambiguous marker prefix ``gzip+b64:``. Smaller payloads (and
  payloads that would not actually shrink) are stored verbatim, so small
  rows stay human-readable in raw SQL and never grow.
* :func:`decode_payload` — on read. Values without the marker are legacy
  plain text and pass through unchanged (full backward compatibility with
  every database written before this codec existed); marked values are
  base64-decoded and gunzipped back to the exact original text.
* :func:`loads_payload` — ``json.loads(decode_payload(...))`` for the
  common read shape.

Provenance invariants are untouched: a stored ``sha256`` describes
the ORIGINAL payload text, and decompression restores that text
byte-for-byte, so every stored hash stays verifiable against the
decompressed value. Only the storage representation changes —
never the content.

Failure contract: a marked value that cannot be decoded (truncated
base64, corrupt gzip stream, non-UTF-8 result) raises
:class:`PayloadDecodeError`, which subclasses ``json.JSONDecodeError``.
Every existing payload reader already treats ``JSONDecodeError`` as
"stored payload unusable" (STALE marking / ``{}`` fallback / cached
re-sync skip), so a corrupt compressed payload degrades exactly like a
corrupt plain one instead of crashing the caller.
"""
from __future__ import annotations

import base64
import binascii
import gzip
import json
import zlib

PREFIX = "gzip+b64:"

# Below this size the base64 framing (+33%) plus the gzip header cost
# more than the redundancy saves; the value is also small enough that it
# contributes nothing measurable to the database size.
_MIN_COMPRESS_BYTES = 512

# gzip level 6: within a few percent of level 9 on JSON text, but
# noticeably faster — the migration converts gigabytes in one pass.
_COMPRESS_LEVEL = 6


class PayloadDecodeError(json.JSONDecodeError):
    """A ``gzip+b64:``-marked stored payload could not be decoded.

    Subclasses ``json.JSONDecodeError`` so the established corrupt-payload
    handling at every read site (which catches ``JSONDecodeError`` or its
    parent ``ValueError``) applies unchanged.
    """

    def __init__(self, reason: str):
        super().__init__(f"compressed payload undecodable: {reason}", "", 0)


def is_compressed(stored: str | bytes | None) -> bool:
    return isinstance(stored, str) and stored.startswith(PREFIX)


def encode_payload(text: str | None) -> str | None:
    """Storage representation for ``text`` (see module docstring)."""
    if text is None:
        return None
    raw = text.encode("utf-8")
    if len(raw) < _MIN_COMPRESS_BYTES:
        return text
    packed = PREFIX + base64.b64encode(
        gzip.compress(raw, compresslevel=_COMPRESS_LEVEL, mtime=0)).decode("ascii")
    # Paranoia: never store a representation that is larger than the
    # original (incompressible input); the plain text stays canonical.
    return packed if len(packed) < len(text) else text


def decode_payload(stored: str | bytes | None) -> str | None:
    """Original text for a stored value; plain values pass through.

    A ``bytes`` value (a BLOB in a TEXT column — hand-edited or
    corruptly written database) is decoded as UTF-8 exactly like
    ``json.loads`` would treat it: invalid UTF-8 raises
    ``UnicodeDecodeError`` (a ``ValueError``), preserving the read
    tolerance the callers had before this codec existed.
    """
    if stored is None:
        return None
    if isinstance(stored, bytes):
        return stored.decode("utf-8")
    if not is_compressed(stored):
        return stored
    body = stored[len(PREFIX):]
    if not body:
        raise PayloadDecodeError("empty body after the marker prefix")
    try:
        raw = gzip.decompress(base64.b64decode(body, validate=True))
        return raw.decode("utf-8")
    except (binascii.Error, OSError, EOFError, zlib.error,
            UnicodeDecodeError) as exc:
        raise PayloadDecodeError(str(exc)) from exc


def loads_payload(stored: str | bytes | None):
    """``json.loads`` over the decoded payload (the common read shape).

    Raises ``json.JSONDecodeError`` for unparseable plain payloads and
    :class:`PayloadDecodeError` (a ``JSONDecodeError``) for undecodable
    compressed ones — callers keep their existing ``except`` clauses.
    """
    return json.loads(decode_payload(stored))  # type: ignore[arg-type]
