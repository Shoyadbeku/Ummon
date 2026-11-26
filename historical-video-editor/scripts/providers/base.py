"""Provider base class, candidate factory and registry."""
from __future__ import annotations

import hashlib
import html
import re
from typing import Callable

from common import env, log  # noqa: F401  (re-exported for providers)
from licenses import classify

REGISTRY: dict[str, type["Provider"]] = {}


def register(cls):
    REGISTRY[cls.name] = cls
    return cls


def strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    return " ".join(html.unescape(s).split())


def make_candidate(provider: str, media_type: str, *, page_url: str, title: str = "", media_url: str = "",
                   thumb_url: str = "", width: int = 0, height: int = 0, duration: float = 0.0, author: str = "",
                   handle: str = "", license_raw: str = "", license_url: str = "", date: str = "",
                   source_label: str = "", description: str = "", download_method: str = "http",
                   archival: bool = True, query: str = "", lang: str = "", extra: dict | None = None,
                   monetized: bool = True) -> dict:
    lic = classify(license_raw, license_url, provider, monetized)
    cid = hashlib.sha1(f"{provider}|{page_url}|{media_url}".encode()).hexdigest()[:12]
    return {
        "id": f"{provider[:4]}-{cid}",
        "provider": provider,
        "media_type": media_type,           # video | image | graphic
        "title": strip_html(title)[:300],
        "description": strip_html(description)[:600],
        "page_url": page_url,               # ORIGINAL page (never a search-engine result page)
        "media_url": media_url,             # direct file if known
        "thumb_url": thumb_url,
        "width": int(width or 0),
        "height": int(height or 0),
        "duration": float(duration or 0.0),
        "author": strip_html(author)[:120],
        "handle": handle,
        "license": lic,
        "license_raw": license_raw,
        "date": str(date or "")[:40],
        "source_label": source_label or provider,
        "download_method": download_method, # http | ytdlp | none
        "archival": archival,
        "query": query,
        "lang": lang,
        "extra": extra or {},
    }


class ProviderUnavailable(Exception):
    """Raised when a provider lacks keys or is disabled — reported, never faked."""


class Provider:
    name = "base"
    media_types: tuple[str, ...] = ("video", "image")
    requires: tuple[str, ...] = ()   # env vars
    label = ""

    def __init__(self, cfg: dict, http):
        self.cfg = cfg
        self.http = http
        self.monetized = bool(cfg["project"].get("channel_monetized", True))
        self.limit = int(cfg["search"]["max_results_per_query"])
        missing = [k for k in self.requires if not env(k)]
        if missing:
            raise ProviderUnavailable(f"{self.name}: missing {', '.join(missing)}")

    def cand(self, media_type: str, **kw) -> dict:
        kw.setdefault("source_label", self.label or self.name)
        return make_candidate(self.name, media_type, monetized=self.monetized, **kw)

    def search(self, query: str, media_type: str, lang: str = "en") -> list[dict]:  # pragma: no cover
        raise NotImplementedError


def get_providers(names: list[str], cfg: dict, http, media_type: str) -> tuple[list[Provider], dict[str, str]]:
    """Instantiate providers; return (usable, {name: reason_unavailable})."""
    # import modules so @register runs
    from providers import archives, platforms, search_engines, stock  # noqa: F401  (registers providers)

    ok, skipped = [], {}
    for n in names:
        cls = REGISTRY.get(n)
        if not cls:
            skipped[n] = "unknown provider"
            continue
        if media_type not in cls.media_types:
            continue
        try:
            ok.append(cls(cfg, http))
        except ProviderUnavailable as e:
            skipped[n] = str(e)
    return ok, skipped


def safe(fn: Callable[[], list[dict]], name: str, errors: dict) -> list[dict]:
    try:
        return fn()
    except Exception as e:  # provider failure must not stop the pipeline
        errors.setdefault(name, []).append(str(e)[:300])
        log.warning("%s failed: %s", name, str(e)[:200])
        return []
