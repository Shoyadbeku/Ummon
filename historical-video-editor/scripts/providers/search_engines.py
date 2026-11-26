"""Image search engines: Yandex Images (primary) and Google Images.

Both are only used to DISCOVER images. The search-engine result page is never
the source: each hit carries the ORIGINAL page URL (Yandex `pageUrl`, Google
`image.contextLink`), which verify_license.py then inspects (Commons/Flickr/
museum pages get their real licence re-checked; anything else stays risk 4).

Without keys we still produce manual search links (reports/manual_search_links.md)
so a human can browse Yandex/Google — this is reported honestly as "manual".
"""
from __future__ import annotations

import base64
import re
from urllib.parse import quote_plus

from common import env
from providers.base import Provider, register


@register
class YandexImages(Provider):
    """Yandex Cloud Search API v2 — image search (POST /v2/image/search).
    Docs: https://yandex.cloud/en/docs/search-api/concepts/image-search"""
    name = "yandex_images"
    label = "Yandex Images"
    media_types = ("image",)
    requires = ("YANDEX_SEARCH_API_KEY", "YANDEX_FOLDER_ID")
    URL = "https://searchapi.api.cloud.yandex.net/v2/image/search"

    def search(self, query, media_type, lang="en"):
        search_type = {"ru": "SEARCH_TYPE_RU", "uz": "SEARCH_TYPE_RU", "tr": "SEARCH_TYPE_TR",
                       "kk": "SEARCH_TYPE_KK", "be": "SEARCH_TYPE_BE"}.get(lang, "SEARCH_TYPE_COM")
        body = {"query": {"searchType": search_type, "queryText": query, "familyMode": "FAMILY_MODE_MODERATE"},
                "imageSpec": {"size": "IMAGE_SIZE_LARGE"}, "docsOnPage": str(min(self.limit, 60)),
                "folderId": env("YANDEX_FOLDER_ID")}
        r = self.http.request("POST", self.URL, json=body,
                              headers={"Authorization": f"Api-Key {env('YANDEX_SEARCH_API_KEY')}"})
        if r.status_code != 200:
            raise ConnectionError(f"Yandex HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        images = data.get("images")
        if images is None and data.get("rawData"):  # XML variant
            images = self._parse_xml(base64.b64decode(data["rawData"]).decode("utf-8", "replace"))
        out = []
        for im in images or []:
            page = im.get("pageUrl") or im.get("page_url") or ""
            if not page:
                continue  # we refuse results without an original page
            out.append(self.cand(
                "image", page_url=page, title=im.get("pageTitle") or im.get("passage") or "",
                media_url=im.get("url", ""), width=int(im.get("width") or 0), height=int(im.get("height") or 0),
                license_raw="", source_label=re.sub(r"^www\.", "", im.get("host") or ""), query=query, lang=lang,
                extra={"found_via": "Yandex Images", "discovery_only": True}))
        return out

    @staticmethod
    def _parse_xml(xml: str) -> list[dict]:
        out = []
        for doc in re.findall(r"<doc\b.*?</doc>", xml, re.S):
            def g(tag):
                m = re.search(rf"<{tag}>(.*?)</{tag}>", doc, re.S)
                return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
            out.append({"url": g("image-link") or g("url"), "pageUrl": g("url"), "pageTitle": g("title"),
                        "width": g("original-width") or 0, "height": g("original-height") or 0, "host": g("domain")})
        return out


@register
class GoogleImages(Provider):
    """Google Programmable Search JSON API (searchType=image) with CC rights filter."""
    name = "google_images"
    label = "Google Images"
    media_types = ("image",)
    requires = ("GOOGLE_API_KEY", "GOOGLE_CSE_ID")

    def search(self, query, media_type, lang="en"):
        params = {"key": env("GOOGLE_API_KEY"), "cx": env("GOOGLE_CSE_ID"), "q": query, "searchType": "image",
                  "num": min(10, self.limit), "imgSize": "xlarge", "safe": "active",
                  "rights": "cc_publicdomain|cc_attribute|cc_sharealike", "hl": lang}
        data = self.http.get_json("https://www.googleapis.com/customsearch/v1", params=params)
        out = []
        for it in data.get("items", []):
            img = it.get("image", {})
            page = img.get("contextLink", "")
            if not page:
                continue
            out.append(self.cand(
                "image", page_url=page, title=it.get("title", ""), media_url=it.get("link", ""),
                thumb_url=img.get("thumbnailLink", ""), width=img.get("width", 0), height=img.get("height", 0),
                license_raw="", source_label=it.get("displayLink", ""), query=query, lang=lang,
                extra={"found_via": "Google Images", "discovery_only": True}))
        return out


def manual_search_links(query: str) -> dict:
    q = quote_plus(query)
    return {
        "yandex_images": f"https://yandex.ru/images/search?text={q}&isize=large",
        "google_images_cc": f"https://www.google.com/search?tbm=isch&q={q}&tbs=sur:fmc,isz:l",
        "commons": f"https://commons.wikimedia.org/w/index.php?search={q}&title=Special:MediaSearch&type=image",
        "europeana": f"https://www.europeana.eu/en/search?query={q}&reusability=open",
        "mixkit": f"https://mixkit.co/free-stock-video/{quote_plus(query.replace(' ', '-'))}/",
        "mover_uz": f"https://mover.uz/search?val={q}",
        "x": f"https://x.com/search?q={q}%20filter%3Avideos&f=live",
        "facebook": f"https://www.facebook.com/search/videos/?q={q}",
        "rutube": f"https://rutube.ru/search/?query={q}",
        "vk_video": f"https://vkvideo.ru/?q={q}",
    }
