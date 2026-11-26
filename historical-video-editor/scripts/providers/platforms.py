"""Social / video platforms.

Policy (see references/fair_use.md):
  * YouTube Data API search is restricted to videoLicense=creativeCommon -> CC BY, downloadable.
  * yt-dlp discovery, Rutube, VK, Reddit, X, Facebook, Mover.uz results are DISCOVERY ONLY:
    licence = unknown (risk 4). They are NOT downloaded automatically unless the user records a
    licence/permission for that URL in manual_urls.txt, or the platform metadata itself states a
    Creative Commons licence (verified in verify_license.py).
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from common import env, log
from providers.base import Provider, ProviderUnavailable, register


def ytdlp_bin() -> str | None:
    return shutil.which("yt-dlp")


def ytdlp_json(target: str, flat: bool = True, timeout: int = 90) -> dict:
    exe = ytdlp_bin()
    if not exe:
        raise ProviderUnavailable("yt-dlp not installed (pip install yt-dlp)")
    is_search = bool(re.match(r"^[a-z]+search\d*(all)?:", target))
    cmd = [exe, "-J", "--no-warnings", "--skip-download", "--flat-playlist" if (is_search and flat) else "--no-playlist"]
    cmd.append(target)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise ConnectionError(f"yt-dlp: {p.stderr.strip()[-300:]}")
    return json.loads(p.stdout or "{}")


def license_from_ytdlp(info: dict) -> str:
    lic = info.get("license") or ""
    if not lic and "creative commons" in (info.get("description") or "").lower()[:4000]:
        return ""  # description claims are not trusted as licence
    return lic


# ---------------------------------------------------------------------------
@register
class YouTubeCC(Provider):
    """Official YouTube Data API v3 — Creative Commons videos only."""
    name = "youtube_cc"
    label = "YouTube"
    media_types = ("video",)
    requires = ("YOUTUBE_API_KEY",)

    def search(self, query, media_type, lang="en"):
        params = {"part": "snippet", "type": "video", "videoLicense": "creativeCommon", "q": query,
                  "maxResults": min(50, self.limit), "key": env("YOUTUBE_API_KEY"), "relevanceLanguage": lang,
                  "videoDefinition": "any"}
        data = self.http.get_json("https://www.googleapis.com/youtube/v3/search", params=params)
        out = []
        for it in data.get("items", []):
            vid = it["id"].get("videoId")
            sn = it.get("snippet", {})
            out.append(self.cand(
                "video", page_url=f"https://www.youtube.com/watch?v={vid}", title=sn.get("title", ""),
                description=sn.get("description", ""), thumb_url=(sn.get("thumbnails", {}).get("high") or {}).get("url", ""),
                author=sn.get("channelTitle", ""), handle=sn.get("channelTitle", ""),
                license_raw="Creative Commons Attribution license (reuse allowed)",
                license_url="https://creativecommons.org/licenses/by/3.0/", date=sn.get("publishedAt", ""),
                download_method="ytdlp", query=query, lang=lang, extra={"youtube_id": vid}))
        return out


# ---------------------------------------------------------------------------
@register
class YtDlpDiscovery(Provider):
    """yt-dlp search (YouTube) — finds candidates; licence verified per video later."""
    name = "ytdlp_discovery"
    label = "YouTube"
    media_types = ("video",)

    def __init__(self, cfg, http):
        super().__init__(cfg, http)
        if not ytdlp_bin():
            raise ProviderUnavailable("yt-dlp not installed")

    def search(self, query, media_type, lang="en"):
        n = min(10, self.limit)
        data = ytdlp_json(f"ytsearch{n}:{query}")
        out = []
        for e in data.get("entries", []) or []:
            url = e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
            if "/shorts/" in url:
                continue
            out.append(self.cand(
                "video", page_url=url, title=e.get("title", ""), description=e.get("description") or "",
                duration=e.get("duration") or 0, author=e.get("channel") or e.get("uploader") or "",
                handle=e.get("channel") or "", thumb_url=(e.get("thumbnails") or [{}])[-1].get("url", ""),
                license_raw="", download_method="ytdlp", query=query, lang=lang,
                extra={"discovery_only": True, "views": e.get("view_count")}))
        return out


# ---------------------------------------------------------------------------
@register
class Rutube(Provider):
    name = "rutube"
    label = "Rutube"
    media_types = ("video",)

    def search(self, query, media_type, lang="en"):
        data = self.http.get_json("https://rutube.ru/api/search/video/", params={"query": query, "page": 1},
                                  headers={"Accept": "application/json"})
        out = []
        for r in (data.get("results") or [])[: self.limit]:
            author = (r.get("author") or {}).get("name", "")
            out.append(self.cand(
                "video", page_url=r.get("video_url", ""), title=r.get("title", ""),
                description=r.get("description", ""), thumb_url=r.get("thumbnail_url", ""),
                duration=r.get("duration") or 0, author=author, handle=author, license_raw="",
                date=r.get("publication_ts") or r.get("created_ts", ""), download_method="ytdlp",
                query=query, lang=lang, extra={"discovery_only": True}))
        return out


# ---------------------------------------------------------------------------
@register
class VKVideo(Provider):
    name = "vk_video"
    label = "VK Video"
    media_types = ("video",)
    requires = ("VK_ACCESS_TOKEN",)

    def search(self, query, media_type, lang="en"):
        params = {"q": query, "count": min(200, self.limit), "adult": 0, "access_token": env("VK_ACCESS_TOKEN"),
                  "v": "5.199", "sort": 2}
        data = self.http.get_json("https://api.vk.com/method/video.search", params=params)
        if "error" in data:
            raise ConnectionError(f"VK: {data['error'].get('error_msg')}")
        out = []
        for v in data.get("response", {}).get("items", []):
            url = f"https://vk.com/video{v.get('owner_id')}_{v.get('id')}"
            imgs = v.get("image") or []
            out.append(self.cand(
                "video", page_url=url, title=v.get("title", ""), description=v.get("description", ""),
                thumb_url=imgs[-1]["url"] if imgs else "", duration=v.get("duration", 0),
                width=v.get("width", 0), height=v.get("height", 0), author=str(v.get("owner_id")),
                handle=f"vk.com/id{v.get('owner_id')}" if v.get("owner_id", 0) > 0 else f"vk.com/club{-v.get('owner_id', 0)}",
                license_raw="", date=v.get("date", ""), download_method="ytdlp", query=query, lang=lang,
                extra={"discovery_only": True}))
        return out


# ---------------------------------------------------------------------------
@register
class Reddit(Provider):
    name = "reddit"
    label = "Reddit"
    media_types = ("video", "image")
    requires = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET")
    _tok: tuple[str, float] | None = None

    def _token(self) -> str:
        if self._tok and self._tok[1] > time.time():
            return self._tok[0]
        auth = base64.b64encode(f"{env('REDDIT_CLIENT_ID')}:{env('REDDIT_CLIENT_SECRET')}".encode()).decode()
        r = self.http.request("POST", "https://www.reddit.com/api/v1/access_token",
                              data={"grant_type": "client_credentials"}, headers={"Authorization": f"Basic {auth}"})
        if r.status_code != 200:
            raise ConnectionError(f"Reddit auth HTTP {r.status_code}")
        j = r.json()
        Reddit._tok = (j["access_token"], time.time() + int(j.get("expires_in", 3600)) - 60)
        return Reddit._tok[0]

    def search(self, query, media_type, lang="en"):
        h = {"Authorization": f"bearer {self._token()}"}
        sr = "OldSchoolCool+HistoryPorn+ColorizedHistory+history+ArchivalFootage+TheWayWeWere+CentralAsia+uzbekistan"
        data = self.http.get_json(f"https://oauth.reddit.com/r/{sr}/search", headers=h,
                                  params={"q": query, "restrict_sr": 1, "limit": min(100, self.limit), "type": "link"})
        out = []
        for ch in data.get("data", {}).get("children", []):
            d = ch.get("data", {})
            is_vid = bool(d.get("is_video"))
            if (media_type == "video") != is_vid:
                continue
            url = "https://www.reddit.com" + d.get("permalink", "")
            out.append(self.cand(
                media_type, page_url=url, title=d.get("title", ""), media_url="" if is_vid else d.get("url", ""),
                thumb_url=d.get("thumbnail", "") if str(d.get("thumbnail", "")).startswith("http") else "",
                author=f"u/{d.get('author', '')}", handle=f"r/{d.get('subreddit', '')}", license_raw="",
                download_method="ytdlp" if is_vid else "http", query=query, lang=lang,
                extra={"discovery_only": True, "linked_url": d.get("url")}))
        return out


# ---------------------------------------------------------------------------
@register
class ManualUrls(Provider):
    """Read <project>/manual_urls.txt — one URL per line, optional fields separated by ' | ':

        https://x.com/user/status/123 | license=permission | author=@user | note=email 2026-10-01
        https://mover.uz/watch/abc     | license=CC BY 4.0
        https://mixkit.co/free-stock-video/desert-1234/ | license=mixkit

    Works for any site yt-dlp supports (X, Facebook, VK, Rutube, OK.ru, Vimeo, Dailymotion,
    many news sites) plus direct .mp4/.jpg links. 'license=permission' means the user holds
    written permission (stored in sources report)."""
    name = "manual_urls"
    label = "Manual"
    media_types = ("video", "image")
    _cache: dict[str, list[dict]] = {}

    def search(self, query, media_type, lang="en"):
        return []  # manual URLs are not query-based; see load()

    def load(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(" | ")]
            url, meta = parts[0], {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    meta[k.strip().lower()] = v.strip()
            is_img = bool(re.search(r"\.(jpe?g|png|webp|tiff?)(\?|$)", url, re.I))
            info = {}
            if not is_img and not re.search(r"\.(mp4|webm|mov|mkv|ogv)(\?|$)", url, re.I):
                try:
                    info = ytdlp_json(url, flat=False)
                except Exception as e:  # noqa: BLE001
                    log.warning("manual url metadata failed for %s: %s", url, str(e)[:150])
            lic = meta.get("license", "") or license_from_ytdlp(info)
            if lic.lower() == "permission":
                lic_raw = "Used with permission"
            else:
                lic_raw = lic
            host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0])
            label = {"x.com": "X", "twitter.com": "X", "facebook.com": "Facebook", "fb.watch": "Facebook",
                     "mover.uz": "Mover.uz", "vk.com": "VK Video", "vkvideo.ru": "VK Video", "rutube.ru": "Rutube",
                     "youtube.com": "YouTube", "youtu.be": "YouTube", "mixkit.co": "Mixkit"}.get(host, host)
            author = meta.get("author") or info.get("uploader") or info.get("channel") or ""
            handle = meta.get("author") if (meta.get("author", "").startswith("@")) else (
                f"@{info['uploader_id']}" if info.get("uploader_id") and label == "X" else "")
            c = self.cand(
                "image" if is_img else "video", page_url=url, title=info.get("title") or meta.get("title", url),
                description=info.get("description") or meta.get("note", ""), media_url=url if (is_img or not info) else "",
                duration=info.get("duration") or 0, width=info.get("width") or 0, height=info.get("height") or 0,
                author=author, handle=handle, license_raw=lic_raw, date=info.get("upload_date", ""),
                source_label=label, download_method="http" if (is_img or not info) else "ytdlp",
                archival=meta.get("archival", "yes") != "no", query="manual", lang="",
                extra={"manual": True, "permission": lic.lower() == "permission", "note": meta.get("note", ""),
                       "scene": meta.get("scene", ""), "present_day": meta.get("present_day") == "yes",
                       "reconstruction": meta.get("reconstruction") == "yes"})
            if lic.lower() == "permission":
                c["license"].update(code="permission", label="Used with permission", risk=1, commercial_ok=True,
                                    modify_ok=True, attribution_required=True)
            elif lic.lower() == "mixkit":
                from licenses import classify
                c["license"] = classify("", "", "mixkit")
            out.append(c)
        return out
