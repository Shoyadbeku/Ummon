import json, base64, sys, os, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from scenes import SCENES, STYLE
NEG = "text, watermark, letters, logo, deformed, extra fingers, blurry, cartoon, gore, blood"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
only = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else range(len(SCENES))
for i in only:
    p = f"{out}/{i:02d}.png"
    if os.path.exists(p): continue
    body = {"prompt": SCENES[i][1] + STYLE, "negative_prompt": NEG, "width": 1024, "height": 576,
            "steps": 2, "cfg_scale": 1.0, "seed": 1000 + i + int(os.environ.get("SEED_OFS", 0)), "sampler_name": "euler_a"}
    t = time.time()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:7860/sdapi/v1/txt2img",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=3600)
    d = json.load(r)
    open(p, "wb").write(base64.b64decode(d["images"][0]))
    print(i, f"{time.time()-t:.0f}s", flush=True)
