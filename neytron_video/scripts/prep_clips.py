"""Pre-render every clip usage to a graded, correctly framed 30fps H.264 file in public/clips/.
roles: frame (main shot, 4:5 window over blurred bg / full-bleed for vertical sources),
       bg (blurred dark background for motion graphics), tile (720x720 square for grids)."""
import json, subprocess, sys, os, concurrent.futures as cf
ROOT = "."
shots = json.load(open(f"{ROOT}/src/shots.json"))
os.makedirs(f"{ROOT}/public/clips", exist_ok=True)
probe = {}
for l in open(f"{ROOT}/raw/probe.txt"):
    p = l.split();
    if len(p) >= 3: w, h = map(int, p[1].split(",")[:2]); probe[p[0]] = (w, h, float(p[2]))
def pr(cid):
    if cid not in probe:
        out = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-show_entries","format=duration","-of","csv=p=0",f"{ROOT}/raw/{cid}.mp4"],capture_output=True,text=True).stdout.split()
        w, h = map(int, out[0].split(",")[:2]); probe[cid] = (w, h, float(out[1]))
    return probe[cid]
GRADE = "eq=contrast=1.07:saturation=1.06:gamma=0.97,colorbalance=rs=-0.03:gs=0.0:bs=0.04:rh=0.04:bh=-0.03,vignette=angle=PI/5"
jobs = []
def add(cid, role, need, key):
    jobs.append((cid[2:], role, need, key))
for i, s in enumerate(shots):
    need = s["dur"] + 0.5
    if s["kind"] == "clip":
        s["file"] = f"clips/s{i:03d}.mp4"; add(s["clip"], "frame", need, s["file"])
    else:
        p = s["props"]
        if p.get("bg"):
            p["bgFile"] = f"clips/s{i:03d}_bg.mp4"; add(p["bg"], "bg", need, p["bgFile"])
        for j, c in enumerate(p.get("clips", [])):
            p.setdefault("clipFiles", []).append(f"clips/s{i:03d}_t{j}.mp4"); add(c, "tile", need, p["clipFiles"][-1])
        for k in ("clipA", "clipB"):
            if p.get(k):
                p[k + "File"] = f"clips/s{i:03d}_{k}.mp4"; add(p[k], "half", need, p[k + "File"])
json.dump(shots, open(f"{ROOT}/src/shots.json", "w"), ensure_ascii=False, indent=1)
mask = f"{ROOT}/raw/mask_4x5.png"
if not os.path.exists(mask):
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=white:s=1080x1350","-vf",
        "format=gray,geq=lum='255*min(1,min(Y/150,(1350-Y)/150))'","-frames:v","1",mask],check=True)
def run(job):
    cid, role, need, key = job
    out = f"{ROOT}/public/{key}"
    if os.path.exists(out) and os.path.getsize(out) > 1000: return
    w, h, d = pr(cid)
    vertical = h > w
    start = 0.4 if d > need + 0.8 else 0.0
    avail = d - start - 0.05
    speed = max(1.0, need / avail)  # slow-mo if the clip is too short
    pre = f"trim=start={start},setpts=(PTS-STARTPTS)*{speed:.4f},fps=30"
    if role == "frame" and not vertical:
        fc = (f"[0:v]{pre},split[a][b];"
              f"[a]scale=-2:1920,crop=1080:1920,boxblur=28:2,eq=brightness=-0.10:saturation=0.75[bg];"
              f"[b]crop=ih*0.8:ih,scale=1080:1350:flags=lanczos,unsharp=5:5:0.5[fg0];[fg0][1:v]alphamerge[fg];"
              f"[bg][fg]overlay=0:285,{GRADE},format=yuv420p[v]")
        inputs = ["-i", f"{ROOT}/raw/{cid}.mp4", "-loop", "1", "-i", mask]
    elif role in ("frame", "bg"):
        extra = ",boxblur=6:1,eq=brightness=-0.18:saturation=0.8" if role == "bg" else ",unsharp=5:5:0.4"
        fc = f"[0:v]{pre},scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920{extra},{GRADE},format=yuv420p[v]"
        inputs = ["-i", f"{ROOT}/raw/{cid}.mp4"]
    elif role == "tile":
        fc = f"[0:v]{pre},crop=min(iw\\,ih):min(iw\\,ih),scale=720:720:flags=lanczos,{GRADE},format=yuv420p[v]"
        inputs = ["-i", f"{ROOT}/raw/{cid}.mp4"]
    else:  # half: 1080x960 landscape-ish crop
        fc = f"[0:v]{pre},scale=1080:960:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:960,{GRADE},format=yuv420p[v]"
        inputs = ["-i", f"{ROOT}/raw/{cid}.mp4"]
    cmd = ["ffmpeg","-v","error","-y",*inputs,"-filter_complex",fc,"-map","[v]","-t",f"{need:.3f}","-an",
           "-c:v","libx264","-preset","veryfast","-crf","19","-g","15","-movflags","+faststart",out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print("FAIL", key, r.stderr[-400:])
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(run, jobs))
print(len(jobs), "jobs done")
