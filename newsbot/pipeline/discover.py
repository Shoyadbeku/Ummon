"""STEP 1 + 3: news discovery from RSS feeds and Viral Potential Scoring.

The heuristic score is a *pre-filter*. The final editorial choice (and fact-check across
sources) is made by the AI editor in the scheduled session, which also runs web searches.
"""
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import urllib.request

from .config import FEEDS, USER_AGENT
from .db import conn, now_utc, log
from .textsim import tokens, jaccard

# Keyword weights (uz + en). Positive = public-interest impact, negative = excluded topics.
IMPACT = {
    # daily life / economy
    "narx": 14, "narxi": 14, "qimmat": 12, "arzon": 10, "soliq": 12, "ish haqi": 14, "maosh": 12, "pensiya": 14,
    "kredit": 8, "dollar": 8, "kurs": 8, "inflyatsiya": 10, "gaz": 10, "elektr": 10, "svet": 10, "benzin": 12, "metan": 12,
    "kommunal": 12, "ta'rif": 10, "tarif": 10, "jarima": 10, "qonun": 9, "farmon": 9, "qaror": 7, "taqiq": 10,
    "viza": 9, "chegara": 8, "migrant": 9, "metro": 8, "avtobus": 6, "aeroport": 6, "poyezd": 6, "yo'l": 4,
    # emergencies
    "zilzila": 18, "yong'in": 14, "portlash": 16, "halok": 16, "avariya": 12, "suv toshqini": 16, "favqulodda": 16,
    "earthquake": 18, "explosion": 16, "killed": 14, "dead": 12, "flood": 14, "wildfire": 14, "crash": 10,
    # politics / world
    "prezident": 6, "mirziyoyev": 8, "president": 6, "war": 12, "ceasefire": 14, "sanctions": 10, "election": 9,
    "summit": 8, "nato": 8, "ukraine": 9, "iran": 9, "israel": 9, "gaza": 10, "china": 7, "russia": 8, "trump": 8,
    "putin": 8, "xi": 5, "oil": 7, "tariff": 10, "markets": 6, "stocks": 5, "bitcoin": 7,
    # tech / science
    "sun'iy intellekt": 10, " ai ": 8, "artificial intelligence": 10, "robot": 6, "space": 6, "nasa": 6, "kashfiyot": 8,
    "discovery": 6, "vaccine": 8, "virus": 9,
    # uzbekistan relevance in world feeds
    "uzbekistan": 20, "o'zbekiston": 10, "central asia": 12, "tashkent": 18, "kazakhstan": 6, "kyrgyzstan": 6,
}
EXCLUDE = {
    # showbiz / gossip are excluded by editorial policy
    "celebrity": -40, "actor": -25, "actress": -25, "singer": -20, "kardashian": -50, "oscars": -30, "grammy": -30,
    "box office": -30, "film": -12, "serial": -15, "aktyor": -25, "aktrisa": -25, "xonanda": -25, "shou": -30,
    "konsert": -20, "kino": -15, "football": -6, "futbol": -6,  # sport allowed but de-prioritised
    "horoscope": -60, "goroskop": -60, "reklama": -60, "sponsored": -60, "quiz": -40,
}


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _published(e) -> str | None:
    for key in ("published", "updated"):
        if e.get(key):
            try:
                return parsedate_to_datetime(e[key]).astimezone(timezone.utc).isoformat(timespec="seconds")
            except Exception:
                pass
    for key in ("published_parsed", "updated_parsed"):
        if e.get(key):
            return datetime(*e[key][:6], tzinfo=timezone.utc).isoformat(timespec="seconds")
    return None


def _image(e) -> str | None:
    for m in e.get("media_content", []) + e.get("media_thumbnail", []):
        if m.get("url"):
            return m["url"]
    for l in e.get("links", []):
        if l.get("type", "").startswith("image"):
            return l.get("href")
    return None


def crawl() -> int:
    new = 0
    warnings = []
    with conn() as c:
        for f in FEEDS:
            try:
                d = feedparser.parse(_fetch(f["url"]))
            except Exception as ex:  # retry next run; log and keep going
                warnings.append(f"feed failed {f['name']}: {ex}")
                continue
            for e in d.entries[:60]:
                url = e.get("link")
                if not url:
                    continue
                cur = c.execute(
                    "INSERT OR IGNORE INTO news_items (url,title,summary,source,region,trust,published_at,first_seen,image_url) VALUES (?,?,?,?,?,?,?,?,?)",
                    (url, _clean(e.get("title", "")), _clean(e.get("summary", ""))[:1200], f["name"], f["region"], f["trust"],
                     _published(e), now_utc(), _image(e)),
                )
                new += cur.rowcount
    for w in warnings:   # logged after the transaction closes (avoids sqlite lock)
        log("WARN", w)
    log("INFO", f"crawl done, {new} new items")
    return new


def _hours_old(iso: str | None) -> float:
    if not iso:
        return 12.0
    dt = datetime.fromisoformat(iso)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)


def score_items(hours: float = 24) -> None:
    """Viral Potential Score 0-100 = freshness + impact + coverage + trust + visual + local relevance."""
    with conn() as c:
        rows = c.execute("SELECT * FROM news_items").fetchall()
        rows = [r for r in rows if _hours_old(r["published_at"]) <= hours]
        toks = {r["id"]: tokens(r["title"] + " " + (r["summary"] or "")[:200]) for r in rows}
        for r in rows:
            text = f" {r['title']} {r['summary']} ".lower()
            age = _hours_old(r["published_at"])
            freshness = 30 if age <= 1 else 26 if age <= 3 else 22 if age <= 6 else 12 if age <= 12 else 5
            impact = sum(w for k, w in IMPACT.items() if k in text)
            impact = max(0, min(30, impact))
            penalty = sum(w for k, w in EXCLUDE.items() if k in text)
            # coverage: how many OTHER sources carry a similar story (proxy for "being discussed")
            others = {o["source"] for o in rows if o["id"] != r["id"] and o["source"] != r["source"]
                      and jaccard(toks[r["id"]], toks[o["id"]]) >= 0.28}
            coverage = min(20, 7 * len(others))
            trust = round(10 * (r["trust"] or 0.7))
            visual = 5 if r["image_url"] else 0
            local = 5 if r["region"] == "uz" or "uzbek" in text or "o'zbek" in text else 0
            total = max(0, min(100, freshness + impact + coverage + trust + visual + local + penalty))
            detail = dict(freshness=freshness, impact=impact, coverage=coverage, coverage_sources=sorted(others),
                          trust=trust, visual=visual, local=local, penalty=penalty, age_h=round(age, 1))
            c.execute("UPDATE news_items SET score=?, score_detail=? WHERE id=?", (total, json.dumps(detail, ensure_ascii=False), r["id"]))


def candidates(region: str, hours: float = 6, limit: int = 15, fallback_hours: float = 24):
    """Top unused items for a region; widens the window to 24h if the last N hours are thin."""
    from .dedupe import already_covered
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM news_items WHERE region=? AND used_in_episode IS NULL ORDER BY score DESC", (region,)
        ).fetchall()
    out = []
    for window in (hours, fallback_hours):
        out = []
        for r in rows:
            if _hours_old(r["published_at"]) > window:
                continue
            dup = already_covered(r["title"] + " " + (r["summary"] or ""))
            out.append({**dict(r), "score_detail": json.loads(r["score_detail"] or "{}"), "duplicate_of": dup})
            if len(out) >= limit:
                break
        if len([o for o in out if not o["duplicate_of"]]) >= 3:
            break
    return out
