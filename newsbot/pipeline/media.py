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


def _download(url: str, max_bytes: int = 250 * 1024 * 1024) -> bytes:
    """Polite download from upload.wikimedia.org: pause between files, back off on 429."""
    import time
    for i in range(5):
        time.sleep(2.5)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=180) as r:
                buf = bytearray()
                while chunk := r.read(1 << 20):
                    buf += chunk
                    if len(buf) > max_bytes:
                        raise RuntimeError("file too large")
                return bytes(buf)
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 4:
                raise
            time.sleep(int(e.headers.get("retry-after") or 20) + 15 * i)
    raise RuntimeError("unreachable")


def search_commons(query: str, limit: int = 8) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 1920,
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
                raw = _download(r["thumb"])
                tmp = fn.with_suffix(".src")
                tmp.write_bytes(raw)
                # normalise: max 1600px, jpeg, strip metadata
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-vf", "scale='min(1920,iw)':-2", "-q:v", "3", str(fn)], check=True)
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


# ---------------------------------------------------------------- video B-roll (Wikimedia Commons)

def search_commons_video(query: str, limit: int = 10, min_dur: float = 6) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:video",
        "gsrnamespace": 6, "gsrlimit": limit, "prop": "videoinfo", "viprop": "url|extmetadata|size|derivatives",
    }
    data = _get(API + "?" + urllib.parse.urlencode(params))
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        vi = (p.get("videoinfo") or [{}])[0]
        md = vi.get("extmetadata", {})
        lic = _strip(md.get("LicenseShortName", {}).get("value", ""))
        if not lic or BAD.search(lic) or not OK_LICENSES.search(lic):
            continue
        dur = float(vi.get("duration") or 0)
        ders = [d for d in vi.get("derivatives", []) if "webm" in d.get("type", "") or "mp4" in d.get("type", "")]
        ders.sort(key=lambda d: abs((d.get("height") or 0) - 1080))
        if dur < min_dur or not ders or (ders[0].get("height") or 0) < 470:
            continue
        out.append({
            "title": p.get("title", ""), "src": ders[0]["src"], "page": vi.get("descriptionurl"), "license": lic,
            "author": _strip(md.get("Artist", {}).get("value", ""))[:80] or "Wikimedia Commons",
            "duration": dur, "w": vi.get("width"), "h": vi.get("height"),
            "desc": _strip(md.get("ImageDescription", {}).get("value", ""))[:200],
        })
    return out


def fetch_clip(ep_dir: Path, ep_id: str, item: dict, name: str, clip_sec: float = 6.0) -> dict | None:
    """Downloads a Commons video derivative and cuts a short clip (no audio) from its middle."""
    mdir = ep_dir / "media"
    mdir.mkdir(parents=True, exist_ok=True)
    raw = mdir / f"{name}.src"
    out = mdir / f"{name}.mp4"
    try:
        raw.write_bytes(_download(item["src"]))
        start = max(0.0, item["duration"] * 0.3 - clip_sec / 2)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", str(raw), "-t", f"{clip_sec}",
                        "-an", "-vf", "scale=-2:'min(1080,ih)',fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", str(out)], check=True)
    except Exception as ex:
        log("WARN", f"clip failed {item.get('page')}: {ex}", ep_id)
        return None
    finally:
        raw.unlink(missing_ok=True)
    return {"file": f"media/{out.name}", "kind": "video", "source_url": item["page"], "license": item["license"],
            "author": item["author"], "title": item["title"], "desc": item["desc"], "clip_start": round(start, 2)}


def credit_for(m: dict) -> str:
    """Short on-screen source credit shown while the asset is visible."""
    kind = "FOOTAGE" if m.get("kind") == "video" else "PHOTO"
    author = re.sub(r"\s+", " ", m.get("author") or "").strip()[:38]
    src = m.get("credit_source") or "Wikimedia Commons"
    return f"{kind}: {author} / {src} ({m.get('license')})" if author else f"{kind}: {src} ({m.get('license')})"


def fetch_titles(ep_dir: Path, ep_id: str, titles: list[str], illustrative: bool = True, clip_sec: float = 6.0) -> list[dict]:
    """Fetch specific Commons files (images or videos) chosen by the editor after reviewing search results."""
    params = {"action": "query", "format": "json", "titles": "|".join(titles), "prop": "imageinfo|videoinfo",
              "iiprop": "url|extmetadata|size|mediatype", "iiurlwidth": 1920, "viprop": "url|extmetadata|size|derivatives"}
    data = _get(API + "?" + urllib.parse.urlencode(params))
    pages = {p["title"]: p for p in data.get("query", {}).get("pages", {}).values()}
    mj = ep_dir / "media.json"
    existing = json.loads(mj.read_text()) if mj.exists() else []
    got = []
    for t in titles:
        p = pages.get(t.replace("_", " "))
        if not p:
            log("WARN", f"not found: {t}", ep_id); continue
        info = (p.get("videoinfo") or p.get("imageinfo") or [{}])[0]
        md = info.get("extmetadata", {})
        lic = _strip(md.get("LicenseShortName", {}).get("value", ""))
        if not lic or BAD.search(lic) or not OK_LICENSES.search(lic):
            log("WARN", f"licence rejected {t}: {lic}", ep_id); continue
        author = _strip(md.get("Artist", {}).get("value", ""))[:80] or "Wikimedia Commons"
        n = len(existing) + len(got) + 1
        is_video = info.get("mediatype") == "VIDEO" or t.lower().endswith((".webm", ".ogv", ".mp4"))
        if is_video:
            ders = [d for d in info.get("derivatives", []) if "webm" in d.get("type", "") or "mp4" in d.get("type", "")]
            ders.sort(key=lambda d: abs((d.get("height") or 0) - 1080))
            if not ders:   # originals on upload.wikimedia.org are rate-limited; use transcoded derivatives only
                log("WARN", f"no derivative for {t}", ep_id); continue
            item = {"title": t, "src": ders[0]["src"], "page": info.get("descriptionurl"),
                    "license": lic, "author": author, "duration": float(info.get("duration") or 10), "desc": ""}
            m = fetch_clip(ep_dir, ep_id, item, f"{n:02d}", clip_sec)
        else:
            fn = ep_dir / "media" / f"{n:02d}.jpg"
            fn.parent.mkdir(parents=True, exist_ok=True)
            try:
                if not info.get("thumburl"):
                    raise RuntimeError("no thumbnail url")
                raw = _download(info["thumburl"])
                tmp = fn.with_suffix(".src"); tmp.write_bytes(raw)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-vf", "scale='min(1920,iw)':-2", "-q:v", "3", str(fn)], check=True)
                tmp.unlink()
                m = {"file": f"media/{fn.name}", "kind": "image", "source_url": info.get("descriptionurl"), "license": lic,
                     "author": author, "title": t}
            except Exception as ex:
                log("WARN", f"image failed {t}: {ex}", ep_id); m = None
        if m:
            m["illustrative"] = illustrative
            got.append(m)
    register(ep_dir, ep_id, got)
    return got
