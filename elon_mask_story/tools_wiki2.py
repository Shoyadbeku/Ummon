import json, sys, time, urllib.parse, urllib.request, os, re
UA = "ShortsEditor/1.0 (educational documentary video; python-urllib)"
OUT = sys.argv[1]
def get(url, binary=False, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                d = r.read()
            return d if binary else json.loads(d)
        except Exception:
            time.sleep(5 + i * 8)
    raise RuntimeError(url)
pages = ["Stanford_University", "Hoover_Tower", "Stanford_Memorial_Church", "Compaq", "EBay", "Falcon_1", "Tesla_Roadster_(first_generation)",
         "Martin_Eberhard", "Marc_Tarpenning", "Tesla_Model_3", "Tesla_Model_S", "Omelek_Island", "Kimbal_Musk", "Zip2", "X.com_(bank)",
         "PayPal", "SpaceX_Dragon", "Falcon_9", "Tesla_Fremont_Factory", "Silicon_Valley", "Palo_Alto,_California", "Mosaic_(web_browser)", "Dial-up_Internet_access", "Netscape_Navigator", "IBM_Personal_Computer", "SpaceX_Merlin"]
r = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": "|".join(pages), "prop": "pageimages", "piprop": "name", "format": "json", "redirects": 1}))
files = sorted({"File:" + p["pageimage"] for p in r["query"]["pages"].values() if p.get("pageimage")})
files += ["File:Falcon 1 Flight 4 liftoff.jpg", "File:Elon Musk 2004.jpg" ]
print(len(files), "candidates")
mp = os.path.join(OUT, "wiki_sources.json"); meta = json.load(open(mp)) if os.path.exists(mp) else []
have = {m["title"] for m in meta}
for f in files:
    if f in have: continue
    time.sleep(4)
    try:
        d = get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": f, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1800, "format": "json"}))
        p = list(d["query"]["pages"].values())[0]
        if "imageinfo" not in p:  # not on commons -> local enwiki (usually non-free)
            print("SKIP (not on Commons, likely non-free):", f); continue
        ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
        cl = lambda k: re.sub("<[^>]+>", "", em.get(k, {}).get("value", "")).strip()
        lic = cl("LicenseShortName")
        if f.lower().endswith(".svg") or not re.search(r"CC|Public domain|PD|CC0", lic, re.I) or "non-free" in lic.lower():
            print("SKIP", f, lic); continue
        name = re.sub(r"[^A-Za-z0-9]+", "_", f[5:].rsplit(".", 1)[0])[:60] + ".jpg"
        data = None
        for u in [ii.get("thumburl", "").split("?")[0], ii["url"]]:
            if not u: continue
            try: data = get(u, binary=True, tries=4); break
            except Exception: pass
        if not data: print("DLFAIL", f); continue
        open(os.path.join(OUT, name), "wb").write(data)
        meta.append({"file": name, "title": f, "page": ii["descriptionurl"], "license": lic, "author": cl("Artist")[:150], "size": [ii["width"], ii["height"]]})
        json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
        print("OK", name, "|", lic, "|", cl("Artist")[:50], flush=True)
    except Exception as e:
        print("ERR", f, e)
