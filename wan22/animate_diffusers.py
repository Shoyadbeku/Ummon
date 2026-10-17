"""Wan 2.2 (diffusers) bilan frames/*.jpg rasmlarini jonlantirish va bitta videoga yig'ish.

GPU kerak (NVIDIA, kamida ~24 GB VRAM; 5B model + CPU offload bilan 16 GB ham ishlaydi, sekinroq).
O'rnatish:
    pip install -U diffusers transformers accelerate ftfy imageio imageio-ffmpeg sentencepiece
Ishga tushirish (repo ildizidan):
    python wan22/animate_diffusers.py                # Wan2.2-TI2V-5B (tezroq, kam xotira)
    python wan22/animate_diffusers.py --model a14b   # Wan2.2-I2V-A14B (sifatliroq, ~80 GB VRAM yoki offload)
"""
import argparse
from pathlib import Path

import torch
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline, WanPipeline
from diffusers.utils import export_to_video, load_image

from concat import FPS, FRAMES_DIR, OUT_DIR, ROOT, concat
from prompts import FRAMES, NEGATIVE, STYLE

# 9:16 vertikal; ikkala o'lcham 32 ga karrali
WIDTH, HEIGHT = 704, 1280


def load_pipe(model: str):
    if model == "a14b":
        repo = "Wan-AI/Wan2.2-I2V-A14B-Diffusers"
        vae = AutoencoderKLWan.from_pretrained(repo, subfolder="vae", torch_dtype=torch.float32)
        pipe = WanImageToVideoPipeline.from_pretrained(repo, vae=vae, torch_dtype=torch.bfloat16)
    else:
        repo = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
        vae = AutoencoderKLWan.from_pretrained(repo, subfolder="vae", torch_dtype=torch.float32)
        pipe = WanPipeline.from_pretrained(repo, vae=vae, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    return pipe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["5b", "a14b"], default="5b")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pipe = load_pipe(args.model)
    # Wan 4k+1 kadr talab qiladi
    num_frames = int(args.seconds * FPS) // 4 * 4 + 1

    clips = []
    for name, motion in FRAMES:
        out = OUT_DIR / f"{Path(name).stem}.mp4"
        clips.append(out)
        if out.exists():
            print(f"skip {out.name}")
            continue
        image = load_image(str(FRAMES_DIR / name)).resize((WIDTH, HEIGHT))
        frames = pipe(
            image=image,
            prompt=f"{motion} {STYLE}",
            negative_prompt=NEGATIVE,
            height=HEIGHT,
            width=WIDTH,
            num_frames=num_frames,
            num_inference_steps=args.steps,
            guidance_scale=5.0,
            generator=torch.Generator("cpu").manual_seed(args.seed),
        ).frames[0]
        export_to_video(frames, str(out), fps=FPS)
        print(f"done {out.name}")

    concat(clips, ROOT / "fox_sheep_story_wan22.mp4")


if __name__ == "__main__":
    main()
