"""STEP 6-7: media research + asset validation with license tracking.

Automatic sources are limited to material whose licence permits reuse:
  * Wikimedia Commons (CC0 / Public domain / CC BY / CC BY-SA) — credit is burned into the video
  * files the admin drops into episodes/<id>/media/ together with a licence note (official press
    photos, own footage, purchased stock, footage used with written permission)

News photos from agencies, TV, Telegram, X, VK, Rutube etc. are NOT downloaded automatically:
being online does not make them free to reuse. Add them manually only with permission.
"""
import json
import re
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from .config import USER_AGENT
from .db import conn, log

OK_LICENSES = re.compile(r"^(cc0|public domain|pd|cc[ -]by(-sa)?([ -]\d\.\d)?|attribution)", re.I)
BAD = re.compile(r"(nc|nd|non-?commercial|no ?deriv|fair use)", re.I)
API = "https://commons.wikimedia.org/w/api.php"


def _get(url: str, tries: int = 4) -> dict:
    import time
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(int(e.headers.get("retry-after") or 5) + 2 * i)  # retry with backoff
    return {}


def _strip(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def search_commons(query: str, limit: int = 8) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 1600,
    }
    data = _get(API + "?" + urllib.parse.urlencode(params))
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = _strip(md.get("LicenseShortName", {}).get("value", ""))
        if not lic or BAD.search(lic) or not OK_LICENSES.search(lic):
            continue
        if ii.get("width", 0) < 900:
            continue
        out.append({
            "title": p.get("title", ""),
            "thumb": ii.get("thumburl") or ii.get("url"),
            "page": ii.get("descriptionurl"),
            "license": lic,
            "author": _strip(md.get("Artist", {}).get("value", ""))[:80] or "Wikimedia Commons",
            "date": _strip(md.get("DateTimeOriginal", {}).get("value", ""))[:20],
            "desc": _strip(md.get("ImageDescription", {}).get("value", ""))[:200],
        })
    return out


def fetch_media(ep_dir: Path, ep_id: str, queries: list[str], per_query: int = 2, max_total: int = 6) -> list[dict]:
    """Downloads licence-clean images into ep_dir/media and records credits in DB + media.json."""
    mdir = ep_dir / "media"
    mdir.mkdir(parents=True, exist_ok=True)
    got, seen = [], set()
    for q in queries:
        try:
            res = search_commons(q)
        except Exception as ex:
            log("WARN", f"commons search failed '{q}': {ex}", ep_id)
            continue
        n = 0
        for r in res:
            if r["page"] in seen or len(got) >= max_total:
                continue
            fn = mdir / f"{len(got) + 1:02d}.jpg"
            try:
                req = urllib.request.Request(r["thumb"], headers={"User-Agent": USER_AGENT})
                raw = urllib.request.urlopen(req, timeout=40).read()
                tmp = fn.with_suffix(".src")
                tmp.write_bytes(raw)
                # normalise: max 1600px, jpeg, strip metadata
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", str(fn)], check=True)
                tmp.unlink()
            except Exception as ex:
                log("WARN", f"download failed {r['page']}: {ex}", ep_id)
                continue
            seen.add(r["page"])
            item = {"file": f"media/{fn.name}", "kind": "image", "source_url": r["page"], "license": r["license"],
                    "author": r["author"], "title": r["title"], "query": q, "date": r["date"], "desc": r["desc"]}
            got.append(item)
            n += 1
            if n >= per_query:
                break
    register(ep_dir, ep_id, got)
    return got


def register(ep_dir: Path, ep_id: str, items: list[dict]):
    """Merge items into media.json and the DB (also used for manually added, licensed files)."""
    mj = ep_dir / "media.json"
    existing = json.loads(mj.read_text()) if mj.exists() else []
    files = {m["file"] for m in existing}
    existing += [m for m in items if m["file"] not in files]
    mj.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    with conn() as c:
        c.execute("DELETE FROM media_assets WHERE episode_id=?", (ep_id,))
        for m in existing:
            c.execute("INSERT INTO media_assets (episode_id,file,source_url,license,author,title,kind) VALUES (?,?,?,?,?,?,?)",
                      (ep_id, m["file"], m.get("source_url"), m.get("license"), m.get("author"), m.get("title"), m.get("kind", "image")))
    return existing


def credits_line(items: list[dict]) -> str:
    if not items:
        return ""
    parts = []
    for m in items:
        a = re.sub(r"\s+", " ", m.get("author", ""))[:40]
        parts.append(f"{a} ({m.get('license')})")
    uniq = list(dict.fromkeys(parts))
    return "Foto: " + "; ".join(uniq[:4]) + (" va b." if len(uniq) > 4 else "") + " — Wikimedia Commons"
