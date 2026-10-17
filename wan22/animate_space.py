"""GPU bo'lmasa: Hugging Face Space'dagi Wan 2.2 14B I2V (diffusers, Lightning LoRA) orqali jonlantirish.

    pip install gradio_client
    HF_TOKEN=hf_xxx python wan22/animate_space.py

ZeroGPU kunlik limiti bor; HF_TOKEN (PRO bo'lsa yaxshi) limitni oshiradi.
"""
import os
import shutil
from pathlib import Path

from gradio_client import Client, handle_file

from concat import FRAMES_DIR, OUT_DIR, ROOT, concat
from prompts import FRAMES, NEGATIVE, STYLE

SPACE = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = Client(SPACE, hf_token=os.environ.get("HF_TOKEN"))
    clips = []
    for name, motion in FRAMES:
        out = OUT_DIR / f"{Path(name).stem}.mp4"
        clips.append(out)
        if out.exists():
            print(f"skip {out.name}")
            continue
        video, seed = client.predict(
            input_image=handle_file(str(FRAMES_DIR / name)),
            prompt=f"{motion} {STYLE}",
            negative_prompt=NEGATIVE,
            duration_seconds=4,
            steps=6,
            seed=42,
            randomize_seed=False,
            api_name="/generate_video",
        )
        path = video["video"] if isinstance(video, dict) else video
        shutil.copy(path, out)
        print(f"done {out.name} (seed {seed})")
    concat(clips, ROOT / "fox_sheep_story_wan22.mp4")


if __name__ == "__main__":
    main()
