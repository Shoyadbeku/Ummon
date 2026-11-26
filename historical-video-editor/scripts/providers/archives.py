"""Archive / museum providers with official public APIs:
Internet Archive, Wikimedia Commons, Library of Congress, Europeana,
The Met (Open Access), Smithsonian Open Access, Openverse.
"""
from __future__ import annotations

import re
import time
from urllib.parse import quote

from common import env, log
from providers.base import Provider, register, strip_html


# ---------------------------------------------------------------------------
@register
class InternetArchive(Provider):
    name = "internet_archive"
    label = "Internet Archive"
    media_types = ("video", "image")
    API = "https://archive.org/advancedsearch.php"
    # collections that are curated public-domain / archival film
    GOOD = {"prelinger", "prelinger_library", "publicdomainmovies", "feature_films", "classic_tv",
            "newsandpublicaffairs", "universal_newsreels", "nasa", "ephemera", "usgovernmentdocuments",
            "fedflix", "pathe", "britishpathe", "gosfilmofond", "softwarelibrary_msdos_films"}
    BAD = {"tvarchive", "tvnews", "podcasts_mirror", "fringe", "deemphasize"}

    def search(self, query, media_type, lang="en"):
        mt = "movies" if media_type == "video" else "image"
        q = (f'(title:({query}) OR subject:({query}) OR description:({query})) AND mediatype:{mt} '
             f'AND -collection:(tvarchive OR tvnews OR podcasts_mirror OR fringe)')
        params = {"q": q, "rows": self.limit, "output": "json", "sort[]": "downloads desc",
                  "fl[]": ["identifier", "title", "licenseurl", "collection", "year", "creator", "date",
                           "description", "rights"]}
        data = self.http.get_json(self.API, params=params)
        out = []
        for d in data.get("response", {}).get("docs", []):
            ident = d["identifier"]
            cols = set(d.get("collection") if isinstance(d.get("collection"), list) else [d.get("collection", "")])
            if cols & self.BAD:
                continue
            lic = d.get("licenseurl") or ""
            rights = d.get("rights") if isinstance(d.get("rights"), str) else ""
            if not lic and cols & {"prelinger", "publicdomainmovies", "fedflix", "nasa", "universal_newsreels"}:
                lic = "Public Domain (collection: %s)" % ", ".join(sorted(cols & self.GOOD))
            out.append(self.cand(
                media_type, page_url=f"https://archive.org/details/{ident}", title=d.get("title", ident),
                description=d.get("description", "") if isinstance(d.get("description"), str) else "",
                thumb_url=f"https://archive.org/services/img/{ident}",
                author=d.get("creator", "") if isinstance(d.get("creator"), str) else "",
                license_raw=lic or rights, license_url=lic if lic.startswith("http") else "",
                date=d.get("year") or d.get("date", ""), query=query, lang=lang,
                download_method="http", extra={"ia_identifier": ident, "collections": sorted(cols)[:6],
                                               "curated": bool(cols & self.GOOD)}))
        return out

    def resolve(self, cand: dict) -> dict:
        """Fill media_url/size from the item's file list (called by download step)."""
        ident = cand["extra"]["ia_identifier"]
        meta = self.http.get_json(f"https://archive.org/metadata/{ident}")
        files = meta.get("files", [])
        best = None
        if cand["media_type"] == "video":
            for f in files:
                name = f.get("name", "")
                if not name.lower().endswith((".mp4", ".ogv", ".webm", ".mpeg", ".mpg", ".mov")):
                    continue
                h = int(f.get("height") or 0)
                size = int(f.get("size") or 0)
                score = (name.lower().endswith(".mp4"), h, -size)
                if size and size > 2_500_000_000:  # skip giant masters
                    continue
                if best is None or score > best[0]:
                    best = (score, f)
        else:
            for f in files:
                name = f.get("name", "")
                if name.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")) and "thumb" not in name.lower():
                    size = int(f.get("size") or 0)
                    if best is None or size > best[0][0]:
                        best = ((size,), f)
        if best:
            f = best[1]
            cand["media_url"] = f"https://archive.org/download/{ident}/{quote(f['name'])}"
            cand["height"] = int(f.get("height") or cand.get("height") or 0)
            cand["width"] = int(f.get("width") or cand.get("width") or 0)
            try:
                cand["duration"] = float(f.get("length") or 0) or cand.get("duration", 0)
            except ValueError:
                pass
        md = meta.get("metadata", {})
        if not cand["license_raw"] and md.get("licenseurl"):
            cand["license_raw"] = md["licenseurl"]
        return cand


