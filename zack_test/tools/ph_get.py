#!/usr/bin/env python3
# Poly Haven (CC0) yuklovchi: python3 -I ph_get.py <id> [<id> ...]  [PH_DIR=/tmp/claude-0/assets/ph/]
# HDRI -> PH/<id>.hdr ; tekstura -> PH/<id>/{diff,rough,nor}.jpg ; model -> PH/<id>/<id>.gltf (+bin, tekstura)
import json, os, sys, urllib.request
PH = os.environ.get("PH_DIR", "/tmp/claude-0/assets/ph/"); RES = os.environ.get("PH_RES", "1k")
UA = {"User-Agent": "ummon-zack/1.0"}          # UA'siz so'rovga API 403 qaytaradi
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()
def save(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path): open(path, "wb").write(get(url))
for aid in sys.argv[1:]:
    t = json.loads(get(f"https://api.polyhaven.com/info/{aid}"))["type"]   # 0 hdri, 1 tekstura, 2 model
    f = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
    if t == 0:
        save(f["hdri"][RES]["hdr"]["url"], f"{PH}{aid}.hdr")
    elif t == 1:
        for k, fn in (("Diffuse", "diff"), ("Rough", "rough"), ("nor_gl", "nor")):
            if k in f: save(f[k][RES]["jpg"]["url"], f"{PH}{aid}/{fn}.jpg")
    else:
        g = f["gltf"][RES]["gltf"]; save(g["url"], f"{PH}{aid}/{aid}.gltf")
        for p, inc in g.get("include", {}).items(): save(inc["url"], f"{PH}{aid}/{p}")
    print("ok", aid, ["hdri", "texture", "model"][t])
