"""Download CC0 assets from Poly Haven (no login).
usage: python3 fetch_polyhaven.py OUTDIR model:Sofa_01 tex:laminate_floor_02 hdri:kloofendal_48d_partly_cloudy_puresky [--res 1k]"""
import sys, os, json, urllib.request
args = [a for a in sys.argv[1:]]
res = "1k"
if "--res" in args:
    i = args.index("--res"); res = args[i + 1]; del args[i:i + 2]
out = args[0]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "asset-fetch/1.0"}
def get(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0: return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(dst, "wb") as f:
        f.write(r.read())
    print("got", dst)
for item in args[1:]:
    kind, name = item.split(":", 1)
    files = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{name}", headers=UA)))
    d = os.path.join(out, name)
    if kind == "hdri":
        get(files["hdri"][res]["hdr"]["url"], os.path.join(d, f"{name}_{res}.hdr"))
    elif kind == "model":
        g = files["gltf"][res]["gltf"]
        get(g["url"], os.path.join(d, os.path.basename(g["url"])))
        for rel, inc in g.get("include", {}).items():
            get(inc["url"], os.path.join(d, rel))
    elif kind == "tex":
        for m in ("Diffuse", "nor_gl", "Rough", "Displacement", "AO"):
            if m in files and res in files[m]:
                fmt = "jpg" if "jpg" in files[m][res] else "png"
                get(files[m][res][fmt]["url"], os.path.join(d, f"{m}.{fmt}"))
