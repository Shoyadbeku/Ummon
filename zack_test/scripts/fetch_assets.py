"""Download every external asset used by the project into zack_test/assets/.
All sources are free, no login: Hugging Face dataset (Mixamo) + Poly Haven (CC0)."""
import json, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
H = {"User-Agent": "blender-asset-fetch/1.0"}  # Poly Haven API rejects urllib's default UA (403)
HF = "https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main"


def op(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H))


def dl(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, "wb").write(op(url).read())
        print("got", os.path.relpath(path, A))


def get(u):
    return json.load(op(u))


dl(f"{HF}/character_refined/Megan.fbx", f"{A}/characters/Megan.fbx")
for a in ["Lifting", "Drinking", "Focus", "Dizzy_Idle"]:
    dl(f"{HF}/animation_motion/{a}.fbx", f"{A}/animations/{a}.fbx")
for m in ["street_rat", "cardboard_box_01", "worn_metal_rack", "wooden_crate_02", "plastic_crate_01"]:
    f = get(f"https://api.polyhaven.com/files/{m}")["gltf"]["2k"]["gltf"]
    dl(f["url"], f"{A}/models/{m}/{m}.gltf")
    for rel, inc in f.get("include", {}).items():
        dl(inc["url"], f"{A}/models/{m}/{rel}")
for h in ["empty_warehouse_01"]:
    f = get(f"https://api.polyhaven.com/files/{h}")["hdri"]["2k"]["hdr"]
    dl(f["url"], f"{A}/hdri/{h}_2k.hdr")
for t in ["brushed_concrete", "anti_slip_concrete", "painted_plaster_wall"]:
    j = get(f"https://api.polyhaven.com/files/{t}")
    for k, name in [("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")]:
        e = j[k]["2k"]; e = e.get("jpg") or e.get("png")
        dl(e["url"], f"{A}/textures/{t}/{t}_{name}_2k." + e["url"].split(".")[-1])
print("assets ready")
