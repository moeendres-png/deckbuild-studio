"""Polite HTTP fetcher for public pages — used ONLY by the external adapters.

Rules (Issue #1 §4/§5, docs/EXTERNAL_DATA.md):
  * honest User-Agent identifying this local tool,
  * robots.txt is fetched once per host and respected (wildcard group;
    a disallowed path raises :class:`RobotsDisallowed` and is never fetched),
  * >= 1 s between requests to the same host,
  * exponential backoff on 429/5xx (Retry-After honoured, capped),
  * conditional GET (ETag / Last-Modified) when the caller has a validator,
  * no cookies, no login, no paywall/access-control bypass, GET only —
    with ONE sanctioned exception: :meth:`Fetcher.post_json` exists only
    for the EDHTop16 API, whose Terms of Service (§ "API Usage")
    expressly provide an API "for developers and data enthusiasts";
    persisted queries are that API's sole access mechanism (plaintext
    GraphQL is disabled server-side). Its request body carries public
    query variables only (a commander name).

Only publicly known commander/card slugs are ever requested. No private
collection data (quantities, locations, deck lists, oracle-id lists) is
sent anywhere: page requests are plain GETs without any request body,
and the single POST channel above never carries collection data either.
"""
from __future__ import annotations

import gzip
import http.client
import json
import re
import time
import zlib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlsplit

USER_AGENT = "DeckbuildStudio/0.2 (personal local Commander deckbuilder cache; +https://github.com/moeendres-png/deckbuild-studio)"


class RobotsDisallowed(Exception):
    pass


class FetchError(Exception):
    def __init__(self, status: int | None, message: str):
        super().__init__(message)
        self.status = status


@dataclass
class Response:
    status: int
    body: bytes
    etag: str | None = None
    last_modified: str | None = None
    url: str = ""

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def _robots_rules(robots_text: str) -> list[str]:
    """Disallow prefixes of the wildcard group (our UA has no own group).

    Group termination follows RFC 9309: a ``user-agent`` line starts a
    new group once the current group has ANY rule lines — ``allow``
    lines count as rule lines for termination even though only
    ``disallow`` prefixes are collected. This matters for Cloudflare's
    managed robots.txt (e.g. data.scryfall.io): its wildcard group is
    ``User-agent: *`` + ``Content-Signal`` + ``Allow: /`` with NO
    disallow lines, directly followed by named training-crawler
    groups with ``Disallow: /`` — without allow-termination the ``*``
    agent would bleed into the next group and its ``Disallow: /``
    would be misread as a wildcard block of the whole host."""
    disallows: list[str] = []
    group_agents: list[str] = []
    group_rules: list[str] = []
    group_has_rules = False
    groups: list[tuple[list[str], list[str]]] = []

    def flush():
        nonlocal group_has_rules
        if group_agents:
            groups.append((list(group_agents), list(group_rules)))
        group_agents.clear()
        group_rules.clear()
        group_has_rules = False

    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if group_has_rules:
                flush()
            group_agents.append(value.lower())
        elif key == "disallow" and group_agents and value:
            group_rules.append(value)
            group_has_rules = True
        elif key == "allow" and group_agents:
            group_has_rules = True
    flush()
    for agents, rules in groups:
        if "*" in agents:
            disallows.extend(rules)
    return disallows


def _robots_match(pattern: str, path: str) -> bool:
    """robots.txt prefix match; '*' is a wildcard, trailing '$' anchors."""
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    regex = "^" + re.escape(pattern).replace(r"\*", ".*")
    if anchored:
        regex += "$"
    return re.match(regex, path) is not None


