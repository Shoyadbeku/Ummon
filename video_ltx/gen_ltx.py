"""Generate scene clips with Lightricks LTX-Video 2B distilled on CPU.

Usage: python gen_ltx.py scenes.json outdir [--only id,id] [--frames 97] [--w 768 --h 448]
Two phases so it fits in 15 GB RAM: (1) T5 encodes all prompts, then is freed;
(2) the transformer + VAE generate each clip from the cached embeddings.
"""
import argparse, gc, json, os, time
import torch

MODEL = os.environ.get("LTX_MODEL_DIR", "/home/user/models/ltxv")  # snapshot of Lightricks/LTX-Video
NEG = ("worst quality, inconsistent motion, blurry, jittery, distorted, deformed hands, "
       "deformed face, text, watermark, subtitles, logo, low resolution, cartoon")

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("out")
ap.add_argument("--only", default="")
ap.add_argument("--frames", type=int, default=97)
ap.add_argument("--w", type=int, default=768); ap.add_argument("--h", type=int, default=448)
ap.add_argument("--steps", type=int, default=8)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
torch.set_num_threads(os.cpu_count())

scenes = json.load(open(a.scenes))
if a.only:
    keep = set(a.only.split(","))
    scenes = [s for s in scenes if s["id"] in keep]
scenes = [s for s in scenes if not os.path.exists(f"{a.out}/{s['id']}.mp4")]
print(f"{len(scenes)} clips to render", flush=True)
if not scenes:
    raise SystemExit

# ---- phase 1: text embeddings
emb_path = f"{a.out}/_emb.pt"
cache = torch.load(emb_path) if os.path.exists(emb_path) else {}
todo = [s for s in scenes if s["prompt"] not in cache] + ([] if NEG in cache else [{"prompt": NEG}])
if todo:
    from transformers import T5EncoderModel, T5Tokenizer
    tok = T5Tokenizer.from_pretrained(MODEL, subfolder="tokenizer")
    te = T5EncoderModel.from_pretrained(MODEL, subfolder="text_encoder", torch_dtype=torch.bfloat16).eval()
    for s in todo:
        t = tok(s["prompt"], padding="max_length", max_length=128, truncation=True, return_tensors="pt")
        with torch.no_grad():
            e = te(t.input_ids, attention_mask=t.attention_mask)[0]
        cache[s["prompt"]] = (e.float(), t.attention_mask)
    torch.save(cache, emb_path)
    del te; gc.collect()
    print("embeddings ready", flush=True)

# ---- phase 2: video
from diffusers import LTXConditionPipeline, LTXVideoTransformer3DModel, AutoencoderKLLTXVideo
from diffusers.utils import export_to_video
ckpt = f"{MODEL}/ltxv-2b-0.9.8-distilled.safetensors"
tr = LTXVideoTransformer3DModel.from_single_file(ckpt, torch_dtype=torch.bfloat16)
vae = AutoencoderKLLTXVideo.from_single_file(ckpt, torch_dtype=torch.bfloat16)
pipe = LTXConditionPipeline.from_pretrained(MODEL, transformer=tr, vae=vae, text_encoder=None,
                                            tokenizer=None, torch_dtype=torch.bfloat16)
pipe.vae.enable_tiling()
from diffusers import FlowMatchEulerDiscreteScheduler
pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config, use_dynamic_shifting=False)
neg_e, neg_m = cache[NEG]
for s in scenes:
    t0 = time.time()
    e, m = cache[s["prompt"]]
    g = torch.Generator().manual_seed(s.get("seed", 7))
    with torch.no_grad():
        frames = pipe(prompt_embeds=e.bfloat16(), prompt_attention_mask=m,
                      negative_prompt_embeds=neg_e.bfloat16(), negative_prompt_attention_mask=neg_m,
                      width=a.w, height=a.h, num_frames=s.get("frames", a.frames), timesteps=[1000, 993, 987, 981, 975, 909, 725, 0.03],
                      guidance_scale=1.0, decode_timestep=0.05, decode_noise_scale=0.025,
                      image_cond_noise_scale=0.0, generator=g, output_type="pil").frames[0]
    export_to_video(frames, f"{a.out}/{s['id']}.mp4", fps=24)
    print(f"done {s['id']} in {time.time()-t0:.0f}s", flush=True)
