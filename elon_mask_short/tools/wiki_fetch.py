"""Fetch Wikimedia Commons images with license metadata (retry/backoff for rate limits)."""
import json, sys, time, urllib.parse, urllib.request, os, re
UA = "ShortsEditor/1.0 (educational short video; python-urllib)"
API = "https://commons.wikimedia.org/w/api.php"
OUT = sys.argv[1]
def get(url, binary=False):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = r.read()
            return d if binary else json.loads(d)
        except Exception as e:
            time.sleep(4 + i * 6)
    raise RuntimeError("failed " + url)
def api(**p):
    p["format"] = "json"
    return get(API + "?" + urllib.parse.urlencode(p))
# 1) lead images of en.wikipedia pages
pages = ["Tesla_Model_S", "Tesla_Model_3", "Tesla_Fremont_Factory", "Gigafactory_Texas", "Tesla_Roadster_(first_generation)", "SpaceX_Starship", "Zip2"]
r = {"query":{"pages":{}}} if 0 else get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": "|".join(pages), "prop": "pageimages", "piprop": "name", "format": "json"}))
extra = ["File:" + p["pageimage"] for p in r["query"]["pages"].values() if p.get("pageimage")]
print("lead images:", extra)
files = ["File:Elon Musk Royal Society (crop2).jpg", "File:Elon Musk 2015.jpg", "File:Elon Musk Colorado 2022 (cropped2).jpg",
         "File:USAFA Hosts Elon Musk (Image 1 of 17) (cropped).jpg", "File:Elon Musk (12271225556).jpg", "File:Elon Musk 2011 Shankbone.JPG",
         "File:Kimbal Musk (cropped).jpg", "File:KIMBAL MUSK OFFICIAL HEADSHOT (cropped).jpg", "File:PayPal Headquarters.jpg",
         "File:Falcon Heavy Side Boosters landing on LZ1 and LZ2 - 2018 (25254688767).jpg"] + extra
mp=os.path.join(OUT,"wiki_sources.json")
meta = json.load(open(mp)) if os.path.exists(mp) else []
have={m["title"] for m in meta}
for f in files:
    if f in have: continue
    time.sleep(6)
    try: d = api(action="query", titles=f, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1600)
    except Exception: print("api fail", f); continue
    p = list(d["query"]["pages"].values())[0]
    if "imageinfo" not in p: print("missing", f); continue
    ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
    clean = lambda k: re.sub("<[^>]+>", "", em.get(k, {}).get("value", "")).strip()
    lic = clean("LicenseShortName")
    name = re.sub(r"[^A-Za-z0-9]+", "_", f[5:].rsplit(".", 1)[0])[:60] + ".jpg"
    if f.lower().endswith(".svg"): continue
    if os.path.exists(os.path.join(OUT, name)): data=None
    else:
        data=None
        for u in [ii.get("thumburl","").split("?")[0], ii["url"]]:
            if not u: continue
            try: data = get(u, binary=True); break
            except Exception as e: print("dl fail", u)
        if data is None: continue
    if data: open(os.path.join(OUT, name), "wb").write(data)
    m = {"file": name, "title": f, "page": ii["descriptionurl"], "license": lic, "author": clean("Artist")[:200], "credit": clean("Credit")[:200], "size": [ii["width"], ii["height"]]}
    meta.append(m); print(m["file"], m["license"]); json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
json.dump(meta, open(os.path.join(OUT, "wiki_sources.json"), "w"), indent=1, ensure_ascii=False)
