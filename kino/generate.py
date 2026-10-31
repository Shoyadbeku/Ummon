"""Wan 2.2 TI2V-5B bilan har bir rasmni videoga aylantiradi (bepul Colab T4 GPU uchun).

Ishlatish: python generate.py --out CLIPS_DIR [--hd] [--steps 30] [--only 1,4]
Tayyor kliplar qayta yaratilmaydi, shuning uchun uzilib qolsa davom ettirish mumkin.
"""
import argparse, gc, html, json, os, re, time
import torch
from PIL import Image

MID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
HERE = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(HERE, "clips"))
ap.add_argument("--hd", action="store_true", help="704x1280 (sekinroq, 2-3 barobar)")
ap.add_argument("--steps", type=int, default=30)
ap.add_argument("--guidance", type=float, default=5.0)
ap.add_argument("--frames", type=int, default=121)  # 24 fps da ~5 s
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--only", default="")
a = ap.parse_args()

cfg = json.load(open(os.path.join(HERE, "scenes.json")))
scenes = cfg["scenes"]
if a.only:
    keep = {int(x) for x in a.only.split(",")}
    scenes = [s for s in scenes if s["id"] in keep]
os.makedirs(a.out, exist_ok=True)
todo = [s for s in scenes if not os.path.exists(os.path.join(a.out, f"clip{s['id']}.mp4"))]
if not todo:
    print("Hamma kliplar tayyor."); raise SystemExit
H, W = (1280, 704) if a.hd else (864, 480)
dev = "cuda"
DT = torch.float16  # T4 da bf16 juda sekin
print(f"GPU: {torch.cuda.get_device_name(0)} | {len(todo)} ta klip | {W}x{H} | {a.frames} kadr | {a.steps} qadam")

# ---------- 1) Matnlarni kodlash (UMT5), keyin xotiradan chiqarish ----------
from transformers import AutoTokenizer, UMT5EncoderModel

def clean(t):
    try:
        import ftfy; t = ftfy.fix_text(t)
    except ImportError:
        pass
    return re.sub(r"\s+", " ", html.unescape(html.unescape(t))).strip()

tok = AutoTokenizer.from_pretrained(MID, subfolder="tokenizer")
te = UMT5EncoderModel.from_pretrained(MID, subfolder="text_encoder", torch_dtype=torch.bfloat16, device_map=dev).eval()

@torch.no_grad()
def enc(text, L=512):
    t = tok([clean(text)], padding="max_length", max_length=L, truncation=True,
            add_special_tokens=True, return_attention_mask=True, return_tensors="pt")
    n = int(t.attention_mask.sum())
    e = te(t.input_ids.to(dev), t.attention_mask.to(dev)).last_hidden_state[0, :n].float()
    out = torch.zeros(1, L, e.shape[-1]); out[0, :n] = e.cpu()
    return out

neg = enc(cfg["negative_prompt"])
embeds = {s["id"]: enc(s["prompt"]) for s in todo}
del te; gc.collect(); torch.cuda.empty_cache()

# ---------- 2) Video modeli ----------
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline, WanTransformer3DModel
from diffusers.utils import export_to_video

tr = WanTransformer3DModel.from_pretrained(MID, subfolder="transformer", torch_dtype=DT, device_map=dev)
vae = AutoencoderKLWan.from_pretrained(MID, subfolder="vae", torch_dtype=torch.float32)
pipe = WanImageToVideoPipeline.from_pretrained(MID, transformer=tr, vae=vae, text_encoder=None, torch_dtype=DT)
pipe.to(dev)
try:
    pipe.vae.enable_tiling()
except Exception:
    pass
pipe.set_progress_bar_config(leave=False)

def fit(img, w, h):  # markazdan kesib, kerakli o'lchamga keltirish
    r = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    l, t = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))

for s in todo:
    t0 = time.time()
    img = fit(Image.open(os.path.join(HERE, s["image"])).convert("RGB"), W, H)
    frames = pipe(image=img, prompt_embeds=embeds[s["id"]].to(dev, DT), negative_prompt_embeds=neg.to(dev, DT),
                  height=H, width=W, num_frames=a.frames, num_inference_steps=a.steps,
                  guidance_scale=a.guidance, generator=torch.Generator(dev).manual_seed(a.seed + s["id"])).frames[0]
    p = os.path.join(a.out, f"clip{s['id']}.mp4")
    export_to_video(frames, p + ".tmp.mp4", fps=cfg["fps"]); os.replace(p + ".tmp.mp4", p)
    print(f"✅ {s['id']}-sahna tayyor ({time.time() - t0:.0f} s)", flush=True)
    torch.cuda.empty_cache()
print("Hamma kliplar tayyor.")
