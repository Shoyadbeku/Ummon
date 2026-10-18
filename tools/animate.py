"""Animate an image into a 10 s silent talking video via the free Wan 2.2 I2V Space.

Usage: python tools/animate.py IMAGE PROMPTS_KEY OUTPUT
"""
import json, os, shutil, subprocess, sys, time
from gradio_client import Client, handle_file

SPACE = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
NEG = ("subtitles, text, captions, watermark, camera movement, zoom, scene change, "
       "deformed face, extra limbs, blurry, frozen static image, characters walking away, style change")

img, key, out = sys.argv[1:4]
prompts = json.load(open("tools/prompts.json"))[key]
client = Client(SPACE, token=os.environ.get("HF_TOKEN") or None)
work = f"work_{key}"
os.makedirs(work, exist_ok=True)

def gen(src, prompt, idx):
    for attempt in range(5):
        try:
            res = client.predict(
                input_image=handle_file(src), prompt=prompt, steps=6, negative_prompt=NEG,
                duration_seconds=5, guidance_scale=1, guidance_scale_2=1,
                seed=42 + idx, randomize_seed=False, api_name="/generate_video")
            vid = res[0]["video"] if isinstance(res[0], dict) else res[0]
            dst = f"{work}/clip{idx}.mp4"
            shutil.copy(vid, dst)
            return dst
        except Exception as e:
            print(f"{key} clip{idx} attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(60 * (attempt + 1))
    sys.exit(f"{key} clip{idx} failed")

c1 = gen(img, prompts[0], 1)
subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", c1, "-frames:v", "1", f"{work}/last.png"], check=True)
c2 = gen(f"{work}/last.png", prompts[1], 2)

# Join, drop audio, force exactly 10 s at 24 fps.
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-i", c1, "-i", c2, "-filter_complex",
                "[0:v]fps=24,setpts=PTS-STARTPTS[a];[1:v]fps=24,setpts=PTS-STARTPTS[b];"
                "[a][b]concat=n=2:v=1[c];[c]tpad=stop_mode=clone:stop_duration=10,trim=duration=10[v]",
                "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-movflags", "+faststart", out], check=True)
