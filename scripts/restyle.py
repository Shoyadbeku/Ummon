"""Restyle a photo into a 3D render look with free Hugging Face Spaces (no token needed)."""
import os
import shutil
import sys
from pathlib import Path

from gradio_client import Client, handle_file

SRC = sys.argv[1] if len(sys.argv) > 1 else "inputs/crosswalk.jpg"
OUT = Path("images")
OUT.mkdir(exist_ok=True)
PROMPT = (
    "Turn this photo into a photorealistic 3D CGI render, Unreal Engine 5 and Blender Cycles style, "
    "semi-glossy CGI skin like a modern video game cinematic, subsurface scattering, slightly stylized 3D materials, "
    "keep the exact same composition, pose, man, curly hair, roller, crosswalk, cones, street and warm sunset lighting, "
    "cinematic depth of field, no text, no watermark"
)
SPACES = [
    ("black-forest-labs/FLUX.1-Kontext-Dev", "/infer",
     lambda img, seed: dict(input_image=img, prompt=PROMPT, seed=seed, randomize_seed=False, guidance_scale=2.5, steps=28)),
    ("Qwen/Qwen-Image-Edit", "/infer",
     lambda img, seed: dict(image=img, prompt=PROMPT, seed=seed, randomize_seed=False, true_guidance_scale=4.0, num_inference_steps=30)),
]
TOKEN = os.environ.get("HF_TOKEN") or None


def first_image(result):
    """Find an image file path in a gradio result (tuple/dict/str)."""
    if isinstance(result, (list, tuple)):
        for r in result:
            p = first_image(r)
            if p:
                return p
    elif isinstance(result, dict):
        for k in ("path", "image", "url"):
            if result.get(k):
                return first_image(result[k])
    elif isinstance(result, str) and Path(result).is_file():
        return result
    return None


ok = 0
for i, seed in enumerate((11, 42, 777), 1):
    for space, api, args in SPACES:
        try:
            client = Client(space, hf_token=TOKEN)
            res = client.predict(**args(handle_file(SRC), seed), api_name=api)
            path = first_image(res)
            if not path:
                raise RuntimeError(f"no image in result: {res!r}")
            dst = OUT / f"crosswalk_3d_{i}{Path(path).suffix or '.png'}"
            shutil.copy(path, dst)
            print(f"[{i}] saved {dst} via {space}")
            ok += 1
            break
        except Exception as e:
            print(f"[{i}] {space} failed: {e}", file=sys.stderr)
            try:
                client.view_api()
            except Exception:
                pass

sys.exit(0 if ok else 1)
