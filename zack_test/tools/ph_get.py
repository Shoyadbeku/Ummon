# Poly Haven (CC0) yuklovchi: modellar (gltf+fayllar), teksturalar (diffuse/normal/rough), HDRI
import json, subprocess, sys, os
OUT = "/tmp/claude-0/assets/ph"
def curl(url, path=None):
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(["curl", "-sSL", "-o", path, url], check=True)
    else:
        return subprocess.run(["curl", "-sSL", url], check=True, capture_output=True).stdout
for aid in sys.argv[1:]:
    d = json.loads(curl(f"https://api.polyhaven.com/files/{aid}"))
    typ = json.loads(curl(f"https://api.polyhaven.com/info/{aid}"))["type"]   # 0=hdri 1=tekstura 2=model
    if "hdri" in d:
        curl(d["hdri"]["2k"]["hdr"]["url"], f"{OUT}/{aid}.hdr")
    elif typ == 1:
        for k, name in (("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")):
            if k in d: curl(d[k]["2k"]["jpg"]["url"], f"{OUT}/{aid}/{name}.jpg")
    else:
        g = d["gltf"]["1k"]["gltf"]
        curl(g["url"], f"{OUT}/{aid}/{aid}.gltf")
        for rel, inc in g.get("include", {}).items():
            curl(inc["url"], f"{OUT}/{aid}/{rel}")
    print("ok", aid)
