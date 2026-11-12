"""Polite HTTP fetcher for public pages — used ONLY by the external adapters.

Rules (Issue #1 §4/§5, docs/EXTERNAL_DATA.md):
  * honest User-Agent identifying this local tool,
  * robots.txt is fetched once per host and respected (wildcard group;
    a disallowed path raises :class:`RobotsDisallowed` and is never fetched),
  * >= 1 s between requests to the same host,
  * exponential backoff on 429/5xx (Retry-After honoured, capped),
  * conditional GET (ETag / Last-Modified) when the caller has a validator,
  * no cookies, no login, no paywall/access-control bypass, GET only.

Only publicly known commander/card slugs are ever requested. No private
collection data (quantities, locations, deck lists, oracle-id lists) is
sent anywhere: requests are plain page GETs without any request body.
"""
from __future__ import annotations

import http.client
import re
import time
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
