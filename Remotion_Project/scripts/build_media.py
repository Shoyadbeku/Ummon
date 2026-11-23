#!/usr/bin/env python3
"""Cut every storyboard shot into a short, muted 1920x1080 / 30 fps clip and write the
timeline JSON consumed by the Remotion composition.

usage: python3 build_media.py <footage_root> [--only N,M]
  footage_root: folder containing YouTube_Archives/, YouTube_Interviews/, ... (downloaded via snapyt.app)
Only the few seconds needed per shot are extracted (fair-use short excerpts).
"""
import json, os, subprocess, sys, re
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from storyboard import S
from sources import SOURCES

ROOT = sys.argv[1]
PROJ = os.path.dirname(HERE)
MEDIA = os.path.join(PROJ, "public", "media")
DATA = os.path.join(PROJ, "src", "data")
os.makedirs(MEDIA, exist_ok=True); os.makedirs(DATA, exist_ok=True)
FPS = 30
AUDIO_END = 813.31
HANDLE = 0.5  # extra seconds for cross-dissolves

_dur = {}
def src_path(sid):
    return os.path.join(ROOT, SOURCES[sid]["folder"], sid + ".mp4")
def src_duration(sid):
    if sid not in _dur:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src_path(sid)],
                             capture_output=True, text=True).stdout.strip()
        _dur[sid] = float(out)
    return _dur[sid]

# ---------- build shot list ----------
shots, scenes = [], []
for i, sc in enumerate(S):
    v_start = 0.0 if i == 0 else sc["start"]
    v_end = S[i + 1]["start"] if i + 1 < len(S) else AUDIO_END
    n = len(sc["shots"])
    f0 = round(v_start * FPS); f1 = round(v_end * FPS)
    bounds = [f0 + round((f1 - f0) * k / n) for k in range(n + 1)]
    lts = sc["extras"].get("lts")
    if lts is None and sc["extras"].get("lt"):
        lts = [sc["extras"]["lt"]] + [None] * (n - 1)
    for k, shot in enumerate(sc["shots"]):
        sid, t, crop, label = shot[:4]
        freeze = len(shot) > 4 and shot[4] == "freeze"
        idx = len(shots)
        dur_f = bounds[k + 1] - bounds[k]
        shots.append(dict(idx=idx, scene=i, src=sid, t=t, crop=crop, label=label,
                          credit=SOURCES[sid]["credit"], kind=SOURCES[sid]["kind"],
                          from_=bounds[k], dur=dur_f, file=f"media/s{idx:03d}.mp4",
                          lt=(lts[k] if lts and k < len(lts) else None), freeze=freeze))
    scenes.append(dict(i=i, start=sc["start"], end=sc["end"], vFrom=f0, vTo=f1, text=sc["text"],
                       extras={k: v for k, v in sc["extras"].items() if k not in ("lt", "lts")}))

# ---------- subtitles: split into readable cues, timed proportionally ----------
def split_text(text, maxlen=84):
    parts = re.split(r"(?<=[.!?;—:])\s+|(?<=,)\s+", text)
    cues, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= maxlen:
            cur = (cur + " " + p).strip()
        else:
            if cur: cues.append(cur)
            while len(p) > maxlen:
                cut = p.rfind(" ", 0, maxlen)
                cues.append(p[:cut]); p = p[cut + 1:]
            cur = p
    if cur: cues.append(cur)
    return cues

subs = []
for sc in S:
    if not sc["text"]:
        continue
    cues = split_text(sc["text"])
    total = sum(len(c) for c in cues)
    t = sc["start"]
    span = sc["end"] - sc["start"]
    for c in cues:
        d = span * len(c) / total
        subs.append(dict(start=round(t, 2), end=round(t + d, 2), text=c))
        t += d

# ---------- cut clips ----------
def cut(sh):
    out = os.path.join(PROJ, "public", sh["file"])
    only = os.environ.get("ONLY")
    if os.path.exists(out) and not only and not os.environ.get("FORCE"):
        return sh["idx"], "skip"
    if only and str(sh["idx"]) not in only.split(","):
        return sh["idx"], "skip"
    need = sh["dur"] / FPS + HANDLE
    sd = src_duration(sh["src"])
    t = min(sh["t"], max(0.0, sd - need - 0.1))
    crop = ""
    if sh["crop"]:
        x, y, w, h = sh["crop"]
        crop = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"
    vf = (f"[0:v]{crop}setsar=1,split[a][b];"
          f"[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=40:2,eq=brightness=-0.18:saturation=0.6[bg];"
          f"[b]scale=1920:1080:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={FPS},format=yuv420p[v]")
    if sh.get("freeze"):  # hold a single verified frame (photo/document) for the whole shot
        vf = vf.replace("[0:v]", "[0:v]trim=end_frame=1,loop=loop=-1:size=1,setpts=N/25/TB,")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-t", f"{need:.3f}"] + (["-t", f"{need:.3f}"] if False else []) + ["-i", src_path(sh["src"]),
           "-filter_complex", vf, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-g", "15", "-t", f"{need:.3f}", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sh["t_used"] = t
    return sh["idx"], ("ok" if r.returncode == 0 else "ERR " + r.stderr[-300:])

with ThreadPoolExecutor(4) as ex:
    for idx, st in ex.map(cut, shots):
        if st != "skip":
            print(idx, st, flush=True)

for sh in shots:
    sd = src_duration(sh["src"]); need = sh["dur"] / FPS + HANDLE
    sh["t_used"] = round(min(sh["t"], max(0.0, sd - need - 0.1)), 2)
    sh["from"] = sh.pop("from_")

json.dump(dict(fps=FPS, durationInFrames=round(AUDIO_END * FPS), shots=shots, scenes=scenes, subs=subs),
          open(os.path.join(DATA, "timeline.json"), "w"), ensure_ascii=False, indent=1)
print("shots", len(shots), "subs", len(subs))
