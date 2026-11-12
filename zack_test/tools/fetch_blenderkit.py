"""Download free BlenderKit assets as glTF (no login needed for free assets).
usage: python3 fetch_blenderkit.py OUTDIR "search words@assetBaseId-prefix:name" ...
example: python3 fetch_blenderkit.py assets/bk "audi e-tron gt@c3c28d91:audi"
Draco-compressed results must be decoded: npx -y @gltf-transform/cli copy in.glb out.glb"""
import sys, os, json, uuid, urllib.request, urllib.parse
UA = {"User-Agent": "asset-fetch/1.0"}
def jget(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for spec in sys.argv[2:]:
    key, name = spec.rsplit(":", 1)
    words, _, key = key.partition("@")
    q = urllib.parse.quote(words)
    res = jget(f"https://www.blenderkit.com/api/v1/search/?query={q}+asset_type:model+is_free:true&page_size=40")["results"]
    hit = next((r for r in res if key and (r["assetBaseId"].startswith(key) or r["id"].startswith(key))), None) or res[0]
    f = next(f for f in hit["files"] if f["fileType"] == "gltf")
    dl = jget(f["downloadUrl"] + f"?scene_uuid={uuid.uuid4()}")
    url = dl["filePath"]
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".glb"
    dst = os.path.join(out, name + ext)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(dst, "wb") as fo:
        fo.write(r.read())
    print("got", hit["name"], hit["assetBaseId"], "->", dst, os.path.getsize(dst))
