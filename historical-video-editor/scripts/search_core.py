"""Shared multi-provider search used by search_videos.py and search_images.py."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import Http, log, write_json
from providers.base import get_providers, safe
from providers.search_engines import manual_search_links

TOKEN = re.compile(r"[\w']+", re.U)
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-4][0-9])\b")
STOP = {"the", "a", "of", "and", "in", "on", "archive", "footage", "historical", "old", "map", "photo",
        "кинохроника", "архивные", "кадры", "arxiv", "kadrlari", "portrait", "портрет", "portret"}


def tokens(s: str) -> set[str]:
    return {t.lower() for t in TOKEN.findall(s or "") if len(t) > 2 and t.lower() not in STOP}


def score_candidate(c: dict, scene: dict, query: str, cfg: dict) -> float:
    text = f"{c['title']} {c['description']}".lower()
    tt = tokens(text)
    qt = tokens(query)
    ent = tokens(" ".join(scene.get("places", []) + scene.get("persons", []) + scene.get("terms", [])))
    rel = (len(qt & tt) / max(1, len(qt))) * 4 + (len(ent & tt) / max(1, len(ent))) * 2 if (qt or ent) else 0
    s = rel
    if rel < 0.5:  # nothing in title/description matches the scene -> almost irrelevant
        s -= 4.0
        c.setdefault("flags", []).append("low_relevance")
    # licence
    s += {0: 3.0, 1: 2.2, 2: 1.5, 3: -1.0, 4: -3.0}.get(c["license"]["risk"], -3)
    # quality
    h = c.get("height") or 0
    if c["media_type"] == "video":
        s += 1.5 if h >= 1080 else 1.0 if h >= 720 else 0.4 if h >= 480 else 0
        if c.get("duration") and c["duration"] < 3:
            s -= 2
    else:
        w = c.get("width") or 0
        s += 1.5 if w >= 2500 else 1.0 if w >= 1600 else 0.3 if w >= 1000 else (-1 if w else 0)
    # archival material preferred for history, stock for generic B-roll
    if c.get("archival"):
        s += 0.8
    if c.get("extra", {}).get("curated"):
        s += 1.0
    # period consistency
    per = scene.get("period", {})
    if per.get("start") is not None:
        years = [int(y) for y in YEAR.findall(text)]
        if years:
            lo, hi = per["start"] - 15, (per.get("end") or per["start"]) + 15
            if any(lo <= y <= hi for y in years):
                s += 1.5
            elif all(y > hi + 30 or y < lo - 60 for y in years):
                # e.g. "1940 Timur and his team" (Soviet film) for a scene about Amir Temur (1336-1405)
                s -= 4.0
                c.setdefault("flags", []).append(f"anachronism:year {years[0]} outside {lo}-{hi}")
    if per.get("media_era") == "pre_photographic" and c["media_type"] == "video" and c.get("archival", True):
        # no film exists for the period: a video can only be present-day footage, a documentary or a feature film
        c.setdefault("flags", []).append("pre_photographic_video: must be present-day/documentary footage, verify")
    for bad in scene.get("exclude_terms", []):
        if re.search(rf"\b{re.escape(bad)}\b", text):
            s -= 2.5
            c.setdefault("flags", []).append(f"anachronism:{bad}")
    if re.search(r"\b(ai generated|ai-generated|midjourney|stable diffusion|sora|нейросеть|reconstruction|реконструкция)\b", text):
        c.setdefault("flags", []).append("possible_ai_or_reconstruction")
        c["reconstruction"] = True
        s -= 1.0
    if c.get("extra", {}).get("discovery_only"):
        c.setdefault("flags", []).append("discovery_only")
    return round(s, 3)


def cached_search(p, q: str, media_type: str, lang: str, cache_dir: Path, errors: dict,
                  ttl_sec: int = 7 * 86400) -> list[dict]:
    """Provider search with an on-disk cache (re-runs are fast and polite to archives)."""
    h = hashlib.sha1(f"{p.name}|{media_type}|{lang}|{q}".encode()).hexdigest()[:16]
    f = cache_dir / f"{p.name}_{h}.json"
    if f.exists() and time.time() - f.stat().st_mtime < ttl_sec:
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            pass
    before = len(errors.get(p.name, []))
    res = safe(lambda: p.search(q, media_type, lang), p.name, errors)
    if len(errors.get(p.name, [])) == before:  # cache only successful calls
        f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res


def scene_queries(scene: dict, langs: list[str], media_type: str, limit: int) -> list[tuple[str, str]]:
    qs: list[tuple[str, str]] = []
    q = scene.get("queries", {})
    # interleave languages so the first N queries are multilingual
    pools = [[(l, x) for x in q.get(l, [])] for l in langs]
    if media_type == "image":
        pools.insert(0, [("en", x) for x in q.get("maps", [])[:1]])
    i = 0
    while len(qs) < limit and any(pools):
        p = pools[i % len(pools)]
        if p:
            qs.append(p.pop(0))
        i += 1
        if i > 200:
            break
    return qs


def run_search(storyboard: dict, cfg: dict, media_type: str, pdir: Path,
               only_providers: list[str] | None = None, max_workers: int = 6) -> dict:
    http = Http(cfg)
    names = only_providers or cfg["search"]["video_providers" if media_type == "video" else "image_providers"]
    providers, skipped = get_providers(names, cfg, http, media_type)
    log.info("%s providers: %s | skipped: %s", media_type, [p.name for p in providers], list(skipped))
    errors: dict[str, list[str]] = {}
    langs = storyboard.get("search_languages") or cfg["project"]["search_languages"]
    per_q = int(cfg["search"]["max_queries_per_scene"])
    results: dict[str, list[dict]] = {}
    stats: dict[str, int] = {}
    manual_links: dict[str, dict] = {}

    # manual URLs belong to all scenes (or the scene given with scene=s003)
    manual = []
    for p in providers:
        if p.name == "manual_urls":
            manual = [m for m in p.load(pdir / "manual_urls.txt") if m["media_type"] == media_type]

    jobs = []
    futures: dict = {}
    cache_dir = pdir / "cache" / "search"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for sc in storyboard["scenes"]:
            for lang, q in scene_queries(sc, langs, media_type, per_q):
                manual_links.setdefault(q, manual_search_links(q))
                for p in providers:
                    if p.name == "manual_urls":
                        continue
                    if p.name in ("pexels", "pixabay", "met_museum", "smithsonian", "openverse") and lang not in ("en", "ru"):
                        continue  # these APIs index English (and partly Russian) metadata only
                    key = f"{p.name}|{media_type}|{lang}|{q.lower()}"
                    if key not in futures:  # identical queries across scenes run once
                        futures[key] = ex.submit(cached_search, p, q, media_type, lang, cache_dir, errors)
                    jobs.append((sc, lang, q, p, futures[key]))
        for sc, lang, q, p, fut in jobs:
            cands = fut.result()
            stats[p.name] = stats.get(p.name, 0) + len(cands)
            bucket = results.setdefault(sc["id"], [])
            for c in cands:
                c = copy.deepcopy(c)
                c["scene_id"] = sc["id"]
                c["score"] = score_candidate(c, sc, q, cfg)
                bucket.append(c)

    for sc in storyboard["scenes"]:
        bucket = results.setdefault(sc["id"], [])
        for m in manual:
            if m["extra"].get("scene") in ("", sc["id"]):
                mc = dict(m, scene_id=sc["id"], score=10.0 if m["extra"].get("scene") == sc["id"] else 2.0)
                bucket.append(mc)
        # dedupe by page/media url keeping best score
        best: dict[str, dict] = {}
        for c in bucket:
            key = (c.get("media_url") or c["page_url"]).split("?")[0].lower()
            if key not in best or c["score"] > best[key]["score"]:
                best[key] = c
        results[sc["id"]] = sorted(best.values(), key=lambda c: c["score"], reverse=True)[:40]

    report = {
        "media_type": media_type,
        "providers_used": [p.name for p in providers],
        "providers_skipped": skipped,
        "provider_errors": {k: {"count": len(v), "examples": sorted(set(v))[:3]} for k, v in errors.items()},
        "candidates_per_provider": stats,
        "scenes": {k: len(v) for k, v in results.items()},
    }
    write_json(pdir / f"candidates_{media_type}.json", results)
    write_json(pdir / "reports" / f"search_report_{media_type}.json", report)
    write_manual_links(pdir / "reports" / "manual_search_links.md", manual_links, media_type)
    return report


def write_manual_links(path: Path, links: dict[str, dict], media_type: str) -> None:
    lines = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    marker = f"## {media_type}"
    if marker in lines:
        return
    if not lines:
        lines = ["# Manual search links", "",
                 "Platforms without an API key/integration (X, Facebook, Mover.uz, Mixkit, Yandex/Google without keys).",
                 "Open, check licence on the ORIGINAL page, then add lines to `manual_urls.txt`:",
                 "`URL | license=CC BY 4.0 | author=@name | scene=s003`", ""]
    lines += [marker, ""]
    for q, d in list(links.items())[:120]:
        lines.append(f"- **{q}** — " + " · ".join(f"[{k}]({v})" for k, v in d.items()))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
