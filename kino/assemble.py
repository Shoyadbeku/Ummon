"""Kliplarni ovozga moslab, 1080x1920 ga kattalashtirib, kino uslubida birlashtiradi.

Ishlatish: python assemble.py --clips CLIPS_DIR --out final.mp4
"""
import argparse, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--clips", default=os.path.join(HERE, "clips"))
ap.add_argument("--out", default=os.path.join(HERE, "kino_final.mp4"))
ap.add_argument("--xfade", type=float, default=0.25)
a = ap.parse_args()

cfg = json.load(open(os.path.join(HERE, "scenes.json")))
fps, d, sc = cfg["fps"], a.xfade, cfg["scenes"]
n = len(sc)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())

inputs, parts = [], []
for k, s in enumerate(sc):
    clip = os.path.join(a.clips, f"clip{s['id']}.mp4")
    L = s["end"] - s["start"] + (cfg["tail"] if k == n - 1 else 0)
    S = L + (d if k < n - 1 else 0)  # o'tish uchun ozgina ortiqcha
    cd = dur(clip)
    f = S / cd
    chain = f"[{k}:v]fps={fps},setpts=PTS-STARTPTS"
    if f > 1.02:  # klip qisqa: sekinlashtirib, kadrlarni interpolyatsiya qilish
        chain += f",setpts={f:.4f}*PTS,minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    chain += (f",trim=duration={S:.3f},setpts=PTS-STARTPTS,"
              f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,"
              f"unsharp=5:5:0.6:5:5:0.0,setsar=1,format=yuv420p[v{k}]")
    inputs += ["-i", clip]
    parts.append(chain)

prev, acc = "v0", 0.0
for k in range(1, n):
    acc += sc[k - 1]["end"] - sc[k - 1]["start"]
    o = f"x{k}"
    parts.append(f"[{prev}][v{k}]xfade=transition=fade:duration={d}:offset={acc:.3f}[{o}]")
    prev = o
total = sc[-1]["end"] - sc[0]["start"] + cfg["tail"]
parts.append(f"[{prev}]eq=contrast=1.04:saturation=1.06,vignette=PI/6,"
             f"fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.6:.3f}:d=0.6[vout]")
parts.append(f"[{n}:a]apad,atrim=duration={total:.3f},afade=t=out:st={total - 0.6:.3f}:d=0.6[aout]")
cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-i", os.path.join(HERE, cfg["audio"]),
       "-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-r", str(fps), a.out]
subprocess.run(cmd, check=True)
print("Tayyor:", a.out, f"({dur(a.out):.2f} s)")
