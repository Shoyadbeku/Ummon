"""Poly Haven (CC0) assetlarini yuklash: modellar (gltf), teksturalar, HDRI.
python get_polyhaven.py OUT_DIR model:Sofa_01 tex:laminate_floor_02 hdri:kloofendal_48d_partly_cloudy_puresky
"""
import json, os, sys, urllib.request
OUT = sys.argv[1]
UA = {"User-Agent": "zack-test-downloader"}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()
def save(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, "wb").write(get(url))
    print("ok", path)
for spec in sys.argv[2:]:
    kind, aid = spec.split(":")
    files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
    if kind == "hdri":
        save(files["hdri"]["2k"]["hdr"]["url"], f"{OUT}/hdri/{aid}.hdr")
    elif kind == "model":
        g = files["gltf"]["1k"]["gltf"]
        d = f"{OUT}/models/{aid}"
        save(g["url"], f"{d}/{aid}.gltf")
        for rel, inc in g.get("include", {}).items():
            save(inc["url"], f"{d}/{rel}")
    elif kind == "tex":
        for m, key in [("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough"), ("Displacement", "disp")]:
            if m in files and "1k" in files[m]:
                fmt = "jpg" if "jpg" in files[m]["1k"] else "png"
                save(files[m]["1k"][fmt]["url"], f"{OUT}/tex/{aid}/{key}.{fmt}")
