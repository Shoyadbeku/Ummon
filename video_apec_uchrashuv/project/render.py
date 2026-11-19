import sys, os, subprocess, math
from multiprocessing import Pool
import scenes as SC
from engine import *

OUT = os.path.join(SC.ROOT, "segs")


def compose(s, lt, ctx):
    dur = s["t1"] - s["t0"]
    ctx["gt"] = s["t0"] + lt
    img = s["plate"](lt, dur, ctx)
    if img.mode != "RGB":
        img = img.convert("RGB")
    for o in s["ov"]:
        r = o(img, lt, dur)
        if r is not None:
            img = r
    gt = s["t0"] + lt
    if gt > 7.3:
        bug(img, gt)
    if s["tk"]:
        ticker(img, gt)
    cr = s["cr_fn"](lt) if "cr_fn" in s else s["cr"]
    credit(img, cr, s["tk"])
    if s["tr"] == "flash":
        img = flash(img, lt)
    elif s["tr"] == "whip":
        img = whip(img, lt)
    return img


def render(k):
    s = SC.S[k]
    f0, f1 = round(s["t0"] * FPS), round(s["t1"] * FPS)
    out = os.path.join(OUT, f"seg_{k:03d}.mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return k
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out + ".tmp.mp4"], stdin=subprocess.PIPE)
    ctx = {}
    for f in range(f0, f1):
        lt = (f - f0) / FPS
        enc.stdin.write(compose(s, lt, ctx).tobytes())
    enc.stdin.close(); enc.wait()
    for v in ctx.values():
        if hasattr(v, "close"):
            v.close()
    os.rename(out + ".tmp.mp4", out)
    return k


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "still":
        os.makedirs("stills", exist_ok=True)
        for t in map(float, sys.argv[2:]):
            k = max(i for i, s in enumerate(SC.S) if s["t0"] <= t)
            s = SC.S[k]; lt = t - s["t0"]
            ctx = {}
            # advance video plates to lt
            img = None
            n = int(lt * FPS)
            for f in range(n + 1):
                if f == n or any(True for _ in []):
                    img = compose(s, f / FPS, ctx)
                else:
                    for kk, v in list(ctx.items()):
                        if hasattr(v, "frame"):
                            v.frame()
                    if not ctx:
                        compose(s, f / FPS, ctx)
            img.save(f"stills/t{t:06.1f}.jpg", quality=85)
            for v in ctx.values():
                if hasattr(v, "close"): v.close()
            print("still", t, k, s["label"])
    else:
        idx = list(range(len(SC.S)))
        with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 3) as pool:
            for k in pool.imap_unordered(render, idx):
                print("done", k, SC.S[k]["label"], flush=True)
