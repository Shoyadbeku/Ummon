"""Automatic QC of output/final_video.mp4 and the frame sequence."""
import os, json, subprocess, glob, re
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "output", "final_video.mp4")
rep = {}
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", V],
                               capture_output=True, text=True, check=True).stdout)
vs = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
as_ = [s for s in pr["streams"] if s["codec_type"] == "audio"]
rep["video"] = dict(codec=vs["codec_name"], w=vs["width"], h=vs["height"], fps=vs["r_frame_rate"],
                    pix_fmt=vs["pix_fmt"], frames=int(vs.get("nb_frames", 0)))
rep["audio"] = [dict(codec=a["codec_name"], sr=a["sample_rate"], ch=a["channels"]) for a in as_]
rep["duration"] = float(pr["format"]["duration"])
# decode integrity
dec = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-f", "null", "-"], capture_output=True, text=True)
rep["decode_errors"] = dec.stderr.strip()[:500] or "none"
# black frames
bd = subprocess.run(["ffmpeg", "-hide_banner", "-i", V, "-vf", "blackdetect=d=0.04:pix_th=0.06", "-an", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
rep["black_segments"] = re.findall(r"black_start:\S+ black_end:\S+", bd)
# loudness / clipping
ld = subprocess.run(["ffmpeg", "-hide_banner", "-i", V, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
summ = ld[ld.rfind("Summary:"):]
m = re.search(r"I:\s+(-?[\d.]+) LUFS", summ); p = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ)
rep["loudness_LUFS"] = float(m.group(1)) if m else None
rep["true_peak_dBFS"] = float(p.group(1)) if p else None
# frame sequence: count, near-black, flicker (luma jump inside a shot)
fs = sorted(glob.glob(os.path.join(ROOT, "renders", "final", "frame_*.png")))
rep["png_frames"] = len(fs)
cuts = {1, 46, 71, 97, 152, 224, 370, 471, 541, 601, 670, 781, 906, 991}
lum, dark, jumps = [], [], []
for f in fs:
    n = int(os.path.basename(f)[6:12])
    a = np.asarray(Image.open(f).convert("L").resize((54, 96)), dtype=np.float32)
    lum.append((n, float(a.mean())))
    if a.mean() < 4:
        dark.append(n)
for (n0, l0), (n1, l1) in zip(lum, lum[1:]):
    if n1 not in cuts and abs(l1 - l0) > 12:
        jumps.append((n1, round(l0, 1), round(l1, 1)))
rep["near_black_frames"] = dark
rep["luma_jumps_inside_shots"] = jumps
print(json.dumps(rep, indent=1))
json.dump(rep, open(os.path.join(ROOT, "logs", "qa_report.json"), "w"), indent=1)
