"""Generate images: Tencent HunyuanImage via HF Inference when HF_TOKEN is set,
otherwise the free, keyless Pollinations API."""
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

W, H = 768, 1344
OUT = Path("images")
OUT.mkdir(exist_ok=True)
prompts = [p.strip() for p in Path("scripts/prompts.txt").read_text().splitlines() if p.strip()]


def hunyuan(prompt, path):
    from huggingface_hub import InferenceClient
    client = InferenceClient(provider="auto", api_key=os.environ["HF_TOKEN"])
    for model in ("tencent/HunyuanImage-3.0", "tencent/HunyuanImage-2.1"):
        try:
            client.text_to_image(prompt, model=model, width=W, height=H).save(path)
            return model
        except Exception as e:
            print(f"{model} failed: {e}", file=sys.stderr)
    return None


def pollinations(prompt, path, seed):
    query = urllib.parse.urlencode({"width": W, "height": H, "model": "flux", "nologo": "true", "seed": seed})
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?{query}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if data[:3] == b"\xff\xd8\xff" or data[:4] == b"\x89PNG":
                path.write_bytes(data)
                return "pollinations/flux"
            print(f"unexpected response: {data[:200]!r}", file=sys.stderr)
        except Exception as e:
            print(f"pollinations attempt {attempt + 1} failed: {e}", file=sys.stderr)
        time.sleep(10 * (attempt + 1))
    return None


ok = 0
for i, prompt in enumerate(prompts, 1):
    path = OUT / f"glue_{i}.jpg"
    used = hunyuan(prompt, path.with_suffix(".png")) if os.environ.get("HF_TOKEN") else None
    if not used:
        used = pollinations(prompt, path, seed=1000 + i)
    print(f"[{i}] {'saved with ' + used if used else 'FAILED'}")
    ok += bool(used)

sys.exit(0 if ok else 1)