@dataclass
class Fetcher:
    min_interval: float = 1.0
    max_retries: int = 3
    timeout: float = 30.0
    sleeper: object = field(default=time.sleep)
    _last_request: dict = field(default_factory=dict)
    _robots: dict = field(default_factory=dict)

    # -- robots ---------------------------------------------------------
    def _disallows(self, host: str, scheme: str) -> list[str]:
        if host not in self._robots:
            rules: list[str] = []
            try:
                req = urllib.request.Request(
                    f"{scheme}://{host}/robots.txt", headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    rules = _robots_rules(resp.read().decode("utf-8", errors="replace"))
            except Exception:
                rules = []  # unreachable robots.txt: proceed, rate limit still applies
            self._robots[host] = rules
        return self._robots[host]

    def assert_allowed(self, url: str) -> None:
        parts = urlsplit(url)
        path = parts.path or "/"
        for pattern in self._disallows(parts.netloc, parts.scheme):
            if _robots_match(pattern, path):
                raise RobotsDisallowed(f"robots.txt disallows {path} (rule: {pattern})")

    # -- fetching ---------------------------------------------------------
    def _throttle(self, host: str) -> None:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last_request.get(host, 0.0))
        if wait > 0:
            self.sleeper(wait)  # type: ignore[operator]
        self._last_request[host] = time.monotonic()

    def get(self, url: str, *, etag: str | None = None,
            last_modified: str | None = None) -> Response:
        self.assert_allowed(url)
        host = urlsplit(url).netloc
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json"}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        backoff = 2.0
        last_error: FetchError | None = None
        for attempt in range(self.max_retries + 1):
            self._throttle(host)
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return Response(status=resp.status, body=resp.read(),
                                    etag=resp.headers.get("ETag"),
                                    last_modified=resp.headers.get("Last-Modified"),
                                    url=url)
            except urllib.error.HTTPError as exc:
                body = exc.read() if exc.fp else b""
                if exc.code == 304:
                    return Response(status=304, body=b"", etag=etag,
                                    last_modified=last_modified, url=url)
                if exc.code in (404, 410):
                    return Response(status=exc.code, body=body, url=url)
                if exc.code in (403, 429) or exc.code >= 500:
                    last_error = FetchError(exc.code, f"HTTP {exc.code} for {url}")
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    if attempt < self.max_retries:
                        delay = backoff ** attempt
                        if retry_after and retry_after.isdigit():
                            delay = min(float(retry_after), 60.0)
                        self.sleeper(delay)  # type: ignore[operator]
                        continue
                    return Response(status=exc.code, body=body, url=url)
                return Response(status=exc.code, body=body, url=url)
            except (urllib.error.URLError, TimeoutError, OSError,
                    http.client.HTTPException) as exc:
                # HTTPException covers IncompleteRead & friends raised by
                # resp.read() on a truncated body — transient, retryable
                last_error = FetchError(None, f"network error for {url}: {exc}")
                if attempt < self.max_retries:
                    self.sleeper(backoff ** attempt)  # type: ignore[operator]
                    continue
                raise last_error
        assert last_error is not None
        raise last_error

    def post_json(self, url: str, payload: dict) -> Response:
        """POST a JSON body — the single sanctioned exception to GET-only.

        Exists ONLY for the EDHTop16 API (see the module docstring):
        its Terms of Service expressly provide an API for developers,
        and persisted queries are the API's sole access mechanism. The
        body carries public query variables only (a commander name) —
        never collection data. Same politeness as :meth:`get`: robots
        respected, per-host throttle, honest User-Agent; retries with
        backoff (Retry-After honoured, capped at 60 s) on 5xx and on
        transient network failures — the EDHTop16 server frequently
        drops connections mid-response (RemoteDisconnected /
        IncompleteRead, observed live 2026-11-12), the same failure
        class :meth:`get` retries for every other source. The request
        offers ``Accept-Encoding: gzip`` and gzip answers are
        decompressed transparently: the wire body shrinks (~13 KB to
        ~3 KB for a staples answer), which measurably reduces the
        mid-response drops — plain HTTP content negotiation, no
        special-casing of the source. 4xx answers are returned to
        the caller without retries; a network failure that survives
        all retries raises :class:`FetchError`."""
        self.assert_allowed(url)
        host = urlsplit(url).netloc
        body = json.dumps(payload).encode("utf-8")
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json",
                   "Content-Type": "application/json",
                   "Accept-Encoding": "gzip"}
        backoff = 2.0
        last_error: FetchError | None = None
        for attempt in range(self.max_retries + 1):
            self._throttle(host)
            req = urllib.request.Request(url, data=body, headers=headers,
                                         method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    return Response(
                        status=resp.status,
                        body=_decompress_body(
                            raw, resp.headers.get("Content-Encoding")),
                        etag=resp.headers.get("ETag"),
                        last_modified=resp.headers.get("Last-Modified"),
                        url=url)
            except urllib.error.HTTPError as exc:
                resp_body = exc.read() if exc.fp else b""
                if exc.headers is not None:
                    resp_body = _decompress_body(
                        resp_body, exc.headers.get("Content-Encoding"))
                if exc.code >= 500 and attempt < self.max_retries:
                    last_error = FetchError(exc.code, f"HTTP {exc.code} for {url}")
                    delay = backoff ** attempt
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    if retry_after and retry_after.isdigit():
                        delay = min(float(retry_after), 60.0)
                    self.sleeper(delay)  # type: ignore[operator]
                    continue
                return Response(status=exc.code, body=resp_body, url=url)
            except (urllib.error.URLError, TimeoutError, OSError, EOFError,
                    zlib.error, http.client.HTTPException) as exc:
                # HTTPException covers IncompleteRead — the server
                # dropping the connection mid-response; EOFError /
                # zlib.error cover a gzip body truncated the same way.
                # Transient, retried with backoff exactly like in get().
                last_error = FetchError(None, f"network error for {url}: {exc}")
                if attempt < self.max_retries:
                    self.sleeper(backoff ** attempt)  # type: ignore[operator]
                    continue
                raise last_error
        assert last_error is not None
        raise last_error


def _decompress_body(body: bytes, content_encoding: str | None) -> bytes:
    """Undo a gzip Content-Encoding; anything else passes through."""
    if content_encoding and content_encoding.lower() == "gzip":
        return gzip.decompress(body)
    return body