# ---------------------------------------------------------------------------
@register
class WikimediaCommons(Provider):
    name = "wikimedia_commons"
    label = "Wikimedia Commons"
    media_types = ("video", "image")
    API = "https://commons.wikimedia.org/w/api.php"

    def search(self, query, media_type, lang="en"):
        ft = "filetype:video" if media_type == "video" else "filetype:bitmap"
        params = {
            "action": "query", "format": "json", "formatversion": 2, "generator": "search",
            "gsrsearch": f"{query} {ft}", "gsrnamespace": 6, "gsrlimit": self.limit,
            "prop": "imageinfo|info", "inprop": "url",
            "iiprop": "url|size|mime|extmetadata|mediatype", "iiurlwidth": 2560,
            "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|DateTimeOriginal|ImageDescription|UsageTerms|Copyrighted",
            "uselang": lang,
        }
        data = self.http.get_json(self.API, params=params)
        out = []
        for p in data.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]
            if not ii:
                continue
            em = ii.get("extmetadata", {})
            g = lambda k: strip_html(em.get(k, {}).get("value", ""))  # noqa: E731
            mime = ii.get("mime", "")
            if media_type == "video" and not mime.startswith(("video/", "application/ogg")):
                continue
            if media_type == "image" and not mime.startswith("image/"):
                continue
            lic = g("LicenseShortName") or g("UsageTerms")
            if g("Copyrighted").lower() == "false" and not lic:
                lic = "Public Domain"
            out.append(self.cand(
                media_type, page_url=ii.get("descriptionurl") or p.get("fullurl", ""),
                title=p.get("title", "").replace("File:", ""), description=g("ImageDescription"),
                media_url=(ii.get("thumburl") if media_type == "image" and ii.get("thumburl") and ii.get("width", 0) > 2560
                           else ii.get("url", "")), thumb_url=ii.get("thumburl", ""),
                width=ii.get("width", 0), height=ii.get("height", 0), duration=ii.get("duration", 0) or 0,
                author=g("Artist") or g("Credit"), license_raw=lic, license_url=g("LicenseUrl"),
                date=g("DateTimeOriginal"), query=query, lang=lang,
                extra={"mime": mime, "scaled_url": ii.get("thumburl", "")}))
        return out

    def license_for_page(self, page_url: str) -> dict | None:
        """Used by verify_license when an image search engine points to a Commons page."""
        m = re.search(r"/wiki/(File:[^?#]+)", page_url)
        if not m:
            return None
        params = {"action": "query", "format": "json", "formatversion": 2, "titles": m.group(1).replace("_", " "),
                  "prop": "imageinfo", "iiprop": "url|size|extmetadata"}
        data = self.http.get_json(self.API, params=params)
        pages = data.get("query", {}).get("pages", [])
        if not pages or not pages[0].get("imageinfo"):
            return None
        ii = pages[0]["imageinfo"][0]
        em = ii.get("extmetadata", {})
        return {"license_raw": strip_html(em.get("LicenseShortName", {}).get("value", "")),
                "license_url": strip_html(em.get("LicenseUrl", {}).get("value", "")),
                "author": strip_html(em.get("Artist", {}).get("value", "")),
                "media_url": ii.get("url", ""), "width": ii.get("width", 0), "height": ii.get("height", 0)}


