import subprocess, os, sys, json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl import SCENES, SRC, CROP, FPS, ts

OUT = "build/segs"
os.makedirs(OUT, exist_ok=True)

LOOK = {
    "n": "eq=contrast=1.06:saturation=1.10:gamma=0.98,vignette=angle=PI/5",
    "d": "eq=contrast=1.14:saturation=0.80:brightness=-0.035,colorbalance=bs=0.06:bm=0.02:bh=-0.03,vignette=angle=PI/4",
    "a": "hue=s=0.22,eq=contrast=1.12:brightness=-0.02,colorchannelmixer=rr=0.95:rg=0.08:gg=0.92:gb=0.05:bb=0.82,noise=alls=14:allf=t,vignette=angle=PI/3.5",
    "b": "boxblur=22:2,eq=brightness=-0.16:saturation=0.65,vignette=angle=PI/4",
}

def job(i):
    t0, t1, src, sin, look, note = SCENES[i]
    n = round(t1 * FPS) - round(t0 * FPS)
    dur = n / FPS
    out = f"{OUT}/s{i:03d}.mp4"
    if look == "k":
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x05070c:s=1920x1080:r={FPS}",
               "-frames:v", str(n)]
    else:
        vid = SRC[src][0]
        pre = ""
        if src in CROP:
            x, y, w, h = CROP[src]
            pre = f"crop={w}:{h}:{x}:{y},"
        z = 1.06 if look != "b" else 1.0
        W, H = int(1920 * z) // 2 * 2, int(1080 * z) // 2 * 2
        dx = W - 1920
        dirn = 1 if i % 2 == 0 else -1
        xexpr = f"{dx}*t/{dur:.3f}" if dirn > 0 else f"{dx}-{dx}*t/{dur:.3f}"
        yexpr = f"{(H-1080)//2}"
        vf = (f"{pre}fps={FPS},scale={W}:{H}:flags=lanczos,crop=1920:1080:'{xexpr}':{yexpr},"
              f"{LOOK[look]},setsar=1,format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ts(sin):.3f}", "-i", f"yt/{vid}.mp4",
               "-an", "-vf", vf, "-frames:v", str(n)]
    cmd += ["-r", str(FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True)
    got = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out],
                             capture_output=True, text=True).stdout.strip())
    return i, n, got

if __name__ == "__main__":
    idx = range(len(SCENES)) if len(sys.argv) < 2 else [int(a) for a in sys.argv[1:]]
    with ThreadPoolExecutor(4) as ex:
        for i, n, got in ex.map(job, idx):
            flag = "" if n == got else "  <-- FRAME MISMATCH"
            print(f"s{i:03d} want {n} got {got}{flag}", flush=True)
    with open("build/concat.txt", "w") as f:
        for i in range(len(SCENES)):
            f.write(f"file 'segs/s{i:03d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "build/concat.txt",
                    "-c", "copy", "build/base.mp4"], check=True)
    print("base done")
