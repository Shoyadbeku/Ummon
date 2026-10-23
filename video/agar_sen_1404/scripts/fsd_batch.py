# Batch txt2img driver on top of FastSD CPU's backend (keeps model loaded between prompts).
import json, os, sys, time
sys.path.insert(0, "/opt/work/fastsdcpu/src")
os.chdir("/opt/work/fastsdcpu")
import transformers
if not hasattr(transformers, "CLIPFeatureExtractor"): transformers.CLIPFeatureExtractor = transformers.CLIPImageProcessor
from backend.models.lcmdiffusion_setting import DiffusionTask
from models.interface_types import InterfaceType
from state import get_context, get_settings

jobs = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
model = sys.argv[3] if len(sys.argv) > 3 else "rupeshs/LCM-dreamshaper-v7-openvino"
ctx = get_context(InterfaceType.CLI); cfg = get_settings().settings; s = cfg.lcm_diffusion_setting
s.use_openvino = True; s.openvino_lcm_model_id = model
s.diffusion_task = DiffusionTask.text_to_image.value; s.lora.enabled = False; s.controlnet = None
s.image_width, s.image_height = int(os.environ.get("W", 768)), int(os.environ.get("H", 448))
s.inference_steps = int(os.environ.get("STEPS", 4)); s.guidance_scale = 1.0; s.number_of_images = 1
s.use_seed = True; s.use_safety_checker = False; s.use_tiny_auto_encoder = False
STYLE = os.environ.get("STYLE", ", cinematic film still, dramatic lighting, rich colors, highly detailed, 8k, masterpiece")
NEG = "text, watermark, logo, letters, blurry, deformed, ugly, extra fingers, bad anatomy, lowres, cartoon"
for j in jobs:
    out = os.path.join(outdir, j["id"] + ".png")
    if os.path.exists(out): continue
    s.prompt = j["prompt"] + STYLE; s.negative_prompt = NEG; s.seed = j.get("seed", 1234)
    t = time.time(); ctx.lcm_text_to_image.init("cpu", s)
    img = ctx.lcm_text_to_image.generate(s)[0]; img.save(out)
    print(f"{j['id']} {time.time()-t:.1f}s", flush=True)