# ---------------------------------------------------------------------------
@register
class LibraryOfCongress(Provider):
    name = "library_of_congress"
    label = "Library of Congress"
    media_types = ("video", "image")

    def search(self, query, media_type, lang="en"):
        coll = "film-and-videos" if media_type == "video" else "photos"
        url = f"https://www.loc.gov/{coll}/"
        data = self.http.get_json(url, params={"q": query, "fo": "json", "c": self.limit, "at": "results"})
        out = []
        for r in data.get("results", []):
            if r.get("access_restricted"):
                continue
            page = r.get("url") or r.get("id", "")
            imgs = r.get("image_url") or []
            rights = r.get("rights_advisory") or r.get("rights") or ""
            if isinstance(rights, list):
                rights = " ".join(rights)
            contrib = r.get("contributor") or []
            out.append(self.cand(
                media_type, page_url=page, title=r.get("title", ""),
                description=" ".join(r.get("description") or []) if isinstance(r.get("description"), list) else r.get("description", ""),
                thumb_url=imgs[0] if imgs else "", media_url=(imgs[-1].split("#")[0] if (imgs and media_type == "image") else ""),
                author=contrib[0] if contrib else "", license_raw=rights, date=r.get("date", ""),
                query=query, lang=lang, extra={"loc_id": r.get("id", "")}))
        return out

    def resolve(self, cand: dict) -> dict:
        data = self.http.get_json(cand["page_url"].rstrip("/") + "/", params={"fo": "json"})
        item = data.get("item", {})
        rights = item.get("rights_advisory") or data.get("rights") or ""
        if rights and not cand["license_raw"]:
            cand["license_raw"] = rights if isinstance(rights, str) else " ".join(rights)
        best = None
        for res in data.get("resources", []):
            for group in res.get("files", []) or []:
                for f in group if isinstance(group, list) else [group]:
                    mt = f.get("mimetype", "")
                    want = "video/" if cand["media_type"] == "video" else "image/"
                    if not mt.startswith(want):
                        continue
                    score = (mt in ("video/mp4", "image/jpeg"), int(f.get("width") or 0), int(f.get("size") or 0))
                    if best is None or score > best[0]:
                        best = (score, f)
        if best:
            cand["media_url"] = best[1]["url"]
            cand["width"] = int(best[1].get("width") or 0)
            cand["height"] = int(best[1].get("height") or 0)
        return cand


# ---------------------------------------------------------------------------
@register
class Europeana(Provider):
    name = "europeana"
    label = "Europeana"
    media_types = ("video", "image")
    requires = ("EUROPEANA_API_KEY",)

    def search(self, query, media_type, lang="en"):
        params = {"wskey": env("EUROPEANA_API_KEY"), "query": query, "rows": self.limit, "media": "true",
                  "qf": f"TYPE:{'VIDEO' if media_type == 'video' else 'IMAGE'}", "reusability": "open",
                  "profile": "rich"}
        data = self.http.get_json("https://api.europeana.eu/record/v2/search.json", params=params)
        out = []
        for it in data.get("items", []):
            rights = (it.get("rights") or [""])[0]
            media = (it.get("edmIsShownBy") or [""])[0]
            page = (it.get("edmIsShownAt") or [it.get("guid", "")])[0]
            out.append(self.cand(
                media_type, page_url=page, title=(it.get("title") or [""])[0],
                description=(it.get("dcDescription") or [""])[0], media_url=media,
                thumb_url=(it.get("edmPreview") or [""])[0], author=(it.get("dcCreator") or [""])[0],
                license_raw=rights, license_url=rights, date=(it.get("year") or [""])[0],
                source_label=f"Europeana / {(it.get('dataProvider') or ['?'])[0]}"[:80],
                query=query, lang=lang, extra={"europeana_id": it.get("id"), "guid": it.get("guid")}))
        return out


