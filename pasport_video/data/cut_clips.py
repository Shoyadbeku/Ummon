"""Cut every storyboard footage reference into a short 1080p30 H.264 clip (audio removed).
Full-frame clips get a light documentary grade; background clips are pre-blurred and darkened
so the Remotion render needs no CSS filters. Usage: cut_clips.py storyboard.json <yt_dir> <out_dir>"""
import json, subprocess, sys, os, concurrent.futures as cf
S = json.load(open(sys.argv[1])); src = sys.argv[2]; out = sys.argv[3]; os.makedirs(out, exist_ok=True)
ONLY = set(sys.argv[4].split(',')) if len(sys.argv) > 4 else None
jobs = {}
for s in S:
    d = s['end'] - s['t'] + 0.6
    for k in ('clip', 'bg', 'left', 'right'):
        v = s.get(k)
        if isinstance(v, list) and len(v) == 2 and isinstance(v[1], (int, float)):
            vid, st = v; bg = k == 'bg'
            name = f"{vid}_{st:.1f}{'_bg' if bg else ''}.mp4"
            dd = min(d, 4.0) if bg else d
            jobs[name] = (vid, st, max(dd, jobs.get(name, (0, 0, 0, 0))[2]), bg)
# Sources with burned-in subtitles: keep only the top part of the frame so they do not clash with ours.
CROP_TOP = {"57smEMRrGto": 0.74, "5eaASdCxyek": 0.74}
BASE = "scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,fps=30"
def run(item):
    name, (vid, st, d, bg) = item
    if bg:
        vf = "scale=960:540,gblur=sigma=9,eq=brightness=-0.22:saturation=0.75,scale=1920:1080,fps=30,format=yuv420p"
    else:
        pre = f"crop=iw*{CROP_TOP[vid]}:ih*{CROP_TOP[vid]}:(iw-iw*{CROP_TOP[vid]})/2:0," if vid in CROP_TOP else ""
        vf = pre + BASE + ",unsharp=5:5:0.35,eq=contrast=1.07:saturation=0.93,format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(st), "-i", os.path.join(src, vid + '.mp4'), "-t", f"{d:.2f}",
                    "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", os.path.join(out, name)], check=True)
    return name
items = [j for j in jobs.items() if ONLY is None or j[1][0] in ONLY]
with cf.ThreadPoolExecutor(4) as ex:
    for n in ex.map(run, items): print(n)
