"""Free stock providers with official APIs: Pexels and Pixabay.
Mixkit has no public API — add Mixkit URLs to manual_urls.txt (licence: mixkit)."""
from __future__ import annotations

from common import env
from providers.base import Provider, register


@register
class Pexels(Provider):
    name = "pexels"
    label = "Pexels"
    media_types = ("video", "image")
    requires = ("PEXELS_API_KEY",)

    def search(self, query, media_type, lang="en"):
        h = {"Authorization": env("PEXELS_API_KEY")}
        locale = {"ru": "ru-RU", "en": "en-US"}.get(lang)
        params = {"query": query, "per_page": self.limit, "orientation": "landscape"}
        if locale:
            params["locale"] = locale
        out = []
        if media_type == "video":
            data = self.http.get_json("https://api.pexels.com/videos/search", params=params, headers=h)
            for v in data.get("videos", []):
                files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("height")]
                files.sort(key=lambda f: (f["height"] <= 2160, f["height"]), reverse=True)
                best = next((f for f in files if f["height"] <= 2160), files[0] if files else None)
                if not best:
                    continue
                out.append(self.cand(
                    "video", page_url=v.get("url", ""), title=v.get("url", "").rstrip("/").split("/")[-1].replace("-", " "),
                    media_url=best["link"], thumb_url=v.get("image", ""), width=best.get("width", 0),
                    height=best.get("height", 0), duration=v.get("duration", 0), author=v.get("user", {}).get("name", ""),
                    archival=False, query=query, lang=lang))
        else:
            data = self.http.get_json("https://api.pexels.com/v1/search", params=params, headers=h)
            for p in data.get("photos", []):
                out.append(self.cand(
                    "image", page_url=p.get("url", ""), title=p.get("alt", ""), media_url=p["src"]["original"],
                    thumb_url=p["src"].get("medium", ""), width=p.get("width", 0), height=p.get("height", 0),
                    author=p.get("photographer", ""), archival=False, query=query, lang=lang))
        return out


@register
class Pixabay(Provider):
    name = "pixabay"
    label = "Pixabay"
    media_types = ("video", "image")
    requires = ("PIXABAY_API_KEY",)

    def search(self, query, media_type, lang="en"):
        params = {"key": env("PIXABAY_API_KEY"), "q": query[:100], "per_page": max(3, min(200, self.limit)),
                  "safesearch": "true", "lang": lang if lang in ("ru", "en", "tr", "de", "fr") else "en"}
        out = []
        if media_type == "video":
            data = self.http.get_json("https://pixabay.com/api/videos/", params=params)
            for h in data.get("hits", []):
                vids = h.get("videos", {})
                best = next((vids[k] for k in ("large", "medium", "small") if vids.get(k, {}).get("url")), None)
                if not best:
                    continue
                out.append(self.cand(
                    "video", page_url=h.get("pageURL", ""), title=h.get("tags", ""), media_url=best["url"],
                    thumb_url=best.get("thumbnail", ""), width=best.get("width", 0), height=best.get("height", 0),
                    duration=h.get("duration", 0), author=h.get("user", ""), archival=False, query=query, lang=lang))
        else:
            params["image_type"] = "photo"
            data = self.http.get_json("https://pixabay.com/api/", params=params)
            for h in data.get("hits", []):
                out.append(self.cand(
                    "image", page_url=h.get("pageURL", ""), title=h.get("tags", ""),
                    media_url=h.get("largeImageURL", ""), thumb_url=h.get("previewURL", ""),
                    width=h.get("imageWidth", 0), height=h.get("imageHeight", 0), author=h.get("user", ""),
                    archival=False, query=query, lang=lang))
        return out