# ---------------------------------------------------------------------------
@register
class MetMuseum(Provider):
    name = "met_museum"
    label = "The Metropolitan Museum of Art"
    media_types = ("image",)
    BASE = "https://collectionapi.metmuseum.org/public/collection"

    def search(self, query, media_type, lang="en"):
        if lang != "en":
            return []
        data = None
        for path in ("/v1.1/search", "/v1/search"):  # v1 search was retired 2026-10
            try:
                data = self.http.get_json(self.BASE + path, params={"q": query, "hasImages": "true",
                                                                    "limit": self.limit, "offset": 0})
                break
            except ConnectionError as e:
                log.debug("met %s: %s", path, e)
        ids = (data or {}).get("objectIDs") or []
        out = []
        for oid in ids[: self.limit]:
            try:
                o = self.http.get_json(f"{self.BASE}/v1/objects/{oid}")
            except ConnectionError:
                continue
            if not o.get("isPublicDomain") or not o.get("primaryImage"):
                continue
            out.append(self.cand(
                "image", page_url=o.get("objectURL", ""), title=o.get("title", ""),
                media_url=o["primaryImage"], thumb_url=o.get("primaryImageSmall", ""),
                author=o.get("artistDisplayName", "") or o.get("culture", ""), license_raw="CC0 (Met Open Access)",
                license_url="https://creativecommons.org/publicdomain/zero/1.0/", date=o.get("objectDate", ""),
                description=f"{o.get('objectName', '')} {o.get('medium', '')} {o.get('period', '')} {o.get('dynasty', '')}",
                query=query, lang=lang, extra={"met_id": oid, "object_begin": o.get("objectBeginDate"),
                                               "object_end": o.get("objectEndDate")}))
        return out


# ---------------------------------------------------------------------------
@register
class Smithsonian(Provider):
    name = "smithsonian"
    label = "Smithsonian Open Access"
    media_types = ("image",)
    requires = ("SMITHSONIAN_API_KEY",)

    def search(self, query, media_type, lang="en"):
        params = {"q": f"{query} AND online_media_type:Images", "api_key": env("SMITHSONIAN_API_KEY"),
                  "rows": self.limit}
        data = self.http.get_json("https://api.si.edu/openaccess/api/v1.0/search", params=params)
        out = []
        for r in data.get("response", {}).get("rows", []):
            c = r.get("content", {})
            dn = c.get("descriptiveNonRepeating", {})
            for m in (dn.get("online_media", {}) or {}).get("media", [])[:1]:
                usage = (m.get("usage") or {}).get("access", "")
                if usage != "CC0":
                    continue
                out.append(self.cand(
                    "image", page_url=dn.get("record_link") or dn.get("guid", ""), title=r.get("title", ""),
                    media_url=m.get("content", ""), thumb_url=m.get("thumbnail", ""),
                    license_raw="CC0", license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    source_label=f"Smithsonian / {dn.get('data_source', '')}"[:80], query=query, lang=lang))
        return out


# ---------------------------------------------------------------------------
@register
class Openverse(Provider):
    name = "openverse"
    label = "Openverse"
    media_types = ("image",)
    _token: tuple[str, float] | None = None

    def _auth(self) -> dict:
        cid, sec = env("OPENVERSE_CLIENT_ID"), env("OPENVERSE_CLIENT_SECRET")
        if not (cid and sec):
            return {}
        if not self._token or self._token[1] < time.time():
            r = self.http.request("POST", "https://api.openverse.org/v1/auth_tokens/token/",
                                  data={"grant_type": "client_credentials", "client_id": cid, "client_secret": sec})
            if r.status_code == 200:
                j = r.json()
                Openverse._token = (j["access_token"], time.time() + int(j.get("expires_in", 3600)) - 60)
        return {"Authorization": f"Bearer {self._token[0]}"} if self._token else {}

    def search(self, query, media_type, lang="en"):
        params = {"q": query, "page_size": min(20, self.limit), "license_type": "commercial,modification",
                  "mature": "false"}
        data = self.http.get_json("https://api.openverse.org/v1/images/", params=params, headers=self._auth())
        out = []
        for it in data.get("results", []):
            lic = it.get("license", "")
            ver = it.get("license_version", "")
            raw = "Public Domain" if lic in ("pdm",) else ("CC0" if lic == "cc0" else f"CC {lic.upper()} {ver}")
            out.append(self.cand(
                "image", page_url=it.get("foreign_landing_url", ""), title=it.get("title", ""),
                media_url=it.get("url", ""), thumb_url=it.get("thumbnail", ""), width=it.get("width") or 0,
                height=it.get("height") or 0, author=it.get("creator", ""), license_raw=raw,
                license_url=it.get("license_url", ""), source_label=f"{it.get('source', 'Openverse')}".replace("_", " ").title(),
                query=query, lang=lang, extra={"openverse_id": it.get("id"), "provider": it.get("provider")}))
        return out
