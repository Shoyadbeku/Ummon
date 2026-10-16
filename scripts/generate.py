"""Generate images with Tencent HunyuanImage via Hugging Face Inference Providers."""
import os
import sys
from pathlib import Path

from huggingface_hub import InferenceClient

MODELS = [m.strip() for m in os.environ.get(
    "HF_MODELS", "tencent/HunyuanImage-3.0,tencent/HunyuanImage-2.1").split(",") if m.strip()]
OUT = Path("images")
OUT.mkdir(exist_ok=True)

if not os.environ.get("HF_TOKEN"):
    sys.exit("HF_TOKEN secret is not set: add it in Settings > Secrets and variables > Actions")

prompts = [p.strip() for p in Path("scripts/prompts.txt").read_text().splitlines() if p.strip()]
client = InferenceClient(provider=os.environ.get("HF_PROVIDER", "auto"), api_key=os.environ["HF_TOKEN"])

failed = 0
for i, prompt in enumerate(prompts, 1):
    for model in MODELS:
        try:
            img = client.text_to_image(prompt, model=model, width=768, height=1344)
        except Exception as e:  # try the next model
            print(f"[{i}] {model} failed: {e}", file=sys.stderr)
            continue
        path = OUT / f"glue_{i}.png"
        img.save(path)
        print(f"[{i}] saved {path} with {model}")
        break
    else:
        failed += 1

sys.exit(1 if failed == len(prompts) else 0)
