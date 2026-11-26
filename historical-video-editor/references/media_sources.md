# Media sources — what each provider gives and how the skill uses it

Status columns: **API** = official API used in code; **Key** = needs `.env` key;
**DL** = automatic download allowed (licence permitting); **Tested** = live-tested from the
build environment on 2026-11-26.

| Provider (config name) | Media | API | Key | DL | Licence info | Tested |
|---|---|---|---|---|---|---|
| Internet Archive (`internet_archive`) | film, newsreels, photos | advancedsearch + metadata | – | yes | `licenseurl`, curated PD collections (Prelinger, FedFlix, NASA, Universal Newsreels) | ✅ |
| Wikimedia Commons (`wikimedia_commons`) | video (webm/ogv), photos, maps, art | MediaWiki API | – (contact in UA recommended) | yes | per-file `extmetadata` LicenseShortName/Url/Artist | ✅ (rate-limited at times: 429) |
| Library of Congress (`library_of_congress`) | films, photos, maps | loc.gov JSON API | – | yes | `rights_advisory` | ⚠️ slow/timeouts from cloud IPs |
| Europeana (`europeana`) | European archives (film, photo) | Search API v2 | EUROPEANA_API_KEY | yes | `rights` (rightsstatements/CC) `reusability=open` | not tested (no key) |
| The Met (`met_museum`) | art, manuscripts, miniatures | Collection API v1.1 search + v1 objects | – | yes | `isPublicDomain` → CC0 | ✅ |
| Smithsonian (`smithsonian`) | museum objects, photos | Open Access API | SMITHSONIAN_API_KEY | yes | `usage.access == CC0` | not tested (no key) |
| Openverse (`openverse`) | CC images from Flickr, museums… | Openverse API | optional client id | yes | license + version + landing page | ✅ (anonymous quota can throttle) |
| Pexels (`pexels`) | modern stock video/photo | Pexels API | PEXELS_API_KEY | yes | Pexels License | not tested (no key) |
| Pixabay (`pixabay`) | modern stock video/photo | Pixabay API | PIXABAY_API_KEY | yes | Pixabay Content License | not tested (no key) |
| YouTube CC (`youtube_cc`) | Creative Commons videos | YouTube Data API v3 | YOUTUBE_API_KEY | yes (CC BY only, yt-dlp) | `videoLicense=creativeCommon` | not tested (no key) |
| YouTube discovery (`ytdlp_discovery`) | any YouTube video | yt-dlp search | – | **no** unless metadata says CC | `license` field read in verify step | ✅ (403 throttling under heavy use) |
| Rutube (`rutube`) | RU video | public search JSON | – | **no** (discovery) | none exposed → unknown | ❌ blocked (HTTP 403) from build env |
| VK Video (`vk_video`) | RU/UZ video | VK API `video.search` | VK_ACCESS_TOKEN (user token) | **no** (discovery) | none → unknown | not tested (no token) |
| Reddit (`reddit`) | posts linking video/photo | OAuth API | REDDIT_CLIENT_ID/SECRET | **no** (discovery) | none → unknown | not tested (no key) |
| Yandex Images (`yandex_images`) | image discovery (primary) | Yandex Cloud Search API v2 `image/search` | YANDEX_SEARCH_API_KEY + YANDEX_FOLDER_ID | only after original page proves licence | original `pageUrl` analysed | not tested (no key); manual links always generated |
| Google Images (`google_images`) | image discovery | Programmable Search JSON API (`searchType=image`, CC rights filter) | GOOGLE_API_KEY + GOOGLE_CSE_ID | only after original page proves licence | `image.contextLink` | not tested (no key)¹ |
| X / Facebook / Mover.uz / Mixkit / Telegram / museums without API (`manual_urls`) | anything | – (no usable public search API) | – | yes if `license=` given in `manual_urls.txt` | user-supplied, kept in report | manual workflow |

¹ Google has announced restrictions on the Programmable Search / Custom Search JSON API (closed to
new customers, whole-web search being phased out). Verify the current status in the Google Cloud
console before relying on it; Yandex, Commons and Openverse cover the same need.

## Search strategy

1. Every scene produces queries in **en / ru / uz** (`search_languages`), plus map queries.
   English archive vocabulary finds most archive film; Russian finds Soviet newsreels
   (кинохроника, Госфильмофонд); Uzbek finds local uploads (Mover.uz, YouTube).
2. Identical queries across scenes run once; results cached in `output/<slug>/cache/search/` (7 days).
3. Scoring = relevance (query + scene entities in title/description) + licence safety +
   resolution + archival bonus + curated-collection bonus + period match − anachronism − AI flags.
4. Verification adds link health, real licence from the platform, resolved file URLs.

## Good archive collections to target with queries

- Internet Archive: `prelinger`, `universal_newsreels`, `fedflix`, `gov.archives.arc.*` (NARA), `nasa`.
- Wikimedia Commons categories: "Zafarnama", "Timurid art", "Russian Turkestan", "Prokudin-Gorsky",
  "Turkestan Album", "Soviet Uzbekistan in the 1920s", "Samarkand in the 19th century".
- Library of Congress: Prokudin-Gorsky collection (colour photos of Central Asia 1905-1915, no known restrictions),
  "Turkestanskii al'bom" (1871-72), Carl Mannerheim photos via Finnish archives (Europeana).
- The Met: Timurid/Safavid miniatures (Shahnama, Zafarnama folios, CC0).
- Europeana: Bundesarchiv, Nederlands Instituut voor Beeld en Geluid (Open Beelden, CC BY-SA newsreels).
- Net-Film / Госфильмофонд (RU): footage is mostly **not** open — discovery only, licence needed.

## Adding a new provider

Create a class in `scripts/providers/*.py`:

```python
@register
class MyArchive(Provider):
    name = "my_archive"; label = "My Archive"; media_types = ("video", "image"); requires = ("MY_KEY",)
    def search(self, query, media_type, lang="en"):
        data = self.http.get_json("https://api.example.org/search", params={"q": query})
        return [self.cand(media_type, page_url=..., media_url=..., title=..., author=..., license_raw=...)]
```

Add `my_archive` to `search.video_providers` / `image_providers` in `config.yaml`.
