"""Animate fox_funeral.jpg into a 10 s silent talking video via the free Wan 2.2 I2V Space."""
import os, shutil, subprocess, sys, time
from gradio_client import Client, handle_file

SPACE = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
NEG = ("subtitles, text, captions, watermark, camera movement, zoom, scene change, "
       "deformed face, extra limbs, blurry, frozen static image, characters walking away, style change")
PROMPTS = [
    "Static camera, 2D cartoon animation. The tall grey fox in the black tuxedo and round glasses "
    "looks down at the little fox and talks to him calmly, his mouth clearly opening and closing as he "
    "speaks, gentle smile, small head nods, ears twitch. The little fox looks up and listens, blinking. "
    "Candle flames flicker, smoke drifts slowly, mourners in the background sob quietly.",
    "Static camera, 2D cartoon animation. The little fox in the sweater vest looks up and talks to the "
    "tall grey fox, his mouth clearly opening and closing as he speaks, eyebrows moving sadly. The tall "
    "fox listens, nods slowly and answers with a few words, mouth moving. Candle flames flicker, smoke "
    "drifts, mourners in the background sob quietly.",
]

token = os.environ.get("HF_TOKEN") or None
client = Client(SPACE, token=token)
os.makedirs("out", exist_ok=True)

def gen(img, prompt, idx):
    for attempt in range(4):
        try:
            res = client.predict(
                input_image=handle_file(img), prompt=prompt, steps=6, negative_prompt=NEG,
                duration_seconds=5, guidance_scale=1, guidance_scale_2=1,
                seed=42 + idx, randomize_seed=False, api_name="/generate_video")
            vid = res[0]["video"] if isinstance(res[0], dict) else res[0]
            dst = f"out/clip{idx}.mp4"
            shutil.copy(vid, dst)
            return dst
        except Exception as e:
            print(f"clip{idx} attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(30 * (attempt + 1))
    sys.exit(f"clip{idx} failed")

c1 = gen("fox_funeral.jpg", PROMPTS[0], 1)
subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", c1, "-frames:v", "1", "out/last.png"], check=True)
c2 = gen("out/last.png", PROMPTS[1], 2)

# Join, drop audio, force exactly 10 s at 24 fps.
subprocess.run(["ffmpeg", "-y", "-i", c1, "-i", c2, "-filter_complex",
                "[0:v]fps=24,setpts=PTS-STARTPTS[a];[1:v]fps=24,setpts=PTS-STARTPTS[b];"
                "[a][b]concat=n=2:v=1[c];[c]tpad=stop_mode=clone:stop_duration=10,trim=duration=10[v]",
                "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-movflags", "+faststart", "fox_talking_10s.mp4"], check=True)
